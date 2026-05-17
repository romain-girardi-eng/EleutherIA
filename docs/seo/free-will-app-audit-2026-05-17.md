# SEO Audit: free-will.app

Date: 2026-05-17
Target: https://free-will.app/
Workflow: local clone of `AgriciDaniel/claude-seo`, using the `/seo audit` checklist: crawlability, indexability, on-page metadata, content, schema, performance, image SEO, and AI search readiness.

## Executive Summary

Estimated full-site SEO Health Score: 40/100

This is not the same as Lighthouse's homepage-only SEO score. Lighthouse gives the rendered homepage a 92/100 SEO score, but the full-site audit finds several sitewide issues that materially reduce discoverability:

- The site is a client-rendered SPA whose initial HTML has an empty `#root`, no headings, no body links, no schema, no images, and only 5 parsed words.
- `robots.txt`, `sitemap.xml`, and `llms.txt` all return the SPA HTML shell with HTTP 200 instead of valid text/XML files.
- Every tested route has the same title, description, Open Graph metadata, and canonical URL pointing to `https://free-will.app/`.
- Unknown URLs return HTTP 200 and render a 404 screen client-side, creating soft-404 risk.
- No structured data is present, despite the project being a strong candidate for Dataset, Organization/Person, ScholarlyArticle/CreativeWork, BreadcrumbList, and WebSite markup.
- Mobile Lighthouse performance is poor: Performance 30/100, LCP 68.0 s, TBT 2,800 ms, total page weight about 12.4 MiB.
- `/texts` is currently broken in the browser because the API request returns HTTP 500, then surfaces as a CORS failure in the app.

## Scope And Tools

Downloaded package:

- `claude-seo/` cloned from https://github.com/AgriciDaniel/claude-seo

Checks run:

- `claude-seo/scripts/fetch_page.py`
- `claude-seo/scripts/parse_html.py`
- Rendered route crawl with Playwright Chromium
- Lighthouse local runs for mobile and desktop
- Header checks with `curl -I`
- `robots.txt`, `sitemap.xml`, `llms.txt`, manifest, route, and API endpoint checks
- Claude SEO credential checks for Google APIs and backlink APIs

Limitations:

- Google API credentials are not configured, so no Search Console, GA4, URL Inspection, CrUX API, or authenticated PageSpeed data was available.
- PageSpeed Insights API returned a rate-limit response without a Google API key. Lighthouse was run locally instead.
- Backlink APIs are not configured. The audit did not include Moz/Bing backlink metrics.

## Priority Findings

### Critical

1. Initial HTML is almost empty for search crawlers and non-JS agents.

Raw HTML for `/`, `/about`, `/passages-canoniques`, and a fake 404 path all parses as:

- 0 H1
- 0 H2
- 0 internal links
- 0 images
- 0 JSON-LD schema blocks
- 5 visible words
- same title, description, canonical, and OG tags

Google can render JavaScript, but Google also documents that app-shell pages require rendering before content is visible and recommends server-side rendering or pre-rendering because it is faster for users and crawlers and because not all bots execute JavaScript.

Impact:

- Slower and less reliable discovery of internal routes.
- Weak AI search and non-Google crawler visibility.
- Weak snippet generation for academic/dataset queries.

Fix:

- Add SSR, SSG, or pre-rendering for public landing pages.
- At minimum pre-render `/`, `/how-it-works`, `/database`, `/graphrag-showcase`, `/research`, `/texts`, `/bibliography`, `/about`, `/credits`, `/recherches`, `/contributions`, and `/passages-canoniques`.
- Ensure initial HTML contains the route's H1, key body copy, crawlable internal links, canonical, title, description, and JSON-LD.

2. `robots.txt` is invalid.

`https://free-will.app/robots.txt` returns:

- HTTP 200
- `content-type: text/html; charset=utf-8`
- the application HTML shell

Lighthouse reported 68 robots.txt parsing errors. Google processes 2xx robots responses as robots files and ignores invalid lines, so this is not a clean "missing robots" state.

Fix:

```txt
User-agent: *
Allow: /

Sitemap: https://free-will.app/sitemap.xml
```

Optionally add AI crawler policy explicitly:

```txt
User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: PerplexityBot
Allow: /
```

3. `sitemap.xml` is missing but returns HTTP 200 HTML.

`https://free-will.app/sitemap.xml` returns the SPA HTML shell, not XML.

Impact:

