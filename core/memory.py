"""
Task memory and conversational context management for JARVIS.
Handles short-term dialogue history and anaphora resolution ('it', 'the second one', 'again').
"""

import re
from typing import List, Dict, Any, Optional
from core.context import context, DeviceType


class ConversationTurn:
    def __init__(self, role: str, text: str):
        self.role = role  # 'user' or 'jarvis'
        self.text = text


class TaskMemory:
    def __init__(self):
        self.conversation_history: List[ConversationTurn] = []
        self.task_stack: List[str] = []
        self.active_file_or_folder: Optional[str] = None

    def add_turn(self, role: str, text: str):
        self.conversation_history.append(ConversationTurn(role, text))
        # Keep last 25 turns in working context
        if len(self.conversation_history) > 25:
            self.conversation_history.pop(0)

    def set_active_path(self, path: str):
        self.active_file_or_folder = path

    def resolve_references(self, command: str) -> str:
        """
        Resolves linguistic references ('it', 'the second one', 'that video', 'again')
        based on active context and memory.
        """
        resolved = command.strip()

        # Check for ordinal references: 'the first one', 'the second one', 'the third result'
        ordinal_patterns = [
            (r"\b(the\s+)?(first|1st)\s+(one|result|video|link)\b", 0),
            (r"\b(the\s+)?(second|2nd)\s+(one|result|video|link)\b", 1),
            (r"\b(the\s+)?(third|3rd)\s+(one|result|video|link)\b", 2),
            (r"\b(the\s+)?(fourth|4th)\s+(one|result|video|link)\b", 3),
            (r"\b(the\s+)?(fifth|5th)\s+(one|result|video|link)\b", 4),
        ]

        for pattern, idx in ordinal_patterns:
            if re.search(pattern, resolved, re.IGNORECASE):
                if context.last_search_results and len(context.last_search_results) > idx:
                    target_item = context.last_search_results[idx]
                    resolved = re.sub(
                        pattern,
                        f"item '{target_item}' (index {idx + 1})",
                        resolved,
                        flags=re.IGNORECASE,
                    )
                else:
                    resolved = re.sub(
                        pattern,
                        f"item at index {idx + 1}",
                        resolved,
                        flags=re.IGNORECASE,
                    )

        # Check for 'it' resolution when referring to media or file
        if re.search(r"\b(pause|play|resume|stop)\s+it\b", resolved, re.IGNORECASE):
            target = context.current_media_title or "currently playing media"
            resolved = re.sub(
                r"\bit\b",
                f"the media '{target}'",
                resolved,
                flags=re.IGNORECASE,
            )
        elif re.search(r"\b(delete|remove)\s+(this\s+(folder|file)|it)\b", resolved, re.IGNORECASE):
            if self.active_file_or_folder:
                resolved = re.sub(
                    r"\b(this\s+(folder|file)|it)\b",
                    f"path '{self.active_file_or_folder}'",
                    resolved,
                    flags=re.IGNORECASE,
                )

        # Device mention detection (Section 12)
        device_spec = self.detect_device_target(command)
        if device_spec != DeviceType.UNKNOWN:
            context.set_device(device_spec)

        return resolved

    def detect_device_target(self, text: str) -> DeviceType:
        """Determines if command specifies laptop/PC vs mobile/phone."""
        text_lower = text.lower()
        if any(term in text_lower for term in ["on my phone", "on phone", "on android", "on mobile"]):
            return DeviceType.ANDROID
        elif any(term in text_lower for term in ["on my laptop", "on laptop", "on pc", "on computer", "on windows"]):
            return DeviceType.WINDOWS
        return DeviceType.UNKNOWN

    def get_conversation_context_prompt(self) -> str:
        """Produces conversation summary for LLM context."""
        summary = context.get_summary()
        recent_dialogue = "\n".join(
            f"{turn.role.upper()}: {turn.text}"
            for turn in self.conversation_history[-6:]
        )
        return (
            f"Active Context:\n"
            f"- Device: {summary['device']}\n"
            f"- Current App: {summary['application']}\n"
            f"- Current Window: {summary['window_title']}\n"
            f"- Current Website: {summary['website']}\n"
            f"- Media Playing: {summary['media_playing']}\n"
            f"- Active File: {self.active_file_or_folder or 'None'}\n\n"
            f"Recent Dialogue:\n{recent_dialogue or '(New conversation)'}\n"
        )


memory = TaskMemory()
