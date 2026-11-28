"""
Complete summarization orchestration pipeline for VeriSum AI.

Preserves all Member 2A interfaces and return keys while integrating Member 2B's:
- Long-document chunking & hierarchical summarization
- Local abstractive synthesis (with optional transformer adapter)
- Quality metrics (compression ratio, sentence coverage, redundancy, conditional ROUGE)
"""

import logging

from app.services.abstractive import generate_abstractive_summary
from app.services.chunking import hierarchical_extractive_summarize
from app.services.document_processor import extract_text_from_file, extract_text_from_string
from app.services.preprocessing import preprocess_document
from app.services.quality_metrics import compute_quality_metrics

logger = logging.getLogger("verisum.pipeline")


def summarize_file(
    file_path,
    summary_length="medium",
    reference_summary=None,
    abstractive_backend="auto",
):
    """Extract text from a supported file and run the full summarization pipeline."""
    logger.info("Summarizing file input (length=%s).", summary_length)
    original_text = extract_text_from_file(file_path)
    return summarize_text(
        original_text,
        summary_length=summary_length,
        reference_summary=reference_summary,
        abstractive_backend=abstractive_backend,
    )


def summarize_text(
    text,
    summary_length="medium",
    reference_summary=None,
    abstractive_backend="auto",
):
    """Run preprocessing, extractive (or hierarchical) + abstractive summarization, and metrics."""
    if reference_summary is not None and not isinstance(reference_summary, str):
        raise ValueError("reference_summary must be a string when provided.")

    original_text = extract_text_from_string(text)
    processed = preprocess_document(original_text)
    sentences = processed["sentences"]

    logger.info(
        "Running summarization pipeline on %d sentences (length=%s).",
        len(sentences),
        summary_length,
    )

    extractive_result = hierarchical_extractive_summarize(
        sentences,
        summary_length=summary_length,
    )

    chunks_arg = (
        extractive_result["chunks"] if extractive_result["chunking_used"] else None
    )
    abstractive_result = generate_abstractive_summary(
        sentences,
        summary_length=summary_length,
        chunks=chunks_arg,
        backend=abstractive_backend,
    )

    quality_metrics = compute_quality_metrics(
        original_text=original_text,
        sentences=sentences,
        extractive_summary=extractive_result["summary"],
        abstractive_summary=abstractive_result["summary"],
        selected_sentence_ids=extractive_result["selected_sentence_ids"],
        reference_summary=reference_summary,
    )

    return {
        "original_text": original_text,
        "cleaned_text": processed["cleaned_text"],
        "sentences": sentences,
        "extractive_summary": extractive_result["summary"],
        "selected_sentence_ids": extractive_result["selected_sentence_ids"],
        "sentence_scores": extractive_result["sentence_scores"],
        "summary_length": summary_length,
        "abstractive_summary": abstractive_result["summary"],
        "abstractive_metadata": {
            "method": abstractive_result["method"],
            "model": abstractive_result["model"],
            "hierarchical_used": abstractive_result["hierarchical_used"],
            "source_chunks_synthesized": abstractive_result["source_chunks_synthesized"],
        },
        "chunking": {
            "chunking_used": extractive_result["chunking_used"],
            "chunk_count": extractive_result["chunk_count"],
            "overlap_sentences": extractive_result["overlap_sentences"],
            "chunks": extractive_result["chunks"],
        },
        "quality_metrics": quality_metrics,
    }
