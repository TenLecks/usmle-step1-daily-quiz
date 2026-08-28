def shuffle_question_options(question, rng):
    """Return a NEW question dict with options/explanations randomly
    reordered and correctIndex updated to match the new position.

    LLMs writing multiple-choice questions have a strong tendency to place
    the correct answer at the same position across many questions (observed
    directly: one real generated set had the correct answer at index 0 in
    all 30 of 30 questions). Reordering locally, after generation, removes
    that positional bias regardless of the model's own habits.
    """
    n = len(question["options"])
    order = list(range(n))
    rng.shuffle(order)
    new_question = dict(question)
    new_question["options"] = [question["options"][i] for i in order]
    new_question["explanations"] = [question["explanations"][i] for i in order]
    new_question["correctIndex"] = order.index(question["correctIndex"])
    return new_question
