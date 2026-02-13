/**
 * Greek Transliteration Utility
 *
 * Converts polytonic Greek text to Latin alphabet for searchability.
 * Users can type "boul" to find "βούλομαι", "heimarmene" to find "εἱμαρμένη".
 *
 * Follows scholarly romanization conventions:
 * - Rough breathing (spiritus asper) → "h" prefix
 * - Smooth breathing (spiritus lenis) → no prefix
 * - Standard Greek letter mappings (θ→th, φ→ph, χ→ch, ψ→ps)
 */

// Greek to Latin character mapping
const GREEK_TO_LATIN: Record<string, string> = {
  // Lowercase letters
  'α': 'a', 'β': 'b', 'γ': 'g', 'δ': 'd', 'ε': 'e',
  'ζ': 'z', 'η': 'e', 'θ': 'th', 'ι': 'i', 'κ': 'k',
  'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'x', 'ο': 'o',
  'π': 'p', 'ρ': 'r', 'σ': 's', 'ς': 's', 'τ': 't',
  'υ': 'u', 'φ': 'ph', 'χ': 'ch', 'ψ': 'ps', 'ω': 'o',

  // Uppercase letters
  'Α': 'A', 'Β': 'B', 'Γ': 'G', 'Δ': 'D', 'Ε': 'E',
  'Ζ': 'Z', 'Η': 'E', 'Θ': 'Th', 'Ι': 'I', 'Κ': 'K',
  'Λ': 'L', 'Μ': 'M', 'Ν': 'N', 'Ξ': 'X', 'Ο': 'O',
  'Π': 'P', 'Ρ': 'R', 'Σ': 'S', 'Τ': 'T', 'Υ': 'U',
  'Φ': 'Ph', 'Χ': 'Ch', 'Ψ': 'Ps', 'Ω': 'O',

  // Archaic letters (rare but included for completeness)
  'ϝ': 'w', 'Ϝ': 'W',  // Digamma
  'ϙ': 'q', 'Ϙ': 'Q',  // Koppa
  'ϛ': 'st', 'Ϛ': 'St',  // Stigma
  'ϡ': 'ss', 'Ϡ': 'Ss',  // Sampi
};

// Unicode combining character for rough breathing (spiritus asper)
const ROUGH_BREATHING_MARK = '\u0314';  // COMBINING REVERSED COMMA ABOVE (dasia)

/**
 * Check if a Greek character has rough breathing (spiritus asper).
 * Rough breathing indicates an "h" sound at the beginning of a word.
 * Examples: ἁ, ἑ, ἡ, ἱ, ὁ, ὑ, ὡ, ῥ
 */
function hasRoughBreathing(char: string): boolean {
  // Normalize to NFD to separate base char from combining marks
  const normalized = char.normalize('NFD');
  return normalized.includes(ROUGH_BREATHING_MARK);
}

/**
 * Remove all diacritics (accents, breathings, iota subscript) from Greek text.
 * Uses Unicode normalization to decompose characters, then filters out
 * combining diacritical marks.
 */
function stripDiacritics(text: string): string {
  // Normalize to NFD (decomposed form)
  const normalized = text.normalize('NFD');

  // Filter out combining diacritical marks (category 'M')
  // In JavaScript, we check if char code is in the combining diacritical marks range
  let result = '';
  for (const char of normalized) {
    const code = char.charCodeAt(0);
    // Skip combining diacritical marks (0x0300-0x036F) and
    // combining diacritical marks extended (0x1AB0-0x1AFF, 0x1DC0-0x1DFF)
    if (
      (code >= 0x0300 && code <= 0x036F) ||
      (code >= 0x1AB0 && code <= 0x1AFF) ||
      (code >= 0x1DC0 && code <= 0x1DFF)
    ) {
      continue;
    }
    result += char;
  }

  // Normalize back to NFC for consistency
  return result.normalize('NFC');
}

/**
 * Transliterate Greek text to Latin alphabet with proper breathing handling.
 *
 * Steps:
 * 1. Detect rough breathing marks (spiritus asper) → add "h" prefix
 * 2. Handle diphthongs: breathing on second vowel applies to whole diphthong
 * 3. Strip remaining diacritics (accents, smooth breathing)
 * 4. Map Greek letters to Latin equivalents
 * 5. Preserve non-Greek characters (spaces, punctuation)
 *
 * Examples:
 *   βούλομαι → boulomai
 *   ἐφ' ἡμῖν → eph hemin (ἡ has rough breathing → h)
 *   εἱμαρμένη → heimarmene (εἱ has rough breathing on ἱ → hei)
 *   ἑκούσιον → hekousion (ἑ has rough breathing → he)
 *   ὁρμή → horme (ὁ has rough breathing → ho)
 *   αὐτεξούσιον → autexousion (no rough breathing)
 *   θεός → theos
 *   ψυχή → psuche
 *   ῥήτωρ → rhetor (ῥ has rough breathing → rh)
 *   αἵρεσις → hairesis (αἵ diphthong with rough breathing → hai)
 *   οἷος → hoios (οἷ diphthong with rough breathing → hoi)
 */
