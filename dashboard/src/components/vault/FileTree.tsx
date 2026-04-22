"use client";

import { useState } from "react";
import { FiChevronRight, FiChevronDown, FiFile, FiFolder } from "react-icons/fi";
import type { FileNode } from "@/lib/types";
import { useAppStore } from "@/store/useAppStore";

function TreeNode({ node, depth = 0 }: { node: FileNode; depth?: number }) {
  const [open, setOpen] = useState(depth < 2);
  const { selectedFilePath, setSelectedFilePath } = useAppStore();
  const isSelected = selectedFilePath === node.path;

  if (node.is_dir) {
    return (
      <div>
        <button
          onClick={() => setOpen(!open)}
          className="flex items-center gap-1.5 w-full text-left px-2 py-1 text-sm hover:bg-white/5 rounded transition-colors"
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
        >
          {open ? <FiChevronDown size={14} /> : <FiChevronRight size={14} />}
          <FiFolder size={14} className="text-accent" />
          <span className="truncate">{node.name}</span>
        </button>
        {open && node.children.map((child) => (
          <TreeNode key={child.path} node={child} depth={depth + 1} />
        ))}
      </div>
    );
  }

  return (
    <button
      onClick={() => setSelectedFilePath(node.path)}
      className={`flex items-center gap-1.5 w-full text-left px-2 py-1 text-sm rounded transition-colors ${
        isSelected ? "bg-accent/15 text-accent" : "hover:bg-white/5 text-muted"
      }`}
      style={{ paddingLeft: `${depth * 16 + 8}px` }}
    >
      <FiFile size={14} />
      <span className="truncate">{node.name}</span>
    </button>
  );
}

export function FileTree({ nodes }: { nodes: FileNode[] }) {
  return (
    <div className="py-1 overflow-auto">
      {nodes.map((node) => (
        <TreeNode key={node.path} node={node} />
      ))}
    </div>
  );
}
