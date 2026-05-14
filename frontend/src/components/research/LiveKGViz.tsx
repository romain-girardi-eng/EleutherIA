/**
 * LiveKGViz — a lightweight SVG constellation that lights up KG nodes as
 * agents touch them during streaming research.
 *
 * Design note: this is *not* a replacement for the full Cosmograph view at
 * /visualizer — it's an ambient companion. Each node is placed by hashed
 * polar layout (stable across hot reloads) and animates a pulse on every hit.
 * For a fully connected interactive graph, link to /visualizer/{nodeId}.
 */

import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import type { KGActivation } from '../../hooks/useResearchStream';

interface Props {
  activations: KGActivation[];
  /** Width and height in CSS pixels; defaults to a square 360. */
  size?: number;
}

interface PlacedNode extends KGActivation {
  x: number;
  y: number;
  r: number;
  color: string;
}

const TYPE_PALETTE: Record<string, string> = {
  person: '#d97706',
  concept: '#7c3aed',
  argument: '#0ea5e9',
  work: '#059669',
  passage: '#f59e0b',
  school: '#db2777',
  default: '#78716c',
};

function hashStr(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) {
    h = (h << 5) - h + s.charCodeAt(i);
    h |= 0;
  }
  return Math.abs(h);
}

function placeNodes(
  activations: KGActivation[],
  size: number,
): PlacedNode[] {
  const cx = size / 2;
  const cy = size / 2;
  const maxR = size * 0.42;
  return activations.map((a, i) => {
    const seed = hashStr(a.node_id);
    // Mix the index in so order matters slightly (newer = pushed outward).
    const angle = ((seed % 360) + i * 17) * (Math.PI / 180);
    const radius = ((seed % 1000) / 1000) * maxR;
    const r = Math.min(14, 4 + Math.log2(a.hits + 1) * 2);
    const color =
      TYPE_PALETTE[a.node_type.toLowerCase() as keyof typeof TYPE_PALETTE] ??
      TYPE_PALETTE.default;
    return {
      ...a,
      x: cx + Math.cos(angle) * radius,
      y: cy + Math.sin(angle) * radius,
      r,
      color,
    };
  });
}

export function LiveKGViz({ activations, size = 360 }: Props) {
  const { t } = useTranslation();
  const placed = useMemo(() => placeNodes(activations, size), [activations, size]);

  return (
    <div className="relative overflow-hidden rounded-2xl border border-stone-200/70 bg-gradient-to-br from-stone-50/60 via-white/40 to-amber-50/40 p-3">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-[11px] font-semibold uppercase tracking-[0.16em] text-stone-500">
          {t('research.kgViz.title')}
        </h3>
        <span className="rounded-full bg-stone-100/80 px-2 py-0.5 text-[10px] font-medium text-stone-500">
          {activations.length} {t('research.kgViz.nodesLabel')}
        </span>
      </div>

      <svg
        viewBox={`0 0 ${size} ${size}`}
        width="100%"
        height={size}
        role="img"
        aria-label={t('research.kgViz.ariaLabel')}
      >
        <defs>
          <radialGradient id="research-kg-bg" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(251,191,36,0.15)" />
            <stop offset="100%" stopColor="rgba(255,255,255,0)" />
          </radialGradient>
        </defs>
        <rect width={size} height={size} fill="url(#research-kg-bg)" />

        {placed.length === 0 && (
          <text
            x={size / 2}
            y={size / 2}
            textAnchor="middle"
            className="fill-stone-400"
            fontSize={11}
            fontStyle="italic"
          >
            {t('research.kgViz.idle')}
          </text>
        )}

        {placed.map((node) => (
          <g key={node.node_id}>
            {/* Pulse halo */}
            <circle
              cx={node.x}
              cy={node.y}
              r={node.r + 4}
              fill={node.color}
              fillOpacity={0.12}
            >
              <animate
                attributeName="r"
                values={`${node.r + 4};${node.r + 12};${node.r + 4}`}
                dur="2.4s"
                repeatCount="indefinite"
              />
              <animate
                attributeName="fill-opacity"
                values="0.18;0;0.18"
                dur="2.4s"
                repeatCount="indefinite"
              />
            </circle>
            <circle
              cx={node.x}
              cy={node.y}
              r={node.r}
              fill={node.color}
              fillOpacity={0.85}
              stroke="white"
              strokeWidth={1.2}
            >
              <title>{`${node.label} · ${node.node_type}${
                node.period ? ` · ${node.period}` : ''
              }`}</title>
            </circle>
          </g>
        ))}
      </svg>
    </div>
  );
}

export default LiveKGViz;
