import { useEffect, useMemo, useState } from 'react';
import { apiClient } from '../../api/client';
import type { KGNode } from '../../types';
import type { KGNeighborSummary } from '../../api/client';
import { chronologicalAnchor, describeSpan, yearToCenturyLabel } from './periods';

// The four relation families that define a debate's argumentative spine.
export const DEBATE_RELATIONS = ['argues_for', 'responds_to', 'precedes', 'critiques'] as const;
export type DebateRelation = (typeof DEBATE_RELATIONS)[number];

export interface SubgraphEdge {
  relation: string;
  source: string;
  target: string;
}

export interface DebateNode extends KGNode {
  anchor: number; // chronological century anchor (signed year)
}

export interface DebateSubgraph {
  concept: DebateNode;
  /** All argument/concept/position nodes reachable via the four relations. */
  related: DebateNode[];
  edges: SubgraphEdge[];
  span: { earliest: string; latest: string; centuries: number };
}

interface State {
  data: DebateSubgraph | null;
  loading: boolean;
  error: string | null;
}

function toDebateNode(node: KGNode): DebateNode {
  return { ...node, anchor: chronologicalAnchor(node) };
}

function isDebateRelation(relation: string): relation is DebateRelation {
  return (DEBATE_RELATIONS as readonly string[]).includes(relation);
}

/**
 * Fetch a concept node and the argues_for / responds_to / precedes / critiques
 * subgraph around it, then hydrate every neighbour into a full KG node so the
 * timeline and argument maps have descriptions, terms and periods to render.
 */
