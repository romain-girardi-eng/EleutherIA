/**
 * Passage Reference Detector Service
 * Detects and resolves explicit passage references in queries
 *
 * When a user asks about "De Fato 39", we should:
 * 1. Detect this is a specific passage reference
 * 2. Look up the exact passage from the database
 * 3. Include it in the context with highest priority
 */

import { Env } from '../types';
import { getLogger } from '../utils/logger';

const logger = getLogger('PassageReferenceDetector');

// Author patterns - detect author mentions to disambiguate works
const AUTHOR_PATTERNS: Record<string, string[]> = {
  'Alexander': ['alexander of aphrodisias', 'alexander', 'alex\\.'],
  'Cicero': ['marcus tullius cicero', 'cicero', 'tully'],
  'Epictetus': ['epictetus'],
  'Marcus Aurelius': ['marcus aurelius', 'marcus'],
  'Lucretius': ['lucretius', 'titus lucretius'],
  'Aristotle': ['aristotle'],
  'Plato': ['plato'],
  'Augustine': ['augustine', 'st\\. augustine'],
  'Plotinus': ['plotinus'],
  'Seneca': ['seneca'],
  'Origen': ['origen'],
  'Justin': ['justin martyr', 'justin'],
  'Irenaeus': ['irenaeus'],
  'Tatian': ['tatian'],
  'Theophilus': ['theophilus'],
  'Melito': ['melito'],
};

// Work title patterns and their canonical forms
// Order matters - longer/more specific patterns first!
const WORK_PATTERNS: Array<{ pattern: string; author: string; titlePattern: string; priority: number }> = [
  // Alexander of Aphrodisias - MUST come before generic "De Fato"
  { pattern: "alexander(?:'s)?\\s+de\\s+fato", author: 'Alexander', titlePattern: '%Fato%', priority: 10 },
  { pattern: "alexander of aphrodisias(?:'s)?\\s+de\\s+fato", author: 'Alexander', titlePattern: '%Fato%', priority: 10 },
  { pattern: "alexander(?:'s)?\\s+on\\s+fate", author: 'Alexander', titlePattern: '%Fato%', priority: 10 },

  // Cicero - generic "De Fato" defaults to Cicero
  { pattern: "cicero(?:'s)?\\s+de\\s+fato", author: 'Cicero', titlePattern: '%Fato%', priority: 9 },
  { pattern: "de\\s+fato", author: 'Cicero', titlePattern: '%Fato%', priority: 5 }, // Default

  // Other Cicero works
  { pattern: "de\\s+finibus", author: 'Cicero', titlePattern: '%Finibus%', priority: 5 },
  { pattern: "de\\s+natura\\s+deorum", author: 'Cicero', titlePattern: '%Natura Deorum%', priority: 5 },
  { pattern: "tusculan", author: 'Cicero', titlePattern: '%Tusculan%', priority: 5 },

  // Lucretius
  { pattern: "de\\s+rerum\\s+natura", author: 'Lucretius', titlePattern: '%Rerum Natura%', priority: 5 },
  { pattern: "drn", author: 'Lucretius', titlePattern: '%Rerum Natura%', priority: 5 },

  // Epictetus
  { pattern: "epictetus(?:'s)?\\s+discourses?", author: 'Epictetus', titlePattern: '%Discourse%', priority: 9 },
  { pattern: "discourses?", author: 'Epictetus', titlePattern: '%Discourse%', priority: 5 },
  { pattern: "enchiridion", author: 'Epictetus', titlePattern: '%Enchiridion%', priority: 5 },
  { pattern: "handbook", author: 'Epictetus', titlePattern: '%Enchiridion%', priority: 5 },

  // Marcus Aurelius
  { pattern: "marcus\\s+aurelius(?:'s)?\\s+meditations?", author: 'Marcus Aurelius', titlePattern: '%Meditation%', priority: 9 },
  { pattern: "meditations?", author: 'Marcus Aurelius', titlePattern: '%Meditation%', priority: 5 },

  // Aristotle
  { pattern: "nicomachean\\s+ethics", author: 'Aristotle', titlePattern: '%Nicomachean%', priority: 5 },
  { pattern: "\\bne\\b", author: 'Aristotle', titlePattern: '%Nicomachean%', priority: 3 },
  { pattern: "\\ben\\b", author: 'Aristotle', titlePattern: '%Nicomachean%', priority: 3 },
  { pattern: "de\\s+interpretatione", author: 'Aristotle', titlePattern: '%Interpretatione%', priority: 5 },
  { pattern: "physics", author: 'Aristotle', titlePattern: '%Physics%', priority: 5 },
  { pattern: "metaphysics", author: 'Aristotle', titlePattern: '%Metaphysics%', priority: 5 },

  // Augustine
  { pattern: "de\\s+libero\\s+arbitrio", author: 'Augustine', titlePattern: '%Libero Arbitrio%', priority: 5 },
  { pattern: "confessions?", author: 'Augustine', titlePattern: '%Confession%', priority: 5 },

  // Plotinus
  { pattern: "plotinus(?:'s)?\\s+enneads?", author: 'Plotinus', titlePattern: '%Ennead%', priority: 9 },
  { pattern: "enneads?", author: 'Plotinus', titlePattern: '%Ennead%', priority: 5 },

  // Seneca
  { pattern: "epistulae\\s+morales", author: 'Seneca', titlePattern: '%Epistul%', priority: 5 },
  { pattern: "letters", author: 'Seneca', titlePattern: '%Epistul%', priority: 3 },
  { pattern: "de\\s+providentia", author: 'Seneca', titlePattern: '%Providentia%', priority: 5 },
  { pattern: "de\\s+ira", author: 'Seneca', titlePattern: '%Ira%', priority: 5 },

  // Origen
  { pattern: "de\\s+principiis", author: 'Origen', titlePattern: '%Principiis%', priority: 5 },
  { pattern: "on\\s+first\\s+principles", author: 'Origen', titlePattern: '%Principiis%', priority: 5 },

  // Justin Martyr
  { pattern: "first\\s+apology", author: 'Justin', titlePattern: '%Apologia%Prima%', priority: 5 },
  { pattern: "apology", author: 'Justin', titlePattern: '%Apolog%', priority: 3 },
  { pattern: "dialogue\\s+with\\s+trypho", author: 'Justin', titlePattern: '%Dialog%', priority: 5 },

  // Irenaeus
  { pattern: "adversus\\s+haereses", author: 'Irenaeus', titlePattern: '%Haereses%', priority: 5 },
  { pattern: "against\\s+heresies", author: 'Irenaeus', titlePattern: '%Haereses%', priority: 5 },

  // Tatian
  { pattern: "oratio\\s+ad\\s+graecos", author: 'Tatian', titlePattern: '%Oratio%', priority: 5 },

  // Theophilus
  { pattern: "ad\\s+autolycum", author: 'Theophilus', titlePattern: '%Autolycum%', priority: 5 },
];

