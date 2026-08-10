"""Support launching the package with ``python -m filekiller``."""

import sys

from .cli import run


if __name__ == "__main__":
    sys.exit(run())
