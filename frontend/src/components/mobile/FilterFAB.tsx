/**
 * FilterFAB Component
 * Floating Action Button for mobile filter access
 * Part of EleutherIA mobile UI redesign - Week 1 Foundation
 */

import { Filter } from 'lucide-react';
import { useHapticFeedback } from '../../hooks/useTouchOptimizations';

interface FilterFABProps {
  onClick: () => void;
  activeCount: number;
  className?: string;
}

export default function FilterFAB({ onClick, activeCount, className = '' }: FilterFABProps) {
  const hasActiveFilters = activeCount > 0;
  const { triggerHaptic } = useHapticFeedback();

  const handleClick = () => {
    triggerHaptic('medium');
    onClick();
  };

  return (
    <button
      onClick={handleClick}
      className={`fixed bottom-20 right-4 w-14 h-14 bg-primary-600 hover:bg-primary-700 active:bg-primary-800 text-white rounded-full shadow-lg hover:shadow-xl flex items-center justify-center md:hidden z-40 transition-all duration-200 active:scale-95 focus:outline-none focus-visible:ring-4 focus-visible:ring-primary-300 ${hasActiveFilters ? 'animate-pulse' : ''} ${className}`}
      aria-label={`Open filters${hasActiveFilters ? ` (${activeCount} active)` : ''}`}
      type="button"
    >
      <Filter className="w-6 h-6" aria-hidden="true" />

      {hasActiveFilters && (
        <span
          className="absolute -top-1 -right-1 min-w-[20px] h-5 px-1.5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center shadow-md"
          aria-label={`${activeCount} filters active`}
        >
          {activeCount > 9 ? '9+' : activeCount}
        </span>
      )}
    </button>
  );
}

export function FilterFABPlaceholder() {
  return <div className="h-20 md:hidden" aria-hidden="true" />;
}
