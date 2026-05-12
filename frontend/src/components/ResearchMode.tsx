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
import { MarkdownReport } from "./MarkdownReport";
import { SuggestedQueries } from "./SuggestedQueries";
import {
  SubQuestionsPanel,
  type SubQuestionArticle,
  type SubQuestionStatus,
} from "./SubQuestionsPanel";
import {
  ResearchProgressTimeline,
  type TimelineStep,
  type TimelineStatus,
} from "./ResearchProgressTimeline";

/**
 * ResearchMode — M3.M2 streaming-UX rebuild.
 *
 * SSE event surface (additive, backward-compatible with M2):
 *   - phase: Decomposing | Searching (i/N) | Synthesizing | done
 *   - token: <chunk>
 *   - subagent: start | done | error  (+ NEW `summary` field on done)
 *   - error: <message>
 *   - decomposed: {sub_questions: string[]}              (NEW M3.M2)
 *   - search_results: {sub_question_index, articles}     (NEW M3.M2)
 *
 * The new events surface intermediate content within ~5s of submit:
 *   - decomposed → SubQuestionsPanel renders numbered sub-questions
 *   - search_results → each sub-question shows its article titles
 *   - enriched subagent:done → expandable rows show 280-char summary
 *
 * Empty state shows curated SuggestedQueries chips. The palette M3.M1
 * handoff key `techpulse-pending-research` triggers an auto-submit on
 * mount.
 *
 * Performance target: time-to-sub-questions-visible ≤ 5s,
 * time-to-first-summary-visible ≤ 20s.
 */

// ---------------------------------------------------------------------------
// Curated suggested queries shown on empty state.
// ---------------------------------------------------------------------------

const EMPTY_STATE_QUERIES: string[] = [
  "OpenAI's last 30 days",
  "AI chip market shifts",
  "Anthropic vs OpenAI announcements",
  "AI funding rounds past month",
  "Cloud security trends",
  "Edge computing developments",
];

// Mount-time handoff key from the Cmd+K palette (M3.M1).
const PENDING_RESEARCH_KEY = "techpulse-pending-research";

// ---------------------------------------------------------------------------
// Follow-up extractor: very simple capitalized-entity scrape with a
// stopword list. The M5 milestone may swap this out for an LLM call.
// ---------------------------------------------------------------------------

const STOPWORDS = new Set([
  "The", "What", "How", "When", "Where", "Why", "Who", "Which",
  "And", "But", "Or", "If", "Of", "For", "From", "With", "Without",
  "In", "On", "At", "To", "By", "As", "Is", "Are", "Was", "Were",
  "Be", "Been", "Being", "Has", "Have", "Had", "Do", "Does", "Did",
  "Can", "Could", "Would", "Should", "Will", "Shall", "May", "Might",
  "Must", "AI", "An", "A", "It", "Its", "This", "That", "These",
  "Those", "Some", "Many", "Most", "More", "Less", "Few", "All",
  "Both", "Each", "Every", "Other", "Such", "No", "Not", "Only",
  "Same", "Than", "Then", "Too", "Very", "Just", "Also", "Even",
  "New", "Old", "First", "Last", "Next", "Past", "Year", "Month",
  "Week", "Day", "Now", "Today", "Sources", "Used", "Executive",
  "Summary", "Key", "Findings", "Trends", "Themes", "Report",
]);

function extractFollowUpEntities(report: string, limit = 3): string[] {
  if (!report) return [];
  const pattern = /\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b/g;
  const counts = new Map<string, number>();
  let m: RegExpExecArray | null;
  while ((m = pattern.exec(report)) !== null) {
    const term = m[0].trim();
    if (!term) continue;
    if (term.length <= 2) continue;
    // Skip if every word is a stopword.
    const words = term.split(/\s+/);
    if (words.every((w) => STOPWORDS.has(w))) continue;
    counts.set(term, (counts.get(term) ?? 0) + 1);
  }
  // Sort by frequency (descending) and pick the top entities.
  const ranked = Array.from(counts.entries())
    .filter(([k]) => k.length > 2 && !STOPWORDS.has(k))
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([k]) => k);
  return ranked;
}

