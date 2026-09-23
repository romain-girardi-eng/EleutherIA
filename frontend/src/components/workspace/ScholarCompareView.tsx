import { ArrowRight, Columns3, X } from 'lucide-react';
import { memo, useMemo, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';

import { useGraphWorkspace } from '../../context/GraphWorkspaceContext';
import type { AtlasNodeMeta } from '../cosmograph/AtlasHelpers';
import { directLinks, sharedNeighbours, type Adjacency } from './scholarModel';
import { useScholarLabels } from './useScholarLabels';

const focusRing = 'outline-none focus-visible:ring-2 focus-visible:ring-orange-700';

interface ScholarCompareViewProps {
  metaById: ReadonlyMap<string, AtlasNodeMeta>;
  adjacency: Adjacency;
  onShowIndex: () => void;
}

function ScholarCompareViewComponent({ metaById, adjacency, onShowIndex }: ScholarCompareViewProps) {
  const { t } = useTranslation();
  const labels = useScholarLabels();
  const { state, data, selectPrimary, toggleCompare } = useGraphWorkspace();
  const ids = state.compareIds;

  const shared = useMemo(() => {
    const entries = sharedNeighbours(adjacency, ids, 60);
    return entries
      .sort(
        (a, b) =>
          b.memberIds.length - a.memberIds.length ||
          (metaById.get(b.id)?.degree ?? 0) - (metaById.get(a.id)?.degree ?? 0),
      )
      .slice(0, 24);
  }, [adjacency, ids, metaById]);
  const links = useMemo(() => directLinks(adjacency, ids), [adjacency, ids]);

  if (ids.length < 2) {
    return (
      <div className="mx-auto max-w-xl px-4 py-16 text-center">
        <Columns3 className="mx-auto h-8 w-8 text-teal-700" aria-hidden="true" />
        <h2 className="mt-4 font-display text-3xl text-stone-950">{t('scholar.compare.emptyTitle')}</h2>
        <p className="mt-3 font-reader text-lg leading-7 text-stone-600">{t('scholar.compare.emptyBody')}</p>
        <button
          type="button"
          onClick={onShowIndex}
          className={`mt-6 inline-flex min-h-11 items-center border border-stone-900 px-5 font-body text-sm font-semibold text-stone-900 hover:bg-stone-900 hover:text-[#fffdf9] ${focusRing}`}
        >
          {t('scholar.compare.backToIndex')}
        </button>
      </div>
    );
  }

  const nodes = ids.map((id) => ({ id, meta: metaById.get(id), raw: data.rawById.get(id) }));
  const labelOf = (id: string) => metaById.get(id)?.label ?? data.rawById.get(id)?.label ?? id;
  const numberOf = (id: string) => ids.indexOf(id) + 1;

  const attributeRows: Array<{ key: string; label: string; render: (entry: (typeof nodes)[number]) => ReactNode }> = [
    { key: 'type', label: t('scholar.table.type'), render: ({ meta, raw }) => (meta ? labels.nodeType(meta) : raw?.type ?? '—') },
    { key: 'period', label: t('scholar.table.period'), render: ({ meta }) => (meta ? labels.period(meta.periodLabel) : '—') },
    { key: 'dates', label: t('scholar.inspector.dates'), render: ({ raw }) => raw?.dates || '—' },
    { key: 'school', label: t('scholar.table.school'), render: ({ meta }) => (meta ? labels.school(meta.schoolLabel) : '—') },
    { key: 'links', label: t('scholar.table.links'), render: ({ meta }) => (meta ? labels.number(meta.degree) : '—') },
    {
      key: 'terms',
      label: t('scholar.compare.terms'),
      render: ({ raw }) => {
        const terms = [raw?.greek_term, raw?.latin_term].filter(Boolean).join(' · ');
        return terms ? <span className="font-reader text-base">{terms}</span> : '—';
      },
    },
    {
      key: 'description',
      label: t('scholar.compare.description'),
      render: ({ raw }) => (
        <span className="line-clamp-[8] font-reader text-[15px] leading-6 text-stone-700">
          {raw?.description || t('scholar.inspector.noDescription')}
        </span>
      ),
    },
    {
      key: 'position',
      label: t('scholar.inspector.position'),
      render: ({ raw }) => (raw?.position_on_free_will
        ? <span className="line-clamp-6 font-reader text-[15px] leading-6 text-stone-700">{raw.position_on_free_will}</span>
        : '—'),
    },
  ];

  return (
    <div className="space-y-8 p-3 sm:p-5">
      <div className="overflow-x-auto border border-stone-300">
        <table className="w-full min-w-[40rem] table-fixed border-collapse text-left font-body text-sm">
          <caption className="sr-only">{t('scholar.compare.caption')}</caption>
          <thead className="bg-[#f1ebe1]">
            <tr>
              <td className="sticky left-0 w-32 border-b border-r border-stone-300 bg-[#f1ebe1]" />
              {nodes.map(({ id }, index) => (
                <th key={id} scope="col" className="min-w-[12rem] border-b border-stone-300 px-3 py-2 align-top">
                  <div className="flex items-start gap-2">
                    <span aria-hidden="true" className="font-display text-2xl leading-none text-teal-700">{index + 1}</span>
                    <button
                      type="button"
                      onClick={() => selectPrimary(id)}
                      className={`min-h-11 flex-1 text-left font-display text-xl font-normal leading-tight text-stone-950 hover:text-orange-800 ${focusRing}`}
                    >
                      {labelOf(id)}
                    </button>
                    <button
                      type="button"
                      onClick={() => toggleCompare(id)}
                      aria-label={t('scholar.table.removeCompare', { label: labelOf(id) })}
                      className={`flex h-11 w-11 shrink-0 items-center justify-center text-stone-500 hover:text-orange-800 ${focusRing}`}
                    >
                      <X className="h-4 w-4" aria-hidden="true" />
                    </button>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {attributeRows.map((row) => (
              <tr key={row.key} className="bg-[#fffdf9] even:bg-[#fbf8f2]">
                <th scope="row" className="sticky left-0 border-b border-r border-stone-200 bg-inherit px-3 py-2.5 align-top text-[10px] font-semibold uppercase tracking-[0.16em] text-stone-500">
                  {row.label}
                </th>
                {nodes.map((entry) => (
                  <td key={entry.id} className="border-b border-stone-200 px-3 py-2.5 align-top text-stone-800">
                    {row.render(entry)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid gap-8 lg:grid-cols-2">
        <section aria-labelledby="scholar-direct-links">
          <h3 id="scholar-direct-links" className="font-body text-[10px] font-semibold uppercase tracking-[0.2em] text-stone-500">
            {t('scholar.compare.directLinks', { count: links.length })}
          </h3>
          {links.length > 0 ? (
            <ul className="mt-2 divide-y divide-stone-200 border-y border-stone-200">
              {links.map((link, index) => (
                <li key={`${link.from}-${link.relation}-${link.to}-${index}`} className="flex flex-wrap items-center gap-x-2 py-2 font-body text-sm">
                  <span className="font-semibold text-stone-900">{numberOf(link.from)}. {labelOf(link.from)}</span>
                  <span className="inline-flex items-center gap-1 text-[11px] uppercase tracking-[0.08em] text-teal-800">
                    {labels.relation(link.relation)} <ArrowRight className="h-3 w-3" aria-hidden="true" />
                  </span>
                  <span className="font-semibold text-stone-900">{numberOf(link.to)}. {labelOf(link.to)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 font-reader text-base text-stone-600">{t('scholar.compare.noDirectLinks')}</p>
          )}
        </section>

        <section aria-labelledby="scholar-shared">
          <h3 id="scholar-shared" className="font-body text-[10px] font-semibold uppercase tracking-[0.2em] text-stone-500">
            {t('scholar.compare.shared', { count: shared.length })}
          </h3>
          {shared.length > 0 ? (
            <ul className="mt-2 divide-y divide-stone-200 border-y border-stone-200">
              {shared.map((entry) => (
                <li key={entry.id}>
                  <button
                    type="button"
                    onClick={() => selectPrimary(entry.id)}
                    className={`flex min-h-11 w-full items-center justify-between gap-3 py-1.5 text-left font-body text-sm hover:bg-[#f7f2e9] ${focusRing}`}
                  >
                    <span className="min-w-0 truncate text-stone-800">{labelOf(entry.id)}</span>
                    <span className="flex shrink-0 gap-1" aria-label={t('scholar.compare.sharedBy', { list: entry.memberIds.map(numberOf).join(', ') })}>
                      {ids.map((id) => (
                        <span
                          key={id}
                          aria-hidden="true"
                          className={`flex h-5 w-5 items-center justify-center text-[10px] font-bold ${entry.memberIds.includes(id) ? 'bg-teal-700 text-[#fffdf9]' : 'border border-stone-300 text-stone-300'}`}
                        >
                          {numberOf(id)}
                        </span>
                      ))}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 font-reader text-base text-stone-600">{t('scholar.compare.noShared')}</p>
          )}
        </section>
      </div>
    </div>
  );
}

export default memo(ScholarCompareViewComponent);
