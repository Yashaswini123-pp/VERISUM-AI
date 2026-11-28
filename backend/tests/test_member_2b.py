from docx import Document
import pytest

from app.services.abstractive import (
    generate_abstractive_summary,
    get_recommended_transformer_models,
)
from app.services.chunking import (
    hierarchical_extractive_summarize,
    split_sentences_into_chunks,
)
from app.services.pipeline import summarize_file, summarize_text
from app.services.quality_metrics import (
    compute_quality_metrics,
    evaluate_rouge,
    measure_redundancy,
)


def _build_minimal_pdf_bytes(text: str) -> bytes:
    """Construct a minimal valid single-page PDF containing readable ASCII text."""
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET".encode("latin-1")
    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        (
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        ),
        (
            f"4 0 obj\n<< /Length {len(stream)} >>\nstream\n".encode("latin-1")
            + stream
            + b"\nendstream\nendobj\n"
        ),
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(out))
        out.extend(obj)
    xref_start = len(out)
    out.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("latin-1"))
    for offset in offsets[1:]:
        out.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    out.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_start}\n%%EOF\n"
        ).encode("latin-1")
    )
    return bytes(out)


def _long_research_document() -> str:
    paragraphs = [
        (
            "Artificial intelligence has transformed modern diagnostic medicine across radiology and pathology. "
            "Deep neural networks analyze medical scans in order to identify early tissue anomalies rapidly. "
            "Radiologists review automated heatmaps alongside clinical notes before finalizing patient reports. "
            "Hospitals report shorter turnaround times when triage queues prioritize urgent imaging findings."
        ),
        (
            "However, automated clinical summaries must remain grounded in verifiable source records. "
            "Unverified generative paraphrases can introduce subtle factual distortions during handoffs. "
            "Therefore, researchers combine extractive sentence ranking with claim verification pipelines. "
            "Claim extraction algorithms isolate atomic factual statements for downstream evidence matching."
        ),
        (
            "Furthermore, evidence retrieval components query peer-reviewed medical databases for corroboration. "
            "Fact verification classifiers label claims as supported, contradicted, or lacking evidence. "
            "Auditable confidence scores help physicians inspect why each claim passed or failed verification. "
            "Transparent user interfaces present highlighted source sentences next to summary statements."
        ),
        (
            "In addition, long multi-page clinical guidelines challenge single-window ranking algorithms. "
            "Sentence-boundary chunking divides large manuscripts into overlapping segments without splitting sentences. "
            "Hierarchical summarization selects salient candidates per section and reconciles them globally. "
            "Quality evaluation metrics track compression ratio, semantic coverage, and summary redundancy."
        ),
        (
            "Finally, deploying local summarization pipelines eliminates external API latency and licensing costs. "
            "Lightweight NLP toolkits run offline while leaving optional room for local transformer models. "
            "Research teams benchmark extractive and abstractive summaries against gold references using ROUGE. "
            "Ongoing studies evaluate clinician trust when verified evidence links accompany every summary."
        ),
    ]
    return " ".join(paragraphs)


def test_normal_text_returns_both_extractive_and_abstractive():
    text = (
        "However, artificial intelligence is able to transform modern healthcare workflows. "
        "Machine learning models analyze medical images in order to detect diseases early. "
        "Clinicians review diagnostic suggestions carefully before making treatment choices. "
        "Researchers continue improving model interpretability across hospital departments."
    )
    result = summarize_text(text, "medium")

    # Member 2A backward-compatible keys
    for key in (
        "original_text",
        "cleaned_text",
        "sentences",
        "extractive_summary",
        "selected_sentence_ids",
        "sentence_scores",
    ):
        assert key in result
        assert result[key]

    # Member 2B keys
    assert result["summary_length"] == "medium"
    assert isinstance(result["abstractive_summary"], str)
    assert result["abstractive_summary"].strip()
    assert result["abstractive_summary"] != result["extractive_summary"]
    assert result["abstractive_metadata"]["method"] == "local_abstractive_fusion"
    assert result["chunking"]["chunking_used"] is False
    assert result["quality_metrics"]["rouge"] is None


def test_single_sentence_input_handled_cleanly():
    text = "Artificial intelligence accelerates scientific literature reviews."
    result = summarize_text(text, "short")

    assert result["extractive_summary"] == text
    assert result["abstractive_summary"]
    assert result["selected_sentence_ids"] == [1]
    assert result["quality_metrics"]["total_sentences"] == 1


def test_chunking_preserves_boundaries_and_overlap():
    sentences = [
        {"id": i, "text": f"Sentence number {i} discusses evidence grounded summarization research topics."}
        for i in range(1, 16)
    ]
    chunks = split_sentences_into_chunks(sentences, max_chunk_words=35, overlap_sentences=1)

    assert len(chunks) >= 3
    for idx in range(1, len(chunks)):
        prev_last_id = chunks[idx - 1]["sentence_ids"][-1]
        assert chunks[idx]["overlap_sentence_ids"] == [prev_last_id]
        assert chunks[idx]["sentence_ids"][0] == prev_last_id


