/**
 * Planning Agent
 *
 * Decomposes complex queries into manageable sub-questions and determines
 * optimal execution strategy.
 *
 * Capabilities:
 * - Query complexity assessment
 * - Sub-question generation
 * - Dependency analysis
 * - Strategy determination (sequential/parallel/adaptive)
 */

import { LLMService } from '../llm';
import { QueryPlan, SubQuestion, ExecutionStrategy } from '../../types/agentic';
import { QueryType, QueryClassification } from '../../types';
import { getLogger } from '../../utils/logger';

const logger = getLogger('PlanningAgent');

export class PlanningAgent {
  private llm: LLMService;
  private classificationCache: Map<string, QueryClassification> = new Map();

  constructor(llm: LLMService) {
    this.llm = llm;
  }

  /**
   * Create execution plan for query
   */
  async plan(query: string): Promise<QueryPlan> {
    logger.info(`Planning execution for query: "${query.substring(0, 50)}..."`);

    const startTime = Date.now();

    // Step 1: Assess complexity
    const complexity = await this.assessComplexity(query);
    logger.info(`Query complexity: ${complexity}`);

    // Step 2: Decompose if complex
    let subQuestions: SubQuestion[];
    if (complexity === 'simple') {
      subQuestions = [{
        id: 'q1',
        question: query,
        type: 'global_abstract',
        dependencies: [],
        priority: 1,
        status: 'pending',
      }];
    } else {
      subQuestions = await this.decompose(query);
    }

    // Step 3: Determine execution strategy
    const strategy = this.determineStrategy(subQuestions);

    const planTime = Date.now() - startTime;
    logger.info(
      `Plan created: ${subQuestions.length} sub-questions, ` +
      `${strategy.mode} execution (${planTime}ms)`
    );

    return {
      originalQuery: query,
      subQuestions,
      strategy,
      estimatedSteps: subQuestions.length,
    };
  }

  /**
   * Rule-based classification fallback (no LLM needed)
   */
  private classifyByRules(query: string): QueryType {
    const lower = query.toLowerCase();

    // Multi-hop patterns (HIGHEST PRIORITY - check first)
    // These require finding connections across distant concepts
    if (lower.match(/how did .* influence|connection between .* and|path from .* to|link between|bridge.*between|trace.*from.*to|relationship between .* and|impact of .* on|effect of .* on|what connects|how .* led to|how .* affected|how .* shaped/i)) {
      return 'multi_hop';
    }

    // Comparative patterns
    if (lower.match(/compare|versus|vs\.?|differ.*from|contrast|between.*and/i)) {
      return 'comparative';
    }

    // Temporal evolution patterns (without influence which is multi-hop)
    if (lower.match(/evolve|evolution|development|history|from.*to|change.*over|led to/i) &&
        !lower.match(/influence|impact|effect|affected|shaped/i)) {
      return 'temporal_evolution';
    }

    // Specific entity patterns (mentions specific philosophers)
    const philosophers = ['chrysippus', 'aristotle', 'epictetus', 'cicero', 'seneca', 'marcus aurelius', 'plato', 'plotinus', 'augustine', 'aquinas'];
    if (philosophers.some(p => lower.includes(p)) || lower.match(/what did .* say|who (is|was)/i)) {
      return 'specific_entity';
    }

    // Dialectical patterns (arguments/debates)
    if (lower.match(/argument|objection|response|critique|defense|refut|debate|controversy/i)) {
      return 'dialectical';
    }

    // Default: global abstract (e.g., "What is Stoic free will?")
    return 'global_abstract';
  }

  /**
   * Assess query complexity
   */
  private async assessComplexity(query: string): Promise<'simple' | 'complex'> {
    // First, try rule-based assessment
    const ruleBasedComplex = this.assessComplexityByRules(query);
    if (ruleBasedComplex !== null) {
      return ruleBasedComplex;
    }

    // Fallback to LLM
    const prompt = `Assess if this philosophical query is SIMPLE or COMPLEX:

Query: "${query}"

SIMPLE queries:
- Single focus
- Ask about one concept/entity
- Examples:
  * "What is Stoic free will?"
  * "What did Chrysippus say about fate?"
  * "Define prohairesis"

COMPLEX queries:
- Multiple parts
- Comparisons
- Temporal evolution
- Multiple entities
- Examples:
  * "Compare Stoic and Epicurean views on free will"
  * "How did prohairesis evolve from Aristotle to Epictetus?"
  * "What are arguments for and against compatibilism?"

Respond ONLY with JSON (no markdown):
{"complexity": "simple" | "complex", "reason": "brief explanation"}`;

    try {
      const response = await this.llm.generateWithRetry(prompt, 'gemini-3-flash-preview', 2);

      // Clean response (remove markdown if present)
      const cleaned = response.replace(/```json\n?|\n?```/g, '').trim();
      const result = JSON.parse(cleaned);

      logger.info(`Complexity: ${result.complexity} - ${result.reason}`);
      return result.complexity;
    } catch (error) {
      logger.error('Complexity assessment failed, using safe default', error);
      // Safe default: treat as simple
      return 'simple';
    }
  }

