export type WaitingPhase =
  | 'connecting'
  | 'classify'
  | 'search'
  | 'read'
  | 'synthesize'
  | 'verify'
  | 'finalize';

export function resolveWaitingPhase(
  stage?: string,
  statusMessage?: string,
): WaitingPhase {
  const value = `${stage ?? ''} ${statusMessage ?? ''}`.toLowerCase();

  if (/verif|citation.audit|citation_verifier|programmatic/.test(value)) return 'verify';
  if (/final|complete|finish|prepar/.test(value)) return 'finalize';
  if (/synth|render|claim.ledger|draft|answer|generat|polish/.test(value)) {
    return 'synthesize';
  }
  if (/read|passage|controversy|evidence|quality.gate|source/.test(value)) return 'read';
  if (/search|retriev|neighbor|subgraph|agent.loop|tool|node/.test(value)) return 'search';
  if (/classif|frame|plan|triage|complexity/.test(value)) return 'classify';
  return 'connecting';
}

export function formatWaitingElapsed(elapsedMs: number): string {
  const seconds = Math.max(0, Math.floor(elapsedMs / 1000));
  const minutes = Math.floor(seconds / 60);
  return `${String(minutes).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
}
