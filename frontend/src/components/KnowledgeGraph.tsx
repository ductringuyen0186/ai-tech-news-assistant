import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import {
  Network,
  Loader2,
  Building2,
  User,
  Cpu,
  Package,
  Sparkles,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Search as SearchIcon,
  X as XIcon,
  TrendingUp,
  ExternalLink,
} from "lucide-react";
import { toast } from "sonner";
import { API_ENDPOINTS, apiFetch } from "../config/api";
import { useTheme } from "./ThemeProvider";

type EntityType = "company" | "person" | "technology" | "product" | "other";

interface GraphNode {
  id: string;
  name: string;
  type: EntityType;
  // mention_count comes from the backend; we surface it as `connections`
  // so the existing details panel keeps working without a refactor.
  connections: number;
  mention_count: number;
}

interface GraphEdge {
  source: string;
  target: string;
  weight: number;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  total_entities: number;
}

interface ApiNode {
  id: string;
  name: string;
  type: string;
  mention_count: number;
}

interface ApiEdge {
  source: string;
  target: string;
  weight: number;
}

interface ApiResponse {
  nodes: ApiNode[];
  edges: ApiEdge[];
  total_entities?: number;
}

// ----- Polish iter 3 / Part B types -----------------------------------------

interface CoMention {
  id: number;
  name: string;
  type: string;
  count: number;
}

interface EntityArticle {
  id: number;
  title: string;
  source: string;
  url: string;
  published_at: string | null;
}

interface EntityDetail {
  id: number;
  name: string;
  type: string;
  mention_count: number;
  first_mention_at: string | null;
  co_mentions: CoMention[];
  articles: EntityArticle[];
}

interface TrendingEntity {
  id: number;
  name: string;
  type: string;
  mention_count: number;
  score: number;
}

const NODE_LIMIT = 50;

const EMPTY_GRAPH: GraphData = { nodes: [], edges: [], total_entities: 0 };

// All four filterable types — clicking a chip toggles its inclusion in the
// active type set. When the set is empty we render everything (default).
const FILTERABLE_TYPES: { key: EntityType; label: string }[] = [
  { key: "company", label: "Companies" },
  { key: "person", label: "People" },
  { key: "technology", label: "Technologies" },
  { key: "product", label: "Products" },
];

function normalizeType(t: string): EntityType {
  const lower = (t || "").toLowerCase();
  if (lower === "company" || lower === "person" || lower === "technology" || lower === "product") {
    return lower;
  }
  return "other";
}

