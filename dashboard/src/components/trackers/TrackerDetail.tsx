"use client";

import { useQuery } from "@tanstack/react-query";
import { getTrackerItems, getTrackers } from "@/lib/api";
import { useAppStore } from "@/store/useAppStore";
import Link from "next/link";
import { FiArrowLeft } from "react-icons/fi";

export function TrackerDetail({ trackerId }: { trackerId: string }) {
  const { setSelectedFilePath } = useAppStore();

  const { data: trackers } = useQuery({
    queryKey: ["trackers"],
    queryFn: getTrackers,
  });
  const tracker = trackers?.find((t) => t.id === trackerId);

  const { data: items, isLoading } = useQuery({
    queryKey: ["tracker-items", trackerId],
    queryFn: () => getTrackerItems(trackerId),
    enabled: !!trackerId,
  });

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <Link
        href="/trackers"
        className="flex items-center gap-1 text-sm text-muted hover:text-foreground mb-4"
      >
        <FiArrowLeft size={14} /> Back to Trackers
      </Link>

      <h1 className="text-xl font-bold mb-1">{tracker?.name || "Tracker"}</h1>
      <p className="text-sm text-muted mb-6">{tracker?.description}</p>

      {isLoading ? (
        <div className="text-muted">Loading items...</div>
      ) : !items?.length ? (
        <div className="text-center text-muted py-12 bg-card border border-border rounded-lg">
          No items extracted yet. Items will appear here after the processor
          analyzes new notes.
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <div
              key={item.file_path}
              className="bg-card border border-border rounded-lg p-4 hover:border-accent/50 cursor-pointer transition-colors"
              onClick={() => setSelectedFilePath(item.file_path)}
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-medium text-sm">{item.title}</h3>
                  <p className="text-xs text-muted mt-1">
                    {item.content_preview}
                  </p>
                </div>
                <span className="text-xs bg-accent/10 text-accent px-1.5 py-0.5 rounded shrink-0">
                  {item.project}
                </span>
              </div>
              <div className="flex items-center gap-2 mt-2 text-xs text-muted">
                <span>{item.date}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
