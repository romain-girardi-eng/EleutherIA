import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { I18nextProvider } from 'react-i18next';
import i18n from '../../../i18n/config';
import { BibliographyPane } from './BibliographyPane';
import { MethodologyNotesPane } from './MethodologyNotesPane';
import { ExportToolbar } from './ExportToolbar';
import { PassageViewer } from './PassageViewer';
import { SessionHistory } from './SessionHistory';
import { AgentTrace } from './AgentTrace';
import { useBibliography } from '../../../hooks/useBibliography';
import type { AgentEvent } from '../../../types/agent-events';
import { doctoralApi } from '../../../services/doctoralApi';
import { apiClient } from '../../../api/client';
import { ToastProvider } from '../../../components/ui/Toast';

const renderWithI18n = (ui: React.ReactElement) =>
  render(
    <ToastProvider>
      <I18nextProvider i18n={i18n}>{ui}</I18nextProvider>
    </ToastProvider>,
  );

// ---------- BibliographyPane ----------

function BibliographyHarness({ children }: { children: (b: ReturnType<typeof useBibliography>) => React.ReactNode }) {
  const b = useBibliography('test-session');
  return <>{children(b)}</>;
}

describe('BibliographyPane', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('renders empty state with no entries', () => {
    renderWithI18n(
      <BibliographyHarness>
        {(b) => <BibliographyPane bibliography={b} />}
      </BibliographyHarness>,
    );
    expect(
      screen.getByText(/Save passages and scholars|Enregistrez/i),
    ).toBeInTheDocument();
  });

  it('shows export toolbar when traceId is provided', () => {
    renderWithI18n(
      <BibliographyHarness>
        {(b) => <BibliographyPane bibliography={b} traceId="trace-abc" />}
      </BibliographyHarness>,
    );
    expect(screen.getByText(/BibTeX/i)).toBeInTheDocument();
    expect(screen.getByText(/Zotero/i)).toBeInTheDocument();
  });

  it('has tabs with ARIA roles', () => {
    renderWithI18n(
      <BibliographyHarness>
        {(b) => <BibliographyPane bibliography={b} />}
      </BibliographyHarness>,
    );
    expect(screen.getAllByRole('tab')).toHaveLength(3);
  });
});

// ---------- MethodologyNotesPane ----------

describe('MethodologyNotesPane', () => {
  it('renders empty state with no events', () => {
    renderWithI18n(<MethodologyNotesPane events={[]} />);
    expect(
      screen.getByText(/Methodology flags|Les avertissements/i),
    ).toBeInTheDocument();
  });

  it('renders methodology_flagged events with severity', () => {
    const events: AgentEvent[] = [
      {
        type: 'methodology_flagged',
        flag_type: 'anachronism',
        severity: 'blocker',
        issue: 'Calling Chrysippus a compatibilist',
        suggested_revision: "Use 'soft determinism' qualifier",
      },
    ];
    renderWithI18n(<MethodologyNotesPane events={events} />);
    expect(screen.getByText(/Calling Chrysippus/i)).toBeInTheDocument();
    expect(screen.getByText(/soft determinism/i)).toBeInTheDocument();
  });

  it('calls onAnchorClick when a citation passage_id is clicked', async () => {
    const onAnchorClick = vi.fn();
    const events: AgentEvent[] = [
      {
        type: 'citation_verified',
        passage_id: 'p_42',
        verified: true,
        reason: 'matches DB',
      },
    ];
    renderWithI18n(
      <MethodologyNotesPane events={events} onAnchorClick={onAnchorClick} />,
    );
    await userEvent.click(screen.getByText('p_42'));
    expect(onAnchorClick).toHaveBeenCalledWith('p_42');
  });
});

// ---------- ExportToolbar ----------

describe('ExportToolbar', () => {
  it('renders all 6 export formats', () => {
    renderWithI18n(<ExportToolbar traceId="t1" />);
    expect(screen.getByText('Markdown')).toBeInTheDocument();
    expect(screen.getByText('LaTeX')).toBeInTheDocument();
    expect(screen.getByText('BibTeX')).toBeInTheDocument();
    expect(screen.getByText('Zotero')).toBeInTheDocument();
    expect(screen.getByText('RIS')).toBeInTheDocument();
    expect(screen.getByText(/Word/i)).toBeInTheDocument();
  });

  it('shows share button — create mode without shareUrl, copy mode with shareUrl', () => {
    const { rerender } = renderWithI18n(<ExportToolbar traceId="t1" />);
    // Without shareUrl: shows "Partager" create button
    expect(screen.getByText(/Partager/i)).toBeInTheDocument();
    rerender(
      <ToastProvider>
        <I18nextProvider i18n={i18n}>
          <ExportToolbar traceId="t1" shareUrl="https://x.test/s" />
        </I18nextProvider>
      </ToastProvider>,
    );
    // With shareUrl: still shows a Share/Partager button (copy mode)
    expect(screen.getByText(/Share|Partager/i)).toBeInTheDocument();
  });

  it('has toolbar role and aria-label', () => {
    renderWithI18n(<ExportToolbar traceId="t1" />);
    expect(screen.getByRole('toolbar')).toBeInTheDocument();
  });
});

