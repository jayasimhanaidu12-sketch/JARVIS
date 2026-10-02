"""
System control module for Windows.
Provides volume control, screenshots, battery/system info, and safe action execution.
"""

import os
import time
import ctypes
import platform
from datetime import datetime
from pathlib import Path
from typing import Tuple, Dict, Any
from config.settings import settings

# Windows Virtual-Key Codes for Multimedia
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002


class SystemController:
    def __init__(self):
        self.screenshots_dir = settings.SCREENSHOTS_DIR

    def _send_virtual_key(self, vk_code: int):
        """Dispatches an extended hardware key press & release to Windows user32."""
        try:
            ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
            time.sleep(0.02)
            ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
        except Exception as e:
            print(f"Error sending virtual key {vk_code}: {e}")

    def volume_up(self, steps: int = 5) -> Tuple[bool, str]:
        """Increases system volume by specified steps."""
        for _ in range(steps):
            self._send_virtual_key(VK_VOLUME_UP)
            time.sleep(0.04)
        return True, f"Increased volume by {steps * 2}%"

    def volume_down(self, steps: int = 5) -> Tuple[bool, str]:
        """Decreases system volume by specified steps."""
        for _ in range(steps):
            self._send_virtual_key(VK_VOLUME_DOWN)
            time.sleep(0.04)
        return True, f"Decreased volume by {steps * 2}%"

    def toggle_mute(self) -> Tuple[bool, str]:
        """Toggles system mute on/off."""
        self._send_virtual_key(VK_VOLUME_MUTE)
        return True, "Toggled system mute."

    def get_system_summary(self) -> Dict[str, Any]:
        """Returns overview of system hardware and OS status."""
        return {
            "os": f"{platform.system()} {platform.release()}",
            "hostname": platform.node(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }


system_controller = SystemController()
