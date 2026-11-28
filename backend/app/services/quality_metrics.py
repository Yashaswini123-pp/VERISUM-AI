"""
Summary quality metrics and conditional ROUGE evaluation for VeriSum AI.

Computes:
- Compression ratio & word-count reduction (extractive and abstractive)
- Sentence coverage (selected ratio, TF-IDF semantic coverage, concept coverage)
- Redundancy measurement (inter-sentence similarity & n-gram repetition)
- ROUGE-1, ROUGE-2, and ROUGE-L ONLY when a genuine reference summary is supplied
"""

import re

import nltk
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.services.chunking import count_words
from app.services.preprocessing import split_into_sentences

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokenize_words(text: str) -> list:
    """Lowercase alphanumeric word tokenization suitable for ROUGE and n-grams."""
    if not text:
        return []
    try:
        tokens = nltk.word_tokenize(text.lower())
        return [tok for tok in tokens if any(ch.isalnum() for ch in tok)]
    except LookupError:
        return _WORD_RE.findall(text.lower())


def _split_safe(text: str) -> list:
    if not text or not text.strip():
        return []
    try:
        return split_into_sentences(text)
    except LookupError:
        return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def _compute_tfidf_cosine(texts_a: list, texts_b: list | None = None):
    """Return cosine similarity matrix across one or two sentence lists."""
    combined = texts_a + (texts_b or [])
    if not combined:
        return None
    try:
        vec = TfidfVectorizer(stop_words="english")
        mat = vec.fit_transform(combined)
    except ValueError:
        try:
            vec = TfidfVectorizer(stop_words=None)
            mat = vec.fit_transform(combined)
        except ValueError:
            return None

    if texts_b is None:
        return cosine_similarity(mat)
    split = len(texts_a)
    return cosine_similarity(mat[:split], mat[split:])


def measure_redundancy(summary_text: str) -> dict:
    """Measure internal repetition within a summary (0.0 = minimal redundancy)."""
    if not summary_text or not summary_text.strip():
        return {
            "redundancy_score": 0.0,
            "pairwise_similarity": 0.0,
            "ngram_repetition_rate": 0.0,
        }

    tokens = _tokenize_words(summary_text)
    if len(tokens) >= 2:
        bigrams = [(tokens[i], tokens[i + 1]) for i in range(len(tokens) - 1)]
        ngram_rep = 1.0 - (len(set(bigrams)) / len(bigrams))
    else:
        ngram_rep = 0.0

    summary_sents = _split_safe(summary_text)
    if len(summary_sents) <= 1:
        pairwise_sim = 0.0
    else:
        sim_matrix = _compute_tfidf_cosine(summary_sents)
        if sim_matrix is None:
            pairwise_sim = 0.0
        else:
            n = len(summary_sents)
            upper_vals = [
                float(sim_matrix[i][j])
                for i in range(n)
                for j in range(i + 1, n)
            ]
            pairwise_sim = sum(upper_vals) / len(upper_vals) if upper_vals else 0.0

    combined = max(0.0, min(1.0, 0.6 * pairwise_sim + 0.4 * ngram_rep))
    return {
        "redundancy_score": round(combined, 4),
        "pairwise_similarity": round(pairwise_sim, 4),
        "ngram_repetition_rate": round(ngram_rep, 4),
    }


def measure_sentence_coverage(
    source_sentences: list,
    summary_text: str,
    selected_sentence_ids: list | None = None,
) -> dict:
    """Measure how well a summary covers the source document sentences & concepts."""
    source_texts = [
        item["text"] if isinstance(item, dict) else item
        for item in source_sentences
        if (item["text"] if isinstance(item, dict) else item).strip()
    ]
    total_source = len(source_texts)

    if total_source == 0 or not summary_text.strip():
        return {
            "selected_sentence_ratio": 0.0,
            "semantic_coverage": 0.0,
            "concept_coverage": 0.0,
        }

    selected_ratio = (
        round(len(set(selected_sentence_ids)) / total_source, 4)
        if selected_sentence_ids is not None
        else None
    )

    summary_sents = _split_safe(summary_text)
    sim_matrix = _compute_tfidf_cosine(source_texts, summary_sents)
    if sim_matrix is not None and sim_matrix.shape[1] > 0:
        max_per_source = [float(row.max()) for row in sim_matrix]
        semantic_cov = sum(max_per_source) / len(max_per_source)
    else:
        semantic_cov = 0.0

    source_concepts = {
        tok
        for tok in _tokenize_words(" ".join(source_texts))
        if tok not in ENGLISH_STOP_WORDS and len(tok) > 2
    }
    summary_concepts = {
        tok
        for tok in _tokenize_words(summary_text)
        if tok not in ENGLISH_STOP_WORDS and len(tok) > 2
    }
    concept_cov = (
        len(source_concepts & summary_concepts) / len(source_concepts)
        if source_concepts
        else 0.0
    )

    result = {
        "semantic_coverage": round(semantic_cov, 4),
        "concept_coverage": round(concept_cov, 4),
    }
    if selected_ratio is not None:
        result["selected_sentence_ratio"] = selected_ratio
    return result


