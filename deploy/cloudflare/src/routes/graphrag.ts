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

// 2025 Advanced RAG Services
import { hydeSearch, hydeEnhancedSearch, generateHypotheticalDocument } from '../services/hyde';
import { expandPhilologicalQuery, quickExpand, expandedSearch } from '../services/query-expander';
import { llmRerank, scholarlyRerank, RerankCandidate } from '../services/reranker';
import { validateRetrievalSufficiency, cragPipeline } from '../services/crag';
import { selfEvaluateAnswer, selfRAGPipeline, explainConfidence } from '../services/self-rag';
import { identifyDebates, scoreDebateIntensity, formatDebateForDisplay, DebateNode, DebateEdge } from '../services/debate-scorer';
import { buildEvidenceTraces, calculateEvidenceQuality } from '../services/evidence-tracer';
import { HierarchicalRetrievalService } from '../services/hierarchical-retrieval';

const logger = getLogger('GraphRAGRoutes');

export const graphragRoutes = new Hono<{ Bindings: Env }>();

// =============================================================================
// ARCHIVED: Legacy V1 Endpoint (Replaced by HiRAG V2 on 2025-12-31)
// =============================================================================
// The legacy /answer endpoint has been replaced by HiRAG V2 which provides:
// - +4.4 points better quality composite score
// - +27% more Greek text in answers
// - Rule-based query classification (multi_hop, comparative, temporal, etc.)
// - Bridge mode for multi-hop reasoning (+5.8 points improvement)
// - Hierarchical community context
// =============================================================================

