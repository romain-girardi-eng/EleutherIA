// frontend/src/components/kg/NodeTooltip.tsx
import { useEffect, useState } from 'react';
import { useSigma } from '@react-sigma/core';
import { getGraphTypeTheme, formatGraphNodeType } from '@/components/graphrag/graphTheme';
import type { KGNodeAttributes } from '@/types/sigma';

export default function NodeTooltip() {
  const sigma = useSigma();
  const [tooltip, setTooltip] = useState<{
    x: number;
    y: number;
    attrs: KGNodeAttributes;
  } | null>(null);

  useEffect(() => {
    const graph = sigma.getGraph();

    const handleEnter = ({ node }: { node: string }) => {
      const attrs = graph.getNodeAttributes(node) as KGNodeAttributes;
      const pos = sigma.graphToViewport({ x: attrs.x, y: attrs.y });
      setTooltip({ x: pos.x, y: pos.y, attrs });
    };

    const handleLeave = () => setTooltip(null);

    sigma.on('enterNode', handleEnter);
    sigma.on('leaveNode', handleLeave);

    return () => {
      sigma.removeListener('enterNode', handleEnter);
      sigma.removeListener('leaveNode', handleLeave);
    };
  }, [sigma]);

  if (!tooltip) return null;

  const theme = getGraphTypeTheme(tooltip.attrs.nodeType);

  return (
    <div
      className="absolute pointer-events-none z-50"
      style={{
        left: tooltip.x + 15,
        top: tooltip.y - 10,
        maxWidth: 320,
      }}
    >
      <div className="bg-slate-900/95 border border-slate-700 rounded-lg shadow-xl p-3 text-sm">
        <div className="flex items-center gap-2 mb-1">
          <span
            className="inline-block w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: theme.color }}
          />
          <span className="font-semibold text-slate-100">{tooltip.attrs.label}</span>
        </div>
        <span
          className="text-xs px-1.5 py-0.5 rounded"
          style={{ backgroundColor: theme.tint, color: theme.text, border: `1px solid ${theme.border}` }}
        >
          {formatGraphNodeType(tooltip.attrs.nodeType)}
        </span>
        {tooltip.attrs.period && (
          <p className="text-xs text-slate-400 mt-1">{tooltip.attrs.period}</p>
        )}
        {tooltip.attrs.description && (
          <p className="text-xs text-slate-300 mt-1 line-clamp-3">{tooltip.attrs.description}</p>
        )}
        {tooltip.attrs.passageCount && !tooltip.attrs.passagesExpanded && (
          <p className="text-xs text-blue-400 mt-1">
            Click to expand {tooltip.attrs.passageCount} passages
          </p>
        )}
      </div>
    </div>
  );
}
