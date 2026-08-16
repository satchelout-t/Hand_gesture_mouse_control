"""Thin wrapper over MediaPipe Hands that returns easy-to-use Hand objects."""

import math
from dataclasses import dataclass, field

import cv2
import mediapipe as mp

from . import config

# Landmark index constants (MediaPipe hand model)
WRIST = 0
THUMB_MCP = 2
THUMB_TIP = 4
INDEX_TIP = 8
MIDDLE_MCP = 9
MIDDLE_TIP = 12
RING_TIP = 16
PINKY_TIP = 20

FINGER_TIPS = [THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP]
FINGER_PIPS = [3, 6, 10, 14, 18]  # joint below each tip (2 down)


@dataclass
class Hand:
    """One detected hand. Coordinates come in two flavours:

    - `lm`   : normalised (0..1) landmarks  -> [(x, y, z), ...]  (resolution independent)
    - `px`   : pixel landmarks              -> [(x, y), ...]     (for drawing)
    """
    label: str                       # "Left" or "Right" (already corrected for mirror)
    lm: list = field(default_factory=list)
    px: list = field(default_factory=list)

    # ---- finger state ----
    def fingers_up(self):
        """Return [thumb, index, middle, ring, pinky] as 1 (up) / 0 (down)."""
        up = []
        # Thumb bends sideways, so it needs an x-comparison rather than the
        # y-test used below. Measure against the MCP joint (long, stable
        # baseline) instead of the adjacent IP joint, and require a margin
        # proportional to hand size so the reading holds at any camera distance.
        scale = self.dist(WRIST, MIDDLE_MCP) or 1e-6
        margin = config.THUMB_MARGIN * scale
        dx = self.lm[THUMB_TIP][0] - self.lm[THUMB_MCP][0]
        # Mirrored frame, palm toward camera: an extended right thumb points to
        # image-right (+x), an extended left thumb to image-left (-x).
        extended = dx > margin if self.label == "Right" else dx < -margin
        up.append(1 if extended else 0)
        # Other four: tip is above (smaller y) than its PIP joint -> finger up.
        for tip, pip in zip(FINGER_TIPS[1:], FINGER_PIPS[1:]):
            up.append(1 if self.lm[tip][1] < self.lm[pip][1] else 0)
        return up

    # ---- geometry helpers (normalised, resolution-independent) ----
    def dist(self, a, b):
        ax, ay = self.lm[a][0], self.lm[a][1]
        bx, by = self.lm[b][0], self.lm[b][1]
        return math.hypot(ax - bx, ay - by)

    def tip_px(self, idx):
        return self.px[idx]


class HandTracker:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            max_num_hands=config.MAX_HANDS,
            min_detection_confidence=config.DETECTION_CONFIDENCE,
            min_tracking_confidence=config.TRACKING_CONFIDENCE,
        )

    def process(self, frame_bgr):
        """Detect hands in a BGR frame. Returns (list_of_Hand, raw_results)."""
        h, w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self.hands.process(rgb)

        hands_out = []
        if results.multi_hand_landmarks:
            for lms, handed in zip(results.multi_hand_landmarks,
                                   results.multi_handedness):
                label = handed.classification[0].label  # "Left"/"Right"
                if config.SWAP_HANDEDNESS:
                    label = "Right" if label == "Left" else "Left"
                lm = [(p.x, p.y, p.z) for p in lms.landmark]
                px = [(int(p.x * w), int(p.y * h)) for p in lms.landmark]
                hands_out.append(Hand(label=label, lm=lm, px=px))
        return hands_out, results

    def draw(self, frame, results):
        if results.multi_hand_landmarks:
            for lms in results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    frame, lms, self.mp_hands.HAND_CONNECTIONS)

    def close(self):
        self.hands.close()
