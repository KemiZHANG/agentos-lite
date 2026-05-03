from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.database import init_db
from app.services import memory, rag
from app.services.codebase import index_repository
from app.services.prompts import seed_prompts
from app.services.tools import register_tools


def main() -> None:
    init_db()
    register_tools()
    seed_prompts()
    memory.create_memory(
        {
            "type": "project_context",
            "title": "MVP priority",
            "content": "Prefer a coherent runnable local MVP with mock providers and documented limitations.",
        }
    )
    for path in (ROOT / "examples" / "sample_docs").glob("*"):
        if path.is_file():
            rag.ingest_document(path.name, path.read_bytes())
    index_repository("sample_repo", str(ROOT / "examples" / "sample_repo"))
    print("Seeded demo documents, memory, prompts, tools, and sample repo.")


if __name__ == "__main__":
    main()
