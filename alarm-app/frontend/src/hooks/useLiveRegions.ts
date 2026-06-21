import { useEffect, useState } from 'react';
import type { AlarmStatus, Region } from '../types';

export interface LiveRegionsSnapshot {
  regions: Region[];
  source: string;
  updatedAt: string;
  /** Oblast-level full air raid (IoT status active) */
  activeOblasts: number;
  /** Oblast-level partial alert */
  warningOblasts: number;
  /** Any alarm signal (active + warning), excludes occupied-only */
  alarmOblasts: number;
}

const EMPTY: LiveRegionsSnapshot = {
  regions: [],
  source: 'offline',
  updatedAt: '',
  activeOblasts: 0,
  warningOblasts: 0,
  alarmOblasts: 0,
};

export function useLiveRegions(pollMs = 15_000): LiveRegionsSnapshot {
  const [snap, setSnap] = useState<LiveRegionsSnapshot>(EMPTY);

  useEffect(() => {
    let cancelled = false;

    const load = () => {
      fetch('/api/regions', { cache: 'no-store' })
        .then(r => r.json())
        .then(data => {
          if (cancelled || !Array.isArray(data.regions)) return;
          const regions = data.regions as Region[];
          const activeOblasts = regions.filter(r => r.status === 'active').length;
          const warningOblasts = regions.filter(r => r.status === 'warning').length;
          setSnap({
            regions,
            source: data.source ?? 'live',
            updatedAt: new Date().toLocaleTimeString('uk-UA', {
              timeZone: 'Europe/Kyiv',
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
              hour12: false,
            }),
            activeOblasts,
            warningOblasts,
            alarmOblasts: activeOblasts + warningOblasts,
          });
        })
        .catch(() => {
          if (!cancelled) setSnap(EMPTY);
        });
    };

    load();
    const timer = window.setInterval(load, pollMs);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [pollMs]);

  return snap;
}

export function dangerLabel(status: AlarmStatus, language: 'uk' | 'en'): string {
  const uk: Record<AlarmStatus, string> = {
    active: 'Тривога',
    warning: 'Часткова тривога',
    clear: 'Спокійно',
    occupied: 'Окуповано',
  };
  const en: Record<AlarmStatus, string> = {
    active: 'Air raid',
    warning: 'Partial alert',
    clear: 'Clear',
    occupied: 'Occupied',
  };
  return language === 'uk' ? uk[status] : en[status];
}

export function dangerLevelRank(status: AlarmStatus): number {
  if (status === 'active') return 3;
  if (status === 'warning') return 2;
  if (status === 'clear') return 1;
  return 0;
}
