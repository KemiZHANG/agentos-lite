"use client";

import { Check, X } from "lucide-react";
import { useEffect, useState } from "react";
import { EmptyState, PageHeader, Panel } from "@/components/Ui";
import { api } from "@/lib/api";

type Tool = { name: string; description: string; risk_level: string; enabled: boolean };
type Approval = { id: string; tool_name: string; status: string; reason: string; requested_payload: Record<string, unknown> };
type ToolCall = { id: string; tool_name: string; status: string; risk_level: string; created_at: string };

export default function ToolsPage() {
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
      <PageHeader title="Tools and Approvals" subtitle="Review tool definitions, risk levels, paused approval requests, and execution logs." />
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <h2 className="font-semibold">Tool Registry</h2>
          <div className="mt-3 space-y-2">
            {tools.map((tool) => (
              <div key={tool.name} className="rounded border border-line p-3 text-sm">
                <div className="flex justify-between gap-3">
                  <span className="font-medium">{tool.name}</span>
                  <span className={`rounded px-2 py-1 text-xs ${tool.risk_level === "safe" ? "bg-moss/10 text-moss" : tool.risk_level === "blocked" ? "bg-clay/10 text-clay" : "bg-aqua/10 text-aqua"}`}>{tool.risk_level}</span>
                </div>
                <p className="mt-2 text-ink/65">{tool.description}</p>
              </div>
            ))}
          </div>
        </Panel>
        <Panel>
          <h2 className="font-semibold">Approval Queue</h2>
          <div className="mt-3 space-y-2">
            {approvals.filter((approval) => approval.status === "pending").length === 0 && <EmptyState text="No pending approvals. Ask chat to remember something or generate a report to create one." />}
            {approvals.filter((approval) => approval.status === "pending").map((approval) => (
              <div key={approval.id} className="rounded border border-line p-3 text-sm">
                <div className="font-medium">{approval.tool_name}</div>
                <div className="mt-1 text-ink/60">{approval.reason}</div>
                <pre className="mt-2 max-h-32 overflow-auto rounded bg-paper p-2 text-xs">{JSON.stringify(approval.requested_payload, null, 2)}</pre>
                <div className="mt-3 flex gap-2">
                  <button onClick={() => decide(approval.id, "approved")} className="focus-ring inline-flex items-center gap-2 rounded bg-moss px-3 py-2 text-xs text-white"><Check size={14} /> Approve</button>
                  <button onClick={() => decide(approval.id, "rejected")} className="focus-ring inline-flex items-center gap-2 rounded border border-clay px-3 py-2 text-xs text-clay"><X size={14} /> Reject</button>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      </div>
      <Panel className="mt-4">
        <h2 className="font-semibold">Tool Call Log</h2>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase tracking-wide text-ink/45"><tr><th className="py-2">Tool</th><th>Status</th><th>Risk</th><th>Created</th></tr></thead>
            <tbody>
              {calls.map((call) => (
                <tr key={call.id} className="border-t border-line"><td className="py-2">{call.tool_name}</td><td>{call.status}</td><td>{call.risk_level}</td><td>{call.created_at}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </>
  );
}

