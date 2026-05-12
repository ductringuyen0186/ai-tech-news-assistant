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
  X,
  Check,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { toast } from "sonner";
import { API_BASE_URL, API_ENDPOINTS } from "../config/api";

/**
 * ResearchMode — M3 + M4 of the Agentic Research mission.
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
 *
 * M4 adds: clickable inline ``[N]`` citation anchors that smooth-scroll to
 * the matching ``#source-N`` entry in the ``Sources Used`` section, an
 * in-flight Cancel button, a transient "Copied!" indicator on the copy
 * button, and a properly-named ``research-<ISO timestamp>.md`` download.
 */

// ---------------------------------------------------------------------------
//  Tiny inline markdown renderer
//
// The codebase has no markdown dependency installed (see frontend/package.json)
// and the M3 constraint is explicit: do NOT introduce a new lib. We render the
// subset of markdown the agent actually emits — headings (#–######), unordered
// lists (- ), ordered lists (1. ), bold (**…**), italic (*…* / _…_), inline
// code (`…`), links ([t](u)), and paragraphs separated by blank lines. Inline
// citation markers like ``[3]`` pass through untouched while the report is
// still streaming, then become anchor links once ``linkifyCitations`` is on
// (the parent flips this on the ``done`` phase).
// ---------------------------------------------------------------------------

/**
 * Smooth-scroll to a ``#source-N`` anchor when an inline citation link is
 * clicked. Falls back gracefully (no-op) if the anchor was never rendered —
 * for example, when the model omits the ``Sources Used`` section.
 */
function handleCitationClick(
  event: React.MouseEvent<HTMLAnchorElement>,
  n: number
): void {
  event.preventDefault();
  const target = document.getElementById(`source-${n}`);
  if (target) {
    target.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function renderInline(
  text: string,
  keyPrefix: string,
  opts?: { linkifyCitations?: boolean }
): React.ReactNode[] {
  const linkifyCitations = opts?.linkifyCitations === true;
  const nodes: React.ReactNode[] = [];
  // Order matters — the link-with-URL branch must sit BEFORE the bare
  // ``[N]`` citation branch so that ``[label](url)`` isn't mis-detected as a
  // citation. The citation branch only fires when the alt text is purely
  // numeric and no ``(`` follows.
  const pattern = linkifyCitations
    ? /(\*\*([^*\n]+)\*\*)|(\*([^*\n]+)\*)|(_([^_\n]+)_)|(`([^`\n]+)`)|(\[([^\]\n]+)\]\(([^)\s]+)\))|(\[(\d+)\])/
    : /(\*\*([^*\n]+)\*\*)|(\*([^*\n]+)\*)|(_([^_\n]+)_)|(`([^`\n]+)`)|(\[([^\]\n]+)\]\(([^)\s]+)\))/;
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
    } else if (linkifyCitations && m[12]) {
      const n = parseInt(m[13], 10);
      nodes.push(
        <a
          key={key}
          href={`#source-${n}`}
          className="citation text-blue-600 hover:underline cursor-pointer"
          onClick={(e) => handleCitationClick(e, n)}
        >
          [{n}]
        </a>
      );
    }
    remaining = remaining.slice(m.index + m[0].length);
  }
  return nodes;
}

interface MarkdownReportProps {
  text: string;
  /**
   * When true (post-``done``), inline ``[N]`` markers become anchor links
   * targeting ``#source-N`` and entries inside the ``Sources Used`` section
   * receive matching ``id="source-N"`` attributes. Off during streaming to
   * avoid flicker as the markers appear mid-token.
   */
  linkifyCitations?: boolean;
}

