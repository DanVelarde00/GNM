"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getActionItems, toggleActionItem, getProjects } from "@/lib/api";
import type { ActionItem } from "@/lib/types";
import { useAppStore } from "@/store/useAppStore";

export function ActionItemTable() {
  const [projectFilter, setProjectFilter] = useState("");
  const [personFilter, setPersonFilter] = useState("");
  const [showCompleted, setShowCompleted] = useState(false);
  const { setSelectedFilePath } = useAppStore();
  const queryClient = useQueryClient();

  const { data: projects } = useQuery({
    queryKey: ["projects"],
    queryFn: getProjects,
  });

  const { data: items, isLoading } = useQuery({
    queryKey: ["action-items", projectFilter, personFilter],
    queryFn: () => getActionItems(projectFilter || undefined, personFilter || undefined),
  });

  const toggle = useMutation({
    mutationFn: (item: ActionItem) =>
      toggleActionItem(item.file_path, item.task_index, !item.completed),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["action-items"] }),
  });

  const filtered = items?.filter((item) =>
    showCompleted ? true : !item.completed
  ) ?? [];

  return (
    <div className="flex flex-col h-full">
      {/* Filters */}
      <div className="px-4 py-3 border-b border-border bg-sidebar flex items-center gap-3 flex-wrap">
        <select
          value={projectFilter}
          onChange={(e) => setProjectFilter(e.target.value)}
          className="text-xs bg-card border border-border rounded px-2 py-1 text-foreground"
        >
          <option value="">All Projects</option>
          {projects?.map((p) => (
            <option key={p.name} value={p.name}>{p.name}</option>
          ))}
        </select>
        <input
          type="text"
          value={personFilter}
          onChange={(e) => setPersonFilter(e.target.value)}
          placeholder="Filter by person..."
          className="text-xs bg-card border border-border rounded px-2 py-1 text-foreground w-40"
        />
        <label className="flex items-center gap-1.5 text-xs text-muted">
          <input
            type="checkbox"
            checked={showCompleted}
            onChange={(e) => setShowCompleted(e.target.checked)}
            className="accent-accent"
          />
          Show completed
        </label>
        <span className="text-xs text-muted ml-auto">
          {filtered.length} item{filtered.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        {isLoading ? (
          <div className="p-8 text-center text-muted">Loading...</div>
        ) : filtered.length === 0 ? (
          <div className="p-8 text-center text-muted">No action items found</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-card/50 sticky top-0">
              <tr className="text-left text-xs text-muted">
                <th className="px-4 py-2 w-8"></th>
                <th className="px-4 py-2">Task</th>
                <th className="px-4 py-2 w-32">Owner</th>
                <th className="px-4 py-2 w-28">Due</th>
                <th className="px-4 py-2 w-28">Project</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((item, i) => (
                <tr
                  key={`${item.file_path}-${item.task_index}-${i}`}
                  className="border-t border-border hover:bg-white/5 transition-colors"
                >
                  <td className="px-4 py-2">
                    <input
                      type="checkbox"
                      checked={item.completed}
                      onChange={() => toggle.mutate(item)}
                      className="accent-accent"
                    />
                  </td>
                  <td
                    className={`px-4 py-2 cursor-pointer hover:text-accent ${
                      item.completed ? "line-through text-muted" : ""
                    }`}
                    onClick={() => setSelectedFilePath(item.file_path)}
                  >
                    {item.task}
                  </td>
                  <td className="px-4 py-2 text-accent text-xs">
                    {item.owner || "—"}
                  </td>
                  <td className="px-4 py-2 text-xs text-muted">
                    {item.due || "—"}
                  </td>
                  <td className="px-4 py-2">
                    <span className="text-xs bg-accent/10 text-accent px-1.5 py-0.5 rounded">
                      {item.project}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
