# Architecture and decisions

## Goal

Every ticket QA verifies in Greybox becomes repeatable automation, for web and app, in a repo that:
- runs without Greybox;
- does not disturb Greybox or Claude Code sessions while either is working;
- lives on GitHub.

## Choices (and what was weighed)

| Area | Choice | Why | Not chosen |
|---|---|---|---|
| Web: language / runner | TypeScript + Playwright Test | The team's choice (2026-10-29). Playwright Test is Playwright's own runner: fixtures, projects per browser, parallel workers, retries with traces, HTML + JUnit reporters, `--grep` on tags - nothing to bolt on. Node runs the explore script with no build step (type stripping). | pytest-playwright (the suite's first web layer, 2026-10-19): a plugin on another runner; its tests were ported one-for-one |
| App: language / runner | Python + pytest | Greybox's run scripts, its action library and its app flows are Python; the app framework (device seam, screen objects) already existed | WebdriverIO (TypeScript): one language with the web suite, but a rewrite of the device layer and a second runner config for no gain on the device side |
| App: driver | Appium 3 + UiAutomator2, behind `qa.app.device` (`AppiumDevice`) | Real waits and gestures, typing into the focused field, Appium Inspector for locators; the protocol device farms (BrowserStack, Sauce) speak; iOS later is the XCUITest driver, not a rewrite. Installed in the repo (`node_modules`), not globally | Playwright `_android` (experimental, Node only, no device farms); Maestro (YAML outside pytest); Espresso (needs the app's source); uiautomator2 library (Android only, no farms). Plain adb stays as `QA_APP_DRIVER=adb` |
| Structure | page / screen objects + fixtures + per-ticket folders | Page objects hold locators. Tests read like the case sheet. A ticket folder keeps tests, data and traceability together; tags (web) and markers (app) slice by ticket, case, surface or role. | One folder per module: loses the link to the ticket and its defects |
| Traceability | web: `tc(ticket, case)` -> tags + annotations (JUnit properties); app: `ticket()` / `case()` markers -> JUnit properties | One id scheme across both reports, the case sheet and the defect | |
| Data | `data.json` per ticket, keyed by company | Ids differ per company (outlet 1747 exists only on stagingbatleap). The company comes from `--company`, `QA_COMPANY` or the portal host. | Data in the test: breaks the moment the company changes |
| Secrets | `.env` (gitignored, can be a symlink to Greybox's) or CI secrets | One place, same variable names as Greybox, read by both suites, never copied | Per-suite copies: drift, and a second leak surface |
| Reports | web: Playwright HTML + JUnit; app: pytest-html + JUnit; artifacts per test | Light, open anywhere, CI-readable | Allure: needs a Java CLI to render |
| Explore | `web/explore/page-inventory.ts`, `explore/app/screen_inventory.py` | Read-only discovery of fields, selectors and screen ids before a test is written. Output goes to `explore/out/` (gitignored). | |

## Coexisting with Greybox and Claude

- Own folder, own git, own `.venv`, own `node_modules` (Playwright Test, Appium and its driver). Node comes from
  `.nvmrc` through nvm for each run; the nvm default is never changed. Playwright browsers sit in the shared,
  versioned `~/.cache/ms-playwright`; a different Playwright version installs alongside and does not replace Greybox's.
- Greybox touches this repo only through `qa-run automate`, which writes into it and never reads back at run time.
- Devices: Appium's UiAutomator2 server holds the device's UI automation service while a session is open, and
  Greybox's `uiautomator dump` fails meanwhile. Greybox and the app suite therefore never run on one device at the
  same moment; at the end of every run the suite quits the session, force-stops `io.appium.uiautomator2.server(.test)`
  and checks that `uiautomator dump` works again. A per-device lock (`reports/.locks/`) keeps two suite runs off one
  device; `QA_DEVICE` picks another device.
- adb: Appium uses the SDK in `ANDROID_HOME` (else `~/Android/Sdk`). Every adb on this machine speaks protocol
  1.0.41, so they share one adb server and none restarts it under Greybox.
- Logins are cached per role in `reports/.auth/` for 6 hours. The portal allows the same user in several sessions,
  so Greybox's sessions are not logged out.

## Found while building

- The outlet form's phone widget (intl-tel-input) checks the stored number on load, before its utils.js arrives,
  and leaves a valid number marked `error`; the submit handler then refuses with "Enter valid phone number." (a jQuery
  UI dialog). Anything that slows the load - tracing, a busy staging server - made it happen more often; it was first
  blamed on tracing. `OutletEditPage.waitPhoneChecked` waits for the library and re-runs the widget's own check.
- The app on the shared emulator can be older than the server accepts ("Update to the version ... or higher"); the
  `app` fixture skips with that message instead of failing.
- The portal's flash bar is `#flash_message`, and pages carry hidden message templates. `BasePage.flash()` reads
  the first visible one.
- Mandatory fields left empty on QA records ("Please select Outlet Attributes") block every save. Page objects fill
  such preconditions explicitly; tests never weaken an assertion to get past one.

## Research notes

- pytest + Playwright layouts in common use: `pages/` for page objects, fixtures in `conftest.py`, defaults in
  `pytest.ini` / pyproject, separate `config/` and test-data folders.
  [mintlify guide](https://www.mintlify.com/darket1989/qa-automation-learning/advanced/best-practices),
  [momentic](https://momentic.ai/resources/building-a-robust-test-suite-with-playwright-for-python-a-comprehensive-guide),
  [testdino POM](https://testdino.com/blog/playwright-pom/)
- Appium vs uiautomator2: Appium is client-server and cross-platform; uiautomator2 is Android-only and lighter, with
  no server. Neither is needed for one Android app driven by visible text.
  [Appium forum](https://discuss.appium.io/t/what-is-difference-between-appium-and-uiautomator2-automation-engine/22047),
  [Panto](https://www.getpanto.ai/blog/python-frameworks-mobile-test-automation),
  [Kobiton](https://kobiton.com/mobile-testing-guide/mobile-test-automation/ui-automator-vs-appium-android-ui-testing/)
- Monorepo CI: path filters and a matrix per suite; markers to slice runs.
  [oneuptime](https://oneuptime.com/blog/post/2026-02-02-github-actions-monorepos/view),
  [demo-python-ui-tests](https://github.com/CodeMaster91-hub/demo-python-ui-tests)
