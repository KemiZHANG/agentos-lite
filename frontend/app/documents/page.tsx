"use client";

import { Eye, RefreshCw, Trash2, Upload } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { EmptyState, PageHeader, Panel } from "@/components/Ui";
import { useI18n } from "@/components/I18nProvider";
import { api } from "@/lib/api";

type Document = { id: string; name: string; mime_type: string; chunk_count: number; created_at: string; metadata?: Record<string, unknown> };
type Chunk = { id: string; chunk_label: string; short_snippet: string; content: string };

export default function DocumentsPage() {
  const { t } = useI18n();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [chunks, setChunks] = useState<Record<string, Chunk[]>>({});
  const [uploadResult, setUploadResult] = useState<Document | null>(null);

  function load() {
    api.get<Document[]>("/documents").then(setDocuments).catch(() => setDocuments([]));
  }

  useEffect(load, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    const result = await api.post<Document>("/documents/upload", form);
    setUploadResult(result);
    setFile(null);
    load();
  }

  async function toggleChunks(documentId: string) {
    if (chunks[documentId]) {
      setChunks((current) => {
        const next = { ...current };
        delete next[documentId];
        return next;
      });
      return;
    }
    setChunks((current) => ({ ...current, [documentId]: [] }));
    const result = await api.get<Chunk[]>(`/documents/${documentId}/chunks`);
    setChunks((current) => ({ ...current, [documentId]: result }));
  }

  async function remove(documentId: string) {
    await api.delete(`/documents/${documentId}`);
    load();
  }

  async function reindex(documentId: string) {
    await api.post(`/documents/${documentId}/reindex`);
    load();
  }

  async function loadSamples() {
    await api.post("/documents/sample-docs/load");
    load();
  }

  return (
    <>
      <PageHeader title={t("documentsTitle")} subtitle={t("documentsSubtitle")} />
      <Panel>
        <form onSubmit={submit} className="flex flex-col gap-3 md:flex-row md:items-center">
          <input type="file" accept=".txt,.md,.markdown,.pdf" onChange={(event) => setFile(event.target.files?.[0] ?? null)} className="focus-ring flex-1 rounded border border-line bg-white px-3 py-2 text-sm" />
          <button className="focus-ring inline-flex items-center justify-center gap-2 rounded bg-ink px-4 py-2 text-sm font-medium text-white">
            <Upload size={16} /> {t("upload")}
          </button>
          <button type="button" onClick={loadSamples} className="focus-ring rounded border border-line px-4 py-2 text-sm">Load sample docs</button>
        </form>
        {uploadResult && (
          <div className="mt-3 rounded border border-line bg-paper p-3 text-sm text-ink/70">
            Uploaded {uploadResult.name}: {String(uploadResult.metadata?.extracted_text_length ?? 0)} chars / {uploadResult.chunk_count} chunks / {String(uploadResult.metadata?.indexed_status ?? "indexed")}
          </div>
        )}
      </Panel>
      <Panel className="mt-4">
        <h2 className="font-semibold">{t("knowledgeBase")}</h2>
        <div className="mt-3 space-y-2">
          {documents.length === 0 && <EmptyState text={t("noDocuments")} />}
          {documents.map((doc) => (
            <div key={doc.id} className="rounded border border-line p-3 text-sm">
              <div className="grid gap-2 md:grid-cols-[1fr_150px_120px_180px] md:items-center">
                <div className="font-medium">{doc.name}</div>
                <div className="text-ink/55">{doc.mime_type}</div>
                <div className="text-ink/55">{doc.chunk_count} chunks</div>
                <div className="flex gap-2">
                  <button onClick={() => toggleChunks(doc.id)} className="focus-ring rounded border border-line p-2"><Eye size={15} /></button>
                  <button onClick={() => reindex(doc.id)} className="focus-ring rounded border border-line p-2"><RefreshCw size={15} /></button>
                  <button onClick={() => remove(doc.id)} className="focus-ring rounded border border-line p-2 text-clay"><Trash2 size={15} /></button>
                </div>
              </div>
              <div className="mt-1 text-xs text-ink/45">{doc.created_at}</div>
              {chunks[doc.id] && (
                <div className="mt-3 grid gap-2">
                  {chunks[doc.id].length === 0 && <div className="text-xs text-ink/50">Loading chunks...</div>}
                  {chunks[doc.id].map((chunk) => (
                    <div key={chunk.id} className="rounded bg-paper p-2 text-xs">
                      <div className="font-semibold">{chunk.chunk_label}</div>
                      <div className="mt-1 text-ink/65">{chunk.short_snippet}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </Panel>
    </>
  );
}
