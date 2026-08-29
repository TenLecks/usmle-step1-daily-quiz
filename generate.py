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
from lib.extract import extract_subject_text
from lib.shuffle import shuffle_question_options

REPO_ROOT = Path(__file__).parent
PDF_ROOT = Path(r"C:\Users\Omer\Desktop\BoardAndBeyond_PDFs")
STATE_PATH = REPO_ROOT / "state.json"
QUESTIONS_PATH = REPO_ROOT / "docs" / "questions.json"
ARCHIVE_DIR = REPO_ROOT / "docs" / "archive"
ARCHIVE_INDEX_PATH = ARCHIVE_DIR / "index.json"
CLAUDE_TIMEOUT_SECONDS = 900  # 15 min ceiling for a single headless run
HISTORY_PER_SUBJECT_CAP = 200
AVOID_STEMS_IN_PROMPT = 60
# Text-only generation (no agentic PDF reading) costs well under $1-2 per
# subject in practice. This is a hard ceiling, not an expected cost — it
# exists so a misbehaving run fails loudly and cheaply instead of silently
# spending an unbounded amount, which is what happened before this design
# (one failed attempt reached $23.57 before hitting the account's own rate
# limit, with zero cost governor anywhere in the pipeline).
CLAUDE_MAX_BUDGET_USD = "5"

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
                    "overview": {"type": "string"},
                },
                "required": ["format", "stem", "options", "correctIndex", "explanations", "overview"],
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


def update_archive(subject, questions):
    """Append today's questions to this subject's cumulative archive (for the
    PWA's "Browse by Subject" mode), and update the subject->count index the
    PWA uses to render the subject menu without fetching all 15 archives."""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = ARCHIVE_DIR / f"{subject}.json"
    if archive_path.exists():
        archive = json.loads(archive_path.read_text(encoding="utf-8"))
    else:
        archive = {"subject": subject, "questions": []}
    archive["questions"].extend(questions)
    archive_path.write_text(json.dumps(archive, indent=2), encoding="utf-8")

    index = json.loads(ARCHIVE_INDEX_PATH.read_text(encoding="utf-8")) if ARCHIVE_INDEX_PATH.exists() else {}
    index[subject] = len(archive["questions"])
    ARCHIVE_INDEX_PATH.write_text(json.dumps(index, indent=2), encoding="utf-8")


def call_claude_headless(prompt):
    # claude.cmd + shell=False avoids Windows shell-quoting problems (shell=True
    # would need list2cmdline to re-quote everything correctly, which is
    # fragile for KB-sized prompts). NOTE: `prompt` (from build_prompt) MUST be
    # a single line with no embedded newlines — claude.cmd is a Windows
    # batch-file wrapper, and batch-file argument passing is line-oriented:
    # a multi-line -p prompt is silently truncated at the first newline.
    #
    # No --add-dir: the prompt already contains the subject's PDF text
    # (extracted locally, see lib/extract.py) rather than asking Claude to
    # read the PDF files itself, so no filesystem access is needed at all.
    # The prompt (subject text can run 100K+ characters) is piped via stdin,
    # not passed as a -p argument: Windows caps a process's total command-line
    # length (~32K chars), which a large embedded-text prompt exceeds,
    # raising "WinError 206: The filename or extension is too long". Passing
    # no prompt after -p makes the CLI read it from stdin instead.
    cmd = [
        "claude.cmd",
        "-p",
        "--output-format", "json",
        "--json-schema", json.dumps(QUESTIONS_SCHEMA),
        "--permission-mode", "bypassPermissions",
        "--max-budget-usd", CLAUDE_MAX_BUDGET_USD,
    ]
    result = subprocess.run(
        cmd, cwd=REPO_ROOT, input=prompt, capture_output=True, text=True,
        timeout=CLAUDE_TIMEOUT_SECONDS, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI exited {result.returncode}: {result.stderr[-2000:]}")
    return result.stdout


def parse_claude_output(raw_stdout):
    outer = json.loads(raw_stdout)
    if not isinstance(outer, dict):
        return outer
    if outer.get("is_error"):
        raise RuntimeError(
            f"claude CLI reported an error: {outer.get('result')!r} "
            f"(permission_denials={outer.get('permission_denials')})"
        )
    # --output-format json includes a ready-parsed "structured_output" field
    # when --json-schema is used — prefer it. Fall back to parsing "result"
    # (a JSON string, or occasionally an already-parsed object) for CLI
    # versions where structured_output isn't present.
    if "structured_output" in outer:
        return outer["structured_output"]
    payload = outer.get("result", outer)
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

    extracted_text = extract_subject_text(folder_path)
    prompt = build_prompt(subject, extracted_text, avoid_stems)
    raw_stdout = call_claude_headless(prompt)
    payload = parse_claude_output(raw_stdout)
    questions = validate_questions(payload)

    rng = random.Random(today)
    rng.shuffle(questions)
    # LLMs writing MCQs tend to place the correct answer at the same
    # position across many questions (confirmed directly: one real
    # generated set had it at index 0 in all 30/30 questions). Reorder each
    # question's own options locally so the correct answer's position is
    # actually randomized, independent of the model's positional bias.
    questions = [shuffle_question_options(q, rng) for q in questions]
    for i, q in enumerate(questions, start=1):
        q["id"] = f"{today}-{i:02d}"

    QUESTIONS_PATH.write_text(
        json.dumps({"date": today, "subject": subject, "questions": questions}, indent=2),
        encoding="utf-8",
    )
    update_archive(subject, questions)

    history.setdefault(subject, []).extend(q["stem"][:100] for q in questions)
    history[subject] = history[subject][-HISTORY_PER_SUBJECT_CAP:]
    save_state(state)

    subprocess.run(
        ["git", "add", "state.json", "docs/questions.json", "docs/archive"],
        cwd=REPO_ROOT, check=True,
    )
    subprocess.run(["git", "commit", "-m", f"Daily quiz: {subject} ({today})"], cwd=REPO_ROOT, check=True)
    subprocess.run(["git", "push"], cwd=REPO_ROOT, check=True)
    print(f"Generated 30 {subject} questions for {today} and pushed to GitHub.")


if __name__ == "__main__":
    main()