export function useDebateSubgraph(conceptId: string | undefined): State {
  const [state, setState] = useState<State>({ data: null, loading: true, error: null });

  useEffect(() => {
    if (!conceptId) {
      setState({ data: null, loading: false, error: 'No concept id provided.' });
      return;
    }

    let cancelled = false;
    setState({ data: null, loading: true, error: null });

    (async () => {
      try {
        const [concept, neighbours] = await Promise.all([
          apiClient.getNodeById(conceptId),
          apiClient.getNodeNeighbors(conceptId, { depth: 1 }),
        ]);

        if (cancelled) return;

        // Collect neighbour ids reachable through the four debate relations.
        const edges: SubgraphEdge[] = [];
        const relatedIds = new Set<string>();

        const consume = (
          groups: Record<string, KGNeighborSummary[]>,
          direction: 'outgoing' | 'incoming'
        ) => {
          for (const [relation, summaries] of Object.entries(groups)) {
            if (!isDebateRelation(relation)) continue;
            for (const summary of summaries) {
              relatedIds.add(summary.node_id);
              if (direction === 'outgoing') {
                edges.push({ relation, source: conceptId, target: summary.node_id });
              } else {
                edges.push({ relation, source: summary.node_id, target: conceptId });
              }
            }
          }
        };

        consume(neighbours.neighbors.outgoing, 'outgoing');
        consume(neighbours.neighbors.incoming, 'incoming');

        // Hydrate each neighbour into a full node (descriptions, terms, periods).
        const hydrated = await Promise.all(
          [...relatedIds].map(async (id) => {
            try {
              return await apiClient.getNodeById(id);
            } catch {
              return null;
            }
          })
        );

        if (cancelled) return;

        const related = hydrated
          .filter((n): n is KGNode => n !== null)
          .map(toDebateNode);

        const conceptNode = toDebateNode(concept);
        const span = describeSpan([conceptNode.anchor, ...related.map((n) => n.anchor)]);

        setState({
          data: { concept: conceptNode, related, edges, span },
          loading: false,
          error: null,
        });
      } catch (err) {
        if (cancelled) return;
        const message =
          err instanceof Error ? err.message : 'Failed to load the debate subgraph.';
        setState({ data: null, loading: false, error: message });
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [conceptId]);

  return state;
}

// ── Adapters: KG nodes → the shapes the existing components already consume ──

export interface TimelineEntry {
  period: string;
  dateRange: string;
  formulation: string;
  author?: string;
  work?: string;
  greekTerm?: string;
  latinTerm?: string;
  significance: string;
  nodeId: string;
}

export interface ConceptEvolutionShape {
  conceptId: string;
  conceptLabel: string;
  timeline: TimelineEntry[];
}

export interface ArgumentMappingShape {
  id: string;
  claim: string;
  premises: Array<{ id: string; text: string; source?: string }>;
  objections?: Array<{ id: string; text: string; source?: string }>;
  responses?: Array<{ id: string; text: string; source?: string }>;
  conclusion: string;
  relatedConcepts: string[];
}

function truncate(text: string | undefined, max = 220): string {
  if (!text) return '';
  return text.length > max ? `${text.slice(0, max - 1).trimEnd()}…` : text;
}

/** Build the ConceptEvolution timeline from the dated nodes in the subgraph. */
export function toConceptEvolution(graph: DebateSubgraph): ConceptEvolutionShape {
  const seed = graph.concept;
  const nodes: DebateNode[] = [seed, ...graph.related];

  const timeline: TimelineEntry[] = nodes
    .map((node) => {
      const dateRange = yearToCenturyLabel(node.anchor);
      const formulation =
        node.position_on_free_will?.trim() ||
        truncate(node.description) ||
        node.label;
      return {
        nodeId: node.id,
        period: node.period?.trim() || (Number.isFinite(node.anchor) ? 'Dated' : 'Undated'),
        dateRange,
        formulation,
        author: node.school || undefined,
        work: node.type === 'work' ? node.label : undefined,
        greekTerm: node.greek_term || undefined,
        latinTerm: node.latin_term || undefined,
        significance:
          truncate(node.description, 360) ||
          `${node.label} — ${node.type.replace(/_/g, ' ')}.`,
      };
    })
    // keep only entries we could place on the timeline
    .filter((entry) => entry.dateRange !== 'Undated');

  return {
    conceptId: seed.id,
    conceptLabel: seed.greek_term
      ? `${seed.label} (${seed.greek_term})`
      : seed.label,
    timeline,
  };
}

/**
 * Build one ArgumentMapping per `argues_for` argument node attached to the
 * concept: premises = description sentences, objections = `critiques` neighbours,
 * responses = `responds_to` neighbours. Pure presentation over verbatim KG text;
 * no ancient-language text is synthesised.
 */
export function toArgumentMappings(graph: DebateSubgraph): ArgumentMappingShape[] {
  const byId = new Map<string, DebateNode>();
  for (const node of [graph.concept, ...graph.related]) byId.set(node.id, node);

  // Arguments directly attached to the concept.
  const argumentIds = new Set(
    graph.edges
      .filter((e) => e.relation === 'argues_for')
      .map((e) => (e.source === graph.concept.id ? e.target : e.source))
      .filter((id) => byId.get(id)?.type === 'argument')
  );

  const mappings: ArgumentMappingShape[] = [];

  for (const argId of argumentIds) {
    const arg = byId.get(argId);
    if (!arg) continue;

    const description = arg.description?.trim() || arg.label;
    // Split the description into premise-sized chunks on sentence boundaries.
    const sentences = description
      .split(/(?<=[.;])\s+(?=[A-Z(“"Ͱ-Ͽ])/)
      .map((s) => s.trim())
      .filter(Boolean);

    const premises = (sentences.length > 1 ? sentences.slice(0, -1) : sentences).map(
      (text, idx) => ({
        id: `${argId}-p${idx}`,
        text,
        source: arg.ancient_sources?.[0],
      })
    );

    const objections = graph.edges
      .filter((e) => e.relation === 'critiques' && (e.target === argId || e.source === argId))
      .map((e) => (e.source === argId ? e.target : e.source))
      .map((id) => byId.get(id))
      .filter((n): n is DebateNode => Boolean(n))
      .map((n) => ({
        id: `${n.id}-obj`,
        text: truncate(n.description) || n.label,
        source: n.label,
      }));

    const responses = graph.edges
      .filter((e) => e.relation === 'responds_to' && (e.target === argId || e.source === argId))
      .map((e) => (e.source === argId ? e.target : e.source))
      .map((id) => byId.get(id))
      .filter((n): n is DebateNode => Boolean(n))
      .map((n) => ({
        id: `${n.id}-res`,
        text: truncate(n.description) || n.label,
        source: n.label,
      }));

    mappings.push({
      id: argId,
      claim: arg.label,
      premises,
      objections: objections.length ? objections : undefined,
      responses: responses.length ? responses : undefined,
      conclusion:
        sentences.length > 1 ? sentences[sentences.length - 1] : description,
      relatedConcepts: [graph.concept.label],
    });
  }

  // Sort by chronology so the maps read earliest → latest.
  return mappings.sort((a, b) => {
    const na = byId.get(a.id)?.anchor ?? 0;
    const nb = byId.get(b.id)?.anchor ?? 0;
    return na - nb;
  });
}

/** Stable hook wrapper that memoises the adapter output. */
export function useDebateAdapters(graph: DebateSubgraph | null) {
  return useMemo(() => {
    if (!graph) return { evolution: null, arguments: [] as ArgumentMappingShape[] };
    return {
      evolution: toConceptEvolution(graph),
      arguments: toArgumentMappings(graph),
    };
  }, [graph]);
}