// ---------- PassageViewer ----------

describe('PassageViewer', () => {
  beforeEach(() => {
    vi.spyOn(doctoralApi, 'getPassage').mockResolvedValue({
      passage_id: 'p1',
      work_id: 'work_a',
      work_label: 'Cicero, De Fato 40',
      cts_urn: 'urn:cts:latinLit:phi0474.phi051:40',
      text_original: 'cylindrum...',
      translation: 'cylinder rolled down a slope',
      translation_provenance: 'crisp_2000',
      edition: 'Bayer',
      editor: 'Bayer',
      year: 1990,
    });
    vi.spyOn(doctoralApi, 'getSection').mockResolvedValue({
      before: [],
      passage: { passage_id: 'p1', text_original: 'cylindrum...' },
      after: [],
    });
    vi.spyOn(doctoralApi, 'getNeighbors').mockResolvedValue({
      node_id: 'p1',
      neighbors: [],
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('does not render when closed', () => {
    renderWithI18n(
      <PassageViewer passageId="p1" open={false} onClose={() => {}} />,
    );
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('fetches and renders the passage detail', async () => {
    renderWithI18n(
      <PassageViewer passageId="p1" open={true} onClose={() => {}} />,
    );
    await waitFor(() =>
      expect(screen.getByText(/Cicero, De Fato 40/)).toBeInTheDocument(),
    );
    expect(screen.getByText(/cylinder rolled/)).toBeInTheDocument();
    expect(screen.getByText(/Crisp 2000/)).toBeInTheDocument();
  });

  it('calls onSaveToBibliography when save clicked', async () => {
    const onSave = vi.fn();
    renderWithI18n(
      <PassageViewer
        passageId="p1"
        open={true}
        onClose={() => {}}
        onSaveToBibliography={onSave}
      />,
    );
    await waitFor(() =>
      expect(screen.getByText(/Cicero, De Fato 40/)).toBeInTheDocument(),
    );
    const saveBtn = screen.getByRole('button', {
      name: /Save to bibliography|Ajouter/i,
    });
    fireEvent.click(saveBtn);
    expect(onSave).toHaveBeenCalled();
    expect(onSave.mock.calls[0][0].kind).toBe('primary');
  });
});

// ---------- SessionHistory ----------

describe('SessionHistory', () => {
  beforeEach(() => {
    vi.spyOn(apiClient, 'listConversations').mockResolvedValue({
      success: true,
      count: 1,
      conversations: [
        {
          conversation_id: 'c1',
          user_id: 'u1',
          title: 'Free will in Chrysippus',
          settings: { rigor_level: 'doctoral' },
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          message_count: 4,
          last_message_preview: null,
        },
      ],
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('does not render when closed', () => {
    renderWithI18n(
      <SessionHistory
        open={false}
        onClose={() => {}}
        onResume={() => {}}
        onBranch={() => {}}
      />,
    );
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('renders list of sessions and triggers resume', async () => {
    const onResume = vi.fn();
    renderWithI18n(
      <SessionHistory
        open={true}
        onClose={() => {}}
        onResume={onResume}
        onBranch={() => {}}
      />,
    );
    await waitFor(() =>
      expect(screen.getByText(/Free will in Chrysippus/)).toBeInTheDocument(),
    );
    fireEvent.click(
      screen.getByRole('button', { name: /Resume|Reprendre/i }),
    );
    expect(onResume).toHaveBeenCalled();
  });
});

// ---------- AgentTrace ----------

describe('AgentTrace', () => {
  beforeEach(() => {
    vi.spyOn(doctoralApi, 'getAudit').mockResolvedValue({
      trace_id: 'tr-1',
      query: 'What did Chrysippus say?',
      started_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
      total_duration_ms: 12_345,
      total_tokens: 4242,
      invocations: [
        {
          agent_id: 'a1',
          parent_agent_id: null,
          agent_name: 'Orchestrator',
          started_at: new Date().toISOString(),
          duration_ms: 500,
          tokens_used: 100,
          status: 'complete',
          tool_calls: [
            {
              tool_call_id: 'tc1',
              tool: 'search_nodes',
              args: { q: 'Chrysippus' },
              result_summary: '4 hits',
              duration_ms: 120,
            },
          ],
        },
        {
          agent_id: 'a2',
          parent_agent_id: 'a1',
          agent_name: 'SourceFinder',
          started_at: new Date().toISOString(),
          status: 'complete',
          tool_calls: [],
        },
      ],
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('does not render when closed', () => {
    renderWithI18n(
      <AgentTrace traceId="tr-1" open={false} onClose={() => {}} />,
    );
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('renders the agent tree from invocations', async () => {
    renderWithI18n(
      <AgentTrace traceId="tr-1" open={true} onClose={() => {}} />,
    );
    await waitFor(() =>
      expect(screen.getByText('Orchestrator')).toBeInTheDocument(),
    );
    expect(screen.getByText('SourceFinder')).toBeInTheDocument();
    expect(screen.getByText('search_nodes')).toBeInTheDocument();
  });
});
