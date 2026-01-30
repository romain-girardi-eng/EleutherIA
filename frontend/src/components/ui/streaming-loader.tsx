/**
 * StreamingLoader - Aurora-styled loading indicators for GraphRAG
 *
 * Uses very pale aurora palette with ShineBorder for elegant,
 * subtle animated borders and glass morphism.
 */

import { cn } from "@/lib/utils";
import { ShineBorder } from "./shine-border";

// Very pale aurora colors for shine border
const PALE_AURORA_COLORS = ["#e0e7ff", "#dbeafe", "#ede9fe"]; // indigo-100, blue-100, violet-100

interface StreamingLoaderProps {
  /** Status message to display */
  status?: string;
  /** Whether content is actively streaming */
  isStreaming?: boolean;
  /** Current step in the process */
  step?: string;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Main streaming status indicator with animated orbs
 */
export function StreamingLoader({
  status = "Processing...",
  isStreaming = true,
  step,
  className
}: StreamingLoaderProps) {
  return (
    <ShineBorder
      color={PALE_AURORA_COLORS}
      borderRadius={12}
      borderWidth={1}
      duration={10}
      className={cn(
        "bg-white/80 backdrop-blur-xl shadow-lg shadow-slate-100/20",
        className
      )}
    >
      <div className="flex items-center gap-4 p-4">
        {/* Animated orbs container */}
        <div className="relative flex items-center justify-center w-12 h-12">
          {/* Outer rotating ring */}
          <div className="absolute inset-0 rounded-full border-2 border-indigo-100 border-t-blue-200 animate-spin"
               style={{ animationDuration: '1.5s' }} />

          {/* Middle pulsing ring */}
          <div className="absolute inset-1 rounded-full border border-violet-100/50 animate-pulse" />

          {/* Inner glowing core */}
          <div className="relative w-5 h-5 rounded-full bg-gradient-to-br from-blue-100 to-indigo-100 shadow-md shadow-blue-50/40 animate-pulse">
            <div className="absolute inset-0.5 rounded-full bg-gradient-to-br from-blue-50 to-indigo-50" />
          </div>

          {/* Orbiting dots */}
          {isStreaming && (
            <>
              <div className="absolute w-2 h-2 rounded-full bg-blue-200 streaming-orbit-1" />
              <div className="absolute w-1.5 h-1.5 rounded-full bg-indigo-200 streaming-orbit-2" />
              <div className="absolute w-1 h-1 rounded-full bg-violet-200 streaming-orbit-3" />
            </>
          )}
        </div>

        {/* Status text */}
        <div className="flex-1 min-w-0">
          {step && (
            <div className="text-xs font-medium text-indigo-400 mb-0.5 uppercase tracking-wide">
              {step}
            </div>
          )}
          <div className="text-sm sm:text-base font-medium text-slate-600 truncate">
            {status}
          </div>
          {isStreaming && (
            <div className="flex gap-1 mt-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-200 animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-200 animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 rounded-full bg-violet-200 animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          )}
        </div>
      </div>
    </ShineBorder>
  );
}

/**
 * Compact inline loader for tight spaces
 */
export function StreamingLoaderCompact({
  status = "Loading...",
  className
}: {
  status?: string;
  className?: string;
}) {
  return (
    <div className={cn("flex items-center gap-3", className)}>
      {/* Three-dot animation */}
      <div className="flex gap-1">
        <span className="w-2 h-2 rounded-full bg-blue-200 animate-bounce" style={{ animationDelay: '0ms' }} />
        <span className="w-2 h-2 rounded-full bg-indigo-200 animate-bounce" style={{ animationDelay: '150ms' }} />
        <span className="w-2 h-2 rounded-full bg-violet-200 animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
      <span className="text-sm font-medium text-slate-500">{status}</span>
    </div>
  );
}

/**
 * Full-screen overlay loader (for heavy operations)
 * Glass morphism with ShineBorder and very pale aurora accents
 */
export function StreamingOverlay({
  status = "Processing...",
  substatus,
  className
}: {
  status?: string;
  substatus?: string;
  className?: string;
}) {
  return (
    <div className={cn(
      "fixed inset-0 z-50 flex items-center justify-center",
      "bg-white/70 backdrop-blur-xl",
      className
    )}>
      {/* Very subtle aurora gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-50/30 via-transparent to-indigo-50/30 pointer-events-none" />

      <ShineBorder
        color={PALE_AURORA_COLORS}
        borderRadius={16}
        borderWidth={1}
        duration={8}
        className="bg-white/90 backdrop-blur-sm shadow-xl shadow-slate-200/50"
      >
        <div className="flex flex-col items-center gap-6 p-8">
          {/* Large animated indicator */}
          <div className="relative w-20 h-20">
            {/* Outer ring */}
            <div className="absolute inset-0 rounded-full border-4 border-blue-50" />
            <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-blue-200 animate-spin"
                 style={{ animationDuration: '1s' }} />

            {/* Middle ring */}
            <div className="absolute inset-2 rounded-full border-2 border-indigo-50" />
            <div className="absolute inset-2 rounded-full border-2 border-transparent border-t-indigo-200 animate-spin"
                 style={{ animationDuration: '1.5s', animationDirection: 'reverse' }} />

            {/* Inner core with icon */}
            <div className="absolute inset-4 rounded-full bg-gradient-to-br from-blue-50 to-indigo-50 flex items-center justify-center">
              <svg className="w-6 h-6 text-indigo-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
          </div>

          {/* Text */}
          <div className="text-center">
            <h3 className="text-lg font-semibold text-slate-700">{status}</h3>
            {substatus && (
              <p className="mt-1 text-sm text-slate-400">{substatus}</p>
            )}
          </div>

          {/* Progress bar */}
          <div className="w-48 h-1 rounded-full bg-slate-100 overflow-hidden">
            <div className="h-full bg-gradient-to-r from-blue-200 via-indigo-200 to-blue-200 animate-shimmer"
                 style={{ width: '100%', backgroundSize: '200% 100%' }} />
          </div>
        </div>
      </ShineBorder>
    </div>
  );
}

/**
 * Knowledge graph traversal indicator
 * Shows nodes being explored with ShineBorder animation
 */
export function GraphTraversalLoader({
  nodesFound = 0,
  edgesTraversed = 0,
  status = "Exploring knowledge graph...",
  className
}: {
  nodesFound?: number;
  edgesTraversed?: number;
  status?: string;
  className?: string;
}) {
  return (
    <ShineBorder
      color={PALE_AURORA_COLORS}
      borderRadius={12}
      borderWidth={1}
      duration={12}
      className={cn(
        "bg-white/80 backdrop-blur-xl shadow-lg shadow-slate-100/50",
        className
      )}
    >
      <div className="p-4">
        {/* Header with animated icon */}
        <div className="flex items-center gap-3 mb-4">
          <div className="relative w-10 h-10">
            {/* Network icon with animation */}
            <svg className="w-10 h-10 text-indigo-200" viewBox="0 0 40 40" fill="none">
              {/* Nodes */}
              <circle cx="20" cy="8" r="4" fill="currentColor" className="animate-pulse" style={{ animationDelay: '0ms' }} />
              <circle cx="8" cy="28" r="4" fill="currentColor" className="animate-pulse" style={{ animationDelay: '200ms' }} />
              <circle cx="32" cy="28" r="4" fill="currentColor" className="animate-pulse" style={{ animationDelay: '400ms' }} />
              <circle cx="20" cy="24" r="3" fill="currentColor" className="opacity-60" />

              {/* Edges */}
              <line x1="20" y1="12" x2="20" y2="21" stroke="currentColor" strokeWidth="1.5" className="opacity-40" />
              <line x1="12" y1="26" x2="17" y2="24" stroke="currentColor" strokeWidth="1.5" className="opacity-40" />
              <line x1="28" y1="26" x2="23" y2="24" stroke="currentColor" strokeWidth="1.5" className="opacity-40" />

              {/* Animated traveling dot */}
              <circle r="2" fill="#c7d2fe" className="graph-travel-dot">
                <animateMotion dur="2s" repeatCount="indefinite" path="M20,8 L20,24 L8,28 L20,24 L32,28 L20,24 L20,8" />
              </circle>
            </svg>
          </div>
          <div className="flex-1">
            <div className="text-sm font-medium text-slate-600">{status}</div>
            <div className="flex gap-4 mt-1 text-xs text-slate-400">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-blue-200" />
                {nodesFound} nodes
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded bg-indigo-200" style={{ borderRadius: '2px' }} />
                {edgesTraversed} edges
              </span>
            </div>
          </div>
        </div>

        {/* Progress indicators */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-2 rounded-lg bg-blue-50/50 backdrop-blur-sm">
            <div className="text-2xl font-bold text-blue-400">{nodesFound}</div>
            <div className="text-xs text-slate-400">Nodes Found</div>
          </div>
          <div className="p-2 rounded-lg bg-indigo-50/50 backdrop-blur-sm">
            <div className="text-2xl font-bold text-indigo-400">{edgesTraversed}</div>
            <div className="text-xs text-slate-400">Edges Traversed</div>
          </div>
        </div>
      </div>
    </ShineBorder>
  );
}

/**
 * Text generation indicator with streaming cursor
 */
export function GeneratingIndicator({
  label = "Generating response",
  showCursor = true,
  className
}: {
  label?: string;
  showCursor?: boolean;
  className?: string;
}) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      {/* Quill/pen icon */}
      <svg className="w-4 h-4 text-indigo-300 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
      </svg>
      <span className="text-sm text-slate-500">{label}</span>
      {showCursor && (
        <span className="inline-block w-0.5 h-4 bg-indigo-200 animate-pulse" />
      )}
    </div>
  );
}

export default StreamingLoader;
