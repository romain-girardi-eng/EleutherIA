/**
 * PageIndex Retrieval Service — Direct KG + Passage retrieval.
 *
 * Replaces the complex multi-LLM pipeline (HyDE, CRAG, SELF-RAG, reranking)
 * with direct database lookups that leverage the curated passage_citations
 * linking KG nodes to actual ancient text passages.
 *
 * Philosophy: With 17k passages and Gemini's 1M token context, we don't need
 * 10 LLM calls to find and validate context. We need ONE good retrieval step
 * and ONE good synthesis call.
 */

import { Env } from '../types';
import { getLogger } from '../utils/logger';

const logger = getLogger('PageIndexRetrieval');

export interface LinkedPassage {
  passageId: string;
  ctsUrn: string;
  canonicalRef: string;
  textContent: string;
  book?: string;
  chapter?: string;
  section?: string;
  author: string;
  workTitle: string;
  language: 'grc' | 'lat' | string;
  confidence: number;
  kgNodeId: string;
}

export interface KGNeighbor {
  nodeId: string;
  label: string;
  type: string;
  description: string;
  relation: string;
  direction: 'outgoing' | 'incoming';
}

/**
 * Fetch passages linked to KG nodes via the passage_citations table.
 *
 * This is the core PageIndex operation: given a set of KG node IDs,
 * retrieve all associated ancient text passages with FULL text content.
 *
 * Join path: kg_node_id → passage_citations → passages → ancient_works
 */
export async function getLinkedPassages(
  nodeIds: string[],
  env: Env,
): Promise<LinkedPassage[]> {
  if (nodeIds.length === 0) return [];

  const supabaseUrl = env.SUPABASE_URL.replace(/\/+$/, '').replace(/\/rest\/v1$/i, '');
  const supabaseKey = env.SUPABASE_KEY;

  try {
    // Use PostgREST embedded resource syntax for the 3-table join
    const idsParam = nodeIds.map(id => `${encodeURIComponent(id)}`).join(',');
    const select = [
      'citation_id',
      'kg_node_id',
      'confidence',
      'citation_type',
      'passages!inner(passage_id,cts_urn,canonical_ref,book,chapter,section,text_content,ancient_works!inner(author,title,language))',
    ].join(',');

    const url = `${supabaseUrl}/rest/v1/passage_citations?kg_node_id=in.(${idsParam})&select=${select}&order=confidence.desc.nullslast&limit=100`;

    const response = await fetch(url, {
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Accept-Profile': 'free_will',
      },
    });

    if (!response.ok) {
      // Fallback: try public schema
      const fallbackUrl = `${supabaseUrl}/rest/v1/passage_citations?kg_node_id=in.(${idsParam})&select=${select}&order=confidence.desc.nullslast&limit=100`;
      const fallbackResponse = await fetch(fallbackUrl, {
        headers: {
          'apikey': supabaseKey,
          'Authorization': `Bearer ${supabaseKey}`,
        },
      });
      if (!fallbackResponse.ok) {
        logger.warn(`passage_citations query failed: ${response.status}`);
        return [];
      }
      const rows = await fallbackResponse.json() as any[];
      return parseLinkedPassages(rows);
    }

    const rows = await response.json() as any[];
    return parseLinkedPassages(rows);
  } catch (error) {
    logger.error('Error fetching linked passages', error);
    return [];
  }
}

function parseLinkedPassages(rows: any[]): LinkedPassage[] {
  if (!Array.isArray(rows)) return [];

  const results: LinkedPassage[] = [];
  const seen = new Set<string>();

  for (const row of rows) {
    const p = row.passages;
    if (!p || !p.text_content) continue;

    // Deduplicate by passage_id
    if (seen.has(p.passage_id)) continue;
    seen.add(p.passage_id);

    const work = p.ancient_works || {};

    results.push({
      passageId: p.passage_id,
      ctsUrn: p.cts_urn || '',
      canonicalRef: p.canonical_ref || '',
      textContent: p.text_content,
      book: p.book,
      chapter: p.chapter,
      section: p.section,
      author: work.author || 'Unknown',
      workTitle: work.title || 'Unknown',
      language: work.language || 'grc',
      confidence: row.confidence ?? 0.5,
      kgNodeId: row.kg_node_id,
    });
  }

  logger.info(`Parsed ${results.length} linked passages from ${rows.length} citation rows`);
  return results;
}

