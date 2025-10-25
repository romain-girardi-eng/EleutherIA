// Mock GraphRAG data for demo/testing without authentication

export const mockGraphRAGResponse = {
  query: "How did the Stoics reconcile fate with moral responsibility?",
  answer: `The Stoics developed a sophisticated compatibilist position that reconciled their belief in universal causal determinism (heimarmenē) with moral responsibility and human agency. This reconciliation centered on several key philosophical moves:

**1. The Distinction Between Internal and External Causes**

Chrysippus, the third head of the Stoa, distinguished between "perfect and principal" (autotelēs kai prokatarktikē) causes that come from within the agent and "auxiliary and proximate" (sunektikē kai proseggizousē) causes that come from outside. While external impressions (phantasiai) trigger our actions, assent (sunkatathesis) to these impressions remains "in our power" (eph' hēmin). This preserved a sphere of human agency within the deterministic framework.

**2. The Cylinder Analogy**

Chrysippus used the famous cylinder analogy to illustrate this distinction: just as a cylinder, once pushed, rolls by its own nature, so too do humans respond to impressions according to their rational nature. The external push is necessary but not sufficient—the cylinder's shape determines how it rolls. Similarly, while fate provides the occasion for action, our character and rational assent determine how we respond.

**3. Rational Assent as the Locus of Responsibility**

The Stoics located moral responsibility in the faculty of rational assent. Since mature rational agents have the capacity to assent or withhold assent from impressions, they bear responsibility for their actions even within a deterministic universe. The wise person (sophos) develops the ability to assent only to katalēptikē phantasiai (cognitive impressions) that correctly represent reality.

**4. Fate and Providence**

The Stoics identified fate (heimarmenē) with divine providence (pronoia) and the rational structure of the cosmos (logos). This meant that determinism was not blind mechanical necessity but rather the optimal rational ordering of events. Human actions, including our rational assents, are part of this providential order while remaining genuinely ours.

**5. The Co-fated (sunēmmenon)**

Chrysippus introduced the concept of "co-fated" events—outcomes that depend on multiple causal chains, including human choices. For example, "Oedipus will be born to Laius" might be fated, but this is co-fated with Laius engaging in intercourse. This preserved a role for human action within the fated order.

This Stoic position was extensively criticized by Academic Skeptics like Carneades, who argued that it failed to preserve genuine freedom, and later by Alexander of Aphrodisias, who defended an incompatibilist Aristotelian alternative. However, it remained one of the most influential compatibilist positions in ancient philosophy and continues to inform modern debates on free will and determinism.`,

  reasoning_path: {
    query_embedding: [], // Empty for mock
    retrieved_nodes: [
      {
        id: "person_chrysippus",
        label: "Chrysippus",
        type: "person",
        description: "Third head of the Stoa (c. 279-206 BCE), developed sophisticated compatibilist theory"
      },
      {
        id: "concept_heimarmene",
        label: "Fate (heimarmenē)",
        type: "concept",
        description: "Stoic concept of universal causal determinism identified with providence and logos"
      },
      {
        id: "concept_eph_hemin",
        label: "eph' hēmin (in our power)",
        type: "concept",
        description: "Greek term for what is 'in our power' or 'up to us'"
      },
      {
        id: "concept_sunkatathesis",
        label: "Assent (sunkatathesis)",
        type: "concept",
        description: "Rational assent to impressions, the locus of Stoic moral responsibility"
      }
    ],
    graph_context: {
      nodes: [
        {
          id: "person_chrysippus",
          label: "Chrysippus",
          type: "person",
          description: "Third head of the Stoa, developed the cylinder analogy and distinction between types of causes"
        },
        {
          id: "person_carneades",
          label: "Carneades",
          type: "person",
          description: "Academic Skeptic who criticized Stoic compatibilism"
        },
        {
          id: "person_alexander_aphrodisias",
          label: "Alexander of Aphrodisias",
          type: "person",
          description: "Peripatetic philosopher who defended incompatibilist alternative"
        },
        {
          id: "concept_phantasia",
          label: "Impression (phantasia)",
          type: "concept",
          description: "Mental impressions that trigger rational assent"
        },
        {
          id: "concept_pronoia",
          label: "Providence (pronoia)",
          type: "concept",
          description: "Divine providence identified with fate by Stoics"
        },
        {
          id: "concept_logos",
          label: "Logos",
          type: "concept",
          description: "Rational structure of the cosmos"
        }
      ],
      edges: [
        {
          source: "person_chrysippus",
          target: "concept_heimarmene",
          relation: "developed"
        },
        {
          source: "person_chrysippus",
          target: "concept_sunkatathesis",
          relation: "formulated"
        },
        {
          source: "person_carneades",
          target: "person_chrysippus",
          relation: "refutes"
        },
        {
          source: "concept_heimarmene",
          target: "concept_pronoia",
          relation: "identified_with"
        }
      ]
    },
    relevant_citations: [
      "Chrysippus, On Fate (fragments)",
      "Cicero, On Fate 39-44",
      "Alexander of Aphrodisias, On Fate 13",
      "Aulus Gellius, Attic Nights 7.2.6-13",
      "Diogenes Laertius, Lives 7.149-150"
    ],
    synthesis_prompt: "Based on the retrieved context about Stoic philosophy..."
  },

  citations: [
    {
      text: "Chrysippus distinguished between perfect and principal causes versus auxiliary and proximate causes",
      source: "Cicero, On Fate 41-43",
      node_id: "person_chrysippus"
    },
    {
      text: "The cylinder analogy illustrates how external causes trigger but do not determine the nature of our response",
      source: "Cicero, On Fate 42-43; Aulus Gellius, Attic Nights 7.2.11",
      node_id: "person_chrysippus"
    },
    {
      text: "Assent (sunkatathesis) remains in our power even within a deterministic universe",
      source: "Epictetus, Discourses 1.1; SVF 2.974-975",
      node_id: "concept_sunkatathesis"
    },
    {
      text: "Stoics identified fate with providence and the rational logos governing the cosmos",
      source: "Diogenes Laertius, Lives 7.149; SVF 2.913-944",
      node_id: "concept_heimarmene"
    },
    {
      text: "Carneades criticized Stoic compatibilism as incoherent",
      source: "Cicero, On Fate 31-33; Academica 2.97",
      node_id: "person_carneades"
    },
    {
      text: "Alexander of Aphrodisias defended an incompatibilist Aristotelian alternative",
      source: "Alexander of Aphrodisias, On Fate 13-14, 26-27",
      node_id: "person_alexander_aphrodisias"
    }
  ],

  confidence_score: 0.94,

  metadata: {
    total_nodes_searched: 47,
    total_edges_traversed: 83,
    llm_model: "gemini-pro",
    processing_time_ms: 2847
  }
};

