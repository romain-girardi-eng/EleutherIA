/**
 * Textual Grounding Service
 * Fetches original Greek/Latin passages and provides structured citations
 * for scholarly answers with proper textual evidence
 */

import { Env } from '../types';
import { getLogger } from '../utils/logger';

const logger = getLogger('TextualGrounding');

export interface TextualGrounding {
  passageId: string;
  ctsUrn: string;
  reference: string;         // e.g., "De Fato 39" or "Meditations 2.2"
  author: string;
  work: string;
  originalText: string;      // Greek or Latin
  language: 'grc' | 'lat';
  translation?: string;      // Will be filled by LLM if not available
  relevanceScore: number;    // How relevant to the query
}

export interface GroundingContext {
  groundings: TextualGrounding[];
  formattedContext: string;  // Ready-to-use context for LLM
}

/**
 * Extract passage IDs from KG node payloads
 * Handles both object and JSON string metadata formats
 */
export function extractPassageIds(nodes: any[]): string[] {
  const passageIds: string[] = [];

  for (const node of nodes) {
    if (!node?.payload) continue;

    const payload = node.payload;

    // First: Parse metadata if it's a JSON string (Qdrant stores it as string)
    let metadata: Record<string, any> = {};
    if (typeof payload.metadata === 'string') {
      try {
        metadata = JSON.parse(payload.metadata);
      } catch {
        // Invalid JSON, keep empty
      }
    } else if (payload.metadata && typeof payload.metadata === 'object') {
      metadata = payload.metadata;
    }

    // Method 1: Direct passage_id on payload (text_embeddings collection format)
    if (payload.passage_id) {
      passageIds.push(payload.passage_id);
      continue;
    }

    // Method 2: passage_id in parsed metadata (KG passage nodes)
    if (metadata.passage_id) {
      passageIds.push(metadata.passage_id);
      continue;
    }

    // Method 3: Check if this is a passage-type node (might not have direct link)
    if (payload.type === 'passage') {
      // Try to extract from node_id pattern (e.g., "passage_ma_med_2_2")
      // These can be looked up in the database by node_id -> passage_id mapping
      const nodeId = payload.node_id || '';
      if (nodeId.startsWith('passage_')) {
        // Store the node_id for potential database lookup
        // (The KG node might be linked to a passage even without passage_id in metadata)
        logger.debug(`Found passage-type node without passage_id: ${nodeId}`);
      }
    }

    // Method 4: Check for linked passages in metadata
    if (metadata.linked_passages && Array.isArray(metadata.linked_passages)) {
      passageIds.push(...metadata.linked_passages);
    }
  }

  logger.info(`Extracted ${passageIds.length} passage IDs from ${nodes.length} nodes`);
  return [...new Set(passageIds)]; // Deduplicate
}

/**
 * Fetch original passages from database
 */
export async function fetchPassageTexts(
  passageIds: string[],
  env: Env
): Promise<Map<string, TextualGrounding>> {
  if (passageIds.length === 0) return new Map();

  const results = new Map<string, TextualGrounding>();

  try {
    const supabaseUrl = env.SUPABASE_URL;
    const supabaseKey = env.SUPABASE_KEY;

    // Batch fetch passages
    const idsParam = passageIds.map(id => `"${id}"`).join(',');
    const url = `${supabaseUrl}/rest/v1/passages?passage_id=in.(${idsParam})&select=passage_id,cts_urn,book,chapter,section,text_content,ancient_works(author,title,language)`;

    const response = await fetch(url, {
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Accept-Profile': 'free_will',
      },
    });

    if (!response.ok) {
      logger.warn(`Failed to fetch passages: ${response.status}`);
      return results;
    }

    const passages = await response.json();

    for (const p of passages) {
      if (!p.text_content) continue;

      const work = p.ancient_works || {};
      const reference = formatReference(work.title, p.book, p.chapter, p.section);

      results.set(p.passage_id, {
        passageId: p.passage_id,
        ctsUrn: p.cts_urn || '',
        reference,
        author: work.author || 'Unknown',
        work: work.title || 'Unknown Work',
        originalText: p.text_content,
        language: work.language === 'lat' ? 'lat' : 'grc',
        relevanceScore: 1.0,
      });
    }

    logger.info(`Fetched ${results.size} passage texts for grounding`);

  } catch (error) {
    logger.error('Error fetching passage texts', error);
  }

  return results;
}

/**
 * Format a citation reference
 */
