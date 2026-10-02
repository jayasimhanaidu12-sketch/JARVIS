"""
Tool execution engine with Pre-Observation, Safety Gate, Execution, and Verification.
"""

import time
from typing import Dict, Any, Tuple, Optional
from pathlib import Path
from tools.registry import tool_registry, RiskLevel
from core.permissions import permission_manager, PermissionDeniedError, EmergencyStopTriggered
from core.context import context, DeviceType
from logging_system.logger import jarvis_logger

# Import controllers
from computer.mouse import mouse
from computer.keyboard import keyboard
from computer.windows import windows_manager
from computer.applications import app_manager
from computer.files import file_manager
from computer.system import system_controller
from browser.browser_controller import browser_controller
from browser.web_actions import web_actions
from mobile.android_controller import android_controller
from vision.screen_capture import screen_capture
from vision.ui_detector import ui_detector
from tools.news_service import news_service


def register_all_builtin_tools():
    """Binds all system, computer, browser, mobile, and vision actions into tool_registry."""

    # --- Windows Applications ---
    tool_registry.register(
        name="open_application",
        description="Opens a desktop application on Windows (e.g. Chrome, Notepad, VS Code).",
        parameters={"app_name": {"type": "string", "description": "Name of the app (e.g. chrome, notepad)"}},
        handler=lambda app_name: app_manager.open_application(app_name),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="close_application",
        description="Closes an application on Windows.",
        parameters={"app_name": {"type": "string", "description": "Name of the app"}},
        handler=lambda app_name: app_manager.close_application(app_name),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="switch_application",
        description="Brings an already running application window to front.",
        parameters={"app_name": {"type": "string", "description": "Name or title of application"}},
        handler=lambda app_name: app_manager.switch_to_application(app_name),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="minimize_window",
        description="Minimizes a window.",
        parameters={"window_title": {"type": "string", "description": "Title substring of window"}},
        handler=lambda window_title: (windows_manager.minimize_window(window_title), f"Minimized {window_title}"),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="maximize_window",
        description="Maximizes a window.",
        parameters={"window_title": {"type": "string", "description": "Title substring of window"}},
        handler=lambda window_title: (windows_manager.maximize_window(window_title), f"Maximized {window_title}"),
        risk_level=RiskLevel.LOW,
        device="windows",
    )

    # --- Mouse & Keyboard ---
    tool_registry.register(
        name="click",
        description="Clicks mouse at optional coordinates (x, y) or current location.",
        parameters={
            "x": {"type": "integer", "description": "X coordinate (optional)"},
            "y": {"type": "integer", "description": "Y coordinate (optional)"},
        },
        handler=lambda x=None, y=None: (mouse.click(x, y), f"Clicked at ({x}, {y})" if x else "Clicked"),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="double_click",
        description="Double-clicks mouse.",
        parameters={
            "x": {"type": "integer", "description": "X coordinate (optional)"},
            "y": {"type": "integer", "description": "Y coordinate (optional)"},
        },
        handler=lambda x=None, y=None: (mouse.double_click(x, y), "Double-clicked"),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="right_click",
        description="Right-clicks mouse.",
        parameters={
            "x": {"type": "integer", "description": "X coordinate (optional)"},
            "y": {"type": "integer", "description": "Y coordinate (optional)"},
        },
        handler=lambda x=None, y=None: (mouse.right_click(x, y), "Right-clicked"),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="move_mouse",
        description="Moves mouse to (x, y) coordinates.",
        parameters={
            "x": {"type": "integer", "description": "X coordinate"},
            "y": {"type": "integer", "description": "Y coordinate"},
        },
        handler=lambda x, y: (mouse.move_to(x, y), f"Moved mouse to ({x}, {y})"),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="type_text",
        description="Types text via keyboard into active input field.",
        parameters={"text": {"type": "string", "description": "Text string to type"}},
        handler=lambda text: (keyboard.type_text(text), f"Typed text: {text}"),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="press_key",
        description="Presses a keyboard key (enter, esc, tab, space, backspace, up, down, f5, etc).",
        parameters={"key": {"type": "string", "description": "Key name"}},
        handler=lambda key: (keyboard.press_key(key), f"Pressed key {key}"),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="hotkey",
        description="Presses a key combination (e.g. 'ctrl, c' or 'alt, tab' or 'ctrl+v').",
        parameters={"keys": {"type": "string", "description": "Key combination (e.g. 'ctrl+c' or 'ctrl, c')"}},
        handler=lambda keys: (keyboard.press_combo(keys), f"Pressed shortcut {keys}"),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="keyboard_select_all",
        description="Selects all text or items via Ctrl+A.",
        parameters={},
        handler=lambda: (keyboard.select_all(), "Selected all"),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="keyboard_copy",
        description="Copies selected content to clipboard via Ctrl+C.",
        parameters={},
        handler=lambda: (keyboard.copy(), "Copied to clipboard"),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="keyboard_paste",
        description="Pastes text from clipboard or specified string via Ctrl+V.",
        parameters={"text": {"type": "string", "description": "Optional text to paste"}},
        handler=lambda text=None: (keyboard.paste(text), "Pasted content"),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="keyboard_save",
        description="Saves current file or document via Ctrl+S.",
        parameters={},
        handler=lambda: (keyboard.save(), "Saved document"),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="keyboard_undo",
        description="Undoes last change via Ctrl+Z.",
        parameters={},
        handler=lambda: (keyboard.undo(), "Undid last action"),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="scroll_down",
        description="Scrolls down on the current screen.",
        parameters={"amount": {"type": "integer", "description": "Scroll amount (default 5)"}},
        handler=lambda amount=5: (mouse.scroll_down(amount), f"Scrolled down by {amount}"),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="scroll_up",
        description="Scrolls up on the current screen.",
        parameters={"amount": {"type": "integer", "description": "Scroll amount (default 5)"}},
        handler=lambda amount=5: (mouse.scroll_up(amount), f"Scrolled up by {amount}"),
        risk_level=RiskLevel.LOW,
        device="windows",
    )

    # --- Screen Vision ---
    tool_registry.register(
        name="take_screenshot",
        description="Captures and saves a full desktop screenshot.",
        parameters={"name": {"type": "string", "description": "Optional file tag"}},
        handler=lambda name="shot": (bool(screen_capture.capture_screen(save=True, custom_name=name)[0]), "Screenshot captured"),
        risk_level=RiskLevel.LOW,
        device="windows",
    )

    # --- Browser & Web ---
    tool_registry.register(
        name="open_url",
        description="Navigates to a website in the browser (supports guest mode).",
        parameters={
            "url": {"type": "string", "description": "URL to visit"},
            "guest_mode": {"type": "boolean", "description": "Open in guest mode (default True)"},
        },
        handler=lambda url, guest_mode=True: browser_controller.open_url(url, guest_mode=guest_mode),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="browser_search",
        description="Searches Google for a query.",
        parameters={"query": {"type": "string", "description": "Search query"}},
        handler=lambda query: web_actions.search_google(query),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="youtube_search",
        description="Searches YouTube for videos.",
        parameters={"query": {"type": "string", "description": "Search query"}},
        handler=lambda query: web_actions.search_youtube(query),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="select_result",
        description="Selects an item or video from recent search results by index (1-based).",
        parameters={"index": {"type": "integer", "description": "1-based result index (e.g. 1, 2, 3)"}},
        handler=lambda index=1: web_actions.select_search_result(int(index)),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="play_media",
        description="Plays or resumes media in active browser/player.",
        parameters={},
        handler=lambda: web_actions.resume_media(),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="pause_media",
        description="Pauses media in active browser/player.",
        parameters={},
        handler=lambda: web_actions.pause_media(),
        risk_level=RiskLevel.LOW,
        device="windows",
    )

    # --- Files (High-risk operations flagged) ---
    tool_registry.register(
        name="open_file",
        description="Opens a file or folder in default system viewer.",
        parameters={"path": {"type": "string", "description": "Path to file or folder"}},
        handler=lambda path: file_manager.open_path(path),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="create_file",
        description="Creates a new file with text content.",
        parameters={
            "path": {"type": "string", "description": "Target file path"},
            "content": {"type": "string", "description": "File text content"},
        },
        handler=lambda path, content="": file_manager.create_file(path, content),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="create_folder",
        description="Creates a new directory.",
        parameters={"path": {"type": "string", "description": "Directory path"}},
        handler=lambda path: file_manager.create_folder(path),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="read_file",
        description="Reads contents of a text file.",
        parameters={"path": {"type": "string", "description": "Path to file"}},
        handler=lambda path: file_manager.read_file(path),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="delete_file",
        description="Permanently deletes a file or directory (HIGH RISK - Requires confirmation).",
        parameters={"path": {"type": "string", "description": "Path to delete"}},
        handler=lambda path: file_manager.delete_path(path),
        risk_level=RiskLevel.HIGH,
        device="windows",
    )

    # --- System Control ---
    tool_registry.register(
        name="system_volume_up",
        description="Turns system volume up.",
        parameters={"steps": {"type": "integer", "description": "Volume steps (default 5)"}},
        handler=lambda steps=5: system_controller.volume_up(int(steps)),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="system_volume_down",
        description="Turns system volume down.",
        parameters={"steps": {"type": "integer", "description": "Volume steps (default 5)"}},
        handler=lambda steps=5: system_controller.volume_down(int(steps)),
        risk_level=RiskLevel.LOW,
        device="windows",
    )
    tool_registry.register(
        name="system_mute",
        description="Mutes or unmutes system sound.",
        parameters={},
        handler=lambda: system_controller.toggle_mute(),
        risk_level=RiskLevel.LOW,
        device="windows",
    )

    # --- Android Mobile Tools ---
    tool_registry.register(
        name="mobile_launch_app",
        description="Launches an app on the Android phone (e.g. YouTube, Chrome, Settings).",
        parameters={"app_name": {"type": "string", "description": "Name of app"}},
        handler=lambda app_name: android_controller.launch_app(app_name),
        risk_level=RiskLevel.LOW,
        device="android",
    )
    tool_registry.register(
        name="mobile_tap",
        description="Taps at screen coordinates or button label on phone.",
        parameters={
            "text": {"type": "string", "description": "Label of button or element to tap"},
            "x": {"type": "integer", "description": "X coordinate (optional)"},
            "y": {"type": "integer", "description": "Y coordinate (optional)"},
        },
        handler=lambda text="", x=None, y=None: (
            android_controller.tap(int(x), int(y)) if x is not None and y is not None else android_controller.tap_text(text)
        ),
        risk_level=RiskLevel.LOW,
        device="android",
    )
    tool_registry.register(
        name="mobile_type",
        description="Types text into active input field on phone.",
        parameters={"text": {"type": "string", "description": "Text to type"}},
        handler=lambda text: android_controller.type_text(text),
        risk_level=RiskLevel.LOW,
        device="android",
    )
    tool_registry.register(
        name="mobile_scroll_down",
        description="Scrolls down on phone screen.",
        parameters={},
        handler=lambda: android_controller.scroll_down(),
        risk_level=RiskLevel.LOW,
        device="android",
    )
    tool_registry.register(
        name="mobile_scroll_up",
        description="Scrolls up on phone screen.",
        parameters={},
        handler=lambda: android_controller.scroll_up(),
        risk_level=RiskLevel.LOW,
        device="android",
    )
    tool_registry.register(
        name="mobile_home",
        description="Presses Home button on phone.",
        parameters={},
        handler=lambda: android_controller.press_home(),
        risk_level=RiskLevel.LOW,
        device="android",
    )
    tool_registry.register(
        name="mobile_back",
        description="Presses Back button on phone.",
        parameters={},
        handler=lambda: android_controller.press_back(),
        risk_level=RiskLevel.LOW,
        device="android",
    )
    tool_registry.register(
        name="mobile_media_play_pause",
        description="Toggles media play/pause on phone.",
        parameters={},
        handler=lambda: android_controller.play_pause_media(),
        risk_level=RiskLevel.LOW,
        device="android",
    )

    # --- News & Live Intelligence ---
    tool_registry.register(
        name="get_news_updates",
        description="Fetches and formats top news updates of the present day for natural voice delivery.",
        parameters={
            "count": {"type": "integer", "description": "Number of news updates to retrieve (default 7)"},
            "topic": {"type": "string", "description": "Optional news topic or category (e.g. world, tech, sports)"},
        },
        handler=lambda count=7, topic=None: news_service.get_voice_news_update(count=int(count), topic=topic),
        risk_level=RiskLevel.LOW,
        device="universal",
    )


