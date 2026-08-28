from pathlib import Path

from pypdf import PdfReader


def extract_subject_text(folder_path):
    """Extract and concatenate text from every PDF under folder_path
    (recursively, sorted for determinism), tagging each file's text with its
    filename. Fully local, no network/API calls, no cost.

    Whitespace (including newlines) is collapsed within each file's text so
    the result is always safe to embed directly in a single-line -p prompt
    (see lib/prompt.py's newline-truncation note) without needing a separate
    flattening step at the call site.
    """
    folder_path = Path(folder_path)
    sections = []
    for pdf_path in sorted(folder_path.rglob("*.pdf")):
        reader = PdfReader(str(pdf_path))
        raw_text = " ".join(page.extract_text() or "" for page in reader.pages)
        flat_text = " ".join(raw_text.split())
        if flat_text:
            sections.append(f"[{pdf_path.stem}] {flat_text}")
    return " ".join(sections)
