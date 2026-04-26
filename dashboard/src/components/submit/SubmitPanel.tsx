"use client";

import { useState, useCallback } from "react";
import { uploadFile, submitText } from "@/lib/api";
import { FiUpload, FiCheck, FiAlertCircle, FiFileText } from "react-icons/fi";

type Tab = "upload" | "paste";

export function SubmitPanel() {
  const [tab, setTab] = useState<Tab>("upload");
  const [sourceType, setSourceType] = useState("manual");
  const [dragOver, setDragOver] = useState(false);
  const [status, setStatus] = useState<"idle" | "uploading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  // Paste tab state
  const [pasteText, setPasteText] = useState("");
  const [pasteFilename, setPasteFilename] = useState("note.txt");

  const handleUpload = useCallback(
    async (files: FileList | File[]) => {
      setStatus("uploading");
      try {
        for (const file of Array.from(files)) {
          await uploadFile(file, sourceType);
        }
        setStatus("success");
        setMessage(`Uploaded ${files.length} file(s) to ${sourceType} inbox`);
        setTimeout(() => setStatus("idle"), 3000);
      } catch (e) {
        setStatus("error");
        setMessage(String(e));
      }
    },
    [sourceType]
  );

  const handlePasteSubmit = useCallback(async () => {
    if (!pasteText.trim()) return;
    setStatus("uploading");
    try {
      await submitText(pasteText, sourceType, pasteFilename || "note.txt");
      setStatus("success");
      setMessage(`Submitted to ${sourceType} inbox as ${pasteFilename || "note.txt"}`);
      setPasteText("");
      setTimeout(() => setStatus("idle"), 3000);
    } catch (e) {
      setStatus("error");
      setMessage(String(e));
    }
  }, [pasteText, pasteFilename, sourceType]);

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-xl font-bold mb-1">Submit Notes</h1>
      <p className="text-sm text-muted mb-6">
        Upload files or paste text to the inbox for processing
      </p>

      {/* Source type */}
      <div className="mb-4">
        <label className="text-xs text-muted block mb-1.5">Source Type</label>
        <div className="flex gap-2">
          {["manual", "otter", "inq"].map((t) => (
            <button
              key={t}
              onClick={() => setSourceType(t)}
              className={`px-3 py-1.5 rounded text-sm capitalize transition-colors ${
                sourceType === t
                  ? "bg-accent text-white"
                  : "bg-card border border-border text-muted hover:text-foreground"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Tab toggle */}
      <div className="flex gap-1 mb-4 border border-border rounded-lg p-1 w-fit">
        <button
          onClick={() => setTab("upload")}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-sm transition-colors ${
            tab === "upload" ? "bg-accent text-white" : "text-muted hover:text-foreground"
          }`}
        >
          <FiUpload size={14} /> Upload File
        </button>
        <button
          onClick={() => setTab("paste")}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-sm transition-colors ${
            tab === "paste" ? "bg-accent text-white" : "text-muted hover:text-foreground"
          }`}
        >
          <FiFileText size={14} /> Paste Text
        </button>
      </div>

      {tab === "upload" ? (
        <div
          className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
            dragOver
              ? "border-accent bg-accent/5"
              : "border-border hover:border-muted"
          }`}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            if (e.dataTransfer.files.length) handleUpload(e.dataTransfer.files);
          }}
        >
          <FiUpload size={32} className="mx-auto text-muted mb-3" />
          <p className="text-sm text-muted mb-2">
            Drag and drop files here, or click to browse
          </p>
          <input
            type="file"
            multiple
            accept=".txt,.md,.docx"
            onChange={(e) => {
              if (e.target.files?.length) handleUpload(e.target.files);
            }}
            className="hidden"
            id="file-upload"
          />
          <label
            htmlFor="file-upload"
            className="inline-block bg-accent text-white px-4 py-2 rounded-lg text-sm cursor-pointer hover:bg-accent-hover transition-colors"
          >
            Choose Files
          </label>
          <p className="text-xs text-muted mt-2">Supported: .txt, .md, .docx</p>
        </div>
      ) : (
        <div className="space-y-3">
          <div>
            <label className="text-xs text-muted block mb-1">Filename</label>
            <input
              type="text"
              value={pasteFilename}
              onChange={(e) => setPasteFilename(e.target.value)}
              placeholder="note.txt"
              className="w-full bg-card border border-border rounded px-3 py-1.5 text-sm focus:outline-none focus:border-accent"
            />
          </div>
          <div>
            <label className="text-xs text-muted block mb-1">Note / Transcript</label>
            <textarea
              value={pasteText}
              onChange={(e) => setPasteText(e.target.value)}
              placeholder="Paste your note or transcript here..."
              rows={14}
              className="w-full bg-card border border-border rounded px-3 py-2 text-sm font-mono resize-y focus:outline-none focus:border-accent"
            />
          </div>
          <button
            onClick={handlePasteSubmit}
            disabled={!pasteText.trim() || status === "uploading"}
            className="bg-accent text-white px-4 py-2 rounded text-sm hover:bg-accent-hover transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {status === "uploading" ? "Submitting..." : "Submit for Processing"}
          </button>
        </div>
      )}

      {/* Status */}
      {status !== "idle" && (
        <div
          className={`mt-4 flex items-center gap-2 px-4 py-2 rounded text-sm ${
            status === "uploading"
              ? "bg-accent/10 text-accent"
              : status === "success"
              ? "bg-success/10 text-success"
              : "bg-error/10 text-error"
          }`}
        >
          {status === "uploading" && <span className="animate-spin">⟳</span>}
          {status === "success" && <FiCheck size={16} />}
          {status === "error" && <FiAlertCircle size={16} />}
          {message}
        </div>
      )}
    </div>
  );
}
