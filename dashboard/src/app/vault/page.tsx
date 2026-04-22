"use client";

import { useQuery } from "@tanstack/react-query";
import { getTree } from "@/lib/api";
import { FileTree } from "@/components/vault/FileTree";
import { NoteViewer } from "@/components/vault/NoteViewer";
import { MarkdownEditor } from "@/components/editor/MarkdownEditor";
import { useAppStore } from "@/store/useAppStore";

export default function VaultPage() {
  const { editing } = useAppStore();
  const { data: tree, isLoading } = useQuery({
    queryKey: ["tree"],
    queryFn: getTree,
  });

  return (
    <div className="flex h-full">
      {/* File tree sidebar */}
      <div className="w-72 border-r border-border bg-sidebar overflow-auto shrink-0">
        <div className="px-3 py-2 border-b border-border">
          <h2 className="text-xs font-semibold text-muted uppercase tracking-wider">
            Vault Files
          </h2>
        </div>
        {isLoading ? (
          <div className="p-4 text-sm text-muted">Loading vault...</div>
        ) : tree ? (
          <FileTree nodes={tree} />
        ) : null}
      </div>

      {/* Content area */}
      {editing ? <MarkdownEditor /> : <NoteViewer />}
    </div>
  );
}
