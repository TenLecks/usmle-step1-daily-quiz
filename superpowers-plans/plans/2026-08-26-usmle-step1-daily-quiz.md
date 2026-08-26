# USMLE Step 1 Daily Quiz Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A zero-backend daily USMLE Step 1 practice system: a local Python script that uses headless Claude Code to turn Boards & Beyond PDF notes into 30 fresh MCQs a day and pushes them to GitHub, and a single-page PWA on GitHub Pages that runs the quiz with full local (localStorage) progress, wrong-answer, and bookmark tracking.

**Architecture:** `generate.py` (run daily by Windows Task Scheduler) picks the next subject in a fixed rotation, shells out to the headless Claude Code CLI with `--add-dir` pointed at that subject's PDF folder and a `--json-schema` that forces structured MCQ output, validates the result in Python, writes `docs/questions.json`, and commits/pushes to GitHub. `docs/index.html` is a single dependency-free HTML/CSS/JS file served by GitHub Pages that fetches `questions.json?v=<timestamp>` (cache-busted) and runs three modes (Daily Quiz, Review Missed, Bookmarked) entirely against `localStorage`.

**Tech Stack:** Python 3.12 (stdlib only, `pytest` for dev-time tests), Claude Code CLI (`@anthropic-ai/claude-code`, installed globally via npm, invoked headless via `-p`), git + GitHub CLI (`gh`), vanilla HTML/CSS/JS (no framework, no build step) on GitHub Pages, Windows Task Scheduler (PowerShell `ScheduledTask` cmdlets).

**Spec:** No separate spec document. Requirements were captured directly from the user's request plus two rounds of clarifying questions on 2026-08-26 (repo: user creates a GitHub account/repo via a browser step Claude cannot perform for them, but delegated the actual repo name and creation *commands* to Claude; auth: existing Claude subscription, not a separate API key; scheduling: Windows Task Scheduler at 6:00 AM with catch-up on next login; coverage: fixed order Cardiology→Pulmonary alphabetically, then Renal/Reproductive in randomized order, 15-day full cycle; format: 10 real-USMLE 5-option vignette questions + 20 simpler 4-option questions per day, every option explained; phone push reminder explicitly deferred to a future plan). This plan's Overview section above and the Global Constraints below are the authoritative requirements record.

## Global Constraints

- Local project root: `C:\Users\Omer\Desktop\usmle-step1-daily-quiz` (separate from `C:\Users\Omer\Desktop\BoardAndBeyond_PDFs`, which is never committed to git — only Claude-generated questions derived from it are).
- Source notes root: `C:\Users\Omer\Desktop\BoardAndBeyond_PDFs\<Subject>\...` (393 PDFs across 15 subject folders, confirmed to exist).
- GitHub repo: new, public, named `usmle-step1-daily-quiz`, created via `gh repo create` (public is required for free GitHub Pages). Claude does not create the GitHub account itself — the user completes the `gh auth login` browser step.
- GitHub Pages source: branch `main`, folder `/docs`.
- Claude Code CLI: installed globally (`npm install -g @anthropic-ai/claude-code`), invoked headless as `claude.cmd -p ... --output-format json --json-schema <schema> --permission-mode bypassPermissions --add-dir <subject folder>`. Authenticates via the existing logged-in Claude subscription — no separate `ANTHROPIC_API_KEY`. Flags verified against `claude --help` output (CLI v2.1.246, Aug 2026); re-verify with `claude --help` if a later CLI version changes them.
- Question mix per day: exactly 10 `"vignette5"` questions (5 options A–E, clinical-vignette stem, single best answer) + exactly 20 `"simple4"` questions (4 options A–D) = 30 total. Every option gets its own explanation string (correct option: why it's right; every other option: why it's wrong).
- Subject rotation: fixed order `Cardiology, Dermatology, Endocrinology, Gastroenterology, Genetics, Hematology, Immunology, Musculoskeletal, Neurology, Ophthalmology, Pathology, Psychiatry, Pulmonary` (13 subjects, alphabetical), then `Renal, Reproductive` in a freshly shuffled order each cycle. One subject per day → full cycle = 15 days.
- Daily automation: Windows Task Scheduler, trigger daily at 6:00 AM, `StartWhenAvailable` enabled so a missed run (PC off) fires at next login; `WakeToRun` enabled so a sleeping (not off) PC wakes if the hardware supports it.
- No JS build step / no bundler / no JS test framework: `docs/index.html` is a single static file, tested manually via a local static server + browser interaction against explicit acceptance criteria in each task — introducing a JS toolchain would contradict the single-file zero-build design and isn't justified for a solo personal app.
- Out of scope for this plan (explicitly deferred by the user): phone push-notification / daily reminder integration. Revisit in a separate future plan.

---

## File Structure

```
usmle-step1-daily-quiz/
├── .gitignore
├── requirements-dev.txt          # pytest only; generate.py itself has zero third-party deps
├── README.md                     # setup + runbook (finalized in Task 13)
├── state.json                    # rotation pointer + per-subject "already asked" history (created by first run)
├── lib/
│   ├── rotation.py                # pure: pick today's subject, advance rotation state
│   ├── schema.py                  # pure: validate Claude's generated questions payload
│   └── prompt.py                  # pure: build the prompt sent to headless Claude
├── generate.py                    # orchestrator: rotation → prompt → call Claude → validate → write → git push
├── tests/
│   ├── test_rotation.py
│   ├── test_schema.py
│   └── test_prompt.py
├── scripts/
│   ├── generate-icons.ps1         # one-time: renders docs/icons/*.png via System.Drawing
│   └── setup-task-scheduler.ps1   # registers the daily Windows Scheduled Task
└── docs/                          # GitHub Pages root
    ├── index.html                 # the entire PWA (HTML+CSS+JS)
    ├── manifest.json
    ├── questions.json             # today's 30 questions (overwritten daily by generate.py)
    └── icons/
        ├── icon-192.png
        ├── icon-512.png
        └── apple-touch-icon.png
```

---

### Task 1: Environment & Repo Setup

**Files:**
- Create: `C:\Users\Omer\Desktop\usmle-step1-daily-quiz\.gitignore`
- Create: `C:\Users\Omer\Desktop\usmle-step1-daily-quiz\requirements-dev.txt`
- Create: `C:\Users\Omer\Desktop\usmle-step1-daily-quiz\README.md` (stub)

**Interfaces:**
- Produces: an authenticated `gh` CLI session, a globally installed `claude` CLI, a public GitHub repo `usmle-step1-daily-quiz` with `origin` remote already pushed, and a local git identity scoped to this repo (`user.name` = the GitHub login, `user.email` = `boazyomer@gmail.com`) that every later task's commits rely on.

- [ ] **Step 1: Install GitHub CLI**

Run in PowerShell:

```powershell
winget install --id GitHub.cli -e --source winget --accept-package-agreements --accept-source-agreements
gh --version
```

