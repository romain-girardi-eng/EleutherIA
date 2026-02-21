/**
 * GraphRAG Routes - SECURED & OPTIMIZED
 * With full evidence chains and CTS URN support
 *
 * v2 Enhancement (2025): HyDE, Query Expansion, CRAG, SELF-RAG, Reranking,
 * Debate Scoring, Evidence Tracing, Multi-hop Synthesis
 */

import { Hono } from 'hono';
import { Env } from '../types';
import { DatabaseService } from '../services/database';
import { QdrantService } from '../services/qdrant';
import { LLMService } from '../services/llm';
import { buildEvidencePackage, isPassageNode } from '../services/evidence-chain-builder';
import { detectPassageReferences, resolvePassageReferences, buildPassageContext } from '../services/passage-reference-detector';
import { getTextualGroundings, TEXTUAL_GROUNDING_PROMPT, TextualGrounding } from '../services/textual-grounding';
import { getLogger } from '../utils/logger';
import { resolveCorsOrigin } from '../utils/cors';
import { authMiddleware, optionalAuthMiddleware, rateLimitMiddleware, validateGraphRAGInput } from '../middleware/auth';

// PageIndex direct retrieval (v3 — simplified pipeline)
import { getLinkedPassages, getNodeNeighbors, buildPageIndexContext } from '../services/pageindex-retrieval';
import { PassageRetrievalService } from '../services/passage-retrieval';

// 2025 Advanced RAG Services (kept for legacy endpoint)
import { hydeSearch, hydeEnhancedSearch, generateHypotheticalDocument } from '../services/hyde';
import { expandPhilologicalQuery, quickExpand, expandedSearch } from '../services/query-expander';
import { llmRerank, scholarlyRerank, RerankCandidate } from '../services/reranker';
import { validateRetrievalSufficiency, cragPipeline } from '../services/crag';
import { selfEvaluateAnswer, selfRAGPipeline, explainConfidence } from '../services/self-rag';
import { identifyDebates, scoreDebateIntensity, formatDebateForDisplay, DebateNode, DebateEdge } from '../services/debate-scorer';
import { buildEvidenceTraces, calculateEvidenceQuality } from '../services/evidence-tracer';
import { HierarchicalRetrievalService } from '../services/hierarchical-retrieval';

const logger = getLogger('GraphRAGRoutes');

/**
 * Sentence-aware text truncation that preserves Unicode diacritics.
 * Cuts at the last sentence boundary before maxChars, falling back to
 * the last whitespace. Appends " [...]" when text is truncated.
 */
function truncateText(text: string | undefined | null, maxChars: number): string {
  if (!text) return '';
  if (text.length <= maxChars) return text;
  const suffix = ' [...]';
  const budget = maxChars - suffix.length;
  if (budget <= 0) return text.slice(0, maxChars);
  const window = text.slice(0, budget);
  // Find last sentence boundary (period, semicolon, question mark, exclamation, Greek ano teleia)
  const sentenceEnd = /[.;·?!]\s/g;
  let lastBoundary = -1;
  let match: RegExpExecArray | null;
  while ((match = sentenceEnd.exec(window)) !== null) {
    lastBoundary = match.index + match[0].length;
  }
  if (lastBoundary > 0) return text.slice(0, lastBoundary).trimEnd() + suffix;
  const lastSpace = window.lastIndexOf(' ');
  if (lastSpace > 0) return text.slice(0, lastSpace).trimEnd() + suffix;
  return window + suffix;
}

export const graphragRoutes = new Hono<{ Bindings: Env }>();

// Legacy V1 and V2 endpoints were removed (replaced by HiRAG V2 on 2025-12-31)

