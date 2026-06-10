import seoConfig from './routes.json';

type SeoSite = typeof seoConfig.site;
type SeoRoute = (typeof seoConfig.routes)[number];
type SeoPrefixRule = (typeof seoConfig.prefixRules)[number];

export type ResolvedSeoRoute = {
  path: string;
  title: string;
  description: string;
  h1: string;
  summary: string;
  robots: string;
  keywords: string;
  canonicalUrl: string;
  imageUrl: string;
  imageAlt: string;
  schemas: string[];
  sitemap?: boolean;
  changefreq?: string;
  priority?: number;
};

export const seoSite: SeoSite = seoConfig.site;

export type SeoLocale = { lang: string; ogLocale: string };

export const seoLocales: SeoLocale[] = seoSite.locales;

const ogLocaleByLang = new Map<string, string>(
  seoLocales.map((locale) => [locale.lang, locale.ogLocale]),
);

export function ogLocaleFor(lang: string): string {
  const base = lang.split('-')[0];
  return ogLocaleByLang.get(base) ?? seoLocales[0].ogLocale;
}

function withLangParam(url: string, lang: string): string {
  const separator = url.includes('?') ? '&' : '?';
  return `${url}${separator}${seoSite.langParam}=${lang}`;
}

export type HreflangAlternate = { hreflang: string; href: string };

/**
 * The SPA serves every language from the same URL; the active locale is
 * selected client-side. `?lang=xx` is honoured by the i18n querystring
 * detector, so each alternate resolves to the advertised language.
 */
export function hreflangAlternatesFor(canonicalUrl: string): HreflangAlternate[] {
  const alternates: HreflangAlternate[] = seoLocales.map((locale) => ({
    hreflang: locale.lang,
    href: withLangParam(canonicalUrl, locale.lang),
  }));
  alternates.push({ hreflang: 'x-default', href: canonicalUrl });
  return alternates;
}

const exactRoutes = new Map<string, SeoRoute>(
  seoConfig.routes.map((route) => [normalizePath(route.path), route]),
);

function normalizePath(pathname: string): string {
  if (!pathname || pathname === '/') return '/';
  return pathname.replace(/\/+$/, '') || '/';
}

export function absoluteUrl(pathOrUrl: string): string {
  if (/^https?:\/\//i.test(pathOrUrl)) return pathOrUrl;
  const path = pathOrUrl.startsWith('/') ? pathOrUrl : `/${pathOrUrl}`;
  return `${seoSite.origin}${path}`;
}

function routeToResolved(route: SeoRoute | SeoPrefixRule, pathname: string): ResolvedSeoRoute {
  const path = normalizePath('path' in route ? route.path : pathname);
  const canonicalPath = 'path' in route ? path : normalizePath(pathname);

  return {
    path,
    title: route.title,
    description: route.description,
    h1: route.h1,
    summary: route.summary,
    robots: route.robots,
    keywords: seoSite.keywords,
    canonicalUrl: absoluteUrl(canonicalPath),
    imageUrl: absoluteUrl(seoSite.defaultImage),
    imageAlt: seoSite.imageAlt,
    schemas: [...route.schemas],
    sitemap: 'priority' in route && route.priority > 0,
    changefreq: 'changefreq' in route ? route.changefreq : undefined,
    priority: 'priority' in route ? route.priority : undefined,
  };
}

export function resolveSeoRoute(pathname: string): ResolvedSeoRoute {
  const normalized = normalizePath(pathname);
  const exact = exactRoutes.get(normalized);
  if (exact) return routeToResolved(exact, normalized);

  const prefixRule = seoConfig.prefixRules.find((rule) => normalized.startsWith(rule.prefix));
  if (prefixRule) return routeToResolved(prefixRule, normalized);

  return {
    path: normalized,
    title: 'Page Not Found | EleutherIA',
    description: 'The requested EleutherIA page could not be found.',
    h1: 'Page Not Found',
    summary: 'This URL does not match a public EleutherIA page.',
    robots: 'noindex, nofollow',
    keywords: seoSite.keywords,
    canonicalUrl: absoluteUrl(normalized),
    imageUrl: absoluteUrl(seoSite.defaultImage),
    imageAlt: seoSite.imageAlt,
    schemas: [],
    sitemap: false,
  };
}

function breadcrumbFor(route: ResolvedSeoRoute): Record<string, unknown> {
  const segments = route.path === '/' ? [] : route.path.split('/').filter(Boolean);
  const items = [
    {
      '@type': 'ListItem',
      position: 1,
      name: 'EleutherIA',
      item: seoSite.origin,
    },
  ];

  let currentPath = '';
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
    inLanguage: seoSite.language,
    itemListElement: items,
  };
}

