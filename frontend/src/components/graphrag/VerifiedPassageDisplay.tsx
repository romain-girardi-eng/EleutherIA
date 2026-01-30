/**
 * VerifiedPassageDisplay - Displays verified ancient passages with original Greek/Latin
 *
 * Shows passages that have been verified against the EleutherIA database,
 * with original Greek/Latin text and transliterations.
 *
 * Uses pale emerald palette for a scholarly, authoritative feel.
 */

import { useState } from 'react';
import { ShineBorder } from '../ui/shine-border';

// Pale scholarly green colors
const SCHOLARLY_COLORS = ["#d1fae5", "#a7f3d0", "#ecfdf5"]; // emerald-100, emerald-200, emerald-50

export interface VerifiedPassage {
  passage_id: string;
  cts_urn: string | null;
  work_title: string;
  work_title_original: string | null;
  author: string;
  author_original: string | null;
  language: string;
  reference: string;
  original_text: string;
  transliteration: string;
  char_start: number;
  char_end: number;
  confidence: number;
}

interface VerifiedPassageDisplayProps {
  passages: VerifiedPassage[];
  maxInitialDisplay?: number;
}

export function VerifiedPassageDisplay({
  passages,
  maxInitialDisplay = 3,
}: VerifiedPassageDisplayProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [expandedPassages, setExpandedPassages] = useState<Set<string>>(new Set());

  if (!passages || passages.length === 0) return null;

  const displayedPassages = isExpanded ? passages : passages.slice(0, maxInitialDisplay);
  const hasMore = passages.length > maxInitialDisplay;

  const togglePassageExpansion = (passageId: string) => {
    setExpandedPassages(prev => {
      const newSet = new Set(prev);
      if (newSet.has(passageId)) {
        newSet.delete(passageId);
      } else {
        newSet.add(passageId);
      }
      return newSet;
    });
  };

  const getLanguageLabel = (language: string) => {
    switch (language.toLowerCase()) {
      case 'grc':
      case 'greek':
        return 'Greek';
      case 'lat':
      case 'latin':
        return 'Latin';
      default:
        return language;
    }
  };

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.9) {
      return (
        <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200">
          High Confidence
        </span>
      );
    } else if (confidence >= 0.7) {
      return (
        <span className="text-xs px-2 py-0.5 rounded-full bg-amber-50 text-amber-600 border border-amber-200">
          Medium Confidence
        </span>
      );
    }
    return (
      <span className="text-xs px-2 py-0.5 rounded-full bg-slate-50 text-slate-500 border border-slate-200">
        Low Confidence
      </span>
    );
  };

  return (
    <ShineBorder
      color={SCHOLARLY_COLORS}
      borderRadius={12}
      borderWidth={1}
      duration={14}
      className="bg-white/80 backdrop-blur-xl shadow-lg shadow-emerald-100/30 mt-4 overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-emerald-100">
        <div className="flex items-center gap-2">
          {/* Scroll/document icon */}
          <svg
            className="w-5 h-5 text-emerald-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <span className="font-semibold text-slate-600">
            Verified Ancient Passages
          </span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-500 border border-emerald-100">
            {passages.length} {passages.length === 1 ? 'passage' : 'passages'}
          </span>
        </div>

        {/* Verified badge */}
        <div className="flex items-center gap-1 text-emerald-500">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
          <span className="text-xs font-medium">Database Verified</span>
        </div>
      </div>

      {/* Passages List */}
      <div className="divide-y divide-emerald-50">
        {displayedPassages.map((passage, index) => {
          const isPassageExpanded = expandedPassages.has(passage.passage_id);
          const truncatedText = passage.original_text.length > 200
            ? passage.original_text.slice(0, 200) + '...'
            : passage.original_text;

          return (
            <div
              key={passage.passage_id || index}
              className="px-4 py-3 hover:bg-emerald-50/30 transition-colors"
            >
              {/* Passage Header */}
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  {/* Author and Work */}
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-slate-700">
                      {passage.author_original || passage.author}
                    </span>
                    <span className="text-slate-400">•</span>
                    <span className="text-slate-600 italic">
                      {passage.work_title_original || passage.work_title}
                    </span>
                    {passage.reference && (
                      <>
                        <span className="text-slate-400">•</span>
                        <span className="text-slate-500 font-mono text-sm">
                          {passage.reference}
                        </span>
                      </>
                    )}
                  </div>

                  {/* Metadata badges */}
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-500 border border-indigo-100">
                      {getLanguageLabel(passage.language)}
                    </span>
                    {passage.cts_urn && (
                      <span className="text-xs text-slate-400 font-mono">
                        {passage.cts_urn}
                      </span>
                    )}
                    {getConfidenceBadge(passage.confidence)}
                  </div>
                </div>

                {/* Expand button */}
                {passage.original_text.length > 200 && (
                  <button
                    onClick={() => togglePassageExpansion(passage.passage_id)}
                    className="ml-2 p-1 text-emerald-400 hover:text-emerald-600 hover:bg-emerald-50 rounded transition-colors"
                    title={isPassageExpanded ? 'Collapse' : 'Expand'}
                  >
                    <svg
                      className={`w-4 h-4 transition-transform duration-200 ${isPassageExpanded ? 'rotate-180' : ''}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                )}
              </div>

              {/* Original Text (Greek/Latin) */}
              <div className="mt-2 p-3 rounded-lg bg-slate-50 border border-slate-100">
                <p
                  className={`text-slate-800 leading-relaxed ${
                    passage.language === 'grc' || passage.language === 'greek'
                      ? 'font-serif text-lg'
                      : 'font-serif italic'
                  }`}
                  lang={passage.language === 'grc' || passage.language === 'greek' ? 'grc' : 'la'}
                >
                  {isPassageExpanded ? passage.original_text : truncatedText}
                </p>
              </div>

              {/* Transliteration (for Greek) */}
              {passage.transliteration && (passage.language === 'grc' || passage.language === 'greek') && (
                <div className="mt-2 p-2 rounded bg-emerald-50/50 border border-emerald-100">
                  <div className="flex items-center gap-1 mb-1">
                    <span className="text-xs text-emerald-600 font-medium">Transliteration:</span>
                  </div>
                  <p className="text-sm text-slate-600 italic">
                    {isPassageExpanded
                      ? passage.transliteration
                      : passage.transliteration.length > 200
                        ? passage.transliteration.slice(0, 200) + '...'
                        : passage.transliteration
                    }
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Show More/Less Button */}
      {hasMore && (
        <div className="px-4 py-3 border-t border-emerald-100">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="w-full flex items-center justify-center gap-2 py-2 text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50 rounded-lg transition-colors"
          >
            {isExpanded ? (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                </svg>
                Show Less
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
                Show {passages.length - maxInitialDisplay} More Passages
              </>
            )}
          </button>
        </div>
      )}
    </ShineBorder>
  );
}
