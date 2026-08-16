# Virtual Mouse Control using Hand Gestures

Real-time hand-gesture control of your mouse, system volume, and screen
brightness using **MediaPipe + OpenCV + PyAutoGUI**. Windows build.

Two-hand design:

- **Right hand → mouse** (move, click, scroll, drag, screenshot)
- **Left hand → system** (volume / brightness)

## Setup (Windows)

```powershell
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Use Python **3.11** — verified on 3.11.5. MediaPipe 0.10.14 publishes no
distribution for Python 3.13 (pip there offers only 0.10.30+), so a plain
`python -m venv` fails at install time if your default Python is newer. List
your versions with `py -0p`, and confirm `python --version` reads 3.11.x
inside the venv.

Press **`q`** in the camera window to quit, or **`Esc`** anywhere (global panic
key — works even when the window has lost focus).

## Gesture map

### Right hand (mouse)

| Gesture | Action |
|---|---|
| Index finger up (middle down) | Move cursor |
| Quick thumb + index pinch | Left click |
| Thumb + middle pinch | Right click |
| Thumb + ring pinch | Double click |
| Thumb + index pinch *held* | Click-and-drag (release to drop) |
| Peace sign (index + middle up), move hand up/down | Scroll |
| Fist (all fingers down) | Screenshot → `gesture_screenshot.png` |
| Open palm | Neutral — reposition without moving cursor |

### Left hand (system)

| Gesture | Action |
|---|---|
| Thumb + index apart/together, **middle down** | Volume 0–100% |
| Thumb + index apart/together, **middle up** | Brightness 0–100% |

(Raising the middle finger flips the pinch from volume to brightness.)

You can use both hands at once — steer the cursor with your right hand while
your left hand rides the volume.

## Project layout

```
gesture-mouse/
├── .gitignore
├── README.md
├── main.py                 # camera loop + on-screen HUD
├── requirements.txt
└── src/
    ├── __init__.py
    ├── config.py           # every tunable knob (thresholds, smoothing, cooldowns)
    ├── hand_tracker.py     # MediaPipe wrapper -> clean Hand objects
    ├── controllers.py      # mouse / volume / brightness system actions (Windows)
    └── gestures.py         # gesture recognition + state machine
```

## Tuning (edit `src/config.py`)

- **Cursor too jittery / laggy** → adjust `SMOOTHING` (higher = smoother, laggier).
- **Clicks not registering** → raise `PINCH_THRESHOLD`; too many accidental clicks → lower it.
- **Hands come out backwards** → toggle `SWAP_HANDEDNESS`.
- **Camera won't open / wrong camera** → change `CAM_INDEX`, or set
  `CAM_BACKEND = "msmf"` if `"dshow"` fails.
- **Thumb misreads as up/down** → adjust `THUMB_MARGIN`.
- **Scroll too fast** → lower `SCROLL_SENSITIVITY` or `SCROLL_MAX_STEP`.
- **Have to reach too far** → shrink `FRAME_MARGIN`.
- **Volume/brightness range feels off** → tune `CONTROL_MIN_DIST` / `CONTROL_MAX_DIST`.

## Adding your own gestures

1. Read finger state with `hand.fingers_up()` → `[thumb, index, middle, ring, pinky]`.
2. Measure distances with `hand.dist(A_TIP, B_TIP)` (normalised, resolution-independent).
3. Add a branch in `GestureEngine.handle_mouse_hand` (or `handle_system_hand`)
   and call a method on the relevant controller.

The engine already handles smoothing, cooldowns, and the drag latch, so new
gestures stay a few lines.

## Notes & gotchas

- **Brightness** works on laptop panels; many external monitors ignore software brightness.
- **Volume** uses `pycaw` (Windows-only). For macOS/Linux, rewrite only
  `controllers.py` (`osascript` / `pactl`) — the rest is platform-agnostic.
- `pyautogui.FAILSAFE` is disabled so gestures don't accidentally trip the
  corner kill-switch. Stop it with **`q`** in the window, or **`Esc`** anywhere.
- Good, even lighting and a plain background dramatically improve tracking.
