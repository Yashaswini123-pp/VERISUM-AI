"""Schemas for the Claim Extraction module.

Defines the data structures used to represent extracted claims and the overall
result of an extraction run. The classes are simple `dataclass` containers so
they can be serialised to JSON, used in type hints and easily extended.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class Claim:
    """A single factual claim extracted from a source document.

    Attributes
    ----------
    id : str
        Unique identifier (UUID4) for the claim.
    text : str
        The exact claim text as extracted from the source.
    sentence_index : int
        Zero‑based index of the sentence the claim originated from.
    char_start : int
        Absolute character offset of the claim start in the original text.
    char_end : int
        Absolute character offset of the claim end in the original text.
    confidence : float
        Model confidence score in the range [0.0, 1.0].
    context : str
        The surrounding sentence or paragraph providing context.
    metadata : Dict[str, Any]
        Optional free‑form metadata (e.g., source line number, language).
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    sentence_index: int = -1
    char_start: int = -1
    char_end: int = -1
    confidence: float = 0.0
    context: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractionResult:
    """Container for the result of a claim‑extraction run.

    Attributes
    ----------
    claims : List[Claim]
        List of extracted claims.
    total_sentences : int
        Number of sentences that were processed.
    errors : List[str]
        Non‑fatal errors or warnings that occurred during extraction.
    """

    claims: List[Claim] = field(default_factory=list)
    total_sentences: int = 0
    errors: List[str] = field(default_factory=list)

    def summary(self) -> Dict[str, Any]:
        """Return a concise summary useful for logging or UI display."""
        return {
            "claim_count": len(self.claims),
            "total_sentences": self.total_sentences,
            "errors": self.errors,
        }
