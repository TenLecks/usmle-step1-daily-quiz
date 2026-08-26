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
