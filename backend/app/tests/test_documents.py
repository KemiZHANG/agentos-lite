from app.db.database import get_db, init_db, json_loads
from app.services import rag


def _setup_db(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTOS_SQLITE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    from app.core.config import get_settings

    get_settings.cache_clear()
    init_db()


def test_markdown_upload_chunk_preview_delete_and_reindex(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    document = rag.ingest_document(
        "product_brief.md",
        b"# Product Brief\n\nAgentOS Lite provides RAG citations, memory, approvals, and LLMOps.",
    )
    assert document["name"] == "product_brief.md"
    assert document["metadata"]["extracted_text_length"] > 20
    assert document["metadata"]["indexed_status"] == "indexed"
    assert document["chunk_count"] >= 1

    chunks = rag.list_document_chunks(document["id"])
    assert chunks[0]["chunk_label"].startswith("product_brief.md chunk")
    assert "AgentOS Lite" in chunks[0]["short_snippet"]

    reindexed = rag.reindex_document(document["id"])
    assert reindexed["metadata"]["indexed_status"] == "reindexed"

    rag.delete_document(document["id"])
    assert rag.list_documents() == []


def test_title_filter_snippet_keywords_and_retrieval_log(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    rag.ingest_document("product_brief.md", b"Product brief: AgentOS Lite supports cited RAG answers and memory.")
    rag.ingest_document("security_notes.md", b"Security notes: blocked tools never execute shell commands.")

    results = rag.retrieve("Summarize the uploaded product brief.", agent_run_id="run-docs")
    assert results
    assert all(item["document_name"] == "product_brief.md" for item in results)
    assert results[0]["short_snippet"]
    assert "product" in results[0]["debug"]["document_title_match_terms"]

    with get_db() as conn:
        row = conn.execute("SELECT * FROM retrieval_logs WHERE agent_run_id = ?", ("run-docs",)).fetchone()
    logged = json_loads(row["results_json"], [])
    assert row["source"] == "documents"
    assert logged[0]["document_name"] == "product_brief.md"
    assert logged[0]["short_snippet"]
