"""Schemas for the Fact Verification module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class VerificationResult:
    """Result of verifying a claim against evidence.

    Attributes
    ----------
    claim_text: str
    evidence_text: str
    label: str  # Supported, Contradicted, Not Enough Information
    confidence: float  # 0.0‑1.0
    metadata: Dict[str, Any]
    """

    claim_text: str
    evidence_text: str
    label: str
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