Expected: prints a `gh version 2.x.x` line. If `winget` itself is missing, install `gh` from https://cli.github.com/ manually instead.

- [ ] **Step 2: Authenticate gh CLI (human step)**

```powershell
gh auth login --web --git-protocol https
```

This opens a browser. **Log in to your existing GitHub account, or create one if you don't have one, and approve the device code shown in the terminal — this part has to be done by you, not Claude.** Once approved:

```powershell
gh auth status
```

Expected: shows "Logged in to github.com as <username>".

- [ ] **Step 3: Capture the GitHub username**

```powershell
$GhUser = gh api user --jq .login
Write-Host "GitHub username: $GhUser"
```

Keep this value — it's used in Step 6 and Step 8 below (and in Task 11 for the Pages URL).

- [ ] **Step 4: Install Claude Code CLI globally**

```powershell
npm install -g @anthropic-ai/claude-code
```

Open a **new** PowerShell window (so the updated PATH is picked up) and run:

```powershell
claude --version
```

Expected: prints a version like `2.1.246 (Claude Code)`. If it still logs in interactively on first use, complete that login once — it uses your existing Claude subscription, not a separate API key.

- [ ] **Step 5: Scaffold the local repo**

```powershell
New-Item -ItemType Directory -Force -Path "C:\Users\Omer\Desktop\usmle-step1-daily-quiz" | Out-Null
Set-Location "C:\Users\Omer\Desktop\usmle-step1-daily-quiz"
git init
```

Create `.gitignore`:

```
__pycache__/
*.pyc
.pytest_cache/
```

Create `requirements-dev.txt`:

```
pytest>=8.0
```

Create `README.md` (stub, expanded fully in Task 13):

```markdown
# USMLE Step 1 Daily Quiz

Daily 30-question USMLE Step 1 practice quiz, generated from local Boards & Beyond
PDF notes via headless Claude Code, served as a PWA on GitHub Pages.

Setup and runbook: see Task 13 of the implementation plan (to be filled in).
```

- [ ] **Step 6: Commit and create the GitHub repo**

```powershell
git add .gitignore requirements-dev.txt README.md
git commit -m "Initial scaffold"
gh repo create usmle-step1-daily-quiz --public --source=. --remote=origin --push
```

- [ ] **Step 7: Verify the repo exists**

```powershell
gh repo view --web
```

Expected: browser opens to `https://github.com/<username>/usmle-step1-daily-quiz` showing the initial commit.

- [ ] **Step 8: Set local git identity for this repo**

```powershell
git config user.name "$GhUser"
git config user.email "boazyomer@gmail.com"
git log -1 --format="%an <%ae>"
```

Expected: prints `<username> <boazyomer@gmail.com>`. This is scoped to this repo only (no `--global`), since no global git identity existed on this machine before this task.

---

### Task 2: Subject Rotation Logic

**Files:**
- Create: `lib/rotation.py`
- Test: `tests/test_rotation.py`

**Interfaces:**
- Consumes: nothing (pure logic, no I/O).
- Produces: `next_subject(state: dict, rng: random.Random | None = None) -> tuple[str, dict]` and the constants `FIXED_ORDER: list[str]`, `RANDOM_TAIL: list[str]` — consumed by `generate.py` in Task 5.

- [ ] **Step 1: Write the failing tests**

`tests/test_rotation.py`:

```python
import random
from lib.rotation import next_subject, FIXED_ORDER, RANDOM_TAIL


def test_first_thirteen_calls_follow_fixed_order():
    state = {}
    subjects = []
    for _ in range(13):
        subject, state = next_subject(state, rng=random.Random(42))
        subjects.append(subject)
    assert subjects == FIXED_ORDER


def test_calls_fourteen_and_fifteen_are_random_tail_permutation():
    state = {}
    subjects = []
    for _ in range(15):
        subject, state = next_subject(state, rng=random.Random(42))
        subjects.append(subject)
    assert sorted(subjects[13:15]) == sorted(RANDOM_TAIL)


def test_cycle_wraps_back_to_start_after_fifteen_days():
    state = {}
    for _ in range(15):
        _, state = next_subject(state, rng=random.Random(1))
    subject, state = next_subject(state, rng=random.Random(1))
    assert subject == FIXED_ORDER[0]
    assert state["cycle_number"] == 2


def test_state_dict_is_not_mutated_in_place():
    state = {"cycle_index": 0, "cycle_number": 1, "tail_order": None}
    original = dict(state)
    next_subject(state, rng=random.Random(7))
    assert state == original
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_rotation.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'lib.rotation'` (or `lib` has no attribute).

- [ ] **Step 3: Write the implementation**

`lib/rotation.py`:

```python
import random

FIXED_ORDER = [
    "Cardiology", "Dermatology", "Endocrinology", "Gastroenterology", "Genetics",
    "Hematology", "Immunology", "Musculoskeletal", "Neurology", "Ophthalmology",
    "Pathology", "Psychiatry", "Pulmonary",
]
RANDOM_TAIL = ["Renal", "Reproductive"]


def next_subject(state, rng=None):
    """Pick today's subject and return (subject, updated_state).

    state keys: cycle_index (0..14), cycle_number (starts at 1), tail_order
    (shuffled copy of RANDOM_TAIL for the current cycle, or None to force a
    reshuffle — happens naturally at the start of every cycle).
    """
    rng = rng or random.Random()
    state = dict(state)
    cycle_index = state.get("cycle_index", 0)
    tail_order = state.get("tail_order")

    if cycle_index == 0 or tail_order is None:
        tail_order = RANDOM_TAIL[:]
        rng.shuffle(tail_order)

    rotation = FIXED_ORDER + tail_order
    subject = rotation[cycle_index]

    cycle_index += 1
    cycle_number = state.get("cycle_number", 1)
    if cycle_index >= len(rotation):
        cycle_index = 0
        cycle_number += 1
        tail_order = None

    state["cycle_index"] = cycle_index
    state["cycle_number"] = cycle_number
    state["tail_order"] = tail_order
    return subject, state
```

Create an empty `lib/__init__.py` so `lib` is importable as a package.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_rotation.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```powershell
git add lib/__init__.py lib/rotation.py tests/test_rotation.py
git commit -m "Add subject rotation logic"
git push
```

---

### Task 3: Question-Payload Validation

**Files:**
- Create: `lib/schema.py`
- Test: `tests/test_schema.py`

**Interfaces:**
- Consumes: nothing (pure logic).
- Produces: `validate_questions(data: dict) -> list[dict]`, raising `ValueError` on any malformed input — consumed by `generate.py` in Task 5 right after parsing Claude's output.

- [ ] **Step 1: Write the failing tests**

`tests/test_schema.py`:

