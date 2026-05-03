from app.db.database import init_db
from app.services import memory
from app.services.agent import detect_intent, run_chat
from app.services.prompts import seed_prompts
from app.services.rag import ingest_document
from app.services.tools import register_tools


def test_agent_intent_routing():
    assert detect_intent("Which files are related to document upload?") == "codebase_question"
    assert detect_intent("Generate test suggestions for this function") == "test_generation"
    assert detect_intent("remember that I prefer mock mode") == "memory_update"
    assert detect_intent("What can AgentOS Lite do?") == "project_overview"
    assert detect_intent("Summarize the uploaded product brief.") == "summarize_document"
    assert detect_intent("How should you explain technical topics to me?") == "general_chat"


def test_summarize_product_brief_uses_retrieved_chunks(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    ingest_document(
        "product_brief.md",
        b"AgentOS Lite supports web chat, RAG citations, memory, approvals, scheduler-ready tasks, LLMOps, and codebase intelligence.",
    )
    response = run_chat("Summarize the uploaded product brief.")
    assert response["intent"] == "summarize_document"
    assert "Summary of product_brief.md" in response["response"]
    assert "web chat" in response["response"]
    assert response["citations"][0]["document_name"] == "product_brief.md"
    assert response["citations"][0]["short_snippet"]


def test_memory_aware_response_uses_memory_content(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    memory.create_memory(
        {
            "type": "user_preference",
            "title": "Explanation style",
            "content": "The user prefers concise technical explanations with practical examples.",
        }
    )
    response = run_chat("How should you explain technical topics to me?")
    assert response["intent"] == "general_chat"
    assert "concise technical explanations" in response["response"]


def test_project_overview_skips_rag_and_explains_features(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    ingest_document("product_brief.md", b"This uploaded document should not be needed for a generic overview.")
    response = run_chat("What can AgentOS Lite do?")
    assert response["intent"] == "project_overview"
    assert "web chat" in response["response"]
    assert "codebase intelligence" in response["response"]
    assert response["citations"] == []


def _setup_db(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTOS_SQLITE_PATH", str(tmp_path / "test.db"))
    from app.core.config import get_settings

    get_settings.cache_clear()
    init_db()
    register_tools()
    seed_prompts()
