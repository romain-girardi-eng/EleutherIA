// frontend/src/components/kg/KGLegend.tsx
import { GRAPH_TYPE_THEMES, formatGraphNodeType } from '@/components/graphrag/graphTheme';

const LEGEND_TYPES = [
  'person', 'work', 'concept', 'argument', 'debate', 'school',
  'event', 'quote', 'passage', 'publication', 'synthesis', 'controversy',
];

export default function KGLegend() {
  return (
    <div className="absolute bottom-4 right-4 z-10 bg-slate-900/80 border border-slate-700 rounded-lg p-3 backdrop-blur-sm">
      <div className="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">Legend</div>
      <div className="grid grid-cols-2 gap-x-6 gap-y-1">
        {LEGEND_TYPES.map((type) => {
          const theme = GRAPH_TYPE_THEMES[type];
          if (!theme) return null;
          return (
            <div key={type} className="flex items-center gap-1.5 text-xs text-slate-300">
              <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: theme.color }} />
              {formatGraphNodeType(type)}
            </div>
          );
        })}
      </div>
    </div>
  );
}
