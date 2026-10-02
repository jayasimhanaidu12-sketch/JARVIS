"""
UI detector for locating interactable elements on screen.
Finds buttons, text boxes, and links without relying on hardcoded static coordinates.
"""

from typing import Optional, Tuple, List
from core.context import UIElementReference
from vision.screen_parser import screen_parser


class UIDetector:
    def find_button(self, label: str) -> Optional[Tuple[int, int]]:
        """Finds a button by its text and returns (center_x, center_y)."""
        window_info = screen_parser.inspect_active_window()
        controls = window_info.get("controls", [])
        label_lower = label.lower()

        for c in controls:
            if c.element_type == "button" and label_lower in c.text.lower():
                left, top, right, bottom = c.bounds
                return (left + right) // 2, (top + bottom) // 2

        return None

    def find_input_field(self, placeholder_or_name: str = "") -> Optional[Tuple[int, int]]:
        """Finds an input/edit box and returns its center coordinates."""
        window_info = screen_parser.inspect_active_window()
        controls = window_info.get("controls", [])
        query_lower = placeholder_or_name.lower()

        for c in controls:
            if c.element_type == "input":
                if not placeholder_or_name or query_lower in c.name.lower() or query_lower in c.text.lower():
                    left, top, right, bottom = c.bounds
                    return (left + right) // 2, (top + bottom) // 2

        return None

    def get_window_center(self) -> Tuple[int, int]:
        """Returns the center coordinates of the active window."""
        window_info = screen_parser.inspect_active_window()
        rect = window_info.get("rect", (0, 0, 1920, 1080))
        left, top, right, bottom = rect
        return (left + right) // 2, (top + bottom) // 2


ui_detector = UIDetector()
