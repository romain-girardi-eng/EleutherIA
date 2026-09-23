import { useTranslation } from 'react-i18next';

import type { AtlasNodeMeta } from '../AtlasHelpers';
import KgSearchBar from '../KgSearchBar';

interface ExploreSearchProps {
  readonly nodes: ReadonlyArray<AtlasNodeMeta>;
  readonly onPick: (node: AtlasNodeMeta) => void;
  readonly resultLimit?: number;
}

/** Bottom-docked, thumb-reachable search: results open upwards. */
export default function ExploreSearch({ nodes, onPick, resultLimit = 12 }: ExploreSearchProps) {
  const { t } = useTranslation();
  return (
    <KgSearchBar
      size="sm"
      dropUp
      clearOnPick
      nodes={nodes}
      onPick={onPick}
      resultLimit={resultLimit}
      placeholder={t('cosmograph.explore.searchPlaceholder', 'Jump to a thinker, concept or work…')}
      ariaLabel={t('cosmograph.explore.searchAria', 'Jump to a node')}
      emptyLabel={t('cosmograph.explore.searchEmpty', 'No match. Try a Greek or Latin term, or a surname.')}
      resultsLabel={t('cosmograph.explore.searchResults', 'Search results')}
    />
  );
}