/*
// ARCHIVED: GraphRAG /answer endpoint (for frontend compatibility)
graphragRoutes.post('/answer/legacy-v1', async (c) => {
    try {
      const body = await c.req.json();
      const {
        query,
        semantic_k = 10,
        graph_depth = 2,
        max_context = 15,
        mode = 'local',
        includeEvidence = true,
        enhanced_mode = true, // Support enhanced mode parameter from frontend
        use_dual = true, // Enable dual-embedding by default
      } = body;

      // Inline validation
      if (!query || typeof query !== 'string' || query.length === 0 || query.length > 1000) {
        return c.json({
          error: 'Invalid input',
          message: 'Query must be a non-empty string (max 1000 characters)',
          success: false,
        }, 400);
      }

      const startTime = Date.now();

      const db = new DatabaseService(c.env);
      const qdrant = new QdrantService(c.env);
      const llm = new LLMService(c.env);
      const sphilberta = new SPhilBERTaService(c.env);

      // PRIORITY: Detect and resolve explicit passage references FIRST
      // When user asks about "De Fato 39", we should retrieve that EXACT passage
      const passageRefs = detectPassageReferences(query);
      const resolvedPassages = await resolvePassageReferences(passageRefs, c.env);
      const priorityContext = buildPassageContext(resolvedPassages);

      if (resolvedPassages.length > 0) {
        logger.info(`Resolved ${resolvedPassages.length} explicit passage references`, {
          passages: resolvedPassages.map(p => p.ctsUrn),
        });
      }

      // Try dual-embedding search for KG nodes
      let nodeResults: any[] = [];
      let usedDualEmbedding = false;

      if (use_dual) {
        try {
          const sphilbertaAvailable = await sphilberta.isAvailable();

          if (sphilbertaAvailable) {
            logger.info('GraphRAG using dual-embedding for KG node search');

            const [sphilbertaVector, geminiVector] = await Promise.all([
              sphilberta.embed(query),
              llm.embed(query),
            ]);

            if (sphilbertaVector) {
              nodeResults = await qdrant.searchDualEmbedding(
                'kg_nodes_dual',
                sphilbertaVector,
                geminiVector,
                Math.min(semantic_k, 20)
              );
              usedDualEmbedding = true;
            }
          }
        } catch (dualError) {
          logger.warn('Dual-embedding failed for GraphRAG, falling back to Gemini-only', dualError);
        }
      }

      // Fallback to Gemini-only if dual-embedding didn't work
      let geminiVector: number[];
      if (!usedDualEmbedding) {
        logger.info('GraphRAG using Gemini-only fallback');
        geminiVector = await llm.embed(query);
        nodeResults = await qdrant.searchWithNamedVector(
          'kg_nodes_dual',
          'gemini',
          geminiVector,
          Math.min(semantic_k, 20)
        );
      } else {
        // Still need geminiVector for edge search
        geminiVector = await llm.embed(query);
      }

      // Also search KG edges for relationship-aware retrieval
      const edgeResults = await qdrant.searchWithNamedVector(
        'kg_edges_dual',
        'gemini',
        geminiVector,
        Math.min(semantic_k, 20),
        0.7
      );

      const dualResults = {
        nodes: nodeResults,
        edges: edgeResults,
        combined: [], // Will be populated below
        stats: {
          totalNodes: nodeResults.length,
          totalEdges: edgeResults.length,
        },
      };

      // Get node information from Qdrant payloads (no database query needed)
      const topNodes = (dualResults.nodes || []).slice(0, max_context);

      // TEXTUAL GROUNDING: Fetch actual passage texts for scholarly citation
      let textualGroundings: TextualGrounding[] = [];
      let groundingContext = '';
      try {
        const grounding = await getTextualGroundings(
          dualResults.nodes,
          geminiVector!,
          c.env
        );
        textualGroundings = grounding.groundings;
        groundingContext = grounding.formattedContext;
        if (textualGroundings.length > 0) {
          logger.info(`Retrieved ${textualGroundings.length} textual groundings for scholarly citation`);
        }
      } catch (groundingError) {
        logger.warn('Textual grounding retrieval failed, continuing without', groundingError);
      }

      // Build context from BOTH nodes and edges
      const contextParts: string[] = [];

      // PRIORITY CONTEXT: Add explicitly requested passages FIRST
      if (priorityContext) {
        contextParts.push(priorityContext);
        contextParts.push(''); // Empty line separator
      }

      // Add textual groundings (original Greek/Latin texts)
      if (groundingContext) {
        contextParts.push(groundingContext);
        contextParts.push(''); // Empty line separator
      }

      contextParts.push('=== SCHOLARLY CONTEXT FROM KNOWLEDGE GRAPH ===');

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

      // Generate answer using Gemini with retry - enhanced prompt for textual grounding
      const prompt = `You are a scholarly expert on ancient philosophy and free will debates.

Context from knowledge graph:
${context}

Question: ${query}

${TEXTUAL_GROUNDING_PROMPT}

IMPORTANT: If the user asked about a SPECIFIC passage (like "De Fato 39"), your answer must focus primarily on the EXACT TEXT provided above. Base your analysis on that specific text, not on general knowledge.

Provide a comprehensive, scholarly answer that:
1. Quotes original Greek/Latin texts when available (with translations)
2. Cites specific passages using proper references (Author, Work Section)
3. Preserves key philosophical terminology in the original language
4. Grounds all claims in the textual evidence provided

CRITICAL CITATION RULES:
- When citing ancient sources, use ONLY chapter/section numbers that exist in the original works (e.g., "Dialogue with Trypho 88" or "First Apology 43")
- NEVER confuse page numbers from modern publications (like "pp. 183-188" from scholarly articles) with ancient text section numbers
- Page numbers in parentheses (pp. X) refer to WHERE modern scholars discuss something, NOT the section of the ancient text
- For Justin Martyr: First Apology has ~68 chapters, Second Apology has ~15 chapters, Dialogue with Trypho has ~142 chapters`;

      const answerResult = await llm.generateWithRetry(prompt, 'gemini-3-flash-preview');
      // Ensure answer is a string
      const answer = typeof answerResult === 'string' ? answerResult : (answerResult?.text || answerResult?.content || String(answerResult || ''));

      const processingTime = Date.now() - startTime;

      // Build evidence package with ancient citations, CTS URNs, and evidence chains
      const evidencePackage = includeEvidence
        ? buildEvidencePackage(answer, dualResults.nodes, dualResults.edges)
        : null;

      // Build explicit passage citations (these are PRIORITY - user explicitly requested them)
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
        confidence: 1.0, // Explicit reference = highest confidence
        isExplicitRequest: true, // Flag to indicate this was explicitly requested
      }));

      // Combine explicit + evidence package citations (explicit first)
      const allCitations = [...explicitCitations, ...(evidencePackage?.ancientCitations || [])];
      const allCtsUrns = [
        ...resolvedPassages.map(p => p.ctsUrn).filter(Boolean),
        ...(evidencePackage?.ctsUrns || []),
      ];

      // Build sources list (explicit passages first, then semantic results)
      const explicitSources = resolvedPassages.map(p =>
        `${p.author}, ${p.workTitle} ${p.section} [EXPLICITLY REQUESTED]`
      );
      const semanticSources = topNodes
        .filter(r => r?.payload)
        .map(r => r.payload.label || r.payload.node_id || 'Unknown');
      const sources = [...explicitSources, ...semanticSources];

      return c.json({
        answer,
        sources,
        // Enhanced evidence fields
        evidence: evidencePackage?.evidenceChains || [],
        evidenceChains: evidencePackage?.evidenceChains || [],
        ancientCitations: allCitations,
        modernBibliography: evidencePackage?.modernCitations || [],
        ctsUrns: allCtsUrns,
        // NEW: Textual groundings with original Greek/Latin texts
        textualGroundings: textualGroundings.map(g => ({
          reference: `${g.author}, ${g.reference}`,
          originalText: g.originalText,
          language: g.language === 'grc' ? 'Greek' : 'Latin',
          ctsUrn: g.ctsUrn,
          passageId: g.passageId,
        })),
        explicitPassagesResolved: resolvedPassages.length,
        retrievalStats: {
          ...dualResults.stats,
          passageNodes: (evidencePackage?.passageCount || 0) + resolvedPassages.length,
          explicitPassages: resolvedPassages.length,
          textualGroundings: textualGroundings.length,
        },
        processingTime,
        mode,
        enhanced_mode,
        retrievalMethod: usedDualEmbedding
          ? 'dual-embedding + dual-level (nodes + edges with RRF)'
          : 'gemini-only + dual-level (nodes + edges)',
        embeddingMode: usedDualEmbedding ? 'dual-embedding-rrf' : 'gemini-only',
        models: usedDualEmbedding ? ['sphilberta', 'gemini'] : ['gemini'],
        parameters: {
          semantic_k,
          graph_depth,
          max_context
        },
        success: true,
      });
    } catch (error) {
      logger.error('GraphRAG answer error', error);
      return c.json({
        error: 'Query processing failed',
        code: 'GRAPHRAG_ANSWER_ERROR',
        success: false,
      }, 500);
    }
  });
*/
// END ARCHIVED V1

