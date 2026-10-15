"""presenter_ui.py - presenter bot with translate mode."""
import hashlib
import re

import streamlit as st

from app import presenter
from app.extras import detect_language
from app.avatar import render_presenter_avatar


LANG_WORDS = {
    "english": "English", "en": "English",
    "hindi": "Hindi", "हिन्दी": "Hindi", "हिंदी": "Hindi", "hi": "Hindi",
    "arabic": "Arabic", "العربية": "Arabic", "عربي": "Arabic", "ar": "Arabic",
    "french": "French", "français": "French", "francais": "French", "fr": "French",
}


def _init():
    ss = st.session_state
    ss.setdefault("presenter_chat", [])
    ss.setdefault("presenter_lang", "English")
    ss.setdefault("presenter_reply_lang", None)
    ss.setdefault("presenter_translate_mode", False)
    ss.setdefault("presenter_context", "")
    ss.setdefault("last_presenter_audio", None)
    ss.setdefault("last_presenter_reply", "")
    ss.setdefault("presenter_mp3", None)
    ss.setdefault("presenter_autoplay", False)
    ss.setdefault("presenter_mic_nonce", 0)


def _render_msg(m):
    with st.chat_message(m["role"]):
        if m.get("content"):
            st.markdown(m["content"])


def _say(role, content, speak_it=False):
    m = {"role": role, "content": content}
    st.session_state.presenter_chat.append(m)
    _render_msg(m)
    if speak_it and role == "assistant" and content:
        lang_now = (st.session_state.get("presenter_reply_lang")
                    or st.session_state.presenter_lang)
        mp3 = presenter.say(content, lang_now)
        st.session_state.presenter_mp3 = mp3
        st.session_state.presenter_autoplay = bool(mp3)
        st.session_state.last_presenter_reply = content


DISPLAY_TO_INTERNAL = {
    "English": "English",
    "हिन्दी": "Hindi",
    "العربية": "Arabic",
    "Français": "French",
}
INTERNAL_TO_DISPLAY = {v: k for k, v in DISPLAY_TO_INTERNAL.items()}


def _extract_lang_word(low: str):
    for word, name in LANG_WORDS.items():
        if re.search(rf"\b{re.escape(word)}\b", low):
            return name
    return None


def _maybe_handle_mode_command(text: str) -> bool:
    low = text.lower().strip()

    if any(p in low for p in [
        "translate everything", "translate what i", "translate what i'm",
        "translate what im", "translate whatever", "translate all i",
        "translate from now", "translate my"
    ]):
        target = _extract_lang_word(low) or "English"
        st.session_state.presenter_translate_mode = True
        st.session_state.presenter_reply_lang = target
        _say("assistant",
             f"Okay — from now on I'll answer in **{target}**. "
             f"Say 'back to English' to stop.")
        return True

    if any(p in low for p in ["reply in", "answer in", "respond in",
                               "speak in", "talk in"]):
        target = _extract_lang_word(low)
        if target:
            st.session_state.presenter_reply_lang = target
            st.session_state.presenter_lang = target
            _say("assistant", f"Got it — I'll reply in **{target}**.")
            return True

    if any(p in low for p in ["back to english", "stop translating",
                               "no more translate", "reply in english",
                               "answer in english"]):
        st.session_state.presenter_translate_mode = False
        st.session_state.presenter_reply_lang = "English"
        st.session_state.presenter_lang = "English"
        _say("assistant", "Back to English.")
        return True

    if "translate" in low:
        target = _extract_lang_word(low)
        if not target:
            _say("assistant", "Which language? Try: 'translate that into Hindi'.")
            return True
        last = st.session_state.get("last_presenter_reply")
        if not last:
            _say("assistant", "There's nothing to translate yet — ask me something first.")
            return True
        with st.spinner("Translating…"):
            out = presenter.translate(last, target)
        _say("assistant", f"**{target}:** {out}", speak_it=True)
        return True

    return False


