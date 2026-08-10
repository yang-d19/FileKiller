"""Print UI Automation list items found on the Windows desktop."""

import uiautomation as auto


def find_on_desktop():
    desktop_pane = auto.PaneControl(searchDepth=1, ClassName="Progman")
    if not desktop_pane.Exists(0, 0):
        for worker in auto.GetRootControl().GetChildren():
            if worker.ClassName == "WorkerW":
                list_control = worker.ListControl()
                if list_control.Exists(0, 0):
                    desktop_pane = worker
                    break

    if desktop_pane and desktop_pane.Exists(0, 0):
        print(f"Found desktop pane: {desktop_pane.ClassName}")
        for item, _depth in auto.WalkTree(
            desktop_pane,
            getChildren=lambda control: control.GetChildren(),
            returnServer=False,
            maxDepth=4,
        ):
            if isinstance(item, auto.ListItemControl):
                print(f"Item: {item.Name}")


if __name__ == "__main__":
    find_on_desktop()
