import { useEffect, useState } from "react";
import { Bookmark, Trash2, ChevronLeft, Loader2, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { Button } from "./ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { MarkdownReport } from "./MarkdownReport";
import { API_ENDPOINTS, apiFetch, API_BASE_URL } from "../config/api";

/**
 * SavedResearchList — M3.M5 Saved sidebar tab.
 *
 * Renders persisted research reports as a list of (question + relative
 * time + delete). Clicking a row drills into a detail view that uses
 * `MarkdownReport` to render the saved markdown with citations linkified
 * (same as a fresh research run on `phase === "done"`). The delete icon
 * optimistically removes the row on a successful DELETE.
 *
 * Empty state: when the list is empty after the initial fetch we show
 * the "No saved research yet" message anchored on the Bookmark icon.
 *
 * Failure state: when the GET fails we render an inline retry button —
 * the same UX as the research error panel, so users know the failure
 * isn't permanent.
 *
 * Test hooks:
 *   - data-testid="saved-research-list"          (the root list panel)
 *   - data-testid="saved-research-item"           (each row)
 *   - data-testid="saved-research-delete-btn"     (each row's delete icon)
 *   - data-testid="saved-research-empty"          (empty state)
 *   - data-testid="saved-research-detail"         (drill-in detail panel)
 *   - data-testid="saved-research-back-btn"       (back-to-list button)
 */

interface SavedListRow {
  id: number;
  question: string;
  created_at: string;
}

interface SavedFull {
  id: number;
  question: string;
  report_md: string;
  sources: Array<Record<string, unknown>>;
  created_at: string;
}

// ---------------------------------------------------------------------- //
//  Helpers
// ---------------------------------------------------------------------- //

function formatRelativeTime(iso: string): string {
  // SQLite default ``CURRENT_TIMESTAMP`` returns a naive UTC timestamp
  // without timezone marker, e.g. "2026-05-12 20:55:27". Append a Z so
  // ``Date.parse`` treats it as UTC rather than local-time-on-this-box.
  const normalized =
    /Z|[+-]\d{2}:?\d{2}$/.test(iso)
      ? iso
      : iso.includes("T")
        ? `${iso}Z`
        : `${iso.replace(" ", "T")}Z`;
  const then = Date.parse(normalized);
  if (Number.isNaN(then)) return iso;
  const now = Date.now();
  const delta = Math.max(0, now - then);
  const sec = Math.round(delta / 1000);
  if (sec < 60) return "just now";
  const min = Math.round(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.round(min / 60);
  if (hr < 24) return `${hr}h ago`;
  const day = Math.round(hr / 24);
  if (day < 30) return `${day}d ago`;
  const mon = Math.round(day / 30);
  if (mon < 12) return `${mon}mo ago`;
  const yr = Math.round(mon / 12);
  return `${yr}y ago`;
}

// ---------------------------------------------------------------------- //
//  Component
// ---------------------------------------------------------------------- //

interface SavedResearchListProps {
  /** Refresh nonce — bump to force a re-fetch (e.g. after a save). */
  refreshKey?: number;
}

export function SavedResearchList({ refreshKey = 0 }: SavedResearchListProps) {
  const [rows, setRows] = useState<SavedListRow[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Detail view state — when set, we render the full report instead of
  // the list. Keeping this as a number id (rather than the full record)
  // lets the back-button always refetch a fresh copy.
  const [detailId, setDetailId] = useState<number | null>(null);
  const [detail, setDetail] = useState<SavedFull | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  // -------------------------------------------------------------------- //
  //  List fetch
  // -------------------------------------------------------------------- //

  async function fetchList() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<SavedListRow[]>(API_ENDPOINTS.savedResearch);
      setRows(Array.isArray(data) ? data : []);
    } catch (err) {
      // eslint-disable-next-line no-console
      console.warn("SavedResearchList: list fetch failed", err);
      setError((err as Error).message || "Failed to load saved research");
      setRows(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void fetchList();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey]);

  // -------------------------------------------------------------------- //
  //  Detail fetch
  // -------------------------------------------------------------------- //

  useEffect(() => {
    if (detailId === null) {
      setDetail(null);
      setDetailError(null);
      return;
    }
    let cancelled = false;
    (async () => {
      setDetailLoading(true);
      setDetailError(null);
      try {
        const data = await apiFetch<SavedFull>(
          API_ENDPOINTS.savedResearchById(detailId)
        );
        if (!cancelled) setDetail(data);
      } catch (err) {
        // eslint-disable-next-line no-console
        console.warn("SavedResearchList: detail fetch failed", err);
        if (!cancelled) {
          setDetailError(
            (err as Error).message || "Failed to load saved report"
          );
          setDetail(null);
        }
      } finally {
        if (!cancelled) setDetailLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [detailId]);

  // -------------------------------------------------------------------- //
  //  Delete
  // -------------------------------------------------------------------- //

  async function handleDelete(id: number) {
    // Optimistic remove — drop the row first, restore if the DELETE fails.
    const prev = rows ?? [];
    setRows(prev.filter((r) => r.id !== id));
    // If the detail view is open on this id, snap back to the list.
    if (detailId === id) setDetailId(null);

    try {
      const url = `${API_BASE_URL}${API_ENDPOINTS.savedResearchById(id)}`;
      const resp = await fetch(url, { method: "DELETE" });
      if (!resp.ok && resp.status !== 204) {
        throw new Error(`DELETE failed: ${resp.status} ${resp.statusText}`);
      }
      toast.success("Saved research deleted");
    } catch (err) {
      // eslint-disable-next-line no-console
      console.warn("SavedResearchList: delete failed", err);
      toast.error("Failed to delete saved research");
      // Restore the row.
      setRows(prev);
    }
  }

  // -------------------------------------------------------------------- //
  //  Render — detail view
  // -------------------------------------------------------------------- //

  if (detailId !== null) {
    return (
      <div className="max-w-4xl mx-auto space-y-6" data-testid="saved-research-detail">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setDetailId(null)}
          data-testid="saved-research-back-btn"
        >
          <ChevronLeft className="w-4 h-4 mr-1" />
          Back to saved
        </Button>

        {detailLoading && (
          <Card>
            <CardContent className="flex items-center gap-2 py-12 justify-center text-muted-foreground">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Loading saved report...</span>
            </CardContent>
          </Card>
        )}

        {detailError && !detailLoading && (
          <Card>
            <CardContent className="flex items-start gap-3 py-6">
              <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm text-foreground font-medium">
                  Failed to load saved report
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {detailError}
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  // Force a refetch by toggling detailId.
                  const id = detailId;
                  setDetailId(null);
                  setTimeout(() => setDetailId(id), 0);
                }}
              >
                Retry
              </Button>
            </CardContent>
          </Card>
        )}

        {detail && !detailLoading && !detailError && (
          <Card>
            <CardHeader>
              <CardTitle className="text-xl font-semibold break-words text-foreground">
                {detail.question}
              </CardTitle>
              <CardDescription className="text-sm">
                Saved {formatRelativeTime(detail.created_at)}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div
                className="min-w-0 overflow-hidden"
                style={{ overflowWrap: "anywhere", wordBreak: "break-word" }}
              >
                <MarkdownReport text={detail.report_md} linkifyCitations />
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  }

  // -------------------------------------------------------------------- //
  //  Render — list view
  // -------------------------------------------------------------------- //

  return (
    <div
      className="max-w-3xl mx-auto space-y-6"
      data-testid="saved-research-list"
    >
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-semibold">
            <Bookmark className="w-5 h-5 text-primary" />
            Saved research
          </CardTitle>
          <CardDescription className="text-sm">
            Research reports you've saved. Click a row to re-open it; the
            trash icon removes it permanently.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading && (
            <div className="flex items-center justify-center py-12 text-muted-foreground gap-2">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Loading saved research...</span>
            </div>
          )}

          {!loading && error && (
            <div className="flex items-start gap-3 py-6 border border-destructive/40 rounded-md px-4 bg-destructive/5">
              <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm text-foreground font-medium">
                  Failed to load saved research
                </p>
                <p className="text-xs text-muted-foreground mt-1">{error}</p>
              </div>
              <Button variant="outline" size="sm" onClick={() => void fetchList()}>
                Retry
              </Button>
            </div>
          )}

          {!loading && !error && rows && rows.length === 0 && (
            <div
              className="text-center py-12"
              data-testid="saved-research-empty"
            >
              <Bookmark className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
              <p className="text-sm text-muted-foreground">
                No saved research yet. Run a research query and click Save.
              </p>
            </div>
          )}

          {!loading && !error && rows && rows.length > 0 && (
            <ul className="divide-y divide-border border border-border rounded-md overflow-hidden">
              {rows.map((row) => (
                <li
                  key={row.id}
                  data-testid="saved-research-item"
                  className="bg-card hover:bg-accent/40 transition-colors"
                >
                  <div className="flex items-stretch">
                    <button
                      type="button"
                      onClick={() => setDetailId(row.id)}
                      className="flex-1 px-4 py-4 min-w-0 flex flex-col items-start text-left space-y-1"
                    >
                      <p
                        className="text-sm text-foreground font-medium truncate text-left w-full"
                        title={row.question}
                      >
                        {row.question}
                      </p>
                      <p className="text-xs text-muted-foreground text-left w-full">
                        {formatRelativeTime(row.created_at)}
                      </p>
                    </button>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        void handleDelete(row.id);
                      }}
                      data-testid="saved-research-delete-btn"
                      aria-label={`Delete saved research: ${row.question}`}
                      className="px-3 flex items-center justify-center text-muted-foreground hover:text-destructive transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
