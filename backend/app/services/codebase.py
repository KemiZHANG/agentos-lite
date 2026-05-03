from __future__ import annotations

import ast
import re
import uuid
from pathlib import Path
from typing import Any

from app.db.database import get_db, json_dumps, json_loads, rows_to_dicts, utc_now


IGNORE_DIRS = {"node_modules", ".git", "dist", "build", "__pycache__", ".venv", "venv", ".next"}
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
            scored.append(
                {
                    "file_id": row["id"],
                    "repository_id": row["repository_id"],
                    "path": row["path"],
                    "language": row["language"],
                    "summary": row["summary"],
                    "score": score,
                    "symbols": symbol_by_file.get(row["id"], [])[:10],
                }
            )
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:limit]


def answer_repo_question(question: str, repository_id: str | None = None) -> dict[str, Any]:
    matches = search_codebase(question, repository_id=repository_id)
    citations = [{"source": "codebase", "title": match["path"], "file_path": match["path"], "score": match["score"]} for match in matches]
    if not matches:
        return {"answer": "No indexed files matched. Index the sample repository first.", "citations": []}
    lines = ["I found these repository areas as the strongest evidence:"]
    for match in matches[:5]:
        symbol_names = ", ".join(symbol["name"] for symbol in match.get("symbols", [])[:5])
        detail = f" - {match['path']}: {match['summary']}"
        if symbol_names:
            detail += f" Symbols: {symbol_names}."
        lines.append(detail)
    return {"answer": "\n".join(lines), "citations": citations}


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
    suggestions: list[dict[str, Any]] = []
    for match in matches[:5]:
        symbol_names = [symbol["name"] for symbol in match.get("symbols", [])[:4]]
        suggestions.append(
            {
                "file_path": match["path"],
                "target_symbols": symbol_names,
                "suggestions": [
                    "Add happy-path coverage for the primary function or endpoint.",
                    "Add edge-case coverage for empty input, malformed input, and missing records.",
                    "Assert returned citations/errors are stable enough for UI display.",
                ],
            }
        )
    return {"target": target, "suggestions": suggestions}


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
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


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

