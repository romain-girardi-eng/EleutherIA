import React from 'react';
import { motion } from 'framer-motion';
import {
  Award,
  BookOpen,
  Link2,
  FileText,
  CheckCircle,
  TrendingUp,
  Target
} from 'lucide-react';
import { useTranslation } from 'react-i18next';

// Inline type definition to support both legacy and new workflow formats
interface QualityMetrics {
  // Legacy fields
  citationCount?: number;
  sourceCount?: number;
  nodeRelevanceScore?: number;
  contextCoherence?: number;
  answerCompleteness?: number;
  overallQuality?: number; // 0-100
  // New SOTA workflow fields
  confidence_score?: number;
  quality_badge?: 'High' | 'Medium' | 'Low' | string;
  relevance_score?: number;
  grounding_score?: number;
  completeness_score?: number;
  caveats?: string[];
}

interface AnswerQualityMetricsProps {
  metrics: QualityMetrics;
  className?: string;
}

export const AnswerQualityMetrics: React.FC<AnswerQualityMetricsProps> = ({
  metrics,
  className = ''
}) => {
  const { t } = useTranslation();

  // Normalize metrics to handle both legacy and new formats
  const normalizedMetrics = {
    citationCount: metrics.citationCount ?? 0,
    sourceCount: metrics.sourceCount ?? 0,
    nodeRelevanceScore: metrics.nodeRelevanceScore ?? (metrics.relevance_score ? metrics.relevance_score / 100 : 0.7),
    contextCoherence: metrics.contextCoherence ?? (metrics.grounding_score ? metrics.grounding_score / 100 : 0.7),
    answerCompleteness: metrics.answerCompleteness ?? (metrics.completeness_score ? metrics.completeness_score / 100 : 0.7),
    overallQuality: metrics.overallQuality ?? metrics.confidence_score ?? 75,
    qualityBadge: metrics.quality_badge,
    caveats: metrics.caveats || [],
  };

  const getQualityLabel = (score: number): string => {
    // Use quality badge if available from new format
    if (normalizedMetrics.qualityBadge) {
      return normalizedMetrics.qualityBadge;
    }
    if (score >= 90) return t('graphrag.quality.excellent');
    if (score >= 75) return t('graphrag.quality.good');
    if (score >= 60) return t('graphrag.quality.fair');
    return t('graphrag.quality.needsImprovement');
  };

  const qualityLabel = getQualityLabel(normalizedMetrics.overallQuality);

  const metricItems = [
    {
      label: t('graphrag.quality.citationsLabel'),
      value: normalizedMetrics.citationCount,
      max: 20,
      score: (normalizedMetrics.citationCount / 20) * 100,
      icon: FileText,
      description: t('graphrag.quality.citationsDesc'),
      bgColor: 'bg-slate-100',
      iconColor: 'text-slate-600',
      barColor: 'from-slate-300 to-slate-500'
    },
    {
      label: t('graphrag.quality.sourcesLabel'),
      value: normalizedMetrics.sourceCount,
      max: 15,
      score: (normalizedMetrics.sourceCount / 15) * 100,
      icon: BookOpen,
      description: t('graphrag.quality.sourcesDesc'),
      bgColor: 'bg-stone-100',
      iconColor: 'text-stone-600',
      barColor: 'from-stone-300 to-stone-500'
    },
    {
      label: t('graphrag.quality.nodeRelevanceLabel'),
      value: `${Math.round(normalizedMetrics.nodeRelevanceScore * 100)}%`,
      max: 100,
      score: normalizedMetrics.nodeRelevanceScore * 100,
      icon: Target,
      description: t('graphrag.quality.nodeRelevanceDesc'),
      bgColor: 'bg-zinc-100',
      iconColor: 'text-zinc-600',
      barColor: 'from-zinc-300 to-zinc-500'
    },
    {
      label: t('graphrag.quality.contextCoherenceLabel'),
      value: `${Math.round(normalizedMetrics.contextCoherence * 100)}%`,
      max: 100,
      score: normalizedMetrics.contextCoherence * 100,
      icon: Link2,
      description: t('graphrag.quality.contextCoherenceDesc'),
      bgColor: 'bg-gray-100',
      iconColor: 'text-gray-600',
      barColor: 'from-gray-300 to-gray-500'
    },
    {
      label: t('graphrag.quality.completenessLabel'),
      value: `${Math.round(normalizedMetrics.answerCompleteness * 100)}%`,
      max: 100,
      score: normalizedMetrics.answerCompleteness * 100,
      icon: CheckCircle,
      description: t('graphrag.quality.completenessDesc'),
      bgColor: 'bg-neutral-100',
      iconColor: 'text-neutral-600',
      barColor: 'from-neutral-300 to-neutral-500'
    }
  ];

  return (
    <div className={`${className}`}>
      {/* Overall Quality Score */}
      <div className="bg-gradient-to-br from-primary-600 to-primary-700 text-white p-4 sm:p-6 rounded-t-2xl">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3 sm:gap-4">
            <div className="p-2 sm:p-3 bg-white/20 rounded-xl">
              <Award className="w-8 h-8 sm:w-10 sm:h-10" />
            </div>
            <div>
              <h2 className="text-xl sm:text-2xl font-bold mb-1">{t('graphrag.quality.title')}</h2>
              <p className="text-white/90 text-xs sm:text-sm">{t('graphrag.quality.subtitle')}</p>
            </div>
          </div>

          <div className="text-left sm:text-right flex sm:block items-baseline gap-3">
            <div className="text-4xl sm:text-6xl font-bold mb-0 sm:mb-1">{Math.round(normalizedMetrics.overallQuality)}</div>
            <div className="text-lg sm:text-xl font-semibold opacity-90">{qualityLabel}</div>
          </div>
        </div>

        {/* Overall Quality Bar */}
        <div className="mt-6">
          <div className="h-4 bg-white/20 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${normalizedMetrics.overallQuality}%` }}
              transition={{ duration: 1, ease: 'easeOut' }}
              className="h-full bg-white rounded-full shadow-lg"
            />
          </div>
          <div className="flex justify-between mt-2 text-sm text-white/80">
            <span>0</span>
            <span>50</span>
            <span>100</span>
          </div>
        </div>
      </div>

      {/* Detailed Metrics */}
      <div className="bg-white p-6 rounded-b-2xl shadow-xl">
        <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-primary-600" />
          {t('graphrag.quality.detailedBreakdown')}
        </h3>

        <div className="space-y-4">
          {metricItems.map((metric, index) => {
            const Icon = metric.icon;
            const percentage = Math.min(metric.score, 100);

            return (
              <motion.div
                key={metric.label}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1, duration: 0.5 }}
                className="group"
              >
                {/* Metric Header */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className={`p-2 ${metric.bgColor} rounded-lg`}>
                      <Icon className={`w-4 h-4 ${metric.iconColor}`} />
                    </div>
                    <div>
                      <div className="font-semibold text-gray-900">{metric.label}</div>
                      <div className="text-xs text-gray-600">{metric.description}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xl font-bold text-gray-900">{metric.value}</div>
                    <div className="text-xs text-gray-600">{Math.round(percentage)}%</div>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${percentage}%` }}
                    transition={{ delay: index * 0.1 + 0.2, duration: 0.8, ease: 'easeOut' }}
                    className={`h-full bg-gradient-to-r ${metric.barColor} rounded-full`}
                  />
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Quality Interpretation */}
        <div className="mt-6 p-4 bg-gray-50 border-2 border-gray-200 rounded-xl">
          <h4 className="font-bold text-gray-900 mb-2 text-sm">{t('graphrag.quality.whatThisMeans')}</h4>
          <div className="space-y-2 text-sm text-gray-700">
            {normalizedMetrics.overallQuality >= 90 && (
              <p>
                <span className="font-semibold text-green-700">{t('graphrag.quality.excellentQuality')}</span> {t('graphrag.quality.excellentQualityDesc')}
              </p>
            )}
            {normalizedMetrics.overallQuality >= 75 && normalizedMetrics.overallQuality < 90 && (
              <p>
                <span className="font-semibold text-blue-700">{t('graphrag.quality.goodQuality')}</span> {t('graphrag.quality.goodQualityDesc')}
              </p>
            )}
            {normalizedMetrics.overallQuality >= 60 && normalizedMetrics.overallQuality < 75 && (
              <p>
                <span className="font-semibold text-yellow-700">{t('graphrag.quality.fairQuality')}</span> {t('graphrag.quality.fairQualityDesc')}
              </p>
            )}
            {normalizedMetrics.overallQuality < 60 && (
              <p>
                <span className="font-semibold text-red-700">{t('graphrag.quality.needsImprovementQuality')}</span> {t('graphrag.quality.needsImprovementQualityDesc')}
              </p>
            )}
          </div>
        </div>

        {/* Quality Badges */}
        <div className="mt-4 flex flex-wrap gap-2">
          {normalizedMetrics.citationCount >= 10 && (
            <div className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-semibold flex items-center gap-1">
              <FileText className="w-3 h-3" />
              {t('graphrag.quality.wellCited')}
            </div>
          )}
          {normalizedMetrics.sourceCount >= 8 && (
            <div className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-xs font-semibold flex items-center gap-1">
              <BookOpen className="w-3 h-3" />
              {t('graphrag.quality.multiSource')}
            </div>
          )}
          {normalizedMetrics.nodeRelevanceScore >= 0.85 && (
            <div className="px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full text-xs font-semibold flex items-center gap-1">
              <Target className="w-3 h-3" />
              {t('graphrag.quality.highlyRelevant')}
            </div>
          )}
          {normalizedMetrics.contextCoherence >= 0.85 && (
            <div className="px-3 py-1 bg-cyan-100 text-cyan-800 rounded-full text-xs font-semibold flex items-center gap-1">
              <Link2 className="w-3 h-3" />
              {t('graphrag.quality.coherent')}
            </div>
          )}
          {normalizedMetrics.answerCompleteness >= 0.85 && (
            <div className="px-3 py-1 bg-emerald-100 text-emerald-800 rounded-full text-xs font-semibold flex items-center gap-1">
              <CheckCircle className="w-3 h-3" />
              {t('graphrag.quality.comprehensive')}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AnswerQualityMetrics;
