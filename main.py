"""Backward-compatible entry point for FileKiller.

Application code lives in the :mod:`filekiller` package.  Imports are re-exported
here so existing scripts that used the original single-file module keep working.
"""

import sys

from filekiller.runtime import configure_qt_media_backend


configure_qt_media_backend()

from filekiller.animation import (  # noqa: E402
    DEFAULT_COLS,
    DEFAULT_ROWS,
    SpriteAnimator,
)
from filekiller.cli import parse_arguments, run  # noqa: E402
from filekiller.config import (  # noqa: E402
    CONFIG_ENV_VAR,
    ResourceConfig,
    ResourceConfigError,
)
from filekiller.platform_windows import register_context_menu  # noqa: E402
from filekiller.widgets import BubbleWidget, ChoicesWidget  # noqa: E402
from filekiller.window import FileKillerWindow, MonsterDeleter  # noqa: E402


COLS = DEFAULT_COLS
ROWS = DEFAULT_ROWS

__all__ = [
    "BubbleWidget",
    "ChoicesWidget",
    "COLS",
    "CONFIG_ENV_VAR",
    "FileKillerWindow",
    "MonsterDeleter",
    "ResourceConfig",
    "ResourceConfigError",
    "ROWS",
    "SpriteAnimator",
    "parse_arguments",
    "register_context_menu",
    "run",
]


if __name__ == "__main__":
    sys.exit(run())
