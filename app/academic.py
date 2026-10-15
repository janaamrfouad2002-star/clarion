"""academic.py - planner with priority, due dates, and daily reminders."""
import os
import smtplib
import sqlite3
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
    c.execute("""
        CREATE TABLE IF NOT EXISTS reminders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT, email TEXT, last_sent TEXT
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


def snooze_task(task_id: int):
    c = _conn()
    row = c.execute("SELECT due FROM tasks WHERE id=?", (task_id,)).fetchone()
    if row and row[0]:
        try:
            d = datetime.strptime(row[0], "%Y-%m-%d") + timedelta(days=1)
            c.execute("UPDATE tasks SET due=? WHERE id=?", (d.strftime("%Y-%m-%d"), task_id))
            c.commit()
        except Exception:
            pass
    c.close()


def _auto_priority(due: str, priority: str) -> str:
    if not due:
        return priority
    try:
        d = datetime.strptime(due, "%Y-%m-%d").date()
        days = (d - datetime.now().date()).days
        if days <= 2 and priority != "high":
            return "high"
    except Exception:
        pass
    return priority


def list_tasks(user: str, only_open: bool = False):
    c = _conn()
    q = """SELECT id, title, subject, due, priority, done FROM tasks WHERE user=?"""
    if only_open:
        q += " AND done=0"
    rows = c.execute(q, (user,)).fetchall()
    c.close()

    def sort_key(row):
        _id, _t, _s, due, pri, done = row
        pri_order = {"high": 0, "normal": 1, "low": 2}.get(pri, 1)
        try:
            due_val = datetime.strptime(due, "%Y-%m-%d").toordinal() if due else 999999
        except Exception:
            due_val = 999999
        return (done, pri_order, due_val)

    rows = [r[:4] + (_auto_priority(r[3], r[4]), r[5]) for r in rows]
    return sorted(rows, key=sort_key)


def due_label(due: str):
    if not due:
        return "", ""
    try:
        d = datetime.strptime(due, "%Y-%m-%d").date()
    except Exception:
        return due, ""
    delta = (d - datetime.now().date()).days
    if delta < 0:
        return f"overdue by {-delta}d", "overdue"
    if delta == 0:
        return "due today", "today"
    if delta == 1:
        return "due tomorrow", "soon"
    if delta <= 7:
        return f"due in {delta}d", "soon"
    return f"due {d.strftime('%b %d')}", ""


def stats(user: str):
    c = _conn()
    row = c.execute("SELECT COUNT(*), SUM(done) FROM tasks WHERE user=?", (user,)).fetchone()
    c.close()
    total = row[0] or 0
    done = row[1] or 0
    return total, done


def set_reminder_email(user: str, email: str):
    c = _conn()
    c.execute("DELETE FROM reminders WHERE user=?", (user,))
    c.execute("INSERT INTO reminders(user, email, last_sent) VALUES(?,?,?)",
              (user, email, ""))
    c.commit()
    c.close()


def get_reminder_email(user: str) -> str:
    c = _conn()
    row = c.execute("SELECT email FROM reminders WHERE user=?", (user,)).fetchone()
    c.close()
    return row[0] if row else ""


def _send_email(to_addr: str, subject: str, body: str) -> bool:
    user = os.getenv("REMINDER_EMAIL")
    pwd = os.getenv("REMINDER_APP_PASSWORD")
    if not (user and pwd and to_addr):
        return False
    try:
        msg = MIMEMultipart()
        msg["From"] = user
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(user, pwd)
            s.send_message(msg)
        return True
    except Exception as e:
        print("REMINDER ERROR:", e)
        return False


def send_daily_reminders() -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    c = _conn()
    reminders = c.execute("SELECT user, email, last_sent FROM reminders").fetchall()
    sent = 0
    for user, email, last_sent in reminders:
        if last_sent == today:
            continue
        tasks = list_tasks(user, only_open=True)
        due_today = [t for t in tasks if t[3] == today]
        overdue = []
        for t in tasks:
            if not t[3]:
                continue
            try:
                d = datetime.strptime(t[3], "%Y-%m-%d").date()
                if d < datetime.now().date():
                    overdue.append(t)
            except Exception:
                pass
        if not (due_today or overdue):
            continue
        body = "Your Lumen plan for today:\n\n"
        if overdue:
            body += "OVERDUE:\n" + "\n".join(f"  - {t[1]}" for t in overdue) + "\n\n"
        if due_today:
            body += "DUE TODAY:\n" + "\n".join(f"  - {t[1]}" for t in due_today) + "\n\n"
        body += "Good luck!"
        if _send_email(email, "Your study plan today", body):
            c.execute("UPDATE reminders SET last_sent=? WHERE user=?", (today, user))
            c.commit()
            sent += 1
    c.close()
    return sent


def generate_plan_from_syllabus(user: str, syllabus_text: str, days: int,
                                hours_per_day: float = 1.0) -> int:
    """Ask the LLM to divide the syllabus into daily tasks over `days` days."""
    from app.llm import _get_model, _text
    from langchain_core.messages import HumanMessage, SystemMessage
    import json
    from datetime import date, timedelta

    model = _get_model()
    if model is None:
        return 0

    sys = (
        "You are an academic planner. Read the syllabus the user provides. "
        "Produce a day-by-day study plan for the next {days} days, "
        "assuming about {h} hours of study per day. "
        "Return ONLY a JSON array. Each item must be: "
        '{{"day": 1, "title": "Short task title", "topic": "Topic name"}}. '
        "Each task should be specific and achievable in one sitting. "
        "No prose. No markdown fences. Just the JSON array."
    ).format(days=days, h=hours_per_day)
    try:
        raw = _text(model.invoke([
            SystemMessage(content=sys),
            HumanMessage(content=syllabus_text[:6000]),
        ])).strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            raw = raw[raw.find("["):raw.rfind("]") + 1]
        items = json.loads(raw)
    except Exception as e:
        print("PLAN GENERATION ERROR:", e)
        return 0

    today = date.today()
    added = 0
    for item in items:
        try:
            day_num = int(item.get("day", 1))
            title = str(item.get("title", "")).strip()
            topic = str(item.get("topic", "")).strip()
            if not title:
                continue
            due = (today + timedelta(days=day_num - 1)).strftime("%Y-%m-%d")
            add_task(user, title, topic, due, "normal")
            added += 1
        except Exception:
            continue
    return added