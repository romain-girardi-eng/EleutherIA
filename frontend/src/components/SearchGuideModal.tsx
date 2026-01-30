import React from 'react';
import { X, HelpCircle, Search, ArrowRight, CheckCircle } from 'lucide-react';

interface SearchGuideModalProps {
  isOpen: boolean;
  onClose: () => void;
}

// Static guide data for hybrid search
const SEARCH_GUIDE = {
  title: "Search Guide",
  description: "Learn how to use EleutherIA's hybrid search",
  mode: {
    name: "Hybrid Search",
    model: "Gemini (3072-dim) + Full-text + Lemmatic",
    method: "RRF (Reciprocal Rank Fusion)",
    granularity: "Passage-level (~200-500 tokens)",
    endpoint: "/api/search/hybrid",
    performance: "62/100 (A/B tested)",
    best_for: [
      "Conceptual philosophical questions",
      "Finding passages about ideas/concepts",
      "General topic exploration",
      '"What did X say about Y?"',
      "Understanding arguments and debates",
      "Cross-lingual concept matching",
    ],
    examples: [
      {
        query: "What is the Stoic view on fate?",
        explanation: "Conceptual query looking for passages discussing Stoic fate",
        why: "Asks ABOUT a concept - combines semantic understanding with exact text matching",
      },
      {
        query: "free will and determinism",
        explanation: "Topic search - find all relevant passages",
        why: "General keywords benefit from multi-modal search",
      },
      {
        query: "Aristotle's critique of Plato",
        explanation: "Looking for passages where Aristotle discusses Plato's views",
        why: "Seeking conceptual discussion across multiple search modes",
      },
      {
        query: "ἐφ' ἡμῖν",
        explanation: "Search for the Greek phrase 'what is up to us'",
        why: "Lemmatic search finds all grammatical forms, semantic finds related concepts",
      },
    ],
    not_for: [
      "Single-word lookups (use the text reader instead)",
      "Browsing without a specific question",
    ],
  },
  tips: [
    "Use Greek or Latin directly for best results",
    "Enable all three modes (Full-text + Lemmatic + Semantic) for comprehensive results",
    "RRF fusion automatically ranks results from multiple search methods",
    "Enable AI mode for query expansion and reranking",
    "Start broad, then narrow down your search",
  ],
};

const SearchGuideModal: React.FC<SearchGuideModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const mode = SEARCH_GUIDE.mode;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <HelpCircle className="w-8 h-8" />
              <div>
                <h2 className="text-2xl font-bold">{SEARCH_GUIDE.title}</h2>
                <p className="text-blue-100">{SEARCH_GUIDE.description}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:bg-white hover:bg-opacity-20 rounded-full p-2 transition"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(90vh-180px)]">
          {/* Mode Header */}
          <div className="bg-blue-50 dark:bg-blue-900/30 border-b border-blue-200 dark:border-blue-700 px-6 py-4">
            <div className="flex items-center space-x-2">
              <Search className="w-5 h-5 text-blue-600" />
              <span className="font-semibold text-blue-800 dark:text-blue-200">{mode.name}</span>
              <span className="text-sm text-blue-600 dark:text-blue-300">- {mode.model}</span>
            </div>
          </div>

          <div className="p-6 space-y-6">
            {/* Overview */}
            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 space-y-2">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-semibold text-gray-700 dark:text-gray-300">Method:</span>
                  <span className="ml-2 text-gray-600 dark:text-gray-400">{mode.method}</span>
                </div>
                <div>
                  <span className="font-semibold text-gray-700 dark:text-gray-300">Granularity:</span>
                  <span className="ml-2 text-gray-600 dark:text-gray-400">{mode.granularity}</span>
                </div>
              </div>
            </div>

            {/* Best For */}
            <div>
              <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-3 flex items-center">
                <CheckCircle className="w-5 h-5 mr-2 text-green-600" />
                Best For:
              </h3>
              <ul className="space-y-2">
                {mode.best_for.map((item, index) => (
                  <li key={index} className="flex items-start">
                    <ArrowRight className="w-4 h-4 mr-2 mt-1 text-green-600 flex-shrink-0" />
                    <span className="text-gray-700 dark:text-gray-300">{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Examples */}
            <div>
              <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-3">
                Example Queries:
              </h3>
              <div className="space-y-4">
                {mode.examples.map((example, index) => (
                  <div
                    key={index}
                    className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-4"
                  >
                    <div className="font-mono text-sm bg-gray-100 dark:bg-gray-800 p-2 rounded mb-2">
                      {example.query}
                    </div>
                    <p className="text-sm text-gray-700 dark:text-gray-300 mb-1">
                      {example.explanation}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 italic">
                      Why: {example.why}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Tips */}
            <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-2">
                Quick Tips:
              </h3>
              <ul className="space-y-1 text-sm text-blue-800 dark:text-blue-200">
                {SEARCH_GUIDE.tips.map((tip, index) => (
                  <li key={index}>• {tip}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-gray-50 dark:bg-gray-900">
          <button
            onClick={onClose}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition"
          >
            Got it!
          </button>
        </div>
      </div>
    </div>
  );
};

export default SearchGuideModal;
