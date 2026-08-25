import { describe, expect, it } from 'vitest';

import { glossary } from '../content/glossary';
import { resolveSeoRoute, sitemapRoutes, structuredDataFor } from './seo';

describe('release-built glossary entity SEO', () => {
  it('resolves a pending entity before the generic prefix but keeps it fail-closed', () => {
    const entity = glossary[0];
    const route = resolveSeoRoute(entity.nodeUrl);
    expect(route.entityId).toBe(entity.id);
    expect(route.robots).toBe('noindex, follow');
    expect(route.description.length).toBeLessThanOrEqual(220);
    expect(structuredDataFor(route)).toEqual([]);
  });

  it('keeps arbitrary graph IDs noindex and out of structured data', () => {
    const route = resolveSeoRoute('/visualizer/not-a-reviewed-public-entity');
    expect(route.robots).toMatch(/noindex/);
    expect(structuredDataFor(route)).toEqual([]);
  });

  it('keeps pending entities out of the sitemap route set', () => {
    const paths = sitemapRoutes().map((route) => route.path);
    for (const entity of glossary) {
      expect(paths).not.toContain(entity.nodeUrl);
    }
  });
});
