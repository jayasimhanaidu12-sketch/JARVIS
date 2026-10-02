"""
Unit tests for individual tools across Windows, Browser, Files, System, and Mobile.
"""

import unittest
from pathlib import Path
from tools.registry import tool_registry
from tools.executor import tool_executor
from computer.files import file_manager
from computer.system import system_controller
from mobile.android_controller import android_controller
from vision.screen_capture import screen_capture


class TestJarvisTools(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("./test_sandbox")
        self.test_dir.mkdir(exist_ok=True)

    def tearDown(self):
        if self.test_dir.exists():
            import shutil
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_tool_registry_populated(self):
        """Verifies that all core tools are registered."""
        expected_tools = [
            "open_application", "close_application", "click", "type_text",
            "open_url", "browser_search", "youtube_search", "select_result",
            "create_file", "delete_file", "system_volume_up", "mobile_launch_app",
            "take_screenshot"
        ]
        for name in expected_tools:
            tool = tool_registry.get_tool(name)
            self.assertIsNotNone(tool, f"Tool '{name}' should be in registry")

    def test_file_operations(self):
        """Verifies file creation, reading, and verification."""
        file_path = str(self.test_dir / "sample.txt")
        content = "Hello from JARVIS automated test suite."

        # Create
        success, msg, verify = tool_executor.execute_tool("create_file", {"path": file_path, "content": content})
        self.assertTrue(success)
        self.assertTrue(Path(file_path).exists())
        self.assertIn("Verified", verify)

        # Read
        success, read_content = file_manager.read_file(file_path)
        self.assertTrue(success)
        self.assertEqual(read_content, content)

    def test_system_volume_control(self):
        """Verifies system volume commands execute without exception."""
        success, msg = system_controller.volume_up(steps=1)
        self.assertTrue(success)

        success, msg = system_controller.volume_down(steps=1)
        self.assertTrue(success)

    def test_screen_capture(self):
        """Verifies screenshot capture returns valid PIL image."""
        img, path = screen_capture.capture_screen(save=False)
        self.assertIsNotNone(img)
        self.assertGreater(img.size[0], 0)
        self.assertGreater(img.size[1], 0)

    def test_mobile_controller(self):
        """Verifies Android mobile tools in simulated/device mode."""
        success, msg = android_controller.launch_app("youtube")
        self.assertTrue(success)

        success, msg = android_controller.tap(100, 200)
        self.assertTrue(success)

        success, msg = android_controller.press_home()
        self.assertTrue(success)


if __name__ == "__main__":
    unittest.main()
