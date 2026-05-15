/**
 * CostCounter — compact live token + USD cost badge.
 *
 * Renders next to the streaming answer pane and updates in real time as
 * ``tokens_used`` / ``tokens_used_rollup`` / ``cost_summary`` SSE events
 * flow through ``useResearchStream``. Hovering reveals a per-model + per-
 * agent breakdown so a researcher can see exactly where the budget went.
 *
 * Formatting rules:
 *   - USD ≥ 1   → "$1.23"      (2 decimals, thousands separator)
 *   - USD < 1   → "$0.0340"   (4 decimals)
 *   - tokens   → locale-formatted integer ("12,348")
 */

import { useTranslation } from 'react-i18next';
import { Coins } from 'lucide-react';
import { useState } from 'react';
import { cn } from '../../lib/utils';
import type { TokenUsageState } from '../../hooks/useResearchStream';

export interface CostCounterProps {
  usage: TokenUsageState;
  /** Optional override — defaults to ``compact`` for the streaming pane. */
  variant?: 'compact' | 'detailed';
  className?: string;
}

// USD + token counts are locale-pinned (en-US) so the badge is stable across
// browser locales — academic citations care about deterministic rendering.
const USD_LOCALE = 'en-US';

export function formatUsd(value: number): string {
  if (!Number.isFinite(value) || value <= 0) {
    return '$0.0000';
  }
  if (value >= 1) {
    return `$${value.toLocaleString(USD_LOCALE, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  }
  return `$${value.toFixed(4)}`;
}

export function formatTokens(value: number): string {
  if (!Number.isFinite(value) || value <= 0) return '0';
  return value.toLocaleString(USD_LOCALE);
}

export function CostCounter({
  usage,
  variant = 'compact',
  className,
}: CostCounterProps) {
  const { t } = useTranslation();
  const [tooltipOpen, setTooltipOpen] = useState(false);

  const totals = (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50/80 px-2.5 py-1 font-mono text-[11px] text-amber-800',
        variant === 'detailed' && 'text-[12px]',
        className,
      )}
      role="status"
      aria-live="polite"
      aria-atomic="true"
    >
      <Coins className="h-3 w-3" aria-hidden="true" />
      <span className="tabular-nums">{formatUsd(usage.total_cost_usd)}</span>
      <span aria-hidden="true" className="text-amber-300">
        ·
      </span>
      <span className="tabular-nums">
        {formatTokens(usage.total_tokens)}{' '}
        <span className="text-[10px] text-amber-600">
          {t('research.cost.tokens')}
        </span>
      </span>
    </span>
  );

  const hasBreakdown =
    Object.keys(usage.by_model).length > 0 ||
    Object.keys(usage.by_agent).length > 0;

  return (
    <span
      className={cn('relative inline-block', className)}
      onMouseEnter={() => setTooltipOpen(true)}
      onMouseLeave={() => setTooltipOpen(false)}
      onFocus={() => setTooltipOpen(true)}
      onBlur={() => setTooltipOpen(false)}
    >
      <button
        type="button"
        aria-haspopup="dialog"
        aria-expanded={tooltipOpen}
        aria-label={t('research.cost.ariaLabel', {
          cost: formatUsd(usage.total_cost_usd),
          tokens: formatTokens(usage.total_tokens),
        })}
        className="cursor-help bg-transparent p-0"
      >
        {totals}
      </button>

      {tooltipOpen && hasBreakdown && (
        <div
          role="dialog"
          className="absolute right-0 z-40 mt-2 w-72 rounded-lg border border-amber-200 bg-white p-3 text-[11.5px] shadow-lg ring-1 ring-amber-100"
        >
          <p className="mb-2 font-display text-[12px] font-semibold text-stone-900">
            {t('research.cost.breakdown')}
          </p>
          {Object.keys(usage.by_model).length > 0 && (
            <section className="mb-2">
              <h4 className="mb-1 text-[10px] uppercase tracking-wider text-stone-500">
                {t('research.cost.byModel')}
              </h4>
              <ul className="space-y-0.5">
                {Object.entries(usage.by_model).map(([model, row]) => (
                  <li
                    key={model}
                    className="flex items-baseline justify-between gap-2"
                  >
                    <span className="truncate font-mono text-stone-700">
                      {model}
                    </span>
                    <span className="tabular-nums text-stone-600">
                      {formatTokens(row.tokens)} {t('research.cost.tokens')} ·{' '}
                      {formatUsd(row.cost_usd)}
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          )}
          {Object.keys(usage.by_agent).length > 0 && (
            <section>
              <h4 className="mb-1 text-[10px] uppercase tracking-wider text-stone-500">
                {t('research.cost.byAgent')}
              </h4>
              <ul className="space-y-0.5">
                {Object.entries(usage.by_agent).map(([agent, row]) => (
                  <li
                    key={agent}
                    className="flex items-baseline justify-between gap-2"
                  >
                    <span className="truncate font-mono text-stone-700">
                      {agent}
                    </span>
                    <span className="tabular-nums text-stone-600">
                      {formatTokens(row.tokens)} {t('research.cost.tokens')} ·{' '}
                      {formatUsd(row.cost_usd)}
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      )}
    </span>
  );
}

export default CostCounter;
