from __future__ import annotations

import ast
import re
import uuid
from pathlib import Path
from typing import Any

from app.db.database import get_db, json_dumps, json_loads, rows_to_dicts, utc_now


IGNORE_DIRS = {"node_modules", ".git", "dist", "build", "__pycache__", ".venv", "venv", ".next", ".cache", "logs"}
IGNORE_FILES = {".env", "agentos_lite.db", "server.log", "server.err"}
SUPPORTED_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".md", ".json"}


def index_repository(name: str, root_path: str) -> dict[str, Any]:
    root = Path(root_path).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Repository path not found: {root}")
    repository_id = str(uuid.uuid4())
    now = utc_now()
    files_indexed = 0
    symbols_indexed = 0
    with get_db() as conn:
        conn.execute(
            "INSERT INTO code_repositories (id, name, root_path, metadata_json, indexed_at) VALUES (?, ?, ?, ?, ?)",
            (repository_id, name, str(root), json_dumps({"ignore_dirs": sorted(IGNORE_DIRS)}), now),
        )
        for file_path in _iter_files(root):
            rel_path = file_path.relative_to(root).as_posix()
            content = file_path.read_text(encoding="utf-8", errors="replace")
            language = _language_for(file_path)
            symbols = parse_symbols(content, language)
            summary = summarize_file(rel_path, content, symbols)
            file_id = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO code_files
                (id, repository_id, path, language, content, summary, metadata_json, indexed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (file_id, repository_id, rel_path, language, content, summary, json_dumps({"size": len(content)}), now),
            )
            files_indexed += 1
            for symbol in symbols:
                conn.execute(
                    """
                    INSERT INTO code_symbols
                    (id, repository_id, file_id, name, kind, line_start, line_end, signature, docstring, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        repository_id,
                        file_id,
                        symbol["name"],
                        symbol["kind"],
                        symbol.get("line_start"),
                        symbol.get("line_end"),
                        symbol.get("signature"),
                        symbol.get("docstring"),
                        json_dumps(symbol.get("metadata", {})),
                    ),
                )
                symbols_indexed += 1
    return {"id": repository_id, "name": name, "root_path": str(root), "files_indexed": files_indexed, "symbols_indexed": symbols_indexed}


def index_current_repository() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[3]
    return index_repository("agentos-lite", str(root))


def list_repositories() -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT r.*, COUNT(DISTINCT f.id) AS file_count, COUNT(DISTINCT s.id) AS symbol_count
            FROM code_repositories r
            LEFT JOIN code_files f ON f.repository_id = r.id
            LEFT JOIN code_symbols s ON s.repository_id = r.id
            GROUP BY r.id
            ORDER BY r.indexed_at DESC
            """
        ).fetchall()
    repos = rows_to_dicts(rows)
    for repo in repos:
        repo["metadata"] = json_loads(repo.pop("metadata_json", None), {})
    return repos


def latest_repository_id() -> str | None:
    repos = list_repositories()
    return repos[0]["id"] if repos else None


def search_codebase(query: str, repository_id: str | None = None, limit: int = 8) -> list[dict[str, Any]]:
    repository_id = repository_id or latest_repository_id()
    if not repository_id:
        return []
    terms = {term.lower() for term in re.findall(r"[a-zA-Z0-9_]+", query) if len(term) > 2}
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM code_files WHERE repository_id = ?",
            (repository_id,),
        ).fetchall()
        symbols = conn.execute(
            "SELECT s.*, f.path FROM code_symbols s JOIN code_files f ON f.id = s.file_id WHERE s.repository_id = ?",
            (repository_id,),
        ).fetchall()
    scored: list[dict[str, Any]] = []
    symbol_by_file: dict[str, list[dict[str, Any]]] = {}
    for symbol in rows_to_dicts(symbols):
        symbol_by_file.setdefault(symbol["file_id"], []).append(symbol)
    for row in rows_to_dicts(rows):
        haystack = f"{row['path']} {row['language']} {row['summary']} {row['content']}".lower()
        score = sum(3 if term in row["path"].lower() else 1 for term in terms if term in haystack)
        for symbol in symbol_by_file.get(row["id"], []):
            symbol_text = f"{symbol['name']} {symbol['kind']} {symbol.get('signature') or ''}".lower()
            score += sum(2 for term in terms if term in symbol_text)
        if score:
            matched_keywords = sorted(term for term in terms if term in haystack)
            matched_symbols = [
                symbol["name"]
                for symbol in symbol_by_file.get(row["id"], [])
                if any(term in f"{symbol['name']} {symbol.get('signature') or ''}".lower() for term in terms)
            ][:8]
            scored.append(
                {
                    "file_id": row["id"],
                    "repository_id": row["repository_id"],
                    "path": row["path"],
                    "language": row["language"],
                    "summary": row["summary"],
                    "score": score,
                    "symbols": symbol_by_file.get(row["id"], [])[:10],
                    "matched_keywords": matched_keywords,
                    "matched_symbols": matched_symbols,
                    "module_role": module_role_for_path(row["path"]),
                    "match_reason": build_match_reason(row["path"], matched_keywords, matched_symbols),
                }
            )
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:limit]


