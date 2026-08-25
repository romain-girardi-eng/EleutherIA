import type { KGNode } from '../types';

export interface FrozenCitationArchive {
  versionDoi: string;
  commit: string;
  snapshotDate: string;
  releaseId: string;
}

export function buildNodeCitation(
  node: Pick<KGNode, 'id' | 'label'>,
  releaseId: string,
  archive: FrozenCitationArchive,
  accessedAt = new Date(),
  origin = 'https://free-will.app',
): string {
  if (archive.releaseId !== releaseId) {
    throw new Error('The frozen citation archive does not match the served KG release.');
  }
  const url = new URL('/visualizer', origin);
  url.searchParams.set('node', node.id);
  url.searchParams.set('release', releaseId);
  url.searchParams.set('mode', 'atlas');
  const accessed = accessedAt.toISOString().slice(0, 10);
  return `Girardi, Romain. "${node.label}." EleutherIA: Ancient Free Will Database. Node ${node.id}. KG release ${releaseId}. Git commit ${archive.commit}. KG snapshot ${archive.snapshotDate}. Zenodo version DOI ${archive.versionDoi}. Accessed ${accessed}. ${url.toString()}`;
}

export function isNodeCitationEligible(node: Pick<KGNode, 'metadata'>): boolean {
  const metadata = node.metadata ?? {};
  const citability = typeof metadata.citability === 'string'
    ? metadata.citability.toLowerCase()
    : '';
  const verdict = typeof metadata.citation_verdict === 'string'
    ? metadata.citation_verdict.toLowerCase()
    : '';
  const unsafe = /discover|non[_ -]?citable|quarant|block|reject|fail|pending|unverified/;
  if (unsafe.test(citability) || unsafe.test(verdict) || metadata.citation_verified === false) {
    return false;
  }
  return metadata.citation_verified === true
    || /verified|corrected|approved|pass/.test(verdict)
    || /(^|[_ -])(citable|citation[_ -]?ready|public)([_ -]|$)/.test(citability);
}
