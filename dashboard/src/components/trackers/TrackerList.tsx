"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getTrackers, createTracker, deleteTracker } from "@/lib/api";
import Link from "next/link";
import { FiPlus, FiTrash2 } from "react-icons/fi";

export function TrackerList() {
  const queryClient = useQueryClient();
  const { data: trackers, isLoading } = useQuery({
    queryKey: ["trackers"],
    queryFn: getTrackers,
  });

  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    name: "",
    description: "",
    folder_name: "",
    extraction_prompt: "",
  });

  const create = useMutation({
    mutationFn: createTracker,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trackers"] });
      setShowCreate(false);
      setForm({ name: "", description: "", folder_name: "", extraction_prompt: "" });
    },
  });

  const remove = useMutation({
    mutationFn: deleteTracker,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["trackers"] }),
  });

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold">Custom Trackers</h1>
          <p className="text-sm text-muted mt-1">
            Create tracking categories the AI will extract from future notes
          </p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-1.5 bg-accent text-white px-3 py-1.5 rounded-lg text-sm hover:bg-accent-hover transition-colors"
        >
          <FiPlus size={16} /> New Tracker
        </button>
      </div>

      {/* Create form */}
      {showCreate && (
        <div className="bg-card border border-border rounded-lg p-4 mb-6 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-muted block mb-1">Name</label>
              <input
                value={form.name}
                onChange={(e) =>
                  setForm({
                    ...form,
                    name: e.target.value,
                    folder_name: e.target.value.replace(/\s+/g, " ").trim(),
                  })
                }
                placeholder="e.g. Substations"
                className="w-full bg-background border border-border rounded px-2 py-1.5 text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-muted block mb-1">Folder Name</label>
              <input
                value={form.folder_name}
                onChange={(e) => setForm({ ...form, folder_name: e.target.value })}
                placeholder="e.g. Substations"
                className="w-full bg-background border border-border rounded px-2 py-1.5 text-sm"
              />
            </div>
          </div>
          <div>
            <label className="text-xs text-muted block mb-1">Description</label>
            <input
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="What does this tracker track?"
              className="w-full bg-background border border-border rounded px-2 py-1.5 text-sm"
            />
          </div>
          <div>
            <label className="text-xs text-muted block mb-1">
              Extraction Prompt (instructions for the AI)
            </label>
            <textarea
              value={form.extraction_prompt}
              onChange={(e) =>
                setForm({ ...form, extraction_prompt: e.target.value })
              }
              placeholder="e.g. Extract any mentions, decisions, or updates related to electrical substations, substation permits, or grid connection points."
              rows={3}
              className="w-full bg-background border border-border rounded px-2 py-1.5 text-sm resize-none"
            />
          </div>
          <div className="flex justify-end gap-2">
            <button
              onClick={() => setShowCreate(false)}
              className="text-xs px-3 py-1.5 rounded text-muted hover:text-foreground"
            >
              Cancel
            </button>
            <button
              onClick={() => create.mutate(form)}
              disabled={!form.name || !form.extraction_prompt || create.isPending}
              className="text-xs px-3 py-1.5 rounded bg-accent text-white hover:bg-accent-hover disabled:opacity-50"
            >
              {create.isPending ? "Creating..." : "Create Tracker"}
            </button>
          </div>
        </div>
      )}

      {/* Tracker cards */}
      {isLoading ? (
        <div className="text-muted">Loading...</div>
      ) : !trackers?.length ? (
        <div className="text-center text-muted py-12 bg-card border border-border rounded-lg">
          <p className="mb-2">No trackers yet</p>
          <p className="text-xs">
            Create a tracker to have the AI start extracting specific topics from notes
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {trackers.map((t) => (
            <div
              key={t.id}
              className="bg-card border border-border rounded-lg p-4 hover:border-accent/50 transition-colors"
            >
              <div className="flex items-start justify-between">
                <Link href={`/trackers/${t.id}`} className="flex-1">
                  <h3 className="font-semibold text-accent">{t.name}</h3>
                  <p className="text-xs text-muted mt-1">{t.description}</p>
                  <p className="text-xs text-muted mt-2">
                    Folder: <code className="text-accent/70">{t.folder_name}/</code>
                  </p>
                </Link>
                <button
                  onClick={() => remove.mutate(t.id)}
                  className="text-muted hover:text-error p-1"
                >
                  <FiTrash2 size={14} />
                </button>
              </div>
              <div className="flex items-center gap-2 mt-3">
                <span
                  className={`text-xs px-1.5 py-0.5 rounded ${
                    t.active
                      ? "bg-success/10 text-success"
                      : "bg-muted/10 text-muted"
                  }`}
                >
                  {t.active ? "Active" : "Inactive"}
                </span>
                <span className="text-xs text-muted">
                  Created {t.created_at}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
