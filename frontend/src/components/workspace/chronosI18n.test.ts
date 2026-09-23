import { describe, expect, it } from 'vitest';

import de from '../../i18n/locales/de.json';
import el from '../../i18n/locales/el.json';
import en from '../../i18n/locales/en.json';
import fr from '../../i18n/locales/fr.json';
import it_ from '../../i18n/locales/it.json';
import { PERIOD_I18N_KEYS } from './chronosTimeline';

type Tree = { [key: string]: string | Tree };

function flatten(tree: Tree, prefix = ''): Map<string, string> {
  const out = new Map<string, string>();
  Object.entries(tree).forEach(([key, value]) => {
    const path = prefix ? `${prefix}.${key}` : key;
    if (typeof value === 'string') out.set(path, value);
    else flatten(value, path).forEach((leaf, leafPath) => out.set(leafPath, leaf));
  });
  return out;
}

const LOCALES = { en, fr, de, it: it_, el } as const;
const chronos = (locale: { chronos: Tree }) => flatten(locale.chronos);

describe('chronos locale namespace', () => {
  it('has the same keys in all five languages', () => {
    const reference = [...chronos(en).keys()].sort();
    Object.entries(LOCALES).forEach(([, locale]) => {
      expect([...chronos(locale).keys()].sort()).toEqual(reference);
    });
  });

  it('translates every editorial period label', () => {
    Object.values(PERIOD_I18N_KEYS).forEach((key) => {
      expect(chronos(en).has(`periods.${key}`)).toBe(true);
    });
  });

  it('follows French typography: no breakable space before high punctuation or inside guillemets', () => {
    chronos(fr).forEach((value, key) => {
      expect(value, key).not.toMatch(/ [?!;:»%€]/);
      expect(value, key).not.toMatch(/« /);
      expect(value, key).not.toMatch(/[^\u202F\u00A0][?!;]/);
    });
  });
});
