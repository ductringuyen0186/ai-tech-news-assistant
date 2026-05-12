import { Loader2, CheckCircle2, Circle } from "lucide-react";
import { Badge } from "./ui/badge";

/**
 * SubQuestionsPanel — M3.M2 sub-questions + per-question search results.
 *
 * Renders the agent's decomposition output the moment the `decomposed`
 * SSE event arrives, so the user sees real content within ~5s of submit
 * instead of waiting on synthesis tokens.
 *
 * Per-question status derives from the parent's bookkeeping:
 *   - pending: no `search_results` event for this index yet
 *   - in-progress: `search_results` arrived but at least one subagent
 *     for this question is still running
 *   - done: all subagents for this question finished (or none ran)
 *
 * The article list per sub-question is populated from `searchResults`
 * (the new `search_results` SSE event); each row shows title + source
 * chip.
 */

export interface SubQuestionArticle {
  id: number;
  title: string;
  source: string;
}

export type SubQuestionStatus = "pending" | "in-progress" | "done";

interface SubQuestionsPanelProps {
  subQuestions: string[];
  /** Map sub-question index (0-based) → article preview list. */
  searchResults: Record<number, SubQuestionArticle[]>;
  /** Map sub-question index (0-based) → status derived by parent. */
  statusByIndex: Record<number, SubQuestionStatus>;
  /**
   * M3.M2 iter 2 — when `true` AND `subQuestions` is empty, render a
   * skeleton row ("Decomposing your question...") so the user gets
   * time-to-first-content within ~1s of submit instead of staring at
   * a spinner-only screen while gpt-oss:20b takes 15+s to decompose.
   */
  isDecomposing?: boolean;
}

function StatusDot({ status }: { status: SubQuestionStatus }): JSX.Element {
  if (status === "done") {
    return (
      <CheckCircle2
        className="w-4 h-4 text-green-600 dark:text-green-400"
        aria-label="done"
        data-testid="sub-question-status-done"
      />
    );
  }
  if (status === "in-progress") {
    return (
      <Loader2
        className="w-4 h-4 text-blue-600 dark:text-blue-400 animate-spin"
        aria-label="in progress"
        data-testid="sub-question-status-running"
      />
    );
  }
  return (
    <Circle
      className="w-4 h-4 text-muted-foreground"
      aria-label="pending"
      data-testid="sub-question-status-pending"
    />
  );
}

export function SubQuestionsPanel({
  subQuestions,
  searchResults,
  statusByIndex,
  isDecomposing = false,
}: SubQuestionsPanelProps): JSX.Element | null {
  const hasQuestions = Array.isArray(subQuestions) && subQuestions.length > 0;
  // If we have no questions AND we're not actively decomposing, render
  // nothing (preserves the idle/empty-state behavior).
  if (!hasQuestions && !isDecomposing) return null;

  // Skeleton path: the `decomposed` SSE event hasn't arrived yet, but
  // the user already pressed Submit. Surface a single placeholder row
  // so they see real content within ~1s of click.
  if (!hasQuestions) {
    return (
      <div
        data-testid="research-sub-questions-panel"
        data-state="decomposing"
        className="border border-gray-200 dark:border-gray-800 rounded-lg overflow-hidden bg-white dark:bg-gray-900"
      >
        <div className="px-3 py-2 bg-muted text-sm font-medium text-foreground border-b border-border">
          Sub-questions
        </div>
        <ol className="divide-y divide-gray-100 dark:divide-gray-800">
          <li
            data-testid="research-sub-questions-skeleton"
            className="px-3 py-2 text-sm text-muted-foreground"
          >
            <div className="flex items-center gap-2 min-w-0">
              <Loader2
                className="w-4 h-4 text-blue-600 dark:text-blue-400 animate-spin flex-shrink-0"
                aria-label="decomposing"
              />
              <span
                className="flex-1 min-w-0"
                style={{ overflowWrap: "anywhere" }}
              >
                Decomposing your question into 3-5 sub-questions...
              </span>
            </div>
          </li>
        </ol>
      </div>
    );
  }

  return (
    <div
      data-testid="research-sub-questions-panel"
      data-state="ready"
      className="border border-gray-200 dark:border-gray-800 rounded-lg overflow-hidden bg-white dark:bg-gray-900"
    >
      <div className="px-3 py-2 bg-muted text-sm font-medium text-foreground border-b border-border">
        Sub-questions ({subQuestions.length})
      </div>
      <ol className="divide-y divide-gray-100 dark:divide-gray-800">
        {subQuestions.map((q, idx) => {
          const status = statusByIndex[idx] ?? "pending";
          const articles = searchResults[idx] ?? [];
          return (
            <li
              key={idx}
              data-testid="research-sub-question-row"
              className="px-3 py-2 text-sm text-foreground"
            >
              <div className="flex items-start gap-2 min-w-0">
                <span className="font-mono text-xs text-muted-foreground mt-0.5">
                  {idx + 1}.
                </span>
                <span className="mt-0.5 flex-shrink-0">
                  <StatusDot status={status} />
                </span>
                <span
                  className="flex-1 min-w-0"
                  style={{ overflowWrap: "anywhere", wordBreak: "break-word" }}
                >
                  {q}
                </span>
              </div>
              {articles.length > 0 && (
                <ul
                  data-testid="research-sub-question-articles"
                  className="mt-1 ml-7 space-y-1"
                >
                  {articles.map((a) => (
                    <li
                      key={a.id}
                      data-testid="research-sub-question-article"
                      className="flex items-center gap-2 text-xs text-muted-foreground min-w-0"
                    >
                      <span
                        className="truncate"
                        style={{ overflowWrap: "anywhere" }}
                      >
                        {a.title}
                      </span>
                      {a.source && (
                        <Badge
                          variant="outline"
                          className="text-[10px] py-0 px-1 flex-shrink-0"
                        >
                          {a.source}
                        </Badge>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </li>
          );
        })}
      </ol>
    </div>
  );
}

export default SubQuestionsPanel;