function MarkdownReport({
  text,
  linkifyCitations = false,
}: MarkdownReportProps): JSX.Element {
  const lines = text.split("\n");
  const blocks: React.ReactNode[] = [];
  let i = 0;
  let blockIdx = 0;
  // Tracks whether the current section is the "Sources Used" section. When
  // true, the next list (ul/ol) we emit gets sequential ``id="source-N"``
  // anchors on each list item, regardless of the model's own numbering.
  let inSourcesSection = false;
  // Counter for source anchor IDs. Only the FIRST list under the Sources
  // heading claims anchors; a malformed report with multiple lists won't
  // produce duplicate IDs.
  let sourceCounter = 0;
  const inlineOpts = { linkifyCitations };

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
      // A heading boundary always closes the previous section. We re-detect
      // the Sources marker each time so a nested ``### Sources`` would also
      // open the anchor numbering.
      if (linkifyCitations && /^sources?\b/i.test(content)) {
        inSourcesSection = true;
        sourceCounter = 0;
      } else {
        inSourcesSection = false;
      }
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
          {renderInline(content, `b-${blockIdx}`, inlineOpts)}
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
        const anchorId =
          inSourcesSection && sourceCounter < 1000
            ? `source-${++sourceCounter}`
            : undefined;
        items.push(
          <li
            key={`li-${blockIdx}-${j}`}
            id={anchorId}
            className="ml-6 list-disc"
          >
            {renderInline(itemText, `li-${blockIdx}-${j}`, inlineOpts)}
          </li>
        );
        j++;
      }
      // The Sources list has been consumed — close out so a stray bullet
      // list later in the document doesn't claim more anchor IDs.
      if (inSourcesSection) {
        inSourcesSection = false;
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
        const anchorId =
          inSourcesSection && sourceCounter < 1000
            ? `source-${++sourceCounter}`
            : undefined;
        items.push(
          <li
            key={`oli-${blockIdx}-${j}`}
            id={anchorId}
            className="ml-6 list-decimal"
          >
            {renderInline(itemText, `oli-${blockIdx}-${j}`, inlineOpts)}
          </li>
        );
        j++;
      }
      if (inSourcesSection) {
        inSourcesSection = false;
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
        {renderInline(paraLines.join(" "), `p-${blockIdx}`, inlineOpts)}
      </p>
    );
  }

  return <div className="prose prose-sm max-w-none">{blocks}</div>;
}

interface AgentEvent {
  type: "phase" | "token" | "error" | "subagent";
  data: string;
  report?: string;
  // Subagent telemetry fields (M5). Present only on ``type: "subagent"``
  // frames where ``data`` is one of "start" | "done" | "error".
  skill?: string;
  article_id?: number;
  duration_ms?: number;
  message?: string;
}

/**
 * Per-subagent row tracked in component state. Keyed in the parent Map by
 * ``${skill}:${article_id}`` so a re-emitted ``start`` for the same pair
 * updates the existing row instead of duplicating.
 */
interface SubagentRow {
  skill: string;
  articleId: number;
  status: "running" | "done" | "error";
  startedAt: number;
  durationMs?: number;
  message?: string;
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
  const [copied, setCopied] = useState(false);
  // M5 — Subagents panel state. ``subagents`` is a Map<key, SubagentRow>
  // where the key is ``${skill}:${article_id}``. React's Map preserves
  // insertion order so iteration matches arrival order. ``subagentsOpen``
  // controls the collapsible panel chevron; it auto-flips to true on the
  // first ``subagent: start`` event of a run and the user can collapse it.
  const [subagents, setSubagents] = useState<Map<string, SubagentRow>>(
    () => new Map()
  );
  const [subagentsOpen, setSubagentsOpen] = useState<boolean>(false);

