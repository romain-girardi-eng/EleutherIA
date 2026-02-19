import { motion } from 'framer-motion';
import { cn } from '../../utils/cn';

export interface DotNavSection {
  id: string;
  label: string;
}

interface DotNavigatorProps {
  sections: DotNavSection[];
  activeId: string;
  onNavigate: (id: string) => void;
  /** Light (for dark overall bg) or dark (for light overall bg) */
  theme?: 'light' | 'dark';
}

export function DotNavigator({
  sections,
  activeId,
  onNavigate,
  theme = 'light',
}: DotNavigatorProps) {
  const dotBase =
    theme === 'light'
      ? 'bg-white/30 hover:bg-white/60 border border-white/40'
      : 'bg-stone-400/40 hover:bg-stone-500/60 border border-stone-300';
  const dotActive =
    theme === 'light'
      ? 'bg-orange-400 border-orange-400 shadow-[0_0_10px_rgba(251,146,60,0.6)]'
      : 'bg-orange-600 border-orange-600 shadow-[0_0_10px_rgba(194,65,12,0.5)]';
  const labelColor =
    theme === 'light' ? 'text-white/80 bg-zinc-900/70' : 'text-stone-700 bg-white/80';

  return (
    <nav
      aria-label="Page sections"
      className="fixed right-5 top-1/2 -translate-y-1/2 z-[200] hidden lg:flex flex-col gap-4"
    >
      {sections.map((section) => {
        const isActive = section.id === activeId;
        return (
          <div key={section.id} className="group relative flex items-center justify-end">
            {/* Tooltip label */}
            <span
              className={cn(
                'absolute right-7 whitespace-nowrap text-xs font-body px-2 py-1 rounded-md',
                'opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none',
                labelColor,
              )}
            >
              {section.label}
            </span>

            {/* Dot button */}
            <button
              onClick={() => onNavigate(section.id)}
              aria-label={`Go to ${section.label}`}
              aria-current={isActive ? 'true' : undefined}
              className={cn(
                'relative w-3 h-3 rounded-full transition-all duration-300 cursor-pointer',
                isActive ? dotActive : dotBase,
              )}
            >
              {isActive && (
                <motion.span
                  layoutId="active-dot"
                  className="absolute inset-0 rounded-full bg-orange-400/40"
                  animate={{ scale: [1, 1.8, 1] }}
                  transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                />
              )}
            </button>
          </div>
        );
      })}
    </nav>
  );
}
