
import pytest

from app.services.document_processor import (
    extract_text_from_string,
    extract_txt,
)


def test_extract_text_from_string():
    text = "Artificial intelligence is transforming healthcare."
    assert extract_text_from_string(text) == text


def test_extract_text_from_string_empty():
    with pytest.raises(ValueError):
        extract_text_from_string("")


def test_extract_txt(tmp_path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text("VeriSum AI testing.", encoding="utf-8")

    result = extract_txt(file_path)

    assert result == "VeriSum AI testing."


def test_extract_txt_missing_file(tmp_path):
    file_path = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError):
        extract_txt(file_path)
