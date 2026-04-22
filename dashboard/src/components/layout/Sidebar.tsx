"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  FiFolder,
  FiMessageSquare,
  FiCheckSquare,
  FiTag,
  FiActivity,
  FiUpload,
  FiSearch,
} from "react-icons/fi";

const NAV = [
  { href: "/vault", label: "Vault", icon: FiFolder },
  { href: "/search", label: "Search", icon: FiSearch },
  { href: "/chat", label: "AI Chat", icon: FiMessageSquare },
  { href: "/action-items", label: "Action Items", icon: FiCheckSquare },
  { href: "/trackers", label: "Trackers", icon: FiTag },
  { href: "/processor", label: "Processor", icon: FiActivity },
  { href: "/submit", label: "Submit", icon: FiUpload },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 bg-sidebar border-r border-border flex flex-col shrink-0">
      <div className="p-4 border-b border-border">
        <h1 className="text-lg font-bold text-accent">GNM Dashboard</h1>
        <p className="text-xs text-muted mt-0.5">Glen&apos;s Note Management</p>
      </div>
      <nav className="flex-1 py-2">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname?.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                active
                  ? "bg-accent/10 text-accent border-r-2 border-accent"
                  : "text-muted hover:text-foreground hover:bg-white/5"
              }`}
            >
              <Icon size={18} />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-border text-xs text-muted">
        Phase 2 &mdash; Dashboard
      </div>
    </aside>
  );
}
