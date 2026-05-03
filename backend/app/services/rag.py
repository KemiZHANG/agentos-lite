from __future__ import annotations

import mimetypes
import re
import time
import uuid
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.db.database import get_db, json_dumps, json_loads, rows_to_dicts, utc_now
from app.services.chunking import chunk_text
from app.services.embeddings import cosine_similarity, get_embedding_provider


def _embedding_provider():
    return get_embedding_provider()


def extract_text_from_upload(filename: str, content: bytes) -> tuple[str, str]:
    suffix = Path(filename).suffix.lower()
    mime_type = mimetypes.guess_type(filename)[0] or "text/plain"
    if suffix in {".txt", ".md", ".markdown"}:
        return content.decode("utf-8", errors="replace"), mime_type
    if suffix == ".pdf":
        return (
            "[PDF extraction stub] PDF upload was received, but the local MVP only extracts TXT and Markdown. "
            "Install a PDF parser in a future iteration to index this file.",
            "application/pdf",
        )
    return content.decode("utf-8", errors="replace"), mime_type


def ingest_document(name: str, raw_content: bytes, user_id: str | None = None) -> dict[str, Any]:
    user_id = user_id or get_settings().default_user_id
    text, mime_type = extract_text_from_upload(name, raw_content)
    document_id = str(uuid.uuid4())
    now = utc_now()
    chunks = chunk_text(text)
    metadata = {"source": "upload", "extracted_text_length": len(text), "indexed_status": "indexed", "chunk_count": len(chunks)}
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO documents (id, user_id, name, mime_type, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (document_id, user_id, name, mime_type, json_dumps(metadata), now),
        )
        for index, chunk in enumerate(chunks):
            conn.execute(
                """
                INSERT INTO document_chunks
                (id, document_id, chunk_index, content, embedding_json, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    document_id,
                    index,
                    chunk,
                    json_dumps(_embedding_provider().embed(chunk)),
                    json_dumps({"document_name": name}),
                    now,
                ),
            )
    return get_document(document_id)


def delete_document(document_id: str) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))


def list_document_chunks(document_id: str) -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT c.*, d.name AS document_name
            FROM document_chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.document_id = ?
            ORDER BY c.chunk_index ASC
            """,
            (document_id,),
        ).fetchall()
    chunks = rows_to_dicts(rows)
    for chunk in chunks:
        chunk["metadata"] = json_loads(chunk.pop("metadata_json", None), {})
        chunk["embedding"] = json_loads(chunk.pop("embedding_json", None), [])
        chunk["chunk_label"] = f"{chunk['document_name']} chunk {chunk['chunk_index'] + 1}"
        chunk["short_snippet"] = make_snippet(chunk["content"], set())
    return chunks


def reindex_document(document_id: str) -> dict[str, Any]:
    doc = get_document(document_id)
    chunks = list_document_chunks(document_id)
    text = "\n\n".join(chunk["content"] for chunk in chunks)
    new_chunks = chunk_text(text)
    now = utc_now()
    with get_db() as conn:
        conn.execute("DELETE FROM document_chunks WHERE document_id = ?", (document_id,))
        for index, chunk in enumerate(new_chunks):
            conn.execute(
                """
                INSERT INTO document_chunks
                (id, document_id, chunk_index, content, embedding_json, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    document_id,
                    index,
                    chunk,
                    json_dumps(_embedding_provider().embed(chunk)),
                    json_dumps({"document_name": doc["name"], "reindexed": True}),
                    now,
                ),
            )
        metadata = {**doc.get("metadata", {}), "indexed_status": "reindexed", "chunk_count": len(new_chunks), "reindexed_at": now}
        conn.execute("UPDATE documents SET metadata_json = ? WHERE id = ?", (json_dumps(metadata), document_id))
    return get_document(document_id)


def load_sample_documents() -> list[dict[str, Any]]:
    root = Path(__file__).resolve().parents[3]
    sample_dir = root / "examples" / "sample_docs"
    loaded = []
    for path in sample_dir.glob("*"):
        if path.is_file() and path.suffix.lower() in {".txt", ".md", ".markdown"}:
            loaded.append(ingest_document(path.name, path.read_bytes()))
    return loaded


def list_documents() -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT d.*, COUNT(c.id) AS chunk_count
            FROM documents d
            LEFT JOIN document_chunks c ON c.document_id = d.id
            GROUP BY d.id
            ORDER BY d.created_at DESC
            """
        ).fetchall()
    docs = rows_to_dicts(rows)
    for doc in docs:
        doc["metadata"] = json_loads(doc.pop("metadata_json", None), {})
    return docs


