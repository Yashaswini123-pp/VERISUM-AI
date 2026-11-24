import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.claim_extraction.claim_extractor import extract_claims
from src.claim_extraction.schemas import Claim, ExtractionResult

# Simple fixture text containing two factual sentences and one non-factual.
TEST_TEXT = (
    "The Eiffel Tower is 324 meters tall. "
    "I love pizza. "
    "Water boils at 100°C at sea level."
)

def test_extract_claims_basic():
    # Use a low threshold so the dummy classifier (based on sentiment model) still
    # returns a non-zero confidence for factual-sounding sentences.
    result = extract_claims(TEST_TEXT, {"candidate_threshold": 0.0})
    assert isinstance(result, ExtractionResult)
    claim_texts = [c.text for c in result.claims]
    assert "The Eiffel Tower is 324 meters tall." in claim_texts
    assert "Water boils at 100°C at sea level." in claim_texts
    for claim in result.claims:
        assert isinstance(claim, Claim)
        assert 0.0 <= claim.confidence <= 1.0
        assert claim.text
        assert claim.sentence_index >= 0
        assert claim.char_start >= 0
        assert claim.char_end >= claim.char_start

def test_extract_claims_empty_input():
    result = extract_claims("", {"candidate_threshold": 0.5})
    assert result.total_sentences == 0
    assert result.claims == []
