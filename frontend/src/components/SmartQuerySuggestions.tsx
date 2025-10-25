import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, TrendingUp, Users, BookOpen, Lightbulb } from 'lucide-react';

interface QuerySuggestion {
  text: string;
  category: 'philosophical' | 'comparative' | 'historical' | 'conceptual';
  description: string;
  estimatedComplexity: 'simple' | 'moderate' | 'complex';
  exampleNodes?: string[];
}

interface SmartQuerySuggestionsProps {
  currentQuery: string;
  onSuggestionClick: (suggestion: string) => void;
  className?: string;
}

const SUGGESTION_CATEGORIES = {
  philosophical: { icon: Lightbulb, color: 'text-purple-600', bg: 'bg-purple-50', border: 'border-purple-200' },
  comparative: { icon: Users, color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-200' },
  historical: { icon: BookOpen, color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-200' },
  conceptual: { icon: TrendingUp, color: 'text-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-200' }
};

// Predefined smart suggestions based on common research patterns
const SMART_SUGGESTIONS: QuerySuggestion[] = [
  // Philosophical questions
  {
    text: "What is Aristotle's concept of voluntary action?",
    category: 'philosophical',
    description: 'Deep dive into a single philosopher',
    estimatedComplexity: 'simple',
    exampleNodes: ['Aristotle', 'Voluntary Action', 'Nicomachean Ethics III.1']
  },
  {
    text: "What does Augustine say about free will and grace?",
    category: 'philosophical',
    description: 'Christian theology on free will',
    estimatedComplexity: 'moderate',
    exampleNodes: ['Augustine', 'Grace', 'Free Will', 'Pelagius']
  },
  {
    text: "How did Epicurus argue for freedom in a deterministic universe?",
    category: 'philosophical',
    description: 'Epicurean atomism and swerve',
    estimatedComplexity: 'moderate',
    exampleNodes: ['Epicurus', 'Swerve', 'Determinism', 'Lucretius']
  },

  // Comparative questions
  {
    text: "How did the Stoics reconcile fate with moral responsibility?",
    category: 'comparative',
    description: 'School-wide doctrinal analysis',
    estimatedComplexity: 'moderate',
    exampleNodes: ['Stoics', 'Fate', 'Moral Responsibility', 'Chrysippus']
  },
  {
    text: "Compare Aristotelian and Stoic views on voluntary action",
    category: 'comparative',
    description: 'Cross-school comparison',
    estimatedComplexity: 'complex',
    exampleNodes: ['Aristotle', 'Stoics', 'Voluntary Action', 'eph hemin']
  },
  {
    text: "What are the key differences between Pelagius and Augustine on free will?",
    category: 'comparative',
    description: 'Theological debate analysis',
    estimatedComplexity: 'moderate',
    exampleNodes: ['Pelagius', 'Augustine', 'Free Will', 'Grace']
  },

  // Historical questions
  {
    text: "How did the concept of 'eph hemin' evolve from Aristotle to the Stoics?",
    category: 'historical',
    description: 'Conceptual evolution tracking',
    estimatedComplexity: 'complex',
    exampleNodes: ['eph hemin', 'Aristotle', 'Stoics', 'Alexander of Aphrodisias']
  },
  {
    text: "What arguments did Carneades use against Stoic determinism?",
    category: 'historical',
    description: 'Academic Skeptic critique',
    estimatedComplexity: 'moderate',
    exampleNodes: ['Carneades', 'Stoic Determinism', 'Chrysippus']
  },
  {
    text: "Trace the transmission of Aristotelian ethics through Arabic commentators",
    category: 'historical',
    description: 'Intellectual transmission',
    estimatedComplexity: 'complex',
    exampleNodes: ['Aristotle', 'Alexander of Aphrodisias', 'Arabic Commentators']
  },

  // Conceptual questions
  {
    text: "What is the relationship between fate and providence in ancient thought?",
    category: 'conceptual',
    description: 'Conceptual relationship analysis',
    estimatedComplexity: 'moderate',
    exampleNodes: ['Fate', 'Providence', 'Stoics', 'Neoplatonists']
  },
  {
    text: "How does 'in nostra potestate' relate to Greek 'eph hemin'?",
    category: 'conceptual',
    description: 'Greek-to-Latin terminology',
    estimatedComplexity: 'simple',
    exampleNodes: ['eph hemin', 'in nostra potestate', 'Cicero']
  },
  {
    text: "What role does necessity play in Stoic physics and ethics?",
    category: 'conceptual',
    description: 'Cross-domain concept analysis',
    estimatedComplexity: 'complex',
    exampleNodes: ['Necessity', 'Stoic Physics', 'Stoic Ethics', 'Chrysippus']
  }
];

export const SmartQuerySuggestions: React.FC<SmartQuerySuggestionsProps> = ({
  currentQuery,
  onSuggestionClick,
  className = ''
}) => {
  const [filteredSuggestions, setFilteredSuggestions] = useState<QuerySuggestion[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  useEffect(() => {
    if (!currentQuery || currentQuery.length < 3) {
      // Show all suggestions when no query or query too short
      setFilteredSuggestions(SMART_SUGGESTIONS);
      return;
    }

    // Filter suggestions based on current query
    const query = currentQuery.toLowerCase();
    const filtered = SMART_SUGGESTIONS.filter(suggestion => {
      const textMatch = suggestion.text.toLowerCase().includes(query);
      const descMatch = suggestion.description.toLowerCase().includes(query);
      const nodeMatch = suggestion.exampleNodes?.some(node =>
        node.toLowerCase().includes(query)
      );
      return textMatch || descMatch || nodeMatch;
    });

    setFilteredSuggestions(filtered.length > 0 ? filtered : SMART_SUGGESTIONS);
  }, [currentQuery]);

  // Filter by selected category
  const displayedSuggestions = selectedCategory
    ? filteredSuggestions.filter(s => s.category === selectedCategory)
    : filteredSuggestions;

  const getCategoryCount = (category: string) => {
    return filteredSuggestions.filter(s => s.category === category).length;
  };

  const getComplexityBadge = (complexity: string) => {
    const colors = {
      simple: 'bg-green-100 text-green-700 border-green-200',
      moderate: 'bg-yellow-100 text-yellow-700 border-yellow-200',
      complex: 'bg-red-100 text-red-700 border-red-200'
    };
    return colors[complexity as keyof typeof colors] || colors.simple;
  };

  return (
    <div className={`w-full ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-primary-600" />
          <h3 className="text-sm font-semibold text-gray-900">Smart Suggestions</h3>
        </div>

        {/* Category Filter */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <button
            onClick={() => setSelectedCategory(null)}
            className={`px-2 py-0.5 text-xs font-medium rounded-full transition-colors ${
              selectedCategory === null
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            All ({filteredSuggestions.length})
          </button>

          {Object.entries(SUGGESTION_CATEGORIES).map(([cat, config]) => {
            const count = getCategoryCount(cat);
            if (count === 0) return null;

            const Icon = config.icon;
            return (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-2 py-0.5 text-xs font-medium rounded-full transition-colors flex items-center gap-1 ${
                  selectedCategory === cat
                    ? `${config.bg} ${config.color} border ${config.border}`
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                <Icon className="w-3 h-3" />
                <span className="capitalize hidden sm:inline">{cat}</span>
                <span className="sm:ml-1">({count})</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Suggestions Grid */}
      <AnimatePresence mode="popLayout">
        {displayedSuggestions.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="text-center py-6 text-gray-500"
          >
            <Sparkles className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No suggestions match your query. Try different keywords!</p>
          </motion.div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 max-w-full">
            {displayedSuggestions.map((suggestion, idx) => {
              const categoryConfig = SUGGESTION_CATEGORIES[suggestion.category];
              const Icon = categoryConfig.icon;

              return (
                <motion.button
                  key={`${suggestion.text}-${idx}`}
                  layout
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ delay: idx * 0.05 }}
                  onClick={() => onSuggestionClick(suggestion.text)}
                  className={`text-left p-2.5 rounded-lg border ${categoryConfig.border} ${categoryConfig.bg} hover:shadow-md transition-all duration-200 hover:scale-[1.02] group w-full min-w-0`}
                >
                  {/* Header */}
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <div className={`p-1.5 rounded ${categoryConfig.bg} border ${categoryConfig.border}`}>
                      <Icon className={`w-3 h-3 ${categoryConfig.color}`} />
                    </div>
                    <span className={`text-xs px-1.5 py-0.5 rounded-full border flex-shrink-0 ${getComplexityBadge(suggestion.estimatedComplexity)}`}>
                      {suggestion.estimatedComplexity}
                    </span>
                  </div>

                  {/* Query Text */}
                  <p className={`text-xs font-semibold mb-1.5 ${categoryConfig.color} group-hover:underline line-clamp-2`}>
                    "{suggestion.text}"
                  </p>

                  {/* Description */}
                  <p className="text-xs text-gray-600 mb-2 line-clamp-1">
                    {suggestion.description}
                  </p>

                  {/* Example Nodes */}
                  {suggestion.exampleNodes && suggestion.exampleNodes.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {suggestion.exampleNodes.slice(0, 2).map((node, nodeIdx) => (
                        <span
                          key={nodeIdx}
                          className="text-xs px-1.5 py-0.5 bg-white border border-gray-200 rounded text-gray-700 truncate max-w-[80px]"
                          title={node}
                        >
                          {node}
                        </span>
                      ))}
                      {suggestion.exampleNodes.length > 2 && (
                        <span className="text-xs px-1.5 py-0.5 text-gray-500">
                          +{suggestion.exampleNodes.length - 2}
                        </span>
                      )}
                    </div>
                  )}
                </motion.button>
              );
            })}
          </div>
        )}
      </AnimatePresence>

      {/* Help Text */}
      <div className="mt-3 p-2 bg-slate-50 border border-slate-200 rounded-lg">
        <p className="text-xs text-gray-600">
          <span className="font-semibold">💡 Tip:</span> Click any suggestion to explore philosophical arguments with citations.
        </p>
      </div>
    </div>
  );
};

export default SmartQuerySuggestions;
