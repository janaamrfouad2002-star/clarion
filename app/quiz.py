"""quiz.py - timed quiz with auto-generated questions from weak misconceptions or syllabus."""
import random
import time

from app import core


# ---------- problem generation ----------

def _problem_for_tag(tag: str, rng: random.Random) -> dict:
    x0 = rng.randint(-9, 9)
    a = rng.choice([2, 3, 4, 5, 6])
    b = rng.randint(2, 9)
    if tag == "FORGOT_TO_DISTRIBUTE":
        problem = f"{a}(x + {b}) = {a * (x0 + b)}"
    else:
        problem = f"{a}x + {b} = {a * x0 + b}"
    return {"problem": problem, "answer": x0, "tag": tag}


def build_quiz(user: str, n_questions: int = 10) -> list[dict]:
    """Prioritise the user's weakest misconception tags, then fill from the rest."""
    from app.core import mistake_map

    rows = mistake_map(user)
    weak = [r[0] for r in sorted(rows, key=lambda r: (r[2], -r[1]))][:4]
    all_tags = list(core.BUGS.keys())
    pool = weak + [t for t in all_tags if t not in weak]

    rng = random.Random(int(time.time()))
    questions = []
    for i in range(n_questions):
        tag = pool[i % len(pool)]
        questions.append(_problem_for_tag(tag, rng))
    rng.shuffle(questions)
    return questions


def build_quiz_from_syllabus(syllabus_text: str, n_questions: int = 10) -> list[dict]:
    """Generate quiz questions STRICTLY from the syllabus text."""
    from app.llm import _get_model, _text
    from langchain_core.messages import HumanMessage, SystemMessage
    import json

    model = _get_model()
    if model is None:
        return []

    sys = (
        "You are a strict exam generator. Your ONLY job is to create questions based "
        "exactly on the provided text. Do not use outside knowledge. "
        f"Generate {n_questions} math/algebra problems that test the specific topics in the text. "
        "Return ONLY a valid JSON array. Each item must be exactly this format: "
        '[{"problem": "2x + 3 = 11", "answer": "x = 4", "topic": "linear equations"}]. '
        "Do not include markdown blocks like ```json. Just the raw array."
    )
    
    user_content = f"Here is the syllabus text. Generate questions ONLY from this:\n\n{syllabus_text[:8000]}"

    try:
        raw = _text(model.invoke([
            SystemMessage(content=sys),
            HumanMessage(content=user_content),
        ])).strip()
        
        # Clean up the response in case the AI adds markdown
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        
        raw = raw.strip()
        if not raw.startswith("["):
            raw = "[" + raw
        if not raw.endswith("]"):
            raw = raw + "]"

        items = json.loads(raw)
        
        return [{"problem": str(i.get("problem", "")).strip(),
                 "answer": str(i.get("answer", "")).strip(),
                 "topic": str(i.get("topic", "")).strip(),
                 "tag": "SYLLABUS"} for i in items]
                 
    except Exception as e:
        print("SYLLABUS QUIZ ERROR:", e)
        return []


# ---------- scoring ----------

def check_answer(question: dict, student_lines: list[str]) -> bool:
    """Run the same algebra checker used elsewhere in the app."""
    steps = [question["problem"]] + [s.strip().replace("^", "**")
                                     for s in student_lines if s.strip()]
    return len(steps) > 1 and core.first_wrong_step(steps) is None


def score_summary(correct: int, total: int, elapsed: float) -> dict:
    pct = round(100 * correct / total) if total else 0
    avg = round(elapsed / total, 1) if total else 0
    if pct >= 80:
        grade = "🌟 Excellent"
    elif pct >= 60:
        grade = "👍 Good"
    elif pct >= 40:
        grade = "🙂 Keep going"
    else:
        grade = "💪 Try again"
    return {"pct": pct, "avg_seconds": avg, "grade": grade}