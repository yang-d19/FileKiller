"""Windows shell integration isolated from cross-platform application code."""

import os
import sys
from pathlib import Path


CONTEXT_MENU_KEY = r"Software\Classes\*\shell\SummonMonster"
CONTEXT_MENU_LABEL = "召唤大将怪兽摧毁"


def build_context_menu_command(
    config_path=None,
    *,
    executable=None,
    entry_script=None,
    frozen=None,
):
    """Build the registry command and icon strings without touching registry."""

    executable = str(executable or sys.executable)
    entry_script = str(
        Path(entry_script or Path(__file__).resolve().parents[1] / "main.py")
        .expanduser()
        .resolve()
    )
    if frozen is None:
        frozen = executable.lower().endswith(".exe") and (
            "python" not in executable.lower()
        )

    config_argument = ""
    if config_path:
        resolved_config = os.path.abspath(os.path.expandvars(str(config_path)))
        config_argument = f' --config "{resolved_config}"'

    if frozen:
        return f'"{executable}"{config_argument} "%1"', f'"{executable}",0'

    command = f'"{executable}" "{entry_script}"{config_argument} "%1"'
    return command, "shell32.dll,32"


def register_context_menu(config_path=None, *, executable=None):
    """Create or refresh the current-user Windows file context-menu entry."""

    if sys.platform != "win32":
        print("Context-menu registration is only available on Windows.")
        return False

    try:
        import winreg

        command, icon = build_context_menu_command(
            config_path, executable=executable
        )
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, CONTEXT_MENU_KEY) as key:
            winreg.SetValue(key, "", winreg.REG_SZ, CONTEXT_MENU_LABEL)
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, icon)

        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER, CONTEXT_MENU_KEY + r"\command"
        ) as command_key:
            winreg.SetValue(command_key, "", winreg.REG_SZ, command)
    except Exception as exc:
        print(f"Error registering menu: {exc}")
        return False

    return True
