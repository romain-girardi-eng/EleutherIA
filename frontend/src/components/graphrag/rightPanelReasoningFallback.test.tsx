/**
 * Reasoning tab fallback — the rung with no chain-of-thought.
 *
 * The Claude rung exposes no CoT by design, so the Reasoning tab used to sit
 * empty for a whole run. It now falls back to the pipeline's OWN research
 * journal — and must say so: the two are never passed off as one another.
 */

import { describe, it, expect, beforeAll, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { I18nextProvider } from 'react-i18next';
import i18n from '../../i18n/config';
import RightPanel from './RightPanel';
import type { AgentStep } from '../../types/graphrag';

vi.mock('./ResearchGraphPanel', () => ({ default: () => null }));
vi.mock('./TraversalDAG', () => ({ default: () => null }));

beforeAll(async () => {
  await i18n.changeLanguage('en');
});

const JOURNAL = '— Searched "autexousion" — no evidence came back.';
const COT = 'Weighing Bobzien against Frede before committing.';

const journalStep: AgentStep = {
  id: 'j1',
  type: 'research_journal',
  reasoning: JOURNAL,
  timestamp: 0,
};

const cotStep: AgentStep = {
  id: 'r1',
  type: 'synthesis_reasoning',
  reasoning: COT,
  timestamp: 0,
};

const renderPanel = (agentSteps: AgentStep[]) =>
  render(
    <I18nextProvider i18n={i18n}>
      <MemoryRouter>
        <RightPanel
          state="reasoning"
          response={null}
          activeSourceIndex={null}
          agentSteps={agentSteps}
          streamEnded
          onNodeClick={() => {}}
          onCloseDetail={() => {}}
        />
      </MemoryRouter>
    </I18nextProvider>,
  );

// `AnimatePresence mode="wait"` unmounts the outgoing tab before mounting the
// incoming one, so the switch is not synchronous even in jsdom.
const openReasoningTab = () =>
  fireEvent.click(screen.getByRole('button', { name: /Reasoning/i }));

describe('RightPanel — Reasoning tab content', () => {
  it('falls back to the research journal when the model streamed no CoT', async () => {
    renderPanel([journalStep]);
    openReasoningTab();

    expect(await screen.findByText(new RegExp('Searched'))).toBeInTheDocument();
    expect(screen.getByText('Research journal')).toBeInTheDocument();
    expect(
      screen.getByText(/not the model's chain-of-thought/i),
    ).toBeInTheDocument();
  });

  it('prefers the model chain-of-thought whenever it exists', async () => {
    renderPanel([journalStep, cotStep]);
    openReasoningTab();

    expect(await screen.findByText(new RegExp(COT))).toBeInTheDocument();
    expect(screen.queryByText(new RegExp('Searched'))).not.toBeInTheDocument();
    expect(screen.getByText('Model reasoning')).toBeInTheDocument();
    expect(screen.queryByText('Research journal')).not.toBeInTheDocument();
  });

  it('stays on Activity when only a journal note has arrived', () => {
    // A dropped lead lands mid-retrieval; its home is the timeline, so it must
    // not yank the user out of the phase view the way live CoT does.
    renderPanel([journalStep]);

    expect(screen.queryByText('Research journal')).not.toBeInTheDocument();
  });
});
