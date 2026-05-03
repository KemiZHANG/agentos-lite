from app.db.database import init_db
from app.services.tools import call_tool, register_tools


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

