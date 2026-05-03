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

