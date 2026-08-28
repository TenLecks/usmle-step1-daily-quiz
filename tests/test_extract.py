from unittest.mock import patch, MagicMock

from lib.extract import extract_subject_text


def _make_reader(pages_text):
    reader = MagicMock()
    reader.pages = [MagicMock(extract_text=MagicMock(return_value=t)) for t in pages_text]
    return reader


def test_extract_combines_multiple_files_with_filename_tags(tmp_path):
    (tmp_path / "Asthma.pdf").write_bytes(b"fake")
    (tmp_path / "COPD.pdf").write_bytes(b"fake")

    readers = {
        str(tmp_path / "Asthma.pdf"): _make_reader(["Asthma is reversible."]),
        str(tmp_path / "COPD.pdf"): _make_reader(["COPD is not reversible."]),
    }

    with patch("lib.extract.PdfReader", side_effect=lambda p: readers[p]):
        text = extract_subject_text(tmp_path)

    assert "[Asthma] Asthma is reversible." in text
    assert "[COPD] COPD is not reversible." in text


def test_extract_flattens_newlines_within_a_file(tmp_path):
    (tmp_path / "Notes.pdf").write_bytes(b"fake")
    reader = _make_reader(["Line one\nLine two\n\nLine three"])

    with patch("lib.extract.PdfReader", return_value=reader):
        text = extract_subject_text(tmp_path)

    assert "\n" not in text
    assert "Line one Line two Line three" in text


def test_extract_joins_multiple_pages_within_a_file(tmp_path):
    (tmp_path / "Notes.pdf").write_bytes(b"fake")
    reader = _make_reader(["Page one content.", "Page two content."])

    with patch("lib.extract.PdfReader", return_value=reader):
        text = extract_subject_text(tmp_path)

    assert "Page one content." in text
    assert "Page two content." in text


def test_extract_skips_files_with_no_extractable_text(tmp_path):
    (tmp_path / "Empty.pdf").write_bytes(b"fake")
    (tmp_path / "Real.pdf").write_bytes(b"fake")

    readers = {
        str(tmp_path / "Empty.pdf"): _make_reader([None, ""]),
        str(tmp_path / "Real.pdf"): _make_reader(["Real content here."]),
    }

    with patch("lib.extract.PdfReader", side_effect=lambda p: readers[p]):
        text = extract_subject_text(tmp_path)

    assert "[Empty]" not in text
    assert "[Real] Real content here." in text


def test_extract_returns_empty_string_for_folder_with_no_pdfs(tmp_path):
    text = extract_subject_text(tmp_path)
    assert text == ""
