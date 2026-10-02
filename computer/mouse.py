"""
Mouse automation module for Windows.
Provides robust cursor positioning, clicking, scrolling, and dragging.
"""

import time
import pyautogui
from typing import Tuple, Optional
from config.settings import settings

# Configure PyAutoGUI safeguards
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05


class MouseController:
    def __init__(self):
        self.default_duration = settings.MOUSE_MOVE_DURATION

    def get_position(self) -> Tuple[int, int]:
        """Returns current mouse cursor coordinates (x, y)."""
        x, y = pyautogui.position()
        return int(x), int(y)

    def move_to(self, x: int, y: int, duration: Optional[float] = None) -> bool:
        """Moves cursor to (x, y) coordinates with smooth interpolation."""
        d = self.default_duration if duration is None else duration
        pyautogui.moveTo(x, y, duration=d)
        return True

    def click(self, x: Optional[int] = None, y: Optional[int] = None, button: str = "left") -> bool:
        """Clicks at coordinates or at the current mouse position."""
        if x is not None and y is not None:
            self.move_to(x, y)
        pyautogui.click(button=button)
        return True

    def double_click(self, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        """Double clicks at coordinates or current position."""
        if x is not None and y is not None:
            self.move_to(x, y)
        pyautogui.doubleClick()
        return True

    def right_click(self, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        """Right clicks at coordinates or current position."""
        return self.click(x, y, button="right")

    def drag_to(self, x: int, y: int, duration: float = 0.5) -> bool:
        """Drags mouse to (x, y)."""
        pyautogui.dragTo(x, y, duration=duration, button="left")
        return True

    def scroll(self, clicks: int) -> bool:
        """
        Scrolls vertically. Positive clicks scroll UP, negative clicks scroll DOWN.
        """
        pyautogui.scroll(clicks)
        return True

    def scroll_up(self, amount: int = 5) -> bool:
        """Scrolls up by specified amount."""
        return self.scroll(amount * 100)

    def scroll_down(self, amount: int = 5) -> bool:
        """Scrolls down by specified amount."""
        return self.scroll(-amount * 100)


mouse = MouseController()
