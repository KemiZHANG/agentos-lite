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
from app.services.embeddings import MockEmbeddingProvider, cosine_similarity


embedding_provider = MockEmbeddingProvider()


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
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO documents (id, user_id, name, mime_type, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (document_id, user_id, name, mime_type, json_dumps({"source": "upload"}), now),
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
                    json_dumps(embedding_provider.embed(chunk)),
                    json_dumps({"document_name": name}),
                    now,
                ),
            )
    return get_document(document_id)


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
    query_embedding = embedding_provider.embed(query)
    terms = {term.lower() for term in re.findall(r"[a-zA-Z0-9_]+", query) if len(term) > 2}
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
