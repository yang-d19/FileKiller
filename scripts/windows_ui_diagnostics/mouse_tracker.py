"""Record the latest right-click coordinate in the temporary directory."""

import tempfile
from pathlib import Path

from pynput import mouse


def on_click(x, y, button, pressed):
    if button == mouse.Button.right and pressed:
        coordinate_file = Path(tempfile.gettempdir()) / "last_right_click.txt"
        try:
            coordinate_file.write_text(f"{int(x)},{int(y)}", encoding="utf-8")
        except OSError:
            pass


def start_tracking():
    print("Mouse tracker started. Listening for right clicks...")
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()


if __name__ == "__main__":
    start_tracking()
