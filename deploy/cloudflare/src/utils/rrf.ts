/**
 * Reciprocal Rank Fusion (RRF) Algorithm
 *
 * Combines multiple ranked lists using the formula:
 * score(d) = Σ (1 / (k + rank_i))
 *
 * where:
 * - d is a document/point
 * - k is a constant (typically 60)
 * - rank_i is the rank of d in the i-th list
 *
 * Reference: Cormack et al. (2009) "Reciprocal Rank Fusion outperforms Condorcet"
 */

export interface RankedResult {
  id: string | number;
  score: number;
  payload?: Record<string, any>;
  [key: string]: any;
}

export interface RRFResult extends RankedResult {
  rrf_score: number;
  sources: string[];
  original_scores: Record<string, number>;
  ranks: Record<string, number>;
}

/**
 * Apply Reciprocal Rank Fusion to combine multiple ranked result lists
 *
 * @param resultLists - Object mapping source names to ranked result lists
 * @param k - RRF constant (default: 60)
 * @returns Combined results sorted by RRF score (descending)
 */
export function reciprocalRankFusion(
  resultLists: Record<string, RankedResult[]>,
  k: number = 60
): RRFResult[] {
  // Map to accumulate RRF scores
  const rrfScores = new Map<string | number, {
    score: number;
    sources: Set<string>;
    original_scores: Record<string, number>;
    ranks: Record<string, number>;
    payload: Record<string, any>;
  }>();

  // Process each result list
  for (const [sourceName, results] of Object.entries(resultLists)) {
    results.forEach((result, index) => {
      const rank = index + 1; // 1-indexed rank
      const rrfContribution = 1 / (k + rank);
      const id = result.id;

      if (!rrfScores.has(id)) {
        rrfScores.set(id, {
          score: 0,
          sources: new Set(),
          original_scores: {},
          ranks: {},
          payload: result.payload || {},
        });
      }

      const entry = rrfScores.get(id)!;
      entry.score += rrfContribution;
      entry.sources.add(sourceName);
      entry.original_scores[sourceName] = result.score;
      entry.ranks[sourceName] = rank;

      // Merge payload (prefer non-null values)
      if (result.payload) {
        entry.payload = { ...entry.payload, ...result.payload };
      }
    });
  }

  // Convert to array and sort by RRF score descending
  const fusedResults: RRFResult[] = Array.from(rrfScores.entries()).map(
    ([id, data]) => ({
      id,
      score: data.score,  // Keep original score field for compatibility
      rrf_score: data.score,
      sources: Array.from(data.sources),
      original_scores: data.original_scores,
      ranks: data.ranks,
      payload: data.payload,
    })
  );

  fusedResults.sort((a, b) => b.rrf_score - a.rrf_score);

  return fusedResults;
}

