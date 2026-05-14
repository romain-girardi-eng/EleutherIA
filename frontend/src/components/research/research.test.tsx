import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { I18nextProvider } from 'react-i18next';
import i18n from '../../i18n/config';
import { CitationCard } from './CitationCard';
import { CitationFeed } from './CitationFeed';
import { AgentTimeline } from './AgentTimeline';
import { LiveKGViz } from './LiveKGViz';
import { StreamingAnswer } from './StreamingAnswer';
import type { CitationEntry, PairedToolCall, KGActivation } from '../../hooks/useResearchStream';
import type { AgentEvent } from '../../types/agent-events';

const renderWithI18n = (ui: React.ReactElement) =>
  render(<I18nextProvider i18n={i18n}>{ui}</I18nextProvider>);

const citation: CitationEntry = {
  passage_id: 'p1',
  cts_urn: 'urn:cts:latinLit:phi0474.phi051:40',
  work_label: 'Cicero, De Fato 40',
  excerpt: 'Chrysippus likens the cylinder rolled down a slope.',
  node_ids: ['person_chrysippus'],
  confidence: 0.91,
  verified: true,
  arrived_at: 0,
};

describe('CitationCard', () => {
  it('renders work label, excerpt, and verified badge', () => {
    renderWithI18n(<CitationCard citation={citation} index={0} />);
    expect(screen.getByText('Cicero, De Fato 40')).toBeInTheDocument();
    expect(screen.getByText(/Chrysippus likens the cylinder/)).toBeInTheDocument();
  });
});

describe('CitationFeed', () => {
  it('renders empty state when no citations', () => {
    renderWithI18n(<CitationFeed citations={[]} isLive={false} />);
    expect(screen.getByText(/Citations will appear here|appariront/i)).toBeInTheDocument();
  });

  it('renders one card per citation', () => {
    renderWithI18n(
      <CitationFeed citations={[citation, { ...citation, passage_id: 'p2' }]} isLive={true} />,
    );
    expect(screen.getAllByText('Cicero, De Fato 40')).toHaveLength(2);
  });
});

describe('AgentTimeline', () => {
  it('shows idle state when no events', () => {
    renderWithI18n(<AgentTimeline events={[]} toolCalls={[]} isLive={false} />);
    expect(screen.getByText(/No session yet|Aucune session/i)).toBeInTheDocument();
  });

  it('renders milestone for agent_start', () => {
    const events: AgentEvent[] = [
      { type: 'agent_start', agent: 'Orchestrator', query: 'my question' },
    ];
    renderWithI18n(<AgentTimeline events={events} toolCalls={[]} isLive={true} />);
    expect(screen.getByText('my question')).toBeInTheDocument();
  });

  it('renders tool call card when paired', () => {
    const pair: PairedToolCall = {
      call: {
        type: 'tool_call',
        agent: 'A',
        tool: 'search_nodes',
        args: { q: 'x' },
        id: 'c1',
      },
      started_at: 0,
    };
    const events: AgentEvent[] = [pair.call];
    renderWithI18n(<AgentTimeline events={events} toolCalls={[pair]} isLive={false} />);
    expect(screen.getByText('search_nodes')).toBeInTheDocument();
  });
});

describe('LiveKGViz', () => {
  it('renders placeholder when no activations', () => {
    renderWithI18n(<LiveKGViz activations={[]} />);
    expect(screen.getByText(/No nodes activated|Aucun nœud/i)).toBeInTheDocument();
  });

  it('renders one circle per activation', () => {
    const activations: KGActivation[] = [
      {
        node_id: 'n1',
        label: 'One',
        node_type: 'concept',
        hits: 1,
        last_seen: 0,
      },
      {
        node_id: 'n2',
        label: 'Two',
        node_type: 'person',
        hits: 2,
        last_seen: 0,
      },
    ];
    const { container } = renderWithI18n(<LiveKGViz activations={activations} />);
    // 2 nodes × 2 circles each (halo + core) + 1 background rect, plus radialGradient
    expect(container.querySelectorAll('circle').length).toBe(4);
  });
});

describe('StreamingAnswer', () => {
  it('shows idle copy when no text', () => {
    renderWithI18n(<StreamingAnswer text="" citations={[]} isLive={false} />);
    expect(screen.getByText(/No answer yet|Aucune réponse/i)).toBeInTheDocument();
  });

  it('renders source chips for [Source N] markers', () => {
    renderWithI18n(
      <StreamingAnswer
        text="The cylinder argument [Source 1] is canonical."
        citations={[citation]}
        isLive={false}
      />,
    );
    expect(screen.getByText('[Source 1]')).toBeInTheDocument();
  });
});
