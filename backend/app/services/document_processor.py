
from pathlib import Path

from pypdf import PdfReader
from docx import Document


def extract_pdf(file_path):
    """Extract text from a PDF file using pypdf."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError("PDF file not found.")

    if path.suffix.lower() != ".pdf":
        raise ValueError("File must be a PDF.")

    reader = PdfReader(str(path))

    text_parts = []

    for page in reader.pages:
        text_parts.append(page.extract_text() or "")

    text = "\n".join(text_parts).strip()

    if not text:
        raise ValueError("No readable text found in PDF.")

    return text


def extract_docx(file_path):
    """Extract text from a DOCX file."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError("DOCX file not found.")

    if path.suffix.lower() != ".docx":
        raise ValueError("File must be a DOCX document.")

    document = Document(str(path))

    paragraphs = [
        paragraph.text
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    text = "\n".join(paragraphs).strip()

    if not text:
        raise ValueError("No readable text found in DOCX.")

    return text


def extract_txt(file_path):
    """Extract text from a TXT file."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError("TXT file not found.")

    if path.suffix.lower() != ".txt":
        raise ValueError("File must be a TXT document.")

    text = path.read_text(encoding="utf-8-sig").strip()

    if not text:
        raise ValueError("TXT file is empty.")

    return text


def extract_text_from_file(file_path):
    """Detect file type and extract its text."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError("File not found.")

    extension = path.suffix.lower()

    if extension == ".pdf":
        return extract_pdf(path)

    elif extension == ".docx":
        return extract_docx(path)

    elif extension == ".txt":
        return extract_txt(path)

    else:
        raise ValueError(
            "Unsupported file type. Use PDF, DOCX, or TXT."
        )


def extract_text_from_string(text):
    """Accept text entered directly by the user."""

    if not isinstance(text, str) or not text.strip():
        raise ValueError("Please enter some text.")

    return text.strip()
