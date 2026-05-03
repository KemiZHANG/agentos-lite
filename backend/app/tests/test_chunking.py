from app.services.chunking import chunk_text


def test_chunk_text_splits_with_overlap():
    text = "Sentence one. " * 100
    chunks = chunk_text(text, chunk_size=120, overlap=20)
    assert len(chunks) > 1
    assert all(chunk for chunk in chunks)


def test_chunk_text_empty():
    assert chunk_text("   ") == []

