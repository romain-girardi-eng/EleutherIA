// Mock GraphRAG data for demo/testing without authentication
import type { GraphRAGResponse } from '../types';
import type { ReasoningStep } from '../types/graphrag';

export const mockGraphRAGResponse: GraphRAGResponse = {
  query: "How did the Stoics reconcile fate with moral responsibility?",
  answer: `The Stoics developed a sophisticated compatibilist position that reconciled their belief in universal causal determinism (heimarmenē) with moral responsibility and human agency.

**1. The Distinction Between Internal and External Causes**

Chrysippus distinguished between "perfect and principal" causes that come from within the agent and "auxiliary and proximate" causes that come from outside. While external impressions trigger our actions, assent to these impressions remains "in our power" (eph' hēmin).

**2. The Cylinder Analogy**

Chrysippus used the cylinder analogy to illustrate this distinction: just as a cylinder, once pushed, rolls by its own nature, so too do humans respond to impressions according to their rational nature.

**3. Rational Assent as the Locus of Responsibility**

The Stoics located moral responsibility in the faculty of rational assent. Since mature rational agents have the capacity to assent or withhold assent from impressions, they bear responsibility for their actions even within a deterministic universe.`,

  citations: {
    ancient_sources: [
      "Cicero, On Fate 41-43",
      "Aulus Gellius, Attic Nights 7.2.11",
      "Epictetus, Discourses 1.1",
      "SVF 2.974-975",
      "Diogenes Laertius, Lives 7.149"
    ],
    modern_scholarship: [
      "Bobzien (1998) Determinism and Freedom in Stoic Philosophy",
      "Long & Sedley (1987) The Hellenistic Philosophers",
      "Frede (2011) A Free Will: Origins of the Notion in Ancient Thought"
    ]
  },

  reasoning_path: {
    starting_nodes: [
      {
        id: "person_chrysippus",
        label: "Chrysippus",
        type: "person",
        reason: "Third head of the Stoa, developed compatibilist theory"
      },
      {
        id: "concept_heimarmene",
        label: "Fate (heimarmenē)",
        type: "concept",
        reason: "Stoic concept of universal causal determinism"
      }
    ],
    expanded_nodes: [
      {
        id: "concept_eph_hemin",
        label: "eph' hēmin (in our power)",
        type: "concept",
        reason: "Greek term for what is 'in our power'"
      }
    ],
    traversed_edges: [
      {
        source: "person_chrysippus",
        target: "concept_heimarmene",
        relation: "theorizes_about",
        description: "Chrysippus developed the Stoic theory of fate"
      }
    ],
    total_nodes: 10,
    total_edges: 4
  },

  nodes_used: 10,
  edges_traversed: 4,
  success: true
};

export const mockReasoningSteps: ReasoningStep[] = [
  {
    id: 1,
    type: 'search',
    label: 'Semantic Search',
    description: 'Searching for relevant concepts',
    status: 'complete',
    nodes: ['person_chrysippus', 'concept_heimarmene']
  },
  {
    id: 2,
    type: 'traverse',
    label: 'Graph Traversal',
    description: 'Exploring related concepts',
    status: 'complete',
    nodes: ['concept_eph_hemin']
  },
  {
    id: 3,
    type: 'context',
    label: 'Building Context',
    description: 'Aggregating knowledge',
    status: 'complete'
  },
  {
    id: 4,
    type: 'synthesis',
    label: 'Synthesis',
    description: 'Generating answer',
    status: 'complete'
  }
];
