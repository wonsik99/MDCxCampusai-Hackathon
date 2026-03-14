"""PDF text extraction helpers."""

from io import BytesIO

from pypdf import PdfReader

from app.core.exceptions import AppError


def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(file_bytes))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if not text.strip():
            raise AppError("The PDF did not contain extractable text.", status_code=422, error_code="empty_pdf")
        return text
    except AppError:
        raise
    except Exception as exc:  # pragma: no cover - defensive wrapper
        raise AppError("Unable to parse PDF contents.", status_code=422, error_code="invalid_pdf") from exc
