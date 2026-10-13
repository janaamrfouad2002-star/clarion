"""extras.py - languages, voice, read-aloud and camera gestures. No grading happens here."""
import io
import os
import re
import urllib.request

from dotenv import load_dotenv

load_dotenv()

LANGS = {
    "English": ("English", "en"),
    "हिन्दी": ("Hindi", "hi"),
    "العربية": ("Arabic", "ar"),
    "Français": ("French", "fr"),
}
AUTO = "🌐 Auto-detect"
CODE = {v[0]: v[1] for v in LANGS.values()}
WHISPER_NAMES = {"english": "English", "hindi": "Hindi", "arabic": "Arabic", "french": "French"}

_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩०१२३४५६७८९", "01234567890123456789")


def normalize_digits(s: str) -> str:
    return s.translate(_DIGITS)


_FR_WORDS = (" le ", " la ", " les ", " un ", " une ", " des ", " est ", " quelle ", " quel ",
             " comment ", " pourquoi ", " donne ", " calcule ", " et ", " je ", " mon ",
             " ma ", " que ", " du ", " de ", " équilibre ", " dérivée ")


def detect_language(text: str):
    t = text or ""
    dev = len(re.findall(r"[\u0900-\u097F]", t))
    arb = len(re.findall(r"[\u0600-\u06FF]", t))
    if dev and dev >= arb:
        return "Hindi"
    if arb:
        return "Arabic"
    low = " " + t.lower() + " "
    if re.search(r"[àâçéèêëîïôûùüÿœ]", low):
        return "French"
    if sum(w in low for w in _FR_WORDS) >= 2:
        return "French"
    if len(re.findall(r"[A-Za-z]{3,}", t)) >= 2:
        return "English"
    return None


