# RAG Pipeline

1. Upload TXT or Markdown through `/documents/upload`.
2. Extract text locally. PDF currently returns a clear extraction stub.
3. Normalize and chunk text.
4. Generate deterministic mock embeddings.
5. Store documents and chunks in SQLite.
6. Retrieve using a blend of cosine similarity over mock embeddings and keyword overlap.
7. Boost or filter by document title when the user mentions a title such as `product brief`.
8. Attach document name, chunk label, snippet, matched keyword debug info, score, and metadata as citations.

If a document-focused answer has no citation, the agent marks confidence low.

`STRICT_CITATION_MODE=true` keeps document answers citation-first. Real embedding provider abstractions exist, but Phase 2 still uses local deterministic retrieval by default.
