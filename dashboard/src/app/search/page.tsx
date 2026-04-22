"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { search, getProjects } from "@/lib/api";
import { useAppStore } from "@/store/useAppStore";
import { FiSearch } from "react-icons/fi";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [projectFilter, setProjectFilter] = useState("");
  const [submitted, setSubmitted] = useState("");
  const { setSelectedFilePath } = useAppStore();

  const { data: projects } = useQuery({
    queryKey: ["projects"],
    queryFn: getProjects,
  });

  const { data: results, isLoading } = useQuery({
    queryKey: ["search", submitted, projectFilter],
    queryFn: () => search(submitted, projectFilter || undefined),
    enabled: !!submitted,
  });

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-xl font-bold mb-4">Search Vault</h1>

      <div className="flex gap-2 mb-6">
        <div className="flex-1 relative">
          <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" size={16} />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && setSubmitted(query)}
            placeholder="Search notes, transcripts, action items..."
            className="w-full bg-card border border-border rounded-lg pl-9 pr-3 py-2 text-sm focus:outline-none focus:border-accent"
          />
        </div>
        <select
          value={projectFilter}
          onChange={(e) => setProjectFilter(e.target.value)}
          className="text-sm bg-card border border-border rounded-lg px-3 py-2 text-foreground"
        >
          <option value="">All Projects</option>
          {projects?.map((p) => (
            <option key={p.name} value={p.name}>{p.name}</option>
          ))}
        </select>
        <button
          onClick={() => setSubmitted(query)}
          className="bg-accent text-white px-4 py-2 rounded-lg text-sm hover:bg-accent-hover transition-colors"
        >
          Search
        </button>
      </div>

      {isLoading && <div className="text-muted">Searching...</div>}

      {results && (
        <div className="space-y-3">
          <p className="text-xs text-muted">{results.length} results</p>
          {results.map((r) => (
            <div
              key={r.path}
              onClick={() => setSelectedFilePath(r.path)}
              className="bg-card border border-border rounded-lg p-4 cursor-pointer hover:border-accent/50 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-sm font-medium">{r.title}</h3>
                  <p className="text-xs text-muted font-mono mt-0.5">{r.path}</p>
                </div>
                <div className="flex items-center gap-2">
                  {r.project && (
                    <span className="text-xs bg-accent/10 text-accent px-1.5 py-0.5 rounded">
                      {r.project}
                    </span>
                  )}
                  {r.type && (
                    <span className="text-xs bg-card border border-border px-1.5 py-0.5 rounded">
                      {r.type}
                    </span>
                  )}
                </div>
              </div>
              {r.participants && (
                <p className="text-xs text-muted mt-1">
                  Participants: {r.participants}
                </p>
              )}
              {r.date && (
                <p className="text-xs text-muted mt-0.5">Date: {r.date}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {submitted && results?.length === 0 && !isLoading && (
        <div className="text-center text-muted py-12">
          No results found for &quot;{submitted}&quot;
        </div>
      )}
    </div>
  );
}
