import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { Button } from './button';

describe('Button asChild composition', () => {
  it('styles the concrete child without forwarding props to a Fragment', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => undefined);
    render(
      <Button asChild className="composed-link">
        <a href="/research">Research</a>
      </Button>,
    );

    expect(screen.getByRole('link', { name: 'Research' })).toHaveClass('composed-link');
    expect(consoleError).not.toHaveBeenCalled();
    consoleError.mockRestore();
  });
});
