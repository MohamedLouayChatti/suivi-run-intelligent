"use client"

import { useCallback, useEffect, useState } from "react"

type Theme = "light" | "dark" | "system"

const STORAGE_KEY = "suivi-run:theme"

function resolveIsDark(theme: Theme): boolean {
  if (theme === "system") {
    return window.matchMedia("(prefers-color-scheme: dark)").matches
  }
  return theme === "dark"
}

function applyTheme(theme: Theme) {
  document.documentElement.classList.toggle("dark", resolveIsDark(theme))
}

// No backend/session persistence yet — the preference only lives in localStorage.
// Called once from `AppProviders` so the `.dark` class is applied on every page load,
// and again from the Appearance settings tab to read/change the current value.
function useTheme() {
  const [theme, setThemeState] = useState<Theme>("system")

  useEffect(() => {
    const stored = (localStorage.getItem(STORAGE_KEY) as Theme | null) ?? "system"
    // localStorage isn't available during SSR, so the stored preference can only be read post-mount.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setThemeState(stored)
    applyTheme(stored)

    if (stored !== "system") return
    const media = window.matchMedia("(prefers-color-scheme: dark)")
    const onChange = () => applyTheme("system")
    media.addEventListener("change", onChange)
    return () => media.removeEventListener("change", onChange)
  }, [])

  const setTheme = useCallback((next: Theme) => {
    localStorage.setItem(STORAGE_KEY, next)
    setThemeState(next)
    applyTheme(next)
  }, [])

  return { theme, setTheme }
}

export { useTheme }
export type { Theme }