def answer_repo_question(question: str, repository_id: str | None = None) -> dict[str, Any]:
    if _is_architecture_question(question):
        return answer_architecture_question(repository_id)
    matches = search_codebase(question, repository_id=repository_id)
    citations = [_code_citation(match) for match in matches]
    if not matches:
        return {"answer": "No indexed files matched. Index the sample repository first.", "citations": []}
    lines = ["I found these repository areas as the strongest evidence:"]
    for match in matches[:5]:
        symbol_names = ", ".join(symbol["name"] for symbol in match.get("symbols", [])[:5])
        detail = f" - {match['path']}: {match['module_role']} {match['match_reason']}"
        if symbol_names:
            detail += f" Symbols: {symbol_names}."
        lines.append(detail)
    return {"answer": "\n".join(lines), "citations": citations}


def answer_architecture_question(repository_id: str | None = None) -> dict[str, Any]:
    files = list_code_files(repository_id)
    if not files:
        return {"answer": "No indexed files are available. Index the sample repository first.", "citations": []}
    grouped = group_files_by_module(files)
    module_order = ["frontend", "backend API", "services", "RAG", "LLM provider", "memory", "tools/approvals", "codebase skill", "LLMOps", "docs/examples", "auth", "documents", "upload", "tasks", "tests", "README / docs", "other"]
    lines = ["Architecture summary:", "The sample repository is organized into small, testable modules with clear responsibilities."]
    citations: list[dict[str, Any]] = []
    for module in module_order:
        module_files = grouped.get(module, [])
        if not module_files:
            continue
        paths = ", ".join(file["path"] for file in module_files)
        role = module_role_for_name(module)
        lines.append(f"- {module}: {role} Files: {paths}.")
        for file in module_files:
            citations.append(_code_citation({**file, "score": file.get("score", 1), "matched_keywords": [module], "matched_symbols": [symbol["name"] for symbol in file.get("symbols", [])[:4]]}))
    lines.append("Read the cited files by module first; they form the quickest mental map of the repo.")
    return {"answer": "\n".join(lines), "citations": citations[:12]}


def find_relevant_files(issue: str, repository_id: str | None = None) -> dict[str, Any]:
    matches = search_codebase(issue, repository_id=repository_id)
    return {
        "issue": issue,
        "files": [
            {
                "path": match["path"],
                "reason": f"Matched issue terms with score {match['score']} across path, symbols, and content.",
                "symbols": [symbol["name"] for symbol in match.get("symbols", [])[:6]],
            }
            for match in matches
        ],
    }


