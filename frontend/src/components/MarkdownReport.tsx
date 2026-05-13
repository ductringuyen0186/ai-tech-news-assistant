import type React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/**
 * MarkdownReport — M3.M2 markdown renderer.
 *
 * Replaces the hand-rolled M3 inline renderer with `react-markdown` +
 * `remark-gfm`. Fixes the GFM table bug (the previous renderer didn't
 * understand `| col | col |\n|---|---|` and rendered tables as raw pipes
 * and dashes).
 *
 * Security: `rehype-raw` is intentionally NOT used. Any HTML inside the
 * model-emitted markdown is escaped, so a poisoned source can't inject
 * arbitrary tags / script / style.
 *
 * Citation linkifier:
 * - When `linkifyCitations=true`, plain-text `[N]` markers in paragraphs,
 *   list items, table cells, etc. are turned into
 *   `<a class="citation" href="#source-N">[N]</a>` anchors. Clicking
 *   smooth-scrolls to the matching `#source-N` id (assigned by the
 *   first list under any `Sources Used` heading).
 * - When `linkifyCitations=false` (default — streaming phase) the markers
 *   pass through as literal text to avoid mid-stream flicker.
 *
 * M3.M4 addition — `renderCitation`:
 * Optional callback invoked for each `[N]` anchor. Receives the citation
 * number plus the rendered anchor element and returns the React node to
 * insert in its place. Used by ResearchMode to wrap each citation in a
 * `<CitationHoverCard>` that fetches `/api/news/{id}` and shows a
 * preview card on hover.
 */

interface MarkdownReportProps {
  text: string;
  /**
   * When true, inline `[N]` markers become anchor links and the first
   * list under a `Sources Used` heading gets sequential `id="source-N"`
   * anchors. Off during streaming.
   */
  linkifyCitations?: boolean;
  /**
   * Optional wrapper for each citation anchor. Called as
   * `renderCitation(n, anchor)` where `n` is the citation index (1-based)
   * and `anchor` is the rendered `<a class="citation">` element. The
   * returned node replaces the bare anchor in the output. Default: pass
   * through.
   */
  renderCitation?: (n: number, anchor: React.ReactElement) => React.ReactNode;
}

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

/**
 * Walk a node's children array and split string children on `[N]` so the
 * numeric citation markers become `<a class="citation">` anchors. Skips
 * non-string children (already-rendered React elements) so nested
 * formatting (bold, code, links) is preserved.
 */
function linkifyChildren(
  children: React.ReactNode,
  keyPrefix: string,
  renderCitation?: (n: number, anchor: React.ReactElement) => React.ReactNode
): React.ReactNode {
  const pattern = /\[(\d+)\]/g;
  const out: React.ReactNode[] = [];
  let i = 0;

  const walk = (node: React.ReactNode): void => {
    if (typeof node === "string") {
      let lastIndex = 0;
      let m: RegExpExecArray | null;
      pattern.lastIndex = 0;
      while ((m = pattern.exec(node)) !== null) {
        if (m.index > lastIndex) {
          out.push(node.slice(lastIndex, m.index));
        }
        const n = parseInt(m[1], 10);
        const key = `${keyPrefix}-cite-${i++}`;
        const anchor = (
          <a
            key={key}
            className="citation text-blue-600 hover:underline cursor-pointer"
            href={`#source-${n}`}
            onClick={(e) => handleCitationClick(e, n)}
          >
            [{n}]
          </a>
        );
        if (renderCitation) {
          // Wrap the anchor (e.g. with a hover card). Force a key on the
          // wrapping span so React's reconciliation stays stable.
          out.push(<span key={key}>{renderCitation(n, anchor)}</span>);
        } else {
          out.push(anchor);
        }
        lastIndex = m.index + m[0].length;
      }
      if (lastIndex < node.length) {
        out.push(node.slice(lastIndex));
      }
      return;
    }
    if (Array.isArray(node)) {
      for (const child of node) walk(child);
      return;
    }
    out.push(node);
  };

  walk(children);
  return out;
}

