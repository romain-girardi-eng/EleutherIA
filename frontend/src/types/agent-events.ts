/**
 * agent-events.ts — SSE event protocol for streaming agentic research.
 *
 * This file is the authoritative contract between the streaming research UI
 * and any backend that drives it (Python ReAct agent, future opencode-based
 * orchestrator, or the dev-only mock SSE server in `frontend/scripts/`).
 *
 * Wire format:
 *   - Endpoint: POST /api/graphrag/query/stream
 *   - Each line begins with `data: ` followed by a JSON-encoded AgentEvent.
 *   - Events arrive in roughly chronological order. The UI tolerates jitter
 *     but expects `final_answer` (or `error`) to terminate the stream.
 *
 * Cancellation:
 *   - The client may POST /api/graphrag/query/{trace_id}/cancel to signal the
 *     backend to halt. The fetch is also aborted client-side via AbortSignal.
 *
 * Adding a new event type:
 *   1. Add a discriminated union member here.
 *   2. Handle it in `useResearchStream.ts` reducer.
 *   3. Render it in `AgentTimeline.tsx` (or a dedicated component).
 *   4. Add a fixture in `frontend/scripts/mock-sse-server.mjs`.
 */

/** A sub-agent's lifecycle phase within a research session. */
export type SubagentStatus = 'started' | 'thinking' | 'complete' | 'failed';

/** Coarse phase of the overall research session, derived from event flow. */
export type SessionStatus =
  | 'idle'
  | 'connecting'
  | 'streaming'
  | 'synthesizing'
  | 'complete'
  | 'cancelled'
  | 'error';

/** Tool-call arguments are deliberately untyped at the boundary — each tool
 *  defines its own arg shape. The UI displays them as pretty-printed JSON. */
export type ToolArgs = Record<string, unknown>;

export interface AgentStartEvent {
  type: 'agent_start';
  agent: string;
  query: string;
  /** Server-assigned trace identifier; used for cancellation + linking. */
  trace_id?: string;
}

export interface AgentStepEvent {
  type: 'agent_step';
  agent: string;
  subagent: string;
  status: SubagentStatus;
  message?: string;
}

export interface ToolCallEvent {
  type: 'tool_call';
  agent: string;
  tool: string;
  args: ToolArgs;
  /** Client-stable identifier so a `tool_result` can be paired with its call. */
  id: string;
}

export interface ToolResultEvent {
  type: 'tool_result';
  tool_call_id: string;
  result_summary: string;
  nodes_touched?: string[];
  passages_touched?: string[];
  /** Optional: latency in milliseconds reported by the backend. */
  duration_ms?: number;
}

export interface CitationFoundEvent {
  type: 'citation_found';
  passage_id: string;
  cts_urn?: string;
  work_label?: string;
  excerpt: string;
  /** KG nodes this citation supports — used to highlight the live graph. */
  node_ids: string[];
  /** Range [0.0, 1.0]; the UI gates display style on this value. */
  confidence: number;
}

export interface KGNodeActivatedEvent {
  type: 'kg_node_activated';
  node_id: string;
  label: string;
  node_type: string;
  period?: string;
}

export interface TokenEvent {
  type: 'token';
  delta: string;
}

export interface CitationVerifiedEvent {
  type: 'citation_verified';
  passage_id: string;
  verified: boolean;
  reason?: string;
}

export interface FinalAnswerCitation {
  passage_id: string;
  claim: string;
  verified: boolean;
}

export interface FinalAnswerEvent {
  type: 'final_answer';
  answer: string;
  citations: FinalAnswerCitation[];
  trace_id: string;
}

export interface ErrorEvent {
  type: 'error';
  agent: string;
  message: string;
}

/** Emitted by the Counter-Evidence Hunter as each opposing testimony is
 *  discovered. The synthesizer's v2 pass uses these findings to steel-man
 *  the answer; the UI streams them live so users see the adversarial loop. */
/** v2 dimensions of disagreement surfaced by the Counter-Evidence Hunter.
 *
 *  - contradiction / qualification / alternative — passage-level opposition (v1)
 *  - scholar_critique           — modern scholar engages_with(critiques|opposes)
 *  - period_shift               — later school reacts to an ancient claim
 *  - doxographical_alternative  — rival modern reconstruction of one fragment
 *  - consensus_dispute          — unresolved scholarly methodological dispute
 */
export type CounterEvidenceTestimonyType =
  | 'contradiction'
  | 'qualification'
  | 'alternative'
  | 'scholar_critique'
  | 'period_shift'
  | 'doxographical_alternative'
  | 'consensus_dispute';

