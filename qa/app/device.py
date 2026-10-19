"""Drives the Bizom Android app over adb: `uiautomator dump` to read the screen, `input` to act.

No Appium server and no agent installed on the device, on purpose:
- nothing to start before a run, and the dependency list stays at pytest + Playwright;
- an on-device UiAutomation agent (uiautomator2 / Appium) holds the UI automation service, which makes every other
  `uiautomator dump` on that device fail - Greybox runs use the same devices, so the suite must not hold it.
Elements are found by what they say (text, content-desc, resource-id), never by coordinates.
A per-device lock keeps two suite processes off one device. `Device` is the only class tests and screens use, so an
Appium-backed implementation can replace it later without touching them.
"""

from __future__ import annotations

import fcntl
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from qa.config import ROOT

_BOUNDS = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")
LOCK_DIR = ROOT / "reports" / ".locks"


class DeviceError(AssertionError):
    pass


@dataclass(frozen=True)
class Node:
    text: str
    desc: str
    resource_id: str
    clazz: str
    bounds: tuple[int, int, int, int]
    clickable: bool
    enabled: bool

    @property
    def center(self) -> tuple[int, int]:
        left, top, right, bottom = self.bounds
        return (left + right) // 2, (top + bottom) // 2

    @property
    def label(self) -> str:
        return self.text or self.desc or self.resource_id.split("/")[-1]

    def matches(self, wanted: str, exact: bool = False) -> bool:
        wanted = wanted.lower()
        fields = [self.text.lower(), self.desc.lower(), self.resource_id.split("/")[-1].lower()]
        return wanted in fields if exact else any(wanted in f for f in fields if f)


def parse(xml: str) -> list[Node]:
    nodes = []
    for element in ET.fromstring(xml).iter("node"):
        match = _BOUNDS.match(element.get("bounds", ""))
        if match:
            nodes.append(Node((element.get("text") or "").strip(), (element.get("content-desc") or "").strip(),
                              element.get("resource-id") or "", element.get("class") or "",
                              tuple(int(g) for g in match.groups()), element.get("clickable") == "true",
                              element.get("enabled") == "true"))
    return nodes


def devices() -> list[str]:
    out = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=20).stdout
    return [line.split()[0] for line in out.splitlines()[1:] if line.strip().endswith("device")]


class Device:
    def __init__(self, serial: str = "", package: str = "co.bizom.apps"):
        found = devices()
        if serial and serial not in found:
            raise DeviceError(f"device {serial} is not connected (adb sees {found or 'none'})")
        if not found:
            raise DeviceError("no Android device on adb")
        self.serial, self.package = serial or found[0], package
        self._lock = None

    # -- the device lock ---------------------------------------------------------------------------------------
    def acquire(self) -> Device:
        LOCK_DIR.mkdir(parents=True, exist_ok=True)
        self._lock = open(LOCK_DIR / f"{self.serial.replace(':', '_')}.lock", "w")  # noqa: SIM115
        try:
            fcntl.flock(self._lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise DeviceError(f"device {self.serial} is in use by another suite run") from exc
        return self

    def release(self) -> None:
        if self._lock:
            fcntl.flock(self._lock, fcntl.LOCK_UN)
            self._lock.close()
            self._lock = None

    # -- adb ----------------------------------------------------------------------------------------------------
    def adb(self, *args: str, binary: bool = False, timeout: int = 60):
        done = subprocess.run(["adb", "-s", self.serial, *args], capture_output=True, timeout=timeout)
        if done.returncode != 0:
            raise DeviceError(f"adb {' '.join(args)}: {done.stderr.decode(errors='replace').strip()}")
        return done.stdout if binary else done.stdout.decode(errors="replace")

    def shell(self, command: str) -> str:
        return self.adb("shell", command)

    # -- reading the screen -------------------------------------------------------------------------------------
    def dump(self, retries: int = 3) -> list[Node]:
        """Every node on screen; retried because uiautomator refuses to dump while the UI animates."""
        last = ""
        for _ in range(retries):
            xml = self.adb("exec-out", "uiautomator dump /dev/tty", binary=True).decode(errors="replace")
            start, end = xml.find("<?xml"), xml.rfind("</hierarchy>")
            if start >= 0 and end > start:
                return parse(xml[start:end + len("</hierarchy>")])
            last = xml[:200]
            time.sleep(1.5)
        raise DeviceError(f"could not read the screen: {last}")

    def texts(self) -> list[str]:
        return [n.label for n in self.dump() if n.label]

    def find(self, text: str, exact: bool = False) -> Node | None:
        nodes = [n for n in self.dump() if n.matches(text, exact)]
        return next((n for n in nodes if n.clickable), nodes[0] if nodes else None)

    def wait_for(self, text: str, timeout: float = 20, exact: bool = False) -> Node:
        deadline = time.monotonic() + timeout
        while True:
            node = self.find(text, exact)
            if node:
                return node
            if time.monotonic() > deadline:
                raise DeviceError(f"'{text}' did not appear in {timeout}s; screen shows {self.texts()[:15]}")
            time.sleep(1)

    def has(self, text: str) -> bool:
        return self.find(text) is not None

    # -- acting -------------------------------------------------------------------------------------------------
    def tap(self, text: str, exact: bool = False, timeout: float = 20, settle: float = 1.2) -> Node:
        node = self.wait_for(text, timeout, exact)
        x, y = node.center
        self.shell(f"input tap {x} {y}")
        time.sleep(settle)
        return node

    def type(self, text: str, value: str, clear: int = 20) -> None:
        """Type into the field `text` names (its hint, label or id)."""
        self.tap(text)
        self.shell("input keyevent " + " ".join(["KEYCODE_DEL"] * clear))
        self.shell("input text " + value.replace(" ", "%s").replace("'", "\\'"))

    def back(self, settle: float = 1.0) -> None:
        self.shell("input keyevent KEYCODE_BACK")
        time.sleep(settle)

    def swipe_up(self, settle: float = 1.0) -> None:
        self.shell("input swipe 540 1600 540 600 400")
        time.sleep(settle)

    def screenshot(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.adb("exec-out", "screencap -p", binary=True))
        return path

    # -- the app ------------------------------------------------------------------------------------------------
    def launch(self, settle: float = 5.0) -> None:
        self.shell(f"monkey -p {self.package} -c android.intent.category.LAUNCHER 1")
        time.sleep(settle)

    def stop(self) -> None:
        self.shell(f"am force-stop {self.package}")

    def is_installed(self) -> bool:
        return self.package in self.shell(f"pm list packages {self.package}")
