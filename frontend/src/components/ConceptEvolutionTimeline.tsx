import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Clock, BookOpen, User, Languages, TrendingUp, Sparkles } from 'lucide-react';

// Inline type definition to avoid module caching issues
interface ConceptEvolution {
  conceptId: string;
  conceptLabel: string;
  timeline: Array<{
    period: string;
    dateRange: string;
    formulation: string;
    author?: string;
    work?: string;
    greekTerm?: string;
    latinTerm?: string;
    significance: string;
  }>;
}

interface ConceptEvolutionTimelineProps {
  evolution: ConceptEvolution;
  className?: string;
}

export const ConceptEvolutionTimeline: React.FC<ConceptEvolutionTimelineProps> = ({
  evolution,
  className = ''
}) => {
  const [selectedPeriod, setSelectedPeriod] = useState<number | null>(null);
  const [hoveredPeriod, setHoveredPeriod] = useState<number | null>(null);

  // Calculate timeline positions
  const sortedTimeline = [...evolution.timeline].sort((a, b) => {
    // Extract start year from dateRange (e.g., "4th c. BCE" -> -400)
    const getYear = (range: string): number => {
      if (range.includes('BCE')) {
        const match = range.match(/(\d+)(st|nd|rd|th) c\. BCE/);
        if (match) return -parseInt(match[1]) * 100;
      } else if (range.includes('CE')) {
        const match = range.match(/(\d+)(st|nd|rd|th) c\. CE/);
        if (match) return parseInt(match[1]) * 100;
      }
      return 0;
    };
    return getYear(a.dateRange) - getYear(b.dateRange);
  });

  return (
    <div className={`${className}`}>
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 text-white p-6 rounded-t-2xl">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-white/20 rounded-xl">
            <TrendingUp className="w-8 h-8" />
          </div>
          <div className="flex-1">
            <h2 className="text-2xl font-bold mb-2">Concept Evolution</h2>
            <p className="text-white/90 text-xl font-semibold">
              {evolution.conceptLabel}
            </p>
            <p className="text-white/80 text-sm mt-2">
              Trace how this concept developed across {sortedTimeline.length} periods spanning{' '}
              {sortedTimeline[0]?.dateRange} to {sortedTimeline[sortedTimeline.length - 1]?.dateRange}
            </p>
          </div>
        </div>
      </div>

      {/* Timeline Visualization */}
      <div className="bg-white p-6 md:p-8 rounded-b-2xl shadow-xl">
        <div className="relative">
          {/* Vertical Timeline Line */}
          <div className="absolute left-8 md:left-12 top-0 bottom-0 w-1 bg-gradient-to-b from-primary-300 via-primary-400 to-primary-500" />

          {/* Timeline Entries */}
          <div className="space-y-8">
            {sortedTimeline.map((entry, idx) => {
              const isSelected = selectedPeriod === idx;
              const isHovered = hoveredPeriod === idx;
              const isActive = isSelected || isHovered;

              return (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, x: -50 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.1, duration: 0.5 }}
                  className="relative"
                  onMouseEnter={() => setHoveredPeriod(idx)}
                  onMouseLeave={() => setHoveredPeriod(null)}
                >
                  {/* Timeline Dot */}
                  <motion.div
                    className={`absolute left-6 md:left-10 w-6 h-6 rounded-full border-4 ${
                      isActive
                        ? 'bg-primary-600 border-primary-200 scale-125'
                        : 'bg-white border-primary-400'
                    } transition-all duration-300 shadow-lg z-10`}
                    animate={{
                      scale: isActive ? 1.25 : 1
                    }}
                  />

                  {/* Content Card */}
                  <motion.div
                    className={`ml-16 md:ml-24 cursor-pointer transition-all duration-300 ${
                      isActive ? 'scale-105' : ''
                    }`}
                    onClick={() => setSelectedPeriod(isSelected ? null : idx)}
                  >
                    <div
                      className={`rounded-xl border-2 p-5 ${
                        isActive
                          ? 'bg-gradient-to-br from-primary-50 to-gray-50 border-primary-400 shadow-lg'
                          : 'bg-white border-gray-200 hover:border-primary-300 shadow-md hover:shadow-lg'
                      }`}
                    >
                      {/* Period Header */}
                      <div className="flex flex-wrap items-center gap-3 mb-3">
                        <div className="flex items-center gap-2 px-3 py-1 bg-primary-600 text-white rounded-full text-sm font-semibold">
                          <Clock className="w-4 h-4" />
                          {entry.dateRange}
                        </div>
                        <div className="px-3 py-1 bg-gray-100 text-gray-900 rounded-full text-sm font-semibold">
                          {entry.period}
                        </div>
                      </div>

                      {/* Main Formulation */}
                      <div className="mb-4">
                        <h3 className="text-lg font-bold text-gray-900 mb-2">Formulation:</h3>
                        <p className="text-gray-800 leading-relaxed italic text-lg">
                          "{entry.formulation}"
                        </p>
                      </div>

                      {/* Author & Work */}
                      {(entry.author || entry.work) && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
                          {entry.author && (
                            <div className="flex items-center gap-2 text-sm">
                              <User className="w-4 h-4 text-primary-600" />
                              <span className="font-medium text-gray-700">Author:</span>
                              <span className="text-gray-900 font-semibold">{entry.author}</span>
                            </div>
                          )}
                          {entry.work && (
                            <div className="flex items-center gap-2 text-sm">
                              <BookOpen className="w-4 h-4 text-primary-600" />
                              <span className="font-medium text-gray-700">Work:</span>
                              <span className="text-gray-900 italic">{entry.work}</span>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Greek/Latin Terms */}
                      {(entry.greekTerm || entry.latinTerm) && (
                        <div className="flex flex-wrap gap-3 mb-4">
                          {entry.greekTerm && (
                            <div className="flex items-center gap-2 px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg">
                              <Languages className="w-4 h-4 text-slate-600" />
                              <div className="text-sm">
                                <span className="font-medium text-gray-700">Greek:</span>{' '}
                                <span className="font-semibold text-slate-900">{entry.greekTerm}</span>
                              </div>
                            </div>
                          )}
                          {entry.latinTerm && (
                            <div className="flex items-center gap-2 px-4 py-2 bg-stone-50 border border-stone-200 rounded-lg">
                              <Languages className="w-4 h-4 text-stone-600" />
                              <div className="text-sm">
                                <span className="font-medium text-gray-700">Latin:</span>{' '}
                                <span className="font-semibold text-stone-900">{entry.latinTerm}</span>
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Significance - Expandable */}
                      <AnimatePresence>
                        {(isSelected || isHovered) && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            transition={{ duration: 0.3 }}
                            className="pt-4 border-t border-primary-200"
                          >
                            <div className="flex items-start gap-2">
                              <Sparkles className="w-5 h-5 text-primary-600 flex-shrink-0 mt-1" />
                              <div>
                                <h4 className="font-bold text-primary-900 mb-2">Historical Significance:</h4>
                                <p className="text-gray-700 leading-relaxed">{entry.significance}</p>
                              </div>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>

                      {/* Click hint */}
                      {!isSelected && (
                        <p className="text-xs text-gray-500 mt-3 italic">
                          Click to see historical significance
                        </p>
                      )}
                    </div>
                  </motion.div>

                  {/* Connection Arrow to Next */}
                  {idx < sortedTimeline.length - 1 && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: idx * 0.1 + 0.3 }}
                      className="absolute left-7 md:left-11 top-full h-8 w-0.5 bg-primary-300 z-0"
                    />
                  )}
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Summary Stats */}
        <div className="mt-8 p-6 bg-gradient-to-r from-primary-50 to-gray-50 border-2 border-primary-200 rounded-xl">
          <h3 className="font-bold text-primary-900 mb-4 text-lg">Evolution Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white p-4 rounded-lg border border-primary-200">
              <div className="text-3xl font-bold text-primary-600 mb-1">
                {sortedTimeline.length}
              </div>
              <div className="text-sm text-gray-700">Stages of Evolution</div>
            </div>
            <div className="bg-white p-4 rounded-lg border border-primary-200">
              <div className="text-3xl font-bold text-primary-600 mb-1">
                {sortedTimeline.filter(e => e.author).length}
              </div>
              <div className="text-sm text-gray-700">Key Thinkers</div>
            </div>
            <div className="bg-white p-4 rounded-lg border border-primary-200">
              <div className="text-3xl font-bold text-primary-600 mb-1">
                {new Set([...sortedTimeline.map(e => e.greekTerm), ...sortedTimeline.map(e => e.latinTerm)].filter(Boolean)).size}
              </div>
              <div className="text-sm text-gray-700">Linguistic Forms</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConceptEvolutionTimeline;
