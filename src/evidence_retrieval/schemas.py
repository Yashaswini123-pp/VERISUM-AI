# Evidence retrieval implementation

"""Schemas for the Evidence Retrieval module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class Evidence:
    """A single piece of evidence.

    Attributes
    ----------
    text: str
    source: str
    relevance: float
    metadata: Dict[str, Any]
    """

    text: str
    source: str
    relevance: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalResult:
    """Result container for evidence retrieval.
    """

    evidence: List[Evidence] = field(default_factory=list)
    query: str = ""
    errors: List[str] = field(default_factory=list)

    def summary(self) -> Dict[str, Any]:
        return {
            "retrieved": len(self.evidence),
            "query": self.query,
            "errors": self.errors,
        }
