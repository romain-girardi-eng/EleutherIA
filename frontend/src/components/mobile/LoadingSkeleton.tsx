/**
 * LoadingSkeleton Component
 * Provides placeholder loading states for better UX
 * Part of EleutherIA mobile UI redesign - Week 3 Performance
 */

import type { ReactNode } from 'react';

interface LoadingSkeletonProps {
  /** Type of skeleton to display */
  variant?: 'text' | 'title' | 'card' | 'graph' | 'timeline' | 'matrix';

  /** Number of items to repeat (for lists) */
  count?: number;

  /** Custom className */
  className?: string;

  /** Show animation */
  animate?: boolean;
}

export default function LoadingSkeleton({
  variant = 'text',
  count = 1,
  className = '',
  animate = true
}: LoadingSkeletonProps) {
  const baseClasses = `bg-gray-200 rounded ${animate ? 'animate-pulse' : ''}`;

  const renderSkeleton = () => {
    switch (variant) {
      case 'title':
        return <div className={`${baseClasses} h-8 w-2/3 ${className}`} />;

      case 'text':
        return <div className={`${baseClasses} h-4 w-full ${className}`} />;

      case 'card':
        return (
          <div className={`academic-card ${className}`}>
            <div className="space-y-3">
              <div className={`${baseClasses} h-6 w-1/3`} />
              <div className={`${baseClasses} h-4 w-full`} />
              <div className={`${baseClasses} h-4 w-5/6`} />
              <div className={`${baseClasses} h-4 w-4/6`} />
            </div>
          </div>
        );

      case 'graph':
        return (
          <div className={`academic-card ${className}`}>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className={`${baseClasses} h-6 w-1/4`} />
                <div className={`${baseClasses} h-8 w-20`} />
              </div>
              <div className={`${baseClasses} h-[500px] md:h-[780px] w-full rounded-lg`} />
            </div>
          </div>
        );

      case 'timeline':
        return (
          <div className={`academic-card ${className}`}>
            <div className={`${baseClasses} h-6 w-1/3 mb-4`} />
            <div className="flex gap-4 overflow-hidden">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="flex-shrink-0 w-[220px]">
                  <div className={`${baseClasses} h-32 rounded-lg`} />
                </div>
              ))}
            </div>
          </div>
        );

      case 'matrix':
        return (
          <div className={`academic-card ${className}`}>
            <div className={`${baseClasses} h-6 w-1/3 mb-4`} />
            <div className="grid grid-cols-4 gap-2">
              {[...Array(16)].map((_, i) => (
                <div key={i} className={`${baseClasses} h-12 rounded`} />
              ))}
            </div>
          </div>
        );

      default:
        return <div className={`${baseClasses} h-4 w-full ${className}`} />;
    }
  };

  if (count === 1) {
    return renderSkeleton();
  }

  return (
    <>
      {[...Array(count)].map((_, index) => (
        <div key={index} className="mb-3 last:mb-0">
          {renderSkeleton()}
        </div>
      ))}
    </>
  );
}

/**
 * SkeletonGroup Component
 * Wrapper for multiple skeleton items
 */
interface SkeletonGroupProps {
  children: ReactNode;
  className?: string;
}

export function SkeletonGroup({ children, className = '' }: SkeletonGroupProps) {
  return (
    <div className={`space-y-4 ${className}`}>
      {children}
    </div>
  );
}

/**
 * InlineLoadingSkeleton Component
 * Small inline loading indicator for buttons and actions
 */
interface InlineLoadingSkeletonProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function InlineLoadingSkeleton({ size = 'md', className = '' }: InlineLoadingSkeletonProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  return (
    <div className={`inline-block ${sizeClasses[size]} ${className}`}>
      <div className="w-full h-full border-2 border-gray-300 border-t-primary-600 rounded-full animate-spin" />
    </div>
  );
}

/**
 * PanelSkeleton Component
 * Skeleton for accordion panels
 */
export function PanelSkeleton({ className = '' }: { className?: string }) {
  return (
    <div className={`academic-card ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="bg-gray-200 rounded h-5 w-5 animate-pulse" />
          <div className="bg-gray-200 rounded h-6 w-32 animate-pulse" />
        </div>
        <div className="bg-gray-200 rounded h-5 w-5 animate-pulse" />
      </div>
    </div>
  );
}
