"""The app's home (beat list) and side drawer."""

from __future__ import annotations

import time

from qa.app.screen import BaseScreen

MENU = ("Open navigation menu", "menuIcon", "Menu")


class HomeScreen(BaseScreen):
    marker = "Sync"

    def open_drawer(self) -> None:
        for name in MENU:
            if self.device.find(name):
                self.device.tap(name, timeout=5)
                return
        raise AssertionError(f"no drawer button on screen; it shows {self.device.texts()[:15]}")

    def go_to(self, *entries: str) -> str:
        """Open a drawer entry by any of its spellings (companies rename them: "Tour Plan Approval" / "Tout Plan
        Approval"); returns the one tapped."""
        self.open_drawer()
        for _ in range(4):
            for entry in entries:
                if self.device.find(entry):
                    self.device.tap(entry)
                    return entry
            self.device.swipe_up()
        raise AssertionError(f"none of {entries} in the drawer")

    def sync_all(self, timeout: float = 240) -> None:
        self.go_to("Sync All", "Sync")
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if not any(t in " ".join(self.device.texts()) for t in ("Syncing", "Please wait", "%")):
                break
            time.sleep(3)
        self.clear_interruptions()
