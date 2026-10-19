# CLAUDE.md - working in QaAutomation

The Bizom automation suite. README.md has the layout; docs/ARCHITECTURE.md has the reasons. Rules:

- **Independent.** Never import Greybox (`graph.*`) or read its folders at run time. Greybox writes into this repo
  only through `qa-run automate`.
- **Own venv.** `.venv/bin/pytest`, or `./run.sh`; never Greybox's `.venv`.
- **Secrets.** Only in `.env` (gitignored, often a symlink to Greybox's) or CI secrets. Never print `.env`. Never put
  a user, password, token or customer value in a test, a page object, data.json or a commit.
  `tickets/*/reference/` is gitignored for the same reason.
- **Before writing a ticket's tests:**
  1. Read `tickets/<KEY>/cases.json`: the verified cases, with Greybox's verdict, actual result and defect.
  2. Read `tickets/<KEY>/reference/` (the Greybox run scripts) for selectors and flow. Do not copy their helpers.
  3. Explore anything unknown with `explore/web/page_inventory.py` / `explore/app/screen_inventory.py`.
- **Writing them:**
  - one test per case, marked `case("<id>")`, in the scaffolded module; the module carries `ticket(...)`, `web` or
    `app`, and `role(...)`;
  - new locators go into a page object (`pages/web/`) or screen object (`screens/app/`), not the test;
  - assert each Expected Result line - the value, message or state it names;
  - per-company data goes in `data.json`; a case Greybox marked Fail with a defect is
    `xfail(reason="DEF-..", strict=True, raises=AssertionError)`;
  - a case that cannot be automated stays skipped with the reason.
- **Precondition vs behaviour.** A save that fails on something the case does not test (an empty mandatory field, a
  widget still loading) is a page-object set-up step. Do not weaken the assertion.
- **Done means:** `./run.sh unit` passes, `./run.sh ticket <KEY>` ran (an Android case may skip when no device is
  connected - say so), `ruff check .` is clean. Then commit on the ticket branch with
  `<KEY>: automate <n> web / <m> app cases`, and push when asked.
- **Known portal traps:** Playwright tracing breaks the outlet form's phone widget, so it is off by default. Pass
  `--tracing=retain-on-failure` only when you need a trace. The portal's flash bar is `#flash_message`. Many selects
  hide behind bootstrap widgets, so use `BasePage.select_values`.
