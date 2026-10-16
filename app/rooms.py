"""rooms.py - study rooms with a shared solution board."""
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
            code TEXT, user TEXT, joined REAL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS posts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT, user TEXT, body TEXT,
            votes INTEGER DEFAULT 0,
            created REAL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS votes(
            post_id INTEGER, voter TEXT,
            PRIMARY KEY (post_id, voter)
        )
    """)
    c.commit()
    return c


def _code():
    letters = string.ascii_uppercase + string.digits
    return "".join(random.choice(letters) for _ in range(6))


def create_room(topic, age_band, host):
    c = _conn()
    code = _code()
    c.execute("INSERT INTO rooms(code, topic, age_band, host, created) VALUES(?,?,?,?,?)",
              (code, topic, age_band, host, time.time()))
    c.execute("INSERT INTO members(code, user, joined) VALUES(?,?,?)",
              (code, host, time.time()))
    c.commit()
    c.close()
    return code


def join_room(code, user):
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


def members_of(code):
    c = _conn()
    rows = c.execute("SELECT user, joined FROM members WHERE code=? ORDER BY joined",
                     (code,)).fetchall()
    c.close()
    return rows


def my_rooms(user):
    c = _conn()
    rows = c.execute(
        """SELECT r.code, r.topic, r.age_band, r.host
           FROM rooms r JOIN members m ON m.code=r.code
           WHERE m.user=? ORDER BY r.created DESC""",
        (user,)
    ).fetchall()
    c.close()
    return rows


def leave_room(code, user):
    c = _conn()
    c.execute("DELETE FROM members WHERE code=? AND user=?", (code, user))
    c.commit()
    c.close()


# ---------- solution board ----------

def post_solution(code, user, body):
    c = _conn()
    c.execute("INSERT INTO posts(code, user, body, votes, created) VALUES(?,?,?,0,?)",
              (code, user, body.strip(), time.time()))
    c.commit()
    c.close()


def list_posts(code, limit=30):
    c = _conn()
    rows = c.execute(
        """SELECT id, user, body, votes, created FROM posts
           WHERE code=? ORDER BY votes DESC, created DESC LIMIT ?""",
        (code, limit)
    ).fetchall()
    c.close()
    return rows


def vote_post(post_id, voter):
    c = _conn()
    already = c.execute("SELECT 1 FROM votes WHERE post_id=? AND voter=?",
                        (post_id, voter)).fetchone()
    if already:
        c.close()
        return False
    c.execute("INSERT INTO votes(post_id, voter) VALUES(?,?)", (post_id, voter))
    c.execute("UPDATE posts SET votes = votes + 1 WHERE id=?", (post_id,))
    c.commit()
    c.close()
    return True


def delete_post(post_id, user):
    c = _conn()
    row = c.execute("SELECT user FROM posts WHERE id=?", (post_id,)).fetchone()
    if row and row[0] == user:
        c.execute("DELETE FROM posts WHERE id=?", (post_id,))
        c.commit()
        c.close()
        return True
    c.close()
    return False