"""shapes.py - verifier modules for geometry, trigonometry, statistics."""
import random
from math import sin, cos, tan, radians, degrees, pi, sqrt

from sympy import (Eq, symbols, solve, simplify, sympify, trigsimp, sin as S_sin,
                   cos as S_cos, tan as S_tan, N, oo)

x = symbols("x")

# ---------- GEOMETRY ----------

GEOM_BUGS = {
    "USED_DIAMETER_AS_RADIUS": "Used diameter instead of radius",
    "FORGOT_SQUARE_IN_AREA": "Forgot to square in area formula",
    "PERIMETER_VS_AREA_CONFUSION": "Used perimeter formula for area",
    "WRONG_TRIANGLE_FORMULA": "Used wrong triangle formula",
}


def check_geometry(kind: str, values: dict, answer: str) -> dict:
    """kind: 'circle_area', 'circle_circumference', 'triangle_area',
             'rectangle_area', 'rectangle_perimeter'."""
    base = {"subject": "geometry", "prev": f"{kind} with {values}", "wrong": answer}

    try:
        student = sympify(answer)
    except Exception:
        return {**base, "status": "unsupported"}

    correct, bug_hint = None, None

    if kind == "circle_area":
        r = values.get("r", 0)
        correct = pi * r ** 2
        if student == pi * r:                       # forget to square
            bug_hint = "FORGOT_SQUARE_IN_AREA"
        elif student == 2 * pi * r:                 # used circumference
            bug_hint = "PERIMETER_VS_AREA_CONFUSION"
        elif student == pi * (2 * r) ** 2:          # used diameter as radius
            bug_hint = "USED_DIAMETER_AS_RADIUS"

    elif kind == "circle_circumference":
        r = values.get("r", 0)
        correct = 2 * pi * r
        if student == pi * r ** 2:
            bug_hint = "PERIMETER_VS_AREA_CONFUSION"
        elif student == pi * r:
            bug_hint = "USED_DIAMETER_AS_RADIUS"

    elif kind == "triangle_area":
        b, h = values.get("b", 0), values.get("h", 0)
        correct = b * h / 2
        if student == b * h:
            bug_hint = "WRONG_TRIANGLE_FORMULA"

    elif kind == "rectangle_area":
        w, h = values.get("w", 0), values.get("h", 0)
        correct = w * h
        if student == 2 * (w + h):
            bug_hint = "PERIMETER_VS_AREA_CONFUSION"

    elif kind == "rectangle_perimeter":
        w, h = values.get("w", 0), values.get("h", 0)
        correct = 2 * (w + h)
        if student == w * h:
            bug_hint = "PERIMETER_VS_AREA_CONFUSION"

    else:
        return {**base, "status": "unsupported"}

    if simplify(student - correct) == 0:
        return {"status": "correct", "subject": "geometry"}

    tag = bug_hint or "WRONG_VALUE"
    return {**base, "status": "wrong", "tag": tag,
            "explanation_correct": str(correct)}

# ---------- TRIGONOMETRY ----------

TRIG_BUGS = {
    "MISSING_ANGLE_UNIT": "Forgot to convert degrees to radians",
    "WRONG_TRIG_RATIO": "Used wrong trig ratio (SOH/CAH/TOA)",
    "FORGOT_PYTHAGOREAN": "Did not use the Pythagorean identity",
}


