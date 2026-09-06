import { describe, expect, it } from 'vitest';
import { responseFromVerdict, settleResponse } from './streamVerdict';
import { publicGraphRagPayload } from '../../utils/publicGraphRagPayload';
import type { GraphRAGResponse } from '../../types';

const citation = { id: 'p1', ref: 'P1', type: 'passage', label: 'Source one', layer: 'primary', verified: true };
const ledger = [{ claim: 'Supported statement', status: 'supported', evidence_ids: ['p1'] }];
const gate = { publishable: true, status: 'passed', reasons: [] };
const verdict = () => responseFromVerdict({ answer: 'Supported statement [P1].', withheld: false, citations: [citation], claim_ledger: ledger, quality_badge: 'High', publication_gate: gate }, 'Question', 3)!;

describe('publication settlement', () => {
  it('preserves the full verdict when terminal enrichment contains empty default arrays', () => {
    const settled = settleResponse(verdict(), { answer: '', trace_id: 'trace-1', citations: {}, passage_citations: [], claim_ledger: [], metadata: { trace_id: 'trace-1' } } as unknown as GraphRAGResponse)!;
    expect(settled.answer).toBe('Supported statement [P1].');
    expect(settled.passage_citations).toEqual([citation]);
    expect(settled.claim_ledger).toEqual(ledger);
    expect(settled.metadata?.publication_gate).toEqual(gate);
    expect(settled.metadata?.quality_badge).toBe('High');
    expect(settled.trace_id).toBe('trace-1');
  });
  it.each(['verdict', 'terminal'])('a block in the %s erases all answer fields, including persisted text', boundary => {
    const blocked = { ...verdict(), metadata: { publication_gate: { publishable: false, reasons: ['verification_failed'] } } };
    const settled = boundary === 'verdict' ? settleResponse(blocked, verdict()) : settleResponse(verdict(), blocked);
    expect(settled?.answer).toBe('');
    expect(settled?.passage_citations).toEqual([]);
    expect(settled?.claim_ledger).toEqual([]);
    expect(settled?.metadata?.publication_gate?.publishable).toBe(false);
  });
  it('ignores malformed or empty verdicts', () => {
    for (const payload of [null, {}, { answer: 'Ungated' }, { answer: '', withheld: false }]) {
      expect(responseFromVerdict(payload, 'q', 0)).toBeNull();
    }
  });
});

it('removes private draft copies from nested browser snapshots without changing the input', () => {
  const draft = 'PRIVATE_DRAFT';
  const input = { messages: [{ graphrag_response: { ...verdict(), metadata: {
    publication_gate: gate,
    debug_trace: { dialectical: { raw_excerpt: draft } },
    scholar_synthesis_reasoning: draft,
    citation: { id: "p1", verification_note: draft },
    research_graph: { claims: [{ claim: draft, status: 'supported' }], stages: [{ details: { answer_excerpt: draft } }] },
    citation_verifier_v2: { failed_citations: [{ citation_id: 'p2', claim: draft, reasoning: draft, pairs: [{ sentence: draft, sentence_index: 2 }] }] },
    text_verification: { unverified: 1, unverified_texts: [{ text: draft, action: 'removed' }] },
  } } }] };
  const before = JSON.stringify(input);
  const sanitized = publicGraphRagPayload(input);
  expect(JSON.stringify(sanitized)).not.toContain(draft);
  expect(sanitized.messages[0].graphrag_response.metadata.publication_gate).toEqual(gate);
  expect(JSON.stringify(input)).toBe(before);
  expect(publicGraphRagPayload(sanitized)).toEqual(sanitized);
});

it('a contradictory withheld verdict still blocks publication', () => {
  const result = responseFromVerdict({ answer: 'MUST NOT PUBLISH', withheld: true, publication_gate: gate }, 'q', 0)!;
  expect(result.metadata?.publication_gate?.publishable).toBe(false);
  expect(settleResponse(result, verdict())?.answer).toBe('');
});

it('accepts terminal provenance missing from a legacy verdict', () => {
  const legacy = responseFromVerdict({ answer: 'Supported statement [P1].', withheld: false }, 'q', 0)!;
  const merged = settleResponse(legacy, verdict())!;
  expect(merged.passage_citations).toEqual([citation]);
  expect(merged.claim_ledger).toEqual(ledger);
  expect(merged.metadata?.quality_badge).toBe('High');
});
