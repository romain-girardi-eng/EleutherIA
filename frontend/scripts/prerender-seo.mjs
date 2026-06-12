import { mkdir, readdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');
const distDir = path.join(rootDir, 'dist');
const configPath = path.join(rootDir, 'src/seo/routes.json');
const indexPath = path.join(distDir, 'index.html');

const config = JSON.parse(await readFile(configPath, 'utf8'));
const baseHtml = await readFile(indexPath, 'utf8');

// Hash-named HomePage chunk — modulepreloaded on the landing page so the
// hero starts downloading in parallel with the entry bundle instead of a
// third network hop after React mounts.
const homeChunk = (await readdir(path.join(distDir, 'assets'))).find(
  (f) => f.startsWith('HomePage-') && f.endsWith('.js'),
);

// Shared content modules — the SAME plain JSON the React pages import, so the
// prerendered static HTML carries the real glossary/FAQ text (critical for GEO:
// AI crawlers and non-JS bots read this body, not a nav stub).
const glossary = JSON.parse(
  await readFile(path.join(rootDir, 'src/content/glossary.json'), 'utf8'),
);
const faqEntries = JSON.parse(
  await readFile(path.join(rootDir, 'src/content/faq.json'), 'utf8'),
);

/** Stable FAQ anchor — mirrors faqAnchor() in src/pages/FAQPage.tsx + seo.ts. */
function faqAnchor(question) {
  return String(question)
    .toLowerCase()
    .replace(/['’"“”]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 64);
}

const topLinks = config.routes
  .filter((route) => route.priority > 0)
  .map((route) => ({
    path: route.path,
    label: route.h1,
  }));

function normalizePath(pathname) {
  if (!pathname || pathname === '/') return '/';
  return pathname.replace(/\/+$/, '') || '/';
}

function absoluteUrl(pathOrUrl) {
  if (/^https?:\/\//i.test(pathOrUrl)) return pathOrUrl;
  const normalized = pathOrUrl.startsWith('/') ? pathOrUrl : `/${pathOrUrl}`;
  return `${config.site.origin}${normalized}`;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

const locales = config.site.locales;
const langParam = config.site.langParam;
const defaultOgLocale = locales[0].ogLocale;

function withLangParam(url, lang) {
  const separator = url.includes('?') ? '&' : '?';
  return `${url}${separator}${langParam}=${lang}`;
}

function hreflangAlternates(canonical) {
  const alternates = locales.map((locale) => ({
    hreflang: locale.lang,
    href: withLangParam(canonical, locale.lang),
  }));
  alternates.push({ hreflang: 'x-default', href: canonical });
  return alternates;
}

function personSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'Person',
    '@id': `${config.site.origin}/about#romain-girardi`,
    name: config.site.author,
    url: config.site.authorUrl,
    sameAs: [config.site.authorOrcid, config.site.repository],
    affiliation: [
      { '@type': 'Organization', name: "Universite Cote d'Azur" },
      { '@type': 'Organization', name: 'Universite de Geneve' },
    ],
  };
}

function websiteSchema(route) {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    '@id': `${config.site.origin}/#website`,
    name: config.site.name,
    url: config.site.origin,
    inLanguage: config.site.language,
    description: route.description,
    creator: { '@id': `${config.site.origin}/about#romain-girardi` },
    potentialAction: {
      '@type': 'SearchAction',
      target: {
        '@type': 'EntryPoint',
        urlTemplate: `${config.site.origin}${config.site.searchAction}`,
      },
      'query-input': 'required name=search_term_string',
    },
  };
}

function datasetSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'Dataset',
    '@id': `${config.site.origin}/#dataset`,
    name: 'EleutherIA: Ancient Free Will Database',
    alternateName: 'Ancient Free Will Knowledge Graph',
    description:
      'A FAIR-aligned knowledge graph and ancient text corpus for Greco-Roman and early Christian debates on free will, fate, providence, and moral responsibility.',
    url: config.site.origin,
    inLanguage: config.site.language,
    identifier: `https://doi.org/${config.site.doi}`,
    sameAs: [`https://doi.org/${config.site.doi}`, config.site.repository],
    license: config.site.license,
    isAccessibleForFree: true,
    keywords: config.site.keywords.split(', '),
    creator: { '@id': `${config.site.origin}/about#romain-girardi` },
    citation: `Girardi, R. (2026). EleutherIA: A FAIR-Compliant Knowledge Graph for Ancient Free Will Debates [Data set]. Zenodo. https://doi.org/${config.site.doi}`,
  };
}

function dataCatalogSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'DataCatalog',
    '@id': `${config.site.origin}/#datacatalog`,
    name: 'EleutherIA Data Catalog',
    description:
      'A FAIR-aligned catalog of structured data on ancient debates about free will, fate, providence, and moral responsibility: a knowledge graph of philosophers, concepts, arguments, and works, plus a Greek and Latin critical-edition corpus, all citation-grounded.',
    url: config.site.origin,
    inLanguage: config.site.language,
    license: config.site.license,
    isAccessibleForFree: true,
    publisher: { '@id': `${config.site.origin}/about#romain-girardi` },
    creator: { '@id': `${config.site.origin}/about#romain-girardi` },
    sameAs: `https://doi.org/${config.site.doi}`,
    dataset: { '@id': `${config.site.origin}/#dataset` },
  };
}

function softwareSchema(route) {
  return {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    '@id': `${config.site.origin}/#software`,
    name: config.site.name,
    applicationCategory: 'EducationalApplication',
    operatingSystem: 'Web',
    url: config.site.origin,
    inLanguage: config.site.language,
    description: route.description,
    creator: { '@id': `${config.site.origin}/about#romain-girardi` },
    license: config.site.license,
    codeRepository: config.site.repository,
    isAccessibleForFree: true,
  };
}

function breadcrumbSchema(route) {
  const segments = route.path === '/' ? [] : route.path.split('/').filter(Boolean);
  let currentPath = '';
  const items = [
    {
      '@type': 'ListItem',
      position: 1,
      name: 'EleutherIA',
      item: config.site.origin,
    },
  ];

  segments.forEach((segment, index) => {
    currentPath += `/${segment}`;
    const isLast = index === segments.length - 1;
    items.push({
      '@type': 'ListItem',
      position: index + 2,
      name: isLast ? route.h1 : segment.replace(/-/g, ' '),
      item: absoluteUrl(currentPath),
    });
  });

  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    inLanguage: config.site.language,
    itemListElement: items,
  };
}

function collectionSchema(route) {
  return {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    '@id': `${absoluteUrl(route.path)}#collection`,
    name: route.h1,
    url: absoluteUrl(route.path),
    inLanguage: config.site.language,
    description: route.description,
    isPartOf: { '@id': `${config.site.origin}/#website` },
  };
}

function definedTermSetSchema(route) {
  const canonical = absoluteUrl(route.path);
  return {
    '@context': 'https://schema.org',
    '@type': 'DefinedTermSet',
    '@id': `${canonical}#glossary`,
    name: route.h1,
    url: canonical,
    inLanguage: config.site.language,
    description: route.description,
    isPartOf: { '@id': `${config.site.origin}/#website` },
    hasDefinedTerm: glossary.map((entry) => ({
      '@type': 'DefinedTerm',
      '@id': `${config.site.origin}${entry.nodeUrl}`,
      name: entry.term,
      ...(entry.originalTerm ? { alternateName: entry.originalTerm } : {}),
      description: entry.definition,
      url: absoluteUrl(entry.nodeUrl),
      inDefinedTermSet: `${canonical}#glossary`,
    })),
  };
}

function faqPageSchema(route) {
  const canonical = absoluteUrl(route.path);
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    '@id': `${canonical}#faq`,
    name: route.h1,
    url: canonical,
    inLanguage: config.site.language,
    description: route.description,
    isPartOf: { '@id': `${config.site.origin}/#website` },
    mainEntity: faqEntries.map((entry) => ({
      '@type': 'Question',
      '@id': `${canonical}#${faqAnchor(entry.question)}`,
      name: entry.question,
      acceptedAnswer: {
        '@type': 'Answer',
        text: entry.answer,
      },
    })),
  };
}

function schemaFor(route) {
  return route.schemas.flatMap((schema) => {
    switch (schema) {
      case 'website':
        return [websiteSchema(route)];
      case 'dataset':
        return [datasetSchema()];
      case 'dataCatalog':
        return [dataCatalogSchema()];
      case 'software':
        return [softwareSchema(route)];
      case 'person':
        return [personSchema()];
      case 'breadcrumb':
        return [breadcrumbSchema(route)];
      case 'collection':
        return [collectionSchema(route)];
      case 'definedTermSet':
        return [definedTermSetSchema(route)];
      case 'faqPage':
        return [faqPageSchema(route)];
      default:
        return [];
    }
  });
}

