"""
ADB (Android Debug Bridge) bridge and device manager.
Provides connection handling, device discovery, shell execution, and simulator fallback.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
from config.settings import settings


class ADBManager:
    def __init__(self):
        self.adb_bin = self._find_adb_binary()
        self.active_device_id: Optional[str] = settings.ANDROID_DEVICE_ID or None
        self.is_simulator_mode: bool = False

    def _find_adb_binary(self) -> str:
        """Finds adb executable from config, PATH, or standard Android SDK directories."""
        if settings.ADB_PATH and shutil.which(settings.ADB_PATH):
            return settings.ADB_PATH

        standard_locations = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk" / "platform-tools" / "adb.exe",
            Path(os.environ.get("PROGRAMFILES", "")) / "Android" / "platform-tools" / "adb.exe",
            Path.home() / "AppData" / "Local" / "Android" / "Sdk" / "platform-tools" / "adb.exe",
        ]
        for loc in standard_locations:
            if loc.is_file():
                return str(loc)

        return "adb"

    def is_adb_installed(self) -> bool:
        """Checks if ADB binary is reachable."""
        try:
            res = subprocess.run(
                [self.adb_bin, "version"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            return res.returncode == 0
        except Exception:
            return False

    def get_connected_devices(self) -> List[str]:
        """Returns list of connected Android device serial IDs."""
        if not self.is_adb_installed():
            return []

        try:
            res = subprocess.run(
                [self.adb_bin, "devices"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            devices = []
            for line in res.stdout.strip().splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 2 and parts[1] == "device":
                    devices.append(parts[0])
            return devices
        except Exception:
            return []

    def execute_shell(self, command: str) -> Tuple[bool, str]:
        """Executes an adb shell command on the target Android device."""
        devices = self.get_connected_devices()
        if not devices:
            # Enable graceful simulator fallback for testing/demo when hardware device is not attached
            self.is_simulator_mode = True
            return True, f"[SIMULATED PHONE]: Executed `shell {command}`"

        self.is_simulator_mode = False
        target = self.active_device_id or devices[0]
        cmd = [self.adb_bin, "-s", target, "shell"] + command.split()
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            return res.returncode == 0, res.stdout.strip()
        except Exception as e:
            return False, f"ADB shell execution error: {e}"


adb_manager = ADBManager()
