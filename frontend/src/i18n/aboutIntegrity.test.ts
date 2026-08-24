import { describe, expect, it } from 'vitest';

import de from './locales/de.json';
import el from './locales/el.json';
import en from './locales/en.json';
import fr from './locales/fr.json';
import itLocale from './locales/it.json';

const locales = { de, el, en, fr, it: itLocale } as const;

const legacyAbsoluteClaims = [
  'Every node, edge, and citation',
  'Chaque nœud, arête et citation',
  'Jeder Knoten, jede Kante und jedes Zitat',
  'Ogni nodo, relazione e citazione',
  'Κάθε κόμβος, ακμή και παραπομπή',
  'All Greek and Latin texts undergo manual verification',
  "Tous les textes grecs et latins font l'objet d'une vérification manuelle",
  'Alle griechischen und lateinischen Texte durchlaufen manuelle Überprüfung',
  'Tutti i testi greci e latini sono sottoposti a verifica manuale',
  'Όλα τα ελληνικά και λατινικά κείμενα υφίστανται χειροκίνητη επαλήθευση',
];

describe('multilingual scholarly-integrity copy', () => {
  it('preserves live-stat placeholders without claiming universal verification', () => {
    for (const messages of Object.values(locales)) {
      const details = messages.about.projectDetails;
      const placeholders = [...details.matchAll(/\{\{([^}]+)}}/g)].map(
        (match) => match[1],
      );
      expect(new Set(placeholders)).toEqual(
        new Set(['nodes', 'edges', 'works', 'passages']),
      );
      for (const claim of legacyAbsoluteClaims) {
        expect(details).not.toContain(claim);
        expect(messages.about.philoDesc).not.toContain(claim);
      }
    }
  });
});
