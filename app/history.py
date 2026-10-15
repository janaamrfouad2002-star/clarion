"""history.py - persistent log of every student attempt (right / wrong / asked)."""
import sqlite3
import time

DB = "history.db"


def _conn():
    c = sqlite3.connect(DB)
    c.execute("""
        CREATE TABLE IF NOT EXISTS attempts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            kind TEXT,        -- 'right' | 'wrong' | 'asked'
            label TEXT,
            tag TEXT,
            created REAL
        )
    """)
    return c


def add(user: str, kind: str, label: str, tag: str = ""):
    c = _conn()
    c.execute("INSERT INTO attempts(user, kind, label, tag, created) VALUES(?,?,?,?,?)",
              (user, kind, (label or "").replace("\n", " ")[:120], tag, time.time()))
    c.commit()
    c.close()


def counts(user: str) -> dict:
    c = _conn()
    rows = c.execute(
        "SELECT kind, COUNT(*) FROM attempts WHERE user=? GROUP BY kind", (user,)
    ).fetchall()
    c.close()
    out = {"right": 0, "wrong": 0, "asked": 0}
    for kind, n in rows:
        out[kind] = n
    return out


def recent(user: str, limit: int = 30):
    c = _conn()
    rows = c.execute(
        """SELECT kind, label, tag FROM attempts
           WHERE user=? ORDER BY created DESC LIMIT ?""",
        (user, limit)
    ).fetchall()
    c.close()
    return rows   # newest first


def all_users():
    c = _conn()
    rows = c.execute("SELECT DISTINCT user FROM attempts").fetchall()
    c.close()
    return [r[0] for r in rows]