from lib.schema import ANGLES


def _flatten(text):
    # Collapses \n, \r, \t and repeated whitespace to single spaces. Applied
    # to every value interpolated into the prompt below (LLM-generated
    # topic/angle tags in avoid_pairs especially) so a value that happens to
    # contain a literal newline can't reintroduce the exact bug the
    # single-line prompt exists to prevent.
    return " ".join(str(text).split())


def build_prompt(subject, extracted_text, avoid_pairs):
    # This entire prompt is deliberately built as ONE LINE with no embedded
    # newline characters. claude.cmd is a Windows batch-file wrapper, and
    # batch-file argument passing is line-oriented: a multi-line -p prompt
    # gets silently truncated at the first newline, so Claude only ever
    # receives a fragment of the task. Confirmed by direct testing — see
    # superpowers-plans/plans/2026-08-26-usmle-step1-daily-quiz.md.
    #
    # extracted_text is the subject's PDFs' text, extracted locally (see
    # lib/extract.py) and embedded directly here rather than having Claude
    # read the PDF files itself. This replaces the original file-reading
    # design: reading ~30 multi-page PDFs in one agentic session could
    # trigger context auto-compaction mid-task, after which the model lost
    # track of which files it had already read and restarted from the
    # beginning — observed directly in a real session log re-reading every
    # file 3-4x, burning ~$23 without ever finishing. Embedding pre-extracted
    # text removes the file-reading step (and that failure mode) entirely.
    subject = _flatten(subject)
    extracted_text = _flatten(extracted_text)
    avoid_block = ""
    if avoid_pairs:
        # avoid_pairs holds {topic, angle} dicts, not raw question stems —
        # this targets repeated CONCEPTS (same topic tested the same way),
        # not repeated wording, and stays cheap to send in full every time
        # since each pair is a few words instead of a full stem.
        joined = "; ".join(
            f"{_flatten(p['topic'])} ({_flatten(p['angle'])})" for p in avoid_pairs
        )
        avoid_block = (
            " Do NOT write another question whose topic and angle both match "
            f"any of these already-used combinations: {joined}. A different "
            "angle on an already-used topic is fine — e.g. if a prior "
            "question already tested a drug's mechanism, a new question on "
            "that same drug's treatment indication or adverse effects is "
            "still allowed, just not another mechanism question about it."
        )

    angles_list = ", ".join(ANGLES)

    return (
        "You are writing USMLE Step 1 practice questions for a solo medical "
        f'student. Here is the full text extracted from this student\'s Boards '
        f'& Beyond style lecture notes for the "{subject}" system, with each '
        f"source file's content tagged by filename in square brackets: "
        f"{extracted_text} "
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
        "option must state briefly why it is incorrect. For every question, "
        "also write an \"overview\" string: a short (2-4 sentence) high-yield "
        "summary of the disease, diagnosis, or mechanism the question is "
        "testing, covering the key facts a student would need to know for "
        "Step 1 — not a restatement of the question or answer choices, but "
        "the general topic overview a student should walk away remembering. "
        "For every question, also write a \"topic\" string naming the "
        "specific drug, disease, or concept the question is centered on "
        "(e.g. \"Amoxicillin\", \"Duchenne muscular dystrophy\"), and an "
        f"\"angle\" string that must be exactly one of: {angles_list} — "
        "whichever best describes which aspect of that topic the question "
        "is testing. Base every question "
        "strictly on the content of the notes provided above. Do not invent "
        "facts that aren't supported by the notes. Vary difficulty and "
        "sub-topics across the notes rather than clustering on one source "
        f"file.{avoid_block} This is a fully automated batch job with no "
        "human available to answer follow-up questions — complete the "
        "entire task (writing all 30 questions) in this single turn, then "
        "stop; do not summarize the notes, do not ask what to do next, and "
        "do not offer options. Respond with structured JSON matching the "
        "provided schema only — no extra commentary."
    )
