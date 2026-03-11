import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Search, Lightbulb } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { tArray } from '../i18n/utils';

interface SearchGuideModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const SearchGuideModal: React.FC<SearchGuideModalProps> = ({ isOpen, onClose }) => {
  const { t } = useTranslation();
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  const mode = {
    name: t('searchGuide.modeName'),
    model: t('searchGuide.model'),
    method: t('searchGuide.method'),
    granularity: t('searchGuide.granularity'),
    bestFor: tArray(t, 'searchGuide.bestForItems'),
    examples: tArray<{ query: string; explanation: string; why: string }>(t, 'searchGuide.examples'),
  };
  const tips = tArray(t, 'searchGuide.tips');

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 bg-stone-900/30 backdrop-blur-[2px]"
            onClick={onClose}
          />

          {/* Modal */}
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
            <motion.div
              ref={modalRef}
              initial={{ opacity: 0, y: 12, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 8, scale: 0.98 }}
              transition={{ type: 'spring', stiffness: 400, damping: 30 }}
              role="dialog"
              aria-modal="true"
              aria-label={t('searchGuide.title')}
              className="pointer-events-auto w-full max-w-2xl max-h-[85vh] flex flex-col overflow-hidden rounded-2xl border border-amber-200/60 bg-parchment-50 shadow-xl shadow-stone-900/10"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="flex items-start justify-between px-6 pt-6 pb-4">
                <div className="space-y-1">
                  <h2 className="font-display text-2xl font-semibold text-stone-800">
                    {t('searchGuide.title')}
                  </h2>
                  <p className="text-sm text-stone-500">
                    {t('searchGuide.description')}
                  </p>
                </div>
                <button
                  onClick={onClose}
                  className="-mr-1 -mt-1 rounded-full p-2 text-stone-400 transition-colors hover:bg-stone-200/50 hover:text-stone-600"
                  aria-label="Close"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="h-px bg-amber-200/50" />

              {/* Content */}
              <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6">

                {/* Mode pill + technical details */}
                <div className="flex flex-wrap items-center gap-2 text-xs text-stone-500">
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-200/60 bg-white/60 px-3 py-1.5 font-medium text-stone-700">
                    <Search className="h-3.5 w-3.5 text-orange-600/70" />
                    {mode.name}
                  </span>
                  <span className="hidden sm:inline">&middot;</span>
                  <span className="hidden sm:inline">{mode.model}</span>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-xl border border-amber-200/40 bg-white/50 px-4 py-3">
                    <p className="text-[10px] font-medium uppercase tracking-widest text-stone-400">
                      {t('searchGuide.methodLabel')}
                    </p>
                    <p className="mt-0.5 text-sm text-stone-700">{mode.method}</p>
                  </div>
                  <div className="rounded-xl border border-amber-200/40 bg-white/50 px-4 py-3">
                    <p className="text-[10px] font-medium uppercase tracking-widest text-stone-400">
                      {t('searchGuide.granularityLabel')}
                    </p>
                    <p className="mt-0.5 text-sm text-stone-700">{mode.granularity}</p>
                  </div>
                </div>

                {/* Best For */}
                <div>
                  <h3 className="mb-2.5 text-xs font-semibold uppercase tracking-widest text-orange-700/70">
                    {t('searchGuide.bestFor')}
                  </h3>
                  <div className="grid gap-1.5 sm:grid-cols-2">
                    {mode.bestFor.map((item, i) => (
                      <p key={i} className="flex items-start gap-2 text-sm text-stone-600">
                        <span className="mt-1.5 h-1 w-1 flex-shrink-0 rounded-full bg-orange-400/70" />
                        {item}
                      </p>
                    ))}
                  </div>
                </div>

                {/* Examples */}
                <div>
                  <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-orange-700/70">
                    {t('searchGuide.exampleQueries')}
                  </h3>
                  <div className="space-y-2.5">
                    {mode.examples.map((example, i) => (
                      <div
                        key={i}
                        className="rounded-xl border border-amber-200/40 bg-white/40 px-4 py-3"
                      >
                        <p className="font-ancient text-sm text-stone-800">
                          {example.query}
                        </p>
                        <p className="mt-1 text-xs text-stone-500">
                          {example.explanation}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Tips */}
                <div className="rounded-xl border border-amber-200/40 bg-amber-50/40 px-4 py-3.5">
                  <h3 className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-widest text-orange-700/70">
                    <Lightbulb className="h-3.5 w-3.5" />
                    {t('searchGuide.quickTips')}
                  </h3>
                  <ul className="space-y-1">
                    {tips.map((tip, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-stone-600">
                        <span className="mt-1.5 h-1 w-1 flex-shrink-0 rounded-full bg-amber-400/70" />
                        {tip}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Footer */}
              <div className="border-t border-amber-200/40 px-6 py-4">
                <button
                  onClick={onClose}
                  className="w-full rounded-full bg-stone-800 px-5 py-2.5 text-sm font-medium text-parchment-50 transition-colors hover:bg-stone-700"
                >
                  {t('searchGuide.gotIt')}
                </button>
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
};

export default SearchGuideModal;
