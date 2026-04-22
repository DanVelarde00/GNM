import type {
  FileNode,
  VaultFile,
  ProjectInfo,
  ActionItem,
  SearchResult,
  TrackerDefinition,
  TrackerItem,
  ProcessorStatus,
  LogEntry,
} from "./types";

const BASE = "/api";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path}: ${res.status}`);
  return res.json();
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`POST ${path}: ${res.status}`);
  return res.json();
}

async function put<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`PUT ${path}: ${res.status}`);
  return res.json();
}

async function del<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`DELETE ${path}: ${res.status}`);
  return res.json();
}

// Files
export const getTree = () => get<FileNode[]>("/files/tree");
export const getFile = (path: string) =>
  get<VaultFile>(`/files/file?path=${encodeURIComponent(path)}`);
export const saveFile = (path: string, content: string) =>
  put<{ ok: boolean }>("/files/file", { path, content });
export const getProjects = () => get<ProjectInfo[]>("/files/projects");

// Search
export const search = (q: string, project?: string, type?: string) => {
  const params = new URLSearchParams({ q });
  if (project) params.set("project", project);
  if (type) params.set("type", type);
  return get<SearchResult[]>(`/search?${params}`);
};
export const rebuildIndex = () => post<{ ok: boolean; indexed: number }>("/search/rebuild");

// Action Items
export const getActionItems = (project?: string, person?: string) => {
  const params = new URLSearchParams();
  if (project) params.set("project", project);
  if (person) params.set("person", person);
  return get<ActionItem[]>(`/action-items?${params}`);
};
export const toggleActionItem = (file_path: string, task_index: number, completed: boolean) =>
  put<{ ok: boolean }>("/action-items/toggle", { file_path, task_index, completed });

// Trackers
export const getTrackers = () => get<TrackerDefinition[]>("/trackers");
export const createTracker = (data: {
  name: string;
  description: string;
  folder_name: string;
  extraction_prompt: string;
}) => post<TrackerDefinition>("/trackers", data);
export const deleteTracker = (id: string) => del<{ ok: boolean }>(`/trackers/${id}`);
export const getTrackerItems = (id: string) => get<TrackerItem[]>(`/trackers/${id}/items`);

// Processor
export const getProcessorStatus = () => get<ProcessorStatus>("/processor/status");
export const startProcessor = () => post<ProcessorStatus>("/processor/start");
export const stopProcessor = () => post<ProcessorStatus>("/processor/stop");
export const restartProcessor = () => post<ProcessorStatus>("/processor/restart");
export const getProcessorLog = (n?: number) =>
  get<LogEntry[]>(`/processor/log${n ? `?n=${n}` : ""}`);

// Weekly Reports
export const generateWeeklyReports = (targetDate?: string) =>
  post<{ ok: boolean; reports: { project: string; path: string; notes_count: number }[] }>(
    "/weekly-reports/generate",
    targetDate ? { target_date: targetDate } : {}
  );

// Submit
export const uploadFile = async (file: File, sourceType: string) => {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("source_type", sourceType);
  const res = await fetch(`${BASE}/submit/file`, { method: "POST", body: fd });
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
  return res.json();
};