/*
// ARCHIVED: Legacy V2 endpoint
graphragRoutes.post('/answer/legacy-v2', async (c) => {
  const startTime = Date.now();

  try {
    const body = await c.req.json();
    const {
      query,
      semantic_k = 15,
      graph_depth = 2,
      max_context = 15,
      mode = 'local',
      includeEvidence = true,
      // V2 Enhancement options
      use_hyde = true,           // HyDE search
      use_expansion = true,      // Query expansion with Greek/Latin
      use_reranking = true,      // LLM reranking
      use_crag = true,           // CRAG validation
      use_selfrag = true,        // SELF-RAG evaluation
      use_debates = true,        // Debate identification
    } = body;

    // Inline validation
    if (!query || typeof query !== 'string' || query.length === 0 || query.length > 1000) {
      return c.json({
        error: 'Invalid input',
        message: 'Query must be a non-empty string (max 1000 characters)',
        success: false,
      }, 400);
    }

    const db = new DatabaseService(c.env);
    const qdrant = new QdrantService(c.env);
    const llm = new LLMService(c.env);

    logger.info(`GraphRAG v2 starting: query="${query.slice(0, 50)}...", hyde=${use_hyde}, expansion=${use_expansion}, reranking=${use_reranking}, crag=${use_crag}, selfrag=${use_selfrag}`);

    // PRIORITY: Detect and resolve explicit passage references FIRST
    const passageRefs = detectPassageReferences(query);
    const resolvedPassages = await resolvePassageReferences(passageRefs, c.env);
    const priorityContext = buildPassageContext(resolvedPassages);

    if (resolvedPassages.length > 0) {
      logger.info(`Resolved ${resolvedPassages.length} explicit passage references`);
    }

    // =================================================================
    // STEP 1 + 2: PARALLELIZED - Query Embedding, Expansion, HyDE, and Searches
    // Optimization: Run all independent operations in parallel to reduce latency
    // =================================================================
    logger.info('Starting parallelized retrieval phase');

    // BATCH 1: Run embedding, expansion, and HyDE hypothesis generation in parallel
    const [
      geminiVector,
      queryExpansionResult,
      hypotheticalDocResult,
    ] = await Promise.all([
      llm.embed(query),
      use_expansion
        ? expandPhilologicalQuery(query, llm).catch(err => {
            logger.warn('Query expansion failed, using fallback', err);
            return quickExpand(query);
          })
        : Promise.resolve(null),
      use_hyde
        ? generateHypotheticalDocument(query, llm).catch(err => {
            logger.warn('HyDE hypothesis generation failed', err);
            return '';
          })
        : Promise.resolve(''),
    ]);

    let queryExpansion = queryExpansionResult;
    let hypotheticalDocument = hypotheticalDocResult;

    if (queryExpansion) {
      logger.info(`Query expanded: ${queryExpansion.greekTerms?.length || 0} Greek, ${queryExpansion.latinTerms?.length || 0} Latin terms`);
    }

    // BATCH 2: Run all searches in parallel (after embedding is ready)
    const [
      standardResults,
      hydeSearchResults,
      nodeResults,
      edgeSearchResults,
    ] = await Promise.all([
      // Standard semantic search
      qdrant.searchTexts(geminiVector, semantic_k * 2, undefined, 0.5),

      // HyDE search (if enabled and we have a hypothetical document)
      use_hyde && hypotheticalDocument
        ? (async () => {
            try {
              const hydeEmbedding = await llm.embed(hypotheticalDocument);
              return await qdrant.searchTexts(hydeEmbedding, semantic_k, undefined, 0.5);
            } catch (err) {
              logger.warn('HyDE search failed', err);
              return [];
            }
          })()
        : Promise.resolve([]),

      // KG nodes search
      qdrant.searchNodes(geminiVector, semantic_k, 0.5),

      // KG edges search (gracefully handle if collection doesn't exist)
      qdrant.searchEdges(geminiVector, semantic_k, 0.7).catch(err => {
        logger.warn('kg_edges collection not available, skipping', err);
        return [];
      }),
    ]);

    // Convert HyDE results to expected format
    let hydeResults: any[] = hydeSearchResults.map(r => ({
      id: r.id,
      score: r.score,
      passageId: r.payload?.passage_id,
      author: r.payload?.author,
      work: r.payload?.title,
      text: r.payload?.text_preview || r.payload?.text_content,
      language: r.payload?.language,
      payload: r.payload,
    }));
    if (hydeResults.length > 0) {
      logger.info(`HyDE search: ${hydeResults.length} results`);
    }

    let edgeResults = edgeSearchResults;

    // Expanded search (run after batch 2 since it needs queryExpansion results)
    let expandedResults: any[] = [];
    if (use_expansion && queryExpansion && queryExpansion.greekTerms?.length > 0) {
      try {
        const expandResult = await expandedSearch(query, queryExpansion, qdrant, llm, semantic_k);
        expandedResults = expandResult.results;
        logger.info(`Expanded search: ${expandedResults.length} results`);
      } catch (err) {
        logger.warn('Expanded search failed, continuing without', err);
      }
    }

    // =================================================================
    // STEP 3: RRF Fusion of all results
    // =================================================================
    const k = 60;  // RRF constant
    const scores = new Map<string, number>();
    const items = new Map<string, any>();

    // Score standard results
    standardResults.forEach((item, rank) => {
      const id = String(item.id);
      scores.set(id, (scores.get(id) || 0) + 1 / (k + rank + 1));
      if (!items.has(id)) items.set(id, item);
    });

    // Score HyDE results (slight boost for bridging semantic gap)
    hydeResults.forEach((item, rank) => {
      const id = String(item.id);
      scores.set(id, (scores.get(id) || 0) + 1.1 / (k + rank + 1));
      if (!items.has(id)) items.set(id, item);
    });

    // Score expanded results
    expandedResults.forEach((item, rank) => {
      const id = String(item.id);
      scores.set(id, (scores.get(id) || 0) + 1 / (k + rank + 1));
      if (!items.has(id)) items.set(id, item);
    });

    // Sort by RRF score and take top candidates
    const fusedIds = Array.from(scores.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 50)
      .map(([id]) => id);

    const fusedResults = fusedIds.map(id => items.get(id)!);

    logger.info(`RRF fusion: ${fusedResults.length} candidates from ${standardResults.length} standard + ${hydeResults.length} HyDE + ${expandedResults.length} expanded`);

    // =================================================================
    // STEP 4: LLM Reranking
    // =================================================================
    let rerankedResults = fusedResults;
    let rerankingApplied = false;

    if (use_reranking && fusedResults.length > 5) {
      try {
        const candidates: RerankCandidate[] = fusedResults.slice(0, 30).map(r => ({
          id: r.id,
          score: r.score,
          text: r.payload?.text_content || r.payload?.text_preview || r.payload?.description || '',
          author: r.payload?.author,
          work: r.payload?.title,
          metadata: r.payload,
        }));

        const rerankResponse = await scholarlyRerank(query, candidates, llm, max_context);
        rerankedResults = rerankResponse.results.map(r => items.get(String(r.id)) || r);
        rerankingApplied = true;
        logger.info(`Reranking: ${rerankResponse.candidatesEvaluated} candidates → ${rerankResponse.results.length} results`);
      } catch (err) {
        logger.warn('Reranking failed, using RRF order', err);
      }
    }

    // Build search score map for evidence tracing
    const searchScores = new Map<string, number>();
    rerankedResults.slice(0, max_context).forEach((r, i) => {
      searchScores.set(String(r.id || r.payload?.node_id), r.score || (1 - i * 0.05));
    });

    // =================================================================
    // STEP 5: Textual Grounding (fetch original Greek/Latin)
    // =================================================================
    let textualGroundings: TextualGrounding[] = [];
    let groundingContext = '';
    try {
      const grounding = await getTextualGroundings(nodeResults, geminiVector, c.env);
      textualGroundings = grounding.groundings;
      groundingContext = grounding.formattedContext;
      logger.info(`Retrieved ${textualGroundings.length} textual groundings`);
    } catch (err) {
      logger.warn('Textual grounding failed', err);
    }

    // =================================================================
    // STEP 6: Build Context
    // =================================================================
    const contextParts: string[] = [];

    // Priority context (explicit passage references)
    if (priorityContext) {
      contextParts.push(priorityContext);
      contextParts.push('');
    }

    // Textual groundings (original Greek/Latin)
    if (groundingContext) {
      contextParts.push(groundingContext);
      contextParts.push('');
    }

    contextParts.push('=== SCHOLARLY CONTEXT FROM KNOWLEDGE GRAPH ===');

    // Add top text results
    for (const result of rerankedResults.slice(0, max_context)) {
      if (!result?.payload) continue;
      const p = result.payload;
      const author = p.author || 'Unknown';
      const work = p.title || 'Unknown';
      const text = p.text_content || p.text_preview || p.description || '';
      contextParts.push(`[Passage] ${author}, ${work}: ${text.slice(0, 500)}`);
    }

    // Add KG nodes
    for (const nodeResult of nodeResults.slice(0, max_context)) {
      if (!nodeResult?.payload) continue;
      const node = nodeResult.payload;
      const name = node.label || node.node_id || 'Unknown';
      const desc = node.description || '';
      contextParts.push(`[Entity] ${name}: ${desc}`);
    }

    // Add relationships from edges
    for (const edge of edgeResults.slice(0, graph_depth * 5)) {
      if (!edge?.payload) continue;
      const { source_id, target_id, relation, description } = edge.payload;
      contextParts.push(
        `[Relationship] ${source_id || 'unknown'} --${relation || 'related'}--> ${target_id || 'unknown'}: ${description || ''}`
      );
    }

    let context = contextParts.join('\n\n');

    // =================================================================
    // STEP 7: CRAG Validation (FAST MODE: skip, THOROUGH MODE: full pipeline)
    // =================================================================
    let cragValidation: any = null;
    let cragTriggeredSecondary = false;

    // Only run CRAG in thorough mode (use_crag must be explicitly true AND mode !== 'fast')
    const shouldRunCRAG = use_crag && mode !== 'fast';

    if (shouldRunCRAG) {
      try {
        // Use simpler validation without full pipeline for speed
        cragValidation = await validateRetrievalSufficiency(query, context, llm);
        cragTriggeredSecondary = cragValidation.needsSecondaryRetrieval;

        // Only trigger secondary retrieval if confidence is very low
        if (cragTriggeredSecondary && cragValidation.confidenceScore < 40) {
          logger.info(`CRAG: low confidence (${cragValidation.confidenceScore}), triggering secondary retrieval`);
          // For speed, skip secondary retrieval and just note it was needed
          cragValidation.secondarySkipped = true;
        } else {
          logger.info(`CRAG: validation passed (confidence: ${cragValidation.confidenceScore})`);
        }
      } catch (err) {
        logger.warn('CRAG validation failed', err);
      }
    }

    // =================================================================
    // STEP 8: Debate Identification
    // =================================================================
    let debatesIdentified: any[] = [];

    if (use_debates) {
      try {
        const debateNodes: DebateNode[] = nodeResults.map(r => ({
          id: r.payload?.node_id || String(r.id),
          label: r.payload?.label || r.payload?.name || 'Unknown',
          type: r.payload?.type || 'concept',
          school: r.payload?.school || r.payload?.metadata?.school,
          period: r.payload?.period,
        }));

        const debateEdges: DebateEdge[] = edgeResults.map(r => ({
          id: r.payload?.edge_id || String(r.id),
          source: r.payload?.source_id || '',
          target: r.payload?.target_id || '',
          relation: r.payload?.relation || '',
        }));

        debatesIdentified = identifyDebates(debateNodes, debateEdges);
        logger.info(`Identified ${debatesIdentified.length} debates`);
      } catch (err) {
        logger.warn('Debate identification failed', err);
      }
    }

    // Add debate context to prompt if debates found
    let debateContext = '';
    if (debatesIdentified.length > 0) {
      debateContext = '\n\n=== PHILOSOPHICAL DEBATES IDENTIFIED ===\n' +
        debatesIdentified.slice(0, 3).map(d => formatDebateForDisplay(d)).join('\n\n');
    }

    // =================================================================
    // STEP 9: LLM Generation
    // =================================================================
    const enhancedPrompt = `You are a scholarly expert on ancient philosophy and free will debates.

Context from knowledge graph:
${context}
${debateContext}

Question: ${query}

${TEXTUAL_GROUNDING_PROMPT}

IMPORTANT: If the user asked about a SPECIFIC passage (like "De Fato 39"), your answer must focus primarily on the EXACT TEXT provided above. Base your analysis on that specific text, not on general knowledge.

Provide a comprehensive, scholarly answer that:
1. Quotes original Greek/Latin texts when available (with translations)
2. Cites specific passages using proper references (Author, Work Section)
3. Preserves key philosophical terminology in the original language
4. Grounds all claims in the textual evidence provided
${debatesIdentified.length > 0 ? '5. Addresses the philosophical debates identified above' : ''}

CRITICAL CITATION RULES:
- When citing ancient sources, use ONLY chapter/section numbers that exist in the original works (e.g., "Dialogue with Trypho 88" or "First Apology 43")
- NEVER confuse page numbers from modern publications (like "pp. 183-188" from scholarly articles) with ancient text section numbers
- Page numbers in parentheses (pp. X) refer to WHERE modern scholars discuss something, NOT the section of the ancient text
- If you see "KEY FINDING (pp. 183-188)" in the context, this means pages 183-188 of a modern publication, NOT section 183 of an ancient work
- For Justin Martyr: First Apology has ~68 chapters, Second Apology has ~15 chapters, Dialogue with Trypho has ~142 chapters`;

    let answer = await llm.generateWithRetry(enhancedPrompt, 'gemini-3-flash-preview');
    if (typeof answer !== 'string') {
      answer = answer?.text || answer?.content || String(answer || '');
    }

    // =================================================================
    // STEP 10: SELF-RAG Evaluation (FAST MODE: simple eval, THOROUGH MODE: full pipeline)
    // =================================================================
    let selfEvaluation: any = null;
    let wasRefined = false;
    const sourceLabels = rerankedResults.slice(0, max_context)
      .map(r => r.payload?.label || r.payload?.author || 'Unknown');

    // Only run SELF-RAG in thorough mode
    const shouldRunSelfRAG = use_selfrag && mode !== 'fast';

    if (shouldRunSelfRAG) {
      try {
        // Use simpler evaluation for speed (no refinement attempt)
        selfEvaluation = await selfEvaluateAnswer(query, answer, sourceLabels.length, sourceLabels, llm);
        logger.info(`SELF-RAG: evaluation complete (confidence: ${selfEvaluation.confidenceScore})`);
      } catch (err) {
        logger.warn('SELF-RAG evaluation failed', err);
      }
    } else if (use_selfrag) {
      // In fast mode, provide a default quality estimate based on source count
      selfEvaluation = {
        relevanceScore: 80,
        groundingScore: Math.min(100, sourceLabels.length * 12),
        completenessScore: 70,
        confidenceScore: 75,
        qualityBadge: sourceLabels.length >= 5 ? 'High' : sourceLabels.length >= 3 ? 'Medium' : 'Low',
        shouldRefine: false,
        caveats: [],
        improvements: [],
        evaluationTime: 0,
      };
      logger.info('SELF-RAG: fast mode, using estimated quality');
    }

    // =================================================================
    // STEP 11: Build Evidence Traces
    // =================================================================
    const evidenceTraces = buildEvidenceTraces(
      rerankedResults.slice(0, max_context).map(r => r.payload || {}),
      searchScores,
      new Map(),  // Graph expansions (would need additional tracking)
      new Map(),  // Community info
      use_hyde,
      use_expansion,
      rerankingApplied ? new Map(rerankedResults.slice(0, max_context).map((r, i) => [String(r.id), 100 - i * 5])) : undefined,
      query
    );

    const evidenceQuality = calculateEvidenceQuality(evidenceTraces.traces);

    // =================================================================
    // STEP 12: Build Response
    // =================================================================
    const processingTime = Date.now() - startTime;

    // Evidence package - combine kg_nodes with text_embeddings (reranked results include passages)
    // Convert rerankedResults to node-like objects for buildEvidencePackage
    const allSourceNodes = [
      ...nodeResults,
      ...rerankedResults.slice(0, max_context).map(r => ({
        ...r,
        payload: r.payload || r,
      })),
    ];
    const evidencePackage = includeEvidence
      ? buildEvidencePackage(answer, allSourceNodes, edgeResults)
      : null;

    // Explicit citations
    const explicitCitations = resolvedPassages.map(p => ({
      citationText: `${p.author}, ${p.workTitle} ${p.section}`,
      passageId: p.passageId,
      workId: p.workId,
      ctsUrn: p.ctsUrn,
      title: p.workTitle,
      author: p.author,
      originalText: p.textContent.substring(0, 500),
      language: p.ctsUrn?.includes('latinLit') ? 'latin' : 'greek',
      reference: p.section,
      confidence: 1.0,
      isExplicitRequest: true,
    }));

    const allCitations = [...explicitCitations, ...(evidencePackage?.ancientCitations || [])];
    const allCtsUrns = [
      ...resolvedPassages.map(p => p.ctsUrn).filter(Boolean),
      ...(evidencePackage?.ctsUrns || []),
      // Include CTS URNs from textual groundings (fetched from PostgreSQL)
      ...textualGroundings.map(g => g.ctsUrn).filter(Boolean),
    ];
    // Deduplicate CTS URNs
    const uniqueCtsUrns = [...new Set(allCtsUrns)];

    // Temporal distribution
    const temporalDistribution: any = {};
    for (const node of nodeResults) {
      const period = node.payload?.period?.toLowerCase().replace(/\s+/g, '_');
      if (period && ['presocratic', 'classical', 'hellenistic', 'imperial', 'late_antiquity'].includes(period)) {
        if (!temporalDistribution[period]) temporalDistribution[period] = [];
        temporalDistribution[period].push(node.payload?.label || 'Unknown');
      }
    }

    return c.json({
      answer,
      sources: sourceLabels,

      // Evidence chains
      evidence: evidencePackage?.evidenceChains || [],
      evidenceChains: evidencePackage?.evidenceChains || [],
      ancientCitations: allCitations,
      modernBibliography: evidencePackage?.modernCitations || [],
      ctsUrns: uniqueCtsUrns,

      // Textual groundings
      textualGroundings: textualGroundings.map(g => ({
        reference: `${g.author}, ${g.reference}`,
        originalText: g.originalText,
        language: g.language === 'grc' ? 'Greek' : 'Latin',
        ctsUrn: g.ctsUrn,
        passageId: g.passageId,
      })),

      // V2 Enhanced fields
      qualityScore: selfEvaluation?.confidenceScore || evidenceQuality.overallScore * 100,
      qualityBadge: selfEvaluation?.qualityBadge || evidenceQuality.badge,
      caveats: selfEvaluation?.caveats || [],
      confidenceExplanation: selfEvaluation ? explainConfidence(selfEvaluation) : evidenceQuality.explanation,

      // Evidence explainability
      evidenceTraces: evidenceTraces.traces,
      evidenceQuality: evidenceQuality,

      // Temporal distribution
      temporalDistribution: Object.keys(temporalDistribution).length > 0 ? temporalDistribution : undefined,

      // Debates
      debatesIdentified: debatesIdentified.map(d => ({
        topic: d.topic,
        description: d.description,
        level: d.score.level,
        schools: d.score.schools,
        keyFigures: d.score.keyFigures,
      })),

      // Retrieval strategy details
      retrievalStrategy: {
        hydeUsed: use_hyde,
        queryExpanded: use_expansion,
        reranked: rerankingApplied,
        cragValidated: use_crag,
        cragTriggeredSecondary,
        selfEvaluated: use_selfrag,
        wasRefined,
      },

      // Query expansion details
      queryExpansion: queryExpansion ? {
        greekTerms: queryExpansion.greekTerms,
        latinTerms: queryExpansion.latinTerms,
        philosophers: queryExpansion.philosophers,
        concepts: queryExpansion.concepts,
      } : undefined,

      // CRAG validation result
      cragValidation: cragValidation ? {
        confidenceScore: cragValidation.confidenceScore,
        needsSecondaryRetrieval: cragValidation.needsSecondaryRetrieval,
        missingAspects: cragValidation.missingAspects,
      } : undefined,

      // SELF-RAG evaluation
      selfEvaluation: selfEvaluation ? {
        relevanceScore: selfEvaluation.relevanceScore,
        groundingScore: selfEvaluation.groundingScore,
        completenessScore: selfEvaluation.completenessScore,
        confidenceScore: selfEvaluation.confidenceScore,
      } : undefined,

      // HyDE details
      hydeDetails: use_hyde && hypotheticalDocument ? {
        hypotheticalDocumentPreview: hypotheticalDocument.slice(0, 300) + '...',
        hydeResultsCount: hydeResults.length,
      } : undefined,

      // Stats
      retrievalStats: {
        totalNodes: nodeResults.length,
        totalEdges: edgeResults.length,
        standardResults: standardResults.length,
        hydeResults: hydeResults.length,
        expandedResults: expandedResults.length,
        fusedCandidates: fusedResults.length,
        finalResults: rerankedResults.slice(0, max_context).length,
        passageNodes: (evidencePackage?.passageCount || 0) + resolvedPassages.length,
        explicitPassages: resolvedPassages.length,
        textualGroundings: textualGroundings.length,
        debatesIdentified: debatesIdentified.length,
      },

      processingTime,
      mode,
      version: 'v2',
      parameters: {
        semantic_k,
        graph_depth,
        max_context,
        use_hyde,
        use_expansion,
        use_reranking,
        use_crag,
        use_selfrag,
        use_debates,
      },
      success: true,
    });
  } catch (error) {
    logger.error('GraphRAG v2 answer error', error);
    return c.json({
      error: 'Query processing failed',
      code: 'GRAPHRAG_V2_ANSWER_ERROR',
      message: error instanceof Error ? error.message : 'Unknown error',
      success: false,
    }, 500);
  }
});
*/
// END ARCHIVED V2

