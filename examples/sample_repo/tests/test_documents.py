from app.documents import create_chunks, extract_text, upload_document


def test_upload_document_chunks_markdown():
    result = upload_document("notes.md", b"# Notes\n\nhello world")
    assert result["chunk_count"] == 1
    assert "hello world" in result["chunks"][0]


def test_extract_text_rejects_unknown_suffix():
    assert extract_text("archive.zip", b"binary") == ""


def test_create_chunks_handles_empty_text():
    assert create_chunks("") == []

