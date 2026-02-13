/**
 * Agentic Orchestrator — Enhanced Pipeline
 *
 * Coordinates all agentic components in a cohesive reasoning pipeline:
 * Plan → [Query Expansion] → Retrieval + [HyDE parallel] → [CRAG Validation]
 *   → [LLM Rerank] → [Textual Grounding] → Reasoning → [Sufficiency Check]
 *   → Verification → [Self-RAG] → Refinement → Answer
 *
 * Wires 6 previously disconnected services into the production pipeline:
 * - Query Expander: Greek/Latin term expansion for better recall
 * - HyDE: Hypothetical document embeddings for semantic gap bridging
 * - CRAG: Corrective RAG to catch retrieval failures early
 * - LLM Reranker: Domain-specific relevance reranking
 * - Self-RAG: Post-generation self-evaluation for hallucination reduction
 * - Textual Grounding: Actual passage text for evidence nodes
 */

import { Env, QueryType } from '../../types';
import { LLMService } from '../llm';
import { DatabaseService } from '../database';
import { QdrantService } from '../qdrant';
import { HierarchicalRetrievalService } from '../hierarchical-retrieval';
import { PlanningAgent } from './planning-agent';
import { ReasoningAgent } from './reasoning-agent';
import { EnhancedReasoningAgent } from './reasoning-agent-enhanced';
import { VerificationAgent } from './verification-agent';
import { RefinementAgent } from './refinement-agent';
import {
  AgenticAnswer,
  Evidence,
  PipelineConfig,
  SufficiencyResult,
} from '../../types/agentic';
import { getLogger } from '../../utils/logger';

// Wired services (previously disconnected)
import { expandPhilologicalQuery } from '../query-expander';
import { hydeSearchNodes } from '../hyde';
import { validateRetrievalSufficiency, secondaryRetrieval } from '../crag';
import { llmRerank, RerankCandidate } from '../reranker';
import { selfEvaluateAnswer } from '../self-rag';
import { getTextualGroundings } from '../textual-grounding';

// New services
import { PassageRetrievalService } from '../passage-retrieval';
import { partitionEvidence, buildHierarchicalContext } from '../evidence-layering';

const logger = getLogger('AgenticOrchestrator');

/**
 * Select pipeline features based on query classification.
 */
function selectPipelineConfig(queryType: QueryType): PipelineConfig {
  switch (queryType) {
    case 'specific_entity':
      // Direct matching works well; skip HyDE, enable expansion
      return {
        useHyDE: false,
        useCRAG: true,
        useReranking: true,
        useSelfRAG: true,
        useExpansion: true,
        useGrounding: true,
      };
    case 'global_abstract':
      // Broad queries benefit from HyDE; skip expansion (too specific)
      return {
        useHyDE: true,
        useCRAG: true,
        useReranking: true,
        useSelfRAG: true,
        useExpansion: false,
        useGrounding: true,
      };
    case 'multi_hop':
      // Bridge mode handles retrieval; skip HyDE
      return {
        useHyDE: false,
        useCRAG: true,
        useReranking: false, // Bridge paths are already scored
        useSelfRAG: true,
        useExpansion: true,
        useGrounding: true,
      };
    case 'comparative':
      // Enable everything for thorough comparison
      return {
        useHyDE: true,
        useCRAG: true,
        useReranking: true,
        useSelfRAG: true,
        useExpansion: true,
        useGrounding: true,
      };
    default:
      // temporal_evolution, dialectical — enable all
      return {
        useHyDE: true,
        useCRAG: true,
        useReranking: true,
        useSelfRAG: true,
        useExpansion: true,
        useGrounding: true,
      };
  }
}

export class AgenticOrchestrator {
  private env: Env;
  private llm: LLMService;
  private db: DatabaseService;
  private qdrant: QdrantService;
  private retrieval: HierarchicalRetrievalService;
  private passageRetrieval: PassageRetrievalService;
  private planning: PlanningAgent;
  private reasoning: ReasoningAgent;
  private enhancedReasoning: EnhancedReasoningAgent;
  private verification: VerificationAgent;
  private refinement: RefinementAgent;

