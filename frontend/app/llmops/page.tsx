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
        <Stat label={t("avgLatency")} value={formatLatency(data?.summary.avg_latency_ms ?? 0, true)} />
        <Stat label={t("tools")} value={data?.summary.tool_calls ?? 0} tone="clay" />
        <Stat label={t("retrievals")} value={data?.summary.retrieval_logs ?? 0} />
      </div>
      <div className="mt-4 grid gap-4">
        <AgentRunsTable title={t("agentRuns")} emptyText={t("noRecords")} rows={data?.agent_runs ?? []} />
        <ModelCallsTable title={t("modelCalls")} emptyText={t("noRecords")} rows={data?.model_calls ?? []} />
        <RetrievalsTable title={t("retrievalLogs")} emptyText={t("noRecords")} rows={data?.retrieval_logs ?? []} />
        <ToolCallsTable title={t("toolCalls")} emptyText={t("noRecords")} rows={data?.tool_calls ?? []} />
      </div>
    </>
  );
}

function AgentRunsTable({ title, emptyText, rows }: { title: string; emptyText: string; rows: Record<string, unknown>[] }) {
  return (
    <Panel>
      <h2 className="font-semibold">{title}</h2>
      {rows.length === 0 ? <EmptyState text={emptyText} /> : (
        <DataTable
          headers={["Intent", "Status", "Started", "Completed", "Error"]}
          rows={rows.slice(0, 12).map((row) => [
            text(row.intent),
            text(row.status),
            shortDate(row.started_at),
            shortDate(row.completed_at),
            text(row.error) || "-"
          ])}
        />
      )}
      <RawJson rows={rows} />
    </Panel>
  );
}

function ModelCallsTable({ title, emptyText, rows }: { title: string; emptyText: string; rows: Record<string, unknown>[] }) {
  return (
    <Panel>
      <h2 className="font-semibold">{title}</h2>
      {rows.length === 0 ? <EmptyState text={emptyText} /> : (
        <DataTable
          headers={["Provider", "Model", "Prompt", "Tokens", "Latency", "Fallback", "Status"]}
          rows={rows.slice(0, 12).map((row) => [
            text(row.provider),
            text(row.model),
            `${text(row.prompt_template_name) || "-"} v${text(row.prompt_template_version) || "-"}`,
            `${number(row.input_tokens)} in / ${number(row.output_tokens)} out`,
            formatLatency(row.latency_ms, row.provider === "mock"),
            booleanLabel(row.fallback_used),
            text(row.status),
          ])}
        />
      )}
      <RawJson rows={rows} />
    </Panel>
  );
}

function RetrievalsTable({ title, emptyText, rows }: { title: string; emptyText: string; rows: Record<string, unknown>[] }) {
  return (
    <Panel>
      <h2 className="font-semibold">{title}</h2>
      {rows.length === 0 ? <EmptyState text={emptyText} /> : (
        <DataTable
          headers={["Source", "Query", "Results", "Latency", "Created"]}
          rows={rows.slice(0, 12).map((row) => [
            text(row.source),
            truncate(text(row.query), 72),
            number(row.result_count).toString(),
            formatLatency(row.latency_ms, true),
            shortDate(row.created_at),
          ])}
        />
      )}
      <RawJson rows={rows} />
    </Panel>
  );
}

function ToolCallsTable({ title, emptyText, rows }: { title: string; emptyText: string; rows: Record<string, unknown>[] }) {
  return (
    <Panel>
      <h2 className="font-semibold">{title}</h2>
      {rows.length === 0 ? <EmptyState text={emptyText} /> : (
        <DataTable
          headers={["Tool", "Risk", "Status", "Created", "Error"]}
          rows={rows.slice(0, 12).map((row) => [
            text(row.tool_name),
            text(row.risk_level),
            text(row.status),
            shortDate(row.created_at),
            text(row.error) || "-",
          ])}
        />
      )}
      <RawJson rows={rows} />
    </Panel>
  );
}

function DataTable({ headers, rows }: { headers: string[]; rows: string[][] }) {
  return (
    <div className="mt-3 overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="text-xs uppercase tracking-wide text-ink/45">
          <tr>{headers.map((header) => <th key={header} className="whitespace-nowrap px-2 py-2">{header}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex} className="border-t border-line">
              {row.map((cell, cellIndex) => <td key={cellIndex} className="max-w-[360px] px-2 py-2 align-top text-ink/75">{cell}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RawJson({ rows }: { rows: Record<string, unknown>[] }) {
  return (
    <details className="mt-3 rounded border border-line bg-paper p-3">
      <summary className="cursor-pointer text-xs font-semibold uppercase tracking-wide text-ink/55">Raw JSON</summary>
      <div className="mt-3 max-h-72 overflow-auto">
        {rows.map((row, index) => (
          <pre key={index} className="mb-2 overflow-auto rounded bg-ink p-3 text-xs text-white">{JSON.stringify(row, null, 2)}</pre>
        ))}
      </div>
    </details>
  );
}

function text(value: unknown): string {
  return typeof value === "string" ? value : value === null || value === undefined ? "" : String(value);
}

function number(value: unknown): number {
  return typeof value === "number" ? value : Number(value || 0);
}

function booleanLabel(value: unknown): string {
  return value === true || value === 1 ? "yes" : "no";
}

function truncate(value: string, max: number): string {
  return value.length > max ? `${value.slice(0, max - 3)}...` : value;
}

function shortDate(value: unknown): string {
  const raw = text(value);
  if (!raw) return "-";
  return raw.replace("T", " ").replace("+00:00", "Z").slice(0, 19);
}

function formatLatency(value: unknown, localMock = false): string {
  const ms = number(value);
  if (ms <= 0) return localMock ? "local mock" : "<1ms";
  if (ms < 1) return "<1ms";
  return `${ms}ms`;
}