```python
import pytest
from lib.schema import validate_questions


def make_question(fmt="simple4", correct=0):
    n = 5 if fmt == "vignette5" else 4
    return {
        "format": fmt,
        "stem": "A patient presents with...",
        "options": [f"Option {i}" for i in range(n)],
        "correctIndex": correct,
        "explanations": [f"Explanation {i}" for i in range(n)],
    }


def make_valid_payload():
    questions = [make_question("vignette5") for _ in range(10)] + [make_question("simple4") for _ in range(20)]
    return {"questions": questions}


def test_valid_payload_passes():
    result = validate_questions(make_valid_payload())
    assert len(result) == 30


def test_missing_questions_key_raises():
    with pytest.raises(ValueError, match="questions"):
        validate_questions({})


def test_wrong_total_count_raises():
    payload = make_valid_payload()
    payload["questions"].pop()
    with pytest.raises(ValueError, match="expected 30"):
        validate_questions(payload)


def test_wrong_option_count_for_format_raises():
    payload = make_valid_payload()
    payload["questions"][0]["options"] = ["only one option"]
    with pytest.raises(ValueError, match="requires exactly 5 options"):
        validate_questions(payload)


def test_correct_index_out_of_range_raises():
    payload = make_valid_payload()
    payload["questions"][0]["correctIndex"] = 99
    with pytest.raises(ValueError, match="correctIndex"):
        validate_questions(payload)


def test_wrong_format_mix_raises():
    questions = [make_question("simple4") for _ in range(30)]
    with pytest.raises(ValueError, match="expected 10 vignette5"):
        validate_questions({"questions": questions})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_schema.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'lib.schema'`.

- [ ] **Step 3: Write the implementation**

`lib/schema.py`:

```python
REQUIRED_VIGNETTE5 = 10
REQUIRED_SIMPLE4 = 20
FORMAT_OPTION_COUNTS = {"vignette5": 5, "simple4": 4}


def validate_questions(data):
    """Validate the parsed Claude output. Raises ValueError with a specific
    message on the first problem found. Returns the list of question dicts
    on success."""
    if not isinstance(data, dict) or "questions" not in data:
        raise ValueError("top-level response must be an object with a 'questions' key")

    questions = data["questions"]
    if not isinstance(questions, list):
        raise ValueError("'questions' must be a list")
    total_required = REQUIRED_VIGNETTE5 + REQUIRED_SIMPLE4
    if len(questions) != total_required:
        raise ValueError(f"expected {total_required} questions, got {len(questions)}")

    format_counts = {"vignette5": 0, "simple4": 0}
    for i, q in enumerate(questions):
        fmt = q.get("format")
        if fmt not in FORMAT_OPTION_COUNTS:
            raise ValueError(f"question {i}: format must be 'vignette5' or 'simple4', got {fmt!r}")
        format_counts[fmt] += 1

        expected_len = FORMAT_OPTION_COUNTS[fmt]
        options = q.get("options")
        if not isinstance(options, list) or len(options) != expected_len:
            raise ValueError(f"question {i}: {fmt} requires exactly {expected_len} options, got {options!r}")

        correct_index = q.get("correctIndex")
        if not isinstance(correct_index, int) or not (0 <= correct_index < expected_len):
            raise ValueError(
                f"question {i}: correctIndex must be an integer in range 0-{expected_len - 1}, got {correct_index!r}"
            )

        explanations = q.get("explanations")
        if not isinstance(explanations, list) or len(explanations) != expected_len:
            raise ValueError(f"question {i}: explanations must have exactly {expected_len} entries, got {explanations!r}")

        stem = q.get("stem")
        if not isinstance(stem, str) or not stem.strip():
            raise ValueError(f"question {i}: stem must be a non-empty string")

    if format_counts["vignette5"] != REQUIRED_VIGNETTE5:
        raise ValueError(f"expected {REQUIRED_VIGNETTE5} vignette5 questions, got {format_counts['vignette5']}")
    if format_counts["simple4"] != REQUIRED_SIMPLE4:
        raise ValueError(f"expected {REQUIRED_SIMPLE4} simple4 questions, got {format_counts['simple4']}")

    return questions
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_schema.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```powershell
git add lib/schema.py tests/test_schema.py
git commit -m "Add generated-question schema validation"
git push
```

---

### Task 4: Prompt Builder

**Files:**
- Create: `lib/prompt.py`
- Test: `tests/test_prompt.py`

**Interfaces:**
- Consumes: nothing (pure logic).
- Produces: `build_prompt(subject: str, folder_path: pathlib.Path, avoid_stems: list[str]) -> str` — consumed by `generate.py` in Task 5.

- [ ] **Step 1: Write the failing tests**

`tests/test_prompt.py`:

```python
from pathlib import Path
from lib.prompt import build_prompt


def test_prompt_includes_subject_and_folder():
    prompt = build_prompt("Cardiology", Path("C:/PDFs/Cardiology"), [])
    assert "Cardiology" in prompt
    assert "PDFs" in prompt
    assert "10" in prompt and "20" in prompt


def test_prompt_includes_avoid_list_when_present():
    prompt = build_prompt("Renal", Path("C:/PDFs/Renal"), ["Old question about ADH"])
    assert "Old question about ADH" in prompt


def test_prompt_omits_avoid_block_when_empty():
    prompt = build_prompt("Renal", Path("C:/PDFs/Renal"), [])
    assert "Do NOT repeat" not in prompt
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_prompt.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'lib.prompt'`.

- [ ] **Step 3: Write the implementation**

`lib/prompt.py`:

```python
def build_prompt(subject, folder_path, avoid_stems):
    avoid_block = ""
    if avoid_stems:
        bullet_list = "\n".join(f"- {s}" for s in avoid_stems)
        avoid_block = (
            "\n\nDo NOT repeat these previously-used question topics/stems "
            f"(paraphrase to something new instead):\n{bullet_list}\n"
        )

    return f"""You are writing USMLE Step 1 practice questions for a solo medical student.

Read every PDF lecture-note file inside this folder (Boards & Beyond style notes for the "{subject}" system):
{folder_path}

Generate exactly 30 original multiple-choice questions covering high-yield content from those notes:
- Exactly 10 questions in "vignette5" format: a realistic clinical-vignette stem (patient
  presentation, history, labs/imaging as relevant), 5 answer options (A-E), single best answer.
- Exactly 20 questions in "simple4" format: a shorter, more direct question testing a single fact
  or concept from the notes, 4 answer options (A-D), single best answer.

For every question, write one explanation string per option, in the same order as the options:
the explanation for the correct option must state why it is correct; the explanation for every
other option must state briefly why it is incorrect.

Base every question strictly on the content of the PDFs in the folder above. Do not invent facts
that aren't supported by the notes. Vary difficulty and sub-topics across the notes rather than
clustering on one file.{avoid_block}

Respond with structured JSON matching the provided schema only — no extra commentary."""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_prompt.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```powershell
git add lib/prompt.py tests/test_prompt.py
git commit -m "Add headless-Claude prompt builder"
git push
```

---