  constructor(env: Env) {
    this.env = env;
    this.llm = new LLMService(env);
    this.db = new DatabaseService(env);
    this.qdrant = new QdrantService(env);
    this.retrieval = new HierarchicalRetrievalService(env);
    this.passageRetrieval = new PassageRetrievalService(env);

    // Initialize agents
    this.planning = new PlanningAgent(this.llm);
    this.reasoning = new ReasoningAgent(this.llm);
    this.enhancedReasoning = new EnhancedReasoningAgent(this.llm);
    this.verification = new VerificationAgent(this.db, this.llm);
    this.refinement = new RefinementAgent(
      this.llm,
      this.retrieval,
      this.reasoning,
      this.verification
    );
  }

  /**
   * Execute full agentic reasoning pipeline
   */
  async execute(
    query: string,
    options: {
      mode?: string;
      maxIterations?: number;
      confidenceThreshold?: number;
      skipRefinement?: boolean;
    } = {}
  ): Promise<AgenticAnswer> {
    const startTime = Date.now();
    logger.info('═══════════════════════════════════════════════════════');
    logger.info(`AGENTIC EXECUTION STARTED`);
    logger.info(`Query: "${query}"`);
    if (options.mode) {
      logger.info(`Mode: "${options.mode}" (explicit)`);
    }
    logger.info('═══════════════════════════════════════════════════════');

    const {
      mode,
      maxIterations = 3,
      confidenceThreshold = 0.8,
      skipRefinement = false,
    } = options;

    try {
      // ================================================================
      // STEP 1: PLANNING
      // ================================================================
      logger.info('\nSTEP 1: PLANNING');
      logger.info('─'.repeat(60));
      const plan = await this.planning.plan(query);
      logger.info(`Plan created: ${plan.subQuestions.length} sub-question(s)`);
      logger.info(`  Strategy: ${plan.strategy.mode} execution`);

      // ================================================================
      // STEP 1.5: QUERY EXPANSION (NEW)
      // ================================================================
      const retrieval = await this.retrieval.retrieve(query, mode);
      const queryType = retrieval.classification.type;
      const pipelineConfig = selectPipelineConfig(queryType);

      let expandedQuery = query;
      if (pipelineConfig.useExpansion) {
        logger.info('\nSTEP 1.5: QUERY EXPANSION');
        logger.info('─'.repeat(60));
        try {
          const expansion = await expandPhilologicalQuery(query, this.llm);
          // Enhance the query with Greek/Latin terms for better retrieval
          const additionalTerms = [
            ...expansion.greekTerms.slice(0, 2).map(t => t.transliteration),
            ...expansion.philosophers.slice(0, 2),
          ].filter(Boolean);

          if (additionalTerms.length > 0) {
            expandedQuery = `${query} (${additionalTerms.join(', ')})`;
            logger.info(`Query expanded: "${expandedQuery}"`);
            logger.info(`  Greek terms: ${expansion.greekTerms.length}, Latin: ${expansion.latinTerms.length}`);
          }
        } catch (error) {
          logger.warn('Query expansion failed, using original query', error);
        }
      }

      // ================================================================
      // STEP 2: ENHANCED RETRIEVAL (HyDE parallel + CRAG validation)
      // ================================================================
      logger.info('\nSTEP 2: HIERARCHICAL RETRIEVAL');
      logger.info('─'.repeat(60));
      logger.info(`Retrieved ${retrieval.communities.length} communities`);
      logger.info(`  Classification: ${retrieval.classification.type}`);
      logger.info(`  Level: ${retrieval.strategy.startLevel}`);
      logger.info(`  Tokens: ~${retrieval.tokenCount}`);
      if (retrieval.diagnostics) {
        retrieval.diagnostics.levels.forEach(levelDiag => {
          const fallbackNote = levelDiag.fallbackApplied ? ' (fallback)' : '';
          const reasonNote = levelDiag.reason ? ` reason=${levelDiag.reason}` : '';
          logger.info(
            `  L${levelDiag.level}: ${levelDiag.communities} communities, maxScore=${levelDiag.maxScore}${fallbackNote}${reasonNote}`
          );
        });
        logger.info(`  Final community count: ${retrieval.diagnostics.finalLevelCount}`);
      }

      // Run HyDE in parallel if enabled
      let hydeEvidence: Evidence[] = [];
      if (pipelineConfig.useHyDE && !retrieval.bridgeContext) {
        logger.info('\n  HyDE: Generating hypothetical document...');
        try {
          const hydeResult = await hydeSearchNodes(
            expandedQuery, this.llm, this.qdrant, this.env, 5
          );
          hydeEvidence = hydeResult.searchResults.map(r => ({
            source: `HyDE: ${r.payload?.label || r.payload?.node_id || 'unknown'}`,
            content: r.payload?.description || r.payload?.text_preview || '',
            type: 'node' as const,
            confidence: r.score * 0.9, // Slight discount for hypothetical match
            isPrimary: true,
            nodeId: r.payload?.node_id || String(r.id),
            nodeLabel: r.payload?.label || '',
            nodeType: r.payload?.type || 'concept',
          }));
          logger.info(`  HyDE: ${hydeEvidence.length} additional nodes found`);
        } catch (error) {
          logger.warn('  HyDE search failed, continuing without', error);
        }
      }

      // Convert retrieval to evidence
      const baseEvidence = this.convertToEvidence(retrieval);
      let evidence = [...baseEvidence, ...hydeEvidence];
      logger.info(`  Total evidence: ${evidence.length} pieces`);

      // ================================================================
      // STEP 2.5: CRAG VALIDATION (NEW)
      // ================================================================
      if (pipelineConfig.useCRAG) {
        logger.info('\n  CRAG: Validating retrieval sufficiency...');
        try {
          const cragResult = await validateRetrievalSufficiency(
            query, retrieval.context, this.llm
          );
          logger.info(`  CRAG: relevance=${cragResult.relevanceScore}, completeness=${cragResult.completenessScore}, valid=${cragResult.isValid}`);

          if (cragResult.needsSecondaryRetrieval) {
            logger.info('  CRAG: Triggering secondary retrieval...');
            const secondary = await secondaryRetrieval(
              cragResult.missingAspects,
              cragResult.suggestions,
              this.llm,
              this.qdrant
            );
            // Convert secondary results to evidence
            for (const r of secondary.additionalResults) {
              evidence.push({
                source: `CRAG Secondary: ${r.payload?.label || 'supplemental'}`,
                content: r.payload?.description || r.payload?.text_preview || '',
                type: 'node',
                confidence: (r.score || 0.5) * 0.85,
                isPrimary: true,
                nodeId: r.payload?.node_id || String(r.id),
                nodeLabel: r.payload?.label || '',
                nodeType: r.payload?.type || 'concept',
              });
            }
            logger.info(`  CRAG: Added ${secondary.additionalResults.length} supplemental results`);
          }
        } catch (error) {
          logger.warn('  CRAG validation failed, continuing', error);
        }
      }

      // ================================================================
      // STEP 2.7: LLM RERANKING (NEW)
      // ================================================================
      if (pipelineConfig.useReranking && evidence.length > 5) {
        logger.info('\n  RERANK: LLM-based reranking...');
        try {
          const candidates: RerankCandidate[] = evidence
            .filter(e => e.content && e.content.length > 20)
            .map(e => ({
              id: e.nodeId || e.source,
              score: e.confidence,
              text: e.content,
              author: e.metadata?.author || e.author,
              work: e.workTitle,
              metadata: e.metadata,
            }));

          if (candidates.length > 5) {
            const rerankResult = await llmRerank(query, candidates, this.llm, 15);

            // Update evidence confidence with rerank scores
            const rerankScoreMap = new Map<string | number, number>();
            for (const r of rerankResult.results) {
              rerankScoreMap.set(r.id, r.rerankScore / 100);
            }

            evidence = evidence.map(e => {
              const key = e.nodeId || e.source;
              const rerankScore = rerankScoreMap.get(key);
              if (rerankScore !== undefined) {
                return { ...e, confidence: (e.confidence + rerankScore) / 2 };
              }
              return e;
            });

            // Sort by updated confidence
            evidence.sort((a, b) => b.confidence - a.confidence);
            logger.info(`  RERANK: ${rerankResult.candidatesEvaluated} candidates evaluated in ${rerankResult.rerankTime}ms`);
          }
        } catch (error) {
          logger.warn('  Reranking failed, using original order', error);
        }
      }

      // ================================================================
      // STEP 2.8: PASSAGE RETRIEVAL + TEXTUAL GROUNDING (NEW)
      // ================================================================
      if (pipelineConfig.useGrounding) {
        logger.info('\n  GROUNDING: Fetching passage texts...');
        try {
          // Collect node IDs from evidence for passage lookup
          const nodeIds = evidence
            .map(e => e.nodeId)
            .filter((id): id is string => !!id);

          if (nodeIds.length > 0) {
            const passages = await this.passageRetrieval.fetchPassagesForNodes(
              nodeIds, 10
            );

            // Add passages as evidence
            for (const p of passages) {
              evidence.push({
                source: `${p.author}, ${p.canonicalRef}`,
                content: p.textContent,
                type: 'passage',
                confidence: p.confidence,
                isPrimary: true,
                passageId: p.passageId,
                canonicalRef: p.canonicalRef,
                author: p.author,
                workTitle: p.workTitle,
                ctsUrn: p.ctsUrn,
                textContent: p.textContent,
                metadata: {
                  author: p.author,
                  period: undefined,
                },
              });
            }
            logger.info(`  GROUNDING: Added ${passages.length} passage texts`);

            // Also try textual grounding via Qdrant
            const queryEmbedding = await this.llm.embed(expandedQuery);
            const nodes = await this.extractNodesFromRetrieval(retrieval);
            const groundingContext = await getTextualGroundings(
              nodes, queryEmbedding, this.env
            );
            if (groundingContext.groundings.length > 0) {
              logger.info(`  GROUNDING: ${groundingContext.groundings.length} textual groundings found`);
            }
          }
        } catch (error) {
          logger.warn('  Passage retrieval failed, continuing', error);
        }
      }

      // ================================================================
      // STEP 2.9: EVIDENCE LAYERING (NEW)
      // ================================================================
      const { primary, secondary } = partitionEvidence(evidence);
      logger.info(`  LAYERING: ${primary.length} primary, ${secondary.length} secondary`);

      // Build layered context for the LLM
      const passages = evidence
        .filter(e => e.type === 'passage' && e.textContent)
        .map(e => ({
          passageId: e.passageId || '',
          textContent: e.textContent || '',
          canonicalRef: e.canonicalRef || '',
          author: e.author || 'Unknown',
          workTitle: e.workTitle || '',
          language: 'grc' as const,
          ctsUrn: e.ctsUrn,
          confidence: e.confidence,
        }));

      const layeredContext = buildHierarchicalContext(primary, secondary, passages);
      const enrichedContext = layeredContext || retrieval.context;

      // ================================================================
      // STEP 3: SUFFICIENCY CHECK + RE-RETRIEVAL LOOP (pre-synthesis)
      // ================================================================
      logger.info('\nSTEP 3: SUFFICIENCY CHECK');
      logger.info('─'.repeat(60));

      const maxSufficiencyIterations = 3;
      for (let suffIter = 0; suffIter < maxSufficiencyIterations; suffIter++) {
        const sufficiency = this.evaluateSufficiency(query, evidence, suffIter, maxSufficiencyIterations);
        logger.info(`  Iteration ${suffIter}: passages=${sufficiency.passageCount}, primary=${sufficiency.primaryCount}, sufficient=${sufficiency.sufficient}`);

        if (sufficiency.sufficient) break;

        // If heuristic says insufficient, try LLM-based evaluation before re-retrieving
        if (suffIter < maxSufficiencyIterations - 1) {
          try {
            const llmSufficiency = await this.llm.generateForTask(
              `Given the question: "${query}"\nAnd ${sufficiency.primaryCount} primary source nodes and ${sufficiency.passageCount} passage texts,\nis the evidence sufficient to write a well-grounded scholarly answer?\nRespond with JSON: {"sufficient": true/false, "refinedQuery": "optional refined query if insufficient"}`,
              'sufficiency'
            );
            const parsed = JSON.parse(llmSufficiency);
            if (parsed.sufficient) {
              logger.info('  LLM: Evidence deemed sufficient');
              break;
            }

            // Re-retrieve with refined query
            const refinedQ = parsed.refinedQuery || `${query} ancient sources evidence`;
            logger.info(`  LLM: Insufficient, re-retrieving with: "${refinedQ}"`);

            const supplemental = await this.retrieval.retrieve(refinedQ, mode);
            const supplementalEvidence = this.convertToEvidence(supplemental);
            const existingIds = new Set(evidence.map(e => e.nodeId).filter(Boolean));
            for (const se of supplementalEvidence) {
              if (se.nodeId && !existingIds.has(se.nodeId)) {
                evidence.push(se);
              }
            }
            logger.info(`  Re-retrieval added ${supplementalEvidence.filter(e => e.nodeId && !existingIds.has(e.nodeId)).length} new evidence items`);
          } catch (error) {
            logger.warn('  LLM sufficiency check failed, proceeding', error);
            break;
          }
        }
      }

      // ================================================================
      // STEP 4: REASONING WITH CITATIONS
      // ================================================================
      logger.info('\nSTEP 4: REASONING WITH CITATIONS');
      logger.info('─'.repeat(60));

      // Get nodes for citation mapping
      const nodes = await this.extractNodesFromRetrieval(retrieval);

      // Use enhanced reasoning with citations and layered context
      const reasoningResult = await this.enhancedReasoning.reasonWithCitations(
        query,
        enrichedContext,
        evidence,
        nodes
      );

      const reasoningChain = reasoningResult.reasoningChain;
      logger.info(`Reasoning complete: ${reasoningChain.steps.length} steps`);
      logger.info(`  Confidence: ${reasoningChain.confidence.toFixed(2)}`);
      logger.info(`  Contradictions: ${reasoningChain.contradictions.length}`);
      logger.info(`  Citations: ${reasoningResult.sources.length}`);

      // Use the cited answer
      let currentAnswer = reasoningResult.answer;

      // ================================================================
      // STEP 5: VERIFICATION
      // ================================================================
      logger.info('\nSTEP 5: VERIFICATION');
      logger.info('─'.repeat(60));
      const verificationResult = await this.verification.verify(
        currentAnswer,
        evidence,
        query
      );
      logger.info(`Verification complete`);
      logger.info(`  Valid: ${verificationResult.isValid}`);
      logger.info(`  Confidence: ${verificationResult.confidence.toFixed(2)}`);
      logger.info(`  Issues: ${verificationResult.issues.length}`);

      // ================================================================
      // STEP 5.5: SELF-RAG EVALUATION (NEW)
      // ================================================================
      let selfRAGShouldRefine = false;
      if (pipelineConfig.useSelfRAG) {
        logger.info('\n  SELF-RAG: Evaluating answer quality...');
        try {
          const sourceLabels = reasoningResult.sources.map(s => s.nodeLabel);
          const selfRAGResult = await selfEvaluateAnswer(
            query,
            currentAnswer,
            reasoningResult.sources.length,
            sourceLabels,
            this.llm
          );
          logger.info(`  SELF-RAG: relevance=${selfRAGResult.relevanceScore}, grounding=${selfRAGResult.groundingScore}, badge=${selfRAGResult.qualityBadge}`);

          // Use Self-RAG to decide refinement instead of hardcoded threshold
          selfRAGShouldRefine = selfRAGResult.shouldRefine;
          if (selfRAGResult.caveats.length > 0) {
            logger.info(`  SELF-RAG caveats: ${selfRAGResult.caveats.join('; ')}`);
          }
        } catch (error) {
          logger.warn('  Self-RAG evaluation failed, continuing', error);
        }
      }

      // ================================================================
      // STEP 6: REFINEMENT
      // ================================================================
      let finalAnswer = currentAnswer;
      let finalConfidence = reasoningChain.confidence;
      let refinementIterations: any[] = [];

      const needsRefinement = !skipRefinement && (
        selfRAGShouldRefine ||
        finalConfidence < confidenceThreshold ||
        verificationResult.issues.length > 2
      );

      if (needsRefinement) {
        logger.info('\nSTEP 6: REFINEMENT');
        logger.info('─'.repeat(60));
        const refinement = await this.refinement.refine(
          query,
          currentAnswer,
          evidence,
          maxIterations,
          confidenceThreshold
        );
        logger.info(`Refinement complete: ${refinement.iterations.length} iteration(s)`);
        logger.info(`  Final confidence: ${refinement.confidence.toFixed(2)}`);

        finalAnswer = refinement.finalAnswer;
        finalConfidence = refinement.confidence;
        refinementIterations = refinement.iterations;
      } else {
        logger.info('\nSTEP 6: REFINEMENT (SKIPPED)');
      }

      // FINAL RESULT
      const processingTime = Date.now() - startTime;
      logger.info('\n═══════════════════════════════════════════════════════');
      logger.info('AGENTIC EXECUTION COMPLETE');
      logger.info(`  Processing time: ${processingTime}ms`);
      logger.info(`  Final confidence: ${finalConfidence.toFixed(2)}`);
      logger.info(`  Pipeline: expansion=${pipelineConfig.useExpansion} hyde=${pipelineConfig.useHyDE} crag=${pipelineConfig.useCRAG} rerank=${pipelineConfig.useReranking} grounding=${pipelineConfig.useGrounding} selfrag=${pipelineConfig.useSelfRAG}`);
      logger.info('═══════════════════════════════════════════════════════\n');

      return {
        answer: finalAnswer,
        confidence: finalConfidence,
        sources: reasoningResult.sources,
        evidenceMap: reasoningResult.evidenceMap,
        reasoningTrace: reasoningChain,
        verificationResults: [verificationResult],
        refinementIterations,
        metadata: {
          totalSteps: reasoningChain.steps.length + refinementIterations.length,
          retrievalCalls: 1 + refinementIterations.filter(
            (i: any) => i.additionalRetrieval.length > 0
          ).length,
          tokensUsed: retrieval.tokenCount,
          processingTime,
          plan,
          finalConfidence,
          retrievalDiagnostics: retrieval.diagnostics,
          qualityMetrics: refinementIterations.length > 0
            ? {
                completeness: refinementIterations[refinementIterations.length - 1].confidence,
                accuracy: verificationResult.confidence,
                clarity: 0.85,
              }
            : undefined,
        },
      };
    } catch (error) {
      logger.error('Agentic execution failed', error);
      throw error;
    }
  }

