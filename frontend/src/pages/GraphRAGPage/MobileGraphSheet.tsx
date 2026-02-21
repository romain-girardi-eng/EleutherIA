import { useState } from 'react';
import { motion } from 'framer-motion';
import { BarChart3 } from 'lucide-react';
import { BottomSheet } from '../../components/ui/BottomSheet';
import RightPanel from '../../components/graphrag/RightPanel';
import type { RightPanelState } from '../../components/graphrag/RightPanel';
import type { GraphRAGResponse } from '../../types';

interface MobileGraphSheetProps {
  rightPanelState: RightPanelState;
  response: GraphRAGResponse | null;
  allResponses?: GraphRAGResponse[];
  activeSourceIndex: number | null;
  onNodeClick: (nodeId: string) => void;
  onCloseDetail: () => void;
  onPrevSource: () => void;
  onNextSource: () => void;
  onHighlightRef?: (fn: (citationIndex: number) => void) => void;
}

export default function MobileGraphSheet({
  rightPanelState,
  response,
  allResponses,
  activeSourceIndex,
  onNodeClick,
  onCloseDetail,
  onPrevSource,
  onNextSource,
  onHighlightRef,
}: MobileGraphSheetProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (rightPanelState === 'idle') return null;

  return (
    <>
      <motion.button
        className="fixed bottom-24 right-4 z-50 flex lg:hidden items-center justify-center w-12 h-12 rounded-xl bg-gray-900 text-white shadow-lg"
        onClick={() => setIsOpen(true)}
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
        aria-label="Open knowledge graph"
      >
        <BarChart3 className="w-5 h-5" />
      </motion.button>

      <BottomSheet
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Knowledge Graph"
        height="60%"
        showHandle
        dragToClose
      >
        <div className="h-full min-h-[300px]">
          <RightPanel
            state={rightPanelState}
            response={response}
            allResponses={allResponses}
            activeSourceIndex={activeSourceIndex}
            onNodeClick={onNodeClick}
            onCloseDetail={onCloseDetail}
            onPrevSource={onPrevSource}
            onNextSource={onNextSource}
            onHighlightRef={onHighlightRef}
            className="h-full"
          />
        </div>
      </BottomSheet>
    </>
  );
}
