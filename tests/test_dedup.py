from lib.dedup import find_repeated_pairs, normalize_pair


def test_normalize_pair_is_case_and_whitespace_insensitive():
    a = normalize_pair({"topic": "  Amoxicillin ", "angle": "Mechanism"})
    b = normalize_pair({"topic": "amoxicillin", "angle": "mechanism"})
    assert a == b


def test_no_repeats_returns_empty_list():
    prior = [{"topic": "Amoxicillin", "angle": "mechanism"}]
    new = [{"topic": "Amoxicillin", "angle": "treatment"}]
    assert find_repeated_pairs(new, prior) == []


def test_finds_repeat_against_prior_history():
    prior = [{"topic": "Amoxicillin", "angle": "mechanism"}]
    new = [{"topic": "Amoxicillin", "angle": "mechanism"}]
    assert find_repeated_pairs(new, prior) == new


def test_repeat_match_is_case_and_whitespace_insensitive():
    prior = [{"topic": "Amoxicillin", "angle": "mechanism"}]
    new = [{"topic": " amoxicillin ", "angle": "MECHANISM"}]
    assert find_repeated_pairs(new, prior) == new


def test_finds_repeat_within_the_new_batch_itself():
    new = [
        {"topic": "Amoxicillin", "angle": "mechanism"},
        {"topic": "Amoxicillin", "angle": "treatment"},
        {"topic": "Amoxicillin", "angle": "mechanism"},
    ]
    repeats = find_repeated_pairs(new, [])
    assert repeats == [{"topic": "Amoxicillin", "angle": "mechanism"}]


def test_different_topic_same_angle_is_not_a_repeat():
    prior = [{"topic": "Amoxicillin", "angle": "mechanism"}]
    new = [{"topic": "Penicillin", "angle": "mechanism"}]
    assert find_repeated_pairs(new, prior) == []
