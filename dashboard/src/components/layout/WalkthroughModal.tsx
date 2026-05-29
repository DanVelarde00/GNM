"use client";

import { useState, useEffect, useCallback } from "react";
import {
  FiFolder,
  FiSearch,
  FiMessageSquare,
  FiCheckSquare,
  FiTag,
  FiActivity,
  FiUpload,
  FiGitBranch,
  FiX,
  FiArrowRight,
  FiArrowLeft,
} from "react-icons/fi";

interface Step {
  icon: React.ElementType;
  title: string;
  description: string;
  tip?: string;
}

const STEPS: Step[] = [
  {
    icon: FiGitBranch,
    title: "Welcome to GNM Dashboard",
    description:
      "This is your note management hub. Your Otter recordings and Inq pen notes are automatically pulled in, processed by AI, and turned into structured notes — all organised by project.",
    tip: "Everything updates in the background. You just read, ask questions, and act on what matters.",
  },
  {
    icon: FiFolder,
    title: "Vault",
    description:
      "Browse all your AI-processed notes. Notes are organised by project (Calico, Goldstone, etc.) with a People folder linking individuals across meetings.",
    tip: "Click any file in the left panel to read it. The edit button lets you correct anything the AI got wrong.",
  },
  {
    icon: FiSearch,
    title: "Search",
    description:
      "Full-text search across every note in the vault. Filter by project to narrow results. Finds matches in summaries, action items, decisions, and participant names.",
    tip: "Try searching for a person's name to find every meeting they appeared in.",
  },
  {
    icon: FiMessageSquare,
    title: "AI Chat",
    description:
      "Ask plain-English questions about your notes. The AI searches the vault for relevant context and answers from what's actually in your notes — not guesses.",
    tip: 'Try: "What are the open action items for Goldstone?" or "What did we decide about the SCE contract?"',
  },
  {
    icon: FiCheckSquare,
    title: "Action Items",
    description:
      "Every task extracted from every meeting, in one place. Filter by project or person, and tick items off as they're completed — the change saves back to the note.",
    tip: "Action items are extracted automatically whenever a new note is processed.",
  },
  {
    icon: FiTag,
    title: "Trackers",
    description:
      'Custom categories the AI extracts automatically from future notes. For example, a "Substations" tracker would pull out every substation mentioned across all meetings.',
    tip: "Create a tracker once and it will start populating from every note processed afterward.",
  },
  {
    icon: FiActivity,
    title: "Processor",
    description:
      "This is the engine behind GNM. It watches for new files, calls the AI to process them, and routes everything into the vault. You can start, stop, and watch live logs here.",
    tip: "If something isn't processing, check the live log here first — it will show exactly what happened.",
  },
  {
    icon: FiUpload,
    title: "Submit",
    description:
      "Drop in a file (PDF, Word doc, text file) or paste text directly to have it processed immediately. Useful for notes that didn't come through Otter.",
    tip: "PDFs must have a text layer — scanned images won't work.",
  },
  {
    icon: FiGitBranch,
    title: "Graph",
    description:
      "A visual map of how your notes connect through wiki-links. Each dot is a note; lines show connections. Colour indicates project. Click any node to open the note.",
    tip: "Zoom in with the scroll wheel to read note labels. Drag nodes to rearrange.",
  },
];

interface Props {
  open: boolean;
  onClose: () => void;
}

export function WalkthroughModal({ open, onClose }: Props) {
  const [step, setStep] = useState(0);

  const close = useCallback(() => {
    onClose();
    setStep(0);
  }, [onClose]);

  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
      if (e.key === "ArrowRight") setStep((s) => Math.min(s + 1, STEPS.length - 1));
      if (e.key === "ArrowLeft") setStep((s) => Math.max(s - 1, 0));
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, close]);

  if (!open) return null;

  const current = STEPS[step];
  const Icon = current.icon;
  const isLast = step === STEPS.length - 1;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
      onClick={(e) => e.target === e.currentTarget && close()}
    >
      <div className="bg-card border border-border rounded-xl shadow-2xl w-full max-w-lg mx-4 p-6 relative">
        {/* Close */}
        <button
          onClick={close}
          className="absolute top-4 right-4 text-muted hover:text-foreground transition-colors"
        >
          <FiX size={18} />
        </button>

        {/* Step dots */}
        <div className="flex items-center gap-1.5 mb-6">
          {STEPS.map((_, i) => (
            <button
              key={i}
              onClick={() => setStep(i)}
              className={`h-1.5 rounded-full transition-all ${
                i === step ? "w-6 bg-accent" : "w-1.5 bg-border hover:bg-muted"
              }`}
            />
          ))}
        </div>

        {/* Content */}
        <div className="flex gap-4 mb-6">
          <div className="shrink-0 w-12 h-12 rounded-lg bg-accent/10 flex items-center justify-center">
            <Icon size={24} className="text-accent" />
          </div>
          <div>
            <h2 className="text-base font-semibold mb-2">{current.title}</h2>
            <p className="text-sm text-muted leading-relaxed">{current.description}</p>
            {current.tip && (
              <p className="mt-3 text-xs text-accent/80 bg-accent/5 border border-accent/20 rounded-lg px-3 py-2 leading-relaxed">
                💡 {current.tip}
              </p>
            )}
          </div>
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => setStep((s) => Math.max(s - 1, 0))}
            disabled={step === 0}
            className="flex items-center gap-1.5 text-sm text-muted hover:text-foreground disabled:opacity-30 transition-colors"
          >
            <FiArrowLeft size={14} /> Back
          </button>

          <span className="text-xs text-muted">
            {step + 1} / {STEPS.length}
          </span>

          {isLast ? (
            <button
              onClick={close}
              className="flex items-center gap-1.5 text-sm bg-accent text-white px-4 py-1.5 rounded-lg hover:bg-accent-hover transition-colors"
            >
              Got it!
            </button>
          ) : (
            <button
              onClick={() => setStep((s) => s + 1)}
              className="flex items-center gap-1.5 text-sm text-accent hover:text-accent-hover transition-colors"
            >
              Next <FiArrowRight size={14} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
