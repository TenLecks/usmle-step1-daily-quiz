from lib.prompt import build_prompt


def test_prompt_includes_subject_and_extracted_text():
    prompt = build_prompt("Cardiology", "[Heart Failure] EF is reduced in HFrEF.", [])
    assert "Cardiology" in prompt
    assert "EF is reduced in HFrEF" in prompt
    assert "10" in prompt and "20" in prompt


def test_prompt_includes_avoid_list_when_present():
    prompt = build_prompt("Renal", "[ADH] ADH acts on the collecting duct.", ["Old question about ADH"])
    assert "Old question about ADH" in prompt


def test_prompt_omits_avoid_block_when_empty():
    prompt = build_prompt("Renal", "[ADH] ADH acts on the collecting duct.", [])
    assert "Do NOT repeat" not in prompt


def test_prompt_has_no_embedded_newlines():
    # claude.cmd is a Windows batch-file wrapper; batch-file argument passing
    # is line-oriented and silently truncates a -p prompt at the first
    # newline, so the prompt must be a single line with no \n characters.
    prompt = build_prompt(
        "Cardiology", "[Heart Failure] EF is reduced in HFrEF.", ["Old question about ADH"]
    )
    assert "\n" not in prompt


def test_prompt_strips_newlines_from_llm_generated_avoid_stems():
    # avoid_stems entries come from prior LLM-generated question stems
    # (truncated, unsanitized) — a stem the model happened to format with
    # embedded newlines must not reintroduce them into the prompt.
    prompt = build_prompt(
        "Cardiology",
        "[Heart Failure] EF is reduced in HFrEF.",
        ["Old stem line one\nLabs:\nNa 140\nK 6.2"],
    )
    assert "\n" not in prompt
    assert "Labs:" in prompt and "Na 140" in prompt


def test_prompt_strips_newlines_from_extracted_text():
    # extracted_text comes from lib.extract.extract_subject_text, which
    # already flattens whitespace per-file — but build_prompt must not
    # assume that and should be safe even if a raw multi-line string is
    # passed in directly (defense in depth against the exact bug this
    # single-line design exists to prevent).
    prompt = build_prompt(
        "Cardiology", "[Heart Failure] Line one\nLine two\nLine three", []
    )
    assert "\n" not in prompt
    assert "Line one" in prompt and "Line two" in prompt
