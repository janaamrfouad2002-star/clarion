"""rooms.py - lightweight study rooms grouped by topic and age band."""
import random
import sqlite3
import string
import time

DB = "rooms.db"


def _conn():
    c = sqlite3.connect(DB)
    c.execute("""
        CREATE TABLE IF NOT EXISTS rooms(
            code TEXT PRIMARY KEY,
            topic TEXT,
            age_band TEXT,
            host TEXT,
            created REAL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS members(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            user TEXT,
            joined REAL
        )
    """)
    c.commit()
    return c


def _code():
    letters = string.ascii_uppercase + string.digits
    return "".join(random.choice(letters) for _ in range(6))


def create_room(topic: str, age_band: str, host: str) -> str:
    c = _conn()
    code = _code()
    c.execute("INSERT INTO rooms(code, topic, age_band, host, created) VALUES(?,?,?,?,?)",
              (code, topic, age_band, host, time.time()))
    c.execute("INSERT INTO members(code, user, joined) VALUES(?,?,?)",
              (code, host, time.time()))
    c.commit()
    c.close()
    return code


def join_room(code: str, user: str) -> bool:
    code = code.strip().upper()
    c = _conn()
    exists = c.execute("SELECT 1 FROM rooms WHERE code=?", (code,)).fetchone()
    if not exists:
        c.close()
        return False
    already = c.execute("SELECT 1 FROM members WHERE code=? AND user=?",
                        (code, user)).fetchone()
    if not already:
        c.execute("INSERT INTO members(code, user, joined) VALUES(?,?,?)",
                  (code, user, time.time()))
        c.commit()
    c.close()
    return True


def list_rooms():
    c = _conn()
    rows = c.execute(
        """SELECT r.code, r.topic, r.age_band, r.host, COUNT(m.id)
           FROM rooms r LEFT JOIN members m ON m.code=r.code
           GROUP BY r.code ORDER BY r.created DESC LIMIT 30"""
    ).fetchall()
    c.close()
    return rows


def members_of(code: str):
    c = _conn()
    rows = c.execute("SELECT user, joined FROM members WHERE code=? ORDER BY joined",
                     (code,)).fetchall()
    c.close()
    return rows


def my_rooms(user: str):
    c = _conn()
    rows = c.execute(
        """SELECT r.code, r.topic, r.age_band, r.host
           FROM rooms r JOIN members m ON m.code=r.code
           WHERE m.user=? ORDER BY r.created DESC""",
        (user,)
    ).fetchall()
    c.close()
    return rows


def leave_room(code: str, user: str):
    c = _conn()
    c.execute("DELETE FROM members WHERE code=? AND user=?", (code, user))
    c.commit()
    c.close()