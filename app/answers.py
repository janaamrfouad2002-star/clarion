"""answers.py - wrap general LLM answers with an unverified label."""

GENERAL_LABEL = "🌐 General answer (not verified by software)"


def general_answer(text, img, mime, lang):
    """Return a labelled general answer for anything outside our verified subjects."""
    from app.llm import answer_question
    body = answer_question(text, img, mime, lang) or ""
    if not body:
        body = "I couldn't reach the AI just now. Please try again."
    return f"**{GENERAL_LABEL}**\n\n{body}"