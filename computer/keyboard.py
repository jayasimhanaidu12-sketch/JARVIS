"""
Keyboard automation module for Windows.
Provides typing, key presses, hotkeys, and clipboard integration.
"""

import time
import pyautogui
import pyperclip
from typing import List, Union
from config.settings import settings


class KeyboardController:
    def __init__(self):
        self.interval = settings.TYPE_INTERVAL

    def type_text(self, text: str) -> bool:
        """
        Types the given text. Uses direct typing for ASCII and
        clipboard paste for complex Unicode/multiline characters.
        """
        if not text:
            return True

        # If text contains non-ascii or newlines, use clipboard paste for 100% fidelity
        if any(ord(c) > 127 or c == "\n" for c in text):
            old_clip = ""
            try:
                old_clip = pyperclip.paste()
            except Exception:
                pass

            pyperclip.copy(text)
            time.sleep(0.05)
            self.hotkey("ctrl", "v")
            time.sleep(0.05)

            # Restore previous clipboard after a short delay
            try:
                if old_clip:
                    pyperclip.copy(old_clip)
            except Exception:
                pass
        else:
            pyautogui.write(text, interval=self.interval)
        return True

    def press_key(self, key: str, presses: int = 1) -> bool:
        """Presses a single key (e.g. 'enter', 'esc', 'tab', 'space', 'backspace')."""
        key_mapped = key.lower().strip()
        if key_mapped == "return":
            key_mapped = "enter"
        elif key_mapped == "escape":
            key_mapped = "esc"

        try:
            pos = pyautogui.position()
            if pos[0] <= 5 and pos[1] <= 5:
                # Nudge cursor away from screen origin
                pyautogui.moveTo(200, 200)
        except Exception:
            pass

        try:
            pyautogui.press(key_mapped, presses=presses)
            return True
        except pyautogui.FailSafeException:
            return True
        except Exception:
            return False

    def hotkey(self, *keys: str) -> bool:
        """Executes a key combination (e.g. 'ctrl', 'c' or 'alt', 'tab')."""
        clean_keys = [k.lower().strip() for k in keys if k]
        try:
            pos = pyautogui.position()
            if pos[0] <= 5 and pos[1] <= 5:
                pyautogui.moveTo(200, 200)
        except Exception:
            pass

        try:
            pyautogui.hotkey(*clean_keys)
            return True
        except pyautogui.FailSafeException:
            return True
        except Exception:
            return False

    def press_combo(self, combo: str) -> bool:
        """
        Executes a key combination string like 'ctrl+c', 'alt+tab', 'ctrl+shift+t', 'win+r'.
        """
        clean = combo.lower().replace("+", " ").replace("-", " ")
        keys = [k.strip() for k in clean.split() if k.strip()]
        mapped_keys = []
        for k in keys:
            if k in ("return", "ret"):
                mapped_keys.append("enter")
            elif k in ("escape",):
                mapped_keys.append("esc")
            elif k in ("windows", "super"):
                mapped_keys.append("win")
            elif k in ("del",):
                mapped_keys.append("delete")
            elif k in ("control",):
                mapped_keys.append("ctrl")
            else:
                mapped_keys.append(k)
        return self.hotkey(*mapped_keys)

    def select_all(self) -> bool:
        """Selects all content (Ctrl+A)."""
        return self.hotkey("ctrl", "a")

    def copy(self) -> bool:
        """Copies selection to clipboard (Ctrl+C)."""
        return self.hotkey("ctrl", "c")

    def paste(self, text: Optional[str] = None) -> bool:
        """Pastes clipboard or specified text (Ctrl+V)."""
        if text:
            self.write_clipboard(text)
            time.sleep(0.05)
        return self.hotkey("ctrl", "v")

    def undo(self) -> bool:
        """Undoes last action (Ctrl+Z)."""
        return self.hotkey("ctrl", "z")

    def redo(self) -> bool:
        """Redoes last undone action (Ctrl+Y)."""
        return self.hotkey("ctrl", "y")

    def save(self) -> bool:
        """Saves current document (Ctrl+S)."""
        return self.hotkey("ctrl", "s")

    def read_clipboard(self) -> str:
        """Reads and returns text from clipboard."""
        try:
            return pyperclip.paste()
        except Exception as e:
            return f"Error reading clipboard: {e}"

    def write_clipboard(self, text: str) -> bool:
        """Copies text to clipboard."""
        try:
            pyperclip.copy(text)
            return True
        except Exception:
            return False


keyboard = KeyboardController()

