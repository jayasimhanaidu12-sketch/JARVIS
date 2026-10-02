"""
Core Autonomous Agent Loop for JARVIS.
Orchestrates: Listen -> Understand -> Plan -> Observe -> Act -> Verify -> Respond.
Implements auto-recovery, replanning, and natural vocal interaction.
"""

import time
import re
from typing import List, Dict, Any, Optional
from config.settings import settings
from core.context import context, DeviceType
from core.memory import memory
from core.permissions import permission_manager, EmergencyStopTriggered, PermissionDeniedError
from core.planner import task_planner, PlanStep
from tools.executor import tool_executor
from voice.text_to_speech import tts
from logging_system.logger import jarvis_logger


class JarvisAgent:
    def __init__(self):
        self.max_retries = settings.AUTO_RECOVERY_RETRIES
        self.is_busy = False

    def _format_with_sir(self, text: str) -> str:
        """
        Ensures the response always respectfully addresses the user as 'Sir',
        matching the iconic Iron Man J.A.R.V.I.S. persona.
        """
        clean = text.strip()
        if not clean:
            return "Yes, sir."

        # If 'sir' is already present, return as is
        if re.search(r"\bsir\b", clean, re.IGNORECASE):
            return clean

        # Handle questions vs statements cleanly
        if clean.endswith("?"):
            body = clean[:-1].strip().rstrip(",;:-")
            return f"{body}, sir?"
        elif clean.endswith((".", "!")):
            punct = clean[-1]
            body = clean[:-1].strip().rstrip(",;:-")
            return f"{body}, sir{punct}"
        else:
            return f"{clean}, sir."

    def handle_emergency_stop(self) -> str:
        """Handles immediate shutdown signal."""
        permission_manager.trigger_emergency_stop("User invoked JARVIS STOP")
        tts.stop_speaking()
        response = "Automation stopped immediately, sir."
        tts.speak(response)
        memory.add_turn("jarvis", response)
        return response

    # Name introduction patterns for auto-greeting
    _NAME_PATTERNS = [
        re.compile(r"\bmy\s+name\s+is\s+(.+)", re.IGNORECASE),
        re.compile(r"\bi(?:'|\u2019)?m\s+(.+)", re.IGNORECASE),
        re.compile(r"\bcall\s+me\s+(.+)", re.IGNORECASE),
        re.compile(r"\bthis\s+is\s+(.+?)(?:\s+speaking)?\.?$", re.IGNORECASE),
        re.compile(r"\bi\s+am\s+(.+)", re.IGNORECASE),
    ]
    _NAME_STOPWORDS = {
        "hungry", "tired", "bored", "happy", "sad", "fine", "good", "great",
        "okay", "ok", "busy", "here", "back", "ready", "done", "sorry",
        "lost", "confused", "looking", "trying", "going", "coming", "leaving",
        "not", "just", "doing", "feeling", "getting", "having", "making",
        "working", "waiting", "watching", "listening", "thinking", "wondering",
        "sure", "so", "very", "really", "actually", "about", "at", "in", "on",
        "a", "an", "the", "your", "his", "her", "their", "my",
    }

    def _detect_name_introduction(self, text: str):
        """
        Detects if the user is introducing themselves by name.
        Returns the extracted name (title-cased) if detected, else None.
        
        Examples:
            "my name is Jayasimha" → "Jayasimha"
            "I'm Tony Stark"       → "Tony Stark"
            "call me Peter"        → "Peter"
        """
        clean = text.strip()
        if not clean:
            return None
        for pattern in self._NAME_PATTERNS:
            match = pattern.search(clean)
            if match:
                raw_name = match.group(1).strip().rstrip(".!?,;:")
                # Remove trailing filler
                raw_name = re.split(
                    r"\b(?:and|but|so|can|could|would|please|help|i need|what|how)\b",
                    raw_name, flags=re.IGNORECASE
                )[0].strip()
                if not raw_name:
                    continue
                first_word = raw_name.split()[0].lower()
                if first_word in self._NAME_STOPWORDS:
                    continue
                if len(raw_name.split()) > 5 or len(raw_name) > 50:
                    continue
                return raw_name.title()
        return None

    # "How are you" greeting patterns
    _HOW_ARE_YOU_PATTERNS = [
        re.compile(r"^(?:hi|hello|hey|yo)?\s*(?:jarvis)?\s*,?\s*(?:how\s+are\s+you|how\s+r\s+u|how're\s+you|how\s+are\s+you\s+doing|how's\s+it\s+going)(?:\s+jarvis)?(?:\s+today)?[\s\.\?!]*$", re.IGNORECASE),
        re.compile(r"^(?:how\s+are\s+you|how\s+are\s+you\s+doing)\s*(?:jarvis)?[\s\.\?!]*$", re.IGNORECASE),
    ]

    def _is_how_are_you_greeting(self, text: str) -> bool:
        clean = text.strip()
        if not clean:
            return False
        for pattern in self._HOW_ARE_YOU_PATTERNS:
            if pattern.search(clean):
                return True
        return False

    def process_command(self, raw_command: str) -> str:
        """
        Main Agent Execution Pipeline:
        1. Resolve references & check emergency stop.
        2. Plan tasks via TaskPlanner.
        3. Execute each step: Observe -> Act -> Observe -> Verify.
        4. Auto-recover / Replan upon failure.
        5. Formulate concise, natural response and speak.
        """
        clean_cmd = raw_command.strip()
        if not clean_cmd:
            return ""

        print(f"\n[AGENT PROCESSING]: \"{clean_cmd}\"")
        memory.add_turn("user", clean_cmd)

        # Immediate Emergency Stop Check
        if "jarvis stop" in clean_cmd.lower() or clean_cmd.lower() == "stop":
            return self.handle_emergency_stop()

        # If previous emergency stop was set, allow user to resume
        if permission_manager.is_emergency_stopped:
            permission_manager.reset_emergency_stop()

        # "Hi jarvis how are you" Greeting Detection
        if self._is_how_are_you_greeting(clean_cmd):
            greeting = "Hello  i'm jarvis How may i assist you today ."
            tts.speak(greeting)
            memory.add_turn("jarvis", greeting)
            return greeting

        # Name Introduction Detection — auto-greet when user says their name
        detected_name = self._detect_name_introduction(clean_cmd)
        if detected_name:
            greeting = f"Hello {detected_name} my name is jarvis how can i assist you today."
            tts.speak(greeting)
            memory.add_turn("jarvis", greeting)
            return greeting

        self.is_busy = True

        # Strip leading wake word for cleaner intent parsing
        cmd_for_planning = re.sub(r"^(?:hey\s+|ok\s+|okay\s+)?jarvis\s*[,.:;!-]?\s*", "", clean_cmd, flags=re.IGNORECASE).strip()
        if not cmd_for_planning:
            cmd_for_planning = clean_cmd

        try:
            # 1. Intent Understanding & Planning
            steps: List[PlanStep] = task_planner.plan(cmd_for_planning)
            if not steps:
                msg = "I'm not sure how to do that yet, sir. Could you clarify what you'd like me to do?"
                tts.speak(msg)
                memory.add_turn("jarvis", msg)
                return msg

            # If emergency stop was planned
            if steps[0].tool_name == "emergency_stop":
                return self.handle_emergency_stop()

            # 2. Execution Loop across planned steps
            completed_steps: List[str] = []
            overall_success = True
            final_response = ""

            for i, step in enumerate(steps):
                # Check for interruption
                if permission_manager.is_emergency_stopped:
                    break

                step_success = False
                attempts = 0

                while attempts <= self.max_retries and not step_success:
                    attempts += 1
                    try:
                        # Voice Narration of current action
                        if attempts == 1:
                            tts.speak(f"{step.description}, sir.", wait=False)

                        # OBSERVE -> ACT -> VERIFY
                        success, result_msg, verify_msg = tool_executor.execute_tool(
                            tool_name=step.tool_name,
                            params=step.parameters,
                            user_command=clean_cmd,
                        )

                        if success:
                            step_success = True
                            completed_steps.append(result_msg or step.description)
                        else:
                            # If blocked by user permission denial or emergency stop, do not retry
                            denial_phrase = (verify_msg + result_msg).lower()
                            if "user denied" in denial_phrase or "confirmation" in denial_phrase or "declined" in denial_phrase:
                                msg = "Action canceled because confirmation was declined, sir."
                                tts.speak(msg)
                                memory.add_turn("jarvis", msg)
                                return msg
                            if "emergency stop" in (verify_msg + result_msg).lower():
                                return self.handle_emergency_stop()

                            # Auto-recovery: Wait briefly and retry or re-observe
                            if attempts <= self.max_retries:
                                time.sleep(0.4)

                    except EmergencyStopTriggered:
                        return self.handle_emergency_stop()
                    except PermissionDeniedError:
                        msg = "Action canceled because confirmation was declined, sir."
                        tts.speak(msg)
                        return msg
                    except Exception as ex:
                        if attempts > self.max_retries:
                            overall_success = False
                            final_response = f"I encountered an issue executing {step.description}, sir: {str(ex)}"
                            break

                if not step_success:
                    overall_success = False
                    final_response = f"I couldn't complete {step.description}, sir. Would you like me to try another way?"
                    break

            # 3. Formulate Natural Voice Response (Section 3 & 20)
            if overall_success and not final_response:
                final_response = self._synthesize_natural_response(clean_cmd, steps, completed_steps)

            # Ensure every response addresses user as Sir
            final_response = self._format_with_sir(final_response)

            # 4. Speak and log response
            tts.speak(final_response)
            memory.add_turn("jarvis", final_response)
            return final_response

        finally:
            self.is_busy = False

    def _synthesize_natural_response(
        self,
        command: str,
        steps: List[PlanStep],
        completed: List[str],
    ) -> str:
        """
        Creates concise, human-like voice responses matching JARVIS persona.
        Always addresses Tony Stark / user respectfully as 'Sir'.
        """
        cmd_lower = command.lower()

        # News & Live Updates (Top 7 updates for the present day)
        if any(s.tool_name == "get_news_updates" for s in steps):
            for res in reversed(completed):
                if res and ("update" in res.lower() or "news" in res.lower() or "headline" in res.lower()):
                    return res
            return "Here are today's top news updates, sir."

        # Web & YouTube Searches
        if "youtube" in cmd_lower:
            if any(s.tool_name == "open_url" for s in steps):
                return "YouTube is open in guest mode, sir."
            elif any(s.tool_name == "pause_media" for s in steps):
                return "I've opened the video and paused it for you, sir."
            elif any(s.tool_name == "select_result" for s in steps):
                return "Playing the requested video on YouTube, sir."
            return "Searching YouTube, sir."

        # Web & Google Searches (including Search About Me)
        if any(s.tool_name == "browser_search" for s in steps):
            for s in steps:
                if s.tool_name == "browser_search":
                    q = s.parameters.get("query", "")
                    if "gudise" in q.lower() or "jayasimha" in q.lower() or "about me" in cmd_lower or "who am i" in cmd_lower:
                        return f"Opening browser and searching for {settings.USER_NAME}, sir."
                    return f"Search for {q} completed, sir."

        if "search" in cmd_lower and "chrome" in cmd_lower:
            return "Chrome is open and I've performed your search, sir."

        if cmd_lower.startswith("search"):
            return "Search completed, sir."

        # App Launching
        if any(s.tool_name == "open_application" for s in steps):
            app = steps[0].parameters.get("app_name", "the application")
            return f"{app.capitalize()} is open, sir."

        # Media Control
        if any(s.tool_name == "pause_media" for s in steps):
            return "The video is paused, sir."
        if any(s.tool_name == "play_media" for s in steps):
            return "Resumed playback, sir."

        # Phone Control
        if context.active_device == DeviceType.ANDROID:
            return "Command executed on your phone, sir."

        # Keyboard Actions
        if any(s.tool_name == "type_text" for s in steps):
            type_step = next(s for s in steps if s.tool_name == "type_text")
            txt = type_step.parameters.get("text", "")
            if any(s.tool_name == "open_application" for s in steps):
                app = steps[0].parameters.get("app_name", "the app")
                return f"I've opened {app} and typed the text for you, sir."
            return f"Typed '{txt}', sir."

        if any(s.tool_name == "press_key" for s in steps):
            k = steps[0].parameters.get("key", "the key")
            return f"Pressed {k}, sir."

        if any(s.tool_name in ("hotkey", "keyboard_copy", "keyboard_paste", "keyboard_select_all", "keyboard_save", "keyboard_undo") for s in steps):
            if any(s.tool_name == "keyboard_copy" for s in steps):
                return "Copied to clipboard, sir."
            if any(s.tool_name == "keyboard_paste" for s in steps):
                return "Pasted, sir."
            if any(s.tool_name == "keyboard_select_all" for s in steps):
                return "Selected all, sir."
            if any(s.tool_name == "keyboard_save" for s in steps):
                return "Document saved, sir."
            if any(s.tool_name == "keyboard_undo" for s in steps):
                return "Action undone, sir."
            return "Executed keyboard shortcut, sir."

        # General completion
        if completed:
            return f"{completed[-1]}, sir."

        return "Task completed, sir."


jarvis_agent = JarvisAgent()
