"""The framework itself - config, device parsing, evidence, page helpers. No portal, device or secret needed."""

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
    e = Evidence("tests/web/x.py::test_a[1]")
    first, second = e.path("saved"), e.path("saved")
    first.write_text("x")
    assert first.name == "saved.png" and e.path("saved").name == "saved_02.png" and second.name == "saved.png"
    assert json.loads(e.json("api", {"token": "t"}).read_text()) == {"token": "***"}


def test_base_page_helpers_on_an_offline_page():
    sync_api = pytest.importorskip("playwright.sync_api")
    from qa.web.page import BasePage

    with sync_api.sync_playwright() as pw:
        try:
            browser = pw.chromium.launch()
        except Exception as exc:  # noqa: BLE001
            pytest.skip(f"no chromium: {exc}")
        page = browser.new_page()
        page.set_content("""<label for=n>Name</label><input id=n><button>Save</button><button>Delete outlet</button>
            <div class=alert style='display:block'>Outlet is saved</div>
            <table><thead><tr><th>Name</th><th>CST</th></tr></thead><tbody><tr><td>QA 1</td><td>A (1)</td></tr></tbody></table>""")
        p = BasePage(page, "https://example.test")
        p.fill("Name", "QA 1")
        assert page.input_value("#n") == "QA 1"
        assert p.flash(timeout_ms=1000) == "Outlet is saved"
        assert p.table_rows() == [{"Name": "QA 1", "CST": "A (1)"}]
        with pytest.raises(PermissionError):
            p.click("Delete outlet")
        browser.close()