function formatReference(
  title: string | undefined,
  book: string | undefined,
  chapter: string | undefined,
  section: string | undefined
): string {
  const parts: string[] = [];
  if (title) parts.push(title);

  const loc: string[] = [];
  if (book) loc.push(book);
  if (chapter) loc.push(chapter);
  if (section) loc.push(section);

  if (loc.length > 0) {
    parts.push(loc.join('.'));
  }

  return parts.join(' ');
}

/**
 * Build formatted context with original texts for LLM
 */
export function buildGroundingContext(
  groundings: TextualGrounding[],
  maxLength: number = 8000
): string {
  if (groundings.length === 0) return '';

  const parts: string[] = [
    '=== PRIMARY SOURCE TEXTS (Original Greek/Latin) ===',
    'These are the actual ancient texts. Quote them directly and provide translations.',
    '',
  ];

  let currentLength = parts.join('\n').length;

  for (const g of groundings) {
    const langLabel = g.language === 'grc' ? 'Greek' : 'Latin';
    const entry = [
      `--- ${g.author}, ${g.reference} ---`,
      `[${langLabel}] ${g.originalText}`,
      g.ctsUrn ? `CTS URN: ${g.ctsUrn}` : '',
      '',
    ].filter(Boolean).join('\n');

    if (currentLength + entry.length > maxLength) break;

    parts.push(entry);
    currentLength += entry.length;
  }

  return parts.join('\n');
}

/**
 * Search for relevant passages by semantic similarity in Qdrant text_embeddings collection
 * This provides actual ancient texts when KG nodes don't have passage_id links
 */
export async function searchRelevantPassages(
  query: string,
  embedding: number[],
  env: Env,
  limit: number = 5
): Promise<TextualGrounding[]> {
  const results: TextualGrounding[] = [];

  try {
    // Search Qdrant text_embeddings collection directly
    const qdrantUrl = `https://${env.QDRANT_HOST}:6333`;
    const qdrantKey = env.QDRANT_API_KEY;

    const searchResponse = await fetch(`${qdrantUrl}/collections/text_embeddings/points/search`, {
      method: 'POST',
      headers: {
        'api-key': qdrantKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        vector: embedding,
        limit: limit,
        score_threshold: 0.5,  // Lowered from 0.7 for better recall on comparative queries
        with_payload: true,
      }),
    });

    if (!searchResponse.ok) {
      const errorText = await searchResponse.text();
      logger.warn(`Qdrant text_embeddings search failed: ${searchResponse.status} - ${errorText}`);
      // Fall back to Supabase RPC
      return await searchPassagesViaSupabase(embedding, env, limit);
    }

    const searchData = await searchResponse.json();
    const points = searchData.result || [];

    logger.info(`Found ${points.length} passages in text_embeddings collection (threshold: 0.5, limit: ${limit})`);

    for (const point of points) {
      const payload = point.payload || {};

      // Fetch full text content from database using passage_id
      const passageText = await fetchSinglePassageText(payload.passage_id, env);

      results.push({
        passageId: payload.passage_id || '',
        ctsUrn: payload.canonical_ref || '',
        reference: `${payload.author || 'Unknown'}, ${payload.title || 'Unknown'} ${payload.canonical_ref?.split(':').pop() || ''}`,
        author: payload.author || 'Unknown',
        work: payload.title || 'Unknown Work',
        originalText: passageText || payload.text_preview || '',
        language: payload.language === 'lat' ? 'lat' : 'grc',
        relevanceScore: point.score || 0.7,
      });
    }

  } catch (error) {
    logger.warn('Qdrant passage search failed, trying Supabase fallback', error);
    return await searchPassagesViaSupabase(embedding, env, limit);
  }

  return results;
}

/**
 * Fetch a single passage's full text from database
 */
async function fetchSinglePassageText(passageId: string, env: Env): Promise<string | null> {
  if (!passageId) return null;

  try {
    const supabaseUrl = env.SUPABASE_URL;
    const supabaseKey = env.SUPABASE_KEY;

    const url = `${supabaseUrl}/rest/v1/passages?passage_id=eq.${passageId}&select=text_content`;

    const response = await fetch(url, {
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Accept-Profile': 'free_will',
      },
    });

    if (!response.ok) return null;

    const passages = await response.json();
    return passages[0]?.text_content || null;
  } catch {
    return null;
  }
}

/**
 * Fallback: Search passages via Supabase RPC
 */
