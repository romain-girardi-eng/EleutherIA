import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';

interface AncientCitation {
  citation_text: string;
  confidence: number;
  cts_urn?: string;
}

interface BibliographyEntry {
  citation_key: string;
  author: string;
  year?: number;
  title: string;
  full_citation_chicago: string;
}

interface EvidenceChain {
  claim: string;
  kgNodes?: string[];
  kg_nodes?: string[];
  ancientSources?: AncientCitation[];
  ancient_sources?: AncientCitation[];
  modernSources?: BibliographyEntry[];
  modern_sources?: BibliographyEntry[];
  confidence: number;
}

interface EvidenceChainPanelProps {
  evidenceChains: EvidenceChain[];
}

const EvidenceChainPanel: React.FC<EvidenceChainPanelProps> = ({ evidenceChains }) => {
  const { t } = useTranslation();
  const [expandedChain, setExpandedChain] = useState<number | null>(null);

  if (!evidenceChains || evidenceChains.length === 0) {
    return null;
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-700 bg-green-50 border-green-200';
    if (confidence >= 0.6) return 'text-blue-700 bg-blue-50 border-blue-200';
    if (confidence >= 0.4) return 'text-yellow-700 bg-yellow-50 border-yellow-200';
    return 'text-red-700 bg-red-50 border-red-200';
  };

  const toggleChain = (index: number) => {
    setExpandedChain(expandedChain === index ? null : index);
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 px-4 py-3">
        <h3 className="text-white font-semibold flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
          {t('evidenceChain.title')}
        </h3>
        <p className="text-primary-100 text-xs mt-1">
          {t('evidenceChain.subtitle')}
        </p>
      </div>

      {/* Evidence Chains List */}
      <div className="divide-y divide-gray-200">
        {evidenceChains.map((chain, index) => (
          <div key={index} className="p-4 hover:bg-gray-50 transition-colors">
            {/* Chain Header - Claim */}
            <div
              className="flex items-start gap-3 cursor-pointer"
              onClick={() => toggleChain(index)}
            >
              <div className="flex-shrink-0 mt-1">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm border-2 ${getConfidenceColor(chain.confidence)}`}>
                  {index + 1}
                </div>
              </div>

              <div className="flex-grow min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${getConfidenceColor(chain.confidence)}`}>
                    {(chain.confidence * 100).toFixed(0)}% {t('evidenceChain.confidence')}
                  </span>
                  <span className="text-xs text-gray-500">
                    {(chain.ancientSources ?? chain.ancient_sources ?? []).length} {t('evidenceChain.ancientSourcesCount', { count: (chain.ancientSources ?? chain.ancient_sources ?? []).length })} · {(chain.modernSources ?? chain.modern_sources ?? []).length} {t('evidenceChain.modernSourcesCount', { count: (chain.modernSources ?? chain.modern_sources ?? []).length })}
                  </span>
                </div>

                <p className="text-sm text-gray-900 leading-relaxed">
                  {chain.claim}
                </p>
              </div>

              <div className="flex-shrink-0">
                <svg
                  className={`w-5 h-5 text-gray-400 transition-transform ${expandedChain === index ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>

            {/* Expanded Chain Details */}
            {expandedChain === index && (
              <div className="mt-4 ml-11 space-y-4">
                {/* KG Nodes */}
                {(chain.kgNodes ?? chain.kg_nodes ?? []).length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-gray-700 mb-2 flex items-center gap-1">
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16l2.879-2.879m0 0a3 3 0 104.243-4.242 3 3 0 00-4.243 4.242zM21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      {t('evidenceChain.kgNodesLabel')}
                    </h4>
                    <div className="flex flex-wrap gap-1">
                      {(chain.kgNodes ?? chain.kg_nodes ?? []).map((nodeId, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded border border-gray-200"
                        >
                          {nodeId}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Ancient Sources */}
                {(chain.ancientSources ?? chain.ancient_sources ?? []).length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-gray-700 mb-2 flex items-center gap-1">
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                      </svg>
                      {t('evidenceChain.ancientSourcesLabel')}
                    </h4>
                    <div className="space-y-2">
                      {(chain.ancientSources ?? chain.ancient_sources ?? []).map((source, idx) => (
                        <div key={idx} className="text-xs bg-blue-50 p-2 rounded border border-blue-100">
                          <div className="flex items-center justify-between">
                            <span className="font-medium text-blue-900">{source.citation_text}</span>
                            <span className="text-blue-600 font-semibold">
                              {(source.confidence * 100).toFixed(0)}%
                            </span>
                          </div>
                          {source.cts_urn && (
                            <div className="mt-1 text-blue-600 font-mono text-[10px]">
                              {source.cts_urn}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Modern Sources */}
                {(chain.modernSources ?? chain.modern_sources ?? []).length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-gray-700 mb-2 flex items-center gap-1">
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      {t('evidenceChain.modernScholarshipLabel')}
                    </h4>
                    <div className="space-y-1">
                      {(chain.modernSources ?? chain.modern_sources ?? []).map((source, idx) => (
                        <div key={idx} className="text-xs text-gray-700 bg-green-50 p-2 rounded border border-green-100">
                          <span className="font-medium text-green-900">
                            {source.author} ({source.year})
                          </span>
                          {' - '}
                          <span className="text-green-800">{source.title}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Evidence Path Visualization */}
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <div className="flex items-center text-xs text-gray-600">
                    <span className="font-semibold">{t('evidenceChain.evidencePathLabel')}</span>
                    <svg className="w-4 h-4 mx-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    <span>{t('evidenceChain.claim')}</span>
                    <svg className="w-4 h-4 mx-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    <span>{t('evidenceChain.kgNodes')}</span>
                    <svg className="w-4 h-4 mx-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    <span>{t('evidenceChain.ancientSources')}</span>
                    <svg className="w-4 h-4 mx-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    <span>{t('evidenceChain.modernAnalysis')}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Info Footer */}
      <div className="bg-gray-50 px-4 py-3 text-xs text-gray-600">
        <p>
          <strong>{t('evidenceChain.howToRead')}</strong> {t('evidenceChain.howToReadDesc')}
        </p>
      </div>
    </div>
  );
};

export default EvidenceChainPanel;
