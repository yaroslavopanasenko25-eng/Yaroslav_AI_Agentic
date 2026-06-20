import { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAppSettings } from '../App';

interface Message {
  id: string;
  role: 'user' | 'bot';
  text: string;
}

const BOT_UK = [
  'Якщо оголошено тривогу — негайно спускайтеся до укриття або підвалу. Уникайте вікон.',
  'Найближче укриття — у вкладці «Безпека» → карта укриттів.',
  'Тривожна валіза: документи, вода (3 л/добу), ліки, ліхтарик, заряджений телефон.',
  'Під час атаки — подалі від вікон і зовнішніх стін, ляжте на підлогу.',
  'Після відбою зачекайте 15–20 хвилин, перш ніж виходити.',
  'Підпишіться на офіційний Telegram-канал своєї ОВА.',
  'Дзвоніть 112 в надзвичайних ситуаціях, 101 — пожежна, 103 — швидка.',
  'Запасіться водою на 3–5 днів і консервами. Тримайте павербанк зарядженим.',
];
const BOT_EN = [
  'If an alarm sounds, immediately go to a shelter or basement. Avoid windows.',
  'Find the nearest shelter in the "Safety" tab → shelter map.',
  'Emergency bag: documents, water (3L/day), medicines, flashlight, charged phone.',
  'During an attack, stay away from windows and outer walls, lie flat on the floor.',
  'After the all-clear, wait 15–20 minutes before going outside.',
  'Subscribe to your regional official Telegram channel for timely alerts.',
  'Call 112 for emergencies, 101 for fire, 103 for ambulance.',
  'Store water for 3–5 days and canned food. Keep your powerbank charged.',
];

// ── Grok logo (xAI) ───────────────────────────────────────────────────────────
const GrokIcon = () => (
  <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
    {/* Grok's distinctive multi-arm geometric shape */}
    <path
      d="M16 2 L18.5 13.5 L30 16 L18.5 18.5 L16 30 L13.5 18.5 L2 16 L13.5 13.5 Z"
      fill="white"
      opacity="0.95"
    />
    <path
      d="M16 7 L17.6 13.4 L24 16 L17.6 18.6 L16 25 L14.4 18.6 L8 16 L14.4 13.4 Z"
      fill="url(#grokGrad)"
      opacity="0.4"
    />
    <defs>
      <radialGradient id="grokGrad" cx="50%" cy="50%" r="50%">
        <stop offset="0%" stopColor="#ffffff" stopOpacity="0.9"/>
        <stop offset="100%" stopColor="#60a5fa" stopOpacity="0.3"/>
      </radialGradient>
    </defs>
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
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

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

    try {
      const res = await fetch('/api/v1/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'bot', text: data.reply }]);
    } catch {
      await new Promise(r => setTimeout(r, 700 + Math.random() * 600));
      const pool = language === 'uk' ? BOT_UK : BOT_EN;
      const reply = pool[Math.floor(Math.random() * pool.length)];
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'bot', text: reply }]);
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
