import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AILoader } from '../ui/ai-loader';
import type { ReasoningStep } from '../../types/graphrag';

interface ReasoningPathVisualizerProps {
  query: string;
  steps: ReasoningStep[];
  isActive?: boolean;
  onStepClick?: (stepId: number) => void;
}

// Map step types to display words
const stepWords: Record<string, string> = {
  search: 'Searching',
  traverse: 'Exploring',
  context: 'Connecting',
  synthesis: 'Reasoning',
  complete: 'Complete',
};

// Fallback words to cycle through if no active step
const thinkingWords = [
  'Thinking',
  'Searching',
  'Exploring',
  'Reasoning',
  'Connecting',
  'Analyzing',
  'Weaving',
  'Pondering',
  'Inquiring',
];

export const ReasoningPathVisualizer: React.FC<ReasoningPathVisualizerProps> = ({
  steps,
}) => {
  const [wordIndex, setWordIndex] = useState(0);
  const activeStep = steps.find(s => s.status === 'active');
  const completedCount = steps.filter(s => s.status === 'complete').length;
  const progress = (completedCount / steps.length) * 100;

  // Get current word based on active step or cycle through thinking words
  const currentWord = activeStep
    ? stepWords[activeStep.type] || 'Thinking'
    : thinkingWords[wordIndex];

  // Cycle through words when no specific step is active
  useEffect(() => {
    if (activeStep) return; // Don't cycle if we have an active step

    const interval = setInterval(() => {
      setWordIndex((prev) => (prev + 1) % thinkingWords.length);
    }, 2000);

    return () => clearInterval(interval);
  }, [activeStep]);

  return (
    <div className="flex flex-col items-center justify-center py-8 w-full">
      {/* Parchment glass card for the loader */}
      <div className="bg-gradient-to-br from-parchment-100/95 via-parchment-50/95 to-parchment-100/95 backdrop-blur-xl rounded-3xl p-8 shadow-2xl border border-amber-200/40 flex flex-col items-center">
        {/* Animated loader with changing word */}
        <div className="relative flex items-center justify-center">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentWord}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.3 }}
              className="flex items-center justify-center"
            >
              <AILoader text={currentWord} size="lg" />
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Subtle step description */}
        {activeStep && (
          <motion.p
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 text-sm text-stone-400 text-center max-w-md"
          >
            {activeStep.description}
          </motion.p>
        )}

        {/* Minimal progress indicator */}
        <div className="mt-6 w-48 mx-auto">
          <div className="h-1 bg-stone-200 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-orange-400 via-amber-400 to-orange-300"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.5, ease: 'easeOut' }}
            />
          </div>
          <p className="text-xs text-stone-500 text-center mt-2">
            {completedCount} of {steps.length} steps
          </p>
        </div>
      </div>
    </div>
  );
};

export default ReasoningPathVisualizer;
