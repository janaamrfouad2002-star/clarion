"""flashcards.py - auto-generated and manual flashcards with SM-2 scheduling."""
import sqlite3
import time

DB = "flashcards.db"


def _conn():
    c = sqlite3.connect(DB)
    c.execute("""
        CREATE TABLE IF NOT EXISTS cards(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            front TEXT,
            back TEXT,
            tag TEXT,
            source TEXT,
            ease REAL DEFAULT 2.5,
            interval_days REAL DEFAULT 0,
            reps INTEGER DEFAULT 0,
            next_review REAL DEFAULT 0,
            created REAL
        )
    """)
    c.commit()
    return c


def _auto_card(wrong_line: str, tag: str):
    tag_display = (tag or "UNKNOWN").replace("_", " ").title()
    front = f"What kind of mistake is this?\n{wrong_line}"
    back = (
        f"**{tag_display}**\n\n"
        f"The line `{wrong_line}` contains this error. "
        f"Rewrite the step correctly and check whether the answer changes."
    )
    return front, back


def generate_from_history(user: str) -> int:
    """Create flashcards from every distinct wrong attempt not already carded."""
    from app import history

    # Pull directly from the SQLite file, not via history.recent, so we
    # are immune to any argument or ordering change in that helper.
    raw_conn = sqlite3.connect("history.db")
    rows = raw_conn.execute(
        "SELECT kind, label, tag FROM attempts WHERE user=? AND kind='wrong'",
        (user,)
    ).fetchall()
    raw_conn.close()

    print(f"[flashcards] found {len(rows)} wrong attempts for {user}")

    c = _conn()
    existing = {r[0] for r in c.execute(
        "SELECT front FROM cards WHERE user=? AND source='auto'", (user,)
    ).fetchall()}

    added = 0
    for kind, label, tag in rows:
        if not label:
            continue
        front, back = _auto_card(label, tag or "")
        if front in existing:
            continue
        c.execute("""INSERT INTO cards(user, front, back, tag, source,
                                       ease, interval_days, reps, next_review, created)
                     VALUES(?,?,?,?,?,?,?,?,?,?)""",
                  (user, front, back, tag or "", "auto", 2.5, 0, 0, 0, time.time()))
        existing.add(front)
        added += 1
    c.commit()
    c.close()
    print(f"[flashcards] inserted {added} new cards")
    return added


def add_manual(user: str, front: str, back: str, tag: str = ""):
    c = _conn()
    c.execute("""INSERT INTO cards(user, front, back, tag, source,
                                   ease, interval_days, reps, next_review, created)
                 VALUES(?,?,?,?,?,?,?,?,?,?)""",
              (user, front.strip(), back.strip(), tag, "manual", 2.5, 0, 0, 0, time.time()))
    c.commit()
    c.close()


def due_cards(user: str, limit: int = 20):
    c = _conn()
    now = time.time()
    rows = c.execute(
        """SELECT id, front, back, tag FROM cards
           WHERE user=? AND next_review<=?
           ORDER BY next_review ASC LIMIT ?""",
        (user, now, limit)
    ).fetchall()
    c.close()
    return rows


def stats(user: str) -> dict:
    c = _conn()
    total = c.execute("SELECT COUNT(*) FROM cards WHERE user=?", (user,)).fetchone()[0]
    now = time.time()
    due = c.execute(
        "SELECT COUNT(*) FROM cards WHERE user=? AND next_review<=?", (user, now)
    ).fetchone()[0]
    learned = c.execute(
        "SELECT COUNT(*) FROM cards WHERE user=? AND reps>=3", (user,)
    ).fetchone()[0]
    c.close()
    return {"total": total, "due": due, "learned": learned}


def review(user: str, card_id: int, quality: int):
    c = _conn()
    row = c.execute(
        "SELECT ease, interval_days, reps FROM cards WHERE id=? AND user=?",
        (card_id, user)
    ).fetchone()
    if not row:
        c.close()
        return
    ease, interval, reps = row
    if quality <= 1:
        interval = 0.5
        reps = 0
    else:
        if reps == 0:
            interval = 1
        elif reps == 1:
            interval = 3
        else:
            interval = interval * ease
        reps += 1
        ease = max(1.3, ease + (0.1 - (3 - quality) * 0.08))
    next_review = time.time() + interval * 86400
    c.execute("""UPDATE cards SET ease=?, interval_days=?, reps=?, next_review=?
                 WHERE id=? AND user=?""",
              (ease, interval, reps, next_review, card_id, user))
    c.commit()
    c.close()


def delete_card(user: str, card_id: int):
    c = _conn()
    c.execute("DELETE FROM cards WHERE id=? AND user=?", (card_id, user))
    c.commit()
    c.close()