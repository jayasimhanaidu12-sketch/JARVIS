"""
Safety, Permissions, and Emergency Stop system for JARVIS.
Enforces low-risk vs high-risk boundaries and immediate shutdown on 'JARVIS STOP'.
"""

import threading
from enum import Enum
from typing import Callable, Optional, Dict, Any
from config.settings import settings


class RiskLevel(Enum):
    LOW = "low"
    HIGH = "high"


class PermissionDeniedError(Exception):
    """Raised when user denies execution of a high-risk action."""
    pass


class EmergencyStopTriggered(Exception):
    """Raised when emergency stop is active."""
    pass


class PermissionManager:
    # Set of actions that are considered high-risk according to Section 13
    HIGH_RISK_TOOLS = {
        "delete_file",
        "delete_directory",
        "execute_shell",
        "shutdown_system",
        "restart_system",
        "kill_process",
        "clear_directory",
        "mobile_uninstall_app",
        "mobile_factory_reset",
    }

    def __init__(self):
        self._emergency_stop = threading.Event()
        self._confirmation_callback: Optional[Callable[[str, Dict[str, Any]], bool]] = None

    def set_confirmation_callback(self, cb: Callable[[str, Dict[str, Any]], bool]):
        """Sets a custom confirmation UI callback (e.g., desktop dialog or voice prompt)."""
        self._confirmation_callback = cb

    @property
    def is_emergency_stopped(self) -> bool:
        return self._emergency_stop.is_set()

    def trigger_emergency_stop(self, reason: str = "User initiated STOP"):
        """Immediately halts all active automation tasks."""
        self._emergency_stop.set()
        print(f"\n[EMERGENCY STOP TRIGGERED]: {reason}\n")

    def reset_emergency_stop(self):
        """Clears the emergency stop flag to resume operations."""
        self._emergency_stop.clear()
        print("\n[EMERGENCY STOP RESET]: Operations resumed.\n")

    def check_emergency(self):
        if self.is_emergency_stopped:
            raise EmergencyStopTriggered("Action aborted: JARVIS Emergency Stop is active.")

    def classify_risk(self, tool_name: str, params: Optional[Dict[str, Any]] = None) -> RiskLevel:
        """Determines if an action is low-risk or high-risk."""
        if tool_name in self.HIGH_RISK_TOOLS:
            return RiskLevel.HIGH
        return RiskLevel.LOW

    def verify_permission(self, tool_name: str, params: Optional[Dict[str, Any]] = None, description: str = "") -> bool:
        """
        Verifies permission before executing a tool.
        Throws EmergencyStopTriggered or PermissionDeniedError if not allowed.
        """
        self.check_emergency()

        risk = self.classify_risk(tool_name, params)
        if risk == RiskLevel.LOW or not settings.REQUIRE_CONFIRMATION_HIGH_RISK:
            return True

        # High-risk action: Explicit confirmation required!
        prompt_msg = description or f"Dangerous action requested: '{tool_name}' with {params or {}}."

        if self._confirmation_callback:
            approved = self._confirmation_callback(tool_name, params or {})
        else:
            # Fallback to console prompt if no UI callback is attached
            print(f"\n[HIGH-RISK CONFIRMATION NEEDED]: {prompt_msg}")
            choice = input("Do you confirm this action? (yes/no): ").strip().lower()
            approved = choice in ("yes", "y")

        if not approved:
            raise PermissionDeniedError(f"User denied execution of high-risk action: {tool_name}")

        return True


permission_manager = PermissionManager()
