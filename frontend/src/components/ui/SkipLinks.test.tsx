import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { SkipLinks } from './SkipLinks';

describe('SkipLinks shortcut ownership', () => {
  it('uses Alt+number only and ignores the workspace Alt+Shift chord', () => {
    Element.prototype.scrollIntoView = vi.fn();
    const { container } = render(
      <>
        <SkipLinks />
        <main id="main-content" tabIndex={-1}>Main</main>
        <nav id="navigation" tabIndex={-1}>Navigation</nav>
        <div id="search" tabIndex={-1}>Search</div>
        <footer id="footer" tabIndex={-1}>Footer</footer>
      </>,
    );
    const main = container.querySelector<HTMLElement>('#main-content');

    fireEvent.keyDown(document, { key: '¡', code: 'Digit1', altKey: true, shiftKey: true });
    expect(main).not.toHaveFocus();

    fireEvent.keyDown(document, { key: '¡', code: 'Digit1', altKey: true });
    expect(main).toHaveFocus();
  });

  it('omits skip destinations intentionally absent from a full-screen shell', () => {
    render(<SkipLinks excludeTargets={['footer']} />);

    expect(screen.queryByRole('link', { name: /Skip to footer/ })).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Skip to main content/ })).toBeVisible();
  });
});
