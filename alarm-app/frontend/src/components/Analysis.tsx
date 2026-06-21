import { useState, useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useAppSettings } from '../App';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, LineChart, Line, Legend,
} from 'recharts';
import type { AlarmEvent } from '../types';
import { kyivChartDate, kyivHourLabel } from '../utils/kyivTime';
import LiveStatsBar from './LiveStatsBar';

// ── Deterministic pseudo-random ───────────────────────────────────────────────
function sr(seed: number): number {
  const x = Math.sin(seed + 1) * 10000;
  return x - Math.floor(x);
}

// ── Period definition ─────────────────────────────────────────────────────────
type Period = '1h' | '1d' | '7d' | '14d' | '30d';

interface PeriodConfig {
  label: string;
  labelUk: string;
  points: number;
  dateFn: (i: number) => string;
  timeFn: (i: number) => string;
}

const PERIOD_CONFIG: Record<Period, PeriodConfig> = {
  '1h':  { label: '1H',   labelUk: '1год',  points: 12, dateFn: (i) => `${String(i * 5).padStart(2,'0')}m`,      timeFn: (i) => `${String(i * 5).padStart(2,'0')}m` },
  '1d':  { label: '1D',   labelUk: '1д',    points: 24, dateFn: (i) => kyivHourLabel(i),        timeFn: (i) => kyivHourLabel(i)   },
  '7d':  { label: '7D',   labelUk: '7д',    points: 7,  dateFn: (i) => kyivChartDate(i - 6), timeFn: () => '00:00' },
  '14d': { label: '14D',  labelUk: '14д',   points: 14, dateFn: (i) => kyivChartDate(i - 13), timeFn: () => '00:00' },
  '30d': { label: '30D',  labelUk: '30д',   points: 30, dateFn: (i) => kyivChartDate(i - 29), timeFn: () => '00:00' },
};

const PERIODS: Period[] = ['1h', '1d', '7d', '14d', '30d'];

