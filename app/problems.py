"""problems.py - fixed problem sets for the pre/post/delayed study phases."""
import json
import os
import random

TAGS = ["SIGN_ERROR_MOVING_TERM", "FORGOT_TO_DIVIDE",
        "MULTIPLIED_INSTEAD_OF_DIVIDED", "FORGOT_TO_DISTRIBUTE"]

# 5 per tag = 20 problems per phase
PER_TAG = 5


def _generate(tag: str, rng: random.Random) -> str:
    """One problem of the given misconception tag."""
    x0 = rng.randint(-9, 9)
    a = rng.choice([2, 3, 4, 5, 6])
    b = rng.randint(2, 9)
    if tag == "FORGOT_TO_DISTRIBUTE":
        return f"{a}(x + {b}) = {a * (x0 + b)}"
    c = a * x0 + b
    return f"{a}x + {b} = {c}"


def build_set(seed: int) -> list[dict]:
    """20 problems, 5 per misconception, deterministic by seed."""
    rng = random.Random(seed)
    problems = []
    for tag in TAGS:
        for _ in range(PER_TAG):
            problems.append({"tag": tag, "problem": _generate(tag, rng)})
    rng.shuffle(problems)
    return problems


def save_all(path: str = "data"):
    os.makedirs(path, exist_ok=True)
    sets = {
        "pretest": build_set(1001),
        "posttest": build_set(2002),
        "delayed": build_set(3003),
    }
    for name, items in sets.items():
        with open(os.path.join(path, f"{name}.json"), "w") as f:
            json.dump(items, f, indent=2)
    return sets


def load(name: str, path: str = "data") -> list[dict]:
    fp = os.path.join(path, f"{name}.json")
    if not os.path.exists(fp):
        save_all(path)
    with open(fp) as f:
        return json.load(f)


if __name__ == "__main__":
    save_all()
    print("Wrote pretest.json, posttest.json, delayed.json to ./data/")