- Search engines do not get a canonical route inventory.
- Public routes, canonical passage detail pages, contribution/detail pages, and text pages are harder to discover.
- The incorrect homepage canonical on every route becomes even more damaging because sitemap canonicals are absent.

Fix:

- Generate a real sitemap index or sitemap XML.
- Include only indexable public pages.
- Exclude login/admin/profile/protected routes.
- Add lastmod where you can maintain it truthfully.
- Reference the sitemap in robots.txt.

4. All tested routes canonicalize to the homepage.

Rendered routes including `/how-it-works`, `/database`, `/graphrag`, `/texts`, `/bibliography`, `/about`, `/credits`, `/recherches`, `/contributions`, and `/passages-canoniques` all contain:

```html
<link rel="canonical" href="https://free-will.app/" />
```

Impact:

- Signals that every route is a duplicate or alternate of the homepage.
- Search engines may consolidate ranking signals to `/` and avoid indexing valuable route pages.

Fix:

- Set a route-specific canonical in server HTML or pre-rendered HTML:
  - `/about` -> `https://free-will.app/about`
  - `/passages-canoniques` -> `https://free-will.app/passages-canoniques`
  - `/bibliography` -> `https://free-will.app/bibliography`
- For protected or utility pages, use `noindex` rather than homepage canonicals.

5. Soft 404 behavior.

`https://free-will.app/this-path-should-not-exist` returns HTTP 200, then renders a client-side 404 page.

Impact:

- Google may treat invalid URLs as soft 404s.
- Crawl budget can be wasted.
- Error URLs can be indexed or canonicalized incorrectly.

Fix:

- Serve a real HTTP 404 for unknown routes at the edge/server layer.
- Keep the client 404 UI, but pair it with the correct HTTP status.

6. `/texts` is currently broken.

The route requests:

`https://free-will.app/api/works?offset=0&limit=500&sort_by=most_cited`

Observed behavior:

- Browser console reports CORS failure.
- Direct GET returns HTTP 500 and body `Internal Server Error`.
- The rendered page says `Network Error` and shows zero works.

Impact:

- A strategically important indexable content page has thin/error content.
- Users and crawlers cannot see the ancient works inventory.

Fix:

- Fix the API 500 first.
- Ensure error responses include CORS headers if the frontend needs them.
- Pre-render or statically embed the first-page work list and key internal links so `/texts` remains useful even when API hydration fails.

### High

7. Duplicate title and meta description across the whole site.

All rendered routes use:

- Title: `EleutherIA - Ancient Free Will Database`
- Description: `A revolutionary digital humanities platform combining Knowledge Graph, PostgreSQL, and AI-powered semantic search...`

Fix examples:

- `/how-it-works`: `How EleutherIA Works | Knowledge Graph, Embeddings, GraphRAG`
- `/database`: `EleutherIA Database Overview | Ancient Free Will Knowledge Graph`
- `/passages-canoniques`: `Canonical Free Will Passages | EleutherIA Reception Map`
- `/bibliography`: `Bibliography on Ancient Free Will | EleutherIA`
- `/texts`: `Ancient Works Library | Free Will, Fate, and Moral Responsibility`

8. No structured data.

Detected JSON-LD blocks: 0.

Recommended schema:

- Home: `WebSite`, `Organization` or `Person`, `Dataset`, `SoftwareApplication`
- Dataset landing/about: `Dataset` with DOI, license, creator, keywords, citation, sameAs
- Bibliography/text pages: `CollectionPage`, `CreativeWork`, `Book`, `ScholarlyArticle` where applicable
- Public research answers: `ScholarlyArticle` or `Article`
- All public route pages: `BreadcrumbList`

9. Performance is materially hurting SEO and UX.

Lighthouse:

| Mode | Performance | SEO | Accessibility | Best Practices | FCP | LCP | TBT | CLS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Mobile | 30 | 92 | 93 | 81 | 6.7 s | 68.0 s | 2,800 ms | 0 |
| Desktop | 49 | 92 | 96 | 81 | 1.4 s | 11.1 s | 410 ms | 0.007 |

Largest payloads on the homepage:

- `ParticleCloud-data.json`: ~6.8 MB transferred
- `philosopher-particles.json`: ~4.7 MB transferred
- `cosmograph-vendor`: ~398 KB transferred, ~1.9 MB uncompressed
- main app JS: ~294 KB transferred, ~1.0 MB uncompressed

Fix:

