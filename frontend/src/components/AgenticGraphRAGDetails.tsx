import React, { useState } from 'react';
import { ChevronDown, ChevronRight, CheckCircle2, Zap, BookOpen, Code } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useKgStats, formatCount } from '../hooks/useKgStats';

interface ImplementationSection {
  title: string;
  icon: React.ReactNode;
  content: React.ReactNode;
}

const AgenticGraphRAGDetails: React.FC = () => {
  const { t, i18n } = useTranslation();
  const stats = useKgStats();
  const fmt = (n: number) => formatCount(n, i18n.language);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['overview']));

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const sections: ImplementationSection[] = [
    {
      title: t('agenticGraphrag.overview.title'),
      icon: <BookOpen className="w-5 h-5" />,
      content: (
        <div className="space-y-4">
          <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
            <h4 className="font-semibold text-blue-900 mb-2">{t('agenticGraphrag.overview.architectureLabel')}</h4>
            <p className="text-sm text-blue-800 mb-2">
              {t('agenticGraphrag.overview.description', { nodeCount: fmt(stats.nodes), edgeCount: fmt(stats.edges) })}
            </p>
          </div>

          <div>
            <h4 className="font-semibold text-gray-900 mb-2">{t('agenticGraphrag.overview.coreInnovation')}</h4>
            <p className="text-gray-700 text-sm leading-relaxed">
              {t('agenticGraphrag.overview.innovationDescription')}
            </p>
            <ul className="list-disc list-inside text-sm text-gray-700 mt-2 space-y-1 ml-4">
              <li><strong>{t('agenticGraphrag.overview.fsmOrchestration')}</strong></li>
              <li><strong>{t('agenticGraphrag.overview.multiModel')}</strong></li>
              <li><strong>{t('agenticGraphrag.overview.vectorlessFallback')}</strong></li>
            </ul>
          </div>
        </div>
      )
    },
    {
      title: t('agenticGraphrag.pipeline.title'),
      icon: <CheckCircle2 className="w-5 h-5 text-green-600" />,
      content: (
        <div className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <h5 className="font-semibold text-green-900 mb-2 flex items-center">
                <CheckCircle2 className="w-4 h-4 mr-2" />
                {t('agenticGraphrag.pipeline.embedding.title')}
              </h5>
              <p className="text-sm text-gray-700">
                {t('agenticGraphrag.pipeline.embedding.description')}
              </p>
            </div>

            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <h5 className="font-semibold text-green-900 mb-2 flex items-center">
                <CheckCircle2 className="w-4 h-4 mr-2" />
                {t('agenticGraphrag.pipeline.parallelSearch.title')}
              </h5>
              <p className="text-sm text-gray-700">
                {t('agenticGraphrag.pipeline.parallelSearch.description')}
              </p>
            </div>

            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <h5 className="font-semibold text-green-900 mb-2 flex items-center">
                <CheckCircle2 className="w-4 h-4 mr-2" />
                {t('agenticGraphrag.pipeline.enrichment.title')}
              </h5>
              <p className="text-sm text-gray-700">
                {t('agenticGraphrag.pipeline.enrichment.description')}
              </p>
            </div>

            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <h5 className="font-semibold text-green-900 mb-2 flex items-center">
                <CheckCircle2 className="w-4 h-4 mr-2" />
                {t('agenticGraphrag.pipeline.synthesis.title')}
              </h5>
              <p className="text-sm text-gray-700">
                {t('agenticGraphrag.pipeline.synthesis.description')}
              </p>
            </div>
          </div>
        </div>
      )
    },
    {
      title: t('agenticGraphrag.capabilities.title'),
      icon: <Zap className="w-5 h-5 text-purple-600" />,
      content: (
        <div className="space-y-4">
          <div className="bg-purple-50 border-l-4 border-purple-500 p-4 rounded">
            <h5 className="font-semibold text-purple-900 mb-2">{t('agenticGraphrag.capabilities.multiModelTitle')}</h5>
            <p className="text-sm text-gray-700 mb-3">
              {t('agenticGraphrag.capabilities.multiModelDesc')}
            </p>
            <ul className="list-disc list-inside text-sm text-gray-700 space-y-1 ml-4">
              <li><strong>Gemini 3:</strong> {t('agenticGraphrag.capabilities.gemini')}</li>
              <li><strong>Kimi K2.5 Thinking:</strong> {t('agenticGraphrag.capabilities.kimi')}</li>
            </ul>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <h5 className="font-semibold text-gray-900 mb-2">{t('agenticGraphrag.capabilities.keyStrengths')}</h5>
              <div className="space-y-2">
                <div className="flex items-start">
                  <div className="bg-purple-100 rounded-full p-1 mr-2 mt-0.5">
                    <CheckCircle2 className="w-3 h-3 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{t('agenticGraphrag.capabilities.noTruncation.title')}</p>
                    <p className="text-xs text-gray-600">{t('agenticGraphrag.capabilities.noTruncation.description')}</p>
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="bg-purple-100 rounded-full p-1 mr-2 mt-0.5">
                    <CheckCircle2 className="w-3 h-3 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{t('agenticGraphrag.capabilities.passageCitations.title')}</p>
                    <p className="text-xs text-gray-600">{t('agenticGraphrag.capabilities.passageCitations.description')}</p>
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="bg-purple-100 rounded-full p-1 mr-2 mt-0.5">
                    <CheckCircle2 className="w-3 h-3 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{t('agenticGraphrag.capabilities.reasoningTrace.title')}</p>
                    <p className="text-xs text-gray-600">{t('agenticGraphrag.capabilities.reasoningTrace.description')}</p>
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="bg-purple-100 rounded-full p-1 mr-2 mt-0.5">
                    <CheckCircle2 className="w-3 h-3 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{t('agenticGraphrag.capabilities.sqlFallback.title')}</p>
                    <p className="text-xs text-gray-600">{t('agenticGraphrag.capabilities.sqlFallback.description')}</p>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h5 className="font-semibold text-gray-900 mb-2">{t('agenticGraphrag.capabilities.evolutionTitle')}</h5>
              <div className="space-y-2">
                <div className="bg-gray-50 p-2 rounded border border-gray-200">
                  <p className="text-sm font-medium text-gray-900">{t('agenticGraphrag.capabilities.evolution.fromHirag')}</p>
                  <p className="text-xs text-gray-600">{t('agenticGraphrag.capabilities.evolution.fromHiragDesc')}</p>
                </div>
                <div className="bg-gray-50 p-2 rounded border border-gray-200">
                  <p className="text-sm font-medium text-gray-900">{t('agenticGraphrag.capabilities.evolution.pageindexV3')}</p>
                  <p className="text-xs text-gray-600">{t('agenticGraphrag.capabilities.evolution.pageindexV3Desc')}</p>
                </div>
                <div className="bg-gray-50 p-2 rounded border border-gray-200">
                  <p className="text-sm font-medium text-gray-900">{t('agenticGraphrag.capabilities.evolution.current')}</p>
                  <p className="text-xs text-gray-600">{t('agenticGraphrag.capabilities.evolution.currentDesc')}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-amber-50 border border-amber-200 p-4 rounded-lg">
            <h5 className="font-semibold text-amber-900 mb-2">{t('agenticGraphrag.capabilities.netResult')}</h5>
            <p className="text-sm text-gray-700">
              {t('agenticGraphrag.capabilities.netResultDescription')}
            </p>
          </div>
        </div>
      )
    },
    {
      title: t('agenticGraphrag.technical.title'),
      icon: <Code className="w-5 h-5 text-blue-600" />,
      content: (
        <div className="space-y-4">
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <h5 className="font-semibold text-gray-900 mb-3">{t('agenticGraphrag.technical.architectureTitle')}</h5>
            <div className="space-y-3">
              <div>
                <p className="text-sm font-medium text-gray-900 mb-1">{t('agenticGraphrag.technical.agentFSM')}</p>
                <code className="text-xs bg-white px-2 py-1 rounded border border-gray-300 block overflow-x-auto">
                  graphrag/src/eleutheria_graphrag/agents/
                </code>
                <p className="text-xs text-gray-600 mt-1">
                  {t('agenticGraphrag.technical.agentFSMDesc')}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900 mb-1">{t('agenticGraphrag.technical.llmService')}</p>
                <code className="text-xs bg-white px-2 py-1 rounded border border-gray-300 block overflow-x-auto">
                  graphrag/src/eleutheria_graphrag/services/llm_service.py
                </code>
                <p className="text-xs text-gray-600 mt-1">
                  {t('agenticGraphrag.technical.llmServiceDesc')}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900 mb-1">{t('agenticGraphrag.technical.apiEndpoints')}</p>
                <code className="text-xs bg-white px-2 py-1 rounded border border-gray-300 block overflow-x-auto">
                  graphrag/src/eleutheria_graphrag/api/
                </code>
                <p className="text-xs text-gray-600 mt-1">
                  {t('agenticGraphrag.technical.apiEndpointsDesc')}
                </p>
              </div>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <h5 className="font-semibold text-blue-900 mb-2">{t('agenticGraphrag.technical.pipelineSteps')}</h5>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start">
                  <code className="bg-blue-100 px-2 py-0.5 rounded text-xs mr-2 mt-0.5 font-mono">1</code>
                  <span className="text-gray-700">{t('agenticGraphrag.technical.steps.embed')}</span>
                </li>
                <li className="flex items-start">
                  <code className="bg-blue-100 px-2 py-0.5 rounded text-xs mr-2 mt-0.5 font-mono">2</code>
                  <span className="text-gray-700">{t('agenticGraphrag.technical.steps.search')}</span>
                </li>
                <li className="flex items-start">
                  <code className="bg-blue-100 px-2 py-0.5 rounded text-xs mr-2 mt-0.5 font-mono">3</code>
                  <span className="text-gray-700">{t('agenticGraphrag.technical.steps.enrich')}</span>
                </li>
                <li className="flex items-start">
                  <code className="bg-blue-100 px-2 py-0.5 rounded text-xs mr-2 mt-0.5 font-mono">4</code>
                  <span className="text-gray-700">{t('agenticGraphrag.technical.steps.context')}</span>
                </li>
                <li className="flex items-start">
                  <code className="bg-blue-100 px-2 py-0.5 rounded text-xs mr-2 mt-0.5 font-mono">5</code>
                  <span className="text-gray-700">{t('agenticGraphrag.technical.steps.synthesize')}</span>
                </li>
              </ul>
            </div>

            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <h5 className="font-semibold text-blue-900 mb-2">{t('agenticGraphrag.technical.performanceMetrics')}</h5>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-700">{t('agenticGraphrag.technical.metrics.llmCalls')}:</span>
                  <span className="font-mono text-blue-900">2</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-700">{t('agenticGraphrag.technical.metrics.kgNodes')}:</span>
                  <span className="font-mono text-blue-900">{fmt(stats.nodes)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-700">{t('agenticGraphrag.technical.metrics.passages')}:</span>
                  <span className="font-mono text-blue-900">{fmt(stats.passages)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-700">{t('agenticGraphrag.technical.metrics.contextWindow')}:</span>
                  <span className="font-mono text-blue-900">~1M tokens</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-700">{t('agenticGraphrag.technical.metrics.responseTime')}:</span>
                  <span className="font-mono text-blue-900">&lt;5s</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-green-50 border border-green-200 p-4 rounded-lg">
            <h5 className="font-semibold text-green-900 mb-2">{t('agenticGraphrag.technical.reproducibility')}</h5>
            <p className="text-sm text-gray-700 mb-2">
              {t('agenticGraphrag.technical.reproducibilityDesc')}
            </p>
          </div>
        </div>
      )
    }
  ];

  return (
    <div className="max-w-6xl mx-auto p-6 font-body">
      <div className="mb-6">
        <h2 className="font-display text-3xl text-gray-900 mb-2">{t('agenticGraphrag.pageTitle')}</h2>
        <p className="text-gray-600">
          {t('agenticGraphrag.pageDescription')}
        </p>
      </div>

      <div className="space-y-3">
        {sections.map((section, index) => {
          const sectionId = section.title.toLowerCase().replace(/\s+/g, '-');
          const isExpanded = expandedSections.has(sectionId);

          return (
            <div key={index} className="border border-gray-200 rounded-lg overflow-hidden bg-white shadow-sm">
              <button
                onClick={() => toggleSection(sectionId)}
                className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  {section.icon}
                  <h3 className="font-display text-lg text-gray-900">{section.title}</h3>
                </div>
                {isExpanded ? (
                  <ChevronDown className="w-5 h-5 text-gray-500" />
                ) : (
                  <ChevronRight className="w-5 h-5 text-gray-500" />
                )}
              </button>

              {isExpanded && (
                <div className="p-6 pt-0 border-t border-gray-100">
                  {section.content}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="mt-8 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 p-6 rounded-lg">
        <h3 className="font-display text-xl text-gray-900 mb-3">{t('agenticGraphrag.summary.title')}</h3>
        <div className="space-y-2 text-sm text-gray-700">
          <p>
            <strong>{t('agenticGraphrag.summary.architecture')}:</strong> {t('agenticGraphrag.summary.architectureText')}
          </p>
          <p>
            <strong>{t('agenticGraphrag.summary.models')}:</strong> {t('agenticGraphrag.summary.modelsText')}
          </p>
          <p>
            <strong>{t('agenticGraphrag.summary.result')}:</strong> {t('agenticGraphrag.summary.resultText', { nodeCount: fmt(stats.nodes), passageCount: fmt(stats.passages) })}
          </p>
        </div>
      </div>
    </div>
  );
};

export default AgenticGraphRAGDetails;