def check_trig(kind: str, values: dict, answer: str) -> dict:
    """kind: 'sin', 'cos', 'tan', 'find_hypotenuse', 'find_angle'."""
    base = {"subject": "trigonometry", "prev": f"{kind} with {values}", "wrong": answer}
    try:
        student = float(sympify(answer))
    except Exception:
        return {**base, "status": "unsupported"}

    deg = values.get("angle_deg")
    rad = values.get("angle_rad")
    if rad is None and deg is not None:
        rad = radians(deg)

    correct, bug_hint = None, None

    if kind == "sin":
        correct = sin(rad)
        if abs(student - sin(deg if deg is not None else 0)) < 1e-6:
            bug_hint = "MISSING_ANGLE_UNIT"
    elif kind == "cos":
        correct = cos(rad)
        if abs(student - cos(deg if deg is not None else 0)) < 1e-6:
            bug_hint = "MISSING_ANGLE_UNIT"
    elif kind == "tan":
        correct = tan(rad)
        if abs(student - tan(deg if deg is not None else 0)) < 1e-6:
            bug_hint = "MISSING_ANGLE_UNIT"
    elif kind == "find_hypotenuse":
        a, b = values.get("opp", 0), values.get("adj", 0)
        correct = sqrt(a ** 2 + b ** 2)
        if abs(student - (a + b)) < 1e-3:
            bug_hint = "FORGOT_PYTHAGOREAN"
    else:
        return {**base, "status": "unsupported"}

    if abs(student - correct) < 1e-3:
        return {"status": "correct", "subject": "trigonometry"}

    return {**base, "status": "wrong", "tag": bug_hint or "WRONG_VALUE",
            "explanation_correct": round(correct, 6)}

# ---------- STATISTICS ----------

STAT_BUGS = {
    "MEAN_VS_MEDIAN_CONFUSION": "Computed median instead of mean",
    "FORGOT_SQUARE_DIFFERENCES": "Forgot to square the differences when finding variance",
    "SAMPLE_VS_POPULATION": "Used sample size instead of population size for variance",
    "FORGOT_SQRT_FOR_SD": "Forgot to take square root of variance",
}


def check_stat(kind: str, values: dict, answer: str) -> dict:
    """kind: 'mean', 'median', 'mode', 'variance', 'std'."""
    base = {"subject": "statistics", "prev": f"{kind} of {values.get('data')}", "wrong": answer}
    data = values.get("data", [])
    if not data:
        return {**base, "status": "unsupported"}

    n = len(data)
    try:
        student = float(sympify(answer))
    except Exception:
        return {**base, "status": "unsupported"}

    srt = sorted(data)
    mean = sum(data) / n
    median = (srt[n // 2] if n % 2 else (srt[n // 2 - 1] + srt[n // 2]) / 2)
    var_pop = sum((v - mean) ** 2 for v in data) / n

    correct, bug_hint = None, None

    if kind == "mean":
        correct = mean
        if abs(student - median) < 1e-6:
            bug_hint = "MEAN_VS_MEDIAN_CONFUSION"
    elif kind == "median":
        correct = median
        if abs(student - mean) < 1e-6:
            bug_hint = "MEAN_VS_MEDIAN_CONFUSION"
    elif kind == "variance":
        correct = var_pop
        if abs(student - sum((v - mean) for v in data) / n) < 1e-6:
            bug_hint = "FORGOT_SQUARE_DIFFERENCES"
        elif abs(student - var_pop * n / (n - 1)) < 1e-6:
            bug_hint = "SAMPLE_VS_POPULATION"
    elif kind == "std":
        correct = var_pop ** 0.5
        if abs(student - var_pop) < 1e-6:
            bug_hint = "FORGOT_SQRT_FOR_SD"
    else:
        return {**base, "status": "unsupported"}

    if abs(student - correct) < 1e-6:
        return {"status": "correct", "subject": "statistics"}

    return {**base, "status": "wrong", "tag": bug_hint or "WRONG_VALUE",
            "explanation_correct": round(correct, 6)}


def make_geom_twin(kind: str) -> str:
    r = random.randint(2, 10)
    if kind == "circle_area":
        return f"Area of a circle with radius r = {r}"
    if kind == "triangle_area":
        return f"Area of a triangle with base b = {r} and height h = {random.randint(2,10)}"
    return f"Problem with {kind}"


def make_trig_twin(kind: str) -> str:
    deg = random.choice([30, 45, 60, 90])
    return f"{kind}({deg}°)"

def make_stat_twin(kind: str) -> str:
    data = [random.randint(1, 10) for _ in range(5)]
    return f"{kind} of the data set {data}"