# ---------------- all on-screen text ----------------
T = {
    "English": {
        "tagline": "Learn from your mistakes. Ask in any language.",
        "welcome": "👋 Hi! Ask me a question, send your working, upload a photo, or use your voice. "
                   "I'll find exactly where the mistake happened and help you fix it.",
        "try": "Try one of these:",
        "examples": ["What is the derivative of x^3 + 2x?", "Balance H2 + O2 -> H2O",
                     "2x + 3 = 11\n2x = 14\nx = 7", "Calculate 20 m / (4 s)"],
        "placeholder": "Ask a question, or send your working (type it or upload a photo).",
        "mic": "🎤 Ask by voice", "cam": "📷 Show a hand gesture",
        "name": "Your name",
        "read": "What I read (check it is right!)",
        "correct": "All correct! ✅",
        "mistake": "Verified mistake", "your_line": "Your line",
        "answer": "Answer (computed by software)",
        "try_similar": "Try a similar one",
        "check_btn": "Check",
        "fixed": "Well done! You've got it now. 🎉",
        "same": "Same trouble. We'll review this again later.",
        "cant_read_twin": "I couldn't read your answer.",
        "map": "Mistake map", "due": "Ready to review", "level": "level", "errors": "errors",
        "none": "No mistakes recorded yet.",
        "no_gesture": "No hand gesture found. Hold your hand up clearly.",
        "cant_hear": "I couldn't hear that. Try again, or type your question.",
        "cant_read": "I couldn't read the maths. Open 'What I read': if it is wrong, type the problem.",
        "sorry": "Sorry, I couldn't reach the AI just now. Please try again.",
        "read_aloud": "Listen to the last answer", "clear": "Clear chat",
        "no_audio": "Couldn't make audio right now.",
        "tasks": {
            "algebra": ("Solve step by step", "Your working, one equation per line"),
            "derivative": ("Differentiate", "Your final answer"),
            "integral": ("Integrate", "Your final answer (include + C)"),
            "chemistry_balance": ("Balance this equation", "Your balanced equation, like 2H2 + O2 -> 2H2O"),
            "physics_calc": ("Calculate (include units)", "Your answer with units, like 5 m/s")},
    },
    "Hindi": {
        "tagline": "अपनी गलतियों से सीखें। किसी भी भाषा में पूछें।",
        "welcome": "👋 नमस्ते! कोई सवाल पूछें या अपना हल भेजें।",
        "try": "इनमें से कोई आज़माएँ:",
        "examples": ["x^3 + 2x का अवकलज क्या है?", "H2 + O2 -> H2O को संतुलित करो",
                     "2x + 3 = 11\n2x = 14\nx = 7", "20 m / (4 s) की गणना करो"],
        "placeholder": "सवाल पूछें या अपना हल भेजें।",
        "mic": "🎤 बोलकर पूछें", "cam": "📷 हाथ का इशारा दिखाएँ",
        "name": "आपका नाम", "read": "मैंने क्या पढ़ा (जाँच लें!)",
        "correct": "बिल्कुल सही! ✅", "mistake": "पुष्टि की गई गलती", "your_line": "आपकी पंक्ति",
        "answer": "उत्तर (सॉफ़्टवेयर से गणना)", "try_similar": "ऐसा ही एक और हल करें",
        "check_btn": "जाँचें", "fixed": "बहुत बढ़िया! 🎉",
        "same": "अभी भी वही दिक्कत है।", "cant_read_twin": "मैं आपका उत्तर पढ़ नहीं पाया।",
        "map": "गलतियों का नक्शा", "due": "दोहराने के लिए तैयार", "level": "स्तर", "errors": "गलतियाँ",
        "none": "अभी कोई गलती दर्ज नहीं।", "no_gesture": "कोई इशारा नहीं मिला।",
        "cant_hear": "मैं सुन नहीं पाया।", "cant_read": "मैं यह गणित पढ़ नहीं पाया।",
        "sorry": "माफ़ कीजिए, अभी AI से संपर्क नहीं हो पाया।",
        "read_aloud": "आखिरी जवाब सुनें", "clear": "चैट साफ़ करें",
        "no_audio": "अभी आवाज़ नहीं बन पाई।",
        "tasks": {
            "algebra": ("चरण-दर-चरण हल करें", "आपका हल"),
            "derivative": ("अवकलन करें", "अंतिम उत्तर"),
            "integral": ("समाकलन करें", "अंतिम उत्तर"),
            "chemistry_balance": ("संतुलित करें", "संतुलित समीकरण"),
            "physics_calc": ("गणना करें", "इकाई सहित उत्तर")},
    },
    "Arabic": {
        "tagline": "تعلّم من أخطائك. اسأل بأي لغة.",
        "welcome": "👋 مرحباً! اطرح سؤالاً أو أرسل حلّك.",
        "try": "جرّب أحد هذه الأمثلة:",
        "examples": ["ما مشتقة x^3 + 2x؟", "وازن المعادلة H2 + O2 -> H2O",
                     "2x + 3 = 11\n2x = 14\nx = 7", "احسب 20 m / (4 s)"],
        "placeholder": "اطرح سؤالاً أو أرسل حلّك.",
        "mic": "🎤 اسأل بالصوت", "cam": "📷 أظهر إشارة بيدك",
        "name": "اسمك", "read": "ما قرأته (تأكد!)",
        "correct": "كل شيء صحيح! ✅", "mistake": "خطأ مؤكَّد", "your_line": "سطرك",
        "answer": "الجواب (محسوب بالبرنامج)", "try_similar": "جرّب مسألة مشابهة",
        "check_btn": "تحقق", "fixed": "رائع! 🎉",
        "same": "ما زالت المشكلة نفسها.", "cant_read_twin": "لم أستطع قراءة إجابتك.",
        "map": "خريطة الأخطاء", "due": "جاهز للمراجعة", "level": "المستوى", "errors": "أخطاء",
        "none": "لا توجد أخطاء مسجلة بعد.", "no_gesture": "لم أجد إشارة.",
        "cant_hear": "لم أسمع جيداً.", "cant_read": "لم أستطع قراءة المسألة.",
        "sorry": "عذراً، حاول مرة أخرى.", "read_aloud": "استمع", "clear": "مسح",
        "no_audio": "تعذّر إنشاء الصوت.",
        "tasks": {
            "algebra": ("حلّ خطوة بخطوة", "حلّك"),
            "derivative": ("اشتقّ", "جوابك"),
            "integral": ("أوجد التكامل", "جوابك"),
            "chemistry_balance": ("وازن", "المعادلة الموزونة"),
            "physics_calc": ("احسب", "الجواب مع الوحدة")},
    },
    "French": {
        "tagline": "Apprenez de vos erreurs. Posez vos questions.",
        "welcome": "👋 Bonjour ! Posez une question ou envoyez votre travail.",
        "try": "Essayez l'un de ces exemples :",
        "examples": ["Quelle est la dérivée de x^3 + 2x ?", "Équilibre H2 + O2 -> H2O",
                     "2x + 3 = 11\n2x = 14\nx = 7", "Calcule 20 m / (4 s)"],
        "placeholder": "Posez une question ou envoyez votre travail.",
        "mic": "🎤 Poser à voix haute", "cam": "📷 Montrez un geste",
        "name": "Votre nom", "read": "Ce que j'ai lu (vérifiez !)",
        "correct": "Tout est correct ! ✅", "mistake": "Erreur vérifiée", "your_line": "Votre ligne",
        "answer": "Réponse (calculée)", "try_similar": "Essayez un exercice similaire",
        "check_btn": "Vérifier", "fixed": "Bravo ! 🎉",
        "same": "Même difficulté.", "cant_read_twin": "Je n'ai pas pu lire votre réponse.",
        "map": "Carte des erreurs", "due": "À réviser", "level": "niveau", "errors": "erreurs",
        "none": "Aucune erreur enregistrée.", "no_gesture": "Aucun geste trouvé.",
        "cant_hear": "Je n'ai pas entendu.", "cant_read": "Je n'ai pas pu lire les maths.",
        "sorry": "Désolé, réessayez.", "read_aloud": "Écouter", "clear": "Effacer",
        "no_audio": "Impossible de créer l'audio.",
        "tasks": {
            "algebra": ("Résolvez étape par étape", "Votre résolution"),
            "derivative": ("Dérivez", "Votre réponse"),
            "integral": ("Intégrez", "Votre réponse"),
            "chemistry_balance": ("Équilibrez", "Votre équation"),
            "physics_calc": ("Calculez", "Réponse avec unités")},
    },
}


