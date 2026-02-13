/**
 * Agentic Orchestrator
 *
 * Coordinates all agentic components in a cohesive reasoning pipeline:
 * Plan → Retrieve → Reason → Verify → Refine → Answer
 *
 * This is the main entry point for agentic GraphRAG queries.
 */

import { Env } from '../../types';
import { LLMService } from '../llm';
import { DatabaseService } from '../database';
import { HierarchicalRetrievalService } from '../hierarchical-retrieval';
import { PlanningAgent } from './planning-agent';
import { ReasoningAgent } from './reasoning-agent';
import { EnhancedReasoningAgent } from './reasoning-agent-enhanced';
import { VerificationAgent } from './verification-agent';
import { RefinementAgent } from './refinement-agent';
import { AgenticAnswer, Evidence } from '../../types/agentic';
import { getLogger } from '../../utils/logger';

const logger = getLogger('AgenticOrchestrator');

export class AgenticOrchestrator {
  private env: Env;
  private llm: LLMService;
  private db: DatabaseService;
  private retrieval: HierarchicalRetrievalService;
  private planning: PlanningAgent;
  private reasoning: ReasoningAgent;
  private enhancedReasoning: EnhancedReasoningAgent;
  private verification: VerificationAgent;
  private refinement: RefinementAgent;

