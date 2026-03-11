// frontend/src/components/kg/DetailPanel.tsx
import { X } from 'lucide-react';
import { getGraphTypeTheme, formatGraphNodeType } from '@/components/graphrag/graphTheme';
import type { KGNode } from '@/types';

interface DetailPanelProps {
  node: KGNode | null;
  onClose: () => void;
}

export default function DetailPanel({ node, onClose }: DetailPanelProps) {
  if (!node) return null;

  const theme = getGraphTypeTheme(node.type);

  return (
    <div className="absolute top-0 right-0 h-full w-80 bg-slate-900/95 border-l border-slate-700 backdrop-blur-sm z-20 overflow-y-auto">
      <div className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-3 h-3 rounded-full" style={{ backgroundColor: theme.color }} />
              <h3 className="font-semibold text-slate-100 text-base">{node.label}</h3>
            </div>
            <span
              className="text-xs px-1.5 py-0.5 rounded"
              style={{ backgroundColor: theme.tint, color: theme.text, border: `1px solid ${theme.border}` }}
            >
              {formatGraphNodeType(node.type)}
            </span>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-slate-800 rounded text-slate-400">
            <X className="w-4 h-4" />
          </button>
        </div>

        {node.period && (
          <div className="mb-3">
            <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">Period</div>
            <div className="text-sm text-slate-300">{node.period}</div>
          </div>
        )}

        {node.description && (
          <div className="mb-3">
            <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">Description</div>
            <div className="text-sm text-slate-300 leading-relaxed">{node.description}</div>
          </div>
        )}

        {node.school && (
          <div className="mb-3">
            <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">School</div>
            <div className="text-sm text-slate-300">{node.school}</div>
          </div>
        )}
      </div>
    </div>
  );
}
