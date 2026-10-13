import hashlib
import html
import secrets
import time

import pandas as pd
import streamlit as st

from app import academic, auth
from app.core import record, due, mistake_map
from app.engine import analyse, make_twin, check_twin
from app.extras import (LANGS, AUTO, CODE, T, GESTURE_REPLY, detect_language,
                        normalize_digits, transcribe, speak)
from app.llm import (extract, explain_with_llm, explain_solution, answer_question,
                     simplify, translate_text)
from app.presenter_ui import render as render_presenter

st.set_page_config(page_title="Mistake-to-Mastery", page_icon="🎓",
                   layout="wide", initial_sidebar_state="expanded")

# ============================================================
# STYLE
# ============================================================
st.markdown("""
<style>
:root { --brand:#6366f1; --brand2:#a855f7; --ink:#0f172a; --muted:#64748b;
        --line:#e5e7eb; --ok:#10b981; --bad:#ef4444; }
html, body, [class*="css"] { font-family: Inter,-apple-system,"Segoe UI",Roboto,sans-serif; }
.stApp { background:
   radial-gradient(900px 500px at 8% -5%, #e0e7ff 0%, transparent 60%),
   radial-gradient(800px 500px at 100% 10%, #fae8ff 0%, transparent 55%), #f8fafc; }
.block-container { padding-top: 1rem !important; padding-bottom: 7rem !important; max-width: 1150px; }
header[data-testid="stHeader"] { background: transparent; }

.hero { border-radius: 22px; padding: 22px 28px; margin-bottom: 16px; color:#fff;
  background: linear-gradient(-45deg,#6366f1,#a855f7,#ec4899,#6366f1); background-size:300% 300%;
  animation: shift 14s ease infinite; box-shadow: 0 24px 50px -28px rgba(99,102,241,.7); }
.hero h1 { margin:0 0 4px; font-size:1.8rem; font-weight:800; letter-spacing:-.02em; }
.hero p { margin:0; opacity:.95; }
.chips { margin-top:12px; display:flex; flex-wrap:wrap; gap:8px; }
.chip { background:rgba(255,255,255,.18); border:1px solid rgba(255,255,255,.4);
  padding:3px 12px; border-radius:999px; font-size:.78rem; }
@keyframes shift { 0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%} }

[data-testid="stSidebar"] { background: linear-gradient(180deg,#f5f6ff,#fff); border-right:1px solid var(--line); }
.usercard { display:flex; gap:10px; align-items:center; padding:10px; border-radius:14px;
  background:#fff; border:1px solid var(--line); margin-bottom:10px; }
.avatar { width:38px; height:38px; border-radius:50%; display:flex; align-items:center;
  justify-content:center; color:#fff; font-weight:800;
  background:linear-gradient(135deg,var(--brand),var(--brand2)); }
.sec { font-weight:800; font-size:.98rem; margin:12px 0 8px; display:flex; gap:8px; align-items:center; }
.sec::before { content:""; width:5px; height:16px; border-radius:3px;
  background: linear-gradient(180deg,var(--brand),var(--brand2)); }

.stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:10px; margin-bottom:14px; }
.stat { background:#fff; border:1px solid var(--line); border-radius:14px; padding:14px 6px; text-align:center; }
.stat b { display:block; font-size:1.6rem; }
.stat span { font-size:.78rem; color:var(--muted); }
.stat.ok b { color:var(--ok); } .stat.bad b { color:var(--bad); } .stat.mid b { color:var(--brand); }
.ring { display:flex; align-items:center; gap:12px; padding:8px 10px; margin-bottom:8px;
  background:#fff; border:1px solid var(--line); border-radius:14px; }
.ring svg { width:46px; height:46px; flex-shrink:0; }
.ring circle { fill:none; stroke-width:5; transform:rotate(-90deg); transform-origin:50% 50%; }
.ring .bg { stroke:#e5e7eb; } .ring .fg { stroke:url(#g); stroke-linecap:round; }
.ring .lbl { color:var(--muted); font-size:.78rem; }
.act { display:flex; gap:8px; align-items:flex-start; padding:8px 10px; border-radius:12px;
  background:#fff; border:1px solid var(--line); margin-bottom:6px; font-size:.88rem; }
.act small { color:var(--muted); display:block; }
.task { padding:10px 12px; border-radius:12px; background:#fff; border:1px solid var(--line);
  border-left:4px solid var(--brand); margin-bottom:4px; font-weight:600; }
.task.high { border-left-color:var(--bad); } .task.low { border-left-color:var(--ok); }
.task.done .tt { text-decoration:line-through; opacity:.5; }
.task small { color:var(--muted); font-weight:400; display:block; }
.card { background:#fff; border:1px solid var(--line); border-radius:16px; padding:16px 18px; }

div.stButton > button { border-radius:10px; border:1px solid var(--line); background:#fff;
  font-weight:600; transition:all .15s ease; }
div.stButton > button:hover { border-color:var(--brand); color:var(--brand); transform:translateY(-1px); }
div.stButton > button[kind="primary"], div.stFormSubmitButton > button[kind="primary"] {
  background:linear-gradient(90deg,var(--brand),var(--brand2)); color:#fff; border:none; }

[data-testid="stChatMessage"] { border-radius:16px; border:1px solid var(--line); background:#fff;
  padding:10px 14px; margin-bottom:8px; box-shadow:0 4px 14px -12px rgba(15,23,42,.2); }
[data-testid="stChatInput"] { border-radius:20px !important; border:1px solid #c7d2fe !important;
  background:#fff !important; box-shadow:0 14px 34px -16px rgba(99,102,241,.6); }
[data-testid="stBottom"] > div { background:transparent !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# TEXT: navigation, pages and login in 4 languages
# ============================================================
S = {
    "English": dict(
        learn="Learn", present="Present", tracking="My progress", planner="Academic planner",
        gestures="Live gestures", right="Right", wrong="Wrong", mastered="Mastered",
        accuracy="Accuracy", recent="Recent activity",
        no_activity="Nothing yet. Ask your first question!",
        add_task="Add a task", task="Task", subject="Subject (optional)",
        due="Due date (optional)", priority="Priority", add="Add", done="Done", undo="Undo",
        no_tasks="No tasks yet.", of_done="done",
        present_sub="Talk live during your demo. It answers, explains and translates.",
        gesture_help="Allow the camera, then show 👍 👎 ☝️ or ✋.",
        chat_hint="Ask below any time. Your answer opens in Learn.",
        g_up="👍 Got it", g_down="👎 Explain it simpler", g_point="☝️ I have a question",
        g_palm="✋ Please wait", no_mistakes="No mistakes recorded yet."),
    "Hindi": dict(
        learn="सीखें", present="प्रस्तुति", tracking="मेरी प्रगति", planner="अकादमिक योजना",
        gestures="लाइव इशारे", right="सही", wrong="गलत", mastered="सीख लिया",
        accuracy="सटीकता", recent="हाल की गतिविधि",
        no_activity="अभी कुछ नहीं। अपना पहला सवाल पूछें!",
        add_task="कार्य जोड़ें", task="कार्य", subject="विषय (वैकल्पिक)",
        due="अंतिम तिथि (वैकल्पिक)", priority="प्राथमिकता", add="जोड़ें", done="पूरा", undo="वापस",
        no_tasks="अभी कोई कार्य नहीं।", of_done="पूरे",
        present_sub="डेमो के दौरान लाइव बोलें। यह जवाब देता, समझाता और अनुवाद करता है।",
        gesture_help="कैमरा चालू करें, फिर 👍 👎 ☝️ या ✋ दिखाएँ।",
        chat_hint="कभी भी नीचे पूछें। जवाब 'सीखें' पेज पर खुलेगा।",
        g_up="👍 समझ गया", g_down="👎 और आसान समझाओ", g_point="☝️ मेरा एक सवाल है",
        g_palm="✋ रुकिए", no_mistakes="अभी कोई गलती दर्ज नहीं।"),
    "Arabic": dict(
        learn="تعلّم", present="عرض", tracking="تقدّمي", planner="المخطط الدراسي",
        gestures="إيماءات مباشرة", right="صحيح", wrong="خطأ", mastered="أتقنتها",
        accuracy="الدقة", recent="النشاط الأخير",
        no_activity="لا شيء بعد. اطرح سؤالك الأول!",
        add_task="أضف مهمة", task="المهمة", subject="المادة (اختياري)",
        due="تاريخ التسليم (اختياري)", priority="الأولوية", add="إضافة", done="تم", undo="تراجع",
        no_tasks="لا توجد مهام بعد.", of_done="منجزة",
        present_sub="تحدّث مباشرة أثناء العرض. يجيب ويشرح ويترجم.",
        gesture_help="اسمح بالكاميرا ثم أظهر 👍 👎 ☝️ أو ✋.",
        chat_hint="اسأل في الأسفل في أي وقت. ستظهر الإجابة في صفحة «تعلّم».",
        g_up="👍 فهمت", g_down="👎 اشرح بشكل أبسط", g_point="☝️ لدي سؤال",
        g_palm="✋ انتظر من فضلك", no_mistakes="لا توجد أخطاء مسجلة بعد."),
    "French": dict(
        learn="Apprendre", present="Présenter", tracking="Ma progression", planner="Planificateur",
        gestures="Gestes en direct", right="Justes", wrong="Fausses", mastered="Maîtrisées",
        accuracy="Précision", recent="Activité récente",
        no_activity="Rien pour le moment. Posez votre première question !",
        add_task="Ajouter une tâche", task="Tâche", subject="Matière (facultatif)",
        due="Échéance (facultatif)", priority="Priorité", add="Ajouter", done="Fait", undo="Annuler",
        no_tasks="Aucune tâche.", of_done="terminées",
        present_sub="Parlez en direct pendant votre démo. Il répond, explique et traduit.",
        gesture_help="Autorisez la caméra, puis montrez 👍 👎 ☝️ ou ✋.",
        chat_hint="Posez votre question en bas à tout moment. La réponse s'ouvre dans Apprendre.",
        g_up="👍 Compris", g_down="👎 Expliquez plus simplement", g_point="☝️ J'ai une question",
        g_palm="✋ Attendez s'il vous plaît", no_mistakes="Aucune erreur enregistrée."),
}

LG = {
    "English": dict(
        login="Log in", signup="Create account", username="Username", password="Password",
        confirm="Confirm password", login_btn="Log in", signup_btn="Create account",
        guest="Continue as guest", bad_login="Wrong username or password.",
        locked="Too many tries. Please wait {n} seconds.",
        created="Account created! Logging you in…",
        bad_user="Username: 3 to 30 letters, numbers, . _ or -",
        short_pw="Password must be at least 6 characters.", taken="That username is taken.",
        mismatch="Passwords don't match.", logout="Log out",
        guest_note="Guest progress is not saved to an account.", hello="Hello"),
    "Hindi": dict(
        login="लॉग इन", signup="खाता बनाएँ", username="उपयोगकर्ता नाम", password="पासवर्ड",
        confirm="पासवर्ड दोबारा लिखें", login_btn="लॉग इन", signup_btn="खाता बनाएँ",
        guest="अतिथि के रूप में जारी रखें", bad_login="उपयोगकर्ता नाम या पासवर्ड गलत है।",
        locked="बहुत ज़्यादा कोशिशें। कृपया {n} सेकंड रुकें।",
        created="खाता बन गया! लॉग इन हो रहा है…",
        bad_user="उपयोगकर्ता नाम: 3 से 30 अक्षर, अंक, . _ या -",
        short_pw="पासवर्ड कम से कम 6 अक्षरों का होना चाहिए।",
        taken="यह उपयोगकर्ता नाम पहले से लिया जा चुका है।",
        mismatch="पासवर्ड मेल नहीं खाते।", logout="लॉग आउट",
        guest_note="अतिथि की प्रगति किसी खाते में सहेजी नहीं जाती।", hello="नमस्ते"),
    "Arabic": dict(
        login="تسجيل الدخول", signup="إنشاء حساب", username="اسم المستخدم",
        password="كلمة المرور", confirm="تأكيد كلمة المرور", login_btn="دخول",
        signup_btn="إنشاء الحساب", guest="المتابعة كضيف",
        bad_login="اسم المستخدم أو كلمة المرور غير صحيحة.",
        locked="محاولات كثيرة. انتظر {n} ثانية.",
        created="تم إنشاء الحساب! جارٍ تسجيل الدخول…",
        bad_user="اسم المستخدم: من 3 إلى 30 حرفاً أو رقماً أو . _ أو -",
        short_pw="يجب ألا تقل كلمة المرور عن 6 أحرف.", taken="اسم المستخدم مستخدم بالفعل.",
        mismatch="كلمتا المرور غير متطابقتين.", logout="تسجيل الخروج",
        guest_note="تقدّم الضيف لا يُحفظ في حساب.", hello="مرحباً"),
    "French": dict(
        login="Connexion", signup="Créer un compte", username="Nom d'utilisateur",
        password="Mot de passe", confirm="Confirmer le mot de passe", login_btn="Se connecter",
        signup_btn="Créer le compte", guest="Continuer en invité",
        bad_login="Nom d'utilisateur ou mot de passe incorrect.",
        locked="Trop d'essais. Patientez {n} secondes.",
        created="Compte créé ! Connexion…",
        bad_user="Nom d'utilisateur : 3 à 30 lettres, chiffres, . _ ou -",
        short_pw="Le mot de passe doit contenir au moins 6 caractères.",
        taken="Ce nom d'utilisateur est déjà pris.",
        mismatch="Les mots de passe ne correspondent pas.", logout="Se déconnecter",
        guest_note="La progression d'un invité n'est pas enregistrée dans un compte.",
        hello="Bonjour"),
}

# ============================================================
# STATE AND SMALL HELPERS
# ============================================================
ss = st.session_state
ss.setdefault("chat", [])
ss.setdefault("ui_lang", "English")
ss.setdefault("lang_pref", AUTO)
ss.setdefault("page", "learn")
ss.setdefault("history", {})
ss.setdefault("user", None)
ss.setdefault("fails", 0)
ss.setdefault("locked_until", 0.0)

LANG_OPTIONS = [AUTO] + list(LANGS)


def L():
    name = ss.ui_lang
    return name, T[name], S[name], LG[name]


def friendly(tag: str) -> str:
    base = tag.replace("_", " ").capitalize()
    if ss.ui_lang == "English":
        return base
    return translate_text(base, ss.ui_lang)


def hero(title, subtitle, chips=()):
    chip_html = "".join(f'<span class="chip">{c}</span>' for c in chips)
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p>'
                f'<div class="chips">{chip_html}</div></div>', unsafe_allow_html=True)


def lang_picker(key: str):
    cur = ss.lang_pref
    ch = st.selectbox("🌐 Language / भाषा / اللغة / Langue", LANG_OPTIONS,
                      index=LANG_OPTIONS.index(cur), key=key)
    if ch != cur:
        ss.lang_pref = ch
        if ch != AUTO:
            ss.ui_lang = LANGS[ch][0]
        st.rerun()


if ss.ui_lang == "Arabic":
    st.markdown("<style>[data-testid='stChatMessage']{direction:rtl;text-align:right}</style>",
                unsafe_allow_html=True)


# ============================================================
# LOGIN PAGE
# ============================================================
def login_page():
    lang, t, s, lg = L()
    st.markdown("<style>[data-testid='stSidebar'],[data-testid='stSidebarCollapsedControl'],"
                "[data-testid='collapsedControl']{display:none}</style>", unsafe_allow_html=True)
    hero("🎓 Mistake-to-Mastery", t["tagline"],
         ["🧠 Verified mistakes", "🗣️ 4 languages", "🎥 Gestures", "🎤 Voice", "📅 Planner"])
    _, mid, _ = st.columns([1, 1.6, 1])
    with mid:
        lang_picker("lp_login")
        tab_in, tab_up = st.tabs([lg["login"], lg["signup"]])
        with tab_in:
            with st.form("login_form"):
                u = st.text_input(lg["username"])
                p = st.text_input(lg["password"], type="password")
                go = st.form_submit_button(lg["login_btn"], type="primary",
                                          use_container_width=True)
            if go:
                now = time.time()
                if now < ss.locked_until:
                    st.error(lg["locked"].format(n=int(ss.locked_until - now) + 1))
                elif auth.verify(u, p):
                    ss.fails = 0
                    ss.user = u.strip().lower()
                    ss.page = "learn"
                    st.rerun()
                else:
                    ss.fails += 1
                    if ss.fails >= 5:
                        ss.locked_until = now + 30
                        ss.fails = 0
                    st.error(lg["bad_login"])
        with tab_up:
            with st.form("signup_form"):
                u2 = st.text_input(lg["username"], key="su_user")
                p2 = st.text_input(lg["password"], type="password", key="su_pw")
                p3 = st.text_input(lg["confirm"], type="password", key="su_pw2")
                go2 = st.form_submit_button(lg["signup_btn"], type="primary",
                                            use_container_width=True)
            if go2:
                if p2 != p3:
                    st.error(lg["mismatch"])
                else:
                    code = auth.create_user(u2, p2)
                    if code == "ok":
                        st.success(lg["created"])
                        ss.user = u2.strip().lower()
                        ss.page = "learn"
                        st.rerun()
                    else:
                        st.error(lg[code])
        st.caption(lg["guest_note"])
        if st.button(lg["guest"], use_container_width=True):
            ss.user = "guest-" + secrets.token_hex(2)
            ss.page = "learn"
            st.rerun()


if not ss.user:
    login_page()
    st.stop()

user = ss.user
lang, t, s, lg = L()

# ============================================================
# SIDEBAR: account, language and navigation only
# ============================================================
with st.sidebar:
    st.markdown(
        f'<div class="usercard"><div class="avatar">{html.escape(user[0].upper())}</div>'
        f'<div><b>{lg["hello"]}, {html.escape(user)}</b></div></div>',
        unsafe_allow_html=True)
    lang_picker("lp_side")
    st.markdown("---")
    PAGES = [("learn", "💬", s["learn"]), ("progress", "📊", s["tracking"]),
             ("gestures", "🎥", s["gestures"]), ("planner", "📅", s["planner"]),
             ("present", "🎤", s["present"])]
    for key, icon, label in PAGES:
        kind = "primary" if ss.page == key else "secondary"
        if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True, type=kind):
            ss.page = key
            st.rerun()
    st.markdown("---")
    if user.startswith("guest-"):
        st.caption(lg["guest_note"])
    if st.button("🚪 " + lg["logout"], use_container_width=True, key="logout"):
        for k in ("user", "chat", "twin", "inbox", "last_gesture"):
            ss.pop(k, None)
        ss.page = "learn"
        st.rerun()

# ============================================================
# CHAT BAR: pinned at the bottom on every page
# ============================================================
AUDIO_IN_BAR = True
try:
    prompt = st.chat_input(t["placeholder"], accept_file=True,
                           file_type=["png", "jpg", "jpeg"], accept_audio=True)
except TypeError:                      # older Streamlit: no mic inside the chat bar
    AUDIO_IN_BAR = False
    prompt = st.chat_input(t["placeholder"], accept_file=True,
                           file_type=["png", "jpg", "jpeg"])

if prompt:
    files = getattr(prompt, "files", None) or []
    aud = getattr(prompt, "audio", None)
    typed = prompt.text or ""
    has_audio = aud is not None and not typed
    ss["inbox"] = {
        "text": typed,
        "img": files[0].getvalue() if files else None,
        "mime": files[0].type if files else "image/png",
        "audio": aud.getvalue() if has_audio else None,
    }
    if ss.page != "learn":              # answers always appear in the Learn page
        ss.page = "learn"
        st.rerun()


# ============================================================
# SHARED CHAT FUNCTIONS
# ============================================================
def log(kind, label, tag=""):
    entry = {"k": kind, "label": (label or "").replace("\n", " ")[:70], "tag": tag}
    ss.history.setdefault(user, []).append(entry)


def render(m):
    if m["role"] == "read":
        with st.expander(T[ss.ui_lang]["read"]):
            st.json(m["content"])
    else:
        with st.chat_message(m["role"]):
            if m.get("content"):
                st.markdown(m["content"])
            if m.get("img"):
                st.image(m["img"], width=300)


def say(role, content, img=None):
    m = {"role": role, "content": content, "img": img}
    ss.chat.append(m)
    render(m)


def apply_gesture(name: str):
    """Adds the reply to the chat history and returns it as text."""
    lang_, t_, _, _ = L()
    if name == "Thumb_Down":
        last = next((m["content"] for m in reversed(ss.chat)
                     if m["role"] == "assistant" and m.get("content")), None)
        with st.spinner("..."):
            reply = simplify(last, lang_) if last else None
        reply = reply or t_["sorry"]
    else:
        reply = GESTURE_REPLY[lang_].get(name)
    if reply:
        ss.chat.append({"role": "assistant", "content": reply, "img": None})
        ss["last_gesture"] = (name, reply)
    return reply


# ============================================================
# PAGE: LEARN (chat)
# ============================================================
def page_learn():
    lang_, t_, s_, lg_ = L()
    hero("🎓 Mistake-to-Mastery", t_["tagline"],
         ["🧠 Verified mistakes", "🗣️ 4 languages", "🎥 Gestures", "🎤 Voice", "📅 Planner"])
    if ss.chat and st.button("🗑️ " + t_["clear"], key="clear_chat"):
        ss.chat = []
        ss.pop("twin", None)
        st.rerun()

    fallback_audio = None
    if not AUDIO_IN_BAR:
        with st.expander("🎤 " + t_["mic"]):
            fb = st.audio_input(t_["mic"], label_visibility="collapsed")
        if fb is not None:
            h = hashlib.md5(fb.getvalue()).hexdigest()
            if ss.get("fb_audio") != h:
                ss["fb_audio"] = h
                fallback_audio = fb.getvalue()

    chat_box = st.container()
    with chat_box:
        for m in ss.chat:
            render(m)

        welcome = st.empty()
        if not ss.chat:
            with welcome.container():
                st.markdown(f'<div class="card">{t_["welcome"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="sec">{t_["try"]}</div>', unsafe_allow_html=True)
                cols = st.columns(2)
                for i, example in enumerate(t_["examples"]):
                    if cols[i % 2].button(example.replace("\n", " / "), key=f"ex{i}",
                                          use_container_width=True):
                        ss["queued"] = example

        inbox = ss.pop("inbox", None) or {}
        text = inbox.get("text", "")
        img = inbox.get("img")
        mime = inbox.get("mime", "image/png")
        audio_bytes = inbox.get("audio") or fallback_audio
        queued = ss.pop("queued", None)
        if queued and not text:
            text = queued

        from_voice, voice_lang = False, None
        if audio_bytes and not text:
            code = None if ss.lang_pref == AUTO else CODE[ss.ui_lang]
            with st.spinner("🎤 ..."):
                vt, voice_lang = transcribe(audio_bytes, code)
            if vt:
                text, from_voice = vt, True
            else:
                st.warning(t_["cant_hear"])

        if text or img:
            welcome.empty()
            text = normalize_digits(text)
            start_lang = ss.ui_lang
            if ss.lang_pref == AUTO:
                if from_voice and voice_lang:
                    detected = voice_lang
                else:
                    detected = detect_language(text)
                if detected:
                    ss.ui_lang = detected
            lang_, t_, s_, lg_ = L()

            say("user", ("🎤 " if from_voice else "") + (text or "📷"), img)
            with st.spinner("..."):
                ex = extract(text, img, mime)
            ss.chat.append({"role": "read", "content": ex.model_dump()})
            render(ss.chat[-1])

            try:
                result = analyse(ex)
            except Exception as e:
                print("ANALYSE ERROR:", repr(e), ex.model_dump())
                result = None
                say("assistant", t_["cant_read"])

            if result:
                status = result["status"]
                if status == "correct":
                    say("assistant", "✅ " + t_["correct"])
                    log("right", text or "📷")
                elif status == "solved":
                    with st.spinner("..."):
                        reply = explain_solution(result["question"], result["answer"],
                                                 lang_, t_["answer"])
                    say("assistant", reply)
                    log("asked", result["question"])
                elif status == "unsupported":
                    with st.spinner("..."):
                        reply = answer_question(text, img, mime, lang_) or t_["sorry"]
                    say("assistant", reply)
                    log("asked", text or "📷")
                else:
                    with st.spinner("..."):
                        hint = explain_with_llm(result["prev"], result["wrong"],
                                                result["tag"], lang_) or ""
                    say("assistant",
                        f"**{t_['mistake']}:** `{friendly(result['tag'])}`\n\n"
                        f"{t_['your_line']}: `{result['wrong']}`\n\n{hint}")
                    record(user, result["tag"], correct=False)
                    log("wrong", result["wrong"], result["tag"])
                    ss["twin"] = {"subject": result["subject"], "tag": result["tag"],
                                  "problem": make_twin(result["subject"], result["tag"])}
            if ss.ui_lang != start_lang:
                st.rerun()

    last_reply = next((m["content"] for m in reversed(ss.chat)
                       if m["role"] == "assistant" and m.get("content")), None)
    if last_reply and st.button("🔊 " + t_["read_aloud"], key="speak_btn"):
        mp3 = speak(last_reply, CODE[ss.ui_lang])
        if mp3:
            st.audio(mp3, format="audio/mp3", autoplay=True)
        else:
            st.warning(t_["no_audio"])

    tw = ss.get("twin")
    if tw:
        task, label = t_["tasks"].get(tw["subject"], ("Solve", "Your answer"))
        with st.container(border=True):
            st.markdown(f'<div class="sec">🧩 {t_["try_similar"]}</div>', unsafe_allow_html=True)
            st.write(f"**{task}**")
            st.code(tw["problem"])
            ans = st.text_area(label, key="twin_ans")
            if st.button("✅ " + t_["check_btn"], type="primary", key="twin_check"):
                try:
                    ok = check_twin(tw["subject"], tw["problem"], normalize_digits(ans))
                except Exception:
                    st.error(t_["cant_read_twin"])
                    st.stop()
                record(user, tw["tag"], correct=ok)
                log("right" if ok else "wrong", tw["problem"], tw["tag"])
                if ok:
                    st.success(t_["fixed"])
                    st.balloons()
                else:
                    st.warning(t_["same"])


# ============================================================
# PAGE: MY PROGRESS
# ============================================================
def page_progress():
    lang_, t_, s_, lg_ = L()
    hero("📊 " + s_["tracking"], s_["chat_hint"])
    hist = ss.history.setdefault(user, [])
    n_right = sum(1 for h in hist if h["k"] == "right")
    n_wrong = sum(1 for h in hist if h["k"] == "wrong")
    rows = mistake_map(user)
    n_master = sum(1 for r in rows if r[2] >= 3)
    if n_right + n_wrong:
        acc = f"{round(100 * n_right / (n_right + n_wrong))}%"
    else:
        acc = "–"
    st.markdown(f"""<div class="stats">
      <div class="stat ok"><b>{n_right}</b><span>{s_["right"]}</span></div>
      <div class="stat bad"><b>{n_wrong}</b><span>{s_["wrong"]}</span></div>
      <div class="stat mid"><b>{n_master}</b><span>{s_["mastered"]}</span></div>
      <div class="stat mid"><b>{acc}</b><span>{s_["accuracy"]}</span></div></div>""",
                unsafe_allow_html=True)

    left, right = st.columns([3, 2])
    with left:
        st.markdown(f'<div class="sec">🧠 {t_["map"]}</div>', unsafe_allow_html=True)
        if not rows:
            st.caption(s_["no_mistakes"])
        circ = 2 * 3.14159 * 18
        for tag, errors, box in rows:
            off = circ * (1 - min(box, 4) / 4)
            st.markdown(f"""<div class="ring"><svg viewBox="0 0 44 44">
              <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#6366f1"/><stop offset="100%" stop-color="#a855f7"/>
              </linearGradient></defs>
              <circle class="bg" cx="22" cy="22" r="18"/>
              <circle class="fg" cx="22" cy="22" r="18" stroke-dasharray="{circ:.1f}"
                      stroke-dashoffset="{off:.1f}"/></svg>
              <div><div><b>{html.escape(friendly(tag))}</b></div>
              <div class="lbl">{errors} {t_["errors"]} · {t_["level"]} {box}/4</div></div></div>""",
                        unsafe_allow_html=True)
        if rows:
            df = pd.DataFrame({"errors": [r[1] for r in rows]},
                              index=[friendly(r[0]) for r in rows])
            st.bar_chart(df)
        due_tags = due(user)
        if due_tags:
            st.info("🔔 " + t_["due"] + ": " + ", ".join(friendly(x) for x in due_tags))
    with right:
        st.markdown(f'<div class="sec">🕘 {s_["recent"]}</div>', unsafe_allow_html=True)
        if not hist:
            st.caption(s_["no_activity"])
        icon = {"right": "✅", "wrong": "❌", "asked": "💡"}
        for h in reversed(hist[-30:]):
            tag_line = ""
            if h.get("tag"):
                tag_line = f"<small>{html.escape(friendly(h['tag']))}</small>"
            st.markdown(f'<div class="act"><span>{icon[h["k"]]}</span><div>'
                        f'{html.escape(h["label"])}{tag_line}</div></div>',
                        unsafe_allow_html=True)


# ============================================================
# PAGE: LIVE GESTURES
# ============================================================
def page_gestures():
    lang_, t_, s_, lg_ = L()
    hero("🎥 " + s_["gestures"], s_["gesture_help"])
    c1, c2 = st.columns([3, 2])
    with c1:
        with st.container(border=True):
            try:
                from app.live_video import render_live_video, pop_gesture
                render_live_video(key="learn_live", cooldown=3.5)
                g = pop_gesture()
                if g:
                    apply_gesture(g)
            except Exception as e:
                st.warning(f"Live camera unavailable: {e}")
    with c2:
        with st.container(border=True):
            st.markdown('<div class="sec">👋</div>', unsafe_allow_html=True)
            for k in ("g_up", "g_down", "g_point", "g_palm"):
                st.write(s_[k])
            last = ss.get("last_gesture")
            if last:
                st.success(last[0])
                st.markdown(last[1])
    st.caption("💬 " + s_["chat_hint"])


# ============================================================
# PAGE: ACADEMIC PLANNER
# ============================================================
def page_planner():
    lang_, t_, s_, lg_ = L()
    hero("📅 " + s_["planner"], s_["chat_hint"])
    c1, c2 = st.columns([2, 3])
    with c1:
        with st.container(border=True):
            st.markdown(f'<div class="sec">➕ {s_["add_task"]}</div>', unsafe_allow_html=True)
            with st.form("add_task_form", clear_on_submit=True):
                title = st.text_input(s_["task"])
                subj = st.text_input(s_["subject"])
                due_d = st.text_input(s_["due"])
                pri = st.selectbox(s_["priority"], ["normal", "high", "low"])
                submitted = st.form_submit_button(s_["add"], type="primary",
                                                  use_container_width=True)
                if submitted and title.strip():
                    academic.add_task(user, title.strip(), subj, due_d, pri)
                    st.rerun()
    with c2:
        total, done_n = academic.stats(user)
        if total:
            st.progress(done_n / total, text=f"{done_n}/{total} {s_['of_done']}")
        plan_rows = academic.list_tasks(user, only_open=False)
        if not plan_rows:
            st.caption(s_["no_tasks"])
        for tid, ttitle, tsub, tdue, tpri, tdone in plan_rows:
            meta = " · ".join(x for x in [tsub, tdue] if x)
            meta_html = f"<small>{html.escape(meta)}</small>" if meta else ""
            done_cls = "done" if tdone else ""
            st.markdown(f'<div class="task {tpri} {done_cls}">'
                        f'<span class="tt">{html.escape(ttitle)}</span>{meta_html}</div>',
                        unsafe_allow_html=True)
            b1, b2 = st.columns([4, 1])
            btn_label = ("↩︎ " + s_["undo"]) if tdone else ("✔ " + s_["done"])
            if b1.button(btn_label, key=f"td_{tid}", use_container_width=True):
                academic.toggle_task(tid)
                st.rerun()
            if b2.button("🗑", key=f"tx_{tid}", use_container_width=True):
                academic.delete_task(tid)
                st.rerun()


# ============================================================
# PAGE: PRESENT
# ============================================================
def page_present():
    lang_, t_, s_, lg_ = L()
    hero("🎤 " + s_["present"], s_["present_sub"])
    with st.container(border=True):
        render_presenter()


# ============================================================
# ROUTER
# ============================================================
ROUTES = {
    "learn": page_learn,
    "progress": page_progress,
    "gestures": page_gestures,
    "planner": page_planner,
    "present": page_present,
}
ROUTES.get(ss.page, page_learn)()