  constructor(env: Env) {
    this.env = env;
    this.llm = new LLMService(env);
    this.db = new DatabaseService(env);
    this.retrieval = new HierarchicalRetrievalService(env);

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
      mode?: string; // New: explicit mode selection
      maxIterations?: number;
      confidenceThreshold?: number;
      skipRefinement?: boolean;
    } = {}
  ): Promise<AgenticAnswer> {
    const startTime = Date.now();
    logger.info('═══════════════════════════════════════════════════════');
    logger.info(`🤖 AGENTIC EXECUTION STARTED`);
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
      // STEP 1: PLANNING
      logger.info('\n📋 STEP 1: PLANNING');
      logger.info('─'.repeat(60));
      const plan = await this.planning.plan(query);
      logger.info(`✓ Plan created: ${plan.subQuestions.length} sub-question(s)`);
      logger.info(`  Strategy: ${plan.strategy.mode} execution`);

      // STEP 2: RETRIEVAL
      logger.info('\n🔍 STEP 2: HIERARCHICAL RETRIEVAL');
      logger.info('─'.repeat(60));
      const retrieval = await this.retrieval.retrieve(query, mode);
      logger.info(`✓ Retrieved ${retrieval.communities.length} communities`);
      logger.info(`  Classification: ${retrieval.classification.type}`);
      logger.info(`  Level: ${retrieval.strategy.startLevel}`);
      logger.info(`  Tokens: ~${retrieval.tokenCount}`);
      if (retrieval.diagnostics) {
        retrieval.diagnostics.levels.forEach(levelDiag => {
          const fallbackNote = levelDiag.fallbackApplied ? ' (fallback)' : '';
          const reasonNote = levelDiag.reason ? ` reason=${levelDiag.reason}` : '';
          logger.info(
            `  • L${levelDiag.level}: ${levelDiag.communities} communities, maxScore=${levelDiag.maxScore}${fallbackNote}${reasonNote}`
          );
        });
        logger.info(`  Final community count: ${retrieval.diagnostics.finalLevelCount}`);
      }

      // Convert retrieval to evidence
      const evidence = this.convertToEvidence(retrieval);
      logger.info(`  Converted to ${evidence.length} pieces of evidence`);

      // STEP 3: REASONING WITH CITATIONS
      logger.info('\n🧠 STEP 3: REASONING WITH CITATIONS');
      logger.info('─'.repeat(60));

      // Get nodes for citation mapping
      const nodes = await this.extractNodesFromRetrieval(retrieval);

      // Use enhanced reasoning with citations
      const reasoningResult = await this.enhancedReasoning.reasonWithCitations(
        query,
        retrieval.context,
        evidence,
        nodes
      );

      const reasoningChain = reasoningResult.reasoningChain;
      logger.info(`✓ Reasoning complete: ${reasoningChain.steps.length} steps`);
      logger.info(`  Confidence: ${reasoningChain.confidence.toFixed(2)}`);
      logger.info(`  Contradictions: ${reasoningChain.contradictions.length}`);
      logger.info(`  Citations: ${reasoningResult.sources.length}`);

      // Use the cited answer
      const initialAnswer = reasoningResult.answer;

      // STEP 4: VERIFICATION
      logger.info('\n✅ STEP 4: VERIFICATION');
      logger.info('─'.repeat(60));
      const verificationResult = await this.verification.verify(
        initialAnswer,
        evidence,
        query
      );
      logger.info(`✓ Verification complete`);
      logger.info(`  Valid: ${verificationResult.isValid}`);
      logger.info(`  Confidence: ${verificationResult.confidence.toFixed(2)}`);
      logger.info(`  Issues: ${verificationResult.issues.length}`);

      // STEP 5: REFINEMENT
      let finalAnswer = initialAnswer;
      let finalConfidence = reasoningChain.confidence;
      let refinementIterations: any[] = [];

      if (!skipRefinement) {
        logger.info('\n🔄 STEP 5: REFINEMENT');
        logger.info('─'.repeat(60));
        const refinement = await this.refinement.refine(
          query,
          initialAnswer,
          evidence,
          maxIterations,
          confidenceThreshold
        );
        logger.info(`✓ Refinement complete: ${refinement.iterations.length} iteration(s)`);
        logger.info(`  Final confidence: ${refinement.confidence.toFixed(2)}`);

        finalAnswer = refinement.finalAnswer;
        finalConfidence = refinement.confidence;
        refinementIterations = refinement.iterations;
      } else {
        logger.info('\n⏭️  STEP 5: REFINEMENT (SKIPPED)');
      }

      // FINAL RESULT
      const processingTime = Date.now() - startTime;
      logger.info('\n═══════════════════════════════════════════════════════');
      logger.info('✅ AGENTIC EXECUTION COMPLETE');
      logger.info(`  Processing time: ${processingTime}ms`);
      logger.info(`  Final confidence: ${finalConfidence.toFixed(2)}`);
      logger.info('═══════════════════════════════════════════════════════\n');

      return {
        answer: finalAnswer,
        confidence: finalConfidence,
        sources: reasoningResult.sources, // Add source citations
        evidenceMap: reasoningResult.evidenceMap, // Add evidence mapping
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
                clarity: 0.85, // Placeholder
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
          confidence: 0.9, // Bridge paths are highly reliable
          isPrimary: true,
          nodeId: nodeIds[0], // Primary node for this evidence
          nodeLabel: path.nodes[0].label,
          nodeType: path.nodes[0].type || 'concept',
          nodePath: nodeIds, // Full path of node IDs
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
      // Extract first representative node ID if available
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
        nodeId: nodeId, // Community representative node
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
    // Find the synthesis step
    const synthesisStep = reasoning.steps.find(
      (step: any) => step.action === 'synthesize'
    );

    if (synthesisStep && synthesisStep.output && synthesisStep.output.answer) {
      return synthesisStep.output.answer;
    }

    // Fallback: use last step's output
    const lastStep = reasoning.steps[reasoning.steps.length - 1];
    if (lastStep && lastStep.output) {
      if (typeof lastStep.output === 'string') {
        return lastStep.output;
      }
      if (lastStep.output.answer) {
        return lastStep.output.answer;
      }
    }

    // Last resort
    return 'Unable to generate answer from reasoning chain.';
  }

  /**
   * Execute plan with multiple sub-questions
   */
  private async executePlan(plan: any): Promise<string[]> {
    const results: string[] = [];

    if (plan.strategy.mode === 'parallel' && plan.subQuestions.length <= 3) {
      // Execute in parallel
      logger.info('Executing sub-questions in parallel');
      const promises = plan.subQuestions.map((sq: any) =>
        this.executeSubQuestion(sq.question)
      );
      results.push(...await Promise.all(promises));
    } else {
      // Execute sequentially
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
        // Get node IDs from community members
        const nodeIds = new Set<string>();
        for (const community of retrieval.communities) {
          if (community.members) {
            community.members.forEach((id: string) => nodeIds.add(id));
          }
        }

        // Fetch nodes from database
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
      // Retrieval health check would need implementation
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
