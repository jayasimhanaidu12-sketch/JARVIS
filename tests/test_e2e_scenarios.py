"""
End-to-End Scenario Verification for Section 22:
Test 1: "Open Chrome."
Test 2: "Open Chrome and search for AI agents."
Test 3: "Open YouTube, search for Python tutorials, open the second result and pause the video."
Test 4: "Delete this folder." (Requires confirmation)
Test 5: "JARVIS STOP." (Emergency halt)
"""

import unittest
from pathlib import Path
from core.agent import jarvis_agent
from core.permissions import permission_manager
from core.context import context, DeviceType


class TestE2EScenarios(unittest.TestCase):
    def setUp(self):
        permission_manager.reset_emergency_stop()
        context.set_device(DeviceType.WINDOWS)

    def tearDown(self):
        permission_manager.reset_emergency_stop()

    def test_scenario_1_open_chrome(self):
        """Test 1: 'Open Chrome.' Expected: Chrome launches/focuses and JARVIS confirms it."""
        response = jarvis_agent.process_command("Open Chrome")
        self.assertTrue(len(response) > 0)
        self.assertIn("chrome", response.lower())

    def test_scenario_2_open_chrome_and_search(self):
        """Test 2: 'Open Chrome and search for AI agents.' Expected: Launches browser, submits query, verifies."""
        response = jarvis_agent.process_command("Open Chrome and search for AI agents")
        self.assertTrue(len(response) > 0)
        self.assertIn("search", response.lower())

    def test_scenario_3_youtube_multi_step_workflow(self):
        """Test 3: 'Open YouTube, search for Python tutorials, open the second result and pause the video.'"""
        cmd = "Open YouTube, search for Python tutorials, open the second result and pause the video"
        response = jarvis_agent.process_command(cmd)
        self.assertTrue(len(response) > 0)
        self.assertTrue(any(w in response.lower() for w in ["video", "paused", "youtube"]))

    def test_scenario_4_high_risk_folder_deletion(self):
        """Test 4: 'Delete this folder.' Expected: Confirmation requested before deletion."""
        sandbox = Path("./test_danger_folder")
        sandbox.mkdir(exist_ok=True)

        # 1. Denied confirmation
        permission_manager.set_confirmation_callback(lambda tool, params: False)
        resp_denied = jarvis_agent.process_command(f"Delete folder called '{sandbox.name}'")
        self.assertTrue(sandbox.exists(), "Folder must remain intact when confirmation is denied.")
        self.assertIn("canceled", resp_denied.lower())

        # 2. Approved confirmation
        permission_manager.set_confirmation_callback(lambda tool, params: True)
        resp_approved = jarvis_agent.process_command(f"Delete folder called '{sandbox.name}'")
        self.assertFalse(sandbox.exists(), "Folder should be deleted after approval.")

    def test_scenario_5_jarvis_stop(self):
        """Test 5: 'JARVIS STOP.' Expected: Current automation immediately stops."""
        response = jarvis_agent.process_command("JARVIS STOP")
        self.assertTrue(permission_manager.is_emergency_stopped)
        self.assertIn("stopped", response.lower())


if __name__ == "__main__":
    unittest.main()
