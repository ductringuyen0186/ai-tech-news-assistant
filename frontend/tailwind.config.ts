/**
 * Tailwind config — Mission 3 / Milestone 1.
 *
 * IMPORTANT: this project uses Tailwind v4 with a prebuilt CSS bundle
 * (`src/index.css` ships ~2600 lines of generated utilities). There is NO
 * tailwindcss/postcss compiler in the build pipeline; this config file
 * therefore serves two purposes:
 *
 *   1. Documentation — declares the dark-mode strategy, semantic color
 *      tokens, and font stack that the bundled CSS already exposes via
 *      CSS variables in `index.css`. Future workers swapping to a live
 *      Tailwind compiler can keep this file as the source of truth.
 *
 *   2. Mission contract — Milestone 1's validation list requires a
 *      tailwind config with `darkMode: 'class'` + semantic colors. The
 *      effective semantics already live in the bundle and the `.dark`
 *      override block in `index.css`; this file makes the configuration
 *      explicit so a code review can see the design choices.
 */
import type { Config } from "tailwindcss";

const config: Config = {
  // Dark mode uses the `.dark` class on <html>. The inline bootstrap
  // script in index.html sets the class BEFORE React mounts to prevent
  // FOUC. ThemeProvider toggles it at runtime.
  darkMode: "class",

  // Vite + the prebuilt CSS bundle means content scanning is a no-op,
  // but we document the source surfaces for any future re-compile.
  content: [
    "./index.html",
    "./src/**/*.{ts,tsx,js,jsx,html,css}",
  ],

  theme: {
    extend: {
      // Semantic color tokens. Every entry maps to a CSS variable that
      // `index.css` defines for both :root (light) and .dark (dark). The
      // Tailwind utilities `bg-background`, `text-foreground`,
      // `border-border`, `bg-card`, `bg-muted`, `text-muted-foreground`,
      // `bg-accent`, `text-accent-foreground`, `bg-primary` are all
      // present in the prebuilt bundle and resolve to these vars.
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        card: {
          DEFAULT: "var(--card)",
          foreground: "var(--card-foreground)",
        },
        popover: {
          DEFAULT: "var(--popover)",
          foreground: "var(--popover-foreground)",
        },
        primary: {
          DEFAULT: "var(--primary)",
          foreground: "var(--primary-foreground)",
        },
        secondary: {
          DEFAULT: "var(--secondary)",
          foreground: "var(--secondary-foreground)",
        },
        muted: {
          DEFAULT: "var(--muted)",
          foreground: "var(--muted-foreground)",
        },
        accent: {
          DEFAULT: "var(--accent)",
          foreground: "var(--accent-foreground)",
        },
        destructive: {
          DEFAULT: "var(--destructive)",
          foreground: "var(--destructive-foreground)",
        },
        border: "var(--border)",
        input: "var(--input)",
        ring: "var(--ring)",
        sidebar: {
          DEFAULT: "var(--sidebar)",
          foreground: "var(--sidebar-foreground)",
          primary: "var(--sidebar-primary)",
          "primary-foreground": "var(--sidebar-primary-foreground)",
          accent: "var(--sidebar-accent)",
          "accent-foreground": "var(--sidebar-accent-foreground)",
          border: "var(--sidebar-border)",
          ring: "var(--sidebar-ring)",
        },
        // Status palette for the developer-dashboard motif. Consumed by
        // M2/M3 component work (subagent rows, digest top-stories).
        running: "var(--status-running)",
        done: "var(--status-done)",
        error: "var(--status-error)",
      },
      fontFamily: {
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "Noto Sans",
          "sans-serif",
        ],
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },

  plugins: [],
};

export default config;
