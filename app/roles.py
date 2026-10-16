"""roles.py - simple role management for Lumen."""
import os
import sqlite3

DB = "roles.db"


def _conn():
    c = sqlite3.connect(DB)
    c.execute("""
        CREATE TABLE IF NOT EXISTS roles(
            user TEXT PRIMARY KEY,
            role TEXT DEFAULT 'student'
        )
    """)
    c.commit()
    return c


def get_role(user: str) -> str:
    c = _conn()
    row = c.execute("SELECT role FROM roles WHERE user=?", (user,)).fetchone()
    c.close()
    return row[0] if row else "student"


def set_role(user: str, role: str):
    c = _conn()
    c.execute("INSERT OR REPLACE INTO roles(user, role) VALUES(?,?)", (user, role))
    c.commit()
    c.close()


def try_promote(user: str, code: str) -> bool:
    """If the code matches TEACHER_CODE, promote the user to teacher."""
    expected = os.getenv("TEACHER_CODE", "")
    if not expected or code.strip() != expected:
        return False
    set_role(user, "teacher")
    return True