// GraphRAG query endpoint (non-streaming)
graphragRoutes.post('/query',
  authMiddleware,
  rateLimitMiddleware(30, 15), // 30 requests per 15 minutes
  validateGraphRAGInput,
  async (c) => {
    try {
      const body = await c.req.json();
      const {
        query,
        semantic_k = 10,
        graph_depth = 2,
        max_context = 15,
        mode = 'local',
        includeEvidence = true,
        use_dual = true,
      } = body;

      const startTime = Date.now();

      const db = new DatabaseService(c.env);
      const qdrant = new QdrantService(c.env);
      const llm = new LLMService(c.env);
      // Use Gemini embedding for KG node search
      let nodeResults: any[] = [];
      const geminiVector = await llm.embed(query);
      nodeResults = await qdrant.searchWithNamedVector(
        'kg_nodes_dual',
        'gemini',
        geminiVector,
        Math.min(semantic_k, 20)
      );

      // Search KG edges (gracefully handle if collection doesn't exist)
      let edgeResults: any[] = [];
      try {
        edgeResults = await qdrant.searchEdges(
          geminiVector,
          Math.min(semantic_k, 20),
          0.7
        );
      } catch (edgeErr) {
        logger.warn('kg_edges collection not available, skipping edge search', edgeErr);
        // Continue without edges - they're not critical for answer generation
      }

      const dualResults = {
        nodes: nodeResults,
        edges: edgeResults,
        combined: [],
        stats: {
          totalNodes: nodeResults.length,
          totalEdges: edgeResults.length,
        },
      };

      // Get node information from Qdrant payloads (no database query needed)
      const topNodes = (dualResults.nodes || []).slice(0, max_context);

      // Build context from BOTH nodes and edges
      const contextParts: string[] = [];

      // Add nodes (using payload data directly)
      for (const nodeResult of topNodes) {
        if (!nodeResult?.payload) continue;
        const node = nodeResult.payload;
        const name = node.label || node.node_id || 'Unknown';
        const desc = node.description || '';
        contextParts.push(`[Entity] ${name}: ${desc}`);
      }

      // Add relationship information from edges
      for (const edge of (dualResults.edges || []).slice(0, graph_depth * 5)) {
        if (!edge?.payload) continue;
        const { source_id, target_id, relation, description } = edge.payload;
        contextParts.push(
          `[Relationship] ${source_id || 'unknown'} --${relation || 'related'}--> ${target_id || 'unknown'}: ${description || ''}`
        );
      }

      const context = contextParts.join('\n\n');

      // Generate answer using Gemini with retry
      const prompt = `You are a scholarly expert on ancient philosophy and free will debates.

Context from knowledge graph:
${context}

Question: ${query}

Provide a comprehensive answer based on the context above. Be precise and cite specific philosophers or texts when relevant.

CRITICAL CITATION RULES:
- When citing ancient sources, use ONLY chapter/section numbers that exist in the original works
- NEVER confuse page numbers from modern publications (like "pp. 183-188") with ancient text section numbers
- For Justin Martyr: First Apology has ~68 chapters, Dialogue with Trypho has ~142 chapters`;

      const answerResult = await llm.generateWithRetry(prompt, 'gemini-3-flash-preview');
      // Ensure answer is a string
      const answer = typeof answerResult === 'string' ? answerResult : (answerResult?.text || answerResult?.content || String(answerResult || ''));

      const processingTime = Date.now() - startTime;

      // Build evidence package with ancient citations, CTS URNs, and evidence chains
      const evidencePackage = includeEvidence
        ? buildEvidencePackage(answer, dualResults.nodes, dualResults.edges)
        : null;

      // Build properly formatted SourceCitation[] for frontend
      const formattedSources = topNodes
        .filter((nodeResult: any) => nodeResult?.payload)
        .map((nodeResult: any, i: number) => ({
          id: i + 1,
          nodeId: nodeResult.payload.node_id || `source_${i}`,
          nodeLabel: nodeResult.payload.label || nodeResult.payload.node_id || 'Unknown',
          nodeType: nodeResult.payload.type || 'concept',
          content: nodeResult.payload.description || '',
          metadata: {
            school: nodeResult.payload.metadata?.school,
            period: nodeResult.payload.period,
            author: nodeResult.payload.metadata?.author,
          }
        }));

      return c.json({
        answer,
        sources: formattedSources,
        // Enhanced evidence fields
        evidence: evidencePackage?.evidenceChains || [],
        evidenceChains: evidencePackage?.evidenceChains || [],
        ancientCitations: evidencePackage?.ancientCitations || [],
        modernBibliography: evidencePackage?.modernCitations || [],
        ctsUrns: evidencePackage?.ctsUrns || [],
        retrievalStats: {
          ...dualResults.stats,
          passageNodes: evidencePackage?.passageCount || 0,
        },
        processingTime,
        mode,
        retrievalMethod: 'gemini-only + dual-level (nodes + edges)',
        embeddingMode: 'gemini-only',
        models: ['gemini'],
        parameters: {
          semantic_k,
          graph_depth,
          max_context
        },
        success: true,
      });
    } catch (error) {
      logger.error('GraphRAG query error', error);
      return c.json({
        error: 'Query processing failed',
        code: 'GRAPHRAG_QUERY_ERROR',
        success: false,
      }, 500);
    }
  });

