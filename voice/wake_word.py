"""
Wake word detection and activation controller for JARVIS.
Detects 'Jarvis' or 'Hey Jarvis' to activate the command listener.
"""

from typing import Tuple
from config.settings import settings


class WakeWordDetector:
    def __init__(self):
        self.wake_word = settings.WAKE_WORD.lower()

    def check_wake_word(self, speech_text: str) -> Tuple[bool, str]:
        """
        Checks if the utterance contains the wake word.
        Returns: (activated: bool, clean_command: str)
        Example: 'Hey Jarvis open Chrome' -> (True, 'open Chrome')
        """
        text = speech_text.strip().lower()

        prefixes = [
            f"hey {self.wake_word}",
            f"ok {self.wake_word}",
            f"okay {self.wake_word}",
            self.wake_word,
        ]

        for p in prefixes:
            if text.startswith(p):
                command = text[len(p):].strip(" ,.:;!?")
                return True, command

        # If wake word is anywhere in the string
        if self.wake_word in text:
            parts = text.split(self.wake_word, 1)
            command = parts[1].strip(" ,.:;!?")
            return True, command

        return False, speech_text


wake_detector = WakeWordDetector()
