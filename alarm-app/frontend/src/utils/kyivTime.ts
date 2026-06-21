/** All user-visible times in the app use Europe/Kyiv (Kyiv local time). */

export const KYIV_TZ = 'Europe/Kyiv';

export function formatKyivTime(isoOrMs: string | number, locale = 'uk-UA'): string {
  const date = typeof isoOrMs === 'number' ? new Date(isoOrMs) : new Date(isoOrMs);
  return date.toLocaleTimeString(locale, {
    timeZone: KYIV_TZ,
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });
}

export function formatKyivDate(isoOrMs: string | number, locale = 'uk-UA'): string {
  const date = typeof isoOrMs === 'number' ? new Date(isoOrMs) : new Date(isoOrMs);
  return date.toLocaleDateString(locale, {
    timeZone: KYIV_TZ,
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

export function kyivDateLabel(isoOrMs: string | number, language: 'uk' | 'en'): string {
  const date = typeof isoOrMs === 'number' ? new Date(isoOrMs) : new Date(isoOrMs);
  const kyivToday = new Date().toLocaleDateString('en-CA', { timeZone: KYIV_TZ });
  const kyivDay = date.toLocaleDateString('en-CA', { timeZone: KYIV_TZ });
  if (kyivDay === kyivToday) {
    return language === 'uk' ? 'Сьогодні' : 'Today';
  }
  return formatKyivDate(isoOrMs, language === 'uk' ? 'uk-UA' : 'en-GB');
}

/** Offset a Kyiv calendar day from today (for demo chart labels). */
export function kyivChartDate(offsetDays: number): string {
  const now = Date.now();
  const target = now + offsetDays * 86_400_000;
  const d = new Date(target);
  const month = d.toLocaleString('en-GB', { timeZone: KYIV_TZ, month: '2-digit' });
  const day = d.toLocaleString('en-GB', { timeZone: KYIV_TZ, day: '2-digit' });
  return `${month}.${day}`;
}

export function kyivHourLabel(hour: number): string {
  return `${String(hour).padStart(2, '0')}:00`;
}

export function nowKyivClock(locale: 'uk' | 'en'): string {
  return new Date().toLocaleString(locale === 'uk' ? 'uk-UA' : 'en-GB', {
    timeZone: KYIV_TZ,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });
}
