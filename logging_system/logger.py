"""
Structured Action Logger for JARVIS.
Tracks: TIME, USER COMMAND, PLANNED ACTION, TOOL USED, RESULT, VERIFICATION, ERROR.
"""

import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from config.settings import settings


class JarvisActionRecord:
    def __init__(
        self,
        command: str = "",
        action: str = "",
        tool: str = "",
        params: Optional[Dict[str, Any]] = None,
        result: str = "",
        verification: str = "",
        error: Optional[str] = None,
        success: bool = True,
    ):
        self.timestamp = datetime.now().strftime("%H:%M:%S")
        self.command = command
        self.action = action
        self.tool = tool
        self.params = params or {}
        self.result = result
        self.verification = verification
        self.error = error
        self.success = success

    def to_formatted_block(self) -> str:
        lines = [
            f"[{self.timestamp}]",
            f"Command:      {self.command or '(None)'}",
            f"Action:       {self.action or '(None)'}",
            f"Tool:         {self.tool or '(None)'} {self.params if self.params else ''}",
            f"Result:       {self.result or '(Pending)'}",
            f"Verification: {self.verification or '(Not verified)'}",
        ]
        if self.error:
            lines.append(f"ERROR:        {self.error}")
        return "\n".join(lines)


class JarvisLogger:
    def __init__(self):
        self.history: List[JarvisActionRecord] = []
        self.log_file = settings.LOGS_DIR / "jarvis_actions.log"

        # Python standard logger setup
        self._logger = logging.getLogger("JARVIS")
        self._logger.setLevel(logging.INFO)

        # Clear existing handlers if re-instantiated
        if not self._logger.handlers:
            file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
            file_handler.setFormatter(
                logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
            )
            self._logger.addHandler(file_handler)

            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(
                logging.Formatter("[%(asctime)s] [JARVIS] %(message)s", datefmt="%H:%M:%S")
            )
            self._logger.addHandler(console_handler)

        self._callbacks = []

    def register_ui_callback(self, cb):
        """Allows GUI/dashboard to receive real-time action events."""
        self._callbacks.append(cb)

    def log_event(self, message: str, level: str = "info"):
        level = level.lower()
        if level == "error":
            self._logger.error(message)
        elif level == "warning":
            self._logger.warning(message)
        elif level == "debug":
            self._logger.debug(message)
        else:
            self._logger.info(message)

    def record_action(
        self,
        command: str = "",
        action: str = "",
        tool: str = "",
        params: Optional[Dict[str, Any]] = None,
        result: str = "",
        verification: str = "",
        error: Optional[str] = None,
        success: bool = True,
    ) -> JarvisActionRecord:
        record = JarvisActionRecord(
            command=command,
            action=action,
            tool=tool,
            params=params,
            result=result,
            verification=verification,
            error=error,
            success=success,
        )
        self.history.append(record)

        # Append structured block to actions log
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(record.to_formatted_block() + "\n" + "-" * 40 + "\n")
        except Exception as e:
            self._logger.warning(f"Failed writing to action log file: {e}")

        # Notify UI callbacks
        for cb in self._callbacks:
            try:
                cb(record)
            except Exception:
                pass

        # Print structured console output
        print(f"\n{record.to_formatted_block()}\n")
        return record

    def get_recent_history(self, limit: int = 15) -> List[JarvisActionRecord]:
        return self.history[-limit:]


jarvis_logger = JarvisLogger()
