import random
from collections import Counter

import pytest

from lib.shuffle import shuffle_question_options


def make_question(correct_index=0, n=4):
    return {
        "format": "simple4" if n == 4 else "vignette5",
        "stem": "Sample stem",
        "options": [f"Option {chr(65 + i)}" for i in range(n)],
        "correctIndex": correct_index,
        "explanations": [f"Explanation {chr(65 + i)}" for i in range(n)],
    }


def test_correct_option_text_still_matches_new_correct_index():
    q = make_question(correct_index=0)
    shuffled = shuffle_question_options(q, random.Random(1))
    assert shuffled["options"][shuffled["correctIndex"]] == "Option A"


def test_explanation_stays_paired_with_its_option():
    q = make_question(correct_index=2)
    shuffled = shuffle_question_options(q, random.Random(2))
    for i, opt in enumerate(shuffled["options"]):
        letter = opt[-1]
        assert shuffled["explanations"][i] == f"Explanation {letter}"


def test_option_set_is_unchanged_just_reordered():
    q = make_question(correct_index=1)
    shuffled = shuffle_question_options(q, random.Random(3))
    assert sorted(shuffled["options"]) == sorted(q["options"])


def test_does_not_mutate_the_input_question():
    q = make_question(correct_index=0)
    original_options = list(q["options"])
    shuffle_question_options(q, random.Random(4))
    assert q["options"] == original_options
    assert q["correctIndex"] == 0


def test_other_fields_are_preserved():
    q = make_question(correct_index=0)
    shuffled = shuffle_question_options(q, random.Random(5))
    assert shuffled["stem"] == q["stem"]
    assert shuffled["format"] == q["format"]


def test_correct_index_distribution_is_not_always_the_same_position():
    # Regression test for the real bug: 30/30 generated questions all had
    # correctIndex 0. Shuffling 200 copies of the same question with
    # different rng draws must not collapse back onto a single position.
    positions = Counter()
    for seed in range(200):
        q = make_question(correct_index=0, n=4)
        shuffled = shuffle_question_options(q, random.Random(seed))
        positions[shuffled["correctIndex"]] += 1
    assert len(positions) > 1
    assert max(positions.values()) < 200


@pytest.mark.parametrize("n", [4, 5])
def test_works_for_both_option_counts(n):
    q = make_question(correct_index=n - 1, n=n)
    shuffled = shuffle_question_options(q, random.Random(6))
    assert len(shuffled["options"]) == n
    assert len(shuffled["explanations"]) == n
    assert 0 <= shuffled["correctIndex"] < n
