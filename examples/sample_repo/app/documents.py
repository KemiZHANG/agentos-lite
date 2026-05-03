"""Document upload and chunking flow for the sample repository."""

from pathlib import Path


def extract_text(filename: str, content: bytes) -> str:
    """Extract text from Markdown and TXT documents."""
    suffix = Path(filename).suffix.lower()
    if suffix not in {".txt", ".md", ".markdown"}:
        return ""
    return content.decode("utf-8", errors="replace")


def create_chunks(text: str, size: int = 500) -> list[str]:
    """Split text into fixed-size demo chunks."""
    clean = " ".join(text.split())
    return [clean[index : index + size] for index in range(0, len(clean), size) if clean[index : index + size]]


def upload_document(filename: str, content: bytes) -> dict:
    """Handle a document upload and return indexed chunks."""
    text = extract_text(filename, content)
    chunks = create_chunks(text)
    return {"filename": filename, "chunks": chunks, "chunk_count": len(chunks)}

