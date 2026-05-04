"use client";

import { Plus } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { EmptyState, PageHeader, Panel } from "@/components/Ui";
import { useI18n } from "@/components/I18nProvider";
import { api } from "@/lib/api";

type Settings = Record<string, string | boolean | number | null>;
type Prompt = { id: string; name: string; version: string; task_type: string; active: number; content: string };
type ScheduledTask = { id: string; name: string; description: string; schedule: string; status: string };
type ProviderHealth = { provider: string; model: string; key_configured: boolean; status: string; latency_ms: number; error?: string | null; fallback_available: boolean; fallback_used: boolean; fallback_reason?: string | null; remaining_calls?: number | null };

export default function SettingsPage() {
  const { t } = useI18n();
  const [settings, setSettings] = useState<Settings>({});
  const [settingsError, setSettingsError] = useState<string | null>(null);
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [tasks, setTasks] = useState<ScheduledTask[]>([]);
  const [providerHealth, setProviderHealth] = useState<ProviderHealth | null>(null);
  const [testingProvider, setTestingProvider] = useState(false);
  const [taskName, setTaskName] = useState("Weekly knowledge refresh");
  const [schedule, setSchedule] = useState("weekly:Monday 09:00");

  function load() {
    api.get<Settings>("/settings").then((value) => {
      setSettings(value);
      setSettingsError(null);
    }).catch((error) => {
      setSettings({});
      setSettingsError(error instanceof Error ? error.message : "Backend unavailable");
    });
    api.get<Prompt[]>("/settings/prompts").then(setPrompts).catch(() => setPrompts([]));
    api.get<ScheduledTask[]>("/settings/scheduled-tasks").then(setTasks).catch(() => setTasks([]));
  }

  useEffect(load, []);

  async function createTask(event: FormEvent) {
    event.preventDefault();
    await api.post("/settings/scheduled-tasks", { name: taskName, description: "Scheduler-ready placeholder task", schedule, status: "pending", payload: { integration: "future APScheduler or Celery beat" } });
    load();
  }

  async function testProvider() {
    setTestingProvider(true);
    try {
      setProviderHealth(await api.get<ProviderHealth>("/settings/provider-health"));
    } catch (error) {
      setProviderHealth({ provider: "unknown", model: "-", key_configured: false, status: "failed", latency_ms: 0, error: error instanceof Error ? error.message : "Provider test failed", fallback_available: false, fallback_used: false });
    } finally {
      setTestingProvider(false);
    }
  }

  return (
    <>
      <PageHeader title={t("settingsTitle")} subtitle={t("settingsSubtitle")} />
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <h2 className="font-semibold">{t("runtime")}</h2>
          {settingsError && (
            <div className="mt-3 rounded border border-clay/40 bg-clay/10 p-3 text-sm text-clay">
              Backend unavailable. Check NEXT_PUBLIC_API_BASE_URL. {settingsError}
            </div>
          )}
          <div className="mt-3 rounded border border-line bg-paper p-3 text-sm">
            <div className="text-xs uppercase tracking-wide text-ink/45">Current mode</div>
            <div className="mt-1 text-lg font-semibold">{modeLabel(settings.current_mode)}</div>
            <div className="mt-1 text-ink/60">
              Provider {formatSettingValue(settings.llm_provider)} / model {formatSettingValue(settings.active_model)}
            </div>
            {settings.demo_mode === true && (
              <div className="mt-2 rounded border border-aqua/40 bg-aqua/10 p-2 text-xs text-ink/70">
                Hosted Demo Mode: Gemini calls are limited to {formatSettingValue(settings.max_calls_per_day)} per user per day.
                After that, local mock fallback is used. Remaining: {formatSettingValue(settings.current_session_remaining_calls)}.
              </div>
            )}
          </div>
          <button onClick={testProvider} className="focus-ring mt-3 rounded bg-moss px-3 py-2 text-sm text-white">{testingProvider ? "Testing..." : "Test Provider"}</button>
          {providerHealth && (
            <div className="mt-3 rounded border border-line bg-paper p-3 text-sm">
              <div className="font-medium">{providerHealth.provider} / {providerHealth.model}</div>
              <div className="mt-1 text-ink/65">status: {providerHealth.status} / key: {providerHealth.key_configured ? "yes" : "no"} / latency: {formatLatency(providerHealth.latency_ms)}</div>
              <div className="mt-1 text-ink/65">fallback: {providerHealth.fallback_used ? "used" : providerHealth.fallback_available ? "available" : "off"} {providerHealth.fallback_reason ? `/ ${providerHealth.fallback_reason}` : ""}</div>
              {providerHealth.remaining_calls !== null && providerHealth.remaining_calls !== undefined && <div className="mt-1 text-ink/65">remaining demo calls: {providerHealth.remaining_calls}</div>}
              {providerHealth.error && <div className="mt-2 text-clay">{providerHealth.error}</div>}
            </div>
          )}
          <dl className="mt-3 space-y-2 text-sm">
            {Object.entries(settings).map(([key, value]) => (
              <div key={key} className="flex justify-between gap-4 border-b border-line py-2">
                <dt className="text-ink/55">{key}</dt>
                <dd className="break-all text-right">{formatSettingValue(value)}</dd>
              </div>
            ))}
          </dl>
        </Panel>
        <Panel>
          <h2 className="font-semibold">{t("schedulerTasks")}</h2>
          <form onSubmit={createTask} className="mt-3 grid gap-2 md:grid-cols-[1fr_1fr_auto]">
            <input value={taskName} onChange={(event) => setTaskName(event.target.value)} className="focus-ring rounded border border-line px-3 py-2 text-sm" />
            <input value={schedule} onChange={(event) => setSchedule(event.target.value)} className="focus-ring rounded border border-line px-3 py-2 text-sm" />
            <button className="focus-ring inline-flex items-center justify-center gap-2 rounded bg-ink px-4 py-2 text-sm text-white"><Plus size={16} /> {t("add")}</button>
          </form>
          <div className="mt-3 space-y-2">
            {tasks.length === 0 && <EmptyState text={t("noScheduledTasks")} />}
            {tasks.map((task) => (
              <div key={task.id} className="rounded border border-line p-3 text-sm">
                <div className="font-medium">{task.name}</div>
                <div className="text-ink/55">{task.schedule} / {task.status}</div>
              </div>
            ))}
          </div>
        </Panel>
      </div>
      <Panel className="mt-4">
        <h2 className="font-semibold">{t("promptTemplates")}</h2>
        <div className="mt-3 grid gap-2">
          {prompts.map((prompt) => (
            <div key={prompt.id} className="rounded border border-line p-3 text-sm">
              <div className="font-medium">{prompt.name} v{prompt.version} <span className="text-ink/45">/ {prompt.task_type}</span></div>
              <p className="mt-1 text-ink/65">{prompt.content}</p>
            </div>
          ))}
        </div>
      </Panel>
    </>
  );
}

function formatLatency(value: number): string {
  if (!value) return "local mock";
  return value < 1 ? "<1ms" : `${value}ms`;
}

function formatSettingValue(value: string | boolean | number | null | undefined): string {
  if (typeof value === "boolean") return value ? "yes" : "no";
  if (value === null || value === undefined || value === "") return "-";
  return String(value);
}

function modeLabel(value: string | boolean | number | null | undefined): string {
  if (value === "hosted_demo") return "Hosted demo";
  if (value === "local_gemini") return "Local Gemini";
  return "Local mock";
}
