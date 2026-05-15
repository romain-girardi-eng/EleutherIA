import { useTranslation } from 'react-i18next';
import { CheckCircle2, AlertTriangle, HelpCircle, Loader2 } from 'lucide-react';
import type { ReproducibilityStatus } from '../../api/community';
import { cn } from '../../lib/utils';

interface ReproducibilityBadgeProps {
  status: ReproducibilityStatus | null;
  loading?: boolean;
  className?: string;
}

function formatTimestamp(iso: string, locale: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat(locale, {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

export default function ReproducibilityBadge({
  status,
  loading,
  className,
}: ReproducibilityBadgeProps) {
  const { t, i18n } = useTranslation();

  if (loading) {
    return (
      <span
        className={cn(
          'inline-flex items-center gap-1.5 rounded-full border border-stone-200/70 bg-stone-100/60 px-2.5 py-1 text-[11px] font-medium text-stone-500',
          className
        )}
      >
        <Loader2 className="h-3 w-3 animate-spin" aria-hidden="true" />
        {t('reproducibility.badge.loading')}
      </span>
    );
  }

  if (!status) return null;

  const cachedAt = formatTimestamp(status.cached_at, i18n.language);
  const currentAt = formatTimestamp(status.current_kg_updated_at, i18n.language);

  const tooltip = t('reproducibility.badge.tooltip', {
    cachedVersion: status.cached_at_kg_version,
    currentVersion: status.current_kg_version,
    cachedAt,
    currentAt,
  });

  if (status.status === 'unchanged') {
    return (
      <span
        title={tooltip}
        aria-label={tooltip}
        className={cn(
          'inline-flex items-center gap-1.5 rounded-full border border-emerald-200/70 bg-emerald-50/70 px-2.5 py-1 text-[11px] font-medium text-emerald-800',
          className
        )}
      >
        <CheckCircle2 className="h-3 w-3" aria-hidden="true" />
        {t('reproducibility.badge.unchanged', {
          version: status.cached_at_kg_version,
        })}
      </span>
    );
  }

  if (status.status === 'kg_advanced') {
    return (
      <span
        title={tooltip}
        aria-label={tooltip}
        className={cn(
          'inline-flex items-center gap-1.5 rounded-full border border-amber-300/70 bg-amber-50/70 px-2.5 py-1 text-[11px] font-medium text-amber-900',
          className
        )}
      >
        <AlertTriangle className="h-3 w-3" aria-hidden="true" />
        {t('reproducibility.badge.kgAdvanced', { count: status.kg_advanced_by })}
      </span>
    );
  }

  return (
    <span
      title={tooltip}
      aria-label={tooltip}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border border-stone-300/70 bg-stone-100/70 px-2.5 py-1 text-[11px] font-medium text-stone-600',
        className
      )}
    >
      <HelpCircle className="h-3 w-3" aria-hidden="true" />
      {t('reproducibility.badge.staleUnknown')}
    </span>
  );
}
