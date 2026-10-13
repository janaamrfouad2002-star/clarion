"""chat_input_bar.py - a single-row composer with mic, photo, and text."""
import hashlib

import streamlit as st


def composer(placeholder: str, user_key: str = "composer"):
    """Returns (text, image_bytes, image_mime, sent)."""
    ss = st.session_state
    ss.setdefault(f"{user_key}_mic_nonce", 0)

    # Outer container styled like a rounded bar
    cols = st.columns([0.6, 0.6, 8, 1.2])

    # Left: photo button
    with cols[0]:
        st.markdown("<div style='padding-top:8px'></div>", unsafe_allow_html=True)
        upload = st.file_uploader(
            "photo", type=["png", "jpg", "jpeg"],
            key=f"{user_key}_photo",
            label_visibility="collapsed",
        )

    # Left: mic (audio_input inside a compact container)
    with cols[1]:
        st.markdown("<div style='padding-top:8px'></div>", unsafe_allow_html=True)
        audio = st.audio_input("mic", key=f"{user_key}_mic_{ss[f'{user_key}_mic_nonce']}",
                               label_visibility="collapsed")

    # Middle: text
    with cols[2]:
        text = st.text_input(placeholder, key=f"{user_key}_text",
                             label_visibility="collapsed")

    # Right: send button
    with cols[3]:
        st.markdown("<div style='padding-top:8px'></div>", unsafe_allow_html=True)
        send = st.button("➤", key=f"{user_key}_send", use_container_width=True)

    img, mime = None, "image/png"
    if upload is not None:
        img = upload.getvalue()
        mime = upload.type

    # Voice
    voice_text = None
    if audio is not None:
        data = audio.getvalue()
        h = hashlib.md5(data).hexdigest()
        if ss.get(f"{user_key}_last_audio") != h:
            ss[f"{user_key}_last_audio"] = h
            from app.extras import transcribe
            with st.spinner("Transcribing…"):
                vt, _vl = transcribe(data, None)
            ss[f"{user_key}_mic_nonce"] += 1
            voice_text = vt

    # Prefer voice, fall back to typed
    final_text = voice_text or text or ""
    sent = send and (final_text or img is not None)
    return final_text, img, mime, sent