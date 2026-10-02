"""
Android device automation controller for JARVIS.
Handles app launching, tapping, swiping, hardware keys, and screenshots via ADB.
"""

import time
from typing import Tuple, Optional
from core.context import context
from mobile.adb import adb_manager
from mobile.mobile_ui import mobile_ui

# Android KeyCodes
KEYCODE_HOME = 3
KEYCODE_BACK = 4
KEYCODE_VOLUME_UP = 24
KEYCODE_VOLUME_DOWN = 25
KEYCODE_MEDIA_PLAY_PAUSE = 85
KEYCODE_APP_SWITCH = 187  # Recents

# Common Android Package Names
ANDROID_PACKAGES = {
    "youtube": "com.google.android.youtube",
    "chrome": "com.android.chrome",
    "camera": "com.google.android.GoogleCamera",
    "settings": "com.android.settings",
    "calculator": "com.google.android.calculator",
    "maps": "com.google.android.apps.maps",
}


class AndroidController:
    def launch_app(self, app_name: str) -> Tuple[bool, str]:
        """Launches an Android application by name or package."""
        clean = app_name.lower().strip()
        pkg = ANDROID_PACKAGES.get(clean, app_name)

        cmd = f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1"
        success, out = adb_manager.execute_shell(cmd)
        if success:
            context.update_application_state(f"Android:{clean}")
            return True, f"Launched {app_name} on phone"
        return False, f"Failed to launch {app_name} on phone: {out}"

    def tap(self, x: int, y: int) -> Tuple[bool, str]:
        """Sends tap event at (x, y) coordinates."""
        cmd = f"input tap {x} {y}"
        success, out = adb_manager.execute_shell(cmd)
        return success, f"Tapped at ({x}, {y}) on phone"

    def tap_text(self, text: str) -> Tuple[bool, str]:
        """Finds element by visible text and taps its center."""
        elem = mobile_ui.find_element_by_text(text)
        if not elem:
            return False, f"Element with text '{text}' not found on phone screen."
        cx, cy = elem.center
        return self.tap(cx, cy)

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> Tuple[bool, str]:
        """Performs a touch swipe gesture."""
        cmd = f"input swipe {x1} {y1} {x2} {y2} {duration_ms}"
        success, _ = adb_manager.execute_shell(cmd)
        return success, f"Swiped on phone"

    def scroll_down(self) -> Tuple[bool, str]:
        """Scrolls down on phone screen."""
        return self.swipe(500, 1400, 500, 400, 350)

    def scroll_up(self) -> Tuple[bool, str]:
        """Scrolls up on phone screen."""
        return self.swipe(500, 400, 500, 1400, 350)

    def type_text(self, text: str) -> Tuple[bool, str]:
        """Types text on Android input field."""
        # Replace spaces with %s for adb input text
        safe_text = text.replace(" ", "%s")
        cmd = f"input text {safe_text}"
        success, _ = adb_manager.execute_shell(cmd)
        return success, f"Typed text on phone"

    def press_key(self, keycode: int) -> Tuple[bool, str]:
        """Sends keyevent to Android device."""
        cmd = f"input keyevent {keycode}"
        success, _ = adb_manager.execute_shell(cmd)
        return success, f"Sent keyevent {keycode} to phone"

    def press_home(self) -> Tuple[bool, str]:
        return self.press_key(KEYCODE_HOME)

    def press_back(self) -> Tuple[bool, str]:
        return self.press_key(KEYCODE_BACK)

    def press_recents(self) -> Tuple[bool, str]:
        return self.press_key(KEYCODE_APP_SWITCH)

    def volume_up(self) -> Tuple[bool, str]:
        return self.press_key(KEYCODE_VOLUME_UP)

    def volume_down(self) -> Tuple[bool, str]:
        return self.press_key(KEYCODE_VOLUME_DOWN)

    def play_pause_media(self) -> Tuple[bool, str]:
        return self.press_key(KEYCODE_MEDIA_PLAY_PAUSE)


android_controller = AndroidController()
