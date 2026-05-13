/**
 * CommandPalette — Mission 3 / Milestone 1.
 *
 * Global Cmd+K (macOS) / Ctrl+K (Win/Linux) command palette. Lists:
 *   - 6 tab destinations (mirror of SIDEBAR_NAV_ITEMS)
 *   - The last 10 research queries from
 *     `localStorage.techpulse-recent-research` (set by ResearchMode in
 *     M2). When unset / malformed we render an empty section.
 *
 * Selecting a tab switches the active tab. Selecting a recent research
 * query switches to the Research tab AND writes the query into
 * `localStorage.techpulse-pending-research` so ResearchMode can pick it
 * up on next mount (auto-submit is M2's concern).
 *
 * The provider also exposes a `useCommandPalette()` hook with `open()` /
 * `close()` so any descendant (e.g. the Cmd+K button in the sidebar) can
 * trigger it imperatively.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  ReactNode,
} from "react";
import { Command } from "cmdk";
import { DialogTitle } from "./ui/dialog";
import {
  Newspaper,
  Lightbulb,
  Network,
  Mail,
  Settings,
  Bookmark,
  History,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Tab catalogue — single source of truth for the palette's destination list.
// Kept in sync with Sidebar.tsx's SIDEBAR_NAV_ITEMS. Duplicated here (rather
// than imported) so this file stays independent from Sidebar — the palette
// is mounted at App-root level and Sidebar consumes it (not the other way
// round).
// ---------------------------------------------------------------------------
interface TabEntry {
  value: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const TAB_ENTRIES: TabEntry[] = [
  { value: "feed", label: "News Feed", icon: Newspaper },
  { value: "research", label: "Research", icon: Lightbulb },
  { value: "knowledge", label: "Knowledge", icon: Network },
  { value: "digest", label: "Digest", icon: Mail },
  { value: "saved", label: "Saved", icon: Bookmark },
  { value: "preferences", label: "Settings", icon: Settings },
];

const RECENT_RESEARCH_KEY = "techpulse-recent-research";
const PENDING_RESEARCH_KEY = "techpulse-pending-research";

// ---------------------------------------------------------------------------
// Context — exposes open() / close() to descendants.
// ---------------------------------------------------------------------------
interface CommandPaletteContextValue {
  open: () => void;
  close: () => void;
  toggle: () => void;
  isOpen: boolean;
}

const CommandPaletteContext = createContext<CommandPaletteContextValue | null>(null);

export function useCommandPalette(): CommandPaletteContextValue {
  const ctx = useContext(CommandPaletteContext);
  if (!ctx) {
    throw new Error("useCommandPalette must be used inside <CommandPaletteProvider>");
  }
  return ctx;
}

// ---------------------------------------------------------------------------
// Helper: pull the 10 most recent research queries from localStorage. The
// shape is whatever ResearchMode chooses to write in M2 — we accept both
// `string[]` (just the question text) and `{question: string}[]` shapes and
// silently coerce. Malformed JSON returns an empty array.
// ---------------------------------------------------------------------------
function readRecentResearch(): string[] {
  try {
    const raw = localStorage.getItem(RECENT_RESEARCH_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object" && typeof item.question === "string") {
          return item.question;
        }
        return "";
      })
      .filter((q) => q.length > 0)
      .slice(0, 10);
  } catch {
    return [];
  }
}

// ---------------------------------------------------------------------------
// Provider — wraps the app and renders the modal as a portal-like overlay.
// ---------------------------------------------------------------------------
interface CommandPaletteProviderProps {
  children: ReactNode;
  /** Currently active tab value (controlled by App.tsx). */
  activeTab: string;
  /** Callback to switch the active tab. */
  onSelectTab: (value: string) => void;
}

