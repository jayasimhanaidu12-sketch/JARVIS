"""
Main entry point for JARVIS — Universal Voice-Controlled AI Agent.
Supports GUI Control Panel, CLI Interactive Terminal, Continuous Voice Loop, and Automated Self-Tests.
"""

import sys
import argparse
import time
from config.settings import settings
from core.agent import jarvis_agent
from voice.speech_to_text import stt
from voice.wake_word import wake_detector
from voice.text_to_speech import tts
from ui.dashboard import launch_dashboard
import sys

# Ensure UTF-8 output and handle pythonw.exe (no stdout) safely
if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
else:
    class DummyStream:
        def write(self, *args, **kwargs): pass
        def flush(self, *args, **kwargs): pass
    sys.stdout = DummyStream()
    sys.stderr = DummyStream()


def run_cli_mode():
    """Runs interactive terminal loop."""
    print("=" * 65)
    print("  J A R V I S — Universal Voice-Controlled AI Agent")
    print("  Mode: Interactive CLI | Type 'exit' or 'JARVIS STOP' to quit")
    print("=" * 65)

    tts.speak("JARVIS online and ready for your command, sir.")

    while True:
        try:
            cmd = input("\n👤 Command: ").strip()
            if not cmd:
                continue
            if cmd.lower() in ("exit", "quit", "q"):
                print("Exiting JARVIS...")
                tts.speak("Shutting down, sir.")
                break

            response = jarvis_agent.process_command(cmd)
        except (KeyboardInterrupt, EOFError):
            print("\nShutting down JARVIS.")
            tts.speak("Shutting down, sir.")
            break


def run_voice_continuous_mode():
    """Runs continuous background listening loop with wake word detection."""
    print("=" * 65)
    print("  J A R V I S — Continuous Voice Mode Active")
    print(f"  Say '{settings.WAKE_WORD.capitalize()}' or 'Hey {settings.WAKE_WORD.capitalize()}' followed by command.")
    print("  Say 'JARVIS STOP' anytime to abort.")
    print("=" * 65)

    tts.speak(f"Listening for wake word {settings.WAKE_WORD}, sir.")

    while True:
        try:
            heard = stt.listen_from_mic(duration_seconds=3.5)
            if not heard:
                continue

            activated, clean_cmd = wake_detector.check_wake_word(heard)
            if activated:
                if clean_cmd:
                    jarvis_agent.process_command(clean_cmd)
                else:
                    tts.speak("Yes? How can I assist you?")
                    follow_up = stt.listen_from_mic(duration_seconds=4.5)
                    if follow_up:
                        jarvis_agent.process_command(follow_up)
            elif "jarvis stop" in heard.lower() or heard.lower() == "stop":
                jarvis_agent.handle_emergency_stop()

        except KeyboardInterrupt:
            print("\nExiting voice mode.")
            break


def run_automated_tests():
    """Runs automated verification suite directly."""
    import unittest
    suite = unittest.defaultTestLoader.discover("tests")
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


def main():
    parser = argparse.ArgumentParser(description="JARVIS Universal Voice-Controlled AI Agent")
    parser.add_argument("--gui", action="store_true", help="Launch desktop control panel (Default)")
    parser.add_argument("--cli", action="store_true", help="Run interactive terminal loop")
    parser.add_argument("--voice", action="store_true", help="Run continuous wake-word listening loop")
    parser.add_argument("--test", action="store_true", help="Run automated test suite")

    args = parser.parse_args()

    if args.test:
        run_automated_tests()
    elif args.cli:
        run_cli_mode()
    elif args.voice:
        run_voice_continuous_mode()
    else:
        # Default: Launch GUI Control Panel if display available, otherwise CLI
        try:
            launch_dashboard()
        except Exception as e:
            print(f"Could not open GUI window ({e}). Starting in CLI mode...")
            run_cli_mode()


if __name__ == "__main__":
    main()
