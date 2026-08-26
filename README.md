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
3. `gh repo create usmle-step1-daily-quiz --public --source=. --remote=origin --push`.
4. Enable GitHub Pages: Settings → Pages → Deploy from branch `main`, folder `/docs`.
5. Run `scripts\generate-icons.ps1` once to create the PWA icons.
6. Run `scripts\setup-task-scheduler.ps1` once to register the daily 6:00 AM task.

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
- `git push` fails with an auth error inside the scheduled task: `gh auth status` in
  a normal terminal — if it's expired, re-run `gh auth login --web` interactively;
  the GitHub CLI credential helper is what `git push` relies on.
- Claude's JSON doesn't parse in `generate.py`: see the troubleshooting note in
  Task 5, Step 2 of the implementation plan — the `--output-format json` wrapper
  shape may have changed in a newer CLI version.
- Scheduled task shows a non-zero `LastTaskResult`: run `python generate.py`
  interactively from the same working directory to see the real error message
  (Task Scheduler swallows stdout/stderr by default).

## Explicitly out of scope

Phone push notifications / daily reminders are not built yet — deferred by design
to a future, separate plan (a true zero-backend push needs a third-party service
like ntfy.sh; the daily quiz itself doesn't depend on it).
