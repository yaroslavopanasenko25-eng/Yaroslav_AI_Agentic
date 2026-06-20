"use client";

import { createContext, useContext, useEffect, useState } from "react";

type FontSize = "small" | "medium" | "large";

interface SettingsContextProps {
  fontSize: FontSize;
  setFontSize: (size: FontSize) => void;
  language: string;
  setLanguage: (lang: string) => void;
  dyslexiaMode: boolean;
  setDyslexiaMode: (mode: boolean) => void;
  theme: string;
  setTheme: (theme: string) => void;
}

const SettingsContext = createContext<SettingsContextProps | undefined>(undefined);

export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const [fontSize, setFontSize] = useState<FontSize>("medium");
  const [language, setLanguage] = useState("en");
  const [dyslexiaMode, setDyslexiaMode] = useState(false);
  const [theme, setTheme] = useState("dark");

  useEffect(() => {
    const root = document.documentElement;
    // Set theme
    if (theme === "dark") {
      root.classList.add("dark");
      root.classList.remove("light");
    } else {
      root.classList.add("light");
      root.classList.remove("dark");
    }

    // Set font base class
    root.classList.remove("text-sm", "text-base", "text-lg", "font-dyslexic", "tracking-widest");
    
    if (fontSize === "small") root.classList.add("text-sm");
    else if (fontSize === "large") root.classList.add("text-lg");
    else root.classList.add("text-base");

    if (dyslexiaMode) {
      root.classList.add("tracking-widest", "font-dyslexic");
    }
  }, [fontSize, theme, dyslexiaMode]);

  return (
    <SettingsContext.Provider
      value={{ fontSize, setFontSize, language, setLanguage, dyslexiaMode, setDyslexiaMode, theme, setTheme }}
    >
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings() {
  const context = useContext(SettingsContext);
  if (!context) throw new Error("useSettings must be used within a SettingsProvider");
  return context;
}
