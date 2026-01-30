import type { CSSProperties } from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '../../utils/cn';
import { AILoader, PageLoader as AIPageLoader } from './ai-loader';

export type LoadingType = 'spinner' | 'skeleton' | 'dots' | 'progress' | 'pulse' | 'bars';

interface LoadingStateProps {
  /** Type of loading indicator */
  type?: LoadingType;
  /** Optional message to display */
  message?: string;
  /** Progress value (0-100) for progress type */
  progress?: number;
  /** Additional CSS classes */
  className?: string;
  /** Size of the loader */
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  /** Color variant */
  color?: 'primary' | 'secondary' | 'accent' | 'neutral';
  /** Whether to center the loader in its container */
  center?: boolean;
  /** Whether to show as overlay */
  overlay?: boolean;
  /** Whether to show backdrop with overlay */
  backdrop?: boolean;
}

/**
 * LoadingState component with multiple loading indicators
 *
 * @example
 * <LoadingState type="spinner" message="Loading data..." />
 *
 * @example
 * <LoadingState type="progress" progress={65} />
 *
 * @example
 * <LoadingState type="skeleton" />
 */
export function LoadingState({
  type = 'spinner',
  message,
  progress = 0,
  className,
  size = 'md',
  color = 'primary',
  center = true,
  overlay = false,
  backdrop = true,
}: LoadingStateProps) {
  const sizeClasses = {
    xs: { loader: 'h-3 w-3', text: 'text-xs' },
    sm: { loader: 'h-4 w-4', text: 'text-sm' },
    md: { loader: 'h-8 w-8', text: 'text-base' },
    lg: { loader: 'h-12 w-12', text: 'text-lg' },
    xl: { loader: 'h-16 w-16', text: 'text-xl' },
  };

  const colorClasses = {
    primary: 'text-primary-600',
    secondary: 'text-secondary-600',
    accent: 'text-accent-600',
    neutral: 'text-gray-600',
  };

  const renderLoader = () => {
    switch (type) {
      case 'spinner':
        return (
          <Loader2
            className={cn(
              'animate-spin',
              sizeClasses[size].loader,
              colorClasses[color]
            )}
            aria-label="Loading"
          />
        );

      case 'skeleton':
        return (
          <div className="space-y-3 w-full">
            <div className="h-4 bg-gray-200 rounded animate-pulse w-3/4"></div>
            <div className="h-3 bg-gray-200 rounded animate-pulse w-1/2"></div>
            <div className="h-3 bg-gray-200 rounded animate-pulse w-5/6"></div>
            <div className="h-3 bg-gray-200 rounded animate-pulse w-2/3"></div>
          </div>
        );

      case 'dots':
        const dotSize = {
          xs: 'h-1.5 w-1.5',
          sm: 'h-2 w-2',
          md: 'h-3 w-3',
          lg: 'h-4 w-4',
          xl: 'h-5 w-5',
        };

        return (
          <div className="flex space-x-2">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className={cn(
                  'rounded-full animate-pulse',
                  dotSize[size],
                  color === 'primary' ? 'bg-primary-600' :
                  color === 'secondary' ? 'bg-secondary-600' :
                  color === 'accent' ? 'bg-accent-600' : 'bg-gray-600'
                )}
                style={{
                  animationDelay: `${i * 150}ms`,
                  animationDuration: '1.4s',
                }}
              />
            ))}
          </div>
        );

      case 'progress':
        return (
          <div className="w-full space-y-2">
            <div className="bg-gray-200 rounded-full h-2 overflow-hidden">
              <div
                className={cn(
                  'h-full rounded-full transition-all duration-300 ease-out',
                  color === 'primary' ? 'bg-primary-600' :
                  color === 'secondary' ? 'bg-secondary-600' :
                  color === 'accent' ? 'bg-accent-600' : 'bg-gray-600'
                )}
                style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
                role="progressbar"
                aria-valuenow={progress}
                aria-valuemin={0}
                aria-valuemax={100}
              />
            </div>
            {progress > 0 && (
              <p className={cn('text-center', sizeClasses[size].text, colorClasses[color])}>
                {Math.round(progress)}%
              </p>
            )}
          </div>
        );

      case 'pulse':
        return (
          <div className={cn(
            'rounded-full animate-ping',
            sizeClasses[size].loader,
            color === 'primary' ? 'bg-primary-600' :
            color === 'secondary' ? 'bg-secondary-600' :
            color === 'accent' ? 'bg-accent-600' : 'bg-gray-600'
          )} />
        );

      case 'bars':
        const barSize = {
          xs: 'h-3 w-0.5',
          sm: 'h-4 w-1',
          md: 'h-8 w-1.5',
          lg: 'h-12 w-2',
          xl: 'h-16 w-3',
        };

        return (
          <div className="flex items-center space-x-1">
            {[0, 1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className={cn(
                  'rounded-full',
                  barSize[size],
                  color === 'primary' ? 'bg-primary-600' :
                  color === 'secondary' ? 'bg-secondary-600' :
                  color === 'accent' ? 'bg-accent-600' : 'bg-gray-600'
                )}
                style={{
                  animation: 'pulse 1.4s ease-in-out infinite',
                  animationDelay: `${i * 100}ms`,
                }}
              />
            ))}
          </div>
        );

      default:
        return null;
    }
  };

  const content = (
    <div
      className={cn(
        'flex flex-col items-center justify-center',
        center && !overlay && 'mx-auto',
        className
      )}
      role="status"
      aria-live="polite"
    >
      {renderLoader()}
      {message && (
        <p className={cn(
          'mt-3',
          sizeClasses[size].text,
          colorClasses[color]
        )}>
          {message}
        </p>
      )}
      <span className="sr-only">Loading...</span>
    </div>
  );

  if (overlay) {
    return (
      <div className={cn(
        'fixed inset-0 z-50 flex items-center justify-center',
        backdrop && 'bg-black/50'
      )}>
        <div className="bg-white rounded-lg p-6 shadow-xl">
          {content}
        </div>
      </div>
    );
  }

  return content;
}

