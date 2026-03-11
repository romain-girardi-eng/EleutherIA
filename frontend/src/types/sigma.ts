// frontend/src/types/sigma.ts
import type { Attributes } from 'graphology-types';

/** Node attributes stored in the Graphology graph */
export interface KGNodeAttributes extends Attributes {
  label: string;
  /** Semantic node type (person, work, etc.) — NOT Sigma's renderer type */
  nodeType: string;
  x: number;
  y: number;
  size: number;
  color: string;
  period?: string;
  description?: string;
  metadata?: Record<string, unknown>;
  community?: number;
  // Aggregation
  isAggregate?: boolean;
  passageCount?: number;
  passagesExpanded?: boolean;
  // Original data for detail panel
  originalId: string;
}

/** Edge attributes stored in the Graphology graph */
export interface KGEdgeAttributes extends Attributes {
  relation: string;
  category: EdgeCategory;
  description?: string;
  color?: string;
  size?: number;
}

/** Edge categories from ontology, driving visibility */
export type EdgeCategory =
  | 'argumentative'
  | 'intellectual'
  | 'doctrinal'
  | 'semantic'
  | 'structural'
  | 'authorship'
  | 'citation'
  | 'affiliation'
  | 'textual'
  | 'debate'
  | 'hermeneutic'
  | 'temporal';

/** Categories always visible past zoom level 1 */
export const ALWAYS_VISIBLE_CATEGORIES: EdgeCategory[] = [
  'argumentative',
  'intellectual',
  'doctrinal',
  'semantic',
];

/** Categories only visible on hover/select */
export const HOVER_ONLY_CATEGORIES: EdgeCategory[] = [
  'structural',
  'authorship',
  'citation',
  'affiliation',
  'textual',
  'debate',
  'hermeneutic',
  'temporal',
];

/** Zoom levels driven by camera.ratio */
export const ZoomLevel = {
  Overview: 1,      // ratio > 1.2
  Community: 2,     // 0.4 – 1.2
  Neighborhood: 3,  // 0.08 – 0.4
  Detail: 4,        // < 0.08
} as const;
export type ZoomLevel = (typeof ZoomLevel)[keyof typeof ZoomLevel];

/** Map relation type → edge category (from kg/ontology/edge_types.json) */
export const RELATION_TO_CATEGORY: Record<string, EdgeCategory> = {
  // argumentative
  argues_for: 'argumentative',
  argues_against: 'argumentative',
  refutes: 'argumentative',
  responds_to: 'argumentative',
  supports: 'argumentative',
  critiques: 'argumentative',
  // intellectual
  influences: 'intellectual',
  influenced_by: 'intellectual',
  taught_by: 'intellectual',
  teaches: 'intellectual',
  student_of: 'intellectual',
  extends: 'intellectual',
  // affiliation
  belongs_to_school: 'affiliation',
  has_member: 'affiliation',
  member_of: 'affiliation',
  founded: 'affiliation',
  // authorship
  wrote: 'authorship',
  authored_by: 'authorship',
  created_by: 'authorship',
  developed_by: 'authorship',
  // citation
  cites: 'citation',
  cited_by: 'citation',
  source_for: 'citation',
  evidenced_by: 'citation',
  // textual
  preserves: 'textual',
  preserved_in: 'textual',
  // structural (including translation_of per ontology)
  translation_of: 'structural',
  contains: 'structural',
  part_of: 'structural',
  has_section: 'structural',
  has_chapter: 'structural',
  belongs_to_corpus: 'structural',
  // semantic
  discusses: 'semantic',
  discussed_in: 'semantic',
  defines: 'semantic',
  related_to: 'semantic',
  contrasts_with: 'semantic',
  parallel_to: 'semantic',
  employs: 'semantic',
  presupposes: 'semantic',
  grounded_in: 'semantic',
  // doctrinal
  holds_position: 'doctrinal',
  endorses: 'doctrinal',
  rejects: 'doctrinal',
  // debate
  participates_in: 'debate',
  contributes_to: 'debate',
  // hermeneutic
  interprets: 'hermeneutic',
  interpreted_by: 'hermeneutic',
  represents: 'hermeneutic',
  exemplifies: 'hermeneutic',
  specializes_in: 'hermeneutic',
  // temporal
  contemporary_of: 'temporal',
  precedes: 'temporal',
  follows: 'temporal',
};

/** Node type → base size (for Sigma rendering) */
export const TYPE_SIZES: Record<string, number> = {
  person: 11,
  school: 10,
  concept: 9,
  argument: 8,
  debate: 8,
  work: 8,
  event: 7,
  quote: 7,
  publication: 7,
  synthesis: 7,
  controversy: 7,
  reformulation: 6,
  conceptual_evolution: 6,
  group: 6,
  argument_framework: 6,
  passage: 4,
  default: 5,
};