function stripSeoTags(html) {
  return html
    .replace(/\s*<title>[\s\S]*?<\/title>/i, '')
    .replace(/\s*<meta\s+(?:name|property)=["'](?:title|description|keywords|author|robots|language|og:[^"']+|twitter:[^"']+)["'][^>]*>\n?/gi, '')
    .replace(/\s*<link\s+rel=["']canonical["'][^>]*>\n?/gi, '')
    .replace(/\s*<link\s+rel=["']alternate["'][^>]*hreflang=[^>]*>\n?/gi, '')
    .replace(/\s*<script[^>]+type=["']application\/ld\+json["'][^>]*>[\s\S]*?<\/script>\n?/gi, '');
}

function seoHead(route) {
  const canonical = absoluteUrl(route.path);
  const image = absoluteUrl(config.site.defaultImage);
  const ogType = route.schemas.includes('article') ? 'article' : 'website';
  const indexable = !/noindex/i.test(route.robots);
  const hreflang = indexable
    ? hreflangAlternates(canonical)
        .map((alt) => `    <link rel="alternate" hreflang="${escapeHtml(alt.hreflang)}" href="${escapeHtml(alt.href)}" />`)
        .join('\n') + '\n'
    : '';
  const ogLocaleAlternates = locales
    .filter((locale) => locale.ogLocale !== defaultOgLocale)
    .map((locale) => `<meta property="og:locale:alternate" content="${escapeHtml(locale.ogLocale)}" />`)
    .join('\n    ');
  const jsonLd = schemaFor(route)
    .map((schema) => `<script type="application/ld+json" data-eleutheria-jsonld="true">${JSON.stringify(schema)}</script>`)
    .join('\n    ');

  return `    <title>${escapeHtml(route.title)}</title>
    <meta name="title" content="${escapeHtml(route.title)}" />
    <meta name="description" content="${escapeHtml(route.description)}" />
    <meta name="keywords" content="${escapeHtml(config.site.keywords)}" />
    <meta name="author" content="${escapeHtml(config.site.author)}" />
    <meta name="robots" content="${escapeHtml(route.robots)}" />
    <meta name="language" content="English" />
    <link rel="canonical" href="${escapeHtml(canonical)}" />
${hreflang}    <meta property="og:type" content="${escapeHtml(ogType)}" />
    <meta property="og:url" content="${escapeHtml(canonical)}" />
    <meta property="og:title" content="${escapeHtml(route.title)}" />
    <meta property="og:description" content="${escapeHtml(route.description)}" />
    <meta property="og:image" content="${escapeHtml(image)}" />
    <meta property="og:image:width" content="${escapeHtml(config.site.imageWidth)}" />
    <meta property="og:image:height" content="${escapeHtml(config.site.imageHeight)}" />
    <meta property="og:image:alt" content="${escapeHtml(config.site.imageAlt)}" />
    <meta property="og:site_name" content="${escapeHtml(config.site.name)}" />
    <meta property="og:locale" content="${escapeHtml(defaultOgLocale)}" />
    ${ogLocaleAlternates}
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:url" content="${escapeHtml(canonical)}" />
    <meta name="twitter:title" content="${escapeHtml(route.title)}" />
    <meta name="twitter:description" content="${escapeHtml(route.description)}" />
    <meta name="twitter:image" content="${escapeHtml(image)}" />
    ${jsonLd}`;
}

function coreLinksNav(route) {
  const links = topLinks
    .filter((link) => link.path !== route.path)
    .slice(0, 8)
    .map((link) => `<li><a href="${escapeHtml(link.path)}">${escapeHtml(link.label)}</a></li>`)
    .join('');
  return `<nav aria-label="Core EleutherIA pages">
        <ul style="display:grid;gap:.5rem;margin:0;padding-left:1.25rem">${links}</ul>
      </nav>`;
}

/**
 * Glossary body — emits the real term + definition text as a static <dl> so AI
 * crawlers and non-JS bots read actual content, not a nav stub. Greek/Latin in
 * `originalTerm`/`definition` comes verbatim from the shared JSON.
 */
function glossaryBody(route) {
  const terms = glossary
    .map((entry) => {
      const original = entry.originalTerm
        ? ` <span lang="grc" style="color:#c2410c">(${escapeHtml(entry.originalTerm)})</span>`
        : '';
      return `<div style="margin:0 0 1.5rem">
          <dt style="font-weight:700;font-size:1.25rem;margin:0 0 .35rem">${escapeHtml(entry.term)}${original}</dt>
          <dd style="margin:0 0 .35rem">${escapeHtml(entry.definition)}</dd>
          <dd style="margin:0"><a href="${escapeHtml(entry.nodeUrl)}">View in graph</a></dd>
        </div>`;
    })
    .join('');

  return `<main data-prerendered-seo="true" style="font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:48rem;margin:4rem auto;padding:2rem;color:#292524;line-height:1.6">
      <p style="margin:0 0 .75rem;color:#a16207;font-weight:700;letter-spacing:.08em;text-transform:uppercase;font-size:.75rem">EleutherIA — Glossary</p>
      <h1 style="font-size:clamp(2rem,6vw,4rem);line-height:1.05;margin:0 0 1rem">${escapeHtml(route.h1)}</h1>
      <p style="font-size:1.125rem;margin:0 0 1.5rem">${escapeHtml(route.summary)}</p>
      <dl style="margin:0 0 2rem">${terms}</dl>
      ${coreLinksNav(route)}
    </main>`;
}

/**
 * FAQ body — emits the real question + answer text as static sections so the
 * prerendered HTML is independently citable by AI search.
 */
function faqBody(route) {
  const items = faqEntries
    .map(
      (entry) => `<section id="${escapeHtml(faqAnchor(entry.question))}" style="margin:0 0 1.5rem">
          <h2 style="font-size:1.25rem;margin:0 0 .35rem">${escapeHtml(entry.question)}</h2>
          <p style="margin:0">${escapeHtml(entry.answer)}</p>
        </section>`,
    )
    .join('');

  return `<main data-prerendered-seo="true" style="font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:48rem;margin:4rem auto;padding:2rem;color:#292524;line-height:1.6">
      <p style="margin:0 0 .75rem;color:#a16207;font-weight:700;letter-spacing:.08em;text-transform:uppercase;font-size:.75rem">EleutherIA — FAQ</p>
      <h1 style="font-size:clamp(2rem,6vw,4rem);line-height:1.05;margin:0 0 1rem">${escapeHtml(route.h1)}</h1>
      <p style="font-size:1.125rem;margin:0 0 1.5rem">${escapeHtml(route.summary)}</p>
      ${items}
      ${coreLinksNav(route)}
    </main>`;
}

function fallbackBody(route) {
  if (normalizePath(route.path) === '/glossary') return glossaryBody(route);
  if (normalizePath(route.path) === '/faq') return faqBody(route);

  return `<main data-prerendered-seo="true" style="font-family:'DM Sans',system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:48rem;margin:4rem auto;padding:2rem;color:#292524;line-height:1.6">
      <p style="margin:0 0 .75rem;color:#a16207;font-weight:700;letter-spacing:.08em;text-transform:uppercase;font-size:.75rem">EleutherIA</p>
      <h1 style="font-family:Georgia,'Times New Roman',serif;font-size:clamp(2rem,6vw,4rem);line-height:1.05;margin:0 0 1rem">${escapeHtml(route.h1)}</h1>
      <p style="font-size:1.125rem;margin:0 0 1.5rem">${escapeHtml(route.summary)}</p>
      ${coreLinksNav(route)}
      <p style="display:flex;align-items:center;gap:.5rem;margin:2.5rem 0 0;color:#a8a29e;font-size:.8125rem">
        <span style="display:inline-block;width:.5rem;height:.5rem;border-radius:9999px;background:#d97706;animation:eleutheria-pulse 1.2s ease-in-out infinite"></span>
        Loading the interactive interface…
      </p>
      <style>@keyframes eleutheria-pulse{0%,100%{opacity:.25}50%{opacity:1}}</style>
    </main>`;
}

function renderRouteHtml(route) {
  const stripped = stripSeoTags(baseHtml);
  let head = seoHead(route);
  if (normalizePath(route.path) === '/' && homeChunk) {
    head += `\n  <link rel="modulepreload" crossorigin href="/assets/${homeChunk}">`;
  }
  const withHead = stripped.replace('</head>', `${head}\n  </head>`);
  return withHead.replace(
    /<div id="root"([^>]*)><\/div>/,
    `<div id="root"$1>${fallbackBody(route)}</div>`,
  );
}

function outputPathFor(routePath) {
  const normalized = normalizePath(routePath);
  if (normalized === '/') return indexPath;
  return path.join(distDir, normalized.slice(1), 'index.html');
}

for (const route of config.routes) {
  const filePath = outputPathFor(route.path);
  await mkdir(path.dirname(filePath), { recursive: true });
  await writeFile(filePath, renderRouteHtml(route), 'utf8');
}

const lastmod = new Date().toISOString().slice(0, 10);

const sitemapXml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">
${config.routes
  .filter((route) => route.priority > 0)
  .map((route) => {
    const loc = absoluteUrl(route.path);
    const alternates = hreflangAlternates(loc)
      .map(
        (alt) =>
          `    <xhtml:link rel="alternate" hreflang="${alt.hreflang}" href="${alt.href}" />`,
      )
      .join('\n');
    return `  <url>
    <loc>${loc}</loc>
    <lastmod>${lastmod}</lastmod>
    <changefreq>${route.changefreq}</changefreq>
    <priority>${Number(route.priority).toFixed(2).replace(/0$/, '').replace(/\.0$/, '.0')}</priority>
${alternates}
  </url>`;
  })
  .join('\n')}
</urlset>
`;

await writeFile(path.join(distDir, 'sitemap.xml'), sitemapXml, 'utf8');

// SPA fallback copy for Cloudflare Pages: _redirects proxies dynamic
// routes (/texts/:id, /share/:token, …) here. Targeting /index.html
// directly is impossible — Pages' clean-URL normalization turns the
// rewrite into a 308 to /.
await writeFile(path.join(distDir, 'spa.html'), baseHtml, 'utf8');

console.log(`SEO prerendered ${config.routes.length} route HTML files.`);
