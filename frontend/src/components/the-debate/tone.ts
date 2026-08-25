/**
 * the-debate — the two-and-a-half hue system.
 *
 * Hue = language of the source. Value = focus. That is the whole palette.
 *
 * Aegean  #1E4D6B on parchment #FCF9F4 = 8.6:1
 * Terracotta ink #B44A12 on parchment  = 5.1:1
 * Sage ink #44513F on parchment        = 8.0:1
 *
 * All three clear AA for body text, which is the point: the colour is allowed
 * to touch running prose, so it can carry meaning instead of sitting in a
 * decorative chip.
 */

import type { Tone } from './types';

export interface ToneTokens {
  /** Text colour, AA on parchment. */
  ink: string;
  /** Hairline / rule colour. */
  rule: string;
  /** A 4% wash. Never a card, only a ground for a marginal block. */
  wash: string;
  /** SVG fill, for rail marks. */
  fill: string;
  /** SVG stroke, for rail marks and reuse arcs. */
  stroke: string;
  /** What the hue means, spelled out. Used in the language chip. */
  label: string;
  /** BCP-47 tag for the ancient text this tone stands for. */
  lang: 'grc' | 'la' | 'en';
}

export const TONE: Record<Tone, ToneTokens> = {
  greek: {
    ink: 'text-[#1E4D6B]',
    rule: 'border-[#1E4D6B]/40',
    wash: 'bg-[#1E4D6B]/[0.04]',
    fill: 'fill-[#1E4D6B]',
    stroke: 'stroke-[#1E4D6B]',
    label: 'Greek',
    lang: 'grc',
  },
  latin: {
    ink: 'text-[#B44A12]',
    rule: 'border-[#B44A12]/40',
    wash: 'bg-[#B44A12]/[0.04]',
    fill: 'fill-[#B44A12]',
    stroke: 'stroke-[#B44A12]',
    label: 'Latin',
    lang: 'la',
  },
  meta: {
    ink: 'text-[#44513F]',
    rule: 'border-[#44513F]/40',
    wash: 'bg-[#44513F]/[0.04]',
    fill: 'fill-[#44513F]',
    stroke: 'stroke-[#44513F]',
    label: 'Modern scholarship',
    lang: 'en',
  },
};

/** Leading is not a style choice: polytonic diacritics need the room. */
export const ANCIENT_LEADING: Record<'grc' | 'la', string> = {
  grc: 'leading-[1.85]',
  la: 'leading-[1.72]',
};

/**
 * EB Garamond ships an OpenType `locl` feature for Latin, and it is on by
 * default the moment a run is marked `lang="la"`: u is substituted with v, so
 * Cicero's `volubilitas` renders as `volvbilitas` and Boethius' `igitur` as
 * `igitvr`. That is a defensible epigraphic convention and it is not what the
 * edition prints. Silently re-spelling a critical text is exactly the kind of
 * quiet fabrication this project forbids, so the feature is switched off on
 * every Latin run and `lang="la"` is kept for screen readers and hyphenation.
 *
 * Greek needs no equivalent: the polytonic coverage comes from the greek-ext
 * subset, which the app already loads, and it substitutes nothing.
 */
export const EDITION_ORTHOGRAPHY: Record<'grc' | 'la', string> = {
  grc: '',
  la: "[font-feature-settings:'locl'_0]",
};

/** Measure, likewise. Greek words are long and the diacritics are dense. */
export const ANCIENT_MEASURE: Record<'grc' | 'la', string> = {
  grc: 'max-w-[48ch]',
  la: 'max-w-[52ch]',
};
