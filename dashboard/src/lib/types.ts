export interface FileNode {
  name: string;
  path: string;
  is_dir: boolean;
  children: FileNode[];
}

export interface VaultFile {
  path: string;
  frontmatter: Record<string, unknown>;
  body: string;
  raw: string;
}

export interface ProjectInfo {
  name: string;
  path: string;
  has_notes: boolean;
  has_transcripts: boolean;
  has_analyzed: boolean;
  has_action_items: boolean;
  people_count: number;
}

export interface ActionItem {
  task: string;
  owner: string | null;
  due: string | null;
  completed: boolean;
  project: string;
  file_path: string;
  task_index: number;
  date: string;
  source_note: string;
}

export interface SearchResult {
  path: string;
  project: string;
  type: string;
  date: string;
  title: string;
  participants: string;
  score: number;
  highlights: string;
}

export interface TrackerDefinition {
  id: string;
  name: string;
  description: string;
  folder_name: string;
  extraction_prompt: string;
  icon: string;
  color: string;
  active: boolean;
  created_at: string;
}

export interface TrackerItem {
  tracker_id: string;
  project: string;
  file_path: string;
  title: string;
  date: string;
  content_preview: string;
  tags: string[];
}

export interface ProcessorStatus {
  running: boolean;
  pid: number | null;
  uptime_seconds: number;
}

export interface LogEntry {
  ts: number;
  msg: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatChunk {
  type: "sources" | "token" | "done" | "error";
  content?: string;
  files?: string[];
  message?: string;
}
