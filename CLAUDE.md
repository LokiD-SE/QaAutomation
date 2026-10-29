# CLAUDE.md - working in QaAutomation

The Bizom automation suite: web = Playwright Test (TypeScript, `web/`), app = pytest + Appium (Python, `qa/`,
`screens/`, `tests/app/`). README.md has the layout; docs/ARCHITECTURE.md has the reasons. Rules:

- **Independent.** Never import Greybox (`graph.*`) or read its folders at run time. Greybox writes into this repo
  only through `qa-run automate`.
- **Own toolchains.** `./run.sh` (it picks Node from `.nvmrc` for itself), or `npx playwright test` after
  `nvm use`, and `.venv/bin/pytest`. Never Greybox's `.venv`; never change the nvm default.
- **Secrets.** Only in `.env` (gitignored, often a symlink to Greybox's) or CI secrets. Never print `.env`. Never put
  a user, password, token or customer value in a test, a page / screen object, data.json or a commit.
  `tickets/*/reference/` is gitignored for the same reason.
- **Before writing a ticket's tests:**
  1. Read `tickets/<KEY>/cases.json`: the verified cases, with Greybox's verdict, actual result and defect.
  2. Read `tickets/<KEY>/reference/` (the Greybox run scripts) for selectors and flow. Do not copy their helpers.
  3. Explore anything unknown with `node web/explore/page-inventory.ts <path>` /
     `.venv/bin/python -m explore.app.screen_inventory`.
- **Writing web tests** (`web/tests/<slug>/`):
  - one `test(...)` per case, with `tc(TICKET, '<id>')` - replace the scaffolded `test.fixme` and keep its id;
  - import `test` / `expect` from `web/support/fixtures.ts`, never from `@playwright/test` (only unit tests do);
  - new locators go into a page object (`web/pages/`), not the test;
  - a Greybox Fail with a defect starts with `test.fail(true, 'DEF-..: ...')`; a test that writes records is tagged
    `@destructive`.
- **Writing app tests** (`tests/app/<slug>/`):
  - one test per case, marked `case("<id>")`; the module carries `ticket(...)`, `app` and `role(...)`;
  - new locators go into a screen object (`screens/app/`); tests use the `app` fixture, never Appium or adb directly;
  - a Greybox Fail with a defect is `xfail(reason="DEF-..", strict=True, raises=AssertionError)`.
- **Both:** assert each Expected Result line - the value, message or state it names; per-company data goes in
  `data.json`; a case that cannot be automated stays skipped (`test.fixme` / `pytest.skip`) with the reason.
- **Precondition vs behaviour.** A save that fails on something the case does not test (an empty mandatory field, a
  widget still loading) is a page-object set-up step. Do not weaken the assertion.
- **Done means:** `./run.sh unit` passes, `npx tsc --noEmit` and `.venv/bin/ruff check .` are clean,
  `./run.sh ticket <KEY>` ran (app cases skip without a device or with a build the server refuses - say so). Then
  commit on the ticket branch with `<KEY>: automate <n> web / <m> app cases`, and push when asked.
- **Devices.** App tests hold the device through an Appium session and free it for Greybox at the end. Never run them
  while Greybox is driving the same device.
- **Known portal traps:** the outlet form's phone widget marks a valid number invalid when it is checked before its
  library loads; `OutletEditPage.waitPhoneChecked` re-runs the check - reuse it for any form with `#libphonenumberId`.
  The portal's alerts are jQuery UI dialogs (`.ui-dialog-content`), read by `BasePage.flash`; its flash bar is
  `#flash_message`. Many selects hide behind bootstrap widgets, so use `BasePage.selectValues`. A trace makes a save
  ~4x slower: `QA_TRACE=1` only when you need one.
