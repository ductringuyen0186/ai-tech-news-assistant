/**
 * Settings — M3.M4
 *
 * Hosts the Settings tab (the "preferences" Radix tab value, labeled
 * "Settings" in the sidebar). Renders:
 *   1. Appearance: theme toggle (dark / light) backed by useTheme().
 *      Selecting a value writes localStorage and flips <html class="dark">.
 *   2. Appearance: density toggle (compact / comfortable) — UI only.
 *      Writes localStorage.techpulse-density. A helper line under the
 *      group explicitly says behavior is deferred so the user knows
 *      saving it doesn't change layout yet.
 *   3. Topic preferences card — the existing TopicFilter (reformatted to
 *      use the dense layout / design tokens implicitly via the wrapping
 *      cards). Kept as a thin pass-through so the existing settings tests
 *      (`getByText(/Topic Preferences/i)`, `Save Preferences` etc.) keep
 *      working without changes.
 *
 * The dense styling here mirrors NewsFeed / Digest from M3.M3: ≤14px body
 * text, ≤12px card padding, tokens for surface colors.
 */
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { RadioGroup, RadioGroupItem } from "./ui/radio-group";
import { Label } from "./ui/label";
import { Settings as SettingsIcon, Palette, LayoutGrid } from "lucide-react";
import { useTheme, Theme } from "./ThemeProvider";
import { TopicFilter } from "./TopicFilter";

export const DENSITY_STORAGE_KEY = "techpulse-density";
type Density = "compact" | "comfortable";

function readStoredDensity(): Density {
  try {
    const v = localStorage.getItem(DENSITY_STORAGE_KEY);
    if (v === "compact" || v === "comfortable") return v;
  } catch {
    // privacy mode etc.
  }
  return "comfortable";
}

interface SettingsProps {
  selectedCategories: string[];
  onCategoriesChange: (categories: string[]) => void;
  onSave: () => void;
  isSaving?: boolean;
  hasUnsavedChanges?: boolean;
}

export function Settings({
  selectedCategories,
  onCategoriesChange,
  onSave,
  isSaving = false,
  hasUnsavedChanges = false,
}: SettingsProps) {
  const { theme, setTheme } = useTheme();
  const [density, setDensityState] = useState<Density>(() => readStoredDensity());

  const handleThemeChange = (next: string) => {
    if (next === "dark" || next === "light") {
      setTheme(next as Theme);
    }
  };

  const handleDensityChange = (next: string) => {
    if (next === "compact" || next === "comfortable") {
      setDensityState(next);
      try {
        localStorage.setItem(DENSITY_STORAGE_KEY, next);
      } catch {
        // Best-effort.
      }
    }
  };

  return (
    <div className="space-y-6" data-testid="settings-root">
      {/* Page header — dense, matches NewsFeed/Digest cadence. */}
      <div className="flex items-center gap-2">
        <SettingsIcon className="w-5 h-5 text-muted-foreground" />
        <h2 className="text-xl font-semibold tracking-tight text-foreground">Settings</h2>
      </div>

      {/* Appearance card — theme + density radio groups. */}
      <Card className="bg-card border border-border">
        <CardHeader className="pb-4 px-5 pt-5">
          <CardTitle className="flex items-center gap-2 text-base font-semibold text-foreground">
            <Palette className="w-4 h-4 text-muted-foreground" />
            Appearance
          </CardTitle>
          <CardDescription className="text-xs">
            Visual preferences. Theme persists across reloads; density is
            saved but does not yet change layout.
          </CardDescription>
        </CardHeader>
        <CardContent className="px-5 pb-5 space-y-5">
          {/* Theme — radio group bound to useTheme(). */}
          <div className="space-y-2" data-testid="settings-theme">
            <Label className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Theme
            </Label>
            <RadioGroup
              value={theme}
              onValueChange={handleThemeChange}
              className="grid grid-cols-2 gap-3"
            >
              <Label
                htmlFor="theme-dark"
                data-active={theme === "dark"}
                className={`flex items-center gap-2 rounded-md border p-3 cursor-pointer transition-colors text-sm ${
                  theme === "dark"
                    ? "border-primary bg-primary/10 text-foreground"
                    : "border-border bg-card text-muted-foreground hover:bg-accent hover:text-foreground"
                }`}
              >
                <RadioGroupItem
                  value="dark"
                  id="theme-dark"
                  data-testid="settings-theme-dark"
                />
                <span>Dark</span>
              </Label>
              <Label
                htmlFor="theme-light"
                data-active={theme === "light"}
                className={`flex items-center gap-2 rounded-md border p-3 cursor-pointer transition-colors text-sm ${
                  theme === "light"
                    ? "border-primary bg-primary/10 text-foreground"
                    : "border-border bg-card text-muted-foreground hover:bg-accent hover:text-foreground"
                }`}
              >
                <RadioGroupItem
                  value="light"
                  id="theme-light"
                  data-testid="settings-theme-light"
                />
                <span>Light</span>
              </Label>
            </RadioGroup>
          </div>

          {/* Density — UI only for v1. */}
          <div className="space-y-2" data-testid="settings-density">
            <Label className="text-xs font-medium uppercase tracking-wide text-muted-foreground flex items-center gap-1.5">
              <LayoutGrid className="w-3 h-3" />
              Density
            </Label>
            <RadioGroup
              value={density}
              onValueChange={handleDensityChange}
              className="grid grid-cols-2 gap-3"
            >
              <Label
                htmlFor="density-compact"
                data-active={density === "compact"}
                className={`flex items-center gap-2 rounded-md border p-3 cursor-pointer transition-colors text-sm ${
                  density === "compact"
                    ? "border-primary bg-primary/10 text-foreground"
                    : "border-border bg-card text-muted-foreground hover:bg-accent hover:text-foreground"
                }`}
              >
                <RadioGroupItem
                  value="compact"
                  id="density-compact"
                  data-testid="settings-density-compact"
                />
                <span>Compact</span>
              </Label>
              <Label
                htmlFor="density-comfortable"
                data-active={density === "comfortable"}
                className={`flex items-center gap-2 rounded-md border p-3 cursor-pointer transition-colors text-sm ${
                  density === "comfortable"
                    ? "border-primary bg-primary/10 text-foreground"
                    : "border-border bg-card text-muted-foreground hover:bg-accent hover:text-foreground"
                }`}
              >
                <RadioGroupItem
                  value="comfortable"
                  id="density-comfortable"
                  data-testid="settings-density-comfortable"
                />
                <span>Comfortable</span>
              </Label>
            </RadioGroup>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Density behavior coming in a future release. Your preference
              is saved.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Topic preferences — keeps the existing TopicFilter contract so the
          settings.spec.ts tests' `getByText(/Topic Preferences/i)`,
          `Save Preferences`, and the per-category checkbox locators all
          keep matching. We just wrap it with the new dense surface. */}
      <TopicFilter
        selectedCategories={selectedCategories}
        onCategoriesChange={onCategoriesChange}
        onSave={onSave}
        isSaving={isSaving}
        hasUnsavedChanges={hasUnsavedChanges}
      />
    </div>
  );
}

export default Settings;
