import { useMemo, useState } from 'react';
import { Filter, XCircle, ChevronDown, ChevronRight } from 'lucide-react';
import { useKGWorkspace } from '../../context/KGWorkspaceContext';
import type { TimelineOverview } from '../../types';

const NODE_TYPE_OPTIONS: Array<{ value: string; label: string; emoji: string }> = [
  { value: 'person', label: 'Persons', emoji: '👤' },
  { value: 'work', label: 'Works', emoji: '📚' },
  { value: 'concept', label: 'Concepts', emoji: '💡' },
  { value: 'argument', label: 'Arguments', emoji: '⚖️' },
  { value: 'debate', label: 'Debates', emoji: '🗣️' },
  { value: 'reformulation', label: 'Reformulations', emoji: '🔄' },
  { value: 'quote', label: 'Quotes', emoji: '📝' },
];

function extractPeriods(timeline: TimelineOverview | null) {
  if (!timeline) return [];
  return Array.from(new Set(timeline.periods.map((period) => period.key).filter(Boolean)));
}

function extractSchools(timeline: TimelineOverview | null) {
  if (!timeline) return [];
  const schools = new Set<string>();
  timeline.periods.forEach((period) => {
    period.nodes.forEach((node) => {
      if (node.school) {
        schools.add(node.school);
      }
    });
  });
  return Array.from(schools);
}

function useFilterOptions(timeline: TimelineOverview | null) {
  const periodOptions = useMemo(() => extractPeriods(timeline), [timeline]);
  const schoolOptions = useMemo(() => extractSchools(timeline), [timeline]);
  return { periodOptions, schoolOptions };
}

export default function WorkspaceFilterBar() {
  const {
    state: { filters, timeline },
    setFilters,
  } = useKGWorkspace();
  const { periodOptions, schoolOptions } = useFilterOptions(timeline);
  const [search, setSearch] = useState(filters.searchTerm || '');
  const [isExpanded, setIsExpanded] = useState(false);

  const toggleValue = (key: 'nodeTypes' | 'periods' | 'schools', value: string) => {
    setFilters((prev) => {
      const current = new Set(prev[key]);
      if (current.has(value)) {
        current.delete(value);
      } else {
        current.add(value);
      }
      return {
        ...prev,
        [key]: Array.from(current),
      };
    });
  };

  const clearFilters = () => {
    setFilters({
      nodeTypes: [],
      periods: [],
      schools: [],
      relations: [],
      searchTerm: '',
    });
    setSearch('');
  };

  const applySearch = (value: string) => {
    setSearch(value);
    setFilters({ searchTerm: value });
  };

  // Count active filters for summary display
  const activePeriodsCount = filters.periods.length;
  const activeSchoolsCount = filters.schools.length;
  const hasActiveFilters = activePeriodsCount > 0 || activeSchoolsCount > 0;

  return (
    <div className="academic-card">
      <div className="flex flex-col gap-3">
        {/* Header with title and actions */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-sm font-medium text-academic-text">
            <Filter className="w-4 h-4 text-primary-600" />
            Coordinated Filters
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={clearFilters}
              className="inline-flex items-center gap-1 text-xs text-academic-muted hover:text-red-500 transition-colors"
            >
              <XCircle className="w-4 h-4" />
              Reset all
            </button>
          </div>
        </div>

        {/* Always visible: Node Types and Search */}
        <div className="flex flex-col gap-3">
          {/* Node Types - Always visible */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold text-academic-muted uppercase min-w-[90px]">Types:</span>
            <div className="flex flex-wrap gap-1.5">
              {NODE_TYPE_OPTIONS.map((option) => {
                const active = filters.nodeTypes.includes(option.value);
                return (
                  <button
                    key={option.value}
                    onClick={() => toggleValue('nodeTypes', option.value)}
                    className={`px-2 py-1 rounded-md border text-xs transition-colors ${
                      active
                        ? 'bg-primary-600 text-white border-primary-600'
                        : 'border-gray-200 text-academic-text hover:border-primary-300 hover:bg-primary-50'
                    }`}
                    title={option.label}
                  >
                    <span className="mr-0.5">{option.emoji}</span>
                    {option.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Search - Always visible */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-academic-muted uppercase min-w-[90px]">Search:</span>
            <input
              type="search"
              value={search}
              onChange={(event) => applySearch(event.target.value)}
              placeholder="Search labels, descriptions, or evidence…"
              className="flex-1 px-3 py-1.5 border border-gray-200 rounded-md focus:ring-2 focus:ring-primary-500 focus:outline-none text-xs"
            />
          </div>

          {/* Collapsible Advanced Filters */}
          <div className="border-t border-gray-200 pt-3">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center justify-between w-full text-left hover:bg-gray-50 rounded-md p-2 transition-colors"
            >
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-academic-muted uppercase">Advanced Filters</span>
                {hasActiveFilters && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-primary-100 text-primary-700 text-xs rounded-full">
                    {activePeriodsCount + activeSchoolsCount} active
                  </span>
                )}
              </div>
              {isExpanded ? (
                <ChevronDown className="w-4 h-4 text-academic-muted" />
              ) : (
                <ChevronRight className="w-4 h-4 text-academic-muted" />
              )}
            </button>

            {/* Collapsible content */}
            {isExpanded && (
              <div className="mt-3 space-y-3 animate-in slide-in-from-top-2 duration-200">
                {/* Periods */}
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs font-semibold text-academic-muted uppercase min-w-[90px]">Periods:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {periodOptions.map((period) => {
                      const active = filters.periods.includes(period);
                      return (
                        <button
                          key={period}
                          onClick={() => toggleValue('periods', period)}
                          className={`px-2 py-1 rounded-md border text-xs transition-colors ${
                            active
                              ? 'bg-amber-500 text-white border-amber-500'
                              : 'border-gray-200 text-academic-text hover:border-amber-400 hover:bg-amber-50'
                          }`}
                        >
                          {period}
                        </button>
                      );
                    })}
                    {periodOptions.length === 0 && (
                      <span className="text-xs text-academic-muted italic">Load timeline to unlock</span>
                    )}
                  </div>
                </div>

                {/* Schools */}
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs font-semibold text-academic-muted uppercase min-w-[90px]">Schools:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {schoolOptions.map((school) => {
                      const active = filters.schools.includes(school);
                      return (
                        <button
                          key={school}
                          onClick={() => toggleValue('schools', school)}
                          className={`px-2 py-1 rounded-md border text-xs transition-colors ${
                            active
                              ? 'bg-emerald-500 text-white border-emerald-500'
                              : 'border-gray-200 text-academic-text hover:border-emerald-400 hover:bg-emerald-50'
                          }`}
                        >
                          {school}
                        </button>
                      );
                    })}
                    {schoolOptions.length === 0 && (
                      <span className="text-xs text-academic-muted italic">No school metadata</span>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
