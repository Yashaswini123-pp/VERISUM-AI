"""
Long-document chunking and hierarchical extractive summarization for VeriSum AI.

Splits long documents cleanly on sentence boundaries with configurable sentence
overlap so cross-chunk context is preserved, then runs two-stage Map-Reduce
TextRank summarization via Member 2A's extractive module.
"""

import logging

from app.services.extractive import (
    generate_extractive_summary,
    rank_sentences,
)

logger = logging.getLogger("verisum.chunking")

LENGTH_RATIOS = {
    "short": 0.20,
    "medium": 0.35,
    "detailed": 0.50,
}


def count_words(text: str) -> int:
    """Count whitespace-delimited words in a string."""
    if not text or not text.strip():
        return 0
    return len(text.split())


def is_long_document(
    sentences: list,
    word_threshold: int = 220,
    sentence_threshold: int = 12,
) -> bool:
    """Return True when a document is large enough to benefit from chunking."""
    if not sentences:
        return False
    total_words = sum(
        count_words(item["text"] if isinstance(item, dict) else item)
        for item in sentences
    )
    return len(sentences) > sentence_threshold or total_words > word_threshold


def split_sentences_into_chunks(
    sentences: list,
    max_chunk_words: int = 180,
    overlap_sentences: int = 1,
) -> list:
    """Group indexed sentences into overlapping word-budgeted chunks.

    Sentence boundaries are always respected (sentences are never cut in half).
    """
    if not sentences:
        return []

    if max_chunk_words <= 0:
        raise ValueError("max_chunk_words must be positive.")
    if overlap_sentences < 0:
        raise ValueError("overlap_sentences cannot be negative.")

    normalized = [
        item if isinstance(item, dict) else {"id": idx + 1, "text": item}
        for idx, item in enumerate(sentences)
    ]

    chunks = []
    start = 0
    total = len(normalized)

    while start < total:
        current = []
        current_words = 0
        idx = start

        while idx < total:
            sent = normalized[idx]
            sent_words = count_words(sent["text"])
            if current and (current_words + sent_words > max_chunk_words):
                break
            current.append(sent)
            current_words += sent_words
            idx += 1

        overlap_count = 0
        if start > 0 and overlap_sentences > 0:
            # Overlap sentences are the leading sentences carried over from previous chunk.
            overlap_count = min(overlap_sentences, len(current) - 1) if len(current) > 1 else 0

        chunks.append(
            {
                "chunk_index": len(chunks),
                "sentences": current,
                "sentence_ids": [s["id"] for s in current],
                "overlap_sentence_ids": [s["id"] for s in current[:overlap_count]],
                "word_count": current_words,
            }
        )

        if idx >= total:
            break

        # Step back by overlap_sentences while guaranteeing forward progress.
        step_back = min(overlap_sentences, max(0, len(current) - 1))
        next_start = idx - step_back
        start = next_start if next_start > start else idx

    return chunks


