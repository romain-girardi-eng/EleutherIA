import { describe, it, expect } from 'vitest';
import {
  buildResolvedCitations,
  buildBibliography,
  isLeakedId,
} from './citationBibliography';
import type { PassageCitation } from '../types';

const LEAKED_RE =
  /^(?:b_[0-9a-f]+|scholarly_argument_|scholar_position_|concept_|person_|work_|argument_|publication_|pub_)/;

describe('citationBibliography', () => {
  it('flags raw node ids as leaked', () => {
    expect(isLeakedId('scholarly_argument_long_2002')).toBe(true);
    expect(isLeakedId('b_2dceaab7')).toBe(true);
    expect(isLeakedId('publication_bobzien_1998')).toBe(true);
    expect(isLeakedId('Bobzien, S. (1998). Determinism and Freedom')).toBe(false);
    expect(isLeakedId('')).toBe(false);
  });

  it('builds resolved citations from typed passage_citations, keeping the id but never rendering it', () => {
    const passageCitations: PassageCitation[] = [
      {
        ref: 'P1',
        type: 'passage',
        id: 'b_2dceaab7',
        label: 'Cicero, De Fato 41-43',
        layer: 'primary',
        cts_urn: 'urn:cts:latinLit:phi0474.phi049:41-43',
      },
      {
        ref: 'P2',
        type: 'node',
        id: 'publication_bobzien_1998',
        label: 'Bobzien, S. (1998). Determinism and Freedom in Stoic Philosophy.',
        layer: 'secondary',
        doi: '10.1093/0199247676.001.0001',
      },
    ];

    const resolved = buildResolvedCitations(passageCitations, undefined, undefined);

    expect(resolved).toHaveLength(2);
    for (const c of resolved) {
      // The rendered label is the resolved human label, NEVER the node id.
      expect(c.text).not.toBe(c.node_id);
      expect(c.text).not.toMatch(LEAKED_RE);
    }
    const primary = resolved.find((c) => c.layer === 'primary');
    expect(primary?.text).toBe('Cicero, De Fato 41-43');
    expect(primary?.node_id).toBe('b_2dceaab7'); // id kept for click routing
    expect(primary?.cts_urn).toBe('urn:cts:latinLit:phi0474.phi049:41-43');
  });

  it('drops typed citations whose label is still a raw leaked id', () => {
    const passageCitations: PassageCitation[] = [
      {
        ref: 'P1',
        type: 'node',
        id: 'scholar_position_long_2002',
        label: 'scholar_position_long_2002', // unresolved → must be hidden
        layer: 'secondary',
      },
      {
        ref: 'P2',
        type: 'passage',
        id: 'b_abc',
        label: 'Epictetus, Discourses 1.1',
        layer: 'primary',
      },
    ];
    const resolved = buildResolvedCitations(passageCitations, undefined, undefined);
    expect(resolved).toHaveLength(1);
    expect(resolved[0].text).toBe('Epictetus, Discourses 1.1');
  });

  it('falls back to ancient/modern string lists only when no typed citations exist', () => {
    const resolved = buildResolvedCitations(
      [],
      ['Cicero, On Fate 41-43'],
      ['Frede, M. (2011). A Free Will.'],
    );
    expect(resolved.map((c) => c.text)).toEqual([
      'Cicero, On Fate 41-43',
      'Frede, M. (2011). A Free Will.',
    ]);
    expect(resolved[0].layer).toBe('primary');
    expect(resolved[1].layer).toBe('secondary');
  });

  it('builds a deduplicated, author-sorted bibliography with structured bibtex', () => {
    const resolved = buildResolvedCitations(
      [
        {
          id: 'pub_frede',
          label: 'Frede, M. (2011). A Free Will: Origins of the Notion.',
          layer: 'secondary',
          doi: '10.1525/9780520947443',
        },
        {
          id: 'pub_bobzien',
          label: 'Bobzien, S. (1998). Determinism and Freedom in Stoic Philosophy.',
          layer: 'secondary',
        },
        {
          id: 'pub_bobzien_dup',
          label: 'Bobzien, S. (1998). Determinism and Freedom in Stoic Philosophy.',
          layer: 'secondary',
        },
      ],
      undefined,
      undefined,
    );
    const biblio = buildBibliography(resolved.filter((c) => c.layer === 'secondary'));

    // Deduplicated (two identical Bobzien entries collapse to one).
    expect(biblio).toHaveLength(2);
    // Sorted by author: Bobzien before Frede.
    expect(biblio.map((e) => e.author)).toEqual(['Bobzien', 'Frede']);
    // BibTeX built from structured fields, never leaks a raw id.
    const frede = biblio.find((e) => e.author === 'Frede');
    expect(frede?.bibtex).toContain('@misc{Frede2011');
    expect(frede?.bibtex).toContain('doi = {10.1525/9780520947443}');
    expect(frede?.year).toBe(2011);
    for (const e of biblio) {
      expect(e.full_citation_chicago).not.toMatch(LEAKED_RE);
    }
  });
});
