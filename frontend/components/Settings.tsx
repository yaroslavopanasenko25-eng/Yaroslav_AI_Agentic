"use client";

/**
 * Operator settings panel for UI preferences.
 * Supports dark/light preference toggling and English/Ukrainian language selection.
 */
import { useState } from "react";

type ThemeMode = "dark" | "light";
type LanguageCode = "en" | "uk";

export default function Settings(): JSX.Element {
  const [theme, setTheme] = useState<ThemeMode>("dark");
  const [language, setLanguage] = useState<LanguageCode>("en");
  const [errorMessage, setErrorMessage] = useState<string>("");

  const handleThemeChange = (nextTheme: ThemeMode): void => {
    try {
      setTheme(nextTheme);
      setErrorMessage("");
    } catch (error) {
      console.error("Theme update failed", error);
      setErrorMessage("Unable to update theme right now.");
    }
  };

  const handleLanguageChange = (nextLanguage: LanguageCode): void => {
    try {
      setLanguage(nextLanguage);
      setErrorMessage("");
    } catch (error) {
      console.error("Language update failed", error);
      setErrorMessage("Unable to update language right now.");
    }
  };

  try {
    return (
      <aside className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-md shadow-black/30">
        <h2 className="text-xl font-semibold text-slate-100">Settings</h2>
        <p className="mt-3 text-sm text-slate-300">
          Configure dashboard preferences for analysts and operators.
        </p>

        <div className="mt-6 space-y-5">
          <div>
            <label htmlFor="theme" className="mb-2 block text-sm font-medium text-slate-200">
              Theme
            </label>
            <select
              id="theme"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
              value={theme}
              onChange={(event) => handleThemeChange(event.target.value as ThemeMode)}
            >
              <option value="dark">Dark</option>
              <option value="light">Light</option>
            </select>
          </div>

          <div>
            <label htmlFor="language" className="mb-2 block text-sm font-medium text-slate-200">
              Language
            </label>
            <select
              id="language"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
              value={language}
              onChange={(event) => handleLanguageChange(event.target.value as LanguageCode)}
            >
              <option value="en">English</option>
              <option value="uk">Українська</option>
            </select>
          </div>

          {errorMessage ? <p className="text-sm text-rose-400">{errorMessage}</p> : null}
        </div>
      </aside>
    );
  } catch (error) {
    console.error("Settings panel rendering failed", error);
    return (
      <aside className="rounded-2xl border border-rose-700/50 bg-rose-900/20 p-6 text-rose-200">
        Settings panel is temporarily unavailable.
      </aside>
    );
  }
}
