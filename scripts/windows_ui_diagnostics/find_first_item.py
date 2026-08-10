"""Print the first Windows UI Automation list item found."""

import uiautomation as auto


def find_first_item():
    auto.SetGlobalSearchTimeout(3.0)
    desktop = auto.GetRootControl()
    for item, _depth in auto.WalkTree(
        desktop,
        getChildren=lambda control: control.GetChildren(),
        maxDepth=5,
    ):
        if isinstance(item, auto.ListItemControl):
            print(f"Found item: {item.Name}, Rect: {item.BoundingRectangle}")
            return item
    return None


if __name__ == "__main__":
    find_first_item()
