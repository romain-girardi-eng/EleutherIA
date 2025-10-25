export const graphragTourSteps = [
  {
    target: '[data-tour="query-input"]',
    title: 'Ask Your Research Questions',
    content: 'Type any question about ancient philosophy and free will. The system uses GraphRAG to search the knowledge graph and provide scholarly answers with citations.',
    placement: 'bottom' as const
  },
  {
    target: '[data-tour="suggestions"]',
    title: 'Smart Query Suggestions',
    content: 'Browse curated example questions organized by category: philosophical, comparative, historical, and conceptual analysis. Click any suggestion to try it instantly.',
    placement: 'top' as const
  },
  {
    target: '[data-tour="reasoning-path"]',
    title: 'Visual Reasoning Path',
    content: 'Watch the AI reasoning process unfold in real-time. See how it searches nodes, traverses the graph, builds context, and synthesizes the answer.',
    placement: 'left' as const
  },
  {
    target: '[data-tour="answer-section"]',
    title: 'Scholarly Answers with Citations',
    content: 'Get comprehensive answers grounded in the knowledge graph with inline citations. Each claim is backed by ancient sources or modern scholarship.',
    placement: 'top' as const
  },
  {
    target: '[data-tour="quality-metrics"]',
    title: 'Answer Quality Metrics',
    content: 'Evaluate answer quality with transparent metrics: citation count, source diversity, node relevance, context coherence, and completeness scores.',
    placement: 'top' as const
  },
  {
    target: '[data-tour="citations"]',
    title: 'Citation Management',
    content: 'Export citations in multiple academic formats (APA, MLA, Chicago, BibTeX). Copy them directly to your research notes or bibliography.',
    placement: 'top' as const
  },
  {
    target: '[data-tour="settings"]',
    title: 'Advanced Settings',
    content: 'Fine-tune the GraphRAG pipeline: adjust semantic search depth, graph traversal distance, context window size, and streaming preferences.',
    placement: 'left' as const
  }
];
