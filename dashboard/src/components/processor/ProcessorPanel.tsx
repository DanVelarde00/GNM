"use client";

import { useState, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getProcessorStatus,
  startProcessor,
  stopProcessor,
  restartProcessor,
  generateWeeklyReports,
  getOtterStatus,
  pullOtterTranscripts,
} from "@/lib/api";
import type { LogEntry } from "@/lib/types";
import { FiPlay, FiSquare, FiRefreshCw, FiFileText, FiDownload } from "react-icons/fi";

export function ProcessorPanel() {
  const queryClient = useQueryClient();
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const logEndRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  const { data: status } = useQuery({
    queryKey: ["processor-status"],
    queryFn: getProcessorStatus,
    refetchInterval: 3000,
  });

  const start = useMutation({
    mutationFn: startProcessor,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["processor-status"] }),
  });
  const stop = useMutation({
    mutationFn: stopProcessor,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["processor-status"] }),
  });
  const restart = useMutation({
    mutationFn: restartProcessor,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["processor-status"] }),
  });

  const [weeklyResult, setWeeklyResult] = useState<string>("");
  const weekly = useMutation({
    mutationFn: () => generateWeeklyReports(),
    onSuccess: (data) => {
      const reports = data.reports;
      if (reports.length === 0) {
        setWeeklyResult("No projects had notes this week");
      } else {
        setWeeklyResult(`Generated ${reports.length} report(s): ${reports.map(r => r.project).join(", ")}`);
      }
      setTimeout(() => setWeeklyResult(""), 5000);
    },
    onError: (e) => setWeeklyResult(`Error: ${e}`),
  });

  const { data: otterStatus } = useQuery({
    queryKey: ["otter-status"],
    queryFn: getOtterStatus,
  });

  const [otterResult, setOtterResult] = useState<string>("");
  const pullOtter = useMutation({
    mutationFn: pullOtterTranscripts,
    onSuccess: (data) => {
      setOtterResult(
        data.pulled === 0
          ? "No new transcripts"
          : `Pulled ${data.pulled} transcript(s): ${data.files.join(", ")}`
      );
      setTimeout(() => setOtterResult(""), 6000);
    },
    onError: (e) => setOtterResult(`Error: ${e}`),
  });

  // WebSocket for live log
  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${protocol}//localhost:8000/api/processor/ws`);

    ws.onmessage = (event) => {
      const entry: LogEntry = JSON.parse(event.data);
      setLogs((prev) => [...prev.slice(-499), entry]);
    };

    ws.onerror = () => {};
    ws.onclose = () => {};

    return () => ws.close();
  }, []);

  useEffect(() => {
    if (autoScroll) {
      logEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs, autoScroll]);

  const formatUptime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) return `${h}h ${m}m`;
    if (m > 0) return `${m}m ${s}s`;
    return `${s}s`;
  };

  const colorLine = (msg: string) => {
    if (msg.includes("ERROR") || msg.includes("Error")) return "text-error";
    if (msg.includes("Processing") || msg.includes("Calling")) return "text-warning";
    if (msg.includes("Done") || msg.includes("Created") || msg.includes("started")) return "text-success";
    return "text-muted";
  };

  return (
    <div className="flex flex-col h-full">
      {/* Status bar */}
      <div className="px-4 py-3 border-b border-border bg-sidebar flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span
            className={`w-2.5 h-2.5 rounded-full ${
              status?.running ? "bg-success animate-pulse" : "bg-muted"
            }`}
          />
          <span className="text-sm font-medium">
            {status?.running ? "Running" : "Stopped"}
          </span>
        </div>

        {status?.running && (
          <>
            <span className="text-xs text-muted">
              PID: {status.pid}
            </span>
            <span className="text-xs text-muted">
              Uptime: {formatUptime(status.uptime_seconds)}
            </span>
          </>
        )}

        <div className="flex items-center gap-2 ml-auto">
          {otterStatus?.configured && (
            <button
              onClick={() => pullOtter.mutate()}
              disabled={pullOtter.isPending}
              className="flex items-center gap-1 text-xs px-3 py-1.5 rounded bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 disabled:opacity-50"
            >
              <FiDownload size={12} /> {pullOtter.isPending ? "Pulling..." : "Pull Otter"}
            </button>
          )}
          <button
            onClick={() => weekly.mutate()}
            disabled={weekly.isPending}
            className="flex items-center gap-1 text-xs px-3 py-1.5 rounded bg-accent/20 text-accent hover:bg-accent/30 disabled:opacity-50"
          >
            <FiFileText size={12} /> {weekly.isPending ? "Generating..." : "Weekly Reports"}
          </button>
          {!status?.running ? (
            <button
              onClick={() => start.mutate()}
              className="flex items-center gap-1 text-xs px-3 py-1.5 rounded bg-success/20 text-success hover:bg-success/30"
            >
              <FiPlay size={12} /> Start
            </button>
          ) : (
            <>
              <button
                onClick={() => restart.mutate()}
                className="flex items-center gap-1 text-xs px-3 py-1.5 rounded bg-warning/20 text-warning hover:bg-warning/30"
              >
                <FiRefreshCw size={12} /> Restart
              </button>
              <button
                onClick={() => stop.mutate()}
                className="flex items-center gap-1 text-xs px-3 py-1.5 rounded bg-error/20 text-error hover:bg-error/30"
              >
                <FiSquare size={12} /> Stop
              </button>
            </>
          )}
        </div>
        {weeklyResult && (
          <span className="text-xs text-accent ml-2">{weeklyResult}</span>
        )}
        {otterResult && (
          <span className="text-xs text-blue-400 ml-2">{otterResult}</span>
        )}
      </div>

      {/* Log output */}
      <div
        className="flex-1 overflow-auto bg-background p-4 font-mono text-xs"
        onScroll={(e) => {
          const el = e.currentTarget;
          const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 50;
          setAutoScroll(atBottom);
        }}
      >
        {logs.length === 0 ? (
          <div className="text-muted">Waiting for log output...</div>
        ) : (
          logs.map((entry, i) => (
            <div key={i} className={`py-0.5 ${colorLine(entry.msg)}`}>
              <span className="text-muted/50 mr-2">
                {new Date(entry.ts * 1000).toLocaleTimeString()}
              </span>
              {entry.msg}
            </div>
          ))
        )}
        <div ref={logEndRef} />
      </div>
    </div>
  );
}
