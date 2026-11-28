"""
Local, zero-cost abstractive summarization service for VeriSum AI.

Provides a lightweight, offline-capable abstractive synthesis engine using
already-installed NLTK + scikit-learn primitives (clause compression,
discourse normalization, non-redundant proposition selection, and cross-sentence
fusion), plus an optional pluggable adapter for local HuggingFace transformer
models if `transformers` + `torch` are installed.
"""

import importlib.util
import logging
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.services.chunking import count_words

logger = logging.getLogger("verisum.abstractive")

RECOMMENDED_MODELS = [
    {
        "model_id": "Falconsai/text_summarization",
        "architecture": "T5-small fine-tuned",
        "approx_size": "~242 MB",
        "notes": "Fastest lightweight local neural abstractive summarizer for CPU.",
    },
    {
        "model_id": "sshleifer/distilbart-cnn-6-6",
        "architecture": "DistilBART",
        "approx_size": "~460 MB",
        "notes": "Strong balance between fluency and CPU memory footprint.",
    },
    {
        "model_id": "facebook/bart-large-cnn",
        "architecture": "BART-Large",
        "approx_size": "~1.6 GB",
        "notes": "High-quality abstractive summarization; best with GPU or ample RAM.",
    },
]

_LEAD_DISCOURSE_RE = re.compile(
    r"^(?:however|furthermore|moreover|additionally|meanwhile|consequently|"
    r"therefore|nevertheless|nonetheless|in addition|as a result|"
    r"for example|for instance|in contrast|specifically|notably|importantly|"
    r"on the other hand|it is worth noting that|researchers note that|"
    r"studies show that|in summary|overall),?\s+",
    re.IGNORECASE,
)

_PARENTHETICAL_RE = re.compile(r"\s*\([^)]{1,120}\)|\s*\[[^\]]{1,120}\]")

_PHRASE_SIMPLIFICATIONS = [
    (re.compile(r"\bin order to\b", re.IGNORECASE), "to"),
    (re.compile(r"\bdue to the fact that\b", re.IGNORECASE), "because"),
    (re.compile(r"\bat the present time\b", re.IGNORECASE), "currently"),
    (re.compile(r"\ba large number of\b", re.IGNORECASE), "many"),
    (re.compile(r"\b(?:is|are) able to\b", re.IGNORECASE), "can"),
    (re.compile(r"\bhas the ability to\b", re.IGNORECASE), "can"),
    (re.compile(r"\bhave the ability to\b", re.IGNORECASE), "can"),
    (re.compile(r"\bplays an important role in\b", re.IGNORECASE), "supports"),
    (re.compile(r"\bplay an important role in\b", re.IGNORECASE), "support"),
    (re.compile(r"\bfor the purpose of\b", re.IGNORECASE), "for"),
    (re.compile(r"\bin the process of\b", re.IGNORECASE), "currently"),
]

_TARGET_LENGTH_PROPORTIONS = {
    "short": 0.25,
    "medium": 0.40,
    "detailed": 0.55,
}


def get_recommended_transformer_models() -> list:
    """Return recommended local HuggingFace models and their installation status."""
    transformers_ready = (
        importlib.util.find_spec("transformers") is not None
        and importlib.util.find_spec("torch") is not None
    )
    return [
        {**model, "installed_runtime_ready": transformers_ready}
        for model in RECOMMENDED_MODELS
    ]


def _compute_tfidf_matrix(texts: list):
    """Compute TF-IDF matrix, falling back cleanly if stop-word removal empties vocab."""
    if not texts:
        return None, None
    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform(texts)
        return vectorizer, matrix
    except ValueError:
        try:
            vectorizer = TfidfVectorizer(stop_words=None)
            matrix = vectorizer.fit_transform(texts)
            return vectorizer, matrix
        except ValueError:
            return None, None


def _compress_clause(sentence: str, aggressive: bool = False) -> str:
    """Syntactically condense a sentence without altering core factual meaning."""
    cleaned = re.sub(r"\s+", " ", sentence).strip()
    if not cleaned:
        return ""

    # Strip parenthetical asides and trailing punctuation temporarily.
    text = _PARENTHETICAL_RE.sub("", cleaned).strip()
    text = _LEAD_DISCOURSE_RE.sub("", text).strip()

    for pattern, replacement in _PHRASE_SIMPLIFICATIONS:
        text = pattern.sub(replacement, text)

    # Remove non-restrictive relative clauses bounded by commas (", which ...,")
    # when aggressive compression is requested and enough content remains.
    if aggressive:
        candidate = re.sub(
            r",\s+(?:which|who)\s+[^,.;]{4,80},",
            ",",
            text,
            count=1,
            flags=re.IGNORECASE,
        )
        if count_words(candidate) >= 5:
            text = candidate

    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip(" ,;:")

    if count_words(text) < 4:
        text = cleaned

    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    if text and text[-1] not in ".!?":
        text += "."

    return text


