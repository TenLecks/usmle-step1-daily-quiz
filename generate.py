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
