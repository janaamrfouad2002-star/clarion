"""mic.py - an in-browser voice recorder component for Streamlit.
Replaces st.audio_input and avoids its 'An error has occurred' toast."""
import streamlit.components.v1 as components


_MIC_HTML = """
<div id="mic-wrap">
  <button id="mic-btn" aria-label="Record">
    <svg id="icon-mic" viewBox="0 0 24 24" width="22" height="22" fill="white">
      <path d="M12 14a3 3 0 0 0 3-3V6a3 3 0 1 0-6 0v5a3 3 0 0 0 3 3z"/>
      <path d="M19 11a1 1 0 1 0-2 0 5 5 0 0 1-10 0 1 1 0 1 0-2 0 7 7 0 0 0 6 6.92V21H9a1 1 0 1 0 0 2h6a1 1 0 1 0 0-2h-2v-3.08A7 7 0 0 0 19 11z"/>
    </svg>
    <svg id="icon-stop" viewBox="0 0 24 24" width="18" height="18" fill="white" style="display:none">
      <rect x="6" y="6" width="12" height="12" rx="2"/>
    </svg>
  </button>
  <div id="mic-status">Click to speak</div>
  <div id="mic-timer">00:00</div>
</div>

<style>
  html, body { margin:0; padding:0; background: transparent; font-family: Inter, -apple-system, sans-serif; }
  #mic-wrap {
    display:flex; align-items:center; gap:10px;
    padding:10px 14px;
    border:1px solid #e2e8f0;
    background:#fff;
    border-radius:14px;
    box-shadow: 0 4px 14px -10px rgba(15,23,42,.2);
  }
  #mic-btn {
    width:44px; height:44px; border-radius:50%;
    border:none; cursor:pointer;
    background: linear-gradient(135deg,#6366f1,#a855f7);
    display:flex; align-items:center; justify-content:center;
    box-shadow: 0 8px 20px -8px rgba(99,102,241,.7);
    transition: transform .15s ease, filter .15s ease;
    position: relative;
  }
  #mic-btn:hover { transform: translateY(-1px); filter: brightness(1.05); }
  #mic-btn.recording {
    background: linear-gradient(135deg,#ef4444,#ec4899);
    animation: pulse 1.2s ease-in-out infinite;
  }
  @keyframes pulse {
    0%,100% { box-shadow: 0 0 0 0 rgba(239,68,68,.55); }
    70%     { box-shadow: 0 0 0 14px rgba(239,68,68,0); }
  }
  #mic-status { font-weight:600; color:#0f172a; font-size:.92rem; }
  #mic-timer  { color:#64748b; font-size:.82rem; margin-left:auto; font-variant-numeric: tabular-nums; }
</style>

<script>
const wrap   = document.getElementById("mic-wrap");
const btn    = document.getElementById("mic-btn");
const iconM  = document.getElementById("icon-mic");
const iconS  = document.getElementById("icon-stop");
const status = document.getElementById("mic-status");
const timer  = document.getElementById("mic-timer");

let recorder = null;
let chunks = [];
let stream = null;
let t0 = 0;
let tick = null;

function fmt(s) {
  const m = Math.floor(s / 60);
  const r = Math.floor(s % 60);
  return String(m).padStart(2,"0") + ":" + String(r).padStart(2,"0");
}

async function startRecording() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (e) {
    status.textContent = "Microphone permission denied";
    return;
  }
  chunks = [];
  recorder = new MediaRecorder(stream);
  recorder.ondataavailable = e => { if (e.data.size > 0) chunks.push(e.data); };
  recorder.onstop = () => {
    const blob = new Blob(chunks, { type: "audio/webm" });
    const reader = new FileReader();
    reader.onloadend = () => {
      // Strip the data URL prefix and send the base64 to Streamlit
      const b64 = reader.result.split(",")[1];
      if (window.Streamlit && Streamlit.setComponentValue) {
        Streamlit.setComponentValue(b64);
      } else if (window.parent && window.parent.postMessage) {
        window.parent.postMessage({ type: "streamlit:setComponentValue", value: b64 }, "*");
      }
    };
    reader.readAsDataURL(blob);
    if (stream) stream.getTracks().forEach(t => t.stop());
    clearInterval(tick);
    btn.classList.remove("recording");
    iconM.style.display = "";
    iconS.style.display = "none";
    status.textContent = "Sent!";
    timer.textContent = "00:00";
  };
  recorder.start();
  btn.classList.add("recording");
  iconM.style.display = "none";
  iconS.style.display = "";
  status.textContent = "Recording… click to stop";
  t0 = Date.now();
  tick = setInterval(() => {
    timer.textContent = fmt((Date.now() - t0) / 1000);
  }, 250);
}

function stopRecording() {
  if (recorder && recorder.state !== "inactive") {
    recorder.stop();
  }
}

btn.addEventListener("click", () => {
  if (recorder && recorder.state === "recording") {
    stopRecording();
  } else {
    startRecording();
  }
});
</script>
"""


def mic_recorder(key: str = "mic"):
    """Show an in-browser mic button. Returns base64 audio bytes (str) or None."""
    return components.html(_MIC_HTML, height=90)