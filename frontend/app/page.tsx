"use client";

import { useEffect, useState } from "react";
import { PageHeader, Panel, Stat } from "@/components/Ui";
import { api } from "@/lib/api";

type LlmOps = { summary: { agent_runs: number; model_calls: number; avg_latency_ms: number; tool_calls: number; retrieval_logs: number } };
type Settings = { llm_provider: string; embedding_provider: string; sqlite_path: string; default_user_id: string };

export default function OverviewPage() {
  const [ops, setOps] = useState<LlmOps | null>(null);
  const [settings, setSettings] = useState<Settings | null>(null);

  useEffect(() => {
    api.get<LlmOps>("/llmops").then(setOps).catch(() => setOps(null));
    api.get<Settings>("/settings").then(setSettings).catch(() => setSettings(null));
  }, []);

  return (
    <>
      <PageHeader
        title="Overview"
        subtitle="A local-first AI workspace with chat, RAG citations, long-term memory, human approvals, tool execution logs, scheduler-ready tasks, and codebase intelligence."
      />
      <div className="grid gap-4 md:grid-cols-4">
        <Stat label="Agent runs" value={ops?.summary.agent_runs ?? 0} />
        <Stat label="Model calls" value={ops?.summary.model_calls ?? 0} tone="aqua" />
        <Stat label="Tool calls" value={ops?.summary.tool_calls ?? 0} />
        <Stat label="Retrieval logs" value={ops?.summary.retrieval_logs ?? 0} tone="clay" />
      </div>
      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Panel>
          <h2 className="text-lg font-semibold">Runtime</h2>
          <dl className="mt-4 space-y-3 text-sm">
            <div className="flex justify-between gap-4"><dt className="text-ink/55">LLM provider</dt><dd>{settings?.llm_provider ?? "mock"}</dd></div>
            <div className="flex justify-between gap-4"><dt className="text-ink/55">Embedding provider</dt><dd>{settings?.embedding_provider ?? "mock"}</dd></div>
            <div className="flex justify-between gap-4"><dt className="text-ink/55">Default user</dt><dd>{settings?.default_user_id ?? "local-user"}</dd></div>
            <div className="flex justify-between gap-4"><dt className="text-ink/55">SQLite path</dt><dd className="break-all text-right">{settings?.sqlite_path ?? "backend/agentos_lite.db"}</dd></div>
          </dl>
        </Panel>
        <Panel>
          <h2 className="text-lg font-semibold">MVP guardrails</h2>
          <div className="mt-4 grid gap-3 text-sm text-ink/70">
            <div className="rounded border border-line p-3">MockLLMProvider and MockEmbeddingProvider run without secrets.</div>
            <div className="rounded border border-line p-3">Risky tools pause for approval; dangerous operations are blocked.</div>
            <div className="rounded border border-line p-3">Document answers without citations are marked low confidence.</div>
          </div>
        </Panel>
      </div>
    </>
  );
}

