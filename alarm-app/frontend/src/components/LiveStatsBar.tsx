import { useMemo } from 'react';
import type { AlarmStatus } from '../types';
import { useLiveRegions, dangerLabel } from '../hooks/useLiveRegions';

export interface PeriodStats {
  totalAlerts: number;
  avgDurationMinutes: number;
  periodLabelUk: string;
  periodLabelEn: string;
}

interface Props {
  language: 'uk' | 'en';
  periodStats: PeriodStats;
  selectedRegionId: string;
  onRegionChange: (id: string) => void;
  loading?: boolean;
}

const STATUS_CLASS: Record<AlarmStatus, string> = {
  active: 'red',
  warning: 'orange',
  clear: 'green',
  occupied: 'gray',
};

export default function LiveStatsBar({
  language,
  periodStats,
  selectedRegionId,
  onRegionChange,
  loading = false,
}: Props) {
  const live = useLiveRegions();
  const isUk = language === 'uk';

  const selectableRegions = useMemo(
    () => [...live.regions]
      .sort((a, b) => (isUk ? a.nameUk : a.nameEn).localeCompare(isUk ? b.nameUk : b.nameEn, 'uk')),
    [live.regions, isUk],
  );

  const regionOptionLabel = (r: { nameUk: string; nameEn: string; status: AlarmStatus }) => {
    const name = isUk ? r.nameUk : r.nameEn;
    if (r.status === 'occupied') {
      return isUk ? `${name} (окуповано)` : `${name} (occupied)`;
    }
    return name;
  };

  const selected = live.regions.find(r => r.id === selectedRegionId)
    ?? selectableRegions[0]
    ?? null;

  const dangerStatus: AlarmStatus = selected?.status ?? 'clear';
  const dangerText = dangerLabel(dangerStatus, language);

  return (
    <div className="live-stats-wrap">
      <div className="stat-grid live-stats-grid">
        {/* 1 — Oblast alarm count (same on every page, live IoT map) */}
        <div className="glass-card stat-card">
          <div className="stat-icon red">🗺️</div>
          <div className="stat-value">{live.source !== 'offline' ? live.alarmOblasts : '—'}</div>
          <div className="stat-label">
            {isUk ? 'Областей з тривогою' : 'Oblasts in alarm'}
            {live.source !== 'offline' && live.alarmOblasts > 0 && (
              <span style={{ display: 'block', fontSize: 10, color: 'var(--text-secondary)', marginTop: 4 }}>
                {isUk
                  ? `${live.activeOblasts} повна · ${live.warningOblasts} часткова`
                  : `${live.activeOblasts} full · ${live.warningOblasts} partial`}
              </span>
            )}
          </div>
        </div>

        {/* 2 — Total alerts in selected period */}
        <div className="glass-card stat-card">
          <div className="stat-icon orange">📊</div>
          <div className="stat-value">
            {loading ? '…' : periodStats.totalAlerts}
          </div>
          <div className="stat-label">
            {isUk
              ? `Тривоги · ${periodStats.periodLabelUk.toLowerCase()}`
              : `Alerts · ${periodStats.periodLabelEn.toLowerCase()}`}
          </div>
        </div>

        {/* 3 — Average duration in selected period */}
        <div className="glass-card stat-card">
          <div className="stat-icon blue">⏱</div>
          <div className="stat-value">
            {loading ? '…' : periodStats.avgDurationMinutes}
          </div>
          <div className="stat-label">
            {isUk ? 'Сер. тривалість (хв)' : 'Avg duration (min)'}
          </div>
        </div>

        {/* 4 — Current danger in selected oblast */}
        <div className="glass-card stat-card stat-card-region">
          <div className={`stat-icon ${STATUS_CLASS[dangerStatus]}`}>⚠️</div>
          <div className="stat-value stat-value-danger">{dangerText}</div>
          <div className="stat-label">{isUk ? 'Рівень небезпеки' : 'Danger level'}</div>
          <select
            className="region-select"
            value={selected?.id ?? ''}
            onChange={e => onRegionChange(e.target.value)}
            aria-label={isUk ? 'Область' : 'Oblast'}
          >
            {selectableRegions.map(r => (
              <option key={r.id} value={r.id}>
                {regionOptionLabel(r)}
              </option>
            ))}
          </select>
        </div>
      </div>
      {live.source !== 'offline' && (
        <div className="live-stats-meta">
          ● {isUk ? 'alerts.in.ua · IoT карта' : 'alerts.in.ua · IoT map'}
          {live.updatedAt && (
            <span style={{ marginLeft: 8, opacity: 0.7 }}>
              {isUk ? 'оновлено' : 'updated'} {live.updatedAt}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