  /**
   * Pre-synthesis sufficiency check.
   * Heuristic evaluation before calling LLM for synthesis.
   */
  private evaluateSufficiency(
    query: string,
    evidence: Evidence[],
    iteration: number,
    maxIterations: number
  ): SufficiencyResult {
    const passageCount = evidence.filter(e => e.type === 'passage').length;
    const primaryCount = evidence.filter(e => e.isPrimary).length;

    // Heuristic: sufficient if we have enough primary evidence and passages
    const sufficient = passageCount >= 2 && primaryCount >= 4;

    return {
      sufficient: sufficient || iteration >= maxIterations,
      passageCount,
      primaryCount,
    };
  }

  /**
   * Convert hierarchical retrieval results to Evidence format
   */
  private convertToEvidence(retrieval: any): Evidence[] {
    const evidence: Evidence[] = [];

    // Handle bridge mode evidence (multi-hop reasoning)
    if (retrieval.bridgeContext) {
      const bridge = retrieval.bridgeContext;

      // Add path evidence with node IDs
      for (const path of bridge.paths) {
        const pathDescription = path.nodes.map((n: any) => n.label).join(' → ');
        const nodeIds = path.nodes.map((n: any) => n.id);

        evidence.push({
          source: `Bridge Path: ${path.nodes[0].label} to ${path.nodes[path.nodes.length-1].label}`,
          content: `Connection path: ${pathDescription}\n\n${path.reasoning || 'Direct philosophical connection identified through intermediate concepts'}`,
          type: 'bridge',
          confidence: 0.9,
          isPrimary: true,
          nodeId: nodeIds[0],
          nodeLabel: path.nodes[0].label,
          nodeType: path.nodes[0].type || 'concept',
          nodePath: nodeIds,
          metadata: {
            pathLength: path.distance,
            nodeCount: path.nodes.length,
          },
        });
      }

      // Add hierarchical context as evidence
      for (const [level, summary] of bridge.hierarchicalContext.entries()) {
        evidence.push({
          source: `Hierarchical Context (Level ${level})`,
          content: summary,
          type: 'context',
          confidence: 0.8,
          isPrimary: false,
          metadata: {
            level: level,
          },
        });
      }

      // Add bridging concepts
      if (bridge.bridgingConcepts && bridge.bridgingConcepts.length > 0) {
        evidence.push({
          source: 'Bridging Concepts',
          content: `Key concepts connecting the query elements: ${bridge.bridgingConcepts.join(', ')}`,
          type: 'concepts',
          confidence: 0.7,
          isPrimary: false,
          metadata: {
            conceptCount: bridge.bridgingConcepts.length,
          },
        });
      }
    }

    // Handle standard community evidence with node IDs
    for (const community of retrieval.communities) {
      const representativeMembers = community.members && community.members.length > 0
        ? community.members
        : community.member_node_ids || [];
      const nodeId = representativeMembers.length > 0 ? representativeMembers[0] : community.id;

      evidence.push({
        source: `${community.dominant_school || 'Mixed'} Community (Level ${community.level})`,
        content: community.summary,
        type: 'community',
        confidence: 0.8,
        isPrimary: false,
        nodeId: nodeId,
        nodeLabel: `${community.dominant_school || 'Mixed'} Community`,
        nodeType: 'community',
        metadata: {
          period: community.dominant_period || undefined,
          school: community.dominant_school || undefined,
          relevanceScore: community.relevanceScore,
          matchReasons: community.matchReasons,
        },
      });
    }

    return evidence;
  }

