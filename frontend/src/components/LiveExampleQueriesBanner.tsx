import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, ArrowRight } from 'lucide-react';

interface LiveExampleQueriesBannerProps {
  onQueryClick?: (query: string) => void;
  className?: string;
}

const EXAMPLE_QUERIES = [
  {
    query: "What is Aristotle's concept of voluntary action?",
    category: 'Foundational Concepts',
    color: 'from-blue-500 to-indigo-600'
  },
  {
    query: "How did the Stoics reconcile fate with moral responsibility?",
    category: 'Philosophical Debates',
    color: 'from-purple-500 to-pink-600'
  },
  {
    query: "What arguments did Carneades use against Stoic determinism?",
    category: 'Critical Analysis',
    color: 'from-emerald-500 to-teal-600'
  },
  {
    query: "How does Augustine's view of grace relate to free will?",
    category: 'Theological Perspectives',
    color: 'from-amber-500 to-orange-600'
  },
  {
    query: "How did 'eph hemin' evolve from Aristotle to the Stoics?",
    category: 'Conceptual Evolution',
    color: 'from-rose-500 to-red-600'
  },
  {
    query: "Compare Epicurean and Stoic views on freedom and necessity",
    category: 'Comparative Analysis',
    color: 'from-cyan-500 to-blue-600'
  }
];

export const LiveExampleQueriesBanner: React.FC<LiveExampleQueriesBannerProps> = ({
  onQueryClick,
  className = ''
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    if (isPaused) return;

    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % EXAMPLE_QUERIES.length);
    }, 5000); // Change every 5 seconds

    return () => clearInterval(interval);
  }, [isPaused]);

  const currentQuery = EXAMPLE_QUERIES[currentIndex];

  return (
    <div className={`${className}`}>
      <div
        className="relative overflow-hidden rounded-2xl shadow-xl cursor-pointer group"
        onMouseEnter={() => setIsPaused(true)}
        onMouseLeave={() => setIsPaused(false)}
        onClick={() => onQueryClick?.(currentQuery.query)}
      >
        {/* Animated Background */}
        <motion.div
          key={currentIndex}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.5 }}
          className={`absolute inset-0 bg-gradient-to-r ${currentQuery.color}`}
        />

        {/* Sparkle Effect */}
        <div className="absolute inset-0 opacity-20">
          <motion.div
            animate={{
              backgroundPosition: ['0% 0%', '100% 100%'],
            }}
            transition={{
              duration: 20,
              repeat: Infinity,
              ease: 'linear'
            }}
            className="absolute inset-0"
            style={{
              backgroundImage: 'radial-gradient(circle, white 1px, transparent 1px)',
              backgroundSize: '50px 50px'
            }}
          />
        </div>

        {/* Content */}
        <div className="relative p-6 md:p-8">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              {/* Header */}
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-5 h-5 text-white" />
                <span className="text-white/90 font-semibold text-sm uppercase tracking-wide">
                  Try This Question
                </span>
              </div>

              {/* Category Badge */}
              <AnimatePresence mode="wait">
                <motion.div
                  key={`category-${currentIndex}`}
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  transition={{ duration: 0.3 }}
                  className="inline-block px-3 py-1 bg-white/20 backdrop-blur-sm border border-white/30 rounded-full text-white text-xs font-semibold mb-3"
                >
                  {currentQuery.category}
                </motion.div>
              </AnimatePresence>

              {/* Query Text */}
              <AnimatePresence mode="wait">
                <motion.p
                  key={`query-${currentIndex}`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.5 }}
                  className="text-white text-xl md:text-2xl font-bold leading-relaxed italic"
                >
                  "{currentQuery.query}"
                </motion.p>
              </AnimatePresence>

              {/* CTA */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="mt-4 flex items-center gap-2 text-white/90 group-hover:text-white transition-colors"
              >
                <span className="text-sm font-semibold">Click to ask this question</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </motion.div>
            </div>

            {/* Index Indicator */}
            <div className="hidden md:flex flex-col gap-2">
              <div className="text-white/70 text-sm font-semibold mb-1">
                {currentIndex + 1}/{EXAMPLE_QUERIES.length}
              </div>
              {EXAMPLE_QUERIES.map((_, idx) => (
                <button
                  key={idx}
                  onClick={(e) => {
                    e.stopPropagation();
                    setCurrentIndex(idx);
                  }}
                  className={`w-2 h-2 rounded-full transition-all ${
                    idx === currentIndex
                      ? 'bg-white w-8'
                      : 'bg-white/40 hover:bg-white/60'
                  }`}
                  aria-label={`Go to query ${idx + 1}`}
                />
              ))}
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mt-6 h-1 bg-white/20 rounded-full overflow-hidden">
            <motion.div
              key={`progress-${currentIndex}`}
              initial={{ width: '0%' }}
              animate={{ width: isPaused ? '100%' : '100%' }}
              transition={{
                duration: isPaused ? 0 : 5,
                ease: 'linear'
              }}
              className="h-full bg-white rounded-full"
            />
          </div>
        </div>

        {/* Hover Overlay */}
        <motion.div
          className="absolute inset-0 bg-white/0 group-hover:bg-white/10 transition-colors pointer-events-none"
        />
      </div>

      {/* Navigation Dots - Mobile */}
      <div className="flex md:hidden justify-center gap-2 mt-4">
        {EXAMPLE_QUERIES.map((_, idx) => (
          <button
            key={idx}
            onClick={() => setCurrentIndex(idx)}
            className={`w-2 h-2 rounded-full transition-all ${
              idx === currentIndex
                ? 'bg-primary-600 w-8'
                : 'bg-gray-300 hover:bg-gray-400'
            }`}
            aria-label={`Go to query ${idx + 1}`}
          />
        ))}
      </div>
    </div>
  );
};

export default LiveExampleQueriesBanner;
