"use client";

import { useSettings } from "./SettingsProvider";
import { Moon, Sun, MonitorSmartphone, Type, Globe, Accessibility } from "lucide-react";

export default function Settings(): JSX.Element {
  const { 
    theme, setTheme, 
    fontSize, setFontSize, 
    language, setLanguage, 
    dyslexiaMode, setDyslexiaMode 
  } = useSettings();

  const isUk = language === "uk";

  return (
    <aside className="rounded-[2rem] border border-white/20 dark:border-white/10 bg-white/40 dark:bg-slate-900/40 p-6 shadow-[0_8px_32px_rgba(0,0,0,0.12)] backdrop-blur-2xl h-full space-y-8 animate-in fade-in slide-in-from-right-4 duration-700">
      <div className="flex items-center gap-3">
        <MonitorSmartphone className="h-6 w-6 text-indigo-500 dark:text-emerald-400" />
        <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100">
          {isUk ? "Налаштування" : "Settings"}
        </h2>
      </div>

      <div className="space-y-6">
        {/* Theme Toggle - iOS Control Center Style */}
        <div className="space-y-3">
          <label className="block text-sm font-semibold text-slate-600 dark:text-slate-300">
            {isUk ? "Тема оформлення" : "Appearance"}
          </label>
          <div className="flex p-1 rounded-2xl bg-slate-200/50 dark:bg-slate-800/50 backdrop-blur-md">
            <button
              onClick={() => setTheme("light")}
              className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-xl text-sm font-medium transition-all duration-300 ${
                theme === "light" 
                  ? "bg-white text-indigo-600 shadow-md" 
                  : "text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
              }`}
            >
              <Sun className="h-4 w-4" /> Light
            </button>
            <button
              onClick={() => setTheme("dark")}
              className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-xl text-sm font-medium transition-all duration-300 ${
                theme === "dark" 
                  ? "bg-slate-700 text-emerald-400 shadow-md" 
                  : "text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
              }`}
            >
              <Moon className="h-4 w-4" /> Dark
            </button>
          </div>
        </div>

        {/* Language Selection */}
        <div className="space-y-3">
          <label className="block text-sm font-semibold text-slate-600 dark:text-slate-300">
            <div className="flex items-center gap-2"><Globe className="h-4 w-4"/> {isUk ? "Мова" : "Language"}</div>
          </label>
          <div className="flex p-1 rounded-2xl bg-slate-200/50 dark:bg-slate-800/50 backdrop-blur-md">
            <button
              onClick={() => setLanguage("en")}
              className={`flex-1 py-2 rounded-xl text-sm font-medium transition-all duration-300 ${
                language === "en" ? "bg-white dark:bg-slate-700 text-indigo-600 dark:text-emerald-400 shadow-md" : "text-slate-500"
              }`}
            >
              English
            </button>
            <button
              onClick={() => setLanguage("uk")}
              className={`flex-1 py-2 rounded-xl text-sm font-medium transition-all duration-300 ${
                language === "uk" ? "bg-white dark:bg-slate-700 text-indigo-600 dark:text-emerald-400 shadow-md" : "text-slate-500"
              }`}
            >
              Українська
            </button>
          </div>
        </div>

        {/* Typography Controls */}
        <div className="space-y-3">
          <label className="block text-sm font-semibold text-slate-600 dark:text-slate-300">
            <div className="flex items-center gap-2"><Type className="h-4 w-4"/> {isUk ? "Розмір тексту" : "Typography Base"}</div>
          </label>
          <div className="flex gap-2">
            {["small", "medium", "large"].map((s) => (
              <button
                key={s}
                onClick={() => setFontSize(s as any)}
                className={`flex-1 py-3 rounded-2xl border transition-all duration-300 capitalize text-sm font-medium ${
                  fontSize === s 
                    ? "border-indigo-500 dark:border-emerald-500 bg-indigo-50 dark:bg-emerald-900/20 text-indigo-700 dark:text-emerald-400" 
                    : "border-slate-200 dark:border-slate-700/50 hover:border-slate-300 dark:hover:border-slate-600 text-slate-600 dark:text-slate-400"
                }`}
              >
                {s === "small" ? "A" : s === "medium" ? "Text" : "Large"}
              </button>
            ))}
          </div>
        </div>

        {/* Accessibility Mode Segment */}
        <div className="pt-4 border-t border-slate-200 dark:border-slate-800">
          <div className="flex items-center justify-between p-4 rounded-2xl bg-white/50 dark:bg-slate-800/30 backdrop-blur-sm border border-slate-100 dark:border-slate-700/50">
            <div>
              <p className="flex items-center gap-2 text-sm font-bold text-slate-800 dark:text-slate-200">
                <Accessibility className="h-4 w-4 text-indigo-500 dark:text-emerald-400" />
                {isUk ? "Режим Дислексії" : "Dyslexia Reader"}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                {isUk ? "Збільшений інтервал" : "Wider tracking & sans fonts"}
              </p>
            </div>
            <button
              onClick={() => setDyslexiaMode(!dyslexiaMode)}
              className={`relative inline-flex h-7 w-12 items-center rounded-full transition-all duration-500 shadow-inner ${
                dyslexiaMode ? "bg-indigo-500 dark:bg-emerald-500" : "bg-slate-300 dark:bg-slate-700"
              }`}
            >
              <span
                className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-sm transition-transform duration-500 ${
                  dyslexiaMode ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
}
