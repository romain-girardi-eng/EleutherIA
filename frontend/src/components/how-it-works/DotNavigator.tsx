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
}

export function DotNavigator({ sections, activeId, onNavigate }: DotNavigatorProps) {
  return (
    <nav
      aria-label="Page sections"
      className="fixed right-5 top-1/2 -translate-y-1/2 z-[200] hidden lg:flex flex-col gap-3.5"
    >
      {sections.map((section) => {
        const isActive = section.id === activeId;
        return (
          <div key={section.id} className="group relative flex items-center justify-end">
            {/* Tooltip */}
            <span
              className="absolute right-6 whitespace-nowrap text-xs font-body px-2 py-1 rounded-md
                         text-white bg-zinc-800/80 backdrop-blur-sm
                         opacity-0 group-hover:opacity-100 transition-opacity duration-150
                         pointer-events-none"
            >
              {section.label}
            </span>

            {/* Dot */}
            <button
              onClick={() => onNavigate(section.id)}
              aria-label={`Go to ${section.label}`}
              aria-current={isActive ? 'true' : undefined}
              className={cn(
                'relative w-2.5 h-2.5 rounded-full transition-all duration-300 cursor-pointer',
                // Always dark-outlined so visible on any bg
                'ring-1 ring-stone-400/60 ring-offset-1 ring-offset-transparent',
                isActive
                  ? 'bg-orange-500 ring-orange-400/70 scale-110'
                  : 'bg-stone-300/70 hover:bg-stone-400',
              )}
            >
              {/* Subtle static ring on active — no infinite scale animation */}
              {isActive && (
                <motion.span
                  layoutId="dot-ring"
                  className="absolute -inset-1 rounded-full border border-orange-400/50"
                  initial={false}
                  transition={{ type: 'spring', stiffness: 300, damping: 25 }}
                />
              )}
            </button>
          </div>
        );
      })}
    </nav>
  );
}
