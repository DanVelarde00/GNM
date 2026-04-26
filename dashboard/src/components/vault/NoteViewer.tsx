"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { getFile, deleteNote } from "@/lib/api";
import { useAppStore } from "@/store/useAppStore";
import { FiEdit2, FiX, FiTrash2 } from "react-icons/fi";

export function NoteViewer() {
  const { selectedFilePath, setSelectedFilePath, setEditing } = useAppStore();
  const queryClient = useQueryClient();
  const [confirming, setConfirming] = useState(false);

  const { data: file, isLoading } = useQuery({
    queryKey: ["file", selectedFilePath],
    queryFn: () => getFile(selectedFilePath!),
    enabled: !!selectedFilePath,
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteNote(selectedFilePath!),
    onSuccess: () => {
      setSelectedFilePath(null);
      setConfirming(false);
      queryClient.invalidateQueries({ queryKey: ["tree"] });
    },
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

          {confirming ? (
            <div className="flex items-center gap-1">
              <span className="text-xs text-error">Delete note + all derived files?</span>
              <button
                onClick={() => deleteMutation.mutate()}
                disabled={deleteMutation.isPending}
                className="text-xs px-2 py-1 rounded bg-error text-white hover:opacity-80 transition-opacity disabled:opacity-40"
              >
                {deleteMutation.isPending ? "Deleting…" : "Yes"}
              </button>
              <button
                onClick={() => setConfirming(false)}
                className="text-xs px-2 py-1 rounded bg-card border border-border text-muted hover:text-foreground transition-colors"
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              onClick={() => setConfirming(true)}
              className="flex items-center gap-1 text-xs px-2 py-1 rounded bg-error/10 text-error hover:bg-error/20 transition-colors"
            >
              <FiTrash2 size={12} /> Delete
            </button>
          )}

          <button
            onClick={() => { setSelectedFilePath(null); setConfirming(false); }}
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
