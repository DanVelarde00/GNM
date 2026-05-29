"use client";

import { useQuery } from "@tanstack/react-query";
import { getGraph } from "@/lib/api";
import { VaultGraph } from "@/components/graph/VaultGraph";

const PROJECT_COLORS: Record<string, string> = {
  Calico: "#6366f1",
  Cobia: "#22c55e",
  Goldstone: "#f59e0b",
  Vistra: "#ef4444",
  Zelestra: "#8b5cf6",
  Personal: "#06b6d4",
  People: "#ec4899",
};

export default function GraphPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["graph"],
    queryFn: getGraph,
    staleTime: 60_000,
  });

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b border-border bg-sidebar flex items-center gap-4 shrink-0">
        <h2 className="text-sm font-semibold">Vault Graph</h2>
        {data && (
          <span className="text-xs text-muted">
            {data.nodes.length} notes · {data.links.length} connections
          </span>
        )}
        {/* Legend */}
        <div className="ml-auto flex items-center gap-3 flex-wrap">
          {Object.entries(PROJECT_COLORS).map(([project, color]) => (
            <span key={project} className="flex items-center gap-1 text-xs text-muted">
              <span
                className="inline-block w-2.5 h-2.5 rounded-full"
                style={{ backgroundColor: color }}
              />
              {project}
            </span>
          ))}
        </div>
      </div>

      {/* Graph canvas */}
      <div className="flex-1 relative overflow-hidden">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center text-sm text-muted">
            Building graph...
          </div>
        )}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center text-sm text-red-400">
            Failed to load graph
          </div>
        )}
        {data && <VaultGraph data={data} />}
      </div>

      <div className="px-4 py-2 border-t border-border bg-sidebar text-xs text-muted shrink-0">
        Scroll to zoom · drag to pan · click a node to open the note
      </div>
    </div>
  );
}