  /**
   * Rule-based complexity assessment (fast, no LLM)
   */
  private assessComplexityByRules(query: string): 'simple' | 'complex' | null {
    const lower = query.toLowerCase();

    // Definitely complex patterns
    if (lower.match(/compare.*and|versus|vs\.?|from.*to.*via|multiple|several|various/i)) {
      return 'complex';
    }

    // Definitely simple patterns
    if (lower.match(/^what (is|was)|^define|^explain .* in.*words$/i)) {
      return 'simple';
    }

    // Uncertain - let LLM decide
    return null;
  }

  /**
   * Decompose complex query into sub-questions
   */
  private async decompose(query: string): Promise<SubQuestion[]> {
    const prompt = `Decompose this complex philosophical query into simpler sub-questions.

Query: "${query}"

Guidelines:
1. Create 2-5 sub-questions (not more!)
2. Each should be independently answerable
3. Identify dependencies (which must be answered first)
4. Assign priorities (1 = first, 2 = depends on 1, etc.)
5. Classify each question type:
   - global_abstract: "What is X philosophy?"
   - specific_entity: "What did philosopher X say?"
   - comparative: "How do X and Y differ?"
   - temporal_evolution: "How did X change over time?"
   - dialectical: "Arguments for/against X"
   - multi_hop: "How did X influence Y?" (connections across concepts)

Example:
Query: "Compare Stoic and Epicurean responses to determinism"

Output:
[
  {
    "id": "q1",
    "question": "What is the Stoic view on determinism and fate?",
    "type": "global_abstract",
    "dependencies": [],
    "priority": 1
  },
  {
    "id": "q2",
    "question": "What is the Epicurean view on determinism and atomic swerve?",
    "type": "global_abstract",
    "dependencies": [],
    "priority": 1
  },
  {
    "id": "q3",
    "question": "How do these two approaches differ?",
    "type": "comparative",
    "dependencies": ["q1", "q2"],
    "priority": 2
  }
]

Respond ONLY with JSON array (no markdown):`;

    try {
      const response = await this.llm.generateWithRetry(prompt, 'gemini-3-flash-preview', 2);

      // Clean response
      const cleaned = response.replace(/```json\n?|\n?```/g, '').trim();
      const subQuestions = JSON.parse(cleaned);

      // Validate and add status
      const validated = subQuestions.map((sq: any, index: number) => ({
        id: sq.id || `q${index + 1}`,
        question: sq.question,
        type: sq.type || 'global_abstract',
        dependencies: sq.dependencies || [],
        priority: sq.priority || 1,
        status: 'pending' as const,
      }));

      logger.info(`Decomposed into ${validated.length} sub-questions`);
      return validated;
    } catch (error) {
      logger.error('Query decomposition failed, using single-question fallback', error);

      // Fallback: treat as single question with rule-based type classification
      const type = this.classifyByRules(query);
      return [{
        id: 'q1',
        question: query,
        type,
        dependencies: [],
        priority: 1,
        status: 'pending',
      }];
    }
  }

  /**
   * Determine optimal execution strategy
   */
  private determineStrategy(subQuestions: SubQuestion[]): ExecutionStrategy {
    // Check for dependencies
    const hasDependencies = subQuestions.some(sq => sq.dependencies.length > 0);

    // Check for priority levels
    const priorities = new Set(subQuestions.map(sq => sq.priority));
    const hasMultiplePriorities = priorities.size > 1;

    let mode: 'sequential' | 'parallel' | 'adaptive';

    if (hasDependencies || hasMultiplePriorities) {
      mode = 'sequential'; // Must execute in order
    } else if (subQuestions.length <= 3) {
      mode = 'parallel'; // Can execute simultaneously
    } else {
      mode = 'adaptive'; // Mix of parallel and sequential
    }

    return {
      mode,
      maxIterations: 3,
      confidenceThreshold: 0.8,
    };
  }

  /**
   * Validate and optimize plan
   */
  async optimizePlan(plan: QueryPlan): Promise<QueryPlan> {
    // Remove duplicate questions
    const uniqueQuestions = new Map<string, SubQuestion>();
    for (const sq of plan.subQuestions) {
      const normalized = sq.question.toLowerCase().trim();
      if (!uniqueQuestions.has(normalized)) {
        uniqueQuestions.set(normalized, sq);
      }
    }

    return {
      ...plan,
      subQuestions: Array.from(uniqueQuestions.values()),
      estimatedSteps: uniqueQuestions.size,
    };
  }

  /**
   * Get next sub-question to execute based on dependencies
   */
  getNextQuestion(plan: QueryPlan): SubQuestion | null {
    // Find pending question with no pending dependencies
    for (const sq of plan.subQuestions) {
      if (sq.status !== 'pending') continue;

      // Check if all dependencies are completed
      const dependenciesComplete = sq.dependencies.every(depId => {
        const dep = plan.subQuestions.find(q => q.id === depId);
        return dep?.status === 'completed';
      });

      if (dependenciesComplete) {
        return sq;
      }
    }

    return null;
  }

  /**
   * Update sub-question status
   */
  updateQuestionStatus(
    plan: QueryPlan,
    questionId: string,
    status: 'pending' | 'in_progress' | 'completed',
    result?: any
  ): QueryPlan {
    return {
      ...plan,
      subQuestions: plan.subQuestions.map(sq =>
        sq.id === questionId
          ? { ...sq, status, result }
          : sq
      ),
    };
  }

  /**
   * Check if plan is complete
   */
  isPlanComplete(plan: QueryPlan): boolean {
    return plan.subQuestions.every(sq => sq.status === 'completed');
  }
}