### Task 5: generate.py Orchestrator + First Real Run

**Files:**
- Create: `generate.py`

**Interfaces:**
- Consumes: `lib.rotation.next_subject`, `lib.schema.validate_questions`, `lib.prompt.build_prompt` (Tasks 2–4).
- Produces: `docs/questions.json` (the exact file `docs/index.html` fetches, starting Task 8) and `state.json` (rotation + history, read/written every run) — this is the artifact every later task depends on for real sample data.

- [ ] **Step 1: Write generate.py**

```python
#!/usr/bin/env python3
import json
import random
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib.rotation import next_subject
from lib.schema import validate_questions
from lib.prompt import build_prompt

REPO_ROOT = Path(__file__).parent
PDF_ROOT = Path(r"C:\Users\Omer\Desktop\BoardAndBeyond_PDFs")
STATE_PATH = REPO_ROOT / "state.json"
QUESTIONS_PATH = REPO_ROOT / "docs" / "questions.json"
CLAUDE_TIMEOUT_SECONDS = 900  # 15 min ceiling for a single headless run
HISTORY_PER_SUBJECT_CAP = 200
AVOID_STEMS_IN_PROMPT = 60

QUESTIONS_SCHEMA = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "minItems": 30,
            "maxItems": 30,
            "items": {
                "type": "object",
                "properties": {
                    "format": {"type": "string", "enum": ["vignette5", "simple4"]},
                    "stem": {"type": "string"},
                    "options": {"type": "array", "items": {"type": "string"}},
                    "correctIndex": {"type": "integer"},
                    "explanations": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["format", "stem", "options", "correctIndex", "explanations"],
            },
        }
    },
    "required": ["questions"],
}


def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"cycle_index": 0, "cycle_number": 1, "tail_order": None, "history": {}}


def save_state(state):
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def call_claude_headless(prompt, folder_path):
    # claude.cmd + shell=False avoids Windows shell-quoting problems with a
    # large multi-line prompt string (shell=True would need list2cmdline to
    # re-quote everything correctly, which is fragile for KB-sized prompts).
    cmd = [
        "claude.cmd",
        "-p", prompt,
        "--output-format", "json",
        "--json-schema", json.dumps(QUESTIONS_SCHEMA),
        "--permission-mode", "bypassPermissions",
        "--add-dir", str(folder_path),
    ]
    result = subprocess.run(
        cmd, cwd=REPO_ROOT, capture_output=True, text=True,
        timeout=CLAUDE_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI exited {result.returncode}: {result.stderr[-2000:]}")
    return result.stdout


def parse_claude_output(raw_stdout):
    outer = json.loads(raw_stdout)
    # --output-format json wraps the response as {"result": ...}; depending on
    # CLI version "result" may be a JSON string or an already-parsed object —
    # handle both rather than assuming one shape.
    payload = outer.get("result", outer) if isinstance(outer, dict) else outer
    if isinstance(payload, str):
        payload = json.loads(payload)
    return payload


def main():
    today = date.today().isoformat()
    state = load_state()
    subject, state = next_subject(state)
    folder_path = PDF_ROOT / subject

    history = state.setdefault("history", {})
    avoid_stems = history.get(subject, [])[-AVOID_STEMS_IN_PROMPT:]

    prompt = build_prompt(subject, folder_path, avoid_stems)
    raw_stdout = call_claude_headless(prompt, folder_path)
    payload = parse_claude_output(raw_stdout)
    questions = validate_questions(payload)

    rng = random.Random(today)
    rng.shuffle(questions)
    for i, q in enumerate(questions, start=1):
        q["id"] = f"{today}-{i:02d}"

    QUESTIONS_PATH.write_text(
        json.dumps({"date": today, "subject": subject, "questions": questions}, indent=2),
        encoding="utf-8",
    )

    history.setdefault(subject, []).extend(q["stem"][:100] for q in questions)
    history[subject] = history[subject][-HISTORY_PER_SUBJECT_CAP:]
    save_state(state)

    subprocess.run(["git", "add", "state.json", "docs/questions.json"], cwd=REPO_ROOT, check=True)
    subprocess.run(["git", "commit", "-m", f"Daily quiz: {subject} ({today})"], cwd=REPO_ROOT, check=True)
    subprocess.run(["git", "push"], cwd=REPO_ROOT, check=True)
    print(f"Generated 30 {subject} questions for {today} and pushed to GitHub.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it for real**

```powershell
Set-Location "C:\Users\Omer\Desktop\usmle-step1-daily-quiz"
python generate.py
```

**Important:** run this from a plain PowerShell/terminal window, not from inside an active Claude Code session — nested nested-agent invocations can be blocked by an outer session's own permission classifier, which is unrelated to whether the command itself works.

Expected: after up to a few minutes, prints `Generated 30 Cardiology questions for <today> and pushed to GitHub.` (Cardiology is first in `FIXED_ORDER`). If it fails on the `parse_claude_output` step because the actual `--output-format json` shape differs from the assumed `{"result": ...}` wrapper, run:

```powershell
claude.cmd -p "reply with the JSON object {\"ok\": true}" --output-format json --json-schema '{"type":"object","properties":{"ok":{"type":"boolean"}},"required":["ok"]}'
```

and adjust `parse_claude_output` to match the actual shape you see, then re-run `python generate.py`.

- [ ] **Step 3: Verify the output**

```powershell
Get-Content docs\questions.json | python -m json.tool | Select-Object -First 20
python -m pytest tests/ -v
```

Expected: valid JSON with `"subject": "Cardiology"` and 30 questions; all existing unit tests still pass (Task 5 doesn't change `lib/`, so this is a regression check).

- [ ] **Step 4: Commit**

Already committed and pushed by `generate.py` itself in Step 2 (`state.json` + `docs/questions.json`). Commit `generate.py` separately:

```powershell
git add generate.py
git commit -m "Add generate.py orchestrator"
git push
```

---

### Task 6: PWA Icons

**Files:**
- Create: `scripts/generate-icons.ps1`
- Create (by running the script): `docs/icons/icon-192.png`, `docs/icons/icon-512.png`, `docs/icons/apple-touch-icon.png`

**Interfaces:**
- Produces: three PNG files consumed by `manifest.json` (Task 7) and `docs/index.html`'s `<link rel="apple-touch-icon">` (Task 8).

- [ ] **Step 1: Write the icon-generation script**

`scripts/generate-icons.ps1`:

```powershell
Add-Type -AssemblyName System.Drawing