export function MarkdownReport({
  text,
  linkifyCitations = false,
  renderCitation,
}: MarkdownReportProps): JSX.Element {
  // -----------------------------------------------------------------------
  // Source-anchor state. While react-markdown walks the AST it calls our
  // `components.h2` override; we use closure variables to track whether
  // we're currently rendering inside a "Sources Used" section, and to
  // assign sequential `id="source-N"` attributes to the first list under
  // that heading.
  //
  // react-markdown re-renders the entire tree on every text update, so we
  // reset these counters at the start of every render.
  // -----------------------------------------------------------------------
  let inSourcesSection = false;
  let sourceCounter = 0;

  // M3.M5.5 — Claude-aesthetic markdown contrast. The previous gray-900/
  // gray-50 pairing rendered too dim on the new warm-charcoal dark theme;
  // route H1–H4 through the semantic `text-foreground` token so they
  // inherit the same cream tone the rest of the report uses.
  const headingClass = (level: number) => {
    if (level === 1)
      return "text-2xl font-bold mt-5 mb-3 text-foreground";
    if (level === 2)
      return "text-xl font-semibold mt-5 mb-2 text-foreground";
    if (level === 3)
      return "text-base font-semibold mt-4 mb-2 text-foreground";
    return "text-sm font-semibold mt-3 mb-1.5 text-foreground";
  };

  return (
    <div className="prose prose-sm max-w-none dark:prose-invert">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children, ...rest }) => {
            const text = String(children ?? "").trim();
            if (linkifyCitations && /^sources?\b/i.test(text)) {
              inSourcesSection = true;
              sourceCounter = 0;
            } else {
              inSourcesSection = false;
            }
            return (
              <h1 className={headingClass(1)} {...rest}>
                {children}
              </h1>
            );
          },
          h2: ({ children, ...rest }) => {
            const text = String(children ?? "").trim();
            if (linkifyCitations && /^sources?\b/i.test(text)) {
              inSourcesSection = true;
              sourceCounter = 0;
            } else {
              inSourcesSection = false;
            }
            return (
              <h2 className={headingClass(2)} {...rest}>
                {children}
              </h2>
            );
          },
          h3: ({ children, ...rest }) => {
            const t = String(children ?? "").trim();
            if (linkifyCitations && /^sources?\b/i.test(t)) {
              inSourcesSection = true;
              sourceCounter = 0;
            } else {
              inSourcesSection = false;
            }
            return (
              <h3 className={headingClass(3)} {...rest}>
                {children}
              </h3>
            );
          },
          h4: ({ children, ...rest }) => (
            <h4 className={headingClass(4)} {...rest}>
              {children}
            </h4>
          ),
          p: ({ children, ...rest }) => (
            <p
              className="my-3 leading-relaxed text-foreground text-sm"
              style={{
                overflowWrap: "anywhere",
                wordBreak: "break-word",
              }}
              {...rest}
            >
              {linkifyCitations
                ? linkifyChildren(children, "p", renderCitation)
                : children}
            </p>
          ),
          ul: ({ children, ...rest }) => (
            <ul
              className="my-3 space-y-1.5 text-foreground text-sm list-disc ml-6 leading-relaxed"
              {...rest}
            >
              {children}
            </ul>
          ),
          ol: ({ children, ...rest }) => (
            <ol
              className="my-3 space-y-1.5 text-foreground text-sm list-decimal ml-6 leading-relaxed"
              {...rest}
            >
              {children}
            </ol>
          ),
          li: ({ children, ...rest }) => {
            // If we're inside the Sources section, claim a sequential
            // anchor id for this <li>. Cap at 1000 so a runaway list
            // doesn't generate silly counts.
            const anchorId =
              inSourcesSection && sourceCounter < 1000
                ? `source-${++sourceCounter}`
                : undefined;
            return (
              <li id={anchorId} {...rest}>
                {linkifyCitations
                  ? linkifyChildren(children, "li", renderCitation)
                  : children}
              </li>
            );
          },
          a: ({ href, children, ...rest }) => {
            // Already-linkified citation anchors keep their existing
            // styling. External links open in a new tab.
            const isCitation =
              typeof href === "string" && href.startsWith("#source-");
            if (isCitation) {
              const m = href.match(/^#source-(\d+)$/);
              const n = m ? parseInt(m[1], 10) : 0;
              return (
                <a
                  className="citation text-blue-600 hover:underline cursor-pointer"
                  href={href}
                  onClick={(e) => handleCitationClick(e, n)}
                  {...rest}
                >
                  {children}
                </a>
              );
            }
            return (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline break-words"
                {...rest}
              >
                {children}
              </a>
            );
          },
          code: ({ inline, className, children, ...rest }: any) => {
            if (inline) {
              return (
                <code
                  className="bg-muted text-foreground rounded px-1 py-0.5 text-[0.9em] font-mono"
                  {...rest}
                >
                  {children}
                </code>
              );
            }
            return (
              <code
                className={`block bg-muted text-foreground rounded p-3 text-[0.9em] font-mono overflow-x-auto ${className ?? ""}`}
                {...rest}
              >
                {children}
              </code>
            );
          },
          pre: ({ children, ...rest }) => (
            <pre
              className="my-2 bg-muted rounded p-3 overflow-x-auto"
              {...rest}
            >
              {children}
            </pre>
          ),
          // ----- GFM table support (the table-bug fix) -----
          table: ({ children, ...rest }) => (
            <div className="my-3 overflow-x-auto">
              <table
                className="min-w-full border-collapse border border-border text-sm"
                {...rest}
              >
                {children}
              </table>
            </div>
          ),
          thead: ({ children, ...rest }) => (
            <thead
              className="bg-muted text-foreground"
              {...rest}
            >
              {children}
            </thead>
          ),
          tbody: ({ children, ...rest }) => (
            <tbody className="divide-y divide-border" {...rest}>
              {children}
            </tbody>
          ),
          tr: ({ children, ...rest }) => <tr {...rest}>{children}</tr>,
          th: ({ children, ...rest }: any) => (
            <th
              className="border border-border px-3 py-2 text-left font-semibold text-foreground"
              {...rest}
            >
              {children}
            </th>
          ),
          td: ({ children, ...rest }: any) => (
            <td
              className="border border-border px-3 py-2 align-top text-foreground"
              {...rest}
            >
              {linkifyCitations
                ? linkifyChildren(children, "td", renderCitation)
                : children}
            </td>
          ),
          blockquote: ({ children, ...rest }) => (
            <blockquote
              className="border-l-4 border-border pl-3 my-2 italic text-muted-foreground"
              {...rest}
            >
              {children}
            </blockquote>
          ),
          hr: () => (
            <hr className="my-4 border-border" />
          ),
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  );
}

export default MarkdownReport;
