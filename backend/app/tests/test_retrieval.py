from app.db.database import init_db
from app.services.rag import ingest_document, retrieve


def test_mock_retrieval_returns_citation_ready_chunks(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTOS_SQLITE_PATH", str(tmp_path / "test.db"))
    from app.core.config import get_settings

    get_settings.cache_clear()
    init_db()
    ingest_document("brief.md", b"AgentOS Lite supports citations and memory.")
    results = retrieve("citations memory")
    assert results
    assert results[0]["document_name"] == "brief.md"
    assert results[0]["chunk_label"] == "brief.md chunk 1"
    assert results[0]["short_snippet"]


def test_retrieval_prefers_document_title_match(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTOS_SQLITE_PATH", str(tmp_path / "test.db"))
    from app.core.config import get_settings

    get_settings.cache_clear()
    init_db()
    ingest_document("product_brief.md", b"AgentOS Lite supports web chat and approvals.")
    ingest_document("security_notes.txt", b"Guardrails block dangerous operations.")
    results = retrieve("summarize uploaded product brief")
    assert results[0]["document_name"] == "product_brief.md"
    assert all(result["document_name"] == "product_brief.md" for result in results)
    assert "debug" in results[0]