export function CommandPaletteProvider({
  children,
  activeTab: _activeTab,
  onSelectTab,
}: CommandPaletteProviderProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [recentResearch, setRecentResearch] = useState<string[]>([]);

  const open = useCallback(() => {
    // Refresh the recents list every time we open — cheap, and the user
    // probably ran a research since they last opened the palette.
    setRecentResearch(readRecentResearch());
    setIsOpen(true);
  }, []);

  const close = useCallback(() => setIsOpen(false), []);

  const toggle = useCallback(() => {
    setIsOpen((prev) => {
      if (!prev) {
        setRecentResearch(readRecentResearch());
      }
      return !prev;
    });
  }, []);

  // Global Cmd+K / Ctrl+K hotkey. We attach to `window` so the shortcut
  // works regardless of which element has focus. `preventDefault` stops
  // the browser's default "focus address bar" / "search" mapping.
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const key = e.key.toLowerCase();
      const isModifier = e.metaKey || e.ctrlKey;
      if (isModifier && key === "k") {
        e.preventDefault();
        toggle();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [toggle]);

  const ctxValue = useMemo<CommandPaletteContextValue>(
    () => ({ open, close, toggle, isOpen }),
    [open, close, toggle, isOpen]
  );

  const handleSelectTab = (value: string) => {
    onSelectTab(value);
    close();
  };

  const handleSelectRecent = (question: string) => {
    // Stash the query so ResearchMode can pick it up on its next render.
    try {
      localStorage.setItem(PENDING_RESEARCH_KEY, question);
    } catch {
      // If storage is unavailable we just navigate without prefill.
    }
    onSelectTab("research");
    close();
  };

  return (
    <CommandPaletteContext.Provider value={ctxValue}>
      {children}
      {isOpen && (
        <CommandPaletteModal
          recentResearch={recentResearch}
          onSelectTab={handleSelectTab}
          onSelectRecent={handleSelectRecent}
          onClose={close}
        />
      )}
    </CommandPaletteContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// Modal — built on cmdk. cmdk handles arrow keys + Enter navigation and the
// Escape-to-close keybinding through its `<Command.Dialog>` primitive.
// ---------------------------------------------------------------------------
interface CommandPaletteModalProps {
  recentResearch: string[];
  onSelectTab: (value: string) => void;
  onSelectRecent: (question: string) => void;
  onClose: () => void;
}

function CommandPaletteModal({
  recentResearch,
  onSelectTab,
  onSelectRecent,
  onClose,
}: CommandPaletteModalProps) {
  return (
    <Command.Dialog
      open
      onOpenChange={(o) => {
        if (!o) onClose();
      }}
      label="Command palette"
      // The className passed to Command.Dialog flows to the inner Command
      // root (cmdk's source code: `<Command className={className} />`).
      // overlayClassName/contentClassName style the Radix overlay + content
      // wrappers. The Radix Dialog Content already handles Esc-to-close and
      // backdrop-click-to-close through onOpenChange.
      className="flex flex-col"
      overlayClassName="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
      contentClassName="fixed top-[15vh] left-1/2 -translate-x-1/2 z-50 w-[min(640px,calc(100vw-2rem))] max-h-[60vh] bg-popover text-popover-foreground border border-border rounded-xl shadow-2xl overflow-hidden"
    >
      <>
        {/*
          Radix Dialog requires an accessible title. cmdk's Command.Dialog
          wraps Radix Dialog but doesn't auto-inject one. Add a
          screen-reader-only title to silence the a11y warnings AND
          improve screen-reader UX.
        */}
        <DialogTitle className="sr-only">Command palette</DialogTitle>
        <Command.Input
          placeholder="Jump to a tab or recent research..."
          className="w-full px-4 py-3 text-sm bg-transparent border-b border-border outline-none placeholder:text-muted-foreground"
        />
        <Command.List className="flex-1 overflow-y-auto p-2">
          <Command.Empty className="px-3 py-6 text-sm text-muted-foreground text-center">
            No matches.
          </Command.Empty>

          <Command.Group
            heading="Navigation"
            className="text-[11px] text-muted-foreground uppercase tracking-wider px-2 py-1"
          >
            {TAB_ENTRIES.map((tab) => {
              const Icon = tab.icon;
              return (
                <Command.Item
                  key={tab.value}
                  value={`tab:${tab.value}:${tab.label}`}
                  onSelect={() => onSelectTab(tab.value)}
                  className="flex items-center gap-2 px-2 py-1.5 text-sm rounded-md cursor-pointer text-foreground data-[selected=true]:bg-accent data-[selected=true]:text-accent-foreground"
                >
                  <Icon className="w-4 h-4 text-muted-foreground" />
                  <span>{tab.label}</span>
                </Command.Item>
              );
            })}
          </Command.Group>

          {recentResearch.length > 0 && (
            <Command.Group
              heading="Recent research"
              className="text-[11px] text-muted-foreground uppercase tracking-wider px-2 py-1 mt-2"
            >
              {recentResearch.map((question, idx) => (
                <Command.Item
                  key={`recent-${idx}`}
                  value={`recent:${idx}:${question}`}
                  onSelect={() => onSelectRecent(question)}
                  className="flex items-center gap-2 px-2 py-1.5 text-sm rounded-md cursor-pointer text-foreground data-[selected=true]:bg-accent data-[selected=true]:text-accent-foreground"
                >
                  <History className="w-4 h-4 text-muted-foreground shrink-0" />
                  <span className="truncate">{question}</span>
                </Command.Item>
              ))}
            </Command.Group>
          )}
        </Command.List>
        <div className="border-t border-border px-3 py-2 text-[11px] text-muted-foreground flex items-center justify-between">
          <span>
            <kbd className="px-1 py-[1px] border border-border rounded bg-muted text-[10px]">
              esc
            </kbd>{" "}
            to close
          </span>
          <span>
            <kbd className="px-1 py-[1px] border border-border rounded bg-muted text-[10px]">
              up
            </kbd>{" "}
            <kbd className="px-1 py-[1px] border border-border rounded bg-muted text-[10px]">
              down
            </kbd>{" "}
            navigate ·{" "}
            <kbd className="px-1 py-[1px] border border-border rounded bg-muted text-[10px]">
              enter
            </kbd>{" "}
            select
          </span>
        </div>
      </>
    </Command.Dialog>
  );
}
