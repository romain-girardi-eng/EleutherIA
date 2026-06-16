import { MemoryRouter } from 'react-router-dom';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CitationRenderer } from './CitationRenderer';
import type { SourceCitation } from '../types';

const scholarlySources: SourceCitation[] = [
  {
    id: 1,
    nodeId: 'origen-de-principiis',
    nodeLabel: 'Origen, De Principiis',
    nodeType: 'Work',
    metadata: {},
  },
  {
    id: 2,
    nodeId: 'origen-contra-celsum',
    nodeLabel: 'Origen, Contra Celsum',
    nodeType: 'Work',
    metadata: {},
  },
];

describe('CitationRenderer', () => {
  it('renders grouped [Source N] citations as clickable source buttons', async () => {
    const user = userEvent.setup();
    const onSourceClick = vi.fn();

    render(
      <MemoryRouter>
        <CitationRenderer
          content="Origen distinguishes foreknowledge from causality [Source 1, Source 2]."
          sources={scholarlySources}
          onSourceClick={onSourceClick}
        />
      </MemoryRouter>,
    );

    const sourceOne = screen.getByRole('button', {
      name: 'Source 1: Origen, De Principiis',
    });
    const sourceTwo = screen.getByRole('button', {
      name: 'Source 2: Origen, Contra Celsum',
    });

    expect(sourceOne).toBeInTheDocument();
    expect(sourceTwo).toBeInTheDocument();

    await user.click(sourceTwo);

    expect(onSourceClick).toHaveBeenCalledWith(1, scholarlySources[1]);
  });

  it('renders an inline scholar badge with the resolved label, never the raw node id', async () => {
    const user = userEvent.setup();
    const onNodeCitationClick = vi.fn();

    render(
      <MemoryRouter>
        <CitationRenderer
          content="The Stoic view is debated [P_scholarly_argument_long_2002: Long 2002, CUP p.12]."
          sources={[]}
          onNodeCitationClick={onNodeCitationClick}
        />
      </MemoryRouter>,
    );

    // The badge shows the human label ("Long 2002"), NOT the raw node id.
    const badge = screen.getByRole('button', {
      name: /Scholar citation/i,
    });
    expect(badge).toBeInTheDocument();
    expect(badge.textContent).toContain('Long 2002');
    expect(badge.textContent).not.toContain('scholarly_argument_');

    await user.click(badge);
    // Clicking opens exactly ONE surface, carrying the stable node id.
    expect(onNodeCitationClick).toHaveBeenCalledTimes(1);
    expect(onNodeCitationClick).toHaveBeenCalledWith('scholarly_argument_long_2002');
  });

  it('keeps [P1] passage citations clickable', async () => {
    const user = userEvent.setup();
    const onPassageCitationClick = vi.fn();

    render(
      <MemoryRouter>
        <CitationRenderer
          content="See the passage context [P1]."
          sources={[
            {
              id: 1,
              nodeId: '123e4567-e89b-12d3-a456-426614174000',
              nodeLabel: 'Origen passage',
              nodeType: 'Passage',
              metadata: {},
            },
          ]}
          onPassageCitationClick={onPassageCitationClick}
        />
      </MemoryRouter>,
    );

    await user.click(screen.getByRole('button', { name: 'P1' }));

    expect(onPassageCitationClick).toHaveBeenCalledWith(
      '123e4567-e89b-12d3-a456-426614174000',
    );
  });
});
