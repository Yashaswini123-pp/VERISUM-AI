
from app.services.pipeline import summarize_text


def test_summarize_text():
    text = (
        "Artificial intelligence is transforming healthcare. "
        "Machine learning helps doctors detect diseases. "
        "AI systems can analyze medical images quickly. "
        "Researchers are improving AI accuracy every year. "
        "These technologies support better medical decisions."
    )

    result = summarize_text(text, "medium")

    assert result["original_text"] == text
    assert result["cleaned_text"]
    assert len(result["sentences"]) == 5
    assert result["extractive_summary"]
    assert result["selected_sentence_ids"]
    assert result["sentence_scores"]


def test_empty_text():
    import pytest

    with pytest.raises(ValueError):
        summarize_text("")
