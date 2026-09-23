import { ChevronDown } from 'lucide-react';
import { useId, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ATLAS_THEME } from './atlasTheme';
import { edgeWidth } from './AtlasHelpers';

interface LegendProps {
  /** Legacy label bag; the legend now resolves its own strings. */
  labels?: Partial<Record<string, string>>;
}

const STORAGE_KEY = 'eleutheria.atlas.legend.layoutOpen';

function readStored(): boolean {
  try {
    return window.localStorage.getItem(STORAGE_KEY) !== '0';
  } catch {
    return true;
  }
}

function writeStored(open: boolean) {
  try {
    window.localStorage.setItem(STORAGE_KEY, open ? '1' : '0');
  } catch {
    // Storage can be unavailable (private mode); the toggle still works.
  }
}

const NODES = ATLAS_THEME.nodes;

/** Passage dots packed in a disc, in reading order from the centre out. */
function discDots(count: number, radius: number): ReadonlyArray<readonly [number, number]> {
  const golden = Math.PI * (3 - Math.sqrt(5));
  return Array.from({ length: count }, (_, i) => {
    const r = radius * Math.sqrt((i + 1.4) / (count + 1.4));
    return [Math.cos(i * golden) * r, Math.sin(i * golden) * r] as const;
  });
}

function WorkDiscGlyph() {
  return (
    <svg viewBox="-20 -20 40 40" className="h-10 w-10 shrink-0" aria-hidden>
      {discDots(26, 16).map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r={1.7} fill={NODES.passage} opacity={0.75} />
      ))}
      <circle r={4.2} fill={NODES.work} stroke="#fffdf9" strokeWidth={1.2} />
      <circle r={2.2} cx={0} cy={0} fill={NODES.person} />
    </svg>
  );
}

function OrbitGlyph() {
  const orbit = Array.from({ length: 7 }, (_, i) => {
    const a = (i / 7) * Math.PI * 2 - Math.PI / 2;
    return [Math.cos(a) * 13, Math.sin(a) * 13] as const;
  });
  return (
    <svg viewBox="-20 -20 40 40" className="h-10 w-10 shrink-0" aria-hidden>
      <circle r={13} fill="none" stroke={ATLAS_THEME.mutedInk} strokeOpacity={0.25} strokeDasharray="1.5 2.5" />
      {orbit.map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r={2.4} fill={NODES.argument} />
      ))}
      <circle r={4.6} fill={NODES.fallback} stroke="#fffdf9" strokeWidth={1.2} />
    </svg>
  );
}

function SizeGlyph() {
  return (
    <svg viewBox="0 0 40 20" className="h-5 w-10 shrink-0" aria-hidden>
      <circle cx={4} cy={14} r={1.8} fill={ATLAS_THEME.mutedInk} opacity={0.35} />
      <circle cx={13} cy={12} r={3.6} fill={ATLAS_THEME.mutedInk} opacity={0.7} />
      <circle cx={29} cy={10} r={8} fill={ATLAS_THEME.mutedInk} />
    </svg>
  );
}