function buildFollowUps(report: string): string[] {
  const entities = extractFollowUpEntities(report, 3);
  const out: string[] = [];
  if (entities[0]) {
    out.push(
      `How is ${entities[0]} positioned vs the rest of the market?`
    );
  }
  if (entities[1]) {
    out.push(`What are the most recent developments around ${entities[1]}?`);
  }
  if (entities[2]) {
    out.push(`Drill into ${entities[2]}'s funding history.`);
  }
  // Pad with generic templates.
  const generic = [
    "What risks should we watch out for next quarter?",
    "Which companies are most affected?",
    "How does this compare to the previous month?",
  ];
  let gi = 0;
  while (out.length < 3 && gi < generic.length) {
    if (!out.includes(generic[gi])) out.push(generic[gi]);
    gi += 1;
  }
  return out.slice(0, 3);
}

// ---------------------------------------------------------------------------
// SSE event types
// ---------------------------------------------------------------------------

interface AgentEvent {
  type: "phase" | "token" | "error" | "subagent" | "decomposed" | "search_results";
  data?: string;
  report?: string;
  // subagent telemetry
  skill?: string;
  article_id?: number;
  duration_ms?: number;
  message?: string;
  summary?: string; // NEW M3.M2 — first 280 chars of per-article summary
  // decomposed
  sub_questions?: string[];
  // search_results
  sub_question_index?: number;
  articles?: Array<{ id: number; title: string; source: string }>;
}

interface SubagentRow {
  skill: string;
  articleId: number;
  status: "running" | "done" | "error";
  startedAt: number;
  durationMs?: number;
  message?: string;
  /** First 280 chars of per-article summary (M3.M2 enriched done event). */
  summary?: string;
}

interface ResearchModeProps {
  // No props needed.
}