def _select_salient_non_redundant_indices(
    texts: list,
    target_count: int,
    redundancy_threshold: float = 0.62,
) -> list:
    """Select salient sentences via TF-IDF centroid + lead relevance and MMR."""
    total = len(texts)
    if total == 0:
        return []
    if total == 1:
        return [0]

    _, matrix = _compute_tfidf_matrix(texts)
    if matrix is None:
        return list(range(min(target_count, total)))

    doc_centroid = matrix.mean(axis=0).A
    centroid_sim = cosine_similarity(matrix, doc_centroid).ravel()
    pair_sim = cosine_similarity(matrix)

    # Slight lead bias preserves framing context for abstractive synthesis.
    salience = [
        float(centroid_sim[i]) + (0.08 if i == 0 else 0.03 if i == 1 else 0.0)
        for i in range(total)
    ]

    chosen = []
    remaining = set(range(total))

    while len(chosen) < target_count and remaining:
        best_idx = None
        best_score = -1.0

        for idx in remaining:
            max_dup = max((pair_sim[idx][c] for c in chosen), default=0.0)
            mmr = salience[idx] - (0.45 * max_dup)
            if best_idx is None or mmr > best_score:
                best_idx = idx
                best_score = mmr

        if best_idx is None:
            break

        # Skip nearly identical restatements once at least one sentence is chosen.
        if chosen and max(pair_sim[best_idx][c] for c in chosen) > redundancy_threshold:
            remaining.remove(best_idx)
            continue

        chosen.append(best_idx)
        remaining.remove(best_idx)

    if not chosen:
        chosen = [0]

    return sorted(chosen)


def _extract_subject_prefix(sentence: str) -> str:
    """Identify leading 1-3 word subject phrase before common copula/action verbs."""
    match = re.match(
        r"^([A-Z][A-Za-z0-9\-]*(?:\s+[A-Za-z0-9\-]+){0,2})\s+"
        r"(?:is|are|was|were|can|could|may|will|helps?|uses?|analyzes?|"
        r"improves?|supports?|provides?|detects?|enables?|reduces?|transforms?)\b",
        sentence.strip(),
    )
    return match.group(1).lower() if match else ""


def _fuse_compressed_clauses(clauses: list, summary_length: str) -> str:
    """Fuse compressed propositions into cohesive abstractive prose."""
    if not clauses:
        return ""
    if len(clauses) == 1:
        return clauses[0]

    fused = []
    i = 0
    while i < len(clauses):
        current = clauses[i].rstrip(".!?")
        if i + 1 < len(clauses):
            nxt = clauses[i + 1].rstrip(".!?")
            subj_a = _extract_subject_prefix(current)
            subj_b = _extract_subject_prefix(nxt)

            # Merge adjacent propositions sharing the same subject or paired short points.
            if subj_a and subj_a == subj_b:
                remainder = nxt[len(subj_b):].strip()
                if remainder:
                    merged = f"{current} and {remainder}."
                    fused.append(merged)
                    i += 2
                    continue
            if summary_length == "short" and count_words(current) + count_words(nxt) <= 32:
                lower_nxt = nxt[0].lower() + nxt[1:] if nxt else nxt
                fused.append(f"{current}, while {lower_nxt}.")
                i += 2
                continue

        fused.append(f"{current}.")
        i += 1

    # Add smooth synthesis transition on longer multi-sentence outputs.
    if len(fused) >= 3 and summary_length in ("medium", "detailed"):
        last = fused[-1]
        if not last.lower().startswith(("overall,", "additionally,", "furthermore,")):
            last_body = last[0].lower() + last[1:] if len(last) > 1 else last
            fused[-1] = f"Overall, {last_body}"

    return " ".join(fused)


def _try_transformers_abstractive(
    text: str,
    summary_length: str,
    model_name: str,
) -> dict | None:
    """Optional HuggingFace Transformers seq2seq summarizer if runtime is available."""
    if (
        importlib.util.find_spec("transformers") is None
        or importlib.util.find_spec("torch") is None
    ):
        return None

    try:
        from transformers import pipeline as hf_pipeline

        length_bounds = {
            "short": (25, 65),
            "medium": (50, 120),
            "detailed": (90, 200),
        }
        min_len, max_len = length_bounds[summary_length]
        summarizer = hf_pipeline("summarization", model=model_name)
        output = summarizer(
            text[:3500],
            min_length=min_len,
            max_length=max_len,
            do_sample=False,
        )
        summary_text = output[0]["summary_text"].strip()
        return {
            "summary": summary_text,
            "method": "transformers_seq2seq",
            "model": model_name,
        }
    except Exception as exc:  # pragma: no cover - optional heavy runtime path
        logger.warning("Transformers abstractive fallback triggered: %s", exc)
        return None


