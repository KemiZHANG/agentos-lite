from app.db.database import init_db
from pathlib import Path

from app.services import codebase, memory
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
    pasted_markdown = "# Launch notes\n\n- Write product brief\n- Add upload docs\n- Track tasks\n"
    assert detect_intent(pasted_markdown) == "general_chat"


def test_codebase_architecture_response_is_module_based(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    codebase.index_repository("sample_repo", str(_sample_repo_path()))
    response = run_chat("Explain the architecture of this repo.")
    assert response["intent"] == "codebase_question"
    assert "Architecture summary" in response["response"]
    assert "- auth:" in response["response"]
    assert "- documents:" in response["response"]
    assert any(citation["file_path"] == "app/auth.py" for citation in response["citations"])


def test_test_generation_response_has_demo_sections(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    codebase.index_repository("sample_repo", str(_sample_repo_path()))
    response = run_chat("Generate test suggestions for the document upload module")
    assert response["intent"] == "test_generation"
    assert "Suggested tests" in response["response"]
    assert "Target files" in response["response"]
    assert "Edge cases" in response["response"]
    assert "Existing related tests" in response["response"]
    assert "app/documents.py" in response["response"] or "app/upload.ts" in response["response"]


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


def test_chinese_project_overview_template(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    response = run_chat("What can AgentOS Lite do?", response_language="zh")
    assert response["intent"] == "project_overview"
    assert "自托管 AI 工作空间" in response["response"]


def _setup_db(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTOS_SQLITE_PATH", str(tmp_path / "test.db"))
    from app.core.config import get_settings

    get_settings.cache_clear()
    init_db()
    register_tools()
    seed_prompts()


def _sample_repo_path() -> Path:
    return Path(__file__).resolve().parents[3] / "examples" / "sample_repo"
