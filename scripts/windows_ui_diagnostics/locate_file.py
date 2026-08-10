"""Find a named file in the Windows UI Automation tree."""

import os
import sys

import uiautomation as auto


def find_file_position(filepath):
    filename = os.path.basename(filepath)
    filename_without_extension = os.path.splitext(filename)[0]
    print(f"Searching for: {filename} or {filename_without_extension}")

    auto.SetGlobalSearchTimeout(1.0)
    item = auto.ListItemControl(Name=filename)
    if not item.Exists(0, 0):
        item = auto.ListItemControl(Name=filename_without_extension)

    if item.Exists(0, 0):
        rect = item.BoundingRectangle
        print(f"Found globally! Rect: {rect.left}, {rect.top}")
        return rect

    print("Not found.")
    return None


if __name__ == "__main__" and len(sys.argv) > 1:
    find_file_position(sys.argv[1])