export interface PassageReference {
  workTitle: string;
  author: string;
  section: string;
  book?: string;
  chapter?: string;
  fullReference: string;
}

export interface ResolvedPassage {
  passageId: string;
  workId: string;
  ctsUrn: string;
  section: string;
  book?: string;
  chapter?: string;
  textContent: string;
  author: string;
  workTitle: string;
}

// Roman numeral conversion
function romanToArabic(roman: string): number {
  const romanMap: Record<string, number> = {
    'i': 1, 'v': 5, 'x': 10, 'l': 50, 'c': 100, 'd': 500, 'm': 1000
  };
  let result = 0;
  const lower = roman.toLowerCase();
  for (let i = 0; i < lower.length; i++) {
    const current = romanMap[lower[i]] || 0;
    const next = romanMap[lower[i + 1]] || 0;
    if (current < next) {
      result -= current;
    } else {
      result += current;
    }
  }
  return result;
}

/**
 * Detect passage references in a query
 */
export function detectPassageReferences(query: string): PassageReference[] {
  const references: PassageReference[] = [];
  const lowerQuery = query.toLowerCase();

  // First, check if a specific author is mentioned to disambiguate
  let detectedAuthor: string | null = null;
  for (const [author, patterns] of Object.entries(AUTHOR_PATTERNS)) {
    for (const pattern of patterns) {
      if (new RegExp(pattern, 'i').test(lowerQuery)) {
        detectedAuthor = author;
        break;
      }
    }
    if (detectedAuthor) break;
  }

  logger.info(`Detected author in query: ${detectedAuthor || 'none'}`);

  // Sort patterns by priority (higher first)
  const sortedPatterns = [...WORK_PATTERNS].sort((a, b) => b.priority - a.priority);

  // Section number patterns
  const sectionPatterns = [
    // "Work 39" or "Work section 39" (also handles "39-42" ranges - captures just the start)
    /\s+(?:section\s+)?(\d+)(?:-\d+)?(?:\s|$|[,;.?!])/i,
    // "Work 6.8" or "Work 2.2"
    /\s+(\d+\.\d+(?:\.\d+)?)(?:\s|$|[,;.?!])/i,
    // "Work III.1" or "Work II.251" or "Work II.251-260" (roman numerals)
    /\s+((?:i{1,3}|iv|v|vi{0,3}|ix|x|xi{1,3}|xiv|xv|xvi{0,3}|xix|xx)[.:]?\d+(?:\.\d+)?)(?:-\d+)?(?:\s|$|[,;.?!])/i,
    // "Work I.1.1" (book.chapter.section)
    /\s+((?:i{1,3}|iv|v|vi{0,3}|ix|x)[.:]\d+[.:]\d+)(?:\s|$|[,;.?!])/i,
  ];

  for (const workPattern of sortedPatterns) {
    // Determine which author to use:
    // - If detected author matches pattern author, use pattern author
    // - If detected author differs but pattern is generic (priority < 9), use detected author
    // - If detected author differs and pattern is author-specific (priority >= 9), skip
    let effectiveAuthor = workPattern.author;

    if (detectedAuthor && workPattern.author !== detectedAuthor) {
      if (workPattern.priority >= 9) {
        // Author-specific pattern for wrong author - skip
        continue;
      }
      // Generic pattern - use the detected author instead
      effectiveAuthor = detectedAuthor;
    }

    const workRegex = new RegExp(workPattern.pattern, 'gi');
    let workMatch;

    while ((workMatch = workRegex.exec(lowerQuery)) !== null) {
      const workMatchEnd = workMatch.index + workMatch[0].length;
      const restOfQuery = lowerQuery.substring(workMatchEnd);

      // Try to find a section number after the work title
      for (const sectionPattern of sectionPatterns) {
        const sectionMatch = restOfQuery.match(sectionPattern);
        if (sectionMatch) {
          let sectionRef = sectionMatch[1];
          let book: string | undefined;
          let chapter: string | undefined;
          let section: string;

          // Parse the section reference
          if (/^[ivxlcdm]+/i.test(sectionRef)) {
            // Roman numeral prefix
            const romanMatch = sectionRef.match(/^([ivxlcdm]+)[.:]?(.*)$/i);
            if (romanMatch) {
              book = String(romanToArabic(romanMatch[1]));
              const rest = romanMatch[2];
              if (rest.includes('.')) {
                const parts = rest.split('.');
                chapter = parts[0];
                section = parts.slice(1).join('.');
              } else {
                section = rest;
              }
            } else {
              section = sectionRef;
            }
          } else if (sectionRef.includes('.')) {
            // Decimal format: 6.8 or 2.2.1
            const parts = sectionRef.split('.');
            if (parts.length === 2) {
              book = parts[0];
              section = parts[1];
            } else if (parts.length >= 3) {
              book = parts[0];
              chapter = parts[1];
              section = parts.slice(2).join('.');
            } else {
              section = sectionRef;
            }
          } else {
            section = sectionRef;
          }

          const fullRef = workMatch[0] + sectionMatch[0].trim();

          references.push({
            workTitle: workPattern.titlePattern,
            author: effectiveAuthor,
            section,
            book,
            chapter,
            fullReference: fullRef.trim(),
          });

          logger.info(`Detected passage reference: ${fullRef.trim()} -> ${effectiveAuthor}, ${workPattern.titlePattern}, section ${section}, book ${book || 'none'}`);

          // Only take the first section match for this work
          break;
        }
      }
    }
  }

  // Remove duplicates (same work + section)
  const unique = references.filter((ref, index, self) =>
    index === self.findIndex(r =>
      r.author === ref.author &&
      r.workTitle === ref.workTitle &&
      r.section === ref.section &&
      r.book === ref.book
    )
  );

  logger.info(`Detected ${unique.length} passage references in query`, { references: unique });
  return unique;
}

