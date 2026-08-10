"""Print the UI Automation control under a screen coordinate."""

import sys

import uiautomation as auto


def inspect_point(x, y):
    control = auto.ControlFromPoint(x, y)
    print(f"Control under {x}, {y}: {control.Name} ({control.ClassName})")


if __name__ == "__main__" and len(sys.argv) > 2:
    inspect_point(int(sys.argv[1]), int(sys.argv[2]))
