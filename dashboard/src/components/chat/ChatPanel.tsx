"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { getProjects } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";
import { FiSend, FiFile } from "react-icons/fi";

export function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [sources, setSources] = useState<string[]>([]);
  const [projectFilter, setProjectFilter] = useState<string>("");
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: projects } = useQuery({
    queryKey: ["projects"],
    queryFn: getProjects,
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = useCallback(() => {
    if (!input.trim() || streaming) return;

    const userMsg: ChatMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setStreaming(true);
    setSources([]);

    // Open WebSocket connection
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${protocol}//localhost:8000/api/chat/ws`);
    wsRef.current = ws;

    let assistantContent = "";

    ws.onopen = () => {
      ws.send(
        JSON.stringify({
          message: input,
          history: messages,
          project_filter: projectFilter || null,
        })
      );
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "sources") {
        setSources(data.files || []);
      } else if (data.type === "token") {
        assistantContent += data.content;
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last?.role === "assistant") {
            updated[updated.length - 1] = { ...last, content: assistantContent };
          } else {
            updated.push({ role: "assistant", content: assistantContent });
          }
          return updated;
        });
      } else if (data.type === "done") {
        setStreaming(false);
        ws.close();
      } else if (data.type === "error") {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: `Error: ${data.message}` },
        ]);
        setStreaming(false);
        ws.close();
      }
    };

    ws.onerror = () => {
      setStreaming(false);
    };
  }, [input, streaming, messages, projectFilter]);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b border-border bg-sidebar flex items-center gap-3">
        <h2 className="text-sm font-semibold">AI Chat</h2>
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
      </div>

      {/* Sources */}
      {sources.length > 0 && (
        <div className="px-4 py-2 border-b border-border bg-card/50 flex flex-wrap gap-1">
          <span className="text-xs text-muted mr-1">Sources:</span>
          {sources.map((s) => (
            <span
              key={s}
              className="inline-flex items-center gap-1 text-xs bg-accent/10 text-accent px-1.5 py-0.5 rounded"
            >
              <FiFile size={10} /> {s.split("/").pop()}
            </span>
          ))}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-auto px-4 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-muted py-20">
            <p className="text-lg mb-2">Ask about Glen&apos;s notes</p>
            <p className="text-sm">
              e.g. &quot;What did Glen discuss about substations?&quot; or &quot;Summarize Goldstone action items&quot;
            </p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${
                msg.role === "user"
                  ? "bg-accent text-white"
                  : "bg-card border border-border"
              }`}
            >
              {msg.role === "assistant" ? (
                <div className="prose prose-invert prose-sm max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {msg.content}
                  </ReactMarkdown>
                </div>
              ) : (
                msg.content
              )}
            </div>
          </div>
        ))}
        {streaming && (
          <div className="text-xs text-muted animate-pulse">Thinking...</div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-4 py-3 border-t border-border bg-sidebar">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
            placeholder="Ask about Glen's notes..."
            className="flex-1 bg-card border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent"
            disabled={streaming}
          />
          <button
            onClick={sendMessage}
            disabled={streaming || !input.trim()}
            className="bg-accent text-white px-4 py-2 rounded-lg hover:bg-accent-hover transition-colors disabled:opacity-50"
          >
            <FiSend size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
