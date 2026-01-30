import { memo, useMemo } from 'react';
import { Clock } from 'lucide-react';
import { useKGWorkspace } from '../../context/KGWorkspaceContext';
import AccordionPanel from '../mobile/AccordionPanel';
import type { TimelineNodeSummary, TimelinePeriodSummary } from '../../types';

const MIN_NODE_COUNT = 6;

function formatYear(year?: number | null) {
  if (year === null || year === undefined) {
    return '';
  }
  if (year < 0) {
    return `${Math.abs(year)} BCE`;
  }
  if (year === 0) {
    return '0';
  }
  return `${year} CE`;
}

function periodWidth(period: TimelinePeriodSummary, minYear?: number | null, maxYear?: number | null) {
  if (minYear === null || minYear === undefined || maxYear === null || maxYear === undefined) {
    return 1;
  }
  const start = period.startYear ?? minYear;
  const end = period.endYear ?? start;
  const clampedStart = Math.max(minYear, start);
  const clampedEnd = Math.min(maxYear, end);
  const span = Math.max(clampedEnd - clampedStart, 50); // enforce minimum width
  return span;
}

function normalizeWidths(periods: TimelinePeriodSummary[], minYear?: number | null, maxYear?: number | null) {
  const spans = periods.map((period) => periodWidth(period, minYear, maxYear));
  const total = spans.reduce((sum, span) => sum + span, 0);
  return periods.map((period, index) => ({
    period,
    width: total > 0 ? (spans[index] / total) * 100 : 100 / periods.length,
  }));
}

function TimelinePanelComponent() {
  const {
    state: { timeline, loading },
    updateSelection,
  } = useKGWorkspace();

  const normalized = useMemo(() => {
    if (!timeline) {
      return [];
    }
    return normalizeWidths(timeline.periods, timeline.range.minYear, timeline.range.maxYear);
  }, [timeline]);

  const totalPeriods = timeline?.periods.length || 0;
  const timeRange =
    timeline && timeline.range.minYear !== undefined && timeline.range.maxYear !== undefined
      ? `${formatYear(timeline.range.minYear)} → ${formatYear(timeline.range.maxYear)}`
      : null;

  if (loading && !timeline) {
    return (
      <AccordionPanel
        title="Chrono-Storyline"
        icon={<Clock className="w-5 h-5" />}
        defaultExpanded={false}
      >
        <div className="py-16 text-center text-academic-muted text-sm">Loading timeline…</div>
      </AccordionPanel>
    );
  }

  if (!timeline || timeline.periods.length === 0) {
    return (
      <AccordionPanel
        title="Chrono-Storyline"
        icon={<Clock className="w-5 h-5" />}
        defaultExpanded={false}
      >
        <div className="py-16 text-center text-academic-muted text-sm">
          Timeline data is unavailable for the current filter selection.
        </div>
      </AccordionPanel>
    );
  }

  return (
    <AccordionPanel
      title="Chrono-Storyline"
      icon={<Clock className="w-5 h-5" />}
      badge={`${totalPeriods} periods`}
      defaultExpanded={false}
    >
      {timeRange && (
        <div className="text-xs text-academic-muted mb-4">
          {timeRange}
        </div>
      )}

      <div className="overflow-x-auto -mx-4 px-4 pb-2">
        {/* Stack vertically on mobile, horizontal scroll on larger screens */}
        <div className="flex flex-col sm:flex-row sm:min-w-[640px] gap-4 sm:gap-0">
          {normalized.map(({ period, width }) => (
            <TimelinePeriodBlock
              key={period.key}
              period={period}
              width={width}
              onSelectNode={(node) =>
                updateSelection({
                  nodes: [node.id],
                  focusNodeId: node.id,
                })
              }
            />
          ))}
        </div>
      </div>
    </AccordionPanel>
  );
}

interface TimelinePeriodBlockProps {
  period: TimelinePeriodSummary;
  width: number;
  onSelectNode: (node: TimelineNodeSummary) => void;
}

function TimelinePeriodBlock({ period, width, onSelectNode }: TimelinePeriodBlockProps) {
  const nodes = useMemo(() => {
    const sorted = [...period.nodes].sort((a, b) => {
      if (a.startYear !== undefined && b.startYear !== undefined) {
        return (a.startYear ?? 0) - (b.startYear ?? 0);
      }
      if (a.relationCount && b.relationCount) {
        return b.relationCount - a.relationCount;
      }
      return (a.label || '').localeCompare(b.label || '');
    });
    return sorted.slice(0, Math.max(MIN_NODE_COUNT, Math.round(period.nodes.length * 0.25)));
  }, [period.nodes]);

  // On mobile (< 640px): full width, stacked vertically
  // On desktop (≥ 640px): proportional width based on period span
  return (
    <div
      className="border border-gray-200 rounded-lg p-4 mr-0 sm:mr-4 last:mr-0 bg-white flex-shrink-0"
      style={{ minWidth: '220px', flex: `0 0 ${width}%` }}
    >
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="text-xs uppercase text-academic-muted font-semibold">{period.label}</div>
          <div className="text-xs text-academic-muted">
            {formatYear(period.startYear)} — {formatYear(period.endYear)}
          </div>
        </div>
        <div className="text-xs text-academic-muted text-right">
          {Object.entries(period.counts)
            .map(([type, count]) => `${count} ${type}`)
            .slice(0, 2)
            .join(' • ')}
        </div>
      </div>
      <div className="space-y-2">
        {nodes.map((node) => (
          <button
            key={node.id}
            onClick={() => onSelectNode(node)}
            className="w-full text-left px-3 py-2 border border-gray-200 rounded-md hover:border-primary-400 hover:bg-primary-50 transition-colors"
          >
            <div className="flex items-center justify-between text-sm font-medium text-academic-text">
              <span className="truncate pr-2">{node.label}</span>
              <span className="text-xs text-academic-muted">{formatYear(node.startYear)}</span>
            </div>
            {node.school && <div className="text-xs text-academic-muted">{node.school}</div>}
            {node.relatedTypes && node.relatedTypes.length > 0 && (
              <div className="mt-1 flex flex-wrap gap-1">
                {node.relatedTypes.map((relation) => (
                  relation && (
                    <span key={relation} className="text-[10px] uppercase tracking-wide bg-gray-100 px-1.5 py-0.5 rounded">
                      {relation.replace(/_/g, ' ')}
                    </span>
                  )
                ))}
              </div>
            )}
          </button>
        ))}
        {period.nodes.length > nodes.length && (
          <div className="text-xs text-academic-muted italic">
            +{period.nodes.length - nodes.length} additional nodes hidden for clarity
          </div>
        )}
      </div>
    </div>
  );
}

export const TimelinePanel = memo(TimelinePanelComponent);
export default TimelinePanel;
