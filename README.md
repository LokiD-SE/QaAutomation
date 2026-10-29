# QaAutomation

Bizom web + Android automation, grown ticket by ticket from Greybox's verified runs. One repo, two suites:

| Surface | Runner | Drives with | Lives in |
|---|---|---|---|
| Web portal | **Playwright Test** (TypeScript) | Playwright | `web/`, `playwright.config.ts` |
| Android app | **pytest** (Python) | **Appium** UiAutomator2 (adb as fallback) | `qa/`, `screens/`, `tests/app/` |

It runs on its own: Greybox is not imported and does not need to be running.

```bash
./setup.sh                                   # Node 24 (nvm), Playwright + Chromium, Appium + UiAutomator2, .venv, .env
./run.sh unit                                # both frameworks' own tests - no portal, device or secrets
./run.sh smoke --company stagingbatleap      # portal login + app login
./run.sh ticket PR1-T13616                   # one ticket, both surfaces
./run.sh web --company stagingbatleap -x     # every web test against one company (extra args go to playwright test)
./run.sh app --company stagingbatleap        # every app test (extra args go to pytest)
QA_HEADED=1 ./run.sh web --grep @TC_WEB_002  # watch one case in a browser
QA_BROWSERS=chromium,firefox ./run.sh web    # cross-browser
npm run report                               # open the last web HTML report
```

Reports (`reports/`, gitignored):
- web: `web-html/` (Playwright's HTML report, with screenshots and traces), `web-junit.xml` (ticket and case ids as
  properties), `web-artifacts/` (per-test output);
- app: `app-report.html` (self-contained), `app-junit.xml`, `artifacts/<test>/` (screenshots, JSON evidence),
  `appium.log` (the Appium server a run started).

## Layout

```
web/                         Playwright Test - the portal
  support/config.ts          settings from .env / environment, per company and role (Greybox's variable names)
  support/session.ts         portal login, cached per role as a storage state (reports/.auth/)
  support/fixtures.ts        test / expect to import: page logged in as the test's role, asRole(), evidence, ticketData
  support/tags.ts            tc(ticket, caseId) - tags + annotations for traceability
  support/evidence.ts        screenshots / JSON attached to the report; secrets masked
  pages/                     page objects: base-page.ts, one per portal page   e.g. outlets.ts
  tests/<ticket>/            one folder per ticket: *.spec.ts + data.json (per-company test data)
  tests/smoke/, tests/unit/  login smoke; the framework's own tests
  explore/page-inventory.ts  what a portal page shows: fields, selectors, buttons, tables (+ screenshot)
playwright.config.ts         projects (unit + browsers), reporters, timeouts, traces

qa/                          the app framework - small and stable
  config.py                  settings, per company and role; QA_APP_DRIVER / QA_APPIUM_URL / QA_DEVICE
  evidence.py                per-test evidence folder; secrets masked in JSON evidence
  app/device.py              Device (adb) and AppiumDevice - one interface; open_device() builds the configured one
  app/appium_server.py       uses the Appium server at QA_APPIUM_URL, or starts one from node_modules for the run
  app/screen.py              BaseScreen, LoginScreen
screens/app/                 screen objects (one per app screen)   e.g. home.py
tests/
  conftest.py                fixtures: device (locked, Appium session, freed for Greybox at the end), app, evidence, ticket_data
  unit/                      framework tests
  app/<ticket>/, app/smoke/
explore/app/screen_inventory.py   what an app screen shows: texts, clickable ids, inputs (+ screenshot, dump)
tickets/<KEY>/               what Greybox exported for a ticket: cases.json (the verified cases), README
docs/ARCHITECTURE.md         decisions and the reasons for them
```

## Writing a web test

```ts
import { OutletEditPage } from '../../pages/outlets.ts';
import { expect, test } from '../../support/fixtures.ts';
import { tc } from '../../support/tags.ts';

const TICKET = 'PR1-T13616';
test.use({ role: 'ADMIN' });

test('brackets and spaces are saved', tc(TICKET, 'TC_WEB_002', '@destructive'), async ({ page, portal, ticketData, evidence }) => {
  const outlet = await new OutletEditPage(page, portal, ticketData.outlet_id).open();
  const result = await outlet.setCst('CST 123 (Unit) [A]').then((o) => o.submit());
  await evidence.page(page, 'after_submit');
  expect(result.saved, result.message).toBe(true);
  expect(await outlet.storedCst()).toBe('CST 123 (Unit) [A]');
});
```

- Every test carries `tc(ticket, caseId)`: tags (`--grep @PR1-T13616`, `--grep @TC_WEB_002`) and JUnit properties.
- Tests talk to page objects, never to raw selectors.
- Data that differs per company goes in the ticket folder's `data.json`, keyed by company, never in the test.
- A known open defect starts with `test.fail(true, 'DEF-..: ...')`. It turns red the day the fix ships, so the line
  gets removed.
- A test that writes shared settings or records is tagged `@destructive`. Run those only on a QA company; CI skips them.
- Tests in one file run in order on one worker (they share the ticket's QA record); files run in parallel.

## Writing an app test

```python
pytestmark = [pytest.mark.app, pytest.mark.ticket("PR1-T13585"), pytest.mark.role("DISTRIBUTOR SALESMAN")]

@pytest.mark.case("TC_APP_004")
def test_sale_is_blocked(app, ticket_data, evidence):
    HomeScreen(app).go_to("Outlets")
    ...
```

Markers: `unit app smoke regression destructive ticket(key) case(id) role(name)`; select with `-m`. A known open
defect is `xfail(reason="DEF-..", strict=True, raises=AssertionError)`.

The app driver is Appium by default. The fixture starts an Appium server from `node_modules` when none answers at
`QA_APPIUM_URL`, opens one session for the run, and at the end quits it and force-stops Appium's on-device server, so
Greybox's `uiautomator dump` works on that device again. Do not run Greybox and the app suite on the same device at
the same moment. `QA_APP_DRIVER=adb` runs the same tests over plain adb.

## From a Greybox ticket to tests

In Greybox: `qa-run automate PR1-T13616` exports the ticket's verified cases to `tickets/PR1-T13616/` and scaffolds
one stub per case - web cases as `test.fixme` in `web/tests/pr1_t13616/pr1_t13616.spec.ts`, app cases as skipped
tests in `tests/app/pr1_t13616/test_pr1_t13616.py` - on a branch `ticket/PR1-T13616`. The tests are then written
against `web/pages/` / `screens/` (see CLAUDE.md), run with `./run.sh ticket PR1-T13616`, committed, and pushed.

## CI

`.github/workflows/ci.yml` runs the type check, lint, both frameworks' tests and test collection on every push. A
manual workflow runs web tests (a `--grep`, destructive ones excluded) against a company when its URL and logins are
repository secrets (staging must be reachable from GitHub's runners). App tests need a device and run locally.
