import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import type { PanInfo } from 'framer-motion';
import {
  X,
  ExternalLink,
  BookOpen,
  User,
  Lightbulb,
  Calendar,
  School,
  ArrowRight,
  Share2,
} from 'lucide-react';

interface NodeData {
  id: string;
  label: string;
  type?: string;
  description?: string;
  period?: string;
  school?: string;
  metadata?: Record<string, unknown>;
  sources?: Array<{
    citation: string;
    cts_urn?: string;
    url?: string;
  }>;
  edges?: Array<{
    target_id: string;
    target_label: string;
    relationship: string;
  }>;
}

interface NodeDetailSheetProps {
  node: NodeData | null;
  onClose: () => void;
  onNodeClick?: (nodeId: string) => void;
}

export const NodeDetailSheet: React.FC<NodeDetailSheetProps> = ({
  node,
  onClose,
  onNodeClick,
}) => {
  const { t } = useTranslation();
  const handleDragEnd = (_event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    // Close if dragged down significantly
    if (info.offset.y > 100 || info.velocity.y > 500) {
      onClose();
    }
  };

  const getTypeIcon = (type?: string) => {
    switch (type?.toLowerCase()) {
      case 'person':
        return <User className="h-5 w-5" />;
      case 'concept':
        return <Lightbulb className="h-5 w-5" />;
      case 'text':
        return <BookOpen className="h-5 w-5" />;
      default:
        return <Lightbulb className="h-5 w-5" />;
    }
  };

  const getTypeColor = (type?: string) => {
    switch (type?.toLowerCase()) {
      case 'person':
        return 'bg-blue-500';
      case 'concept':
        return 'bg-purple-500';
      case 'text':
        return 'bg-green-500';
      default:
        return 'bg-gray-500';
    }
  };

  const handleShare = async () => {
    if (node && typeof navigator.share === 'function') {
      try {
        await navigator.share({
          title: node.label,
          text: node.description || `Learn about ${node.label} in the EleutherIA knowledge graph`,
          url: `${window.location.origin}/visualizer?node=${node.id}`,
        });
      } catch (err) {
        console.log('Share cancelled or failed:', err);
      }
    }
  };

  return (
    <AnimatePresence>
      {node && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 z-40"
            aria-hidden="true"
          />

          {/* Sheet */}
          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            drag="y"
            dragConstraints={{ top: 0 }}
            dragElastic={0.2}
            onDragEnd={handleDragEnd}
            className="fixed bottom-0 left-0 right-0 z-50 bg-slate-900 rounded-t-3xl shadow-2xl max-h-[85vh] overflow-hidden"
            role="dialog"
            aria-modal="true"
            aria-labelledby="node-detail-title"
          >
            {/* Drag Handle */}
            <div className="flex justify-center pt-3 pb-2">
              <div className="w-12 h-1.5 bg-slate-600 rounded-full" />
            </div>

            {/* Header */}
            <div className="px-6 pb-4 flex items-start justify-between">
              <div className="flex items-start gap-3 flex-1">
                <div className={`p-2 rounded-lg ${getTypeColor(node.type)} text-white`}>
                  {getTypeIcon(node.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <h2
                    id="node-detail-title"
                    className="text-xl font-semibold text-white truncate"
                  >
                    {node.label}
                  </h2>
                  {node.type && (
                    <span className="text-sm text-slate-400 capitalize">{node.type}</span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                {typeof navigator.share === 'function' && (
                  <button
                    onClick={handleShare}
                    className="p-2 rounded-full hover:bg-slate-800 transition-colors"
                    aria-label={t('graphUi.nodeSheet.share')}
                  >
                    <Share2 className="h-5 w-5 text-slate-400" />
                  </button>
                )}
                <button
                  onClick={onClose}
                  className="p-2 rounded-full hover:bg-slate-800 transition-colors"
                  aria-label={t('graphUi.nodeSheet.close')}
                >
                  <X className="h-5 w-5 text-slate-400" />
                </button>
              </div>
            </div>

            {/* Scrollable Content */}
            <div className="overflow-y-auto max-h-[calc(85vh-100px)] px-6 pb-6">
              {/* Metadata Pills */}
              {(node.period || node.school) && (
                <div className="flex flex-wrap gap-2 mb-4">
                  {node.period && (
                    <span className="inline-flex items-center gap-1 px-3 py-1 bg-slate-800 rounded-full text-xs text-slate-300">
                      <Calendar className="h-3 w-3" />
                      {node.period}
                    </span>
                  )}
                  {node.school && (
                    <span className="inline-flex items-center gap-1 px-3 py-1 bg-slate-800 rounded-full text-xs text-slate-300">
                      <School className="h-3 w-3" />
                      {node.school}
                    </span>
                  )}
                </div>
              )}

              {/* Description */}
              {node.description && (
                <div className="mb-6">
                  <h3 className="text-sm font-medium text-slate-400 mb-2">{t('graphUi.nodeSheet.description')}</h3>
                  <p className="text-slate-200 text-sm leading-relaxed">{node.description}</p>
                </div>
              )}

              {/* Sources */}
              {node.sources && node.sources.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-sm font-medium text-slate-400 mb-2">
                    {t('graphUi.nodeSheet.sources', { count: node.sources.length })}
                  </h3>
                  <div className="space-y-2">
                    {node.sources.slice(0, 5).map((source, idx) => (
                      <div
                        key={idx}
                        className="bg-slate-800 rounded-lg p-3 text-sm text-slate-300"
                      >
                        <p className="leading-relaxed">{source.citation}</p>
                        {source.cts_urn && (
                          <p className="text-xs text-slate-500 mt-1 font-mono">
                            {source.cts_urn}
                          </p>
                        )}
                        {source.url && (
                          <a
                            href={source.url}
                            target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-blue-400 text-xs mt-2 hover:underline"
                        >
                            {t('graphUi.nodeSheet.viewSource')} <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>
                    ))}
                    {node.sources.length > 5 && (
                      <p className="text-xs text-slate-500">
                        {t('graphUi.nodeSheet.moreSources', { count: node.sources.length - 5 })}
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Related Nodes */}
              {node.edges && node.edges.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-slate-400 mb-2">
                    {t('graphUi.nodeSheet.relatedConcepts', { count: node.edges.length })}
                  </h3>
                  <div className="space-y-2">
                    {node.edges.slice(0, 8).map((edge, idx) => (
                      <button
                        key={idx}
                        onClick={() => onNodeClick?.(edge.target_id)}
                        className="w-full flex items-center justify-between bg-slate-800 rounded-lg p-3 hover:bg-slate-700 transition-colors text-left"
                        aria-label={t('graphUi.nodeSheet.navigateTo', { label: edge.target_label })}
                      >
                        <div>
                          <p className="text-sm text-white font-medium">{edge.target_label}</p>
                          <p className="text-xs text-slate-400 capitalize">
                            {edge.relationship.replace(/_/g, ' ')}
                          </p>
                        </div>
                        <ArrowRight className="h-4 w-4 text-slate-400" />
                      </button>
                    ))}
                    {node.edges.length > 8 && (
                      <p className="text-xs text-slate-500">
                        {t('graphUi.nodeSheet.moreConnections', { count: node.edges.length - 8 })}
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
