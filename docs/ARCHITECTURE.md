# Architecture and decisions

## Goal

Every ticket QA verifies in Greybox becomes repeatable automation, for web and app, in a repo that:
- runs without Greybox;
- does not disturb Greybox or Claude Code sessions while either is working;
- lives on GitHub.

## Choices (and what was weighed)

| Area | Choice | Why | Not chosen |
|---|---|---|---|
| Language / runner | Python + pytest | Greybox's run scripts, its action library and the team's ticket flow are already Python. pytest fixtures, markers and plugins (HTML, JUnit, xdist) cover what TestNG gives the Java suites, with far less ceremony. | Java + TestNG (bizomwebautomation, bizomandroid_lt): heavier, and a second language for the Greybox-to-suite flow |
| Web | Playwright via pytest-playwright | Auto-waiting, one browser download, storage-state login reuse, screenshots on failure; the plugin supplies `page` / `browser` and the CLI options | Selenium: drivers to manage, explicit waits everywhere |
| App | adb + `uiautomator dump`, behind `qa.app.device.Device` | No server and no on-device agent. Elements are found by text / content-desc / resource-id. A UiAutomation agent (uiautomator2 library, Appium's UiAutomator2) holds the device's automation service, so Greybox's `uiautomator dump` on the same device would fail mid-run. | Appium: a server to run, plus Java + Node toolchains; uiautomator2: holds the service. `Device` is the seam if either is ever needed (iOS, gestures). |
| Structure | page / screen objects + fixtures + per-ticket folders | Page objects hold locators. Tests read like the case sheet. A ticket folder keeps tests, data and traceability together, and markers allow slicing by ticket, surface or role. | One folder per module: loses the link to the ticket and its defects |
| Data | `data.json` per ticket, keyed by company | Ids differ per company (outlet 1747 exists only on stagingbatleap). The company comes from `--company`, `QA_COMPANY` or the portal host. | Data in the test: breaks the moment the company changes |
| Secrets | `.env` (gitignored, can be a symlink to Greybox's) or CI secrets | One place, same variable names as Greybox, never copied | Per-suite copies: drift, and a second leak surface |
| Reports | pytest-html (self-contained) + JUnit XML + an artifacts folder | Light; JUnit carries ticket / case properties for traceability; HTML opens anywhere | Allure: needs a Java CLI to render |
| Explore | `explore/web`, `explore/app` inventory scripts | Read-only discovery of fields, selectors and screen ids before a test is written. Output goes to `explore/out/` (gitignored). | |

## Coexisting with Greybox and Claude

- Own folder, own git, own `.venv`. Playwright browsers sit in the shared, versioned `~/.cache/ms-playwright`; a
  different Playwright version installs alongside and does not replace Greybox's.
- Greybox touches this repo only through `qa-run automate`, which writes into it and never reads back at run time.
- Devices: no agent is installed. A per-device lock (`reports/.locks/`) keeps two suite runs off one device. A
  Greybox run and a suite run on the same device at the same moment still contend for the screen: pick another
  device with `QA_DEVICE`, or run one after the other.
- Logins are cached per role in `reports/.auth/` for 6 hours. The portal allows the same user in several sessions,
  so Greybox's sessions are not logged out.

## Found while building

- Playwright tracing breaks the outlet form's phone widget (intl-tel-input): every save was refused with "Enter
  valid phone number." Tracing is off by default.
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
