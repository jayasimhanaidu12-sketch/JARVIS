"""
Web actions module for JARVIS.
Handles automated web search, YouTube integration, and media playback toggling.
"""

import time
import urllib.parse
from typing import Tuple, List, Optional
from core.context import context
from browser.browser_controller import browser_controller
from computer.keyboard import keyboard
from computer.mouse import mouse
from computer.windows import windows_manager


class WebActions:
    def search_google(self, query: str) -> Tuple[bool, str]:
        """Performs a Google Search in browser."""
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={encoded}"
        success, msg = browser_controller.open_url(url)
        if success:
            context.update_browser_state(
                url,
                results=[f"Result 1 for {query}", f"Result 2 for {query}", f"Result 3 for {query}"]
            )
            return True, f"Searched Google for '{query}'"
        return False, msg

    def search_youtube(self, query: str) -> Tuple[bool, str]:
        """Performs a YouTube Search in browser."""
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.youtube.com/results?search_query={encoded}"
        success, msg = browser_controller.open_url(url)
        if success:
            context.update_browser_state(
                url,
                results=[
                    f"Video 1 for {query}",
                    f"Video 2 for {query}",
                    f"Video 3 for {query}",
                    f"Video 4 for {query}",
                ]
            )
            context.update_media_state(title=f"YouTube results: {query}", playing=False)
            return True, f"Searched YouTube for '{query}'"
        return False, msg

    def select_search_result(self, index: int = 1) -> Tuple[bool, str]:
        """
        Selects a specific search result or video by index.
        In YouTube/Google page, navigates to the result via keyboard tab or enter.
        """
        # Focus browser window
        windows_manager.focus_window("chrome") or windows_manager.focus_window("edge")
        time.sleep(0.3)

        # Tab navigation to result links or click relative area
        # For web video results, pressing Tab multiple times or Enter
        for _ in range(index * 2):
            keyboard.press_key("tab")
            time.sleep(0.05)
        keyboard.press_key("enter")

        item_desc = f"result number {index}"
        if context.last_search_results and len(context.last_search_results) >= index:
            item_desc = context.last_search_results[index - 1]

        context.update_media_state(title=item_desc, playing=True)
        return True, f"Selected {item_desc}"

    def media_play_pause(self, action: str = "toggle") -> Tuple[bool, str]:
        """
        Toggles or sets media play/pause state in active browser or desktop player.
        YouTube uses 'k' or 'space' key for play/pause.
        """
        windows_manager.focus_window("chrome") or windows_manager.focus_window("edge")
        time.sleep(0.2)

        # 'k' is YouTube's standard universal play/pause shortcut
        keyboard.press_key("k")

        is_now_playing = not context.is_media_playing if action == "toggle" else (action == "play")
        context.update_media_state(playing=is_now_playing)
        status_text = "resumed" if is_now_playing else "paused"
        return True, f"Media has been {status_text}."

    def pause_media(self) -> Tuple[bool, str]:
        return self.media_play_pause("pause")

    def resume_media(self) -> Tuple[bool, str]:
        return self.media_play_pause("play")


web_actions = WebActions()
