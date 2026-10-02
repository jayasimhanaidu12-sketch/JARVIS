"""
Screen and UI hierarchy parser for Windows.
Inspects structured UI controls (buttons, inputs, labels, windows) using Win32 and accessibility APIs.
"""

from typing import List, Dict, Any, Optional, Tuple
from core.context import UIElementReference, context

try:
    import win32gui
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False


class ScreenParser:
    def inspect_active_window(self) -> Dict[str, Any]:
        """Gathers structured information about the currently focused window."""
        if not HAS_WIN32:
            return {"title": "Desktop", "rect": (0, 0, 1920, 1080), "controls": []}

        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd).strip() if hwnd else "Desktop"
        rect = win32gui.GetWindowRect(hwnd) if hwnd else (0, 0, 1920, 1080)

        controls = self.extract_window_controls(hwnd)
        return {
            "hwnd": hwnd,
            "title": title,
            "rect": rect,
            "controls": controls,
        }

    def extract_window_controls(self, parent_hwnd: int) -> List[UIElementReference]:
        """Enumerates child controls (buttons, edit boxes, combos) within a window."""
        controls: List[UIElementReference] = []
        if not HAS_WIN32 or not parent_hwnd:
            return controls

        def enum_child_proc(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                text = win32gui.GetWindowText(hwnd).strip()
                cls = win32gui.GetClassName(hwnd).lower()
                rect = win32gui.GetWindowRect(hwnd)

                elem_type = "control"
                if "button" in cls:
                    elem_type = "button"
                elif "edit" in cls or "input" in cls:
                    elem_type = "input"
                elif "static" in cls or "text" in cls:
                    elem_type = "label"
                elif "combo" in cls:
                    elem_type = "combobox"

                if text or elem_type in ("button", "input"):
                    controls.append(
                        UIElementReference(
                            name=text or cls,
                            element_type=elem_type,
                            bounds=rect,
                            text=text,
                            extra={"class": cls, "hwnd": hwnd},
                        )
                    )
            return True

        try:
            win32gui.EnumChildWindows(parent_hwnd, enum_child_proc, None)
        except Exception:
            pass

        return controls


screen_parser = ScreenParser()
