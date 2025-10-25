import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Network, Brain, BookOpen, CheckCircle, ChevronRight } from 'lucide-react';
import type { ReasoningStep } from '../../types/graphrag';

interface ReasoningPathVisualizerProps {
  query: string;
  steps: ReasoningStep[];
  isActive?: boolean;
  onStepClick?: (stepId: number) => void;
}

const stepIcons = {
  search: Search,
  traverse: Network,
  context: BookOpen,
  synthesis: Brain,
  complete: CheckCircle,
};

const stepColors = {
  search: 'from-blue-500 to-cyan-500',
  traverse: 'from-purple-500 to-pink-500',
  context: 'from-orange-500 to-amber-500',
  synthesis: 'from-green-500 to-emerald-500',
  complete: 'from-gray-500 to-slate-500',
};

export const ReasoningPathVisualizer: React.FC<ReasoningPathVisualizerProps> = ({
  query,
  steps,
  onStepClick,
}) => {

  return (
    <div className="w-full bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-xl shadow-2xl p-6 border border-gray-700">
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
          <Brain className="w-6 h-6 text-emerald-400" />
          GraphRAG Reasoning Path
        </h3>
        <p className="text-gray-400 text-sm italic">"{query}"</p>
      </div>

      {/* Steps Container */}
      <div className="relative">
        {/* Connection Line */}
        <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-blue-500 via-purple-500 to-green-500 opacity-30" />

        {/* Steps */}
        <div className="space-y-4">
          <AnimatePresence>
            {steps.map((step, index) => {
              const Icon = stepIcons[step.type];
              const isActive = step.status === 'active';
              const isComplete = step.status === 'complete';
              const isPending = step.status === 'pending';

              return (
                <motion.div
                  key={step.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ delay: index * 0.1 }}
                  className={`relative flex items-start gap-4 cursor-pointer group ${
                    isPending ? 'opacity-50' : ''
                  }`}
                  onClick={() => onStepClick?.(step.id)}
                >
                  {/* Step Icon */}
                  <div className="relative z-10">
                    <motion.div
                      className={`w-16 h-16 rounded-full bg-gradient-to-br ${
                        stepColors[step.type]
                      } flex items-center justify-center shadow-lg`}
                      animate={
                        isActive
                          ? {
                              scale: [1, 1.1, 1],
                              rotate: [0, 5, -5, 0],
                            }
                          : {}
                      }
                      transition={{
                        duration: 2,
                        repeat: isActive ? Infinity : 0,
                      }}
                    >
                      <Icon className="w-8 h-8 text-white" />
                    </motion.div>

                    {/* Pulse Effect for Active Step */}
                    {isActive && (
                      <motion.div
                        className={`absolute inset-0 rounded-full bg-gradient-to-br ${
                          stepColors[step.type]
                        } opacity-50`}
                        animate={{
                          scale: [1, 1.5, 1],
                          opacity: [0.5, 0, 0.5],
                        }}
                        transition={{
                          duration: 2,
                          repeat: Infinity,
                        }}
                      />
                    )}

                    {/* Checkmark for Complete */}
                    {isComplete && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="absolute -top-1 -right-1 w-6 h-6 bg-green-500 rounded-full flex items-center justify-center border-2 border-gray-900"
                      >
                        <CheckCircle className="w-4 h-4 text-white" />
                      </motion.div>
                    )}
                  </div>

                  {/* Step Content */}
                  <div className="flex-1 bg-gray-800/50 rounded-lg p-4 border border-gray-700 group-hover:border-gray-600 transition-colors">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-lg font-semibold text-white">
                        {step.label}
                      </h4>
                      {isActive && (
                        <motion.div
                          animate={{ opacity: [1, 0.5, 1] }}
                          transition={{ duration: 1.5, repeat: Infinity }}
                          className="text-xs font-medium text-emerald-400 px-2 py-1 bg-emerald-400/10 rounded"
                        >
                          Processing...
                        </motion.div>
                      )}
                      {isComplete && step.duration && (
                        <span className="text-xs text-gray-500">
                          {step.duration}ms
                        </span>
                      )}
                    </div>

                    <p className="text-gray-400 text-sm mb-3">
                      {step.description}
                    </p>

                    {/* Nodes Retrieved */}
                    {step.nodes && step.nodes.length > 0 && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        className="mt-3 pt-3 border-t border-gray-700"
                      >
                        <div className="flex flex-wrap gap-2">
                          {step.nodes.map((node, idx) => (
                            <motion.div
                              key={idx}
                              initial={{ scale: 0 }}
                              animate={{ scale: 1 }}
                              transition={{ delay: idx * 0.05 }}
                              className="px-2 py-1 bg-blue-500/20 border border-blue-500/50 rounded text-xs text-blue-300"
                            >
                              {node}
                            </motion.div>
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </div>

                  {/* Arrow Connector */}
                  {index < steps.length - 1 && (
                    <div className="absolute left-8 -bottom-2 transform -translate-x-1/2">
                      <ChevronRight className="w-4 h-4 text-gray-600 rotate-90" />
                    </div>
                  )}
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mt-6 pt-6 border-t border-gray-700">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-400">Overall Progress</span>
          <span className="text-sm font-medium text-white">
            {Math.round(
              (steps.filter((s) => s.status === 'complete').length /
                steps.length) *
                100
            )}
            %
          </span>
        </div>
        <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-green-500"
            initial={{ width: 0 }}
            animate={{
              width: `${
                (steps.filter((s) => s.status === 'complete').length /
                  steps.length) *
                100
              }%`,
            }}
            transition={{ duration: 0.5 }}
          />
        </div>
      </div>
    </div>
  );
};

export default ReasoningPathVisualizer;
