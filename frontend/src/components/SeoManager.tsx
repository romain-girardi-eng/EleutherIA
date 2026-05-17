import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { resolveSeoRoute, seoSite, structuredDataFor } from '../seo/seo';

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

function setCanonical(href: string): void {
  let tag = document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]');
  if (!tag) {
    tag = document.createElement('link');
    tag.setAttribute('rel', 'canonical');
    document.head.appendChild(tag);
  }
  tag.setAttribute('href', href);
}

export function SeoManager() {
  const location = useLocation();

  useEffect(() => {
    const route = resolveSeoRoute(location.pathname);
    const ogType = route.schemas.includes('article') ? 'article' : 'website';

    document.documentElement.lang = seoSite.language;
    document.title = route.title;

    setNamedMeta('title', route.title);
    setNamedMeta('description', route.description);
    setNamedMeta('keywords', route.keywords);
    setNamedMeta('author', seoSite.author);
    setNamedMeta('robots', route.robots);
    setNamedMeta('language', 'English');

    setPropertyMeta('og:type', ogType);
    setPropertyMeta('og:url', route.canonicalUrl);
    setPropertyMeta('og:title', route.title);
    setPropertyMeta('og:description', route.description);
    setPropertyMeta('og:image', route.imageUrl);
    setPropertyMeta('og:image:width', seoSite.imageWidth);
    setPropertyMeta('og:image:height', seoSite.imageHeight);
    setPropertyMeta('og:image:alt', route.imageAlt);
    setPropertyMeta('og:site_name', seoSite.name);

    setNamedMeta('twitter:card', 'summary_large_image');
    setNamedMeta('twitter:url', route.canonicalUrl);
    setNamedMeta('twitter:title', route.title);
    setNamedMeta('twitter:description', route.description);
    setNamedMeta('twitter:image', route.imageUrl);

    setCanonical(route.canonicalUrl);

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
  }, [location.pathname]);

  return null;
}
