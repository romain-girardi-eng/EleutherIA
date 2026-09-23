import type { AtlasNodeMeta } from './AtlasHelpers';

/**
 * Accent-, case- and breathing-insensitive search over the graph labels.
 *
 * The index is built once per node array (cached in a WeakMap, so every
 * search bar on the page shares it) and each query is a single linear scan
 * with a bounded top-k insertion: no per-keystroke allocation of 23k
 * intermediate objects, no full sort.
 */

const SPECIAL_FOLDS: Readonly<Record<string, string>> = {
  ς: 'σ',
  æ: 'ae',
  œ: 'oe',
  ß: 'ss',
  ø: 'o',
  đ: 'd',
  ł: 'l',
};

const MARKS = /\p{M}/gu;
const SEPARATORS = /[\s\p{P}\p{S}]+/gu;

function foldSpecials(value: string): string {
  let out = '';
  for (const char of value) out += SPECIAL_FOLDS[char] ?? char;
  return out;
}

/** Lowercases, strips diacritics (Greek accents and breathings, iota
 * subscripts, Latin macrons) and collapses punctuation to single spaces. */
export function foldText(value: string): string {
  return foldSpecials(value.toLowerCase().normalize('NFD').replace(MARKS, ''))
    .replace(SEPARATORS, ' ')
    .trim();
}

function foldChar(char: string): string {
  const base = foldSpecials(char.toLowerCase().normalize('NFD').replace(MARKS, ''));
  return base.replace(SEPARATORS, ' ');
}

/** Returns the `[start, end)` range of the first match of `query` inside
 * `label`, expressed in the ORIGINAL string's UTF-16 offsets. */
export function matchRange(label: string, query: string): readonly [number, number] | null {
  const needle = foldText(query);
  if (!needle) return null;
  let folded = '';
  const origin: number[] = [];
  let offset = 0;
  for (const char of label) {
    const piece = foldChar(char);
    for (let i = 0; i < piece.length; i += 1) origin.push(offset);
    folded += piece;
    offset += char.length;
  }
  const words = needle.split(' ');
  // Prefer a word-initial hit of the whole query, then of its first token.
  const candidates = [needle, words[0]];
  for (const candidate of candidates) {
    if (!candidate) continue;
    let at = -1;
    let from = 0;
    while (from <= folded.length) {
      const found = folded.indexOf(candidate, from);
      if (found < 0) break;
      if (found === 0 || folded[found - 1] === ' ') {
        at = found;
        break;
      }
      if (at < 0) at = found;
      from = found + 1;
    }
    if (at >= 0) {
      const endIndex = at + candidate.length - 1;
      const start = origin[at] ?? 0;
      const lastOrigin = origin[endIndex] ?? start;
      const lastChar = label.codePointAt(lastOrigin);
      const end = lastOrigin + (lastChar !== undefined && lastChar > 0xffff ? 2 : 1);
      return [start, end];
    }
  }
  return null;
}

/** Display group of a node: modern persons are scholars. */
export function searchGroupOf(node: Pick<AtlasNodeMeta, 'typeKey' | 'layer'>): string {
  return node.layer === 'modern' && node.typeKey === 'person' ? 'scholar' : node.typeKey;
}

const GROUP_BOOST: Readonly<Record<string, number>> = {
  concept: 70,
  person: 64,
  scholar: 56,
  school: 60,
  debate: 52,
  controversy: 52,
  work: 48,
  publication: 26,
  argument: 18,
  synthesis: 12,
  passage: 0,
};

interface IndexEntry {
  readonly node: AtlasNodeMeta;
  readonly group: string;
  readonly label: string;
  readonly words: ReadonlyArray<string>;
  readonly alt: string;
  readonly altWords: ReadonlyArray<string>;
  readonly prior: number;
}

export interface SearchIndex {
  readonly entries: ReadonlyArray<IndexEntry>;
  /** Entries sorted by prior (importance + type), used for empty queries. */
  readonly byPrior: ReadonlyArray<IndexEntry>;
}

const cache = new WeakMap<ReadonlyArray<AtlasNodeMeta>, SearchIndex>();

