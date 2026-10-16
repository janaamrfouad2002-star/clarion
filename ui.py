import hashlib
import html
import secrets
import time

import pandas as pd
import streamlit as st

from app import (academic, auth, history, flashcards, quiz, rooms, roles,
                 answers, progress_report, adaptive)
from app.core import record, due, mistake_map
from app.engine import analyse, make_twin, check_twin
from app.extras import (LANGS, AUTO, CODE, T, GESTURE_REPLY, detect_language,
                        normalize_digits, transcribe, speak)
from app.llm import (extract, explain_with_llm, explain_solution, answer_question,
                     simplify, translate_text)
from app.presenter_ui import render as render_presenter

st.set_page_config(page_title="Lumen", page_icon="💡",
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
.task .tt { font-weight:700; }
.task.overdue { border-left-color:#dc2626; background:#fef2f2; }
.task.today   { border-left-color:#f59e0b; background:#fffbeb; }
.task.soon    { border-left-color:#f59e0b; }
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

[data-testid="stFileUploader"] section { padding: 4px 8px !important; min-height: 40px !important; }
[data-testid="stFileUploader"] small { display:none !important; }
[data-testid="stFileUploader"] label { display:none !important; }

.teacher-badge { display:inline-block; background:linear-gradient(90deg,#6366f1,#a855f7);
  color:#fff; padding:2px 10px; border-radius:999px; font-size:.72rem; font-weight:700;
  margin-left:6px; }

/* ---- Onboarding cards ---- */
.tour-card { background:#fff; border:1px solid var(--line); border-radius:18px;
  padding:22px 26px; margin-bottom:14px; box-shadow:0 12px 30px -22px rgba(15,23,42,.3);
  animation: fadeUp .35s ease both; }
.tour-card h3 { margin:0 0 6px; color:#4f46e5; }
.tour-card p  { margin:0; color:#334155; }
@keyframes fadeUp { from { opacity:0; transform: translateY(8px); } to { opacity:1; transform: translateY(0); } }

/* ---- Streak chip ---- */
.streak { display:flex; align-items:center; gap:8px; padding:8px 12px; border-radius:12px;
  background:linear-gradient(90deg,#fef3c7,#fde68a); border:1px solid #fbbf24;
  font-weight:700; color:#78350f; margin-bottom:10px; }

/* ---- Solution board post ---- */
.post { border:1px solid var(--line); border-radius:14px; padding:12px 14px;
  background:#fff; margin-bottom:8px; }
.post .meta { color:var(--muted); font-size:.78rem; margin-bottom:4px; }
.post .body { white-space:pre-wrap; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# TEXT
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
        g_palm="✋ Please wait", no_mistakes="No mistakes recorded yet.",
        teacher="Teacher", flashcards="Flashcards", quiz="Quiz",
        fl_generate="Generate from mistakes", fl_new="New card", fl_front="Front",
        fl_back="Back", fl_add="Add card", fl_due="Due for review", fl_learned="Learned",
        fl_review="How well did you know it?", fl_again="Again", fl_hard="Hard",
        fl_good="Good", fl_easy="Easy", fl_empty="No cards yet. Generate some from mistakes!",
        quiz_start="Start quiz", quiz_next="Next question", quiz_score="Score",
        quiz_time="Time left", quiz_progress="Question", quiz_done="Quiz complete!",
        quiz_again="Play again", quiz_write="Write your working (one equation per line)",
        quiz_submit="Submit answer", quiz_timer="seconds per question",
        quiz_syllabus="Or upload a syllabus to generate a quiz:",
        quiz_build="Build quiz from this file",
        plan_syllabus="Generate a plan from your syllabus",
        plan_upload="Upload syllabus (PDF or text)",
        plan_days="Days available", plan_hours="Hours per day",
        plan_build="Build my plan",
        rooms="Study rooms",
        surprise="Surprise me"),
    "Hindi": dict(
        learn="सीखें", present="प्रस्तुति", tracking="मेरी प्रगति", planner="अकादमिक योजना",
        gestures="लाइव इशारे", right="सही", wrong="गलत", mastered="सीख लिया",
        accuracy="सटीकता", recent="हाल की गतिविधि",
        no_activity="अभी कुछ नहीं। अपना पहला सवाल पूछें!",
        add_task="कार्य जोड़ें", task="कार्य", subject="विषय (वैकल्पिक)",
        due="अंतिम तिथि (वैकल्पिक)", priority="प्राथमिकता", add="जोड़ें", done="पूरा", undo="वापस",
        no_tasks="अभी कोई कार्य नहीं।", of_done="पूरे",
        present_sub="डेमो के दौरान लाइव बोलें।",
        gesture_help="कैमरा चालू करें, फिर 👍 👎 ☝️ या ✋ दिखाएँ।",
        chat_hint="कभी भी नीचे पूछें।",
        g_up="👍 समझ गया", g_down="👎 और आसान समझाओ", g_point="☝️ मेरा एक सवाल है",
        g_palm="✋ रुकिए", no_mistakes="अभी कोई गलती दर्ज नहीं।",
        teacher="शिक्षक", flashcards="फ्लैशकार्ड", quiz="क्विज़",
        fl_generate="गलतियों से बनाएँ", fl_new="नया कार्ड", fl_front="सामने",
        fl_back="पीछे", fl_add="जोड़ें", fl_due="दोहराने के लिए", fl_learned="सीखा",
        fl_review="कितना आया?", fl_again="फिर से", fl_hard="कठिन",
        fl_good="ठीक", fl_easy="आसान", fl_empty="अभी कोई कार्ड नहीं।",
        quiz_start="क्विज़ शुरू करें", quiz_next="अगला सवाल", quiz_score="स्कोर",
        quiz_time="बचा समय", quiz_progress="प्रश्न", quiz_done="क्विज़ पूरी!",
        quiz_again="फिर खेलें", quiz_write="अपना हल लिखें",
        quiz_submit="जमा करें", quiz_timer="प्रति प्रश्न सेकंड",
        quiz_syllabus="या सिलेबस अपलोड करें:",
        quiz_build="इस फ़ाइल से क्विज़ बनाएँ",
        plan_syllabus="सिलेबस से योजना बनाएँ",
        plan_upload="सिलेबस अपलोड करें (PDF या टेक्स्ट)",
        plan_days="उपलब्ध दिन", plan_hours="प्रति दिन घंटे",
        plan_build="मेरी योजना बनाएँ",
        rooms="अध्ययन कक्ष",
        surprise="कुछ नया दिखाओ"),
    "Arabic": dict(
        learn="تعلّم", present="عرض", tracking="تقدّمي", planner="المخطط الدراسي",
        gestures="إيماءات مباشرة", right="صحيح", wrong="خطأ", mastered="أتقنتها",
        accuracy="الدقة", recent="النشاط الأخير",
        no_activity="لا شيء بعد.",
        add_task="أضف مهمة", task="المهمة", subject="المادة (اختياري)",
        due="تاريخ التسليم (اختياري)", priority="الأولوية", add="إضافة", done="تم", undo="تراجع",
        no_tasks="لا توجد مهام بعد.", of_done="منجزة",
        present_sub="تحدّث مباشرة أثناء العرض.",
        gesture_help="اسمح بالكاميرا ثم أظهر 👍 👎 ☝️ أو ✋.",
        chat_hint="اسأل في الأسفل في أي وقت.",
        g_up="👍 فهمت", g_down="👎 اشرح أبسط", g_point="☝️ لدي سؤال",
        g_palm="✋ انتظر", no_mistakes="لا توجد أخطاء بعد.",
        teacher="المعلم", flashcards="بطاقات", quiz="اختبار",
        fl_generate="أنشئ من الأخطاء", fl_new="بطاقة جديدة", fl_front="الأمام",
        fl_back="الخلف", fl_add="إضافة", fl_due="للمراجعة", fl_learned="تعلمتها",
        fl_review="كيف كان أداؤك؟", fl_again="مرة أخرى", fl_hard="صعب",
        fl_good="جيد", fl_easy="سهل", fl_empty="لا توجد بطاقات بعد.",
        quiz_start="ابدأ الاختبار", quiz_next="السؤال التالي", quiz_score="النتيجة",
        quiz_time="الوقت المتبقي", quiz_progress="سؤال", quiz_done="انتهى!",
        quiz_again="العب مرة أخرى", quiz_write="اكتب حلك",
        quiz_submit="إرسال", quiz_timer="ثانية لكل سؤال",
        quiz_syllabus="أو ارفع المنهج:",
        quiz_build="أنشئ اختباراً من هذا الملف",
        plan_syllabus="أنشئ خطة من المنهج",
        plan_upload="ارفع المنهج (PDF أو نص)",
        plan_days="الأيام المتاحة", plan_hours="ساعات يومياً",
        plan_build="أنشئ خطتي",
        rooms="غرف الدراسة",
        surprise="فاجئني"),
    "French": dict(
        learn="Apprendre", present="Présenter", tracking="Ma progression",
        planner="Planificateur", gestures="Gestes", right="Justes", wrong="Fausses",
        mastered="Maîtrisées", accuracy="Précision", recent="Activité récente",
        no_activity="Rien pour le moment.",
        add_task="Ajouter une tâche", task="Tâche", subject="Matière (facultatif)",
        due="Échéance (facultatif)", priority="Priorité", add="Ajouter", done="Fait", undo="Annuler",
        no_tasks="Aucune tâche.", of_done="terminées",
        present_sub="Parlez en direct pendant votre démo.",
        gesture_help="Autorisez la caméra, puis montrez 👍 👎 ☝️ ou ✋.",
        chat_hint="Posez votre question en bas.",
        g_up="👍 Compris", g_down="👎 Plus simple", g_point="☝️ Une question",
        g_palm="✋ Attendez", no_mistakes="Aucune erreur.",
        teacher="Enseignant", flashcards="Cartes", quiz="Quiz",
        fl_generate="Générer depuis les erreurs", fl_new="Nouvelle carte", fl_front="Recto",
        fl_back="Verso", fl_add="Ajouter", fl_due="À réviser", fl_learned="Apprises",
        fl_review="Comment était-ce ?", fl_again="Encore", fl_hard="Difficile",
        fl_good="Bien", fl_easy="Facile", fl_empty="Pas encore de cartes.",
        quiz_start="Démarrer", quiz_next="Suivant", quiz_score="Score",
        quiz_time="Temps restant", quiz_progress="Question", quiz_done="Terminé !",
        quiz_again="Rejouer", quiz_write="Votre résolution",
        quiz_submit="Envoyer", quiz_timer="secondes par question",
        quiz_syllabus="Ou téléversez votre programme :",
        quiz_build="Créer un quiz depuis ce fichier",
        plan_syllabus="Créer un plan depuis le programme",
        plan_upload="Téléverser le programme (PDF ou texte)",
        plan_days="Jours disponibles", plan_hours="Heures par jour",
        plan_build="Créer mon plan",
        rooms="Salles d'étude",
        surprise="Surprends-moi"),
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
        confirm="पासवर्ड दोबारा", login_btn="लॉग इन", signup_btn="खाता बनाएँ",
        guest="अतिथि के रूप में जारी रखें", bad_login="गलत उपयोगकर्ता नाम या पासवर्ड।",
        locked="बहुत ज़्यादा कोशिशें। {n} सेकंड रुकें।",
        created="खाता बन गया!",
        bad_user="3 से 30 अक्षर, अंक, . _ या -", short_pw="कम से कम 6 अक्षर।",
        taken="यह नाम लिया जा चुका है।", mismatch="पासवर्ड मेल नहीं।",
        logout="लॉग आउट", guest_note="अतिथि की प्रगति सहेजी नहीं जाती।", hello="नमस्ते"),
    "Arabic": dict(
        login="دخول", signup="إنشاء حساب", username="اسم المستخدم", password="كلمة المرور",
        confirm="تأكيد كلمة المرور", login_btn="دخول", signup_btn="إنشاء الحساب",
        guest="المتابعة كضيف", bad_login="بيانات الدخول غير صحيحة.",
        locked="محاولات كثيرة. انتظر {n} ثانية.",
        created="تم إنشاء الحساب!",
        bad_user="من 3 إلى 30 حرفاً", short_pw="6 أحرف على الأقل.",
        taken="الاسم مستخدم", mismatch="كلمتا المرور غير متطابقتين.",
        logout="خروج", guest_note="تقدّم الضيف لا يُحفظ.", hello="مرحباً"),
    "French": dict(
        login="Connexion", signup="Créer un compte", username="Nom d'utilisateur",
        password="Mot de passe", confirm="Confirmer", login_btn="Se connecter",
        signup_btn="Créer", guest="Invité", bad_login="Identifiants incorrects.",
        locked="Trop d'essais. Patientez {n} s.", created="Compte créé !",
        bad_user="3 à 30 caractères", short_pw="6 caractères minimum.",
        taken="Nom déjà utilisé", mismatch="Mots de passe différents.",
        logout="Déconnexion", guest_note="Progression invité non enregistrée.", hello="Bonjour"),
}

# ============================================================
# STATE
# ============================================================
ss = st.session_state
ss.setdefault("chat", [])
ss.setdefault("ui_lang", "English")
ss.setdefault("lang_pref", AUTO)
ss.setdefault("page", "learn")
ss.setdefault("user", None)
ss.setdefault("fails", 0)
ss.setdefault("locked_until", 0.0)
ss.setdefault("tour_step", 0)          # onboarding: 0 = not started, 1..4 = steps, 5 = done

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


def extract_uploaded_text(upload):
    if upload is None:
        return ""
    try:
        if upload.type == "application/pdf":
            import PyPDF2
            reader = PyPDF2.PdfReader(upload)
            return "\n".join((p.extract_text() or "") for p in reader.pages)
        return upload.read().decode("utf-8", errors="ignore")
    except Exception as e:
        st.error(f"Could not read file: {e}")
        return ""


if ss.ui_lang == "Arabic":
    st.markdown("<style>[data-testid='stChatMessage']{direction:rtl;text-align:right}</style>",
                unsafe_allow_html=True)


# ============================================================
# LOGIN
# ============================================================
def login_page():
    lang, t, s, lg = L()
    st.markdown("<style>[data-testid='stSidebar'],[data-testid='stSidebarCollapsedControl'],"
                "[data-testid='collapsedControl']{display:none}</style>", unsafe_allow_html=True)
    hero("💡 Lumen", t["tagline"],
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
# SIDEBAR
# ============================================================
current_role = roles.get_role(user)
counts = history.counts(user)
today_total = counts["right"] + counts["wrong"]

with st.sidebar:
    badge = '<span class="teacher-badge">TEACHER</span>' if current_role == "teacher" else ""
    st.markdown(
        f'<div class="usercard"><div class="avatar">{html.escape(user[0].upper())}</div>'
        f'<div><b>{lg["hello"]}, {html.escape(user)}</b>{badge}</div></div>',
        unsafe_allow_html=True)

    # Streak chip
    goal = 10
    st.markdown(
        f'<div class="streak">🔥 Today: {today_total}/{goal}</div>',
        unsafe_allow_html=True)

    lang_picker("lp_side")
    st.markdown("---")

    PAGES = [("learn", "💬", s["learn"]),
             ("present", "🎤", s["present"]),
             ("progress", "📊", s["tracking"]),
             ("flashcards", "📇", s.get("flashcards", "Flashcards")),
             ("quiz", "🎯", s.get("quiz", "Quiz")),
             ("rooms", "👥", s.get("rooms", "Study rooms")),
             ("gestures", "🎥", s["gestures"]),
             ("planner", "📅", s["planner"])]
    if current_role == "teacher":
        PAGES.append(("teacher", "🏫", s.get("teacher", "Teacher")))

    for key, icon, label in PAGES:
        kind = "primary" if ss.page == key else "secondary"
        if st.button(f"{icon}  {label}", key=f"nav_{key}",
                     use_container_width=True, type=kind):
            ss.page = key
            st.rerun()

    st.markdown("---")

    if current_role != "teacher":
        with st.expander("👩‍🏫 I am a teacher"):
            st.caption("Enter your teacher code to unlock class-wide tools.")
            code_in = st.text_input("Teacher code", type="password", key="teacher_code")
            if st.button("Unlock teacher tools", key="unlock_teacher",
                         use_container_width=True):
                if roles.try_promote(user, code_in):
                    st.success("Teacher tools unlocked.")
                    st.rerun()
                else:
                    st.error("Incorrect code.")

    if user.startswith("guest-"):
        st.caption(lg["guest_note"])
    if st.button("🚪 " + lg["logout"], use_container_width=True, key="logout"):
        for k in ("user", "chat", "twin", "inbox", "last_gesture",
                  "quiz_qs", "quiz_i", "quiz_score", "quiz_started", "tour_step"):
            ss.pop(k, None)
        ss.page = "learn"
        st.rerun()

# ============================================================
# BOTTOM CHAT BAR — only on Learn
# ============================================================
AUDIO_IN_BAR = True
prompt = None
if ss.page == "learn":
    try:
        prompt = st.chat_input(t["placeholder"], accept_file=True,
                               file_type=["png", "jpg", "jpeg"], accept_audio=True)
    except TypeError:
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
    if ss.page != "learn":
        ss.page = "learn"
        st.rerun()


# ============================================================
# HELPERS
# ============================================================
def log(kind, label, tag=""):
    try:
        history.add(user, kind, label, tag)
    except Exception as e:
        print("LOG ERROR:", e)


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
# ONBOARDING TOUR
# ============================================================
def page_tour():
    hero("👋 Welcome to Lumen", "A 30-second tour before you start.")
    steps = [
        ("1. Type your working",
         "In the box at the bottom of the Learn page, type your steps — one "
         "equation per line. Or speak, or upload a photo of your notebook."),
        ("2. We find the mistake",
         "Lumen compares each line to the previous one, finds the first line "
         "that changed the answer, and names the misconception behind it."),
        ("3. Practice on a twin problem",
         "After every mistake you get a fresh problem with the same structure "
         "but new numbers. Solving it confirms you've fixed the error."),
        ("4. Every mistake becomes a flashcard",
         "The Flashcards page collects every error you've made into cards you "
         "can review. The learner model schedules them for spaced repetition."),
    ]
    for title, body in steps:
        st.markdown(
            f'<div class="tour-card"><h3>{title}</h3><p>{body}</p></div>',
            unsafe_allow_html=True)

    if st.button("🚀 Start learning", type="primary", use_container_width=True):
        ss.tour_step = 5
        ss.page = "learn"
        st.rerun()


# ============================================================
# PAGE: LEARN
# ============================================================
def page_learn():
    # First-visit onboarding
    if ss.get("tour_step", 0) == 0:
        ss.tour_step = 1
        ss.page = "tour"
        st.rerun()

    lang_, t_, s_, lg_ = L()
    hero("💡 Lumen", t_["tagline"],
         ["🧠 Verified mistakes", "🗣️ 4 languages", "📇 Flashcards", "🎯 Quiz", "📅 Planner"])
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
            if ss.lang_pref == AUTO and len(text.strip()) >= 4:
                if from_voice and voice_lang:
                    detected = voice_lang
                else:
                    detected = detect_language(text)
                if detected and detected != ss.ui_lang:
                    import re as _re
                    if detected == "Arabic":
                        script_chars = len(_re.findall(r"[\u0600-\u06FF]", text))
                    elif detected == "Hindi":
                        script_chars = len(_re.findall(r"[\u0900-\u097F]", text))
                    else:
                        script_chars = len(_re.findall(r"[A-Za-zÀ-ÿ]", text))
                    if script_chars >= 3:
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
                    # General answer — clearly labelled as not verified
                    with st.spinner("..."):
                        reply = answers.general_answer(text, img, mime, lang_)
                    say("assistant", reply)
                    log("asked", text or "📷")
                else:
                    with st.spinner("..."):
                        hint = explain_with_llm(result["prev"], result["wrong"],
                                                result["tag"], lang_) or ""
                    tag_raw = result["tag"]
                    conf = result.get("confidence", 1.0)
                    if tag_raw.endswith("?") or conf < 0.99:
                        base = tag_raw.rstrip("?")
                        shown = f"{friendly(base)} (≈{int(conf * 100)}% confidence)"
                    else:
                        shown = friendly(tag_raw)
                    say("assistant",
                        f"**{t_['mistake']}:** `{shown}`\n\n"
                        f"{t_['your_line']}: `{result['wrong']}`\n\n{hint}")
                    record(user, tag_raw.rstrip("?"), correct=False)
                    log("wrong", result["wrong"], tag_raw.rstrip("?"))
                    clean_tag = tag_raw.rstrip("?")
                    # Adaptive difficulty for the twin
                    difficulty = adaptive.pick_difficulty(user, clean_tag)
                    problem = adaptive.make_problem(clean_tag, difficulty)
                    ss["twin"] = {"subject": result["subject"],
                                  "tag": clean_tag,
                                  "problem": problem,
                                  "difficulty": difficulty}
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

    # "Explain more simply" button for the last hint
    if last_reply:
        if st.button("💡 Explain this to me more simply", key="explain_more"):
            with st.spinner("..."):
                simpler = simplify(last_reply, lang_) or t_["sorry"]
            say("assistant", simpler)

    tw = ss.get("twin")
    if tw:
        task, label = t_["tasks"].get(tw["subject"], ("Solve", "Your answer"))
        diff = tw.get("difficulty", "medium")
        diff_badge = {"easy": "🟢 Easy", "medium": "🟡 Medium", "hard": "🔴 Hard"}.get(diff, "")
        with st.container(border=True):
            st.markdown(f'<div class="sec">🧩 {t_["try_similar"]} {diff_badge}</div>',
                        unsafe_allow_html=True)
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
                # Update the adaptive streak
                adaptive.record_attempt(user, tw["tag"], ok)
                if ok:
                    st.success(t_["fixed"])
                    st.balloons()
                else:
                    st.warning(t_["same"])


# ============================================================
# PAGE: PRESENT
# ============================================================
def page_present():
    lang_, t_, s_, lg_ = L()
    hero("🎤 " + s_["present"], s_["present_sub"])
    render_presenter()


# ============================================================
# PAGE: PROGRESS
# ============================================================
def page_progress():
    lang_, t_, s_, lg_ = L()
    hero("📊 " + s_["tracking"], s_["chat_hint"])
    counts = history.counts(user)
    n_right = counts["right"]
    n_wrong = counts["wrong"]
    rows = mistake_map(user)
    n_master = sum(1 for r in rows if r[2] >= 3)
    acc = f"{round(100 * n_right / (n_right + n_wrong))}%" if (n_right + n_wrong) else "–"
    st.markdown(f"""<div class="stats">
      <div class="stat ok"><b>{n_right}</b><span>{s_["right"]}</span></div>
      <div class="stat bad"><b>{n_wrong}</b><span>{s_["wrong"]}</span></div>
      <div class="stat mid"><b>{n_master}</b><span>{s_["mastered"]}</span></div>
      <div class="stat mid"><b>{acc}</b><span>{s_["accuracy"]}</span></div></div>""",
                unsafe_allow_html=True)

    # Export PDF
    if st.button("📄 Download my progress report (PDF)", key="dl_pdf"):
        try:
            pdf_bytes = progress_report.build_pdf(user)
            st.download_button("💾 Save PDF", data=pdf_bytes,
                               file_name=f"lumen_progress_{user}.pdf",
                               mime="application/pdf",
                               key="save_pdf")
        except Exception as e:
            st.error(f"Could not generate PDF: {e}")

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
            labels = [friendly(r[0]) for r in rows]
            errors = [r[1] for r in rows]
            df = pd.DataFrame({"Errors": errors}, index=labels)
            df.index.name = "Misconception"
            st.bar_chart(df, height=320, use_container_width=True, color="#6366f1")
        due_tags = due(user)
        if due_tags:
            st.info("🔔 " + t_["due"] + ": " + ", ".join(friendly(x) for x in due_tags))
    with right:
        st.markdown(f'<div class="sec">🕘 {s_["recent"]}</div>', unsafe_allow_html=True)
        recent = history.recent(user, limit=30)
        if not recent:
            st.caption(s_["no_activity"])
        icon = {"right": "✅", "wrong": "❌", "asked": "💡"}
        for k, lbl, tg in recent:
            tag_line = ""
            if tg:
                tag_line = f"<small>{html.escape(friendly(tg))}</small>"
            st.markdown(f'<div class="act"><span>{icon.get(k, "•")}</span><div>'
                        f'{html.escape(lbl)}{tag_line}</div></div>',
                        unsafe_allow_html=True)


# ============================================================
# PAGE: FLASHCARDS
# ============================================================
def page_flashcards():
    lang_, t_, s_, lg_ = L()
    hero("📇 Flashcards",
         "Every mistake you make becomes a card. Review cards you got wrong before.")

    st_stats = flashcards.stats(user)
    c1, c2, c3 = st.columns(3)
    c1.metric("Due for review", st_stats["due"])
    c2.metric("Total cards", st_stats["total"])
    c3.metric("Learned", st_stats["learned"])

    st.markdown('<div class="sec">✨ Auto-generate from your mistakes</div>',
                unsafe_allow_html=True)
    st.caption("Reads every wrong step you have made in Learn and turns it into a card.")
    if st.button("Generate now", type="primary", use_container_width=True,
                 key="fc_gen"):
        n = flashcards.generate_from_history(user)
        if n == 0:
            st.info("No new mistakes to convert. Make a wrong attempt in Learn first, "
                    "then click this again.")
        else:
            st.success(f"Added {n} new card(s).")
            st.rerun()

    st.markdown('<div class="sec">📖 Cards due for review</div>', unsafe_allow_html=True)
    cards = flashcards.due_cards(user, limit=20)
    if not cards:
        st.success("Nothing due. Nice work!")
    else:
        for cid, front, back, tag in cards[:5]:
            with st.container(border=True):
                st.markdown(f"**{front}**")
                with st.expander("Show answer"):
                    st.markdown(back)
                bc = st.columns(4)
                for i, (label, q) in enumerate(
                        [("Again", 0), ("Hard", 1), ("Good", 2), ("Easy", 3)]):
                    if bc[i].button(label, key=f"rev_{cid}_{i}", use_container_width=True):
                        flashcards.review(user, cid, q)
                        st.rerun()

    with st.expander("➕ Add your own card (optional)"):
        st.caption("Front = the question. Back = the answer. Most cards come from "
                   "your mistakes automatically — you only need this if you want a "
                   "card that isn't based on an error.")
        front_in = st.text_input("Front (question)", key="fc_front_input")
        back_in = st.text_area("Back (answer)", key="fc_back_input")
        if st.button("Add card", key="fc_add_btn", type="primary"):
            if front_in.strip() and back_in.strip():
                flashcards.add_manual(user, front_in, back_in)
                st.success("Card added.")
                st.rerun()
            else:
                st.warning("Please fill in both fields.")


# ============================================================
# PAGE: QUIZ
# ============================================================
def page_quiz():
    lang_, t_, s_, lg_ = L()
    hero("🎯 " + s_.get("quiz", "Quiz"),
         "Timed practice targeting your weakest misconceptions.")
    ss.setdefault("quiz_qs", [])
    ss.setdefault("quiz_i", 0)
    ss.setdefault("quiz_score", 0)
    ss.setdefault("quiz_started", 0.0)
    ss.setdefault("quiz_seconds", 30)

    if not ss.quiz_qs:
        c1, c2 = st.columns(2)
        n_q = c1.slider("Questions", 5, 20, 10, key="quiz_n")
        secs = c2.slider("Seconds per question", 15, 120, 30, key="quiz_secs")
        if st.button("▶️ Start quiz", type="primary", use_container_width=True):
            ss.quiz_qs = quiz.build_quiz(user, n_questions=n_q)
            ss.quiz_i = 0
            ss.quiz_score = 0
            ss.quiz_seconds = secs
            ss.quiz_started = time.time()
            st.rerun()

        st.markdown("---")
        st.markdown(f"**{s_.get('quiz_syllabus', 'Or upload a syllabus to generate a quiz:')}**")
        up = st.file_uploader("Syllabus", type=["pdf", "txt"],
                              key="quiz_syl_upload", label_visibility="collapsed")
        if up is not None and st.button("📚 " + s_.get("quiz_build", "Build quiz from this file"),
                                        type="primary", use_container_width=True,
                                        key="quiz_build_btn"):
            text_content = extract_uploaded_text(up)
            if not text_content.strip():
                st.warning("No text found in the file.")
            else:
                with st.spinner("Generating questions…"):
                    try:
                        qs = quiz.build_quiz_from_syllabus(text_content, n_questions=n_q)
                    except Exception as e:
                        st.error(f"Quiz generation failed: {e}")
                        qs = []
                if qs:
                    ss.quiz_qs = qs
                    ss.quiz_i = 0
                    ss.quiz_score = 0
                    ss.quiz_seconds = secs
                    ss.quiz_started = time.time()
                    st.rerun()
                else:
                    st.error("Could not generate questions. Check GOOGLE_API_KEY.")
        return

    total = len(ss.quiz_qs)

    if ss.quiz_i >= total:
        summary = quiz.score_summary(ss.quiz_score, total, 0)
        st.subheader("Quiz complete!")
        st.metric("Score", f"{ss.quiz_score}/{total}")
        st.metric("Grade", summary["grade"])
        if st.button("🔁 Play again", type="primary"):
            ss.quiz_qs = []
            st.rerun()
        return

    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=1000, key=f"quiz_tick_{ss.quiz_i}")

    q = ss.quiz_qs[ss.quiz_i]
    elapsed = time.time() - ss.quiz_started
    remaining = max(0, ss.quiz_seconds - elapsed)

    st.progress(ss.quiz_i / total,
                text=f"Question {ss.quiz_i + 1}/{total}")
    c1, c2 = st.columns([3, 1])
    c1.markdown(f"**Solve:** `{q['problem']}`")
    c2.metric("Time left", f"{int(remaining)}s")

    if remaining <= 0:
        ss.quiz_i += 1
        ss.quiz_started = time.time()
        st.rerun()

    with st.form(f"quiz_form_{ss.quiz_i}"):
        ans = st.text_area("Write your working", key=f"quiz_ans_{ss.quiz_i}")
        submitted = st.form_submit_button("✅ Submit answer", type="primary")

    if submitted:
        lines = [l.strip() for l in ans.splitlines() if l.strip()]
        ok = quiz.check_answer(q, lines)
        if ok:
            ss.quiz_score += 1
            st.success("✅ Correct")
        else:
            st.error("❌ Incorrect")
        ss.quiz_i += 1
        ss.quiz_started = time.time()
        st.rerun()


# ============================================================
# PAGE: STUDY ROOMS  (with solution board)
# ============================================================
def page_rooms():
    lang_, t_, s_, lg_ = L()
    hero("👥 Study rooms",
         "Join a room, share your solutions, upvote the best ones.")

    with st.container(border=True):
        st.markdown('<div class="sec">➕ Create a room</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        topic = c1.text_input("Topic", key="room_topic",
                              placeholder="e.g. Linear equations")
        age_band = c2.selectbox("Age band",
                                ["10-12", "13-15", "16-18", "18+"],
                                key="room_age")
        if st.button("Create room", type="primary", key="room_create"):
            if topic.strip():
                code = rooms.create_room(topic.strip(), age_band, user)
                st.success(f"Room created. Share code: {code}")
                st.rerun()
            else:
                st.warning("Please enter a topic.")

    with st.container(border=True):
        st.markdown('<div class="sec">🔗 Join a room by code</div>', unsafe_allow_html=True)
        code_in = st.text_input("Room code", key="room_code", max_chars=6)
        if st.button("Join", key="room_join"):
            if code_in.strip():
                ok = rooms.join_room(code_in, user)
                if ok:
                    st.success("Joined!")
                    st.rerun()
                else:
                    st.error("Room not found.")

    mine = rooms.my_rooms(user)
    if mine:
        st.markdown('<div class="sec">📌 My rooms</div>', unsafe_allow_html=True)
        for code, topic, age_band, host in mine:
            with st.container(border=True):
                st.markdown(f"**{topic}** · {age_band} · host: `{host}` · code: `{code}`")
                others = [m for m, _ in rooms.members_of(code) if m != user]
                if others:
                    st.caption("Also here: " + ", ".join(others))
                else:
                    st.caption("You are the only one here so far.")

                # ---- Solution board ----
                st.markdown('<div class="sec">💬 Solution board</div>',
                            unsafe_allow_html=True)
                new_post = st.text_area(
                    "Post a solution, a question, or a tip",
                    key=f"post_body_{code}",
                    height=100,
                )
                if st.button("📤 Post", key=f"post_btn_{code}", type="primary"):
                    if new_post.strip():
                        rooms.post_solution(code, user, new_post)
                        st.rerun()

                posts = rooms.list_posts(code, limit=20)
                if not posts:
                    st.caption("No posts yet. Be the first to share.")
                else:
                    for pid, puser, body, votes, created in posts:
                        st.markdown(
                            f'<div class="post"><div class="meta">{html.escape(puser)}'
                            f' · {votes} ⬆</div>'
                            f'<div class="body">{html.escape(body)}</div></div>',
                            unsafe_allow_html=True)
                        bc1, bc2 = st.columns([1, 5])
                        if bc1.button("⬆ Upvote", key=f"vote_{pid}"):
                            if rooms.vote_post(pid, user):
                                st.rerun()
                        if puser == user:
                            if bc2.button("🗑 Delete", key=f"del_{pid}"):
                                rooms.delete_post(pid, user)
                                st.rerun()

                if st.button("Leave room", key=f"leave_{code}"):
                    rooms.leave_room(code, user)
                    st.rerun()

    st.markdown('<div class="sec">🌍 Open rooms</div>', unsafe_allow_html=True)
    all_rooms = rooms.list_rooms()
    if not all_rooms:
        st.caption("No rooms yet. Create one above.")
    else:
        for code, topic, age_band, host, n in all_rooms:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"**{topic}** · {age_band}")
                c1.caption(f"Host: {host} · {n} member(s) · code `{code}`")
                if c2.button("Join", key=f"open_join_{code}"):
                    rooms.join_room(code, user)
                    st.rerun()


# ============================================================
# PAGE: GESTURES
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
# PAGE: PLANNER
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
                due_d = st.date_input("Due date (optional)", value=None,
                                      key="plan_due_date")
                pri = st.selectbox(s_["priority"], ["normal", "high", "low"])
                submitted = st.form_submit_button(s_["add"], type="primary",
                                                  use_container_width=True)
                if submitted and title.strip():
                    due_str = due_d.strftime("%Y-%m-%d") if due_d else ""
                    academic.add_task(user, title.strip(), subj, due_str, pri)
                    st.rerun()

        with st.container(border=True):
            st.markdown(f'<div class="sec">📚 {s_.get("plan_syllabus", "Generate a plan from your syllabus")}</div>',
                        unsafe_allow_html=True)
            plan_up = st.file_uploader(s_.get("plan_upload", "Upload syllabus (PDF or text)"),
                                       type=["pdf", "txt"],
                                       key="plan_syllabus",
                                       label_visibility="collapsed")
            days = st.number_input(s_.get("plan_days", "Days available"),
                                   3, 90, 14, key="plan_days")
            hrs = st.slider(s_.get("plan_hours", "Hours per day"),
                            0.5, 6.0, 1.0, 0.5, key="plan_hrs")
            if plan_up is not None and st.button(s_.get("plan_build", "Build my plan"),
                                                 type="primary",
                                                 use_container_width=True,
                                                 key="plan_build"):
                text_content = extract_uploaded_text(plan_up)
                if not text_content.strip():
                    st.warning("No text found in the file.")
                else:
                    with st.spinner("Building your plan…"):
                        try:
                            n = academic.generate_plan_from_syllabus(
                                user, text_content, int(days), float(hrs)
                            )
                        except Exception as e:
                            st.error(f"Plan generation failed: {e}")
                            n = 0
                    if n:
                        st.success(f"Added {n} tasks to your planner.")
                        st.rerun()
                    else:
                        st.error("Could not build the plan. Check GOOGLE_API_KEY.")

        with st.container(border=True):
            st.markdown('<div class="sec">📧 Daily email reminder</div>',
                        unsafe_allow_html=True)
            current_email = academic.get_reminder_email(user)
            email_in = st.text_input("Your email", value=current_email, key="plan_email")
            if st.button("Save email", use_container_width=True):
                academic.set_reminder_email(user, email_in.strip())
                st.success("Saved.")

    with c2:
        total, done_n = academic.stats(user)
        if total:
            st.progress(done_n / total, text=f"{done_n}/{total} {s_['of_done']}")
        tasks = academic.list_tasks(user, only_open=False)
        if not tasks:
            st.caption(s_["no_tasks"])
        for tid, ttitle, tsub, tdue, tpri, tdone in tasks:
            label, due_cls = academic.due_label(tdue)
            meta = " · ".join(x for x in [tsub, label] if x)
            done_cls = "done" if tdone else ""
            st.markdown(f'<div class="task {tpri} {done_cls} {due_cls}">'
                        f'<span class="tt">{html.escape(ttitle)}</span>'
                        f'<small>{html.escape(meta)}</small></div>',
                        unsafe_allow_html=True)
            b1, b2, b3 = st.columns([3, 1, 1])
            btn_label = ("↩︎ " + s_["undo"]) if tdone else ("✔ " + s_["done"])
            if b1.button(btn_label, key=f"td_{tid}", use_container_width=True):
                academic.toggle_task(tid)
                st.rerun()
            if b2.button("⏰", key=f"ts_{tid}", use_container_width=True):
                academic.snooze_task(tid)
                st.rerun()
            if b3.button("🗑", key=f"tx_{tid}", use_container_width=True):
                academic.delete_task(tid)
                st.rerun()


# ============================================================
# PAGE: TEACHER  (teacher-only)
# ============================================================
def page_teacher():
    if roles.get_role(user) != "teacher":
        st.error("This page is for teachers only. "
                 "Enter the teacher code in the sidebar to unlock it.")
        return

    try:
        from app import teacher as teacher_mod
    except ImportError:
        st.error("`app/teacher.py` not found.")
        return
    lang_, t_, s_, lg_ = L()
    hero("🏫 Teacher dashboard", "Aggregate misconception data across all students.")
    students = history.all_users()
    if not students:
        st.info("No student data yet.")
        return
    st.markdown('<div class="sec">🔥 Top misconceptions</div>', unsafe_allow_html=True)
    top = teacher_mod.top_misconceptions(limit=10)
    if top:
        df = pd.DataFrame([{"Misconception": friendly(tag),
                            "Total errors": total,
                            "Students affected": students_n}
                           for tag, total, students_n in top])
        st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown('<div class="sec">⚠️ Students at risk</div>', unsafe_allow_html=True)
    risk = teacher_mod.students_at_risk(threshold=3)
    if not risk:
        st.success("No students are stuck at the same mistake 3+ times.")
    else:
        df2 = pd.DataFrame([{"Student": u, "Misconception": friendly(tag),
                             "Errors": errors, "Box": box}
                            for u, tag, errors, box in risk])
        st.dataframe(df2, use_container_width=True, hide_index=True)
    st.markdown('<div class="sec">📊 Class heatmap</div>', unsafe_allow_html=True)
    heat = teacher_mod.class_heatmap()
    all_tags = sorted({tag for row in heat.values() for tag in row})
    if all_tags:
        matrix = [{"Student": st_, **{friendly(tag): heat[st_].get(tag, 0)
                                       for tag in all_tags}} for st_ in sorted(heat)]
        st.dataframe(pd.DataFrame(matrix), use_container_width=True, hide_index=True)
        chart_df = pd.DataFrame(
            {friendly(tag): [heat[st_].get(tag, 0) for st_ in sorted(heat)]
             for tag in all_tags},
            index=sorted(heat))
        st.bar_chart(chart_df)


# ============================================================
# ROUTER
# ============================================================
ROUTES = {
    "tour": page_tour,
    "learn": page_learn,
    "present": page_present,
    "progress": page_progress,
    "flashcards": page_flashcards,
    "quiz": page_quiz,
    "rooms": page_rooms,
    "gestures": page_gestures,
    "planner": page_planner,
    "teacher": page_teacher,
}
ROUTES.get(ss.page, page_learn)()