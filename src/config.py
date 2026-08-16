"""Central place for every tunable knob. Adjust these to your camera / hands."""

# --- Camera ---
CAM_INDEX = 0            # change to 1 if you have multiple webcams
CAM_WIDTH = 640
CAM_HEIGHT = 480
FLIP_FRAME = True        # mirror the frame so movement feels natural
# Capture backend. "dshow" opens in <1s on Windows and honours the width/height
# above; the default "msmf" can take 5-10s and often ignores them.
CAM_BACKEND = "dshow"    # "dshow" | "msmf" | "auto"

# MediaPipe determines handedness assuming the input image is ALREADY mirrored
# (selfie view). FLIP_FRAME mirrors the frame *before* detection, so the
# "Left"/"Right" label already matches your real hands -- no swap needed.
# Set this to True only if you also set FLIP_FRAME = False.
SWAP_HANDEDNESS = False

# --- MediaPipe ---
MAX_HANDS = 2
DETECTION_CONFIDENCE = 0.7
TRACKING_CONFIDENCE = 0.6

# --- Cursor ---
# Region of the camera frame that maps to the whole screen. Shrinking the
# active area (a margin/"frame reduction") means you don't have to stretch
# your arm to the screen edges.
FRAME_MARGIN = 100       # pixels of dead border on each side
SMOOTHING = 5            # higher = smoother but laggier cursor (try 3-8)

# --- Finger state ---
# The thumb counts as extended only when its tip clears the MCP joint by this
# fraction of hand size. Scaling by hand size keeps it valid at any distance
# from the camera; the margin stops a half-curled thumb flickering up/down.
THUMB_MARGIN = 0.15

# --- Pinch thresholds (normalised: fraction of frame width) ---
# Distance between two fingertips below this counts as a "pinch".
PINCH_THRESHOLD = 0.05
DRAG_HOLD_FRAMES = 8     # frames a pinch must persist before it becomes a drag

# --- Cooldowns (seconds) so one gesture = one action, not 30 ---
CLICK_COOLDOWN = 0.4
SCREENSHOT_COOLDOWN = 1.5

# --- Scroll ---
SCROLL_SENSITIVITY = 40  # bigger = faster scrolling
SCROLL_DEADZONE = 0.015  # ignore tiny vertical jitter (fraction of height)
SCROLL_MAX_STEP = 5      # hard cap on wheel notches per frame (runaway guard)

# --- System control (left hand) ---
# Thumb-tip to index-tip distance range (normalised) mapped to 0-100%.
CONTROL_MIN_DIST = 0.03
CONTROL_MAX_DIST = 0.25
CONTROL_SMOOTHING = 3

# --- UI ---
SHOW_FPS = True
SHOW_LANDMARKS = True

# --- Safety ---
# Global panic key: works even when the camera window is NOT focused, which
# matters because gesture clicks can steal focus away from it. 0x1B = Esc.
PANIC_VK = 0x1B
