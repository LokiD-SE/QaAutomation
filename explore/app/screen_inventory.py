"""Explore app screens before writing tests: walk a drawer path and record what each screen shows.

    python -m explore.app.screen_inventory                       # the screen that is open now
    python -m explore.app.screen_inventory --drawer "Claims" --tap "To Approve"   [--serial emulator-5554]

Writes explore/out/app/<screen>/ - screen.png, screen.xml (the uiautomator dump) and inventory.json (texts, the
clickable elements with resource-id, the input fields with their hint). Taps only what you name; it never saves.
"""

from __future__ import annotations

import argparse
import json
import re

from qa.app.device import Device
from qa.config import ROOT, settings
from screens.app.home import HomeScreen

OUT = ROOT / "explore" / "out" / "app"


def record(device: Device, name: str) -> None:
    folder = OUT / re.sub(r"[^\w.-]+", "_", name)
    folder.mkdir(parents=True, exist_ok=True)
    device.screenshot(folder / "screen.png")
    nodes = device.dump()
    (folder / "screen.xml").write_text(device.adb("exec-out", "uiautomator dump /dev/tty"), encoding="utf-8")
    inventory = {
        "texts": [n.label for n in nodes if n.label],
        "clickable": [{"label": n.label, "id": n.resource_id.split("/")[-1], "class": n.clazz.split(".")[-1]}
                      for n in nodes if n.clickable],
        "inputs": [{"hint": n.text, "id": n.resource_id.split("/")[-1]} for n in nodes if n.clazz.endswith("EditText")],
    }
    (folder / "inventory.json").write_text(json.dumps(inventory, indent=1), encoding="utf-8")
    print(f"{name}: {len(inventory['clickable'])} clickable, {len(inventory['inputs'])} inputs -> {folder}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--serial", default="")
    parser.add_argument("--drawer", action="append", default=[], help="drawer entry to open (spellings: repeat)")
    parser.add_argument("--tap", action="append", default=[], help="then tap these, in order, recording each screen")
    args = parser.parse_args(argv)
    cfg = settings()
    device = Device(args.serial or cfg.device_serial, cfg.app_package).acquire()
    try:
        record(device, "current")
        if args.drawer:
            entry = HomeScreen(device).go_to(*args.drawer)
            record(device, entry)
        for name in args.tap:
            device.tap(name)
            record(device, name)
    finally:
        device.release()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
