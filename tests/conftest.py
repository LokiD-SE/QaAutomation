"""Fixtures shared by every test.

Web: the pytest-playwright `page` is already logged in - as the test's @pytest.mark.role (ADMIN by default) - through a
saved storage state, so its own failure screenshots / traces keep working. `as_role("APPROVER")` gives a second
logged-in page for multi-user flows.
App: `app` is the locked device with the app open and logged in (`@pytest.mark.role` picks the app user).
Missing settings or devices skip the test with the reason; they are never reported as product failures.

    pytest -m web --company stagingbatleap            # web tests against one company
    pytest --ticket PR1-T13616                         # one ticket's tests, both surfaces
    QA_HEADED=1 pytest tests/web/pr1_t13616 -x         # watch it
"""

from __future__ import annotations

import json

import pytest

from qa.app.device import Device, DeviceError
from qa.app.screen import LoginScreen
from qa.config import ConfigError, settings
from qa.evidence import Evidence
from qa.web.session import auth_state


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
def base_url(qa_settings, pytestconfig):
    url = pytestconfig.getoption("base_url", default=None) or qa_settings.web_url
    if not url:
        pytest.skip("no portal URL: set BIZOM_WEB_URL (or BIZOM_WEB_URL_<COMPANY>) in .env")
    return url.rstrip("/")


@pytest.fixture
def browser_context_args(request, browser, base_url, qa_settings):
    """Every web test's context: logged in as its role through a cached storage state."""
    args = {"base_url": base_url, "ignore_https_errors": True, "viewport": {"width": 1440, "height": 900}}
    try:
        who = qa_settings.web_login(_role(request))
    except ConfigError as exc:
        pytest.skip(str(exc))
    args["storage_state"] = str(auth_state(browser, base_url, who, args))
    return args


@pytest.fixture
def as_role(browser, base_url, qa_settings):
    """as_role("APPROVER") -> a page logged in as that role, in its own context (closed after the test)."""
    contexts = []

    def make(role: str):
        try:
            who = qa_settings.web_login(role)
        except ConfigError as exc:
            pytest.skip(str(exc))
        args = {"base_url": base_url, "ignore_https_errors": True}
        context = browser.new_context(storage_state=str(auth_state(browser, base_url, who, args)), **args)
        contexts.append(context)
        return context.new_page()

    yield make
    for context in contexts:
        context.close()


@pytest.fixture(scope="session")
def device(qa_settings):
    try:
        handle = Device(qa_settings.device_serial, qa_settings.app_package).acquire()
    except DeviceError as exc:
        pytest.skip(f"app tests need a device: {exc}")
    if not handle.is_installed():
        handle.release()
        pytest.skip(f"{qa_settings.app_package} is not installed on {handle.serial}")
    yield handle
    handle.release()


@pytest.fixture
def app(device, request, qa_settings):
    """The device with the app open; logged in as the test's role when the login screen shows."""
    try:
        who = qa_settings.app_login(_role(request) if request.node.get_closest_marker("role") else "")
    except ConfigError as exc:
        pytest.skip(str(exc))
    device.launch()
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
    if handle is not None:  # pytest-playwright captures the web side; the device screen is captured here
        try:
            shot = Evidence(item.nodeid).app(handle, "failure")
            report.sections.append(("app screenshot", str(shot)))
        except Exception:  # noqa: BLE001 - evidence must never mask the real failure
            pass
