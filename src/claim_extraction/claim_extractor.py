# Claim extraction implementation.
# Provides a single public function `extract_claims` that extracts factual claims
# from an English text. The implementation is lightweight, offline‑only, and
# uses a simple rule‑based heuristic.

from __future__ import annotations

import os
from typing import List, Optional, Dict, Any

# Optional spaCy import – if unavailable we fall back to a naive splitter.
try:
    import spacy
except ImportError:
    spacy = None

from .schemas import Claim, ExtractionResult

# ---------------------------------------------------------------------------
# spaCy pipeline (lazy) – only loaded when spaCy is available.
# ---------------------------------------------------------------------------
_nlp = None  # type: ignore

def _get_nlp():
    global _nlp
    if _nlp is None:
        if spacy is None:
            _nlp = None
        else:
            try:
                _nlp = spacy.load("en_core_web_sm")
            except Exception:
                _nlp = None
    return _nlp

# ---------------------------------------------------------------------------
# Sentence splitter.
# ---------------------------------------------------------------------------
def _split_sentences(text: str) -> List[str]:
    nlp = _get_nlp()
    if nlp is None:
        # Very naive fallback – split on sentence‑ending punctuation while preserving it.
        import re
        return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s]
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]

# ---------------------------------------------------------------------------
# Simple rule‑based claim scorer.
# ---------------------------------------------------------------------------
def _score_sentence(sentence: str) -> float:
    """Return a confidence (0.0‑1.0) that *sentence* contains a factual claim.

    Heuristic:
    * If spaCy is available, we check for the presence of a verb (POS tag starts
      with ``V``). If a verb is found we assign confidence 0.8, otherwise 0.0.
    * If spaCy is not available, we fall back to a length‑based rule – sentences
      longer than three tokens get confidence 0.8.
    """
    nlp = _get_nlp()
    if nlp is None:
        return 0.8 if len(sentence.split()) > 3 else 0.0
    doc = nlp(sentence)
    has_verb = any(tok.pos_.startswith('V') for tok in doc)
    return 0.8 if has_verb else 0.0

def _is_claim(confidence: float, threshold: float) -> bool:
    return confidence >= threshold

# ---------------------------------------------------------------------------
# Public API.
# ---------------------------------------------------------------------------
def extract_claims(text: str, config: Optional[Dict[str, Any]] = None) -> ExtractionResult:
    cfg = {"candidate_threshold": 0.55, "use_llm_fallback": False}
    if config:
        cfg.update(config)
    sentences = _split_sentences(text)
    result = ExtractionResult(total_sentences=len(sentences))
    for idx, sent in enumerate(sentences):
        confidence = _score_sentence(sent)
        if _is_claim(confidence, cfg["candidate_threshold"]):
            claim = Claim(
                text=sent,
                sentence_index=idx,
                char_start=text.find(sent),
                char_end=text.find(sent) + len(sent),
                confidence=confidence,
                context=sent,
                metadata={"method": "rule_based"},
            )
            result.claims.append(claim)
        elif cfg["use_llm_fallback"]:
            claim = Claim(
                text=sent,
                sentence_index=idx,
                char_start=text.find(sent),
                char_end=text.find(sent) + len(sent),
                confidence=0.1,
                context=sent,
                metadata={"method": "llm_fallback"},
            )
            result.claims.append(claim)
    return result

# ---------------------------------------------------------------------------
# Optional CLI helper.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse, json
    parser = argparse.ArgumentParser(description="Extract factual claims from text.")
    parser.add_argument("file", help="Path to a text file to process")
    parser.add_argument("--threshold", type=float, default=0.55)
    args = parser.parse_args()
    with open(args.file, "r", encoding="utf-8") as f:
        txt = f.read()
    res = extract_claims(txt, {"candidate_threshold": args.threshold})
    print(json.dumps({"claims": [c.__dict__ for c in res.claims]}, indent=2))
