import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  hreflangAlternatesFor,
  ogLocaleFor,
  resolveSeoRoute,
  seoIndexableLocales,
  seoSite,
  structuredDataFor,
} from '../seo/seo';

function setMeta(selector: string, create: () => HTMLMetaElement, content: string): void {
  let tag = document.head.querySelector<HTMLMetaElement>(selector);
  if (!tag) {
    tag = create();
    document.head.appendChild(tag);
  }
  tag.setAttribute('content', content);
}

function setNamedMeta(name: string, content: string): void {
  setMeta(
    `meta[name="${name}"]`,
    () => {
      const tag = document.createElement('meta');
      tag.setAttribute('name', name);
      return tag;
    },
    content,
  );
}

function setPropertyMeta(property: string, content: string): void {
  setMeta(
    `meta[property="${property}"]`,
    () => {
      const tag = document.createElement('meta');
      tag.setAttribute('property', property);
      return tag;
    },
    content,
  );
}

function setCanonical(href: string | null): void {
  let tag = document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]');
  if (!href) {
    tag?.remove();
    return;
  }
  if (!tag) {
    tag = document.createElement('link');
    tag.setAttribute('rel', 'canonical');
    document.head.appendChild(tag);
  }
  tag.setAttribute('href', href);
}

function setHreflangAlternates(canonicalUrl: string, indexable: boolean): void {
  document
    .querySelectorAll('link[rel="alternate"][data-eleutheria-hreflang="true"]')
    .forEach((link) => link.remove());

  if (!indexable) return;

  hreflangAlternatesFor(canonicalUrl).forEach(({ hreflang, href }) => {
    const tag = document.createElement('link');
    tag.setAttribute('rel', 'alternate');
    tag.setAttribute('hreflang', hreflang);
    tag.setAttribute('href', href);
    tag.dataset.eleutheriaHreflang = 'true';
    document.head.appendChild(tag);
  });
}

function setOgLocaleAlternates(activeOgLocale: string, indexable: boolean): void {
  document
    .querySelectorAll('meta[property="og:locale:alternate"]')
    .forEach((meta) => meta.remove());

  if (!indexable) return;

  seoIndexableLocales
    .filter((locale) => locale.ogLocale !== activeOgLocale)
    .forEach((locale) => {
      const tag = document.createElement('meta');
      tag.setAttribute('property', 'og:locale:alternate');
      tag.setAttribute('content', locale.ogLocale);
      document.head.appendChild(tag);
    });
}

export function SeoManager() {
  const location = useLocation();
  const { i18n } = useTranslation();
  const activeLang = i18n.language;

  useEffect(() => {
    const route = resolveSeoRoute(location.pathname);
    const ogType = route.schemas.includes('article') ? 'article' : 'website';
    const activeOgLocale = ogLocaleFor(activeLang);
    const indexable = !/noindex/i.test(route.robots);

    document.documentElement.lang = activeLang.split('-')[0] || seoSite.language;
    document.title = route.title;

    setNamedMeta('title', route.title);
    setNamedMeta('description', route.description);
    setNamedMeta('keywords', route.keywords);
    setNamedMeta('author', seoSite.author);
    setNamedMeta('robots', route.robots);
    setNamedMeta('language', activeLang.split('-')[0] || seoSite.language);

    setPropertyMeta('og:type', ogType);
    setPropertyMeta('og:url', route.canonicalUrl);
    setPropertyMeta('og:title', route.title);
    setPropertyMeta('og:description', route.description);
    setPropertyMeta('og:image', route.imageUrl);
    setPropertyMeta('og:image:width', seoSite.imageWidth);
    setPropertyMeta('og:image:height', seoSite.imageHeight);
    setPropertyMeta('og:image:alt', route.imageAlt);
    setPropertyMeta('og:site_name', seoSite.name);
    setPropertyMeta('og:locale', activeOgLocale);
    setOgLocaleAlternates(activeOgLocale, indexable);

    setNamedMeta('twitter:card', 'summary_large_image');
    setNamedMeta('twitter:url', route.canonicalUrl);
    setNamedMeta('twitter:title', route.title);
    setNamedMeta('twitter:description', route.description);
    setNamedMeta('twitter:image', route.imageUrl);

    setCanonical(indexable ? route.canonicalUrl : null);
    setHreflangAlternates(route.canonicalUrl, indexable);

    document
      .querySelectorAll('script[data-eleutheria-jsonld="true"]')
      .forEach((script) => script.remove());

    structuredDataFor(route).forEach((schema) => {
      const script = document.createElement('script');
      script.type = 'application/ld+json';
      script.dataset.eleutheriaJsonld = 'true';
      script.text = JSON.stringify(schema);
      document.head.appendChild(script);
    });
  }, [location.pathname, activeLang]);

  return null;
}
