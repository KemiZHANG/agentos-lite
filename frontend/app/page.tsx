"use client";

import { useEffect, useState } from "react";
import { PageHeader, Panel, Stat } from "@/components/Ui";
import { useI18n } from "@/components/I18nProvider";
import { api } from "@/lib/api";

type LlmOps = { summary: { agent_runs: number; model_calls: number; avg_latency_ms: number; tool_calls: number; retrieval_logs: number } };
type Settings = { llm_provider: string; embedding_provider: string; sqlite_path: string; default_user_id: string };

export default function OverviewPage() {
  const { t } = useI18n();
  const [ops, setOps] = useState<LlmOps | null>(null);
  const [settings, setSettings] = useState<Settings | null>(null);

  useEffect(() => {
    api.get<LlmOps>("/llmops").then(setOps).catch(() => setOps(null));
    api.get<Settings>("/settings").then(setSettings).catch(() => setSettings(null));
  }, []);

  return (
    <>
      <PageHeader
        title={t("overviewTitle")}
        subtitle={t("overviewSubtitle")}
      />
      <div className="grid gap-4 md:grid-cols-4">
        <Stat label={t("agentRuns")} value={ops?.summary.agent_runs ?? 0} />
        <Stat label={t("modelCalls")} value={ops?.summary.model_calls ?? 0} tone="aqua" />
        <Stat label={t("toolCalls")} value={ops?.summary.tool_calls ?? 0} />
        <Stat label={t("retrievalLogs")} value={ops?.summary.retrieval_logs ?? 0} tone="clay" />
      </div>
      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Panel>
          <h2 className="text-lg font-semibold">{t("runtime")}</h2>
          <dl className="mt-4 space-y-3 text-sm">
            <div className="flex justify-between gap-4"><dt className="text-ink/55">{t("llmProvider")}</dt><dd>{settings?.llm_provider ?? "mock"}</dd></div>
            <div className="flex justify-between gap-4"><dt className="text-ink/55">{t("embeddingProvider")}</dt><dd>{settings?.embedding_provider ?? "mock"}</dd></div>
            <div className="flex justify-between gap-4"><dt className="text-ink/55">{t("defaultUser")}</dt><dd>{settings?.default_user_id ?? "local-user"}</dd></div>
            <div className="flex justify-between gap-4"><dt className="text-ink/55">{t("sqlitePath")}</dt><dd className="break-all text-right">{settings?.sqlite_path ?? "backend/agentos_lite.db"}</dd></div>
          </dl>
        </Panel>
        <Panel>
          <h2 className="text-lg font-semibold">{t("guardrails")}</h2>
          <div className="mt-4 grid gap-3 text-sm text-ink/70">
            <div className="rounded border border-line p-3">{t("mockProviders")}</div>
            <div className="rounded border border-line p-3">{t("riskyTools")}</div>
            <div className="rounded border border-line p-3">{t("lowConfidence")}</div>
          </div>
        </Panel>
      </div>
      <Panel className="mt-6">
        <h2 className="text-lg font-semibold">Agent workspace flow</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-6">
          {["Ask", "Retrieve context", "Plan", "Use tools", "Require approval", "Monitor runs"].map((step, index) => (
            <div key={step} className="rounded border border-line bg-paper p-3 text-sm">
              <div className="text-xs text-ink/45">Step {index + 1}</div>
              <div className="mt-1 font-semibold">{step}</div>
            </div>
          ))}
        </div>
      </Panel>
      <div className="mt-4 grid gap-4 md:grid-cols-4">
        {[
          ["Knowledge RAG", "Upload documents, retrieve grounded chunks, and answer with citations."],
          ["Long-term Memory", "Store preferences and project context so the agent can adapt over time."],
          ["Codebase Intelligence", "Index repositories, explain architecture, locate files, and suggest tests."],
          ["LLMOps & Guardrails", "Inspect traces, providers, tools, approvals, fallback, and strict citation mode."],
        ].map(([title, body]) => (
          <Panel key={title}>
            <h3 className="font-semibold">{title}</h3>
            <p className="mt-2 text-sm leading-6 text-ink/65">{body}</p>
          </Panel>
        ))}
      </div>
    </>
  );
}
