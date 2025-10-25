import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  GitBranch,
  CheckCircle,
  XCircle,
  ArrowRight,
  Book,
  Lightbulb,
  AlertCircle,
  Shield
} from 'lucide-react';
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

interface ArgumentMapperProps {
  argument: ArgumentMapping;
  className?: string;
  onNodeClick?: (nodeId: string) => void;
}

export const ArgumentMapper: React.FC<ArgumentMapperProps> = ({
  argument,
  className = '',
  onNodeClick
}) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['premises']));
  const [selectedElement, setSelectedElement] = useState<string | null>(null);

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const isPremisesExpanded = expandedSections.has('premises');
  const isObjectionsExpanded = expandedSections.has('objections');
  const isResponsesExpanded = expandedSections.has('responses');

  return (
    <div className={`${className}`}>
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 text-white p-6 rounded-t-2xl">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-white/20 rounded-xl">
            <GitBranch className="w-8 h-8" />
          </div>
          <div className="flex-1">
            <h2 className="text-2xl font-bold mb-2">Argument Structure</h2>
            <p className="text-white/90 text-lg italic leading-relaxed">
              "{argument.claim}"
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {argument.relatedConcepts.map((concept, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 bg-white/20 border border-white/30 rounded-full text-sm cursor-pointer hover:bg-white/30 transition-colors"
                  onClick={() => onNodeClick?.(concept)}
                >
                  {concept}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Argument Flow Diagram */}
      <div className="bg-white rounded-b-2xl shadow-xl p-6">
        {/* Premises Section */}
        <div className="mb-6">
          <button
            onClick={() => toggleSection('premises')}
            className="w-full flex items-center justify-between p-4 bg-green-50 border-2 border-green-200 rounded-xl hover:bg-green-100 transition-colors"
          >
            <div className="flex items-center gap-3">
              <Lightbulb className="w-6 h-6 text-green-700" />
              <h3 className="text-lg font-bold text-green-900">
                Premises ({argument.premises.length})
              </h3>
            </div>
            <motion.div
              animate={{ rotate: isPremisesExpanded ? 180 : 0 }}
              transition={{ duration: 0.3 }}
            >
              <ArrowRight className="w-5 h-5 text-green-700 rotate-90" />
            </motion.div>
          </button>

          <AnimatePresence>
            {isPremisesExpanded && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
                className="mt-3 space-y-3"
              >
                {argument.premises.map((premise, idx) => (
                  <motion.div
                    key={premise.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.1 }}
                    className={`p-4 border-2 border-green-200 rounded-lg hover:shadow-md transition-all cursor-pointer ${
                      selectedElement === premise.id ? 'bg-green-100 border-green-400' : 'bg-white'
                    }`}
                    onClick={() => setSelectedElement(premise.id)}
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
                        P{idx + 1}
                      </div>
                      <div className="flex-1">
                        <p className="text-gray-900 leading-relaxed">{premise.text}</p>
                        {premise.source && (
                          <div className="mt-2 flex items-center gap-2 text-sm text-gray-600">
                            <Book className="w-4 h-4" />
                            <span className="italic">{premise.source}</span>
                          </div>
                        )}
                      </div>
                      <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Flow Arrow */}
        <div className="flex justify-center mb-6">
          <div className="flex flex-col items-center">
            <ArrowRight className="w-8 h-8 text-gray-400 rotate-90" />
            <span className="text-sm text-gray-500 font-medium mt-1">Therefore</span>
          </div>
        </div>

        {/* Conclusion */}
        <div className="mb-6 p-6 bg-gradient-to-br from-indigo-50 to-purple-50 border-2 border-indigo-300 rounded-xl">
          <div className="flex items-start gap-4">
            <div className="p-2 bg-indigo-600 text-white rounded-lg">
              <CheckCircle className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-bold text-indigo-900 mb-2">Conclusion</h3>
              <p className="text-gray-900 text-lg leading-relaxed italic">
                "{argument.conclusion}"
              </p>
            </div>
          </div>
        </div>

        {/* Objections Section */}
        {argument.objections && argument.objections.length > 0 && (
          <div className="mb-6">
            <button
              onClick={() => toggleSection('objections')}
              className="w-full flex items-center justify-between p-4 bg-red-50 border-2 border-red-200 rounded-xl hover:bg-red-100 transition-colors"
            >
              <div className="flex items-center gap-3">
                <AlertCircle className="w-6 h-6 text-red-700" />
                <h3 className="text-lg font-bold text-red-900">
                  Objections ({argument.objections.length})
                </h3>
              </div>
              <motion.div
                animate={{ rotate: isObjectionsExpanded ? 180 : 0 }}
                transition={{ duration: 0.3 }}
              >
                <ArrowRight className="w-5 h-5 text-red-700 rotate-90" />
              </motion.div>
            </button>

            <AnimatePresence>
              {isObjectionsExpanded && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.3 }}
                  className="mt-3 space-y-3"
                >
                  {argument.objections.map((objection, idx) => (
                    <motion.div
                      key={objection.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.1 }}
                      className={`p-4 border-2 border-red-200 rounded-lg hover:shadow-md transition-all cursor-pointer ${
                        selectedElement === objection.id ? 'bg-red-100 border-red-400' : 'bg-white'
                      }`}
                      onClick={() => setSelectedElement(objection.id)}
                    >
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 w-8 h-8 bg-red-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
                          O{idx + 1}
                        </div>
                        <div className="flex-1">
                          <p className="text-gray-900 leading-relaxed">{objection.text}</p>
                          {objection.source && (
                            <div className="mt-2 flex items-center gap-2 text-sm text-gray-600">
                              <Book className="w-4 h-4" />
                              <span className="italic">{objection.source}</span>
                            </div>
                          )}
                        </div>
                        <XCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
                      </div>
                    </motion.div>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {/* Responses Section */}
        {argument.responses && argument.responses.length > 0 && (
          <div>
            <button
              onClick={() => toggleSection('responses')}
              className="w-full flex items-center justify-between p-4 bg-blue-50 border-2 border-blue-200 rounded-xl hover:bg-blue-100 transition-colors"
            >
              <div className="flex items-center gap-3">
                <Shield className="w-6 h-6 text-blue-700" />
                <h3 className="text-lg font-bold text-blue-900">
                  Responses ({argument.responses.length})
                </h3>
              </div>
              <motion.div
                animate={{ rotate: isResponsesExpanded ? 180 : 0 }}
                transition={{ duration: 0.3 }}
              >
                <ArrowRight className="w-5 h-5 text-blue-700 rotate-90" />
              </motion.div>
            </button>

            <AnimatePresence>
              {isResponsesExpanded && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.3 }}
                  className="mt-3 space-y-3"
                >
                  {argument.responses.map((response, idx) => (
                    <motion.div
                      key={response.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.1 }}
                      className={`p-4 border-2 border-blue-200 rounded-lg hover:shadow-md transition-all cursor-pointer ${
                        selectedElement === response.id ? 'bg-blue-100 border-blue-400' : 'bg-white'
                      }`}
                      onClick={() => setSelectedElement(response.id)}
                    >
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
                          R{idx + 1}
                        </div>
                        <div className="flex-1">
                          <p className="text-gray-900 leading-relaxed">{response.text}</p>
                          {response.source && (
                            <div className="mt-2 flex items-center gap-2 text-sm text-gray-600">
                              <Book className="w-4 h-4" />
                              <span className="italic">{response.source}</span>
                            </div>
                          )}
                        </div>
                        <Shield className="w-5 h-5 text-blue-600 flex-shrink-0" />
                      </div>
                    </motion.div>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {/* Legend */}
        <div className="mt-8 p-4 bg-gray-50 border border-gray-200 rounded-xl">
          <h4 className="font-semibold text-gray-900 mb-3 text-sm">Legend</h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-green-600 text-white rounded-full flex items-center justify-center text-xs font-bold">P</div>
              <span className="text-gray-700">Premises (supporting statements)</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-indigo-600" />
              <span className="text-gray-700">Conclusion (main claim)</span>
            </div>
            {argument.objections && argument.objections.length > 0 && (
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 bg-red-600 text-white rounded-full flex items-center justify-center text-xs font-bold">O</div>
                <span className="text-gray-700">Objections (counter-arguments)</span>
              </div>
            )}
            {argument.responses && argument.responses.length > 0 && (
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold">R</div>
                <span className="text-gray-700">Responses (defenses)</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ArgumentMapper;
