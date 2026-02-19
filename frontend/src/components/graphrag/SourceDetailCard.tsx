import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import type { SourceCitation } from '../../types';

interface SourceDetailCardProps {
  source: SourceCitation;
  citationText?: { original: string; originalLanguage: string; translation: string };
  citationIndex: number;
  totalCitations: number;
  onClose: () => void;
  onPrev: () => void;
  onNext: () => void;
}

const NODE_TYPE_COLORS: Record<string, string> = {
  person:   'bg-blue-100 text-blue-800 border-blue-200',
  concept:  'bg-green-100 text-green-800 border-green-200',
  argument: 'bg-purple-100 text-purple-800 border-purple-200',
  work:     'bg-amber-100 text-amber-800 border-amber-200',
  default:  'bg-gray-100 text-gray-800 border-gray-200',
};

function getTypeColor(type: string) {
  return NODE_TYPE_COLORS[type.toLowerCase()] ?? NODE_TYPE_COLORS.default;
}

export default function SourceDetailCard({
  source,
  citationText,
  citationIndex,
  totalCitations,
  onClose,
  onPrev,
  onNext,
}: SourceDetailCardProps) {
  const navigate = useNavigate();

  return (
    <motion.div
      initial={{ y: '100%', opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      exit={{ y: '100%', opacity: 0 }}
      transition={{ type: 'spring', damping: 28, stiffness: 280 }}
      className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden flex flex-col h-full"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 shrink-0">
        <div className="flex items-center gap-2 min-w-0">
          <span className="font-bold text-gray-900 text-sm">[{source.id}]</span>
          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${getTypeColor(source.nodeType)}`}>
            {source.nodeType || 'Source'}
          </span>
          <span className="text-sm font-medium text-gray-800 truncate">{source.nodeLabel}</span>
        </div>
        <button
          onClick={onClose}
          className="ml-2 shrink-0 p-1 rounded-full hover:bg-gray-100 text-gray-500 hover:text-gray-700 transition-colors"
          aria-label="Close source detail"
        >
          ✕
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 px-4 py-3 space-y-3 text-sm overflow-y-auto">
        {citationText?.original && (
          <div>
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
              {citationText.originalLanguage === 'greek' ? 'Greek' :
               citationText.originalLanguage === 'latin' ? 'Latin' : 'Original'}
            </div>
            <p className="font-serif italic text-gray-800 leading-relaxed text-sm">
              {citationText.original}
            </p>
          </div>
        )}
        {citationText?.translation && (
          <div>
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Translation</div>
            <p className="text-gray-700 leading-relaxed text-sm">{citationText.translation}</p>
          </div>
        )}
        {!citationText?.original && !citationText?.translation && (
          <p className="text-gray-400 italic text-xs">No passage text available for this source.</p>
        )}
        {source.metadata?.period && (
          <div className="text-xs text-gray-500">Period: {source.metadata.period}</div>
        )}
        {source.metadata?.school && (
          <div className="text-xs text-gray-500">School: {source.metadata.school as string}</div>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between px-4 py-2 border-t border-gray-100 bg-gray-50 shrink-0">
        <div className="flex items-center gap-2">
          <button
            onClick={onPrev}
            disabled={citationIndex <= 0}
            className="px-2 py-1 rounded hover:bg-gray-200 disabled:opacity-30 transition-colors text-gray-600 text-base leading-none"
            aria-label="Previous source"
          >
            ‹
          </button>
          <span className="text-xs text-gray-500">{citationIndex + 1} / {totalCitations}</span>
          <button
            onClick={onNext}
            disabled={citationIndex >= totalCitations - 1}
            className="px-2 py-1 rounded hover:bg-gray-200 disabled:opacity-30 transition-colors text-gray-600 text-base leading-none"
            aria-label="Next source"
          >
            ›
          </button>
        </div>
        {source.nodeId && !source.nodeId.startsWith('source_') && (
          <button
            onClick={() => navigate(`/node/${source.nodeId}`)}
            className="text-xs text-blue-600 hover:text-blue-800 hover:underline transition-colors"
          >
            View in Visualizer →
          </button>
        )}
      </div>
    </motion.div>
  );
}
