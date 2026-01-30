/**
 * FilterDrawer Component
 * Bottom slide-in drawer for mobile filter access
 * Part of EleutherIA mobile UI redesign - Week 2 Interactive Controls
 */

import { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import WorkspaceFilterBar from '../workspace/WorkspaceFilterBar';
import { useHapticFeedback } from '../../hooks/useTouchOptimizations';

interface FilterDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function FilterDrawer({ isOpen, onClose }: FilterDrawerProps) {
  const drawerRef = useRef<HTMLDivElement>(null);
  const startY = useRef<number>(0);
  const currentY = useRef<number>(0);
  const { triggerHaptic } = useHapticFeedback();

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      // Prevent body scroll when drawer is open
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  // Touch handling for drag-to-close
  const handleTouchStart = (e: React.TouchEvent) => {
    startY.current = e.touches[0].clientY;
    currentY.current = startY.current;
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    currentY.current = e.touches[0].clientY;
    const deltaY = currentY.current - startY.current;

    // Only allow dragging down
    if (deltaY > 0 && drawerRef.current) {
      drawerRef.current.style.transform = `translateY(${deltaY}px)`;
    }
  };

  const handleTouchEnd = () => {
    const deltaY = currentY.current - startY.current;

    if (drawerRef.current) {
      drawerRef.current.style.transform = '';
    }

    // Close if dragged down more than 100px
    if (deltaY > 100) {
      triggerHaptic('medium');
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-40 md:hidden transition-opacity duration-300"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div
        ref={drawerRef}
        className="fixed bottom-0 left-0 right-0 bg-white rounded-t-2xl shadow-2xl z-50 md:hidden max-h-[85vh] overflow-hidden flex flex-col transition-transform duration-300"
        style={{
          animation: isOpen ? 'slideUp 300ms ease-out' : 'slideDown 300ms ease-in',
        }}
        role="dialog"
        aria-modal="true"
        aria-labelledby="filter-drawer-title"
      >
        {/* Drag Handle */}
        <div
          className="w-full pt-3 pb-2 flex justify-center cursor-grab active:cursor-grabbing"
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
        >
          <div className="w-12 h-1.5 bg-gray-300 rounded-full" aria-hidden="true" />
        </div>

        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
          <h2 id="filter-drawer-title" className="text-lg font-semibold text-academic-text">
            Filters
          </h2>
          <button
            onClick={() => {
              triggerHaptic('light');
              onClose();
            }}
            className="p-2 -mr-2 text-gray-500 hover:text-gray-700 active:bg-gray-100 rounded-full transition-colors"
            aria-label="Close filters"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content - Scrollable */}
        <div className="flex-1 overflow-y-auto overscroll-contain px-4 py-4">
          <WorkspaceFilterBar />
        </div>

        {/* Footer - Apply button */}
        <div className="px-4 py-3 border-t border-gray-200 bg-gray-50">
          <button
            onClick={() => {
              triggerHaptic('success');
              onClose();
            }}
            className="w-full py-3 px-4 bg-primary-600 hover:bg-primary-700 active:bg-primary-800 text-white font-semibold rounded-lg transition-colors shadow-sm active:scale-98"
          >
            Apply Filters
          </button>
        </div>
      </div>

      {/* Animations */}
      <style>{`
        @keyframes slideUp {
          from {
            transform: translateY(100%);
          }
          to {
            transform: translateY(0);
          }
        }

        @keyframes slideDown {
          from {
            transform: translateY(0);
          }
          to {
            transform: translateY(100%);
          }
        }

        .active\\:scale-98:active {
          transform: scale(0.98);
        }
      `}</style>
    </>
  );
}
