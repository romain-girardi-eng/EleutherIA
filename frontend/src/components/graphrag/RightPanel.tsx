import { AnimatePresence, motion } from 'framer-motion';
import KnowledgeGraphMini from './KnowledgeGraphMini';
import SourceDetailCard from './SourceDetailCard';
import type { GraphRAGResponse, SourceCitation } from '../../types';

type RightPanelState = 'idle' | 'loading' | 'graph' | 'source-detail';

interface RightPanelProps {
  state: RightPanelState;
  response: GraphRAGResponse | null;
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
  activeSourceIndex,
  onNodeClick,
  onCloseDetail,
  onPrevSource,
  onNextSource,
  onHighlightRef,
  className = '',
}: RightPanelProps) {
  const sources: SourceCitation[] = response?.sources ?? [];
  const activeSource = (activeSourceIndex !== null && activeSourceIndex < sources.length)
    ? sources[activeSourceIndex]
    : null;

  const citationTexts = (response as any)?.citationTexts as Record<string, { original: string; originalLanguage: string; translation: string }> | undefined;
  const activeCitationText = (activeSource && citationTexts)
    ? citationTexts[activeSource.nodeLabel] ?? Object.values(citationTexts)[activeSourceIndex ?? 0] ?? undefined
    : undefined;

  return (
    <div className={`flex flex-col h-full relative overflow-hidden ${className}`}>
      <AnimatePresence mode="wait">

        {/* ── IDLE ─────────────────────────────────────────── */}
        {state === 'idle' && (
          <motion.div
            key="idle"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="flex-1 flex flex-col items-center justify-center text-center px-6 h-full"
          >
            <div className="space-y-4">
              <div className="relative w-44 h-44 mx-auto">
                {[0, 1, 2, 3, 4].map(i => (
                  <motion.div
                    key={i}
                    className="absolute rounded-full border-2 border-gray-200"
                    style={{
                      width: 14 + i * 5,
                      height: 14 + i * 5,
                      left: `${18 + i * 13}%`,
                      top: `${15 + (i % 3) * 24}%`,
                    }}
                    animate={{ opacity: [0.3, 0.7, 0.3] }}
                    transition={{ duration: 1.8, repeat: Infinity, delay: i * 0.3 }}
                  />
                ))}
                <svg className="absolute inset-0 w-full h-full opacity-20" viewBox="0 0 200 200">
                  <line x1="40" y1="30" x2="85" y2="70" stroke="#9CA3AF" strokeWidth="1.5" />
                  <line x1="85" y1="70" x2="135" y2="48" stroke="#9CA3AF" strokeWidth="1.5" />
                  <line x1="85" y1="70" x2="105" y2="135" stroke="#9CA3AF" strokeWidth="1.5" />
                  <line x1="135" y1="48" x2="165" y2="105" stroke="#9CA3AF" strokeWidth="1.5" />
                </svg>
              </div>
              <p className="text-sm text-gray-400">Knowledge graph will appear here</p>
            </div>
          </motion.div>
        )}

        {/* ── LOADING ──────────────────────────────────────── */}
        {state === 'loading' && (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="flex-1 flex flex-col items-center justify-center gap-3 px-6 h-full"
          >
            {[0, 1, 2, 3].map(i => (
              <motion.div
                key={i}
                className="w-full h-7 rounded-lg bg-gray-100"
                animate={{ opacity: [0.3, 0.7, 0.3] }}
                transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.15 }}
              />
            ))}
            <div className="flex gap-3 mt-1">
              {[0, 1, 2].map(i => (
                <motion.div
                  key={i}
                  className="w-8 h-8 rounded-full bg-gray-100"
                  animate={{ opacity: [0.3, 0.7, 0.3] }}
                  transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
                />
              ))}
            </div>
          </motion.div>
        )}

        {/* ── GRAPH ────────────────────────────────────────── */}
        {state === 'graph' && (
          <motion.div
            key="graph"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="flex-1 h-full"
          >
            <KnowledgeGraphMini
              response={response}
              activeCitationIndex={null}
              onNodeClick={onNodeClick}
              onHighlightRef={onHighlightRef}
            />
          </motion.div>
        )}

        {/* ── SOURCE DETAIL ─────────────────────────────────── */}
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
              <KnowledgeGraphMini
                response={response}
                activeCitationIndex={activeSourceIndex}
                onNodeClick={onNodeClick}
                onHighlightRef={onHighlightRef}
              />
            </div>

            {/* Source detail card bottom 60% */}
            <div className="flex-1 p-3 overflow-hidden">
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
