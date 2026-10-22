"""answers.py - wrap general LLM answers."""

def general_answer(text, img, mime, lang):
    """Return a general answer for anything outside our verified subjects."""
    from app.llm import answer_question
    body = answer_question(text, img, mime, lang) or ""
    if not body:
        body = "I couldn't reach the AI just now. Please try again."
    return body