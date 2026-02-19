import { forwardRef } from 'react';
import { cn } from '../../utils/cn';

interface ScrollSectionProps {
  id: string;
  children: React.ReactNode;
  className?: string;
  /** Inner content wrapper: centered column with max-width */
  innerClassName?: string;
  /** Skip the inner wrapper entirely */
  noInner?: boolean;
}

/**
 * Full-viewport scroll-snap section.
 * Parent container must have `scroll-snap-type: y mandatory`.
 */
export const ScrollSection = forwardRef<HTMLElement, ScrollSectionProps>(
  ({ id, children, className, innerClassName, noInner = false }, ref) => {
    return (
      <section
        ref={ref}
        id={id}
        className={cn(
          // Scroll snap
          'scroll-snap-align-start',
          // Layout
          'relative min-h-screen w-full',
          // Overflow guard
          'overflow-hidden',
          className,
        )}
        style={{ scrollSnapAlign: 'start' }}
      >
        {noInner ? (
          children
        ) : (
          <div
            className={cn(
              'relative z-10 flex flex-col items-center justify-center min-h-screen',
              'px-4 sm:px-6 lg:px-8',
              'max-w-7xl mx-auto w-full',
              innerClassName,
            )}
          >
            {children}
          </div>
        )}
      </section>
    );
  },
);

ScrollSection.displayName = 'ScrollSection';