def get_document(document_id: str) -> dict[str, Any]:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT d.*, COUNT(c.id) AS chunk_count
            FROM documents d
            LEFT JOIN document_chunks c ON c.document_id = d.id
            WHERE d.id = ?
            GROUP BY d.id
            """,
            (document_id,),
        ).fetchone()
    if row is None:
        raise KeyError(document_id)
    doc = dict(row)
    doc["metadata"] = json_loads(doc.pop("metadata_json", None), {})
    return doc


def retrieve(query: str, limit: int = 5, agent_run_id: str | None = None) -> list[dict[str, Any]]:
    started = time.perf_counter()
    query_embedding = _embedding_provider().embed(query)
    terms = {term.lower() for term in re.findall(r"[a-zA-Z0-9_]+", query) if len(term) > 2}
    requested_title_terms = _requested_document_title_terms(query)
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT c.*, d.name AS document_name
            FROM document_chunks c
            JOIN documents d ON d.id = c.document_id
            """
        ).fetchall()
    scored: list[dict[str, Any]] = []
    for row in rows_to_dicts(rows):
        embedding = json_loads(row["embedding_json"], [])
        semantic = cosine_similarity(query_embedding, embedding)
        document_name = row["document_name"]
        normalized_name = re.sub(r"[^a-zA-Z0-9]+", " ", document_name).lower()
        if requested_title_terms and not all(term in normalized_name for term in requested_title_terms):
            continue
        content_lower = row["content"].lower()
        keyword = sum(1 for term in terms if term in content_lower) * 0.08
        title_match = sum(1 for term in terms if term in normalized_name) * 0.25
        score = semantic + keyword + title_match
        if score > 0:
            scored.append(
                {
                    "chunk_id": row["id"],
                    "document_id": row["document_id"],
                    "document_name": document_name,
                    "chunk_label": f"{document_name} chunk {row['chunk_index'] + 1}",
                    "content": row["content"],
                    "short_snippet": make_snippet(row["content"], terms),
                    "score": round(score, 4),
                    "metadata": json_loads(row["metadata_json"], {}),
                    "debug": {
                        "matched_keywords": sorted(term for term in terms if term in content_lower),
                        "document_title_match_terms": sorted(term for term in terms if term in normalized_name),
                        "semantic_score": round(semantic, 4),
                        "keyword_score": round(keyword, 4),
                        "title_score": round(title_match, 4),
                    },
                }
            )
    scored.sort(key=lambda item: item["score"], reverse=True)
    results = scored[:limit]
    if agent_run_id:
        latency_ms = int((time.perf_counter() - started) * 1000)
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO retrieval_logs
                (id, agent_run_id, source, query, result_count, results_json, latency_ms, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    agent_run_id,
                    "documents",
                    query,
                    len(results),
                    json_dumps(results),
                    latency_ms,
                    utc_now(),
                ),
            )
    return results


def make_snippet(content: str, terms: set[str] | None = None, length: int = 220) -> str:
    clean = " ".join(content.split())
    if not clean:
        return ""
    terms = terms or set()
    start = 0
    for term in terms:
        index = clean.lower().find(term)
        if index >= 0:
            start = max(0, index - 60)
            break
    snippet = clean[start : start + length].strip()
    if start > 0:
        snippet = "..." + snippet
    if start + length < len(clean):
        snippet += "..."
    return snippet


def _requested_document_title_terms(query: str) -> list[str]:
    lower = query.lower()
    known_titles = {
        "product brief": ["product", "brief"],
        "security notes": ["security", "notes"],
    }
    for phrase, terms in known_titles.items():
        if phrase in lower:
            return terms
    match = re.search(r"([a-zA-Z0-9_-]+)\.(md|txt|markdown|pdf)", lower)
    if match:
        return [match.group(1).replace("_", " ").replace("-", " ")]
    return []
