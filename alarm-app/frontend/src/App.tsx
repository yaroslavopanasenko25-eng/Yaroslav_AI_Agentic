import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import type { Theme, Language, Tab, AppSettings } from './types';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import Analysis from './components/Analysis';
import Safety from './components/Safety';
import Settings from './components/Settings';
import AIAgent from './components/AIAgent';

export const SettingsContext = createContext<AppSettings>({
  theme: 'dark',
  language: 'uk',
  dyslexiaMode: false,
  setTheme: () => {},
  setLanguage: () => {},
  setDyslexiaMode: () => {},
});

export const useAppSettings = () => useContext(SettingsContext);

function App() {
  const { i18n } = useTranslation();
  const [tab, setTab] = useState<Tab>('dashboard');
  const [settingsOpen, setSettingsOpen] = useState(false);

  const [theme, setThemeState] = useState<Theme>(
    () => (localStorage.getItem('theme') as Theme) || 'dark',
  );
  const [language, setLanguageState] = useState<Language>(
    () => (localStorage.getItem('language') as Language) || 'uk',
  );
  const [dyslexiaMode, setDyslexiaModeState] = useState<boolean>(
    () => localStorage.getItem('dyslexia') === 'true',
  );

  const setTheme = useCallback((t: Theme) => {
    setThemeState(t);
    localStorage.setItem('theme', t);
  }, []);

  const setLanguage = useCallback((l: Language) => {
    setLanguageState(l);
    localStorage.setItem('language', l);
    i18n.changeLanguage(l);
  }, [i18n]);

  const setDyslexiaMode = useCallback((v: boolean) => {
    setDyslexiaModeState(v);
    localStorage.setItem('dyslexia', String(v));
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    root.setAttribute('data-theme', theme);
    root.setAttribute('data-dyslexia', String(dyslexiaMode));
  }, [theme, dyslexiaMode]);

  // Close settings on Escape key
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setSettingsOpen(false);
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, []);

  return (
    <SettingsContext.Provider value={{ theme, language, dyslexiaMode, setTheme, setLanguage, setDyslexiaMode }}>
      <div className="app-shell" data-theme={theme} data-dyslexia={dyslexiaMode}>
        <Sidebar activeTab={tab} onTabChange={setTab} onSettingsOpen={() => setSettingsOpen(true)} />
        <main className="content-area">
          {tab === 'dashboard' && <Dashboard />}
          {tab === 'analysis' && <Analysis />}
          {tab === 'safety'   && <Safety />}
        </main>
        <AIAgent />

        {/* Settings bottom sheet */}
        <div
          className={`settings-backdrop${settingsOpen ? ' open' : ''}`}
          onClick={() => setSettingsOpen(false)}
          aria-hidden="true"
        />
        <div
          className={`settings-sheet${settingsOpen ? ' open' : ''}`}
          role="dialog"
          aria-modal="true"
          aria-label="Settings"
        >
          <div className="settings-handle" />
          <Settings onClose={() => setSettingsOpen(false)} />
        </div>
      </div>
    </SettingsContext.Provider>
  );
}

export default App;
