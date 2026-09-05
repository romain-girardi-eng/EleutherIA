import { useTranslation } from 'react-i18next';
import { ArrowRight, BookOpen } from 'lucide-react';
import AdvancedOptions from '../../components/graphrag/AdvancedOptions';
import { ModelSelector, type GraphRagModelOption } from './ChatInput';
import { ScholarlyWaitExpectation } from './WaitingExperience';

interface WelcomeHeroProps {
  query: string;
  setQuery: (q: string) => void;
  notice: string | null;
  inputRef: React.RefObject<HTMLTextAreaElement | null>;
  onSubmit: (e: React.FormEvent) => void;
  onDemo: () => void;
  selectedModel: string;
  modelOptions: GraphRagModelOption[];
  onModelChange: (model: string) => void;
  advancedProps: { ancientOnly: boolean; setAncientOnly: (v: boolean) => void };
}

export default function WelcomeHero({
  query, setQuery, notice, inputRef, onSubmit, onDemo,
  selectedModel, modelOptions, onModelChange, advancedProps,
}: WelcomeHeroProps) {
  const { t } = useTranslation();
  return (
    <div className="mx-auto flex min-h-[85vh] w-full max-w-5xl flex-col justify-center px-5 pb-16 pt-28 sm:px-10 font-body">
      <div className="max-w-3xl">
        <p className="mb-5 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-orange-800">
          <BookOpen className="h-4 w-4" aria-hidden="true" />
          {t('graphRagUi.welcome.eyebrow')}
        </p>
        <h1 className="max-w-2xl font-display text-5xl leading-[1.06] text-stone-900 sm:text-7xl">
          {t('graphRagUi.welcome.title')}
        </h1>
        <p className="mt-5 max-w-xl text-base leading-7 text-stone-700 sm:text-lg">
          {t('graphRagUi.welcome.description')}
        </p>
      </div>

      <form onSubmit={onSubmit} className="mt-10 max-w-3xl">
        <label htmlFor="scholarly-question" className="mb-2 block text-sm font-semibold text-stone-800">
          {t('graphRagUi.welcome.question')}
        </label>
        <div className="flex flex-col gap-2 rounded-xl border border-stone-300 bg-parchment-50 p-2 focus-within:border-orange-700 focus-within:ring-2 focus-within:ring-orange-700/15 sm:flex-row">
          <textarea
            id="scholarly-question"
            ref={inputRef}
            rows={3}
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder={t('graphrag.placeholder')}
            aria-describedby="scholarly-question-hint"
            className="min-h-12 min-w-0 flex-1 resize-y border-0 py-3 bg-transparent px-3 text-base text-stone-900 placeholder:text-stone-500 focus:outline-none focus:ring-0"
          />
          <button type="submit" disabled={!query.trim()}
            className="inline-flex min-h-12 items-center justify-center gap-3 rounded-lg bg-orange-800 px-6 text-sm font-semibold text-orange-50 transition-colors hover:bg-orange-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-orange-800 disabled:cursor-not-allowed disabled:opacity-50">
            {t('graphRagUi.welcome.submit')} <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
        <p id="scholarly-question-hint" className="mt-3 text-sm leading-6 text-stone-600">{t('graphRagUi.welcome.hint')}</p>
      </form>

      <div className="mt-6 max-w-3xl">
        <p className="text-xs font-semibold uppercase tracking-wider text-stone-600">{t('graphRagUi.welcome.examples')}</p>
        <div className="mt-2 divide-y divide-stone-300/60">
          {['compare', 'passage', 'debate'].map(key => (
            <button key={key} type="button" onClick={() => { setQuery(t(`graphRagUi.welcome.${key}`)); inputRef.current?.focus(); }}
              className="group flex min-h-12 w-full items-center justify-between gap-5 py-3 text-left text-sm leading-6 text-stone-700 transition-colors hover:text-orange-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-orange-700">
              {t(`graphRagUi.welcome.${key}`)}
              <ArrowRight className="h-4 w-4 shrink-0 text-orange-800" aria-hidden="true" />
            </button>
          ))}
        </div>
        <details className="mt-5 border-t border-stone-300/70 pt-3">
          <summary className="min-h-11 cursor-pointer py-2 text-sm font-medium text-stone-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-orange-700">{t('graphRagUi.welcome.settings')}</summary>
          <div className="space-y-3 py-3">
            <ModelSelector selectedModel={selectedModel} modelOptions={modelOptions} onModelChange={onModelChange} />
            <AdvancedOptions {...advancedProps} />
          </div>
        </details>
        <ScholarlyWaitExpectation className="mt-3 !justify-start !px-0 !text-left !text-xs !text-stone-600" />
        <button type="button" onClick={onDemo} className="mt-4 min-h-11 text-sm text-orange-800 underline decoration-orange-800/40 underline-offset-4 hover:decoration-orange-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-orange-700">
          {t('graphRagUi.welcome.demo')}
        </button>
        {notice && <p role="status" data-testid="run-notice" className="mt-4 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">{notice}</p>}
      </div>
    </div>
  );
}
