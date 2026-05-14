import { motion } from 'framer-motion';
import { Loader2, Brain, CheckCircle2, AlertTriangle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { cn } from '../../lib/utils';
import type { ActiveSubagent } from '../../hooks/useResearchStream';

interface Props {
  agent: ActiveSubagent;
  /** Optional translation key under `research.subagents.*` for the localized name. */
  nameKey?: string;
}

export function SubagentStatusCard({ agent, nameKey }: Props) {
  const { t } = useTranslation();
  const localizedName = nameKey
    ? t(`research.subagents.${nameKey}`, { defaultValue: agent.subagent })
    : agent.subagent;

  const Icon =
    agent.status === 'thinking'
      ? Brain
      : agent.status === 'failed'
      ? AlertTriangle
      : agent.status === 'complete'
      ? CheckCircle2
      : Loader2;

  const tone =
    agent.status === 'failed'
      ? 'border-rose-200/80 bg-rose-50/80 text-rose-700'
      : agent.status === 'complete'
      ? 'border-emerald-200/80 bg-emerald-50/80 text-emerald-700'
      : 'border-amber-200/80 bg-amber-50/80 text-amber-800';

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -6 }}
      transition={{ duration: 0.2 }}
      className={cn('flex items-start gap-2 rounded-xl border px-3 py-2 shadow-sm', tone)}
    >
      <Icon
        className={cn(
          'h-4 w-4 shrink-0',
          agent.status !== 'complete' && agent.status !== 'failed' && 'animate-spin',
        )}
        aria-hidden="true"
      />
      <div className="min-w-0">
        <p className="text-[11px] font-semibold uppercase tracking-[0.12em]">
          {agent.agent}
        </p>
        <p className="truncate text-[13px] font-medium leading-5 text-stone-800">
          {localizedName}
        </p>
        {agent.message && (
          <p className="mt-0.5 truncate text-[11px] italic text-stone-500">
            {agent.message}
          </p>
        )}
      </div>
    </motion.div>
  );
}

export default SubagentStatusCard;
