"""adaptive.py - track streaks and pick difficulty for twin problems."""
import random
import sqlite3
import time

DB = "adaptive.db"


def _conn():
    c = sqlite3.connect(DB)
    c.execute("""
        CREATE TABLE IF NOT EXISTS streaks(
            user TEXT, tag TEXT,
            consecutive INT DEFAULT 0,
            updated REAL,
            PRIMARY KEY (user, tag)
        )
    """)
    c.commit()
    return c


def record_attempt(user, tag, correct):
    """Update the streak for this user-tag pair."""
    c = _conn()
    c.execute("INSERT OR IGNORE INTO streaks(user, tag, consecutive) VALUES(?,?,0)",
              (user, tag))
    row = c.execute("SELECT consecutive FROM streaks WHERE user=? AND tag=?",
                    (user, tag)).fetchone()
    streak = row[0] if row else 0
    streak = streak + 1 if correct else 0
    c.execute("UPDATE streaks SET consecutive=?, updated=? WHERE user=? AND tag=?",
              (streak, time.time(), user, tag))
    c.commit()
    c.close()
    return streak


def get_streak(user, tag):
    c = _conn()
    row = c.execute("SELECT consecutive FROM streaks WHERE user=? AND tag=?",
                    (user, tag)).fetchone()
    c.close()
    return row[0] if row else 0


def pick_difficulty(user, tag):
    """Return 'easy' | 'medium' | 'hard' for the next twin."""
    s = get_streak(user, tag)
    if s >= 3:
        return "hard"
    if s == 0:
        return "easy"
    return "medium"


def make_problem(tag, difficulty):
    """Generate a problem of the given difficulty for the tag."""
    if difficulty == "easy":
        coeffs, sol_range = [2, 3], range(-3, 4)
    elif difficulty == "hard":
        coeffs, sol_range = [4, 5, 6, 7, 8, 9], range(-12, 13)
    else:
        coeffs, sol_range = [2, 3, 4, 5], range(-9, 10)

    x0 = random.choice(list(sol_range))
    a = random.choice(coeffs)
    b = random.randint(2, 9)

    if tag == "FORGOT_TO_DISTRIBUTE":
        return f"{a}(x + {b}) = {a * (x0 + b)}"
    c = a * x0 + b
    return f"{a}x + {b} = {c}"