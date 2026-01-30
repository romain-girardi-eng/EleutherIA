import { Search, Filter, X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent } from './ui/card';

export interface WorkFiltersState {
  search: string;
  author: string;
  language: string;
  period: string;
  source: string;
}

interface WorkFiltersProps {
  filters: WorkFiltersState;
  onFilterChange: (filters: WorkFiltersState) => void;
  onReset: () => void;
  availableAuthors?: string[];
  availablePeriods?: string[];
  availableSources?: string[];
}

export function WorkFilters({
  filters,
  onFilterChange,
  onReset,
  availableAuthors = [],
  availablePeriods = [],
  availableSources = [],
}: WorkFiltersProps) {
  const { t } = useTranslation();
  const handleChange = (key: keyof WorkFiltersState, value: string) => {
    onFilterChange({
      ...filters,
      [key]: value,
    });
  };

  const hasActiveFilters =
    filters.search ||
    filters.author ||
    filters.language !== 'all' ||
    filters.period ||
    filters.source;

  return (
    <Card variant="elevated" padding="lg" className="mb-6">
      <CardContent noPadding>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-primary-600" />
            <h3 className="text-lg font-semibold text-gray-900">{t('search.filters')}</h3>
          </div>
          {hasActiveFilters && (
            <button
              onClick={onReset}
              className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
            >
              <X className="w-4 h-4" />
              {t('texts.reset')}
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {/* Search Input */}
          <div className="lg:col-span-2">
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">
              {t('common.search')}
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                id="search"
                type="text"
                placeholder={t('texts.searchAuthor')}
                value={filters.search}
                onChange={(e) => handleChange('search', e.target.value)}
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
              />
            </div>
          </div>

          {/* Author Filter */}
          <div>
            <label htmlFor="author" className="block text-sm font-medium text-gray-700 mb-1">
              {t('search.filterBy.author')}
            </label>
            <select
              id="author"
              value={filters.author}
              onChange={(e) => handleChange('author', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
            >
              <option value="">{t('texts.allAuthors')}</option>
              {availableAuthors.slice(0, 20).map((author) => (
                <option key={author} value={author}>
                  {author}
                </option>
              ))}
            </select>
          </div>

          {/* Language Filter */}
          <div>
            <label htmlFor="language" className="block text-sm font-medium text-gray-700 mb-1">
              {t('search.filterBy.language')}
            </label>
            <select
              id="language"
              value={filters.language}
              onChange={(e) => handleChange('language', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
            >
              <option value="all">{t('texts.allLanguages')}</option>
              <option value="grc">{t('texts.greek')}</option>
              <option value="lat">{t('texts.latin')}</option>
              <option value="eng">{t('texts.english')}</option>
              <option value="unknown">Unknown</option>
            </select>
          </div>

          {/* Period Filter */}
          <div>
            <label htmlFor="period" className="block text-sm font-medium text-gray-700 mb-1">
              {t('search.filterBy.period')}
            </label>
            <select
              id="period"
              value={filters.period}
              onChange={(e) => handleChange('period', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
            >
              <option value="">All Periods</option>
              {availablePeriods.map((period) => (
                <option key={period} value={period}>
                  {period}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Second Row - Source Filter */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mt-4">
          <div className="lg:col-span-2">
            <label htmlFor="source" className="block text-sm font-medium text-gray-700 mb-1">
              Source
            </label>
            <select
              id="source"
              value={filters.source}
              onChange={(e) => handleChange('source', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
            >
              <option value="">All Sources</option>
              {availableSources.map((source) => (
                <option key={source} value={source}>
                  {source}
                </option>
              ))}
            </select>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