export function ResearchMode({}: ResearchModeProps) {
  const [query, setQuery] = useState("");
  const [isResearching, setIsResearching] = useState(false);
  const [phase, setPhase] = useState<string>("");
  const [reportText, setReportText] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [lastSubmittedQuery, setLastSubmittedQuery] = useState<string>("");
  const [copied, setCopied] = useState(false);
  const [subagents, setSubagents] = useState<Map<string, SubagentRow>>(
    () => new Map()
  );
  const [subagentsOpen, setSubagentsOpen] = useState<boolean>(false);
  // M3.M2 NEW state.
  const [subQuestions, setSubQuestions] = useState<string[]>([]);
  const [searchResults, setSearchResults] = useState<
    Record<number, SubQuestionArticle[]>
  >({});
  const [expandedRows, setExpandedRows] = useState<Set<string>>(
    () => new Set()
  );
  // Tracks per-step elapsed durations + per-step done timestamps so the
  // vertical timeline can render elapsed time once a step completes.
  const [stepDurations, setStepDurations] = useState<
    Record<string, number>
  >({});
  const [stepStatuses, setStepStatuses] = useState<
    Record<string, TimelineStatus>
  >({});
  const runStartRef = useRef<number>(0);
  const stepStartRef = useRef<Record<string, number>>({});

  const abortRef = useRef<AbortController | null>(null);
  const copiedTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // M3.M1 palette handoff: on mount, if the palette stashed a query in
  // localStorage, pull it, clear the key, and auto-submit.
  // Use a ref so we only consume once even under StrictMode double-mount.
  const consumedHandoffRef = useRef<boolean>(false);
  useEffect(() => {
    if (consumedHandoffRef.current) return;
    consumedHandoffRef.current = true;
    try {
      const pending = window.localStorage.getItem(PENDING_RESEARCH_KEY);
      if (pending && pending.trim()) {
        window.localStorage.removeItem(PENDING_RESEARCH_KEY);
        setQuery(pending);
        // Defer the actual submit one tick so the input value is in
        // place when conductResearch reads it.
        setTimeout(() => {
          void conductResearch(pending);
        }, 50);
      }
    } catch {
      // localStorage unavailable — silently skip.
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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

  // -----------------------------------------------------------------------
  // Step ID helpers — the vertical timeline.
  // -----------------------------------------------------------------------
  const STEP_IDS = {
    decomposing: "decomposing",
    searching: "searching",
    reading: "reading",
    synthesizing: "synthesizing",
    done: "done",
  } as const;

  function markStepRunning(id: string) {
    stepStartRef.current[id] = Date.now();
    setStepStatuses((prev) => ({ ...prev, [id]: "in-progress" }));
  }
  function markStepDone(id: string) {
    const start = stepStartRef.current[id] ?? Date.now();
    const elapsed = Date.now() - start;
    setStepDurations((prev) => ({ ...prev, [id]: elapsed }));
    setStepStatuses((prev) => ({ ...prev, [id]: "done" }));
  }

  // -----------------------------------------------------------------------
  // SSE event handler.
  // -----------------------------------------------------------------------

  function handleEvent(
    ev: AgentEvent,
    tokenAcc: { current: string }
  ): { done: boolean; finalReport?: string; errored?: string } {
    if (ev.type === "phase") {
      const ph = ev.data ?? "";
      setPhase(ph);

      // Translate the legacy phase strings into the vertical timeline.
      if (ph === "Decomposing") {
        markStepRunning(STEP_IDS.decomposing);
      } else if (ph.startsWith("Searching")) {
        // First Searching event marks Decomposing as done + Searching as running.
        setStepStatuses((prev) => {
          const next = { ...prev };
          if (next[STEP_IDS.decomposing] !== "done") {
            const s = stepStartRef.current[STEP_IDS.decomposing] ?? Date.now();
            setStepDurations((prevDur) => ({
              ...prevDur,
              [STEP_IDS.decomposing]: Date.now() - s,
            }));
            next[STEP_IDS.decomposing] = "done";
          }
          if (next[STEP_IDS.searching] !== "in-progress") {
            stepStartRef.current[STEP_IDS.searching] = Date.now();
            next[STEP_IDS.searching] = "in-progress";
          }
          return next;
        });
      } else if (ph === "Synthesizing") {
        // Close out Searching + Reading; open Synthesizing.
        setStepStatuses((prev) => {
          const next = { ...prev };
          for (const id of [STEP_IDS.searching, STEP_IDS.reading]) {
            if (next[id] === "in-progress" || next[id] === undefined) {
              const s = stepStartRef.current[id] ?? Date.now();
              setStepDurations((prevDur) => ({
                ...prevDur,
                [id]: Date.now() - s,
              }));
              next[id] = "done";
            }
          }
          stepStartRef.current[STEP_IDS.synthesizing] = Date.now();
          next[STEP_IDS.synthesizing] = "in-progress";
          return next;
        });
      } else if (ph === "done") {
        markStepDone(STEP_IDS.synthesizing);
        markStepDone(STEP_IDS.done);
        const finalReport =
          typeof ev.report === "string" ? ev.report : tokenAcc.current;
        return { done: true, finalReport };
      }
      return { done: false };
    }

    if (ev.type === "decomposed") {
      const qs = Array.isArray(ev.sub_questions) ? ev.sub_questions : [];
      setSubQuestions(qs);
      // Mark Decomposing as done as soon as the sub-questions are known.
      markStepDone(STEP_IDS.decomposing);
      return { done: false };
    }

    if (ev.type === "search_results") {
      const idx =
        typeof ev.sub_question_index === "number" ? ev.sub_question_index : 0;
      const articles = Array.isArray(ev.articles) ? ev.articles : [];
      setSearchResults((prev) => ({ ...prev, [idx]: articles }));
      return { done: false };
    }

    if (ev.type === "token") {
      tokenAcc.current = tokenAcc.current + (ev.data || "");
      setReportText(tokenAcc.current);
      return { done: false };
    }

    if (ev.type === "subagent") {
      const stage = ev.data;
      const skill = ev.skill ?? "unknown";
      const articleId =
        typeof ev.article_id === "number" ? ev.article_id : -1;
      const key = `${skill}:${articleId}`;
      setSubagents((prev) => {
        const next = new Map(prev);
        const existing = next.get(key);
        if (stage === "start") {
          next.set(key, {
            skill,
            articleId,
            status: "running",
            startedAt: existing?.startedAt ?? Date.now(),
          });
          // First subagent start — flip "Reading articles" to in-progress.
          setStepStatuses((s) => {
            const ns = { ...s };
            if (ns[STEP_IDS.reading] !== "in-progress" && ns[STEP_IDS.reading] !== "done") {
              stepStartRef.current[STEP_IDS.reading] = Date.now();
              ns[STEP_IDS.reading] = "in-progress";
            }
            return ns;
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
            summary: ev.summary, // NEW M3.M2 — store enriched summary
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

  // -----------------------------------------------------------------------
  // Conduct research (POST + SSE consume).
  // -----------------------------------------------------------------------

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
    setSubagents(new Map());
    setSubagentsOpen(false);
    setSubQuestions([]);
    setSearchResults({});
    setExpandedRows(new Set());
    setStepDurations({});
    setStepStatuses({
      [STEP_IDS.decomposing]: "in-progress",
      [STEP_IDS.searching]: "pending",
      [STEP_IDS.reading]: "pending",
      [STEP_IDS.synthesizing]: "pending",
      [STEP_IDS.done]: "pending",
    });
    runStartRef.current = Date.now();
    stepStartRef.current = {
      [STEP_IDS.decomposing]: Date.now(),
    };

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
          if (j && typeof j.detail === "string") detail = j.detail;
        } catch {
          // not JSON — keep status text
        }
        throw new Error(detail);
      }

      if (!resp.body) throw new Error("Streaming response has no body");

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
      if ((err as Error).name === "AbortError") return;
      // eslint-disable-next-line no-console
      console.warn("research SSE: stream failed:", err);
      setErrorMessage((err as Error).message || "research interrupted");
      setPhase("error");
    } finally {
      setIsResearching(false);
      if (abortRef.current === ac) abortRef.current = null;
    }
  };

  const onRetry = () => {
    if (lastSubmittedQuery) void conductResearch(lastSubmittedQuery);
  };

  const handleCancel = () => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    setIsResearching(false);
    setPhase("");
    setErrorMessage(null);
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
        // fallthrough
      }
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
      if (copiedTimerRef.current) clearTimeout(copiedTimerRef.current);
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
      const stamp = new Date().toISOString().replace(/[:.]/g, "-");
      a.download = `research-${stamp}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (err) {
      // eslint-disable-next-line no-console
      console.warn("research download failed:", err);
      toast.error("Download failed");
    }
  };

  function formatDuration(ms: number): string {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  }

  function truncateMessage(msg: string, max = 80): string {
    if (msg.length <= max) return msg;
    return msg.slice(0, max - 1) + "…";
  }

  // -----------------------------------------------------------------------
  // Derived state
  // -----------------------------------------------------------------------

  const showErrorPanel = phase === "error" && errorMessage !== null;
  const showReport = !showErrorPanel && reportText.length > 0;
  const showEmptyState = !showErrorPanel && !showReport && !isResearching;

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

  // Sub-question status: depends on whether search_results arrived and
  // whether the matching subagents are still in flight. The simplest
  // approximation: pending if no search_results yet; in-progress while
  // subagents are running for any article in that bucket; done if
  // search arrived and no subagents are running on its articles.
  const subQuestionStatusByIndex: Record<number, SubQuestionStatus> = {};
  for (let i = 0; i < subQuestions.length; i += 1) {
    const articles = searchResults[i];
    if (!articles) {
      // No search results yet for this sub-question.
      // If overall searching phase has happened beyond i, mark in-progress;
      // otherwise pending.
      subQuestionStatusByIndex[i] = phase.startsWith("Searching") || subagentRows.length > 0
        ? "in-progress"
        : "pending";
      continue;
    }
    if (articles.length === 0) {
      subQuestionStatusByIndex[i] = "done";
      continue;
    }
    // Done iff all related subagents are finished.
    const articleIds = new Set(articles.map((a) => a.id));
    let anyRunning = false;
    let anyDoneOrError = false;
    for (const row of subagentRows) {
      if (articleIds.has(row.articleId)) {
        if (row.status === "running") anyRunning = true;
        if (row.status === "done" || row.status === "error") anyDoneOrError = true;
      }
    }
    if (anyRunning) subQuestionStatusByIndex[i] = "in-progress";
    else if (anyDoneOrError || phase === "Synthesizing" || phase === "done")
      subQuestionStatusByIndex[i] = "done";
    else subQuestionStatusByIndex[i] = "in-progress";
  }

  // Vertical timeline steps.
  const totalArticles = subagentRows.length;
  const readingDetail = totalArticles
    ? `${runningCount} in flight, ${doneCount} done${
        erroredCount ? `, ${erroredCount} errored` : ""
      }`
    : undefined;
  const timelineSteps: TimelineStep[] = [
    {
      id: STEP_IDS.decomposing,
      label: "Decomposing",
      status: stepStatuses[STEP_IDS.decomposing] ?? "pending",
      durationMs: stepDurations[STEP_IDS.decomposing],
      detail: subQuestions.length
        ? `${subQuestions.length} sub-questions`
        : undefined,
    },
    {
      id: STEP_IDS.searching,
      label: "Searching",
      status: stepStatuses[STEP_IDS.searching] ?? "pending",
      durationMs: stepDurations[STEP_IDS.searching],
      detail: subQuestions.length
        ? `${Object.keys(searchResults).length}/${subQuestions.length} sub-questions`
        : undefined,
    },
    {
      id: STEP_IDS.reading,
      label: "Reading articles",
      status: stepStatuses[STEP_IDS.reading] ?? "pending",
      durationMs: stepDurations[STEP_IDS.reading],
      detail: readingDetail,
    },
    {
      id: STEP_IDS.synthesizing,
      label: "Synthesizing",
      status: stepStatuses[STEP_IDS.synthesizing] ?? "pending",
      durationMs: stepDurations[STEP_IDS.synthesizing],
    },
    {
      id: STEP_IDS.done,
      label: "Done",
      status: stepStatuses[STEP_IDS.done] ?? "pending",
    },
  ];
  if (phase === "error") {
    // Bubble up an error state on whichever step is currently in-flight.
    for (const s of timelineSteps) {
      if (s.status === "in-progress") {
        s.status = "error";
        break;
      }
    }
  }
  // Active step: the in-progress one (if any), else the last done, else
  // the first pending.
  const inProgressStep = timelineSteps.find((s) => s.status === "in-progress");
  const lastDoneStep = [...timelineSteps].reverse().find((s) => s.status === "done");
  const activeStepId =
    inProgressStep?.id ??
    (phase === "done"
      ? STEP_IDS.done
      : lastDoneStep?.id ?? timelineSteps[0].id);

  // Backward-compat phase chip text — mirrors the old single-chip badge.
  const phaseChipText =
    phase === "done"
      ? "Done"
      : phase === "error"
      ? "Error"
      : phase || "";

  // Follow-up suggestions — only when a report is done.
  const followUps = phase === "done" && reportText ? buildFollowUps(reportText) : [];

  // -----------------------------------------------------------------------
  // Toggle expanded row.
  // -----------------------------------------------------------------------
  function toggleRowExpanded(key: string) {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
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
            <Button onClick={() => conductResearch()} disabled={isResearching}>
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

          {showEmptyState && (
            <SuggestedQueries
              queries={EMPTY_STATE_QUERIES}
              onSelect={(q) => {
                setQuery(q);
                void conductResearch(q);
              }}
              label="Suggested queries:"
              data-testid="research-empty-suggestions"
            />
          )}
        </CardContent>
      </Card>

      {/* Sub-questions panel — renders IMMEDIATELY on submit (as a
          skeleton row) so the user sees real content within ~1s of
          click, then upgrades to the numbered list the moment the
          `decomposed` SSE event arrives. This is the M3.M2 iter 2
          time-to-first-content fix. */}
      {(subQuestions.length > 0 || isResearching) && (
        <SubQuestionsPanel
          subQuestions={subQuestions}
          searchResults={searchResults}
          statusByIndex={subQuestionStatusByIndex}
          isDecomposing={isResearching && subQuestions.length === 0}
        />
      )}

      {(isResearching || phase || showReport || showErrorPanel) && (
        <Card data-testid="research-report-card">
          <CardHeader>
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div className="flex items-center gap-2 min-w-0">
                <CardTitle className="text-lg">Research Report</CardTitle>
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
            {/* Vertical progress timeline replaces the single-chip
                phase indicator. The active step's status text carries
                the legacy `research-phase-chip` testid for backward
                compat. */}
            <div className="mb-4">
              <ResearchProgressTimeline
                steps={timelineSteps}
                activeStepId={activeStepId}
                phaseChipText={phaseChipText}
              />
            </div>

            {showSubagentsPanel && (
              <div
                data-testid="research-subagents-panel"
                className="mb-4 border border-gray-200 dark:border-gray-800 rounded-lg overflow-hidden"
              >
                <button
                  type="button"
                  onClick={() => setSubagentsOpen((open) => !open)}
                  data-testid="research-subagents-header"
                  aria-expanded={subagentsOpen}
                  className="w-full flex items-center gap-2 px-3 py-2 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 text-left text-sm font-medium text-gray-800 dark:text-gray-200"
                >
                  {subagentsOpen ? (
                    <ChevronDown className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                  )}
                  <span>{subagentsHeaderText}</span>
                </button>
                {subagentsOpen && (
                  <ul className="divide-y divide-gray-100 dark:divide-gray-800">
                    {subagentRows.map((row) => {
                      const key = `${row.skill}:${row.articleId}`;
                      const isExpanded = expandedRows.has(key);
                      const canExpand =
                        row.status === "done" &&
                        typeof row.summary === "string" &&
                        row.summary.length > 0;
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
                          data-expanded={isExpanded ? "true" : "false"}
                          className="text-sm text-gray-800 dark:text-gray-200"
                        >
                          <button
                            type="button"
                            data-testid="research-subagent-row-toggle"
                            onClick={() => canExpand && toggleRowExpanded(key)}
                            disabled={!canExpand}
                            aria-expanded={isExpanded}
                            className={`w-full flex items-center gap-3 px-3 py-2 text-left min-w-0 ${
                              canExpand
                                ? "cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
                                : "cursor-default"
                            }`}
                          >
                            {canExpand ? (
                              isExpanded ? (
                                <ChevronDown className="w-3 h-3 text-gray-500 flex-shrink-0" />
                              ) : (
                                <ChevronRight className="w-3 h-3 text-gray-500 flex-shrink-0" />
                              )
                            ) : (
                              <span className="w-3 h-3 flex-shrink-0" />
                            )}
                            <span
                              className="font-mono text-xs text-gray-700 dark:text-gray-300 truncate"
                              style={{ overflowWrap: "anywhere" }}
                            >
                              {row.skill}
                            </span>
                            <span className="text-gray-500 dark:text-gray-500 text-xs">
                              #{row.articleId}
                            </span>
                            <Badge
                              variant={badgeVariant}
                              className="capitalize"
                            >
                              {statusLabel}
                            </Badge>
                            {row.status === "done" &&
                              typeof row.durationMs === "number" && (
                                <span className="text-xs text-gray-500 dark:text-gray-500">
                                  {formatDuration(row.durationMs)}
                                </span>
                              )}
                            {row.status === "error" && row.message && (
                              <span
                                className="text-xs text-red-600 dark:text-red-400 truncate"
                                title={row.message}
                                style={{ overflowWrap: "anywhere" }}
                              >
                                {truncateMessage(row.message)}
                              </span>
                            )}
                          </button>
                          {isExpanded && row.summary && (
                            <div
                              data-testid="research-subagent-summary"
                              className="px-6 pb-3 text-xs text-gray-700 dark:text-gray-300 bg-gray-50/50 dark:bg-gray-900/30"
                              style={{ overflowWrap: "anywhere" }}
                            >
                              {row.summary}
                            </div>
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
                className="flex flex-col items-start gap-3 p-4 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 rounded-lg"
              >
                <div className="flex items-center gap-2 text-red-700 dark:text-red-400">
                  <AlertTriangle className="w-5 h-5" />
                  <span className="font-semibold">
                    Research interrupted — retry?
                  </span>
                </div>
                {errorMessage && (
                  <p
                    className="text-sm text-red-700 dark:text-red-400"
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

            {/* Follow-up suggestions — only after a clean done.
                Iter 2 fix: chips are real <button> elements (see
                SuggestedQueries) and each has the distinct
                `research-follow-up-chip` testid so a11y tests can
                target them without colliding with empty-state chips. */}
            {followUps.length > 0 && (
              <div className="mt-6 border-t border-gray-200 dark:border-gray-800 pt-4">
                <SuggestedQueries
                  queries={followUps}
                  onSelect={(q) => {
                    setQuery(q);
                    void conductResearch(q);
                  }}
                  label="Suggested follow-ups:"
                  data-testid="research-follow-ups"
                  chipTestId="research-follow-up-chip"
                />
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {showEmptyState && (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Search className="w-12 h-12 text-gray-400 mb-4" />
            <p className="text-gray-600 dark:text-gray-400 text-center">
              Enter a research query above to get started
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-500 text-center mt-2">
              Our AI agent will search, filter, and generate a comprehensive
              report
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