async function searchPassagesViaSupabase(
  embedding: number[],
  env: Env,
  limit: number
): Promise<TextualGrounding[]> {
  const results: TextualGrounding[] = [];

  try {
    const supabaseUrl = env.SUPABASE_URL;
    const supabaseKey = env.SUPABASE_KEY;

    const url = `${supabaseUrl}/rest/v1/rpc/search_passages_by_embedding`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query_embedding: embedding,
        match_count: limit,
        similarity_threshold: 0.7,
      }),
    });

    if (!response.ok) {
      logger.info('Supabase passage embedding search not available');
      return results;
    }

    const passages = await response.json();

    for (const p of passages) {
      results.push({
        passageId: p.passage_id,
        ctsUrn: p.cts_urn || '',
        reference: formatReference(p.title, p.book, p.chapter, p.section),
        author: p.author || 'Unknown',
        work: p.title || 'Unknown Work',
        originalText: p.text_content || '',
        language: p.language === 'lat' ? 'lat' : 'grc',
        relevanceScore: p.similarity || 0.7,
      });
    }

  } catch (error) {
    logger.warn('Supabase passage search failed', error);
  }

  return results;
}

/**
 * Enhanced prompt suffix for textual grounding
 */
export const TEXTUAL_GROUNDING_PROMPT = `
CRITICAL REQUIREMENTS FOR TEXTUAL GROUNDING:

1. QUOTE ORIGINAL TEXTS: When citing ancient sources, include the original Greek or Latin text in quotation marks, followed by your English translation in parentheses.

   Example format:
   As Epictetus states: "Τῶν ὄντων τὰ μέν ἐστιν ἐφ' ἡμῖν, τὰ δὲ οὐκ ἐφ' ἡμῖν" ("Of things that exist, some are in our power, others are not in our power" - Enchiridion 1).

2. ALWAYS PROVIDE TRANSLATIONS: Every Greek or Latin quotation MUST be followed by an English translation.

3. CITE PRECISELY: Use the format: Author, Work Book.Chapter.Section (e.g., "Cicero, De Fato 39" or "Marcus Aurelius, Meditations 2.2").

4. PRESERVE KEY TERMS: Keep important philosophical terms in their original language with translation:
   - τὸ ἐφ' ἡμῖν (to eph' hēmin, "what is in our power")
   - αὐτεξούσιον (autexousion, "self-determination")
   - εἱμαρμένη (heimarmenē, "fate")
   - συγκατάθεσις (synkatathesis, "assent")

5. USE CTS URNs: When available, include the CTS URN for precise scholarly reference.
`;

/**
 * Main function to get textual groundings for a GraphRAG query
 * Combines passage_id extraction from KG nodes with semantic search of text_embeddings
 */
export async function getTextualGroundings(
  nodes: any[],
  queryEmbedding: number[],
  env: Env
): Promise<GroundingContext> {
  const allGroundings: TextualGrounding[] = [];
  const seenPassageIds = new Set<string>();

  // Strategy 1: Extract passage IDs from KG nodes (passage-type nodes with metadata.passage_id)
  const passageIds = extractPassageIds(nodes);
  if (passageIds.length > 0) {
    const kgGroundingsMap = await fetchPassageTexts(passageIds, env);
    for (const grounding of kgGroundingsMap.values()) {
      if (!seenPassageIds.has(grounding.passageId)) {
        seenPassageIds.add(grounding.passageId);
        allGroundings.push(grounding);
      }
    }
    logger.info(`Strategy 1 (KG nodes): Found ${kgGroundingsMap.size} passages`);
  }

  // Strategy 2: Always search text_embeddings for semantically relevant passages
  // This ensures we have actual ancient texts even when KG nodes don't link to passages
  const semanticLimit = Math.max(5, 8 - allGroundings.length);
  const semanticPassages = await searchRelevantPassages(
    '', // query not needed if using embedding
    queryEmbedding,
    env,
    semanticLimit
  );

  for (const passage of semanticPassages) {
    if (!seenPassageIds.has(passage.passageId) && passage.passageId) {
      seenPassageIds.add(passage.passageId);
      allGroundings.push(passage);
    }
  }
  logger.info(`Strategy 2 (semantic search): Found ${semanticPassages.length} passages, ${allGroundings.length} total unique`);

  // Sort by relevance score (highest first)
  allGroundings.sort((a, b) => b.relevanceScore - a.relevanceScore);

  // Limit to top passages to avoid context overflow
  const topGroundings = allGroundings.slice(0, 8);

  // Build formatted context
  const formattedContext = buildGroundingContext(topGroundings);

  return {
    groundings: topGroundings,
    formattedContext,
  };
}
