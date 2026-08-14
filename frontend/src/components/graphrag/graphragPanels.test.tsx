import { describe, it, expect, beforeAll } from 'vitest';
import { render, screen } from '@testing-library/react';
import { I18nextProvider } from 'react-i18next';
import i18n from '../../i18n/config';
import ResearchTimelinePanel from './ResearchTimelinePanel';
import LiveReasoningPanel from './LiveReasoningPanel';
import type { AgentStep } from '../../types/graphrag';

const renderWithI18n = (ui: React.ReactElement) =>
  render(<I18nextProvider i18n={i18n}>{ui}</I18nextProvider>);

beforeAll(async () => {
  await i18n.changeLanguage('en');
});

const toolResult = (id: string, tool: string, extra: Partial<AgentStep> = {}): AgentStep => ({
  id,
  type: 'tool_result',
  tool,
  summary: `${tool} done`,
  timestamp: 0,
  ...extra,
});

describe('ResearchTimelinePanel — skipped phases', () => {
  it('marks an empty phase as skipped when a later phase has rows', () => {
    // Only a "read" tool ran: classification and search were jumped over.
    const steps: AgentStep[] = [toolResult('s1', 'read_passages', { passageCount: 4 })];

    renderWithI18n(
      <ResearchTimelinePanel steps={steps} isActive={false} response={null} />,
    );

    // Classification + Search precede Reading → skipped, not pending.
    expect(screen.getAllByText('Skipped')).toHaveLength(2);
    expect(screen.getByRole('button', { name: /Classification/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /Search/i })).toBeDisabled();
    // Reading itself has rows and stays interactive.
    expect(screen.getByRole('button', { name: /Reading/i })).not.toBeDisabled();
  });

  it('leaves trailing empty phases pending, not skipped', () => {
    const steps: AgentStep[] = [toolResult('s1', 'search_nodes', { nodeCount: 3 })];

    renderWithI18n(
      <ResearchTimelinePanel steps={steps} isActive response={null} />,
    );

    // Only Classification precedes Search; Reading/Synthesis/Verification
    // are still ahead of the run.
    expect(screen.getAllByText('Skipped')).toHaveLength(1);
    expect(screen.getByRole('button', { name: /Synthesis/i })).toBeDisabled();
  });
});

describe('LiveReasoningPanel — empty states', () => {
  it('shows the idle empty state before a run starts', () => {
    renderWithI18n(<LiveReasoningPanel reasoning="" isStreaming={false} />);

    expect(
      screen.getByText(/full chain-of-thought will appear here during a live query/i),
    ).toBeInTheDocument();
    expect(screen.queryByText('No reasoning captured')).not.toBeInTheDocument();
  });

  it('shows the waiting state while the stream is open', () => {
    renderWithI18n(<LiveReasoningPanel reasoning="" isStreaming hasRunEnded={false} />);

    expect(screen.getByText(/Retrieval is still in progress/i)).toBeInTheDocument();
    expect(screen.queryByText('No reasoning captured')).not.toBeInTheDocument();
  });

  it('shows a distinct state when the run ended without a reasoning trace', () => {
    renderWithI18n(<LiveReasoningPanel reasoning="" isStreaming={false} hasRunEnded />);

    expect(screen.getByText('No reasoning captured')).toBeInTheDocument();
    expect(
      screen.getByText(/finished without streaming a chain-of-thought/i),
    ).toBeInTheDocument();
  });

  it('renders the trace when reasoning was captured', () => {
    renderWithI18n(
      <LiveReasoningPanel reasoning="Chrysippus distinguishes…" isStreaming={false} hasRunEnded />,
    );

    expect(screen.getByText(/Chrysippus distinguishes/)).toBeInTheDocument();
    expect(screen.queryByText('No reasoning captured')).not.toBeInTheDocument();
  });
});
