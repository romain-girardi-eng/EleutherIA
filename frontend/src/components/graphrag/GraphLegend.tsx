import { cn } from '../../utils/cn';

const LEGEND_ITEMS = [
  { type: 'person', label: 'Person', color: '#60a5fa' },
  { type: 'concept', label: 'Concept', color: '#c084fc' },
  { type: 'argument', label: 'Argument', color: '#f472b6' },
  { type: 'work', label: 'Work', color: '#fbbf24' },
  { type: 'school', label: 'School', color: '#4ade80' },
  { type: 'debate', label: 'Debate', color: '#fb7185' },
];

interface GraphLegendProps {
  className?: string;
}

export default function GraphLegend({ className }: GraphLegendProps) {
  return (
    <div
      className={cn(
        'flex items-center gap-3 px-3 py-2 bg-white/5 backdrop-blur-sm rounded-lg border border-white/10',
        className,
      )}
    >
      {LEGEND_ITEMS.map((item) => (
        <div key={item.type} className="flex items-center gap-1.5">
          <span
            className="inline-block w-2 h-2 rounded-full"
            style={{ backgroundColor: item.color }}
          />
          <span className="text-[10px] font-medium text-white/50">{item.label}</span>
        </div>
      ))}
    </div>
  );
}