/**
 * Get 1-hop neighbors of KG nodes via the kg_edges table.
 *
 * Fetches edges where our seed nodes are source or target, then
 * resolves the neighbor node IDs into labels/descriptions via a
 * second query to kg_nodes.
 */
export async function getNodeNeighbors(
  nodeIds: string[],
  env: Env,
): Promise<KGNeighbor[]> {
  if (nodeIds.length === 0) return [];

  const supabaseUrl = env.SUPABASE_URL.replace(/\/+$/, '').replace(/\/rest\/v1$/i, '');
  const supabaseKey = env.SUPABASE_KEY;
  const headers = {
    'apikey': supabaseKey,
    'Authorization': `Bearer ${supabaseKey}`,
    'Accept-Profile': 'free_will',
  };

  try {
    const idsParam = nodeIds.map(id => `${encodeURIComponent(id)}`).join(',');

    // Fetch outgoing and incoming edges in parallel (no joins — simpler and more reliable)
    const [outRes, inRes] = await Promise.all([
      fetch(`${supabaseUrl}/rest/v1/kg_edges?source_id=in.(${idsParam})&select=source_id,target_id,relation,description&limit=80`, { headers }).catch(() => null),
      fetch(`${supabaseUrl}/rest/v1/kg_edges?target_id=in.(${idsParam})&select=source_id,target_id,relation,description&limit=80`, { headers }).catch(() => null),
    ]);

    // Collect neighbor node IDs from edges
    const neighborMap = new Map<string, { relation: string; direction: 'outgoing' | 'incoming'; edgeDesc: string }>();
    const seedSet = new Set(nodeIds);

    if (outRes?.ok) {
      const rows = await outRes.json() as any[];
      for (const row of (Array.isArray(rows) ? rows : [])) {
        if (row.target_id && !seedSet.has(row.target_id) && !neighborMap.has(row.target_id)) {
          neighborMap.set(row.target_id, { relation: row.relation || 'related_to', direction: 'outgoing', edgeDesc: row.description || '' });
        }
      }
    }

    if (inRes?.ok) {
      const rows = await inRes.json() as any[];
      for (const row of (Array.isArray(rows) ? rows : [])) {
        if (row.source_id && !seedSet.has(row.source_id) && !neighborMap.has(row.source_id)) {
          neighborMap.set(row.source_id, { relation: row.relation || 'related_to', direction: 'incoming', edgeDesc: row.description || '' });
        }
      }
    }

    if (neighborMap.size === 0) return [];

    // Fetch neighbor node details
    const neighborIds = Array.from(neighborMap.keys()).slice(0, 50);
    const nIdsParam = neighborIds.map(id => `${encodeURIComponent(id)}`).join(',');
    const nodesRes = await fetch(
      `${supabaseUrl}/rest/v1/kg_nodes?node_id=in.(${nIdsParam})&select=node_id,label,type,description&limit=50`,
      { headers },
    ).catch(() => null);

    const neighbors: KGNeighbor[] = [];
    if (nodesRes?.ok) {
      const nodeRows = await nodesRes.json() as any[];
      for (const n of (Array.isArray(nodeRows) ? nodeRows : [])) {
        const edge = neighborMap.get(n.node_id);
        if (!edge) continue;
        neighbors.push({
          nodeId: n.node_id,
          label: n.label || n.node_id,
          type: n.type || 'concept',
          description: n.description || edge.edgeDesc,
          relation: edge.relation,
          direction: edge.direction,
        });
      }
    }

    logger.info(`Found ${neighbors.length} KG neighbors for ${nodeIds.length} seed nodes`);
    return neighbors;
  } catch (error) {
    logger.error('Error fetching node neighbors', error);
    return [];
  }
}

