import { useTranslation } from 'react-i18next';
import { useAppSettings } from '../App';

interface Props {
  onClose: () => void;
}

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="ios-toggle">
      <input type="checkbox" checked={checked} onChange={e => onChange(e.target.checked)} />
      <span className="ios-toggle-track" />
      <span className="ios-toggle-thumb" />
    </label>
  );
}

export default function Settings({ onClose }: Props) {
  const { t } = useTranslation();
  const { theme, language, dyslexiaMode, setTheme, setLanguage, setDyslexiaMode } = useAppSettings();

  return (
    <div className="settings-sheet-content">
      {/* Title row */}
      <div className="settings-sheet-header">
        <span className="settings-sheet-title">{t('settings')}</span>
        <button className="settings-close-btn" onClick={onClose} aria-label={t('close')}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" width="16" height="16">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>

      <div className="settings-sheet-body">
        {/* Appearance */}
        <div className="settings-group-label">{language === 'uk' ? 'ОФОРМЛЕННЯ' : 'APPEARANCE'}</div>
        <div className="glass-card settings-group">
          <div className="settings-row">
            <div>
              <div className="settings-row-label">{language === 'uk' ? 'Тема' : 'Theme'}</div>
              <div className="settings-row-desc">{language === 'uk' ? 'Темна або світла' : 'Dark or light'}</div>
            </div>
            <div className="theme-selector">
              <button className={`theme-btn dark-btn${theme === 'dark' ? ' active' : ''}`} onClick={() => setTheme('dark')} aria-label={t('darkTheme')}>🌙</button>
              <button className={`theme-btn light-btn${theme === 'light' ? ' active' : ''}`} onClick={() => setTheme('light')} aria-label={t('lightTheme')}>☀️</button>
            </div>
          </div>
        </div>

        {/* Language */}
        <div className="settings-group-label">{language === 'uk' ? 'МОВА' : 'LANGUAGE'}</div>
        <div className="glass-card settings-group">
          <div className="settings-row">
            <div>
              <div className="settings-row-label">{t('language')}</div>
              <div className="settings-row-desc">{language === 'uk' ? 'Мова інтерфейсу' : 'Interface language'}</div>
            </div>
            <div className="lang-selector">
              <button className={`lang-btn${language === 'uk' ? ' active' : ''}`} onClick={() => setLanguage('uk')}>🇺🇦 UA</button>
              <button className={`lang-btn${language === 'en' ? ' active' : ''}`} onClick={() => setLanguage('en')}>🇬🇧 EN</button>
            </div>
          </div>
        </div>

        {/* Accessibility */}
        <div className="settings-group-label">{language === 'uk' ? 'ДОСТУПНІСТЬ' : 'ACCESSIBILITY'}</div>
        <div className="glass-card settings-group">
          <div className="settings-row">
            <div>
              <div className="settings-row-label">{t('dyslexiaMode')}</div>
              <div className="settings-row-desc">{language === 'uk' ? 'Шрифт OpenDyslexic' : 'OpenDyslexic font'}</div>
            </div>
            <Toggle checked={dyslexiaMode} onChange={setDyslexiaMode} />
          </div>
        </div>

        {/* About */}
        <div className="settings-group-label">{language === 'uk' ? 'ПРО ЗАСТОСУНОК' : 'ABOUT'}</div>
        <div className="glass-card settings-group">
          <div className="settings-row" style={{ cursor: 'default' }}>
            <div>
              <div className="settings-row-label">Ukraine Alarm Shield</div>
              <div className="settings-row-desc">v1.0.0 · mock / ukrainealarm.com</div>
            </div>
          </div>
          <div className="settings-row" style={{ cursor: 'default', borderBottom: 'none' }}>
            <div>
              <div className="settings-row-label" style={{ fontSize: 13 }}>{language === 'uk' ? 'Екстрені номери' : 'Emergency numbers'}</div>
              <div className="settings-row-desc" style={{ marginTop: 4, lineHeight: 1.8 }}>
                101 — {language === 'uk' ? 'пожежна' : 'fire'} &nbsp;·&nbsp;
                102 — {language === 'uk' ? 'поліція' : 'police'} &nbsp;·&nbsp;
                103 — {language === 'uk' ? 'швидка' : 'ambulance'} &nbsp;·&nbsp;
                <strong>112</strong> — {language === 'uk' ? 'єдина екстрена' : 'emergency'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
