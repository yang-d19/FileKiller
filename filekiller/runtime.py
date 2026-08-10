"""Process-wide runtime setup that must happen before importing QtMultimedia."""

import os
import sys


def configure_qt_media_backend() -> None:
    """Prefer Windows Media Foundation when running on Windows.

    Some supported PyQt6 wheels expose an FFmpeg plugin without shipping all
    matching DLLs. Qt may select that unusable plugin unless the native backend
    is chosen before QtMultimedia is imported.
    """

    if sys.platform == "win32":
        # Preserve the original project's known-good Windows audio behavior,
        # even when a parent process happens to provide a different backend.
        os.environ["QT_MEDIA_BACKEND"] = "windows"