- Do not load graph particle datasets on initial homepage render unless they are needed above the fold.
- Lazy load the animated graph after text content paints.
- Consider a static poster/canvas placeholder for LCP, then hydrate animation on idle or interaction.
- Split graph and Cosmograph code out of the homepage critical path.
- Compress, reduce, or tile the large JSON payloads.
- Give hashed static assets longer immutable cache lifetimes.

10. Security headers are incomplete.

Present:

- `referrer-policy: strict-origin-when-cross-origin`
- `x-content-type-options: nosniff`

Missing from checked responses:

- `strict-transport-security`
- `content-security-policy`
- `x-frame-options` or CSP `frame-ancestors`
- `permissions-policy`

Fix:

- Add HSTS once HTTPS is stable.
- Add a CSP that allows required script/font/API origins and blocks unsafe framing.
- Add `frame-ancestors 'none'` unless embedding is required.

### Medium

11. Several routes are thin or not index-worthy.

Rendered word counts:

- `/visualizer`: 41 words, 0 H1
- `/graph`: 41 words, 0 H1
- `/login`: 150 words, 0 H1
- `/texts`: 172 words and broken API state
- `/`: 113 words in rendered text, with duplicate H1s

Fix:

- Add SEO fallback copy and one H1 to visual graph routes, or mark them `noindex` if they are purely interactive.
- Mark login/admin/profile/protected pages `noindex, nofollow`.
- Add route-specific content and internal links to public indexable pages.

12. Images have alt text but no explicit dimensions.

Across rendered routes, all images had alt text, but every checked image lacked explicit `width` and `height` attributes. Lighthouse flags this as a layout stability risk.

Fix:

- Add intrinsic dimensions to logos and key images.
- Preserve responsive display with CSS while keeping attributes in markup.

13. Social metadata is homepage-only.

Open Graph and Twitter metadata is static and points to the homepage. Twitter tags use `property="twitter:*"` in raw HTML; many parsers expect `name="twitter:*"`.

Fix:

- Generate route-specific OG title, description, URL, and image.
- Use `name="twitter:card"`, `name="twitter:title"`, etc.

14. `llms.txt` is missing but returns HTML.

`https://free-will.app/llms.txt` returns the SPA HTML shell.

Fix:

- Add a concise `llms.txt` describing the project, important public URLs, citation/license details, dataset DOI, and preferred summaries.
- Keep it text/plain.

15. Manifest shortcut `/search` points to an undefined client route.

The PWA manifest includes `url: "/search"`, but the tested route returned the app shell and is not defined in `App.tsx` routes.

Fix:

- Add a real `/search` route or update the shortcut to an existing route such as `/database` or `/texts`.

## Category Scores

| Category | Weight | Score | Notes |
|---|---:|---:|---|
| Technical SEO | 22% | 48/100 | Invalid robots/sitemap, soft 404s, app-shell HTML, missing security headers |
| Content Quality | 23% | 52/100 | Strong subject matter, but raw HTML is empty and `/texts` is broken |
| On-page SEO | 20% | 38/100 | Duplicate title/meta/canonical on every route |
| Schema / Structured Data | 10% | 0/100 | No JSON-LD detected |
| Performance | 10% | 35/100 | Mobile LCP/TBT and 12.4 MiB payload are severe |
| AI Search Readiness | 10% | 30/100 | No `llms.txt`, no schema, JS-only content, weak machine-readable citations |
| Images | 5% | 75/100 | Alt text present, dimensions missing |

Weighted score: approximately 40/100.

## Quick Wins

1. Ship real `/robots.txt` and `/sitemap.xml`.
2. Set route-specific canonical URLs.
3. Return HTTP 404 for unknown paths.
4. Fix the `/api/works` 500 that breaks `/texts`.
5. Add `noindex` to login/admin/profile/protected routes.
6. Add Dataset + WebSite + Organization/Person JSON-LD to the homepage/about page.
7. Add unique title/description per public route.
8. Defer graph JSON and Cosmograph code from the initial homepage load.
9. Add explicit image dimensions.
10. Add `llms.txt`.

## Sources

- Claude SEO skill package: https://github.com/AgriciDaniel/claude-seo
- Audited site: https://free-will.app/
- Google JavaScript SEO basics: https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics
- Google robots.txt specification: https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec
- Google canonicalization guidance: https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls
- Google Organization structured data: https://developers.google.com/search/docs/appearance/structured-data/organization
- Google Dataset structured data: https://developers.google.com/search/docs/data-types/dataset
