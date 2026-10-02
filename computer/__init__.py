"""Computer control package."""
from computer.mouse import mouse
from computer.keyboard import keyboard
from computer.windows import windows_manager
from computer.applications import app_manager
from computer.files import file_manager
from computer.system import system_controller

__all__ = [
    "mouse",
    "keyboard",
    "windows_manager",
    "app_manager",
    "file_manager",
    "system_controller",
]