def render():
    _init()
    ss = st.session_state

    st.subheader("🎤 Presenter bot")
    st.caption("Talk live during your demo — it answers, explains and translates.")

    display_names = list(DISPLAY_TO_INTERNAL.keys())
    current_display = INTERNAL_TO_DISPLAY.get(ss.presenter_lang, "English")

    top_left, top_right = st.columns([2, 1])
    with top_left:
        picked_display = st.selectbox(
            "🌐 Presenter language",
            display_names,
            index=display_names.index(current_display),
            key="presenter_lang_pick",
        )
        ss.presenter_lang = DISPLAY_TO_INTERNAL[picked_display]
    with top_right:
        st.write("")
        st.write("")
        if st.button("🔊 Test voice", use_container_width=True):
            test = {
                "English": "Hello! I can speak English.",
                "Hindi": "नमस्ते! मैं हिन्दी बोल सकती हूँ।",
                "Arabic": "مرحباً! أستطيع التحدث بالعربية.",
                "French": "Bonjour ! Je peux parler français.",
            }[ss.presenter_lang]
            _say("assistant", test, speak_it=True)
            st.rerun()

    reply_lang = ss.get("presenter_reply_lang") or ss.presenter_lang
    mode = "🌐 Translate-mode ON" if ss.get("presenter_translate_mode") else "🌐 Normal mode"
    st.caption(f"{mode} · replying in **{reply_lang}**")

    left, right = st.columns([1, 2])
    with left:
        render_presenter_avatar(audio_bytes=ss.presenter_mp3,
                                autoplay=ss.presenter_autoplay)
        ss.presenter_autoplay = False

    with right:
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("▶️ Start", use_container_width=True):
                _say("assistant", presenter.intro(ss.presenter_lang), speak_it=True)
                _say("assistant", presenter.demo_offer(ss.presenter_lang))
        with c2:
            if st.button("📜 Pitch", use_container_width=True):
                for title, body in presenter.beats(ss.presenter_lang):
                    _say("assistant", f"**{title}** — {body}")
        with c3:
            if st.button("🗑️ Clear", use_container_width=True):
                ss.presenter_chat = []
                ss.last_presenter_reply = ""
                ss.presenter_mp3 = None
                ss.presenter_translate_mode = False
                ss.presenter_reply_lang = None
                st.rerun()

        if ss.last_presenter_reply and st.button("🔊 Listen to last reply"):
            mp3 = presenter.say(ss.last_presenter_reply, reply_lang)
            if mp3:
                ss.presenter_mp3 = mp3
                ss.presenter_autoplay = True
                st.rerun()

    for m in ss.presenter_chat:
        _render_msg(m)

    # ---------- voice input: back to the simple st.audio_input ----------
    with st.expander("🎙️ Speak to the presenter", expanded=True):
        audio = st.audio_input(
            "Record your question",
            key=f"presenter_audio_{ss.presenter_mic_nonce}",
            label_visibility="collapsed",
        )
        if audio is not None:
            data = audio.getvalue()
            h = hashlib.md5(data).hexdigest()
            if ss.last_presenter_audio != h:
                ss.last_presenter_audio = h
                with st.spinner("Transcribing…"):
                    text, detected = presenter.listen(data, None)
                if not text:
                    st.warning("I couldn't hear that. Try again.")
                else:
                    ss.presenter_mic_nonce += 1
                    _handle_turn(text, detected, speak_it=True)
                    st.rerun()

    # ---------- typed input inside the presenter ----------
    text = st.chat_input("Ask the presenter, or say 'reply in Hindi'…",
                         key="presenter_input")
    if text:
        _handle_turn(text, None, speak_it=True)


def _handle_turn(text: str, detected_from_voice, speak_it: bool):
    ss = st.session_state

    if _maybe_handle_mode_command(text):
        return

    detected = detected_from_voice or detect_language(text)
    if detected:
        ss.presenter_lang = detected

    reply_lang = ss.get("presenter_reply_lang") or ss.presenter_lang

    _say("user", text)
    with st.spinner("Thinking…"):
        reply = presenter.respond(text, reply_lang, ss.get("presenter_context") or "")
    _say("assistant", reply, speak_it=speak_it)