from app.db.database import init_db
from app.services import memory


def test_memory_crud(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTOS_SQLITE_PATH", str(tmp_path / "test.db"))
    from app.core.config import get_settings

    get_settings.cache_clear()
    init_db()
    created = memory.create_memory({"type": "note", "title": "Demo", "content": "Remember local mode"})
    assert created["title"] == "Demo"
    updated = memory.update_memory(created["id"], {"content": "Remember mock mode"})
    assert "mock" in updated["content"]
    assert memory.retrieve_memories("mock")
    memory.delete_memory(created["id"])
    assert memory.list_memories() == []

