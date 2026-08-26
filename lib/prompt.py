def _flatten(text):
    # Collapses \n, \r, \t and repeated whitespace to single spaces. Applied
    # to every value interpolated into the prompt below (LLM-generated stems
    # in avoid_stems especially) so a value that happens to contain a literal
    # newline can't reintroduce the exact bug the single-line prompt exists
    # to prevent.
    return " ".join(str(text).split())


def build_prompt(subject, folder_path, avoid_stems):
    # This entire prompt is deliberately built as ONE LINE with no embedded
    # newline characters. claude.cmd is a Windows batch-file wrapper, and
    # batch-file argument passing is line-oriented: a multi-line -p prompt
    # gets silently truncated at the first newline, so Claude only ever
    # receives a fragment of the task. Confirmed by direct testing — see
    # superpowers-plans/plans/2026-08-26-usmle-step1-daily-quiz.md.
    subject = _flatten(subject)
    folder_path = _flatten(folder_path)
    avoid_block = ""
    if avoid_stems:
        joined = "; ".join(_flatten(s) for s in avoid_stems)
        avoid_block = (
            f" Do NOT repeat these previously-used question topics/stems "
            f"(paraphrase to something new instead): {joined}."
        )

    return (
        "You are writing USMLE Step 1 practice questions for a solo medical "
        f'student. Read every PDF lecture-note file inside this folder (Boards '
        f'& Beyond style notes for the "{subject}" system): {folder_path}. '
        "Generate exactly 30 original multiple-choice questions covering "
        "high-yield content from those notes: exactly 10 questions in "
        '"vignette5" format (a realistic clinical-vignette stem with patient '
        "presentation, history, labs/imaging as relevant, 5 answer options "
        "A-E, single best answer), and exactly 20 questions in \"simple4\" "
        "format (a shorter, more direct question testing a single fact or "
        "concept from the notes, 4 answer options A-D, single best answer). "
        "For every question, write one explanation string per option, in the "
        "same order as the options: the explanation for the correct option "
        "must state why it is correct; the explanation for every other "
        "option must state briefly why it is incorrect. Base every question "
        "strictly on the content of the PDFs in the folder above. Do not "
        "invent facts that aren't supported by the notes. Vary difficulty "
        "and sub-topics across the notes rather than clustering on one "
        f"file.{avoid_block} This is a fully automated batch job with no "
        "human available to answer follow-up questions — complete the "
        "entire task (reading the files and writing all 30 questions) in "
        "this single turn, then stop; do not summarize the notes, do not "
        "ask what to do next, and do not offer options. Respond with "
        "structured JSON matching the provided schema only — no extra "
        "commentary."
    )
