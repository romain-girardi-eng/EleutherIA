import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type React from 'react';
import { I18nextProvider } from 'react-i18next';
import { beforeAll, describe, expect, it, vi } from 'vitest';

import i18n from '../../i18n/config';
import type { TimelineOverview } from '../../types';
import TimelinePanel, { TIMELINE_PAGE_SIZE } from './TimelinePanel';

vi.mock('../mobile/AccordionPanel', () => ({
  default: ({
    children,
    className,
    headingLevel,
    title,
  }: {
    children: React.ReactNode;
    className?: string;
    headingLevel?: number;
    title: string;
  }) => (
    <section aria-label={title} className={className}>
      {headingLevel === 2 ? <h2>{title}</h2> : <h3>{title}</h3>}
      {children}
    </section>
  ),
}));

beforeAll(async () => {
  await i18n.changeLanguage('en');
});

const renderPanel = (ui: React.ReactElement) => render(<I18nextProvider i18n={i18n}>{ui}</I18nextProvider>);

function timeline(nodeCount = 80): TimelineOverview {
  return {
    periods: [
      {
        key: 'classical-greek',
        label: 'Classical Greek',
        startYear: -450,
        endYear: -323,
        counts: { concept: nodeCount },
        nodes: Array.from({ length: nodeCount }, (_, index) => ({
          id: `node-${index}`,
          label: `Node ${index.toString().padStart(3, '0')}`,
          type: 'concept',
          period: 'Classical Greek',
          school: index === nodeCount - 1 ? 'Hidden school' : 'Peripatetic',
          startYear: null,
          relationCount: 0,
        })),
      },
      {
        key: 'hellenistic',
        label: 'Hellenistic',
        startYear: -323,
        endYear: -31,
        counts: { person: 2 },
        nodes: [
          { id: 'zeno', label: 'Zeno of Citium', type: 'person', period: 'Hellenistic', school: 'Stoic', relationCount: 9 },
          { id: 'anon', label: 'Anonymous doxography', type: 'work', period: 'Hellenistic', school: null, relationCount: 1 },
        ],
      },
    ],
    totals: { nodes: nodeCount + 2, edges: 0, byType: { concept: nodeCount, person: 1, work: 1 } },
    range: { minYear: -450, maxYear: -31 },
  };
}

describe('TimelinePanel bounded progressive rendering', () => {
  it('keeps the live node DOM bounded and pages through the scoped period', async () => {
    const user = userEvent.setup();
    renderPanel(<TimelinePanel timeline={timeline()} activePeriodKey="classical-greek" onSelectNode={vi.fn()} />);

    expect(screen.getByRole('heading', { level: 2, name: 'Loci ledger' })).toBeVisible();
    expect(screen.getByLabelText('Loci ledger')).toHaveClass('min-w-0');
    expect(screen.getAllByTestId('timeline-node')).toHaveLength(TIMELINE_PAGE_SIZE);
    expect(screen.getAllByTestId('timeline-node')[0]).toHaveClass('min-h-11');
    expect(screen.getByText('Node 000')).toBeInTheDocument();
    expect(screen.queryByText('Node 024')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Next loci in Classical Greek' }));

    expect(screen.getAllByTestId('timeline-node')).toHaveLength(TIMELINE_PAGE_SIZE);
    expect(screen.getByText('Node 024')).toBeInTheDocument();
    expect(screen.queryByText('Node 000')).not.toBeInTheDocument();
    expect(screen.getByText('Showing 25–48 of 80')).toHaveAttribute('aria-live', 'polite');
  });

  it('lists every visible period, most connected first, when no period is scoped', () => {
    renderPanel(<TimelinePanel timeline={timeline()} onSelectNode={vi.fn()} />);
    expect(screen.getAllByTestId('timeline-node')[0]).toHaveTextContent('Zeno of Citium');
    expect(screen.getByText('82 loci, most connected first.')).toBeInTheDocument();
  });

  it('searches every node in scope, including rows outside the mounted page', async () => {
    const user = userEvent.setup();
    const onSelectNode = vi.fn();
    renderPanel(<TimelinePanel timeline={timeline()} onSelectNode={onSelectNode} />);

    await user.type(screen.getByRole('searchbox', { name: 'Search the loci in view' }), 'Hidden school');

    await waitFor(() => expect(screen.getByText('Node 079')).toBeInTheDocument());
    expect(screen.getAllByTestId('timeline-node')).toHaveLength(1);
    expect(screen.getByText('1 match in view.')).toHaveAttribute('aria-live', 'polite');

    await user.click(screen.getByRole('button', { name: /Node 079/ }));
    expect(onSelectNode).toHaveBeenCalledWith('node-79');
  });

  it('narrows to a school, including the "no school recorded" bucket', () => {
    const { rerender } = renderPanel(
      <TimelinePanel
        timeline={timeline()}
        schoolFilter={{ key: 'Stoic', members: ['Stoic'] }}
        onSelectNode={vi.fn()}
      />,
    );
    expect(screen.getAllByTestId('timeline-node')).toHaveLength(1);
    expect(screen.getByText('Zeno of Citium')).toBeInTheDocument();

    rerender(
      <I18nextProvider i18n={i18n}>
        <TimelinePanel timeline={timeline()} schoolFilter={{ key: '__none__', members: [null] }} onSelectNode={vi.fn()} />
      </I18nextProvider>,
    );
    expect(screen.getAllByTestId('timeline-node')).toHaveLength(1);
    expect(screen.getByText('Anonymous doxography')).toBeInTheDocument();
  });

  it('reflects the shared selection, comparison and evidence thread', async () => {
    const user = userEvent.setup();
    const onToggleCompare = vi.fn();
    renderPanel(
      <TimelinePanel
        timeline={timeline()}
        activePeriodKey="hellenistic"
        primarySelection="zeno"
        compareIds={['anon']}
        threadIds={['x', 'zeno']}
        onSelectNode={vi.fn()}
        onToggleCompare={onToggleCompare}
      />,
    );
    expect(screen.getAllByTestId('timeline-node')[0]).toHaveAttribute('aria-current', 'true');
    expect(screen.getByText('Step 2')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Remove Anonymous doxography from the comparison' })).toHaveAttribute('aria-pressed', 'true');

    await user.click(screen.getByRole('button', { name: 'Add Zeno of Citium to the comparison' }));
    expect(onToggleCompare).toHaveBeenCalledWith('zeno');
  });
});
