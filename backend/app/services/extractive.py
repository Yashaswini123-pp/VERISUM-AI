
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx


def calculate_sentence_similarity(sentences):
    """Calculate similarity between sentences using TF-IDF."""

    texts = [
        item["text"] if isinstance(item, dict) else item
        for item in sentences
    ]

    if len(texts) <= 1:
        return None

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(texts)

    return cosine_similarity(tfidf_matrix)


def rank_sentences(sentences):
    """Rank sentences using the TextRank algorithm."""

    if not sentences:
        return []

    if len(sentences) == 1:
        return [1.0]

    similarity_matrix = calculate_sentence_similarity(sentences)

    if similarity_matrix is None:
        return [1.0]

    graph = nx.from_numpy_array(similarity_matrix)

    scores = nx.pagerank(graph, weight="weight")

    return [scores[i] for i in range(len(sentences))]


def generate_extractive_summary(sentences, summary_length="medium"):
    """Generate an extractive summary while preserving original order."""

    if not sentences:
        return {
            "summary": "",
            "selected_sentence_ids": [],
            "sentence_scores": []
        }

    if summary_length not in ("short", "medium", "detailed"):
        raise ValueError(
            "summary_length must be short, medium, or detailed."
        )

    sentence_texts = [
        item["text"] if isinstance(item, dict) else item
        for item in sentences
    ]

    sentence_ids = [
        item["id"] if isinstance(item, dict) else index + 1
        for index, item in enumerate(sentences)
    ]

    scores = rank_sentences(sentences)

    total = len(sentences)

    ratios = {
        "short": 0.20,
        "medium": 0.35,
        "detailed": 0.50
    }

    count = max(1, round(total * ratios[summary_length]))

    ranked_indices = sorted(
        range(total),
        key=lambda i: scores[i],
        reverse=True
    )

    selected_indices = sorted(ranked_indices[:count])

    summary = " ".join(
        sentence_texts[i] for i in selected_indices
    )

    selected_ids = [
        sentence_ids[i] for i in selected_indices
    ]

    sentence_scores = [
        {
            "id": sentence_ids[i],
            "score": float(scores[i])
        }
        for i in range(total)
    ]

    return {
        "summary": summary,
        "selected_sentence_ids": selected_ids,
        "sentence_scores": sentence_scores
    }