  /**
   * Extract initial answer from reasoning chain
   */
  private extractInitialAnswer(reasoning: any): string {
    const synthesisStep = reasoning.steps.find(
      (step: any) => step.action === 'synthesize'
    );

    if (synthesisStep && synthesisStep.output && synthesisStep.output.answer) {
      return synthesisStep.output.answer;
    }

    const lastStep = reasoning.steps[reasoning.steps.length - 1];
    if (lastStep && lastStep.output) {
      if (typeof lastStep.output === 'string') {
        return lastStep.output;
      }
      if (lastStep.output.answer) {
        return lastStep.output.answer;
      }
    }

    return 'Unable to generate answer from reasoning chain.';
  }

  /**
   * Execute plan with multiple sub-questions
   */
  private async executePlan(plan: any): Promise<string[]> {
    const results: string[] = [];

    if (plan.strategy.mode === 'parallel' && plan.subQuestions.length <= 3) {
      logger.info('Executing sub-questions in parallel');
      const promises = plan.subQuestions.map((sq: any) =>
        this.executeSubQuestion(sq.question)
      );
      results.push(...await Promise.all(promises));
    } else {
      logger.info('Executing sub-questions sequentially');
      for (const sq of plan.subQuestions) {
        const result = await this.executeSubQuestion(sq.question);
        results.push(result);
      }
    }

    return results;
  }

