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
