/**
 * The two surfaces the parallel-run model adds to the chat column: the tab
 * bar (one chip per run) and the ask box (never disabled by a background
 * stream; Stop targets the active run only).
 */

import { describe, it, expect, beforeAll, vi } from 'vitest';
import { createRef } from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { I18nextProvider } from 'react-i18next';
import i18n from '../../i18n/config';
import RunTabs from './RunTabs';
import ChatInput from './ChatInput';

const wrap = (ui: React.ReactElement) =>
  render(<I18nextProvider i18n={i18n}>{ui}</I18nextProvider>);

beforeAll(async () => {
  await i18n.changeLanguage('en');
});

describe('RunTabs', () => {
  const runs = [
    { id: 'a', question: 'Did Chrysippus hold that assent is up to us?', status: 'streaming' as const },
    { id: 'b', question: 'What does Alexander argue in De fato 20?', status: 'done' as const },
    { id: 'c', question: 'How does Origen read Romans 9?', status: 'error' as const },
  ];

  it('stays hidden while a single run exists', () => {
    const { container } = wrap(
      <RunTabs
        runs={[runs[0]]}
        activeRunId="a"
        onSelect={vi.fn()}
        onClose={vi.fn()}
        onRetry={vi.fn()}
      />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it('renders one chip per run with its live status', () => {
    wrap(
      <RunTabs
        runs={runs}
        activeRunId="b"
        onSelect={vi.fn()}
        onClose={vi.fn()}
        onRetry={vi.fn()}
      />,
    );

    const tabs = screen.getAllByRole('tab');
    expect(tabs).toHaveLength(3);
    expect(tabs[1]).toHaveAttribute('aria-selected', 'true');
    expect(tabs[0]).toHaveAttribute('aria-selected', 'false');

    expect(screen.getByLabelText('Running')).toBeInTheDocument();
    expect(screen.getByLabelText('Answered')).toBeInTheDocument();
    expect(screen.getByLabelText('Failed')).toBeInTheDocument();
  });

  it('selects and closes the run it was aimed at', () => {
    const onSelect = vi.fn();
    const onClose = vi.fn();
    wrap(
      <RunTabs
        runs={runs}
        activeRunId="a"
        onSelect={onSelect}
        onClose={onClose}
        onRetry={vi.fn()}
      />,
    );

    fireEvent.click(screen.getAllByRole('tab')[2]);
    expect(onSelect).toHaveBeenCalledWith('c');

    fireEvent.click(
      screen.getByLabelText(`Close this run — ${runs[1].question}`),
    );
    expect(onClose).toHaveBeenCalledWith('b');
  });
});

describe('ChatInput', () => {
  const baseProps = {
    query: 'a question',
    setQuery: vi.fn(),
    inputRef: createRef<HTMLTextAreaElement>(),
    onSubmit: vi.fn(),
    onStop: vi.fn(),
    maxConcurrentRuns: 3,
  };

  it('keeps the ask box live during a stream and stops only the active run', () => {
    const onStop = vi.fn();
    wrap(<ChatInput {...baseProps} onStop={onStop} streaming canSubmit />);

    expect(screen.getByRole('textbox')).not.toBeDisabled();
    expect(screen.getByRole('button', { name: 'Ask' })).toBeEnabled();

    fireEvent.click(screen.getByRole('button', { name: 'Stop the active run' }));
    expect(onStop).toHaveBeenCalledTimes(1);
  });

  it('explains why asking is blocked once the cap is reached', () => {
    wrap(<ChatInput {...baseProps} streaming canSubmit={false} />);

    expect(screen.getByRole('button', { name: 'Ask' })).toBeDisabled();
    expect(screen.getByTestId('run-cap-hint')).toHaveTextContent(
      /Up to 3 questions can run at once/i,
    );
  });

  it('offers no Stop button when the active run is not streaming', () => {
    wrap(<ChatInput {...baseProps} streaming={false} canSubmit />);
    expect(
      screen.queryByRole('button', { name: 'Stop the active run' }),
    ).not.toBeInTheDocument();
  });
});
