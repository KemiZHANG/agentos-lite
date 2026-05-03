export type TaskStatus = "pending" | "active" | "paused" | "completed";

export interface ScheduledTask {
  id: string;
  name: string;
  schedule: string;
  status: TaskStatus;
}

export function createScheduledTask(name: string, schedule: string): ScheduledTask {
  return {
    id: `task_${name.toLowerCase().replaceAll(" ", "_")}`,
    name,
    schedule,
    status: "pending",
  };
}

export function activateTask(task: ScheduledTask): ScheduledTask {
  return { ...task, status: "active" };
}

