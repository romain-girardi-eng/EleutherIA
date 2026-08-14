import { useState } from 'react';
import { motion } from 'framer-motion';
import { Network } from 'lucide-react';
import { BottomSheet } from '../../components/ui/BottomSheet';
import RightPanel from '../../components/graphrag/RightPanel';
import type { RightPanelState } from '../../components/graphrag/RightPanel';
import type { GraphRAGResponse } from '../../types';
import type { AgentStep, PassageContext } from '../../types/graphrag';
import type { TokenCost } from '../../components/graphrag/ResearchTimelinePanel';

interface MobileGraphSheetProps {
  rightPanelState: RightPanelState;
  response: GraphRAGResponse | null;
  allResponses?: GraphRAGResponse[];
  activeSourceIndex: number | null;
  passageContext?: PassageContext | null;
  agentSteps?: AgentStep[];
  agentActive?: boolean;
  isStreaming?: boolean;
  streamEnded?: boolean;
  cost?: TokenCost | null;
  onNodeClick: (nodeId: string) => void;
  onSourceSelect?: (sourceIndex: number) => void;
  onCloseDetail: () => void;
  onLoadMorePassages?: (direction: 'up' | 'down') => void;
  onHighlightRef?: (fn: (citationIndex: number) => void) => void;
}

export default function MobileGraphSheet({
  rightPanelState,
  response,
  allResponses,
  activeSourceIndex,
  passageContext,
  agentSteps,
  agentActive,
  isStreaming,
  streamEnded,
  cost,
  onNodeClick,
  onSourceSelect,
  onCloseDetail,
  onLoadMorePassages,
  onHighlightRef,
}: MobileGraphSheetProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (rightPanelState === 'idle') return null;

  return (
    <>
      <motion.button
        className="fixed bottom-[calc(6rem+env(safe-area-inset-bottom))] right-[calc(1rem+env(safe-area-inset-right))] z-50 flex lg:hidden items-center gap-2 min-h-11 rounded-full border border-stone-200/80 bg-white/92 px-4 py-3 text-stone-800 shadow-[0_24px_50px_-34px_rgba(120,53,15,0.45)] backdrop-blur-xl"
        onClick={() => setIsOpen(true)}
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
        aria-label="Open knowledge graph"
        type="button"
      >
        <Network className="h-4 w-4 text-amber-700" />
        <span className="text-sm font-semibold">Answer graph</span>
      </motion.button>

      <BottomSheet
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Selected Answer Graph"
        height="75%"
        showHandle
        dragToClose
      >
        <div className="h-full min-h-[300px] pb-2">
          <RightPanel
            state={rightPanelState}
            response={response}
            allResponses={allResponses}
            activeSourceIndex={activeSourceIndex}
            passageContext={passageContext}
            agentSteps={agentSteps}
            agentActive={agentActive}
            isStreaming={isStreaming}
            streamEnded={streamEnded}
            cost={cost}
            onNodeClick={onNodeClick}
            onSourceSelect={onSourceSelect}
            onCloseDetail={onCloseDetail}
            onLoadMorePassages={onLoadMorePassages}
            onHighlightRef={onHighlightRef}
            className="h-full"
          />
        </div>
      </BottomSheet>
    </>
  );
}