export default function Legend(_props: LegendProps) {
  const { t } = useTranslation();
  const [layoutOpen, setLayoutOpen] = useState(readStored);
  const layoutId = useId();

  const colours: ReadonlyArray<{ key: string; color: string; label: string }> = [
    { key: 'person', color: NODES.person, label: t('cosmograph.legend.kinds.person', 'Ancient figures') },
    { key: 'scholar', color: NODES.scholar, label: t('cosmograph.legend.kinds.scholar', 'Scholars') },
    { key: 'work', color: NODES.work, label: t('cosmograph.legend.kinds.work', 'Works') },
    { key: 'passage', color: NODES.passage, label: t('cosmograph.legend.kinds.passage', 'Passages') },
    { key: 'concept', color: NODES.concept, label: t('cosmograph.legend.kinds.concept', 'Concepts') },
    { key: 'argument', color: NODES.argument, label: t('cosmograph.legend.kinds.argument', 'Arguments') },
    { key: 'school', color: NODES.school, label: t('cosmograph.legend.kinds.school', 'Schools') },
    { key: 'debate', color: NODES.debate, label: t('cosmograph.legend.kinds.debate', 'Debates') },
    { key: 'other', color: NODES.fallback, label: t('cosmograph.legend.kinds.other', 'Publications & other') },
  ];

  const links: ReadonlyArray<{ key: string; width: number; opacity: number; label: string }> = [
    { key: 'structural', width: edgeWidth('authored_by'), opacity: 0.8, label: t('cosmograph.legend.structural', 'Authorship, membership, part of') },
    { key: 'doctrinal', width: edgeWidth('interprets'), opacity: 0.6, label: t('cosmograph.legend.doctrinal', 'Interprets, critiques, discusses') },
    { key: 'citation', width: edgeWidth('cites'), opacity: 0.45, label: t('cosmograph.legend.citation', 'Cites, translates, evidences') },
  ];

  return (
    <aside
      aria-label={t('cosmograph.legend.title', 'Legend')}
      className="pointer-events-auto w-[18rem] max-w-[calc(100vw-2rem)] rounded-2xl border border-stone-300 bg-[#fffdf9]/95 p-3.5 font-body text-[12px] leading-snug text-stone-700 shadow-[0_20px_50px_rgba(72,52,36,0.14)] backdrop-blur-xl"
    >
      <h2 className="font-display text-[15px] leading-none text-stone-950">
        {t('cosmograph.legend.title', 'Legend')}
      </h2>

      <ul className="mt-3 grid grid-cols-2 gap-x-3 gap-y-1.5" aria-label={t('cosmograph.legend.types', 'Colour = kind of node')}>
        {colours.map((entry) => (
          <li key={entry.key} className={['flex min-w-0 items-center gap-2', entry.key === 'other' ? 'col-span-2' : ''].join(' ')}>
            <span aria-hidden className="h-2.5 w-2.5 shrink-0 rounded-full ring-1 ring-stone-900/10" style={{ backgroundColor: entry.color }} />
            <span className="truncate" title={entry.label}>{entry.label}</span>
          </li>
        ))}
      </ul>

      <div className="mt-3 flex items-center gap-2.5 border-t border-stone-200 pt-3">
        <SizeGlyph />
        <p>{t('cosmograph.legend.size', 'Size = number of connections. Minor loci stay faint until you zoom in.')}</p>
      </div>

      <button
        type="button"
        aria-expanded={layoutOpen}
        aria-controls={layoutId}
        onClick={() => {
          setLayoutOpen((open) => {
            writeStored(!open);
            return !open;
          });
        }}
        className="mt-3 flex min-h-8 w-full items-center justify-between border-t border-stone-200 pt-2.5 text-left font-semibold text-stone-900 hover:text-orange-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-700"
      >
        {t('cosmograph.legend.layout', 'Reading the layout')}
        <ChevronDown
          aria-hidden
          className={['h-4 w-4 text-stone-500 transition-transform motion-reduce:transition-none', layoutOpen ? 'rotate-180' : ''].join(' ')}
        />
      </button>

      {layoutOpen && (
        <div id={layoutId} className="mt-2 space-y-2.5">
          <div className="flex items-center gap-2.5">
            <WorkDiscGlyph />
            <p>{t('cosmograph.legend.workDisc', 'Each work is a disc of its passages in canonical order; its author sits at the centre of their main work.')}</p>
          </div>
          <div className="flex items-center gap-2.5">
            <OrbitGlyph />
            <p>{t('cosmograph.legend.orbit', 'Arguments gather around the publication that advances them.')}</p>
          </div>
          <ul className="space-y-1.5 pt-1" aria-label={t('cosmograph.legend.relations', 'Link weight')}>
            {links.map((link) => (
              <li key={link.key} className="flex items-center gap-2.5">
                <svg viewBox="0 0 40 6" className="h-1.5 w-10 shrink-0" aria-hidden>
                  <line x1={1} y1={3} x2={39} y2={3} stroke={ATLAS_THEME.mutedInk} strokeOpacity={link.opacity} strokeWidth={link.width} strokeLinecap="round" />
                </svg>
                <span>{link.label}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </aside>
  );
}
