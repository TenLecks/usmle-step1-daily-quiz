# USMLE Step 1 Daily Quiz

Daily 30-question USMLE Step 1 practice quiz, generated from local Boards & Beyond
PDF notes (`C:\Users\Omer\Desktop\BoardAndBeyond_PDFs`) via headless Claude Code,
served as a zero-backend PWA on GitHub Pages.

Live app: `https://tenlecks.github.io/usmle-step1-daily-quiz/`

## How it works

- `generate.py` runs once a day (via Windows Task Scheduler, see below). It picks the
  next subject in rotation (`lib/rotation.py`), builds a prompt (`lib/prompt.py`),
  and calls the Claude Code CLI headlessly (`claude -p ... --json-schema ...`) with
  access to that subject's PDF folder. The response is validated (`lib/schema.py`),
  written to `docs/questions.json`, and pushed to GitHub.
- `docs/index.html` is the entire PWA — no backend, no build step. It fetches
  `questions.json?v=<timestamp>` on load (cache-busted) and tracks everything else
  (progress, wrong-answer bank, bookmarks, score history) in `localStorage`.
- Subject rotation: Cardiology → Pulmonary alphabetically (13 subjects), then Renal
  and Reproductive in a freshly randomized order each cycle. Full cycle = 15 days.
  State lives in `state.json`, including which question stems were already used per
  subject (fed back into the prompt so re-cycled subjects don't repeat questions).

## One-time setup (already done if you followed the implementation plan)

1. Install GitHub CLI (`winget install --id GitHub.cli`) and run `gh auth login --web`.
2. Install the Claude Code CLI globally: `npm install -g @anthropic-ai/claude-code`.
   - On a fresh Windows machine this can fail with "File ...\npm.ps1 cannot be
     loaded because running scripts is disabled on this system" — a PowerShell
     execution-policy block on `.ps1` scripts. Either always invoke `npm.cmd`
     explicitly, or fix it once and for all with
     `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`
     (the standard safe developer setting).
3. Run `claude` once and log in via `/login` in the browser flow it opens
   (or run `claude auth login` directly). This is a separate login from
   `gh auth login` above — it authenticates the Claude Code CLI itself against
   your Claude subscription account. Without it, `claude.cmd` fails immediately
   with "Not logged in · Please run /login". Note the same execution-policy
   issue as step 2 can affect plain `claude`/`claude --version` (PowerShell
   prefers the `.ps1` wrapper over `.cmd`) — use `claude.cmd` explicitly or
   apply the same `Set-ExecutionPolicy` fix.
4. `gh repo create usmle-step1-daily-quiz --public --source=. --remote=origin --push`.
5. Enable GitHub Pages: Settings → Pages → Deploy from branch `main`, folder `/docs`.
   `docs/.nojekyll` is already committed — GitHub Pages' legacy build system
   runs Jekyll by default, which can hang/fail on a plain static site with no
   Jekyll config, so keep this file if you ever regenerate `docs/` from scratch.
   Note: a brand-new GitHub account's first Pages deployment has been observed
   sitting in `queued` or failing with `startup_failure` for a while — this
   looks like GitHub-side anti-abuse throttling on new accounts rather than a
   config problem, but it isn't confirmed resolved.
6. Run `scripts\generate-icons.ps1` once to create the PWA icons.
7. Run `scripts\setup-task-scheduler.ps1` once to register the daily 6:00 AM task.
8. Run `gh auth setup-git` once so `git push` from the scheduled task (which
   runs unattended, not interactively) can use `gh`'s stored credentials — see
   Troubleshooting below.

## Manual operations

- **Regenerate today's quiz by hand:** `python generate.py` (from the repo root, in
  a plain terminal — not from inside another Claude Code session).
- **Change the daily run time:** edit the `-At "6:00AM"` value in
  `scripts/setup-task-scheduler.ps1` and re-run it (`-Force` re-registers the task).
- **Reset the rotation / question history:** delete `state.json` and commit; the
  next run starts back at Cardiology with no "avoid repeating" history.
- **Run the tests:** `pip install -r requirements-dev.txt` then `python -m pytest`.

## Troubleshooting

- `claude` not found after `npm install -g`: open a new terminal so PATH refreshes.
- `npm install -g` or plain `claude`/`claude --version` fails with "...cannot be
  loaded because running scripts is disabled on this system": a PowerShell
  execution-policy block on `.ps1` scripts (PowerShell prefers the `.ps1`
  wrapper over `.cmd`). Use `npm.cmd`/`claude.cmd` explicitly, or run
  `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` once.
- `git push` fails inside the scheduled task with "Cannot prompt because user
  interactivity has been disabled" / "could not read Username for
  'https://github.com'", even though interactive `gh` commands (`gh auth login`,
  `gh repo create --push`) work fine: `gh`'s stored credentials aren't wired
  into git's own credential helper yet. Fix is a one-time `gh auth setup-git`
  run (not a re-login) — this is what actually resolved it, and it's now step 8
  of one-time setup above.
- Claude responds with conversational text instead of JSON in `generate.py`
  (historical bug, now fixed): `claude.cmd` is a Windows batch-file wrapper, and
  batch-file argument passing is line-oriented — a multi-line `-p` prompt was
  silently truncated at the first newline, so Claude only ever received a
  fragment of the task. Fixed permanently in `lib/prompt.py`, which builds the
  prompt as a single line with no embedded newlines, and verified end-to-end
  with a real 30-question generation. If this resurfaces, check that any edit
  to `lib/prompt.py` hasn't reintroduced a literal newline in the prompt string.
- Scheduled task shows a non-zero `LastTaskResult`: run `python generate.py`
  interactively from the same working directory to see the real error message
  (Task Scheduler swallows stdout/stderr by default).

## Explicitly out of scope

Phone push notifications / daily reminders are not built yet — deferred by design
to a future, separate plan (a true zero-backend push needs a third-party service
like ntfy.sh; the daily quiz itself doesn't depend on it).
