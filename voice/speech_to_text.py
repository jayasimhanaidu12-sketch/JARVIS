"""
Speech-to-Text (STT) module for JARVIS.
Captures live audio from microphone via sounddevice, bridges to SpeechRecognition/Whisper,
and provides seamless text input fallback.
"""

import time
import numpy as np
from typing import Optional
from config.settings import settings
from core.permissions import permission_manager

try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False

try:
    import speech_recognition as sr
    HAS_SR = True
except ImportError:
    HAS_SR = False


class SpeechToText:
    def __init__(self):
        self.sample_rate = 16000
        self.recognizer = sr.Recognizer() if HAS_SR else None

    def listen_from_mic(self, duration_seconds: float = 4.5) -> Optional[str]:
        """
        Records from default microphone for specified duration using sounddevice,
        then transcribes to text via speech recognizer.
        """
        if not HAS_SOUNDDEVICE or not HAS_SR:
            print("[STT Info]: Audio libraries not fully present, using text input.")
            return None

        if permission_manager.is_emergency_stopped:
            return None

        try:
            print(f"\n[LISTENING for {duration_seconds}s]...")
            # Record 16-bit PCM Mono at 16kHz
            num_samples = int(self.sample_rate * duration_seconds)
            recording = sd.rec(
                num_samples,
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16",
            )
            sd.wait()

            # Check if recorded audio has sufficient volume (noise gate)
            rms = np.sqrt(np.mean(recording.astype(np.float32) ** 2))
            if rms < 60:  # Threshold for silence
                return None

            print("[PROCESSING SPEECH]...")
            raw_bytes = recording.tobytes()
            audio_data = sr.AudioData(raw_bytes, self.sample_rate, 2)

            # Transcribe
            text = self.recognizer.recognize_google(
                audio_data,
                language=settings.STT_LANGUAGE,
            )
            print(f"[HEARD]: \"{text}\"")
            return text.strip()

        except sr.UnknownValueError:
            return None
        except Exception as e:
            # Silence or connection failure
            return None

    def prompt_command(self, use_voice: bool = True) -> str:
        """
        Gets next command either from microphone or terminal input.
        """
        if use_voice and HAS_SOUNDDEVICE and HAS_SR:
            heard = self.listen_from_mic()
            if heard:
                return heard

        # Fallback to terminal input
        try:
            cmd = input("\n[USER]: Enter command for JARVIS: ").strip()
            return cmd
        except (KeyboardInterrupt, EOFError):
            return "JARVIS STOP"


stt = SpeechToText()
