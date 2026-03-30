import { useState, useEffect } from 'react';

interface ModelInfo {
  key: string;
  label: string;
  provider: string;
  context: number;
  tier: string;
  pricing: { input: number; output: number };
}

interface ModelSelectorProps {
  selectedModel: string;
  selectedMode: string;
  onModelChange: (model: string) => void;
  onModeChange: (mode: string) => void;
}

const MODES = [
  { value: 'auto', label: 'Auto (vector + fallback)' },
  { value: 'vector', label: 'Vector (Qdrant)' },
  { value: 'sql', label: 'SQL (vectorless)' },
];

export function ModelSelector({
  selectedModel,
  selectedMode,
  onModelChange,
  onModeChange,
}: ModelSelectorProps) {
  const [models, setModels] = useState<ModelInfo[]>([]);

  useEffect(() => {
    fetch('/api/graphrag/models')
      .then((r) => r.json())
      .then(setModels)
      .catch(console.error);
  }, []);

  return (
    <div className="flex items-center gap-2 text-sm">
      <select
        value={selectedModel}
        onChange={(e) => onModelChange(e.target.value)}
        className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-zinc-300"
      >
        {models.map((m) => (
          <option key={m.key} value={m.key}>
            {m.label} · {m.tier}
          </option>
        ))}
      </select>
      <select
        value={selectedMode}
        onChange={(e) => onModeChange(e.target.value)}
        className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-zinc-300"
      >
        {MODES.map((m) => (
          <option key={m.value} value={m.value}>
            {m.label}
          </option>
        ))}
      </select>
    </div>
  );
}
