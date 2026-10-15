"""teacher.py - aggregate views for a teacher / researcher."""
import sqlite3

from app.core import DB as LEARNER_DB


def _conn():
    return sqlite3.connect(LEARNER_DB)


def all_students():
    c = _conn()
    rows = c.execute("SELECT DISTINCT user FROM mistakes ORDER BY user").fetchall()
    c.close()
    return [r[0] for r in rows]


def class_heatmap():
    c = _conn()
    rows = c.execute("SELECT user, tag, errors FROM mistakes").fetchall()
    c.close()
    out = {}
    for user, tag, errors in rows:
        out.setdefault(user, {})[tag] = errors
    return out


def top_misconceptions(limit: int = 10):
    c = _conn()
    rows = c.execute("""
        SELECT tag, SUM(errors) as total, COUNT(DISTINCT user) as students
        FROM mistakes GROUP BY tag ORDER BY total DESC LIMIT ?
    """, (limit,)).fetchall()
    c.close()
    return rows


def students_at_risk(threshold: int = 3):
    c = _conn()
    rows = c.execute("""
        SELECT user, tag, errors, box FROM mistakes
        WHERE box = 0 AND errors >= ?
        ORDER BY errors DESC
    """, (threshold,)).fetchall()
    c.close()
    return rows