import { cn } from '../../utils/cn';
import { formatGraphNodeType, getGraphTypeTheme } from './graphTheme';

const DEFAULT_TYPES = ['person', 'concept', 'argument', 'work', 'school', 'debate'];

interface GraphLegendProps {
  className?: string;
  types?: string[];
}

export default function GraphLegend({ className, types }: GraphLegendProps) {
  const legendTypes = (types && types.length > 0 ? types : DEFAULT_TYPES).slice(0, 5);

  return (
    <div
      className={cn(
        'flex flex-wrap items-center gap-1.5 rounded-2xl border border-stone-200/80 bg-white/82 px-2.5 py-2 shadow-[0_16px_36px_-28px_rgba(120,53,15,0.3)] backdrop-blur-xl',
        className,
      )}
    >
      {legendTypes.map((type) => {
        const theme = getGraphTypeTheme(type);

        return (
          <div
            key={type}
            className="flex items-center gap-1.5 rounded-full border px-2 py-1"
            style={{
              borderColor: theme.border,
              backgroundColor: theme.tint,
            }}
          >
            <span
              className="inline-block h-2.5 w-2.5 rounded-full shadow-[0_0_0_4px_rgba(255,255,255,0.72)]"
              style={{ backgroundColor: theme.color }}
            />
            <span
              className="text-[10px] font-medium"
              style={{ color: theme.text }}
            >
              {formatGraphNodeType(type)}
            </span>
          </div>
        );
      })}
    </div>
  );
}
