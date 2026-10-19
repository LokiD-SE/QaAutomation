"""BaseScreen: what every app screen object needs. Screen objects in screens/app/ subclass it."""

from __future__ import annotations

import time

from qa.app.device import Device
from qa.config import Login

# Pop-ups that stand in front of every screen after login or sync; handled, never asserted on.
INTERRUPTIONS = ("Allow", "While using the app", "Only this time", "OK", "Okay", "Skip", "Later", "Not now")


class BaseScreen:
    marker = ""  # a text only this screen shows - used by is_open()

    def __init__(self, device: Device):
        self.device = device

    def is_open(self, timeout: float = 15) -> bool:
        try:
            self.device.wait_for(self.marker, timeout)
            return True
        except AssertionError:
            return False

    def clear_interruptions(self, rounds: int = 3) -> list[str]:
        handled = []
        for _ in range(rounds):
            node = next((n for n in self.device.dump() if n.clickable and n.label in INTERRUPTIONS), None)
            if not node:
                break
            self.device.tap(node.label, exact=True, timeout=3)
            handled.append(node.label)
        return handled


class LoginScreen(BaseScreen):
    marker = "Username"

    def login(self, who: Login, timeout: float = 60) -> None:
        self.device.type("Username", who.user)
        self.device.type("Password", who.password)
        self.device.tap("Login", exact=True)
        deadline = time.monotonic() + timeout
        while self.device.has("Username") and time.monotonic() < deadline:
            time.sleep(2)
        if self.device.has("Username"):
            raise AssertionError(f"app login as {who.user} stayed on the login screen")
        self.clear_interruptions()
