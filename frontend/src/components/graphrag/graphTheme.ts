export interface GraphTypeTheme {
  label: string;
  color: string;
  tint: string;
  border: string;
  text: string;
  glow: string;
}

export const GRAPH_TYPE_THEMES: Record<string, GraphTypeTheme> = {
  person: {
    label: 'Person',
    color: '#6E85E9',
    tint: '#EFF3FF',
    border: '#CDD7FF',
    text: '#3F57AF',
    glow: '#E2E9FF',
  },
  concept: {
    label: 'Concept',
    color: '#8D79DF',
    tint: '#F1EDFF',
    border: '#D9D0FF',
    text: '#5D46B2',
    glow: '#E8E1FF',
  },
  argument: {
    label: 'Argument',
    color: '#D97B61',
    tint: '#FFF1EB',
    border: '#F3CABB',
    text: '#A14F3A',
    glow: '#FFE2D8',
  },
  position: {
    label: 'Position',
    color: '#B56E4D',
    tint: '#FFF4EC',
    border: '#EDCDBA',
    text: '#86472F',
    glow: '#F9E4D6',
  },
  debate: {
    label: 'Debate',
    color: '#C7645B',
    tint: '#FFF0ED',
    border: '#F0C1BA',
    text: '#933C36',
    glow: '#FFD8D3',
  },
  school: {
    label: 'School',
    color: '#5E9B76',
    tint: '#EDF8F0',
    border: '#BCDFC8',
    text: '#2F6744',
    glow: '#DAF3E2',
  },
  work: {
    label: 'Work',
    color: '#C79A31',
    tint: '#FFF7E0',
    border: '#F0D79B',
    text: '#876114',
    glow: '#FFEAB3',
  },
  event: {
    label: 'Event',
    color: '#D08B4B',
    tint: '#FFF4E9',
    border: '#F0D1AF',
    text: '#91591F',
    glow: '#FFE5C9',
  },
  quote: {
    label: 'Quote',
    color: '#C47186',
    tint: '#FFF1F5',
    border: '#F1C8D4',
    text: '#96405B',
    glow: '#FFDDE7',
  },
  reformulation: {
    label: 'Reformulation',
    color: '#7E8ED8',
    tint: '#F0F3FF',
    border: '#D0D7F7',
    text: '#4657A2',
    glow: '#E3E8FF',
  },
  passage: {
    label: 'Passage',
    color: '#8992A6',
    tint: '#F5F6F9',
    border: '#D7DBE4',
    text: '#5C6477',
    glow: '#ECEFF5',
  },
  publication: {
    label: 'Publication',
    color: '#4C9BAA',
    tint: '#ECF9FB',
    border: '#BFE2E8',
    text: '#276B77',
    glow: '#D9F1F5',
  },
  source_collection: {
    label: 'Source Collection',
    color: '#718D92',
    tint: '#EFF6F6',
    border: '#C8DADB',
    text: '#476469',
    glow: '#E0ECEC',
  },
  synthesis: {
    label: 'Synthesis',
    color: '#599C82',
    tint: '#EDF8F4',
    border: '#BDE0D3',
    text: '#2D6952',
    glow: '#D8F1E7',
  },
  controversy: {
    label: 'Controversy',
    color: '#C16062',
    tint: '#FFF1F1',
    border: '#F0C3C4',
    text: '#913839',
    glow: '#FFD9DA',
  },
  conceptual_evolution: {
    label: 'Concept Evolution',
    color: '#7084D6',
    tint: '#F0F3FF',
    border: '#CFD7F8',
    text: '#4558A6',
    glow: '#E0E7FF',
  },
  group: {
    label: 'Group',
    color: '#6E9C4E',
    tint: '#F1F8EA',
    border: '#CDE2B5',
    text: '#4D6F30',
    glow: '#E1F1D1',
  },
  argument_framework: {
    label: 'Framework',
    color: '#A56BC4',
    tint: '#F8F0FD',
    border: '#E1CAEF',
    text: '#72418E',
    glow: '#F0DFF9',
  },
  default: {
    label: 'Node',
    color: '#8A8F98',
    tint: '#F6F5F4',
    border: '#DEDBD7',
    text: '#57534E',
    glow: '#EEEAE6',
  },
};

function toTitleCase(value: string): string {
  return value
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
    .trim();
}

export function getGraphTypeTheme(type?: string | null): GraphTypeTheme {
  const key = type?.toLowerCase() ?? 'default';
  return GRAPH_TYPE_THEMES[key] ?? {
    ...GRAPH_TYPE_THEMES.default,
    label: type ? toTitleCase(type) : GRAPH_TYPE_THEMES.default.label,
  };
}

export function formatGraphNodeType(type?: string | null): string {
  return getGraphTypeTheme(type).label;
}
