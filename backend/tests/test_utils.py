"""Unit tests for deterministic parsing and prerequisite helpers."""

from app.core.exceptions import AppError
from app.schemas.ai import ConceptExtractionItem
from app.utils.pdf import extract_text_from_pdf
from app.utils.prerequisite import enrich_with_prerequisites


def test_prerequisite_helper_infers_missing_linear_algebra_steps():
    enriched = enrich_with_prerequisites(
        [ConceptExtractionItem(name="Eigenvalues", slug="eigenvalues", description="Stretch factors")]
    )

    assert [concept.slug for concept in enriched] == [
        "matrix-multiplication",
        "determinant",
        "eigenvalues",
    ]
    assert enriched[0].is_inferred is True
    assert enriched[-1].is_inferred is False


def test_pdf_extractor_rejects_invalid_payload():
    try:
        extract_text_from_pdf(b"not-a-real-pdf")
    except AppError as exc:
        assert exc.error_code == "invalid_pdf"
    else:  # pragma: no cover - explicit failure branch
        raise AssertionError("Invalid PDF payload should raise an AppError.")
