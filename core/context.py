"""
Context awareness layer for JARVIS.
Tracks active device, current application, browser tabs, media state, and screen details.
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field


class DeviceType(Enum):
    WINDOWS = "windows"
    ANDROID = "android"
    UNKNOWN = "unknown"


@dataclass
class UIElementReference:
    name: str
    element_type: str  # button, input, link, window, menu
    bounds: tuple = (0, 0, 0, 0)  # x, y, width, height
    text: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)


class SystemContext:
    def __init__(self):
        self.active_device: DeviceType = DeviceType.WINDOWS
        self.current_application: str = ""
        self.current_window_title: str = ""
        self.current_website: str = ""
        self.current_media_title: str = ""
        self.is_media_playing: bool = False
        self.last_search_results: List[str] = []
        self.recent_elements: List[UIElementReference] = []
        self.last_action_name: str = ""
        self.last_action_params: Dict[str, Any] = {}
        self.last_action_success: bool = True
        self.screen_resolution: tuple = (1920, 1080)

    def set_device(self, device: DeviceType):
        self.active_device = device

    def update_application_state(self, app_name: str, window_title: str = ""):
        self.current_application = app_name
        if window_title:
            self.current_window_title = window_title

    def update_browser_state(self, url_or_site: str, results: Optional[List[str]] = None):
        self.current_website = url_or_site
        if results is not None:
            self.last_search_results = results

    def update_media_state(self, title: str = "", playing: bool = False):
        if title:
            self.current_media_title = title
        self.is_media_playing = playing

    def record_last_action(self, action_name: str, params: Dict[str, Any], success: bool):
        self.last_action_name = action_name
        self.last_action_params = params
        self.last_action_success = success

    def get_summary(self) -> Dict[str, Any]:
        return {
            "device": self.active_device.value,
            "application": self.current_application or "None",
            "window_title": self.current_window_title or "None",
            "website": self.current_website or "None",
            "media_title": self.current_media_title or "None",
            "media_playing": self.is_media_playing,
            "last_action": self.last_action_name or "None",
        }


context = SystemContext()
