import { AnimatePresence, motion } from 'framer-motion';
import { Network } from 'lucide-react';
import CosmographView from './CosmographView';
import SourceDetailCard from './SourceDetailCard';
import { cn } from '../../utils/cn';
import type { GraphRAGResponse, SourceCitation } from '../../types';

type RightPanelState = 'idle' | 'loading' | 'graph' | 'source-detail';

interface RightPanelProps {
  state: RightPanelState;
  response: GraphRAGResponse | null;
  allResponses?: GraphRAGResponse[];
  activeSourceIndex: number | null;
  onNodeClick: (nodeId: string) => void;
  onCloseDetail: () => void;
  onPrevSource: () => void;
  onNextSource: () => void;
  onHighlightRef?: (fn: (citationIndex: number) => void) => void;
  className?: string;
}

export default function RightPanel({
  state,
  response,
  allResponses,
  activeSourceIndex,
  onNodeClick,
  onCloseDetail,
  onPrevSource,
  onNextSource,
  onHighlightRef,
  className = '',
}: RightPanelProps) {
  const sources: SourceCitation[] = response?.sources ?? [];
  const activeSource =
    activeSourceIndex !== null && activeSourceIndex < sources.length
      ? sources[activeSourceIndex]
      : null;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const citationTexts = (response as any)?.citationTexts as
    | Record<string, { original: string; originalLanguage: string; translation: string }>
    | undefined;
  const activeCitationText =
    activeSource && citationTexts
      ? (citationTexts[activeSource.nodeLabel] ??
        Object.values(citationTexts)[activeSourceIndex ?? 0] ??
        undefined)
      : undefined;

  return (
    <div className={cn('flex flex-col h-full relative overflow-hidden bg-[#020617] rounded-xl', className)}>
      <AnimatePresence mode="wait">
        {/* IDLE */}
        {state === 'idle' && (
          <motion.div
            key="idle"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="flex-1 flex flex-col items-center justify-center text-center px-8 h-full"
          >
            <div className="space-y-5">
              <div className="mx-auto flex items-center justify-center w-16 h-16 rounded-2xl bg-white/5 border border-white/10">
                <Network className="w-7 h-7 text-white/30" />
              </div>
              <div className="space-y-1.5">
                <p className="text-sm font-medium text-white/50">Knowledge Graph</p>
                <p className="text-xs text-white/30 max-w-[200px] mx-auto leading-relaxed">
                  Ask a question to see the knowledge graph and its connections
                </p>
              </div>
            </div>
          </motion.div>
        )}

        {/* LOADING */}
        {state === 'loading' && (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="flex-1 flex flex-col items-center justify-center gap-4 px-6 h-full"
          >
            {/* Animated radar pulse */}
            <div className="relative w-20 h-20">
              {[0, 1, 2].map((i) => (
                <motion.div
                  key={i}
                  className="absolute inset-0 rounded-full border-2 border-blue-400/40"
                  initial={{ scale: 0.3, opacity: 0.8 }}
                  animate={{ scale: 1.5, opacity: 0 }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    delay: i * 0.6,
                    ease: 'easeOut',
                  }}
                />
              ))}
              <div className="absolute inset-0 flex items-center justify-center">
                <Network className="w-6 h-6 text-blue-400" />
              </div>
            </div>
            <div className="text-center space-y-1">
              <p className="text-sm font-medium text-white/60">Building knowledge graph</p>
              <motion.p
                className="text-xs text-white/30"
                animate={{ opacity: [0.3, 0.8, 0.3] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              >
                Traversing connections...
              </motion.p>
            </div>
          </motion.div>
        )}

        {/* GRAPH */}
        {state === 'graph' && (
          <motion.div
            key="graph"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="flex-1 h-full"
          >
            <CosmographView
              response={response}
              allResponses={allResponses}
              highlightedNodeIndex={null}
              onNodeClick={onNodeClick}
              onHighlightRef={onHighlightRef}
            />
          </motion.div>
        )}

        {/* SOURCE DETAIL */}
        {state === 'source-detail' && (
          <motion.div
            key="source-detail"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="flex flex-col h-full"
          >
            {/* Graph top 40% */}
            <div style={{ flex: '0 0 40%' }} className="relative overflow-hidden">
              <CosmographView
                response={response}
                allResponses={allResponses}
                highlightedNodeIndex={activeSourceIndex}
                onNodeClick={onNodeClick}
                onHighlightRef={onHighlightRef}
                showControls={false}
              />
            </div>

            {/* Source detail card bottom 60% */}
            <div className="flex-1 p-3 overflow-hidden bg-white rounded-t-xl">
              <AnimatePresence mode="wait">
                {activeSource ? (
                  <SourceDetailCard
                    key={activeSource.id}
                    source={activeSource}
                    citationText={activeCitationText}
                    citationIndex={activeSourceIndex!}
                    totalCitations={sources.length}
                    onClose={onCloseDetail}
                    onPrev={onPrevSource}
                    onNext={onNextSource}
                  />
                ) : (
                  <motion.div
                    key="no-source"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex items-center justify-center h-full text-sm text-gray-400"
                  >
                    No source selected
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
