"""The brain: turns Hand objects into system actions.

Right hand  -> mouse (move / click / scroll / drag / screenshot)
Left  hand  -> system control (volume / brightness)

State (cooldowns, smoothing, drag latch) lives here so main.py stays a
clean loop.
"""

import time

import numpy as np

from . import config
from .hand_tracker import (
    THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP,
)


class GestureEngine:
    def __init__(self, mouse, volume=None, brightness=None):
        self.mouse = mouse
        self.volume = volume
        self.brightness = brightness

        # cursor smoothing memory
        self.prev_x, self.prev_y = None, None
        # cooldown timers
        self.last_click = 0.0
        self.last_screenshot = 0.0
        # drag latch
        self.pinch_frames = 0
        # scroll memory
        self.prev_scroll_y = None
        # system-control smoothing
        self.smooth_vol = None
        self.smooth_bri = None

        self.status = "idle"   # human-readable, drawn on screen

    # ---------------------------------------------------------------- helpers
    def _cooldown(self, last, gap):
        return (time.time() - last) > gap

    def _map_cursor(self, hand, cam_w, cam_h):
        ix, iy = hand.px[INDEX_TIP]
        m = config.FRAME_MARGIN
        sx = np.interp(ix, (m, cam_w - m), (0, self.mouse.screen_w))
        sy = np.interp(iy, (m, cam_h - m), (0, self.mouse.screen_h))
        # First frame: snap to the target. Otherwise the cursor sweeps in from
        # the top-left corner over the first ~20 frames.
        if self.prev_x is None:
            self.prev_x, self.prev_y = sx, sy
            return sx, sy
        # exponential smoothing
        cx = self.prev_x + (sx - self.prev_x) / config.SMOOTHING
        cy = self.prev_y + (sy - self.prev_y) / config.SMOOTHING
        self.prev_x, self.prev_y = cx, cy
        return cx, cy

    # ---------------------------------------------------------------- right hand
    def handle_mouse_hand(self, hand, cam_w, cam_h):
        fingers = hand.fingers_up()          # [thumb, index, middle, ring, pinky]
        thumb, index, middle, ring, pinky = fingers

        # --- SCREENSHOT: fist (all down) ---
        if fingers == [0, 0, 0, 0, 0]:
            self.mouse.drag_end()
            if self._cooldown(self.last_screenshot, config.SCREENSHOT_COOLDOWN):
                self.mouse.screenshot()
                self.last_screenshot = time.time()
            self.status = "screenshot"
            return

        # --- SCROLL: peace sign (index + middle up, others down) ---
        if index and middle and not ring and not pinky:
            self.mouse.drag_end()
            _, ny = hand.lm[INDEX_TIP][0], hand.lm[INDEX_TIP][1]
            if self.prev_scroll_y is not None:
                dy = self.prev_scroll_y - ny            # up = positive
                if abs(dy) > config.SCROLL_DEADZONE:
                    # dy is a *fraction* of frame height, so the old extra x20
                    # turned a 5% hand movement into 40 wheel notches.
                    step = dy * config.SCROLL_SENSITIVITY
                    step = max(-config.SCROLL_MAX_STEP,
                               min(config.SCROLL_MAX_STEP, step))
                    self.mouse.scroll(step)
            self.prev_scroll_y = ny
            self.status = "scroll"
            return
        self.prev_scroll_y = None

        # --- MOVE + CLICKS: index up, middle down ---
        if index and not middle:
            cx, cy = self._map_cursor(hand, cam_w, cam_h)

            d_index = hand.dist(THUMB_TIP, INDEX_TIP)
            d_middle = hand.dist(THUMB_TIP, MIDDLE_TIP)
            d_ring = hand.dist(THUMB_TIP, RING_TIP)

            # drag: sustained thumb-index pinch
            if d_index < config.PINCH_THRESHOLD:
                self.pinch_frames += 1
                if self.pinch_frames >= config.DRAG_HOLD_FRAMES:
                    self.mouse.drag_start()
                    self.mouse.move(cx, cy)
                    self.status = "drag"
                    return
            else:
                # quick pinch released before drag threshold -> left click
                if 0 < self.pinch_frames < config.DRAG_HOLD_FRAMES \
                        and self._cooldown(self.last_click, config.CLICK_COOLDOWN):
                    self.mouse.left_click()
                    self.last_click = time.time()
                    self.status = "left click"
                self.pinch_frames = 0
                self.mouse.drag_end()

            # right click: thumb-middle pinch
            if d_middle < config.PINCH_THRESHOLD \
                    and self._cooldown(self.last_click, config.CLICK_COOLDOWN):
                self.mouse.right_click()
                self.last_click = time.time()
                self.status = "right click"
            # double click: thumb-ring pinch
            elif d_ring < config.PINCH_THRESHOLD \
                    and self._cooldown(self.last_click, config.CLICK_COOLDOWN):
                self.mouse.double_click()
                self.last_click = time.time()
                self.status = "double click"

            self.mouse.move(cx, cy)
            if self.status not in ("drag",):
                self.status = self.status if time.time() - self.last_click < 0.3 else "move"
            return

        # open palm / anything else -> neutral (release drag, reposition freely)
        self.mouse.drag_end()
        self.pinch_frames = 0
        self.status = "neutral"

    # ---------------------------------------------------------------- left hand
    def handle_system_hand(self, hand):
        fingers = hand.fingers_up()
        thumb, index, middle, ring, pinky = fingers

        # need thumb + index extended to give a distance to read
        if not (thumb and index):
            self.status = "sys: idle"
            return

        raw = hand.dist(THUMB_TIP, INDEX_TIP)
        pct = np.interp(raw,
                        (config.CONTROL_MIN_DIST, config.CONTROL_MAX_DIST),
                        (0, 100))

        # middle finger UP -> brightness, DOWN -> volume
        if middle:
            if self.brightness:
                self.smooth_bri = pct if self.smooth_bri is None else \
                    self.smooth_bri + (pct - self.smooth_bri) / config.CONTROL_SMOOTHING
                self.brightness.set_percent(self.smooth_bri)
            self.status = f"brightness {int(pct)}%"
        else:
            if self.volume:
                self.smooth_vol = pct if self.smooth_vol is None else \
                    self.smooth_vol + (pct - self.smooth_vol) / config.CONTROL_SMOOTHING
                self.volume.set_percent(self.smooth_vol)
            self.status = f"volume {int(pct)}%"

    # ---------------------------------------------------------------- dispatch
    def update(self, hands, cam_w, cam_h):
        right = next((h for h in hands if h.label == "Right"), None)
        left = next((h for h in hands if h.label == "Left"), None)

        if right is not None:
            self.handle_mouse_hand(right, cam_w, cam_h)
        else:
            # no mouse hand present: make sure we aren't stuck mid-drag
            self.mouse.drag_end()

        if left is not None:
            self.handle_system_hand(left)

        if not hands:
            self.status = "no hands"
