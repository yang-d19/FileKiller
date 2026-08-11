"""Install the Windows Explorer entry for launching FileKiller."""

import sys
from pathlib import Path

from filekiller.config import ResourceConfig
from filekiller.platform_windows import register_context_menu


def preferred_executable(project_root=None, interpreter=None):
    """Prefer the windowed packaged app, falling back to a console-free Python."""

    project_root = Path(project_root or Path(__file__).resolve().parent)
    packaged_executable = project_root / "dist" / "FileKiller.exe"
    if packaged_executable.is_file():
        return packaged_executable

    executable = Path(interpreter or sys.executable)
    if executable.name.lower() == "python.exe":
        pythonw = executable.with_name("pythonw.exe")
        if pythonw.is_file():
            return pythonw
    return executable


def add_context_menu():
    """Backward-compatible name used by the original helper script."""

    resources = ResourceConfig.load()
    success = register_context_menu(
        executable=str(preferred_executable()), label=resources.context_menu_label
    )
    if success:
        print("Successfully added context menu entry!")
    return success


if __name__ == "__main__":
    add_context_menu()