/**
 * Skeleton loading components for specific use cases
 */

interface SkeletonProps {
  className?: string;
  animate?: boolean;
  style?: CSSProperties;
}

export function Skeleton({ className, animate = true, style }: SkeletonProps) {
  return (
    <div
      className={cn(
        'bg-gray-200 rounded',
        animate && 'animate-pulse',
        className
      )}
      style={style}
    />
  );
}

export function TextSkeleton({ lines = 3, className }: { lines?: number; className?: string }) {
  return (
    <div className={cn('space-y-2', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          className="h-4"
          style={{ width: `${Math.random() * 40 + 60}%` }}
        />
      ))}
    </div>
  );
}

export function CardSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn(
      'bg-white border border-gray-200 rounded-lg p-6 space-y-4',
      className
    )}>
      <div className="flex items-start justify-between">
        <div className="space-y-2 flex-1">
          <Skeleton className="h-6 w-2/3" />
          <Skeleton className="h-4 w-1/3" />
        </div>
        <Skeleton className="h-10 w-20" />
      </div>
      <TextSkeleton lines={2} />
      <div className="flex gap-3">
        <Skeleton className="h-6 w-16 rounded-full" />
        <Skeleton className="h-6 w-20 rounded-full" />
        <Skeleton className="h-6 w-12 rounded-full" />
      </div>
    </div>
  );
}

export function TableSkeleton({
  rows = 5,
  columns = 4,
  className
}: {
  rows?: number;
  columns?: number;
  className?: string;
}) {
  return (
    <div className={cn('overflow-hidden', className)}>
      <table className="w-full">
        <thead>
          <tr className="border-b">
            {Array.from({ length: columns }).map((_, i) => (
              <th key={i} className="p-3 text-left">
                <Skeleton className="h-4 w-20" />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: rows }).map((_, rowIndex) => (
            <tr key={rowIndex} className="border-b">
              {Array.from({ length: columns }).map((_, colIndex) => (
                <td key={colIndex} className="p-3">
                  <Skeleton
                    className="h-4"
                    style={{ width: `${Math.random() * 50 + 50}%` }}
                  />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function AvatarSkeleton({
  size = 'md',
  className
}: {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}) {
  const sizeClasses = {
    xs: 'h-6 w-6',
    sm: 'h-8 w-8',
    md: 'h-10 w-10',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16',
  };

  return (
    <Skeleton
      className={cn(
        'rounded-full',
        sizeClasses[size],
        className
      )}
    />
  );
}

export function ListSkeleton({
  items = 5,
  className
}: {
  items?: number;
  className?: string;
}) {
  return (
    <div className={cn('space-y-3', className)}>
      {Array.from({ length: items }).map((_, i) => (
        <div key={i} className="flex items-center space-x-3">
          <AvatarSkeleton size="sm" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-1/4" />
            <Skeleton className="h-3 w-3/4" />
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Loading spinner for buttons
 */
export function ButtonSpinner({ className }: { className?: string }) {
  return (
    <Loader2 className={cn('h-4 w-4 animate-spin', className)} />
  );
}

/**
 * Page loader for full-page loading states
 * Now uses the new AI Loader component
 */
export function PageLoader({ message = 'Loading...' }: { message?: string }) {
  return <AIPageLoader text="Loading" message={message} />;
}

/**
 * Inline loader for small loading states
 * Now uses the new AI Loader component
 */
export function InlineLoader({ className }: { className?: string }) {
  return (
    <span className={cn('inline-flex items-center', className)}>
      <AILoader text="Loading" size="sm" />
    </span>
  );
}