GESTURE_REPLY = {
    "English": {
        "Thumb_Up": "Got it! ✅",
        "Thumb_Down": "Let me explain that again, more simply.",
        "Pointing_Up": "Go ahead, ask your question.",
        "Open_Palm": "Okay, I'll wait. ✋",
        "Peace": "Peace! ✌️ Ready when you are.",
        "OK": "Perfect! 👌 Ask away.",
        "Rock_On": "Rock on! 🤘 Let's solve some maths.",
        "Call_Me": "Call me anytime — ask your question! 🤙",
        "ILY": "Love it! 🤟 Let's get to work.",
        "Vulcan": "Live long and learn! 🖖",
        "Crossed_Fingers": "Fingers crossed! 🤞",
        "Shaka": "Hang loose! 🤙",
        "Fist": "Ready! 💪 Ask me something.",
        "Heart_Hands": "❤️ Sending love back!",
        "Raised_Fist": "Let's do this! ✊",
        "Middle_Finger": "That's not very nice 😅 — but I'll still help.",
        "Pinched_Fingers": "Chef's kiss! 🤌",
    },
    "Hindi": {
        "Thumb_Up": "बढ़िया! ✅", "Thumb_Down": "और आसान तरीके से समझाता हूँ।",
        "Pointing_Up": "पूछिए।", "Open_Palm": "ठीक है, रुकता हूँ। ✋",
        "Peace": "शांति! ✌️", "OK": "बहुत बढ़िया! 👌", "Rock_On": "चलो शुरू करें! 🤘",
        "ILY": "प्यार! 🤟", "Shaka": "हैंग लूज़! 🤙",
    },
    "Arabic": {
        "Thumb_Up": "رائع! ✅", "Thumb_Down": "سأشرح أبسط.",
        "Pointing_Up": "تفضّل.", "Open_Palm": "حسناً. ✋",
        "Peace": "سلام! ✌️", "OK": "ممتاز! 👌", "Rock_On": "هيا! 🤘",
    },
    "French": {
        "Thumb_Up": "Super ! ✅", "Thumb_Down": "Je réexplique plus simplement.",
        "Pointing_Up": "Allez-y.", "Open_Palm": "D'accord. ✋",
        "Peace": "Peace ! ✌️", "OK": "Parfait ! 👌", "Rock_On": "C'est parti ! 🤘",
    },
}


