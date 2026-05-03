"use client";

import { Plus, Trash2 } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { EmptyState, PageHeader, Panel } from "@/components/Ui";
import { api } from "@/lib/api";

type Memory = { id: string; type: string; title: string; content: string; updated_at: string };

export default function MemoryPage() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [title, setTitle] = useState("Project preference");
  const [content, setContent] = useState("Prefer runnable MVP decisions over unfinished architecture.");
  const [type, setType] = useState("user_preference");

  function load() {
    api.get<Memory[]>("/memory").then(setMemories).catch(() => setMemories([]));
  }

  useEffect(load, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    await api.post("/memory", { type, title, content });
    load();
  }

  async function remove(id: string) {
    await api.delete(`/memory/${id}`);
    load();
  }

  return (
    <>
      <PageHeader title="Memory Management" subtitle="Create, review, and remove long-term memories used by the agent before answering." />
      <Panel>
        <form onSubmit={submit} className="grid gap-3 md:grid-cols-[180px_1fr_2fr_auto]">
          <select value={type} onChange={(event) => setType(event.target.value)} className="focus-ring rounded border border-line px-3 py-2 text-sm">
            <option value="user_preference">user_preference</option>
            <option value="project_context">project_context</option>
            <option value="tool_result">tool_result</option>
            <option value="note">note</option>
          </select>
          <input value={title} onChange={(event) => setTitle(event.target.value)} className="focus-ring rounded border border-line px-3 py-2 text-sm" />
          <input value={content} onChange={(event) => setContent(event.target.value)} className="focus-ring rounded border border-line px-3 py-2 text-sm" />
          <button className="focus-ring inline-flex items-center justify-center gap-2 rounded bg-ink px-4 py-2 text-sm text-white"><Plus size={16} /> Save</button>
        </form>
      </Panel>
      <div className="mt-4 grid gap-3">
        {memories.length === 0 && <EmptyState text="No memories yet. Add one or ask chat to remember something, then approve the tool call." />}
        {memories.map((memory) => (
          <Panel key={memory.id}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-xs uppercase tracking-wide text-moss">{memory.type}</div>
                <h2 className="mt-1 font-semibold">{memory.title}</h2>
                <p className="mt-2 text-sm leading-6 text-ink/70">{memory.content}</p>
              </div>
              <button onClick={() => remove(memory.id)} className="focus-ring rounded border border-line p-2 text-clay"><Trash2 size={16} /></button>
            </div>
          </Panel>
        ))}
      </div>
    </>
  );
}

