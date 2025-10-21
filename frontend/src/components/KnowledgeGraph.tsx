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
  ZoomIn, 
  ZoomOut,
  Maximize2
} from "lucide-react";
import { toast } from "sonner";

interface GraphNode {
  id: string;
  name: string;
  type: "company" | "person" | "technology";
  connections: number;
}

interface GraphEdge {
  source: string;
  target: string;
  relationship: string;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

interface KnowledgeGraphProps {
  // No props needed - using mock data for now
}

export function KnowledgeGraph({}: KnowledgeGraphProps) {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [zoom, setZoom] = useState(1);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const nodePositionsRef = useRef<Map<string, { x: number; y: number; vx: number; vy: number }>>(new Map());
  const animationFrameRef = useRef<number>();

  useEffect(() => {
    fetchGraphData();
  }, []);

  const fetchGraphData = async () => {
    try {
      // Mock knowledge graph data for now
      const mockData: GraphData = {
        nodes: [
          { id: "openai", name: "OpenAI", type: "company", connections: 15 },
          { id: "anthropic", name: "Anthropic", type: "company", connections: 10 },
          { id: "google", name: "Google", type: "company", connections: 20 },
          { id: "gpt4", name: "GPT-4", type: "technology", connections: 12 },
          { id: "claude", name: "Claude", type: "technology", connections: 8 },
          { id: "sam-altman", name: "Sam Altman", type: "person", connections: 14 },
          { id: "transformers", name: "Transformers", type: "technology", connections: 18 },
          { id: "llm", name: "Large Language Models", type: "technology", connections: 16 },
        ],
        edges: [
          { source: "openai", target: "gpt4", relationship: "develops" },
          { source: "anthropic", target: "claude", relationship: "develops" },
          { source: "sam-altman", target: "openai", relationship: "leads" },
          { source: "gpt4", target: "llm", relationship: "is-a" },
          { source: "claude", target: "llm", relationship: "is-a" },
          { source: "llm", target: "transformers", relationship: "uses" },
          { source: "google", target: "transformers", relationship: "invented" },
          { source: "google", target: "llm", relationship: "develops" },
        ]
      };
      
      setGraphData(mockData);
      initializePositions(mockData);
      toast.success("Knowledge graph loaded");
    } catch (error) {
      console.error("Error fetching knowledge graph:", error);
      toast.error("Failed to load knowledge graph");
    } finally {
      setLoading(false);
    }
  };

  const initializePositions = (data: GraphData) => {
    const positions = new Map();
    const centerX = 400;
    const centerY = 300;
    const radius = 200;

    data.nodes.forEach((node, index) => {
      const angle = (index / data.nodes.length) * 2 * Math.PI;
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

      // Attraction along edges
      graphData.edges.forEach((edge) => {
        const pos1 = newPositions.get(edge.source);
        const pos2 = newPositions.get(edge.target);
        if (!pos1 || !pos2) return;

        const dx = pos2.x - pos1.x;
        const dy = pos2.y - pos1.y;
        const distance = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = distance * 0.001;

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
      ctx.strokeStyle = "#cbd5e1";
      ctx.lineWidth = 1.5;
      graphData.edges.forEach((edge) => {
        const pos1 = newPositions.get(edge.source);
        const pos2 = newPositions.get(edge.target);
        if (!pos1 || !pos2) return;

        ctx.beginPath();
        ctx.moveTo(pos1.x, pos1.y);
        ctx.lineTo(pos2.x, pos2.y);
        ctx.stroke();
      });

      // Draw nodes
      graphData.nodes.forEach((node) => {
        const pos = newPositions.get(node.id);
        if (!pos) return;

        const nodeColor = {
          company: "#3b82f6",
          person: "#10b981",
          technology: "#f59e0b",
        }[node.type];

        // Node circle
        ctx.fillStyle = nodeColor;
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, 20, 0, 2 * Math.PI);
        ctx.fill();

        // Node border
        ctx.strokeStyle = selectedNode?.id === node.id ? "#1e40af" : "#fff";
        ctx.lineWidth = selectedNode?.id === node.id ? 3 : 2;
        ctx.stroke();

        // Node label
        ctx.fillStyle = "#1f2937";
        ctx.font = "12px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(node.name, pos.x, pos.y + 35);
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
    const x = ((event.clientX - rect.left) - canvas.width / 2) / zoom + canvas.width / 2;
    const y = ((event.clientY - rect.top) - canvas.height / 2) / zoom + canvas.height / 2;

    // Find clicked node
    for (const node of graphData.nodes) {
      const pos = nodePositionsRef.current.get(node.id);
      if (!pos) continue;

      const distance = Math.sqrt((x - pos.x) ** 2 + (y - pos.y) ** 2);
      if (distance < 20) {
        setSelectedNode(node);
        return;
      }
    }

    setSelectedNode(null);
  };

  const getNodeIcon = (type: string) => {
    switch (type) {
      case "company":
        return <Building2 className="w-4 h-4" />;
      case "person":
        return <User className="w-4 h-4" />;
      case "technology":
        return <Cpu className="w-4 h-4" />;
      default:
        return null;
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

  return (
    <div className="max-w-6xl mx-auto space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Network className="w-5 h-5 text-blue-600" />
            Knowledge Graph
          </CardTitle>
          <CardDescription>
            Explore relationships between companies, people, and technologies in the tech ecosystem
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Legend */}
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-blue-600 rounded-full" />
                <span>Companies</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-green-600 rounded-full" />
                <span>People</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-orange-600 rounded-full" />
                <span>Technologies</span>
              </div>
            </div>

            {/* Graph Canvas */}
            <div className="relative border rounded-lg overflow-hidden bg-gray-50">
              <canvas
                ref={canvasRef}
                width={800}
                height={600}
                className="w-full cursor-pointer"
                onClick={handleCanvasClick}
              />

              {/* Zoom Controls */}
              <div className="absolute top-4 right-4 flex flex-col gap-2">
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => setZoom(Math.min(zoom + 0.2, 3))}
                >
                  <ZoomIn className="w-4 h-4" />
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => setZoom(Math.max(zoom - 0.2, 0.5))}
                >
                  <ZoomOut className="w-4 h-4" />
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => setZoom(1)}
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
                      <strong>Connections:</strong> {selectedNode.connections}
                    </p>
                    {graphData && (
                      <div className="mt-2">
                        <p className="font-semibold mb-1">Connected to:</p>
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
                              return (
                                <Badge key={idx} variant="secondary" className="text-xs">
                                  {connectedNode?.name}
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
        <div className="grid grid-cols-3 gap-4">
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
              <div className="text-3xl font-bold text-orange-600">
                {graphData.nodes.filter((n) => n.type === "technology").length}
              </div>
              <div className="text-sm text-gray-600">Technologies</div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}