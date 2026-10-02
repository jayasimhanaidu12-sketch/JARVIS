"""
Window management module for Windows.
Handles window discovery, focusing, maximizing, minimizing, and closing.
"""

import time
import subprocess
from typing import List, Dict, Any, Optional
from core.context import context

try:
    import win32gui
    import win32con
    import win32process
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False


class WindowInfo:
    def __init__(self, hwnd: int, title: str, pid: int = 0, rect: tuple = (0, 0, 0, 0)):
        self.hwnd = hwnd
        self.title = title
        self.pid = pid
        self.rect = rect  # (left, top, right, bottom)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hwnd": self.hwnd,
            "title": self.title,
            "pid": self.pid,
            "rect": self.rect,
        }


class WindowsManager:
    def list_windows(self) -> List[WindowInfo]:
        """Returns all open, titled, visible top-level windows."""
        windows: List[WindowInfo] = []
        if not HAS_WIN32:
            return windows

        def enum_handler(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).strip()
                if title:
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        rect = win32gui.GetWindowRect(hwnd)
                        # Check that the window has non-zero area
                        if (rect[2] - rect[0] > 10) and (rect[3] - rect[1] > 10):
                            windows.append(WindowInfo(hwnd=hwnd, title=title, pid=pid, rect=rect))
                    except Exception:
                        pass
            return True

        try:
            win32gui.EnumWindows(enum_handler, None)
        except Exception:
            pass
        return windows

    def find_window(self, query: str) -> Optional[WindowInfo]:
        """Finds the best matching window by title substring (case-insensitive)."""
        query_lower = query.lower()
        windows = self.list_windows()
        for w in windows:
            if query_lower in w.title.lower():
                return w
        return None

    def focus_window(self, query_or_title: str) -> bool:
        """Brings the matching window to the foreground."""
        w = self.find_window(query_or_title)
        if not w:
            # If not found directly, try Alt+Tab or application switch
            return False

        try:
            # If minimized, restore it first
            if win32gui.IsIconic(w.hwnd):
                win32gui.ShowWindow(w.hwnd, win32con.SW_RESTORE)
            else:
                win32gui.ShowWindow(w.hwnd, win32con.SW_SHOW)

            win32gui.SetForegroundWindow(w.hwnd)
            time.sleep(0.15)
            context.update_application_state(w.title.split("-")[-1].strip(), w.title)
            return True
        except Exception:
            return False

    def minimize_window(self, query_or_title: str) -> bool:
        """Minimizes the specified window."""
        w = self.find_window(query_or_title)
        if w and HAS_WIN32:
            try:
                win32gui.ShowWindow(w.hwnd, win32con.SW_MINIMIZE)
                return True
            except Exception:
                return False
        return False

    def maximize_window(self, query_or_title: str) -> bool:
        """Maximizes the specified window."""
        w = self.find_window(query_or_title)
        if w and HAS_WIN32:
            try:
                win32gui.ShowWindow(w.hwnd, win32con.SW_MAXIMIZE)
                return True
            except Exception:
                return False
        return False

    def restore_window(self, query_or_title: str) -> bool:
        """Restores a minimized or maximized window to normal size."""
        w = self.find_window(query_or_title)
        if w and HAS_WIN32:
            try:
                win32gui.ShowWindow(w.hwnd, win32con.SW_RESTORE)
                return True
            except Exception:
                return False
        return False

    def close_window(self, query_or_title: str) -> bool:
        """Sends WM_CLOSE to cleanly close a window."""
        w = self.find_window(query_or_title)
        if w and HAS_WIN32:
            try:
                win32gui.PostMessage(w.hwnd, win32con.WM_CLOSE, 0, 0)
                return True
            except Exception:
                return False
        return False

    def get_active_window(self) -> Optional[WindowInfo]:
        """Returns details about the currently active foreground window."""
        if not HAS_WIN32:
            return None
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                title = win32gui.GetWindowText(hwnd).strip()
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                rect = win32gui.GetWindowRect(hwnd)
                return WindowInfo(hwnd=hwnd, title=title, pid=pid, rect=rect)
        except Exception:
            pass
        return None


windows_manager = WindowsManager()