function New-Icon {
    param([int]$Size, [string]$Path)
    $bmp = New-Object System.Drawing.Bitmap($Size, $Size)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $bg = [System.Drawing.Color]::FromArgb(255, 37, 99, 235)  # #2563eb
    $g.Clear($bg)
    $fontSize = [int]($Size * 0.42)
    $font = New-Object System.Drawing.Font("Arial", $fontSize, [System.Drawing.FontStyle]::Bold)
    $brush = [System.Drawing.Brushes]::White
    $fmt = New-Object System.Drawing.StringFormat
    $fmt.Alignment = [System.Drawing.StringAlignment]::Center
    $fmt.LineAlignment = [System.Drawing.StringAlignment]::Center
    $rect = New-Object System.Drawing.RectangleF(0, 0, $Size, $Size)
    $g.DrawString("Q1", $font, $brush, $rect, $fmt)
    $bmp.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose()
    $bmp.Dispose()
}

$iconDir = Join-Path $PSScriptRoot "..\docs\icons"
New-Item -ItemType Directory -Force -Path $iconDir | Out-Null
New-Icon -Size 192 -Path (Join-Path $iconDir "icon-192.png")
New-Icon -Size 512 -Path (Join-Path $iconDir "icon-512.png")
New-Icon -Size 180 -Path (Join-Path $iconDir "apple-touch-icon.png")
Write-Host "Icons written to $iconDir"
```

- [ ] **Step 2: Run it**

```powershell
Set-Location "C:\Users\Omer\Desktop\usmle-step1-daily-quiz"
.\scripts\generate-icons.ps1
```

Expected: prints `Icons written to ...\docs\icons` and the three PNG files exist.

- [ ] **Step 3: Verify**

```powershell
Get-ChildItem docs\icons
```

Expected: `icon-192.png`, `icon-512.png`, `apple-touch-icon.png`, all non-zero size.

- [ ] **Step 4: Commit**

```powershell
git add scripts/generate-icons.ps1 docs/icons/*.png
git commit -m "Add PWA icon generator and generated icons"
git push
```

---

### Task 7: PWA Manifest

**Files:**
- Create: `docs/manifest.json`

**Interfaces:**
- Produces: `docs/manifest.json`, linked from `docs/index.html`'s `<link rel="manifest">` in Task 8.

- [ ] **Step 1: Write manifest.json**

`docs/manifest.json`:

```json
{
  "name": "USMLE Step 1 Daily Quiz",
  "short_name": "Step1 Quiz",
  "description": "Daily 30-question USMLE Step 1 practice quiz generated from Boards & Beyond notes",
  "start_url": "./index.html",
  "scope": "./",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#0f172a",
  "theme_color": "#2563eb",
  "icons": [
    { "src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable" },
    { "src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable" }
  ]
}
```

- [ ] **Step 2: Verify it's valid JSON**

```powershell
Get-Content docs\manifest.json | python -m json.tool
```

Expected: pretty-printed JSON with no errors.

- [ ] **Step 3: Commit**

```powershell
git add docs/manifest.json
git commit -m "Add PWA manifest"
git push
```

---

### Task 8: Daily Quiz Core Engine (docs/index.html)

**Files:**
- Create: `docs/index.html`

**Interfaces:**
- Consumes: `docs/questions.json` (Task 5's output, via `fetch('questions.json?v=' + Date.now())`), `docs/manifest.json` (Task 7).
- Produces: the functions `loadJSON`, `saveJSON`, `todayStr`, `renderHome`, `renderQuestion`, `selectOption`, `nextQuestion`, `finishSession`, and the extension hooks `onAnswerSubmitted(question, selectedIndex, isCorrect)`, `renderQuestionExtras(question)`, `attachExtrasHandlers(question)` — Task 9 replaces `onAnswerSubmitted` and the body of `startReviewQuiz`; Task 10 replaces `renderQuestionExtras`, `attachExtrasHandlers`, and the body of `startBookmarksQuiz`. The `LS_KEYS` object names every localStorage key used by all three tasks.

- [ ] **Step 1: Write docs/index.html**

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>USMLE Step 1 Daily Quiz</title>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#2563eb">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Step1 Quiz">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<link rel="manifest" href="manifest.json">
<style>
  :root {
    --bg: #0f172a; --panel: #1e293b; --text: #e2e8f0; --muted: #94a3b8;
    --accent: #2563eb; --correct: #16a34a; --incorrect: #dc2626; --border: #334155;
  }
  * { box-sizing: border-box; }
  body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg); color: var(--text); min-height: 100vh; }
  #app { max-width: 640px; margin: 0 auto; padding: 16px; padding-bottom: 48px; }
  h1 { font-size: 1.3rem; margin: 8px 0 4px; }
  .subtitle { color: var(--muted); margin: 0 0 20px; font-size: 0.9rem; }
  .card { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 16px; margin-bottom: 12px; }
  .home-btn { display: block; width: 100%; text-align: left; background: var(--panel); border: 1px solid var(--border);
    color: var(--text); border-radius: 12px; padding: 16px; margin-bottom: 12px; font-size: 1rem; cursor: pointer; }
  .home-btn:active { background: var(--accent); }
  .home-btn .count { color: var(--muted); font-size: 0.85rem; margin-top: 4px; }
  .progress-bar { height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; margin-bottom: 16px; }
  .progress-bar-fill { height: 100%; background: var(--accent); transition: width 0.2s; }
  .stem { font-size: 1.05rem; line-height: 1.5; margin-bottom: 16px; white-space: pre-wrap; }
  .option { display: block; width: 100%; text-align: left; background: var(--panel); border: 1px solid var(--border);
    color: var(--text); border-radius: 10px; padding: 12px 14px; margin-bottom: 10px; font-size: 0.95rem; cursor: pointer; }
  .option.correct { background: rgba(22,163,74,0.25); border-color: var(--correct); }
  .option.incorrect { background: rgba(220,38,38,0.25); border-color: var(--incorrect); }
  .option:disabled { cursor: default; opacity: 0.9; }
  .explanation { background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 12px 14px; margin-top: 4px; margin-bottom: 8px; font-size: 0.9rem; }
  .explanation.correct-exp { border-color: var(--correct); }
  .explanation.incorrect-exp { border-color: var(--incorrect); opacity: 0.85; }
  .btn-primary { display: block; width: 100%; padding: 14px; border: none; border-radius: 10px;
    background: var(--accent); color: white; font-size: 1rem; font-weight: 600; cursor: pointer; margin-top: 12px; }
  .btn-secondary { display: block; width: 100%; padding: 12px; border: 1px solid var(--border); border-radius: 10px;
    background: transparent; color: var(--text); font-size: 0.95rem; cursor: pointer; margin-top: 8px; }
  .top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
  .back-link { color: var(--muted); text-decoration: none; font-size: 0.9rem; background: none; border: none; cursor: pointer; }
  .star-btn { background: none; border: none; font-size: 1.4rem; cursor: pointer; color: var(--muted); }
  .star-btn.active { color: #facc15; }
  .empty-state { color: var(--muted); text-align: center; padding: 32px 16px; }
</style>
</head>
<body>
<div id="app"></div>
<script>
'use strict';

const LS_KEYS = {
  progress: 'usmle_progress_v1',
  history: 'usmle_history_v1',
  wrongBank: 'usmle_wrong_bank_v1',
  bookmarks: 'usmle_bookmarks_v1',
};

function loadJSON(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch (e) {
    return fallback;
  }
}

function saveJSON(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

async function fetchDailyQuestions() {
  const res = await fetch(`questions.json?v=${Date.now()}`, { cache: 'no-store' });
  if (!res.ok) throw new Error(`Failed to load questions.json: ${res.status}`);
  return res.json();
}

function getProgress() {
  const p = loadJSON(LS_KEYS.progress, null);
  if (p && p.date === todayStr()) return p;
  return null;
}

function saveProgress(progress) {
  saveJSON(LS_KEYS.progress, progress);
}

function getHistory() {
  return loadJSON(LS_KEYS.history, []);
}

function addHistoryEntry(entry) {
  const history = getHistory();
  history.push(entry);
  saveJSON(LS_KEYS.history, history.slice(-365));
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// --- extension hooks (Task 9 replaces onAnswerSubmitted; Task 10 replaces the other two) ---
function onAnswerSubmitted(question, selectedIndex, isCorrect) {
  // Task 9 (Review Missed) replaces this to also record wrong answers.
}

function renderQuestionExtras(question) {
  // Task 10 (Bookmarks) replaces this to render a star toggle button.
  return '';
}

function attachExtrasHandlers(question) {
  // Task 10 (Bookmarks) replaces this to wire the star toggle button's click handler.
}

// --- app state ---
let session = null; // { mode: 'daily'|'review'|'bookmarks', questions, index, progress? }

const app = document.getElementById('app');

function render(html) {
  app.innerHTML = html;
}

async function renderHome() {
  const progress = getProgress();
  let dailyLabel = 'Start Daily Quiz';
  let dailySub = '30 new questions';
  if (progress && progress.completed) {
    dailyLabel = 'Retry Daily Quiz';
    dailySub = `Completed today — score ${progress.score}/${progress.total}`;
  } else if (progress && progress.answers.length > 0) {
    dailyLabel = 'Continue Daily Quiz';
    dailySub = `Question ${progress.answers.length + 1} of ${progress.total}`;
  }

  const wrongBank = loadJSON(LS_KEYS.wrongBank, {});
  const bookmarks = loadJSON(LS_KEYS.bookmarks, {});
  const wrongCount = Object.keys(wrongBank).length;
  const bookmarkCount = Object.keys(bookmarks).length;

  render(`
    <h1>USMLE Step 1 Daily Quiz</h1>
    <p class="subtitle">Boards &amp; Beyond — 30 questions a day</p>
    <button class="home-btn" id="btn-daily">
      <div>${dailyLabel}</div>
      <div class="count">${dailySub}</div>
    </button>
    <button class="home-btn" id="btn-review">
      <div>Review Missed</div>
      <div class="count">${wrongCount} question${wrongCount === 1 ? '' : 's'} to review</div>
    </button>
    <button class="home-btn" id="btn-bookmarks">
      <div>Bookmarked</div>
      <div class="count">${bookmarkCount} bookmarked</div>
    </button>
  `);

  document.getElementById('btn-daily').addEventListener('click', startDailyQuiz);
  document.getElementById('btn-review').addEventListener('click', startReviewQuiz);
  document.getElementById('btn-bookmarks').addEventListener('click', startBookmarksQuiz);
}

async function startDailyQuiz() {
  let progress = getProgress();
  let data;
  try {
    data = await fetchDailyQuestions();
  } catch (e) {
    render(`<div class="empty-state">Could not load today's questions.<br>${escapeHtml(e.message)}</div>
      <button class="btn-secondary" id="btn-back">Back</button>`);
    document.getElementById('btn-back').addEventListener('click', renderHome);
    return;
  }

  if (!progress) {
    progress = {
      date: todayStr(),
      subject: data.subject,
      total: data.questions.length,
      answers: [],
      score: 0,
      completed: false,
    };
    saveProgress(progress);
  }

  session = {
    mode: 'daily',
    questions: data.questions,
    index: progress.answers.length,
    progress,
  };

  if (progress.completed) {
    renderSummary();
  } else {
    renderQuestion();
  }
}

function renderQuestion() {
  const q = session.questions[session.index];
  const total = session.questions.length;
  const pct = Math.round((session.index / total) * 100);

  render(`
    <div class="top-bar">
      <button class="back-link" id="btn-home">&larr; Home</button>
      <span id="extras">${renderQuestionExtras(q)}</span>
      <span class="subtitle" style="margin:0;">Q ${session.index + 1} / ${total}</span>
    </div>
    <div class="progress-bar"><div class="progress-bar-fill" style="width:${pct}%"></div></div>
    <div class="card">
      <div class="stem">${escapeHtml(q.stem)}</div>
      <div id="options"></div>
      <div id="explanations"></div>
      <div id="next-holder"></div>
    </div>
  `);

  document.getElementById('btn-home').addEventListener('click', () => { session = null; renderHome(); });
  attachExtrasHandlers(q);

  const optionsEl = document.getElementById('options');
  q.options.forEach((opt, i) => {
    const btn = document.createElement('button');
    btn.className = 'option';
    btn.textContent = `${String.fromCharCode(65 + i)}. ${opt}`;
    btn.addEventListener('click', () => selectOption(i));
    optionsEl.appendChild(btn);
  });
}

function selectOption(selectedIndex) {
  const q = session.questions[session.index];
  const isCorrect = selectedIndex === q.correctIndex;
  const optionButtons = document.querySelectorAll('#options .option');

  optionButtons.forEach((btn, i) => {
    btn.disabled = true;
    if (i === q.correctIndex) btn.classList.add('correct');
    if (i === selectedIndex && !isCorrect) btn.classList.add('incorrect');
  });

  const expEl = document.getElementById('explanations');
  q.explanations.forEach((text, i) => {
    const div = document.createElement('div');
    div.className = 'explanation ' + (i === q.correctIndex ? 'correct-exp' : 'incorrect-exp');
    div.textContent = `${String.fromCharCode(65 + i)}. ${text}`;
    expEl.appendChild(div);
  });

  onAnswerSubmitted(q, selectedIndex, isCorrect);

  if (session.mode === 'daily') {
    session.progress.answers.push({ questionId: q.id, selectedIndex, correct: isCorrect });
    if (isCorrect) session.progress.score += 1;
    saveProgress(session.progress);
  }

  const nextHolder = document.getElementById('next-holder');
  const nextBtn = document.createElement('button');
  nextBtn.className = 'btn-primary';
  nextBtn.textContent = session.index + 1 < session.questions.length ? 'Next' : 'Finish';
  nextBtn.addEventListener('click', nextQuestion);
  nextHolder.appendChild(nextBtn);
}

function nextQuestion() {
  session.index += 1;
  if (session.index >= session.questions.length) {
    finishSession();
  } else {
    renderQuestion();
  }
}

function finishSession() {
  if (session.mode === 'daily') {
    session.progress.completed = true;
    saveProgress(session.progress);
    addHistoryEntry({
      date: session.progress.date,
      subject: session.progress.subject,
      score: session.progress.score,
      total: session.progress.total,
    });
    renderSummary();
  } else {
    session = null;
    renderHome();
  }
}

function renderSummary() {
  const p = session.progress;
  render(`
    <h1>Daily Quiz Complete</h1>
    <div class="card">
      <p>Subject: ${escapeHtml(p.subject)}</p>
      <p>Score: ${p.score} / ${p.total}</p>
    </div>
    <button class="btn-primary" id="btn-home">Back to Home</button>
  `);
  document.getElementById('btn-home').addEventListener('click', () => { session = null; renderHome(); });
}

// Real implementations land in Task 9 (Review) and Task 10 (Bookmarks).
// For this task, both currently just return to Home.
async function startReviewQuiz() { await renderHome(); }
async function startBookmarksQuiz() { await renderHome(); }

renderHome();
</script>
</body>
</html>
```

- [ ] **Step 2: Serve it locally and test manually**

```powershell
Set-Location "C:\Users\Omer\Desktop\usmle-step1-daily-quiz\docs"
python -m http.server 8000
```

Open `http://localhost:8000/` in a browser (use the Browser tool, resized to a mobile viewport). Verify against these acceptance criteria:

1. Home screen shows "Start Daily Quiz — 30 new questions", "Review Missed — 0 questions to review", "Bookmarked — 0 bookmarked".
2. Clicking "Start Daily Quiz" shows question 1 of 30 with a stem and either 4 or 5 options.
3. Clicking an option: all options become disabled, the correct one turns green, a wrong pick (if selected) turns red, and an explanation block appears under each option.
4. Clicking "Next" advances to question 2, progress bar and "Q x/30" update.
5. Reloading the page mid-quiz and clicking "Continue Daily Quiz" resumes at the same question (progress persisted).
6. Completing all 30 questions shows the summary screen with a score, and the home screen afterward shows "Retry Daily Quiz — Completed today — score X/30".
7. Clicking "Review Missed" or "Bookmarked" returns to Home (expected for this task — real behavior ships in Tasks 9–10).

Stop the server with Ctrl+C when done.

- [ ] **Step 3: Commit**

```powershell
git add docs/index.html
git commit -m "Add Daily Quiz core engine (PWA)"
git push
```

---

### Task 9: Review Missed Mode

**Files:**
- Modify: `docs/index.html`

**Interfaces:**
- Consumes: `LS_KEYS.wrongBank`, `session`, `renderQuestion` (from Task 8).
- Produces: a fully working "Review Missed" mode; wrong answers get captured on every quiz (daily or review), and a correct answer in review mode removes that question from the bank.

- [ ] **Step 1: Replace `onAnswerSubmitted`**

Find this function in `docs/index.html` (added in Task 8):

```javascript
function onAnswerSubmitted(question, selectedIndex, isCorrect) {
  // Task 9 (Review Missed) replaces this to also record wrong answers.
}
```

Replace it with:

```javascript
function onAnswerSubmitted(question, selectedIndex, isCorrect) {
  const wrongBank = loadJSON(LS_KEYS.wrongBank, {});
  if (!isCorrect) {
    const existing = wrongBank[question.id];
    wrongBank[question.id] = {
      question,
      dateAdded: existing ? existing.dateAdded : todayStr(),
      timesWrong: (existing ? existing.timesWrong : 0) + 1,
    };
    saveJSON(LS_KEYS.wrongBank, wrongBank);
  } else if (session.mode === 'review' && wrongBank[question.id]) {
    delete wrongBank[question.id];
    saveJSON(LS_KEYS.wrongBank, wrongBank);
  }
}
```

- [ ] **Step 2: Replace `startReviewQuiz`**

Find:

```javascript
async function startReviewQuiz() { await renderHome(); }
```

Replace with:

```javascript
async function startReviewQuiz() {
  const wrongBank = loadJSON(LS_KEYS.wrongBank, {});
  const questions = Object.values(wrongBank).map(entry => entry.question);
  if (questions.length === 0) {
    render(`<div class="empty-state">Nothing to review — no wrong answers saved yet.</div>
      <button class="btn-secondary" id="btn-back">Back</button>`);
    document.getElementById('btn-back').addEventListener('click', renderHome);
    return;
  }
  session = { mode: 'review', questions, index: 0 };
  renderQuestion();
}
```

- [ ] **Step 3: Test manually**

```powershell
Set-Location "C:\Users\Omer\Desktop\usmle-step1-daily-quiz\docs"
python -m http.server 8000
```

In the browser: start a Daily Quiz, deliberately answer 2–3 questions wrong, finish or go Home. Verify:

1. Home screen now shows "Review Missed — N questions to review" with the correct count.
2. Clicking "Review Missed" shows only the questions you got wrong.
3. Answering one correctly in Review mode and returning Home: the count decreases by 1.
4. Clicking "Review Missed" with the bank empty shows "Nothing to review — no wrong answers saved yet." with a working Back button.

Stop the server with Ctrl+C.

- [ ] **Step 4: Commit**

```powershell
git add docs/index.html
git commit -m "Add Review Missed mode with wrong-answer bank"
git push
```

---

### Task 10: Bookmarked Mode

**Files:**
- Modify: `docs/index.html`

**Interfaces:**
- Consumes: `LS_KEYS.bookmarks`, `session`, `renderQuestion`, the `#extras` span (from Task 8).
- Produces: a star-toggle button on every question and a fully working "Bookmarked" mode.

- [ ] **Step 1: Replace `renderQuestionExtras` and `attachExtrasHandlers`**

Find these two functions in `docs/index.html`:

```javascript
function renderQuestionExtras(question) {
  // Task 10 (Bookmarks) replaces this to render a star toggle button.
  return '';
}

function attachExtrasHandlers(question) {
  // Task 10 (Bookmarks) replaces this to wire the star toggle button's click handler.
}
```

Replace both with:

```javascript
function renderQuestionExtras(question) {
  const bookmarks = loadJSON(LS_KEYS.bookmarks, {});
  const active = !!bookmarks[question.id];
  return `<button class="star-btn ${active ? 'active' : ''}" id="btn-star">${active ? '\u2605' : '\u2606'}</button>`;
}

function attachExtrasHandlers(question) {
  const btn = document.getElementById('btn-star');
  if (!btn) return;
  btn.addEventListener('click', () => {
    const bookmarks = loadJSON(LS_KEYS.bookmarks, {});
    if (bookmarks[question.id]) {
      delete bookmarks[question.id];
    } else {
      bookmarks[question.id] = { question, dateAdded: todayStr() };
    }
    saveJSON(LS_KEYS.bookmarks, bookmarks);
    document.getElementById('extras').innerHTML = renderQuestionExtras(question);
    attachExtrasHandlers(question);
  });
}
```

- [ ] **Step 2: Replace `startBookmarksQuiz`**

Find:

```javascript
async function startBookmarksQuiz() { await renderHome(); }
```

Replace with:

```javascript
async function startBookmarksQuiz() {
  const bookmarks = loadJSON(LS_KEYS.bookmarks, {});
  const questions = Object.values(bookmarks).map(entry => entry.question);
  if (questions.length === 0) {
    render(`<div class="empty-state">No bookmarked questions yet.</div>
      <button class="btn-secondary" id="btn-back">Back</button>`);
    document.getElementById('btn-back').addEventListener('click', renderHome);
    return;
  }
  session = { mode: 'bookmarks', questions, index: 0 };
  renderQuestion();
}
```

- [ ] **Step 3: Test manually**

```powershell
Set-Location "C:\Users\Omer\Desktop\usmle-step1-daily-quiz\docs"
python -m http.server 8000
```

In the browser: start a Daily Quiz, on question 1 click the star icon (top of the card, next to "Q 1/30"). Verify:

1. The star fills in (☆ → ★) immediately on click, no page reload needed.
2. Go Home: "Bookmarked" now shows "1 bookmarked".
3. Click "Bookmarked": shows that one question; answering it (right or wrong) does not remove it from Bookmarked (unlike Review Missed).
4. Re-open the same question and click the star again: it un-fills, and going Home shows "0 bookmarked".

Stop the server with Ctrl+C.

- [ ] **Step 4: Commit**

```powershell
git add docs/index.html
git commit -m "Add Bookmarked mode with star toggle"
git push
```

---

### Task 11: GitHub Pages + Live Mobile Verification

**Files:**
- None created — infra/config task against the existing repo.

**Interfaces:**
- Consumes: everything under `docs/` (Tasks 6–10).
- Produces: a live URL `https://<username>.github.io/usmle-step1-daily-quiz/`.

- [ ] **Step 1: Enable GitHub Pages**

```powershell
$GhUser = gh api user --jq .login
'{"source":{"branch":"main","path":"/docs"}}' | gh api --method POST "repos/$GhUser/usmle-step1-daily-quiz/pages" --input -
```

If this errors (Pages API payload shapes occasionally change), enable it manually instead: on github.com, go to the repo → **Settings → Pages → Build and deployment → Source: Deploy from a branch → Branch: `main` / `/docs` → Save**.

- [ ] **Step 2: Wait for the first deployment and verify it's live**

```powershell
Start-Sleep -Seconds 60
$GhUser = gh api user --jq .login
Invoke-WebRequest -Uri "https://$GhUser.github.io/usmle-step1-daily-quiz/" -UseBasicParsing | Select-Object StatusCode
```

Expected: `StatusCode 200`. If it's still 404, wait another minute (first Pages deploy can take a few minutes) and retry.

- [ ] **Step 3: Verify on a mobile viewport in the Browser tool**

Navigate the Browser pane to `https://<username>.github.io/usmle-step1-daily-quiz/`, resize to the `mobile` preset, and run through the same checklist as Task 8/9/10 Step 3 (Daily Quiz, Review Missed, Bookmarked) against the live site instead of `localhost`. Also verify:

1. No console errors (`read_console_messages`).
2. The page has a `<link rel="manifest">` resolving to a 200 (check via `read_network_requests`).

- [ ] **Step 4: No commit needed**

This task only changes repo settings, not files.

---

### Task 12: Windows Task Scheduler Automation

**Files:**
- Create: `scripts/setup-task-scheduler.ps1`

**Interfaces:**
- Consumes: `generate.py` (Task 5).
- Produces: a registered Windows Scheduled Task named `USMLE Daily Quiz Generator`.

- [ ] **Step 1: Write the setup script**

`scripts/setup-task-scheduler.ps1`:

```powershell
$PythonExe = "C:\Users\Omer\AppData\Local\Programs\Python\Python312\python.exe"
$RepoRoot = "C:\Users\Omer\Desktop\usmle-step1-daily-quiz"
$TaskName = "USMLE Daily Quiz Generator"

$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "generate.py" -WorkingDirectory $RepoRoot
$Trigger = New-ScheduledTaskTrigger -Daily -At "6:00AM"
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -DontStopOnIdleEnd
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger `
  -Settings $Settings -Principal $Principal `
  -Description "Generates today's 30 USMLE Step 1 practice questions and pushes them to GitHub Pages." `
  -Force

Write-Host "Registered scheduled task '$TaskName'. Runs daily at 6:00 AM, catches up on next login if missed, wakes the PC if it's asleep (not off) and the hardware supports it."
```

- [ ] **Step 2: Run it (as the logged-in user, not elevated)**

```powershell
Set-Location "C:\Users\Omer\Desktop\usmle-step1-daily-quiz"
.\scripts\setup-task-scheduler.ps1
```

Expected: prints the confirmation message with no errors.

- [ ] **Step 3: Verify the task is registered**

```powershell
Get-ScheduledTask -TaskName "USMLE Daily Quiz Generator" | Select-Object TaskName, State
```

Expected: `State` is `Ready`.

- [ ] **Step 4: Dry-run it through the scheduler (not just interactively)**

```powershell
Start-ScheduledTask -TaskName "USMLE Daily Quiz Generator"
Start-Sleep -Seconds 30
Get-ScheduledTaskInfo -TaskName "USMLE Daily Quiz Generator" | Select-Object LastRunTime, LastTaskResult
```

Expected: `LastTaskResult` is `0` (success) once the run finishes — this may take a few minutes since it calls headless Claude; re-check `Get-ScheduledTaskInfo` after waiting longer if it's still running. Confirm a new commit landed:

```powershell
git log -1 --oneline
```

Expected: shows today's `Daily quiz: <next subject> (<date>)` commit, pushed by the scheduled run.

- [ ] **Step 5: Commit**

```powershell
git add scripts/setup-task-scheduler.ps1
git commit -m "Add Windows Task Scheduler automation for daily generation"
git push
```

---

### Task 13: Finalize README

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: nothing — documentation only.

- [ ] **Step 1: Replace the README stub**

`README.md`:

```markdown
# USMLE Step 1 Daily Quiz

Daily 30-question USMLE Step 1 practice quiz, generated from local Boards & Beyond
PDF notes (`C:\Users\Omer\Desktop\BoardAndBeyond_PDFs`) via headless Claude Code,
served as a zero-backend PWA on GitHub Pages.

Live app: `https://<your-github-username>.github.io/usmle-step1-daily-quiz/`

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
```

- [ ] **Step 2: Verify**

```powershell
Get-Content README.md | Select-Object -First 5
```

Expected: shows the new title/intro, confirming the write succeeded.

- [ ] **Step 3: Commit**

```powershell
git add README.md
git commit -m "Write full setup and runbook documentation"
git push
```
