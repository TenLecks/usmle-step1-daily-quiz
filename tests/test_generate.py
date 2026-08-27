import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from generate import parse_claude_output


def test_parse_claude_output_returns_structured_output_directly():
    raw = json.dumps({
        "is_error": False,
        "structured_output": {"questions": ["q1", "q2"]},
        "result": "ignored when structured_output is present",
    })
    assert parse_claude_output(raw) == {"questions": ["q1", "q2"]}


def test_parse_claude_output_raises_on_is_error():
    raw = json.dumps({
        "is_error": True,
        "result": "something went wrong",
        "permission_denials": [],
    })
    with pytest.raises(RuntimeError):
        parse_claude_output(raw)


def test_parse_claude_output_parses_legacy_result_json_string():
    # Legacy response: no "structured_output" key, "result" is a JSON string.
    inner = {"questions": ["q1", "q2"]}
    raw = json.dumps({
        "is_error": False,
        "result": json.dumps(inner),
    })
    assert parse_claude_output(raw) == inner


def test_parse_claude_output_returns_non_dict_outer_as_is():
    # Guards the isinstance(outer, dict) check — a bare list must pass through
    # unchanged instead of crashing on outer.get(...).
    raw = json.dumps(["not", "a", "dict"])
    assert parse_claude_output(raw) == ["not", "a", "dict"]
