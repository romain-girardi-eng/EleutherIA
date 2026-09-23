import type { TFunction } from 'i18next';

import { PERIOD_I18N_KEYS } from './chronosTimeline';

/** Historical years never pass through a sign: -400 reads as "400 BCE". */
export function formatHistoricalYear(t: TFunction, year: number | null | undefined): string {
  if (year === null || year === undefined) return t('chronos.year.open');
  if (year < 0) return t('chronos.year.bce', { year: Math.abs(year) });
  return t('chronos.year.ce', { year });
}

export function formatYearRange(
  t: TFunction,
  start: number | null | undefined,
  end: number | null | undefined,
): string {
  if (start === null || start === undefined || end === null || end === undefined) {
    return t('chronos.period.undatedRange');
  }
  return t('chronos.year.range', {
    start: formatHistoricalYear(t, start),
    end: formatHistoricalYear(t, end),
  });
}

export function periodName(t: TFunction, label: string): string {
  const key = PERIOD_I18N_KEYS[label];
  return key ? t(`chronos.periods.${key}`, { defaultValue: label }) : label;
}

export function typeName(t: TFunction, typeKey: string): string {
  return t(`chronos.types.${typeKey}`, { defaultValue: typeKey.replace(/_/g, ' ') });
}

export function formatCount(locale: string, value: number): string {
  return value.toLocaleString(locale);
}