def _ngram_f1(candidate_tokens: list, reference_tokens: list, n: int) -> dict:
    if len(candidate_tokens) < n or len(reference_tokens) < n:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    def counts(tokens):
        freq = {}
        for i in range(len(tokens) - n + 1):
            gram = tuple(tokens[i : i + n])
            freq[gram] = freq.get(gram, 0) + 1
        return freq

    cand_counts = counts(candidate_tokens)
    ref_counts = counts(reference_tokens)

    overlap = sum(
        min(cand_counts[g], ref_counts[g])
        for g in cand_counts
        if g in ref_counts
    )
    total_cand = sum(cand_counts.values())
    total_ref = sum(ref_counts.values())

    precision = overlap / total_cand if total_cand else 0.0
    recall = overlap / total_ref if total_ref else 0.0
    f1 = (
        (2 * precision * recall / (precision + recall))
        if (precision + recall) > 0
        else 0.0
    )
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def _lcs_length(seq_a: list, seq_b: list) -> int:
    if not seq_a or not seq_b:
        return 0
    m, n = len(seq_a), len(seq_b)
    prev = [0] * (n + 1)
    for i in range(1, m + 1):
        curr = [0] * (n + 1)
        tok_a = seq_a[i - 1]
        for j in range(1, n + 1):
            if tok_a == seq_b[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev = curr
    return prev[n]


def evaluate_rouge(candidate_summary: str, reference_summary: str) -> dict:
    """Compute ROUGE-1, ROUGE-2, and ROUGE-L against a genuine reference summary."""
    if not reference_summary or not reference_summary.strip():
        raise ValueError("reference_summary must be non-empty to evaluate ROUGE.")

    cand_tokens = _tokenize_words(candidate_summary or "")
    ref_tokens = _tokenize_words(reference_summary)

    rouge_1 = _ngram_f1(cand_tokens, ref_tokens, 1)
    rouge_2 = _ngram_f1(cand_tokens, ref_tokens, 2)

    lcs = _lcs_length(cand_tokens, ref_tokens)
    prec_l = lcs / len(cand_tokens) if cand_tokens else 0.0
    rec_l = lcs / len(ref_tokens) if ref_tokens else 0.0
    f1_l = (2 * prec_l * rec_l / (prec_l + rec_l)) if (prec_l + rec_l) > 0 else 0.0

    return {
        "rouge1": rouge_1,
        "rouge2": rouge_2,
        "rougeL": {
            "precision": round(prec_l, 4),
            "recall": round(rec_l, 4),
            "f1": round(f1_l, 4),
        },
    }


def _build_summary_profile(
    original_words: int,
    source_sentences: list,
    summary_text: str,
    selected_sentence_ids: list | None = None,
) -> dict:
    summary_words = count_words(summary_text)
    compression_ratio = (
        round(summary_words / original_words, 4) if original_words > 0 else 0.0
    )
    space_savings = round(max(0.0, (1.0 - compression_ratio) * 100.0), 2)

    return {
        "word_count": summary_words,
        "compression_ratio": compression_ratio,
        "reduction_percent": space_savings,
        "coverage": measure_sentence_coverage(
            source_sentences, summary_text, selected_sentence_ids
        ),
        "redundancy": measure_redundancy(summary_text),
    }


def compute_quality_metrics(
    original_text: str,
    sentences: list,
    extractive_summary: str,
    abstractive_summary: str,
    selected_sentence_ids: list,
    reference_summary: str | None = None,
) -> dict:
    """Compute comprehensive quality metrics for extractive and abstractive outputs.

    ROUGE scores are only computed when `reference_summary` is genuinely supplied.
    """
    original_words = count_words(original_text)
    extractive_profile = _build_summary_profile(
        original_words, sentences, extractive_summary, selected_sentence_ids
    )
    abstractive_profile = _build_summary_profile(
        original_words, sentences, abstractive_summary, None
    )

    rouge_payload = None
    if isinstance(reference_summary, str) and reference_summary.strip():
        rouge_payload = {
            "extractive": evaluate_rouge(extractive_summary, reference_summary),
            "abstractive": evaluate_rouge(abstractive_summary, reference_summary),
        }

    return {
        "original_word_count": original_words,
        "total_sentences": len(sentences),
        "selected_sentence_count": len(selected_sentence_ids),
        "compression_ratio": extractive_profile["compression_ratio"],
        "abstractive_compression_ratio": abstractive_profile["compression_ratio"],
        "sentence_coverage": extractive_profile["coverage"],
        "abstractive_coverage": abstractive_profile["coverage"],
        "redundancy": {
            "extractive": extractive_profile["redundancy"],
            "abstractive": abstractive_profile["redundancy"],
        },
        "extractive": extractive_profile,
        "abstractive": abstractive_profile,
        "rouge": rouge_payload,
    }
