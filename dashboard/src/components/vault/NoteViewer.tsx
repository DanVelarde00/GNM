"use client";

import { useQuery } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { getFile } from "@/lib/api";
import { useAppStore } from "@/store/useAppStore";
import { FiEdit2, FiX } from "react-icons/fi";

export function NoteViewer() {
  const { selectedFilePath, setSelectedFilePath, setEditing } = useAppStore();

  const { data: file, isLoading } = useQuery({
    queryKey: ["file", selectedFilePath],
    queryFn: () => getFile(selectedFilePath!),
    enabled: !!selectedFilePath,
  });

  if (!selectedFilePath) {
    return (
      <div className="flex-1 flex items-center justify-center text-muted">
        <p>Select a file from the tree to view it</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center text-muted">
        Loading...
      </div>
    );
  }

  if (!file) return null;

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-sidebar">
        <span className="text-sm font-mono text-muted truncate">{file.path}</span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setEditing(true)}
            className="flex items-center gap-1 text-xs px-2 py-1 rounded bg-accent/10 text-accent hover:bg-accent/20 transition-colors"
          >
            <FiEdit2 size={12} /> Edit
          </button>
          <button
            onClick={() => setSelectedFilePath(null)}
            className="text-muted hover:text-foreground"
          >
            <FiX size={16} />
          </button>
        </div>
      </div>

      {/* Frontmatter */}
      {Object.keys(file.frontmatter).length > 0 && (
        <div className="px-4 py-2 bg-card/50 border-b border-border text-xs font-mono">
          {Object.entries(file.frontmatter).map(([k, v]) => (
            <div key={k} className="flex gap-2">
              <span className="text-accent">{k}:</span>
              <span className="text-muted">{JSON.stringify(v)}</span>
            </div>
          ))}
        </div>
      )}

      {/* Body */}
      <div className="flex-1 overflow-auto px-6 py-4 prose prose-invert prose-sm max-w-none">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            a: ({ href, children }) => (
              <span className="text-accent cursor-pointer hover:underline">
                {children}
              </span>
            ),
            input: ({ checked, ...props }) => (
              <input
                type="checkbox"
                checked={checked}
                readOnly
                className="mr-1 accent-accent"
                {...props}
              />
            ),
          }}
        >
          {file.body}
        </ReactMarkdown>
      </div>
    </div>
  );
}
