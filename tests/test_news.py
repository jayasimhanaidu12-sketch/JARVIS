"""
Unit and Integration tests for Present Day News Updates and Voice Formatting.
"""

import unittest
from tools.news_service import news_service
from core.planner import task_planner
from tools.executor import tool_executor


class TestNewsUpdates(unittest.TestCase):
    def test_news_planner_detection(self):
        """Tests that various user news request phrasing maps to get_news_updates tool."""
        queries = [
            "jarvis what is the news update today . jarvis search about the present day and give me the 7 updates in the voice format.",
            "what is the news update today",
            "jarvis what is the news update today",
            "search about the present day and give me the 7 updates in the voice format",
            "give me the 7 updates in the voice format",
            "news update today",
            "what are today's news updates",
            "what is the latest news update",
            "give me today's news",
        ]

        for q in queries:
            steps = task_planner.plan(q)
            self.assertTrue(len(steps) >= 1, f"Failed to plan for: '{q}'")
            self.assertEqual(steps[0].tool_name, "get_news_updates", f"Wrong tool planned for '{q}'")
            self.assertEqual(steps[0].parameters.get("count"), 7)

    def test_news_custom_count_planning(self):
        """Tests that requests with specific counts (e.g. 5 updates) extract count properly."""
        steps = task_planner.plan("give me 5 news updates today")
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0].tool_name, "get_news_updates")
        self.assertEqual(steps[0].parameters.get("count"), 5)

    def test_news_custom_topic_planning(self):
        """Tests that specific topics like 'tech news' are extracted."""
        steps = task_planner.plan("what is the tech news update today")
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0].tool_name, "get_news_updates")
        self.assertEqual(steps[0].parameters.get("topic"), "tech")

    def test_news_voice_formatting(self):
        """Tests that headlines are properly formatted into spoken ordinal sentences."""
        sample_items = [
            {"headline": "Global summit concludes on climate pact", "source": "Reuters"},
            {"headline": "Spacecraft successfully touches down on asteroid", "source": "BBC News"},
            {"headline": "New breakthrough in quantum computing announced", "source": "Nature"},
            {"headline": "Tech companies unveil next-gen AI chipsets", "source": "Bloomberg"},
            {"headline": "Major economic indices rise following trade report", "source": "Financial Times"},
            {"headline": "International sports tournament kicks off this weekend", "source": "ESPN"},
            {"headline": "Clean energy investments reach new milestone", "source": "AP News"},
        ]

        formatted = news_service.format_news_for_voice(sample_items, count=7)

        self.assertIn("Here are today's top 7 news updates, sir:", formatted)
        self.assertIn("First: Global summit concludes on climate pact", formatted)
        self.assertIn("Second: Spacecraft successfully touches down on asteroid", formatted)
        self.assertIn("Third: New breakthrough in quantum computing announced", formatted)
        self.assertIn("Fourth: Tech companies unveil next-gen AI chipsets", formatted)
        self.assertIn("Fifth: Major economic indices rise following trade report", formatted)
        self.assertIn("Sixth: International sports tournament kicks off this weekend", formatted)
        self.assertIn("And seventh: Clean energy investments reach new milestone", formatted)
        self.assertIn("Those are the primary headlines for today, sir.", formatted)

    def test_news_executor_integration(self):
        """Tests end-to-end execution of get_news_updates tool via tool_executor."""
        success, result_msg, verify_msg = tool_executor.execute_tool(
            "get_news_updates",
            params={"count": 7},
            user_command="what is the news update today",
        )

        self.assertTrue(success)
        self.assertIn("top 7 news updates", result_msg.lower())
        self.assertIn("first:", result_msg.lower())
        self.assertIn("and seventh:", result_msg.lower())
        self.assertIn("Verified", verify_msg)


if __name__ == "__main__":
    unittest.main()