export const mockReasoningSteps = [
  {
    id: 1,
    type: 'search' as const,
    label: 'Semantic Search',
    description: 'Finding relevant nodes about Stoic philosophy and fate',
    nodes: ['Chrysippus', 'Stoics', 'Fate', 'heimarmenē'],
    duration: 342,
    status: 'complete' as const,
    metadata: {
      nodeCount: 12,
      similarity: 0.89
    }
  },
  {
    id: 2,
    type: 'traverse' as const,
    label: 'Graph Traversal',
    description: 'Expanding context through philosophical relationships',
    nodes: ['sunkatathesis', 'eph hemin', 'phantasia', 'pronoia'],
    edges: ['developed', 'formulated', 'identified_with'],
    duration: 523,
    status: 'complete' as const,
    metadata: {
      nodeCount: 8,
      edgeCount: 15
    }
  },
  {
    id: 3,
    type: 'context' as const,
    label: 'Context Assembly',
    description: 'Building comprehensive philosophical context',
    duration: 412,
    status: 'complete' as const,
    metadata: {
      contextLength: 4750
    }
  },
  {
    id: 4,
    type: 'synthesis' as const,
    label: 'Answer Synthesis',
    description: 'Generating scholarly answer with citations',
    duration: 1570,
    status: 'complete' as const,
    metadata: {
      citationCount: 6
    }
  },
  {
    id: 5,
    type: 'complete' as const,
    label: 'Complete',
    description: 'Answer ready with 6 citations and 94% confidence',
    duration: 0,
    status: 'complete' as const,
    metadata: {
      confidence: 0.94
    }
  }
];

