"""
Application management for Windows.
Handles launching, terminating, switching, and verifying applications.
"""

import os
import time
import subprocess
from typing import List, Dict, Optional, Tuple
from core.context import context
from computer.windows import windows_manager


# Common application alias lookup table
APP_ALIASES: Dict[str, List[str]] = {
    "chrome": ["chrome.exe", "google chrome", "chrome"],
    "google chrome": ["chrome.exe", "chrome"],
    "edge": ["msedge.exe", "microsoft edge", "msedge"],
    "microsoft edge": ["msedge.exe"],
    "notepad": ["notepad.exe", "notepad"],
    "calculator": ["calc.exe", "calculator"],
    "explorer": ["explorer.exe", "file explorer"],
    "file explorer": ["explorer.exe"],
    "vscode": ["code.cmd", "code.exe", "code"],
    "vs code": ["code.cmd", "code.exe", "code"],
    "visual studio code": ["code.cmd", "code.exe", "code"],
    "terminal": ["wt.exe", "powershell.exe", "cmd.exe"],
    "powershell": ["powershell.exe"],
    "cmd": ["cmd.exe"],
    "task manager": ["taskmgr.exe"],
    "spotify": ["spotify.exe"],
    "word": ["winword.exe"],
    "excel": ["excel.exe"],
}


class ApplicationManager:
    def __init__(self):
        self.aliases = APP_ALIASES

    def resolve_app_command(self, app_name: str) -> str:
        """Translates natural app name into executable command or path."""
        clean = app_name.strip().lower()
        if clean in ("chrome", "google chrome"):
            for p in [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            ]:
                if os.path.exists(p):
                    return p
        elif clean in ("edge", "microsoft edge"):
            for p in [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            ]:
                if os.path.exists(p):
                    return p

        if clean in self.aliases:
            return self.aliases[clean][0]
        # Return as-is if no alias
        return app_name

    def is_process_running(self, process_name: str) -> bool:
        """Verifies whether a process is running on the system."""
        clean = process_name.lower().replace(".exe", "")
        try:
            output = subprocess.check_output(
                ["tasklist", "/FI", f"IMAGENAME eq {clean}*", "/FO", "CSV"],
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            # If the process is found, its name will appear in CSV output
            return clean in output.lower()
        except Exception:
            return False

    def get_running_process_list(self) -> List[str]:
        """Returns a list of currently active process executable names."""
        try:
            output = subprocess.check_output(
                ["tasklist", "/FO", "CSV", "/NH"],
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            procs = set()
            for line in output.strip().splitlines():
                parts = line.split(",")
                if parts:
                    name = parts[0].strip('"\n\r ').lower()
                    if name:
                        procs.add(name)
            return sorted(list(procs))
        except Exception:
            return []

    def open_application(self, app_name: str, wait_seconds: float = 2.0) -> Tuple[bool, str]:
        """
        Launches an application and verifies that it is active.
        Returns: (success: bool, status_message: str)
        """
        resolved_cmd = self.resolve_app_command(app_name)
        proc_key = resolved_cmd.lower().replace(".exe", "").replace(".cmd", "")

        try:
            # Check if already running and bring to focus
            if windows_manager.focus_window(app_name):
                context.update_application_state(app_name)
                return True, f"{app_name.capitalize()} is already open and brought to front."

            # Launch via os.startfile or subprocess
            try:
                os.startfile(resolved_cmd)
            except Exception:
                # Fallback to subprocess if startfile fails
                subprocess.Popen(
                    resolved_cmd,
                    shell=True,
                    creationflags=subprocess.DETACHED_PROCESS if os.name == "nt" else 0,
                )

            # Verification loop
            start_time = time.time()
            verified = False
            while time.time() - start_time < wait_seconds + 1.5:
                time.sleep(0.4)
                if self.is_process_running(proc_key) or windows_manager.find_window(app_name):
                    verified = True
                    break

            if verified:
                context.update_application_state(app_name)
                return True, f"Successfully launched {app_name}."
            else:
                return False, f"Attempted to open {app_name}, but the process was not detected within timeout."

        except Exception as e:
            return False, f"Failed to launch {app_name}: {str(e)}"

    def close_application(self, app_name: str) -> Tuple[bool, str]:
        """
        Closes an application cleanly first via WM_CLOSE,
        or taskkill if necessary.
        """
        resolved_cmd = self.resolve_app_command(app_name)
        proc_key = resolved_cmd.lower()
        if not proc_key.endswith(".exe"):
            proc_key += ".exe"

        # Try closing window cleanly first
        closed_cleanly = windows_manager.close_window(app_name)
        time.sleep(0.5)

        if not self.is_process_running(proc_key.replace(".exe", "")):
            return True, f"{app_name.capitalize()} closed successfully."

        # If still running, attempt standard taskkill
        try:
            subprocess.run(
                ["taskkill", "/IM", proc_key, "/T"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            time.sleep(0.5)
            if not self.is_process_running(proc_key.replace(".exe", "")):
                return True, f"{app_name.capitalize()} has been terminated."
            else:
                return False, f"Could not terminate {app_name}."
        except Exception as e:
            return False, f"Error terminating {app_name}: {e}"

    def switch_to_application(self, app_name: str) -> Tuple[bool, str]:
        """Switches focus to an open application."""
        success = windows_manager.focus_window(app_name)
        if success:
            return True, f"Switched to {app_name}."
        else:
            return False, f"Could not find open window for '{app_name}'."


app_manager = ApplicationManager()
