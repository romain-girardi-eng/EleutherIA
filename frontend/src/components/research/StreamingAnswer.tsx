/**
 * StreamingAnswer — markdown renderer that grows token-by-token.
 *
 * Inline `[Source N]` references become hoverable chips that surface the
 * matching citation excerpt. The component itself is presentational: it
 * accepts the live token stream and the resolved citation array.
 */

import { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import * as HoverCard from '@radix-ui/react-hover-card';
import { useTranslation } from 'react-i18next';
import { BookOpen } from 'lucide-react';
import { cn } from '../../lib/utils';
import type { CitationEntry } from '../../hooks/useResearchStream';

interface Props {
  text: string;
  citations: CitationEntry[];
  /** When true, a soft caret pulses at the end of the rendered text. */
  isLive: boolean;
  className?: string;
}

const SOURCE_PATTERN = /\[Source\s+(\d+)\]/g;

interface Segment {
  kind: 'text' | 'source';
  value: string;
  index?: number;
}

function splitSegments(input: string): Segment[] {
  if (!input) return [];
  const segments: Segment[] = [];
  let lastIdx = 0;
  let match: RegExpExecArray | null;
  // Reset the regex's lastIndex by using a fresh copy of the source pattern.
  const re = new RegExp(SOURCE_PATTERN.source, 'g');
  while ((match = re.exec(input)) !== null) {
    if (match.index > lastIdx) {
      segments.push({ kind: 'text', value: input.slice(lastIdx, match.index) });
    }
    segments.push({
      kind: 'source',
      value: match[0],
      index: Number.parseInt(match[1], 10) - 1,
    });
    lastIdx = match.index + match[0].length;
  }
  if (lastIdx < input.length) {
    segments.push({ kind: 'text', value: input.slice(lastIdx) });
  }
  return segments;
}

export function StreamingAnswer({ text, citations, isLive, className }: Props) {
  const { t } = useTranslation();
  const segments = useMemo(() => splitSegments(text), [text]);

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
      {segments.map((seg, i) => {
        if (seg.kind === 'text') {
          return <ReactMarkdown key={i}>{seg.value}</ReactMarkdown>;
        }
        const citation = seg.index !== undefined ? citations[seg.index] : undefined;
        return (
          <HoverCard.Root key={i} openDelay={120} closeDelay={80}>
            <HoverCard.Trigger asChild>
              <button
                type="button"
                className="mx-0.5 inline-flex items-center gap-0.5 rounded-md bg-amber-50 px-1 py-0 font-mono text-[11px] font-semibold text-amber-800 hover:bg-amber-100"
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
      })}
      {isLive && (
        <span
          aria-hidden="true"
          className="ml-0.5 inline-block h-3.5 w-0.5 animate-pulse bg-amber-500 align-middle"
        />
      )}
    </article>
  );
}

export default StreamingAnswer;
