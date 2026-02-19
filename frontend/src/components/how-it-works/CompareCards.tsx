import { motion } from 'framer-motion';
import { CheckCircle2, XCircle } from 'lucide-react';
import { cn } from '../../utils/cn';

interface CompareItem {
  text: string;
}

interface CompareCardData {
  label: string;
  title: string;
  metric?: { value: string; description: string };
  items: CompareItem[];
}

interface CompareCardsProps {
  before: CompareCardData;
  after: CompareCardData;
  className?: string;
}

export function CompareCards({ before, after, className }: CompareCardsProps) {
  return (
    <div className={cn('grid md:grid-cols-2 gap-6 w-full', className)}>
      {/* Problem card */}
      <motion.div
        initial={{ opacity: 0, x: -30 }}
        whileInView={{ opacity: 1, x: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="relative h-full rounded-2xl border border-red-300/60 bg-red-50/60 p-8 flex flex-col">
          {/* Label tag */}
          <span className="inline-flex items-center gap-1.5 self-start text-xs font-body font-semibold text-red-600 bg-red-100 rounded-full px-3 py-1 mb-4 uppercase tracking-wider">
            <XCircle className="w-3.5 h-3.5" />
            {before.label}
          </span>

          <h3 className="font-display text-2xl text-red-800 mb-5 leading-snug">
            {before.title}
          </h3>

          <ul className="space-y-3 flex-1">
            {before.items.map((item, i) => (
              <li key={i} className="flex items-start gap-2.5 text-sm font-body text-red-700/80">
                <span className="mt-0.5 text-red-400 flex-shrink-0">✕</span>
                {item.text}
              </li>
            ))}
          </ul>

          {before.metric && (
            <div className="mt-6 pt-5 border-t border-red-200/60">
              <p className="text-xs text-red-500 font-body uppercase tracking-wider mb-1">
                {before.metric.description}
              </p>
              <p className="font-display text-4xl text-red-700">
                {before.metric.value}
              </p>
            </div>
          )}
        </div>
      </motion.div>

      {/* Solution card */}
      <motion.div
        initial={{ opacity: 0, x: 30 }}
        whileInView={{ opacity: 1, x: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1], delay: 0.1 }}
      >
        <div className="relative h-full rounded-2xl border border-emerald-300/60 bg-emerald-50/60 p-8 flex flex-col">
          {/* Label tag */}
          <span className="inline-flex items-center gap-1.5 self-start text-xs font-body font-semibold text-emerald-700 bg-emerald-100 rounded-full px-3 py-1 mb-4 uppercase tracking-wider">
            <CheckCircle2 className="w-3.5 h-3.5" />
            {after.label}
          </span>

          <h3 className="font-display text-2xl text-emerald-800 mb-5 leading-snug">
            {after.title}
          </h3>

          <ul className="space-y-3 flex-1">
            {after.items.map((item, i) => (
              <li key={i} className="flex items-start gap-2.5 text-sm font-body text-emerald-800/80">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                {item.text}
              </li>
            ))}
          </ul>

          {after.metric && (
            <div className="mt-6 pt-5 border-t border-emerald-200/60">
              <p className="text-xs text-emerald-600 font-body uppercase tracking-wider mb-1">
                {after.metric.description}
              </p>
              <p className="font-display text-4xl text-emerald-700">
                {after.metric.value}
              </p>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}