def generate_test_suggestions(target: str, repository_id: str | None = None) -> dict[str, Any]:
    matches = search_codebase(target, repository_id=repository_id)
    if not matches and "document upload" in target.lower():
        matches = search_codebase("document upload chunks extract upload", repository_id=repository_id)
    suggestions: list[dict[str, Any]] = []
    for match in matches[:5]:
        symbol_names = [symbol["name"] for symbol in match.get("symbols", [])[:4]]
        suggestions.append(
            {
                "file_path": match["path"],
                "target_symbols": symbol_names,
                "match_reason": match.get("match_reason", ""),
                "suggestions": [
                    _happy_path_suggestion(match["path"], symbol_names),
                    _edge_case_suggestion(match["path"]),
                    "Assert returned metadata and error messages remain stable enough for the UI and agent citations.",
                ],
            }
        )
    existing_tests = [match for match in matches if "test" in match["path"].lower()]
    target_files = [match for match in matches if "test" not in match["path"].lower()]
    return {
        "target": target,
        "target_files": target_files[:6],
        "existing_related_tests": existing_tests[:4],
        "edge_cases": [
            "Empty file content",
            "Unsupported extension such as .zip",
            "Markdown headings and whitespace-heavy input",
            "Large text that must split into multiple chunks",
            "Invalid bytes that require replacement decoding",
        ],
        "suggestions": suggestions,
        "citations": [_code_citation(match) for match in matches[:8]],
        "markdown": test_suggestions_to_markdown(target, suggestions, target_files[:6], existing_tests[:4]),
    }


def repo_map(repository_id: str | None = None) -> dict[str, Any]:
    files = list_code_files(repository_id)
    languages: dict[str, int] = {}
    top_dirs: dict[str, int] = {}
    modules: dict[str, int] = {}
    symbol_count = 0
    indexed_at = None
    for file in files:
        languages[file["language"]] = languages.get(file["language"], 0) + 1
        top_dir = file["path"].split("/", 1)[0] if "/" in file["path"] else file["path"]
        top_dirs[top_dir] = top_dirs.get(top_dir, 0) + 1
        module = module_name_for_path(file["path"])
        modules[module] = modules.get(module, 0) + 1
        symbol_count += len(file.get("symbols", []))
        indexed_at = file.get("indexed_at") or indexed_at
    return {
        "total_files": len(files),
        "symbols": symbol_count,
        "languages": languages,
        "main_modules": modules,
        "top_directories": dict(sorted(top_dirs.items(), key=lambda item: item[1], reverse=True)[:10]),
        "indexed_time": indexed_at,
    }


def list_code_files(repository_id: str | None = None) -> list[dict[str, Any]]:
    repository_id = repository_id or latest_repository_id()
    if not repository_id:
        return []
    with get_db() as conn:
        file_rows = rows_to_dicts(conn.execute("SELECT * FROM code_files WHERE repository_id = ? ORDER BY path", (repository_id,)).fetchall())
        symbol_rows = rows_to_dicts(
            conn.execute(
                "SELECT s.*, f.path FROM code_symbols s JOIN code_files f ON f.id = s.file_id WHERE s.repository_id = ?",
                (repository_id,),
            ).fetchall()
        )
    symbols_by_file: dict[str, list[dict[str, Any]]] = {}
    for symbol in symbol_rows:
        symbols_by_file.setdefault(symbol["file_id"], []).append(symbol)
    for file in file_rows:
        file["symbols"] = symbols_by_file.get(file["id"], [])
        file["module_role"] = module_role_for_path(file["path"])
        file["matched_keywords"] = []
        file["matched_symbols"] = [symbol["name"] for symbol in file["symbols"][:6]]
        file["match_reason"] = f"Module role: {file['module_role']}"
    return file_rows