// =============================================================================
// ARCHIVED: V2 Endpoint (Replaced by HiRAG V2 on 2025-12-31)
// =============================================================================
// V2 features are now included in HiRAG V2:
// - HyDE (Hypothetical Document Embeddings)
// - Query Expansion with Greek/Latin terms
// - LLM Reranking
// - CRAG (Corrective RAG) validation
// - SELF-RAG evaluation
// - Debate scoring
// All these features are now combined with HiRAG's hierarchical retrieval
// =============================================================================

/*
// ARCHIVED: GraphRAG /answer/v2 endpoint - Enhanced with HyDE, CRAG, SELF-RAG, and more
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
      const sphilberta = new SPhilBERTaService(c.env);

      // Try dual-embedding search for KG nodes
      let nodeResults: any[] = [];
      let usedDualEmbedding = false;

      if (use_dual) {
        try {
          const sphilbertaAvailable = await sphilberta.isAvailable();

          if (sphilbertaAvailable) {
            logger.info('GraphRAG /query using dual-embedding');

            const [sphilbertaVector, geminiVector] = await Promise.all([
              sphilberta.embed(query),
              llm.embed(query),
            ]);

            if (sphilbertaVector) {
              nodeResults = await qdrant.searchDualEmbedding(
                'kg_nodes_dual',
                sphilbertaVector,
                geminiVector,
                Math.min(semantic_k, 20)
              );
              usedDualEmbedding = true;
            }
          }
        } catch (dualError) {
          logger.warn('Dual-embedding failed, falling back', dualError);
        }
      }

      // Fallback to Gemini-only
      let geminiVector: number[];
      if (!usedDualEmbedding) {
        geminiVector = await llm.embed(query);
        nodeResults = await qdrant.searchWithNamedVector(
          'kg_nodes_dual',
          'gemini',
          geminiVector,
          Math.min(semantic_k, 20)
        );
      } else {
        geminiVector = await llm.embed(query);
      }

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
        retrievalMethod: usedDualEmbedding
          ? 'dual-embedding + dual-level (nodes + edges with RRF)'
          : 'gemini-only + dual-level (nodes + edges)',
        embeddingMode: usedDualEmbedding ? 'dual-embedding-rrf' : 'gemini-only',
        models: usedDualEmbedding ? ['sphilberta', 'gemini'] : ['gemini'],
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
          const sphilberta = new SPhilBERTaService(c.env);

          // Step 2: Generate embeddings (try dual-embedding)
          sendEvent('status', { message: 'Generating query embeddings...', step: 2, total_steps: 5 });

          let nodeResults: any[] = [];
          let usedDualEmbedding = false;

          try {
            const sphilbertaAvailable = await sphilberta.isAvailable();

            if (sphilbertaAvailable) {
              const [sphilbertaVector, geminiVector] = await Promise.all([
                sphilberta.embed(query),
                llm.embed(query),
              ]);

              if (sphilbertaVector) {
                nodeResults = await qdrant.searchDualEmbedding(
                  'kg_nodes_dual',
                  sphilbertaVector,
                  geminiVector,
                  semantic_k
                );
                usedDualEmbedding = true;
              }
            }
          } catch (dualError) {
            logger.warn('Streaming dual-embedding failed', dualError);
          }

          // Fallback to Gemini-only
          let geminiVector: number[];
          if (!usedDualEmbedding) {
            geminiVector = await llm.embed(query);
            nodeResults = await qdrant.searchWithNamedVector(
              'kg_nodes_dual',
              'gemini',
              geminiVector,
              semantic_k
            );
          } else {
            geminiVector = await llm.embed(query);
          }

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
            embedding_mode: usedDualEmbedding ? 'dual-embedding-rrf' : 'gemini-only'
          });

          // Step 4: Build context
          sendEvent('status', { message: 'Building context...', step: 4, total_steps: 5 });

          const nodeIds = dualResults.nodes.slice(0, max_context).map(r => r.payload.node_id);
          const nodeDetails = await Promise.all(
            nodeIds.map(id => db.getNode(id))
          );

          const contextParts = [];
          for (const node of nodeDetails.filter(n => n)) {
            const nodeName = node.label || node.name || 'Unknown';
            const nodeDesc = typeof node.description === 'string' ? node.description : '';
            contextParts.push(`[Entity] ${nodeName}: ${nodeDesc}`);
          }

          for (const edge of dualResults.edges.slice(0, graph_depth * 5)) {
            const { source_id, target_id, relation, description } = edge.payload;
            const edgeDesc = typeof description === 'string' ? description : '';
            contextParts.push(
              `[Relationship] ${source_id} --${relation}--> ${target_id}: ${edgeDesc}`
            );
          }

          const context = contextParts.join('\n\n');

          // Step 5: Generate answer with REAL STREAMING
          sendEvent('status', { message: 'Generating answer...', step: 5, total_steps: 5 });

          const prompt = `You are a scholarly expert on ancient philosophy and free will debates.

Context from knowledge graph:
${context}

Question: ${query}

Provide a comprehensive answer based on the context above. Be precise and cite specific philosophers or texts when relevant.

CRITICAL CITATION RULES:
- When citing ancient sources, use ONLY chapter/section numbers that exist in the original works
- NEVER confuse page numbers from modern publications (like "pp. 183-188") with ancient text section numbers
- For Justin Martyr: First Apology has ~68 chapters, Dialogue with Trypho has ~142 chapters`;

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
          const validNodes = nodeDetails.filter(n => n);
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
          const formattedSources = validNodes.map((node, i) => ({
            id: i + 1,  // Citation number [1], [2], etc.
            nodeId: node.node_id || node.id || `source_${i}`,
            nodeLabel: node.label || node.name || 'Unknown',
            nodeType: node.type || 'concept',
            content: node.description || '',
            metadata: {
              school: node.metadata?.school,
              period: node.period,
              author: node.metadata?.author,
            }
          }));

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
            retrievalMethod: usedDualEmbedding
              ? 'dual-embedding + dual-level (nodes + edges with RRF)'
              : 'gemini-only + dual-level (nodes + edges)',
            embeddingMode: usedDualEmbedding ? 'dual-embedding-rrf' : 'gemini-only',
            models: use_thinking && llm.hasThinkingSupport()
              ? ['kimi-k2-thinking']
              : (usedDualEmbedding ? ['sphilberta', 'gemini'] : ['gemini']),
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
      'Content-Type': 'text/event-stream',
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
// DEFAULT: HiRAG V2 - Production GraphRAG Endpoint (2025-12-31)
// =============================================================================
// This is the primary /answer endpoint, combining HiRAG + V2 enhancements.
// Benchmark results (vs legacy V1):
// - +4.4 points composite quality score
// - +27% more Greek text in answers
// - 3/3 multi-hop queries used bridge mode
// - Wins 5/6 query type categories
// =============================================================================

/**
 * GraphRAG /answer endpoint - HiRAG V2 (DEFAULT)
 *
 * HiRAG Features:
 * - Rule-based query classification (multi_hop, comparative, temporal, etc.)
 * - Hierarchical community-based retrieval
 * - Bridge mode for multi-hop reasoning (+5.8 points improvement)
 * - 250× token reduction on global questions
 *
 * V2 Features:
 * - HyDE (hypothetical document embeddings)
 * - Query expansion with Greek/Latin terms
 * - LLM reranking
 * - CRAG validation
 * - SELF-RAG evaluation
 * - Debate identification
 *
 * Quality: 80.6/100 composite score (vs 76.2 legacy V1)
 */
