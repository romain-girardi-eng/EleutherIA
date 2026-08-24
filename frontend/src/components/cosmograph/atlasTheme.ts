/**
 * Runtime colour contract for the light-dominant intellectual Atlas.
 *
 * Keep GPU colours and DOM chrome on one small palette. Decoration may be
 * removed by adaptive quality, so the core ink, node, focus, and edge signals
 * must remain intelligible without glow, bloom, or animation.
 */
export const ATLAS_THEME = {
  surface: '#f7f2e9',
  panel: '#fffdf9',
  ink: '#292524',
  mutedInk: '#57534e',
  focus: '#0f766e',
  hover: '#c2410c',
  nodes: {
    person: '#9a5b3d',
    scholar: '#0f766e',
    concept: '#2563eb',
    argument: '#7c3aed',
    work: '#a16207',
    school: '#c2410c',
    passage: '#6b5b3e',
    debate: '#9333ea',
    fallback: '#64748b',
  },
} as const;
