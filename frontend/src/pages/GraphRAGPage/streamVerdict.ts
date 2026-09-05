import type { GraphRAGResponse, PassageCitation } from '../../types';
import type { ClaimLedgerEntry, GraphRAGMetadata } from '../../types/graphrag';
import { publicGraphRagPayload } from '../../utils/publicGraphRagPayload';

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/** Translate the agent verdict to the same response shape as terminal/cache data. */
export function responseFromVerdict(
  value: unknown, query: string, nodes: number,
): GraphRAGResponse | null {
  if (!isRecord(value)) return null;
  const gate = isRecord(value.publication_gate) ? value.publication_gate : {};
  const withheld = value.withheld === true || gate.publishable === false;
  const answer = typeof value.answer === 'string' ? value.answer : '';
  if (!withheld && (!answer.trim() || value.withheld !== false)) return null;
  const citations = Array.isArray(value.citations)
    ? value.citations.filter(isRecord) as unknown as PassageCitation[] : [];
  return publicGraphRagPayload({
    query,
    answer: withheld ? '' : answer,
    citations: {
      ancient_sources: withheld ? [] : citations.filter(c => c.layer !== 'secondary').map(c => c.label).filter((s): s is string => typeof s === 'string' && !!s.trim()),
      modern_scholarship: withheld ? [] : citations.filter(c => c.layer === 'secondary').map(c => c.label).filter((s): s is string => typeof s === 'string' && !!s.trim()),
    },
    passage_citations: withheld ? [] : citations,
    claim_ledger: withheld ? [] : (Array.isArray(value.claim_ledger) ? value.claim_ledger : []) as ClaimLedgerEntry[],
    metadata: {
      quality_badge: value.quality_badge,
      publication_gate: Object.keys(gate).length ? (withheld
        ? { ...gate, publishable: false, status: 'blocked' } : gate) : {
        publishable: !withheld,
        status: withheld ? 'blocked' : value.status ?? 'passed',
        reasons: Array.isArray(value.reasons) ? value.reasons : [],
        withholding: isRecord(value.withholding) ? value.withholding : {},
      },
    } as GraphRAGMetadata,
    sources: [],
    reasoning_path: { starting_nodes: [], expanded_nodes: [], traversed_edges: [], total_nodes: nodes, total_edges: 0 },
    nodes_used: nodes,
    edges_traversed: 0,
    degraded: false,
    success: !withheld,
  });
}

/** The verdict owns publication; a terminal can enrich graph/trace data.
 * In particular trace-only/empty defaults cannot erase verified provenance.
 * A blocking gate from either boundary always wins, including stored answer text.
 */
export function settleResponse(
  verdict: GraphRAGResponse | null, terminal: GraphRAGResponse | null,
): GraphRAGResponse | null {
  if (!verdict && !terminal) return null;
  const merged = publicGraphRagPayload({
    ...verdict,
    ...terminal,
    ...(verdict ? {
      answer: verdict.answer,
      citations: verdict.passage_citations?.length ? verdict.citations : terminal?.citations ?? verdict.citations,
      passage_citations: verdict.passage_citations?.length ? verdict.passage_citations : terminal?.passage_citations ?? verdict.passage_citations,
      claim_ledger: verdict.claim_ledger?.length ? verdict.claim_ledger : terminal?.claim_ledger ?? verdict.claim_ledger,
      degraded: false,
    } : {}),
    metadata: {
      ...terminal?.metadata,
      ...Object.fromEntries(Object.entries(verdict?.metadata ?? {}).filter(([, value]) => value !== undefined)),
    },
  } as GraphRAGResponse);
  const verdictGate = verdict?.metadata?.publication_gate;
  const terminalGate = terminal?.metadata?.publication_gate;
  const blocked = [verdictGate, terminalGate].find(g => isRecord(g) && g.publishable === false);
  if (blocked) {
    merged.answer = '';
    merged.citations = { ancient_sources: [], modern_scholarship: [] };
    merged.passage_citations = [];
    merged.claim_ledger = [];
    merged.success = false;
    merged.metadata = { ...merged.metadata, quality_badge: 'Blocked', publication_gate: blocked };
  }
  return merged;
}
