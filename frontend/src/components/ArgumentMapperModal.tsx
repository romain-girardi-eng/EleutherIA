import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { ArgumentMapper } from './ArgumentMapper';

// Inline type definition to avoid module caching issues
interface ArgumentMapping {
  id: string;
  claim: string;
  premises: Array<{
    id: string;
    text: string;
    source?: string;
  }>;
  objections?: Array<{
    id: string;
    text: string;
    source?: string;
  }>;
  responses?: Array<{
    id: string;
    text: string;
    source?: string;
  }>;
  conclusion: string;
  relatedConcepts: string[];
}

interface ArgumentMapperModalProps {
  isOpen: boolean;
  onClose: () => void;
  argument: ArgumentMapping | null;
  onNodeClick?: (nodeId: string) => void;
}

export const ArgumentMapperModal: React.FC<ArgumentMapperModalProps> = ({
  isOpen,
  onClose,
  argument,
  onNodeClick
}) => {
  if (!argument) return null;

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
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed inset-4 md:inset-8 lg:inset-16 z-50 overflow-hidden"
          >
            <div className="h-full flex flex-col bg-white rounded-2xl shadow-2xl">
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b border-gray-200">
                <h2 className="text-2xl font-bold text-gray-900">Argument Analysis</h2>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  aria-label="Close"
                >
                  <X className="w-6 h-6 text-gray-600" />
                </button>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-4 md:p-6">
                <ArgumentMapper
                  argument={argument}
                  onNodeClick={onNodeClick}
                />
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default ArgumentMapperModal;
