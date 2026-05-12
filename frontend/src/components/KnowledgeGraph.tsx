import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
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

const NODE_LIMIT = 50;

const EMPTY_GRAPH: GraphData = { nodes: [], edges: [], total_entities: 0 };

function normalizeType(t: string): EntityType {
  const lower = (t || "").toLowerCase();
  if (lower === "company" || lower === "person" || lower === "technology" || lower === "product") {
    return lower;
  }
  return "other";
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

interface KnowledgeGraphProps {
  // Endpoint-backed; no props needed. Kept as a typed object so callers
  // that do `<KnowledgeGraph />` still type-check.
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

  useEffect(() => {
    fetchGraphData();
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

  useEffect(() => {
    if (!graphData || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Animation loop for force-directed graph
    const animate = () => {
      // Clear canvas + paint the themed background so dark mode actually
      // looks dark (the surrounding container is bg-card too).
      ctx.fillStyle = palette.background;
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.save();
      ctx.translate(canvas.width / 2, canvas.height / 2);
      ctx.scale(zoom, zoom);
      ctx.translate(-canvas.width / 2, -canvas.height / 2);

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

      // Draw edges — softer / lower contrast using border token with alpha.
      // We append "80" (50% alpha) to the hex border color so edges fade
      // into the background rather than competing with node fills.
      const edgeColor =
        palette.border.length === 7 ? `${palette.border}99` : palette.border;
      graphData.edges.forEach((edge) => {
        const pos1 = newPositions.get(edge.source);
        const pos2 = newPositions.get(edge.target);
        if (!pos1 || !pos2) return;

        const w = Math.max(1, Math.min(edge.weight || 1, 5));
        ctx.strokeStyle = edgeColor;
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

        const r = Math.max(12, Math.min(28, 12 + Math.sqrt(node.mention_count) * 3));

        // Node circle
        ctx.fillStyle = isActive ? palette.primary : baseColor[node.type];
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, r, 0, 2 * Math.PI);
        ctx.fill();

        // Node border — primary on the active node, themed border on the
        // rest. The active border is thicker so it pops without needing
        // any white halo.
        ctx.strokeStyle = isActive ? palette.primary : palette.border;
        ctx.lineWidth = isActive ? 3 : 1.5;
        ctx.stroke();

        // Node label — use the themed foreground so it stays readable on
        // both dark and light backgrounds.
        ctx.fillStyle = palette.label;
        ctx.font = "12px sans-serif";
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
  }, [graphData, zoom, selectedNode, palette]);

  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas || !graphData) return;

    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const cx = (event.clientX - rect.left) * scaleX;
    const cy = (event.clientY - rect.top) * scaleY;
    const x = (cx - canvas.width / 2) / zoom + canvas.width / 2;
    const y = (cy - canvas.height / 2) / zoom + canvas.height / 2;

    // Find clicked node
    for (const node of graphData.nodes) {
      const pos = nodePositionsRef.current.get(node.id);
      if (!pos) continue;

      const r = Math.max(12, Math.min(28, 12 + Math.sqrt(node.mention_count) * 3));
      const distance = Math.sqrt((x - pos.x) ** 2 + (y - pos.y) ** 2);
      if (distance < r + 4) {
        setSelectedNode(node);
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

  const getNodeIcon = (type: string) => {
    switch (type) {
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

  return (
    <div className="max-w-6xl mx-auto space-y-3">
      {/* Stat row — Linear-dense. ≤14px body, 12px padding. We surface the
          counts above the canvas so the page-top "what's in here" reading
          works without scrolling past 600px of graph. */}
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

      <Card className="bg-card border border-border">
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
                  onClick={() => setZoom(1)}
                  aria-label="Reset zoom"
                  className="h-7 w-7 p-0"
                >
                  <Maximize2 className="w-3.5 h-3.5" />
                </Button>
              </div>
            </div>

            {/* Selected Node Details */}
            {selectedNode && (
              <Card className="bg-accent/30 border border-primary/40">
                <CardHeader className="pb-2 pt-3 px-3">
                  <CardTitle className="text-sm flex items-center gap-2">
                    {getNodeIcon(selectedNode.type)}
                    {selectedNode.name}
                  </CardTitle>
                  <CardDescription>
                    <Badge variant="outline" className="text-[10px] h-4 px-1.5">
                      {selectedNode.type}
                    </Badge>
                  </CardDescription>
                </CardHeader>
                <CardContent className="px-3 pb-3 pt-0">
                  <div className="text-xs">
                    <p className="text-foreground">
                      <strong>Mentions:</strong> {selectedNode.mention_count}
                    </p>
                    {graphData && (
                      <div className="mt-2">
                        <p className="font-medium mb-1 text-foreground">
                          Co-mentioned with:
                        </p>
                        <div className="flex flex-wrap gap-1">
                          {graphData.edges
                            .filter(
                              (edge) =>
                                edge.source === selectedNode.id ||
                                edge.target === selectedNode.id
                            )
                            .map((edge, idx) => {
                              const connectedId =
                                edge.source === selectedNode.id
                                  ? edge.target
                                  : edge.source;
                              const connectedNode = graphData.nodes.find(
                                (n) => n.id === connectedId
                              );
                              if (!connectedNode) return null;
                              return (
                                <Badge
                                  key={idx}
                                  variant="secondary"
                                  className="text-[10px] h-4 px-1.5"
                                >
                                  {connectedNode.name}{" "}
                                  <span className="opacity-60">×{edge.weight}</span>
                                </Badge>
                              );
                            })}
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
