import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import en from './locales/en.json';
import { extraResources } from './extraResources';

// Type definition for translations
export type TranslationKey = keyof typeof en;
type LocaleCode = keyof typeof extraResources;
type TranslationResource = Record<string, unknown>;

const localeLoaders: Partial<Record<LocaleCode, () => Promise<{ default: TranslationResource }>>> = {
  fr: () => import('./locales/fr.json') as Promise<{ default: TranslationResource }>,
  de: () => import('./locales/de.json') as Promise<{ default: TranslationResource }>,
  it: () => import('./locales/it.json') as Promise<{ default: TranslationResource }>,
  el: () => import('./locales/el.json') as Promise<{ default: TranslationResource }>,
};

const loadingLocales = new Map<string, Promise<boolean>>();

function normalizeLocale(locale: string): LocaleCode {
  const baseLocale = locale.split('-')[0] as LocaleCode;
  return baseLocale in extraResources ? baseLocale : 'en';
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/** Recursively merge `extra` keys into `base`. Only adds or overrides — never removes. */
function deepMerge(
  base: Record<string, unknown>,
  extra?: Record<string, unknown>,
): Record<string, unknown> {
  if (!extra) {
    return base;
  }

  const merged: Record<string, unknown> = { ...base };

  Object.entries(extra).forEach(([key, value]) => {
    const current = merged[key];

    if (isPlainObject(current) && isPlainObject(value)) {
      merged[key] = deepMerge(current, value);
      return;
    }

    merged[key] = value;
  });

  return merged;
}

async function loadLocale(locale: string): Promise<boolean> {
  const normalizedLocale = normalizeLocale(locale);
  if (normalizedLocale === 'en' || i18n.hasResourceBundle(normalizedLocale, 'translation')) {
    return false;
  }

  const existingLoad = loadingLocales.get(normalizedLocale);
  if (existingLoad) return existingLoad;

  const loader = localeLoaders[normalizedLocale];
  if (!loader) return false;

  const load = loader().then(({ default: baseResource }) => {
    i18n.addResourceBundle(
      normalizedLocale,
      'translation',
      deepMerge(baseResource, extraResources[normalizedLocale]),
      true,
      true,
    );
    return true;
  }).finally(() => {
    loadingLocales.delete(normalizedLocale);
  });

  loadingLocales.set(normalizedLocale, load);
  return load;
}

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: deepMerge(en, extraResources.en) },
    },
    fallbackLng: 'en',
    supportedLngs: ['en', 'fr', 'de', 'it', 'el'],
    partialBundledLanguages: true,

    interpolation: {
      escapeValue: false // React already escapes values
    },

    detection: {
      // `querystring` first so hreflang `?lang=xx` URLs resolve to the
      // advertised language; the choice is then cached to localStorage.
      order: ['querystring', 'localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'],
      lookupQuerystring: 'lang',
      lookupLocalStorage: 'eleutherai-language'
    },

    // Date and number formatting
    react: {
      useSuspense: false // Avoid suspense issues
    }
  });

i18n.on('languageChanged', (locale) => {
  if (i18n.hasResourceBundle(normalizeLocale(locale), 'translation')) return;

  void loadLocale(locale).then((loaded) => {
    if (loaded && normalizeLocale(i18n.language) === normalizeLocale(locale)) {
      i18n.emit('languageChanged', i18n.language);
    }
  });
});

void loadLocale(i18n.language).then((loaded) => {
  if (loaded) i18n.emit('languageChanged', i18n.language);
});

export default i18n;

// Language metadata for the switcher
export const languages = [
  { code: 'en', name: 'English', nativeName: 'English', flag: '🇬🇧' },
  { code: 'fr', name: 'French', nativeName: 'Français', flag: '🇫🇷' },
  { code: 'de', name: 'German', nativeName: 'Deutsch', flag: '🇩🇪' },
  { code: 'it', name: 'Italian', nativeName: 'Italiano', flag: '🇮🇹' },
  { code: 'el', name: 'Modern Greek', nativeName: 'Ελληνικά', flag: '🇬🇷' }
];

// Format numbers according to locale
export const formatNumber = (num: number, locale: string = i18n.language): string => {
  return new Intl.NumberFormat(locale).format(num);
};

// Format dates according to locale
export const formatDate = (date: Date | string, locale: string = i18n.language): string => {
  const d = typeof date === 'string' ? new Date(date) : date;
  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  }).format(d);
};

// Format relative time (e.g., "2 days ago")
export const formatRelativeTime = (date: Date | string, locale: string = i18n.language): string => {
  const d = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - d.getTime()) / 1000);

  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' });

  if (diffInSeconds < 60) return rtf.format(-diffInSeconds, 'second');
  if (diffInSeconds < 3600) return rtf.format(-Math.floor(diffInSeconds / 60), 'minute');
  if (diffInSeconds < 86400) return rtf.format(-Math.floor(diffInSeconds / 3600), 'hour');
  if (diffInSeconds < 2592000) return rtf.format(-Math.floor(diffInSeconds / 86400), 'day');
  if (diffInSeconds < 31536000) return rtf.format(-Math.floor(diffInSeconds / 2592000), 'month');
  return rtf.format(-Math.floor(diffInSeconds / 31536000), 'year');
};
