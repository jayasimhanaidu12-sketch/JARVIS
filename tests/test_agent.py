"""
Unit and Integration tests for Task Planner and Core Agent Loop (Tests 1, 2, 3).
"""

import unittest
from core.planner import task_planner
from core.agent import jarvis_agent
from core.context import context, DeviceType
from core.memory import memory


class TestJarvisAgentLoop(unittest.TestCase):
    def setUp(self):
        context.set_device(DeviceType.WINDOWS)

    def test_single_step_open_app_planning(self):
        """Test 1: 'Open Chrome' plans open_application."""
        steps = task_planner.plan("Open Chrome")
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0].tool_name, "open_application")
        self.assertEqual(steps[0].parameters.get("app_name"), "chrome")

    def test_compound_chrome_search_planning(self):
        """Test 2: 'Open Chrome and search for AI agents' plans compound flow."""
        steps = task_planner.plan("Open Chrome and search for AI agents")
        self.assertEqual(len(steps), 2)
        self.assertEqual(steps[0].tool_name, "open_application")
        self.assertEqual(steps[1].tool_name, "browser_search")
        self.assertEqual(steps[1].parameters.get("query"), "ai agents")

    def test_complex_youtube_multistep_workflow(self):
        """Test 3: 'Open YouTube, search for Python tutorials, open the second result and pause the video'."""
        cmd = "Open YouTube, search for Python tutorials, open the second result and pause the video"
        steps = task_planner.plan(cmd)
        tool_names = [s.tool_name for s in steps]

        self.assertIn("open_application", tool_names)
        self.assertIn("youtube_search", tool_names)
        self.assertIn("select_result", tool_names)
        self.assertIn("pause_media", tool_names)

        # Check second result parameter
        select_step = next(s for s in steps if s.tool_name == "select_result")
        self.assertEqual(select_step.parameters.get("index"), 2)

    def test_anaphora_resolution(self):
        """Tests that 'pause it' resolves to the current active media."""
        context.update_media_state(title="Python Tutorial Video", playing=True)
        resolved = memory.resolve_references("Pause it")
        self.assertIn("Python Tutorial Video", resolved)

    def test_device_selection_inference(self):
        """Tests that 'on my phone' switches target device to Android."""
        steps = task_planner.plan("Open YouTube on my phone")
        self.assertEqual(context.active_device, DeviceType.ANDROID)
        self.assertEqual(steps[0].tool_name, "mobile_launch_app")

    def test_search_about_me_planning(self):
        """Tests that 'search about me' maps to user's name Gudise Jayasimha Naidu."""
        steps = task_planner.plan("search about me")
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0].tool_name, "browser_search")
        self.assertEqual(steps[0].parameters.get("query"), "Gudise Jayasimha Naidu")

    def test_how_are_you_greeting(self):
        """Tests that 'hi jarvis how are you' replies with the exact greeting."""
        expected = "Hello  i'm jarvis How may i assist you today ."
        self.assertEqual(jarvis_agent.process_command("hi jarvis how are you"), expected)
        self.assertEqual(jarvis_agent.process_command("hello jarvis how are you"), expected)
        self.assertEqual(jarvis_agent.process_command("jarvis how are you"), expected)
        self.assertEqual(jarvis_agent.process_command("how are you"), expected)


if __name__ == "__main__":
    unittest.main()
