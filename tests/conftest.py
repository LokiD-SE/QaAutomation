"""Fixtures for the app tests (the web tests are Playwright Test, in web/).

`device` is the locked device for the whole run - an Appium session by default (QA_APP_DRIVER=adb for plain adb) - and
is freed for Greybox at the end. `app` is that device with the app open and logged in (`@pytest.mark.role` picks the
app user). Missing settings or devices skip the test with the reason; they are never reported as product failures.

    pytest -m app --company stagingbatleap             # app tests against one company
    pytest --ticket PR1-T13616                          # one ticket's app tests
    QA_APP_DRIVER=adb pytest tests/app/smoke            # without Appium
"""

from __future__ import annotations

import json

import pytest

from qa.app.device import DeviceError, open_device
from qa.app.screen import LoginScreen
from qa.config import ConfigError, settings
from qa.evidence import Evidence


def pytest_addoption(parser):
    group = parser.getgroup("qa")
    group.addoption("--company", default=None, help="company slug: uses BIZOM_*_<COMPANY> values from .env")
    group.addoption("--ticket", action="append", default=[], help="run only tests marked ticket(KEY); repeatable")


def pytest_collection_modifyitems(config, items):
    wanted = {t.upper() for t in config.getoption("--ticket")}
    keep, drop = [], []
    for item in items:
        tickets = {str(a).upper() for m in item.iter_markers("ticket") for a in m.args}
        cases = [str(a) for m in item.iter_markers("case") for a in m.args]
        for key in sorted(tickets):
            item.user_properties.append(("ticket", key))  # into junit.xml: test -> ticket -> case traceability
        for case in cases:
            item.user_properties.append(("case", case))
        (keep if not wanted or tickets & wanted else drop).append(item)
    if drop:
        config.hook.pytest_deselected(items=drop)
        items[:] = keep


def _role(request) -> str:
    marker = request.node.get_closest_marker("role")
    return str(marker.args[0]) if marker and marker.args else "ADMIN"


@pytest.fixture(scope="session")
def qa_settings(pytestconfig):
    return settings(pytestconfig.getoption("--company"))


@pytest.fixture(scope="session")
def device(qa_settings):
    try:
        handle = open_device(qa_settings)
    except DeviceError as exc:
        pytest.skip(f"app tests need a device: {exc}")
    yield handle
    handle.close()  # Appium: session ended, its on-device server stopped - Greybox can dump the screen again


@pytest.fixture
def app(device, request, qa_settings):
    """The device with the app open; logged in as the test's role when the login screen shows."""
    try:
        who = qa_settings.app_login(_role(request) if request.node.get_closest_marker("role") else "")
    except ConfigError as exc:
        pytest.skip(str(exc))
    device.launch()
    if device.has("update_required_screen") or device.has("old and unsupported version"):
        old = next((t for t in device.texts() if "unsupported version" in t), "the installed build")
        pytest.skip(f"the server refuses this app build - install a newer APK: {old}")
    login = LoginScreen(device)
    if login.is_open(timeout=8):
        login.login(who)
    return device


@pytest.fixture
def evidence(request):
    return Evidence(request.node.nodeid)


@pytest.fixture
def ticket_data(request, qa_settings):
    """The test module's data.json entry for the run's company (QA_COMPANY / --company)."""
    path = request.path.parent / "data.json"
    if not path.is_file():
        pytest.skip(f"no data.json beside {request.path.name}")
    data = json.loads(path.read_text(encoding="utf-8"))
    company = qa_settings.company
    if company not in data:
        pytest.skip(f"no test data for company '{company}' in {path.relative_to(request.config.rootpath)}")
    return data[company]


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed or "app" not in item.fixturenames:
        return
    handle = item.funcargs.get("device")
    if handle is not None:
        try:
            shot = Evidence(item.nodeid).app(handle, "failure")
            report.sections.append(("app screenshot", str(shot)))
        except Exception:  # noqa: BLE001 - evidence must never mask the real failure
            pass