// GraphRAG status endpoint
graphragRoutes.get('/status', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const qdrant = new QdrantService(c.env);
    const llm = new LLMService(c.env);

    const [dbHealth, qdrantHealth, llmHealth] = await Promise.all([
      db.healthCheck(),
      qdrant.healthCheck(),
      llm.healthCheck(),
    ]);

    return c.json({
      status: dbHealth && qdrantHealth && llmHealth ? 'healthy' : 'degraded',
      services: {
        database: dbHealth ? 'connected' : 'disconnected',
        qdrant: qdrantHealth ? 'connected' : 'disconnected',
        llm: llmHealth ? 'available' : 'unavailable',
      },
    });
  } catch (error) {
    logger.error('GraphRAG status check error', error);
    return c.json({
      error: 'Status check failed',
      code: 'STATUS_CHECK_ERROR'
    }, 500);
  }
});

// GraphRAG streaming endpoint with Server-Sent Events - SECURED & REAL STREAMING
graphragRoutes.get('/query/stream',
  authMiddleware,
  rateLimitMiddleware(20, 15), // More restrictive for streaming: 20 per 15 min
  validateGraphRAGInput,
  async (c) => {
    const query = c.req.query('query')!; // Validated by middleware
    const semantic_k = Math.min(parseInt(c.req.query('semantic_k') || '10'), 20);
    const graph_depth = Math.min(parseInt(c.req.query('graph_depth') || '2'), 3);
    const max_context = Math.min(parseInt(c.req.query('max_context') || '15'), 25);
    const use_thinking = c.req.query('use_thinking') === 'true';

    // Create SSE stream
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      async start(controller) {
        const sendEvent = (type: string, data: any) => {
          try {
            const message = `data: ${JSON.stringify({ type, data })}\n\n`;
            controller.enqueue(encoder.encode(message));
          } catch (err) {
            logger.error('Error encoding SSE message', err);
          }
        };

        try {
          // Step 1: Initialize services
          sendEvent('status', { message: 'Initializing services...', step: 1, total_steps: 5 });

          const db = new DatabaseService(c.env);
          const qdrant = new QdrantService(c.env);
          const llm = new LLMService(c.env);
          // Step 2: Generate embeddings
          sendEvent('status', { message: 'Generating query embeddings...', step: 2, total_steps: 5 });

          // Use Gemini embedding for KG node search
          let nodeResults: any[] = [];
          const geminiVector = await llm.embed(query);
          nodeResults = await qdrant.searchWithNamedVector(
            'kg_nodes_dual',
            'gemini',
            geminiVector,
            semantic_k
          );

          // Step 3: Search knowledge graph
          sendEvent('status', { message: 'Searching knowledge graph...', step: 3, total_steps: 5 });

          // Search edges using the dual-embedding collection (kg_edges_dual)
          let edgeResults: any[] = [];
          try {
            edgeResults = await qdrant.searchWithNamedVector(
              'kg_edges_dual',
              'gemini',
              geminiVector,
              semantic_k,
              0.7
            );
          } catch (edgeError) {
            logger.warn('Edge search failed (collection may not exist), continuing without edges', edgeError);
          }

          const dualResults = {
            nodes: nodeResults,
            edges: edgeResults,
            combined: [],
            stats: {
              totalNodes: nodeResults.length,
              totalEdges: edgeResults.length,
            },
          };

          sendEvent('nodes', {
            nodes_found: dualResults.nodes.length,
            edges_found: dualResults.edges.length,
            embedding_mode: 'gemini-only'
          });

          // Step 4: Build context
          sendEvent('status', { message: 'Building context...', step: 4, total_steps: 5 });

          const nodeIds = dualResults.nodes.slice(0, max_context).map(r => r.payload.node_id);
          const nodeDetails = await Promise.all(
            nodeIds.map(id => db.getNode(id))
          );

          // Fetch linked passages for these KG nodes
          const passageService = new PassageRetrievalService(c.env);
          const linkedPassages = await passageService.fetchPassagesForNodes(nodeIds, 20);

          const validNodes = nodeDetails.filter(n => n);
          const contextParts: string[] = [];

          // KG entities with numbered source labels
          contextParts.push('=== KNOWLEDGE GRAPH ENTITIES ===');
          validNodes.forEach((node, i) => {
            const nodeName = node.label || node.name || 'Unknown';
            const nodeDesc = typeof node.description === 'string' ? node.description : '';
            const type = node.type || 'concept';
            const school = node.metadata?.school || '';
            const period = node.period || '';
            const meta = [school, period].filter(Boolean).join(', ');
            contextParts.push(`[Source ${i + 1}] [${type}] ${nodeName}${meta ? ` (${meta})` : ''}`);
            if (nodeDesc) contextParts.push(nodeDesc);
            contextParts.push('');
          });

          // Linked passages with numbered source labels (continuing from node count)
          if (linkedPassages.length > 0) {
            contextParts.push('=== PRIMARY ANCIENT SOURCES (from passage_citations database) ===');
            linkedPassages.forEach((p, i) => {
              const ref = p.ctsUrn || p.canonicalRef || '';
              const lang = p.language === 'lat' ? 'Latin' : 'Greek';
              contextParts.push(`[Source ${validNodes.length + i + 1}] [${lang} Source] ${p.author}, ${p.workTitle} (${ref})`);
              contextParts.push(p.textContent);
              contextParts.push('');
            });
          }

          // Edges (not numbered — supplementary context)
          if (dualResults.edges.length > 0) {
            contextParts.push('=== RELATIONSHIPS ===');
            for (const edge of dualResults.edges.slice(0, graph_depth * 5)) {
              const { source_id, target_id, relation, description } = edge.payload;
              const edgeDesc = typeof description === 'string' ? description : '';
              contextParts.push(
                `[Relationship] ${source_id} --${relation}--> ${target_id}: ${edgeDesc}`
              );
            }
          }

          const context = contextParts.join('\n\n');

          // Step 5: Generate answer with REAL STREAMING
          sendEvent('status', { message: 'Generating answer...', step: 5, total_steps: 5 });

          const prompt = `You are a world-class scholar of ancient Greek and Roman philosophy, specializing in debates about fate, free will, and moral responsibility.

=== CONTEXT FROM KNOWLEDGE GRAPH AND ANCIENT TEXT DATABASE ===

${context}

=== END CONTEXT ===

QUESTION: ${query}

INSTRUCTIONS FOR YOUR SCHOLARLY ANSWER:

1. **Quote original Greek/Latin text** directly from the passages provided above. Do NOT fabricate or reconstruct ancient text from memory. Only quote text that appears verbatim in the context above.

2. **Provide translations** in parentheses after each Greek/Latin quotation.

3. **Cite using numbered source references** like [1], [2], [3] corresponding to the [Source N] labels in the context above. Place the citation marker immediately after the relevant claim or quotation. For example: "Chrysippus argues that fate is compatible with moral responsibility [3]."

4. **Use proper philosophical terminology** in the original language when available.

5. **Ground every claim** in the textual evidence provided. If a claim is not supported by the passages above, say so explicitly.

6. **Structure your answer** with clear sections and scholarly formatting.

7. **IMPORTANT:** Every major claim or quotation MUST have a [N] citation marker referencing one of the numbered sources. This enables the reader to click through to the source.

CRITICAL: NEVER fabricate ancient Greek or Latin text. If no relevant passage exists in the context, say so rather than inventing a quotation.`;

          // 🚀 REAL STREAMING - With optional Kimi K2 thinking mode
          let fullAnswer = '';
          let thinkingProcess: string | undefined;
          let chunkCount = 0;

          try {
            // If thinking mode is enabled and Kimi K2 is available, use it
            if (use_thinking && llm.hasThinkingSupport()) {
              sendEvent('status', { message: 'Generating answer with Kimi K2 thinking...', step: 5, total_steps: 6 });

              const thinkingResult = await llm.generateWithThinking(prompt, undefined, true);
              fullAnswer = thinkingResult.response;
              thinkingProcess = thinkingResult.thinkingProcess;

              // Stream thinking process first if available
              if (thinkingProcess) {
                sendEvent('status', { message: 'Streaming thinking process...', step: 5, total_steps: 6 });
                const chunkSize = 100;
                for (let i = 0; i < thinkingProcess.length; i += chunkSize) {
                  const chunk = thinkingProcess.slice(i, i + chunkSize);
                  const progress = Math.min(1.0, (i + chunkSize) / thinkingProcess.length);
                  sendEvent('thinking_chunk', { data: chunk, progress });
                  await new Promise(resolve => setTimeout(resolve, 0)); // Yield control
                }
                sendEvent('thinking_complete', {});
              }

              // Stream the answer word by word
              const words = fullAnswer.split(' ');
              for (let i = 0; i < words.length; i++) {
                sendEvent('answer_chunk', {
                  data: words[i] + ' ',
                  progress: (i + 1) / words.length
                });
                if (i % 5 === 0) {
                  await new Promise(resolve => setTimeout(resolve, 0));
                }
              }
            } else {
              // Standard Gemini streaming
              for await (const chunk of llm.generateStream(prompt, 'gemini-3-flash-preview')) {
                fullAnswer += chunk;
                chunkCount++;

                // Send chunk immediately as it arrives
                sendEvent('answer_chunk', {
                  data: chunk,
                  progress: null // Progressive, not percentage-based
                });

                // Yield control periodically to prevent blocking
                if (chunkCount % 5 === 0) {
                  await new Promise(resolve => setTimeout(resolve, 0));
                }
              }
            }
          } catch (streamError) {
            logger.error('Streaming generation error', streamError);
            throw streamError;
          }

          // Build reasoning_path for frontend visualization
          const startingNodes = validNodes.slice(0, 5).map((node, i) => ({
            id: node.node_id || node.id || `node_${i}`,
            type: node.type || 'Concept',
            label: node.label || node.name || 'Unknown',
            reason: `Semantic similarity match (rank ${i + 1})`
          }));
          const expandedNodes = validNodes.slice(5).map((node, i) => ({
            id: node.node_id || node.id || `expanded_${i}`,
            type: node.type || 'Concept',
            label: node.label || node.name || 'Unknown',
            reason: 'Related through graph traversal'
          }));

          // Build properly formatted SourceCitation[] for frontend
          const formattedSources = [
            // KG nodes first (matching [Source 1]..[N] in context)
            ...validNodes.map((node, i) => ({
              id: i + 1,
              nodeId: node.node_id || node.id || `source_${i}`,
              nodeLabel: node.label || node.name || 'Unknown',
              nodeType: node.type || 'concept',
              content: node.description || '',
              metadata: {
                school: node.metadata?.school,
                period: node.period,
                author: node.metadata?.author,
              }
            })),
            // Linked passages (matching [Source N+1]..[M] in context)
            ...linkedPassages.map((p, i) => ({
              id: validNodes.length + i + 1,
              nodeId: p.passageId,
              nodeLabel: `${p.author}, ${p.workTitle}`,
              nodeType: 'Passage' as string,
              content: p.textContent.slice(0, 500),
              metadata: {
                author: p.author,
                ctsUrn: p.ctsUrn,
                confidence: p.confidence,
              }
            })),
          ];

          // Build evidence package with ancient citations, CTS URNs, and evidence chains
          const evidencePackage = buildEvidencePackage(fullAnswer, dualResults.nodes, dualResults.edges);

          // Send complete result
          sendEvent('complete', {
            query,
            answer: fullAnswer,
            thinking_process: thinkingProcess,  // Include thinking process if available
            sources: formattedSources,
            // Enhanced evidence fields
            evidence: evidencePackage.evidenceChains,
            evidenceChains: evidencePackage.evidenceChains,
            ancientCitations: evidencePackage.ancientCitations,
            modernBibliography: evidencePackage.modernCitations,
            ctsUrns: evidencePackage.ctsUrns,
            nodes_used: validNodes.length,
            edges_traversed: dualResults.edges.length,
            passageNodes: evidencePackage.passageCount,
            reasoning_path: {
              starting_nodes: startingNodes,
              expanded_nodes: expandedNodes,
              total_nodes: validNodes.length
            },
            retrievalMethod: 'gemini-only + dual-level (nodes + edges)',
            embeddingMode: 'gemini-only',
            models: use_thinking && llm.hasThinkingSupport()
              ? ['kimi-k2-thinking']
              : ['gemini'],
            parameters: {
              semantic_k,
              graph_depth,
              max_context,
              use_thinking
            },
            success: true
          });

        } catch (error) {
          logger.error('Streaming GraphRAG error', error);
          sendEvent('error', {
            message: error instanceof Error ? error.message : 'Unknown error',
            code: 'GRAPHRAG_STREAM_ERROR'
          });
        } finally {
          // 🛡️ MEMORY LEAK FIX - Always close controller
          try {
            controller.close();
          } catch (err) {
            logger.warn('Error closing stream controller', err);
          }
        }
      }
    });

    // SSE needs explicit CORS headers; reject cross-origin requests not in allowlist.
    const requestOrigin = c.req.header('Origin') || '';
    const allowOrigin = resolveCorsOrigin(requestOrigin, c.env.ALLOWED_ORIGINS || '*');
    if (requestOrigin && !allowOrigin) {
      return c.json({
        error: 'Origin not allowed',
      }, 403);
    }

    const headers: Record<string, string> = {
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'X-Accel-Buffering': 'no', // Disable nginx buffering
      'Vary': 'Origin',
    };

    if (allowOrigin) {
      headers['Access-Control-Allow-Origin'] = allowOrigin;
      headers['Access-Control-Allow-Credentials'] = 'true';
    }

    return new Response(stream, { headers });
  });

