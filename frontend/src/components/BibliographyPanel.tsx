import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';

interface BibliographyEntry {
  citation_key: string;
  author: string;
  year?: number;
  title: string;
  full_citation_chicago: string;
  full_citation_apa?: string;
  full_citation_harvard?: string;
  bibtex: string;
  page_reference?: string;
}

interface BibliographyPanelProps {
  bibliography: BibliographyEntry[];
  chicagoBibliography?: string;
  apaBibliography?: string;
  harvardBibliography?: string;
  bibtexBibliography?: string;
  ctsUrns?: string[];
}

const BibliographyPanel: React.FC<BibliographyPanelProps> = ({
  bibliography,
  chicagoBibliography,
  apaBibliography,
  harvardBibliography,
  bibtexBibliography,
  ctsUrns = [],
}) => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<'chicago' | 'apa' | 'harvard' | 'bibtex' | 'urns'>('chicago');
  const [copied, setCopied] = useState(false);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  if (!bibliography || bibliography.length === 0) {
    return null;
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 px-4 py-3">
        <h3 className="text-white font-semibold flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          {t('bibliography.title')}
        </h3>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 bg-gray-50 overflow-x-auto">
        <button
          onClick={() => setActiveTab('chicago')}
          className={`flex-1 px-4 py-2 text-sm font-medium transition-colors whitespace-nowrap ${
            activeTab === 'chicago'
              ? 'bg-white text-primary-600 border-b-2 border-primary-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Chicago
        </button>
        <button
          onClick={() => setActiveTab('apa')}
          className={`flex-1 px-4 py-2 text-sm font-medium transition-colors whitespace-nowrap ${
            activeTab === 'apa'
              ? 'bg-white text-primary-600 border-b-2 border-primary-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          APA
        </button>
        <button
          onClick={() => setActiveTab('harvard')}
          className={`flex-1 px-4 py-2 text-sm font-medium transition-colors whitespace-nowrap ${
            activeTab === 'harvard'
              ? 'bg-white text-primary-600 border-b-2 border-primary-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Harvard
        </button>
        <button
          onClick={() => setActiveTab('bibtex')}
          className={`flex-1 px-4 py-2 text-sm font-medium transition-colors whitespace-nowrap ${
            activeTab === 'bibtex'
              ? 'bg-white text-primary-600 border-b-2 border-primary-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          BibTeX
        </button>
        {ctsUrns.length > 0 && (
          <button
            onClick={() => setActiveTab('urns')}
            className={`flex-1 px-4 py-2 text-sm font-medium transition-colors whitespace-nowrap ${
              activeTab === 'urns'
                ? 'bg-white text-primary-600 border-b-2 border-primary-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            CTS URNs
          </button>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        {activeTab === 'chicago' && (
          <div className="space-y-3">
            <div className="flex justify-between items-center mb-3">
              <span className="text-sm text-gray-600">
                {bibliography.length} {bibliography.length === 1 ? t('bibliography.reference') : t('bibliography.references')}
              </span>
              <button
                onClick={() => copyToClipboard(chicagoBibliography || '')}
                className="text-xs px-3 py-1 bg-primary-50 text-primary-700 rounded-md hover:bg-primary-100 transition-colors flex items-center gap-1"
              >
                {copied ? (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    {t('common.copied')}
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    Copy All
                  </>
                )}
              </button>
            </div>
            {bibliography.map((entry, index) => (
              <div key={entry.citation_key} className="text-sm text-gray-700 hover:bg-gray-50 p-2 rounded transition-colors">
                <span className="font-medium text-primary-600">[{index + 1}]</span>{' '}
                {entry.full_citation_chicago}
                {entry.page_reference && (
                  <span className="text-gray-500 ml-2">({entry.page_reference})</span>
                )}
              </div>
            ))}
          </div>
        )}

        {activeTab === 'apa' && (
          <div className="space-y-3">
            <div className="flex justify-between items-center mb-3">
              <span className="text-sm text-gray-600">
                {bibliography.length} {bibliography.length === 1 ? 'source' : 'sources'} · APA 7th Edition
              </span>
              <button
                onClick={() => copyToClipboard(apaBibliography || '')}
                className="text-xs px-3 py-1 bg-primary-50 text-primary-700 rounded-md hover:bg-primary-100 transition-colors flex items-center gap-1"
              >
                {copied ? (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Copied!
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    Copy All
                  </>
                )}
              </button>
            </div>
            {bibliography.map((entry, index) => (
              <div key={entry.citation_key} className="text-sm text-gray-700 hover:bg-gray-50 p-2 rounded transition-colors">
                <span className="font-medium text-primary-600">[{index + 1}]</span>{' '}
                {entry.full_citation_apa || entry.full_citation_chicago}
                {entry.page_reference && (
                  <span className="text-gray-500 ml-2">({entry.page_reference})</span>
                )}
              </div>
            ))}
            <p className="text-xs text-gray-500 mt-3 pt-3 border-t border-gray-200">
              APA (American Psychological Association) style is commonly used in psychology, education, and social sciences.
            </p>
          </div>
        )}

        {activeTab === 'harvard' && (
          <div className="space-y-3">
            <div className="flex justify-between items-center mb-3">
              <span className="text-sm text-gray-600">
                {bibliography.length} {bibliography.length === 1 ? 'source' : 'sources'} · Harvard Referencing
              </span>
              <button
                onClick={() => copyToClipboard(harvardBibliography || '')}
                className="text-xs px-3 py-1 bg-primary-50 text-primary-700 rounded-md hover:bg-primary-100 transition-colors flex items-center gap-1"
              >
                {copied ? (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Copied!
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    Copy All
                  </>
                )}
              </button>
            </div>
            {bibliography.map((entry, index) => (
              <div key={entry.citation_key} className="text-sm text-gray-700 hover:bg-gray-50 p-2 rounded transition-colors">
                <span className="font-medium text-primary-600">[{index + 1}]</span>{' '}
                {entry.full_citation_harvard || entry.full_citation_chicago}
                {entry.page_reference && (
                  <span className="text-gray-500 ml-2">({entry.page_reference})</span>
                )}
              </div>
            ))}
            <p className="text-xs text-gray-500 mt-3 pt-3 border-t border-gray-200">
              Harvard style is commonly used in UK universities and interdisciplinary research.
            </p>
          </div>
        )}

        {activeTab === 'bibtex' && (
          <div className="space-y-3">
            <div className="flex justify-between items-center mb-3">
              <span className="text-sm text-gray-600">
                BibTeX entries for LaTeX
              </span>
              <button
                onClick={() => copyToClipboard(bibtexBibliography || '')}
                className="text-xs px-3 py-1 bg-primary-50 text-primary-700 rounded-md hover:bg-primary-100 transition-colors flex items-center gap-1"
              >
                {copied ? (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Copied!
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    Copy All
                  </>
                )}
              </button>
            </div>
            <pre className="text-xs bg-gray-50 p-3 rounded border border-gray-200 overflow-x-auto font-mono">
              {bibtexBibliography || bibliography.map(entry => entry.bibtex).join('\n\n')}
            </pre>
          </div>
        )}

        {activeTab === 'urns' && ctsUrns.length > 0 && (
          <div className="space-y-3">
            <div className="flex justify-between items-center mb-3">
              <span className="text-sm text-gray-600">
                Canonical Text Services URNs
              </span>
              <button
                onClick={() => copyToClipboard(ctsUrns.join('\n'))}
                className="text-xs px-3 py-1 bg-primary-50 text-primary-700 rounded-md hover:bg-primary-100 transition-colors flex items-center gap-1"
              >
                {copied ? (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Copied!
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    Copy All
                  </>
                )}
              </button>
            </div>
            <div className="space-y-2">
              {ctsUrns.map((urn, index) => (
                <div key={index} className="text-xs font-mono bg-gray-50 p-2 rounded border border-gray-200 hover:bg-gray-100 transition-colors">
                  {urn}
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-3">
              CTS URNs provide canonical, persistent references to ancient texts recognized by scholarly databases (Perseus, TLG, PHI).
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default BibliographyPanel;
