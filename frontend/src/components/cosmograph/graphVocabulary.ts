import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';

/** Stable i18n key fragment for a free-text data label ("Roman Imperial"). */
export function vocabularySlug(value: string): string {
  return value
    .toLowerCase()
    .normalize('NFD')
    .replace(/\p{M}/gu, '')
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '');
}

function humanize(value: string): string {
  const spaced = value.replace(/_/g, ' ').trim();
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

export interface GraphVocabulary {
  /** Plural display name of a node group ("Concepts"). */
  readonly group: (key: string) => string;
  /** Singular display name of a node group ("Concept"). */
  readonly kind: (key: string) => string;
  readonly period: (raw: string) => string;
  readonly school: (raw: string) => string;
  /** Lower-case verb phrase for a relation ("authored by"). */
  readonly relation: (raw: string) => string;
  readonly count: (value: number) => string;
}

/**
 * Data labels (types, periods, schools, relations) arrive in English from
 * the release. Known values are translated; unknown ones fall back to a
 * humanized form of the raw value, never to a bare key.
 */
export function useGraphVocabulary(): GraphVocabulary {
  const { t, i18n } = useTranslation();
  const language = i18n.language;
  return useMemo(() => {
    const formatter = new Intl.NumberFormat(language);
    return {
      group: (key) =>
        t(`cosmograph.search.groups.${vocabularySlug(key)}`, { defaultValue: humanize(key) }),
      kind: (key) =>
        t(`cosmograph.search.kinds.${vocabularySlug(key)}`, { defaultValue: humanize(key) }),
      period: (raw) =>
        t(`cosmograph.filters.periods.${vocabularySlug(raw)}`, { defaultValue: raw }),
      school: (raw) =>
        t(`cosmograph.filters.schools.${vocabularySlug(raw)}`, { defaultValue: raw }),
      relation: (raw) =>
        t(`cosmograph.path.relations.${vocabularySlug(raw)}`, {
          defaultValue: raw.replace(/_/g, ' '),
        }),
      count: (value) => formatter.format(value),
    };
  }, [t, language]);
}
