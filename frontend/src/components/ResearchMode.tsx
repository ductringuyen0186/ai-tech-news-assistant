import { useEffect, useRef, useState } from "react";
import type React from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
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
  Bookmark,
  BookmarkCheck,
  User,
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

/**
 * ResearchMode -- M3 polish iter 2 conversational redesign.
 *
 * Replaces the previous vertically-stacked panel layout
 * (sub-questions / timeline / subagents / report / follow-ups) with a
 * Claude.ai-style chat transcript:
 *
 *   - User question becomes a right-aligned message bubble
 *     (`bg-secondary`, max-w-2xl, "You . just now" label).
 *   - Agent response is ONE coherent card (`bg-card`, full width) with
 *     an agent-icon header, a phase line, collapsed-by-default
 *     "tool use" blocks ("Decomposed into N sub-questions", "Read M
 *     articles"), the streamed markdown report, and a citation chip
 *     row at the bottom.
 *   - Copy / Download / Save move INTO the agent card's header
 *     (top-right corner, icon-only, tooltips via `title` attr).
 *   - Follow-up chips become a "Continue with:" bar below the agent
 *     message; clicking one starts a NEW Q&A and replaces the
 *     previous transcript (v1: one Q&A at a time, multi-turn deferred
 *     to v2).
 *
 * SSE event surface (unchanged from M3.M2):
 *   - phase: Decomposing | Searching (i/N) | Synthesizing | done
 *   - token: <chunk>
 *   - subagent: start | done | error  (+ enriched `summary` on done)
 *   - error: <message>
 *   - decomposed: {sub_questions: string[]}
 *   - search_results: {sub_question_index, articles}
 *
 * Preserves every existing data-testid used by the Playwright suite:
 *   research-phase-chip, research-subagents-panel, research-subagent-row,
 *   research-report-body, research-report-card, research-save-btn,
 *   research-copy-btn, research-download-btn, research-cancel-btn,
 *   research-retry-btn, research-error-panel, research-follow-ups,
 *   research-follow-up-chip, research-empty-suggestions,
 *   research-sub-questions-panel, research-sub-questions-skeleton,
 *   research-sub-question-row, research-subagent-row-toggle,
 *   research-subagent-summary.
 *
 * Honors `prefers-reduced-motion` via `useReducedMotion` -- all
 * fade/slide transitions resolve instantly when the OS asks for it.
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
    const words = term.split(/\s+/);
    if (words.every((w) => STOPWORDS.has(w))) continue;
    counts.set(term, (counts.get(term) ?? 0) + 1);
  }
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

/**
 * Extract the sorted list of unique citation numbers referenced in the
 * report body -- used to render the "Sources: [1] [2] [3]" chip row at
 * the bottom of the agent card. Each chip is a link to `#source-N`,
 * matching the anchors that `MarkdownReport` assigns to the entries
 * inside the "Sources Used" list.
 */
function extractCitationNumbers(report: string): number[] {
  if (!report) return [];
  const pattern = /\[(\d+)\]/g;
  const seen = new Set<number>();
  let m: RegExpExecArray | null;
  while ((m = pattern.exec(report)) !== null) {
    const n = parseInt(m[1], 10);
    if (!Number.isNaN(n) && n > 0) seen.add(n);
  }
  return Array.from(seen).sort((a, b) => a - b);
}

// ---------------------------------------------------------------------------
// SSE event types
// ---------------------------------------------------------------------------

interface AgentEvent {
  type: "phase" | "token" | "error" | "subagent" | "decomposed" | "search_results";
  data?: string;
  report?: string;
  skill?: string;
  article_id?: number;
  duration_ms?: number;
  message?: string;
  summary?: string;
  sub_questions?: string[];
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
  summary?: string;
}

type StepStatus = "pending" | "in-progress" | "done" | "error";

interface ResearchModeProps {
  // No props needed.
}

