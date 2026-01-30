import React from 'react';
import { cn } from '@/utils/cn';

interface FocusIndicatorProps {
  children: React.ReactNode;
  className?: string;
  ringColor?: string;
  ringWidth?: number;
  ringOffset?: number;
}

/**
 * Wrapper component that provides consistent, visible focus indicators
 * Meets WCAG 2.1 AA requirements for focus visibility
 */
export const FocusIndicator: React.FC<FocusIndicatorProps> = ({
  children,
  className,
  ringColor = 'ring-blue-500',
  ringWidth = 2,
  ringOffset = 2,
}) => {
  const ringClass = `focus-within:ring-${ringWidth}`;
  const offsetClass = `focus-within:ring-offset-${ringOffset}`;

  return (
    <div
      className={cn(
        'rounded-md transition-shadow duration-200',
        'focus-within:outline-none',
        ringClass,
        offsetClass,
        ringColor,
        className
      )}
    >
      {children}
    </div>
  );
};

/**
 * High contrast wrapper for improved visibility
 */
interface HighContrastWrapperProps {
  children: React.ReactNode;
  className?: string;
}

export const HighContrastWrapper: React.FC<HighContrastWrapperProps> = ({
  children,
  className,
}) => {
  const [prefersHighContrast, setPrefersHighContrast] = React.useState(false);

  React.useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-contrast: more)');
    setPrefersHighContrast(mediaQuery.matches);

    const handler = (e: MediaQueryListEvent) => setPrefersHighContrast(e.matches);
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  return (
    <div
      className={cn(
        prefersHighContrast && 'high-contrast-mode',
        className
      )}
      data-high-contrast={prefersHighContrast}
    >
      {children}
    </div>
  );
};

/**
 * Reduced motion wrapper
 * Disables animations when user prefers reduced motion
 */
interface ReducedMotionWrapperProps {
  children: React.ReactNode;
  className?: string;
}

export const ReducedMotionWrapper: React.FC<ReducedMotionWrapperProps> = ({
  children,
  className,
}) => {
  const [prefersReducedMotion, setPrefersReducedMotion] = React.useState(false);

  React.useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const handler = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches);
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  return (
    <div
      className={cn(
        prefersReducedMotion && 'motion-reduce',
        className
      )}
      data-reduced-motion={prefersReducedMotion}
    >
      {children}
    </div>
  );
};

/**
 * Accessible loading indicator with proper ARIA
 */
interface AccessibleLoadingProps {
  isLoading: boolean;
  loadingText?: string;
  children: React.ReactNode;
}

export const AccessibleLoading: React.FC<AccessibleLoadingProps> = ({
  isLoading,
  loadingText = 'Loading...',
  children,
}) => {
  return (
    <div aria-busy={isLoading} aria-live="polite">
      {isLoading ? (
        <div role="status" aria-label={loadingText}>
          <span className="sr-only">{loadingText}</span>
          {/* Visual loading indicator */}
          <div className="flex items-center justify-center p-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
          </div>
        </div>
      ) : (
        children
      )}
    </div>
  );
};

/**
 * Error boundary with accessible error message
 */
interface AccessibleErrorProps {
  error: Error | null;
  resetError?: () => void;
  children: React.ReactNode;
}

export const AccessibleError: React.FC<AccessibleErrorProps> = ({
  error,
  resetError,
  children,
}) => {
  if (error) {
    return (
      <div
        role="alert"
        aria-live="assertive"
        className="bg-red-50 border border-red-200 rounded-lg p-4"
      >
        <h2 className="text-lg font-semibold text-red-800 mb-2">
          An error occurred
        </h2>
        <p className="text-red-700 mb-4">{error.message}</p>
        {resetError && (
          <button
            onClick={resetError}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
          >
            Try again
          </button>
        )}
      </div>
    );
  }

  return <>{children}</>;
};

/**
 * Screen reader only text
 * Visually hidden but accessible to screen readers
 */
interface SROnlyProps {
  children: React.ReactNode;
}

export const SROnly: React.FC<SROnlyProps> = ({ children }) => {
  return <span className="sr-only">{children}</span>;
};

/**
 * Visually hidden helper
 * Alternative to sr-only with more control
 */
interface VisuallyHiddenProps {
  children: React.ReactNode;
  as?: 'span' | 'div' | 'p' | 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
}

export const VisuallyHidden: React.FC<VisuallyHiddenProps> = ({
  children,
  as: Component = 'span',
}) => {
  const style: React.CSSProperties = {
    position: 'absolute',
    width: '1px',
    height: '1px',
    padding: '0',
    margin: '-1px',
    overflow: 'hidden',
    clip: 'rect(0, 0, 0, 0)',
    whiteSpace: 'nowrap',
    border: '0',
  };

  return React.createElement(Component, { style }, children);
};

/**
 * External link component with proper accessibility attributes
 */
interface ExternalLinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  children: React.ReactNode;
  showIcon?: boolean;
}

export const ExternalLink: React.FC<ExternalLinkProps> = ({
  children,
  showIcon = true,
  ...props
}) => {
  return (
    <a
      {...props}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        'inline-flex items-center gap-1',
        'text-blue-600 hover:text-blue-800 underline',
        'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded',
        props.className
      )}
    >
      {children}
      {showIcon && (
        <svg
          className="h-4 w-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
          />
        </svg>
      )}
      <SROnly>(opens in new tab)</SROnly>
    </a>
  );
};
