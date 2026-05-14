/**
 * StreamingAnswer — tests for the thesis-grade footnote / bibliography /
 * export-toolbar behaviour. The existing `[Source N]` chip rendering is
 * covered by `research.test.tsx`.
 */

import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { I18nextProvider } from 'react-i18next';
import i18n from '../../i18n/config';
import {
  StreamingAnswer,
  type BibliographyItem,
  type FootnoteItem,
} from './StreamingAnswer';
import type { CitationEntry } from '../../hooks/useResearchStream';

const renderWithI18n = (ui: React.ReactElement) =>
  render(<I18nextProvider i18n={i18n}>{ui}</I18nextProvider>);

const citations: CitationEntry[] = [];

const footnote: FootnoteItem = {
  n: 1,
  text: 'Classical formulation of the voluntary.',
  citations: [
    {
      author: 'Aristotle',
      work_label: 'Nicomachean Ethics',
      page_or_section: '1110a4-6',
      quote_greek: 'δοκεῖ δὴ ἑκούσιον εἶναι',
      quote_translation: 'An act seems voluntary',
      cts_urn: 'urn:cts:greekLit:tlg0086.tlg010:1110a4',
    },
  ],
};

const bibliography: BibliographyItem[] = [
  {
    kind: 'primary',
    author: 'Aristotle',
    title: 'Nicomachean Ethics',
    year: 1894,
    edition: 'Ingram Bywater',
    publisher: 'Clarendon Press',
    cts_urn: 'urn:cts:greekLit:tlg0086.tlg010',
  },
  {
    kind: 'secondary',
    author: 'Susanne Bobzien',
    title: 'Determinism and Freedom in Stoic Philosophy',
    year: 1998,
    publisher: 'Oxford University Press',
  },
];

describe('StreamingAnswer (thesis output)', () => {
  it('renders [^n] footnote anchors as superscript buttons', () => {
    renderWithI18n(
      <StreamingAnswer
        text="Aristotle grounds the voluntary in the agent.[^1]"
        citations={citations}
        footnotes={[footnote]}
        isLive={false}
      />,
    );
    const anchor = screen.getByTestId('footnote-anchor-1');
    expect(anchor).toBeInTheDocument();
    expect(anchor).toHaveAttribute('aria-label', 'footnote 1');
  });

  it('renders the bibliography pane with primary / secondary sections', () => {
    renderWithI18n(
      <StreamingAnswer
        text="Body text."
        citations={citations}
        bibliography={bibliography}
        isLive={false}
      />,
    );
    const pane = screen.getByTestId('bibliography-pane');
    expect(pane).toBeInTheDocument();
    expect(pane.textContent).toContain('Primary Sources');
    expect(pane.textContent).toContain('Secondary Literature');
    expect(pane.textContent).toContain('Aristotle');
    expect(pane.textContent).toContain('Bobzien');
  });

  it('renders the export toolbar when traceId is supplied', () => {
    renderWithI18n(
      <StreamingAnswer
        text="Body text."
        citations={citations}
        traceId="abc-123"
        isLive={false}
      />,
    );
    const toolbar = screen.getByTestId('export-toolbar');
    expect(toolbar).toBeInTheDocument();
    const markdown = screen.getByTestId('export-markdown');
    expect(markdown).toHaveAttribute(
      'href',
      '/api/graphrag/query/abc-123/export?format=markdown&download=true',
    );
    expect(screen.getByTestId('export-latex')).toBeInTheDocument();
    expect(screen.getByTestId('export-bibtex')).toBeInTheDocument();
    expect(screen.getByTestId('export-zotero')).toBeInTheDocument();
    expect(screen.getByTestId('export-ris')).toBeInTheDocument();
  });

  it('omits the export toolbar when traceId is missing', () => {
    renderWithI18n(
      <StreamingAnswer text="Body text." citations={citations} isLive={false} />,
    );
    expect(screen.queryByTestId('export-toolbar')).toBeNull();
  });
});
