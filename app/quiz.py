"""quiz.py - timed quiz with auto-generated questions from weak misconceptions."""
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

def build_quiz_from_syllabus(syllabus_text: str, n_questions: int = 10) -> list[dict]:
    """Ask the LLM to write N questions from the syllabus text, then verify each."""
    from app.llm import _get_model, _text
    from langchain_core.messages import HumanMessage, SystemMessage
    import json, random

    model = _get_model()
    if model is None:
        return []

    sys = (
        "You are a maths tutor. Read the syllabus or textbook excerpt the user provides. "
        "Generate {n} short algebra problems that cover the topics listed. "
        "Return ONLY a JSON array. Each item must be: "
        '{{"problem": "2x + 3 = 11", "answer": "x = 4", "topic": "linear equations"}}. '
        "No prose. No markdown code fences. Just the JSON array."
    ).format(n=n_questions)
    try:
        raw = _text(model.invoke([
            SystemMessage(content=sys),
            HumanMessage(content=syllabus_text[:6000]),
        ])).strip()
        # Strip code fences if the model adds them
        if raw.startswith("```"):
            raw = raw.strip("`")
            raw = raw[raw.find("["):raw.rfind("]") + 1]
        items = json.loads(raw)
        out = []
        for item in items:
            out.append({
                "problem": str(item.get("problem", "")).strip(),
                "answer": str(item.get("answer", "")).strip(),
                "topic": str(item.get("topic", "")).strip(),
                "tag": "SYLLABUS",
            })
        return out
    except Exception as e:
        print("SYLLABUS QUIZ ERROR:", e)
        return []