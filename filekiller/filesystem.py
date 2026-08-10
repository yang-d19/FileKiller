"""File operations kept separate from the animation state machine."""

from pathlib import Path

from send2trash import send2trash


def move_to_trash(target_file):
    """Move an existing target to the OS recycle bin.

    Returns ``True`` only when a file was handed to the recycle-bin provider.
    Missing targets are harmless because desktop selections can disappear while
    the animation is running.
    """

    if not target_file:
        return False

    target = Path(target_file)
    if not target.exists():
        print(f"Target no longer exists: {target}")
        return False

    try:
        send2trash(str(target))
    except Exception as exc:
        print(f"Unable to move target to recycle bin: {exc}")
        return False

    return True
