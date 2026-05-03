"use client";

import { Send, ShieldAlert } from "lucide-react";
import { FormEvent, useState } from "react";
import { EmptyState, PageHeader, Panel } from "@/components/Ui";
import { useI18n } from "@/components/I18nProvider";
import { api, ChatResponse } from "@/lib/api";

type Message = { role: "user" | "assistant"; content: string; response?: ChatResponse };

export default function ChatPage() {
  const { locale, t } = useI18n();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("Which files are related to document upload?");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!input.trim() || loading) return;
    const userText = input.trim();
    setMessages((current) => [...current, { role: "user", content: userText }]);
    setInput("");
    setLoading(true);
    try {
      const response = await api.post<ChatResponse>("/chat", { message: userText, conversation_id: conversationId, response_language: locale });
      setConversationId(response.conversation_id);
      setMessages((current) => [...current, { role: "assistant", content: response.response, response }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHeader title={t("chatTitle")} subtitle={t("chatSubtitle")} />
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_360px]">
        <Panel className="min-h-[620px]">
          <div className="space-y-4">
            {messages.length === 0 && <EmptyState text={t("chatEmpty")} />}
            {messages.map((message, index) => (
              <div key={index} className={`rounded border p-4 ${message.role === "user" ? "border-line bg-paper" : "border-moss/30 bg-white"}`}>
                <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink/50">{message.role}</div>
                <div className="whitespace-pre-wrap text-sm leading-6">{message.content}</div>
                {message.response?.approval_required && (
                  <div className="mt-3 flex items-center gap-2 rounded border border-clay/40 bg-clay/10 p-2 text-sm text-clay">
                    <ShieldAlert size={16} /> {t("approvalPaused")}
                  </div>
                )}
              </div>
            ))}
          </div>
          <form onSubmit={submit} className="mt-5 flex gap-2">
            <input value={input} onChange={(event) => setInput(event.target.value)} className="focus-ring min-w-0 flex-1 rounded border border-line bg-white px-3 py-2 text-sm" />
            <button className="focus-ring inline-flex items-center gap-2 rounded bg-ink px-4 py-2 text-sm font-medium text-white" disabled={loading}>
              <Send size={16} /> {loading ? t("sending") : t("send")}
            </button>
          </form>
        </Panel>
        <div className="space-y-4">
          <Panel>
            <h2 className="font-semibold">{t("trace")}</h2>
            <div className="mt-3 space-y-2">
              {messages.at(-1)?.response?.trace.map((step) => (
                <div key={step.step} className="rounded border border-line p-2 text-xs">
                  <div className="font-semibold">{step.step} <span className="text-ink/45">/ {step.status}</span></div>
                  <div className="mt-1 text-ink/65">{step.detail}</div>
                </div>
              )) ?? <EmptyState text={t("noTrace")} />}
            </div>
          </Panel>
          <Panel>
            <h2 className="font-semibold">{t("citations")}</h2>
            <div className="mt-3 space-y-2">
              {(messages.at(-1)?.response?.citations.length ?? 0) > 0 ? messages.at(-1)?.response?.citations.map((citation, index) => (
                <div key={`${citation.title}-${index}`} className="rounded border border-line p-2 text-xs">
                  <div className="flex items-start justify-between gap-2">
                    <div className="font-semibold">{citation.source_type === "document" ? citation.source : citation.source_type ?? citation.source}</div>
                    <div className="text-right text-ink/45">{citation.relevance_score !== null && citation.relevance_score !== undefined ? `score ${citation.relevance_score}` : citation.score !== null && citation.score !== undefined ? `score ${citation.score}` : ""}</div>
                  </div>
                  <div className="mt-1 font-medium">{citation.title}</div>
                  <div className="mt-1 text-ink/55">{citation.document_name ?? citation.file_path ?? citation.chunk_id ?? citation.source}</div>
                  {citation.short_snippet && <div className="mt-2 rounded bg-paper p-2 text-ink/70">{citation.short_snippet}</div>}
                </div>
              )) : <EmptyState text={t("noCitations")} />}
            </div>
          </Panel>
          <Panel>
            <h2 className="font-semibold">{t("toolCallsPanel")}</h2>
            <pre className="mt-3 max-h-64 overflow-auto rounded bg-ink p-3 text-xs text-white">{JSON.stringify(messages.at(-1)?.response?.tool_calls ?? [], null, 2)}</pre>
          </Panel>
        </div>
      </div>
    </>
  );
}
