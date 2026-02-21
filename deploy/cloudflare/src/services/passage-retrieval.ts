/**
 * Passage-Level Retrieval Service
 *
 * Fetches actual ancient text passages linked to KG nodes via passage_citations.
 * Bridges the gap between abstract KG evidence and concrete textual evidence.
 */

import { Env } from '../types';
import { getLogger } from '../utils/logger';

const logger = getLogger('PassageRetrieval');

export interface Passage {
  passageId: string;
  textContent: string;
  canonicalRef: string;
  author: string;
  workTitle: string;
  language: 'grc' | 'lat';
  ctsUrn?: string;
  confidence: number;
  book?: string;
  chapter?: string;
  section?: string;
}

export class PassageRetrievalService {
  private env: Env;

  constructor(env: Env) {
    this.env = env;
  }

  /**
   * Fetch passages linked to KG nodes via passage_citations table.
   * Uses a single batched Supabase REST call.
   */
  async fetchPassagesForNodes(nodeIds: string[], limit: number = 10): Promise<Passage[]> {
    if (nodeIds.length === 0) return [];

    try {
      const idsParam = nodeIds.map(id => `"${id}"`).join(',');

      // Query passage_citations joined with passages and ancient_works
      const url = `${this.env.SUPABASE_URL}/rest/v1/passage_citations?kg_node_id=in.(${idsParam})&select=confidence,passages(passage_id,text_content,cts_urn,book,chapter,section,ancient_works(author,title,language))&order=confidence.desc&limit=${limit}`;

      const response = await fetch(url, {
        headers: {
          'apikey': this.env.SUPABASE_KEY,
          'Authorization': `Bearer ${this.env.SUPABASE_KEY}`,
          'Accept-Profile': 'free_will',
        },
      });

      if (!response.ok) {
        logger.warn(`Passage fetch failed: ${response.status}`);
        return [];
      }

      const citations = await response.json() as any[];
      const passages: Passage[] = [];
      const seen = new Set<string>();

      for (const citation of citations) {
        const p = citation.passages;
        if (!p || !p.text_content || seen.has(p.passage_id)) continue;
        seen.add(p.passage_id);

        const work = p.ancient_works || {};
        const ref = this.formatReference(work.title, p.book, p.chapter, p.section);

        passages.push({
          passageId: p.passage_id,
          textContent: p.text_content,
          canonicalRef: ref,
          author: work.author || 'Unknown',
          workTitle: work.title || 'Unknown Work',
          language: work.language === 'lat' ? 'lat' : 'grc',
          ctsUrn: p.cts_urn || undefined,
          confidence: citation.confidence || 0.5,
          book: p.book || undefined,
          chapter: p.chapter || undefined,
          section: p.section || undefined,
        });
      }

      logger.info(`Fetched ${passages.length} passages for ${nodeIds.length} nodes`);
      return passages;
    } catch (error) {
      logger.error('Error fetching passages for nodes', error);
      return [];
    }
  }

  /**
   * Fetch context-expanded passages (surrounding passages for context window).
   */
  async fetchContextExpanded(passageId: string, window: number = 2): Promise<Passage[]> {
    try {
      // Get the passage's work_id and position first
      const url = `${this.env.SUPABASE_URL}/rest/v1/passages?passage_id=eq.${passageId}&select=work_id,position,passage_id,text_content,cts_urn,book,chapter,section,ancient_works(author,title,language)`;

      const response = await fetch(url, {
        headers: {
          'apikey': this.env.SUPABASE_KEY,
          'Authorization': `Bearer ${this.env.SUPABASE_KEY}`,
          'Accept-Profile': 'free_will',
        },
      });

      if (!response.ok) return [];

      const data = await response.json() as any[];
      if (data.length === 0) return [];

      const passage = data[0];
      const position = passage.position || 0;
      const workId = passage.work_id;

      // Fetch surrounding passages
      const contextUrl = `${this.env.SUPABASE_URL}/rest/v1/passages?work_id=eq.${workId}&position=gte.${position - window}&position=lte.${position + window}&select=passage_id,text_content,cts_urn,book,chapter,section,ancient_works(author,title,language)&order=position`;

      const contextResponse = await fetch(contextUrl, {
        headers: {
          'apikey': this.env.SUPABASE_KEY,
          'Authorization': `Bearer ${this.env.SUPABASE_KEY}`,
          'Accept-Profile': 'free_will',
        },
      });

      if (!contextResponse.ok) return [];

      const contextData = await contextResponse.json() as any[];
      return contextData.map((p: any) => {
        const work = p.ancient_works || {};
        return {
          passageId: p.passage_id,
          textContent: p.text_content || '',
          canonicalRef: this.formatReference(work.title, p.book, p.chapter, p.section),
          author: work.author || 'Unknown',
          workTitle: work.title || 'Unknown Work',
          language: work.language === 'lat' ? 'lat' : 'grc',
          ctsUrn: p.cts_urn || undefined,
          confidence: 1.0,
          book: p.book || undefined,
          chapter: p.chapter || undefined,
          section: p.section || undefined,
        };
      });
    } catch (error) {
      logger.error('Error fetching context-expanded passages', error);
      return [];
    }
  }

  private formatReference(
    title?: string, book?: string, chapter?: string, section?: string
  ): string {
    const parts: string[] = [];
    if (title) parts.push(title);
    const loc: string[] = [];
    if (book) loc.push(book);
    if (chapter) loc.push(chapter);
    if (section) loc.push(section);
    if (loc.length > 0) parts.push(loc.join('.'));
    return parts.join(' ');
  }
}
