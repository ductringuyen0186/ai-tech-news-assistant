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
  Maximize2
} from "lucide-react";
import { toast } from "sonner";
import { API_ENDPOINTS, apiFetch } from "../config/api";

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
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const nodePositionsRef = useRef<Map<string, { x: number; y: number; vx: number; vy: number }>>(new Map());
  const animationFrameRef = useRef<number>();

  useEffect(() => {
    fetchGraphData();
  }, []);

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
      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);
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

      // Draw edges
      graphData.edges.forEach((edge) => {
        const pos1 = newPositions.get(edge.source);
        const pos2 = newPositions.get(edge.target);
        if (!pos1 || !pos2) return;

        const w = Math.max(1, Math.min(edge.weight || 1, 5));
        ctx.strokeStyle = "#cbd5e1";
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

        const nodeColor: Record<EntityType, string> = {
          company: "#3b82f6",
          person: "#10b981",
          technology: "#f59e0b",
          product: "#a855f7",
          other: "#94a3b8",
        };

        const r = Math.max(12, Math.min(28, 12 + Math.sqrt(node.mention_count) * 3));

        // Node circle
        ctx.fillStyle = nodeColor[node.type];
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, r, 0, 2 * Math.PI);
        ctx.fill();

        // Node border
        ctx.strokeStyle = selectedNode?.id === node.id ? "#1e40af" : "#fff";
        ctx.lineWidth = selectedNode?.id === node.id ? 3 : 2;
        ctx.stroke();

        // Node label
        ctx.fillStyle = "#1f2937";
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
  }, [graphData, zoom, selectedNode]);

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
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </CardContent>
      </Card>
    );
  }

  const isEmpty = !graphData || graphData.nodes.length === 0;

  return (
    <div className="max-w-6xl mx-auto space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Network className="w-5 h-5 text-blue-600" />
            Knowledge Graph
          </CardTitle>
          <CardDescription>
            Entities and co-mentions extracted from this week's articles. Node size scales with mention count; edge thickness with co-occurrence weight.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Legend */}
            <div className="flex flex-wrap items-center gap-4 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-blue-600 rounded-full" />
                <span>Companies</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-green-600 rounded-full" />
                <span>People</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-orange-500 rounded-full" />
                <span>Technologies</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-purple-500 rounded-full" />
                <span>Products</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-slate-400 rounded-full" />
                <span>Other</span>
              </div>
            </div>

            {errorMsg && (
              <div className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                Couldn't reach the knowledge graph endpoint: {errorMsg}
              </div>
            )}

            {isEmpty && !errorMsg && (
              <div className="rounded border border-blue-200 bg-blue-50 p-3 text-sm text-blue-700">
                No entities extracted yet. Run an ingest + summarize cycle to populate the graph.
              </div>
            )}

            {/* Graph Canvas */}
            <div className="relative border rounded-lg overflow-hidden bg-gray-50">
              <canvas
                ref={canvasRef}
                width={800}
                height={600}
                className="w-full cursor-pointer"
                onClick={handleCanvasClick}
                onWheel={handleCanvasWheel}
              />

              {/* Zoom Controls */}
              <div className="absolute top-4 right-4 flex flex-col gap-2">
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => setZoom(Math.min(zoom + 0.2, 3))}
                  aria-label="Zoom in"
                >
                  <ZoomIn className="w-4 h-4" />
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => setZoom(Math.max(zoom - 0.2, 0.4))}
                  aria-label="Zoom out"
                >
                  <ZoomOut className="w-4 h-4" />
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => setZoom(1)}
                  aria-label="Reset zoom"
                >
                  <Maximize2 className="w-4 h-4" />
                </Button>
              </div>
            </div>

            {/* Selected Node Details */}
            {selectedNode && (
              <Card className="bg-blue-50 border-blue-200">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg flex items-center gap-2">
                    {getNodeIcon(selectedNode.type)}
                    {selectedNode.name}
                  </CardTitle>
                  <CardDescription>
                    <Badge variant="outline" className="text-xs">
                      {selectedNode.type}
                    </Badge>
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-sm">
                    <p className="text-gray-700">
                      <strong>Mentions:</strong> {selectedNode.mention_count}
                    </p>
                    {graphData && (
                      <div className="mt-2">
                        <p className="font-semibold mb-1">Co-mentioned with:</p>
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
                                <Badge key={idx} variant="secondary" className="text-xs">
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

      {/* Stats */}
      {graphData && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-3xl font-bold text-blue-600">
                {graphData.nodes.filter((n) => n.type === "company").length}
              </div>
              <div className="text-sm text-gray-600">Companies</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-3xl font-bold text-green-600">
                {graphData.nodes.filter((n) => n.type === "person").length}
              </div>
              <div className="text-sm text-gray-600">People</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-3xl font-bold text-orange-500">
                {graphData.nodes.filter((n) => n.type === "technology").length}
              </div>
              <div className="text-sm text-gray-600">Technologies</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-3xl font-bold text-purple-500">
                {graphData.nodes.filter((n) => n.type === "product").length}
              </div>
              <div className="text-sm text-gray-600">Products</div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
