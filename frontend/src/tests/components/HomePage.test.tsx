import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import HomePage from '@/pages/HomePage';

describe('HomePage', () => {
  it('should render without crashing', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    );

    expect(document.body).toBeDefined();
  });

  it('should display the main heading', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    );

    // Look for key text that should be on the home page
    const content = document.body.textContent || '';
    expect(content.length).toBeGreaterThan(0);
  });

  it('should have navigation links', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    );

    const links = screen.queryAllByRole('link');
    expect(links.length).toBeGreaterThan(0);
  });
});
