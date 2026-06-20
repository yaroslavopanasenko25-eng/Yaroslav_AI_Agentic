import type { Tab } from '../types';
import { useTranslation } from 'react-i18next';

interface Props {
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
  onSettingsOpen: () => void;
}

const IconDashboard = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="7" height="7" rx="1.5" />
    <rect x="14" y="3" width="7" height="7" rx="1.5" />
    <rect x="3" y="14" width="7" height="7" rx="1.5" />
    <rect x="14" y="14" width="7" height="7" rx="1.5" />
  </svg>
);

const IconAnalysis = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
  </svg>
);

const IconSafety = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);

const IconSettings = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
  </svg>
);

const LogoMark = () => (
  <svg viewBox="0 0 36 36" fill="none">
    <circle cx="18" cy="18" r="17" stroke="rgba(10,132,255,0.6)" strokeWidth="1.5" />
    <path d="M18 8 L26 26 L10 26 Z" fill="none" stroke="#0A84FF" strokeWidth="2" strokeLinejoin="round" />
    <circle cx="18" cy="22" r="1.5" fill="#0A84FF" />
    <line x1="18" y1="14" x2="18" y2="20" stroke="#0A84FF" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

const NAV_ITEMS: { id: Tab; label: string; Icon: () => JSX.Element }[] = [
  { id: 'dashboard', label: 'dashboard', Icon: IconDashboard },
  { id: 'analysis',  label: 'analysis',  Icon: IconAnalysis  },
  { id: 'safety',    label: 'safety',    Icon: IconSafety    },
];

export default function Sidebar({ activeTab, onTabChange, onSettingsOpen }: Props) {
  const { t } = useTranslation();

  return (
    <nav className="sidebar">
      <div className="sidebar-top">
        <div className="logo-mark">
          <LogoMark />
        </div>
        {NAV_ITEMS.map(({ id, label, Icon }) => (
          <button
            key={id}
            className={`nav-btn${activeTab === id ? ' active' : ''}`}
            onClick={() => onTabChange(id)}
            title={t(label)}
            aria-label={t(label)}
          >
            <Icon />
          </button>
        ))}
      </div>
      <div className="sidebar-bottom">
        <button
          className="nav-btn"
          onClick={onSettingsOpen}
          title={t('settings')}
          aria-label={t('settings')}
        >
          <IconSettings />
        </button>
      </div>
    </nav>
  );
}
