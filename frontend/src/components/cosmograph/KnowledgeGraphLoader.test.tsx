import { act, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { KnowledgeGraphLoader } from './KnowledgeGraphLoader';

vi.mock('../../hooks/useKgStats', () => ({
  useKgStats: () => ({ nodes: 23330, edges: 113800, isCached: false, isLoading: false, error: null }),
}));

describe('KnowledgeGraphLoader', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('states the real work and never quotes an edge total it cannot match', () => {
    render(<KnowledgeGraphLoader phase="data" />);
    const status = screen.getByRole('progressbar');
    expect(status.getAttribute('aria-valuetext')).toMatch(/nodes and their relations/);
    expect(screen.queryByText(/113/)).not.toBeInTheDocument();
  });

  it('admits when loading is slow, with the elapsed time', () => {
    render(<KnowledgeGraphLoader phase="render" />);
    expect(screen.getByText('Drawing the graph on screen…')).toBeInTheDocument();
    expect(screen.queryByText(/Still working/)).not.toBeInTheDocument();
    act(() => {
      vi.advanceTimersByTime(7000);
    });
    expect(screen.getByText(/Still working/)).toBeInTheDocument();
  });

  it('shows the still poster instead of the film on small or touch screens', () => {
    const { container } = render(<KnowledgeGraphLoader />);
    expect(container.querySelector('video')).toBeNull();
    expect(container.querySelector('img')).not.toBeNull();
  });
});
