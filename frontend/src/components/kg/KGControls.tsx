// frontend/src/components/kg/KGControls.tsx
import { useCallback } from 'react';
import { useSigma } from '@react-sigma/core';
import { ZoomIn, ZoomOut, Maximize2, Eye, EyeOff } from 'lucide-react';

interface KGControlsProps {
  passagesVisible: boolean;
  onTogglePassages: () => void;
  nodeCount: number;
  edgeCount: number;
}

export default function KGControls({
  passagesVisible,
  onTogglePassages,
  nodeCount,
  edgeCount,
}: KGControlsProps) {
  const sigma = useSigma();

  const zoomIn = useCallback(() => {
    const camera = sigma.getCamera();
    camera.animatedZoom({ duration: 300 });
  }, [sigma]);

  const zoomOut = useCallback(() => {
    const camera = sigma.getCamera();
    camera.animatedUnzoom({ duration: 300 });
  }, [sigma]);

  const fitView = useCallback(() => {
    const camera = sigma.getCamera();
    camera.animatedReset({ duration: 500 });
  }, [sigma]);

  return (
    <>
      {/* Stats bar */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10">
        <div className="bg-slate-900/80 border border-slate-700 rounded-full px-4 py-1.5 text-xs text-slate-300 backdrop-blur-sm flex items-center gap-3">
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
            {nodeCount.toLocaleString()} nodes
          </span>
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
            {edgeCount.toLocaleString()} edges
          </span>
        </div>
      </div>

      {/* Zoom controls */}
      <div className="absolute left-3 bottom-20 z-10 flex flex-col gap-1">
        <button onClick={zoomIn} className="p-1.5 bg-slate-900/80 border border-slate-700 rounded-lg hover:bg-slate-800 text-slate-300">
          <ZoomIn className="w-4 h-4" />
        </button>
        <button onClick={zoomOut} className="p-1.5 bg-slate-900/80 border border-slate-700 rounded-lg hover:bg-slate-800 text-slate-300">
          <ZoomOut className="w-4 h-4" />
        </button>
        <button onClick={fitView} className="p-1.5 bg-slate-900/80 border border-slate-700 rounded-lg hover:bg-slate-800 text-slate-300">
          <Maximize2 className="w-4 h-4" />
        </button>
      </div>

      {/* Passages toggle */}
      <div className="absolute top-4 right-4 z-10">
        <button
          onClick={onTogglePassages}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs border backdrop-blur-sm ${
            passagesVisible
              ? 'bg-blue-500/20 border-blue-500/50 text-blue-300'
              : 'bg-slate-900/80 border-slate-700 text-slate-400'
          }`}
        >
          {passagesVisible ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
          Passages {passagesVisible ? 'ON' : 'OFF'}
        </button>
      </div>
    </>
  );
}
