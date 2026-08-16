import { describe, it, expect } from 'vitest';
import {
  MAX_CONCURRENT_RUNS,
  canStartRun,
  createRun,
  initialRunsState,
  runsReducer,
  selectActiveRun,
  selectAllResponses,
  selectStreamingCount,
  type RunStatus,
  type RunsState,
} from './runs';
import type { GraphRAGResponse } from '../../types';

const open = (state: RunsState, id: string, status: RunStatus = 'streaming') =>
  runsReducer(state, {
    type: 'run/open',
    run: createRun({ id, question: `q ${id}`, model: 'm', mode: 'auto', status }),
  });

const threeRuns = () => open(open(open(initialRunsState, 'a'), 'b'), 'c');

describe('runsReducer', () => {
  it('opens a run and makes it active', () => {
    const state = open(initialRunsState, 'a');
    expect(state.order).toEqual(['a']);
    expect(state.activeRunId).toBe('a');
    expect(selectActiveRun(state)?.question).toBe('q a');
  });

  it('ignores a duplicate id', () => {
    const state = open(open(initialRunsState, 'a'), 'a');
    expect(state.order).toEqual(['a']);
  });

  it('patches one run without touching its siblings', () => {
    const state = runsReducer(threeRuns(), {
      type: 'run/patch',
      id: 'b',
      patch: { status: 'done', streamEnded: true },
    });
    expect(state.runs.b.status).toBe('done');
    expect(state.runs.a.status).toBe('streaming');
    expect(state.runs.c.status).toBe('streaming');
  });

  it('grows an accumulating step with its separator', () => {
    let state = open(initialRunsState, 'a');
    state = runsReducer(state, {
      type: 'run/appendStep',
      id: 'a',
      step: { id: 'step-1', type: 'research_journal', reasoning: 'one', timestamp: 0 },
    });
    state = runsReducer(state, {
      type: 'run/growStep',
      id: 'a',
      stepId: 'step-1',
      text: 'two',
      separator: '\n\n',
    });
    expect(state.runs.a.agentSteps[0].reasoning).toBe('one\n\ntwo');
  });

  it('replaces every assistant message with the final one', () => {
    let state = open(initialRunsState, 'a');
    const msg = (role: 'user' | 'assistant', content: string) => ({
      role,
      content,
      timestamp: new Date(),
    });
    state = runsReducer(state, { type: 'run/appendMessage', id: 'a', message: msg('user', 'q') });
    state = runsReducer(state, { type: 'run/appendMessage', id: 'a', message: msg('assistant', 'partial') });
    state = runsReducer(state, { type: 'run/replaceAssistant', id: 'a', message: msg('assistant', 'final') });
    expect(state.runs.a.messages.map((m) => m.content)).toEqual(['q', 'final']);
  });

  it('hands the active slot to the neighbour when the active run closes', () => {
    let state = threeRuns();
    state = runsReducer(state, { type: 'run/activate', id: 'b' });
    state = runsReducer(state, { type: 'run/close', id: 'b' });
    expect(state.order).toEqual(['a', 'c']);
    expect(state.activeRunId).toBe('c');

    state = runsReducer(state, { type: 'run/close', id: 'c' });
    expect(state.activeRunId).toBe('a');

    state = runsReducer(state, { type: 'run/close', id: 'a' });
    expect(state.activeRunId).toBeNull();
    expect(state.runs).toEqual({});
  });

  it('leaves the active run alone when a background run closes', () => {
    let state = threeRuns();
    state = runsReducer(state, { type: 'run/activate', id: 'c' });
    state = runsReducer(state, { type: 'run/close', id: 'a' });
    expect(state.activeRunId).toBe('c');
  });

  it('is a no-op for unknown ids', () => {
    const state = threeRuns();
    expect(runsReducer(state, { type: 'run/patch', id: 'zz', patch: { status: 'done' } })).toBe(state);
    expect(runsReducer(state, { type: 'run/close', id: 'zz' })).toBe(state);
    expect(runsReducer(state, { type: 'run/activate', id: 'zz' })).toBe(state);
  });
});

describe('run selectors', () => {
  it('counts streams and caps submissions at MAX_CONCURRENT_RUNS', () => {
    const two = open(open(initialRunsState, 'a'), 'b');
    expect(selectStreamingCount(two)).toBe(2);
    expect(canStartRun(two)).toBe(true);

    const three = open(two, 'c');
    expect(selectStreamingCount(three)).toBe(MAX_CONCURRENT_RUNS);
    expect(canStartRun(three)).toBe(false);

    // A finished run frees a slot again.
    const settled = runsReducer(three, { type: 'run/patch', id: 'a', patch: { status: 'done' } });
    expect(canStartRun(settled)).toBe(true);
  });

  it('collects responses in tab order, skipping runs with none', () => {
    let state = threeRuns();
    state = runsReducer(state, {
      type: 'run/patch',
      id: 'c',
      patch: { response: { query: 'third' } as GraphRAGResponse },
    });
    state = runsReducer(state, {
      type: 'run/patch',
      id: 'a',
      patch: { response: { query: 'first' } as GraphRAGResponse },
    });
    expect(selectAllResponses(state).map((r) => r.query)).toEqual(['first', 'third']);
  });
});