def hierarchical_extractive_summarize(
    sentences: list,
    summary_length: str = "medium",
    max_chunk_words: int = 180,
    overlap_sentences: int = 1,
    word_threshold: int = 220,
    sentence_threshold: int = 12,
) -> dict:
    """Summarize documents, applying hierarchical chunked TextRank for long inputs.

    For short documents, delegates directly to Member 2A's
    `generate_extractive_summary()` so short-document behavior is unchanged.
    """
    if summary_length not in LENGTH_RATIOS:
        raise ValueError("summary_length must be short, medium, or detailed.")

    if not sentences:
        return {
            "summary": "",
            "selected_sentence_ids": [],
            "sentence_scores": [],
            "chunking_used": False,
            "chunk_count": 0,
            "overlap_sentences": 0,
            "chunks": [],
        }

    normalized = [
        item if isinstance(item, dict) else {"id": idx + 1, "text": item}
        for idx, item in enumerate(sentences)
    ]

    if not is_long_document(
        normalized,
        word_threshold=word_threshold,
        sentence_threshold=sentence_threshold,
    ):
        base = generate_extractive_summary(normalized, summary_length)
        total_words = sum(count_words(s["text"]) for s in normalized)
        return {
            **base,
            "chunking_used": False,
            "chunk_count": 1,
            "overlap_sentences": 0,
            "chunks": [
                {
                    "chunk_index": 0,
                    "sentence_ids": [s["id"] for s in normalized],
                    "overlap_sentence_ids": [],
                    "word_count": total_words,
                    "chunk_summary": base["summary"],
                    "selected_sentence_ids": base["selected_sentence_ids"],
                }
            ],
        }

    chunks = split_sentences_into_chunks(
        normalized,
        max_chunk_words=max_chunk_words,
        overlap_sentences=overlap_sentences,
    )

    if len(chunks) <= 1:
        base = generate_extractive_summary(normalized, summary_length)
        return {
            **base,
            "chunking_used": False,
            "chunk_count": 1,
            "overlap_sentences": 0,
            "chunks": [
                {
                    "chunk_index": 0,
                    "sentence_ids": chunks[0]["sentence_ids"],
                    "overlap_sentence_ids": [],
                    "word_count": chunks[0]["word_count"],
                    "chunk_summary": base["summary"],
                    "selected_sentence_ids": base["selected_sentence_ids"],
                }
            ],
        }

    logger.info(
        "Running hierarchical extractive summarization across %d chunks (overlap=%d).",
        len(chunks),
        overlap_sentences,
    )

    # Stage 1: Map — summarize each overlapping chunk via Member 2A's extractive engine.
    chunk_stage_length = "detailed" if summary_length == "detailed" else "medium"
    candidate_ids_seen = set()
    candidate_sentences = []
    chunk_summaries = []
    score_accumulator = {s["id"]: [] for s in normalized}

    for chunk in chunks:
        chunk_res = generate_extractive_summary(chunk["sentences"], chunk_stage_length)
        for item in chunk_res["sentence_scores"]:
            score_accumulator[item["id"]].append(item["score"])

        chunk_selected = set(chunk_res["selected_sentence_ids"])
        for sent in chunk["sentences"]:
            if sent["id"] in chunk_selected and sent["id"] not in candidate_ids_seen:
                candidate_ids_seen.add(sent["id"])
                candidate_sentences.append(sent)

        chunk_summaries.append(
            {
                "chunk_index": chunk["chunk_index"],
                "sentence_ids": chunk["sentence_ids"],
                "overlap_sentence_ids": chunk["overlap_sentence_ids"],
                "word_count": chunk["word_count"],
                "chunk_summary": chunk_res["summary"],
                "selected_sentence_ids": chunk_res["selected_sentence_ids"],
            }
        )

    # Preserve original document order for Stage-2 candidates.
    candidate_sentences.sort(key=lambda s: s["id"])

    # Stage 2: Reduce — rank pooled candidates and enforce document-level target ratio.
    stage2_scores = rank_sentences(candidate_sentences) if candidate_sentences else []
    target_count = max(1, round(len(normalized) * LENGTH_RATIOS[summary_length]))
    target_count = min(target_count, len(candidate_sentences))

    ranked_candidate_indices = sorted(
        range(len(candidate_sentences)),
        key=lambda i: stage2_scores[i],
        reverse=True,
    )
    chosen_indices = sorted(ranked_candidate_indices[:target_count])
    selected_sentences = [candidate_sentences[i] for i in chosen_indices]

    final_summary = " ".join(s["text"] for s in selected_sentences)
    selected_ids = [s["id"] for s in selected_sentences]

    # Global document scores + Stage-1 averaged fallback for full traceability.
    try:
        global_scores = rank_sentences(normalized)
    except ValueError:
        global_scores = [
            sum(score_accumulator[s["id"]]) / max(1, len(score_accumulator[s["id"]]))
            for s in normalized
        ]

    sentence_scores = [
        {"id": normalized[i]["id"], "score": float(global_scores[i])}
        for i in range(len(normalized))
    ]

    return {
        "summary": final_summary,
        "selected_sentence_ids": selected_ids,
        "sentence_scores": sentence_scores,
        "chunking_used": True,
        "chunk_count": len(chunks),
        "overlap_sentences": overlap_sentences,
        "chunks": chunk_summaries,
    }