function formatDate(value: string | null): string {
  if (!value) return "—";
  const dt = new Date(value.replace(" ", "T"));
  if (isNaN(dt.getTime())) return value;
  return dt.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/**
 * Read the resolved CSS variable for a token like `--primary` and return
 * it as a plain CSS color string. Tokens in this repo are stored as hex
 * (e.g. `#3B82F6`) so we can hand the raw value straight to canvas's
 * fillStyle/strokeStyle.
 *
 * We re-read on every theme change so the canvas re-skins when the user
 * flips between dark and light without a full reload.
 */
function readCssVar(name: string): string {
  if (typeof window === "undefined") return "";
  const v = getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
  return v;
}

interface CanvasPalette {
  background: string;
  border: string;
  primary: string;
  primaryFaded: string;
  muted: string;
  label: string;
  // Entity-type accent colors. We keep the same brand hues but pull the
  // muted/non-active variants from the design tokens so dark mode reads.
  company: string;
  person: string;
  technology: string;
  product: string;
  other: string;
}

function readPalette(): CanvasPalette {
  const primary = readCssVar("--primary") || "#3B82F6";
  const border = readCssVar("--border") || "#262626";
  const muted = readCssVar("--muted-foreground") || "#94a3b8";
  const card = readCssVar("--card") || "#111111";
  const fg = readCssVar("--foreground") || "#FAFAFA";
  return {
    background: card,
    border,
    primary,
    // Hex-tinted alpha; canvas accepts `#rrggbbaa`.
    primaryFaded: primary.length === 7 ? `${primary}80` : primary,
    muted,
    label: fg,
    company: "#3b82f6",
    person: "#10b981",
    technology: "#f59e0b",
    product: "#a855f7",
    other: muted,
  };
}

interface KnowledgeGraphProps {
  // Endpoint-backed; no props needed. Kept as a typed object so callers
  // that do `<KnowledgeGraph />` still type-check.
}

export function KnowledgeGraph({}: KnowledgeGraphProps) {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [zoom, setZoom] = useState(1);
  // Re-read palette on theme change so the canvas reskins live.
  const { theme } = useTheme();
  const [palette, setPalette] = useState<CanvasPalette>(() => readPalette());
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const nodePositionsRef = useRef<Map<string, { x: number; y: number; vx: number; vy: number }>>(new Map());
  const animationFrameRef = useRef<number>();

  // ----- B1: type filter chips -------------------------------------------
  const [activeTypes, setActiveTypes] = useState<Set<EntityType>>(new Set());

  // ----- B2: search + arrow-key cycle ------------------------------------
  const [searchQuery, setSearchQuery] = useState("");
  // Index into the filtered match list. -1 means "no focused match yet".
  const [focusedMatchIdx, setFocusedMatchIdx] = useState(-1);
  // Camera-centring offset for Enter-to-center; applied as a translate
  // delta on top of the canvas centre. (0, 0) = canvas centre.
  const [cameraOffset, setCameraOffset] = useState({ x: 0, y: 0 });
  const searchInputRef = useRef<HTMLInputElement>(null);

  // ----- B3: entity detail drawer ----------------------------------------
  const [detail, setDetail] = useState<EntityDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);
  const reduceMotion = useReducedMotion();

  // ----- B4: trending entities -------------------------------------------
  const [trending, setTrending] = useState<TrendingEntity[]>([]);

  useEffect(() => {
    fetchGraphData();
    fetchTrending();
  }, []);

  // Re-read the palette whenever the theme switches. The CSS variables
  // already changed at this point because the `dark` class flipped.
  useEffect(() => {
    setPalette(readPalette());
  }, [theme]);

  const fetchGraphData = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const url = `${API_ENDPOINTS.knowledgeGraph}?limit=${NODE_LIMIT}`;
      const data = await apiFetch<ApiResponse>(url);

      const nodes: GraphNode[] = (data.nodes || []).map((n) => ({
        id: n.id,
        name: n.name,
        type: normalizeType(n.type),
        connections: n.mention_count,
        mention_count: n.mention_count,
      }));
      const edges: GraphEdge[] = (data.edges || []).map((e) => ({
        source: e.source,
        target: e.target,
        weight: e.weight,
      }));
      const next: GraphData = {
        nodes,
        edges,
        total_entities: data.total_entities ?? nodes.length,
      };

      setGraphData(next);
      initializePositions(next);

      if (nodes.length === 0) {
        // Not an error — just nothing to show yet.
        toast.message("Knowledge graph is empty", {
          description: "Run an ingest + summarize cycle to populate entities.",
        });
      } else {
        toast.success(`Loaded ${nodes.length} entities`);
      }
    } catch (error) {
      console.error("Error fetching knowledge graph:", error);
      const message =
        error instanceof Error ? error.message : "Failed to load knowledge graph";
      setErrorMsg(message);
      // Show an empty graph rather than fall back to fake data.
      setGraphData(EMPTY_GRAPH);
      initializePositions(EMPTY_GRAPH);
      toast.error("Failed to load knowledge graph");
    } finally {
      setLoading(false);
    }
  };

  const fetchTrending = async () => {
    try {
      const data = await apiFetch<{ entities: TrendingEntity[] }>(
        `${API_ENDPOINTS.knowledgeGraphTrending}?days=7&limit=5`
      );
      setTrending(data.entities || []);
    } catch (error) {
      console.error("Error fetching trending entities:", error);
      setTrending([]);
    }
  };

  const initializePositions = (data: GraphData) => {
    const positions = new Map();
    const centerX = 400;
    const centerY = 300;
    const radius = Math.min(220, 80 + data.nodes.length * 4);

    data.nodes.forEach((node, index) => {
      const angle = (index / Math.max(data.nodes.length, 1)) * 2 * Math.PI;
      positions.set(node.id, {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
        vx: 0,
        vy: 0,
      });
    });

    nodePositionsRef.current = positions;
  };

  // -- B2: derive the ordered list of matches for the current search ------
  const matches = useMemo(() => {
    if (!graphData) return [] as GraphNode[];
    const q = searchQuery.trim().toLowerCase();
    if (!q) return [] as GraphNode[];
    return graphData.nodes.filter((n) =>
      n.name.toLowerCase().includes(q)
    );
  }, [graphData, searchQuery]);

  // Reset the focused index when the match list changes meaningfully.
  useEffect(() => {
    if (matches.length === 0) {
      setFocusedMatchIdx(-1);
    } else if (focusedMatchIdx >= matches.length) {
      setFocusedMatchIdx(0);
    } else if (focusedMatchIdx === -1) {
      setFocusedMatchIdx(0);
    }
    // We intentionally don't include focusedMatchIdx — that would loop.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [matches]);

  // -- Canvas draw loop ----------------------------------------------------
  useEffect(() => {
    if (!graphData || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Set of node IDs that match the search query (lowercased).
    const matchSet = new Set(matches.map((m) => m.id));
    const focusedId =
      focusedMatchIdx >= 0 && matches[focusedMatchIdx]
        ? matches[focusedMatchIdx].id
        : null;
    const typeFilterActive = activeTypes.size > 0;

    // Animation loop for force-directed graph
    const animate = () => {
      // Clear canvas + paint the themed background so dark mode actually
      // looks dark (the surrounding container is bg-card too).
      ctx.fillStyle = palette.background;
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.save();
      ctx.translate(canvas.width / 2, canvas.height / 2);
      ctx.scale(zoom, zoom);
      ctx.translate(-canvas.width / 2 + cameraOffset.x, -canvas.height / 2 + cameraOffset.y);

      // Apply forces
      const newPositions = new Map(nodePositionsRef.current);

      // Repulsion between nodes
      graphData.nodes.forEach((node1) => {
        const pos1 = newPositions.get(node1.id);
        if (!pos1) return;

        graphData.nodes.forEach((node2) => {
          if (node1.id === node2.id) return;
          const pos2 = newPositions.get(node2.id);
          if (!pos2) return;

          const dx = pos1.x - pos2.x;
          const dy = pos1.y - pos2.y;
          const distance = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = 1000 / (distance * distance);

          pos1.vx += (dx / distance) * force;
          pos1.vy += (dy / distance) * force;
        });
      });

      // Attraction along edges (heavier-weight edges pull harder)
      graphData.edges.forEach((edge) => {
        const pos1 = newPositions.get(edge.source);
        const pos2 = newPositions.get(edge.target);
        if (!pos1 || !pos2) return;

        const dx = pos2.x - pos1.x;
        const dy = pos2.y - pos1.y;
        const distance = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = distance * 0.001 * Math.min(edge.weight || 1, 5);

        pos1.vx += (dx / distance) * force;
        pos1.vy += (dy / distance) * force;
        pos2.vx -= (dx / distance) * force;
        pos2.vy -= (dy / distance) * force;
      });

      // Update positions
      newPositions.forEach((pos) => {
        pos.x += pos.vx;
        pos.y += pos.vy;
        pos.vx *= 0.8; // Damping
        pos.vy *= 0.8;

        // Keep in bounds
        pos.x = Math.max(50, Math.min(750, pos.x));
        pos.y = Math.max(50, Math.min(550, pos.y));
      });

      nodePositionsRef.current = newPositions;

      // Helper — should this node be "dimmed" (filtered out / unmatched)?
      const isDimmed = (node: GraphNode): boolean => {
        if (typeFilterActive && !activeTypes.has(node.type)) return true;
        if (searchQuery.trim() && !matchSet.has(node.id)) return true;
        return false;
      };

      // Draw edges — softer / lower contrast using border token with alpha.
      // We append "80" (50% alpha) to the hex border color so edges fade
      // into the background rather than competing with node fills.
      const edgeColor =
        palette.border.length === 7 ? `${palette.border}99` : palette.border;
      const edgeDim =
        palette.border.length === 7 ? `${palette.border}33` : palette.border;
      graphData.edges.forEach((edge) => {
        const pos1 = newPositions.get(edge.source);
        const pos2 = newPositions.get(edge.target);
        if (!pos1 || !pos2) return;
        const n1 = graphData.nodes.find((n) => n.id === edge.source);
        const n2 = graphData.nodes.find((n) => n.id === edge.target);
        const edgeFilteredOut =
          (n1 && isDimmed(n1)) || (n2 && isDimmed(n2));

        const w = Math.max(1, Math.min(edge.weight || 1, 5));
        ctx.strokeStyle = edgeFilteredOut ? edgeDim : edgeColor;
        ctx.lineWidth = 0.8 + w * 0.4;
        ctx.beginPath();
        ctx.moveTo(pos1.x, pos1.y);
        ctx.lineTo(pos2.x, pos2.y);
        ctx.stroke();
      });

      // Draw nodes (radius scales with mention_count, capped)
      graphData.nodes.forEach((node) => {
        const pos = newPositions.get(node.id);
        if (!pos) return;

        const isActive = selectedNode?.id === node.id;
        const dimmed = isDimmed(node);
        const isFocused = focusedId === node.id;
        const isMatch = matchSet.has(node.id);

        // Active node always uses --primary so the highlight reads as
        // "this is the one you selected". Non-active nodes keep the
        // entity-type accent palette so the legend still makes sense.
        const baseColor: Record<EntityType, string> = {
          company: palette.company,
          person: palette.person,
          technology: palette.technology,
          product: palette.product,
          other: palette.other,
        };

        const baseRadius = Math.max(12, Math.min(28, 12 + Math.sqrt(node.mention_count) * 3));
        // B2: matched nodes render slightly larger; focused match is largest.
        const r = isFocused ? baseRadius + 4 : isMatch ? baseRadius + 2 : baseRadius;

        // Node circle
        let fill: string;
        if (isActive || isFocused) {
          fill = palette.primary;
        } else if (dimmed) {
          fill =
            palette.muted.length === 7 ? `${palette.muted}40` : palette.muted;
        } else {
          fill = baseColor[node.type];
        }
        ctx.fillStyle = fill;
        ctx.globalAlpha = dimmed ? 0.35 : 1;
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, r, 0, 2 * Math.PI);
        ctx.fill();

        // Node border — primary on active/focused, themed border elsewhere.
        ctx.strokeStyle = isActive || isFocused ? palette.primary : palette.border;
        ctx.lineWidth = isActive || isFocused ? 3 : 1.5;
        ctx.stroke();
        ctx.globalAlpha = 1;

        // Node label — use the themed foreground so it stays readable on
        // both dark and light backgrounds.
        ctx.fillStyle = dimmed ? palette.muted : palette.label;
        ctx.font = isMatch ? "bold 12px sans-serif" : "12px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(node.name, pos.x, pos.y + r + 14);
      });

      ctx.restore();
      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    };
  }, [graphData, zoom, selectedNode, palette, matches, focusedMatchIdx, activeTypes, searchQuery, cameraOffset]);

  // -- B3: load detail and open drawer ------------------------------------
  const openDetail = useCallback(async (entityId: string | number) => {
    setDetailOpen(true);
    setDetailLoading(true);
    try {
      const data = await apiFetch<EntityDetail>(
        API_ENDPOINTS.knowledgeGraphEntity(entityId)
      );
      setDetail(data);
    } catch (err) {
      console.error("Failed to load entity detail", err);
      toast.error("Failed to load entity detail");
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const closeDetail = useCallback(() => {
    setDetailOpen(false);
  }, []);

  // -- B2: arrow-key handler on the search input --------------------------
  const handleSearchKey = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (matches.length === 0) {
        if (e.key === "Escape") {
          setSearchQuery("");
        }
        return;
      }
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setFocusedMatchIdx((idx) =>
          idx + 1 >= matches.length ? 0 : idx + 1
        );
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setFocusedMatchIdx((idx) =>
          idx <= 0 ? matches.length - 1 : idx - 1
        );
      } else if (e.key === "Enter") {
        e.preventDefault();
        const m = matches[focusedMatchIdx >= 0 ? focusedMatchIdx : 0];
        if (m) {
          // Center camera: compute offset so the matched node lands at the
          // canvas centre. Positions live in the 0..800 x 0..600 logical
          // space; centring means we offset by (400 - x, 300 - y).
          const pos = nodePositionsRef.current.get(m.id);
          if (pos) {
            setCameraOffset({ x: 400 - pos.x, y: 300 - pos.y });
          }
          setSelectedNode(m);
        }
      } else if (e.key === "Escape") {
        e.preventDefault();
        setSearchQuery("");
        setFocusedMatchIdx(-1);
        setCameraOffset({ x: 0, y: 0 });
      }
    },
    [matches, focusedMatchIdx]
  );

  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas || !graphData) return;

    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const cx = (event.clientX - rect.left) * scaleX;
    const cy = (event.clientY - rect.top) * scaleY;
    // Reverse the canvas transform: undo the cameraOffset translate as well
    // as the zoom-from-centre.
    const x =
      (cx - canvas.width / 2) / zoom + canvas.width / 2 - cameraOffset.x;
    const y =
      (cy - canvas.height / 2) / zoom + canvas.height / 2 - cameraOffset.y;

    // Find clicked node
    for (const node of graphData.nodes) {
      const pos = nodePositionsRef.current.get(node.id);
      if (!pos) continue;

      const r = Math.max(12, Math.min(28, 12 + Math.sqrt(node.mention_count) * 3));
      const distance = Math.sqrt((x - pos.x) ** 2 + (y - pos.y) ** 2);
      if (distance < r + 4) {
        setSelectedNode(node);
        // B3: open the detail drawer for the clicked node.
        openDetail(node.id);
        return;
      }
    }

    setSelectedNode(null);
  };

  const handleCanvasWheel = (event: React.WheelEvent<HTMLCanvasElement>) => {
    // Simple ctrl/cmd-scroll zoom. Trackpads send small deltaY values too.
    if (!event.ctrlKey && !event.metaKey) return;
    event.preventDefault();
    const delta = event.deltaY > 0 ? -0.1 : 0.1;
    setZoom((z) => Math.max(0.4, Math.min(3, z + delta)));
  };

  const toggleType = (t: EntityType) => {
    setActiveTypes((prev) => {
      const next = new Set(prev);
      if (next.has(t)) next.delete(t);
      else next.add(t);
      return next;
    });
  };

  const getNodeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case "company":
        return <Building2 className="w-4 h-4" />;
      case "person":
        return <User className="w-4 h-4" />;
      case "technology":
        return <Cpu className="w-4 h-4" />;
      case "product":
        return <Package className="w-4 h-4" />;
      default:
        return <Sparkles className="w-4 h-4" />;
    }
  };

  if (loading) {
    return (
      <Card className="bg-card border border-border">
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </CardContent>
      </Card>
    );
  }

  const isEmpty = !graphData || graphData.nodes.length === 0;

  // Stat counts used by the dense stat card row.
  const companyCount = graphData
    ? graphData.nodes.filter((n) => n.type === "company").length
    : 0;
  const personCount = graphData
    ? graphData.nodes.filter((n) => n.type === "person").length
    : 0;
  const techCount = graphData
    ? graphData.nodes.filter((n) => n.type === "technology").length
    : 0;
  const productCount = graphData
    ? graphData.nodes.filter((n) => n.type === "product").length
    : 0;

  // Color lookup for the detail-panel co-mention chips.
  const typeColor: Record<string, string> = {
    company: "#3b82f6",
    person: "#10b981",
    technology: "#f59e0b",
    product: "#a855f7",
  };

  return (
    <div className="max-w-6xl mx-auto space-y-3">
      {/* Stat row — Linear-dense. ≤14px body, 12px padding. */}
      {graphData && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          <Card
            data-testid="kg-stat-companies"
            className="bg-card border border-border"
          >
            <CardContent className="p-3">
              <div className="text-[11px] uppercase tracking-wide text-muted-foreground">
                Companies
              </div>
              <div
                className="text-xl font-semibold mt-1"
                style={{ color: "#3b82f6" }}
              >
                {companyCount}
              </div>
            </CardContent>
          </Card>
          <Card
            data-testid="kg-stat-people"
            className="bg-card border border-border"
          >
            <CardContent className="p-3">
              <div className="text-[11px] uppercase tracking-wide text-muted-foreground">
                People
              </div>
              <div
                className="text-xl font-semibold mt-1"
                style={{ color: "#10b981" }}
              >
                {personCount}
              </div>
            </CardContent>
          </Card>
          <Card
            data-testid="kg-stat-technologies"
            className="bg-card border border-border"
          >
            <CardContent className="p-3">
              <div className="text-[11px] uppercase tracking-wide text-muted-foreground">
                Technologies
              </div>
              <div
                className="text-xl font-semibold mt-1"
                style={{ color: "#f59e0b" }}
              >
                {techCount}
              </div>
            </CardContent>
          </Card>
          <Card
            data-testid="kg-stat-products"
            className="bg-card border border-border"
          >
            <CardContent className="p-3">
              <div className="text-[11px] uppercase tracking-wide text-muted-foreground">
                Products
              </div>
              <div
                className="text-xl font-semibold mt-1"
                style={{ color: "#a855f7" }}
              >
                {productCount}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-3">
        <Card className="bg-card border border-border lg:col-span-3">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-[15px]">
              <Network className="w-4 h-4 text-primary" />
              Knowledge Graph
            </CardTitle>
            <CardDescription className="text-xs">
              Entities and co-mentions extracted from this week's articles.
              Node size scales with mention count; edge thickness with
              co-occurrence weight.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="space-y-3">
              {/* B1: type filter chips ------------------------------------ */}
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="text-[11px] text-muted-foreground pr-1">
                  Filter:
                </span>
                {FILTERABLE_TYPES.map(({ key, label }) => {
                  const isOn = activeTypes.has(key);
                  return (
                    <button
                      key={key}
                      type="button"
                      data-testid={`kg-type-filter-${label.toLowerCase()}`}
                      onClick={() => toggleType(key)}
                      className={[
                        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] transition-colors",
                        isOn
                          ? "border-primary bg-primary/10 text-primary"
                          : "border-border bg-card text-foreground hover:bg-accent/40",
                      ].join(" ")}
                    >
                      <span
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: typeColor[key] || palette.muted }}
                      />
                      {label}
                    </button>
                  );
                })}
                {activeTypes.size > 0 && (
                  <button
                    type="button"
                    onClick={() => setActiveTypes(new Set())}
                    className="text-[11px] text-muted-foreground hover:text-foreground underline pl-1"
                  >
                    Clear
                  </button>
                )}
              </div>

              {/* B2: search input ---------------------------------------- */}
              <div className="relative max-w-md">
                <SearchIcon className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground pointer-events-none" />
                <Input
                  ref={searchInputRef}
                  data-testid="kg-search-input"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={handleSearchKey}
                  placeholder="Search entities... (↑/↓ to cycle, Enter to centre, Esc to clear)"
                  className="h-8 pl-7 pr-7 text-xs"
                />
                {searchQuery && (
                  <button
                    type="button"
                    aria-label="Clear search"
                    onClick={() => {
                      setSearchQuery("");
                      setFocusedMatchIdx(-1);
                      setCameraOffset({ x: 0, y: 0 });
                      searchInputRef.current?.focus();
                    }}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  >
                    <XIcon className="w-3.5 h-3.5" />
                  </button>
                )}
                {searchQuery && (
                  <div className="absolute right-7 top-1/2 -translate-y-1/2 text-[10px] text-muted-foreground tabular-nums pointer-events-none">
                    {matches.length === 0
                      ? "No matches"
                      : `${focusedMatchIdx + 1}/${matches.length}`}
                  </div>
                )}
              </div>

              {/* Legend — compact, 12px text. */}
              <div className="flex flex-wrap items-center gap-3 text-[11px] text-muted-foreground">
                <div className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: "#3b82f6" }} />
                  <span>Companies</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: "#10b981" }} />
                  <span>People</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: "#f59e0b" }} />
                  <span>Technologies</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: "#a855f7" }} />
                  <span>Products</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-muted-foreground" />
                  <span>Other</span>
                </div>
              </div>

              {errorMsg && (
                <div className="rounded-md border border-destructive/40 bg-destructive/10 p-2.5 text-xs text-destructive">
                  Couldn't reach the knowledge graph endpoint: {errorMsg}
                </div>
              )}

              {isEmpty && !errorMsg && (
                <div
                  data-testid="kg-empty-state"
                  className="rounded-md border border-border bg-muted/30 p-6 text-center"
                >
                  <Network className="w-10 h-10 text-muted-foreground mx-auto mb-2" />
                  <p className="text-sm font-medium text-foreground">
                    No entities indexed yet
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    No entities extracted yet. Run an ingest + summarize cycle
                    to populate the graph.
                  </p>
                </div>
              )}

              {/* Graph Canvas — bg matches --card so dark mode looks dark. */}
              <div className="relative rounded-md overflow-hidden border border-border bg-card">
                <canvas
                  ref={canvasRef}
                  width={800}
                  height={600}
                  className="w-full cursor-pointer"
                  onClick={handleCanvasClick}
                  onWheel={handleCanvasWheel}
                />

                {/* Zoom Controls */}
                <div className="absolute top-3 right-3 flex flex-col gap-1.5">
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => setZoom(Math.min(zoom + 0.2, 3))}
                    aria-label="Zoom in"
                    className="h-7 w-7 p-0"
                  >
                    <ZoomIn className="w-3.5 h-3.5" />
                  </Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => setZoom(Math.max(zoom - 0.2, 0.4))}
                    aria-label="Zoom out"
                    className="h-7 w-7 p-0"
                  >
                    <ZoomOut className="w-3.5 h-3.5" />
                  </Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => {
                      setZoom(1);
                      setCameraOffset({ x: 0, y: 0 });
                    }}
                    aria-label="Reset zoom"
                    className="h-7 w-7 p-0"
                  >
                    <Maximize2 className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* B4: Trending entities sidebar ------------------------------- */}
        <Card
          data-testid="kg-trending-widget"
          className="bg-card border border-border h-fit"
        >
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-primary" />
              Trending this week
            </CardTitle>
            <CardDescription className="text-xs">
              Top mentions, recency-weighted
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0 pb-3">
            {trending.length === 0 ? (
              <p className="text-xs text-muted-foreground py-2">
                No trends in window yet.
              </p>
            ) : (
              <ol className="space-y-1.5">
                {trending.map((t, idx) => (
                  <li key={t.id}>
                    <button
                      type="button"
                      data-testid={`kg-trending-entity-${t.id}`}
                      onClick={() => openDetail(t.id)}
                      className="w-full flex items-center gap-2 p-1.5 rounded-md border border-transparent hover:border-border hover:bg-accent/40 transition-colors text-left"
                    >
                      <span className="text-[10px] font-medium text-muted-foreground tabular-nums w-4">
                        {idx + 1}
                      </span>
                      <span
                        className="w-2 h-2 rounded-full shrink-0"
                        style={{
                          backgroundColor:
                            typeColor[t.type.toLowerCase()] || palette.muted,
                        }}
                      />
                      <span className="flex-1 text-xs truncate text-foreground">
                        {t.name}
                      </span>
                      <Badge
                        variant="secondary"
                        className="h-4 px-1 text-[10px] font-normal"
                      >
                        {t.mention_count}
                      </Badge>
                    </button>
                  </li>
                ))}
              </ol>
            )}
          </CardContent>
        </Card>
      </div>

      {/* B3: entity detail drawer ------------------------------------- */}
      <AnimatePresence>
        {detailOpen && (
          <>
            {/* Click-outside scrim */}
            <motion.div
              key="kg-detail-scrim"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: reduceMotion ? 0 : 0.15 }}
              className="fixed inset-0 z-40"
              style={{ backgroundColor: "rgba(0,0,0,0.35)" }}
              onClick={closeDetail}
            />
            <motion.aside
              key="kg-detail-drawer"
              data-testid="kg-entity-detail-panel"
              initial={reduceMotion ? { x: 0 } : { x: "100%" }}
              animate={{ x: 0 }}
              exit={reduceMotion ? { x: 0 } : { x: "100%" }}
              transition={{ duration: reduceMotion ? 0 : 0.22, ease: "easeOut" }}
              className="fixed right-0 top-0 bottom-0 z-50 kg-drawer-width bg-card border-l border-border shadow-xl flex flex-col"
              role="dialog"
              aria-label="Entity detail"
            >
              <div className="flex items-start justify-between gap-3 px-4 py-3 border-b border-border">
                <div className="flex-1 min-w-0">
                  {detailLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
                  ) : detail ? (
                    <>
                      <h2 className="text-base font-semibold text-foreground flex items-center gap-2 truncate">
                        {getNodeIcon(detail.type)}
                        <span className="truncate">{detail.name}</span>
                      </h2>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge
                          variant="outline"
                          className="h-4 px-1.5 text-[10px] capitalize"
                          style={{
                            color:
                              typeColor[detail.type.toLowerCase()] || undefined,
                            borderColor:
                              typeColor[detail.type.toLowerCase()] || undefined,
                          }}
                        >
                          {detail.type}
                        </Badge>
                        <span className="text-[11px] text-muted-foreground">
                          {detail.mention_count} mention
                          {detail.mention_count === 1 ? "" : "s"}
                        </span>
                      </div>
                    </>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      Failed to load entity.
                    </p>
                  )}
                </div>
                <button
                  type="button"
                  data-testid="kg-entity-detail-close-btn"
                  onClick={closeDetail}
                  aria-label="Close detail panel"
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  <XIcon className="w-4 h-4" />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4 text-sm">
                {detailLoading && (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-primary" />
                  </div>
                )}
                {!detailLoading && detail && (
                  <>
                    {/* Meta */}
                    <div className="space-y-1">
                      <div className="text-[10px] uppercase tracking-wide text-muted-foreground">
                        First mention
                      </div>
                      <div className="text-xs text-foreground">
                        {formatDate(detail.first_mention_at)}
                      </div>
                    </div>

                    {/* Co-mentions */}
                    <div>
                      <div className="text-[10px] uppercase tracking-wide text-muted-foreground mb-1.5">
                        Top co-mentions
                      </div>
                      {detail.co_mentions.length === 0 ? (
                        <p className="text-xs text-muted-foreground">
                          No other entities co-mentioned in the same articles.
                        </p>
                      ) : (
                        <div className="flex flex-wrap gap-1">
                          {detail.co_mentions.map((c) => (
                            <button
                              key={c.id}
                              type="button"
                              data-testid={`kg-entity-co-mention-${c.id}`}
                              onClick={() => openDetail(c.id)}
                              className="inline-flex items-center gap-1 rounded-full border border-border bg-card px-2 py-0.5 text-[11px] hover:bg-accent/40 transition-colors"
                            >
                              <span
                                className="w-1.5 h-1.5 rounded-full"
                                style={{
                                  backgroundColor:
                                    typeColor[c.type.toLowerCase()] || palette.muted,
                                }}
                              />
                              <span>{c.name}</span>
                              <span className="opacity-60 tabular-nums">
                                ×{c.count}
                              </span>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Articles */}
                    <div>
                      <div className="text-[10px] uppercase tracking-wide text-muted-foreground mb-1.5">
                        Mentioned in
                      </div>
                      {detail.articles.length === 0 ? (
                        <p className="text-xs text-muted-foreground">
                          No articles found.
                        </p>
                      ) : (
                        <ul className="space-y-2">
                          {detail.articles.map((a) => (
                            <li
                              key={a.id}
                              className="border-l-2 border-border pl-2"
                            >
                              <a
                                data-testid={`kg-entity-article-${a.id}`}
                                href={a.url || "#"}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="block group"
                              >
                                <div className="text-xs font-medium text-foreground group-hover:text-primary leading-snug flex items-start gap-1">
                                  <span className="flex-1">{a.title}</span>
                                  <ExternalLink className="w-3 h-3 text-muted-foreground group-hover:text-primary shrink-0 mt-0.5" />
                                </div>
                                <div className="flex items-center gap-2 mt-0.5 text-[10px] text-muted-foreground">
                                  <span>{a.source}</span>
                                  <span>·</span>
                                  <span>{formatDate(a.published_at)}</span>
                                </div>
                              </a>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </>
                )}
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