const PERIOD_LABELS: Record<Period, { activeUk: string; activeEn: string; totalUk: string; totalEn: string }> = {
  '1h':  { activeUk: 'Активні зараз', activeEn: 'Active now', totalUk: 'За годину', totalEn: 'Last hour' },
  '1d':  { activeUk: 'Активні зараз', activeEn: 'Active now', totalUk: 'Сьогодні', totalEn: 'Today' },
  '7d':  { activeUk: 'Активні зараз', activeEn: 'Active now', totalUk: 'За 7 днів', totalEn: 'Last 7 days' },
  '14d': { activeUk: 'Активні зараз', activeEn: 'Active now', totalUk: 'За 14 днів', totalEn: 'Last 14 days' },
  '30d': { activeUk: 'Активні зараз', activeEn: 'Active now', totalUk: 'За 30 днів', totalEn: 'Last 30 days' },
};

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
function generateData(period: Period): { barData: object[]; lineData: object[]; history: AlarmEvent[]; totals: { missiles: number; drones: number; destroyed: number; hit: number; totalAlerts?: number; activeAlerts?: number; avgDurationMinutes?: number; regionsAffected?: number } } {
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
interface AnalysisData {
  barData: object[];
  lineData: object[];
  history: AlarmEvent[];
  totals: {
    missiles: number;
    drones: number;
    destroyed: number;
    hit: number;
    totalAlerts?: number;
    activeAlerts?: number;
    avgDurationMinutes?: number;
    regionsAffected?: number;
    interceptionsAvailable?: boolean;
    targetsDestroyed?: number;
    targetsTotal?: number;
  };
  source?: string;
  updatedAt?: string;
  warDays?: number;
  periodDays?: number;
  warDataNote?: string;
}

type LiveAlarmEvent = AlarmEvent & {
  regionLabel?: string;
  oblastLabel?: string;
  alertType?: string;
  durationLabel?: string;
  dateLabel?: string;
  isActive?: boolean;
};

function formatStartCell(ev: LiveAlarmEvent, language: 'uk' | 'en'): string {
  const label = ev.dateLabel
    || (ev.date ? (language === 'uk' ? 'Сьогодні' : 'Today') : '');
  if (label && ev.startTime) {
    return `${label}, ${ev.startTime}`;
  }
  return ev.startTime || label || '—';
}

export default function Analysis() {
  const { t } = useTranslation();
  const { language, selectedRegionId, setSelectedRegionId } = useAppSettings();
  const [period, setPeriod] = useState<Period>('14d');
  const [apiData, setApiData] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(true);
  const [updatedAt, setUpdatedAt] = useState<string>('');

  useEffect(() => {
    let cancelled = false;

    const load = (initial = false) => {
      if (initial) setLoading(true);
      fetch(`/api/alarms/analysis?period=${period}`, { cache: 'no-store' })
        .then(r => r.json())
        .then(data => {
          if (cancelled) return;
          if (data.barData && data.history && data.source !== 'demo') {
            setApiData(data);
            if (data.updatedAt) setUpdatedAt(data.updatedAt);
          } else if (!apiData) {
            setApiData(null);
          }
        })
        .catch(() => { if (!cancelled && !apiData) setApiData(null); })
        .finally(() => { if (!cancelled && initial) setLoading(false); });
    };

    load(true);
    const timer = window.setInterval(() => load(false), 15_000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps -- keep prior live data on period switch until new fetch completes
  }, [period]);

  const mockData = useMemo(() => generateData(period), [period]);

  const isLive = Boolean(apiData && apiData.source !== 'demo');
  const { barData, lineData, history, totals, source } = isLive && apiData
    ? { ...apiData, source: apiData.source }
    : { ...mockData, source: 'demo' };

  const totalAlerts = totals.totalAlerts ?? (totals.missiles + totals.drones);
  const avgDuration = totals.avgDurationMinutes ?? 0;
  const periodLabels = PERIOD_LABELS[period];
  const interceptRate = totals.missiles + totals.drones > 0
    ? Math.round(totals.destroyed / (totals.missiles + totals.drones) * 100)
    : 0;

  const alertTypeLabel = (type?: string) => {
    if (!type) return '—';
    if (type === 'air_raid') return language === 'uk' ? 'Повітряна тривога' : 'Air raid';
    return type.replace(/_/g, ' ');
  };

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
          {!isLive && !loading && (
            <div style={{ fontSize: 12, color: 'var(--accent-orange)', marginTop: 4 }}>
              {language === 'uk'
                ? 'Немає зʼєднання з API — запустіть бекенд на порту 8080'
                : 'No API connection — start backend on port 8080'}
            </div>
          )}
          {isLive && (
            <div style={{ fontSize: 12, color: 'var(--accent-green)', marginTop: 4 }}>
              ● {language === 'uk' ? 'Дані alerts.in.ua · час Київ' : 'alerts.in.ua data · Kyiv time'}
              {updatedAt && (
                <span style={{ color: 'var(--text-secondary)', marginLeft: 8 }}>
                  {language === 'uk' ? 'оновлено' : 'updated'} {updatedAt}
                </span>
              )}
              {loading ? ' …' : ''}
            </div>
          )}
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

      <LiveStatsBar
        language={language}
        selectedRegionId={selectedRegionId}
        onRegionChange={setSelectedRegionId}
        loading={loading}
        periodStats={{
          totalAlerts,
          avgDurationMinutes: avgDuration,
          periodLabelUk: periodLabels.totalUk,
          periodLabelEn: periodLabels.totalEn,
        }}
      />

      {!isLive && (
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
      )}

      {/* Charts + table */}
      <div className="analysis-grid">
        {/* Bar: threats by day */}
        <div className="glass-card chart-card">
          <div className="section-title">
            {isLive
              ? (language === 'uk' ? `Тривоги ${periodLabels.totalUk.toLowerCase()}` : `Alerts ${periodLabels.totalEn.toLowerCase()}`)
              : (language === 'uk' ? 'Загрози по днях' : 'Threats by Period')}
          </div>
          <div className="chart-inner">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={barData} margin={{ top: 8, right: 20, left: -8, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
                <YAxis tick={{ fontSize: 10 }} width={36} />
                <Tooltip contentStyle={tooltipStyle} />
                <Legend wrapperStyle={{ fontSize: 11, paddingTop: 4 }} />
                <Bar dataKey="missiles"  name={isLive ? (language === 'uk' ? 'Повітряні' : 'Air raid') : t('missiles')}  fill="#FF453A" radius={[3,3,0,0]} />
                <Bar dataKey="drones"    name={isLive ? (language === 'uk' ? 'Інші' : 'Other') : t('drones')}    fill="#FF9F0A" radius={[3,3,0,0]} />
                {!isLive && <Bar dataKey="destroyed" name={t('destroyed')} fill="#30D158" radius={[3,3,0,0]} />}
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

        {/* History / active alerts table */}
        <div className="glass-card full-width analysis-table-card">
          <div className="section-title">
            {isLive
              ? (language === 'uk' ? `Тривоги ${periodLabels.totalUk.toLowerCase()}` : `Alerts ${periodLabels.totalEn.toLowerCase()}`)
              : t('alarmHistory')}
          </div>
          <div className="alarm-table-wrap">
            <table className="alarm-table">
              <thead>
                <tr>
                  {isLive ? (
                    <>
                      <th>{language === 'uk' ? 'Локація' : 'Location'}</th>
                      <th>{language === 'uk' ? 'Область' : 'Oblast'}</th>
                      <th>{language === 'uk' ? 'Початок' : 'Start'}</th>
                      <th>{t('duration')}</th>
                      <th>{language === 'uk' ? 'Тип' : 'Type'}</th>
                    </>
                  ) : (
                    <>
                      <th>{language === 'uk' ? 'Дата' : 'Date'}</th>
                      <th>{language === 'uk' ? 'Початок' : 'Start'}</th>
                      <th>{t('duration')}</th>
                      <th>{language === 'uk' ? 'Регіони' : 'Regions'}</th>
                      <th>{t('missiles')}</th>
                      <th>{t('drones')}</th>
                      <th>{t('destroyed')}</th>
                      <th>{t('hit')}</th>
                    </>
                  )}
                </tr>
              </thead>
              <tbody>
                {history.map(ev => {
                  const liveEv = ev as LiveAlarmEvent;
                  if (isLive) {
                    return (
                      <tr key={ev.id}>
                        <td style={{ fontWeight: 600 }}>{liveEv.regionLabel || regionNames[ev.regions[0]] || ev.regions[0]}</td>
                        <td style={{ color: 'var(--text-secondary)' }}>{liveEv.oblastLabel || '—'}</td>
                        <td style={{ whiteSpace: 'nowrap' }}>{formatStartCell(liveEv, language)}</td>
                        <td style={{ whiteSpace: 'nowrap' }}>
                          {liveEv.durationLabel || `${ev.duration} ${t('minutes')}`}
                        </td>
                        <td>
                          <span className="threat-pill missiles">{alertTypeLabel(liveEv.alertType)}</span>
                        </td>
                      </tr>
                    );
                  }

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
                          {liveEv.regionLabel
                            || regionNames[ev.regions[0]]
                            || ev.regions[0]}
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
