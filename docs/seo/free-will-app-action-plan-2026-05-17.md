# SEO Action Plan: free-will.app

Date: 2026-05-17

## Phase 1: Indexing Blockers

Priority: Critical
Target: Same day

1. Add valid `public/robots.txt`.

```txt
User-agent: *
Allow: /

Sitemap: https://free-will.app/sitemap.xml
```

2. Generate `public/sitemap.xml`.

Include:

- `/`
- `/how-it-works`
- `/database`
- `/graphrag`
- `/graphrag-showcase`
- `/research`
- `/texts`
- `/bibliography`
- `/about`
- `/credits`
- `/recherches`
- `/contributions`
- `/passages-canoniques`
- Public detail pages that are stable and index-worthy

Exclude:

- `/login`
- `/admin`
- `/profile`
- `/contribuer`
- unknown/catch-all routes

3. Fix canonical URL generation.

Each public route must self-canonicalize. Do not point every page to `/`.

4. Fix unknown-route status handling.

Serve real HTTP 404 responses for unmatched paths. If hosting cannot do this directly for SPA fallback, add an edge function or switch public SEO pages to SSR/SSG.

5. Fix `/texts`.

The API endpoint currently returns HTTP 500:

`https://free-will.app/api/works?offset=0&limit=500&sort_by=most_cited`

Fix the server error and make sure 4xx/5xx API responses include the same CORS policy as successful responses.

## Phase 2: Make Public Pages Crawlable

Priority: High
Target: 1 week

1. Add SSR/SSG/prerendering for indexable public routes.

Minimum pre-render set:

- `/`
- `/how-it-works`
- `/database`
- `/graphrag-showcase`
- `/research`
- `/texts`
- `/bibliography`
- `/about`
- `/credits`
- `/recherches`
- `/contributions`
- `/passages-canoniques`

Each pre-rendered route should contain:

- one H1
- route-specific title and meta description
- self-canonical link
- crawlable internal links
- meaningful body copy
- route-specific Open Graph/Twitter tags
- JSON-LD where applicable

2. Mark utility/protected routes as noindex.

Use:

```html
<meta name="robots" content="noindex, nofollow" />
```

For:

- `/login`
- `/admin`
- `/profile`
- `/contribuer`
- any private share/admin/moderation pages not intended for search

## Phase 3: Structured Data

Priority: High
Target: 1 week

1. Add homepage/about JSON-LD.

Recommended graph:

- `WebSite`
- `Person` for Romain Girardi, or `Organization` if publishing under a lab/project entity
- `Dataset`
- `SoftwareApplication`

2. Add Dataset markup.

Include:

- `name`
- `description`
- `creator`
- `identifier` with DOI
- `license`
- `keywords`
- `isAccessibleForFree`
- `sameAs` links to Zenodo, GitHub, PyPI, PhilPapers if appropriate

3. Add BreadcrumbList.

Add breadcrumbs for public pages and detail pages.

4. Add CreativeWork/ScholarlyArticle markup where appropriate.

Use on:

- published research pages
- canonical passage detail pages
- ancient work/text detail pages

## Phase 4: Performance

Priority: High
Target: 2 weeks

1. Remove the graph payloads from the homepage critical path.

Current largest homepage payloads:

- `ParticleCloud-data.json`: about 6.8 MB transferred
- `philosopher-particles.json`: about 4.7 MB transferred

2. Replace initial animated graph with a light poster state.

Load the interactive graph after:

- first paint
- user interaction
- `requestIdleCallback`
- or after the visible content is stable

3. Split route bundles.

Do not preload `cosmograph-vendor`, charts, animation vendor, or graph data on routes that do not need them immediately.

4. Improve cache policy.

Hashed assets can use:

```txt
Cache-Control: public, max-age=31536000, immutable
```

Keep HTML short-lived.

5. Add image dimensions.

Add `width` and `height` attributes to logo and visual assets.

## Phase 5: Metadata And Content

Priority: Medium
Target: 1 month

1. Add route-specific titles and descriptions.

Suggested titles:

- `/`: `EleutherIA | Ancient Free Will Knowledge Graph`
- `/how-it-works`: `How EleutherIA Works | Knowledge Graph, Embeddings, GraphRAG`
- `/database`: `EleutherIA Database Overview | Ancient Free Will Knowledge Graph`
- `/graphrag`: `GraphRAG Q&A for Ancient Free Will | EleutherIA`
- `/graphrag-showcase`: `Agentic GraphRAG for Ancient Philosophy | EleutherIA`
- `/texts`: `Ancient Works Library | EleutherIA`
- `/bibliography`: `Bibliography on Ancient Free Will | EleutherIA`
- `/passages-canoniques`: `Canonical Free Will Passages | EleutherIA`
- `/about`: `About EleutherIA | Romain Girardi`

2. Add or improve H1 structure.

Fix:

- `/` has duplicate H1s
- `/visualizer` has no H1
- `/graph` has no H1
- `/login` has no H1, and should likely be noindexed

3. Add `llms.txt`.

Include:

- one-line project summary
- canonical URLs
- dataset DOI
- license
- creator/contact
- preferred citation
- links to public data/docs

4. Fix manifest shortcut.

`/search` is listed in the PWA manifest but is not a defined app route. Add the route or remove/update the shortcut.

## Verification Checklist

After implementation:

1. `curl https://free-will.app/robots.txt` returns valid text rules.
2. `curl https://free-will.app/sitemap.xml` returns valid XML.
3. `curl https://free-will.app/about` contains route-specific title, H1 text, canonical, and body content in raw HTML.
4. `curl -I https://free-will.app/unknown-test-url` returns 404.
5. Lighthouse mobile performance improves above 70.
6. Google Rich Results Test detects valid JSON-LD.
7. Search Console sitemap submission succeeds.
8. URL Inspection shows public route pages are crawlable, indexable, and self-canonical.
