"""
Browser controller for JARVIS.
Handles launching browsers, opening URLs, and tab management.
"""

import os
import time
import webbrowser
import subprocess
import shutil
from typing import Tuple, Optional
from config.settings import settings
from core.context import context
from computer.applications import app_manager
from computer.windows import windows_manager
from computer.keyboard import keyboard


class BrowserController:
    def __init__(self):
        self.default_browser = settings.DEFAULT_BROWSER
        self.chrome_path = self._find_browser_binary("chrome")
        self.edge_path = self._find_browser_binary("edge")

    def _find_browser_binary(self, browser_name: str) -> Optional[str]:
        """Locates the browser executable path on Windows."""
        candidate_paths = []
        if browser_name.lower() == "chrome":
            candidate_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            ]
        elif browser_name.lower() == "edge":
            candidate_paths = [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            ]

        for p in candidate_paths:
            if os.path.exists(p):
                return p
        return shutil.which(f"{browser_name}.exe") or shutil.which(browser_name)

    def open_browser(self, browser_name: Optional[str] = None, guest_mode: bool = True) -> Tuple[bool, str]:
        """Launches the requested browser and brings it to focus."""
        target = (browser_name or self.default_browser).lower()
        exe = self.chrome_path if target == "chrome" else (self.edge_path or "msedge.exe")
        cmd = [exe] if exe else [target]
        if guest_mode:
            cmd.append("--guest")

        try:
            subprocess.Popen(cmd, creationflags=subprocess.DETACHED_PROCESS if os.name == "nt" else 0)
            context.update_application_state(target)
            return True, f"Launched {target.capitalize()} in guest mode."
        except Exception:
            success, msg = app_manager.open_application(target)
            return success, msg

    def open_url(self, url: str, browser_name: Optional[str] = None, guest_mode: bool = True) -> Tuple[bool, str]:
        """
        Navigates to a URL. Opens in Guest Mode by default.
        Ensures scheme (https://) is present.
        """
        clean_url = url.strip()
        if not clean_url.startswith(("http://", "https://")):
            clean_url = f"https://{clean_url}"

        target = (browser_name or self.default_browser).lower()
        exe = self.chrome_path if target == "chrome" else self.edge_path

        if exe and os.path.exists(exe):
            cmd = [exe]
            if guest_mode:
                cmd.append("--guest")
            cmd.append(clean_url)
            try:
                subprocess.Popen(cmd, creationflags=subprocess.DETACHED_PROCESS if os.name == "nt" else 0)
                context.update_application_state(target)
                context.update_browser_state(clean_url)
                mode_str = " in guest mode" if guest_mode else ""
                return True, f"Opened {clean_url}{mode_str}"
            except Exception as e:
                print(f"Direct browser launch failed: {e}")

        # Fallback to webbrowser standard library
        try:
            webbrowser.open(clean_url)
            context.update_browser_state(clean_url)
            return True, f"Navigated to {clean_url}"
        except Exception as e:
            return False, f"Failed to open URL {clean_url}: {e}"

    def new_tab(self) -> bool:
        """Opens a new browser tab with Ctrl+T."""
        return keyboard.hotkey("ctrl", "t")

    def close_tab(self) -> bool:
        """Closes the current browser tab with Ctrl+W."""
        return keyboard.hotkey("ctrl", "w")

    def switch_tab(self, next_tab: bool = True) -> bool:
        """Cycles browser tabs with Ctrl+Tab or Ctrl+Shift+Tab."""
        if next_tab:
            return keyboard.hotkey("ctrl", "tab")
        else:
            return keyboard.hotkey("ctrl", "shift", "tab")


browser_controller = BrowserController()
