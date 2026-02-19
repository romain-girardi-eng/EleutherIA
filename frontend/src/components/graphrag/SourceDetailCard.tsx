import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { X, ChevronLeft, ChevronRight, ExternalLink } from 'lucide-react';
import { cn } from '../../utils/cn';
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

const NODE_TYPE_STYLES: Record<string, string> = {
  person: 'bg-blue-50 text-blue-700 border-blue-200',
  concept: 'bg-green-50 text-green-700 border-green-200',
  argument: 'bg-purple-50 text-purple-700 border-purple-200',
  work: 'bg-amber-50 text-amber-700 border-amber-200',
  default: 'bg-gray-50 text-gray-700 border-gray-200',
};

function getTypeStyle(type: string) {
  return NODE_TYPE_STYLES[type.toLowerCase()] ?? NODE_TYPE_STYLES.default;
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
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.2, ease: 'easeOut' }}
      className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden flex flex-col h-full"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 shrink-0">
        <div className="flex items-center gap-2 min-w-0">
          <span className="flex items-center justify-center w-6 h-6 rounded-md bg-gray-100 text-xs font-bold text-gray-600">
            {source.id}
          </span>
          <span
            className={cn(
              'inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold border',
              getTypeStyle(source.nodeType),
            )}
          >
            {source.nodeType || 'Source'}
          </span>
          <span className="text-sm font-medium text-gray-800 truncate">{source.nodeLabel}</span>
        </div>
        <button
          onClick={onClose}
          className="ml-2 shrink-0 p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="Close source detail"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 px-4 py-3 space-y-3 text-sm overflow-y-auto">
        {citationText?.original && (
          <div className="space-y-1">
            <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-widest">
              {citationText.originalLanguage === 'greek'
                ? 'Greek'
                : citationText.originalLanguage === 'latin'
                  ? 'Latin'
                  : 'Original'}
            </div>
            <p className="font-serif italic text-gray-700 leading-relaxed text-[13px]">
              {citationText.original}
            </p>
          </div>
        )}
        {citationText?.translation && (
          <div className="space-y-1">
            <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-widest">
              Translation
            </div>
            <p className="text-gray-600 leading-relaxed text-[13px]">{citationText.translation}</p>
          </div>
        )}
        {!citationText?.original && !citationText?.translation && (
          <p className="text-gray-400 italic text-xs">No passage text available for this source.</p>
        )}
        {(source.metadata?.period || source.metadata?.school) && (
          <div className="flex items-center gap-3 pt-1">
            {source.metadata?.period && (
              <span className="text-[10px] text-gray-400 font-medium">
                {source.metadata.period}
              </span>
            )}
            {source.metadata?.school && (
              <span className="text-[10px] text-gray-400 italic">
                {source.metadata.school as string}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between px-4 py-2.5 border-t border-gray-100 bg-gray-50/50 shrink-0">
        <div className="flex items-center gap-1.5">
          <button
            onClick={onPrev}
            disabled={citationIndex <= 0}
            className="p-1.5 rounded-lg hover:bg-gray-200 disabled:opacity-25 transition-colors text-gray-500"
            aria-label="Previous source"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
          </button>
          <span className="text-[10px] font-medium text-gray-400 tabular-nums min-w-[40px] text-center">
            {citationIndex + 1} / {totalCitations}
          </span>
          <button
            onClick={onNext}
            disabled={citationIndex >= totalCitations - 1}
            className="p-1.5 rounded-lg hover:bg-gray-200 disabled:opacity-25 transition-colors text-gray-500"
            aria-label="Next source"
          >
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
        {source.nodeId && !source.nodeId.startsWith('source_') && (
          <button
            onClick={() => navigate(`/node/${source.nodeId}`)}
            className="flex items-center gap-1 text-[10px] font-medium text-blue-600 hover:text-blue-700 transition-colors"
          >
            View in Visualizer
            <ExternalLink className="w-3 h-3" />
          </button>
        )}
      </div>
    </motion.div>
  );
}
