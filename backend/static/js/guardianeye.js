/** Minimal browser glue for Python/Jinja2 UI (maps, charts, polling). Logic lives in FastAPI. */
const GuardianEye = (() => {
  const cfg = window.GUARDIANEYE || {};
  const lang = cfg.lang || 'uk';
  const isUk = lang === 'uk';

  const DANGER_UK = { active: 'Тривога', warning: 'Часткова тривога', clear: 'Спокійно', occupied: 'Окуповано' };
  const DANGER_EN = { active: 'Air raid', warning: 'Partial alert', clear: 'Clear', occupied: 'Occupied' };
  const dangerLabel = s => (isUk ? DANGER_UK : DANGER_EN)[s] || s;

  const ICON_CLASS = { active: 'red', warning: 'orange', clear: 'green', occupied: 'gray' };

  let selectedRegion = localStorage.getItem('selectedRegion') || 'kyiv-city';
  let barChart = null;
  let lineChart = null;
  let analysisPeriod = '14d';
  let chatHistory = [];

  function $(id) { return document.getElementById(id); }

  function applySettings() {
    const shell = $('app-shell');
    const theme = localStorage.getItem('theme') || 'dark';
    const dyslexia = localStorage.getItem('dyslexia') === 'true';
    shell?.setAttribute('data-theme', theme);
    shell?.setAttribute('data-dyslexia', String(dyslexia));
    document.querySelectorAll('.theme-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.theme === theme);
    });
    const dys = $('dyslexia-toggle');
    if (dys) dys.checked = dyslexia;
  }

  function initSettings() {
    applySettings();
    $('settings-open')?.addEventListener('click', () => {
      $('settings-backdrop')?.classList.add('open');
      $('settings-sheet')?.classList.add('open');
    });
    const close = () => {
      $('settings-backdrop')?.classList.remove('open');
      $('settings-sheet')?.classList.remove('open');
    };
    $('settings-close')?.addEventListener('click', close);
    $('settings-backdrop')?.addEventListener('click', close);
    document.querySelectorAll('.theme-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        localStorage.setItem('theme', btn.dataset.theme);
        applySettings();
      });
    });
    $('dyslexia-toggle')?.addEventListener('change', e => {
      localStorage.setItem('dyslexia', String(e.target.checked));
      applySettings();
    });
  }

  async function fetchRegions() {
    const r = await fetch('/api/v1/regions', { cache: 'no-store' });
    return r.json();
  }

  function updateLiveStats(regions, totals, periodLabel) {
    const active = regions.filter(r => r.status === 'active').length;
    const warning = regions.filter(r => r.status === 'warning').length;
    const el = id => $(id);
    if (el('stat-oblasts')) el('stat-oblasts').textContent = active + warning;
    const det = el('stat-oblasts-detail');
    if (det) det.textContent = isUk
      ? `${active} повна · ${warning} часткова`
      : `${active} full · ${warning} partial`;
    if (totals) {
      if (el('stat-total')) el('stat-total').textContent = totals.totalAlerts ?? '—';
      if (el('stat-avg')) el('stat-avg').textContent = totals.avgDurationMinutes ?? '—';
      if (el('stat-total-label') && periodLabel) {
        el('stat-total-label').textContent = isUk
          ? `Тривоги · ${periodLabel.toLowerCase()}`
          : `Alerts · ${periodLabel.toLowerCase()}`;
      }
    }
    const sel = regions.find(r => r.id === selectedRegion) || regions[0];
    if (sel && el('stat-danger')) {
      el('stat-danger').textContent = dangerLabel(sel.status);
      const icon = el('stat-danger-icon');
      if (icon) icon.className = `stat-icon ${ICON_CLASS[sel.status] || 'green'}`;
    }
    const meta = el('live-stats-meta');
    if (meta) meta.style.display = 'block';
  }

  async function pollLiveStats() {
    if (!$('live-stats')) return;
    try {
      const data = await fetchRegions();
      const regions = data.regions || [];
      let totals = null;
      let periodLabel = '';
      if ($('bar-chart')) {
        const a = await fetch(`/api/v1/alarms/analysis?period=${analysisPeriod}`, { cache: 'no-store' });
        const aj = await a.json();
        if (aj.totals) {
          totals = aj.totals;
          periodLabel = (cfg.periodLabels?.[analysisPeriod]?.total) || analysisPeriod;
        }
      }
      updateLiveStats(regions, totals, periodLabel);
    } catch (_) { /* offline */ }
  }

  function initRegionSelect() {
    const sel = $('region-select');
    if (!sel) return;
    sel.value = selectedRegion;
    sel.addEventListener('change', () => {
      selectedRegion = sel.value;
      localStorage.setItem('selectedRegion', selectedRegion);
      pollLiveStats();
      loadDispatchBrief();
    });
  }

  function renderCharts(data) {
    const barCtx = $('bar-chart')?.getContext('2d');
    const lineCtx = $('line-chart')?.getContext('2d');
    if (!barCtx || !lineCtx) return;
    if (barChart) barChart.destroy();
    if (lineChart) lineChart.destroy();
    const grid = 'rgba(255,255,255,0.08)';
    const ticks = 'rgba(255,255,255,0.5)';
    barChart = new Chart(barCtx, {
      type: 'bar',
      data: {
        labels: data.barData.map(d => d.date),
        datasets: [
          { label: isUk ? 'Повітряні' : 'Air raid', data: data.barData.map(d => d.missiles), backgroundColor: '#FF453A' },
          { label: isUk ? 'Інші' : 'Other', data: data.barData.map(d => d.drones), backgroundColor: '#FF9F0A' },
        ],
      },
      options: { responsive: true, plugins: { legend: { labels: { color: ticks } } }, scales: { x: { ticks: { color: ticks } }, y: { ticks: { color: ticks }, grid: { color: grid } } } },
    });
    lineChart = new Chart(lineCtx, {
      type: 'line',
      data: {
        labels: data.lineData.map(d => d.date),
        datasets: [
          { label: isUk ? 'Тривалість (хв)' : 'Duration (min)', data: data.lineData.map(d => d.duration), borderColor: '#0A84FF', tension: 0.3 },
          { label: isUk ? 'Регіони' : 'Regions', data: data.lineData.map(d => d.regions), borderColor: '#BF5AF2', tension: 0.3 },
          { label: isUk ? 'Загрози' : 'Threats', data: data.lineData.map(d => d.threats), borderColor: '#FF9F0A', tension: 0.3 },
        ],
      },
      options: { responsive: true, plugins: { legend: { labels: { color: ticks } } }, scales: { x: { ticks: { color: ticks } }, y: { ticks: { color: ticks }, grid: { color: grid } } } },
    });
  }

  function renderTable(data, live) {
    const thead = $('alarm-thead');
    const tbody = $('alarm-tbody');
    if (!thead || !tbody) return;
    if (live) {
      thead.innerHTML = `<tr><th>${isUk ? 'Локація' : 'Location'}</th><th>${isUk ? 'Область' : 'Oblast'}</th><th>${isUk ? 'Початок' : 'Start'}</th><th>${isUk ? 'Тривалість' : 'Duration'}</th><th>${isUk ? 'Тип' : 'Type'}</th></tr>`;
      tbody.innerHTML = (data.history || []).map(ev => `
        <tr><td>${ev.regionLabel || '—'}</td><td>${ev.oblastLabel || '—'}</td>
        <td>${ev.dateLabel || ''} ${ev.startTime || ''}</td>
        <td>${ev.durationLabel || ev.duration || '—'}</td>
        <td><span class="threat-pill missiles">${ev.alertType || 'air_raid'}</span></td></tr>`).join('');
    } else {
      thead.innerHTML = `<tr><th>Date</th><th>Start</th><th>Dur</th><th>Regions</th></tr>`;
      tbody.innerHTML = (data.history || []).slice(0, 20).map(ev => `
        <tr><td>${ev.date}</td><td>${ev.startTime}</td><td>${ev.duration}</td><td>${(ev.regions || []).join(', ')}</td></tr>`).join('');
    }
  }

  async function loadAnalysis(period) {
    analysisPeriod = period;
    const status = $('analysis-status');
    try {
      const r = await fetch(`/api/v1/alarms/analysis?period=${period}`, { cache: 'no-store' });
      const data = await r.json();
      const live = data.source && data.source !== 'demo';
      if (status) {
        status.textContent = live
          ? (isUk ? '● Дані alerts.in.ua · час Київ' : '● alerts.in.ua data · Kyiv time')
          : (isUk ? 'Демо-режим — немає API' : 'Demo mode — no API');
        status.style.color = live ? 'var(--accent-green)' : 'var(--accent-orange)';
      }
      renderCharts(data);
      renderTable(data, live);
      await pollLiveStats();
    } catch (e) {
      if (status) status.textContent = isUk ? 'Помилка завантаження' : 'Load error';
    }
  }

  function initAnalysis() {
    initRegionSelect();
    pollLiveStats();
    setInterval(pollLiveStats, 15000);
    document.querySelectorAll('.period-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        loadAnalysis(btn.dataset.period);
      });
    });
    loadAnalysis('14d');
  }

  async function initSafetyMap() {
    const el = $('shelter-map');
    if (!el || typeof L === 'undefined') return;
    const map = L.map(el).setView([50.4501, 30.5234], 11);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { attribution: '© OSM' }).addTo(map);
    try {
      const r = await fetch('/static/data/shelters.json');
      const shelters = await r.json();
      shelters.slice(0, 800).forEach(s => {
        L.marker([s.lat, s.lng]).addTo(map).bindPopup(`<b>${s.nameUk}</b><br>${s.city || ''}`);
      });
    } catch (_) { /* no shelters file */ }
  }

  const QUICK = isUk
    ? ['Що робити зараз?', 'Найближче укриття', 'Коли можлива тривога?', 'Екстрені номери']
    : ['What to do now?', 'Nearest shelter', 'When might alarm occur?', 'Emergency numbers'];

  async function loadDispatchBrief() {
    const params = new URLSearchParams({ region_id: selectedRegion, language: lang });
    try {
      const r = await fetch(`/api/v1/ai/dispatch?${params}`);
      const d = await r.json();
      const st = $('ai-dispatch-status');
      const bar = $('ai-dispatch-bar');
      if (st && d.priority_label) {
        st.innerHTML = `<span class="dispatch-badge dispatch-${d.priority}">${d.priority_label}${d.risk?.next_6h_probability != null ? ` · ${d.risk.next_6h_probability}%` : ''}</span>`;
      }
      if (bar && d.region_name) {
        bar.hidden = false;
        bar.textContent = `${d.region_name} · ${d.status_label || ''}`;
      }
    } catch (_) { /* ignore */ }
  }

  function appendMsg(role, text) {
    const box = $('ai-messages');
    if (!box) return;
    const div = document.createElement('div');
    div.className = `ai-msg ${role}`;
    div.textContent = text;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
  }

  async function sendChat(text) {
    if (!text.trim()) return;
    appendMsg('user', text);
    chatHistory.push({ role: 'user', content: text });
    const typing = document.createElement('div');
    typing.className = 'ai-msg bot typing';
    typing.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';
    $('ai-messages')?.appendChild(typing);
    try {
      const body = {
        message: text,
        history: chatHistory.slice(-10),
        language: lang,
        region_id: selectedRegion,
      };
      if (navigator.geolocation) {
        /* optional — skip blocking */
      }
      const r = await fetch('/api/v1/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      typing.remove();
      if (!r.ok) throw new Error('API error');
      const data = await r.json();
      appendMsg('bot', data.reply);
      chatHistory.push({ role: 'assistant', content: data.reply });
      if (data.dispatch) loadDispatchBrief();
    } catch (e) {
      typing.remove();
      appendMsg('bot', isUk ? 'Не вдалося зʼєднатися з бекендом.' : 'Could not reach backend.');
    }
  }

  function initAI() {
    const fab = $('ai-fab');
    const win = $('ai-window');
    const quick = $('ai-quick-actions');
    QUICK.forEach(q => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'ai-quick-btn';
      b.textContent = q;
      b.addEventListener('click', () => sendChat(q));
      quick?.appendChild(b);
    });
    fab?.addEventListener('click', () => {
      const open = win?.hasAttribute('hidden');
      if (open) {
        win.removeAttribute('hidden');
        fab.classList.add('open');
        if ($('ai-messages')?.childElementCount === 0) {
          appendMsg('bot', isUk
            ? 'Привіт! Я диспетчер GuardianEye — тривоги, укриття, прогноз, екстрені дії.'
            : 'Hello! GuardianEye dispatcher — alarms, shelters, forecast, emergency guidance.');
        }
        loadDispatchBrief();
      } else {
        win.setAttribute('hidden', '');
        fab.classList.remove('open');
      }
    });
    $('ai-close')?.addEventListener('click', () => {
      win?.setAttribute('hidden', '');
      fab?.classList.remove('open');
    });
    $('ai-send')?.addEventListener('click', () => {
      const inp = $('ai-input');
      if (inp) { sendChat(inp.value); inp.value = ''; }
    });
    $('ai-input')?.addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); $('ai-send')?.click(); }
    });
  }

  function init() {
    initSettings();
    initRegionSelect();
    initAI();
    if ($('live-stats') && !$('bar-chart')) {
      pollLiveStats();
      setInterval(pollLiveStats, 15000);
    }
  }

  document.addEventListener('DOMContentLoaded', init);

  return { initAnalysis, initSafetyMap };
})();
