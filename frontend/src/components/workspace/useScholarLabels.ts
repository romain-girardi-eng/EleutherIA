import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';

import { relationLabel, type AtlasNodeMeta } from '../cosmograph/AtlasHelpers';
import { UNATTACHED_SCHOOL, UNSPECIFIED_PERIOD } from './scholarModel';

const KNOWN_TYPES = new Set(['person', 'scholar', 'concept', 'argument', 'work', 'school', 'passage', 'debate', 'publication']);

export interface ScholarLabels {
  type: (typeKey: string, fallback?: string) => string;
  nodeType: (node: Pick<AtlasNodeMeta, 'typeKey' | 'layer' | 'typeLabel'>) => string;
  period: (period: string) => string;
  school: (school: string) => string;
  relation: (relation: string) => string;
  number: (value: number) => string;
  locale: string;
}

/**
 * Only the system defaults the graph runtime injects (unknown period/school,
 * the type vocabulary) are translated. Period, school and relation values are
 * editorial data and are displayed as recorded in the release.
 */
export function useScholarLabels(): ScholarLabels {
  const { t, i18n } = useTranslation();
  const locale = i18n.language || 'en';
  return useMemo(() => {
    const formatter = new Intl.NumberFormat(locale);
    const type = (typeKey: string, fallback?: string) =>
      KNOWN_TYPES.has(typeKey) ? t(`scholar.types.${typeKey}`) : fallback ?? typeKey;
    return {
      type,
      nodeType: (node) =>
        type(node.layer === 'modern' && node.typeKey === 'person' ? 'scholar' : node.typeKey, node.typeLabel),
      period: (period) => (period === UNSPECIFIED_PERIOD ? t('scholar.values.unspecified') : period),
      school: (school) => (school === UNATTACHED_SCHOOL ? t('scholar.values.unattached') : school),
      relation: (relation) => relationLabel(relation),
      number: (value) => formatter.format(value),
      locale,
    };
  }, [locale, t]);
}
