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
        "overview": "High-yield overview of the underlying disease and mechanism.",
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


def test_missing_overview_raises():
    payload = make_valid_payload()
    del payload["questions"][0]["overview"]
    with pytest.raises(ValueError, match="overview"):
        validate_questions(payload)


def test_blank_overview_raises():
    payload = make_valid_payload()
    payload["questions"][0]["overview"] = "   "
    with pytest.raises(ValueError, match="overview"):
        validate_questions(payload)