function personSchema(): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'Person',
    '@id': `${seoSite.origin}/about#romain-girardi`,
    name: seoSite.author,
    url: seoSite.authorUrl,
    sameAs: [seoSite.authorOrcid, seoSite.repository],
    affiliation: [
      {
        '@type': 'Organization',
        name: "Universite Cote d'Azur"
      },
      {
        '@type': 'Organization',
        name: 'Universite de Geneve'
      }
    ],
  };
}

function websiteSchema(route: ResolvedSeoRoute): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    '@id': `${seoSite.origin}/#website`,
    name: seoSite.name,
    url: seoSite.origin,
    inLanguage: seoSite.language,
    description: route.description,
    creator: { '@id': `${seoSite.origin}/about#romain-girardi` },
    potentialAction: {
      '@type': 'SearchAction',
      target: {
        '@type': 'EntryPoint',
        urlTemplate: `${seoSite.origin}${seoSite.searchAction}`,
      },
      'query-input': 'required name=search_term_string',
    },
  };
}

function datasetSchema(): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'Dataset',
    '@id': `${seoSite.origin}/#dataset`,
    name: 'EleutherIA: Ancient Free Will Database',
    alternateName: 'Ancient Free Will Knowledge Graph',
    description:
      'A FAIR-aligned knowledge graph and ancient text corpus for Greco-Roman and early Christian debates on free will, fate, providence, and moral responsibility.',
    url: seoSite.origin,
    inLanguage: seoSite.language,
    identifier: `https://doi.org/${seoSite.doi}`,
    sameAs: [`https://doi.org/${seoSite.doi}`, seoSite.repository],
    license: seoSite.license,
    isAccessibleForFree: true,
    keywords: seoSite.keywords.split(', '),
    creator: { '@id': `${seoSite.origin}/about#romain-girardi` },
    citation: `Girardi, R. (2026). EleutherIA: A FAIR-Compliant Knowledge Graph for Ancient Free Will Debates [Data set]. Zenodo. https://doi.org/${seoSite.doi}`,
  };
}

function dataCatalogSchema(): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'DataCatalog',
    '@id': `${seoSite.origin}/#datacatalog`,
    name: 'EleutherIA Data Catalog',
    description:
      'A FAIR-aligned catalog of structured data on ancient debates about free will, fate, providence, and moral responsibility: a knowledge graph of philosophers, concepts, arguments, and works, plus a Greek and Latin critical-edition corpus, all citation-grounded.',
    url: seoSite.origin,
    inLanguage: seoSite.language,
    license: seoSite.license,
    isAccessibleForFree: true,
    publisher: { '@id': `${seoSite.origin}/about#romain-girardi` },
    creator: { '@id': `${seoSite.origin}/about#romain-girardi` },
    sameAs: `https://doi.org/${seoSite.doi}`,
    dataset: { '@id': `${seoSite.origin}/#dataset` },
  };
}

function softwareSchema(route: ResolvedSeoRoute): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    '@id': `${seoSite.origin}/#software`,
    name: seoSite.name,
    applicationCategory: 'EducationalApplication',
    operatingSystem: 'Web',
    url: seoSite.origin,
    inLanguage: seoSite.language,
    description: route.description,
    creator: { '@id': `${seoSite.origin}/about#romain-girardi` },
    license: seoSite.license,
    codeRepository: seoSite.repository,
    isAccessibleForFree: true,
  };
}

function collectionSchema(route: ResolvedSeoRoute): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    '@id': `${route.canonicalUrl}#collection`,
    name: route.h1,
    url: route.canonicalUrl,
    inLanguage: seoSite.language,
    description: route.description,
    isPartOf: { '@id': `${seoSite.origin}/#website` },
  };
}

function articleSchema(route: ResolvedSeoRoute): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'ScholarlyArticle',
    '@id': `${route.canonicalUrl}#article`,
    headline: route.h1,
    url: route.canonicalUrl,
    inLanguage: seoSite.language,
    description: route.description,
    author: { '@id': `${seoSite.origin}/about#romain-girardi` },
    isPartOf: { '@id': `${seoSite.origin}/#website` },
  };
}

function creativeWorkSchema(route: ResolvedSeoRoute): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'CreativeWork',
    '@id': `${route.canonicalUrl}#creative-work`,
    name: route.h1,
    url: route.canonicalUrl,
    inLanguage: seoSite.language,
    description: route.description,
    isPartOf: { '@id': `${seoSite.origin}/#dataset` },
  };
}

export function structuredDataFor(route: ResolvedSeoRoute): Record<string, unknown>[] {
  const schemas = route.schemas.flatMap((schema) => {
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
        return [breadcrumbFor(route)];
      case 'collection':
        return [collectionSchema(route)];
      case 'article':
        return [articleSchema(route)];
      case 'creativeWork':
        return [creativeWorkSchema(route)];
      default:
        return [];
    }
  });

  return schemas;
}

export function sitemapRoutes(): ResolvedSeoRoute[] {
  return seoConfig.routes
    .map((route) => routeToResolved(route, route.path))
    .filter((route) => route.sitemap);
}