export interface CounterEvidenceFoundEvent {
  type: 'counter_evidence_found';
  claim_id: string;
  testimony_type: CounterEvidenceTestimonyType;
  source: string;
  excerpt: string;
  force: 'strong' | 'moderate' | 'weak';
}

/** Emitted once after the Counter-Evidence Hunter finishes — lets the UI
 *  close out the adversarial-loop indicator and surface the aggregate. */
export interface CounterEvidenceCompleteEvent {
  type: 'counter_evidence_complete';
  total_testimonia: number;
  aggregate_summary: string;
}

/** Emitted by the Methodology agent as each issue is detected on the
 *  citation-verified draft (anachronism, source criticism, scholarly
 *  consensus drift, period/school misattribution). */
export interface MethodologyFlaggedEvent {
  type: 'methodology_flagged';
  flag_type:
    | 'anachronism'
    | 'source_criticism'
    | 'scholarly_consensus'
    | 'period_appropriateness';
  severity: 'blocker' | 'major' | 'minor';
  issue: string;
  suggested_revision: string;
  /** Identifier of the offending claim, or — when no claim_id is available —
   *  a short verbatim excerpt of the flagged sentence. Lets the UI anchor
   *  the flag to a specific location in the draft. */
  claim_id_or_excerpt: string;
}

/** Emitted once the Methodology agent has cleared all blockers — gates the
 *  handoff to the Polishing agent. */
export interface MethodologyApprovedEvent {
  type: 'methodology_approved';
}

/** Emitted after the Polishing agent has rewritten the draft into doctoral
 *  chapter form. `sections_modified` counts the structural changes the
 *  polisher made (added or restructured sections). */
export interface PolishingPassCompleteEvent {
  type: 'polishing_pass_complete';
  sections_modified: number;
}

/** Emitted when an agent (orchestrator or sub-agent) begins executing.
 *  ``parent_agent_id`` lets the UI reconstruct the agent tree for the
 *  AgentTrace view. ``subagent_index`` is the zero-based child slot when
 *  multiple siblings exist (so order is preserved across reconnects). */
export interface AgentInvocationEvent {
  type: 'agent_invocation';
  agent_id: string;
  parent_agent_id: string | null;
  started_at: string;
  subagent_index: number;
}

/** Emitted when a sub-agent finishes. Pairs with the matching
 *  ``agent_invocation`` via ``agent_id``. */
export interface SubagentCompleteEvent {
  type: 'subagent_complete';
  agent_id: string;
  completed_at: string;
  success: boolean;
  tools_called: number;
  tokens_used: number | null;
}

/** Emitted at the end of each pipeline stage (classify / retrieve /
 *  agent_loop / synthesis / verify / polish). Carries per-stage latency
 *  so the AgentTrace pane can render a stacked latency bar. Added in
 *  Wave 7 (2026-05-15) to make the ~14min deep-mode cost visible. */
export interface StageCompleteEvent {
  type: 'stage_complete';
  stage:
    | 'classify'
    | 'retrieve'
    | 'agent_loop'
    | 'synthesis'
    | 'verify'
    | 'polish';
  duration_ms: number;
  metadata?: Record<string, unknown>;
}

export type AgentEvent =
  | AgentStartEvent
  | AgentStepEvent
  | ToolCallEvent
  | ToolResultEvent
  | CitationFoundEvent
  | KGNodeActivatedEvent
  | TokenEvent
  | CitationVerifiedEvent
  | CounterEvidenceFoundEvent
  | CounterEvidenceCompleteEvent
  | MethodologyFlaggedEvent
  | MethodologyApprovedEvent
  | PolishingPassCompleteEvent
  | AgentInvocationEvent
  | SubagentCompleteEvent
  | StageCompleteEvent
  | FinalAnswerEvent
  | ErrorEvent;

/** Narrow `unknown` to AgentEvent. Used by the SSE reader; defensive against
 *  malformed lines from an upstream pipeline we don't control. */
export function isAgentEvent(value: unknown): value is AgentEvent {
  if (!value || typeof value !== 'object') return false;
  const candidate = value as { type?: unknown };
  if (typeof candidate.type !== 'string') return false;
  return [
    'agent_start',
    'agent_step',
    'tool_call',
    'tool_result',
    'citation_found',
    'kg_node_activated',
    'token',
    'citation_verified',
    'counter_evidence_found',
    'counter_evidence_complete',
    'methodology_flagged',
    'methodology_approved',
    'polishing_pass_complete',
    'agent_invocation',
    'subagent_complete',
    'stage_complete',
    'final_answer',
    'error',
  ].includes(candidate.type);
}
