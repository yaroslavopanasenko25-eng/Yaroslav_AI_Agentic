import { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useAppSettings } from '../App';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, LineChart, Line, Legend,
} from 'recharts';
import type { AlarmEvent } from '../types';

// ── Deterministic pseudo-random ───────────────────────────────────────────────
function sr(seed: number): number {
  const x = Math.sin(seed + 1) * 10000;
  return x - Math.floor(x);
}

// ── Period definition ─────────────────────────────────────────────────────────
type Period = '1h' | '1d' | '7d' | '14d' | '30d' | 'all';

interface PeriodConfig {
  label: string;
  labelUk: string;
  points: number;
  dateFn: (i: number) => string;
  timeFn: (i: number) => string;
}

const PERIOD_CONFIG: Record<Period, PeriodConfig> = {
  '1h':  { label: '1H',   labelUk: '1год',  points: 12, dateFn: (i) => `${String(i * 5).padStart(2,'0')}m`,      timeFn: (i) => `${String(i * 5).padStart(2,'0')}m` },
  '1d':  { label: '1D',   labelUk: '1д',    points: 24, dateFn: (i) => `${String(i).padStart(2,'0')}:00`,        timeFn: (i) => `${String(i).padStart(2,'0')}:00`   },
  '7d':  { label: '7D',   labelUk: '7д',    points: 7,  dateFn: (i) => { const d = new Date(); d.setDate(d.getDate()-6+i); return d.toLocaleDateString('uk',{month:'numeric',day:'numeric'}); }, timeFn: () => '00:00' },
  '14d': { label: '14D',  labelUk: '14д',   points: 14, dateFn: (i) => { const d = new Date(); d.setDate(d.getDate()-13+i); return `${String(d.getMonth()+1).padStart(2,'0')}.${String(d.getDate()).padStart(2,'0')}`; }, timeFn: () => '00:00' },
  '30d': { label: '30D',  labelUk: '30д',   points: 30, dateFn: (i) => { const d = new Date(); d.setDate(d.getDate()-29+i); return `${String(d.getMonth()+1).padStart(2,'0')}.${String(d.getDate()).padStart(2,'0')}`; }, timeFn: () => '00:00' },
  'all': { label: 'ALL',  labelUk: 'Всі',   points: 60, dateFn: (i) => { const d = new Date(); d.setDate(d.getDate()-59+i); return `${String(d.getMonth()+1).padStart(2,'0')}.${String(d.getDate()).padStart(2,'0')}`; }, timeFn: () => '00:00' },
};

const PERIODS: Period[] = ['1h', '1d', '7d', '14d', '30d', 'all'];

const REGION_NAMES_UK: Record<string, string> = {
  kharkiv:'Харківська', donetsk:'Донецька', sumy:'Сумська',
  zaporizhzhia:'Запорізька', 'kyiv-city':'м. Київ', dnipro:'Дніпропетровська',
  chernihiv:'Чернігівська', kherson:'Херсонська', mykolaiv:'Миколаївська',
  odesa:'Одеська', rivne:'Рівненська',
};
const REGION_NAMES_EN: Record<string, string> = {
  kharkiv:'Kharkiv', donetsk:'Donetsk', sumy:'Sumy',
  zaporizhzhia:'Zaporizhzhia', 'kyiv-city':'Kyiv City', dnipro:'Dnipropetrovsk',
  chernihiv:'Chernihiv', kherson:'Kherson', mykolaiv:'Mykolaiv',
  odesa:'Odesa', rivne:'Rivne',
};
const ALL_REGION_IDS = Object.keys(REGION_NAMES_UK);

