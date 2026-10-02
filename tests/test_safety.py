"""
Unit tests for Safety, High-Risk Action Confirmation, and Emergency Stop (Tests 4 & 5).
"""

import unittest
from pathlib import Path
from core.permissions import (
    permission_manager,
    RiskLevel,
    EmergencyStopTriggered,
    PermissionDeniedError,
)
from tools.executor import tool_executor
from core.agent import jarvis_agent


class TestSafetyAndPermissions(unittest.TestCase):
    def setUp(self):
        permission_manager.reset_emergency_stop()
        self.test_file = Path("./safety_test.txt")
        self.test_file.write_text("critical data", encoding="utf-8")

    def tearDown(self):
        permission_manager.reset_emergency_stop()
        if self.test_file.exists():
            self.test_file.unlink()

    def test_risk_classification(self):
        """Verifies safe tools are Low Risk and destructive tools are High Risk."""
        self.assertEqual(permission_manager.classify_risk("open_application"), RiskLevel.LOW)
        self.assertEqual(permission_manager.classify_risk("browser_search"), RiskLevel.LOW)
        self.assertEqual(permission_manager.classify_risk("delete_file"), RiskLevel.HIGH)
        self.assertEqual(permission_manager.classify_risk("delete_directory"), RiskLevel.HIGH)

    def test_denied_confirmation_blocks_deletion(self):
        """Test 4: High-risk action blocked when user declines confirmation."""
        # Mock confirmation callback that denies execution
        permission_manager.set_confirmation_callback(lambda tool, params: False)

        success, msg, verify = tool_executor.execute_tool(
            "delete_file",
            {"path": str(self.test_file)},
            user_command="Delete this file",
        )

        self.assertFalse(success)
        self.assertTrue(self.test_file.exists(), "File must NOT be deleted when confirmation is denied.")
        self.assertIn("denied", verify.lower())

    def test_approved_confirmation_allows_deletion(self):
        """Test 4 part 2: High-risk action proceeds when user explicitly approves."""
        permission_manager.set_confirmation_callback(lambda tool, params: True)

        success, msg, verify = tool_executor.execute_tool(
            "delete_file",
            {"path": str(self.test_file)},
            user_command="Delete this file",
        )

        self.assertTrue(success)
        self.assertFalse(self.test_file.exists(), "File should be deleted after explicit user approval.")

    def test_emergency_stop_command(self):
        """Test 5: 'JARVIS STOP' immediately triggers emergency stop flag."""
        response = jarvis_agent.process_command("JARVIS STOP")
        self.assertTrue(permission_manager.is_emergency_stopped)
        self.assertIn("stopped", response.lower())

        # Any subsequent tool execution must immediately raise or be blocked
        success, msg, verify = tool_executor.execute_tool("browser_search", {"query": "python"})
        self.assertFalse(success)
        self.assertIn("emergency stop", verify.lower())


if __name__ == "__main__":
    unittest.main()
