import random

FIXED_ORDER = [
    "Cardiology", "Dermatology", "Endocrinology", "Gastroenterology", "Genetics",
    "Hematology", "Immunology", "Musculoskeletal", "Neurology", "Ophthalmology",
    "Pathology", "Psychiatry", "Pulmonary",
]
RANDOM_TAIL = ["Renal", "Reproductive"]


def next_subject(state, rng=None):
    """Pick today's subject and return (subject, updated_state).

    state keys: cycle_index (0..14), cycle_number (starts at 1), tail_order
    (shuffled copy of RANDOM_TAIL for the current cycle, or None to force a
    reshuffle — happens naturally at the start of every cycle).
    """
    rng = rng or random.Random()
    state = dict(state)
    cycle_index = state.get("cycle_index", 0)
    tail_order = state.get("tail_order")

    if cycle_index == 0 or tail_order is None:
        tail_order = RANDOM_TAIL[:]
        rng.shuffle(tail_order)

    rotation = FIXED_ORDER + tail_order
    subject = rotation[cycle_index]

    cycle_index += 1
    cycle_number = state.get("cycle_number", 1)
    if cycle_index >= len(rotation):
        cycle_index = 0
        cycle_number += 1
        tail_order = None

    state["cycle_index"] = cycle_index
    state["cycle_number"] = cycle_number
    state["tail_order"] = tail_order
    return subject, state
