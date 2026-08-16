"""Virtual Mouse Control using Hand Gestures.

Run:  python main.py
Quit: press 'q' in the camera window, or Esc anywhere (global panic key).
"""

import ctypes
import time

import cv2

from src import config
from src.hand_tracker import HandTracker
from src.controllers import MouseController, VolumeController, BrightnessController
from src.gestures import GestureEngine


def make_controllers():
    mouse = MouseController()
    volume = None
    brightness = None
    try:
        volume = VolumeController()
    except Exception as e:
        print(f"[warn] volume control unavailable: {e}")
    try:
        brightness = BrightnessController()
    except Exception as e:
        print(f"[warn] brightness control unavailable: {e}")
    return mouse, volume, brightness


def _backend_flag():
    return {"dshow": cv2.CAP_DSHOW,
            "msmf": cv2.CAP_MSMF}.get(config.CAM_BACKEND, cv2.CAP_ANY)


def panic_pressed():
    """Global Esc check. Unlike cv2.waitKey this fires even when the camera
    window has lost focus -- which happens as soon as a gesture click lands on
    another window, and is otherwise a dead end with FAILSAFE disabled."""
    try:
        return bool(ctypes.windll.user32.GetAsyncKeyState(config.PANIC_VK) & 0x8000)
    except AttributeError:
        return False          # non-Windows: fall back to 'q' in the window


def draw_hud(frame, engine, fps):
    h, w = frame.shape[:2]
    # active region rectangle (where your finger maps to the screen)
    m = config.FRAME_MARGIN
    cv2.rectangle(frame, (m, m), (w - m, h - m), (255, 120, 0), 2)
    cv2.rectangle(frame, (0, 0), (w, 34), (0, 0, 0), -1)
    cv2.putText(frame, f"{engine.status.upper()}", (10, 24),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 120), 2)
    if config.SHOW_FPS:
        cv2.putText(frame, f"{int(fps)} FPS", (w - 90, 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
    cv2.putText(frame, "q / Esc = quit", (10, h - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)


def main():
    cap = cv2.VideoCapture(config.CAM_INDEX, _backend_flag())
    if not cap.isOpened():
        raise SystemExit(
            f"[error] could not open camera {config.CAM_INDEX} via "
            f"'{config.CAM_BACKEND}'. Try another CAM_INDEX (1, 2, ...) or set "
            f"CAM_BACKEND = 'msmf' in src/config.py."
        )
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAM_HEIGHT)

    tracker = HandTracker()
    mouse, volume, brightness = make_controllers()
    engine = GestureEngine(mouse, volume, brightness)

    prev_t = time.time()
    print("Running. Press 'q' in the window, or Esc anywhere, to quit.")
    try:
        while True:
            if panic_pressed():
                print("[panic] Esc pressed - releasing mouse and exiting.")
                break
            ok, frame = cap.read()
            if not ok:
                print("[error] camera frame not received.")
                break
            if config.FLIP_FRAME:
                frame = cv2.flip(frame, 1)

            hands, results = tracker.process(frame)
            cam_h, cam_w = frame.shape[:2]
            engine.update(hands, cam_w, cam_h)

            if config.SHOW_LANDMARKS:
                tracker.draw(frame, results)

            now = time.time()
            fps = 1.0 / max(now - prev_t, 1e-6)
            prev_t = now
            draw_hud(frame, engine, fps)

            cv2.imshow("Gesture Mouse  (q to quit)", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        mouse.drag_end()
        cap.release()
        cv2.destroyAllWindows()
        tracker.close()


if __name__ == "__main__":
    main()
