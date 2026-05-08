import type React from "react";
import { useEffect, useRef, useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Badge } from "./ui/badge";
import {
  Search,
  Loader2,
  Lightbulb,
  AlertTriangle,
  RefreshCw,
  Copy,
  Download,
} from "lucide-react";
import { toast } from "sonner";
import { API_BASE_URL, API_ENDPOINTS } from "../config/api";

/**
 * ResearchMode — M3 of the Agentic Research mission.
 *
 * Submits the user's question to ``POST /api/research`` (SSE stream) and
 * renders the streamed report token-by-token alongside a phase chip.
 *
 * Wire contract (from backend M2 — see ``backend/src/api/routes/research.py``):
 *   data: {"type": "phase", "data": "Decomposing"}
 *   data: {"type": "phase", "data": "Searching (1/3)"}
 *   data: {"type": "token", "data": "<chunk text>"}
 *   ...
 *   data: {"type": "phase", "data": "done", "report": "<full markdown>"}
 *   data: {"type": "error", "data": "<message>"}
 *
 * Comment frames (``: keepalive\n\n``) are filtered out by the parser.
 *
 * We use ``fetch`` + ``ReadableStream`` rather than ``EventSource`` because
 * EventSource cannot send a POST body. The parser splits on the SSE frame
 * delimiter ``\n\n`` and keeps any trailing partial frame as the new buffer
 * for the next chunk.
 */

// ---------------------------------------------------------------------------
//  Tiny inline markdown renderer
//
// The codebase has no markdown dependency installed (see frontend/package.json)
// and the M3 constraint is explicit: do NOT introduce a new lib. We render the
// subset of markdown the agent actually emits — headings (#–######), unordered
// lists (- ), ordered lists (1. ), bold (**…**), italic (*…* / _…_), inline
// code (`…`), links ([t](u)), and paragraphs separated by blank lines. Raw
// citation markers like ``[3]`` pass through untouched (M4 wires them).
// ---------------------------------------------------------------------------

