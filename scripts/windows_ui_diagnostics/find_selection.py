"""Find a selected list or tree item in Explorer or on the desktop."""

import uiautomation as auto


def _selected_item(root):
    for item, _depth in auto.WalkTree(
        root,
        getChildren=lambda control: control.GetChildren(),
        returnServer=False,
        maxDepth=4,
    ):
        if not isinstance(item, (auto.ListItemControl, auto.TreeItemControl)):
            continue
        try:
            if item.GetSelectionItemPattern().IsSelected:
                return item
        except Exception:
            pass
    return None


def find_selected_item():
    auto.SetGlobalSearchTimeout(2.0)
    foreground = auto.GetForegroundControl()
    print(f"Foreground window: {foreground.Name} ({foreground.ClassName})")

    selected = _selected_item(foreground)
    if selected is None:
        progman = auto.PaneControl(searchDepth=1, ClassName="Progman")
        if progman.Exists(0, 0):
            selected = _selected_item(progman)

    if selected is None:
        for worker in auto.GetRootControl().GetChildren():
            if worker.ClassName == "WorkerW":
                selected = _selected_item(worker)
                if selected is not None:
                    break

    if selected is None:
        print("No selected item found.")
        return None

    rect = selected.BoundingRectangle
    print(f"Found selected item: {selected.Name}; Rect: {rect.left}, {rect.top}")
    return selected


if __name__ == "__main__":
    find_selected_item()