export function greekToLatin(text: string): string {
  // First vowel characters that can start a diphthong (stripped of diacritics)
  const FIRST_VOWELS = new Set(['α', 'ε', 'η', 'ο', 'ω']);
  // Second vowel characters that can end a diphthong and carry breathing
  const SECOND_VOWELS = new Set(['ι', 'υ']);

  const result: string[] = [];
  const chars = Array.from(text);
  let i = 0;

  while (i < chars.length) {
    const char = chars[i];
    const cleanChar = stripDiacritics(char);

    // Check if this is the first vowel of a potential diphthong
    if (FIRST_VOWELS.has(cleanChar.toLowerCase()) && i + 1 < chars.length) {
      const nextChar = chars[i + 1];
      const nextClean = stripDiacritics(nextChar);

      // Check if next char is ι or υ (completing a diphthong)
      if (SECOND_VOWELS.has(nextClean.toLowerCase())) {
        // Check if the second vowel has rough breathing
        if (hasRoughBreathing(nextChar)) {
          // Diphthong with rough breathing on second vowel
          // Output: h + first_vowel + second_vowel
          const firstLatin = GREEK_TO_LATIN[cleanChar] || cleanChar;
          const secondLatin = GREEK_TO_LATIN[nextClean] || nextClean;

          if (cleanChar === cleanChar.toUpperCase() && cleanChar !== cleanChar.toLowerCase()) {
            result.push('H' + firstLatin + secondLatin.toLowerCase());
          } else {
            result.push('h' + firstLatin + secondLatin);
          }

          i += 2;  // Skip both vowels
          continue;
        }
      }
    }

    // Standard processing for non-diphthong or diphthong without breathing on second vowel
    const addH = hasRoughBreathing(char);

    if (cleanChar in GREEK_TO_LATIN) {
      let latin = GREEK_TO_LATIN[cleanChar];

      if (addH) {
        // Special case: ρ with rough breathing → "rh" (not "hr")
        if (cleanChar === 'ρ' || cleanChar === 'Ρ') {
          latin = cleanChar === 'ρ' ? 'rh' : 'Rh';
        } else {
          // Vowels with rough breathing: add "h" before
          const isUpper = cleanChar === cleanChar.toUpperCase() && cleanChar !== cleanChar.toLowerCase();
          if (isUpper) {
            latin = 'H' + latin;
          } else {
            latin = 'h' + latin;
          }
        }
      }

      result.push(latin);
    } else {
      // Keep non-Greek characters as-is (spaces, punctuation, Latin letters)
      result.push(cleanChar);
    }

    i += 1;
  }

  return result.join('');
}

/**
 * Detect if a query is primarily Latin alphabet (vs Greek).
 * Used to determine if we should search the transliterated column.
 * Returns true if >50% of alphabetic chars are Latin.
 */
export function isLatinQuery(query: string): boolean {
  if (!query) {
    return false;
  }

  let latinCount = 0;
  let greekCount = 0;

  for (const char of query) {
    // Check if character is alphabetic
    if (/[a-zA-Z]/.test(char)) {
      latinCount++;
    } else {
      const code = char.charCodeAt(0);
      // Greek Unicode ranges
      if ((code >= 0x0370 && code <= 0x03FF) || (code >= 0x1F00 && code <= 0x1FFF)) {
        greekCount++;
      }
    }
  }

  const total = latinCount + greekCount;
  if (total === 0) {
    return false;
  }

  return latinCount > greekCount;
}

/**
 * Normalize a query for searching.
 * - If Greek: strip diacritics for fuzzy matching
 * - If Latin: lowercase for case-insensitive search
 * - Remove extra whitespace
 */
export function normalizeForSearch(query: string): string {
  query = query.trim().toLowerCase();

  if (isLatinQuery(query)) {
    return query;
  } else {
    return stripDiacritics(query).toLowerCase();
  }
}

// Common philosophical terms with their transliterations (for testing)
export const PHILOSOPHICAL_TERMS: Record<string, string> = {
  "τὸ ἐφ' ἡμῖν": 'to eph hemin',  // "what is up to us"
  'αὐτεξούσιον': 'autexousion',    // "self-determination"
  'προαίρεσις': 'proairesis',       // "moral choice"
  'βούλησις': 'boulesis',           // "rational wish"
  'ἑκούσιον': 'hekousion',          // "voluntary"
  'ἀκούσιον': 'akousion',           // "involuntary"
  'εἱμαρμένη': 'heimarmene',        // "fate"
  'ἀνάγκη': 'ananke',               // "necessity"
  'τύχη': 'tuche',                  // "chance/fortune"
  'συγκατάθεσις': 'sunkatathesis',  // "assent"
  'ὁρμή': 'horme',                  // "impulse"
  'φαντασία': 'phantasia',          // "impression"
  'λόγος': 'logos',                 // "reason"
  'ψυχή': 'psuche',                 // "soul"
  'νοῦς': 'nous',                   // "intellect"
  'θεός': 'theos',                  // "god"
  'ἀρετή': 'arete',                 // "virtue"
  'εὐδαιμονία': 'eudaimonia',       // "happiness/flourishing"
};
