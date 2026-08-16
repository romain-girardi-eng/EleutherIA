import { describe, it, expect, beforeAll } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
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

describe('ResearchTimelinePanel — abandoned leads', () => {
  const note = (
    id: string,
    noteKind: AgentStep['noteKind'],
    summary: string,
    extra: Partial<AgentStep> = {},
  ): AgentStep => ({ id, type: 'research_note', noteKind, summary, timestamp: 0, ...extra });

  it('renders a dropped lead inside the phase where it happened', () => {
    const steps: AgentStep[] = [
      toolResult('s1', 'search_nodes', { nodeCount: 3 }),
      note('n1', 'dead_end', 'Searched "αὐτεξούσιον" via search_passages — no evidence came back.', {
        stage: 'agent_loop',
        detail: 'looking for a Stoic anchor',
      }),
    ];

    renderWithI18n(<ResearchTimelinePanel steps={steps} isActive response={null} />);

    // `agent_loop` notes belong to the Search phase, which is expanded (active).
    expect(screen.getByText(/no evidence came back/)).toBeInTheDocument();
    expect(screen.getByText('looking for a Stoic anchor')).toBeInTheDocument();
    expect(screen.getByText('Dead end')).toBeInTheDocument();
    // The phase header counts the dropped lead.
    expect(screen.getByText('1 dropped')).toBeInTheDocument();
  });

  it('labels each kind of dropped lead', () => {
    const steps: AgentStep[] = [
      note('n1', 'abandoned', 'Debate lead abandoned.', { stage: 'controversy_map' }),
      note('n2', 'gap', 'Evidence judged insufficient.', { stage: 'quality_gate' }),
      note('n3', 'rejected_claim', 'Claim dropped.', { stage: 'claim_ledger' }),
    ];

    renderWithI18n(<ResearchTimelinePanel steps={steps} isActive={false} response={null} />);

    // Completed phases collapse; open every phase that has rows.
    for (const name of [/Reading/i, /Synthesis/i]) {
      fireEvent.click(screen.getByRole('button', { name }));
    }

    expect(screen.getByText('Abandoned lead')).toBeInTheDocument();
    expect(screen.getByText('Gap')).toBeInTheDocument();
    expect(screen.getByText('Rejected claim')).toBeInTheDocument();
  });

  it('routes a note to the phase named by its stage', () => {
    const steps: AgentStep[] = [
      note('n1', 'rejected_claim', 'Claim dropped in synthesis.', { stage: 'claim_ledger' }),
    ];

    renderWithI18n(<ResearchTimelinePanel steps={steps} isActive response={null} />);

    // Only Synthesis has rows, so it is the active (expanded) phase.
    expect(screen.getByRole('button', { name: /Synthesis/i })).not.toBeDisabled();
    expect(screen.getByRole('button', { name: /Reading/i })).toBeDisabled();
    expect(screen.getByText('Claim dropped in synthesis.')).toBeInTheDocument();
  });
});

describe('LiveReasoningPanel — pipeline research journal', () => {
  const JOURNAL = '— Searched "αὐτεξούσιον" — nothing came back.';

  it('labels the journal as the pipeline’s own record, not model reasoning', () => {
    renderWithI18n(
      <LiveReasoningPanel reasoning={JOURNAL} isStreaming={false} hasRunEnded isJournal />,
    );

    expect(screen.getByText('Research journal')).toBeInTheDocument();
    expect(screen.queryByText('Model reasoning')).not.toBeInTheDocument();
    expect(
      screen.getByText(/not the model's chain-of-thought/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/Searched/)).toBeInTheDocument();
  });

  it('keeps the model-reasoning framing when the model did stream a trace', () => {
    renderWithI18n(
      <LiveReasoningPanel reasoning="Chrysippus distinguishes…" isStreaming={false} hasRunEnded />,
    );

    expect(screen.getByText('Model reasoning')).toBeInTheDocument();
    expect(screen.queryByText('Research journal')).not.toBeInTheDocument();
    expect(
      screen.queryByText(/not the model's chain-of-thought/i),
    ).not.toBeInTheDocument();
  });

  it('points at the activity timeline when nothing was captured at all', () => {
    renderWithI18n(<LiveReasoningPanel reasoning="" isStreaming={false} hasRunEnded />);

    expect(screen.getByText('No reasoning captured')).toBeInTheDocument();
    expect(screen.getByText(/including the leads it dropped/i)).toBeInTheDocument();
  });
});
