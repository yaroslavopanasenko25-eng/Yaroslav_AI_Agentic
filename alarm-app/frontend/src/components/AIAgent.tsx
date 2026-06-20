import { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAppSettings } from '../App';

interface Message {
  id: string;
  role: 'user' | 'bot';
  text: string;
}

// ── Grok logo (circle + lightning bolt) ───────────────────────────────────────
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

// ── Send arrow icon ───────────────────────────────────────────────────────────
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
  const { language } = useAppSettings();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

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
    if (open && messages.length === 0) {
      setMessages([{ id: 'w', role: 'bot', text: t('aiWelcome') }]);
    }
  }, [open, t, messages.length]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typing]);

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 100);
  }, [open]);

  const send = async () => {
    const text = input.trim();
    if (!text || typing) return;
    setInput('');
    const userMsg: Message = { id: Date.now().toString(), role: 'user', text };
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
          message: text,
          history,
          ...(userLocation ? { lat: userLocation.lat, lng: userLocation.lng } : {}),
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        const detail = typeof err.detail === 'string' ? err.detail : 'Grok API unavailable';
        throw new Error(detail);
      }

      const data = await res.json();
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'bot', text: data.reply }]);
    } catch (err) {
      const offline = language === 'uk'
        ? 'Не вдалося зʼєднатися з Grok. Переконайтеся, що Python-бекенд запущено на порту 8080.'
        : 'Could not reach Grok. Make sure the Python backend is running on port 8080.';
      const msg = err instanceof Error && err.message !== 'Failed to fetch' ? err.message : offline;
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'bot', text: msg }]);
    } finally {
      setTyping(false);
    }
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  };

  return (
    <>
      {open && (
        <div className="ai-window glass-card">
          {/* Header */}
          <div className="ai-header">
            <div className="ai-header-title">
              <div className="ai-avatar-sm">
                <GrokIcon />
              </div>
              <div>
                <div className="ai-name">{t('aiAssistant')}</div>
                <div className="ai-status">Online</div>
              </div>
            </div>
            <button className="ai-close-btn" onClick={() => setOpen(false)} aria-label={t('close')}>
              <CloseIcon />
            </button>
          </div>

          {/* Messages */}
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

          {/* Input */}
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

      {/* Floating action button */}
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
