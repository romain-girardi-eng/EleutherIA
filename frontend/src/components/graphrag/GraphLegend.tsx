import { cn } from '../../utils/cn';

const LEGEND_ITEMS = [
  { type: 'person', label: 'Person', color: '#60A5FA' },
  { type: 'concept', label: 'Concept', color: '#4ADE80' },
  { type: 'argument', label: 'Argument', color: '#C084FC' },
  { type: 'work', label: 'Work', color: '#FBBF24' },
];

interface GraphLegendProps {
  className?: string;
}

export default function GraphLegend({ className }: GraphLegendProps) {
  return (
    <div className={cn('flex items-center gap-3 px-3 py-2 bg-white/90 backdrop-blur-sm rounded-lg border border-gray-100 shadow-sm', className)}>
      {LEGEND_ITEMS.map((item) => (
        <div key={item.type} className="flex items-center gap-1.5">
          <span
            className="inline-block w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: item.color }}
          />
          <span className="text-[10px] font-medium text-gray-500">{item.label}</span>
        </div>
      ))}
    </div>
  );
}
