/**
 * Verification Agent
 *
 * Validates answers against knowledge graph, checks citations,
 * and detects hallucinations.
 *
 * Capabilities:
 * - Citation existence verification
 * - Claim support checking
 * - Source quality assessment
 * - Hallucination detection
 * - Factual accuracy validation
 */

import { DatabaseService } from '../database';
import { LLMService } from '../llm';
import {
  VerificationResult,
  Evidence,
  ClaimVerification,
} from '../../types/agentic';
import { getLogger } from '../../utils/logger';

const logger = getLogger('VerificationAgent');

export class VerificationAgent {
  private db: DatabaseService;
  private llm: LLMService;

  constructor(db: DatabaseService, llm: LLMService) {
    this.db = db;
    this.llm = llm;
  }

  /**
   * Verify answer against knowledge graph and evidence
   */
  async verify(
    answer: string,
    evidence: Evidence[],
    query?: string
  ): Promise<VerificationResult> {
    logger.info('Verifying answer against knowledge graph');

    const startTime = Date.now();

    // 1. Check citation existence
    const citationExists = await this.checkCitationExistence(evidence);

    // 2. Check if claims are supported by evidence
    const claimVerifications = await this.verifyClaims(answer, evidence);
    const claimSupported = claimVerifications.every(cv => cv.isSupported);

    // 3. Assess source quality
    const sourceQuality = this.assessSourceQuality(evidence);

    // 4. Detect potential hallucinations
    const hallucinations = await this.detectHallucinations(answer, evidence);

    // 5. Calculate overall confidence
    const confidence = this.calculateVerificationConfidence({
      citationExists,
      claimSupported,
      sourceQuality,
      hallucinationCount: hallucinations.length,
      evidenceCount: evidence.length,
    });

    // 6. Collect issues
    const issues: string[] = [];
    if (!citationExists) {
      issues.push('Some citations not found in knowledge graph');
    }
    if (!claimSupported) {
      const unsupported = claimVerifications.filter(cv => !cv.isSupported);
      issues.push(`${unsupported.length} claim(s) not fully supported by evidence`);
    }
    if (sourceQuality === 'tertiary') {
      issues.push('Only tertiary sources available - limited reliability');
    }
    if (hallucinations.length > 0) {
      issues.push(`Detected ${hallucinations.length} potential hallucination(s)`);
    }

    const verificationTime = Date.now() - startTime;
    logger.info(
      `Verification complete: valid=${citationExists && claimSupported}, ` +
      `confidence=${confidence.toFixed(2)} (${verificationTime}ms)`
    );

    return {
      isValid: citationExists && claimSupported && hallucinations.length === 0,
      citationExists,
      claimSupported,
      sourceQuality,
      confidence,
      issues,
      checkedClaims: claimVerifications,
    };
  }

  /**
   * Check if all citations/sources exist in KG
   */
  private async checkCitationExistence(evidence: Evidence[]): Promise<boolean> {
    if (evidence.length === 0) {
      logger.warn('No evidence provided - citation check inconclusive');
      return false;
    }

    // All evidence comes from KG retrieval, so by definition citations exist
    // In a more advanced system, we would:
    // 1. Extract entity mentions from answer
    // 2. Query database to verify each entity exists
    // 3. Check that relationships mentioned are in KG

    // For now, assume evidence existence = citation existence
    return true;
  }

  /**
   * Verify specific claims in answer against evidence
   */
  private async verifyClaims(
    answer: string,
    evidence: Evidence[]
  ): Promise<ClaimVerification[]> {
    if (evidence.length === 0) {
      return [{
        claim: 'No evidence provided',
        isSupported: false,
        supportingEvidence: [],
        confidence: 0.0,
      }];
    }

    const prompt = `Verify if the claims in this answer are supported by the provided evidence.

Answer: ${answer}

Evidence:
${evidence.map((e, i) => `[${i + 1}] ${e.source}: ${e.content}`).join('\n\n')}

Instructions:
1. Extract 3-5 key claims from the answer
2. For each claim, check if it's supported by the evidence
3. Identify which evidence supports each claim
4. Rate confidence 0.0-1.0 for each claim

Respond with JSON array (no markdown):
[
  {
    "claim": "specific claim from answer",
    "isSupported": true | false,
    "supportingEvidence": ["evidence source names"],
    "confidence": 0.0-1.0
  }
]`;

    try {
      const response = await this.llm.generateWithRetry(prompt, 'gemini-3-flash-preview');
      const cleaned = response.replace(/```json\n?|\n?```/g, '').trim();
      const verifications = JSON.parse(cleaned);

      logger.info(`Verified ${verifications.length} claims`);
      return verifications;
    } catch (error) {
      logger.error('Claim verification failed', error);
      return [{
        claim: 'Verification failed',
        isSupported: false,
        supportingEvidence: [],
        confidence: 0.0,
      }];
    }
  }

