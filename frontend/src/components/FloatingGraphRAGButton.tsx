import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, X, Send, Sparkles } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const FloatingGraphRAGButton: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated } = useAuth();
  const inputRef = useRef<HTMLInputElement>(null);

  // Don't show on GraphRAG pages
  const isGraphRAGPage = location.pathname === '/graphrag' || location.pathname === '/graphrag-showcase';

  // Keyboard shortcuts DISABLED to allow normal typing
  /*
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd+K (Mac) or Ctrl+K (Windows/Linux)
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (!isGraphRAGPage) {
          setIsOpen(true);
        }
      }
      // Escape to close
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
        setQuery('');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isGraphRAGPage]);
  */

  // Focus input when modal opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      // Navigate to GraphRAG page with query as state
      navigate('/graphrag', { state: { initialQuery: query.trim() } });
      setIsOpen(false);
      setQuery('');
    }
  };

  const handleNavigateToGraphRAG = () => {
    navigate('/graphrag');
    setIsOpen(false);
  };

  if (isGraphRAGPage) {
    return null; // Don't show on GraphRAG pages
  }

  return (
    <>
      {/* Floating Button - Hidden on mobile to avoid overlap with FilterFAB */}
      <motion.button
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.5, type: 'spring', stiffness: 260, damping: 20 }}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(true)}
        className="hidden md:flex fixed bottom-20 right-6 z-40 bg-gradient-to-br from-emerald-500 to-teal-600 text-white rounded-full shadow-2xl hover:shadow-3xl transition-all duration-300 group items-center gap-3 px-5 py-3 relative"
        title="Quick GraphRAG (Cmd+K)"
      >
        {/* Desktop: Icon + Text + Keyboard Shortcut */}
        <Brain className="w-6 h-6 group-hover:scale-110 transition-transform" />
        <div className="flex flex-col items-start">
          <span className="font-semibold text-sm whitespace-nowrap">Ask GraphRAG</span>
          <span className="text-xs opacity-75 whitespace-nowrap">⌘K or Ctrl+K</span>
        </div>
        <Sparkles className="w-4 h-4 opacity-75" />
        <motion.div
          className="absolute inset-0 rounded-full bg-emerald-400 opacity-0 group-hover:opacity-20"
          animate={{
            scale: [1, 1.1, 1],
            opacity: [0.2, 0, 0.2],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      </motion.button>

      {/* Quick Search Modal */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
            />

            {/* Modal */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: -20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: -20 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="fixed top-[5%] sm:top-[50%] left-4 right-4 sm:left-1/2 sm:right-auto sm:transform sm:-translate-x-1/2 sm:-translate-y-1/2 z-50 w-auto sm:w-full sm:max-w-2xl"
            >
              <div className="bg-white rounded-xl sm:rounded-2xl shadow-2xl overflow-hidden max-h-[90vh] sm:max-h-[85vh] flex flex-col">
                {/* Header */}
                <div className="bg-gradient-to-r from-emerald-500 to-teal-600 px-4 py-3 sm:px-6 sm:py-4 flex items-center justify-between flex-shrink-0">
                  <div className="flex items-center gap-2 sm:gap-3 min-w-0">
                    <div className="p-1.5 sm:p-2 bg-white/20 rounded-lg flex-shrink-0">
                      <Brain className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
                    </div>
                    <div className="min-w-0">
                      <h2 className="text-base sm:text-xl font-bold text-white truncate">Quick GraphRAG</h2>
                      <p className="text-xs sm:text-sm text-white/80 hidden sm:block">Ask anything about ancient philosophy</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setIsOpen(false)}
                    className="p-1.5 sm:p-2 hover:bg-white/20 rounded-lg transition-colors flex-shrink-0"
                  >
                    <X className="w-5 h-5 text-white" />
                  </button>
                </div>

                {/* Scrollable Content */}
                <div className="overflow-y-auto flex-1">
                  {/* Search Form */}
                  <form onSubmit={handleSubmit} className="p-4 sm:p-6">
                  <div className="relative">
                    <input
                      ref={inputRef}
                      type="text"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      placeholder="Ask about ancient free will..."
                      autoComplete="off"
                      className="w-full px-3 sm:px-4 py-3 sm:py-4 pr-12 border-2 border-gray-300 rounded-lg sm:rounded-xl focus:border-emerald-500 focus:ring-2 sm:focus:ring-4 focus:ring-emerald-100 outline-none text-sm sm:text-lg transition-all"
                    />
                    <button
                      type="submit"
                      disabled={!query.trim()}
                      className="absolute right-2 top-1/2 transform -translate-y-1/2 p-2 bg-gradient-to-br from-emerald-500 to-teal-600 text-white rounded-lg hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                      <Send className="w-4 h-4 sm:w-5 sm:h-5" />
                    </button>
                  </div>

                  {!isAuthenticated && (
                    <div className="mt-3 sm:mt-4 p-2.5 sm:p-3 bg-amber-50 border border-amber-200 rounded-lg">
                      <p className="text-xs sm:text-sm text-amber-800">
                        <span className="font-semibold">Note:</span> You'll need to log in to use GraphRAG
                      </p>
                    </div>
                  )}
                </form>

                  {/* Example Queries */}
                  <div className="px-4 pb-4 sm:px-6 sm:pb-6">
                    <p className="text-xs sm:text-sm font-semibold text-gray-700 mb-2 sm:mb-3">Try these examples:</p>
                    <div className="space-y-2">
                      {[
                        "How did the Stoics reconcile fate with moral responsibility?",
                        "What arguments did Carneades use against determinism?",
                        "How does Augustine's view of grace relate to free will?",
                      ].map((example, idx) => (
                        <button
                          key={idx}
                          onClick={() => setQuery(example)}
                          className="w-full text-left px-3 sm:px-4 py-2 bg-gray-50 hover:bg-emerald-50 border border-gray-200 hover:border-emerald-300 rounded-lg transition-colors text-xs sm:text-sm text-gray-700 hover:text-emerald-700"
                        >
                          <Sparkles className="w-3 h-3 inline mr-1 sm:mr-2 opacity-50 flex-shrink-0" />
                          <span className="line-clamp-2">{example}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Footer */}
                <div className="px-4 py-3 sm:px-6 sm:py-4 bg-gray-50 border-t border-gray-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 flex-shrink-0">
                  <div className="hidden sm:flex items-center gap-4 text-xs text-gray-600">
                    <div className="flex items-center gap-1">
                      <kbd className="px-2 py-1 bg-white border border-gray-300 rounded shadow-sm font-mono">↵</kbd>
                      <span>to search</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <kbd className="px-2 py-1 bg-white border border-gray-300 rounded shadow-sm font-mono">esc</kbd>
                      <span>to close</span>
                    </div>
                  </div>
                  <button
                    onClick={handleNavigateToGraphRAG}
                    className="text-xs sm:text-sm text-emerald-600 hover:text-emerald-700 font-semibold flex items-center gap-1 w-full sm:w-auto justify-center sm:justify-start"
                  >
                    Go to full GraphRAG
                    <Sparkles className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
};

export default FloatingGraphRAGButton;
