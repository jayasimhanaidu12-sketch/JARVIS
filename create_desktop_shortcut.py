"""
Utility script to create a Windows Desktop Shortcut for JARVIS with custom icon.
"""

import os
import sys
from pathlib import Path


def create_shortcut():
    try:
        import win32com.client
    except ImportError:
        print("pywin32 is required to create a desktop shortcut.")
        return False

    shell = win32com.client.Dispatch("WScript.Shell")
    desktop = shell.SpecialFolders("Desktop")
    shortcut_path = os.path.join(desktop, "JARVIS.lnk")

    app_dir = Path(__file__).resolve().parent
    vbs_path = app_dir / "JARVIS.vbs"
    ico_path = app_dir / "assets" / "jarvis_icon.ico"

    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.TargetPath = "wscript.exe"
    shortcut.Arguments = f'"{vbs_path}"'
    shortcut.WorkingDirectory = str(app_dir)
    if ico_path.exists():
        shortcut.IconLocation = f"{ico_path}, 0"
    shortcut.Description = "JARVIS — Universal Voice-Controlled AI Agent"
    shortcut.Save()

    print(f"Windows Desktop shortcut created successfully at: {shortcut_path}")
    return True


if __name__ == "__main__":
    create_shortcut()
