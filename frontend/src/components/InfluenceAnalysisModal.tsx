import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, TrendingUp, TrendingDown, Network, GitBranch, School, Clock } from 'lucide-react';
import type { KGNode } from '../types';

export interface Connection {
  id: string;
  label: string;
  relation: string;
  type: string;
  school?: string;
}

export interface InfluenceData {
  incoming: Connection[];
  outgoing: Connection[];
}

interface InfluenceAnalysisModalProps {
  isOpen: boolean;
  node: KGNode | null;
  data: InfluenceData | null;
  onClose: () => void;
  onNavigateToNode?: (nodeId: string) => void;
}

export default function InfluenceAnalysisModal({
  isOpen,
  node,
  data,
  onClose,
  onNavigateToNode,
}: InfluenceAnalysisModalProps) {
  const [activeTab, setActiveTab] = useState<'incoming' | 'outgoing' | 'overview'>('overview');
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  // Debug logging
  useEffect(() => {
    console.log('🎭 [Modal] Props changed:', {
      isOpen,
      hasNode: !!node,
      nodeLabel: node?.label,
      hasData: !!data,
      incomingCount: data?.incoming?.length,
      outgoingCount: data?.outgoing?.length
    });
  }, [isOpen, node, data]);

  // Close on escape key
  useEffect(() => {
    if (!isOpen) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen || !node || !data) {
    return null;
  }

  console.log('🎭 [Modal] Rendering modal for node:', node.label);

  // Calculate statistics (after null checks)
  const incomingCount = data.incoming?.length || 0;
  const outgoingCount = data.outgoing?.length || 0;
  const totalConnections = incomingCount + outgoingCount;

  // Count by relationship type
  const relationTypes: Record<string, { incoming: number; outgoing: number }> = {};
  data.incoming?.forEach((conn) => {
    const rel = conn.relation || 'unknown';
    if (!relationTypes[rel]) relationTypes[rel] = { incoming: 0, outgoing: 0 };
    relationTypes[rel].incoming++;
  });
  data.outgoing?.forEach((conn) => {
    const rel = conn.relation || 'unknown';
    if (!relationTypes[rel]) relationTypes[rel] = { incoming: 0, outgoing: 0 };
    relationTypes[rel].outgoing++;
  });

  // Count by school
  const schoolCounts: Record<string, number> = {};
  [...(data.incoming || []), ...(data.outgoing || [])].forEach((conn) => {
    const school = conn.school || 'Unknown';
    schoolCounts[school] = (schoolCounts[school] || 0) + 1;
  });

  const influenceScore = totalConnections > 0
    ? Math.min(100, Math.round((outgoingCount / totalConnections) * 100))
    : 50;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[2000]"
            style={{ position: 'fixed' }}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[90vw] max-w-4xl max-h-[85vh] bg-white rounded-2xl shadow-2xl overflow-hidden z-[2001]"
            style={{ position: 'fixed' }}
          >
            {/* Header with gradient */}
            <div className="relative bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 px-8 py-6 text-white">
              {/* Animated background pattern */}
              <div className="absolute inset-0 opacity-10">
                <div className="absolute inset-0" style={{
                  backgroundImage: 'radial-gradient(circle at 2px 2px, white 1px, transparent 0)',
                  backgroundSize: '32px 32px'
                }} />
              </div>

              <button
                onClick={onClose}
                className="absolute top-4 right-4 p-2 rounded-full hover:bg-white/20 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>

              <div className="relative">
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                >
                  <h2 className="text-3xl font-bold mb-2">Influence Analysis</h2>
                  <p className="text-lg opacity-90">{node.label}</p>
                </motion.div>

                {/* Metadata badges */}
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="flex gap-2 mt-4 flex-wrap"
                >
                  {node.type && (
                    <span className="px-3 py-1 rounded-full bg-white/20 backdrop-blur-lg text-sm font-medium border border-white/30">
                      {node.type}
                    </span>
                  )}
                  {node.school && node.school !== 'Unknown' && (
                    <span className="px-3 py-1 rounded-full bg-white/20 backdrop-blur-lg text-sm font-medium border border-white/30 flex items-center gap-1">
                      <School className="w-3 h-3" />
                      {node.school}
                    </span>
                  )}
                  {node.period && (
                    <span className="px-3 py-1 rounded-full bg-white/20 backdrop-blur-lg text-sm font-medium border border-white/30 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {node.period}
                    </span>
                  )}
                </motion.div>
              </div>
            </div>

            {/* Stats Bar */}
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="grid grid-cols-3 gap-4 px-8 py-6 bg-gradient-to-b from-gray-50 to-white border-b border-gray-200"
            >
              {/* Total Connections */}
              <div className="text-center">
                <div className="flex items-center justify-center mb-2">
                  <Network className="w-5 h-5 text-purple-600" />
                </div>
                <div className="text-3xl font-bold text-gray-900">{totalConnections}</div>
                <div className="text-sm text-gray-600 mt-1">Total Connections</div>
              </div>

              {/* Incoming */}
              <div className="text-center">
                <div className="flex items-center justify-center mb-2">
                  <TrendingDown className="w-5 h-5 text-blue-600" />
                </div>
                <div className="text-3xl font-bold text-blue-600">{incomingCount}</div>
                <div className="text-sm text-gray-600 mt-1">Influenced By</div>
              </div>

              {/* Outgoing */}
              <div className="text-center">
                <div className="flex items-center justify-center mb-2">
                  <TrendingUp className="w-5 h-5 text-emerald-600" />
                </div>
                <div className="text-3xl font-bold text-emerald-600">{outgoingCount}</div>
                <div className="text-sm text-gray-600 mt-1">Influences</div>
              </div>
            </motion.div>

            {/* Influence Score Gauge */}
            {totalConnections > 0 && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.4 }}
                className="px-8 py-4 bg-white border-b border-gray-200"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Influence Direction</span>
                  <span className="text-sm text-gray-600">
                    {influenceScore}% outgoing
                  </span>
                </div>
                <div className="relative h-3 bg-gray-200 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${influenceScore}%` }}
                    transition={{ delay: 0.5, duration: 1, ease: 'easeOut' }}
                    className="absolute left-0 top-0 h-full bg-gradient-to-r from-blue-500 via-purple-500 to-emerald-500 rounded-full"
                  />
                </div>
                <div className="flex justify-between mt-1 text-xs text-gray-500">
                  <span>← Receives influence</span>
                  <span>Exerts influence →</span>
                </div>
              </motion.div>
            )}

            {/* Tabs */}
            <div className="flex border-b border-gray-200 px-8 bg-white sticky top-0 z-10">
              {(['overview', 'incoming', 'outgoing'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-6 py-3 font-medium transition-all relative ${
                    activeTab === tab
                      ? 'text-purple-600'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                  {activeTab === tab && (
                    <motion.div
                      layoutId="activeTab"
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-purple-600"
                      transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                    />
                  )}
                </button>
              ))}
            </div>

            {/* Content */}
            <div className="px-8 py-6 overflow-y-auto max-h-96">
              <AnimatePresence mode="wait">
                {/* Overview Tab */}
                {activeTab === 'overview' && (
                  <motion.div
                    key="overview"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    className="space-y-6"
                  >
                    {/* Relationship Types */}
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                        <GitBranch className="w-5 h-5 text-purple-600" />
                        Relationship Types
                      </h3>
                      <div className="space-y-3">
                        {Object.entries(relationTypes)
                          .sort(([, a], [, b]) => (b.incoming + b.outgoing) - (a.incoming + a.outgoing))
                          .map(([type, counts], index) => {
                            const total = counts.incoming + counts.outgoing;
                            const incomingPercent = (counts.incoming / total) * 100;
                            const outgoingPercent = (counts.outgoing / total) * 100;

                            return (
                              <motion.div
                                key={type}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.05 }}
                                className="bg-gradient-to-r from-gray-50 to-white p-4 rounded-xl border border-gray-200 hover:border-purple-300 transition-all"
                              >
                                <div className="flex items-center justify-between mb-2">
                                  <span className="font-medium text-gray-900">{type}</span>
                                  <span className="text-sm text-gray-600">{total} total</span>
                                </div>
                                <div className="flex gap-2 text-xs text-gray-600 mb-2">
                                  <span className="text-blue-600">← {counts.incoming}</span>
                                  <span className="text-emerald-600">{counts.outgoing} →</span>
                                </div>
                                <div className="flex h-2 rounded-full overflow-hidden bg-gray-200">
                                  <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: `${incomingPercent}%` }}
                                    transition={{ delay: 0.3 + index * 0.05, duration: 0.6 }}
                                    className="bg-blue-500"
                                  />
                                  <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: `${outgoingPercent}%` }}
                                    transition={{ delay: 0.3 + index * 0.05, duration: 0.6 }}
                                    className="bg-emerald-500"
                                  />
                                </div>
                              </motion.div>
                            );
                          })}
                      </div>
                    </div>

                    {/* Schools Distribution */}
                    {Object.keys(schoolCounts).length > 1 && (
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                          <School className="w-5 h-5 text-purple-600" />
                          Philosophical Schools
                        </h3>
                        <div className="grid grid-cols-2 gap-3">
                          {Object.entries(schoolCounts)
                            .sort(([, a], [, b]) => b - a)
                            .map(([school, count], index) => (
                              <motion.div
                                key={school}
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                                transition={{ delay: index * 0.05 }}
                                className="bg-gradient-to-br from-indigo-50 to-purple-50 p-4 rounded-xl border border-indigo-200"
                              >
                                <div className="text-2xl font-bold text-indigo-900">{count}</div>
                                <div className="text-sm text-indigo-700 mt-1">{school}</div>
                              </motion.div>
                            ))}
                        </div>
                      </div>
                    )}
                  </motion.div>
                )}

                {/* Incoming Tab */}
                {activeTab === 'incoming' && (
                  <motion.div
                    key="incoming"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    className="space-y-3"
                  >
                    <p className="text-sm text-gray-600 mb-4">
                      Nodes that influence <strong>{node.label}</strong>
                    </p>
                    {data.incoming?.length === 0 ? (
                      <div className="text-center py-12 text-gray-500">
                        <TrendingDown className="w-12 h-12 mx-auto mb-3 opacity-30" />
                        <p>No incoming influences found</p>
                      </div>
                    ) : (
                      data.incoming?.map((conn, index) => (
                        <motion.button
                          key={conn.id}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.03 }}
                          onClick={() => onNavigateToNode?.(conn.id)}
                          onMouseEnter={() => setHoveredNode(conn.id)}
                          onMouseLeave={() => setHoveredNode(null)}
                          className={`w-full text-left p-4 rounded-xl border-2 transition-all ${
                            hoveredNode === conn.id
                              ? 'border-blue-500 bg-blue-50 shadow-lg scale-[1.02]'
                              : 'border-gray-200 bg-white hover:border-blue-300'
                          }`}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="font-semibold text-gray-900">{conn.label}</div>
                              <div className="text-sm text-blue-600 mt-1">
                                → {conn.relation}
                              </div>
                            </div>
                            <div className="flex flex-col items-end gap-1">
                              <span className="text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-700">
                                {conn.type}
                              </span>
                              {conn.school && conn.school !== 'Unknown' && (
                                <span className="text-xs px-2 py-1 rounded-full bg-indigo-100 text-indigo-700">
                                  {conn.school}
                                </span>
                              )}
                            </div>
                          </div>
                        </motion.button>
                      ))
                    )}
                  </motion.div>
                )}

                {/* Outgoing Tab */}
                {activeTab === 'outgoing' && (
                  <motion.div
                    key="outgoing"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    className="space-y-3"
                  >
                    <p className="text-sm text-gray-600 mb-4">
                      Nodes influenced by <strong>{node.label}</strong>
                    </p>
                    {data.outgoing?.length === 0 ? (
                      <div className="text-center py-12 text-gray-500">
                        <TrendingUp className="w-12 h-12 mx-auto mb-3 opacity-30" />
                        <p>No outgoing influences found</p>
                      </div>
                    ) : (
                      data.outgoing?.map((conn, index) => (
                        <motion.button
                          key={conn.id}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.03 }}
                          onClick={() => onNavigateToNode?.(conn.id)}
                          onMouseEnter={() => setHoveredNode(conn.id)}
                          onMouseLeave={() => setHoveredNode(null)}
                          className={`w-full text-left p-4 rounded-xl border-2 transition-all ${
                            hoveredNode === conn.id
                              ? 'border-emerald-500 bg-emerald-50 shadow-lg scale-[1.02]'
                              : 'border-gray-200 bg-white hover:border-emerald-300'
                          }`}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="font-semibold text-gray-900">{conn.label}</div>
                              <div className="text-sm text-emerald-600 mt-1">
                                {conn.relation} →
                              </div>
                            </div>
                            <div className="flex flex-col items-end gap-1">
                              <span className="text-xs px-2 py-1 rounded-full bg-emerald-100 text-emerald-700">
                                {conn.type}
                              </span>
                              {conn.school && conn.school !== 'Unknown' && (
                                <span className="text-xs px-2 py-1 rounded-full bg-indigo-100 text-indigo-700">
                                  {conn.school}
                                </span>
                              )}
                            </div>
                          </div>
                        </motion.button>
                      ))
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Footer */}
            <div className="px-8 py-4 bg-gray-50 border-t border-gray-200 flex justify-between items-center">
              <p className="text-xs text-gray-500">
                Click on any connection to navigate to that node
              </p>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-medium hover:from-indigo-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl"
              >
                Close
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
