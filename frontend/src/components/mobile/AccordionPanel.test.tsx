import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import AccordionPanel from './AccordionPanel';

vi.mock('../../context/DeviceContext', () => ({
  useDevice: () => ({ isMobile: false }),
}));

describe('AccordionPanel semantics', () => {
  it('renders the requested title heading level', () => {
    render(
      <AccordionPanel title="Chrono-Storyline" headingLevel={2}>
        Timeline
      </AccordionPanel>,
    );

    expect(screen.getByRole('heading', { level: 2, name: 'Chrono-Storyline' })).toBeVisible();
  });
});