/**
 * Build full scholarly context from KG nodes, neighbors, and passages.
 * NO TRUNCATION — Gemini has ~1M token context.
 */
export function buildPageIndexContext(
  seedNodes: Array<{ payload: any; score: number }>,
  neighbors: KGNeighbor[],
  linkedPassages: LinkedPassage[],
  semanticPassages: Array<{ payload: any; score: number }>,
  edges: Array<{ payload: any }>,
): string {
  const parts: string[] = [];

  // Section 1: Primary ancient text passages (from passage_citations — highest quality)
  if (linkedPassages.length > 0) {
    parts.push('=== PRIMARY ANCIENT SOURCES (from passage_citations database) ===');
    parts.push('These passages are directly linked to the knowledge graph entities found.');
    parts.push('');

    for (const p of linkedPassages) {
      const ref = p.ctsUrn || p.canonicalRef || `${p.book || ''}${p.chapter ? '.' + p.chapter : ''}${p.section ? '.' + p.section : ''}`;
      const lang = p.language === 'lat' ? 'Latin' : 'Greek';
      parts.push(`[${lang} Source] ${p.author}, ${p.workTitle} (${ref})`);
      parts.push(`Linked to KG entity: ${p.kgNodeId} | Confidence: ${p.confidence}`);
      parts.push(p.textContent); // FULL text — no truncation
      parts.push('');
    }
  }

  // Section 2: Semantic search passages (supplementary)
  if (semanticPassages.length > 0) {
    parts.push('=== SUPPLEMENTARY PASSAGES (from semantic search) ===');

    for (const result of semanticPassages) {
      const p = result.payload;
      if (!p) continue;
      const author = p.author || 'Unknown';
      const work = p.title || 'Unknown';
      const text = p.text_content || p.text_preview || p.description || '';
      if (!text) continue;
      const ref = p.canonical_ref || p.cts_urn || '';
      const label = ref ? `${author}, ${work} (${ref})` : `${author}, ${work}`;
      parts.push(`[Passage] ${label}`);
      parts.push(text); // FULL text
      parts.push('');
    }
  }

  // Section 3: KG entities (seed nodes from vector search)
  if (seedNodes.length > 0) {
    parts.push('=== KNOWLEDGE GRAPH ENTITIES ===');

    for (const nodeResult of seedNodes) {
      const node = nodeResult.payload;
      if (!node) continue;
      const name = node.label || node.node_id || 'Unknown';
      const type = node.type || 'concept';
      const desc = node.description || '';
      const school = node.metadata?.school || node.school || '';
      const period = node.period || '';
      const meta = [school, period].filter(Boolean).join(', ');
      parts.push(`[${type}] ${name}${meta ? ` (${meta})` : ''}`);
      if (desc) parts.push(desc); // FULL description
      parts.push('');
    }
  }

  // Section 4: KG relationships (neighbors + edges)
  if (neighbors.length > 0 || edges.length > 0) {
    parts.push('=== RELATIONSHIPS & CONNECTIONS ===');

    for (const n of neighbors) {
      const arrow = n.direction === 'outgoing' ? '→' : '←';
      parts.push(`[${n.type}] ${n.label} ${arrow} ${n.relation}`);
      if (n.description) parts.push(n.description);
      parts.push('');
    }

    for (const edge of edges) {
      if (!edge?.payload) continue;
      const { source_id, target_id, relation, description } = edge.payload;
      parts.push(`[Relationship] ${source_id || '?'} --${relation || 'related'}--> ${target_id || '?'}`);
      if (description) parts.push(description);
    }
  }

  return parts.join('\n');
}
