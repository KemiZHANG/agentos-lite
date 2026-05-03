"use client";

import { Check, X } from "lucide-react";
import { useEffect, useState } from "react";
import { EmptyState, PageHeader, Panel } from "@/components/Ui";
import { useI18n } from "@/components/I18nProvider";
import { api } from "@/lib/api";

type Tool = { name: string; description: string; risk_level: string; enabled: boolean; input_schema?: Record<string, unknown> };
type Approval = { id: string; tool_name: string; status: string; risk_level: string; reason: string; requested_payload: Record<string, unknown>; created_at: string; reviewer_note?: string };
type ToolCall = { id: string; tool_name: string; status: string; risk_level: string; created_at: string; input?: Record<string, unknown>; output?: unknown; error?: string };

export default function ToolsPage() {
  const { t } = useI18n();
  const [tools, setTools] = useState<Tool[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [calls, setCalls] = useState<ToolCall[]>([]);

  function load() {
    api.get<Tool[]>("/tools").then(setTools).catch(() => setTools([]));
    api.get<Approval[]>("/approvals").then(setApprovals).catch(() => setApprovals([]));
    api.get<ToolCall[]>("/tools/calls").then(setCalls).catch(() => setCalls([]));
  }

  useEffect(load, []);

  async function decide(id: string, status: "approved" | "rejected") {
    await api.post(`/approvals/${id}/decision`, { status, reviewer_note: "Reviewed in MVP UI" });
    load();
  }

  return (
    <>
      <PageHeader title={t("toolsTitle")} subtitle={t("toolsSubtitle")} />
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <h2 className="font-semibold">{t("toolRegistry")}</h2>
          <div className="mt-3 space-y-2">
            {tools.map((tool) => (
              <div key={tool.name} className="rounded border border-line p-3 text-sm">
                <div className="flex justify-between gap-3">
                  <span className="font-medium">{tool.name}</span>
                  <span className={`rounded px-2 py-1 text-xs ${riskClass(tool.risk_level)}`}>{tool.risk_level}</span>
                </div>
                <p className="mt-2 text-ink/65">{tool.description}</p>
                <div className="mt-2 rounded bg-paper p-2 text-xs text-ink/55">schema: {schemaSummary(tool.input_schema)}</div>
                <div className="mt-1 text-xs text-ink/45">enabled: {tool.enabled ? "yes" : "no"}</div>
              </div>
            ))}
          </div>
        </Panel>
        <Panel>
          <h2 className="font-semibold">{t("approvalQueue")}</h2>
          <div className="mt-3 space-y-2">
            {approvals.filter((approval) => approval.status === "pending").length === 0 && <EmptyState text={t("noApprovals")} />}
            {approvals.filter((approval) => approval.status === "pending").map((approval) => (
              <div key={approval.id} className="rounded border border-line p-3 text-sm">
                <div className="font-medium">{approval.tool_name}</div>
                <div className="mt-1 text-ink/60">{approval.reason} / {approval.risk_level} / {approval.created_at}</div>
                <pre className="mt-2 max-h-32 overflow-auto rounded bg-paper p-2 text-xs">{JSON.stringify(approval.requested_payload, null, 2)}</pre>
                <div className="mt-3 flex gap-2">
                  <button onClick={() => decide(approval.id, "approved")} className="focus-ring inline-flex items-center gap-2 rounded bg-moss px-3 py-2 text-xs text-white"><Check size={14} /> {t("approve")}</button>
                  <button onClick={() => decide(approval.id, "rejected")} className="focus-ring inline-flex items-center gap-2 rounded border border-clay px-3 py-2 text-xs text-clay"><X size={14} /> {t("reject")}</button>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      </div>
      <Panel className="mt-4">
        <h2 className="font-semibold">Approval history</h2>
        <div className="mt-3 grid gap-2">
          {approvals.filter((approval) => approval.status !== "pending").map((approval) => (
            <div key={approval.id} className="rounded border border-line p-3 text-sm">
              <div className="font-medium">{approval.tool_name} / {approval.status}</div>
              <div className="mt-1 text-ink/60">{approval.reason}</div>
            </div>
          ))}
        </div>
      </Panel>
      <Panel className="mt-4">
        <h2 className="font-semibold">{t("toolCallLog")}</h2>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase tracking-wide text-ink/45"><tr><th className="py-2">Tool</th><th>Status</th><th>Risk</th><th>Input</th><th>Output/Error</th><th>Created</th></tr></thead>
            <tbody>
              {calls.map((call) => (
                <tr key={call.id} className="border-t border-line"><td className="py-2">{call.tool_name}</td><td>{call.status}</td><td>{call.risk_level}</td><td>{summarize(call.input)}</td><td>{call.error || summarize(call.output)}</td><td>{call.created_at}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </>
  );
}

function riskClass(risk: string): string {
  if (risk === "safe") return "bg-moss/10 text-moss";
  if (risk === "blocked") return "bg-clay/10 text-clay";
  return "bg-aqua/10 text-aqua";
}

function schemaSummary(schema?: Record<string, unknown>): string {
  const props = schema?.properties;
  if (!props || typeof props !== "object") return "none";
  return Object.keys(props).join(", ");
}

function summarize(value: unknown): string {
  if (!value) return "-";
  const text = typeof value === "string" ? value : JSON.stringify(value);
  return text.length > 90 ? `${text.slice(0, 87)}...` : text;
}
