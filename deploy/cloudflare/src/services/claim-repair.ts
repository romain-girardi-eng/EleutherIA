/**
 * Claim Repair Service (Self-RAG Patch)
 *
 * For unsupported claims, uses targeted LLM correction to either:
 * - Rewrite the claim so it is fully supported by cited sources
 * - Remove the claim if it cannot be supported
 *
 * Strict output contract: no new facts, no new sources.
 * Max 2 retries per claim.
 */

import { ClaimUnit, SourceCitationLike, ClaimRepairResult } from '../types';
import { LLMService } from './llm';
import { buildVerificationContext } from './claim-verifier';
import { REPAIR_PROMPT_TEMPLATE } from '../prompts/graphrag';
import { getLogger } from '../utils/logger';

const logger = getLogger('ClaimRepair');

const MAX_RETRIES = 2;

/**
 * Repair a single unsupported claim using targeted LLM correction.
 */
export async function repairUnsupportedClaim(
  claim: ClaimUnit,
  sources: SourceCitationLike[],
  llm: LLMService,
): Promise<ClaimRepairResult> {
  const sourceContext = buildVerificationContext(claim, sources);

  if (!sourceContext.trim()) {
    // No source context at all — cannot repair, remove
    return {
      claimId: claim.claimId,
      action: 'remove',
      originalText: claim.text,
      mappedNodeIds: [],
    };
  }

  let lastResult: ClaimRepairResult | null = null;

  for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
    const prompt = REPAIR_PROMPT_TEMPLATE
      .replace('{{CLAIM_TEXT}}', claim.text)
      .replace('{{SOURCE_CONTEXT}}', sourceContext);

    try {
      const response = await llm.generateForTask(prompt, 'self_rag');
      const parsed = parseRepairResponse(response, claim);

      if (parsed.action === 'rewrite' && parsed.rewrittenText) {
        // Verify the rewrite doesn't introduce new citation markers
        const originalMarkers = new Set(claim.citationMarkers);
        const newMarkerRegex = /\[(\d+)\]/g;
        let match: RegExpExecArray | null;
        let hasNewMarkers = false;
        while ((match = newMarkerRegex.exec(parsed.rewrittenText)) !== null) {
          if (!originalMarkers.has(parseInt(match[1], 10))) {
            hasNewMarkers = true;
            break;
          }
        }

        if (hasNewMarkers) {
          logger.warn(`Repair attempt ${attempt + 1} introduced new markers, retrying`);
          lastResult = parsed;
          continue;
        }

        return parsed;
      }

      if (parsed.action === 'remove') {
        return parsed;
      }

      // Unexpected action, retry
      lastResult = parsed;
    } catch (error) {
      logger.error(`Repair attempt ${attempt + 1} failed`, error);
      lastResult = {
        claimId: claim.claimId,
        action: 'remove',
        originalText: claim.text,
        mappedNodeIds: [],
      };
    }
  }

  // All retries exhausted — remove claim
  logger.warn(`All repair attempts failed for claim ${claim.claimId}, removing`);
  return {
    claimId: claim.claimId,
    action: 'remove',
    originalText: claim.text,
    mappedNodeIds: [],
  };
}

/**
 * Repair all unsupported claims in a batch.
 */
export async function repairUnsupportedClaimsBatch(
  claims: ClaimUnit[],
  sources: SourceCitationLike[],
  llm: LLMService,
): Promise<Map<string, ClaimRepairResult>> {
  const unsupported = claims.filter(c => c.status === 'unsupported');
  const results = new Map<string, ClaimRepairResult>();

  // Process sequentially to avoid LLM rate limits
  for (const claim of unsupported) {
    const result = await repairUnsupportedClaim(claim, sources, llm);
    results.set(claim.claimId, result);
  }

  logger.info(`Repaired ${results.size} unsupported claims: ${
    Array.from(results.values()).filter(r => r.action === 'rewrite').length
  } rewritten, ${
    Array.from(results.values()).filter(r => r.action === 'remove').length
  } removed`);

  return results;
}

/**
 * Apply repair results to the answer text.
 * Replaces rewritten claims and removes deleted ones.
 */
export function applyRepairs(
  answer: string,
  claims: ClaimUnit[],
  repairs: Map<string, ClaimRepairResult>,
): string {
  let result = answer;

  for (const claim of claims) {
    const repair = repairs.get(claim.claimId);
    if (!repair) continue;

    if (repair.action === 'rewrite' && repair.rewrittenText) {
      result = result.replace(claim.text, repair.rewrittenText);
    } else if (repair.action === 'remove') {
      // Remove the claim sentence. Clean up trailing whitespace.
      result = result.replace(claim.text, '');
    }
  }

  // Clean up artifacts from removals
  result = result
    .replace(/\n{3,}/g, '\n\n')
    .replace(/  +/g, ' ')
    .trim();

  return result;
}

function parseRepairResponse(
  response: string,
  claim: ClaimUnit,
): ClaimRepairResult {
  try {
    // Try to parse as JSON
    const jsonMatch = response.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0]);

      if (parsed.action === 'REMOVE' || parsed.action === 'remove') {
        return {
          claimId: claim.claimId,
          action: 'remove',
          originalText: claim.text,
          mappedNodeIds: [],
        };
      }

      if (parsed.rewritten_claim || parsed.rewrittenClaim || parsed.text) {
        const rewrittenText = parsed.rewritten_claim || parsed.rewrittenClaim || parsed.text;
        return {
          claimId: claim.claimId,
          action: 'rewrite',
          originalText: claim.text,
          rewrittenText,
          mappedNodeIds: parsed.source_node_ids || parsed.mappedNodeIds || claim.sourceNodeIds,
        };
      }
    }

    // Check for plain text REMOVE
    if (response.trim().toUpperCase() === 'REMOVE') {
      return {
        claimId: claim.claimId,
        action: 'remove',
        originalText: claim.text,
        mappedNodeIds: [],
      };
    }

    // If response looks like a rewritten claim
    if (response.trim().length > 10 && !response.includes('{')) {
      return {
        claimId: claim.claimId,
        action: 'rewrite',
        originalText: claim.text,
        rewrittenText: response.trim(),
        mappedNodeIds: claim.sourceNodeIds,
      };
    }
  } catch {
    logger.warn('Failed to parse repair response');
  }

  // Default: remove
  return {
    claimId: claim.claimId,
    action: 'remove',
    originalText: claim.text,
    mappedNodeIds: [],
  };
}
