/**
 * StreamingAnswer — markdown renderer that grows token-by-token.
 *
 * Two reference patterns are recognised:
 *  - `[Source N]`  — legacy free-form synthesizer output (chip + hover card).
 *  - `[^N]`        — new ThesisDraft footnote anchors (numbered, hover card).
 *
 * When a `bibliography` prop is supplied the component renders a primary /
 * secondary bibliography pane underneath the prose, and an export toolbar so
 * the user can download the same draft as Markdown / LaTeX / BibTeX / Zotero
 * / RIS. The component remains presentational: parents wire up the props.
 */

import { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import * as HoverCard from '@radix-ui/react-hover-card';
import { useTranslation } from 'react-i18next';
import { BookOpen, Download } from 'lucide-react';
import { cn } from '../../lib/utils';
import type { CitationEntry } from '../../hooks/useResearchStream';

export interface BibliographyItem {
  kind: 'primary' | 'secondary';
  author: string;
  title: string;
  year?: number;
  publisher?: string;
  edition?: string;
  pages?: string;
  url?: string;
  cts_urn?: string;
  bibtex_key?: string;
}

export interface FootnoteItem {
  n: number;
  text: string;
  /** Optional structured citations for hover preview. */
  citations?: ReadonlyArray<{
    work_label: string;
    author?: string;
    page_or_section?: string;
    quote_greek?: string;
    quote_translation?: string;
    cts_urn?: string;
  }>;
}

export type ExportFormat = 'markdown' | 'latex' | 'bibtex' | 'zotero' | 'ris';

interface Props {
  text: string;
  citations: CitationEntry[];
  /** When true, a soft caret pulses at the end of the rendered text. */
  isLive: boolean;
  className?: string;
  /** Bibliography entries to render below the prose. */
  bibliography?: ReadonlyArray<BibliographyItem>;
  /** Footnote definitions (looked up by `[^N]` anchors). */
  footnotes?: ReadonlyArray<FootnoteItem>;
  /** When supplied, an export toolbar is rendered with download links. */
  traceId?: string;
  /** Override the export URL builder (used in tests). */
  buildExportUrl?: (traceId: string, fmt: ExportFormat) => string;
  /**
   * True while streamed prose is on screen but the citation audit has not
   * completed yet — renders a "preview" banner so unverified claims are
   * never presented as final.
   */
  verificationPending?: boolean;
}

const SOURCE_PATTERN = /\[Source\s+(\d+)\]/g;
const FOOTNOTE_PATTERN = /\[\^(\d+)\]/g;
const COMBINED_PATTERN = new RegExp(
  `${SOURCE_PATTERN.source}|${FOOTNOTE_PATTERN.source}`,
  'g',
);

interface Segment {
  kind: 'text' | 'source' | 'footnote';
  value: string;
  index?: number;
}

function splitSegments(input: string): Segment[] {
  if (!input) return [];
  const segments: Segment[] = [];
  let lastIdx = 0;
  let match: RegExpExecArray | null;
  const re = new RegExp(COMBINED_PATTERN.source, 'g');
  while ((match = re.exec(input)) !== null) {
    if (match.index > lastIdx) {
      segments.push({ kind: 'text', value: input.slice(lastIdx, match.index) });
    }
    const isSource = match[1] !== undefined;
    const raw = isSource ? match[1] : match[2];
    segments.push({
      kind: isSource ? 'source' : 'footnote',
      value: match[0],
      index: Number.parseInt(raw, 10) - (isSource ? 1 : 0),
    });
    lastIdx = match.index + match[0].length;
  }
  if (lastIdx < input.length) {
    segments.push({ kind: 'text', value: input.slice(lastIdx) });
  }
  return segments;
}

const DEFAULT_EXPORT_URL = (traceId: string, fmt: ExportFormat) =>
  `/api/graphrag/query/${encodeURIComponent(traceId)}/export?format=${fmt}&download=true`;

const FORMAT_LABELS: Record<ExportFormat, string> = {
  markdown: 'Markdown',
  latex: 'LaTeX',
  bibtex: 'BibTeX',
  zotero: 'Zotero',
  ris: 'RIS',
};

export function StreamingAnswer({
  text,
  citations,
  isLive,
  className,
  bibliography,
  footnotes,
  traceId,
  buildExportUrl,
  verificationPending,
}: Props) {
  const { t } = useTranslation();
  const segments = useMemo(() => splitSegments(text), [text]);
  const footnoteIndex = useMemo(() => {
    const map = new Map<number, FootnoteItem>();
    (footnotes ?? []).forEach((f) => map.set(f.n, f));
    return map;
  }, [footnotes]);

  if (!text) {
    return (
      <div
        className={cn(
          'rounded-2xl border border-stone-200/70 bg-white/70 p-6 text-center',
          className,
        )}
      >
        <p className="font-display text-[15px] text-stone-600">
          {isLive ? t('research.answer.preparing') : t('research.answer.idle')}
        </p>
        <p className="mt-1 text-[12px] text-stone-400">
          {t('research.answer.idleSubtitle')}
        </p>
      </div>
    );
  }

  const urlFor = buildExportUrl ?? DEFAULT_EXPORT_URL;
  const primary = (bibliography ?? []).filter((b) => b.kind === 'primary');
  const secondary = (bibliography ?? []).filter((b) => b.kind === 'secondary');

  return (
    <article
      aria-live="polite"
      aria-busy={isLive}
      className={cn(
        'prose prose-stone max-w-none rounded-2xl border border-stone-200/70 bg-white/85 p-5',
        'prose-headings:font-display prose-p:leading-7 prose-p:text-stone-700',
        className,
      )}
    >
      {verificationPending && (
        <p
          role="status"
          className="not-prose mb-3 inline-flex items-center gap-1.5 rounded-lg border border-amber-200 bg-amber-50 px-2.5 py-1 text-[11px] font-medium text-amber-800"
        >
          <span
            className="h-1.5 w-1.5 animate-pulse rounded-full bg-amber-500"
            aria-hidden="true"
          />
          {t('research.answer.pendingVerification')}
        </p>
      )}
      {segments.map((seg, i) => {
        if (seg.kind === 'text') {
          return <ReactMarkdown key={i}>{seg.value}</ReactMarkdown>;
        }
        if (seg.kind === 'source') {
          const citation =
            seg.index !== undefined ? citations[seg.index] : undefined;
          return (
            <HoverCard.Root key={i} openDelay={120} closeDelay={80}>
              <HoverCard.Trigger asChild>
                <button
                  type="button"
                  data-citation-id={`c${(seg.index ?? 0) + 1}`}
                  data-passage-anchor={citation?.passage_id}
                  className="mx-0.5 inline-flex items-center gap-0.5 rounded-md bg-amber-50 px-1 py-0 font-mono text-[11px] font-semibold text-amber-800 hover:bg-amber-100"
                  aria-label={`source ${(seg.index ?? 0) + 1}`}
                >
                  <BookOpen className="h-2.5 w-2.5" aria-hidden="true" />
                  {seg.value}
                </button>
              </HoverCard.Trigger>
              <HoverCard.Portal>
                <HoverCard.Content
                  className="z-50 max-w-sm rounded-xl border border-stone-200/70 bg-white px-3 py-2 text-[12px] shadow-lg"
                  side="top"
                  sideOffset={6}
                >
                  {citation ? (
                    <div>
                      <p className="font-medium text-stone-800">
                        {citation.work_label ?? citation.passage_id}
                      </p>
                      {citation.cts_urn && (
                        <p className="mt-0.5 font-mono text-[10px] text-stone-400">
                          {citation.cts_urn}
                        </p>
                      )}
                      <p className="mt-1.5 line-clamp-4 italic leading-5 text-stone-600">
                        {citation.excerpt}
                      </p>
                    </div>
                  ) : (
                    <p className="italic text-stone-500">
                      {t('research.answer.citationMissing')}
                    </p>
                  )}
                  <HoverCard.Arrow className="fill-white" />
                </HoverCard.Content>
              </HoverCard.Portal>
            </HoverCard.Root>
          );
        }
        // Footnote
        const fnNumber = seg.index ?? 0;
        const footnote = footnoteIndex.get(fnNumber);
        return (
          <HoverCard.Root key={i} openDelay={120} closeDelay={80}>
            <HoverCard.Trigger asChild>
              <sup>
                <button
                  type="button"
                  data-testid={`footnote-anchor-${fnNumber}`}
                  aria-label={`footnote ${fnNumber}`}
                  className="ml-0.5 rounded bg-stone-100 px-1 font-mono text-[10px] font-semibold text-stone-700 hover:bg-stone-200"
                >
                  {fnNumber}
                </button>
              </sup>
            </HoverCard.Trigger>
            <HoverCard.Portal>
              <HoverCard.Content
                className="z-50 max-w-md rounded-xl border border-stone-200/70 bg-white px-3 py-2 text-[12px] shadow-lg"
                side="top"
                sideOffset={6}
              >
                {footnote ? (
                  <div>
                    <p className="font-medium text-stone-800">{footnote.text}</p>
                    {footnote.citations?.map((c, idx) => (
                      <div
                        key={idx}
                        className="mt-2 border-t border-stone-100 pt-2 text-stone-600"
                      >
                        <p>
                          <span className="font-semibold">{c.author ?? ''}</span>{' '}
                          <em>{c.work_label}</em>{' '}
                          {c.page_or_section && (
                            <span className="text-stone-500">
                              {c.page_or_section}
                            </span>
                          )}
                        </p>
                        {c.quote_greek && (
                          <p className="mt-0.5 font-serif italic">
                            “{c.quote_greek}”
                          </p>
                        )}
                        {c.quote_translation && (
                          <p className="mt-0.5">“{c.quote_translation}”</p>
                        )}
                        {c.cts_urn && (
                          <p className="mt-0.5 font-mono text-[10px] text-stone-400">
                            {c.cts_urn}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="italic text-stone-500">
                    {t('research.answer.citationMissing')}
                  </p>
                )}
                <HoverCard.Arrow className="fill-white" />
              </HoverCard.Content>
            </HoverCard.Portal>
          </HoverCard.Root>
        );
      })}
      {isLive && (
        <span
          aria-hidden="true"
          className="ml-0.5 inline-block h-3.5 w-0.5 animate-pulse bg-amber-500 align-middle"
        />
      )}

      {(primary.length > 0 || secondary.length > 0) && (
        <section
          aria-label="Bibliography"
          data-testid="bibliography-pane"
          className="not-prose mt-6 border-t border-stone-200/70 pt-4"
        >
          {primary.length > 0 && (
            <div>
              <h3 className="mb-2 font-display text-[13px] uppercase tracking-wide text-stone-600">
                {t('research.answer.primarySources', 'Primary Sources')}
              </h3>
              <ul className="space-y-1 text-[13px] text-stone-700">
                {primary.map((entry, idx) => (
                  <li key={`p-${idx}`} className="leading-6">
                    <BibliographyLine entry={entry} />
                  </li>
                ))}
              </ul>
            </div>
          )}
          {secondary.length > 0 && (
            <div className="mt-4">
              <h3 className="mb-2 font-display text-[13px] uppercase tracking-wide text-stone-600">
                {t('research.answer.secondaryLiterature', 'Secondary Literature')}
              </h3>
              <ul className="space-y-1 text-[13px] text-stone-700">
                {secondary.map((entry, idx) => (
                  <li key={`s-${idx}`} className="leading-6">
                    <BibliographyLine entry={entry} />
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      {traceId && (
        <nav
          aria-label="Export draft"
          data-testid="export-toolbar"
          className="not-prose mt-5 flex flex-wrap items-center gap-2 border-t border-stone-200/70 pt-3 text-[12px]"
        >
          <span className="font-mono uppercase tracking-wide text-stone-500">
            {t('research.answer.download', 'Download')}
          </span>
          {(Object.keys(FORMAT_LABELS) as ExportFormat[]).map((fmt) => (
            <a
              key={fmt}
              href={urlFor(traceId, fmt)}
              data-testid={`export-${fmt}`}
              className="inline-flex items-center gap-1 rounded-md border border-stone-200 px-2 py-1 font-mono text-[11px] uppercase tracking-wide text-stone-600 hover:bg-stone-50"
            >
              <Download className="h-2.5 w-2.5" aria-hidden="true" />
              {FORMAT_LABELS[fmt]}
            </a>
          ))}
        </nav>
      )}
    </article>
  );
}

function BibliographyLine({ entry }: { entry: BibliographyItem }) {
  return (
    <>
      <span className="font-medium">{entry.author}.</span>{' '}
      <em>{entry.title}</em>
      {entry.edition ? `, ed. ${entry.edition}` : ''}
      {entry.publisher ? ` (${entry.publisher}` : ''}
      {entry.year ? `${entry.publisher ? ', ' : ' ('}${entry.year}` : ''}
      {entry.publisher || entry.year ? ')' : ''}
      {entry.pages ? `, pp. ${entry.pages}` : ''}
      {entry.cts_urn && (
        <span className="ml-1 font-mono text-[10px] text-stone-400">
          [{entry.cts_urn}]
        </span>
      )}
      {entry.url && (
        <>
          {' '}
          <a
            href={entry.url}
            target="_blank"
            rel="noreferrer"
            className="text-amber-700 hover:underline"
          >
            link
          </a>
        </>
      )}
    </>
  );
}

export default StreamingAnswer;
