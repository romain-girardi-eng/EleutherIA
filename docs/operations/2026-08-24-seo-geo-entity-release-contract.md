# SEO/GEO entity and release contract

**Status:** implemented locally; production deployment and crawler observation open  
**Date:** 2026-08-24

## Public-entity rule

An arbitrary KG ID is not automatically an indexable scholarly page. The
candidate entity cohort is the 27-node glossary shared by the React page and
the prerender build. Every candidate ID must exist in active `nodes.jsonl`; the
build aborts on a missing ID. A separate versioned publication manifest starts
fail-closed and may approve an ID only after claim-level source, independent and
adversarial review.

For each candidate entity the release build emits crawlable HTML. Only an ID in
`entity-publication.json.approved_ids` additionally receives:

- `/visualizer/<canonical-node-id>/index.html`;
- a unique title, bounded meta description and canonical URL;
- English/x-default hreflang only (other UI translations are not falsely
  advertised as separately rendered pages);
- `DefinedTerm` plus breadcrumb JSON-LD;
- the complete shared glossary definition as crawlable HTML;
- related-entity links and a Scholar-mode link;
- an explicit editorial/unresolved-evidence caveat;
- the source-release fingerprint and release date in the body;
- one source-release-bound sitemap entry.

Pending candidates instead receive `noindex, follow`, no canonical, no
hreflang, no JSON-LD and no sitemap entry. Their HTML remains available for
scholarly review and ordinary navigation without being promoted as a search
artifact.

Hydration preserves the entity pathname while the workspace adds its release,
selection and camera query state. `SeoManager` resolves the candidate before
the generic `/visualizer/` prefix and enforces the same publication manifest as
the static build.

## Unknown-ID rule

The generic `/visualizer/*` and `/graph/*` SPA rewrites were removed from both
Cloudflare Pages `_redirects` and Nginx's dynamic-route fallback. A generated
public entity resolves as a static file; an ungenerated path reaches the real
404 artifact. General graph permalinks use the indexable base route plus query
state (`/visualizer?workspace=1&node=<id>`), avoiding entity-shaped soft 404s.

Inside a development SPA, arbitrary entity paths still resolve through the
generic prefix rule, but they remain `noindex`, have no canonical and produce
no structured data. Production routing enforces the HTTP 404 boundary.

## Release manifest

`dist/seo-release.json` binds the generated surfaces to SHA-256 hashes of:

- KG nodes;
- KG edges;
- corpus manifest;
- scholarly-source manifest;
- glossary and FAQ content;
- SEO route configuration;
- entity publication manifest.

The combined fingerprint is embedded in every public entity and in the sitemap
XML comment. `ELEUTHERIA_RELEASE_DATE` or `SOURCE_DATE_EPOCH` can override the
versioned `site.releaseDate`; there is no wall-clock build-date fallback. The output
contract recomputes every source hash, checks all 27 entity artifacts and
ensures their sitemap/canonical/robots/JSON-LD invariants.

## Current local evidence

- 24 static route pages + 27 candidate entity pages built; **0 indexable entity
  pages until the current claim audits pass**.
- SEO output contract: PASS.
- Browser hydration on Akrasia: entity pathname and selected node retained;
  pending `noindex` state retained; no canonical or JSON-LD; zero console
  errors.
- Arbitrary graph IDs: noindex/no structured data in the app; no production
  wildcard rewrite.

## Open before certification

- Deploy the exact release and verify response status/body/headers from the
  public edge, including an unknown entity returning HTTP 404.
- Submit and inspect the release sitemap in search consoles; monitor indexing,
  canonical selection and rich-result parsing.
- Complete the current claim/locus audit and independently approve safe glossary
  definitions before adding their IDs to the publication manifest.
- Add independently rendered non-English entity pages before advertising their
  hreflang values.

## Primary standards basis

- Google requires structured data to describe visible, relevant page content
  and recommends JSON-LD; each entity therefore renders the same definition in
  HTML and `DefinedTerm` JSON-LD:
  <https://developers.google.com/search/docs/appearance/structured-data/sd-policies>
- Sitemap entries are generated only for canonical URLs, and `lastmod` is tied
  to a versioned significant-content release date rather than a build clock:
  <https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap>
- `DefinedTerm`/`DefinedTermSet` and `inDefinedTermSet` follow the Schema.org
  vocabulary: <https://schema.org/DefinedTermSet>
