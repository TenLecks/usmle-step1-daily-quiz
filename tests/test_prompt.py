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


def test_prompt_has_no_embedded_newlines():
    # claude.cmd is a Windows batch-file wrapper; batch-file argument passing
    # is line-oriented and silently truncates a -p prompt at the first
    # newline, so the prompt must be a single line with no \n characters.
    prompt = build_prompt(
        "Cardiology", Path("C:/PDFs/Cardiology"), ["Old question about ADH"]
    )
    assert "\n" not in prompt


def test_prompt_strips_newlines_from_llm_generated_avoid_stems():
    # avoid_stems entries come from prior LLM-generated question stems
    # (truncated, unsanitized) — a stem the model happened to format with
    # embedded newlines must not reintroduce them into the prompt.
    prompt = build_prompt(
        "Cardiology",
        Path("C:/PDFs/Cardiology"),
        ["Old stem line one\nLabs:\nNa 140\nK 6.2"],
    )
    assert "\n" not in prompt
    assert "Labs:" in prompt and "Na 140" in prompt
