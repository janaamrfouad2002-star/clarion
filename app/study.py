"""study.py - research study infrastructure: participants, phases, logging."""
import sqlite3
import time
import uuid

DB = "study.db"


def _conn():
    c = sqlite3.connect(DB)
    c.execute("""
        CREATE TABLE IF NOT EXISTS participants(
            pid TEXT PRIMARY KEY,
            group_name TEXT,      -- 'tutor' or 'control'
            age INTEGER,
            grade TEXT,
            language TEXT,
            consent INTEGER,      -- 1 if consent form signed
            started REAL,
            finished REAL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pid TEXT,
            phase TEXT,           -- 'pretest' | 'learning' | 'posttest' | 'delayed'
            problem TEXT,
            student_answer TEXT,
            correct INTEGER,
            misconception TEXT,
            seconds REAL,
            created REAL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS surveys(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pid TEXT,
            kind TEXT,            -- 'sus' | 'interview'
            score REAL,
            notes TEXT,
            created REAL
        )
    """)
    c.commit()
    return c


def new_participant(group_name: str, age: int, grade: str, language: str) -> str:
    pid = uuid.uuid4().hex[:8]
    c = _conn()
    c.execute("""INSERT INTO participants(pid, group_name, age, grade, language,
                                          consent, started)
                 VALUES(?,?,?,?,?,?,?)""",
              (pid, group_name, age, grade, language, 1, time.time()))
    c.commit()
    c.close()
    return pid


def log(pid: str, phase: str, problem: str, student_answer: str,
        correct: bool, misconception: str = "", seconds: float = 0.0):
    c = _conn()
    c.execute("""INSERT INTO sessions(pid, phase, problem, student_answer,
                                      correct, misconception, seconds, created)
                 VALUES(?,?,?,?,?,?,?,?)""",
              (pid, phase, problem, student_answer, int(correct),
               misconception, seconds, time.time()))
    c.commit()
    c.close()


def log_survey(pid: str, kind: str, score: float, notes: str = ""):
    c = _conn()
    c.execute("""INSERT INTO surveys(pid, kind, score, notes, created)
                 VALUES(?,?,?,?,?)""",
              (pid, kind, score, notes, time.time()))
    c.commit()
    c.close()


def participant_summary(pid: str) -> dict:
    c = _conn()
    rows = c.execute(
        "SELECT phase, correct FROM sessions WHERE pid=? ORDER BY created",
        (pid,)
    ).fetchall()
    c.close()
    out = {"pretest": [0, 0], "posttest": [0, 0], "delayed": [0, 0],
           "learning": [0, 0]}
    for phase, correct in rows:
        if phase in out:
            out[phase][1] += 1
            out[phase][0] += correct
    return out


def all_participants():
    c = _conn()
    rows = c.execute("""SELECT pid, group_name, age, grade, language, started
                        FROM participants ORDER BY started""").fetchall()
    c.close()
    return rows


def all_sessions(pid: str = None):
    c = _conn()
    if pid:
        rows = c.execute("""SELECT phase, problem, student_answer, correct,
                                   misconception, seconds FROM sessions
                            WHERE pid=? ORDER BY created""", (pid,)).fetchall()
    else:
        rows = c.execute("""SELECT pid, phase, problem, student_answer, correct,
                                   misconception, seconds FROM sessions
                            ORDER BY created""").fetchall()
    c.close()
    return rows