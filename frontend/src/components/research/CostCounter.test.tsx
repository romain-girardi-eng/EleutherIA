/**
 * CostCounter — verifies the live token + USD badge renders the running
 * totals and formats USD according to the rules described in the
 * component header (4 decimals < $1, 2 decimals ≥ $1, thousands separators
 * for tokens).
 */

import type React from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { I18nextProvider } from 'react-i18next';
import i18n from '../../i18n/config';
import { CostCounter, formatTokens, formatUsd } from './CostCounter';
import type { TokenUsageState } from '../../hooks/useResearchStream';

const renderWithI18n = (ui: React.ReactElement) =>
  render(<I18nextProvider i18n={i18n}>{ui}</I18nextProvider>);

const baseUsage: TokenUsageState = {
  total_tokens: 0,
  total_cost_usd: 0,
  by_agent: {},
  by_model: {},
  by_provider: {},
};

describe('CostCounter format helpers', () => {
  it('formats sub-dollar costs with 4 decimals', () => {
    expect(formatUsd(0.034)).toBe('$0.0340');
    expect(formatUsd(0.000123)).toBe('$0.0001');
  });

  it('formats super-dollar costs with thousands separators', () => {
    expect(formatUsd(12.5)).toBe('$12.50');
    expect(formatUsd(1234.5)).toBe('$1,234.50');
  });

  it('treats invalid input as zero', () => {
    expect(formatUsd(Number.NaN)).toBe('$0.0000');
    expect(formatTokens(Number.NaN)).toBe('0');
  });

  it('uses locale-formatted integers for token counts', () => {
    expect(formatTokens(12_348)).toBe('12,348');
  });
});

describe('<CostCounter />', () => {
  it('renders the running totals next to the streaming pane', () => {
    renderWithI18n(
      <CostCounter
        usage={{
          ...baseUsage,
          total_tokens: 12_348,
          total_cost_usd: 0.034,
        }}
      />,
    );
    const badge = screen.getByRole('status');
    expect(badge.textContent ?? '').toMatch(/\$0\.0340/);
    expect(badge.textContent ?? '').toMatch(/12,348/);
  });

  it('renders zero state when no tokens have flowed yet', () => {
    renderWithI18n(<CostCounter usage={baseUsage} />);
    const badge = screen.getByRole('status');
    expect(badge.textContent ?? '').toMatch(/\$0\.0000/);
  });
});
