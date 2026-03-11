// frontend/src/components/kg/CommunityHullsLayer.tsx
import { useEffect, useRef, useCallback } from 'react';
import { useSigma } from '@react-sigma/core';
import { polygonHull } from 'd3-polygon';
import { getHullOpacity } from './SemanticZoomController';

interface CommunityHullsLayerProps {
  communities: Map<number, Set<string>>;
  communityColors: Map<number, string>;
  communityLabels: Map<number, string>;
}

function hexToRgba(hex: string, alpha: number): string {
  const clean = hex.replace('#', '');
  const full =
    clean.length === 3
      ? clean
          .split('')
          .map((c) => c + c)
          .join('')
      : clean;
  const r = parseInt(full.slice(0, 2), 16);
  const g = parseInt(full.slice(2, 4), 16);
  const b = parseInt(full.slice(4, 6), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

function resolveColor(color: string, alpha: number): string {
  if (color.startsWith('#')) {
    return hexToRgba(color, alpha);
  }
  // Already rgba/rgb — replace last numeric value (the alpha channel)
  return color.replace(/[\d.]+\)$/, `${alpha})`);
}

function padHull(
  points: [number, number][],
  padding: number,
): [number, number][] {
  if (points.length < 3) return points;
  const cx = points.reduce((s, p) => s + p[0], 0) / points.length;
  const cy = points.reduce((s, p) => s + p[1], 0) / points.length;
  return points.map(([x, y]) => {
    const dx = x - cx;
    const dy = y - cy;
    const d = Math.sqrt(dx * dx + dy * dy);
    if (d === 0) return [x, y] as [number, number];
    return [x + (dx / d) * padding, y + (dy / d) * padding] as [
      number,
      number,
    ];
  });
}

export default function CommunityHullsLayer({
  communities,
  communityColors,
  communityLabels,
}: CommunityHullsLayerProps) {
  const sigma = useSigma();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const camera = sigma.getCamera();
    const ratio = camera.ratio;
    const opacity = getHullOpacity(ratio);

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (opacity <= 0) return;

    for (const [communityId, nodeIds] of communities) {
      if (nodeIds.size < 3) continue;

      const points: [number, number][] = [];
      for (const nodeId of nodeIds) {
        try {
          const attrs = sigma.getGraph().getNodeAttributes(nodeId);
          const pos = sigma.graphToViewport({
            x: attrs.x as number,
            y: attrs.y as number,
          });
          points.push([pos.x, pos.y]);
        } catch {
          // Node may be hidden or not present
        }
      }

      if (points.length < 3) continue;

      const hull = polygonHull(points);
      if (!hull) continue;

      const padded = padHull(hull, 30);
      const rawColor = communityColors.get(communityId) ?? '#ffffff';

      ctx.beginPath();
      ctx.moveTo(padded[0][0], padded[0][1]);
      for (let i = 1; i < padded.length; i++) {
        ctx.lineTo(padded[i][0], padded[i][1]);
      }
      ctx.closePath();
      ctx.fillStyle = resolveColor(rawColor, opacity);
      ctx.fill();
      ctx.strokeStyle = resolveColor(rawColor, Math.min(opacity * 2, 1));
      ctx.lineWidth = 1;
      ctx.stroke();

      if (ratio > 0.6) {
        const cx = padded.reduce((s, p) => s + p[0], 0) / padded.length;
        const cy = padded.reduce((s, p) => s + p[1], 0) / padded.length;
        const label = communityLabels.get(communityId);
        if (label) {
          ctx.font = `${Math.max(12, 16 / ratio)}px sans-serif`;
          ctx.fillStyle = `rgba(255,255,255,${Math.min(opacity * 4, 0.8)})`;
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(label, cx, cy);
        }
      }
    }
  }, [sigma, communities, communityColors, communityLabels]);

  useEffect(() => {
    const container = sigma.getContainer();
    const canvas = document.createElement('canvas');
    canvas.style.position = 'absolute';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.pointerEvents = 'none';
    canvas.style.zIndex = '0';
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;
    container.style.position = 'relative';
    container.insertBefore(canvas, container.firstChild);
    canvasRef.current = canvas;

    const resizeObserver = new ResizeObserver(() => {
      canvas.width = container.clientWidth;
      canvas.height = container.clientHeight;
      draw();
    });
    resizeObserver.observe(container);

    const camera = sigma.getCamera();
    camera.addListener('updated', draw);

    return () => {
      camera.removeListener('updated', draw);
      resizeObserver.disconnect();
      canvas.remove();
    };
  }, [sigma, draw]);

  useEffect(() => {
    draw();
  }, [draw]);

  return null;
}
