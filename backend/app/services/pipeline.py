
from app.services.document_processor import extract_text_from_file, extract_text_from_string
from app.services.preprocessing import preprocess_document
from app.services.extractive import generate_extractive_summary


def summarize_file(file_path, summary_length="medium"):
    original_text = extract_text_from_file(file_path)
    return summarize_text(original_text, summary_length)


def summarize_text(text, summary_length="medium"):
    original_text = extract_text_from_string(text)

    processed = preprocess_document(original_text)

    result = generate_extractive_summary(
        processed["sentences"],
        summary_length
    )

    return {
        "original_text": original_text,
        "cleaned_text": processed["cleaned_text"],
        "sentences": processed["sentences"],
        "extractive_summary": result["summary"],
        "selected_sentence_ids": result["selected_sentence_ids"],
        "sentence_scores": result["sentence_scores"]
    }
