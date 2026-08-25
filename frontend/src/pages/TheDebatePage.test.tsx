import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { WithGreek } from './TheDebatePage';

describe('WithGreek', () => {
  // Instrument Serif and DM Sans have no Greek coverage, so inline polytonic
  // fell back to Georgia mid-sentence. Every Greek run must be marked so it
  // gets EB Garamond — and lang="grc" so it is machine-legible too.
  it('wraps a Greek run and leaves the surrounding English alone', () => {
    const { container } = render(
      <WithGreek text='everything is woven into fate (εἱμαρμένη), yet assent remains ours.' />,
    );
    const marked = container.querySelectorAll('[lang="grc"]');
    expect(marked).toHaveLength(1);
    expect(marked[0].textContent).toContain('εἱμαρμένη');
    expect(marked[0]).toHaveClass('font-garamond');
    expect(container.textContent).toBe(
      'everything is woven into fate (εἱμαρμένη), yet assent remains ours.',
    );
  });

  it('marks every Greek run, not every other one', () => {
    // Regression guard: classifying the split parts with the /g regex would
    // advance lastIndex and skip alternate matches.
    const { container } = render(
      <WithGreek text='τὸ ἐφ’ ἡμῖν and then εἱμαρμένη and then αὐτεξούσιον.' />,
    );
    expect(container.querySelectorAll('[lang="grc"]')).toHaveLength(3);
  });

  it('preserves text with no Greek at all', () => {
    render(<WithGreek text="free choice (liberum arbitrium) is real." />);
    expect(
      screen.getByText('free choice (liberum arbitrium) is real.'),
    ).toBeInTheDocument();
  });

  it('keeps polytonic breathings and accents inside the marked run', () => {
    const { container } = render(<WithGreek text='the soul’s αὐτεξούσιον grounds it' />);
    const marked = container.querySelector('[lang="grc"]');
    expect(marked?.textContent?.trim()).toBe('αὐτεξούσιον');
  });
});
