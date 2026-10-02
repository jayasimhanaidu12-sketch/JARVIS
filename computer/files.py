"""
File and filesystem operations for JARVIS.
Provides safe folder navigation, file creation, reading, and verified deletion.
"""

import os
import shutil
from pathlib import Path
from typing import Tuple, List, Optional
from core.permissions import permission_manager
from core.memory import memory


class FileManager:
    def open_path(self, target_path: str) -> Tuple[bool, str]:
        """Opens a file or folder in default system handler."""
        path = Path(target_path).expanduser().resolve()
        if not path.exists():
            return False, f"Path does not exist: {path}"

        try:
            os.startfile(str(path))
            memory.set_active_path(str(path))
            return True, f"Opened {path.name}"
        except Exception as e:
            return False, f"Failed to open {path}: {e}"

    def create_folder(self, folder_path: str) -> Tuple[bool, str]:
        """Creates a directory if it doesn't already exist."""
        path = Path(folder_path).expanduser().resolve()
        try:
            path.mkdir(parents=True, exist_ok=True)
            memory.set_active_path(str(path))
            return True, f"Directory created: {path}"
        except Exception as e:
            return False, f"Failed to create directory {path}: {e}"

    def create_file(self, file_path: str, content: str = "") -> Tuple[bool, str]:
        """Creates a new file with optional content."""
        path = Path(file_path).expanduser().resolve()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            memory.set_active_path(str(path))
            return True, f"File created: {path.name}"
        except Exception as e:
            return False, f"Failed to create file {path}: {e}"

    def read_file(self, file_path: str, max_lines: int = 100) -> Tuple[bool, str]:
        """Reads contents of a text file."""
        path = Path(file_path).expanduser().resolve()
        if not path.is_file():
            return False, f"File not found: {path}"

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = [f.readline() for _ in range(max_lines)]
            memory.set_active_path(str(path))
            return True, "".join(lines)
        except Exception as e:
            return False, f"Error reading file {path}: {e}"

    def rename_path(self, old_path: str, new_name: str) -> Tuple[bool, str]:
        """Renames a file or folder."""
        src = Path(old_path).expanduser().resolve()
        if not src.exists():
            return False, f"Target path does not exist: {src}"

        dst = src.parent / new_name
        try:
            src.rename(dst)
            memory.set_active_path(str(dst))
            return True, f"Renamed to {new_name}"
        except Exception as e:
            return False, f"Failed to rename: {e}"

    def delete_path(self, target_path: str) -> Tuple[bool, str]:
        """
        Deletes a file or directory.
        Protected by the safety/permissions layer.
        """
        path = Path(target_path).expanduser().resolve()
        if not path.exists():
            return False, f"Cannot delete non-existent path: {path}"

        # Enforce safety confirmation barrier
        tool_name = "delete_directory" if path.is_dir() else "delete_file"
        try:
            permission_manager.verify_permission(
                tool_name=tool_name,
                params={"path": str(path)},
                description=f"This will permanently delete {'folder' if path.is_dir() else 'file'}: {path}",
            )
        except Exception as e:
            return False, str(e)

        try:
            if path.is_dir():
                import stat

                def _on_rm_error(func, p, _):
                    try:
                        os.chmod(p, stat.S_IWRITE)
                        func(p)
                    except Exception:
                        pass

                shutil.rmtree(path, onerror=_on_rm_error)
                return True, f"Deleted directory: {path.name}"
            else:
                path.unlink()
                return True, f"Deleted file: {path.name}"
        except Exception as e:
            return False, f"Failed to delete {path}: {e}"

    def list_directory(self, folder_path: str = ".") -> Tuple[bool, List[str]]:
        """Lists files and folders inside directory."""
        path = Path(folder_path).expanduser().resolve()
        if not path.is_dir():
            return False, []
        try:
            entries = [f"{'[DIR] ' if p.is_dir() else '[FILE] '}{p.name}" for p in path.iterdir()]
            return True, sorted(entries)
        except Exception:
            return False, []


file_manager = FileManager()
