import React from 'react';
import { X, HelpCircle, Search, ArrowRight, CheckCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { tArray } from '../i18n/utils';

interface SearchGuideModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const SearchGuideModal: React.FC<SearchGuideModalProps> = ({ isOpen, onClose }) => {
  const { t } = useTranslation();

  if (!isOpen) return null;

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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <HelpCircle className="w-8 h-8" />
              <div>
                <h2 className="text-2xl font-bold">{t('searchGuide.title')}</h2>
                <p className="text-blue-100">{t('searchGuide.description')}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:bg-white hover:bg-opacity-20 rounded-full p-2 transition"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(90vh-180px)]">
          {/* Mode Header */}
          <div className="bg-blue-50 dark:bg-blue-900/30 border-b border-blue-200 dark:border-blue-700 px-6 py-4">
            <div className="flex items-center space-x-2">
              <Search className="w-5 h-5 text-blue-600" />
              <span className="font-semibold text-blue-800 dark:text-blue-200">{mode.name}</span>
              <span className="text-sm text-blue-600 dark:text-blue-300">- {mode.model}</span>
            </div>
          </div>

          <div className="p-6 space-y-6">
            {/* Overview */}
            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 space-y-2">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-semibold text-gray-700 dark:text-gray-300">{t('searchGuide.methodLabel')}</span>
                  <span className="ml-2 text-gray-600 dark:text-gray-400">{mode.method}</span>
                </div>
                <div>
                  <span className="font-semibold text-gray-700 dark:text-gray-300">{t('searchGuide.granularityLabel')}</span>
                  <span className="ml-2 text-gray-600 dark:text-gray-400">{mode.granularity}</span>
                </div>
              </div>
            </div>

            {/* Best For */}
            <div>
              <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-3 flex items-center">
                <CheckCircle className="w-5 h-5 mr-2 text-green-600" />
                {t('searchGuide.bestFor')}
              </h3>
              <ul className="space-y-2">
                {mode.bestFor.map((item, index) => (
                  <li key={index} className="flex items-start">
                    <ArrowRight className="w-4 h-4 mr-2 mt-1 text-green-600 flex-shrink-0" />
                    <span className="text-gray-700 dark:text-gray-300">{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Examples */}
            <div>
              <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-3">
                {t('searchGuide.exampleQueries')}
              </h3>
              <div className="space-y-4">
                {mode.examples.map((example, index) => (
                  <div
                    key={index}
                    className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-4"
                  >
                    <div className="font-mono text-sm bg-gray-100 dark:bg-gray-800 p-2 rounded mb-2">
                      {example.query}
                    </div>
                    <p className="text-sm text-gray-700 dark:text-gray-300 mb-1">
                      {example.explanation}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 italic">
                      {t('searchGuide.whyPrefix')} {example.why}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Tips */}
            <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-2">
                {t('searchGuide.quickTips')}
              </h3>
              <ul className="space-y-1 text-sm text-blue-800 dark:text-blue-200">
                {tips.map((tip, index) => (
                  <li key={index}>• {tip}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-gray-50 dark:bg-gray-900">
          <button
            onClick={onClose}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition"
          >
            {t('searchGuide.gotIt')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SearchGuideModal;
