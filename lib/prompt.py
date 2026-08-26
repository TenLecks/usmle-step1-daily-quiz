def build_prompt(subject, folder_path, avoid_stems):
    avoid_block = ""
    if avoid_stems:
        bullet_list = "\n".join(f"- {s}" for s in avoid_stems)
        avoid_block = (
            "\n\nDo NOT repeat these previously-used question topics/stems "
            f"(paraphrase to something new instead):\n{bullet_list}\n"
        )

    return f"""You are writing USMLE Step 1 practice questions for a solo medical student.

Read every PDF lecture-note file inside this folder (Boards & Beyond style notes for the "{subject}" system):
{folder_path}

Generate exactly 30 original multiple-choice questions covering high-yield content from those notes:
- Exactly 10 questions in "vignette5" format: a realistic clinical-vignette stem (patient
  presentation, history, labs/imaging as relevant), 5 answer options (A-E), single best answer.
- Exactly 20 questions in "simple4" format: a shorter, more direct question testing a single fact
  or concept from the notes, 4 answer options (A-D), single best answer.

For every question, write one explanation string per option, in the same order as the options:
the explanation for the correct option must state why it is correct; the explanation for every
other option must state briefly why it is incorrect.

Base every question strictly on the content of the PDFs in the folder above. Do not invent facts
that aren't supported by the notes. Vary difficulty and sub-topics across the notes rather than
clustering on one file.{avoid_block}

Respond with structured JSON matching the provided schema only — no extra commentary."""
