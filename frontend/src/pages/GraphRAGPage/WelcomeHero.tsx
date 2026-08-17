import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { ShineBorder } from '../../components/ui/shine-border';
import { Typewriter } from '../../components/ui/typewriter';
import AdvancedOptions from '../../components/graphrag/AdvancedOptions';
import { ScholarlyWaitExpectation } from './WaitingExperience';

interface WelcomeHeroProps {
  query: string;
  setQuery: (q: string) => void;
  /** Run-independent message (server busy, concurrent-run cap). */
  notice: string | null;
  inputRef: React.RefObject<HTMLInputElement | null>;
  onSubmit: (e: React.FormEvent) => void;
  onDemo: () => void;
  advancedProps: {
    ancientOnly: boolean;
    setAncientOnly: (v: boolean) => void;
  };
}

export default function WelcomeHero({
  query,
  setQuery,
  notice,
  inputRef,
  onSubmit,
  onDemo,
  advancedProps,
}: WelcomeHeroProps) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col items-center justify-center min-h-[85vh] px-4 py-8 sm:py-12 pt-24 sm:pt-28">
      <div className="w-full max-w-2xl">
        <motion.div
          className="text-center mb-8 sm:mb-10"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h1 className="text-3xl sm:text-5xl md:text-6xl font-semibold text-stone-800 mb-3 drop-shadow-sm">
            <Typewriter
              text={['Agentic GraphRAG', 'Knowledge Graph', 'Ancient Philosophy', 'Scholarly Q&A']}
              speed={100}
              waitTime={3500}
              deleteSpeed={60}
              className="text-stone-800"
              cursorChar="_"
            />
          </h1>
          <p className="text-sm sm:text-base text-stone-600 max-w-lg mx-auto">{t('graphrag.description')}</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="space-y-4"
        >
          <form onSubmit={onSubmit}>
            <ShineBorder
              className="!p-0 bg-white/95 backdrop-blur-sm"
              borderRadius={9999}
              color={['#fdba74', '#f97316', '#fbbf24']}
            >
              <div className="flex gap-2 sm:gap-3 p-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={t('graphrag.placeholder')}
                  className="flex-1 min-w-0 px-4 sm:px-6 py-3 text-base bg-transparent focus:outline-none focus:ring-0 border-0"
                  autoFocus
                />
                <button
                  type="submit"
                  disabled={!query.trim()}
                  className="px-4 sm:px-8 py-3 min-h-[44px] bg-gradient-to-br from-orange-600 to-orange-500 text-white rounded-full hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm sm:text-base font-medium whitespace-nowrap"
                >
                  {t('graphrag.ask')}
                </button>
              </div>
            </ShineBorder>
          </form>

          <ScholarlyWaitExpectation />

          <AdvancedOptions {...advancedProps} />

          <div className="flex justify-center">
            <button
              type="button"
              onClick={onDemo}
              className="text-sm text-stone-400 hover:text-stone-600 transition-colors"
            >
              Try Demo
            </button>
          </div>

          {notice && (
            <motion.div
              role="status"
              data-testid="run-notice"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 px-6 py-4 bg-amber-50 border border-amber-200 text-amber-900 rounded-2xl text-sm text-center"
            >
              {notice}
            </motion.div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
