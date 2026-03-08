import type { TFunction } from 'i18next';

/**
 * Safely retrieve an array from i18next's `returnObjects` mode.
 * Returns `fallback` when the key is missing or the value is not an array.
 */
export function tArray<T = string>(
  t: TFunction,
  key: string,
  fallback: T[] = [],
): T[] {
  const result = t(key, { returnObjects: true });
  return Array.isArray(result) ? (result as T[]) : fallback;
}
