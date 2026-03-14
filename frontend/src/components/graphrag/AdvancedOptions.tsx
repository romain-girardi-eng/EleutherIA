import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Settings2 } from 'lucide-react';
import { Toggle } from '../ui/Toggle';
import { RadixTooltip } from '../ui/RadixTooltip';

interface AdvancedOptionsProps {
  ancientOnly: boolean;
  setAncientOnly: (v: boolean) => void;
}

export default function AdvancedOptions({ ancientOnly, setAncientOnly }: AdvancedOptionsProps) {
  const [open, setOpen] = useState(false);

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
            <div className="pt-3 flex justify-center">
              <RadixTooltip content="Only use ancient sources (6th c. BCE – 6th c. CE)">
                <div>
                  <Toggle
                    checked={ancientOnly}
                    onCheckedChange={setAncientOnly}
                    label="Ancient Only"
                  />
                </div>
              </RadixTooltip>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
