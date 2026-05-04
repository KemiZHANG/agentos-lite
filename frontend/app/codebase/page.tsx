"use client";

import { GitBranch, Search } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { EmptyState, PageHeader, Panel } from "@/components/Ui";
import { useI18n } from "@/components/I18nProvider";
import { api } from "@/lib/api";

type Repository = { id: string; name: string; root_path: string; file_count: number; symbol_count: number };
type QuestionResult = { answer: string; citations: { title: string; file_path?: string; score?: number; metadata?: Record<string, unknown> }[] };
type RepoMap = { total_files: number; symbols: number; languages: Record<string, number>; main_modules: Record<string, number>; top_directories: Record<string, number>; indexed_time?: string };

export default function CodebasePage() {
  const { t } = useI18n();
  const [repos, setRepos] = useState<Repository[]>([]);
  const [question, setQuestion] = useState("Explain the architecture of this repo.");
  const [result, setResult] = useState<QuestionResult | null>(null);
  const [repoMap, setRepoMap] = useState<RepoMap | null>(null);
  const [indexing, setIndexing] = useState(false);

  function load() {
    api.get<Repository[]>("/codebase/repositories").then(setRepos).catch(() => setRepos([]));
    api.get<RepoMap>("/codebase/repo-map").then(setRepoMap).catch(() => setRepoMap(null));
  }

  async function indexCurrent() {
    setIndexing(true);
    try {
      await api.post("/codebase/index-current");
      load();
    } finally {
      setIndexing(false);
    }
  }

  useEffect(load, []);

  async function indexSample() {
    setIndexing(true);
    try {
      await api.post("/codebase/index", { name: "sample_repo", root_path: "examples/sample_repo" });
      load();
    } finally {
      setIndexing(false);
    }
  }

  async function ask(event: FormEvent) {
    event.preventDefault();
    const response = await api.post<QuestionResult>("/codebase/question", { question });
    setResult(response);
  }

  return (
    <>
      <PageHeader
        title={t("codebaseTitle")}
        subtitle={t("codebaseSubtitle")}
        actions={<div className="flex gap-2"><button onClick={indexSample} className="focus-ring inline-flex items-center gap-2 rounded bg-ink px-4 py-2 text-sm text-white"><GitBranch size={16} /> {indexing ? t("indexing") : t("indexSampleRepo")}</button><button onClick={indexCurrent} className="focus-ring rounded border border-line px-4 py-2 text-sm">Index AgentOS Lite repo</button></div>}
      />
      <div className="grid gap-4 lg:grid-cols-[380px_1fr]">
        <Panel>
          <h2 className="font-semibold">{t("indexedRepos")}</h2>
          <div className="mt-3 space-y-2">
            {repos.length === 0 && (
              <EmptyState text={t("noRepos")}>
                <button type="button" onClick={indexSample} disabled={indexing} className="focus-ring rounded bg-ink px-3 py-2 text-sm font-medium text-white disabled:opacity-60">
                  {indexing ? t("indexing") : t("indexSampleRepo")}
                </button>
              </EmptyState>
            )}
            {repos.map((repo) => (
              <div key={repo.id} className="rounded border border-line p-3 text-sm">
                <div className="font-medium">{repo.name}</div>
                <div className="mt-1 break-all text-ink/55">{displayRepoPath(repo.root_path)}</div>
                <div className="mt-2 text-ink/65">{repo.file_count} files / {repo.symbol_count} symbols</div>
              </div>
            ))}
          </div>
          {repoMap && (
            <div className="mt-4 rounded border border-line bg-paper p-3 text-xs">
              <div className="font-semibold">Repo map</div>
              <div className="mt-2">{repoMap.total_files} files / {repoMap.symbols} symbols</div>
              <div className="mt-2">Languages: {Object.entries(repoMap.languages).map(([k, v]) => `${k} ${v}`).join(", ") || "-"}</div>
              <div className="mt-2">Modules: {Object.entries(repoMap.main_modules).map(([k, v]) => `${k} ${v}`).join(", ") || "-"}</div>
              <div className="mt-2">Top dirs: {Object.entries(repoMap.top_directories).map(([k, v]) => `${k} ${v}`).join(", ") || "-"}</div>
            </div>
          )}
        </Panel>
        <Panel>
          <form onSubmit={ask} className="flex gap-2">
            <input value={question} onChange={(event) => setQuestion(event.target.value)} className="focus-ring min-w-0 flex-1 rounded border border-line px-3 py-2 text-sm" />
            <button className="focus-ring inline-flex items-center gap-2 rounded bg-moss px-4 py-2 text-sm text-white"><Search size={16} /> {t("ask")}</button>
          </form>
          <div className="mt-4 rounded border border-line bg-paper p-4 text-sm leading-6">
            {result ? <div className="whitespace-pre-wrap">{result.answer}</div> : t("codebasePrompt")}
          </div>
          {result && <button onClick={() => downloadMarkdown(question, result.answer)} className="focus-ring mt-3 rounded border border-line px-3 py-2 text-sm">Export answer as Markdown</button>}
          <div className="mt-4 grid gap-2">
            {result?.citations.map((citation, index) => (
              <div key={`${citation.title}-${index}`} className="rounded border border-line p-2 text-xs">
                <span className="font-semibold">{citation.file_path ?? citation.title}</span>
                <span className="ml-2 text-ink/50">score {citation.score}</span>
                <div className="mt-1 text-ink/60">{metadataText(citation.metadata, "module_role")}</div>
                <div className="mt-1 text-ink/55">{metadataText(citation.metadata, "match_reason")}</div>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </>
  );
}

function downloadMarkdown(question: string, answer: string) {
  const blob = new Blob([`# ${question}\n\n${answer}\n`], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "agentos-codebase-answer.md";
  link.click();
  URL.revokeObjectURL(url);
}

function metadataText(metadata: Record<string, unknown> | undefined, key: string): string {
  const value = metadata?.[key];
  if (Array.isArray(value)) return value.join(", ");
  return typeof value === "string" ? value : "";
}

function displayRepoPath(path: string): string {
  const normalized = path.replace(/\\/g, "/");
  const marker = "agentos-lite/";
  const markerIndex = normalized.toLowerCase().indexOf(marker);
  if (markerIndex >= 0) return normalized.slice(markerIndex);
  const parts = normalized.split("/").filter(Boolean);
  return parts.slice(-2).join("/") || path;
}
