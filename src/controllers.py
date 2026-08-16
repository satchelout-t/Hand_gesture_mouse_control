"""Wrappers for the actual system actions (Windows).

Kept separate from gesture logic so you can swap platforms by rewriting
only this file (e.g. use `osascript` on macOS, `pactl` on Linux).
"""

import pyautogui

pyautogui.FAILSAFE = False   # gestures can fling the cursor to a corner; press 'q' to quit instead
pyautogui.PAUSE = 0          # no artificial delay between calls


class MouseController:
    def __init__(self):
        self.screen_w, self.screen_h = pyautogui.size()
        self.dragging = False

    def move(self, x, y):
        pyautogui.moveTo(x, y)

    def left_click(self):
        pyautogui.click()

    def right_click(self):
        pyautogui.click(button="right")

    def double_click(self):
        pyautogui.doubleClick()

    def scroll(self, amount):
        pyautogui.scroll(int(amount))

    def drag_start(self):
        if not self.dragging:
            pyautogui.mouseDown()
            self.dragging = True

    def drag_end(self):
        if self.dragging:
            pyautogui.mouseUp()
            self.dragging = False

    def screenshot(self, path="gesture_screenshot.png"):
        pyautogui.screenshot(path)
        return path


class VolumeController:
    """Windows master volume via pycaw."""

    def __init__(self):
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self._vol = cast(interface, POINTER(IAudioEndpointVolume))

    def set_percent(self, pct):
        """pct in 0..100 -> linear scalar 0.0..1.0."""
        pct = max(0.0, min(100.0, pct))
        self._vol.SetMasterVolumeLevelScalar(pct / 100.0, None)

    def get_percent(self):
        return self._vol.GetMasterVolumeLevelScalar() * 100.0


class BrightnessController:
    """Display brightness via screen_brightness_control (cross-platform, but
    laptop displays only)."""

    def __init__(self):
        import screen_brightness_control as sbc
        self._sbc = sbc

    def set_percent(self, pct):
        pct = int(max(0, min(100, pct)))
        try:
            self._sbc.set_brightness(pct)
        except Exception:
            pass  # some external monitors don't support software brightness

    def get_percent(self):
        try:
            val = self._sbc.get_brightness()
            return val[0] if isinstance(val, list) else val
        except Exception:
            return 0