// ── Data generation ───────────────────────────────────────────────────────────
function generateData(period: Period): { barData: object[]; lineData: object[]; history: AlarmEvent[]; totals: { missiles: number; drones: number; destroyed: number; hit: number } } {
  const cfg = PERIOD_CONFIG[period];
  const BASE = PERIODS.indexOf(period) * 37; // different seed per period

  const barData = Array.from({ length: cfg.points }, (_, i) => {
    const s = BASE + i;
    const missiles  = Math.floor(sr(s * 3)  * 18) + 2;
    const drones    = Math.floor(sr(s * 7)  * 45) + 6;
    const destroyed = Math.floor((missiles + drones) * (0.5 + sr(s * 11) * 0.38));
    return { date: cfg.dateFn(i), missiles, drones, destroyed };
  });

  const lineData = Array.from({ length: cfg.points }, (_, i) => {
    const s = BASE + i + 100;
    const duration = Math.floor(sr(s * 2) * 180) + 20;
    // Varied regions: wave pattern + noise
    const regions  = Math.max(1, Math.round(3 + Math.sin(i / 2.5) * 2.5 + sr(s * 5) * 3));
    const threats  = Math.floor(sr(s * 9) * 50) + 5;
    return { date: cfg.dateFn(i), duration, regions, threats };
  });

  const history: AlarmEvent[] = Array.from({ length: Math.min(cfg.points, 30) }, (_, i) => {
    const s = BASE + i + 200;
    const mTotal = Math.floor(sr(s * 3) * 18) + 2;
    const mDest  = Math.floor(mTotal * (0.5 + sr(s * 5) * 0.35));
    const mHit   = Math.floor((mTotal - mDest) * 0.55);
    const mLost  = mTotal - mDest - mHit;
    const dTotal = Math.floor(sr(s * 7) * 45) + 6;
    const dDest  = Math.floor(dTotal * (0.55 + sr(s * 11) * 0.35));
    const dHit   = Math.floor((dTotal - dDest) * 0.45);
    const dLost  = dTotal - dDest - dHit;
    const regionCount = Math.max(1, Math.round(2 + sr(s * 13) * 5));
    const regionSlice = [...ALL_REGION_IDS].sort(() => sr(s + i * 3) - 0.5).slice(0, regionCount);

    return {
      id: `${period}-${i}`,
      date: cfg.dateFn(i),
      startTime: cfg.timeFn(i),
      duration: Math.floor(sr(s * 17) * 160) + 25,
      regions: regionSlice,
      threats: [
        { type: 'missiles' as const, total: mTotal, destroyed: mDest, hit: mHit, lost: mLost },
        { type: 'drones'   as const, total: dTotal, destroyed: dDest, hit: dHit, lost: dLost },
      ],
    };
  }).reverse();

  const totals = barData.reduce(
    (acc, row: any) => ({
      missiles:  acc.missiles  + row.missiles,
      drones:    acc.drones    + row.drones,
      destroyed: acc.destroyed + row.destroyed,
      hit:       acc.hit       + (row.missiles + row.drones - row.destroyed),
    }),
    { missiles: 0, drones: 0, destroyed: 0, hit: 0 },
  );

  return { barData, lineData, history, totals };
}

