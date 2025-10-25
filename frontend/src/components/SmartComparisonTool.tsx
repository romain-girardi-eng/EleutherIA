import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GitCompare, Plus, X, Check, AlertCircle, BookOpen } from 'lucide-react';

// Inline type definition
interface ComparisonResult {
  entities: Array<{
    id: string;
    label: string;
    type: string;
  }>;
  dimensions: Array<{
    name: string;
    values: Record<string, string | number>;
  }>;
  similarities: string[];
  differences: string[];
  synthesis?: string;
}

interface SmartComparisonToolProps {
  className?: string;
}

export const SmartComparisonTool: React.FC<SmartComparisonToolProps> = ({
  className = ''
}) => {
  const [selectedEntities, setSelectedEntities] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [comparisonResult, setComparisonResult] = useState<ComparisonResult | null>(null);

  // Predefined common comparisons
  const commonComparisons = [
    {
      title: 'Aristotle vs. Stoics on Voluntary Action',
      entities: ['Aristotle', 'Stoics'],
      description: 'Compare Aristotelian and Stoic theories of voluntary action'
    },
    {
      title: 'Epicurus vs. Stoics on Freedom',
      entities: ['Epicurus', 'Stoics'],
      description: 'Contrast Epicurean swerve with Stoic determinism'
    },
    {
      title: 'Augustine vs. Pelagius on Grace',
      entities: ['Augustine', 'Pelagius'],
      description: 'Examine the debate on free will and divine grace'
    },
    {
      title: 'eph hemin vs. in nostra potestate',
      entities: ['eph hemin', 'in nostra potestate'],
      description: 'Greek and Latin terminology for "in our power"'
    }
  ];

  // Sample entity suggestions
  const entitySuggestions = [
    'Aristotle', 'Stoics', 'Epicurus', 'Augustine', 'Pelagius', 'Chrysippus',
    'Alexander of Aphrodisias', 'Carneades', 'Cicero', 'Plotinus', 'Boethius',
    'eph hemin', 'in nostra potestate', 'Voluntary Action', 'Fate', 'Providence',
    'Determinism', 'Moral Responsibility', 'Grace', 'Free Will'
  ].filter(e => e.toLowerCase().includes(searchTerm.toLowerCase()));

  const handleAddEntity = (entity: string) => {
    if (!selectedEntities.includes(entity) && selectedEntities.length < 4) {
      setSelectedEntities([...selectedEntities, entity]);
      setSearchTerm('');
    }
  };

  const handleRemoveEntity = (entity: string) => {
    setSelectedEntities(selectedEntities.filter(e => e !== entity));
  };

  const handleCompare = async () => {
    if (selectedEntities.length < 2) return;

    setIsSearching(true);

    // Simulate API call - in real implementation, this would call the GraphRAG backend
    setTimeout(() => {
      const mockResult: ComparisonResult = {
        entities: selectedEntities.map(e => ({
          id: e.toLowerCase().replace(/\s+/g, '_'),
          label: e,
          type: 'concept'
        })),
        dimensions: [
          {
            name: 'Core Position',
            values: selectedEntities.reduce((acc, entity) => {
              acc[entity] = `${entity}'s view on free will and determinism`;
              return acc;
            }, {} as Record<string, string>)
          },
          {
            name: 'Historical Period',
            values: selectedEntities.reduce((acc, entity) => {
              acc[entity] = entity.includes('Augustine') || entity.includes('Pelagius')
                ? 'Patristic (4th-5th c. CE)'
                : 'Classical/Hellenistic';
              return acc;
            }, {} as Record<string, string>)
          },
          {
            name: 'Key Arguments',
            values: selectedEntities.reduce((acc, entity) => {
              acc[entity] = 3;
              return acc;
            }, {} as Record<string, number>)
          }
        ],
        similarities: [
          `All ${selectedEntities.length} positions engage with the fundamental question of human agency and moral responsibility`,
          'Each tradition developed technical vocabulary to address these issues',
          'Common concern with reconciling human freedom with causal determinism or divine providence'
        ],
        differences: [
          `${selectedEntities[0]} emphasizes rational deliberation while ${selectedEntities[1]} focuses on assent`,
          'Different metaphysical frameworks lead to distinct conceptions of freedom',
          'Varying degrees of compatibility with determinism'
        ],
        synthesis: `The comparison reveals a progression from ${selectedEntities[0]}'s foundational analysis to later refinements in ${selectedEntities.slice(1).join(' and ')}. Each position contributes unique insights to the ongoing philosophical debate.`
      };

      setComparisonResult(mockResult);
      setIsSearching(false);
    }, 1500);
  };

  const handleUseCommonComparison = (entities: string[]) => {
    setSelectedEntities(entities);
  };

  return (
    <div className={`${className}`}>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg">
            <GitCompare className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Smart Comparison Tool</h2>
            <p className="text-sm text-gray-600">
              Compare philosophers, arguments, and concepts side-by-side
            </p>
          </div>
        </div>
      </div>

      {/* Common Comparisons */}
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Popular Comparisons</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {commonComparisons.map((comparison, idx) => (
            <button
              key={idx}
              onClick={() => handleUseCommonComparison(comparison.entities)}
              className="text-left p-4 bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg hover:shadow-md transition-all group"
            >
              <div className="font-semibold text-blue-900 mb-1 group-hover:text-blue-700">
                {comparison.title}
              </div>
              <div className="text-xs text-blue-700">{comparison.description}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Entity Selection */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Select Entities to Compare (2-4)
        </h3>

        {/* Selected Entities */}
        <div className="flex flex-wrap gap-2 mb-4">
          {selectedEntities.map(entity => (
            <motion.div
              key={entity}
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="flex items-center gap-2 px-4 py-2 bg-primary-100 border border-primary-300 rounded-lg"
            >
              <span className="font-medium text-primary-900">{entity}</span>
              <button
                onClick={() => handleRemoveEntity(entity)}
                className="p-0.5 hover:bg-primary-200 rounded transition-colors"
              >
                <X className="w-4 h-4 text-primary-700" />
              </button>
            </motion.div>
          ))}

          {selectedEntities.length < 4 && (
            <div className="relative flex-1 min-w-[200px]">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search entities..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />

              {/* Suggestions Dropdown */}
              {searchTerm && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto z-10">
                  {entitySuggestions.slice(0, 10).map(entity => (
                    <button
                      key={entity}
                      onClick={() => handleAddEntity(entity)}
                      disabled={selectedEntities.includes(entity)}
                      className="w-full text-left px-4 py-2 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-between"
                    >
                      <span>{entity}</span>
                      {selectedEntities.includes(entity) && (
                        <Check className="w-4 h-4 text-green-600" />
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Compare Button */}
        <button
          onClick={handleCompare}
          disabled={selectedEntities.length < 2 || isSearching}
          className="w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg font-semibold hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg"
        >
          {isSearching ? 'Analyzing...' : `Compare ${selectedEntities.length} Entities`}
        </button>
      </div>

      {/* Comparison Result */}
      <AnimatePresence>
        {comparisonResult && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            {/* Comparison Table */}
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-6 py-4">
                <h3 className="text-xl font-bold">Comparison Matrix</h3>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                        Dimension
                      </th>
                      {comparisonResult.entities.map(entity => (
                        <th key={entity.id} className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                          {entity.label}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {comparisonResult.dimensions.map((dim, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="px-6 py-4 font-medium text-gray-900">{dim.name}</td>
                        {comparisonResult.entities.map(entity => (
                          <td key={entity.id} className="px-6 py-4 text-gray-700">
                            {dim.values[entity.label]}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Similarities */}
            <div className="bg-green-50 border border-green-200 rounded-xl p-6">
              <h3 className="flex items-center gap-2 text-lg font-bold text-green-900 mb-4">
                <Check className="w-5 h-5" />
                Similarities
              </h3>
              <ul className="space-y-2">
                {comparisonResult.similarities.map((sim, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-green-800">
                    <span className="text-green-600 mt-1">•</span>
                    <span>{sim}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Differences */}
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-6">
              <h3 className="flex items-center gap-2 text-lg font-bold text-amber-900 mb-4">
                <AlertCircle className="w-5 h-5" />
                Differences
              </h3>
              <ul className="space-y-2">
                {comparisonResult.differences.map((diff, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-amber-800">
                    <span className="text-amber-600 mt-1">•</span>
                    <span>{diff}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Synthesis */}
            {comparisonResult.synthesis && (
              <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-6">
                <h3 className="flex items-center gap-2 text-lg font-bold text-indigo-900 mb-4">
                  <BookOpen className="w-5 h-5" />
                  Scholarly Synthesis
                </h3>
                <p className="text-indigo-800 leading-relaxed">{comparisonResult.synthesis}</p>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default SmartComparisonTool;
