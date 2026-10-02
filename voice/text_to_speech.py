"""
Text-to-Speech (TTS) module for JARVIS.
Provides high-fidelity, natural neural voice responses using edge-tts
with automatic offline fallback to pyttsx3, and immediate interrupt on Emergency Stop.
"""

import asyncio
import io
import queue
import threading
import time
from typing import Optional

from config.settings import settings
from core.permissions import permission_manager

try:
    import edge_tts
    import sounddevice as sd
    import soundfile as sf
    HAS_NATURAL_TTS = True
except ImportError:
    HAS_NATURAL_TTS = False

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False


class TextToSpeech:
    """
    JARVIS Voice Synthesis Engine.
    Primary: Microsoft Edge Neural Natural Voice (Studio-grade realistic human voice).
    Fallback: Local pyttsx3 SAPI5 engine for 100% offline operation.
    """

    def __init__(self):
        self.enabled = settings.VOICE_ENABLED
        self._speech_queue = queue.Queue()
        self._is_speaking = False
        self._stop_requested = False
        self._worker_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._pyttsx_engine = None

        if (HAS_NATURAL_TTS or HAS_PYTTSX3) and self.enabled:
            self._start_worker()

    def _start_worker(self):
        """Starts background speech worker thread."""
        self._worker_thread = threading.Thread(target=self._speech_loop, daemon=True)
        self._worker_thread.start()

    def _init_pyttsx(self):
        """Lazy-inits offline fallback pyttsx3 engine."""
        if not HAS_PYTTSX3 or self._pyttsx_engine is not None:
            return
        try:
            self._pyttsx_engine = pyttsx3.init()
            self._pyttsx_engine.setProperty("rate", settings.TTS_RATE)
            self._pyttsx_engine.setProperty("volume", settings.TTS_VOLUME)
            voices = self._pyttsx_engine.getProperty("voices")
            if voices and settings.TTS_VOICE_INDEX < len(voices):
                self._pyttsx_engine.setProperty("voice", voices[settings.TTS_VOICE_INDEX].id)
        except Exception as e:
            print(f"[TTS Fallback Init Warning]: {e}")

    def _play_natural(self, text: str) -> bool:
        """
        Synthesizes natural neural speech with edge-tts and plays via sounddevice.
        Returns True on success, False if network error or failure occurs.
        """
        if not HAS_NATURAL_TTS:
            return False

        try:
            voice_name = getattr(settings, "TTS_NATURAL_VOICE", "en-GB-RyanNeural")

            # Adjust speech rate percentage if desired (e.g., "+5%" or "-5%")
            rate_delta = int(getattr(settings, "TTS_RATE", 185) - 180)
            rate_str = f"{'+' if rate_delta >= 0 else ''}{rate_delta // 2}%"

            async def _synth():
                comm = edge_tts.Communicate(text, voice_name, rate=rate_str)
                buf = io.BytesIO()
                async for chunk in comm.stream():
                    if self._stop_requested or permission_manager.is_emergency_stopped:
                        return None
                    if chunk["type"] == "audio":
                        buf.write(chunk["data"])
                buf.seek(0)
                return buf

            loop = asyncio.new_event_loop()
            try:
                buf = loop.run_until_complete(_synth())
            finally:
                loop.close()

            if buf is None:
                return True  # Canceled by emergency stop

            data, samplerate = sf.read(buf, dtype="float32")
            if data.ndim == 1:
                data = data.reshape(-1, 1)
            sd.play(data, samplerate)

            # Wait for playback or cancellation
            while sd.get_stream().active:
                if self._stop_requested or permission_manager.is_emergency_stopped:
                    sd.stop()
                    return True
                time.sleep(0.04)

            return True
        except Exception:
            # Fall back to offline SAPI5 voice if edge-tts fails (e.g. offline)
            return False

    def _play_pyttsx3(self, text: str):
        """Fallback offline speech generation via pyttsx3."""
        if not HAS_PYTTSX3:
            return
        try:
            self._init_pyttsx()
            if self._pyttsx_engine:
                self._pyttsx_engine.say(text)
                self._pyttsx_engine.runAndWait()
        except Exception as e:
            print(f"[TTS pyttsx3 Error]: {e}")

    def _speech_loop(self):
        """Consumes speech queue on a dedicated thread to prevent blocking the agent."""
        while True:
            text = self._speech_queue.get()
            if text is None:
                break

            # If emergency stop was triggered, drop speech item
            if permission_manager.is_emergency_stopped or self._stop_requested:
                self._speech_queue.task_done()
                continue

            self._is_speaking = True
            self._stop_requested = False

            try:
                # Use natural neural voice if enabled
                prefer_natural = getattr(settings, "TTS_ENGINE", "edge-tts").lower() == "edge-tts"
                played = False
                if prefer_natural and HAS_NATURAL_TTS:
                    played = self._play_natural(text)

                if not played and not (self._stop_requested or permission_manager.is_emergency_stopped):
                    self._play_pyttsx3(text)
            except Exception as e:
                print(f"[TTS Output Error]: {e}")
            finally:
                self._is_speaking = False
                self._speech_queue.task_done()

    def speak(self, text: str, wait: bool = True):
        """
        Speaks text through audio speakers.
        Always prints to console as well for transcript clarity.
        """
        clean_text = text.strip()
        if not clean_text:
            return

        print(f"\n[JARVIS]: \"{clean_text}\"")

        if not self.enabled or not (HAS_NATURAL_TTS or HAS_PYTTSX3):
            return

        if permission_manager.is_emergency_stopped:
            return

        self._stop_requested = False
        self._speech_queue.put(clean_text)
        if wait:
            self._speech_queue.join()

    def stop_speaking(self):
        """Flushes remaining speech queue and stops active audio immediately."""
        self._stop_requested = True
        with self._lock:
            while not self._speech_queue.empty():
                try:
                    self._speech_queue.get_nowait()
                    self._speech_queue.task_done()
                except Exception:
                    break
        try:
            if HAS_NATURAL_TTS:
                sd.stop()
        except Exception:
            pass
        try:
            if self._pyttsx_engine:
                self._pyttsx_engine.stop()
        except Exception:
            pass


tts = TextToSpeech()
