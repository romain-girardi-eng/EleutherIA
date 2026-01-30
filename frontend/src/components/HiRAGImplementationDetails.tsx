import React, { useState } from 'react';
import { ChevronDown, ChevronRight, ExternalLink, CheckCircle2, Zap, BookOpen, Code } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface ImplementationSection {
  title: string;
  icon: React.ReactNode;
  content: React.ReactNode;
}

const HiRAGImplementationDetails: React.FC = () => {
  const { t } = useTranslation();
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
      title: t('hirag.overview.title'),
      icon: <BookOpen className="w-5 h-5" />,
      content: (
        <div className="space-y-4">
          <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
            <h4 className="font-semibold text-blue-900 mb-2">{t('hirag.overview.originalResearch')}</h4>
            <p className="text-sm text-blue-800 mb-2">
              {t('hirag.overview.basedOn')}
            </p>
            <div className="bg-white p-3 rounded border border-blue-200">
              <p className="text-sm font-mono text-gray-700 mb-2">
                Huang, H., Wang, D., Zhang, Y., et al. (2025). "HiRAG: Retrieval-Augmented Generation with Hierarchical Knowledge."
                <em> arXiv preprint arXiv:2503.10150v3</em>.
              </p>
              <a
                href="https://arxiv.org/abs/2503.10150v3"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-blue-600 hover:text-blue-800 text-sm font-medium"
              >
                {t('hirag.overview.readPaper')} <ExternalLink className="w-4 h-4 ml-1" />
              </a>
            </div>
          </div>

          <div>
            <h4 className="font-semibold text-gray-900 mb-2">{t('hirag.overview.coreInnovation')}</h4>
            <p className="text-gray-700 text-sm leading-relaxed">
              {t('hirag.overview.innovationDescription')}
            </p>
            <ul className="list-disc list-inside text-sm text-gray-700 mt-2 space-y-1 ml-4">
              <li><strong>{t('hirag.overview.localKnowledge')}</strong></li>
              <li><strong>{t('hirag.overview.globalKnowledge')}</strong></li>
              <li><strong>{t('hirag.overview.bridgeKnowledge')}</strong></li>
            </ul>
            <p className="text-sm text-gray-600 mt-3 italic">
              {t('hirag.overview.paperResults')}
            </p>
          </div>
        </div>
      )
    },
    {
      title: t('hirag.implemented.title'),
      icon: <CheckCircle2 className="w-5 h-5 text-green-600" />,
      content: (
        <div className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <h5 className="font-semibold text-green-900 mb-2 flex items-center">
                <CheckCircle2 className="w-4 h-4 mr-2" />
                {t('hirag.implemented.hierarchical.title')}
              </h5>
              <p className="text-sm text-gray-700">
                <strong>Level-0:</strong> {t('hirag.implemented.hierarchical.level0')}<br/>
                <strong>Level-1:</strong> {t('hirag.implemented.hierarchical.level1')}<br/>
                <strong>Level-2:</strong> {t('hirag.implemented.hierarchical.level2')}
              </p>
            </div>

            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <h5 className="font-semibold text-green-900 mb-2 flex items-center">
                <CheckCircle2 className="w-4 h-4 mr-2" />
                {t('hirag.implemented.bridge.title')}
              </h5>
              <p className="text-sm text-gray-700 mb-2">
                {t('hirag.implemented.bridge.algorithm')}
              </p>
              <p className="text-xs text-gray-600 italic">
                {t('hirag.implemented.bridge.impact')}
              </p>
            </div>

            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <h5 className="font-semibold text-green-900 mb-2 flex items-center">
                <CheckCircle2 className="w-4 h-4 mr-2" />
                {t('hirag.implemented.perCommunity.title')}
              </h5>
              <p className="text-sm text-gray-700">
                {t('hirag.implemented.perCommunity.description')}
              </p>
            </div>

            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <h5 className="font-semibold text-green-900 mb-2 flex items-center">
                <CheckCircle2 className="w-4 h-4 mr-2" />
                {t('hirag.implemented.threeLevel.title')}
              </h5>
              <p className="text-sm text-gray-700">
                {t('hirag.implemented.threeLevel.description')}
              </p>
            </div>
          </div>
        </div>
      )
    },
    {
      title: t('hirag.adaptations.title'),
      icon: <Zap className="w-5 h-5 text-purple-600" />,
      content: (
        <div className="space-y-4">
          <div className="bg-purple-50 border-l-4 border-purple-500 p-4 rounded">
            <h5 className="font-semibold text-purple-900 mb-2">{t('hirag.adaptations.keyDifference')}</h5>
            <p className="text-sm text-gray-700 mb-3">
              {t('hirag.adaptations.summariesIntro')}
            </p>
            <ul className="list-disc list-inside text-sm text-gray-700 space-y-1 ml-4">
              <li><strong>Claude Opus 4.1:</strong> {t('hirag.adaptations.opus')}</li>
              <li><strong>GPT-5-high:</strong> {t('hirag.adaptations.gpt5')}</li>
              <li><strong>{t('hirag.adaptations.humanReview')}:</strong> {t('hirag.adaptations.humanReviewDesc')}</li>
            </ul>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <h5 className="font-semibold text-gray-900 mb-2">{t('hirag.adaptations.whyTitle')}</h5>
              <div className="space-y-2">
                <div className="flex items-start">
                  <div className="bg-purple-100 rounded-full p-1 mr-2 mt-0.5">
                    <CheckCircle2 className="w-3 h-3 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{t('hirag.adaptations.quality.title')}</p>
                    <p className="text-xs text-gray-600">{t('hirag.adaptations.quality.description')}</p>
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="bg-purple-100 rounded-full p-1 mr-2 mt-0.5">
                    <CheckCircle2 className="w-3 h-3 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{t('hirag.adaptations.consistency.title')}</p>
                    <p className="text-xs text-gray-600">{t('hirag.adaptations.consistency.description')}</p>
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="bg-purple-100 rounded-full p-1 mr-2 mt-0.5">
                    <CheckCircle2 className="w-3 h-3 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{t('hirag.adaptations.performance.title')}</p>
                    <p className="text-xs text-gray-600">{t('hirag.adaptations.performance.description')}</p>
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="bg-purple-100 rounded-full p-1 mr-2 mt-0.5">
                    <CheckCircle2 className="w-3 h-3 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{t('hirag.adaptations.rigor.title')}</p>
                    <p className="text-xs text-gray-600">{t('hirag.adaptations.rigor.description')}</p>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h5 className="font-semibold text-gray-900 mb-2">{t('hirag.adaptations.notImplemented')}</h5>
              <div className="space-y-2">
                <div className="bg-gray-50 p-2 rounded border border-gray-200">
                  <p className="text-sm font-medium text-gray-900">{t('hirag.adaptations.gmm.title')}</p>
                  <p className="text-xs text-gray-600">{t('hirag.adaptations.gmm.description')}</p>
                </div>
                <div className="bg-gray-50 p-2 rounded border border-gray-200">
                  <p className="text-sm font-medium text-gray-900">{t('hirag.adaptations.sparsity.title')}</p>
                  <p className="text-xs text-gray-600">{t('hirag.adaptations.sparsity.description')}</p>
                </div>
                <div className="bg-gray-50 p-2 rounded border border-gray-200">
                  <p className="text-sm font-medium text-gray-900">{t('hirag.adaptations.metaAttributes.title')}</p>
                  <p className="text-xs text-gray-600">{t('hirag.adaptations.metaAttributes.description')}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-amber-50 border border-amber-200 p-4 rounded-lg">
            <h5 className="font-semibold text-amber-900 mb-2">{t('hirag.adaptations.netResult')}</h5>
            <p className="text-sm text-gray-700">
              {t('hirag.adaptations.netResultDescription')}
            </p>
          </div>
        </div>
      )
    },
    {
      title: t('hirag.technical.title'),
      icon: <Code className="w-5 h-5 text-blue-600" />,
      content: (
        <div className="space-y-4">
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <h5 className="font-semibold text-gray-900 mb-3">{t('hirag.technical.architectureTitle')}</h5>
            <div className="space-y-3">
              <div>
                <p className="text-sm font-medium text-gray-900 mb-1">{t('hirag.technical.backendService')}</p>
                <code className="text-xs bg-white px-2 py-1 rounded border border-gray-300 block overflow-x-auto">
                  backend/services/hirag_service.py
                </code>
                <p className="text-xs text-gray-600 mt-1">
                  {t('hirag.technical.backendServiceDesc')}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900 mb-1">{t('hirag.technical.summaryLoader')}</p>
                <code className="text-xs bg-white px-2 py-1 rounded border border-gray-300 block overflow-x-auto">
                  backend/services/hirag_summary_loader.py
                </code>
                <p className="text-xs text-gray-600 mt-1">
                  {t('hirag.technical.summaryLoaderDesc')}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900 mb-1">{t('hirag.technical.apiEndpoints')}</p>
                <code className="text-xs bg-white px-2 py-1 rounded border border-gray-300 block overflow-x-auto">
                  backend/api/hirag_routes.py
                </code>
                <p className="text-xs text-gray-600 mt-1">
                  {t('hirag.technical.apiEndpointsDesc')}
                </p>
              </div>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <h5 className="font-semibold text-blue-900 mb-2">{t('hirag.technical.queryModes')}</h5>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start">
                  <code className="bg-blue-100 px-2 py-0.5 rounded text-xs mr-2 mt-0.5 font-mono">hi</code>
                  <span className="text-gray-700">{t('hirag.technical.modes.hi')}</span>
                </li>
                <li className="flex items-start">
                  <code className="bg-blue-100 px-2 py-0.5 rounded text-xs mr-2 mt-0.5 font-mono">hi_bridge</code>
                  <span className="text-gray-700">{t('hirag.technical.modes.hiBridge')}</span>
                </li>
                <li className="flex items-start">
                  <code className="bg-blue-100 px-2 py-0.5 rounded text-xs mr-2 mt-0.5 font-mono">hi_local</code>
                  <span className="text-gray-700">{t('hirag.technical.modes.hiLocal')}</span>
                </li>
                <li className="flex items-start">
                  <code className="bg-blue-100 px-2 py-0.5 rounded text-xs mr-2 mt-0.5 font-mono">hi_global</code>
                  <span className="text-gray-700">{t('hirag.technical.modes.hiGlobal')}</span>
                </li>
                <li className="flex items-start">
                  <code className="bg-blue-100 px-2 py-0.5 rounded text-xs mr-2 mt-0.5 font-mono">hi_nobridge</code>
                  <span className="text-gray-700">{t('hirag.technical.modes.hiNoBridge')}</span>
                </li>
              </ul>
            </div>

            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <h5 className="font-semibold text-blue-900 mb-2">{t('hirag.technical.performanceMetrics')}</h5>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-700">{t('hirag.technical.metrics.globalSummaries')}:</span>
                  <span className="font-mono text-blue-900">14</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-700">{t('hirag.technical.metrics.communitySummaries')}:</span>
                  <span className="font-mono text-blue-900">11</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-700">{t('hirag.technical.metrics.entityNodes')}:</span>
                  <span className="font-mono text-blue-900">503</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-700">{t('hirag.technical.metrics.bridgeCoverage')}:</span>
                  <span className="font-mono text-blue-900">38-83%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-700">{t('hirag.technical.metrics.responseTime')}:</span>
                  <span className="font-mono text-blue-900">&lt;5s</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-green-50 border border-green-200 p-4 rounded-lg">
            <h5 className="font-semibold text-green-900 mb-2">{t('hirag.technical.reproducibility')}</h5>
            <p className="text-sm text-gray-700 mb-2">
              {t('hirag.technical.reproducibilityDesc')}
            </p>
            <p className="text-xs text-gray-600">
              {t('hirag.technical.reproducibilityMetadata')}
            </p>
          </div>
        </div>
      )
    },
    {
      title: t('hirag.comparison.title'),
      icon: <Zap className="w-5 h-5 text-yellow-600" />,
      content: (
        <div className="space-y-4">
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white border border-gray-300 text-sm">
              <thead className="bg-gray-100">
                <tr>
                  <th className="border border-gray-300 px-4 py-2 text-left font-semibold">{t('hirag.comparison.table.feature')}</th>
                  <th className="border border-gray-300 px-4 py-2 text-left font-semibold">{t('hirag.comparison.table.paperHiRAG')}</th>
                  <th className="border border-gray-300 px-4 py-2 text-left font-semibold">{t('hirag.comparison.table.ourImplementation')}</th>
                  <th className="border border-gray-300 px-4 py-2 text-left font-semibold">{t('hirag.comparison.table.impact')}</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="border border-gray-300 px-4 py-2 font-medium">{t('hirag.comparison.table.hierarchicalStructure')}</td>
                  <td className="border border-gray-300 px-4 py-2">{t('hirag.comparison.table.multiLayer')}</td>
                  <td className="border border-gray-300 px-4 py-2">{t('hirag.comparison.table.threeLevels')}</td>
                  <td className="border border-gray-300 px-4 py-2 text-green-700">{t('hirag.comparison.table.equivalent')}</td>
                </tr>
                <tr className="bg-gray-50">
                  <td className="border border-gray-300 px-4 py-2 font-medium">{t('hirag.comparison.table.shortestPath')}</td>
                  <td className="border border-gray-300 px-4 py-2">{t('hirag.comparison.table.algorithm2')}</td>
                  <td className="border border-gray-300 px-4 py-2">{t('hirag.comparison.table.implemented')}</td>
                  <td className="border border-gray-300 px-4 py-2 text-green-700">+15 pts</td>
                </tr>
                <tr>
                  <td className="border border-gray-300 px-4 py-2 font-medium">{t('hirag.comparison.table.perCommunity')}</td>
                  <td className="border border-gray-300 px-4 py-2">✅ m=2</td>
                  <td className="border border-gray-300 px-4 py-2">✅ m=2</td>
                  <td className="border border-gray-300 px-4 py-2 text-green-700">{t('hirag.comparison.table.equivalent')}</td>
                </tr>
                <tr className="bg-gray-50">
                  <td className="border border-gray-300 px-4 py-2 font-medium">{t('hirag.comparison.table.summaryQuality')}</td>
                  <td className="border border-gray-300 px-4 py-2">DeepSeek-V3</td>
                  <td className="border border-gray-300 px-4 py-2">🌟 Opus + GPT-5</td>
                  <td className="border border-gray-300 px-4 py-2 text-blue-700 font-semibold">{t('hirag.comparison.table.higher')}</td>
                </tr>
                <tr>
                  <td className="border border-gray-300 px-4 py-2 font-medium">{t('hirag.comparison.table.humanReview')}</td>
                  <td className="border border-gray-300 px-4 py-2">{t('hirag.comparison.table.none')}</td>
                  <td className="border border-gray-300 px-4 py-2">{t('hirag.comparison.table.expertValidated')}</td>
                  <td className="border border-gray-300 px-4 py-2 text-blue-700 font-semibold">{t('hirag.comparison.table.higher')}</td>
                </tr>
                <tr className="bg-gray-50">
                  <td className="border border-gray-300 px-4 py-2 font-medium">{t('hirag.comparison.table.stability')}</td>
                  <td className="border border-gray-300 px-4 py-2">{t('hirag.comparison.table.dynamic')}</td>
                  <td className="border border-gray-300 px-4 py-2">{t('hirag.comparison.table.preComputed')}</td>
                  <td className="border border-gray-300 px-4 py-2 text-blue-700 font-semibold">{t('hirag.comparison.table.higher')}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded">
            <h5 className="font-semibold text-yellow-900 mb-2">{t('hirag.comparison.expectedPerformance')}</h5>
            <p className="text-sm text-gray-700 mb-2">
              {t('hirag.comparison.performanceIntro')}
            </p>
            <ul className="list-disc list-inside text-sm text-gray-700 space-y-1 ml-4">
              <li>{t('hirag.comparison.winRate')}</li>
              <li>{t('hirag.comparison.recallCoverage')}</li>
              <li>{t('hirag.comparison.higherQuality')}</li>
              <li>{t('hirag.comparison.consistency')}</li>
            </ul>
          </div>

          <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
            <h5 className="font-semibold text-blue-900 mb-2">{t('hirag.comparison.academicNote')}</h5>
            <p className="text-sm text-gray-700">
              {t('hirag.comparison.academicNoteText')}
            </p>
          </div>
        </div>
      )
    }
  ];

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">{t('hirag.pageTitle')}</h2>
        <p className="text-gray-600">
          {t('hirag.pageDescription')}
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
                  <h3 className="text-lg font-semibold text-gray-900">{section.title}</h3>
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
        <h3 className="text-xl font-bold text-gray-900 mb-3">{t('hirag.summary.title')}</h3>
        <div className="space-y-2 text-sm text-gray-700">
          <p>
            <strong>{t('hirag.summary.tookFromPaper')}:</strong> {t('hirag.summary.tookFromPaperText')}
          </p>
          <p>
            <strong>{t('hirag.summary.adapted')}:</strong> {t('hirag.summary.adaptedText')}
          </p>
          <p>
            <strong>{t('hirag.summary.why')}:</strong> {t('hirag.summary.whyText')}
          </p>
        </div>
      </div>
    </div>
  );
};

export default HiRAGImplementationDetails;