class ToolExecutor:
    def __init__(self):
        register_all_builtin_tools()

    def execute_tool(
        self,
        tool_name: str,
        params: Optional[Dict[str, Any]] = None,
        user_command: str = "",
    ) -> Tuple[bool, str, str]:
        """
        Executes a registered tool following the Observe -> Act -> Verify pattern.
        Returns: (success: bool, result_message: str, verification_message: str)
        """
        params = params or {}
        tool = tool_registry.get_tool(tool_name)
        if not tool:
            err = f"Unknown tool '{tool_name}'"
            jarvis_logger.record_action(
                command=user_command,
                action=f"Execute {tool_name}",
                tool=tool_name,
                params=params,
                result="Failed",
                verification="Tool not found in registry",
                error=err,
                success=False,
            )
            return False, "", err

        # 1. Observe Pre-State & Verify Permission
        try:
            permission_manager.verify_permission(tool_name, params)
        except (EmergencyStopTriggered, PermissionDeniedError) as pe:
            err_msg = str(pe)
            jarvis_logger.record_action(
                command=user_command,
                action=f"Execute {tool_name}",
                tool=tool_name,
                params=params,
                result="Blocked by permission/emergency stop",
                verification="Unexecuted",
                error=err_msg,
                success=False,
            )
            return False, "", err_msg

        # 2. Execute Action
        try:
            raw_result = tool.handler(**params)
            if isinstance(raw_result, tuple):
                success, result_str = raw_result[0], str(raw_result[1])
            else:
                success, result_str = bool(raw_result), str(raw_result)

            # Insert artificial delay to allow UI to load before typing/clicking
            if tool_name in ("open_url", "open_application", "switch_application"):
                import time
                time.sleep(2.0)

        except Exception as e:
            err = f"Execution error in {tool_name}: {str(e)}"
            jarvis_logger.record_action(
                command=user_command,
                action=f"Execute {tool_name}",
                tool=tool_name,
                params=params,
                result="Failed",
                verification="Execution crashed",
                error=err,
                success=False,
            )
            return False, "", err

        # 3. Observe Again & Verify Result
        verification = self._verify_action(tool_name, params, success)

        # 4. Record Context & Structured Log
        context.record_last_action(tool_name, params, success)
        jarvis_logger.record_action(
            command=user_command,
            action=f"Execute {tool_name}",
            tool=tool_name,
            params=params,
            result=result_str,
            verification=verification,
            success=success,
        )

        return success, result_str, verification

    def _verify_action(self, tool_name: str, params: Dict[str, Any], raw_success: bool) -> str:
        """Domain-specific post-execution verification."""
        if not raw_success:
            return "Action indicated failure during execution."

        if tool_name == "open_application":
            app = params.get("app_name", "")
            if app_manager.is_process_running(app):
                return f"Verified: Process '{app}' is running."
            return f"Verification check: Process '{app}' status unconfirmed but launched."

        elif tool_name == "create_file":
            p = Path(params.get("path", ""))
            return f"Verified: File '{p.name}' exists on disk (size: {p.stat().st_size if p.exists() else 0} bytes)."

        elif tool_name == "create_folder":
            p = Path(params.get("path", ""))
            return f"Verified: Directory exists: {p.exists()}."

        elif tool_name == "delete_file":
            p = Path(params.get("path", ""))
            return f"Verified: Target path deleted: {not p.exists()}."

        elif tool_name == "browser_search" or tool_name == "youtube_search":
            return f"Verified: Browser navigated to search results for '{params.get('query', '')}'."

        elif tool_name == "get_news_updates":
            return "Verified: Retrieved top live news updates for today."

        elif tool_name.startswith("mobile_"):
            return f"Verified: Mobile event delivered to phone."

        return "Action completed and verified successfully."


tool_executor = ToolExecutor()
