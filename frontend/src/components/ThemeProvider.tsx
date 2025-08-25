"use client";

import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

export type Theme = "light" | "dark" | "system";

interface ThemeContextValue {
  theme: Theme;
  setTheme: (t: Theme) => void;
  resolvedTheme: "light" | "dark";
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

function getSystemTheme(): "light" | "dark" {
  if (typeof window === "undefined") return "light";
  return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState<Theme>("system");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const saved = localStorage.getItem("theme") as Theme | null;
    if (saved) setTheme(saved);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    localStorage.setItem("theme", theme);

    const root = document.documentElement;
    const apply = (mode: "light" | "dark") => {
      if (mode === "dark") root.classList.add("dark");
      else root.classList.remove("dark");
    };

    if (theme === "system") {
      const sys = getSystemTheme();
      apply(sys);
      const mql = window.matchMedia("(prefers-color-scheme: dark)");
      const handler = () => apply(getSystemTheme());
      mql.addEventListener?.("change", handler);
      return () => mql.removeEventListener?.("change", handler);
    } else {
      apply(theme);
    }
  }, [theme, mounted]);

  const value = useMemo<ThemeContextValue>(() => ({
    theme,
    setTheme,
    resolvedTheme: theme === "system" ? getSystemTheme() : theme,
  }), [theme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}
