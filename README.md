# QaAutomation

Bizom web + Android automation, grown ticket by ticket from Greybox's verified runs.
Python, **pytest** as the runner, **Playwright** for the portal, **adb + uiautomator** for the app. No Selenium
grid, no Appium server, no agent on the device. It runs on its own: Greybox is not imported and does not need to
be running.

```bash
./setup.sh                                   # .venv, Chromium, .env (can link Greybox's .env - no secrets copied)
./run.sh unit                                # the framework's own tests - no portal, device or secrets
./run.sh smoke                               # login works on web and app
./run.sh ticket PR1-T13616                   # one ticket, both surfaces
./run.sh web --company stagingbatleap -x     # every web test against one company
QA_HEADED=1 ./run.sh tests/web/pr1_t13616    # watch it in a browser
```

Reports: `reports/report.html` (self-contained), `reports/junit.xml` (with each test's ticket and case ids),
`reports/artifacts/<test>/` (screenshots, JSON evidence; a failing web test also gets Playwright's screenshot).

## Layout

```
qa/                  the framework - small and stable
  config.py          settings from .env / environment, per company and role (Greybox's variable names)
  evidence.py        per-test evidence folder; secrets masked in JSON evidence
  web/session.py     portal login, cached per role as Playwright storage state
  web/page.py        BasePage - navigation, overlays, flash messages, tables, safe clicks
  app/device.py      Device - adb + uiautomator: read the screen, tap / type by text, screenshots, a device lock
  app/screen.py      BaseScreen, LoginScreen
pages/web/           page objects (one per portal page)        e.g. outlets.py
screens/app/         screen objects (one per app screen)       e.g. home.py
tests/
  conftest.py        fixtures: page (logged in as the test's role), as_role(), app, device, evidence, ticket_data
  unit/              framework tests
  web/<ticket>/      one folder per ticket: test_*.py + data.json (per-company test data)
  app/<ticket>/
  web/smoke, app/smoke
explore/
  web/page_inventory.py    what a portal page shows: fields, selectors, buttons, tables (+ screenshot)
  app/screen_inventory.py  what an app screen shows: texts, clickable ids, inputs (+ screenshot, dump)
tickets/<KEY>/       what Greybox exported for a ticket: cases.json (the verified cases), README
docs/ARCHITECTURE.md decisions and the reasons for them
```

## Writing a test

```python
pytestmark = [pytest.mark.web, pytest.mark.ticket("PR1-T13616"), pytest.mark.role("ADMIN")]

@pytest.mark.case("TC_WEB_002")
def test_brackets_and_spaces_are_saved(page, base_url, ticket_data, evidence):
    outlet = OutletEditPage(page, base_url, ticket_data["outlet_id"]).open()
    result = outlet.set_cst("CST 123 (Unit) [A]").submit()
    evidence.web(page, "after_submit")
    assert result.saved, result.message
    assert outlet.stored_cst() == "CST 123 (Unit) [A]"
```

- Every test carries `ticket(...)` and `case(...)`, so a result traces back to the sheet and the defect.
- Tests talk to page / screen objects, never to raw selectors.
- Data that differs per company goes in the ticket folder's `data.json`, keyed by company, never in the test.
- A known open defect is `@pytest.mark.xfail(reason="DEF-..", strict=True, raises=AssertionError)`. It turns red
  the day the fix ships, so the marker gets removed.
- A test that writes shared settings or records is `@pytest.mark.destructive`. Run those only on a QA company.

Markers: `unit web app smoke regression destructive ticket(key) case(id) role(name)`; select with `-m`.

## From a Greybox ticket to tests

In Greybox: `qa-run automate PR1-T13616` exports the ticket's verified cases to `tickets/PR1-T13616/`, scaffolds
`tests/<web|app>/pr1_t13616/` with one test per case (skipped until written), and creates a branch
`ticket/PR1-T13616`. The tests are then written against `pages/` / `screens/` (see CLAUDE.md), run with
`./run.sh ticket PR1-T13616`, committed, and pushed to GitHub.

## CI

`.github/workflows/ci.yml` runs lint, the framework tests and test collection on every push. A manual workflow runs
the web suite against a company when its URL and logins are repository secrets (staging must be reachable from
GitHub's runners).