function renderInline(text: string, keyPrefix: string): React.ReactNode[] {
  const nodes: React.ReactNode[] = [];
  const pattern =
    /(\*\*([^*\n]+)\*\*)|(\*([^*\n]+)\*)|(_([^_\n]+)_)|(`([^`\n]+)`)|(\[([^\]\n]+)\]\(([^)\s]+)\))/;
  let remaining = text;
  let i = 0;
  while (remaining.length > 0) {
    const m = remaining.match(pattern);
    if (!m || m.index === undefined) {
      nodes.push(remaining);
      break;
    }
    if (m.index > 0) {
      nodes.push(remaining.slice(0, m.index));
    }
    const key = `${keyPrefix}-${i++}`;
    if (m[1]) {
      nodes.push(<strong key={key}>{m[2]}</strong>);
    } else if (m[3]) {
      nodes.push(<em key={key}>{m[4]}</em>);
    } else if (m[5]) {
      nodes.push(<em key={key}>{m[6]}</em>);
    } else if (m[7]) {
      nodes.push(
        <code
          key={key}
          className="bg-gray-100 text-gray-800 rounded px-1 py-0.5 text-[0.9em]"
        >
          {m[8]}
        </code>
      );
    } else if (m[9]) {
      nodes.push(
        <a
          key={key}
          href={m[11]}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline break-words"
        >
          {m[10]}
        </a>
      );
    }
    remaining = remaining.slice(m.index + m[0].length);
  }
  return nodes;
}

interface MarkdownReportProps {
  text: string;
}

function MarkdownReport({ text }: MarkdownReportProps): JSX.Element {
  const lines = text.split("\n");
  const blocks: React.ReactNode[] = [];
  let i = 0;
  let blockIdx = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.trim() === "") {
      i++;
      continue;
    }

    const headingMatch = line.match(/^(#{1,6})\s+(.+)$/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      const content = headingMatch[2].trim();
      const cls =
        level === 1
          ? "text-2xl font-bold mt-4 mb-2 text-gray-900"
          : level === 2
          ? "text-xl font-semibold mt-3 mb-2 text-gray-900"
          : level === 3
          ? "text-lg font-semibold mt-3 mb-1 text-gray-900"
          : "text-base font-semibold mt-2 mb-1 text-gray-900";
      const Tag = (`h${level}` as unknown) as keyof JSX.IntrinsicElements;
      blocks.push(
        <Tag key={`b-${blockIdx++}`} className={cls}>
          {renderInline(content, `b-${blockIdx}`)}
        </Tag>
      );
      i++;
      continue;
    }

    if (/^\s*[-*]\s+/.test(line)) {
      const items: React.ReactNode[] = [];
      let j = i;
      while (j < lines.length && /^\s*[-*]\s+/.test(lines[j])) {
        const itemText = lines[j].replace(/^\s*[-*]\s+/, "");
        items.push(
          <li key={`li-${blockIdx}-${j}`} className="ml-6 list-disc">
            {renderInline(itemText, `li-${blockIdx}-${j}`)}
          </li>
        );
        j++;
      }
      blocks.push(
        <ul key={`b-${blockIdx++}`} className="my-2 space-y-1 text-gray-800">
          {items}
        </ul>
      );
      i = j;
      continue;
    }

    if (/^\s*\d+\.\s+/.test(line)) {
      const items: React.ReactNode[] = [];
      let j = i;
      while (j < lines.length && /^\s*\d+\.\s+/.test(lines[j])) {
        const itemText = lines[j].replace(/^\s*\d+\.\s+/, "");
        items.push(
          <li key={`oli-${blockIdx}-${j}`} className="ml-6 list-decimal">
            {renderInline(itemText, `oli-${blockIdx}-${j}`)}
          </li>
        );
        j++;
      }
      blocks.push(
        <ol key={`b-${blockIdx++}`} className="my-2 space-y-1 text-gray-800">
          {items}
        </ol>
      );
      i = j;
      continue;
    }

    const paraLines: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() !== "" &&
      !/^(#{1,6})\s+/.test(lines[i]) &&
      !/^\s*[-*]\s+/.test(lines[i]) &&
      !/^\s*\d+\.\s+/.test(lines[i])
    ) {
      paraLines.push(lines[i]);
      i++;
    }
    blocks.push(
      <p
        key={`b-${blockIdx++}`}
        className="my-2 leading-relaxed text-gray-800"
        style={{ overflowWrap: "anywhere", wordBreak: "break-word" }}
      >
        {renderInline(paraLines.join(" "), `p-${blockIdx}`)}
      </p>
    );
  }

  return <div className="prose prose-sm max-w-none">{blocks}</div>;
}

interface AgentEvent {
  type: "phase" | "token" | "error";
  data: string;
  report?: string;
}

interface ResearchModeProps {
  // No props needed — using API config directly.
}

export function ResearchMode({}: ResearchModeProps) {
  const [query, setQuery] = useState("");
  const [isResearching, setIsResearching] = useState(false);
  const [phase, setPhase] = useState<string>("");
  const [reportText, setReportText] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [lastSubmittedQuery, setLastSubmittedQuery] = useState<string>("");

  const abortRef = useRef<AbortController | null>(null);

  const suggestedQueries = [
    "Summarize the biggest AI funding rounds in the past 2 weeks",
    "What's new with OpenAI this month?",
    "Latest breakthroughs in quantum computing",
    "Recent developments in AI agents and autonomous systems",
    "Military tech innovations in the past month",
  ];

  useEffect(() => {
    return () => {
      if (abortRef.current) {
        abortRef.current.abort();
        abortRef.current = null;
      }
    };
  }, []);

  function handleEvent(
    ev: AgentEvent,
    tokenAcc: { current: string }
  ): { done: boolean; finalReport?: string; errored?: string } {
    if (ev.type === "phase") {
      const ph = ev.data;
      setPhase(ph);
      if (ph === "done") {
        const finalReport =
          typeof ev.report === "string" ? ev.report : tokenAcc.current;
        return { done: true, finalReport };
      }
      return { done: false };
    }
    if (ev.type === "token") {
      tokenAcc.current = tokenAcc.current + (ev.data || "");
      setReportText(tokenAcc.current);
      return { done: false };
    }
    if (ev.type === "error") {
      return { done: true, errored: ev.data || "Unknown error" };
    }
    return { done: false };
  }

  const conductResearch = async (questionOverride?: string) => {
    const question = (questionOverride ?? query).trim();
    if (!question) {
      toast.error("Please enter a research query");
      return;
    }

    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }

    setIsResearching(true);
    setPhase("Decomposing");
    setReportText("");
    setErrorMessage(null);
    setLastSubmittedQuery(question);

    const ac = new AbortController();
    abortRef.current = ac;

    const tokenAcc = { current: "" };

    try {
      const url = `${API_BASE_URL}${API_ENDPOINTS.research}`;
      const resp = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify({ question }),
        signal: ac.signal,
      });

      if (!resp.ok) {
        let detail = `${resp.status} ${resp.statusText}`;
        try {
          const j = await resp.json();
          if (j && typeof j.detail === "string") {
            detail = j.detail;
          }
        } catch {
          // Body wasn't JSON; keep status text.
        }
        throw new Error(detail);
      }

      if (!resp.body) {
        throw new Error("Streaming response has no body");
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";
      let finished = false;

      while (!finished) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        let sepIdx = buffer.indexOf("\n\n");
        while (sepIdx !== -1) {
          const frame = buffer.slice(0, sepIdx);
          buffer = buffer.slice(sepIdx + 2);

          if (frame.startsWith(":")) {
            sepIdx = buffer.indexOf("\n\n");
            continue;
          }

          const dataLines: string[] = [];
          for (const line of frame.split("\n")) {
            if (line.startsWith("data:")) {
              dataLines.push(line.slice(5).replace(/^ /, ""));
            }
          }
          if (dataLines.length > 0) {
            const payload = dataLines.join("\n");
            try {
              const ev = JSON.parse(payload) as AgentEvent;
              const r = handleEvent(ev, tokenAcc);
              if (r.done) {
                if (r.errored) {
                  setErrorMessage(r.errored);
                  setPhase("error");
                } else if (typeof r.finalReport === "string") {
                  setReportText(r.finalReport);
                }
                finished = true;
                break;
              }
            } catch (parseErr) {
              // eslint-disable-next-line no-console
              console.warn("research SSE: failed to parse frame", parseErr);
            }
          }

          sepIdx = buffer.indexOf("\n\n");
        }
      }
    } catch (err) {
      if ((err as Error).name === "AbortError") {
        return;
      }
      // eslint-disable-next-line no-console
      console.warn("research SSE: stream failed:", err);
      setErrorMessage((err as Error).message || "research interrupted");
      setPhase("error");
    } finally {
      setIsResearching(false);
      if (abortRef.current === ac) {
        abortRef.current = null;
      }
    }
  };

  const onRetry = () => {
    if (lastSubmittedQuery) {
      void conductResearch(lastSubmittedQuery);
    }
  };

  const onCopyMarkdown = () => {
    if (!reportText) return;
    try {
      void navigator.clipboard?.writeText(reportText);
      toast.success("Report copied to clipboard");
    } catch {
      toast.error("Copy failed");
    }
  };
  const onDownloadMarkdown = () => {
    if (!reportText) return;
    const blob = new Blob([reportText], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `techpulse-research-${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const phaseVariant: "default" | "secondary" | "destructive" | "outline" =
    phase === "error"
      ? "destructive"
      : phase === "done"
      ? "default"
      : isResearching
      ? "secondary"
      : "outline";

  const showErrorPanel = phase === "error" && errorMessage !== null;
  const showReport = !showErrorPanel && reportText.length > 0;
  const showEmptyState = !showErrorPanel && !showReport && !isResearching;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-blue-600" />
            Agentic Research Mode
          </CardTitle>
          <CardDescription>
            Ask a research question and our AI agent will search, analyze, and
            generate a comprehensive report
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="e.g., Summarize the biggest AI funding rounds in the past 2 weeks"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) =>
                e.key === "Enter" && !isResearching && conductResearch()
              }
              className="flex-1"
              disabled={isResearching}
            />
            <Button
              onClick={() => conductResearch()}
              disabled={isResearching}
            >
              {isResearching ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Researching...
                </>
              ) : (
                <>
                  <Search className="w-4 h-4 mr-2" />
                  Research
                </>
              )}
            </Button>
          </div>

          <div>
            <p className="text-sm text-gray-600 mb-2">Suggested queries:</p>
            <div className="flex flex-wrap gap-2">
              {suggestedQueries.map((suggested, idx) => (
                <Badge
                  key={idx}
                  variant="outline"
                  className="cursor-pointer hover:bg-gray-100"
                  onClick={() => setQuery(suggested)}
                >
                  {suggested}
                </Badge>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {(isResearching || phase || showReport || showErrorPanel) && (
        <Card data-testid="research-report-card">
          <CardHeader>
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div className="flex items-center gap-2 min-w-0">
                <CardTitle className="text-lg">Research Report</CardTitle>
                {phase && (
                  <Badge
                    variant={phaseVariant}
                    data-testid="research-phase-chip"
                    className="ml-2"
                  >
                    {phase === "done"
                      ? "Done"
                      : phase === "error"
                      ? "Error"
                      : phase}
                  </Badge>
                )}
              </div>
              {showReport && phase === "done" && (
                <div className="flex gap-2">
                  <Button
                    onClick={onCopyMarkdown}
                    variant="outline"
                    size="sm"
                    data-testid="research-copy-btn"
                  >
                    <Copy className="w-4 h-4 mr-2" />
                    Copy markdown
                  </Button>
                  <Button
                    onClick={onDownloadMarkdown}
                    variant="outline"
                    size="sm"
                    data-testid="research-download-btn"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Download .md
                  </Button>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {showErrorPanel ? (
              <div
                data-testid="research-error-panel"
                className="flex flex-col items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg"
              >
                <div className="flex items-center gap-2 text-red-700">
                  <AlertTriangle className="w-5 h-5" />
                  <span className="font-semibold">
                    Research interrupted — retry?
                  </span>
                </div>
                {errorMessage && (
                  <p
                    className="text-sm text-red-700"
                    style={{ overflowWrap: "anywhere" }}
                  >
                    {errorMessage}
                  </p>
                )}
                <Button
                  onClick={onRetry}
                  variant="outline"
                  size="sm"
                  data-testid="research-retry-btn"
                  disabled={isResearching || !lastSubmittedQuery}
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Retry
                </Button>
              </div>
            ) : (
              <div
                data-testid="research-report-body"
                className="min-w-0 overflow-hidden"
                style={{ overflowWrap: "anywhere", wordBreak: "break-word" }}
              >
                {reportText.length > 0 ? (
                  <MarkdownReport text={reportText} />
                ) : (
                  <div className="flex items-center gap-2 text-gray-500 py-4">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Waiting for tokens...</span>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {showEmptyState && (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Search className="w-12 h-12 text-gray-400 mb-4" />
            <p className="text-gray-600 text-center">
              Enter a research query above to get started
            </p>
            <p className="text-sm text-gray-500 text-center mt-2">
              Our AI agent will search, filter, and generate a comprehensive
              report
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
