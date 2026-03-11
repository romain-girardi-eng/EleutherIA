// frontend/src/components/kg/SearchBar.tsx
import { useState, useMemo, useCallback } from 'react';
import { useSigma } from '@react-sigma/core';
import { Search } from 'lucide-react';
import { formatGraphNodeType } from '@/components/graphrag/graphTheme';
import type { KGNodeAttributes } from '@/types/sigma';

interface SearchResult {
  id: string;
  label: string;
  type: string;
  color: string;
}

export default function SearchBar() {
  const sigma = useSigma();
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);

  const results = useMemo(() => {
    if (query.length < 2) return [];
    const graph = sigma.getGraph();
    const q = query.toLowerCase();
    const matches: SearchResult[] = [];

    graph.forEachNode((nodeId: string, attrs: Record<string, unknown>) => {
      if (matches.length >= 20) return;
      const a = attrs as unknown as KGNodeAttributes;
      if (a.label.toLowerCase().includes(q)) {
        matches.push({
          id: nodeId,
          label: a.label,
          type: a.nodeType,
          color: a.color,
        });
      }
    });

    // Sort: exact start matches first, then by label length
    matches.sort((a, b) => {
      const aStarts = a.label.toLowerCase().startsWith(q) ? 0 : 1;
      const bStarts = b.label.toLowerCase().startsWith(q) ? 0 : 1;
      if (aStarts !== bStarts) return aStarts - bStarts;
      return a.label.length - b.label.length;
    });

    return matches;
  }, [query, sigma]);

  const handleSelect = useCallback((nodeId: string) => {
    const graph = sigma.getGraph();
    const attrs = graph.getNodeAttributes(nodeId) as KGNodeAttributes;
    const camera = sigma.getCamera();
    camera.animate({ x: attrs.x, y: attrs.y, ratio: 0.15 }, { duration: 500 });
    setQuery('');
    setIsOpen(false);
  }, [sigma]);

  return (
    <div className="relative">
      <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-700 rounded-lg px-3 py-2 backdrop-blur-sm">
        <Search className="w-4 h-4 text-slate-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => { setQuery(e.target.value); setIsOpen(true); }}
          onFocus={() => setIsOpen(true)}
          onBlur={() => setTimeout(() => setIsOpen(false), 200)}
          placeholder="Search nodes..."
          className="bg-transparent text-sm text-slate-100 placeholder-slate-500 outline-none w-48"
        />
      </div>

      {isOpen && results.length > 0 && (
        <div className="absolute top-full mt-1 left-0 w-72 bg-slate-900/95 border border-slate-700 rounded-lg shadow-xl max-h-64 overflow-y-auto z-50">
          {results.map((r) => {
            return (
              <button
                key={r.id}
                onMouseDown={() => handleSelect(r.id)}
                className="w-full text-left px-3 py-2 hover:bg-slate-800 flex items-center gap-2 text-sm"
              >
                <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: r.color }} />
                <span className="text-slate-100 truncate">{r.label}</span>
                <span className="text-xs text-slate-500 ml-auto flex-shrink-0">
                  {formatGraphNodeType(r.type)}
                </span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
