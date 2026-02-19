import { motion } from 'framer-motion';
import { ChevronDown } from 'lucide-react';
import { cn } from '../../utils/cn';

interface ScrollHintProps {
  label?: string;
  className?: string;
  /** Light (for dark backgrounds) or dark (for light backgrounds) */
  theme?: 'light' | 'dark';
}

export function ScrollHint({
  label = 'Scroll to explore',
  className,
  theme = 'light',
}: ScrollHintProps) {
  const textColor = theme === 'light' ? 'text-white/60' : 'text-stone-400';
  const iconColor = theme === 'light' ? 'text-white/40' : 'text-stone-400';

  return (
    <div
      className={cn('flex flex-col items-center gap-2', className)}
      aria-hidden="true"
    >
      <span className={cn('text-xs tracking-widest uppercase font-body', textColor)}>
        {label}
      </span>
      <motion.div
        animate={{ y: [0, 8, 0] }}
        transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut' }}
      >
        <ChevronDown className={cn('w-5 h-5', iconColor)} strokeWidth={1.5} />
      </motion.div>
    </div>
  );
}
