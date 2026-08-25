/**
 * Citation Service
 * Handles fetching citation passages from ancient texts
 */

import { apiEndpoint } from '../api/baseUrl';

export interface CitationPassage {
  citation: string;
  original: string | null;
  originalLanguage: string | null;
  translation: string | null;
  text_id?: string;
  title?: string;
  author?: string;
  error?: string;
  note?: string;
}

/**
 * Fetch the passage text for a given citation reference
 * @param citation Citation reference (e.g., "Cicero, On Fate 41-43")
 * @returns Citation passage with original text and translation
 */
export async function fetchCitationPassage(citation: string): Promise<CitationPassage> {
  try {
    const response = await fetch(apiEndpoint('/api/text/citation-passage'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ citation }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching citation passage:', error);
    return {
      citation,
      original: null,
      originalLanguage: null,
      translation: null,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Fetch citation passages for multiple citations
 * @param citations Array of citation references
 * @returns Map of citation -> passage data
 */
export async function fetchCitationPassages(
  citations: string[]
): Promise<Record<string, CitationPassage>> {
  const results: Record<string, CitationPassage> = {};

  // Fetch in parallel with limit to avoid overwhelming the server
  const batchSize = 5;
  for (let i = 0; i < citations.length; i += batchSize) {
    const batch = citations.slice(i, i + batchSize);
    const promises = batch.map((citation) => fetchCitationPassage(citation));
    const batchResults = await Promise.all(promises);

    batchResults.forEach((result) => {
      if (result.original || result.translation) {
        results[result.citation] = result;
      }
    });
  }

  return results;
}
