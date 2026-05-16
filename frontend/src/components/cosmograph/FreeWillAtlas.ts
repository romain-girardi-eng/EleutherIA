// Curated landing subgraph: the ~40 nodes Romain's thesis actually pivots around.
// Matching is loose — the live KG uses ID suffixes like "_3c_ce", "_280_206bce_i9j0k1l2"
// or even "scholar_..." prefixes. We therefore match by:
//   - exact id or prefix match for canonical anchor ids
//   - keyword match against id for known scholars/works

export const ATLAS_CORE_CONCEPTS_PREFIXES: ReadonlyArray<string> = [
  'concept_autexousion',
  'concept_to_eph_hemin',
  'concept_eph_hemin',
  'concept_prohairesis',
  'concept_heimarmene',
  'concept_free_will',
];

export const ATLAS_PERSON_PREFIXES: ReadonlyArray<string> = [
  'person_aristotle',
  'person_chrysippus',
  'person_alexander_aphrodisias',
  'person_alexander_of_aphrodisias',
  'person_plotinus',
  'person_justin_martyr',
  'person_origen',
  'person_augustine',
  'person_boethius',
];

export const ATLAS_SCHOOLS: ReadonlyArray<string> = [
  'school_stoics',
  'school_epicureans',
  'school_peripatetics',
  'school_middle_platonism',
  'school_neoplatonism',
];

// Scholar / modern reception IDs use multiple naming conventions in the live KG
// (person_, scholar_, person_..._contemporary, etc.). We match by id keyword.
export const ATLAS_SCHOLAR_KEYWORDS: ReadonlyArray<string> = [
  'bobzien',
  'sharples',
  'dihle',
  'karamanolis',
  'kane_robert',
  'frede_dorothea',
  'frede_michael',
];

export const ATLAS_WORK_KEYWORDS: ReadonlyArray<string> = [
  'nicomachean_ethics',
  'alexander_de_fato',
  'cicero_de_fato',
  'plotinus_enneads',
  'origen_de_principiis',
  'boethius_consolatio',
];

const PREFIX_ANCHORS: ReadonlyArray<string> = [
  ...ATLAS_CORE_CONCEPTS_PREFIXES,
  ...ATLAS_PERSON_PREFIXES,
  ...ATLAS_SCHOOLS,
];

const KEYWORD_ANCHORS_PERSON: ReadonlyArray<string> = ATLAS_SCHOLAR_KEYWORDS;
const KEYWORD_ANCHORS_WORK: ReadonlyArray<string> = ATLAS_WORK_KEYWORDS;

export function isAtlasNode(
  nodeId: string,
  nodeType: string | undefined,
): boolean {
  const lower = nodeId.toLowerCase();

  for (const anchor of PREFIX_ANCHORS) {
    const a = anchor.toLowerCase();
    if (lower === a || lower.startsWith(`${a}_`) || lower.startsWith(`${a}-`)) {
      return true;
    }
  }

  if ((nodeType === 'person' || lower.startsWith('scholar_'))
      && KEYWORD_ANCHORS_PERSON.some((kw) => lower.includes(kw))) {
    return true;
  }

  if (nodeType === 'work'
      && KEYWORD_ANCHORS_WORK.some((kw) => lower.includes(kw))) {
    return true;
  }

  return false;
}

export interface AtlasNodeRef {
  id: string;
  type?: string;
}

export function pickAtlasNodeIds(nodes: ReadonlyArray<AtlasNodeRef>): Set<string> {
  const matched = new Set<string>();
  for (const node of nodes) {
    if (isAtlasNode(node.id, node.type)) {
      matched.add(node.id);
    }
  }
  return matched;
}
