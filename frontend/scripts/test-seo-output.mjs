import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');
const distDir = path.join(rootDir, 'dist');
const config = JSON.parse(
  await readFile(path.join(rootDir, 'src/seo/routes.json'), 'utf8'),
);
const glossary = JSON.parse(
  await readFile(path.join(rootDir, 'src/content/glossary.json'), 'utf8'),
);
const entityPublication = JSON.parse(
  await readFile(path.join(rootDir, 'src/seo/entity-publication.json'), 'utf8'),
);

const readDist = (relativePath) =>
  readFile(path.join(distDir, relativePath), 'utf8');

const spa = await readDist('spa.html');
assert.match(spa, /<meta name="robots" content="noindex, nofollow"/i);
assert.match(spa, /<meta name="googlebot" content="noindex, nofollow"/i);
assert.match(spa, /<title>EleutherIA record loader<\/title>/i);
assert.doesNotMatch(spa, /rel="canonical"/i);
assert.doesNotMatch(spa, /hreflang=/i);
assert.doesNotMatch(spa, /application\/ld\+json/i);

const notFound = await readDist('404.html');
assert.match(notFound, /noindex, nofollow/i);
assert.doesNotMatch(notFound, /rel="canonical"/i);

const about = await readDist('about/index.html');
assert.match(
  about,
  /<link rel="canonical" href="https:\/\/free-will\.app\/about"/i,
);
assert.match(about, /hreflang="en" href="https:\/\/free-will\.app\/about"/i);
assert.match(about, /hreflang="x-default"/i);
assert.doesNotMatch(about, /hreflang="(?:fr|de|it|el)"/i);
assert.doesNotMatch(about, /\?lang=/i);
assert.match(about, /application\/ld\+json/i);

const debate = await readDist('the-debate/index.html');
assert.match(debate, /The Ancient Free Will Debate \| EleutherIA/);
assert.match(debate, /rel="canonical" href="https:\/\/free-will\.app\/the-debate"/i);

const sitemap = await readDist('sitemap.xml');
assert.match(sitemap, /<loc>https:\/\/free-will\.app\/the-debate<\/loc>/);
assert.match(sitemap, /hreflang="en"/);
assert.match(sitemap, /hreflang="x-default"/);
assert.doesNotMatch(sitemap, /hreflang="(?:fr|de|it|el)"/);
assert.doesNotMatch(sitemap, /\?lang=/);

const seoRelease = JSON.parse(await readDist('seo-release.json'));
assert.equal(seoRelease.schema_version, '1.0.0');
assert.equal(seoRelease.entity_route_count, glossary.length);
assert.equal(
  seoRelease.indexable_entity_route_count,
  entityPublication.approved_ids.length,
);
assert.equal(seoRelease.release_date, config.site.releaseDate);
assert.match(seoRelease.release_id, /^seo-source-sha256-[a-f0-9]{64}$/);
assert.match(sitemap, new RegExp(`EleutherIA source release: ${seoRelease.release_id}`));
assert.match(sitemap, new RegExp(`<lastmod>${seoRelease.release_date}</lastmod>`));

const sourcePaths = {
  nodes: path.resolve(rootDir, '../data/kg/nodes.jsonl'),
  edges: path.resolve(rootDir, '../data/kg/edges.jsonl'),
  corpusManifest: path.resolve(rootDir, '../data/corpus/manifest.jsonl'),
  scholarlyManifest: path.resolve(rootDir, '../data/scholarly_sources/manifest.jsonl'),
  glossary: path.join(rootDir, 'src/content/glossary.json'),
  faq: path.join(rootDir, 'src/content/faq.json'),
  seoRoutes: path.join(rootDir, 'src/seo/routes.json'),
  entityPublication: path.join(rootDir, 'src/seo/entity-publication.json'),
};
for (const [name, sourcePath] of Object.entries(sourcePaths)) {
  const expected = createHash('sha256')
    .update(await readFile(sourcePath))
    .digest('hex');
  assert.equal(seoRelease.source_hashes[name], expected);
}

for (const entity of glossary) {
  const relative = `${entity.nodeUrl.replace(/^\//, '')}/index.html`;
  const html = await readDist(relative);
  const canonical = `https://free-will.app${entity.nodeUrl}`;
  assert.ok(html.includes(`data-kg-node-id="${entity.id}"`));
  assert.ok(html.includes(`data-source-release="${seoRelease.release_id}"`));
  if (entityPublication.approved_ids.includes(entity.id)) {
    assert.match(html, /<meta name="robots" content="index, follow"/i);
    assert.ok(html.includes(`<link rel="canonical" href="${canonical}"`));
    assert.match(html, /"@type":"DefinedTerm"/);
    assert.ok(sitemap.includes(`<loc>${canonical}</loc>`));
  } else {
    assert.match(html, /<meta name="robots" content="noindex, follow"/i);
    assert.doesNotMatch(html, /rel="canonical"/i);
    assert.doesNotMatch(html, /application\/ld\+json/i);
    assert.ok(!sitemap.includes(`<loc>${canonical}</loc>`));
  }
}

const redirects = await readDist('_redirects');
assert.doesNotMatch(redirects, /^\/visualizer\/\*\s+\/spa\s+200/m);
assert.doesNotMatch(redirects, /^\/graph\/\*\s+\/spa\s+200/m);

const nginx = await readFile(path.join(rootDir, 'nginx.conf'), 'utf8');
const dynamicFallback = nginx.match(/location ~ \^\/\(([^)]+)\)\/\.\+\$/)?.[1] ?? '';
assert.doesNotMatch(dynamicFallback, /(?:^|\|)visualizer(?:\||$)/);
assert.doesNotMatch(dynamicFallback, /(?:^|\|)graph(?:\||$)/);

const llms = await readDist('llms.txt');
assert.match(llms, /Coverage and verification remain incomplete/i);
assert.match(llms, /Crawler access is not a licence\s+grant/i);
assert.match(llms, /\/kg\/\{id\}.*must not be advertised/is);
assert.doesNotMatch(llms, /all content is (?:licensed )?CC BY/i);
assert.doesNotMatch(llms, /zero fabrication/i);
assert.doesNotMatch(llms, /every quotation is verified/i);
assert.doesNotMatch(llms, /source-verified answers/i);

const robots = await readDist('robots.txt');
assert.match(robots, /Crawler access is not a licence\s+grant/i);
assert.doesNotMatch(robots, /All content is licensed/i);

const unsafeDynamicRules = config.prefixRules.filter(
  (rule) => !/noindex/i.test(rule.robots),
);
assert.deepEqual(
  unsafeDynamicRules,
  [],
  'dynamic SPA prefix rules must remain noindex until object-specific SSR/SSG exists',
);

console.log('SEO output contract: OK');
