"""Command-line parsing and application startup."""

import argparse
import os
import sys

from .config import CONFIG_ENV_VAR, ResourceConfig, ResourceConfigError
from .platform_windows import register_context_menu
from .runtime import configure_qt_media_backend


def parse_arguments(argv=None):
    parser = argparse.ArgumentParser(description="FileKiller desktop animation")
    parser.add_argument(
        "--config",
        help=(
            "Resource configuration JSON. Relative resource paths inside it are "
            "resolved from the configuration file's directory."
        ),
    )
    parser.add_argument("target", nargs="?", help="File to move to the recycle bin")
    return parser.parse_args(argv)


def run(argv=None):
    """Load configuration, create the Qt application, and return its exit code."""

    configure_qt_media_backend()
    args = parse_arguments(argv)
    config_override = args.config or os.environ.get(CONFIG_ENV_VAR)
    try:
        resources = ResourceConfig.load(config_override)
    except ResourceConfigError as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc

    register_context_menu(
        resources.source_path if config_override else None,
        label=resources.context_menu_label,
    )

    # Delay UI imports so configuration and CLI helpers stay cheap to inspect
    # and test without creating a graphical application.
    from PyQt6.QtWidgets import QApplication

    from .window import FileKillerWindow

    app = QApplication([sys.argv[0]])
    window = FileKillerWindow(args.target, resources)
    window.show()
    return app.exec()
