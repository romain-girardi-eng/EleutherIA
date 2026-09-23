import type { KGNode } from '../../types';

export interface RelatedNode {
  id: string;
  label: string;
  type: string;
  relation: string;
  direction: 'incoming' | 'outgoing';
}

export interface RelationGroup {
  key: string;
  relation: string;
  direction: 'incoming' | 'outgoing';
  items: RelatedNode[];
}

const TYPE_COLORS: Record<string, string> = {
  person: '#1d4e89',
  work: '#a16207',
  concept: '#c2410c',
  argument: '#9f1239',
  debate: '#7c2d12',
  school: '#3f6212',
  quote: '#b45309',
  passage: '#0369a1',
  publication: '#0f766e',
  event: '#9f1239',
  group: '#57534e',
  controversy: '#b91c1c',
  reformulation: '#4d7c0f',
  synthesis: '#0f766e',
  position: '#7c2d12',
};

export function typeColor(type: string): string {
  return TYPE_COLORS[type] ?? '#57534e';
}

export function humanize(value: string): string {
  const spaced = value.replace(/[_-]+/g, ' ').trim();
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

/** Groups relations by predicate and direction, largest group first. */
export function groupRelations(relationships: ReadonlyArray<RelatedNode>): RelationGroup[] {
  const groups = new Map<string, RelationGroup>();
  const seen = new Set<string>();
  relationships.forEach((rel) => {
    const key = `${rel.direction}:${rel.relation}`;
    const dedupeKey = `${key}:${rel.id}`;
    if (seen.has(dedupeKey)) return;
    seen.add(dedupeKey);
    const group = groups.get(key);
    if (group) {
      group.items.push(rel);
    } else {
      groups.set(key, { key, relation: rel.relation, direction: rel.direction, items: [rel] });
    }
  });
  return [...groups.values()].sort(
    (a, b) => b.items.length - a.items.length || a.relation.localeCompare(b.relation),
  );
}

export type TextLanguage = 'grc' | 'la' | undefined;

const GREEK_CHAR = /[Ͱ-Ͽἀ-῿]/g;

/** Language of a passage body, from metadata first, then from the script itself. */
export function detectTextLanguage(node: KGNode): TextLanguage {
  const metadata = node.metadata ?? {};
  const declared = String(metadata.language ?? '').toLowerCase();
  if (declared === 'grc' || declared === 'el') return 'grc';
  if (declared === 'lat' || declared === 'la') return 'la';
  const urn = typeof metadata.cts_urn === 'string' ? metadata.cts_urn : '';
  if (urn.includes(':greekLit:')) return 'grc';
  if (urn.includes(':latinLit:')) return 'la';
  const sample = (node.description ?? '').slice(0, 400);
  const greek = sample.match(GREEK_CHAR)?.length ?? 0;
  return sample.length > 0 && greek / sample.length > 0.3 ? 'grc' : undefined;
}

/** Passage and quote bodies are primary text: they must never go through Markdown. */
export function isPrimaryTextBody(node: KGNode): boolean {
  return node.type === 'passage' && detectTextLanguage(node) !== undefined;
}

const DEBT_KEYS = [
  'needs_page_verification',
  'needs_reference_remapping',
  'source_identity_unresolved',
  'needs_reocr',
  'needs_locus_mapping',
  'needs_text_ingestion',
] as const;

const FALSY_STRINGS = new Set(['', 'false', '0', 'no', 'off', 'none', 'null']);

export function isAncientLocus(node: KGNode): boolean {
  const metadata = node.metadata ?? {};
  return ['passage', 'quote'].includes(node.type)
    && ['grc', 'lat', 'el', 'la'].includes(String(metadata.language ?? '').toLowerCase())
    && Boolean(metadata.canonical_ref || (typeof metadata.cts_urn === 'string' && metadata.cts_urn.split(':').length === 5))
    && Boolean(metadata.work_title || metadata.work_canonical_id || metadata.cts_urn);
}

export function sourceDebts(node: KGNode): unknown[] {
  const metadata = node.metadata ?? {};
  const ancientLocus = isAncientLocus(node);
  return DEBT_KEYS
    .filter((key) => key !== 'needs_page_verification' || !ancientLocus)
    .map((key) => metadata[key])
    .filter((value) => (typeof value === 'string'
      ? !FALSY_STRINGS.has(value.trim().toLowerCase())
      : value === true || value === 1));
}

export type RecordStatus =
  | { kind: 'flagged' }
  | { kind: 'verified' }
  | { kind: 'corrected' }
  | { kind: 'pending' }
  | { kind: 'raw'; value: string }
  | null;

export function recordStatus(node: KGNode, debts: ReadonlyArray<unknown>): RecordStatus {
  if (debts.length > 0) return { kind: 'flagged' };
  const metadata = node.metadata ?? {};
  const verdict = typeof metadata.citation_verdict === 'string' ? metadata.citation_verdict.toLowerCase() : '';
  const provenance = typeof metadata.provenance_status === 'string' ? metadata.provenance_status.toLowerCase() : '';
  if (/pending|unsupported|unverified/.test(provenance)) return { kind: 'pending' };
  if (verdict.includes('corrected')) return { kind: 'corrected' };
  if (metadata.citation_verified === true || /verified|approved|pass/.test(verdict)) return { kind: 'verified' };
  const raw = [node.scholarly_role, metadata.citability].find(
    (value): value is string => typeof value === 'string' && value.trim().length > 0,
  );
  return raw ? { kind: 'raw', value: humanize(raw) } : null;
}

export function displayMetadataValue(value: unknown, yes: string, no: string): string | null {
  if (typeof value === 'string' && value.trim()) return value;
  if (typeof value === 'number' && Number.isFinite(value)) return String(value);
  if (typeof value === 'boolean') return value ? yes : no;
  return null;
}

type ScholarshipItem = string | { author?: string; year?: number; title?: string; publication?: string; citation?: string; text?: string };

export function formatScholarshipItem(source: ScholarshipItem): string {
  if (typeof source === 'string') return source;
  if (source.citation) return source.citation;
  if (source.text) return source.text;
  return [
    source.author,
    source.year ? `(${source.year})` : undefined,
    source.title,
    source.publication,
  ].filter(Boolean).join('. ');
}

export function modernScholarshipOf(node: KGNode): string[] {
  const raw: unknown = Array.isArray(node.modern_scholarship)
    ? node.modern_scholarship
    : node.metadata?.modern_scholarship;
  if (typeof raw === 'string') return raw.trim() ? [raw] : [];
  if (!Array.isArray(raw)) return [];
  return raw
    .filter((item): item is ScholarshipItem => typeof item === 'string' || (typeof item === 'object' && item !== null))
    .map(formatScholarshipItem)
    .filter((text) => text.trim().length > 0);
}