# ---------------- voice in ----------------
def transcribe(audio_bytes: bytes, language_code=None):
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return "", None
    try:
        from groq import Groq
        kwargs = dict(file=("question.wav", audio_bytes), model="whisper-large-v3-turbo",
                      response_format="verbose_json")
        if language_code:
            kwargs["language"] = language_code
        r = Groq(api_key=key).audio.transcriptions.create(**kwargs)
        lang = WHISPER_NAMES.get(str(getattr(r, "language", "") or "").lower())
        return (r.text or "").strip(), lang
    except Exception as e:
        print("VOICE ERROR:", e)
        return "", None


# ---------------- voice out ----------------
_GTTS_LANG = {
    "en": "en", "english": "en",
    "hi": "hi", "hindi": "hi",
    "ar": "ar", "arabic": "ar",
    "fr": "fr", "french": "fr",
}


def speak(text: str, code: str):
    clean = re.sub(r"[`*#_>]", "", text or "")
    clean = re.sub(r"\s+", " ", clean).strip()[:1000]
    if not clean:
        return None
    target = _GTTS_LANG.get((code or "").lower(), "en")

    def _synth(lang_tag):
        from gtts import gTTS
        buf = io.BytesIO()
        gTTS(clean, lang=lang_tag).write_to_fp(buf)
        return buf.getvalue()

    try:
        return _synth(target)
    except Exception as e:
        print("SPEAK ERROR:", e)
        if target != "en":
            try:
                return _synth("en")
            except Exception as e2:
                print("SPEAK FALLBACK ERROR:", e2)
        return None


# ---------------- gesture recognition ----------------
MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/gesture_recognizer/"
             "gesture_recognizer/float16/1/gesture_recognizer.task")
MODEL_PATH = "gesture_recognizer.task"


def _gesture_with_gemini(image_bytes: bytes):
    """Use Gemini to recognise both MediaPipe gestures AND Gen-Z signs."""
    from langchain_core.messages import HumanMessage, SystemMessage
    from app.llm import _get_model, _content, _text
    model = _get_model(vision=True)
    if model is None:
        return None, "Add GOOGLE_API_KEY to .env, or install mediapipe."

    allowed = [
        "Thumb_Up", "Thumb_Down", "Pointing_Up", "Open_Palm",
        "Peace", "OK", "Rock_On", "Call_Me", "ILY", "Vulcan",
        "Crossed_Fingers", "Shaka", "Fist", "Heart_Hands",
        "Raised_Fist", "Middle_Finger", "Pinched_Fingers",
    ]
    prompt = (
        "Look at the photo of a person's hand(s). Identify the single hand gesture. "
        "Reply with exactly one word from this list and nothing else: "
        + ", ".join(allowed) + ", None. "
        "Use None if no clear gesture is visible. "
        "Notes: 'ILY' is the sign-language I-love-you (thumb, index, pinky extended). "
        "'Rock_On' is index and pinky extended. 'Shaka' is thumb and pinky extended. "
        "'Vulcan' is the Star Trek split-finger salute. 'OK' is thumb and index forming a circle. "
        "'Heart_Hands' is both hands forming a heart shape. 'Call_Me' is thumb and pinky out."
    )
    try:
        msgs = [SystemMessage(content=prompt),
                HumanMessage(content=_content("Which gesture is this?", image_bytes, "image/jpeg"))]
        words = _text(model.invoke(msgs)).strip().split()
        word = words[0].strip(".,'\"") if words else "None"
        return ([(word, 0.0)] if word in allowed else []), None
    except Exception as e:
        print("GESTURE ERROR:", e)
        return None, "I couldn't reach the AI to read the gesture."


def recognise_gesture(image_bytes: bytes):
    """Try Gemini first (recognises Gen-Z signs). Fall back to MediaPipe for basics."""
    result, err = _gesture_with_gemini(image_bytes)
    if result:
        return result, None

    try:
        import mediapipe as mp
        import numpy as np
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision
        from PIL import Image
    except ImportError:
        return result, err

    try:
        if not os.path.exists(MODEL_PATH):
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        img = np.array(Image.open(io.BytesIO(image_bytes)).convert("RGB"))
        opts = vision.GestureRecognizerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=MODEL_PATH), num_hands=2)
        rec = vision.GestureRecognizer.create_from_options(opts)
        res = rec.recognize(mp.Image(image_format=mp.ImageFormat.SRGB, data=img))
        found = [(g[0].category_name, g[0].score) for g in res.gestures
                 if g and g[0].category_name != "None"]
        return found, None
    except Exception as e:
        print("GESTURE ERROR:", e)
        return None, "I couldn't process the camera image."