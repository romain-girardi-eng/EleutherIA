import { TYPE_PALETTE } from './AtlasHelpers';

interface LegendProps {
  labels: {
    title: string;
    types: string;
    period: string;
    relations: string;
    presocratic: string;
    lateAntiquity: string;
    modern: string;
    structural: string;
    doctrinal: string;
    citation: string;
  };
}

export default function Legend({ labels }: LegendProps) {
  return (
    <aside
      aria-label={labels.title}
      className="pointer-events-auto w-[15.5rem] rounded-2xl border border-stone-300 bg-[#fffdf9]/92 p-3 text-[11px] text-stone-600 shadow-[0_20px_50px_rgba(72,52,36,0.14)] backdrop-blur-xl"
    >
      <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-stone-500">
        {labels.title}
      </p>

      <section className="mb-3">
        <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-500">
          {labels.types}
        </p>
        <ul className="grid grid-cols-2 gap-x-2 gap-y-1">
          {TYPE_PALETTE.map((entry) => (
            <li key={entry.key} className="flex items-center gap-1.5">
              <span
                aria-hidden
                className="h-2 w-2 rounded-full"
                style={{ backgroundColor: entry.color }}
              />
              <span className="truncate">{entry.label}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="mb-3">
        <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-500">
          {labels.period}
        </p>
        <div className="flex items-center gap-2">
          <span
            aria-hidden
            className="h-2 w-12 rounded-full bg-teal-700"
            style={{ opacity: 0.55 }}
          />
          <span
            aria-hidden
            className="h-2 w-12 rounded-full bg-teal-700"
            style={{ opacity: 0.85 }}
          />
          <span
            aria-hidden
            className="h-2 w-12 rounded-full bg-stone-600"
            style={{ opacity: 0.75 }}
          />
        </div>
        <div className="mt-1 flex items-center justify-between text-[10px] text-stone-500">
          <span>{labels.presocratic}</span>
          <span>{labels.lateAntiquity}</span>
          <span>{labels.modern}</span>
        </div>
      </section>

      <section>
        <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-500">
          {labels.relations}
        </p>
        <ul className="space-y-1">
          <li className="flex items-center gap-2">
            <span aria-hidden className="block h-[2.4px] w-10 rounded-full bg-stone-600/80" />
            <span>{labels.structural}</span>
          </li>
          <li className="flex items-center gap-2">
            <span aria-hidden className="block h-[1.4px] w-10 rounded-full bg-stone-600/55" />
            <span>{labels.doctrinal}</span>
          </li>
          <li className="flex items-center gap-2">
            <span aria-hidden className="block h-[0.8px] w-10 rounded-full bg-stone-600/35" />
            <span>{labels.citation}</span>
          </li>
        </ul>
      </section>
    </aside>
  );
}
