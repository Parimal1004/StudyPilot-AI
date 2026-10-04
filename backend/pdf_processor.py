"""
PDF processor for StudyPilot AI.
Uses PyMuPDF (fitz) to extract text and answer questions about uploaded documents.
"""
import os
import uuid
import logging
from pathlib import Path
from typing import Tuple

try:
    import pymupdf as fitz  # PyMuPDF >= 1.25
except ImportError:
    import fitz  # PyMuPDF legacy

from utils.llm_client import chat_completion

logger = logging.getLogger(__name__)

MAX_PDF_SIZE_MB = float(os.getenv("MAX_PDF_SIZE_MB", "10"))
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Maximum characters to send to LLM per document context
MAX_CONTEXT_CHARS = 12_000


def save_uploaded_pdf(file_bytes: bytes, original_name: str) -> Tuple[str, str]:
    """
    Save PDF bytes to disk. Returns (saved_filename, file_path).
    Raises ValueError if file is too large or not a PDF.
    """
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_PDF_SIZE_MB:
        raise ValueError(
            f"PDF file is too large ({size_mb:.1f} MB). Maximum allowed: {MAX_PDF_SIZE_MB} MB."
        )

    # Check magic bytes for PDF
    if not file_bytes.startswith(b"%PDF"):
        raise ValueError("The uploaded file does not appear to be a valid PDF.")

    safe_name = f"{uuid.uuid4().hex}_{Path(original_name).name}"
    file_path = UPLOAD_DIR / safe_name
    file_path.write_bytes(file_bytes)
    return safe_name, str(file_path)


def extract_text(file_path: str) -> Tuple[str, int]:
    """
    Extract all text from a PDF. Returns (text, page_count).
    Raises RuntimeError on invalid/corrupt PDF.
    """
    try:
        doc = fitz.open(file_path)
        page_count = len(doc)
        pages_text = []
        for page in doc:
            pages_text.append(page.get_text())
        doc.close()
        full_text = "\n".join(pages_text).strip()
        return full_text, page_count
    except Exception as e:
        logger.error("PDF extraction error: %s", e)
        raise RuntimeError("Could not read the PDF. The file may be corrupted or password-protected.")


def _truncate_context(text: str) -> str:
    """Truncate document text to fit within LLM context limits."""
    if len(text) > MAX_CONTEXT_CHARS:
        return text[:MAX_CONTEXT_CHARS] + "\n\n[Document truncated for length]"
    return text


PDF_QA_SYSTEM = """You are a helpful study assistant. A student has uploaded their notes or textbook as a PDF.
Answer the student's question based ONLY on the content provided from the document.
If the answer is not in the document, say so clearly.
Be concise and helpful."""

PDF_SUMMARY_SYSTEM = """You are a helpful study assistant. Summarize the following document for a college student.
Return a JSON object with:
{
  "summary": "A clear 3-5 sentence overview of the document.",
  "key_points": ["point 1", "point 2", ...]  // 5-8 most important points
}
Return ONLY valid JSON, no extra text."""


def answer_pdf_question(document_text: str, question: str) -> str:
    """Answer a student's question based on the PDF content."""
    context = _truncate_context(document_text)
    user_prompt = (
        f"Document Content:\n{context}\n\n"
        f"Student's Question: {question}"
    )
    return chat_completion(
        system_prompt=PDF_QA_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=800,
    )


def summarize_pdf(document_text: str):
    """Generate a summary and key points from the PDF content."""
    from utils.llm_client import parse_json_response

    context = _truncate_context(document_text)
    user_prompt = f"Document Content:\n{context}\n\nGenerate the summary and key points."
    raw = chat_completion(
        system_prompt=PDF_SUMMARY_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=1000,
        expect_json=True,
    )
    data = parse_json_response(raw)
    return data.get("summary", ""), data.get("key_points", [])
