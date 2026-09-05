/** Public response/cache projection. Mirror eleutheria_graphrag.public_payload.
 * Applied on receive AND restore so older servers/snapshots cannot retain drafts.
 */
const PRIVATE_KEYS = new Set([
  'debug_trace', 'raw_excerpt', 'raw_output', 'raw_response', 'answer_excerpt', 'reasoning_excerpt',
  'raw_answer', 'draft_answer', 'provisionalAnswer', 'provisional_answer',
  'synthesis_reasoning', 'thinking_process', 'thinking', 'full_prompt',
]);

export function publicGraphRagPayload<T>(value: T, diagnostic = false): T {
  if (Array.isArray(value)) return value.map(item => publicGraphRagPayload(item, diagnostic)) as T;
  if (value && typeof value === 'object' && !(value instanceof Date)) {
    return Object.fromEntries(
      Object.entries(value)
        .filter(([key]) => !PRIVATE_KEYS.has(key) && !(diagnostic && ['claim', 'sentence', 'clause', 'reasoning', 'text'].includes(key)))
        .map(([key, item]) => {
          if (key === 'research_graph' && item && typeof item === 'object') item = { ...item, claims: [] };
          if (key === 'claim_ledger' && Array.isArray(item)) item = item.filter(claim => !['insufficient', 'unverified'].includes(claim?.status));
          return [key, publicGraphRagPayload(item, diagnostic || ['citation_verifier_v2', 'text_verification'].includes(key))];
        }),
    ) as T;
  }
  return value;
}
