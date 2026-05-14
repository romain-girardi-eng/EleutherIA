import { useId, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ChevronDown } from 'lucide-react';
import { cn } from '../../utils/cn';
import type { ProofChainStep } from '../../types/graphrag';
import ProofChainPanel from './ProofChainPanel';

interface ProofChainBadgeProps {
  steps: readonly ProofChainStep[] | null | undefined;
  className?: string;
  /** When true, the panel starts expanded. Defaults to collapsed. */
  defaultOpen?: boolean;
}

export default function ProofChainBadge({
  steps,
  className,
  defaultOpen = false,
}: ProofChainBadgeProps) {
  const { t } = useTranslation();
  const panelId = useId();
  const [open, setOpen] = useState(defaultOpen);

  if (!steps || steps.length === 0) {
    return null;
  }

  const label = t('claimLedger.derivationCount', {
    defaultValue: `${t('claimLedger.derivation')} ({{count}})`,
    count: steps.length,
  });

  return (
    <div className={cn('flex flex-col', className)} data-testid="proof-chain-badge">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-controls={panelId}
        className={cn(
          'inline-flex w-fit items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] transition-colors',
          open
            ? 'border-amber-300/80 bg-amber-100/90 text-amber-800'
            : 'border-amber-200/80 bg-amber-50/80 text-amber-700 hover:bg-amber-100/80',
        )}
      >
        <ChevronDown
          aria-hidden="true"
          className={cn('h-3 w-3 transition-transform', open ? 'rotate-0' : '-rotate-90')}
        />
        {label}
      </button>
      {open && (
        <div id={panelId} role="region" aria-label={t('claimLedger.derivation')}>
          <ProofChainPanel steps={steps} />
        </div>
      )}
    </div>
  );
}
