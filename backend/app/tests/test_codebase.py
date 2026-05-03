from app.db.database import get_db, init_db
from app.services import codebase
from app.services.codebase import parse_symbols


def test_python_parser_extracts_functions_and_docstrings():
    symbols = parse_symbols('"""module"""\nimport os\n\ndef run(value):\n    """Run demo."""\n    return value\n', "python")
    names = {symbol["name"] for symbol in symbols}
    assert "os" in names
    assert "run" in names
    assert any(symbol.get("docstring") == "Run demo." for symbol in symbols)


def test_typescript_parser_extracts_exports():
    symbols = parse_symbols('import x from "pkg";\nexport function run(input: string) { return input; }\nexport class Worker {}\n', "typescript")
    names = {symbol["name"] for symbol in symbols}
    assert "pkg" in names
    assert "run" in names
    assert "Worker" in names


def test_codebase_index_ignores_env_database_logs_and_dependencies(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    repo = tmp_path / "repo"
    (repo / "backend" / "app" / "services").mkdir(parents=True)
    (repo / "node_modules").mkdir(parents=True)
    (repo / "logs").mkdir(parents=True)
    (repo / ".env").write_text("GEMINI_API_KEY=should-not-be-indexed", encoding="utf-8")
    (repo / "agentos_lite.db").write_text("sqlite bytes", encoding="utf-8")
    (repo / "logs" / "server.log").write_text("secret log", encoding="utf-8")
    (repo / "node_modules" / "pkg.js").write_text("export const bad = true", encoding="utf-8")
    (repo / "backend" / "app" / "services" / "llm.py").write_text("def get_llm_provider():\n    return 'mock'\n", encoding="utf-8")

    indexed = codebase.index_repository("safe-repo", str(repo))
    assert indexed["files_indexed"] == 1
    with get_db() as conn:
        rows = conn.execute("SELECT path, content FROM code_files").fetchall()
    assert [row["path"] for row in rows] == ["backend/app/services/llm.py"]
    assert "should-not-be-indexed" not in " ".join(row["content"] for row in rows)


def test_architecture_summary_and_test_suggestions_are_structured(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    repo = tmp_path / "repo"
    (repo / "backend" / "app" / "api").mkdir(parents=True)
    (repo / "backend" / "app" / "services").mkdir(parents=True)
    (repo / "frontend" / "app").mkdir(parents=True)
    (repo / "backend" / "app" / "api" / "documents.py").write_text("def upload_document():\n    return True\n", encoding="utf-8")
    (repo / "backend" / "app" / "services" / "rag.py").write_text("def retrieve():\n    return []\n", encoding="utf-8")
    (repo / "frontend" / "app" / "documents.tsx").write_text("export function DocumentsPage() { return null }\n", encoding="utf-8")
    indexed = codebase.index_repository("agentos-test", str(repo))

    architecture = codebase.answer_architecture_question(indexed["id"])
    assert "Architecture summary" in architecture["answer"]
    assert "- frontend:" in architecture["answer"]
    assert "- backend API:" in architecture["answer"]
    assert "- RAG:" in architecture["answer"]

    suggestions = codebase.generate_test_suggestions("Generate test suggestions for document upload.", indexed["id"])
    assert suggestions["markdown"].startswith("# Test Suggestions")
    assert suggestions["target_files"]
    assert suggestions["edge_cases"]
    assert "Suggested tests" in suggestions["markdown"]


def _setup_db(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTOS_SQLITE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    from app.core.config import get_settings

    get_settings.cache_clear()
    init_db()