  const abortRef = useRef<AbortController | null>(null);
  const copiedTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

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
      if (copiedTimerRef.current) {
        clearTimeout(copiedTimerRef.current);
        copiedTimerRef.current = null;
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
    if (ev.type === "subagent") {
      // ``data`` carries the lifecycle stage; ``skill`` + ``article_id``
      // form the row key. Defensive defaults guard against the backend
      // omitting a field — we still want a row, just with placeholder
      // labels, rather than crashing the parser.
      const stage = ev.data;
      const skill = ev.skill ?? "unknown";
      const articleId =
        typeof ev.article_id === "number" ? ev.article_id : -1;
      const key = `${skill}:${articleId}`;
      setSubagents((prev) => {
        const next = new Map(prev);
        const existing = next.get(key);
        if (stage === "start") {
          // Re-emitted ``start`` for the same key resets the row back to
          // ``running`` (no duplicate); preserves insertion order via
          // ``next.set`` of an existing key.
          next.set(key, {
            skill,
            articleId,
            status: "running",
            startedAt: existing?.startedAt ?? Date.now(),
          });
        } else if (stage === "done") {
          const startedAt = existing?.startedAt ?? Date.now();
          next.set(key, {
            skill,
            articleId,
            status: "done",
            startedAt,
            durationMs:
              typeof ev.duration_ms === "number" ? ev.duration_ms : undefined,
          });
        } else if (stage === "error") {
          const startedAt = existing?.startedAt ?? Date.now();
          next.set(key, {
            skill,
            articleId,
            status: "error",
            startedAt,
            message: ev.message,
          });
        }
        return next;
      });
      // Auto-expand on the first event of a run. We use the start stage
      // specifically so a stray late ``done`` event doesn't re-open the
      // panel after the user has collapsed it.
      if (stage === "start") {
        setSubagentsOpen((open) => open || true);
      }
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
    setCopied(false);
    // M5 — clear the subagents map at the start of every run so rows
    // from a previous query don't bleed into the current one. The panel
    // also collapses; it'll re-expand on the first ``subagent: start``.
    setSubagents(new Map());
    setSubagentsOpen(false);

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

  /**
   * User-initiated cancel. Aborts the in-flight fetch (the SSE reader sees
   * an ``AbortError`` and exits silently in the catch block above), then
   * resets the UI to idle so the submit button re-enables and the phase
   * chip disappears. Server-side cancel of the Ollama generation is handled
   * in M2 via the StreamingResponse ``is_disconnected`` callback.
   */
  const handleCancel = () => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    setIsResearching(false);
    setPhase("");
    setErrorMessage(null);
    // Keep ``reportText`` so any partial output the user already sees is
    // preserved — they can read what arrived before cancelling. The phase
    // chip resetting to empty is enough signal that the run is done.
  };

  const onCopyMarkdown = () => {
    if (!reportText) return;
    const writeToClipboard = async (): Promise<boolean> => {
      try {
        if (
          navigator.clipboard &&
          typeof navigator.clipboard.writeText === "function"
        ) {
          await navigator.clipboard.writeText(reportText);
          return true;
        }
      } catch {
        // Fall through to legacy path.
      }
      // Fallback for older browsers / non-secure contexts.
      try {
        const ta = document.createElement("textarea");
        ta.value = reportText;
        ta.setAttribute("readonly", "");
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        const ok = document.execCommand("copy");
        document.body.removeChild(ta);
        return ok;
      } catch {
        return false;
      }
    };
    void writeToClipboard().then((ok) => {
      if (!ok) {
        toast.error("Copy failed");
        return;
      }
      setCopied(true);
      toast.success("Report copied to clipboard");
      if (copiedTimerRef.current) {
        clearTimeout(copiedTimerRef.current);
      }
      copiedTimerRef.current = setTimeout(() => {
        setCopied(false);
        copiedTimerRef.current = null;
      }, 2000);
    });
  };

  const onDownloadMarkdown = () => {
    if (!reportText) return;
    try {
      const blob = new Blob([reportText], { type: "text/markdown" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      // ``research-<ISO timestamp>.md`` per the M4 contract. Colons and
      // dots are stripped on Windows; replace them so the saved file looks
      // tidy in Explorer.
      const stamp = new Date().toISOString().replace(/[:.]/g, "-");
      a.download = `research-${stamp}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      // Defer revocation so Safari has time to start the download.
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (err) {
      // eslint-disable-next-line no-console
      console.warn("research download failed:", err);
      toast.error("Download failed");
    }
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

  // M5 — Subagent panel derived state. We render the panel only once at
  // least one event has been received so a fresh load doesn't show an
  // empty panel. Counts feed the header summary text.
  const subagentRows = Array.from(subagents.values());
  const showSubagentsPanel = subagentRows.length > 0;
  let runningCount = 0;
  let doneCount = 0;
  let erroredCount = 0;
  for (const row of subagentRows) {
    if (row.status === "running") runningCount += 1;
    else if (row.status === "done") doneCount += 1;
    else if (row.status === "error") erroredCount += 1;
  }
  const subagentsHeaderText = `Subagents (${runningCount} running, ${doneCount} done, ${erroredCount} errored)`;

  /**
   * Format a duration in milliseconds as a short human-readable string.
   * Used in the subagent row when a ``done`` event arrives — the user sees
   * "1.2s" or "342ms" next to the badge.
   */
  function formatDuration(ms: number): string {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  }

  /**
   * Truncate a subagent error message for the row display. The full text
   * is preserved on the row's ``title`` attribute so hovering reveals it.
   */
  function truncateMessage(msg: string, max = 80): string {
    if (msg.length <= max) return msg;
    return msg.slice(0, max - 1) + "…";
  }

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
              <div className="flex gap-2 flex-wrap">
                {isResearching && (
                  <Button
                    onClick={handleCancel}
                    variant="outline"
                    size="sm"
                    data-testid="research-cancel-btn"
                    aria-label="Cancel research"
                  >
                    <X className="w-4 h-4 mr-2" />
                    Cancel
                  </Button>
                )}
                {showReport && phase === "done" && (
                  <>
                    <Button
                      onClick={onCopyMarkdown}
                      variant="outline"
                      size="sm"
                      data-testid="research-copy-btn"
                      aria-live="polite"
                    >
                      {copied ? (
                        <>
                          <Check className="w-4 h-4 mr-2" />
                          Copied!
                        </>
                      ) : (
                        <>
                          <Copy className="w-4 h-4 mr-2" />
                          Copy markdown
                        </>
                      )}
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
                  </>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {showSubagentsPanel && (
              <div
                data-testid="research-subagents-panel"
                className="mb-4 border border-gray-200 rounded-lg overflow-hidden"
              >
                <button
                  type="button"
                  onClick={() => setSubagentsOpen((open) => !open)}
                  data-testid="research-subagents-header"
                  aria-expanded={subagentsOpen}
                  className="w-full flex items-center gap-2 px-3 py-2 bg-gray-50 hover:bg-gray-100 text-left text-sm font-medium text-gray-800"
                >
                  {subagentsOpen ? (
                    <ChevronDown className="w-4 h-4 text-gray-600" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-gray-600" />
                  )}
                  <span>{subagentsHeaderText}</span>
                </button>
                {subagentsOpen && (
                  <ul className="divide-y divide-gray-100">
                    {subagentRows.map((row) => {
                      const key = `${row.skill}:${row.articleId}`;
                      const badgeVariant:
                        | "default"
                        | "secondary"
                        | "destructive"
                        | "outline" =
                        row.status === "running"
                          ? "secondary"
                          : row.status === "error"
                          ? "destructive"
                          : "default";
                      const statusLabel =
                        row.status === "running"
                          ? "running"
                          : row.status === "error"
                          ? "error"
                          : "done";
                      return (
                        <li
                          key={key}
                          data-testid="research-subagent-row"
                          className="flex items-center gap-3 px-3 py-2 text-sm text-gray-800 min-w-0"
                        >
                          <span
                            className="font-mono text-xs text-gray-700 truncate"
                            style={{ overflowWrap: "anywhere" }}
                          >
                            {row.skill}
                          </span>
                          <span className="text-gray-500 text-xs">
                            #{row.articleId}
                          </span>
                          <Badge variant={badgeVariant} className="capitalize">
                            {statusLabel}
                          </Badge>
                          {row.status === "done" &&
                            typeof row.durationMs === "number" && (
                              <span className="text-xs text-gray-500">
                                {formatDuration(row.durationMs)}
                              </span>
                            )}
                          {row.status === "error" && row.message && (
                            <span
                              className="text-xs text-red-600 truncate"
                              title={row.message}
                              style={{ overflowWrap: "anywhere" }}
                            >
                              {truncateMessage(row.message)}
                            </span>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            )}
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
                  <MarkdownReport
                    text={reportText}
                    linkifyCitations={phase === "done"}
                  />
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