/**
 * Resolve passage references to actual database passages
 */
export async function resolvePassageReferences(
  references: PassageReference[],
  env: Env
): Promise<ResolvedPassage[]> {
  if (references.length === 0) return [];

  const resolved: ResolvedPassage[] = [];
  const supabaseUrl = env.SUPABASE_URL.replace(/\/+$/, '').replace(/\/rest\/v1$/i, '');
  const supabaseKey = env.SUPABASE_KEY;

  for (const ref of references) {
    try {
      // Try RPC function first
      const rpcUrl = `${supabaseUrl}/rest/v1/rpc/get_passage_by_reference`;

      logger.info(`Calling RPC for: author=${ref.author}, title=${ref.workTitle}, section=${ref.section}, book=${ref.book || 'null'}`);

      const response = await fetch(rpcUrl, {
        method: 'POST',
        headers: {
          'apikey': supabaseKey,
          'Authorization': `Bearer ${supabaseKey}`,
          'Content-Type': 'application/json',
          'Accept-Profile': 'public',
          'Content-Profile': 'public',
        },
        body: JSON.stringify({
          p_author_pattern: `%${ref.author}%`,
          p_title_pattern: ref.workTitle,
          p_section: ref.section,
          p_book: ref.book || null,
        }),
      });

      logger.info(`RPC response status: ${response.status}`);

      if (response.ok) {
        const passages = await response.json();
        logger.info(`RPC returned ${passages?.length || 0} passages`);
        if (passages && passages.length > 0) {
          const p = passages[0];
          resolved.push({
            passageId: p.passage_id,
            workId: p.work_id,
            ctsUrn: p.cts_urn,
            section: p.section,
            book: p.book,
            chapter: p.chapter,
            textContent: p.text_content,
            author: p.author,
            workTitle: p.title,
          });
          logger.info(`Resolved passage reference: ${ref.fullReference} -> ${p.cts_urn}`);
          continue;
        }
      } else {
        const errorText = await response.text();
        logger.warn(`RPC call failed: ${response.status} - ${errorText}`);
      }

      // Fallback: Try direct query to passages table
      logger.info(`Trying fallback query for section=${ref.section}, book=${ref.book || 'null'}`);
      const queryUrl = new URL(`${supabaseUrl}/rest/v1/passages`);
      queryUrl.searchParams.set('select', 'passage_id,work_id,cts_urn,section,book,chapter,text_content,ancient_works(author,title)');
      queryUrl.searchParams.set('section', `eq.${ref.section}`);
      if (ref.book) {
        queryUrl.searchParams.set('book', `eq.${ref.book}`);
      }
      queryUrl.searchParams.set('limit', '5');

      const fallbackResponse = await fetch(queryUrl.toString(), {
        headers: {
          'apikey': supabaseKey,
          'Authorization': `Bearer ${supabaseKey}`,
          'Accept-Profile': 'free_will',
        },
      });

      logger.info(`Fallback response status: ${fallbackResponse.status}`);

      if (fallbackResponse.ok) {
        const passages = await fallbackResponse.json();
        logger.info(`Fallback returned ${passages?.length || 0} passages`);
        // Filter by author
        const titlePatternLower = ref.workTitle.replace(/%/g, '').toLowerCase();
        const matching = passages.filter((p: any) =>
          p.ancient_works?.author?.toLowerCase().includes(ref.author.toLowerCase()) &&
          p.ancient_works?.title?.toLowerCase().includes(titlePatternLower)
        );
        logger.info(`After filtering by author/title: ${matching.length} matches`);
        if (matching.length > 0) {
          const p = matching[0];
          resolved.push({
            passageId: p.passage_id,
            workId: p.work_id,
            ctsUrn: p.cts_urn,
            section: p.section,
            book: p.book,
            chapter: p.chapter,
            textContent: p.text_content,
            author: p.ancient_works?.author || ref.author,
            workTitle: p.ancient_works?.title || ref.workTitle,
          });
          logger.info(`Resolved via fallback: ${ref.fullReference} -> ${p.cts_urn}`);
        }
      } else {
        const errorText = await fallbackResponse.text();
        logger.warn(`Fallback query failed: ${fallbackResponse.status} - ${errorText}`);
      }

    } catch (error) {
      logger.warn(`Failed to resolve passage reference: ${ref.fullReference}`, error);
    }
  }

  return resolved;
}

/**
 * Build priority context from resolved passages
 * These should appear FIRST in the context, before semantic search results
 */
export function buildPassageContext(passages: ResolvedPassage[]): string {
  if (passages.length === 0) return '';

  const parts: string[] = [
    '=== EXACT PASSAGE REQUESTED ===',
    '(The user specifically asked about this passage - this is the PRIMARY source)',
    '',
  ];

  for (const p of passages) {
    parts.push(`[${p.author}, ${p.workTitle} ${p.book ? p.book + '.' : ''}${p.section}]`);
    if (p.ctsUrn) {
      parts.push(`CTS URN: ${p.ctsUrn}`);
    }
    parts.push('');
    parts.push(p.textContent);
    parts.push('');
    parts.push('---');
  }

  return parts.join('\n');
}