// =============================================================================
// DEFAULT: PageIndex V3 — Direct Agentic Search (2026-02-20)
// =============================================================================
// Simplified pipeline: KG traversal + passage_citations + semantic search.
// ONE retrieval step, ONE synthesis call. No HyDE, CRAG, SELF-RAG, reranking.
// Relies on Gemini's 1M token context to handle FULL passage text.
//
// Philosophy: With 17k passages, 10 LLM calls add noise. 1 good retrieval
// step + 1 good synthesis call with complete context = better quality.
// =============================================================================

/**
 * Helper to determine node type from payload (shared across endpoints)
 */
function determineNodeType(payload: any): string {
  if (payload?.type) return payload.type;
  if (payload?.node_type) return payload.node_type;
  if (payload?.node_id) {
    const prefixes = ['concept', 'argument', 'person', 'work', 'reformulation', 'group', 'school', 'evidence'];
    for (const prefix of prefixes) {
      if (payload.node_id.startsWith(prefix + '_')) {
        return prefix.charAt(0).toUpperCase() + prefix.slice(1);
      }
    }
  }
  if (payload?.author || payload?.work_title || payload?.cts_urn) return 'Passage';
  if (payload?.name || payload?.label) return 'Concept';
  return 'Unknown';
}

graphragRoutes.post('/answer', async (c) => {
  const startTime = Date.now();

  try {
    const body = await c.req.json();
    const {
      query,
      semantic_k = 20,
      graph_depth = 2,
      max_context = 25,
      includeEvidence = true,
    } = body;

    // Validation
    if (!query || typeof query !== 'string' || query.length === 0 || query.length > 2000) {
      return c.json({
        error: 'Invalid input',
        message: 'Query must be a non-empty string (max 2000 characters)',
        success: false,
      }, 400);
    }

    const qdrant = new QdrantService(c.env);
    const llm = new LLMService(c.env);

    logger.info(`PageIndex V3: query="${query.slice(0, 80)}..."`);

    // =================================================================
    // STEP 1: PARALLEL — Embedding + Passage Reference Detection
    // =================================================================
    const passageRefs = detectPassageReferences(query);

    const [
      geminiVector,
      resolvedPassages,
    ] = await Promise.all([
      llm.embed(query),
      resolvePassageReferences(passageRefs, c.env),
    ]);

    const priorityContext = buildPassageContext(resolvedPassages);

    if (resolvedPassages.length > 0) {
      logger.info(`Resolved ${resolvedPassages.length} explicit passage references`);
    }

    // =================================================================
    // STEP 2: PARALLEL — KG Node Search + Text Passage Search + Edge Search
    // Single round of vector search — no HyDE, no expansion, no reranking
    // =================================================================
    const [
      nodeResults,
      textResults,
      edgeResults,
    ] = await Promise.all([
      qdrant.searchWithNamedVector('kg_nodes_dual', 'gemini', geminiVector, semantic_k, 0.4),
      qdrant.searchTexts(geminiVector, semantic_k * 2, undefined, 0.45),
      qdrant.searchEdges(geminiVector, Math.min(semantic_k, 15), 0.6).catch(() => []),
    ]);

    logger.info(`Search results: ${nodeResults.length} nodes, ${textResults.length} passages, ${edgeResults.length} edges`);

    // =================================================================
    // STEP 3: PARALLEL — Linked Passages (passage_citations) + Neighbors
    // This is the PageIndex core: use the KG structure to find passages
    // =================================================================
    const seedNodeIds = nodeResults
      .slice(0, max_context)
      .map(r => r.payload?.node_id)
      .filter(Boolean) as string[];

    const [
      linkedPassages,
      neighbors,
      textualGroundings,
    ] = await Promise.all([
      getLinkedPassages(seedNodeIds, c.env),
      getNodeNeighbors(seedNodeIds, c.env),
      getTextualGroundings(nodeResults, geminiVector, c.env).catch(err => {
        logger.warn('Textual grounding failed', err);
        return { groundings: [] as TextualGrounding[], formattedContext: '' };
      }),
    ]);

    // Also get linked passages for neighbor nodes (1-hop expansion)
    const neighborNodeIds = neighbors.map(n => n.nodeId);
    let neighborLinkedPassages: Awaited<ReturnType<typeof getLinkedPassages>> = [];
    if (neighborNodeIds.length > 0) {
      neighborLinkedPassages = await getLinkedPassages(neighborNodeIds, c.env);
    }

    // Merge and deduplicate linked passages
    const allLinkedPassages = [...linkedPassages];
    const seenPassageIds = new Set(linkedPassages.map(p => p.passageId));
    for (const p of neighborLinkedPassages) {
      if (!seenPassageIds.has(p.passageId)) {
        seenPassageIds.add(p.passageId);
        allLinkedPassages.push(p);
      }
    }

    logger.info(`PageIndex: ${allLinkedPassages.length} linked passages (${linkedPassages.length} direct + ${neighborLinkedPassages.length} via neighbors), ${neighbors.length} KG neighbors`);

    // =================================================================
    // STEP 4: Build FULL Context — NO TRUNCATION
    // Gemini has ~1M tokens. Our entire corpus is ~3.4M tokens.
    // We can easily fit 100+ full passages in context.
    // =================================================================
    const contextParts: string[] = [];

    // Priority: explicit passage references (user asked for specific text)
    if (priorityContext) {
      contextParts.push(priorityContext);
      contextParts.push('');
    }

    // Textual groundings (original Greek/Latin from PostgreSQL)
    if (textualGroundings.formattedContext) {
      contextParts.push(textualGroundings.formattedContext);
      contextParts.push('');
    }

    // PageIndex context (full passages, full descriptions, full relationships)
    const pageIndexContext = buildPageIndexContext(
      nodeResults.slice(0, max_context),
      neighbors,
      allLinkedPassages,
      textResults.slice(0, max_context),
      edgeResults.slice(0, graph_depth * 5),
    );
    contextParts.push(pageIndexContext);

    const context = contextParts.join('\n');

    // Log context size for monitoring
    logger.info(`Context size: ${context.length} chars (~${Math.round(context.length / 4)} tokens)`);

    // =================================================================
    // STEP 5: ONE Synthesis Call — Strong scholarly prompt
    // This is the only LLM generation call (besides embedding)
    // =================================================================
    const synthesisPrompt = `You are a world-class scholar of ancient Greek and Roman philosophy, specializing in debates about fate, free will (αὐτεξούσιον / liberum arbitrium), and moral responsibility from the 6th century BCE to the 6th century CE.

You have access to a curated database of ${allLinkedPassages.length + textResults.length} passages from ancient sources and ${nodeResults.length + neighbors.length} knowledge graph entities about ancient philosophical debates on free will.

=== CONTEXT FROM KNOWLEDGE GRAPH AND ANCIENT TEXT DATABASE ===

${context}

=== END CONTEXT ===

QUESTION: ${query}

INSTRUCTIONS FOR YOUR SCHOLARLY ANSWER:

1. **Quote original Greek/Latin text** directly from the passages provided above. Do NOT fabricate or reconstruct ancient text from memory. Only quote text that appears verbatim in the context above.

2. **Provide translations** in parentheses after each Greek/Latin quotation.

3. **Cite using numbered source references** like [1], [2], [3] corresponding to the [Source N] labels in the context above. Place the citation marker immediately after the relevant claim or quotation. For example: "Chrysippus argues that fate is compatible with moral responsibility [3]." Use ONLY source numbers that exist in the context above.

4. **Use proper philosophical terminology** in the original language: αὐτεξούσιον (self-determination), εἱμαρμένη (fate), liberum arbitrium (free choice), etc.

5. **Ground every claim** in the textual evidence provided. If a claim is not supported by the passages above, say so explicitly.

6. **Distinguish clearly** between:
   - What the ancient sources actually say (quote them)
   - How modern scholars interpret them (cite the scholar)
   - Your own analytical synthesis

7. **Structure your answer** with clear sections, markdown headers, and scholarly formatting.

8. **IMPORTANT:** Every major claim or quotation MUST have a [N] citation marker referencing one of the numbered sources. This enables the reader to click through to the source.

CRITICAL: NEVER fabricate ancient Greek or Latin text. If no relevant passage exists in the context, say "No passage in the database directly addresses this" rather than inventing a quotation.`;

    let answer = await llm.generateWithRetry(synthesisPrompt, 'gemini-3-flash-preview');
    if (typeof answer !== 'string') {
      answer = (answer as any)?.text || (answer as any)?.content || String(answer || '');
    }

    // =================================================================
    // STEP 6: Build Response (frontend-compatible structure)
    // =================================================================
    const processingTime = Date.now() - startTime;

    // Build evidence package
    const allSourceNodes = [
      ...nodeResults,
      ...textResults.slice(0, max_context).map(r => ({ ...r, payload: r.payload || r })),
    ];
    const evidencePackage = includeEvidence
      ? buildEvidencePackage(answer, allSourceNodes, edgeResults)
      : null;

    // Structured sources for frontend
    const structuredSources = [
      // KG nodes
      ...nodeResults.slice(0, max_context).map((r, i) => ({
        id: i + 1,
        nodeId: r.payload?.node_id || `node_${i}`,
        nodeLabel: r.payload?.label || r.payload?.node_id || 'Unknown',
        nodeType: determineNodeType(r.payload),
        content: r.payload?.description || '',
        metadata: {
          school: r.payload?.metadata?.school || r.payload?.school,
          period: r.payload?.period,
          author: r.payload?.metadata?.author,
          confidence: r.score || undefined,
        },
      })),
      // Linked passages as sources
      ...allLinkedPassages.slice(0, 20).map((p, i) => ({
        id: nodeResults.length + i + 1,
        nodeId: p.passageId,
        nodeLabel: `${p.author}, ${p.workTitle}`,
        nodeType: 'Passage' as string,
        content: p.textContent.slice(0, 500),
        metadata: {
          author: p.author,
          ctsUrn: p.ctsUrn,
          confidence: p.confidence,
        },
      })),
    ];

    // Explicit citations from passage references
    const explicitCitations = resolvedPassages.map(p => ({
      citationText: `${p.author}, ${p.workTitle} ${p.section}`,
      passageId: p.passageId,
      workId: p.workId,
      ctsUrn: p.ctsUrn,
      title: p.workTitle,
      author: p.author,
      originalText: p.textContent,
      language: p.ctsUrn?.includes('latinLit') ? 'latin' : 'greek',
      reference: p.section,
      confidence: 1.0,
      isExplicitRequest: true,
    }));

    const allCitations = [...explicitCitations, ...(evidencePackage?.ancientCitations || [])];
    const allCtsUrns = [
      ...resolvedPassages.map(p => p.ctsUrn).filter(Boolean),
      ...(evidencePackage?.ctsUrns || []),
      ...textualGroundings.groundings.map(g => g.ctsUrn).filter(Boolean),
      ...allLinkedPassages.map(p => p.ctsUrn).filter(Boolean),
    ];
    const uniqueCtsUrns = [...new Set(allCtsUrns)];

    return c.json({
      answer,
      sources: structuredSources,

      // Evidence chains
      evidence: evidencePackage?.evidenceChains || [],
      evidenceChains: evidencePackage?.evidenceChains || [],
      ancientCitations: allCitations,
      modernBibliography: evidencePackage?.modernCitations || [],
      ctsUrns: uniqueCtsUrns,

      // Textual groundings
      textualGroundings: textualGroundings.groundings.map(g => ({
        reference: `${g.author}, ${g.reference}`,
        originalText: g.originalText,
        language: g.language === 'grc' ? 'Greek' : 'Latin',
        ctsUrn: g.ctsUrn,
        passageId: g.passageId,
      })),

      // Quality (computed from source counts — no extra LLM call)
      qualityScore: Math.min(100, 50 + allLinkedPassages.length * 5 + textualGroundings.groundings.length * 8),
      qualityBadge: allLinkedPassages.length >= 5 ? 'High' : allLinkedPassages.length >= 2 ? 'Medium' : 'Low',

      // PageIndex-specific info
      pageIndexInfo: {
        linkedPassages: allLinkedPassages.length,
        directPassages: linkedPassages.length,
        neighborPassages: neighborLinkedPassages.length,
        kgNeighbors: neighbors.length,
        seedNodes: seedNodeIds.length,
        contextChars: context.length,
        contextTokensEstimate: Math.round(context.length / 4),
      },

      // Stats (frontend-compatible)
      retrievalStats: {
        totalNodes: nodeResults.length,
        totalEdges: edgeResults.length,
        standardResults: textResults.length,
        passageNodes: allLinkedPassages.length + resolvedPassages.length,
        explicitPassages: resolvedPassages.length,
        textualGroundings: textualGroundings.groundings.length,
      },

      processingTime,
      version: 'pageindex-v3',
      parameters: {
        semantic_k,
        graph_depth,
        max_context,
      },
      success: true,
    });
  } catch (error) {
    logger.error('PageIndex V3 answer error', error);
    return c.json({
      error: 'Query processing failed',
      code: 'PAGEINDEX_V3_ANSWER_ERROR',
      message: error instanceof Error ? error.message : 'Unknown error',
      success: false,
    }, 500);
  }
});

// =============================================================================
// BACKWARD COMPATIBILITY: /answer/v2 still available for A/B testing
// =============================================================================
graphragRoutes.post('/answer/hirag-v2', async (c) => {
  // Forward to main /answer handler (now PageIndex V3)
  const response = await graphragRoutes.fetch(
    new Request(new URL('/answer', c.req.url).toString(), {
      method: 'POST',
      headers: c.req.raw.headers,
      body: JSON.stringify(await c.req.json()),
    }),
    c.env as any
  );
  return response;
});

graphragRoutes.post('/answer/v2', async (c) => {
  const response = await graphragRoutes.fetch(
    new Request(new URL('/answer', c.req.url).toString(), {
      method: 'POST',
      headers: c.req.raw.headers,
      body: JSON.stringify(await c.req.json()),
    }),
    c.env as any
  );
  return response;
});
