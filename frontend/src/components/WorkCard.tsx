import { Link } from 'react-router-dom';
import { BookOpen, FileText, Languages, Calendar } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from './ui/card';
import type { AncientWork } from '../types';

interface WorkCardProps {
  work: AncientWork;
}

export function WorkCard({ work }: WorkCardProps) {
  const { t } = useTranslation();

  // Format character count for display
  const formatChars = (chars: number | undefined): string => {
    if (!chars) return '0 chars';
    if (chars >= 1000000) {
      return `${(chars / 1000000).toFixed(1)}M chars`;
    } else if (chars >= 1000) {
      return `${(chars / 1000).toFixed(1)}K chars`;
    }
    return `${chars} chars`;
  };

  // Get language badge color
  const getLanguageBadge = (language: string) => {
    const colors = {
      grc: 'bg-blue-100 text-blue-800 border-blue-200',
      lat: 'bg-amber-100 text-amber-800 border-amber-200',
      eng: 'bg-green-100 text-green-800 border-green-200',
      unknown: 'bg-gray-100 text-gray-800 border-gray-200',
    };
    const labels = {
      grc: t('texts.greek'),
      lat: t('texts.latin'),
      eng: t('texts.english'),
      unknown: 'Unknown',
    };

    const lang = language.toLowerCase();
    const colorClass = colors[lang as keyof typeof colors] || colors.unknown;
    const label = labels[lang as keyof typeof labels] || language;

    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${colorClass}`}>
        <Languages className="w-3 h-3 mr-1" />
        {label}
      </span>
    );
  };

  // Get source badge color
  const getSourceBadge = (source: string) => {
    const sourceColors: Record<string, string> = {
      first1k: 'bg-purple-100 text-purple-800 border-purple-200',
      sblgnt: 'bg-indigo-100 text-indigo-800 border-indigo-200',
      'lxx-swete': 'bg-teal-100 text-teal-800 border-teal-200',
      perseus: 'bg-cyan-100 text-cyan-800 border-cyan-200',
      tlge: 'bg-orange-100 text-orange-800 border-orange-200',
    };

    const color = sourceColors[source.toLowerCase()] || 'bg-gray-100 text-gray-800 border-gray-200';

    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${color}`}>
        {source}
      </span>
    );
  };

  return (
    <Link to={`/texts/${work.work_id}`} className="block h-full">
      <Card
        variant="elevated"
        padding="lg"
        interactive
        className="h-full group hover:border-primary-500 transition-all duration-300 flex flex-col"
      >
        <CardHeader className="pb-4">
          <div className="flex justify-between items-start gap-2 mb-2">
            <CardTitle className="text-base line-clamp-2 group-hover:text-primary-700 transition-colors flex-grow">
              {work.title || 'Untitled Work'}
            </CardTitle>
            {getLanguageBadge(work.language || 'unknown')}
          </div>
          <CardDescription className="text-sm font-medium text-gray-700">
            {work.author || 'Unknown Author'}
          </CardDescription>
        </CardHeader>

        <CardContent className="flex-grow space-y-3">
          {/* Period Badge */}
          {work.period && (
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-academic-muted" />
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-50 text-primary-700 border border-primary-200">
                {work.period}
              </span>
            </div>
          )}

          {/* Statistics */}
          <div className="flex justify-between items-center text-sm text-academic-muted pt-2 border-t border-gray-100">
            <div className="flex items-center gap-1">
              <FileText className="w-4 h-4" />
              <span className="font-medium">{(work.passage_count || 0).toLocaleString()}</span>
              <span className="text-xs">{t('texts.passages')}</span>
            </div>
            <div className="text-xs">
              {formatChars(work.total_chars)}
            </div>
          </div>

          {/* Source & TLG Code */}
          <div className="flex items-center gap-2 flex-wrap">
            {getSourceBadge(work.source || 'unknown')}
            {work.tlg_code && (
              <span className="font-mono text-xs text-primary-600 bg-primary-50 px-2 py-0.5 rounded border border-primary-100">
                {work.tlg_code}
              </span>
            )}
          </div>

          {/* School badge if available */}
          {work.school && (
            <div className="text-xs text-gray-600 italic">
              {work.school}
            </div>
          )}
        </CardContent>

        <CardFooter className="pt-4 border-t border-gray-100">
          <div className="w-full flex items-center justify-between text-primary-600 group-hover:text-primary-700 transition-colors">
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4" />
              <span className="text-sm font-medium">{t('texts.readMore')}</span>
            </div>
            <span className="text-sm group-hover:translate-x-1 transition-transform duration-200">→</span>
          </div>
        </CardFooter>
      </Card>
    </Link>
  );
}
