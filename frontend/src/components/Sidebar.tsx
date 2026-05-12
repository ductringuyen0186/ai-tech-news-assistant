/**
 * Sidebar — Mission 3 / Milestone 1.
 *
 * Left vertical nav with 6 tab entries + Saved Research placeholder + a
 * theme toggle at the bottom. Built on Radix's TabsList/TabsTrigger so
 * the existing 35 Playwright tests' `getByRole("tab", {name: /<Name>/i})`
 * selectors keep working — `TabsList` renders `role="tablist"` and each
 * `TabsTrigger` renders `role="tab"` with the visible text as the
 * accessible name.
 *
 * IMPORTANT: this component MUST be rendered inside a Radix `<Tabs>`
 * root. App.tsx wraps the whole layout in <Tabs value=... onValueChange=...>.
 */
import { TabsList, TabsTrigger } from "./ui/tabs";
import { useTheme } from "./ThemeProvider";
import { useCommandPalette } from "./CommandPalette";
import {
  Newspaper,
  Lightbulb,
  Network,
  Mail,
  MessageCircle,
  Settings,
  Bookmark,
  Sun,
  Moon,
  Command,
} from "lucide-react";

export interface SidebarNavItem {
  /** Tab id (matches the Radix Tabs `value`). */
  value: string;
  /** Visible text — also the accessible name for `getByRole("tab", { name })`. */
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  /** When true, the tab content is a placeholder; click is allowed but
   * the tab body just shows "Coming soon". M5 will wire this up. */
  placeholder?: boolean;
}

export const SIDEBAR_NAV_ITEMS: SidebarNavItem[] = [
  { value: "feed", label: "News Feed", icon: Newspaper },
  { value: "research", label: "Research", icon: Lightbulb },
  { value: "knowledge", label: "Knowledge", icon: Network },
  { value: "digest", label: "Digest", icon: Mail },
  { value: "chat", label: "Ask AI", icon: MessageCircle },
  { value: "saved", label: "Saved", icon: Bookmark, placeholder: true },
  { value: "preferences", label: "Settings", icon: Settings },
];

interface SidebarProps {
  /** Currently active tab value. Drives the active-state styling. */
  activeTab: string;
  /** Optional click-tap visual hint (e.g. unsaved-changes pill on Settings). */
  badges?: Partial<Record<string, "unsaved" | "warn">>;
}

/**
 * Vertical sidebar nav. The TabsList wraps the per-item TabsTriggers; the
 * theme toggle and Cmd+K hint sit outside the TabsList so they don't get
 * roving-focus selected by the tablist arrow-key handler.
 */
export function Sidebar({ activeTab, badges }: SidebarProps) {
  const { theme, toggleTheme } = useTheme();
  const { open: openPalette } = useCommandPalette();

  return (
    <aside
      data-slot="sidebar"
      aria-label="Primary navigation"
      className="flex flex-col w-56 shrink-0 h-screen sticky top-0 border-r border-border bg-sidebar text-sidebar-foreground"
    >
      {/* Branding header */}
      <div className="px-4 py-4 border-b border-border flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shadow-sm">
          <Newspaper className="w-4 h-4 text-primary-foreground" />
        </div>
        <div className="flex flex-col leading-tight">
          <span className="text-sm font-semibold tracking-tight">TechPulse AI</span>
          <span className="text-[11px] text-muted-foreground">tech-news research</span>
        </div>
      </div>

      {/* Cmd+K affordance — a button that opens the palette */}
      <button
        type="button"
        onClick={() => openPalette()}
        className="mx-3 mt-3 mb-1 flex items-center justify-between gap-2 px-2.5 py-1.5 text-xs text-muted-foreground border border-border rounded-md hover:bg-accent hover:text-accent-foreground transition-colors"
        aria-label="Open command palette"
      >
        <span className="flex items-center gap-1.5">
          <Command className="w-3 h-3" />
          <span>Quick nav</span>
        </span>
        <kbd className="text-[10px] px-1 py-[1px] border border-border rounded bg-muted">
          K
        </kbd>
      </button>

      {/* Nav items — Radix TabsList provides role="tablist", TabsTrigger
          provides role="tab" and aria-selected state. We override the
          default horizontal layout with flex-col + full-width items. */}
      <TabsList
        aria-orientation="vertical"
        className="flex flex-col items-stretch gap-0.5 px-2 py-2 h-auto w-full bg-transparent rounded-none"
      >
        {SIDEBAR_NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.value;
          const badge = badges?.[item.value];
          return (
            <TabsTrigger
              key={item.value}
              value={item.value}
              className={[
                // Reset the horizontal-tab styling from ui/tabs.tsx so the
                // sidebar items lay out as full-width rows.
                "relative justify-start gap-2 h-auto py-1.5 px-2.5 text-[13px] w-full",
                "rounded-md border border-transparent",
                "text-muted-foreground hover:text-foreground hover:bg-accent",
                "transition-colors",
                // Active state: accent-tinted background + accent left border.
                isActive
                  ? "bg-accent text-accent-foreground border-l-2 border-l-primary"
                  : "",
              ].join(" ")}
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span className="flex-1 text-left truncate">{item.label}</span>
              {badge === "unsaved" && (
                <span
                  className="w-1.5 h-1.5 rounded-full bg-yellow-500"
                  aria-label="Unsaved changes"
                />
              )}
              {item.placeholder && (
                <span
                  aria-hidden="true"
                  className="text-[10px] text-muted-foreground/70 tracking-wide uppercase"
                >
                  Soon
                </span>
              )}
            </TabsTrigger>
          );
        })}
      </TabsList>

      <div className="flex-1" />

      {/* Theme toggle — bottom of the sidebar */}
      <div className="px-3 py-3 border-t border-border">
        <button
          type="button"
          onClick={toggleTheme}
          aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
          data-testid="theme-toggle"
          className="w-full flex items-center justify-between gap-2 px-2.5 py-1.5 text-xs text-muted-foreground hover:text-foreground hover:bg-accent rounded-md transition-colors border border-transparent hover:border-border"
        >
          <span className="flex items-center gap-1.5">
            {theme === "dark" ? (
              <Moon className="w-3.5 h-3.5" />
            ) : (
              <Sun className="w-3.5 h-3.5" />
            )}
            <span className="capitalize">{theme} theme</span>
          </span>
          <span className="text-[10px] uppercase tracking-wide">Toggle</span>
        </button>
      </div>
    </aside>
  );
}
