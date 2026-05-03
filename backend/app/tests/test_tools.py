from app.db.database import init_db
from app.services.tools import call_tool, decide_approval, list_approvals, list_tool_calls, register_tools


def test_tool_risk_handling(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTOS_SQLITE_PATH", str(tmp_path / "test.db"))
    from app.core.config import get_settings

    get_settings.cache_clear()
    init_db()
    register_tools()
    safe = call_tool("extract_task_list", {"text": "- ship MVP"})
    assert safe["status"] == "completed"
    risky = call_tool("save_memory", {"title": "x", "content": "y"})
    assert risky["status"] == "approval_required"
    blocked = call_tool("dangerous_shell_command", {"command": "rm -rf /"})
    assert blocked["status"] == "blocked"


def test_approval_approve_reject_and_tool_call_log(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTOS_SQLITE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    from app.core.config import get_settings

    get_settings.cache_clear()
    init_db()
    register_tools()

    first = call_tool("save_memory", {"type": "note", "title": "Approved note", "content": "Keep mock mode"})
    second = call_tool("generate_markdown_report", {"title": "Draft", "body": "Needs review"})
    approvals = list_approvals()
    assert len([approval for approval in approvals if approval["status"] == "pending"]) == 2

    approved = decide_approval(first["approval_id"], "approved", "ok")
    rejected = decide_approval(second["approval_id"], "rejected", "not now")
    assert approved["status"] == "approved"
    assert rejected["status"] == "rejected"

    calls = list_tool_calls()
    statuses = {call["tool_name"]: call["status"] for call in calls}
    assert statuses["save_memory"] == "completed"
    assert statuses["generate_markdown_report"] == "rejected"
    assert any(call["input"] for call in calls)
