"""Drives the Bizom Android app. Two drivers behind one interface - screens and tests never know which runs:

- `AppiumDevice` (default, QA_APP_DRIVER=appium): an Appium UiAutomator2 session - real waits, gestures, typing into
  the focused field, the protocol device farms speak. Its on-device server holds the UI automation service while a
  session is open, so Greybox's `uiautomator dump` fails on that device until `close()` frees it again.
- `Device` (QA_APP_DRIVER=adb): plain adb - `uiautomator dump` to read the screen, `input` to act. No server, no agent.

Elements are found by what they say (text, content-desc, resource-id), never by coordinates.
A per-device lock keeps two suite processes off one device. `open_device()` builds the configured one.
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
    """Nodes of a `uiautomator dump` (<node> elements) or an Appium page source (elements named by class)."""
    nodes = []
    for element in ET.fromstring(xml).iter():
        match = _BOUNDS.match(element.get("bounds", ""))
        if match:
            nodes.append(Node((element.get("text") or "").strip(), (element.get("content-desc") or "").strip(),
                              element.get("resource-id") or "", element.get("class") or element.tag,
                              tuple(int(g) for g in match.groups()), element.get("clickable") == "true",
                              element.get("enabled") == "true"))
    return nodes


def devices() -> list[str]:
    out = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=20).stdout
    return [line.split()[0] for line in out.splitlines()[1:] if line.strip().endswith("device")]


class Device:
    driver_name = "adb"

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

    def close(self) -> None:
        self.release()

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


# Appium's on-device server; force-stopping both frees the UI automation service for Greybox's `uiautomator dump`.
APPIUM_DEVICE_PACKAGES = ("io.appium.uiautomator2.server.test", "io.appium.uiautomator2.server")


class AppiumDevice(Device):
    """`Device` over an Appium UiAutomator2 session. Reading the screen and the lock are shared with `Device`; taps,
    typing, gestures and screenshots go through the session. `close()` ends the session, stops the Appium server this
    run started and frees the device for Greybox."""

    driver_name = "appium"

    def __init__(self, serial: str = "", package: str = "co.bizom.apps", server_url: str = ""):
        super().__init__(serial, package)
        self.server_url = server_url
        self.driver = None
        self._server = None

    def start(self) -> AppiumDevice:
        from appium import webdriver
        from appium.options.android import UiAutomator2Options
        from selenium.common.exceptions import WebDriverException

        from qa.app.appium_server import AppiumServerError, ensure_server

        try:
            self._server = ensure_server(self.server_url)
        except AppiumServerError as exc:
            raise DeviceError(str(exc)) from exc
        options = UiAutomator2Options().load_capabilities({
            "platformName": "Android",
            "appium:automationName": "UiAutomator2",
            "appium:udid": self.serial,
            "appium:noReset": True,  # keep the app's login and synced data, as a tester's device would
            "appium:newCommandTimeout": 300,
            "appium:uiautomator2ServerInstallTimeout": 180_000,  # the first install on a device takes > 20 s
            "appium:adbExecTimeout": 60_000,
        })
        try:
            self.driver = webdriver.Remote(self.server_url, options=options)
        except WebDriverException as exc:
            self.close()
            raise DeviceError(f"no Appium session on {self.serial}: {str(exc.msg or exc).splitlines()[0]}") from exc
        return self

    # -- reading the screen -------------------------------------------------------------------------------------
    def dump(self, retries: int = 3) -> list[Node]:
        last = ""
        for _ in range(retries):
            try:
                return parse(self.driver.page_source)
            except Exception as exc:  # noqa: BLE001 - a source taken mid-transition; read again
                last = str(exc)[:200]
                time.sleep(1)
        raise DeviceError(f"could not read the screen: {last}")

    # -- acting -------------------------------------------------------------------------------------------------
    def tap(self, text: str, exact: bool = False, timeout: float = 20, settle: float = 0.8) -> Node:
        node = self.wait_for(text, timeout, exact)
        x, y = node.center
        self.driver.execute_script("mobile: clickGesture", {"x": x, "y": y})
        time.sleep(settle)
        return node

    def type(self, text: str, value: str, clear: int = 20) -> None:
        """Type into the field `text` names (its hint, label or id): tap it, then replace the focused field's value."""
        from appium.webdriver.common.appiumby import AppiumBy

        self.tap(text)
        field = self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().focused(true)")
        field.clear()
        field.send_keys(value)

    def back(self, settle: float = 1.0) -> None:
        self.driver.back()
        time.sleep(settle)

    def swipe_up(self, settle: float = 1.0) -> None:
        size = self.driver.get_window_size()
        self.driver.execute_script("mobile: swipeGesture", {
            "left": size["width"] // 10, "top": size["height"] // 4, "width": size["width"] * 8 // 10,
            "height": size["height"] // 2, "direction": "up", "percent": 0.75})
        time.sleep(settle)

    def screenshot(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.driver.get_screenshot_as_png())
        return path

    # -- the app ------------------------------------------------------------------------------------------------
    def launch(self, settle: float = 3.0) -> None:
        self.driver.activate_app(self.package)
        time.sleep(settle)

    def stop(self) -> None:
        self.driver.terminate_app(self.package)

    # -- teardown -----------------------------------------------------------------------------------------------
    def free_for_greybox(self) -> bool:
        """Stop Appium's on-device server so `uiautomator dump` works again; True when it does."""
        for package in APPIUM_DEVICE_PACKAGES:
            try:
                self.shell(f"am force-stop {package}")
            except DeviceError:
                pass
        for _ in range(3):
            try:
                if "</hierarchy>" in self.adb("exec-out", "uiautomator dump /dev/tty", binary=True).decode(errors="replace"):
                    return True
            except DeviceError:
                pass
            time.sleep(1.5)
        return False

    def close(self) -> None:
        if self.driver is not None:
            try:
                self.driver.quit()
            except Exception:  # noqa: BLE001 - a session already gone is fine; the device still needs freeing
                pass
            self.driver = None
        self.free_for_greybox()
        if self._server is not None:
            self._server.stop()
            self._server = None
        self.release()


def open_device(settings) -> Device:
    """The configured device (QA_APP_DRIVER: appium | adb), locked, with the app installed and - for Appium - a
    session open. Raises DeviceError with the reason when the device cannot be used."""
    if settings.app_driver not in ("appium", "adb"):
        raise DeviceError(f"QA_APP_DRIVER={settings.app_driver}: use appium or adb")
    device = (AppiumDevice(settings.device_serial, settings.app_package, settings.appium_url)
              if settings.app_driver == "appium" else Device(settings.device_serial, settings.app_package))
    device.acquire()
    try:
        if not device.is_installed():
            raise DeviceError(f"{settings.app_package} is not installed on {device.serial}")
        if isinstance(device, AppiumDevice):
            device.start()
    except BaseException:
        device.close()
        raise
    return device