export function getSearchIndex(nodes: ReadonlyArray<AtlasNodeMeta>): SearchIndex {
  const cached = cache.get(nodes);
  if (cached) return cached;
  const entries: IndexEntry[] = nodes.map((node) => {
    const label = foldText(node.label);
    const alt = foldText([node.greekTerm, node.latinTerm].filter(Boolean).join(' '));
    const group = searchGroupOf(node);
    return {
      node,
      group,
      label,
      words: label ? label.split(' ') : [],
      alt,
      altWords: alt ? alt.split(' ') : [],
      prior: Math.log1p(Math.max(0, node.degree)) * 18 + (GROUP_BOOST[group] ?? 10),
    };
  });
  const byPrior = [...entries].sort((a, b) => b.prior - a.prior);
  const index = { entries, byPrior };
  cache.set(nodes, index);
  return index;
}

function someStartsWith(words: ReadonlyArray<string>, prefix: string): boolean {
  for (const word of words) if (word.startsWith(prefix)) return true;
  return false;
}

function textScore(
  text: string,
  words: ReadonlyArray<string>,
  query: string,
  tokens: ReadonlyArray<string>,
): number {
  if (!text) return 0;
  if (text === query) return 1000;
  if (text.startsWith(query)) return 700;
  if (someStartsWith(words, query)) return 520;
  if (tokens.length > 1 && tokens.every((token) => someStartsWith(words, token))) return 430;
  // Substring matches only once the query is specific enough to mean it.
  if (query.length >= 3 && text.includes(query)) return 240;
  return 0;
}

export interface SearchHit {
  readonly node: AtlasNodeMeta;
  readonly group: string;
  readonly score: number;
}

export interface SearchOutcome {
  readonly hits: ReadonlyArray<SearchHit>;
  /** Number of matches per group, before the result cap. */
  readonly groupTotals: ReadonlyMap<string, number>;
  readonly total: number;
}

export function searchNodes(
  index: SearchIndex,
  rawQuery: string,
  { limit, group }: { limit: number; group?: string | null },
): SearchOutcome {
  const query = foldText(rawQuery);
  const groupTotals = new Map<string, number>();

  if (!query) {
    const hits: SearchHit[] = [];
    for (const entry of index.byPrior) {
      groupTotals.set(entry.group, (groupTotals.get(entry.group) ?? 0) + 1);
      if (hits.length < limit && (!group || entry.group === group)) {
        hits.push({ node: entry.node, group: entry.group, score: entry.prior });
      }
    }
    return { hits, groupTotals, total: index.entries.length };
  }

  const tokens = query.split(' ');
  const top: SearchHit[] = [];
  let total = 0;
  for (const entry of index.entries) {
    const base = Math.max(
      textScore(entry.label, entry.words, query, tokens),
      Math.round(textScore(entry.alt, entry.altWords, query, tokens) * 0.9),
    );
    if (base === 0) continue;
    total += 1;
    groupTotals.set(entry.group, (groupTotals.get(entry.group) ?? 0) + 1);
    if (group && entry.group !== group) continue;
    // A shorter label is a tighter match: small tie-breaker.
    const score = base + entry.prior - Math.min(entry.label.length, 120) * 0.15;
    if (top.length === limit && score <= top[top.length - 1].score) continue;
    let at = top.length;
    while (at > 0 && top[at - 1].score < score) at -= 1;
    top.splice(at, 0, { node: entry.node, group: entry.group, score });
    if (top.length > limit) top.pop();
  }
  return { hits: top, groupTotals, total };
}

/** Orders hits into contiguous groups, the group of the best hit first. */
export function groupHits(
  hits: ReadonlyArray<SearchHit>,
): ReadonlyArray<{ group: string; hits: ReadonlyArray<SearchHit> }> {
  const groups = new Map<string, SearchHit[]>();
  for (const hit of hits) {
    const bucket = groups.get(hit.group);
    if (bucket) bucket.push(hit);
    else groups.set(hit.group, [hit]);
  }
  return [...groups.entries()].map(([group, bucket]) => ({ group, hits: bucket }));
}
