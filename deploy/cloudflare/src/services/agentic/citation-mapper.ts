/**
 * Citation Mapper Service
 *
 * Generates numbered citations [1], [2], [3] for evidence and maps them
 * to specific graph node IDs for full traceability and verification.
 */

import { Evidence, SourceCitation, EvidenceMap } from '../../types/agentic';
import { GraphNode } from '../../types';

export class CitationMapper {
  private citationCounter: number = 0;
  private evidenceMap: EvidenceMap = {};
  private sourceCitations: SourceCitation[] = [];
  private nodeRegistry: Map<string, GraphNode> = new Map();

  /**
   * Reset citation counter for new query
   */
  reset(): void {
    this.citationCounter = 0;
    this.evidenceMap = {};
    this.sourceCitations = [];
    this.nodeRegistry.clear();
  }

  /**
   * Register a node for citation tracking
   */
  registerNode(node: GraphNode): void {
    this.nodeRegistry.set(node.id, node);
  }

  /**
   * Register multiple nodes
   */
  registerNodes(nodes: GraphNode[]): void {
    nodes.forEach(node => this.registerNode(node));
  }

  /**
   * Generate citation for evidence
   * Returns the citation number to use in text [1], [2], etc.
   */
  generateCitation(evidence: Evidence): number {
    // Check if we already have a citation for this node
    const existingCitation = this.findExistingCitation(evidence.nodeId);
    if (existingCitation) {
      return existingCitation.id;
    }

    // Create new citation
    this.citationCounter++;
    const citationId = this.citationCounter;

    // Add to evidence map
    if (evidence.nodeId) {
      this.evidenceMap[citationId] = {
        nodeId: evidence.nodeId,
        nodePath: evidence.nodePath,
        confidence: evidence.confidence,
        type: evidence.type
      };
    }

    // Create source citation with full details
    if (evidence.nodeId && this.nodeRegistry.has(evidence.nodeId)) {
      const node = this.nodeRegistry.get(evidence.nodeId)!;

      const sourceCitation: SourceCitation = {
        id: citationId,
        nodeId: evidence.nodeId,
        nodeLabel: evidence.nodeLabel || node.label,
        nodeType: evidence.nodeType || node.type,
        content: this.extractNodeContent(node),
        url: `/node/${evidence.nodeId}`,
        metadata: {
          school: node.properties?.school,
          period: node.properties?.period,
          author: node.properties?.author,
          confidence: evidence.confidence
        }
      };

      this.sourceCitations.push(sourceCitation);
    }

    // Update evidence with citation ID
    evidence.citationId = citationId;

    return citationId;
  }

  /**
   * Find existing citation for a node ID
   */
  private findExistingCitation(nodeId?: string): SourceCitation | undefined {
    if (!nodeId) return undefined;
    return this.sourceCitations.find(c => c.nodeId === nodeId);
  }

  /**
   * Extract meaningful content from node
   */
  private extractNodeContent(node: GraphNode): string {
    // Prioritize different content fields based on node type
    if (node.type === 'quote' && node.properties?.quote) {
      return node.properties.quote;
    }
    if (node.type === 'argument' && node.properties?.premise) {
      return node.properties.premise;
    }
    if (node.properties?.description) {
      return node.properties.description;
    }
    if (node.properties?.content) {
      return node.properties.content;
    }

    // Fallback to label if no content
    return node.label;
  }

  /**
   * Format text with citations
   * Replaces placeholder markers with proper citation numbers
   */
  formatWithCitations(text: string, evidenceList: Evidence[]): string {
    let formattedText = text;

    // Generate citations for all evidence
    const citations = evidenceList.map(e => this.generateCitation(e));

    // Replace placeholders like {{cite:0}}, {{cite:1}} with [1], [2]
    evidenceList.forEach((evidence, index) => {
      const placeholder = `{{cite:${index}}}`;
      const citation = `[${citations[index]}]`;
      formattedText = formattedText.replace(new RegExp(placeholder, 'g'), citation);
    });

    return formattedText;
  }

  /**
   * Add citation to specific claim in text
   */
  addCitationToClaim(claim: string, evidence: Evidence): string {
    const citationId = this.generateCitation(evidence);
    return `${claim} [${citationId}]`;
  }

  /**
   * Get all source citations
   */
  getSourceCitations(): SourceCitation[] {
    return this.sourceCitations;
  }

  /**
   * Get evidence map
   */
  getEvidenceMap(): EvidenceMap {
    return this.evidenceMap;
  }

  /**
   * Generate citation summary section
   */
  generateCitationSummary(): string {
    if (this.sourceCitations.length === 0) {
      return '';
    }

    let summary = '\n\n## Sources\n\n';

    for (const citation of this.sourceCitations) {
      summary += `[${citation.id}] **${citation.nodeLabel}**`;

      if (citation.nodeType) {
        summary += ` (${citation.nodeType})`;
      }

      if (citation.metadata.author) {
        summary += ` - ${citation.metadata.author}`;
      }

      if (citation.metadata.period) {
        summary += `, ${citation.metadata.period}`;
      }

      summary += '\n';

      // Add content excerpt
      const contentExcerpt = citation.content.length > 200
        ? citation.content.substring(0, 200) + '...'
        : citation.content;
      summary += `   *"${contentExcerpt}"*\n`;

      // Add link
      summary += `   [View in graph](${citation.url})\n\n`;
    }

    return summary;
  }

  /**
   * Validate citations in text
   * Ensures all citations have corresponding sources
   */
  validateCitations(text: string): boolean {
    const citationPattern = /\[(\d+)\]/g;
    const matches = text.match(citationPattern);

    if (!matches) return true; // No citations to validate

    for (const match of matches) {
      const citationId = parseInt(match.slice(1, -1));
      if (!this.evidenceMap[citationId]) {
        console.warn(`Citation [${citationId}] has no corresponding evidence`);
        return false;
      }
    }

    return true;
  }

  /**
   * Get citation statistics
   */
  getStats() {
    return {
      totalCitations: this.citationCounter,
      uniqueNodes: new Set(Object.values(this.evidenceMap).map(e => e.nodeId)).size,
      sourceTypes: this.sourceCitations.reduce((acc, c) => {
        acc[c.nodeType] = (acc[c.nodeType] || 0) + 1;
        return acc;
      }, {} as Record<string, number>)
    };
  }
}

// Singleton instance
export const citationMapper = new CitationMapper();