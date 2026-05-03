import { createScheduledTask } from "./tasks";

export type UploadResult = {
  filename: string;
  accepted: boolean;
  reason?: string;
};

export function validateUpload(filename: string): UploadResult {
  const accepted = filename.endsWith(".txt") || filename.endsWith(".md");
  return {
    filename,
    accepted,
    reason: accepted ? undefined : "Only TXT and Markdown are accepted in the demo.",
  };
}

export function scheduleUploadRefresh(filename: string) {
  return createScheduledTask(`Refresh ${filename}`, "daily:09:00");
}

