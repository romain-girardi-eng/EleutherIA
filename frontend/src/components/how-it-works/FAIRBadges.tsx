import { motion } from 'framer-motion';
import { Search, Globe, GitBranch, RotateCcw } from 'lucide-react';
import { cn } from '../../utils/cn';

interface FAIRBadge {
  letter: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  detail: string[];
}

const FAIR_BADGES: FAIRBadge[] = [
  {
    letter: 'F',
    title: 'Findable',
    description: 'Every entity has a unique, persistent identifier',
    icon: <Search className="w-5 h-5" />,
    color: 'orange',
    detail: ['CTS URNs for ancient texts', 'UUIDs for all KG nodes', 'DOI 10.5281/zenodo.17379490'],
  },
  {
    letter: 'A',
    title: 'Accessible',
    description: 'Open REST API, no auth required for reads',
    icon: <Globe className="w-5 h-5" />,
    color: 'amber',
    detail: ['Public JSON API', 'Swagger/OpenAPI docs', 'HTTPS + CORS enabled'],
  },
  {
    letter: 'I',
    title: 'Interoperable',
    description: 'Standard formats compatible with existing tools',
    icon: <GitBranch className="w-5 h-5" />,
    color: 'primary',
    detail: ['JSON-LD & RDF formats', 'TEI XML preservation', 'Compatible with Perseus / TLG / PHI'],
  },
  {
    letter: 'R',
    title: 'Reusable',
    description: 'Traceable provenance, open licence',
    icon: <RotateCcw className="w-5 h-5" />,
    color: 'emerald',
    detail: ['CC BY 4.0 licence', 'Source attribution per passage', 'Confidence scores 0–1'],
  },
];

const colorMap: Record<string, { badge: string; border: string; bg: string; icon: string }> = {
  orange:  { badge: 'bg-orange-500 text-white',   border: 'border-orange-200', bg: 'bg-orange-50/70',  icon: 'text-orange-600' },
  amber:   { badge: 'bg-amber-500 text-white',    border: 'border-amber-200',  bg: 'bg-amber-50/70',   icon: 'text-amber-600'  },
  primary: { badge: 'bg-primary-600 text-white',  border: 'border-primary-200',bg: 'bg-primary-50/70', icon: 'text-primary-600'},
  emerald: { badge: 'bg-emerald-600 text-white',  border: 'border-emerald-200',bg: 'bg-emerald-50/70', icon: 'text-emerald-600'},
};

interface FAIRBadgesProps {
  className?: string;
  /** 'light' = parchment bg, 'dark' = dark bg glass-style */
  variant?: 'light' | 'dark';
}

export function FAIRBadges({ className, variant = 'light' }: FAIRBadgesProps) {
  return (
    <div className={cn('grid grid-cols-2 lg:grid-cols-4 gap-5 w-full', className)}>
      {FAIR_BADGES.map((badge, i) => {
        const c = colorMap[badge.color];
        const cardStyle =
          variant === 'light'
            ? cn('border rounded-2xl p-6 flex flex-col gap-4 h-full', c.bg, c.border)
            : 'border border-white/10 bg-white/6 backdrop-blur-sm rounded-2xl p-6 flex flex-col gap-4 h-full';

        return (
          <motion.div
            key={badge.letter}
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: i * 0.1, ease: [0.22, 1, 0.36, 1] }}
          >
            <div className={cardStyle}>
              {/* Letter badge + icon row */}
              <div className="flex items-center gap-3">
                <span
                  className={cn(
                    'w-12 h-12 rounded-xl flex items-center justify-center',
                    'font-display text-2xl font-normal',
                    c.badge,
                  )}
                >
                  {badge.letter}
                </span>
                <div className={cn('p-2 rounded-lg', variant === 'light' ? 'bg-white/60' : 'bg-white/10')}>
                  <span className={variant === 'light' ? c.icon : 'text-white/70'}>
                    {badge.icon}
                  </span>
                </div>
              </div>

              <div>
                <h4 className={cn('font-display text-xl mb-1', variant === 'light' ? 'text-stone-800' : 'text-white')}>
                  {badge.title}
                </h4>
                <p className={cn('text-sm font-body', variant === 'light' ? 'text-stone-600' : 'text-white/60')}>
                  {badge.description}
                </p>
              </div>

              <ul className="space-y-1.5 mt-auto">
                {badge.detail.map((d) => (
                  <li
                    key={d}
                    className={cn(
                      'text-xs font-body flex items-start gap-1.5',
                      variant === 'light' ? 'text-stone-500' : 'text-white/50',
                    )}
                  >
                    <span className="mt-0.5 opacity-60">•</span>
                    {d}
                  </li>
                ))}
              </ul>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