// ── Component ─────────────────────────────────────────────────────────────────
export default function Analysis() {
  const { t } = useTranslation();
  const { language } = useAppSettings();
  const [period, setPeriod] = useState<Period>('14d');

  const { barData, lineData, history, totals } = useMemo(
    () => generateData(period),
    [period],
  );

  const interceptRate = totals.missiles + totals.drones > 0
    ? Math.round(totals.destroyed / (totals.missiles + totals.drones) * 100)
    : 0;

  const regionNames = language === 'uk' ? REGION_NAMES_UK : REGION_NAMES_EN;

  const tooltipStyle = {
    backgroundColor: 'var(--bg-elevated)',
    border: '1px solid var(--glass-border)',
    borderRadius: '10px',
    fontSize: '12px',
    color: 'var(--text-primary)',
  };

  return (
    <div className="page analysis-page">
      {/* Header + period filter */}
      <div className="page-header">
        <div>
          <h1 className="page-title">{t('analysis')}</h1>
        </div>
        <div className="period-filter">
          {PERIODS.map(p => (
            <button
              key={p}
              className={`period-btn${period === p ? ' active' : ''}`}
              onClick={() => setPeriod(p)}
            >
              {language === 'uk' ? PERIOD_CONFIG[p].labelUk : PERIOD_CONFIG[p].label}
            </button>
          ))}
        </div>
      </div>

      {/* Stat cards */}
      <div className="stat-grid">
        <div className="glass-card stat-card">
          <div className="stat-icon red">🚀</div>
          <div className="stat-value">{totals.missiles}</div>
          <div className="stat-label">{t('missiles')}</div>
        </div>
        <div className="glass-card stat-card">
          <div className="stat-icon orange">🛸</div>
          <div className="stat-value">{totals.drones}</div>
          <div className="stat-label">{t('drones')}</div>
        </div>
        <div className="glass-card stat-card">
          <div className="stat-icon green">🎯</div>
          <div className="stat-value">{totals.destroyed}</div>
          <div className="stat-label">{t('destroyed')}</div>
        </div>
        <div className="glass-card stat-card">
          <div className="stat-icon red">💥</div>
          <div className="stat-value">{totals.hit}</div>
          <div className="stat-label">{t('hit')}</div>
        </div>
      </div>

      {/* Intercept rate */}
      <div className="glass-card intercept-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            {language === 'uk' ? 'Відсоток перехоплення' : 'Interception Rate'}
          </span>
          <span style={{ fontSize: 20, fontWeight: 700, color: 'var(--accent-green)' }}>{interceptRate}%</span>
        </div>
        <div style={{ height: 8, borderRadius: 4, background: 'var(--glass-bg-hover)', overflow: 'hidden' }}>
          <div style={{
            height: '100%',
            borderRadius: 4,
            width: `${interceptRate}%`,
            background: `linear-gradient(90deg, var(--accent-blue), var(--accent-green))`,
            transition: 'width 0.8s cubic-bezier(0.34,1.56,0.64,1)',
          }} />
        </div>
      </div>

      {/* Charts + table */}
      <div className="analysis-grid">
        {/* Bar: threats by day */}
        <div className="glass-card chart-card">
          <div className="section-title">{language === 'uk' ? 'Загрози по днях' : 'Threats by Period'}</div>
          <div className="chart-inner">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={barData} margin={{ top: 8, right: 20, left: -8, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
                <YAxis tick={{ fontSize: 10 }} width={36} />
                <Tooltip contentStyle={tooltipStyle} />
                <Legend wrapperStyle={{ fontSize: 11, paddingTop: 4 }} />
                <Bar dataKey="missiles"  name={t('missiles')}  fill="#FF453A" radius={[3,3,0,0]} />
                <Bar dataKey="drones"    name={t('drones')}    fill="#FF9F0A" radius={[3,3,0,0]} />
                <Bar dataKey="destroyed" name={t('destroyed')} fill="#30D158" radius={[3,3,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Line: duration + regions + threats */}
        <div className="glass-card chart-card">
          <div className="section-title">{language === 'uk' ? 'Тривалість, регіони та загрози' : 'Duration, Regions & Threats'}</div>
          <div className="chart-inner">
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={lineData} margin={{ top: 8, right: 20, left: -8, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
                <YAxis tick={{ fontSize: 10 }} width={36} />
                <Tooltip contentStyle={tooltipStyle} />
                <Legend wrapperStyle={{ fontSize: 11, paddingTop: 4 }} />
                <Line
                  type="monotone" dataKey="duration"
                  name={language === 'uk' ? 'Тривалість (хв)' : 'Duration (min)'}
                  stroke="#0A84FF" strokeWidth={2}
                  dot={false} activeDot={{ r: 4 }}
                />
                <Line
                  type="monotone" dataKey="regions"
                  name={language === 'uk' ? 'Регіони' : 'Regions'}
                  stroke="#BF5AF2" strokeWidth={2}
                  dot={false} activeDot={{ r: 4 }}
                />
                <Line
                  type="monotone" dataKey="threats"
                  name={language === 'uk' ? 'Загрози (всього)' : 'Threats (total)'}
                  stroke="#FF9F0A" strokeWidth={2}
                  dot={false} activeDot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* History table */}
        <div className="glass-card full-width analysis-table-card">
          <div className="section-title">{t('alarmHistory')}</div>
          <div className="alarm-table-wrap">
            <table className="alarm-table">
              <thead>
                <tr>
                  <th>{language === 'uk' ? 'Дата' : 'Date'}</th>
                  <th>{language === 'uk' ? 'Початок' : 'Start'}</th>
                  <th>{t('duration')}</th>
                  <th>{language === 'uk' ? 'Регіони' : 'Regions'}</th>
                  <th>{t('missiles')}</th>
                  <th>{t('drones')}</th>
                  <th>{t('destroyed')}</th>
                  <th>{t('hit')}</th>
                </tr>
              </thead>
              <tbody>
                {history.map(ev => {
                  const m = ev.threats.find(t => t.type === 'missiles');
                  const d = ev.threats.find(t => t.type === 'drones');
                  const totalDest = (m?.destroyed ?? 0) + (d?.destroyed ?? 0);
                  const totalHit  = (m?.hit ?? 0)       + (d?.hit ?? 0);
                  return (
                    <tr key={ev.id}>
                      <td style={{ fontWeight: 600, whiteSpace: 'nowrap' }}>{ev.date}</td>
                      <td style={{ whiteSpace: 'nowrap' }}>{ev.startTime}</td>
                      <td style={{ whiteSpace: 'nowrap' }}>{ev.duration} {t('minutes')}</td>
                      <td>
                        <div className="regions-wrap">
                          {ev.regions.slice(0, 3).map(r => (
                            <span key={r} className="region-chip">{regionNames[r] || r}</span>
                          ))}
                          {ev.regions.length > 3 && (
                            <span className="region-chip">+{ev.regions.length - 3}</span>
                          )}
                        </div>
                      </td>
                      <td><span className="threat-pill missiles">{m?.total ?? 0}</span></td>
                      <td><span className="threat-pill drones">{d?.total ?? 0}</span></td>
                      <td style={{ color: 'var(--accent-green)', fontWeight: 600 }}>{totalDest}</td>
                      <td style={{ color: 'var(--accent-red)', fontWeight: 600 }}>{totalHit}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