graphragRoutes.post('/answer', async (c) => {
  const startTime = Date.now();

  try {
    const body = await c.req.json();
    const {
      query,
      semantic_k = 15,
      graph_depth = 2,
      max_context = 15,
      mode = 'auto',  // auto, local, global, bridge
      includeEvidence = true,
      // V2 Enhancement options
      use_hyde = true,
      use_expansion = true,
      use_reranking = true,
      use_crag = true,
      use_selfrag = true,
      use_debates = true,
      // HiRAG-specific options
      use_hierarchy = true,  // Enable hierarchical retrieval
      use_bridge = true,     // Enable bridge mode for multi-hop
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
    const hierarchical = new HierarchicalRetrievalService(c.env);

    logger.info(`HiRAG V2 starting: query="${query.slice(0, 50)}...", mode=${mode}, hierarchy=${use_hierarchy}`);

    // =================================================================
    // STEP 1: HiRAG Query Classification & Strategy Selection
    // =================================================================
    let classification: any = null;
    let strategy: any = null;
    let hierarchicalContext = '';
    let bridgeContext: any = null;

    if (use_hierarchy) {
      try {
        // Only pass mode to HiRAG if it's a valid query type mode (not speed modes like 'fast'/'comprehensive')
        const validHiragModes = ['local', 'global', 'bridge', 'multi_hop', 'full'];
        const hiragMode = validHiragModes.includes(mode) ? mode : undefined;
        const hiragResult = await hierarchical.retrieve(query, hiragMode);
        classification = hiragResult.classification;
        strategy = hiragResult.strategy;

        // Build hierarchical context from community summaries
        if (hiragResult.communities.length > 0) {
          hierarchicalContext = '\n=== HIERARCHICAL CONTEXT (COMMUNITY SUMMARIES) ===\n' +
            hiragResult.communities.map(c => {
              const header = `[${c.dominant_school || 'Mixed'} - ${c.dominant_period || 'Various periods'}]`;
              return `${header}\n${c.summary}`;
            }).join('\n\n---\n\n');
        }

        // If bridge mode was used, include bridge context
        if (hiragResult.bridgeContext) {
          bridgeContext = hiragResult.bridgeContext;
          hierarchicalContext += '\n\n=== BRIDGE PATHS (MULTI-HOP REASONING) ===\n';
          for (const path of bridgeContext.paths) {
            const pathDesc = path.nodes.map((n: any) => n.label).join(' → ');
            hierarchicalContext += `\nPath: ${pathDesc}\n${path.reasoning || ''}\n`;
          }
          if (bridgeContext.bridgingConcepts.length > 0) {
            hierarchicalContext += `\nKey Bridging Concepts: ${bridgeContext.bridgingConcepts.join(', ')}\n`;
          }
        }

        logger.info(`HiRAG classification: ${classification.type} (confidence: ${classification.confidence}), ` +
          `strategy: L${strategy.startLevel}, communities: ${hiragResult.communities.length}`);
      } catch (hiragErr) {
        logger.warn('HiRAG retrieval failed, falling back to V2-only', hiragErr);
      }
    }

    // =================================================================
    // STEP 2: Priority Passage References (same as V2)
    // =================================================================
    const passageRefs = detectPassageReferences(query);
    const resolvedPassages = await resolvePassageReferences(passageRefs, c.env);
    const priorityContext = buildPassageContext(resolvedPassages);

    if (resolvedPassages.length > 0) {
      logger.info(`Resolved ${resolvedPassages.length} explicit passage references`);
    }

    // =================================================================
    // STEP 3: Parallel V2 Retrieval (HyDE, Expansion, etc.)
    // Adjust strategy based on HiRAG classification
    // =================================================================
    let adjustedSemanticK = semantic_k;

    // For global/abstract queries, rely more on hierarchical context
    if (classification?.type === 'global_abstract') {
      adjustedSemanticK = Math.floor(semantic_k * 0.7); // Reduce passage search
    }
    // For specific entity queries, boost passage search
    else if (classification?.type === 'specific_entity') {
      adjustedSemanticK = Math.floor(semantic_k * 1.3); // More passages
    }

    // Batch 1: Embeddings + Expansion + HyDE hypothesis
    const [
      geminiVector,
      queryExpansionResult,
      hypotheticalDocResult,
    ] = await Promise.all([
      llm.embed(query),
      use_expansion
        ? expandPhilologicalQuery(query, llm).catch(() => quickExpand(query))
        : Promise.resolve(null),
      use_hyde
        ? generateHypotheticalDocument(query, llm).catch(() => '')
        : Promise.resolve(''),
    ]);

    let queryExpansion = queryExpansionResult;
    let hypotheticalDocument = hypotheticalDocResult;

    // Batch 2: Parallel searches
    const [
      standardResults,
      hydeSearchResults,
      nodeResults,
      edgeSearchResults,
    ] = await Promise.all([
      qdrant.searchTexts(geminiVector, adjustedSemanticK * 2, undefined, 0.5),
      use_hyde && hypotheticalDocument
        ? (async () => {
            const hydeEmbedding = await llm.embed(hypotheticalDocument);
            return await qdrant.searchTexts(hydeEmbedding, adjustedSemanticK, undefined, 0.5);
          })().catch(() => [])
        : Promise.resolve([]),
      qdrant.searchNodes(geminiVector, adjustedSemanticK, 0.5),
      qdrant.searchEdges(geminiVector, adjustedSemanticK, 0.7).catch(() => []),
    ]);

    let hydeResults = hydeSearchResults.map((r: any) => ({
      id: r.id,
      score: r.score,
      passageId: r.payload?.passage_id,
      author: r.payload?.author,
      work: r.payload?.title,
      text: r.payload?.text_preview || r.payload?.text_content,
      language: r.payload?.language,
      payload: r.payload,
    }));

    let edgeResults = edgeSearchResults;

    // Expanded search
    let expandedResults: any[] = [];
    if (use_expansion && queryExpansion && queryExpansion.greekTerms?.length > 0) {
      try {
        const expandResult = await expandedSearch(query, queryExpansion, qdrant, llm, adjustedSemanticK);
        expandedResults = expandResult.results;
      } catch (err) {
        logger.warn('Expanded search failed', err);
      }
    }

    // =================================================================
    // STEP 4: RRF Fusion
    // =================================================================
    const k = 60;
    const scores = new Map<string, number>();
    const items = new Map<string, any>();

    standardResults.forEach((item, rank) => {
      const id = String(item.id);
      scores.set(id, (scores.get(id) || 0) + 1 / (k + rank + 1));
      if (!items.has(id)) items.set(id, item);
    });

    hydeResults.forEach((item, rank) => {
      const id = String(item.id);
      scores.set(id, (scores.get(id) || 0) + 1.1 / (k + rank + 1));
      if (!items.has(id)) items.set(id, item);
    });

    expandedResults.forEach((item, rank) => {
      const id = String(item.id);
      scores.set(id, (scores.get(id) || 0) + 1 / (k + rank + 1));
      if (!items.has(id)) items.set(id, item);
    });

    const fusedIds = Array.from(scores.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 50)
      .map(([id]) => id);

    const fusedResults = fusedIds.map(id => items.get(id)!);

    // =================================================================
    // STEP 5: LLM Reranking (if not global_abstract - use hierarchy instead)
    // =================================================================
    let rerankedResults = fusedResults;
    let rerankingApplied = false;

    const shouldRerank = use_reranking &&
      fusedResults.length > 5 &&
      classification?.type !== 'global_abstract'; // Skip reranking for global queries

    if (shouldRerank) {
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
      } catch (err) {
        logger.warn('Reranking failed', err);
      }
    }

    // =================================================================
    // STEP 6: Textual Grounding
    // =================================================================
    let textualGroundings: TextualGrounding[] = [];
    let groundingContext = '';
    try {
      const grounding = await getTextualGroundings(nodeResults, geminiVector, c.env);
      textualGroundings = grounding.groundings;
      groundingContext = grounding.formattedContext;
    } catch (err) {
      logger.warn('Textual grounding failed', err);
    }

    // =================================================================
    // STEP 7: Build Combined Context (HiRAG + V2)
    // =================================================================
    const contextParts: string[] = [];

    // Priority context (explicit passage references)
    if (priorityContext) {
      contextParts.push(priorityContext);
      contextParts.push('');
    }

    // HIRAG ADDITION: Hierarchical context FIRST for global queries
    if (hierarchicalContext && classification?.type !== 'specific_entity') {
      contextParts.push(hierarchicalContext);
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
    // STEP 8: CRAG Validation (skip in fast mode)
    // =================================================================
    let cragValidation: any = null;
    const shouldRunCRAG = use_crag && mode !== 'fast';

    if (shouldRunCRAG) {
      try {
        cragValidation = await validateRetrievalSufficiency(query, context, llm);
        logger.info(`CRAG: confidence=${cragValidation.confidenceScore}`);
      } catch (err) {
        logger.warn('CRAG validation failed', err);
      }
    }

    // =================================================================
    // STEP 9: Debate Identification
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
      } catch (err) {
        logger.warn('Debate identification failed', err);
      }
    }

    let debateContext = '';
    if (debatesIdentified.length > 0) {
      debateContext = '\n\n=== PHILOSOPHICAL DEBATES IDENTIFIED ===\n' +
        debatesIdentified.slice(0, 3).map(d => formatDebateForDisplay(d)).join('\n\n');
    }

    // =================================================================
    // STEP 10: LLM Generation with HiRAG-aware prompt
    // =================================================================
    let promptAddition = '';
    if (classification) {
      if (classification.type === 'global_abstract') {
        promptAddition = `\n\nThis is a GLOBAL question about a broad topic. Use the hierarchical community summaries to provide a comprehensive overview before diving into specific details.`;
      } else if (classification.type === 'comparative') {
        promptAddition = `\n\nThis is a COMPARATIVE question. Highlight the differences and similarities between the entities/schools being compared.`;
      } else if (classification.type === 'multi_hop') {
        promptAddition = `\n\nThis is a MULTI-HOP question requiring reasoning across multiple concepts. Use the bridge paths provided to trace the connections.`;
      } else if (classification.type === 'temporal_evolution') {
        promptAddition = `\n\nThis is a TEMPORAL question about how concepts evolved. Order your response chronologically and highlight changes over time.`;
      }
    }

    const enhancedPrompt = `You are a scholarly expert on ancient philosophy and free will debates.

Context from knowledge graph:
${context}
${debateContext}

Question: ${query}
${promptAddition}

${TEXTUAL_GROUNDING_PROMPT}

IMPORTANT: If the user asked about a SPECIFIC passage (like "De Fato 39"), your answer must focus primarily on the EXACT TEXT provided above.

Provide a comprehensive, scholarly answer that:
1. Quotes original Greek/Latin texts when available (with translations)
2. Cites specific passages using proper references (Author, Work Section)
3. Preserves key philosophical terminology in the original language
4. Grounds all claims in the textual evidence provided
${debatesIdentified.length > 0 ? '5. Addresses the philosophical debates identified above' : ''}

CRITICAL CITATION RULES:
- When citing ancient sources, use ONLY chapter/section numbers that exist in the original works
- NEVER confuse page numbers from modern publications with ancient text section numbers
- For Justin Martyr: First Apology has ~68 chapters, Dialogue with Trypho has ~142 chapters`;

    let answer = await llm.generateWithRetry(enhancedPrompt, 'gemini-3-flash-preview');
    if (typeof answer !== 'string') {
      answer = answer?.text || answer?.content || String(answer || '');
    }

    // =================================================================
    // STEP 11: SELF-RAG Evaluation
    // =================================================================
    let selfEvaluation: any = null;

    // Helper to determine node type from payload
    const determineNodeType = (payload: any): string => {
      // Explicit type field takes priority
      if (payload?.type) return payload.type;
      if (payload?.node_type) return payload.node_type;

      // Extract from node_id prefix if available
      if (payload?.node_id) {
        const prefixes = ['concept', 'argument', 'person', 'work', 'reformulation', 'group', 'school', 'evidence'];
        for (const prefix of prefixes) {
          if (payload.node_id.startsWith(prefix + '_')) {
            return prefix.charAt(0).toUpperCase() + prefix.slice(1);
          }
        }
      }

      // If has author/work info, it's a Passage from ancient text
      if (payload?.author || payload?.work_title || payload?.cts_urn) {
        return 'Passage';
      }

      // If has name field but no author, likely a KG Concept
      if (payload?.name || payload?.label) {
        return 'Concept';
      }

      return 'Unknown';
    };

    // Build properly structured sources for frontend display
    const structuredSources = rerankedResults.slice(0, max_context).map((r, index) => ({
      id: index + 1,
      nodeId: r.id || r.payload?.node_id || `source_${index}`,
      nodeLabel: r.payload?.label || r.payload?.author || r.payload?.title || 'Unknown',
      nodeType: determineNodeType(r.payload),
      content: r.payload?.description || r.payload?.content,
      metadata: {
        school: r.payload?.school,
        period: r.payload?.period,
        author: r.payload?.author,
        confidence: r.score || undefined,
      },
    }));

    // Keep string labels for SELF-RAG evaluation (expects string array)
    const sourceLabels = structuredSources.map(s => s.nodeLabel);

    const shouldRunSelfRAG = use_selfrag && mode !== 'fast';

    if (shouldRunSelfRAG) {
      try {
        selfEvaluation = await selfEvaluateAnswer(query, answer, sourceLabels.length, sourceLabels, llm);
      } catch (err) {
        logger.warn('SELF-RAG failed', err);
      }
    } else if (use_selfrag) {
      // Fast mode estimate
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
    }

    // =================================================================
    // STEP 12: Build Response
    // =================================================================
    const processingTime = Date.now() - startTime;

    // Evidence package
    const allSourceNodes = [
      ...nodeResults,
      ...rerankedResults.slice(0, max_context).map(r => ({ ...r, payload: r.payload || r })),
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
      ...textualGroundings.map(g => g.ctsUrn).filter(Boolean),
    ];
    const uniqueCtsUrns = [...new Set(allCtsUrns)];

    // Build search score map for evidence tracing
    const searchScores = new Map<string, number>();
    rerankedResults.slice(0, max_context).forEach((r, i) => {
      searchScores.set(String(r.id || r.payload?.node_id), r.score || (1 - i * 0.05));
    });

    // Evidence traces
    const evidenceTraces = buildEvidenceTraces(
      rerankedResults.slice(0, max_context).map(r => r.payload || {}),
      searchScores,
      new Map(),
      new Map(),
      use_hyde,
      use_expansion,
      rerankingApplied ? new Map(rerankedResults.slice(0, max_context).map((r, i) => [String(r.id), 100 - i * 5])) : undefined,
      query
    );
    const evidenceQuality = calculateEvidenceQuality(evidenceTraces.traces);

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
      textualGroundings: textualGroundings.map(g => ({
        reference: `${g.author}, ${g.reference}`,
        originalText: g.originalText,
        language: g.language === 'grc' ? 'Greek' : 'Latin',
        ctsUrn: g.ctsUrn,
        passageId: g.passageId,
      })),

      // Quality scores
      qualityScore: selfEvaluation?.confidenceScore || evidenceQuality.overallScore * 100,
      qualityBadge: selfEvaluation?.qualityBadge || evidenceQuality.badge,
      caveats: selfEvaluation?.caveats || [],
      confidenceExplanation: selfEvaluation ? explainConfidence(selfEvaluation) : evidenceQuality.explanation,

      // Evidence explainability
      evidenceTraces: evidenceTraces.traces,
      evidenceQuality,

      // Debates
      debatesIdentified: debatesIdentified.map(d => ({
        topic: d.topic,
        description: d.description,
        level: d.score.level,
        schools: d.score.schools,
        keyFigures: d.score.keyFigures,
      })),

      // ========================
      // HiRAG-SPECIFIC FIELDS
      // ========================
      hiragInfo: {
        queryClassification: classification ? {
          type: classification.type,
          confidence: classification.confidence,
          entities: classification.entities,
          concepts: classification.concepts,
          schools: classification.schools,
          suggestedLevel: classification.suggestedLevel,
        } : null,
        strategy: strategy ? {
          startLevel: strategy.startLevel,
          maxDepth: strategy.maxDepth,
          expandMode: strategy.expandMode,
          maxCommunities: strategy.maxCommunities,
          useBridge: strategy.useBridge,
        } : null,
        bridgeMode: !!bridgeContext,
        bridgePaths: bridgeContext?.paths?.length || 0,
        bridgingConcepts: bridgeContext?.bridgingConcepts || [],
        hierarchicalContextUsed: !!hierarchicalContext,
      },

      // Retrieval strategy details
      retrievalStrategy: {
        hydeUsed: use_hyde,
        queryExpanded: use_expansion,
        reranked: rerankingApplied,
        cragValidated: use_crag,
        selfEvaluated: use_selfrag,
        hierarchicalUsed: use_hierarchy,
        bridgeUsed: !!bridgeContext,
      },

      // Query expansion details
      queryExpansion: queryExpansion ? {
        greekTerms: queryExpansion.greekTerms,
        latinTerms: queryExpansion.latinTerms,
        philosophers: queryExpansion.philosophers,
        concepts: queryExpansion.concepts,
      } : undefined,

      // CRAG validation
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
        adjustedSemanticK,
      },

      processingTime,
      mode,
      version: 'hirag-v2',
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
        use_hierarchy,
        use_bridge,
      },
      success: true,
    });
  } catch (error) {
    logger.error('HiRAG V2 answer error', error);
    return c.json({
      error: 'Query processing failed',
      code: 'HIRAG_V2_ANSWER_ERROR',
      message: error instanceof Error ? error.message : 'Unknown error',
      success: false,
    }, 500);
  }
});

// =============================================================================
// BACKWARD COMPATIBILITY ALIASES
// =============================================================================
// These routes redirect to the main /answer endpoint for existing integrations

// Alias: /answer/hirag-v2 → /answer (for A/B testing scripts)
graphragRoutes.post('/answer/hirag-v2', async (c) => {
  // Forward to main /answer handler
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

// Alias: /answer/v2 → /answer (for frontend compatibility)
graphragRoutes.post('/answer/v2', async (c) => {
  // Forward to main /answer handler
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