def group_files_by_module(files: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for file in files:
        module = module_name_for_path(file["path"])
        grouped.setdefault(module, []).append(file)
    return grouped


def module_name_for_path(path: str) -> str:
    lower = path.lower()
    if lower.startswith("frontend/"):
        return "frontend"
    if lower.startswith("backend/app/api"):
        return "backend API"
    if lower.startswith("backend/app/services/rag") or "/rag" in lower:
        return "RAG"
    if lower.startswith("backend/app/services/llm") or "provider" in lower:
        return "LLM provider"
    if lower.startswith("backend/app/services/memory"):
        return "memory"
    if "tools.py" in lower or "approvals" in lower:
        return "tools/approvals"
    if "codebase" in lower:
        return "codebase skill"
    if "llmops" in lower:
        return "LLMOps"
    if lower.startswith("backend/app/services/"):
        return "services"
    if lower.startswith("docs/") or lower.startswith("examples/"):
        return "docs/examples"
    if "auth" in lower:
        return "auth"
    if "document" in lower:
        return "documents"
    if "upload" in lower:
        return "upload"
    if "task" in lower:
        return "tasks"
    if "test" in lower:
        return "tests"
    if "readme" in lower or lower.endswith(".md"):
        return "README / docs"
    return "other"


def module_role_for_name(module: str) -> str:
    roles = {
        "frontend": "contains the Next.js dashboard pages, bilingual shell, and API client.",
        "backend API": "exposes FastAPI routers for chat, documents, memory, tools, approvals, codebase, LLMOps, and settings.",
        "services": "holds the internal application logic that powers the Agent workflow.",
        "RAG": "extracts documents, chunks content, retrieves local context, and produces citation metadata.",
        "LLM provider": "selects Mock or Gemini, assembles provider calls, and records fallback behavior.",
        "memory": "stores and retrieves long-term user preferences, project context, tool results, and notes.",
        "tools/approvals": "executes safe tools, pauses risky tools for human approval, and blocks dangerous work.",
        "codebase skill": "indexes repositories, extracts symbols, explains architecture, locates files, and suggests tests.",
        "LLMOps": "records agent runs, model calls, retrievals, tool calls, errors, latency, and fallback state.",
        "docs/examples": "contains product docs, sample documents, and sample repositories for demos.",
        "auth": "handles token validation and current-user resolution.",
        "documents": "extracts document text, chunks content, and returns upload indexing results.",
        "upload": "validates upload filenames and connects upload refresh work to scheduled tasks.",
        "tasks": "defines scheduler-ready task objects and status transitions.",
        "tests": "captures existing behavior for document extraction and chunking.",
        "README / docs": "documents the demo repository and suggested questions.",
        "other": "contains supporting files outside the main demo modules.",
    }
    return roles.get(module, roles["other"])


def module_role_for_path(path: str) -> str:
    return module_role_for_name(module_name_for_path(path))


def build_match_reason(path: str, keywords: list[str], symbols: list[str]) -> str:
    reasons = [f"Module role: {module_role_for_path(path)}"]
    if keywords:
        reasons.append("Matched keywords: " + ", ".join(keywords[:6]) + ".")
    if symbols:
        reasons.append("Matched symbols: " + ", ".join(symbols[:6]) + ".")
    return " ".join(reasons)


def _is_architecture_question(question: str) -> bool:
    lower = question.lower()
    return "architecture" in lower or "how is this repo organized" in lower or "explain this repo" in lower


def _code_citation(match: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": "codebase",
        "title": match["path"],
        "file_path": match["path"],
        "score": match.get("score", 1),
        "metadata": {
            "matched_keywords": match.get("matched_keywords", []),
            "matched_symbols": match.get("matched_symbols", []),
            "module_role": match.get("module_role") or module_role_for_path(match["path"]),
            "match_reason": match.get("match_reason") or f"Module role: {module_role_for_path(match['path'])}",
        },
    }


def _happy_path_suggestion(path: str, symbols: list[str]) -> str:
    if "document" in path.lower() or "upload" in path.lower():
        target = ", ".join(symbols[:2]) if symbols else "the upload flow"
        return f"Add happy-path coverage for {target}: accepted Markdown/TXT input should return extracted text, chunks, and stable metadata."
    return "Add happy-path coverage for the primary public function."


def _edge_case_suggestion(path: str) -> str:
    if "upload" in path.lower():
        return "Add edge-case coverage for rejected extensions, empty filenames, and refresh scheduling payloads."
    if "document" in path.lower():
        return "Add edge-case coverage for empty content, unsupported suffixes, malformed bytes, and multi-chunk long documents."
    return "Add edge-case coverage for empty input, malformed input, and missing records."


def parse_symbols(content: str, language: str) -> list[dict[str, Any]]:
    if language == "python":
        return _parse_python_symbols(content)
    if language in {"typescript", "javascript"}:
        return _parse_js_ts_symbols(content)
    return []


def summarize_file(path: str, content: str, symbols: list[dict[str, Any]]) -> str:
    imports = [symbol["name"] for symbol in symbols if symbol["kind"] == "import"][:5]
    functions = [symbol["name"] for symbol in symbols if symbol["kind"] in {"function", "async_function"}][:5]
    classes = [symbol["name"] for symbol in symbols if symbol["kind"] == "class"][:5]
    parts = [f"{path} contains {len(content.splitlines())} lines."]
    if imports:
        parts.append(f"Imports: {', '.join(imports)}.")
    if classes:
        parts.append(f"Classes: {', '.join(classes)}.")
    if functions:
        parts.append(f"Functions: {', '.join(functions)}.")
    return " ".join(parts)


def _iter_files(root: Path):
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        if path.name in IGNORE_FILES or path.suffix.lower() in {".db", ".sqlite", ".sqlite3", ".log", ".err"}:
            continue
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def test_suggestions_to_markdown(target: str, suggestions: list[dict[str, Any]], target_files: list[dict[str, Any]], existing_tests: list[dict[str, Any]]) -> str:
    lines = [f"# Test Suggestions: {target}", "", "## Suggested tests"]
    for item in suggestions:
        lines.append(f"- `{item['file_path']}`")
        for suggestion in item.get("suggestions", []):
            lines.append(f"  - {suggestion}")
    lines.extend(["", "## Target files"])
    for item in target_files:
        lines.append(f"- `{item['path']}`: {item.get('module_role', '')}")
    lines.extend(["", "## Existing related tests"])
    if not existing_tests:
        lines.append("- None found.")
    for item in existing_tests:
        lines.append(f"- `{item['path']}`")
    return "\n".join(lines)


def _language_for(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".py":
        return "python"
    if suffix in {".ts", ".tsx"}:
        return "typescript"
    if suffix in {".js", ".jsx"}:
        return "javascript"
    if suffix == ".md":
        return "markdown"
    if suffix == ".json":
        return "json"
    return "text"


def _parse_python_symbols(content: str) -> list[dict[str, Any]]:
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []
    symbols: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = getattr(node, "module", None) or ""
            for alias in node.names:
                symbols.append({"name": module + ("." if module else "") + alias.name, "kind": "import", "line_start": node.lineno, "line_end": node.lineno})
        elif isinstance(node, ast.ClassDef):
            symbols.append(
                {
                    "name": node.name,
                    "kind": "class",
                    "line_start": node.lineno,
                    "line_end": getattr(node, "end_lineno", node.lineno),
                    "signature": f"class {node.name}",
                    "docstring": ast.get_docstring(node),
                }
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [arg.arg for arg in node.args.args]
            symbols.append(
                {
                    "name": node.name,
                    "kind": "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function",
                    "line_start": node.lineno,
                    "line_end": getattr(node, "end_lineno", node.lineno),
                    "signature": f"{node.name}({', '.join(args)})",
                    "docstring": ast.get_docstring(node),
                }
            )
    return symbols


JS_TS_PATTERNS = [
    ("class", re.compile(r"(?:export\s+)?class\s+([A-Za-z0-9_]+)")),
    ("function", re.compile(r"(?:export\s+)?function\s+([A-Za-z0-9_]+)\s*\(([^)]*)\)")),
    ("async_function", re.compile(r"(?:export\s+)?async\s+function\s+([A-Za-z0-9_]+)\s*\(([^)]*)\)")),
    ("function", re.compile(r"(?:export\s+)?const\s+([A-Za-z0-9_]+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>")),
    ("import", re.compile(r"import\s+(.+?)\s+from\s+['\"](.+?)['\"]")),
    ("export", re.compile(r"export\s+\{([^}]+)\}")),
]


def _parse_js_ts_symbols(content: str) -> list[dict[str, Any]]:
    symbols: list[dict[str, Any]] = []
    lines = content.splitlines()
    for line_number, line in enumerate(lines, start=1):
        for kind, pattern in JS_TS_PATTERNS:
            for match in pattern.finditer(line):
                if kind == "import":
                    name = match.group(2)
                    signature = match.group(0)
                elif kind == "export":
                    name = match.group(1).strip()
                    signature = match.group(0)
                else:
                    name = match.group(1)
                    signature = match.group(0)
                symbols.append({"name": name, "kind": kind, "line_start": line_number, "line_end": line_number, "signature": signature})
    return symbols