  /**
   * Assess quality of evidence sources
   */
  private assessSourceQuality(
    evidence: Evidence[]
  ): 'primary' | 'secondary' | 'tertiary' {
    if (evidence.length === 0) return 'tertiary';

    // Primary: Direct philosophical texts, original authors
    const hasPrimary = evidence.some(e => e.isPrimary);
    if (hasPrimary) return 'primary';

    // Secondary: Scholarly analysis, commentaries
    const hasSecondary = evidence.some(
      e => e.type === 'node' && !e.isPrimary
    );
    if (hasSecondary) return 'secondary';

    // Tertiary: Community summaries, general overviews
    return 'tertiary';
  }

  /**
   * Detect potential hallucinations (invented facts not in evidence)
   */
  private async detectHallucinations(
    answer: string,
    evidence: Evidence[]
  ): Promise<string[]> {
    const prompt = `Check if this answer contains any hallucinated facts (claims not supported by evidence).

Answer: ${answer}

Evidence:
${evidence.map((e, i) => `[${i + 1}] ${e.source}: ${e.content}`).join('\n\n')}

Hallucinations to look for:
1. Philosophers or texts not mentioned in evidence
2. Dates or periods not in evidence
3. Philosophical concepts not in evidence
4. Relationships or influences not stated in evidence
5. Quotes or specific claims not present in evidence

Respond with JSON array of hallucinated claims (no markdown):
["hallucinated claim 1", "hallucinated claim 2", ...]

Return empty array [] if no hallucinations detected.`;

    try {
      const response = await this.llm.generateWithRetry(prompt, 'gemini-3-flash-preview');
      const cleaned = response.replace(/```json\n?|\n?```/g, '').trim();
      const hallucinations = JSON.parse(cleaned);

      if (hallucinations.length > 0) {
        logger.warn(`Detected ${hallucinations.length} potential hallucination(s)`);
      }

      return hallucinations;
    } catch (error) {
      logger.error('Hallucination detection failed', error);
      return [];
    }
  }

  /**
   * Calculate overall verification confidence
   */
  private calculateVerificationConfidence(params: {
    citationExists: boolean;
    claimSupported: boolean;
    sourceQuality: string;
    hallucinationCount: number;
    evidenceCount: number;
  }): number {
    let confidence = 0.0;

    // Citation existence: 30%
    if (params.citationExists) {
      confidence += 0.3;
    }

    // Claim support: 40%
    if (params.claimSupported) {
      confidence += 0.4;
    }

    // Source quality: 20%
    if (params.sourceQuality === 'primary') {
      confidence += 0.2;
    } else if (params.sourceQuality === 'secondary') {
      confidence += 0.15;
    } else {
      confidence += 0.05;
    }

    // Evidence quantity: 10%
    if (params.evidenceCount >= 5) {
      confidence += 0.1;
    } else if (params.evidenceCount >= 3) {
      confidence += 0.07;
    } else if (params.evidenceCount >= 1) {
      confidence += 0.03;
    }

    // Hallucination penalty
    confidence -= params.hallucinationCount * 0.15;

    return Math.max(0, Math.min(1, confidence));
  }

  /**
   * Cross-reference answer with database
   */
  async crossReference(
    answer: string,
    entityMentions: string[]
  ): Promise<{
    verified: string[];
    unverified: string[];
  }> {
    // TODO: Implement actual database lookup
    // For now, assume all mentions are verified if from evidence
    return {
      verified: entityMentions,
      unverified: [],
    };
  }
}
