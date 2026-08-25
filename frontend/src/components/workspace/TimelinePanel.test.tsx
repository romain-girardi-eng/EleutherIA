import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

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

function timeline(nodeCount = 80): TimelineOverview {
  return {
    periods: [
      {
        key: 'classical',
        label: 'Classical Greek',
        startYear: -450,
        endYear: -323,
        counts: { concept: nodeCount },
        nodes: Array.from({ length: nodeCount }, (_, index) => ({
          id: `node-${index}`,
          label: `Node ${index.toString().padStart(3, '0')}`,
          type: 'concept',
          period: 'Classical Greek',
          school: index === nodeCount - 1 ? 'Hidden school' : 'Peripatetics',
          startYear: -400,
          relationCount: 0,
        })),
      },
    ],
    totals: { nodes: nodeCount, edges: 0, byType: { concept: nodeCount } },
    range: { minYear: -450, maxYear: -323 },
  };
}

describe('TimelinePanel bounded progressive rendering', () => {
  it('keeps the live node DOM bounded and pages through the complete period', async () => {
    const user = userEvent.setup();
    render(<TimelinePanel timeline={timeline()} onSelectNode={vi.fn()} />);

    expect(screen.getByRole('heading', { level: 2, name: 'Chrono-Storyline' })).toBeVisible();
    expect(screen.getByLabelText('Chrono-Storyline')).toHaveClass('min-w-0');
    expect(screen.getAllByTestId('timeline-node')).toHaveLength(TIMELINE_PAGE_SIZE);
    expect(screen.getAllByTestId('timeline-node')[0]).toHaveClass('min-h-11');
    expect(screen.getByText('Node 000')).toBeInTheDocument();
    expect(screen.queryByText('Node 024')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Next nodes in Classical Greek' }));

    expect(screen.getAllByTestId('timeline-node')).toHaveLength(TIMELINE_PAGE_SIZE);
    expect(screen.getByText('Node 024')).toBeInTheDocument();
    expect(screen.queryByText('Node 000')).not.toBeInTheDocument();
    expect(screen.getByText('Showing 25–48 of 80')).toHaveAttribute('aria-live', 'polite');
  });

  it('searches every node, including rows outside the mounted page', async () => {
    const user = userEvent.setup();
    const onSelectNode = vi.fn();
    render(<TimelinePanel timeline={timeline()} onSelectNode={onSelectNode} />);

    const search = screen.getByRole('searchbox', {
      name: 'Search every node in this chronology',
    });
    await user.type(search, 'Hidden school');

    await waitFor(() => expect(screen.getByText('Node 079')).toBeInTheDocument());
    expect(screen.getAllByTestId('timeline-node')).toHaveLength(1);
    expect(screen.getByText('1 matching nodes across all periods.')).toHaveAttribute(
      'aria-live',
      'polite',
    );

    await user.click(screen.getByRole('button', { name: /Node 079/ }));
    expect(onSelectNode).toHaveBeenCalledWith('node-79');
  });
});
