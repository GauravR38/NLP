import io
from typing import Optional

import pdfplumber


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from a PDF file uploaded via Streamlit or similar interface.

    Parameters
    ----------
    file_bytes : bytes
        Raw bytes of the uploaded PDF.

    Returns
    -------
    str
        Extracted text from all pages concatenated.
    """
    if not file_bytes:
        return ""

    text_chunks = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text: Optional[str] = page.extract_text()
            if page_text:
                text_chunks.append(page_text)

    return "\n".join(text_chunks).strip()


__all__ = ["extract_text_from_pdf"]

