from docx import Document
from fastapi.testclient import TestClient

from app.main import app
from tests.test_member_2b import _build_minimal_pdf_bytes, _long_research_document

client = TestClient(app)

SAMPLE_TEXT = (
    "Artificial intelligence is transforming healthcare diagnostics. "
    "Machine learning models detect subtle patterns in radiology scans. "
    "Clinical teams verify outputs against patient records before acting. "
    "Automated summaries help doctors review long documents faster."
)


def test_health_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "VeriSum AI"}


def test_models_endpoint():
    response = client.get("/summarize/models")
    assert response.status_code == 200
    body = response.json()
    assert body["default_backend"] == "local_abstractive_fusion"
    assert len(body["recommended_transformer_models"]) >= 2


def test_summarize_text_endpoint_and_metrics():
    response = client.post(
        "/summarize/text",
        data={"text": SAMPLE_TEXT, "summary_length": "medium"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["original_text"] == SAMPLE_TEXT
    assert body["extractive_summary"]
    assert body["abstractive_summary"]
    assert len(body["sentences"]) == 4
    assert body["selected_sentence_ids"]
    assert body["sentence_scores"]
    assert body["chunking"]["chunking_used"] is False
    assert body["quality_metrics"]["rouge"] is None


def test_summarize_text_with_reference_computes_rouge():
    response = client.post(
        "/summarize/text",
        data={
            "text": SAMPLE_TEXT,
            "summary_length": "short",
            "reference_summary": "AI models detect patterns in radiology scans so doctors review records faster.",
        },
    )
    assert response.status_code == 200
    rouge = response.json()["quality_metrics"]["rouge"]
    assert rouge is not None
    assert "rouge1" in rouge["extractive"]
    assert "rougeL" in rouge["abstractive"]


def test_summarize_long_text_triggers_chunking():
    long_doc = _long_research_document()
    response = client.post(
        "/summarize/text",
        data={"text": long_doc, "summary_length": "medium"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["chunking"]["chunking_used"] is True
    assert body["chunking"]["chunk_count"] >= 2
    assert body["abstractive_summary"]


def test_summarize_text_invalid_length():
    response = client.post(
        "/summarize/text",
        data={"text": SAMPLE_TEXT, "summary_length": "huge"},
    )
    assert response.status_code == 422


def test_summarize_text_empty_rejected():
    response = client.post(
        "/summarize/text",
        data={"text": "   ", "summary_length": "short"},
    )
    assert response.status_code == 422


def test_summarize_file_txt_docx_pdf(tmp_path):
    txt_res = client.post(
        "/summarize/file",
        files={"file": ("notes.txt", SAMPLE_TEXT.encode("utf-8"), "text/plain")},
        data={"summary_length": "short"},
    )
    assert txt_res.status_code == 200
    assert txt_res.json()["extractive_summary"]
    assert txt_res.json()["abstractive_summary"]

    docx_path = tmp_path / "notes.docx"
    doc = Document()
    doc.add_paragraph(SAMPLE_TEXT)
    doc.save(str(docx_path))
    docx_res = client.post(
        "/summarize/file",
        files={
            "file": (
                "notes.docx",
                docx_path.read_bytes(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        data={"summary_length": "medium"},
    )
    assert docx_res.status_code == 200
    assert docx_res.json()["abstractive_summary"]

    pdf_bytes = _build_minimal_pdf_bytes(SAMPLE_TEXT)
    pdf_res = client.post(
        "/summarize/file",
        files={"file": ("notes.pdf", pdf_bytes, "application/pdf")},
        data={"summary_length": "medium"},
    )
    assert pdf_res.status_code == 200
    assert pdf_res.json()["extractive_summary"]


def test_summarize_file_invalid_and_empty():
    unsupported = client.post(
        "/summarize/file",
        files={"file": ("notes.csv", b"a,b,c", "text/csv")},
        data={"summary_length": "medium"},
    )
    assert unsupported.status_code == 422

    empty_file = client.post(
        "/summarize/file",
        files={"file": ("empty.txt", b"", "text/plain")},
        data={"summary_length": "medium"},
    )
    assert empty_file.status_code == 422

    corrupt_docx = client.post(
        "/summarize/file",
        files={"file": ("fake.docx", b"not-a-zip-docx", "application/octet-stream")},
        data={"summary_length": "medium"},
    )
    assert corrupt_docx.status_code == 422


def test_extract_claims_endpoint():
    response = client.post(
        "/claims/extract",
        data={"text": SAMPLE_TEXT, "threshold": "0.55"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_sentences"] == 4
    assert len(body["claims"]) >= 1
