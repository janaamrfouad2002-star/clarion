"""engine.py - routes a structured problem to the right verifier."""
from typing import Literal

from pydantic import BaseModel, Field
from sympy import integrate, solve as sym_solve, sympify

from app import calculus, core, science, shapes
from app.core import diagnose_with_confidence

core.EXPLANATIONS.update(calculus.EXPLANATIONS)
core.EXPLANATIONS.update(science.EXPLANATIONS)
core.EXPLANATIONS.update(shapes.GEOM_BUGS)
core.EXPLANATIONS.update(shapes.TRIG_BUGS)
core.EXPLANATIONS.update(shapes.STAT_BUGS)


class Extracted(BaseModel):
    """What the LLM extracts from the student's text and/or photo."""
    subject: Literal[
        "algebra", "derivative", "integral",
        "chemistry_balance", "physics_calc",
        "geometry", "trigonometry", "statistics",
        "other",
    ] = "other"
    steps: list[str] = Field(default_factory=list)
    expression: str = ""
    student_answer: str = ""
    shape_kind: str = ""
    values: dict = Field(default_factory=dict)


def solve_question(ex: Extracted) -> dict:
    if ex.subject == "derivative" and ex.expression.strip():
        f = calculus.parse(ex.expression)
        return {"status": "solved", "subject": "derivative",
                "question": f"derivative of {ex.expression}",
                "answer": str(f.diff(core.x))}
    if ex.subject == "integral" and ex.expression.strip():
        f = calculus.parse(ex.expression)
        return {"status": "solved", "subject": "integral",
                "question": f"integral of {ex.expression}",
                "answer": f"{integrate(f, core.x)} + C"}

    if ex.subject == "algebra" and ex.steps:
        first_raw = ex.steps[0]
        first = first_raw.replace("^", "**")
        low = first_raw.lower()
        if "derivative" in low or "differentiate" in low:
            expr = first_raw.lower().split("of", 1)[-1].strip(" ?.")
            try:
                f = calculus.parse(expr)
                return {"status": "solved", "subject": "derivative",
                        "question": f"derivative of {expr}",
                        "answer": str(f.diff(core.x))}
            except Exception:
                return {"status": "unsupported"}
        if "integral" in low or "integrate" in low:
            expr = first_raw.lower().split("of", 1)[-1].strip(" ?.")
            try:
                f = calculus.parse(expr)
                return {"status": "solved", "subject": "integral",
                        "question": f"integral of {expr}",
                        "answer": f"{integrate(f, core.x)} + C"}
            except Exception:
                return {"status": "unsupported"}
        if "=" not in first:
            try:
                val = sympify(first)
                return {"status": "solved", "subject": "arithmetic",
                        "question": first, "answer": str(val)}
            except Exception:
                return {"status": "unsupported"}
        eq = core.parse_equation(first)
        if not eq.has(core.x):
            return {"status": "unsupported"}
        return {"status": "solved", "subject": "algebra",
                "question": ex.steps[0], "answer": f"x = {sym_solve(eq, core.x)}"}

    if ex.subject == "chemistry_balance" and ex.expression.strip():
        return {"status": "solved", "subject": "chemistry_balance",
                "question": f"Balance: {ex.expression}",
                "answer": science.balance_equation(ex.expression)}
    if ex.subject == "physics_calc" and ex.expression.strip():
        return {"status": "solved", "subject": "physics_calc",
                "question": f"Calculate: {ex.expression}",
                "answer": science.solve_calc(ex.expression)}
    return {"status": "unsupported"}


def analyse(ex: Extracted) -> dict:
    if ex.subject == "algebra":
        steps = [s.replace("^", "**") for s in ex.steps if "=" in s]
        if len(steps) >= 2:
            i = core.first_wrong_step(steps)
            if i is None:
                return {"status": "correct", "subject": "algebra"}
            tag, conf = diagnose_with_confidence(steps[i - 1], steps[i])
            return {"status": "wrong", "subject": "algebra",
                    "tag": tag, "confidence": conf,
                    "prev": steps[i - 1], "wrong": steps[i]}
        return solve_question(ex)

    if ex.subject in ("derivative", "integral"):
        if ex.student_answer.strip():
            return calculus.check(ex.subject, ex.expression, ex.student_answer)
        return solve_question(ex)

    if ex.subject == "chemistry_balance":
        if ex.student_answer.strip():
            return science.check_balance(ex.student_answer)
        return solve_question(ex)

    if ex.subject == "physics_calc":
        if ex.student_answer.strip():
            return science.check_calc(ex.expression, ex.student_answer)
        return solve_question(ex)

    if ex.subject == "geometry":
        if not ex.shape_kind:
            return {"status": "unsupported"}
        if ex.student_answer.strip():
            return shapes.check_geometry(ex.shape_kind, ex.values, ex.student_answer)
        return {"status": "unsupported"}

    if ex.subject == "trigonometry":
        if not ex.shape_kind:
            return {"status": "unsupported"}
        if ex.student_answer.strip():
            return shapes.check_trig(ex.shape_kind, ex.values, ex.student_answer)
        return {"status": "unsupported"}

    if ex.subject == "statistics":
        if not ex.shape_kind:
            return {"status": "unsupported"}
        if ex.student_answer.strip():
            return shapes.check_stat(ex.shape_kind, ex.values, ex.student_answer)
        return {"status": "unsupported"}

    return {"status": "unsupported"}


def make_twin(subject: str, tag: str) -> str:
    if subject == "algebra":
        return core.make_problem(tag)
    if subject == "chemistry_balance":
        return science.make_chem_twin()
    if subject == "physics_calc":
        return science.make_phys_twin()
    if subject == "geometry":
        return shapes.make_geom_twin(tag)
    if subject == "trigonometry":
        return shapes.make_trig_twin(tag)
    if subject == "statistics":
        return shapes.make_stat_twin(tag)
    return calculus.make_problem(subject, tag)


def check_twin(subject: str, problem: str, student_text: str) -> bool:
    if subject == "algebra":
        steps = [problem] + [s.strip().replace("^", "**")
                             for s in student_text.splitlines() if s.strip()]
        return len(steps) > 1 and core.first_wrong_step(steps) is None
    if subject == "chemistry_balance":
        return science.check_chem_twin(problem, student_text)
    if subject == "physics_calc":
        return science.check_calc(problem, student_text)["status"] == "correct"
    if subject in ("geometry", "trigonometry", "statistics"):
        return False
    return calculus.check(subject, problem, student_text)["status"] == "correct"