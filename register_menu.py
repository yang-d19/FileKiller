"""Install the Windows Explorer entry for launching FileKiller."""

import sys
from pathlib import Path

from filekiller.platform_windows import register_context_menu


def add_context_menu():
    """Backward-compatible name used by the original helper script."""

    executable = Path(sys.executable)
    if executable.name.lower() == "python.exe":
        pythonw = executable.with_name("pythonw.exe")
        if pythonw.is_file():
            executable = pythonw

    success = register_context_menu(executable=str(executable))
    if success:
        print("Successfully added context menu entry!")
    return success


if __name__ == "__main__":
    add_context_menu()
