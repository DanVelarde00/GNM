"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { EditorView, keymap } from "@codemirror/view";
import { EditorState } from "@codemirror/state";
import { markdown } from "@codemirror/lang-markdown";
import { defaultKeymap, history, historyKeymap } from "@codemirror/commands";
import { searchKeymap } from "@codemirror/search";
import { getFile, saveFile } from "@/lib/api";
import { useAppStore } from "@/store/useAppStore";
import { FiSave, FiX } from "react-icons/fi";

const theme = EditorView.theme({
  "&": { backgroundColor: "#0f172a", color: "#e2e8f0" },
  ".cm-content": { caretColor: "#6366f1", fontFamily: "var(--font-geist-mono), monospace" },
  ".cm-cursor": { borderLeftColor: "#6366f1" },
  ".cm-activeLine": { backgroundColor: "#1e293b" },
  ".cm-gutters": { backgroundColor: "#1e293b", color: "#64748b", border: "none" },
  ".cm-selectionBackground": { backgroundColor: "#334155 !important" },
  "&.cm-focused .cm-selectionBackground": { backgroundColor: "#334155 !important" },
});

export function MarkdownEditor() {
  const { selectedFilePath, setEditing } = useAppStore();
  const editorRef = useRef<HTMLDivElement>(null);
  const viewRef = useRef<EditorView | null>(null);
  const [saved, setSaved] = useState(false);
  const queryClient = useQueryClient();

  const { data: file } = useQuery({
    queryKey: ["file", selectedFilePath],
    queryFn: () => getFile(selectedFilePath!),
    enabled: !!selectedFilePath,
  });

  const mutation = useMutation({
    mutationFn: ({ path, content }: { path: string; content: string }) =>
      saveFile(path, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["file", selectedFilePath] });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    },
  });

  const handleSave = useCallback(() => {
    if (!viewRef.current || !selectedFilePath) return;
    const content = viewRef.current.state.doc.toString();
    mutation.mutate({ path: selectedFilePath, content });
  }, [selectedFilePath, mutation]);

  useEffect(() => {
    if (!editorRef.current || !file) return;

    const saveKeymap = keymap.of([
      { key: "Mod-s", run: () => { handleSave(); return true; } },
    ]);

    const state = EditorState.create({
      doc: file.raw,
      extensions: [
        saveKeymap,
        keymap.of([...defaultKeymap, ...historyKeymap, ...searchKeymap]),
        history(),
        markdown(),
        theme,
        EditorView.lineWrapping,
      ],
    });

    const view = new EditorView({ state, parent: editorRef.current });
    viewRef.current = view;

    return () => { view.destroy(); };
  }, [file, handleSave]);

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-sidebar">
        <span className="text-sm font-mono text-muted truncate">
          Editing: {selectedFilePath}
        </span>
        <div className="flex items-center gap-2">
          {saved && <span className="text-xs text-success">Saved!</span>}
          <button
            onClick={handleSave}
            disabled={mutation.isPending}
            className="flex items-center gap-1 text-xs px-2 py-1 rounded bg-success/20 text-success hover:bg-success/30 transition-colors"
          >
            <FiSave size={12} /> {mutation.isPending ? "Saving..." : "Save"}
          </button>
          <button
            onClick={() => setEditing(false)}
            className="text-muted hover:text-foreground"
          >
            <FiX size={16} />
          </button>
        </div>
      </div>
      <div ref={editorRef} className="flex-1 overflow-auto" />
    </div>
  );
}
