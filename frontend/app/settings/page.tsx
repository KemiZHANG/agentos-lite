"use client";

import { Plus } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { EmptyState, PageHeader, Panel } from "@/components/Ui";
import { useI18n } from "@/components/I18nProvider";
import { api } from "@/lib/api";

type Settings = Record<string, string>;
type Prompt = { id: string; name: string; version: string; task_type: string; active: number; content: string };
type ScheduledTask = { id: string; name: string; description: string; schedule: string; status: string };

export default function SettingsPage() {
  const { t } = useI18n();
  const [settings, setSettings] = useState<Settings>({});
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [tasks, setTasks] = useState<ScheduledTask[]>([]);
  const [taskName, setTaskName] = useState("Weekly knowledge refresh");
  const [schedule, setSchedule] = useState("weekly:Monday 09:00");

  function load() {
    api.get<Settings>("/settings").then(setSettings).catch(() => setSettings({}));
    api.get<Prompt[]>("/settings/prompts").then(setPrompts).catch(() => setPrompts([]));
    api.get<ScheduledTask[]>("/settings/scheduled-tasks").then(setTasks).catch(() => setTasks([]));
  }

  useEffect(load, []);

  async function createTask(event: FormEvent) {
    event.preventDefault();
    await api.post("/settings/scheduled-tasks", { name: taskName, description: "Scheduler-ready placeholder task", schedule, status: "pending", payload: { integration: "future APScheduler or Celery beat" } });
    load();
  }

  return (
    <>
      <PageHeader title={t("settingsTitle")} subtitle={t("settingsSubtitle")} />
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <h2 className="font-semibold">{t("runtime")}</h2>
          <dl className="mt-3 space-y-2 text-sm">
            {Object.entries(settings).map(([key, value]) => (
              <div key={key} className="flex justify-between gap-4 border-b border-line py-2">
                <dt className="text-ink/55">{key}</dt>
                <dd className="break-all text-right">{value}</dd>
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