def generate_abstractive_summary(
    sentences: list,
    summary_length: str = "medium",
    chunks: list | None = None,
    backend: str = "auto",
    model_name: str = "Falconsai/text_summarization",
) -> dict:
    """Generate a locally runnable abstractive summary from indexed sentences or chunks.

    Parameters
    ----------
    sentences : list
        Sentence dicts (`{"id": int, "text": str}`) or strings.
    summary_length : str
        One of `"short"`, `"medium"`, `"detailed"`.
    chunks : list | None
        Optional chunk metadata from `chunking.py` to perform hierarchical
        chunk-level synthesis before document-level fusion.
    backend : str
        `"auto"` (uses transformers if installed, else lightweight local fusion),
        `"lightweight"` (always uses zero-dependency local fusion), or
        `"transformers"` (attempts transformers first, falling back with log).
    model_name : str
        HuggingFace model ID when transformer backend is enabled.
    """
    if summary_length not in _TARGET_LENGTH_PROPORTIONS:
        raise ValueError("summary_length must be short, medium, or detailed.")

    if not sentences:
        return {
            "summary": "",
            "method": "local_abstractive_fusion",
            "model": "nltk-tfidf-abstractive-fusion",
            "hierarchical_used": False,
            "source_chunks_synthesized": 0,
        }

    texts = [
        item["text"].strip() if isinstance(item, dict) else str(item).strip()
        for item in sentences
        if (item["text"].strip() if isinstance(item, dict) else str(item).strip())
    ]

    if not texts:
        return {
            "summary": "",
            "method": "local_abstractive_fusion",
            "model": "nltk-tfidf-abstractive-fusion",
            "hierarchical_used": False,
            "source_chunks_synthesized": 0,
        }

    if backend in ("auto", "transformers"):
        transformer_res = _try_transformers_abstractive(
            " ".join(texts), summary_length, model_name
        )
        if transformer_res is not None:
            return {
                **transformer_res,
                "hierarchical_used": bool(chunks and len(chunks) > 1),
                "source_chunks_synthesized": len(chunks) if chunks else 1,
            }

    aggressive = summary_length == "short"
    hierarchical_used = bool(chunks and len(chunks) > 1)

    if hierarchical_used:
        # Synthesize focal propositions from each chunk first, then deduplicate globally.
        sentence_by_id = {
            (item["id"] if isinstance(item, dict) else idx + 1): (
                item["text"] if isinstance(item, dict) else item
            )
            for idx, item in enumerate(sentences)
        }
        chunk_candidates = []
        seen_ids = set()

        for chunk in chunks:
            chunk_texts = [
                sentence_by_id[sid]
                for sid in chunk.get("sentence_ids", [])
                if sid in sentence_by_id
            ]
            if not chunk_texts:
                continue
            per_chunk_take = 1 if summary_length == "short" else 2
            local_indices = _select_salient_non_redundant_indices(
                chunk_texts,
                target_count=min(per_chunk_take, len(chunk_texts)),
            )
            for li in local_indices:
                sid = chunk["sentence_ids"][li]
                if sid not in seen_ids:
                    seen_ids.add(sid)
                    chunk_candidates.append(sentence_by_id[sid])

        total_target = max(
            1, round(len(texts) * _TARGET_LENGTH_PROPORTIONS[summary_length])
        )
        if len(chunk_candidates) > total_target:
            final_indices = _select_salient_non_redundant_indices(
                chunk_candidates, target_count=total_target
            )
            chosen_texts = [chunk_candidates[i] for i in final_indices]
        else:
            chosen_texts = chunk_candidates
    else:
        target_count = max(
            1, round(len(texts) * _TARGET_LENGTH_PROPORTIONS[summary_length])
        )
        chosen_indices = _select_salient_non_redundant_indices(
            texts, target_count=target_count
        )
        chosen_texts = [texts[i] for i in chosen_indices]

    compressed = [_compress_clause(t, aggressive=aggressive) for t in chosen_texts]
    compressed = [c for c in compressed if c]
    fused_summary = _fuse_compressed_clauses(compressed, summary_length)

    return {
        "summary": fused_summary,
        "method": "local_abstractive_fusion",
        "model": "nltk-tfidf-abstractive-fusion",
        "hierarchical_used": hierarchical_used,
        "source_chunks_synthesized": len(chunks) if chunks else 1,
    }
