"""academic.py - a simple academic planner stored in SQLite."""
import sqlite3
import time

DB = "planner.db"


def _conn():
    c = sqlite3.connect(DB)
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT, title TEXT, subject TEXT,
            due TEXT, priority TEXT, done INTEGER DEFAULT 0,
            created REAL
        )
    """)
    return c


def add_task(user: str, title: str, subject: str = "", due: str = "",
             priority: str = "normal"):
    c = _conn()
    c.execute("""INSERT INTO tasks(user, title, subject, due, priority, created)
                 VALUES(?,?,?,?,?,?)""",
              (user, title, subject, due, priority, time.time()))
    c.commit()
    c.close()


def list_tasks(user: str, only_open: bool = True):
    c = _conn()
    q = "SELECT id, title, subject, due, priority, done FROM tasks WHERE user=?"
    if only_open:
        q += " AND done=0"
    q += " ORDER BY done, created DESC"
    rows = c.execute(q, (user,)).fetchall()
    c.close()
    return rows


def toggle_task(task_id: int):
    c = _conn()
    c.execute("UPDATE tasks SET done = 1 - done WHERE id=?", (task_id,))
    c.commit()
    c.close()


def delete_task(task_id: int):
    c = _conn()
    c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    c.commit()
    c.close()


def stats(user: str):
    c = _conn()
    row = c.execute(
        "SELECT COUNT(*), SUM(done) FROM tasks WHERE user=?", (user,)
    ).fetchone()
    c.close()
    total = row[0] or 0
    done = row[1] or 0
    return total, done