export const mockQualityMetrics = {
  citationCount: 6,
  sourceCount: 8,
  nodeRelevanceScore: 0.89,
  contextCoherence: 0.92,
  answerCompleteness: 0.91,
  overallQuality: 91
};

export const mockArgumentMapping = {
  id: "stoic_compatibilism",
  claim: "The Stoics successfully reconcile universal determinism with moral responsibility",
  premises: [
    {
      id: "p1",
      text: "Rational assent (sunkatathesis) to impressions is 'in our power' (eph' hēmin)",
      source: "Epictetus, Discourses 1.1; SVF 2.974-975"
    },
    {
      id: "p2",
      text: "Internal causes (our rational nature) are distinct from external triggering causes",
      source: "Cicero, On Fate 41-43"
    },
    {
      id: "p3",
      text: "Fate is identical to divine providence and rational cosmic order",
      source: "Diogenes Laertius 7.149; SVF 2.913"
    }
  ],
  objections: [
    {
      id: "o1",
      text: "If everything is causally determined, assent cannot be genuinely 'up to us'",
      source: "Carneades ap. Cicero, On Fate 31-33"
    },
    {
      id: "o2",
      text: "The cylinder analogy fails because the cylinder's nature is itself determined by prior causes",
      source: "Alexander of Aphrodisias, On Fate 13"
    }
  ],
  responses: [
    {
      id: "r1",
      text: "Internal causes constitute a sufficient sphere of agency even if they are themselves determined",
      source: "Chrysippus' compatibilist position"
    },
    {
      id: "r2",
      text: "Co-fated events preserve a genuine role for human action within the fated order",
      source: "Chrysippus on sunēmmenon"
    }
  ],
  conclusion: "Stoic compatibilism remains a sophisticated but contested position in ancient debates on free will",
  relatedConcepts: ["determinism", "moral responsibility", "compatibilism", "fate", "providence"]
};

export const mockConceptEvolution = {
  conceptId: "eph_hemin",
  conceptLabel: "eph' hēmin (in our power)",
  timeline: [
    {
      period: "Classical Greek",
      dateRange: "4th c. BCE",
      formulation: "What depends on us vs. what doesn't in deliberation and choice",
      author: "Aristotle",
      work: "Nicomachean Ethics III.1-5",
      greekTerm: "ἐφ' ἡμῖν (eph' hēmin)",
      significance: "Foundation of voluntary action and moral responsibility"
    },
    {
      period: "Hellenistic Greek",
      dateRange: "3rd-2nd c. BCE",
      formulation: "Rational assent as the locus of what is 'up to us'",
      author: "Chrysippus",
      work: "On Fate (fragments)",
      greekTerm: "τὸ ἐφ' ἡμῖν (to eph' hēmin)",
      significance: "Compatibilist reinterpretation within deterministic framework"
    },
    {
      period: "Hellenistic Greek",
      dateRange: "2nd-1st c. BCE",
      formulation: "Critique: true 'up to us' requires causal origination",
      author: "Carneades",
      work: "Academic debates (fragments)",
      greekTerm: "ἐφ' ἡμῖν",
      significance: "Incompatibilist challenge to Stoic position"
    },
    {
      period: "Roman Imperial",
      dateRange: "2nd c. CE",
      formulation: "Latin translation and Peripatetic defense",
      author: "Alexander of Aphrodisias",
      work: "On Fate",
      greekTerm: "ἐφ' ἡμῖν",
      latinTerm: "in nostra potestate / in nobis",
      significance: "Reassertion of Aristotelian incompatibilism"
    },
    {
      period: "Patristic",
      dateRange: "4th-5th c. CE",
      formulation: "Free choice in relation to divine grace",
      author: "Augustine",
      work: "On Free Choice of the Will",
      latinTerm: "liberum arbitrium / in potestate nostra",
      significance: "Christian theological appropriation and transformation"
    }
  ]
};
