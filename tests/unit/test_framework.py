"""The app framework itself - config, device parsing and drivers, evidence. No portal, device or secret needed."""

from __future__ import annotations

import json

import pytest

from qa import config as cfg
from qa.app import device as dev
from qa.evidence import Evidence, mask

pytestmark = pytest.mark.unit

XML = """<?xml version='1.0' encoding='UTF-8'?><hierarchy rotation="0">
<node text="" content-desc="Open navigation menu" resource-id="" class="android.widget.ImageButton" bounds="[0,60][120,180]" clickable="true" enabled="true"/>
<node text="Claims" content-desc="" resource-id="co.bizom.apps:id/title" class="android.widget.TextView" bounds="[200,300][600,360]" clickable="false" enabled="true"/>
<node text="" content-desc="" resource-id="co.bizom.apps:id/username" class="android.widget.EditText" bounds="[40,500][1040,600]" clickable="true" enabled="true"/>
</hierarchy>"""


@pytest.fixture
def env(monkeypatch, tmp_path):
    monkeypatch.setattr(cfg, "ROOT", tmp_path)  # no real .env
    for key in [k for k in __import__("os").environ if k.startswith(("BIZOM_", "QA_"))]:
        monkeypatch.delenv(key)
    return monkeypatch


def test_settings_per_company_and_role_logins(env):
    env.setenv("BIZOM_WEB_URL", "https://default.example/")
    env.setenv("BIZOM_WEB_URL_STAGINGX", "https://x.example")
    env.setenv("BIZOM_WEB_USER", "admin1")
    env.setenv("BIZOM_WEB_PASSWORD", "p1")
    env.setenv("BIZOM_WEB_ROLE_ZONE_MANAGER_STAGINGX", "zm/p2")
    env.setenv("BIZOM_WEB_ROLE_APPROVER_STAGINGX", "n/a")
    s = cfg.settings("stagingx")
    assert s.web_url == "https://x.example"
    assert s.web_login() == cfg.Login("admin1", "p1")  # falls back to the default company's admin
    assert s.web_login("zone manager") == cfg.Login("zm", "p2")
    with pytest.raises(cfg.ConfigError, match="n/a"):
        s.web_login("APPROVER")
    with pytest.raises(cfg.ConfigError, match="BIZOM_WEB_ROLE_DSR"):
        s.web_login("DSR")
    assert cfg.settings("").web_url == "https://default.example"
    assert cfg.settings("").company == "default"  # from the portal host when QA_COMPANY is not set


def test_dotenv_does_not_override_the_environment(env, tmp_path):
    (tmp_path / ".env").write_text("BIZOM_WEB_USER=from_file\nBIZOM_WEB_PASSWORD='quoted'\n# comment\n")
    env.setenv("BIZOM_WEB_USER", "from_ci")
    cfg.load_dotenv(tmp_path / ".env")
    assert __import__("os").environ["BIZOM_WEB_USER"] == "from_ci"
    assert __import__("os").environ["BIZOM_WEB_PASSWORD"] == "quoted"


def test_screen_parse_and_find_by_text_desc_or_id():
    nodes = dev.parse(XML)
    assert [n.label for n in nodes] == ["Open navigation menu", "Claims", "username"]
    assert nodes[0].center == (60, 120)
    assert nodes[1].matches("claim") and not nodes[1].matches("claim", exact=True)
    assert nodes[2].matches("username", exact=True)


def test_device_reads_the_screen_and_taps_by_text(monkeypatch):
    calls = []

    def run(cmd, capture_output, timeout, text=False):
        calls.append(cmd)
        out = "List of devices attached\nemulator-5554\tdevice\n" if cmd[:2] == ["adb", "devices"] else (
            XML.encode() if "exec-out" in cmd else b"")
        return type("Done", (), {"returncode": 0, "stdout": out, "stderr": b""})()

    monkeypatch.setattr(dev.subprocess, "run", run)
    monkeypatch.setattr(dev.time, "sleep", lambda s: None)
    device = dev.Device()
    assert device.serial == "emulator-5554"
    node = device.tap("Open navigation menu")
    assert node.center == (60, 120)
    assert calls[-1] == ["adb", "-s", "emulator-5554", "shell", "input tap 60 120"]
    with pytest.raises(dev.DeviceError, match="did not appear"):
        device.wait_for("Not there", timeout=0)


def test_device_lock_keeps_a_second_run_off_the_device(monkeypatch, tmp_path):
    monkeypatch.setattr(dev, "LOCK_DIR", tmp_path)
    monkeypatch.setattr(dev, "devices", lambda: ["emulator-5554"])
    first = dev.Device().acquire()
    with pytest.raises(dev.DeviceError, match="in use"):
        dev.Device().acquire()
    first.release()
    dev.Device().acquire().release()


