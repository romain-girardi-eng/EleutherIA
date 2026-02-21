import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Settings2 } from 'lucide-react';
import { Toggle } from '../ui/Toggle';
import { RadixSelect } from '../ui/RadixSelect';
import { RadixTooltip } from '../ui/RadixTooltip';

interface AdvancedOptionsProps {
  academicMode: boolean;
  setAcademicMode: (v: boolean) => void;
  useThinking: boolean;
  setUseThinking: (v: boolean) => void;
  ancientOnly: boolean;
  setAncientOnly: (v: boolean) => void;
  agenticMode: boolean;
  setAgenticMode: (v: boolean) => void;
  semanticK: number;
  setSemanticK: (v: number) => void;
  graphDepth: number;
  setGraphDepth: (v: number) => void;
  maxContext: number;
  setMaxContext: (v: number) => void;
}

const TOGGLE_MODES = [
  { key: 'academicMode' as const, label: 'Academic', description: 'Enable scholarly citation format and academic language' },
  { key: 'useThinking' as const, label: 'Deep Reasoning', description: 'Use extended thinking for complex questions (slower, more thorough)' },
  { key: 'ancientOnly' as const, label: 'Ancient Only', description: 'Only use ancient sources (6th c. BCE - 6th c. CE)' },
  { key: 'agenticMode' as const, label: 'Agentic', description: 'Full Pydantic-AI pipeline (experimental, 30s cold start)' },
] as const;

const PARAMETERS = [
  { label: 'Breadth', key: 'semanticK' as const, setKey: 'setSemanticK' as const, options: ['5', '10', '15', '20'] },
  { label: 'Depth', key: 'graphDepth' as const, setKey: 'setGraphDepth' as const, options: ['1', '2', '3'] },
  { label: 'Context', key: 'maxContext' as const, setKey: 'setMaxContext' as const, options: ['10', '15', '20', '25'] },
];

export default function AdvancedOptions(props: AdvancedOptionsProps) {
  const [open, setOpen] = useState(false);

  const getToggleValue = (key: typeof TOGGLE_MODES[number]['key']): boolean => {
    return props[key] as boolean;
  };

  const setToggleValue = (key: typeof TOGGLE_MODES[number]['key'], value: boolean) => {
    const setters: Record<string, (v: boolean) => void> = {
      academicMode: props.setAcademicMode,
      useThinking: props.setUseThinking,
      ancientOnly: props.setAncientOnly,
      agenticMode: props.setAgenticMode,
    };
    setters[key]?.(value);
  };

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-sm text-stone-400 hover:text-stone-600 transition-colors"
      >
        <Settings2 className={`w-3.5 h-3.5 transition-transform duration-200 ${open ? 'rotate-90' : ''}`} />
        Advanced options
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.22, ease: 'easeInOut' }}
            className="overflow-hidden w-full"
          >
            <div className="pt-3 space-y-4">
              {/* Mode toggles */}
              <div className="flex flex-wrap justify-center gap-x-5 gap-y-3">
                {TOGGLE_MODES.map((mode) => (
                  <RadixTooltip key={mode.key} content={mode.description}>
                    <div>
                      <Toggle
                        checked={getToggleValue(mode.key)}
                        onCheckedChange={(v) => setToggleValue(mode.key, v)}
                        label={mode.label}
                      />
                    </div>
                  </RadixTooltip>
                ))}
              </div>

              {/* Parameter selects */}
              <div className="flex flex-wrap justify-center gap-3">
                {PARAMETERS.map((p) => (
                  <RadixSelect
                    key={p.label}
                    label={p.label}
                    value={String(props[p.key])}
                    onValueChange={(v) => props[p.setKey](Number(v))}
                    options={p.options.map((o) => ({ value: o, label: o }))}
                  />
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
