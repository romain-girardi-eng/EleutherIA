/**
 * ThinkingProcessPanel - Displays Kimi K2 reasoning process
 *
 * Shows the step-by-step thinking process from Kimi K2 model
 * when thinking mode is enabled.
 *
 * Uses very pale aurora palette with ShineBorder for elegant animated borders.
 */

import { useState, useEffect, useRef } from 'react';
import { ShineBorder } from '../ui/shine-border';

// Very pale aurora colors for shine border
const PALE_AURORA_COLORS = ["#e0e7ff", "#dbeafe", "#ede9fe"]; // indigo-100, blue-100, violet-100

interface ThinkingProcessPanelProps {
  thinking: string;
  isStreaming?: boolean;
  isComplete?: boolean;
}

export function ThinkingProcessPanel({
  thinking,
  isStreaming = false,
  isComplete = false,
}: ThinkingProcessPanelProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const contentRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom while streaming
  useEffect(() => {
    if (isStreaming && contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, [thinking, isStreaming]);

  if (!thinking) return null;

  return (
    <ShineBorder
      color={PALE_AURORA_COLORS}
      borderRadius={12}
      borderWidth={1}
      duration={isStreaming ? 6 : 14}
      className="bg-white/80 backdrop-blur-xl shadow-lg shadow-slate-100/30 mb-4 overflow-hidden"
    >
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-indigo-50/30 transition-colors"
      >
        <div className="flex items-center gap-2">
          {/* Brain/lightbulb icon with animation */}
          <div className={`relative ${isStreaming ? 'animate-pulse' : ''}`}>
            <div className="absolute inset-0 rounded-full bg-indigo-100/30 animate-ping" style={{ animationDuration: '2s' }} />
            <svg
              className="w-5 h-5 text-indigo-300 relative z-10"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
          </div>

          <span className="font-semibold text-slate-600">
            {isStreaming ? 'Reasoning...' : 'Thought Process'}
          </span>

          <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-400 border border-indigo-100">
            Kimi K2
          </span>

          {isComplete && (
            <svg
              className="w-4 h-4 text-emerald-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          )}
        </div>

        {/* Expand/collapse icon */}
        <svg
          className={`w-5 h-5 text-indigo-200 transition-transform duration-200 ${
            isExpanded ? 'rotate-180' : ''
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {/* Content */}
      {isExpanded && (
        <div
          ref={contentRef}
          className="px-4 pb-4 max-h-96 overflow-y-auto"
        >
          <div className="pl-4 border-l-2 border-indigo-100">
            <pre className="text-sm text-slate-600 whitespace-pre-wrap font-mono leading-relaxed">
              {thinking}
              {isStreaming && (
                <span className="inline-block w-0.5 h-4 bg-indigo-200 animate-pulse ml-0.5" />
              )}
            </pre>
          </div>
        </div>
      )}

      {/* Progress bar at bottom while streaming */}
      {isStreaming && (
        <div className="h-1 bg-indigo-50 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-200 via-indigo-200 to-violet-200"
            style={{
              width: '100%',
              backgroundSize: '200% 100%',
              animation: 'streaming-shimmer 2s linear infinite'
            }}
          />
        </div>
      )}
    </ShineBorder>
  );
}

/**
 * Compact version for inline display in chat messages
 */
export function ThinkingProcessCompact({
  thinking,
}: {
  thinking: string;
}) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!thinking) return null;

  // Show preview (first 200 chars)
  const preview = thinking.length > 200
    ? thinking.slice(0, 200) + '...'
    : thinking;

  return (
    <div className="mt-3 pt-3 border-t border-indigo-100/50">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 text-sm text-indigo-400 hover:text-indigo-500 transition-colors"
      >
        <svg
          className="w-4 h-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
          />
        </svg>
        <span>{isExpanded ? 'Hide' : 'Show'} thinking process</span>
        <svg
          className={`w-4 h-4 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {isExpanded && (
        <div className="mt-2 pl-4 border-l-2 border-indigo-100/50">
          <pre className="text-xs text-slate-500 whitespace-pre-wrap font-mono max-h-64 overflow-y-auto">
            {thinking}
          </pre>
        </div>
      )}

      {!isExpanded && thinking.length > 200 && (
        <p className="mt-1 text-xs text-slate-400 italic line-clamp-2">
          {preview}
        </p>
      )}
    </div>
  );
}

export default ThinkingProcessPanel;
