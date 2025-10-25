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

// Inline type definition to avoid module caching issues
interface QualityMetrics {
  citationCount: number;
  sourceCount: number;
  nodeRelevanceScore: number;
  contextCoherence: number;
  answerCompleteness: number;
  overallQuality: number; // 0-100
}

interface AnswerQualityMetricsProps {
  metrics: QualityMetrics;
  className?: string;
}

export const AnswerQualityMetrics: React.FC<AnswerQualityMetricsProps> = ({
  metrics,
  className = ''
}) => {
  const getQualityColor = (score: number): string => {
    if (score >= 90) return 'green';
    if (score >= 75) return 'blue';
    if (score >= 60) return 'yellow';
    return 'red';
  };

  const getQualityLabel = (score: number): string => {
    if (score >= 90) return 'Excellent';
    if (score >= 75) return 'Good';
    if (score >= 60) return 'Fair';
    return 'Needs Improvement';
  };

  const qualityColor = getQualityColor(metrics.overallQuality);
  const qualityLabel = getQualityLabel(metrics.overallQuality);

  const metricItems = [
    {
      label: 'Citations',
      value: metrics.citationCount,
      max: 20,
      score: (metrics.citationCount / 20) * 100,
      icon: FileText,
      description: 'Number of citations provided',
      bgColor: 'bg-slate-100',
      iconColor: 'text-slate-600',
      barColor: 'from-slate-300 to-slate-500'
    },
    {
      label: 'Sources',
      value: metrics.sourceCount,
      max: 15,
      score: (metrics.sourceCount / 15) * 100,
      icon: BookOpen,
      description: 'Unique sources referenced',
      bgColor: 'bg-stone-100',
      iconColor: 'text-stone-600',
      barColor: 'from-stone-300 to-stone-500'
    },
    {
      label: 'Node Relevance',
      value: `${Math.round(metrics.nodeRelevanceScore * 100)}%`,
      max: 100,
      score: metrics.nodeRelevanceScore * 100,
      icon: Target,
      description: 'Relevance of retrieved nodes',
      bgColor: 'bg-zinc-100',
      iconColor: 'text-zinc-600',
      barColor: 'from-zinc-300 to-zinc-500'
    },
    {
      label: 'Context Coherence',
      value: `${Math.round(metrics.contextCoherence * 100)}%`,
      max: 100,
      score: metrics.contextCoherence * 100,
      icon: Link2,
      description: 'How well context fits together',
      bgColor: 'bg-gray-100',
      iconColor: 'text-gray-600',
      barColor: 'from-gray-300 to-gray-500'
    },
    {
      label: 'Completeness',
      value: `${Math.round(metrics.answerCompleteness * 100)}%`,
      max: 100,
      score: metrics.answerCompleteness * 100,
      icon: CheckCircle,
      description: 'Answer thoroughness',
      bgColor: 'bg-neutral-100',
      iconColor: 'text-neutral-600',
      barColor: 'from-neutral-300 to-neutral-500'
    }
  ];

  return (
    <div className={`${className}`}>
      {/* Overall Quality Score */}
      <div className="bg-gradient-to-br from-primary-600 to-primary-700 text-white p-6 rounded-t-2xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-white/20 rounded-xl">
              <Award className="w-10 h-10" />
            </div>
            <div>
              <h2 className="text-2xl font-bold mb-1">Answer Quality</h2>
              <p className="text-white/90 text-sm">Comprehensive quality assessment</p>
            </div>
          </div>

          <div className="text-right">
            <div className="text-6xl font-bold mb-1">{Math.round(metrics.overallQuality)}</div>
            <div className="text-xl font-semibold opacity-90">{qualityLabel}</div>
          </div>
        </div>

        {/* Overall Quality Bar */}
        <div className="mt-6">
          <div className="h-4 bg-white/20 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${metrics.overallQuality}%` }}
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
          Detailed Breakdown
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
          <h4 className="font-bold text-gray-900 mb-2 text-sm">What This Means:</h4>
          <div className="space-y-2 text-sm text-gray-700">
            {metrics.overallQuality >= 90 && (
              <p>
                <span className="font-semibold text-green-700">Excellent quality:</span> This answer is well-grounded
                in multiple sources, highly relevant, and thoroughly addresses your question with proper citations.
              </p>
            )}
            {metrics.overallQuality >= 75 && metrics.overallQuality < 90 && (
              <p>
                <span className="font-semibold text-blue-700">Good quality:</span> This answer provides solid
                information with adequate citations and relevance, though there may be room for additional detail.
              </p>
            )}
            {metrics.overallQuality >= 60 && metrics.overallQuality < 75 && (
              <p>
                <span className="font-semibold text-yellow-700">Fair quality:</span> This answer addresses your
                question but may benefit from more sources or deeper context. Consider refining your query.
              </p>
            )}
            {metrics.overallQuality < 60 && (
              <p>
                <span className="font-semibold text-red-700">Needs improvement:</span> This answer may lack sufficient
                citations or context. Try rephrasing your question or being more specific about what you're looking for.
              </p>
            )}
          </div>
        </div>

        {/* Quality Badges */}
        <div className="mt-4 flex flex-wrap gap-2">
          {metrics.citationCount >= 10 && (
            <div className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-semibold flex items-center gap-1">
              <FileText className="w-3 h-3" />
              Well-Cited
            </div>
          )}
          {metrics.sourceCount >= 8 && (
            <div className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-xs font-semibold flex items-center gap-1">
              <BookOpen className="w-3 h-3" />
              Multi-Source
            </div>
          )}
          {metrics.nodeRelevanceScore >= 0.85 && (
            <div className="px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full text-xs font-semibold flex items-center gap-1">
              <Target className="w-3 h-3" />
              Highly Relevant
            </div>
          )}
          {metrics.contextCoherence >= 0.85 && (
            <div className="px-3 py-1 bg-cyan-100 text-cyan-800 rounded-full text-xs font-semibold flex items-center gap-1">
              <Link2 className="w-3 h-3" />
              Coherent
            </div>
          )}
          {metrics.answerCompleteness >= 0.85 && (
            <div className="px-3 py-1 bg-emerald-100 text-emerald-800 rounded-full text-xs font-semibold flex items-center gap-1">
              <CheckCircle className="w-3 h-3" />
              Comprehensive
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AnswerQualityMetrics;
