"use client";

import { Upload } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { EmptyState, PageHeader, Panel } from "@/components/Ui";
import { useI18n } from "@/components/I18nProvider";
import { api } from "@/lib/api";

type Document = { id: string; name: string; mime_type: string; chunk_count: number; created_at: string };

export default function DocumentsPage() {
  const { t } = useI18n();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [file, setFile] = useState<File | null>(null);

  function load() {
    api.get<Document[]>("/documents").then(setDocuments).catch(() => setDocuments([]));
  }

  useEffect(load, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    await api.post("/documents/upload", form);
    setFile(null);
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
        </form>
      </Panel>
      <Panel className="mt-4">
        <h2 className="font-semibold">{t("knowledgeBase")}</h2>
        <div className="mt-3 space-y-2">
          {documents.length === 0 && <EmptyState text={t("noDocuments")} />}
          {documents.map((doc) => (
            <div key={doc.id} className="grid gap-2 rounded border border-line p-3 text-sm md:grid-cols-[1fr_160px_140px]">
              <div className="font-medium">{doc.name}</div>
              <div className="text-ink/55">{doc.mime_type}</div>
              <div className="text-ink/55">{doc.chunk_count} chunks</div>
            </div>
          ))}
        </div>
      </Panel>
    </>
  );
}