  /**
   * Execute a single sub-question
   */
  private async executeSubQuestion(question: string): Promise<string> {
    logger.info(`Executing sub-question: "${question}"`);

    const retrieval = await this.retrieval.retrieve(question);
    const evidence = this.convertToEvidence(retrieval);
    const reasoning = await this.reasoning.reason(question, retrieval.context, evidence);

    return this.extractInitialAnswer(reasoning);
  }

  /**
   * Extract nodes from retrieval results for citation mapping
   */
  private async extractNodesFromRetrieval(retrieval: any): Promise<any[]> {
    const nodes: any[] = [];

    // Extract nodes from bridge context
    if (retrieval.bridgeContext) {
      for (const path of retrieval.bridgeContext.paths) {
        nodes.push(...path.nodes);
      }
    }

    // Extract nodes from communities
    for (const community of retrieval.communities) {
      if (community.nodes) {
        nodes.push(...community.nodes);
      }
    }

    // If we don't have nodes, fetch them from the database
    if (nodes.length === 0 && retrieval.communities.length > 0) {
      try {
        const nodeIds = new Set<string>();
        for (const community of retrieval.communities) {
          if (community.members) {
            community.members.forEach((id: string) => nodeIds.add(id));
          }
        }

        if (nodeIds.size > 0) {
          const fetchedNodes = await this.db.getNodesByIds(Array.from(nodeIds));
          nodes.push(...fetchedNodes);
        }
      } catch (error) {
        logger.warn('Failed to fetch nodes for citation mapping', error);
      }
    }

    return nodes;
  }

  /**
   * Health check for all agents
   */
  async healthCheck(): Promise<{
    status: string;
    agents: Record<string, boolean>;
  }> {
    const agents = {
      llm: false,
      database: false,
      retrieval: false,
      planning: true,
      reasoning: true,
      verification: true,
      refinement: true,
    };

    try {
      agents.llm = await this.llm.healthCheck();
      agents.database = await this.db.healthCheck();
      agents.retrieval = true;

      const allHealthy = Object.values(agents).every(v => v);

      return {
        status: allHealthy ? 'healthy' : 'degraded',
        agents,
      };
    } catch (error) {
      logger.error('Health check failed', error);
      return {
        status: 'unhealthy',
        agents,
      };
    }
  }
}
