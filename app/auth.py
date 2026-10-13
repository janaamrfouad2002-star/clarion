"""auth.py - simple local accounts. Passwords are salted and hashed, never stored as text."""
import hashlib
import hmac
import os
import re
import sqlite3
import time

DB = "users.db"
ITERATIONS = 200_000


def _conn():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        username TEXT PRIMARY KEY, salt BLOB, hash BLOB, created REAL)""")
    return c


def _hash(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)


def valid_username(username: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_.-]{3,30}", username or ""))


def create_user(username: str, password: str) -> str:
    """Returns 'ok', 'bad_user', 'short_pw' or 'taken'."""
    username = (username or "").strip()
    if not valid_username(username):
        return "bad_user"
    if len(password or "") < 6:
        return "short_pw"
    salt = os.urandom(16)
    c = _conn()
    try:
        c.execute("INSERT INTO users VALUES(?,?,?,?)",
                  (username.lower(), salt, _hash(password, salt), time.time()))
        c.commit()
    except sqlite3.IntegrityError:
        return "taken"
    finally:
        c.close()
    return "ok"


def verify(username: str, password: str) -> bool:
    username = (username or "").strip().lower()
    c = _conn()
    row = c.execute("SELECT salt, hash FROM users WHERE username=?", (username,)).fetchone()
    c.close()
    salt, stored = row if row else (b"\x00" * 16, b"")
    attempt = _hash(password or "", salt)          # same work whether or not the user exists
    return bool(row) and hmac.compare_digest(attempt, stored)