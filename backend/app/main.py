"""
VeriSum AI — FastAPI server.

Exposes the integrated Member 2A + Member 2B summarization pipeline (and Member 3
claim extraction) over HTTP so the React frontend can call them.

Run from the backend/ directory:
    uvicorn app.main:app --reload --port 8000
"""

from dataclasses import asdict
import logging
import os
from pathlib import Path
import sys
import tempfile
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.services.abstractive import get_recommended_transformer_models
from app.services.pipeline import summarize_file, summarize_text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("verisum.api")

# Make repository root importable so `src.claim_extraction` can be resolved
# regardless of whether uvicorn is launched from `backend/` or repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from src.claim_extraction import extract_claims
except ImportError:  # pragma: no cover - optional if src/ is absent
    extract_claims = None

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="VeriSum AI",
    description=(
        "Evidence-Grounded AI Text Summarization and Factual Verification Platform"
    ),
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
VALID_LENGTHS = {"short", "medium", "detailed"}


def _validate_summary_length(summary_length: str) -> None:
    if summary_length not in VALID_LENGTHS:
        raise HTTPException(
            status_code=422,
            detail=f"summary_length must be one of: {', '.join(sorted(VALID_LENGTHS))}",
        )


def _normalize_reference_summary(reference_summary: Optional[str]) -> Optional[str]:
    if reference_summary is None:
        return None
    stripped = reference_summary.strip()
    return stripped if stripped else None


# ---------------------------------------------------------------------------
# Health & model discovery
# ---------------------------------------------------------------------------


@app.get("/", tags=["health"])
def health():
    """Basic health-check — returns service name and status."""
    return {"status": "ok", "service": "VeriSum AI"}


@app.get("/summarize/models", tags=["summarize"])
def list_abstractive_models():
    """List local abstractive synthesis configuration and recommended free models."""
    return {
        "default_backend": "local_abstractive_fusion",
        "recommended_transformer_models": get_recommended_transformer_models(),
    }


# ---------------------------------------------------------------------------
# POST /summarize/text
# ---------------------------------------------------------------------------


@app.post("/summarize/text", tags=["summarize"])
def summarize_text_route(
    text: str = Form(..., description="Raw text to summarise"),
    summary_length: str = Form(
        "medium", description="Compression level: short | medium | detailed"
    ),
    reference_summary: Optional[str] = Form(
        None, description="Optional genuine reference summary for ROUGE evaluation"
    ),
):
    """
    Summarise plain text using extractive TextRank (with chunking for long docs)
    and local abstractive synthesis, returning quality metrics.
    """
    _validate_summary_length(summary_length)
    clean_ref = _normalize_reference_summary(reference_summary)
    try:
        return summarize_text(
            text,
            summary_length=summary_length,
            reference_summary=clean_ref,
        )
    except ValueError as exc:
        logger.warning("Validation error in /summarize/text: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error in /summarize/text")
        raise HTTPException(
            status_code=500, detail=f"Summarization failed: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# POST /summarize/file
# ---------------------------------------------------------------------------


@app.post("/summarize/file", tags=["summarize"])
async def summarize_file_route(
    file: UploadFile = File(..., description="PDF, DOCX, or TXT file to summarise"),
    summary_length: str = Form(
        "medium", description="Compression level: short | medium | detailed"
    ),
    reference_summary: Optional[str] = Form(
        None, description="Optional genuine reference summary for ROUGE evaluation"
    ),
):
    """
    Summarise an uploaded document file (.pdf, .docx, or .txt) with chunking,
    extractive + abstractive outputs, and quality metrics.
    """
    _validate_summary_length(summary_length)
    clean_ref = _normalize_reference_summary(reference_summary)

    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail="Unsupported file type. Upload a PDF, DOCX, or TXT file.",
        )

    contents = await file.read()
    if not contents:
        raise HTTPException(
            status_code=422,
            detail="Uploaded file is empty.",
        )

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        return summarize_file(
            tmp_path,
            summary_length=summary_length,
            reference_summary=clean_ref,
        )

    except (ValueError, FileNotFoundError) as exc:
        logger.warning("Document processing error for %s: %s", filename, exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.warning("Corrupt or unreadable document %s: %s", filename, exc)
        raise HTTPException(
            status_code=422,
            detail=f"Unable to process uploaded document: {exc}",
        ) from exc

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# POST /claims/extract
# ---------------------------------------------------------------------------


@app.post("/claims/extract", tags=["verification"])
def extract_claims_route(
    text: str = Form(..., description="Summary or document text to inspect for claims"),
    threshold: float = Form(
        0.55, description="Confidence threshold between 0.0 and 1.0"
    ),
):
    """Extract factual claims using Member 3's claim_extraction module."""
    if extract_claims is None:
        raise HTTPException(
            status_code=501,
            detail="Claim extraction module is not available.",
        )
    if not text.strip():
        raise HTTPException(status_code=422, detail="Please provide non-empty text.")
    if not 0.0 <= threshold <= 1.0:
        raise HTTPException(
            status_code=422,
            detail="threshold must be between 0.0 and 1.0.",
        )

    extraction = extract_claims(text, {"candidate_threshold": threshold})
    return {
        "claims": [asdict(claim) for claim in extraction.claims],
        "total_sentences": extraction.total_sentences,
        "errors": extraction.errors,
    }
