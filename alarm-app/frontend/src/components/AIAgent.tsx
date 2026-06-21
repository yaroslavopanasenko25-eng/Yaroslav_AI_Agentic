import { useState, useRef, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useAppSettings } from '../App';

interface Message {
  id: string;
  role: 'user' | 'bot';
  text: string;
}

interface DispatchBrief {
  priority: 'critical' | 'high' | 'watch' | 'normal';
  priority_label: string;
  region_name: string;
  status_label: string;
  risk?: { next_6h_probability?: number; risk_level?: string };
}

const QUICK_UK = [
  { key: 'now', text: 'Що робити зараз?' },
  { key: 'shelter', text: 'Найближче укриття' },
  { key: 'predict', text: 'Коли можлива тривога?' },
  { key: '112', text: 'Екстрені номери' },
] as const;

const QUICK_EN = [
  { key: 'now', text: 'What to do now?' },
  { key: 'shelter', text: 'Nearest shelter' },
  { key: 'predict', text: 'When might alarm occur?' },
  { key: '112', text: 'Emergency numbers' },
] as const;

const PRIORITY_CLASS: Record<string, string> = {
  critical: 'dispatch-critical',
  high: 'dispatch-high',
  watch: 'dispatch-watch',
  normal: 'dispatch-normal',
};

const GrokIcon = () => (
  <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="16" cy="16" r="9" stroke="white" strokeWidth="2.2" fill="none" opacity="0.95" />
    <path
      d="M19.5 9.5 L14.5 16 L17 16 L12.5 22.5"
      stroke="white"
      strokeWidth="2.2"
      strokeLinecap="round"
      strokeLinejoin="round"
      fill="none"
    />
  </svg>
);

const SendIcon = () => (
  <svg viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M10 16V6M10 6L6 10M10 6L14 10" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const CloseIcon = () => (
  <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <line x1="15" y1="5" x2="5" y2="15"/><line x1="5" y1="5" x2="15" y2="15"/>
  </svg>
);

export default function AIAgent() {
  const { t } = useTranslation();
  const { language, selectedRegionId } = useAppSettings();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [dispatch, setDispatch] = useState<DispatchBrief | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const quickActions = language === 'uk' ? QUICK_UK : QUICK_EN;

  const loadDispatch = useCallback(() => {
    const params = new URLSearchParams({
      region_id: selectedRegionId,
      language,
    });
    if (userLocation) {
      params.set('lat', String(userLocation.lat));
      params.set('lng', String(userLocation.lng));
    }
    fetch(`/api/v1/ai/dispatch?${params}`, { cache: 'no-store' })
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data?.priority) setDispatch(data); })
      .catch(() => setDispatch(null));
  }, [selectedRegionId, language, userLocation]);

  useEffect(() => {
    if (!open || userLocation) return;
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      pos => setUserLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => {},
      { timeout: 6000, maximumAge: 120_000 },
    );
  }, [open, userLocation]);

  useEffect(() => {
    if (open) loadDispatch();
  }, [open, loadDispatch]);

  useEffect(() => {
    if (open && messages.length === 0) {
      const welcome = language === 'uk'
        ? 'Привіт! Я диспетчер GuardianEye — допоможу з тривогами, укриттями, прогнозом і екстреними діями. Оберіть швидку дію або напишіть питання.'
        : 'Hello! I\'m the GuardianEye dispatcher — alarms, shelters, forecasts, and emergency guidance. Pick a quick action or type your question.';
      setMessages([{ id: 'w', role: 'bot', text: welcome }]);
    }
  }, [open, language, messages.length]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typing]);

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 100);
  }, [open]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || typing) return;
    setInput('');
    const userMsg: Message = { id: Date.now().toString(), role: 'user', text: text.trim() };
    setMessages(prev => [...prev, userMsg]);
    setTyping(true);

    const history = messages
      .filter(m => m.id !== 'w')
      .slice(-10)
      .map(m => ({
        role: m.role === 'user' ? 'user' : 'assistant',
        content: m.text,
      }));

    try {
      const res = await fetch('/api/v1/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text.trim(),
          history,
          language,
          region_id: selectedRegionId,
          ...(userLocation ? { lat: userLocation.lat, lng: userLocation.lng } : {}),
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        const detail = typeof err.detail === 'string' ? err.detail : 'Grok API unavailable';
        throw new Error(detail);
      }

      const data = await res.json();
      if (data.dispatch?.priority) setDispatch(data.dispatch);
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'bot', text: data.reply }]);
    } catch (err) {
      const offline = language === 'uk'
        ? 'Не вдалося зʼєднатися з бекендом. Переконайтеся, що Python-сервер запущено.'
        : 'Could not reach backend. Make sure the Python server is running.';
      const msg = err instanceof Error && err.message !== 'Failed to fetch' ? err.message : offline;
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'bot', text: msg }]);
    } finally {
      setTyping(false);
    }
  };

  const send = () => sendMessage(input);

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  };

  return (
    <>
      {open && (
        <div className="ai-window glass-card">
          <div className="ai-header">
            <div className="ai-header-title">
              <div className="ai-avatar-sm">
                <GrokIcon />
              </div>
              <div>
                <div className="ai-name">{t('aiAssistant')}</div>
                <div className="ai-status">
                  {dispatch ? (
                    <span className={`dispatch-badge ${PRIORITY_CLASS[dispatch.priority] || ''}`}>
                      {dispatch.priority_label}
                      {dispatch.risk?.next_6h_probability != null && (
                        <span style={{ marginLeft: 6, opacity: 0.85 }}>
                          · {dispatch.risk.next_6h_probability}%
                        </span>
                      )}
                    </span>
                  ) : (
                    'Online'
                  )}
                </div>
              </div>
            </div>
            <button className="ai-close-btn" onClick={() => setOpen(false)} aria-label={t('close')}>
              <CloseIcon />
            </button>
          </div>

          {dispatch && (
            <div className="ai-dispatch-bar">
              <span>{dispatch.region_name}</span>
              <span>·</span>
              <span>{dispatch.status_label}</span>
            </div>
          )}

          <div className="ai-quick-actions">
            {quickActions.map(q => (
              <button
                key={q.key}
                type="button"
                className="ai-quick-btn"
                disabled={typing}
                onClick={() => sendMessage(q.text)}
              >
                {q.text}
              </button>
            ))}
          </div>

          <div className="ai-messages">
            {messages.map(msg => (
              <div key={msg.id} className={`ai-msg ${msg.role}`}>{msg.text}</div>
            ))}
            {typing && (
              <div className="ai-msg bot typing">
                <span className="typing-dot"/><span className="typing-dot"/><span className="typing-dot"/>
              </div>
            )}
            <div ref={endRef} />
          </div>

          <div className="ai-input-row">
            <textarea
              ref={inputRef}
              className="ai-input"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder={t('typeMessage')}
              rows={1}
            />
            <button
              className={`ai-send-btn${input.trim() && !typing ? ' ready' : ''}`}
              onClick={send}
              disabled={!input.trim() || typing}
              aria-label={t('send')}
            >
              <SendIcon />
            </button>
          </div>
        </div>
      )}

      <button
        className={`ai-fab${open ? ' open' : ''}`}
        onClick={() => setOpen(p => !p)}
        aria-label={t('aiAssistant')}
      >
        <div className="ai-fab-inner">
          <GrokIcon />
        </div>
      </button>
    </>
  );
}
