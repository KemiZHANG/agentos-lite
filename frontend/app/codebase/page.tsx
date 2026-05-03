"use client";

import { GitBranch, Search } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { EmptyState, PageHeader, Panel } from "@/components/Ui";
import { api } from "@/lib/api";

type Repository = { id: string; name: string; root_path: string; file_count: number; symbol_count: number };
type QuestionResult = { answer: string; citations: { title: string; file_path?: string; score?: number }[] };

export default function CodebasePage() {
  const [repos, setRepos] = useState<Repository[]>([]);
  const [question, setQuestion] = useState("Explain the architecture of this repo.");
  const [result, setResult] = useState<QuestionResult | null>(null);
  const [indexing, setIndexing] = useState(false);

  function load() {
    api.get<Repository[]>("/codebase/repositories").then(setRepos).catch(() => setRepos([]));
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
        title="Codebase Intelligence"
        subtitle="Index a repository, extract Python AST and TS/JS regex symbols, ask architecture questions, locate relevant files, and generate test suggestions."
        actions={<button onClick={indexSample} className="focus-ring inline-flex items-center gap-2 rounded bg-ink px-4 py-2 text-sm text-white"><GitBranch size={16} /> {indexing ? "Indexing" : "Index sample repo"}</button>}
      />
      <div className="grid gap-4 lg:grid-cols-[380px_1fr]">
        <Panel>
          <h2 className="font-semibold">Indexed repositories</h2>
          <div className="mt-3 space-y-2">
            {repos.length === 0 && <EmptyState text="Index examples/sample_repo to enable demo codebase questions." />}
            {repos.map((repo) => (
              <div key={repo.id} className="rounded border border-line p-3 text-sm">
                <div className="font-medium">{repo.name}</div>
                <div className="mt-1 break-all text-ink/55">{repo.root_path}</div>
                <div className="mt-2 text-ink/65">{repo.file_count} files · {repo.symbol_count} symbols</div>
              </div>
            ))}
          </div>
        </Panel>
        <Panel>
          <form onSubmit={ask} className="flex gap-2">
            <input value={question} onChange={(event) => setQuestion(event.target.value)} className="focus-ring min-w-0 flex-1 rounded border border-line px-3 py-2 text-sm" />
            <button className="focus-ring inline-flex items-center gap-2 rounded bg-moss px-4 py-2 text-sm text-white"><Search size={16} /> Ask</button>
          </form>
          <div className="mt-4 rounded border border-line bg-paper p-4 text-sm leading-6">
            {result ? <div className="whitespace-pre-wrap">{result.answer}</div> : "Try: Where is authentication handled? Which files are related to document upload? Generate test suggestions for this function."}
          </div>
          <div className="mt-4 grid gap-2">
            {result?.citations.map((citation, index) => (
              <div key={`${citation.title}-${index}`} className="rounded border border-line p-2 text-xs">
                <span className="font-semibold">{citation.file_path ?? citation.title}</span>
                <span className="ml-2 text-ink/50">score {citation.score}</span>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </>
  );
}

