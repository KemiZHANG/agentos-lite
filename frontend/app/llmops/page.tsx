"use client";

import { useEffect, useState } from "react";
import { EmptyState, PageHeader, Panel, Stat } from "@/components/Ui";
import { useI18n } from "@/components/I18nProvider";
import { api } from "@/lib/api";

type Dashboard = {
  summary: { agent_runs: number; model_calls: number; avg_latency_ms: number; tool_calls: number; retrieval_logs: number };
  agent_runs: Record<string, unknown>[];
  model_calls: Record<string, unknown>[];
  retrieval_logs: Record<string, unknown>[];
  tool_calls: Record<string, unknown>[];
};

export default function LlmOpsPage() {
  const { t } = useI18n();
  const [data, setData] = useState<Dashboard | null>(null);
  useEffect(() => {
    api.get<Dashboard>("/llmops").then(setData).catch(() => setData(null));
  }, []);
  return (
    <>
      <PageHeader title={t("llmopsTitle")} subtitle={t("llmopsSubtitle")} />
      <div className="grid gap-4 md:grid-cols-5">
        <Stat label={t("runs")} value={data?.summary.agent_runs ?? 0} />
        <Stat label={t("calls")} value={data?.summary.model_calls ?? 0} tone="aqua" />
        <Stat label={t("avgLatency")} value={`${data?.summary.avg_latency_ms ?? 0} ms`} />
        <Stat label={t("tools")} value={data?.summary.tool_calls ?? 0} tone="clay" />
        <Stat label={t("retrievals")} value={data?.summary.retrieval_logs ?? 0} />
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <LogPanel title={t("agentRuns")} emptyText={t("noRecords")} rows={data?.agent_runs ?? []} />
        <LogPanel title={t("modelCalls")} emptyText={t("noRecords")} rows={data?.model_calls ?? []} />
        <LogPanel title={t("retrievalLogs")} emptyText={t("noRecords")} rows={data?.retrieval_logs ?? []} />
        <LogPanel title={t("toolCalls")} emptyText={t("noRecords")} rows={data?.tool_calls ?? []} />
      </div>
    </>
  );
}

function LogPanel({ title, emptyText, rows }: { title: string; emptyText: string; rows: Record<string, unknown>[] }) {
  return (
    <Panel>
      <h2 className="font-semibold">{title}</h2>
      <div className="mt-3 max-h-80 overflow-auto">
        {rows.length === 0 && <EmptyState text={emptyText} />}
        {rows.map((row, index) => (
          <pre key={index} className="mb-2 overflow-auto rounded bg-ink p-3 text-xs text-white">{JSON.stringify(row, null, 2)}</pre>
        ))}
      </div>
    </Panel>
  );
}
