/**
 * AccordionPanel Component
 * Responsive wrapper that makes panels collapsible on mobile
 * Part of EleutherIA mobile UI redesign - Week 2 Interactive Controls
 */

import { useState, useRef, useEffect, type ReactNode } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { useDevice } from '../../context/DeviceContext';

interface AccordionPanelProps {
  /** Panel title shown in header */
  title: string;

  /** Optional icon to display next to title */
  icon?: ReactNode;

  /** Panel content */
  children: ReactNode;

  /** Default expanded state (mobile only) */
  defaultExpanded?: boolean;

  /** Optional badge text (e.g., "5 items") */
  badge?: string;

  /** Additional CSS classes for the container */
  className?: string;

  /** Disable accordion behavior (always show content) */
  disableAccordion?: boolean;

  /** Show loading state */
  loading?: boolean;

  /** Semantic heading level for the panel title */
  headingLevel?: 2 | 3 | 4;

  /** Custom loading skeleton */
  loadingSkeleton?: ReactNode;
}

export default function AccordionPanel({
  title,
  icon,
  children,
  defaultExpanded = false,
  badge,
  className = '',
  disableAccordion = false,
  loading = false,
  headingLevel = 3,
  loadingSkeleton,
}: AccordionPanelProps) {
  const { isMobile } = useDevice();
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const contentRef = useRef<HTMLDivElement>(null);
  const [contentHeight, setContentHeight] = useState<number>(0);

  // On desktop or when accordion is disabled, always show content
  const shouldUseAccordion = isMobile && !disableAccordion;
  const showContent = !shouldUseAccordion || isExpanded;
  const Heading = `h${headingLevel}` as 'h2' | 'h3' | 'h4';

  // Measure content height for smooth animation
  useEffect(() => {
    if (contentRef.current) {
      setContentHeight(contentRef.current.scrollHeight);
    }
  }, [children, isExpanded]);

  // Recalculate height on window resize
  useEffect(() => {
    const handleResize = () => {
      if (contentRef.current) {
        setContentHeight(contentRef.current.scrollHeight);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <div className={`academic-card ${className}`}>
      {/* Header - Always visible */}
      <button
        onClick={() => shouldUseAccordion && setIsExpanded(!isExpanded)}
        className={`w-full flex items-center justify-between gap-3 ${
          shouldUseAccordion ? 'cursor-pointer hover:bg-gray-50 active:bg-gray-100 -m-4 p-4 rounded-lg transition-colors' : 'cursor-default mb-4'
        }`}
        disabled={!shouldUseAccordion}
        aria-expanded={showContent}
        aria-controls={`accordion-content-${title.replace(/\s+/g, '-')}`}
      >
        <div className="flex items-center gap-3 min-w-0">
          {icon && <div className="flex-shrink-0 text-primary-600">{icon}</div>}
          <Heading className="text-lg font-semibold text-academic-text text-left truncate">
            {title}
          </Heading>
          {badge && (
            <span className="flex-shrink-0 px-2 py-0.5 bg-primary-100 text-primary-700 text-xs font-medium rounded-full">
              {badge}
            </span>
          )}
        </div>

        {shouldUseAccordion && (
          <div className="flex-shrink-0 text-gray-400">
            {isExpanded ? (
              <ChevronUp className="w-5 h-5" aria-hidden="true" />
            ) : (
              <ChevronDown className="w-5 h-5" aria-hidden="true" />
            )}
          </div>
        )}
      </button>

      {/* Content - Collapsible on mobile */}
      <div
        id={`accordion-content-${title.replace(/\s+/g, '-')}`}
        ref={contentRef}
        className={`overflow-hidden transition-all duration-300 ease-in-out ${
          shouldUseAccordion ? '' : 'mt-0'
        }`}
        style={
          shouldUseAccordion
            ? {
                maxHeight: showContent ? `${contentHeight}px` : '0px',
                opacity: showContent ? 1 : 0,
              }
            : undefined
        }
      >
        <div className={shouldUseAccordion ? 'pt-4' : ''}>
          {loading ? (
            loadingSkeleton || (
              <div className="space-y-3 animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4" />
                <div className="h-4 bg-gray-200 rounded w-full" />
                <div className="h-4 bg-gray-200 rounded w-5/6" />
              </div>
            )
          ) : (
            children
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * AccordionGroup Component
 * Groups multiple accordion panels with coordinated behavior
 */
interface AccordionGroupProps {
  children: ReactNode;
  /** Allow only one panel to be expanded at a time */
  exclusive?: boolean;
  className?: string;
}

export function AccordionGroup({ children, className = '' }: AccordionGroupProps) {
  // TODO: Implement exclusive accordion behavior if needed
  // For now, just renders children in a spaced container

  return (
    <div className={`space-y-4 ${className}`}>
      {children}
    </div>
  );
}
