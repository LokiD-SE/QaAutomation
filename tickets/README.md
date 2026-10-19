# tickets/

One folder per ticket Greybox exported with `qa-run automate <KEY>`:

- `cases.json` - the cases Greybox verified (id, surface, title, preconditions, steps, expected result, Greybox's
  verdict and actual result, defect), and where their tests live;
- `README.md` - the ticket, its run, and which cases are automated, skipped or left manual;
- `reference/` - the Greybox run scripts, for selectors and flow (gitignored: they can hold staging data).
