import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type React from 'react';
import { I18nextProvider } from 'react-i18next';
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest';

import i18n from '../../i18n/config';
import type { TimelinePeriodSummary } from '../../types';
import ChronosAxis from './ChronosAxis';
import { yearToFraction } from './chronosTimeline';

beforeAll(async () => {
  await i18n.changeLanguage('en');
  // jsdom ships no PointerEvent; a MouseEvent subclass carries clientX/button.
  if (!('PointerEvent' in window)) {
    class PointerEventPolyfill extends MouseEvent {
      readonly pointerId: number;
      constructor(type: string, init: PointerEventInit = {}) {
        super(type, init);
        this.pointerId = init.pointerId ?? 0;
      }
    }
    Object.defineProperty(window, 'PointerEvent', { value: PointerEventPolyfill, configurable: true });
  }
});

afterEach(() => {
  vi.restoreAllMocks();
});

function period(label: string, key: string, startYear: number | null, endYear: number | null, count: number): TimelinePeriodSummary {
  return {
    key,
    label,
    startYear,
    endYear,
    counts: {},
    nodes: Array.from({ length: count }, (_, index) => ({
      id: `${key}-${index}`,
      label: `${label} ${index}`,
      type: 'concept',
      period: label,
    })),
  };
}

const PERIODS = [
  period('Classical Greek', 'classical-greek', -450, -323, 20),
  period('Hellenistic', 'hellenistic', -323, -31, 5),
  period('Unspecified', 'unspecified', null, null, 3),
];

function renderAxis(props: Partial<React.ComponentProps<typeof ChronosAxis>> = {}) {
  const onWindowChange = vi.fn();
  const onActivatePeriod = vi.fn();
  render(
    <I18nextProvider i18n={i18n}>
      <ChronosAxis
        periods={PERIODS}
        windowStart={null}
        windowEnd={null}
        onWindowChange={onWindowChange}
        activePeriodKey={null}
        onActivatePeriod={onActivatePeriod}
        markers={new Map()}
        {...props}
      />
    </I18nextProvider>,
  );
  return { onWindowChange, onActivatePeriod };
}

describe('ChronosAxis', () => {
  it('labels rows with era-aware ranges and keeps undated periods off the axis', () => {
    renderAxis();
    expect(screen.getByRole('button', { name: 'Classical Greek, 450 BCE – 323 BCE, 20 loci' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Unspecified, No date range asserted, 3 loci' })).toBeInTheDocument();
    expect(screen.getByText('Undated · not placed on the axis')).toBeInTheDocument();
  });

  it('uses a roving tab stop with arrow-key navigation and toggles a period', async () => {
    const user = userEvent.setup();
    const { onActivatePeriod } = renderAxis();
    const rows = screen.getAllByRole('button', { pressed: false });
    expect(rows[0]).toHaveAttribute('tabindex', '0');
    expect(rows[1]).toHaveAttribute('tabindex', '-1');

    rows[0].focus();
    await user.keyboard('{ArrowDown}');
    expect(rows[1]).toHaveFocus();
    await user.keyboard('{End}');
    expect(rows[2]).toHaveFocus();
    await user.keyboard('{Enter}');
    expect(onActivatePeriod).toHaveBeenCalledWith('unspecified');
  });

  it('clears the active period on Escape', async () => {
    const user = userEvent.setup();
    const { onActivatePeriod } = renderAxis({ activePeriodKey: 'hellenistic' });
    screen.getAllByRole('button')[0].focus();
    await user.keyboard('{Escape}');
    expect(onActivatePeriod).toHaveBeenCalledWith(null);
  });

  it('turns a click on the era strip into that era, and a drag into a snapped window', () => {
    const { onWindowChange } = renderAxis();
    const strip = screen.getByTitle('Drag to select a time window · click an era to jump to it');
    vi.spyOn(strip, 'getBoundingClientRect').mockReturnValue(DOMRect.fromRect({ x: 0, y: 0, width: 1000, height: 40 }));
    Object.defineProperty(strip, 'setPointerCapture', { value: vi.fn(), configurable: true });

    const x = (year: number) => yearToFraction(year) * 1000;
    fireEvent.pointerDown(strip, { button: 0, clientX: x(-200), pointerId: 1 });
    fireEvent.pointerUp(strip, { button: 0, clientX: x(-200), pointerId: 1 });
    expect(onWindowChange).toHaveBeenLastCalledWith(-323, -31);

    fireEvent.pointerDown(strip, { button: 0, clientX: x(-402), pointerId: 1 });
    fireEvent.pointerMove(strip, { clientX: x(-100), pointerId: 1 });
    fireEvent.pointerMove(strip, { clientX: x(197), pointerId: 1 });
    fireEvent.pointerUp(strip, { button: 0, clientX: x(197), pointerId: 1 });
    expect(onWindowChange).toHaveBeenLastCalledWith(-400, 200);
  });
});