def test_long_document_hierarchical_summarization():
    long_text = _long_research_document()
    short_res = summarize_text(long_text, "short")
    detailed_res = summarize_text(long_text, "detailed")

    assert short_res["chunking"]["chunking_used"] is True
    assert short_res["chunking"]["chunk_count"] >= 2
    assert short_res["chunking"]["overlap_sentences"] == 1
    assert len(short_res["chunking"]["chunks"]) == short_res["chunking"]["chunk_count"]
    assert short_res["abstractive_metadata"]["hierarchical_used"] is True
    assert short_res["abstractive_summary"]

    # Ensure sentence IDs are valid, sorted, and scale with requested length.
    total = len(short_res["sentences"])
    assert all(1 <= sid <= total for sid in short_res["selected_sentence_ids"])
    assert short_res["selected_sentence_ids"] == sorted(short_res["selected_sentence_ids"])
    assert len(short_res["selected_sentence_ids"]) < len(detailed_res["selected_sentence_ids"])


def test_quality_metrics_compression_coverage_and_redundancy():
    doc = _long_research_document()
    result = summarize_text(doc, "medium")
    qm = result["quality_metrics"]

    assert 0.0 < qm["compression_ratio"] < 1.0
    assert 0.0 < qm["abstractive_compression_ratio"] < 1.0
    assert 0.0 < qm["sentence_coverage"]["selected_sentence_ratio"] < 1.0
    assert 0.0 <= qm["sentence_coverage"]["semantic_coverage"] <= 1.0
    assert 0.0 <= qm["sentence_coverage"]["concept_coverage"] <= 1.0
    assert qm["rouge"] is None

    repetitive = (
        "AI helps doctors review scans. AI helps doctors review scans. "
        "AI helps doctors review scans."
    )
    diverse = (
        "AI accelerates radiology triage. "
        "Verification checks claims against literature. "
        "Chunking preserves context across long manuscripts."
    )
    assert measure_redundancy(repetitive)["redundancy_score"] > measure_redundancy(diverse)["redundancy_score"]


def test_rouge_computed_only_with_genuine_reference():
    identical = evaluate_rouge(
        "AI improves healthcare diagnosis.",
        "AI improves healthcare diagnosis.",
    )
    assert identical["rouge1"]["f1"] == 1.0
    assert identical["rouge2"]["f1"] == 1.0
    assert identical["rougeL"]["f1"] == 1.0

    with pytest.raises(ValueError):
        evaluate_rouge("Some summary.", "   ")

    doc = _long_research_document()
    no_ref = summarize_text(doc, "short", reference_summary="   ")
    assert no_ref["quality_metrics"]["rouge"] is None

    with_ref = summarize_text(
        doc,
        "short",
        reference_summary=(
            "Artificial intelligence aids radiology triage while verification pipelines "
            "ground claims in peer-reviewed evidence and chunked summarization handles long documents."
        ),
    )
    rouge = with_ref["quality_metrics"]["rouge"]
    assert rouge is not None
    for branch in ("extractive", "abstractive"):
        for metric in ("rouge1", "rouge2", "rougeL"):
            assert 0.0 <= rouge[branch][metric]["f1"] <= 1.0


def test_file_uploads_txt_docx_pdf(tmp_path):
    sample = (
        "Artificial intelligence assists clinicians with diagnostic imaging. "
        "Machine learning highlights anomalies in medical scans. "
        "Verification pipelines ground claims in source evidence. "
        "Quality metrics measure compression and coverage."
    )

    txt_file = tmp_path / "sample.txt"
    txt_file.write_text(sample, encoding="utf-8")
    txt_res = summarize_file(txt_file, "medium")
    assert txt_res["extractive_summary"]
    assert txt_res["abstractive_summary"]

    docx_file = tmp_path / "sample.docx"
    doc = Document()
    doc.add_paragraph(sample)
    doc.save(str(docx_file))
    docx_res = summarize_file(docx_file, "medium")
    assert docx_res["extractive_summary"]
    assert docx_res["abstractive_summary"]

    pdf_file = tmp_path / "sample.pdf"
    pdf_file.write_bytes(_build_minimal_pdf_bytes(sample))
    pdf_res = summarize_file(pdf_file, "medium")
    assert pdf_res["extractive_summary"]
    assert pdf_res["abstractive_summary"]


def test_invalid_inputs_raise_clean_errors():
    with pytest.raises(ValueError):
        summarize_text("   ", "medium")
    with pytest.raises(ValueError):
        summarize_text("Valid sentence here.", "invalid_size")
    with pytest.raises(ValueError):
        summarize_text("Valid sentence here.", "medium", reference_summary=123)
    with pytest.raises(ValueError):
        split_sentences_into_chunks([{"id": 1, "text": "Test."}], max_chunk_words=0)
    with pytest.raises(ValueError):
        hierarchical_extractive_summarize([], "invalid_size")
    empty_metrics = compute_quality_metrics("", [], "", "", [])
    assert empty_metrics["original_word_count"] == 0
    assert empty_metrics["rouge"] is None
    # Verify abstractive model catalog helper returns local model recommendations.
    models = get_recommended_transformer_models()
    assert len(models) >= 2
    assert generate_abstractive_summary([], "medium")["summary"] == ""
