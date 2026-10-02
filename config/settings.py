"""
Configuration and settings management for JARVIS.
Loads from environment variables and provides centralized access.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Automatically load .env if present
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")


class Settings:
    # App Information
    APP_NAME: str = "JARVIS"
    VERSION: str = "1.0.0"
    WORKSPACE_DIR: Path = ROOT_DIR

    # User Profile
    USER_NAME: str = os.getenv("USER_NAME", "Gudise Jayasimha Naidu")

    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "auto")  # auto, openai, gemini, ollama, local
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")

    # Voice Settings
    VOICE_ENABLED: bool = os.getenv("VOICE_ENABLED", "true").lower() in ("true", "1", "yes")
    STT_ENGINE: str = os.getenv("STT_ENGINE", "google")  # google, whisper, local
    STT_LANGUAGE: str = os.getenv("STT_LANGUAGE", "en-US")
    TTS_ENGINE: str = os.getenv("TTS_ENGINE", "edge-tts")  # edge-tts (natural neural), pyttsx3 (offline fallback)
    TTS_NATURAL_VOICE: str = os.getenv("TTS_NATURAL_VOICE", "en-GB-RyanNeural")  # en-GB-RyanNeural (natural JARVIS)
    TTS_RATE: int = int(os.getenv("TTS_RATE", "185"))  # Natural speech speed
    TTS_VOLUME: float = float(os.getenv("TTS_VOLUME", "0.95"))
    TTS_VOICE_INDEX: int = int(os.getenv("TTS_VOICE_INDEX", "0"))
    WAKE_WORD: str = os.getenv("WAKE_WORD", "jarvis").lower()
    CONTINUOUS_LISTENING: bool = os.getenv("CONTINUOUS_LISTENING", "false").lower() in ("true", "1", "yes")

    # Safety & Permissions
    REQUIRE_CONFIRMATION_HIGH_RISK: bool = os.getenv("REQUIRE_CONFIRMATION", "true").lower() in ("true", "1", "yes")
    SAFETY_LEVEL: str = os.getenv("SAFETY_LEVEL", "strict")  # strict, balanced, relaxed
    AUTO_RECOVERY_RETRIES: int = int(os.getenv("AUTO_RECOVERY_RETRIES", "2"))

    # Computer Control Settings
    MOUSE_MOVE_DURATION: float = float(os.getenv("MOUSE_MOVE_DURATION", "0.2"))
    TYPE_INTERVAL: float = float(os.getenv("TYPE_INTERVAL", "0.02"))
    DEFAULT_BROWSER: str = os.getenv("DEFAULT_BROWSER", "chrome")  # chrome, edge, default

    # Android Mobile Settings
    ADB_PATH: str = os.getenv("ADB_PATH", "adb")
    ANDROID_DEVICE_ID: str = os.getenv("ANDROID_DEVICE_ID", "")
    ENABLE_MOBILE_SIMULATOR_FALLBACK: bool = True

    # Directories
    LOGS_DIR: Path = ROOT_DIR / "logs"
    SCREENSHOTS_DIR: Path = ROOT_DIR / "screenshots"


settings = Settings()
settings.LOGS_DIR.mkdir(exist_ok=True)
settings.SCREENSHOTS_DIR.mkdir(exist_ok=True)