export function ResearchMode({}: ResearchModeProps) {
  const reduceMotion = useReducedMotion();
  const [query, setQuery] = useState("");
  const [isResearching, setIsResearching] = useState(false);
  const [phase, setPhase] = useState<string>("");
  const [reportText, setReportText] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [lastSubmittedQuery, setLastSubmittedQuery] = useState<string>("");
  const [copied, setCopied] = useState(false);
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved">(
    "idle"
  );
  const [subagents, setSubagents] = useState<Map<string, SubagentRow>>(
    () => new Map()
  );
  // M3 polish iter 2 -- "tool use" blocks are collapsed by default
  // (Claude.ai style). User clicks the chevron to expand.
  const [subQuestionsOpen, setSubQuestionsOpen] = useState<boolean>(true);
  const [subagentsOpen, setSubagentsOpen] = useState<boolean>(true);
  const [subQuestions, setSubQuestions] = useState<string[]>([]);
  const [searchResults, setSearchResults] = useState<
    Record<number, SubQuestionArticle[]>
  >({});
  const [expandedRows, setExpandedRows] = useState<Set<string>>(
    () => new Set()
  );
  // Per-step bookkeeping -- preserved from M3.M2 so the agent header
  // can still display "elapsed Ns" once the run completes.
  const [stepDurations, setStepDurations] = useState<
    Record<string, number>
  >({});
  const [stepStatuses, setStepStatuses] = useState<
    Record<string, StepStatus>
  >({});
  const runStartRef = useRef<number>(0);
  const stepStartRef = useRef<Record<string, number>>({});
  // Wall-clock tick for the agent header's "elapsed Ns" indicator.
  const [nowMs, setNowMs] = useState<number>(0);

  const abortRef = useRef<AbortController | null>(null);
  const copiedTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // -----------------------------------------------------------------------
  // Step IDs -- internal bookkeeping, no longer rendered as a timeline.
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

  // M3.M1 palette handoff: on mount, if the palette stashed a query in
  // localStorage, pull it, clear the key, and auto-submit.
  const consumedHandoffRef = useRef<boolean>(false);
  useEffect(() => {
    if (consumedHandoffRef.current) return;
    consumedHandoffRef.current = true;
    try {
      const pending = window.localStorage.getItem(PENDING_RESEARCH_KEY);
      if (pending && pending.trim()) {
        window.localStorage.removeItem(PENDING_RESEARCH_KEY);
        setQuery(pending);
        setTimeout(() => {
          void conductResearch(pending);
        }, 50);
      }
    } catch {
      // localStorage unavailable -- silently skip.
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

  // Tick a wall-clock while researching so the agent header can show
  // an "elapsed Ns" line. The tick stops once the run finishes.
  useEffect(() => {
    if (!isResearching) return;
    const id = setInterval(() => setNowMs(Date.now()), 200);
    return () => clearInterval(id);
  }, [isResearching]);

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

      if (ph === "Decomposing") {
        markStepRunning(STEP_IDS.decomposing);
      } else if (ph.startsWith("Searching")) {
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
            summary: ev.summary,
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
    setSaveState("idle");
    setSubagents(new Map());
    setSubQuestionsOpen(true);
    setSubagentsOpen(true);
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
    setNowMs(Date.now());
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
          // not JSON
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

  const onSaveResearch = async () => {
    if (!reportText || saveState !== "idle") return;
    setSaveState("saving");
    try {
      const url = `${API_BASE_URL}${API_ENDPOINTS.savedResearch}`;
      const resp = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: lastSubmittedQuery,
          report_md: reportText,
          sources: [],
        }),
      });
      if (!resp.ok) {
        let detail = `${resp.status} ${resp.statusText}`;
        try {
          const j = await resp.json();
          if (j && typeof j.detail === "string") detail = j.detail;
        } catch {
          // not JSON
        }
        throw new Error(detail);
      }
      setSaveState("saved");
      toast.success("Research saved", {
        description: "Find it in the Saved tab.",
        duration: 3000,
      });
    } catch (err) {
      // eslint-disable-next-line no-console
      console.warn("research save failed:", err);
      toast.error("Failed to save research", {
        description: (err as Error).message || "Please try again.",
        duration: 3000,
      });
      setSaveState("idle");
    }
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
    return msg.slice(0, max - 1) + "...";
  }

  function onCitationClick(e: React.MouseEvent, n: number) {
    e.preventDefault();
    const target = document.getElementById(`source-${n}`);
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  // -----------------------------------------------------------------------
  // Derived state
  // -----------------------------------------------------------------------

  const showErrorPanel = phase === "error" && errorMessage !== null;
  const showReport = !showErrorPanel && reportText.length > 0;
  // The agent message card appears as soon as the user submits -- even
  // while we're still in the early "Decomposing" phase with no tokens
  // yet -- so the user gets a visible "the agent is thinking" surface
  // immediately instead of staring at an empty page.
  const hasActiveQuery =
    lastSubmittedQuery.length > 0 || isResearching || showErrorPanel;
  const showEmptyState =
    !showErrorPanel && !showReport && !isResearching && !hasActiveQuery;

  const subagentRows = Array.from(subagents.values());
  const showSubagentsBlock = subagentRows.length > 0;
  let runningCount = 0;
  let doneCount = 0;
  let erroredCount = 0;
  for (const row of subagentRows) {
    if (row.status === "running") runningCount += 1;
    else if (row.status === "done") doneCount += 1;
    else if (row.status === "error") erroredCount += 1;
  }
  // The summary line doubles as the legacy `research-subagents-header`
  // text (the M3.M2 test contract). Format must match the regex
  //   /Subagents \(\d+ running, \d+ done, \d+ errored\)/i
  // so existing assertions still pass; the chat-style verb ("Reading"
  // / "Read") would break the contract.
  const readArticlesSummary = `Subagents (${runningCount} running, ${doneCount} done, ${erroredCount} errored)`;

  // Sub-question status derivation -- unchanged from M3.M2.
  const subQuestionStatusByIndex: Record<number, SubQuestionStatus> = {};
  for (let i = 0; i < subQuestions.length; i += 1) {
    const articles = searchResults[i];
    if (!articles) {
      subQuestionStatusByIndex[i] = phase.startsWith("Searching") || subagentRows.length > 0
        ? "in-progress"
        : "pending";
      continue;
    }
    if (articles.length === 0) {
      subQuestionStatusByIndex[i] = "done";
      continue;
    }
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

  const subQuestionsSummary = (() => {
    if (subQuestions.length === 0 && isResearching)
      return "Thinking about sub-questions...";
    if (subQuestions.length === 0) return "Decomposed into 0 sub-questions";
    return `Decomposed into ${subQuestions.length} sub-question${subQuestions.length === 1 ? "" : "s"}`;
  })();

  // Backward-compat phase chip text -- mirrors the old single-chip badge
  // so `data-testid="research-phase-chip"` still works in the existing
  // Playwright suite. Maps directly to the SSE `phase` event.
  const phaseChipText =
    phase === "done"
      ? "Done"
      : phase === "error"
      ? "Error"
      : phase || "";

  // Agent header elapsed time -- counts up while running, freezes once
  // the run finishes (sum of per-step durations).
  const agentElapsedMs = (() => {
    if (!runStartRef.current) return 0;
    if (isResearching) return Math.max(0, nowMs - runStartRef.current);
    let total = 0;
    for (const id of Object.values(STEP_IDS)) {
      const d = stepDurations[id];
      if (typeof d === "number") total += d;
    }
    return total;
  })();

  const followUps = phase === "done" && reportText ? buildFollowUps(reportText) : [];
  const citationNumbers = phase === "done" && reportText ? extractCitationNumbers(reportText) : [];

  function toggleRowExpanded(key: string) {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  const phaseChipStatusClass =
    phase === "error"
      ? "text-red-600 dark:text-red-400"
      : phase === "done"
      ? "text-green-700 dark:text-green-400"
      : "text-muted-foreground";

  return (
    <div className="max-w-3xl mx-auto space-y-4">
      {/* =============================================================
       * Header card -- title + input + (when empty) suggested queries.
       * The input lives at the top so the user always knows where to
       * type. On submit, the question becomes a user-message bubble
       * below and the agent card streams in beneath it.
       * ============================================================= */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-primary" />
            Research
          </CardTitle>
          <CardDescription>
            Ask a research question -- the agent will decompose, search, and
            synthesize a report with citations.
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
              label="Try a sample question:"
              data-testid="research-empty-suggestions"
            />
          )}
        </CardContent>
      </Card>

      {/* =============================================================
       * User message bubble -- right-aligned, narrower than the agent
       * card. Renders as soon as a query is in-flight.
       * ============================================================= */}
      {hasActiveQuery && lastSubmittedQuery.length > 0 && (
        <motion.div
          className="flex flex-col items-end"
          initial={
            reduceMotion ? { opacity: 1, y: 0 } : { opacity: 0, y: -4 }
          }
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: reduceMotion ? 0 : 0.18, ease: "easeOut" }}
        >
          <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
            <User className="w-3 h-3" />
            <span className="font-medium">You</span>
            <span>.</span>
            <span>just now</span>
          </div>
          <div
            data-testid="research-user-message"
            className="max-w-2xl bg-secondary text-secondary-foreground rounded-2xl px-4 py-3 text-sm border border-border"
            style={{
              overflowWrap: "anywhere",
              wordBreak: "break-word",
            }}
          >
            {lastSubmittedQuery}
          </div>
        </motion.div>
      )}

      {/* =============================================================
       * Agent message card -- header + tool-use blocks + report body
       * + citation chip row. ONE coherent surface, full width.
       * ============================================================= */}
      {hasActiveQuery && (
        <motion.div
          initial={
            reduceMotion ? { opacity: 1, y: 0 } : { opacity: 0, y: 4 }
          }
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: reduceMotion ? 0 : 0.22, ease: "easeOut" }}
        >
          <Card data-testid="research-report-card" className="bg-card">
            <CardHeader>
              <div className="flex items-center justify-between gap-4 flex-wrap">
                {/* Agent identity + current phase + elapsed time. */}
                <div className="flex items-center gap-2 min-w-0">
                  <Lightbulb className="w-4 h-4 text-primary flex-shrink-0" />
                  <span className="text-sm font-medium text-foreground">
                    Research agent
                  </span>
                  <span className="text-xs text-muted-foreground">.</span>
                  <span
                    data-testid="research-phase-chip"
                    className={`text-xs font-medium ${phaseChipStatusClass}`}
                  >
                    {phaseChipText || (isResearching ? "Thinking..." : "")}
                  </span>
                  {(isResearching || phase === "done") && agentElapsedMs > 0 && (
                    <>
                      <span className="text-xs text-muted-foreground">.</span>
                      <span className="text-xs text-muted-foreground">
                        {formatDuration(agentElapsedMs)}
                      </span>
                    </>
                  )}
                </div>
                {/* Action buttons -- icon-only with title-tooltips. */}
                <div className="flex gap-1.5 flex-wrap">
                  {isResearching && (
                    <Button
                      onClick={handleCancel}
                      variant="outline"
                      size="sm"
                      data-testid="research-cancel-btn"
                      aria-label="Cancel research"
                      title="Cancel research"
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
                        aria-label={copied ? "Copied" : "Copy markdown"}
                        title={copied ? "Copied" : "Copy markdown"}
                        aria-live="polite"
                      >
                        {copied ? (
                          <Check className="w-4 h-4" />
                        ) : (
                          <Copy className="w-4 h-4" />
                        )}
                      </Button>
                      <Button
                        onClick={onDownloadMarkdown}
                        variant="outline"
                        size="sm"
                        data-testid="research-download-btn"
                        aria-label="Download markdown"
                        title="Download .md"
                      >
                        <Download className="w-4 h-4" />
                      </Button>
                      <motion.div
                        whileTap={reduceMotion ? undefined : { scale: 0.95 }}
                        animate={
                          saveState === "saved" && !reduceMotion
                            ? { scale: [1.05, 1] }
                            : { scale: 1 }
                        }
                        transition={{ duration: reduceMotion ? 0 : 0.18 }}
                        style={{ display: "inline-block" }}
                      >
                        <Button
                          onClick={onSaveResearch}
                          variant="outline"
                          size="sm"
                          data-testid="research-save-btn"
                          disabled={saveState !== "idle"}
                          aria-label={
                            saveState === "saved"
                              ? "Saved"
                              : saveState === "saving"
                                ? "Saving"
                                : "Save research"
                          }
                          title={
                            saveState === "saved"
                              ? "Saved"
                              : saveState === "saving"
                                ? "Saving..."
                                : "Save research"
                          }
                          aria-live="polite"
                        >
                          {saveState === "saved" ? (
                            <>
                              <BookmarkCheck className="w-4 h-4 mr-2" />
                              Saved
                            </>
                          ) : saveState === "saving" ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                              Saving...
                            </>
                          ) : (
                            <>
                              <Bookmark className="w-4 h-4 mr-2" />
                              Save
                            </>
                          )}
                        </Button>
                      </motion.div>
                    </>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {/* -----------------------------------------------------
               * Tool-use block #1 -- "Decomposed into N sub-questions"
               * Collapsed by default; expand to see the numbered list
               * with per-question status dots and article previews.
               * The SubQuestionsPanel preserves its existing testids
               * inside the expanded body.
               * ----------------------------------------------------- */}
              {(subQuestions.length > 0 || isResearching) && (
                <ToolUseBlock
                  open={subQuestionsOpen}
                  onToggle={() => setSubQuestionsOpen((v) => !v)}
                  summary={subQuestionsSummary}
                  count={subQuestions.length}
                  loading={isResearching && subQuestions.length === 0}
                  reduceMotion={!!reduceMotion}
                  testid="research-sub-questions-block"
                >
                  <SubQuestionsPanel
                    subQuestions={subQuestions}
                    searchResults={searchResults}
                    statusByIndex={subQuestionStatusByIndex}
                    isDecomposing={isResearching && subQuestions.length === 0}
                  />
                </ToolUseBlock>
              )}

              {/* -----------------------------------------------------
               * Tool-use block #2 -- "Read M articles"
               * Collapsed by default; expand to see per-article rows.
               * Preserves all `research-subagent-*` testids inside.
               * ----------------------------------------------------- */}
              {showSubagentsBlock && (
                <ToolUseBlock
                  open={subagentsOpen}
                  onToggle={() => setSubagentsOpen((v) => !v)}
                  summary={readArticlesSummary}
                  count={subagentRows.length}
                  loading={runningCount > 0}
                  reduceMotion={!!reduceMotion}
                  testid="research-subagents-block"
                  headerTestid="research-subagents-header"
                >
                  <div
                    data-testid="research-subagents-panel"
                    className="border border-border rounded-lg overflow-hidden"
                  >
                    <ul className="divide-y divide-border">
                      <AnimatePresence initial={false}>
                        {subagentRows.map((row, idx) => {
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
                            <motion.li
                              key={key}
                              data-testid="research-subagent-row"
                              data-expanded={isExpanded ? "true" : "false"}
                              className="text-sm text-foreground"
                              initial={
                                reduceMotion
                                  ? { opacity: 1, y: 0 }
                                  : { opacity: 0, y: -4 }
                              }
                              animate={{ opacity: 1, y: 0 }}
                              exit={
                                reduceMotion
                                  ? { opacity: 0, y: 0 }
                                  : { opacity: 0, y: -4 }
                              }
                              transition={{
                                duration: reduceMotion ? 0 : 0.18,
                                delay: reduceMotion
                                  ? 0
                                  : Math.min(idx * 0.05, 0.25),
                                ease: "easeOut",
                              }}
                            >
                              <button
                                type="button"
                                data-testid="research-subagent-row-toggle"
                                onClick={() =>
                                  canExpand && toggleRowExpanded(key)
                                }
                                disabled={!canExpand}
                                aria-expanded={isExpanded}
                                className={`w-full flex items-center gap-3 px-3 py-2 text-left min-w-0 ${
                                  canExpand
                                    ? "cursor-pointer hover:bg-accent"
                                    : "cursor-default"
                                }`}
                              >
                                {canExpand ? (
                                  isExpanded ? (
                                    <ChevronDown className="w-3 h-3 text-muted-foreground flex-shrink-0" />
                                  ) : (
                                    <ChevronRight className="w-3 h-3 text-muted-foreground flex-shrink-0" />
                                  )
                                ) : (
                                  <span className="w-3 h-3 flex-shrink-0" />
                                )}
                                <span
                                  className="font-mono text-xs text-foreground truncate"
                                  style={{ overflowWrap: "anywhere" }}
                                >
                                  {row.skill}
                                </span>
                                <span className="text-muted-foreground text-xs">
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
                                    <span className="text-xs text-muted-foreground">
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
                                  className="px-6 pb-3 text-xs text-muted-foreground bg-muted"
                                  style={{ overflowWrap: "anywhere" }}
                                >
                                  {row.summary}
                                </div>
                              )}
                            </motion.li>
                          );
                        })}
                      </AnimatePresence>
                    </ul>
                  </div>
                </ToolUseBlock>
              )}

              {/* -----------------------------------------------------
               * Streamed markdown report body -- flows top-down,
               * inheriting the agent card's surface. The previous
               * design split this into its own card; iter 2 inlines
               * it into the agent message for the Claude-chat vibe.
               * ----------------------------------------------------- */}
              {showErrorPanel ? (
                <div
                  data-testid="research-error-panel"
                  className="flex flex-col items-start gap-3 p-4 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 rounded-lg"
                >
                  <div className="flex items-center gap-2 text-red-700 dark:text-red-400">
                    <AlertTriangle className="w-5 h-5" />
                    <span className="font-semibold">
                      Research interrupted -- retry?
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
                  style={{
                    overflowWrap: "anywhere",
                    wordBreak: "break-word",
                  }}
                >
                  {reportText.length > 0 ? (
                    <MarkdownReport
                      text={reportText}
                      linkifyCitations={phase === "done"}
                    />
                  ) : (
                    <div className="flex items-center gap-2 text-muted-foreground py-4">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>
                        {phase === "Decomposing"
                          ? "Thinking about sub-questions..."
                          : phase.startsWith("Searching")
                            ? "Searching for articles..."
                            : phase === "Synthesizing"
                              ? "Synthesizing the report..."
                              : "Thinking..."}
                      </span>
                    </div>
                  )}
                </div>
              )}

              {/* -----------------------------------------------------
               * Citation chip row -- bottom of the agent card. Each
               * chip is a button that smooth-scrolls to the matching
               * `#source-N` anchor inside the Sources Used list.
               * Only renders once the run is done.
               * ----------------------------------------------------- */}
              {citationNumbers.length > 0 && (
                <div className="pt-3 border-t border-border flex items-center gap-2 flex-wrap">
                  <span className="text-xs text-muted-foreground font-medium">
                    Sources:
                  </span>
                  {citationNumbers.map((n) => (
                    <a
                      key={n}
                      href={`#source-${n}`}
                      onClick={(e) => onCitationClick(e, n)}
                      className="inline-flex items-center justify-center min-w-[28px] h-6 px-2 rounded-md border border-border bg-muted text-foreground text-xs font-medium hover:bg-accent hover:text-accent-foreground cursor-pointer transition-colors"
                    >
                      [{n}]
                    </a>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* =============================================================
       * Follow-up "Continue with:" bar -- a conversational
       * continuation. Clicking a chip starts a new Q&A and replaces
       * the current transcript (v1 scope: one Q&A at a time).
       * ============================================================= */}
      {followUps.length > 0 && (
        <div className="border border-border rounded-lg p-3 bg-card">
          <SuggestedQueries
            queries={followUps}
            onSelect={(q) => {
              setQuery(q);
              void conductResearch(q);
            }}
            label="Continue with:"
            data-testid="research-follow-ups"
            chipTestId="research-follow-up-chip"
          />
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// ToolUseBlock -- Claude.ai-style collapsible "tool use" surface.
//
// Renders a single muted-background button with a chevron + summary
// line + optional spinner. Click expands the body via framer-motion
// height animation. Honors reduced-motion.
// ---------------------------------------------------------------------------

interface ToolUseBlockProps {
  open: boolean;
  onToggle: () => void;
  /** Summary line shown when collapsed. */
  summary: string;
  /** Item count -- rendered as a small badge after the summary. */
  count?: number;
  /** When true, shows a spinner in the header to signal in-flight work. */
  loading?: boolean;
  reduceMotion: boolean;
  testid?: string;
  /** Optional testid for the clickable header button (legacy contract). */
  headerTestid?: string;
  children: React.ReactNode;
}

function ToolUseBlock({
  open,
  onToggle,
  summary,
  count,
  loading,
  reduceMotion,
  testid,
  headerTestid,
  children,
}: ToolUseBlockProps): JSX.Element {
  return (
    <div
      data-testid={testid}
      className="border border-border rounded-lg overflow-hidden bg-muted"
    >
      <button
        type="button"
        data-testid={headerTestid}
        onClick={onToggle}
        aria-expanded={open}
        className="w-full flex items-center gap-2 px-3 py-2 text-left text-sm text-foreground hover:bg-accent transition-colors"
      >
        {open ? (
          <ChevronDown className="w-3 h-3 text-muted-foreground flex-shrink-0" />
        ) : (
          <ChevronRight className="w-3 h-3 text-muted-foreground flex-shrink-0" />
        )}
        {loading ? (
          <Loader2 className="w-3 h-3 text-primary animate-spin flex-shrink-0" />
        ) : null}
        <span className="flex-1 min-w-0 font-medium">{summary}</span>
        {typeof count === "number" && count > 0 && (
          <Badge
            variant="outline"
            className="text-[10px] py-0 px-1.5 bg-card text-foreground border-border font-medium"
          >
            {count}
          </Badge>
        )}
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            key="tool-use-body"
            initial={
              reduceMotion
                ? { height: "auto", opacity: 1 }
                : { height: 0, opacity: 0 }
            }
            animate={{ height: "auto", opacity: 1 }}
            exit={
              reduceMotion
                ? { height: "auto", opacity: 0 }
                : { height: 0, opacity: 0 }
            }
            transition={{ duration: reduceMotion ? 0 : 0.22, ease: "easeOut" }}
            style={{ overflow: "hidden" }}
          >
            <div className="px-3 pt-1 pb-3 bg-card">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