def test_evidence_masks_secrets_and_numbers_repeats(tmp_path, monkeypatch):
    import qa.evidence as ev

    monkeypatch.setattr(ev, "ARTIFACTS", tmp_path)
    assert mask({"user": "a", "password": "b", "nested": [{"X-Auth-Token": "t"}]}) == {
        "user": "a", "password": "***", "nested": [{"X-Auth-Token": "***"}]}
    e = Evidence("tests/app/x.py::test_a[1]")
    first, second = e.path("saved"), e.path("saved")
    first.write_text("x")
    assert first.name == "saved.png" and e.path("saved").name == "saved_02.png" and second.name == "saved.png"
    assert json.loads(e.json("api", {"token": "t"}).read_text()) == {"token": "***"}


APPIUM_SOURCE = """<?xml version='1.0' encoding='UTF-8' standalone='yes' ?><hierarchy index="0" class="hierarchy" rotation="0" width="1080" height="2205">
<android.widget.FrameLayout class="android.widget.FrameLayout" text="" content-desc="" resource-id="" bounds="[0,0][1080,2205]" clickable="false" enabled="true">
<android.widget.EditText class="android.widget.EditText" text="Username" content-desc="" resource-id="co.bizom.apps:id/username" bounds="[40,500][1040,600]" clickable="true" enabled="true"/>
</android.widget.FrameLayout></hierarchy>"""


class FakeDriver:
    def __init__(self):
        self.calls, self.page_source = [], APPIUM_SOURCE

    def execute_script(self, name, args):
        self.calls.append((name, args))

    def find_element(self, by, selector):
        self.calls.append(("find", selector))
        driver = self

        class Field:
            def clear(self):
                driver.calls.append(("clear",))

            def send_keys(self, value):
                driver.calls.append(("send_keys", value))
        return Field()

    def quit(self):
        self.calls.append(("quit",))


@pytest.fixture
def appium_device(monkeypatch, tmp_path):
    monkeypatch.setattr(dev, "LOCK_DIR", tmp_path)
    monkeypatch.setattr(dev, "devices", lambda: ["emulator-5554"])
    monkeypatch.setattr(dev.time, "sleep", lambda s: None)
    shell = []
    monkeypatch.setattr(dev.Device, "adb", lambda self, *a, binary=False, timeout=60:
                        shell.append(a) or (b"<hierarchy></hierarchy>" if binary else ""))
    device = dev.AppiumDevice(server_url="http://127.0.0.1:4723").acquire()
    device.driver = FakeDriver()
    return device, shell


def test_appium_source_parses_like_a_uiautomator_dump():
    nodes = dev.parse(APPIUM_SOURCE)
    assert [n.clazz for n in nodes] == ["android.widget.FrameLayout", "android.widget.EditText"]
    assert nodes[1].matches("username", exact=True) and nodes[1].center == (540, 550)


def test_appium_device_taps_and_types_through_the_session(appium_device):
    device, shell = appium_device
    device.type("Username", "salesman1")
    assert ("mobile: clickGesture", {"x": 540, "y": 550}) in device.driver.calls
    assert device.driver.calls[-2:] == [("clear",), ("send_keys", "salesman1")]
    assert not any(a[:2] == ("shell", "input tap 540 550") for a in shell)  # nothing went through adb input


def test_appium_close_ends_the_session_and_frees_the_device_for_greybox(appium_device, tmp_path):
    device, shell = appium_device
    fake = device.driver
    device.close()
    assert ("quit",) in fake.calls and device.driver is None
    assert [a for a in shell if a[0] == "shell"] == [("shell", f"am force-stop {p}") for p in dev.APPIUM_DEVICE_PACKAGES]
    assert ("exec-out", "uiautomator dump /dev/tty") in shell  # checked that Greybox can read the screen again
    dev.Device().acquire().release()  # and the lock is gone


def test_open_device_picks_the_driver_and_checks_the_app(monkeypatch, tmp_path):
    monkeypatch.setattr(dev, "LOCK_DIR", tmp_path)
    monkeypatch.setattr(dev, "devices", lambda: ["emulator-5554"])
    monkeypatch.setattr(dev.Device, "is_installed", lambda self: True)
    started = []
    monkeypatch.setattr(dev.AppiumDevice, "start", lambda self: started.append(self.serial) or self)
    s = cfg.Settings(app_driver="adb")
    plain = dev.open_device(s)
    assert type(plain) is dev.Device
    plain.close()
    appium = dev.open_device(cfg.Settings())
    assert isinstance(appium, dev.AppiumDevice) and started == ["emulator-5554"]
    appium.release()
    with pytest.raises(dev.DeviceError, match="QA_APP_DRIVER"):
        dev.open_device(cfg.Settings(app_driver="espresso"))
    monkeypatch.setattr(dev.Device, "is_installed", lambda self: False)
    with pytest.raises(dev.DeviceError, match="not installed"):
        dev.open_device(cfg.Settings(app_driver="adb"))
    dev.Device().acquire().release()  # a refused open leaves no lock behind


def test_app_driver_settings(env):
    assert (cfg.settings("").app_driver, cfg.settings("").appium_url) == ("appium", "http://127.0.0.1:4723")
    env.setenv("QA_APP_DRIVER", "ADB")
    env.setenv("QA_APPIUM_URL", "http://farm.example:4444/")
    assert (cfg.settings("").app_driver, cfg.settings("").appium_url) == ("adb", "http://farm.example:4444")
