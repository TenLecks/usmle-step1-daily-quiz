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

        overview = q.get("overview")
        if not isinstance(overview, str) or not overview.strip():
            raise ValueError(f"question {i}: overview must be a non-empty string")

        stem = q.get("stem")
        if not isinstance(stem, str) or not stem.strip():
            raise ValueError(f"question {i}: stem must be a non-empty string")

    if format_counts["vignette5"] != REQUIRED_VIGNETTE5:
        raise ValueError(f"expected {REQUIRED_VIGNETTE5} vignette5 questions, got {format_counts['vignette5']}")
    if format_counts["simple4"] != REQUIRED_SIMPLE4:
        raise ValueError(f"expected {REQUIRED_SIMPLE4} simple4 questions, got {format_counts['simple4']}")

    return questions
