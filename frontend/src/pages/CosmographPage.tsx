/**
 * CosmographPage — Knowledge Graph Visualization
 *
 * Placeholder while the visualization is being rebuilt.
 */

import { useTranslation } from 'react-i18next';
import { Network } from 'lucide-react';
import ModeSwitcher from '../components/canvas/ModeSwitcher';
import BottomTabNav from '../components/mobile/BottomTabNav';

export default function CosmographPage() {
  const { t } = useTranslation();

  return (
    <div className="fixed top-12 left-0 right-0 bottom-0 overflow-hidden bg-[#030712]">
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4 max-w-sm text-center p-6">
          <div className="w-16 h-16 rounded-full bg-violet-500/20 flex items-center justify-center border border-violet-500/30">
            <Network className="w-8 h-8 text-violet-400" />
          </div>
          <p className="text-white/80 font-medium">
            {t('graphPage.comingSoon', 'Graph visualization coming soon')}
          </p>
          <p className="text-white/40 text-sm">
            {t('graphPage.rebuildNotice', 'The knowledge graph visualizer is being rebuilt from scratch.')}
          </p>
        </div>
      </div>

      <div className="absolute top-4 right-4 z-30">
        <ModeSwitcher />
      </div>

      <div className="md:hidden">
        <BottomTabNav />
      </div>
    </div>
  );
}
