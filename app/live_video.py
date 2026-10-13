"""live_video.py - server-side webcam capture with real-time gesture detection."""
import queue
import threading
import time

import streamlit as st

from app.extras import recognise_gesture


_GESTURE_QUEUE: "queue.Queue[str]" = queue.Queue(maxsize=16)
_CAPTURE_THREAD = None
_STOP_FLAG = threading.Event()
_LAST_PREVIEW_FRAME = {"bytes": None}
_LAST_RESULT = {"name": None, "t": 0.0}
_LOCK = threading.Lock()


def _open_camera(preferred_index: int | None = None):
    """Try to open a working camera. Returns (cap, index) or (None, None)."""
    import cv2
    candidates = []
    if preferred_index is not None:
        candidates.append(preferred_index)
    candidates.extend([0, 1, 2, 3])
    seen = set()
    for idx in candidates:
        if idx in seen:
            continue
        seen.add(idx)
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            # Try to read one frame to confirm
            ok, _ = cap.read()
            if ok:
                print(f"LIVE CAMERA: opened index {idx}")
                return cap, idx
        cap.release()
    return None, None


def _worker(preferred_index: int | None, cooldown: float, preview: bool):
    try:
        import cv2
    except ImportError:
        print("LIVE ERROR: opencv-python not installed")
        return

    cap, idx = _open_camera(preferred_index)
    if cap is None:
        print("LIVE ERROR: no working camera found")
        return

    last_rec_t = 0.0
    while not _STOP_FLAG.is_set():
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.05)
            continue

        h, w = frame.shape[:2]
        max_w = 480
        if w > max_w:
            scale = max_w / w
            frame_small = cv2.resize(frame, (max_w, int(h * scale)))
        else:
            frame_small = frame

        if preview:
            ok2, buf = cv2.imencode(".jpg", frame_small, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            if ok2:
                with _LOCK:
                    _LAST_PREVIEW_FRAME["bytes"] = buf.tobytes()

        now = time.time()
        if now - last_rec_t > cooldown:
            last_rec_t = now
            # Quick check: is the frame bright enough that a hand might be visible?
            try:
                import numpy as np
                gray = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)
                if gray.mean() > 30:   # skip pitch-black frames
                    ok3, buf3 = cv2.imencode(
                        ".jpg", frame_small,
                        [int(cv2.IMWRITE_JPEG_QUALITY), 70],
                    )
                    if ok3:
                        data = buf3.tobytes()
                        try:
                            gestures, err = recognise_gesture(data)
                            if gestures:
                                name = gestures[0][0]
                                with _LOCK:
                                    if name != _LAST_RESULT["name"]:
                                        _LAST_RESULT["name"] = name
                                        _LAST_RESULT["t"] = now
                                        try:
                                            _GESTURE_QUEUE.put_nowait(name)
                                        except queue.Full:
                                            pass
                        except Exception as e:
                            print("LIVE RECOGNITION ERROR:", e)
            except Exception as e:
                print("LIVE LOOP ERROR:", e)

        time.sleep(0.05)

    cap.release()
    print("LIVE CAMERA: released")


def start_live_camera(camera_index: int | None = None, cooldown: float = 3.5,
                      preview: bool = True):
    global _CAPTURE_THREAD
    if _CAPTURE_THREAD and _CAPTURE_THREAD.is_alive():
        return
    _STOP_FLAG.clear()
    _CAPTURE_THREAD = threading.Thread(
        target=_worker, args=(camera_index, cooldown, preview), daemon=True
    )
    _CAPTURE_THREAD.start()


def stop_live_camera():
    _STOP_FLAG.set()


def is_running() -> bool:
    return bool(_CAPTURE_THREAD and _CAPTURE_THREAD.is_alive())


def pop_gesture():
    try:
        return _GESTURE_QUEUE.get_nowait()
    except queue.Empty:
        return None


def latest_preview_frame():
    with _LOCK:
        return _LAST_PREVIEW_FRAME["bytes"]


def render_live_video(key: str = "live_cam", camera_index: int | None = None,
                      cooldown: float = 3.5):
    st.caption("🎥 Live camera — make a hand sign, hold it for 1–2 seconds.")

    running = is_running()
    c1, c2 = st.columns(2)
    with c1:
        if not running and st.button("▶️ Start camera", key=f"{key}_start",
                                     use_container_width=True):
            start_live_camera(camera_index=camera_index, cooldown=cooldown, preview=True)
            st.rerun()
    with c2:
        if running and st.button("⏹️ Stop camera", key=f"{key}_stop",
                                 use_container_width=True):
            stop_live_camera()
            st.rerun()

    if running:
        frame = latest_preview_frame()
        if frame:
            st.image(frame, channels="BGR", width=280)
        else:
            st.info("Starting camera…")

        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=1200, key=f"{key}_refresh")