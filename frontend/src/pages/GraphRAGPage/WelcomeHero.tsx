import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { ShineBorder } from '../../components/ui/shine-border';
import { Typewriter } from '../../components/ui/typewriter';
import AdvancedOptions from '../../components/graphrag/AdvancedOptions';

interface WelcomeHeroProps {
  query: string;
  setQuery: (q: string) => void;
  loading: boolean;
  streaming: boolean;
  error: string | null;
  inputRef: React.RefObject<HTMLInputElement | null>;
  onSubmit: (e: React.FormEvent) => void;
  onDemo: () => void;
  advancedProps: {
    academicMode: boolean;
    setAcademicMode: (v: boolean) => void;
    useThinking: boolean;
    setUseThinking: (v: boolean) => void;
    ancientOnly: boolean;
    setAncientOnly: (v: boolean) => void;
    agenticMode: boolean;
    setAgenticMode: (v: boolean) => void;
    semanticK: number;
    setSemanticK: (v: number) => void;
    graphDepth: number;
    setGraphDepth: (v: number) => void;
    maxContext: number;
    setMaxContext: (v: number) => void;
  };
}

export default function WelcomeHero({
  query,
  setQuery,
  loading,
  streaming,
  error,
  inputRef,
  onSubmit,
  onDemo,
  advancedProps,
}: WelcomeHeroProps) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col items-center justify-center min-h-[85vh] px-4 py-12">
      <div className="w-full max-w-2xl">
        <motion.div
          className="text-center mb-10"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h1 className="text-5xl md:text-6xl font-semibold text-gray-900 mb-3 drop-shadow-sm">
            <Typewriter
              text={['HiRAG', 'Knowledge Graph', 'Ancient Philosophy', 'Scholarly Q&A']}
              speed={100}
              waitTime={3500}
              deleteSpeed={60}
              className="text-gray-900"
              cursorChar="_"
            />
          </h1>
          <p className="text-base text-gray-600 max-w-lg mx-auto">{t('graphrag.description')}</p>
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
              color={['#3B82F6', '#6366F1', '#06B6D4']}
            >
              <div className="flex gap-3 p-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={t('graphrag.placeholder')}
                  className="flex-1 px-6 py-3 text-base bg-transparent focus:outline-none focus:ring-0 border-0"
                  autoFocus
                  disabled={loading || streaming}
                />
                <button
                  type="submit"
                  disabled={!query.trim() || loading || streaming}
                  className="px-8 py-3 bg-gradient-to-br from-gray-900 to-gray-800 text-white rounded-full hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all text-base font-medium whitespace-nowrap"
                >
                  {loading ? 'Thinking...' : t('graphrag.ask')}
                </button>
              </div>
            </ShineBorder>
          </form>

          <AdvancedOptions {...advancedProps} />

          <div className="flex justify-center">
            <button
              type="button"
              onClick={onDemo}
              className="text-sm text-gray-400 hover:text-gray-700 transition-colors"
            >
              Try Demo
            </button>
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 px-6 py-4 bg-red-50 border border-red-200 text-red-800 rounded-2xl text-sm text-center"
            >
              {error}
            </motion.div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
