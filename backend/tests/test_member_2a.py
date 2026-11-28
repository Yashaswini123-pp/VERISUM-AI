
import pytest

from app.services.document_processor import (
    extract_text_from_string,
    extract_txt,
)
from app.services.preprocessing import (
    clean_text,
    split_into_sentences,
    assign_sentence_ids,
    preprocess_document,
)
from app.services.extractive import (
    generate_extractive_summary,
)
from app.services.pipeline import summarize_text


# DOCUMENT PROCESSOR TESTS

def test_text_input():
    assert extract_text_from_string("Hello world") == "Hello world"


def test_empty_text_input():
    with pytest.raises(ValueError):
        extract_text_from_string("")


def test_txt_extraction(tmp_path):
    file = tmp_path / "sample.txt"
    file.write_text("VeriSum AI testing.", encoding="utf-8")
    assert extract_txt(file) == "VeriSum AI testing."


def test_missing_txt():
    with pytest.raises(FileNotFoundError):
        extract_txt("missing.txt")


# PREPROCESSING TESTS

def test_clean_text():
    assert clean_text("Hello   world!") == "Hello world!"


def test_sentence_splitting():
    result = split_into_sentences(
        "AI is useful. Machine learning is powerful."
    )
    assert len(result) == 2


def test_sentence_ids():
    result = assign_sentence_ids(["First.", "Second."])
    assert result[0]["id"] == 1
    assert result[1]["id"] == 2


def test_preprocessing_pipeline():
    result = preprocess_document(
        "AI is useful. Machine learning is powerful."
    )
    assert result["sentence_count"] == 2


# EXTRACTIVE SUMMARIZATION TESTS

def test_extractive_summary():
    sentences = [
        {"id": 1, "text": "Artificial intelligence helps healthcare."},
        {"id": 2, "text": "Machine learning detects diseases."},
        {"id": 3, "text": "AI analyzes medical images."},
        {"id": 4, "text": "Doctors use technology for diagnosis."},
    ]

    result = generate_extractive_summary(sentences, "medium")

    assert result["summary"]
    assert result["selected_sentence_ids"]
    assert result["sentence_scores"]


def test_empty_summary():
    result = generate_extractive_summary([])

    assert result["summary"] == ""
    assert result["selected_sentence_ids"] == []


# COMPLETE PIPELINE TESTS

def test_complete_pipeline():
    text = (
        "Artificial intelligence is transforming healthcare. "
        "Machine learning helps doctors detect diseases. "
        "AI systems analyze medical images. "
        "Researchers improve AI accuracy every year."
    )

    result = summarize_text(text, "medium")

    assert result["original_text"] == text
    assert result["cleaned_text"]
    assert result["sentences"]
    assert result["extractive_summary"]
    assert result["selected_sentence_ids"]
    assert result["sentence_scores"]


def test_pipeline_empty_input():
    with pytest.raises(ValueError):
        summarize_text("")

