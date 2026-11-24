
import re
import nltk


def clean_text(text):
    """Clean unnecessary spaces and formatting from text."""

    if not isinstance(text, str):
        raise TypeError("Input must be a string.")

    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text


def split_into_sentences(text):
    """Split cleaned text into individual sentences."""

    if not text or not text.strip():
        return []

    sentences = nltk.sent_tokenize(text)

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def assign_sentence_ids(sentences):
    """Assign a unique ID to every sentence."""

    return [
        {
            "id": index,
            "text": sentence
        }
        for index, sentence in enumerate(sentences, start=1)
    ]


def preprocess_document(text):
    """Complete document preprocessing pipeline."""

    cleaned_text = clean_text(text)

    sentences = split_into_sentences(cleaned_text)

    sentence_data = assign_sentence_ids(sentences)

    return {
        "cleaned_text": cleaned_text,
        "sentences": sentence_data,
        "sentence_count": len(sentence_data)
    }
