/**
 * Utilities for knowledge graph payloads.
 */

/**
 * Remove very large properties (embeddings, vectors, raw text blobs) from node payloads
 * before returning them to the client. These fields can contain tens of thousands of
 * numbers or characters and easily blow past Cloudflare Workers memory limits.
 */
export function sanitizeNodePayload<T extends Record<string, any>>(node: T): T {
  if (!node) {
    return node;
  }

  const sanitized = { ...node } as Record<string, any>;

  for (const key of Object.keys(sanitized)) {
    const lowerKey = key.toLowerCase();

    if (
      lowerKey.includes('embedding') ||
      lowerKey.includes('vector') ||
      lowerKey.includes('full_text') ||
      lowerKey.includes('tei_xml')
    ) {
      delete sanitized[key];
    }
  }

  return sanitized as T;
}
