"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAppStore } from "@/store/useAppStore";
import type { GraphData } from "@/lib/types";

const PROJECT_COLORS: Record<string, string> = {
  Calico: "#6366f1",
  Cobia: "#22c55e",
  Goldstone: "#f59e0b",
  Vistra: "#ef4444",
  Zelestra: "#8b5cf6",
  Personal: "#06b6d4",
  People: "#ec4899",
  "": "#64748b",
};

interface SimNode {
  id: string;
  label: string;
  project: string;
  type: string;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
}

interface SimLink {
  source: SimNode;
  target: SimNode;
}

export function VaultGraph({ data }: { data: GraphData }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const setSelectedFilePath = useAppStore((s) => s.setSelectedFilePath);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container || !data.nodes.length) return;

    let cancelled = false;

    async function run() {
      const d3 = await import("d3");
      if (cancelled || !canvas || !container) return;

      const w = container.clientWidth;
      const h = container.clientHeight;
      canvas.width = w;
      canvas.height = h;
      const ctx = canvas.getContext("2d")!;

      // Clone so D3 mutations don't affect the original data
      const nodes: SimNode[] = data.nodes.map((n) => ({ ...n }));
      const nodeById = new Map(nodes.map((n) => [n.id, n]));
      const links: SimLink[] = data.links
        .map((l) => ({
          source: nodeById.get(l.source)!,
          target: nodeById.get(l.target)!,
        }))
        .filter((l) => l.source && l.target);

      const sim = d3
        .forceSimulation<SimNode>(nodes)
        .force(
          "link",
          d3
            .forceLink<SimNode, SimLink>(links)
            .id((d) => d.id)
            .distance(60)
            .strength(0.4)
        )
        .force("charge", d3.forceManyBody<SimNode>().strength(-120))
        .force("center", d3.forceCenter(w / 2, h / 2))
        .force("collision", d3.forceCollide<SimNode>(8));

      let transform = d3.zoomIdentity;
      let hoveredNode: SimNode | null = null;
      let draggedNode: SimNode | null = null;

      function nodeColor(n: SimNode) {
        return PROJECT_COLORS[n.project] ?? "#64748b";
      }

      function nodeRadius(n: SimNode) {
        return n.type === "person" ? 5 : 7;
      }

      function draw() {
        ctx.clearRect(0, 0, w, h);
        ctx.save();
        ctx.translate(transform.x, transform.y);
        ctx.scale(transform.k, transform.k);

        // Edges
        ctx.strokeStyle = "#334155";
        ctx.lineWidth = 0.8 / transform.k;
        links.forEach((l) => {
          if (l.source.x == null || l.target.x == null) return;
          ctx.beginPath();
          ctx.moveTo(l.source.x, l.source.y!);
          ctx.lineTo(l.target.x, l.target.y!);
          ctx.stroke();
        });

        // Nodes
        nodes.forEach((n) => {
          if (n.x == null) return;
          const r = nodeRadius(n);
          const isHovered = hoveredNode === n;

          ctx.beginPath();
          ctx.arc(n.x, n.y!, r, 0, 2 * Math.PI);
          ctx.fillStyle = nodeColor(n);
          ctx.fill();

          if (isHovered) {
            ctx.strokeStyle = "#fff";
            ctx.lineWidth = 1.5 / transform.k;
            ctx.stroke();
          }

          // Labels: always for hovered; only when zoomed in otherwise
          if (isHovered || transform.k > 2) {
            ctx.fillStyle = "#e2e8f0";
            const fontSize = Math.max(9, 11 / transform.k);
            ctx.font = `${fontSize}px sans-serif`;
            ctx.fillText(n.label, n.x + r + 3, n.y! + fontSize / 3);
          }
        });

        ctx.restore();
      }

      sim.on("tick", draw);

      // Zoom / pan
      const zoom = d3
        .zoom<HTMLCanvasElement, unknown>()
        .scaleExtent([0.1, 12])
        .on("zoom", (e) => {
          transform = e.transform;
          draw();
        });
      d3.select(canvas).call(zoom);

      // Drag
      function getNodeAt(mx: number, my: number): SimNode | null {
        return (
          nodes.find((n) => {
            if (n.x == null) return false;
            return Math.hypot(n.x - mx, n.y! - my) < nodeRadius(n) + 6;
          }) ?? null
        );
      }

      function toSim(e: MouseEvent) {
        const rect = canvas!.getBoundingClientRect();
        return {
          x: (e.clientX - rect.left - transform.x) / transform.k,
          y: (e.clientY - rect.top - transform.y) / transform.k,
        };
      }

      canvas.addEventListener("mousedown", (e) => {
        const { x, y } = toSim(e);
        const hit = getNodeAt(x, y);
        if (hit) {
          draggedNode = hit;
          hit.fx = hit.x;
          hit.fy = hit.y;
          sim.alphaTarget(0.3).restart();
        }
      });

      canvas.addEventListener("mousemove", (e) => {
        const { x, y } = toSim(e);
        if (draggedNode) {
          draggedNode.fx = x;
          draggedNode.fy = y;
        } else {
          const hit = getNodeAt(x, y);
          if (hit !== hoveredNode) {
            hoveredNode = hit;
            canvas!.style.cursor = hit ? "pointer" : "default";
            draw();
          }
        }
      });

      canvas.addEventListener("mouseup", () => {
        if (draggedNode) {
          draggedNode.fx = null;
          draggedNode.fy = null;
          sim.alphaTarget(0);
          draggedNode = null;
        }
      });

      canvas.addEventListener("click", (e) => {
        if (e.detail === 1) {
          const { x, y } = toSim(e);
          const hit = getNodeAt(x, y);
          if (hit) {
            setSelectedFilePath(hit.id);
            router.push("/vault");
          }
        }
      });

      return () => sim.stop();
    }

    const cleanup = run();
    return () => {
      cancelled = true;
      cleanup.then((fn) => fn?.());
    };
  }, [data, router, setSelectedFilePath]);

  return (
    <div ref={containerRef} className="w-full h-full">
      <canvas ref={canvasRef} className="w-full h-full block" />
    </div>
  );
}
