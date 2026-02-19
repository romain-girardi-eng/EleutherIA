import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

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

interface CheckboxMode {
  key: keyof Pick<AdvancedOptionsProps, 'academicMode' | 'useThinking' | 'ancientOnly' | 'agenticMode'>;
  label: string;
  title?: string;
}

const CHECKBOX_MODES: CheckboxMode[] = [
  { key: 'academicMode', label: '🎓 Academic' },
  { key: 'useThinking', label: '🧠 Deep Reasoning' },
  { key: 'ancientOnly', label: '🏛️ Ancient Only', title: 'Only use ancient sources (6th c. BCE – 6th c. CE)' },
  { key: 'agenticMode', label: '⚡ Agentic', title: 'Full pydantic-AI pipeline (experimental, 30s cold start)' },
];

const PARAMETERS = [
  { label: 'Breadth', propKey: 'semanticK' as const, setPropKey: 'setSemanticK' as const, options: [5, 10, 15, 20] },
  { label: 'Depth',   propKey: 'graphDepth' as const, setPropKey: 'setGraphDepth' as const, options: [1, 2, 3] },
  { label: 'Context', propKey: 'maxContext' as const, setPropKey: 'setMaxContext' as const, options: [10, 15, 20, 25] },
];

export default function AdvancedOptions(props: AdvancedOptionsProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 transition-colors"
      >
        <svg
          className={`w-3.5 h-3.5 transition-transform duration-200 ${open ? 'rotate-90' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
        ⚙ Advanced options
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
            <div className="pt-2 space-y-4">
              {/* Mode checkboxes */}
              <div className="flex flex-wrap justify-center gap-x-6 gap-y-2">
                {CHECKBOX_MODES.map(mode => (
                  <label
                    key={mode.key}
                    className="flex items-center gap-2 cursor-pointer text-sm"
                    title={mode.title}
                  >
                    <input
                      type="checkbox"
                      checked={props[mode.key] as boolean}
                      onChange={e => {
                        switch (mode.key) {
                          case 'academicMode': props.setAcademicMode(e.target.checked); break;
                          case 'useThinking': props.setUseThinking(e.target.checked); break;
                          case 'ancientOnly': props.setAncientOnly(e.target.checked); break;
                          case 'agenticMode': props.setAgenticMode(e.target.checked); break;
                        }
                      }}
                      className="w-4 h-4 bg-white border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                    />
                    <span className="text-gray-700">{mode.label}</span>
                  </label>
                ))}
              </div>

              {/* Parameter dropdowns */}
              <div className="flex flex-wrap justify-center gap-3">
                {PARAMETERS.map(p => (
                  <div
                    key={p.label}
                    className="flex items-center gap-2 text-xs bg-white/60 backdrop-blur-md px-4 py-2 rounded-full border border-gray-200"
                  >
                    <span className="text-gray-700">{p.label}:</span>
                    <select
                      value={props[p.propKey] as number}
                      onChange={e => {
                        const v = Number(e.target.value);
                        switch (p.label) {
                          case 'Breadth': props.setSemanticK(v); break;
                          case 'Depth': props.setGraphDepth(v); break;
                          case 'Context': props.setMaxContext(v); break;
                        }
                      }}
                      className="px-2 py-0.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-black text-xs"
                    >
                      {p.options.map(o => (
                        <option key={o} value={o}>{o}</option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
