import React, { useEffect, useRef, useState, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence, useAnimation } from 'framer-motion';
import type { PanInfo } from 'framer-motion';
import { X } from 'lucide-react';
import { cn } from '../../utils/cn';
import { trapFocus, restoreFocus, lockBodyScroll } from '../../utils/focus';
import { Button } from './button';

interface BottomSheetProps {
  /** Whether the bottom sheet is open */
  isOpen: boolean;
  /** Callback when the sheet should close */
  onClose: () => void;
  /** Title for the bottom sheet */
  title?: string;
  /** Description text */
  description?: string;
  /** Content to display in the sheet */
  children: React.ReactNode;
  /** Additional CSS classes */
  className?: string;
  /** Height preset or custom value */
  height?: 'auto' | 'full' | 'half' | '75%' | string;
  /** Whether to show the drag handle */
  showHandle?: boolean;
  /** Whether clicking outside closes the sheet */
  closeOnOutsideClick?: boolean;
  /** Whether to show close button */
  showCloseButton?: boolean;
  /** Custom close button content */
  closeButton?: React.ReactNode;
  /** Whether to allow drag to dismiss */
  dragToClose?: boolean;
  /** Snap points for the sheet (percentages) */
  snapPoints?: number[];
  /** Initial snap point index */
  initialSnapPoint?: number;
  /** Footer content */
  footer?: React.ReactNode;
  /** Whether to disable focus trap */
  disableFocusTrap?: boolean;
  /** Whether to disable body scroll lock */
  disableScrollLock?: boolean;
  /** Z-index for the sheet */
  zIndex?: number;
}

/**
 * BottomSheet component for mobile-optimized interactions
 *
 * @example
 * <BottomSheet
 *   isOpen={isOpen}
 *   onClose={handleClose}
 *   title="Settings"
 *   height="half"
 * >
 *   <SettingsContent />
 * </BottomSheet>
 */
export function BottomSheet({
  isOpen,
  onClose,
  title,
  description,
  children,
  className,
  height = 'auto',
  showHandle = true,
  closeOnOutsideClick = true,
  showCloseButton = true,
  closeButton,
  dragToClose = true,
  snapPoints = [],
  initialSnapPoint = 0,
  footer,
  disableFocusTrap = false,
  disableScrollLock = false,
  zIndex = 1040,
}: BottomSheetProps) {
  const sheetRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);
  const controls = useAnimation();
  const [currentSnapIndex, setCurrentSnapIndex] = useState(initialSnapPoint);
  const dragConstraintsRef = useRef<HTMLDivElement>(null);

  // Calculate height based on prop
  const getHeight = () => {
    if (height === 'auto') return 'auto';
    if (height === 'full') return '90vh';
    if (height === 'half') return '50vh';
    if (height === '75%') return '75vh';
    return height;
  };

  // Calculate snap point positions
  const getSnapPosition = useCallback((index: number) => {
    if (snapPoints.length === 0) return 0;
    const snapPercentage = snapPoints[Math.min(index, snapPoints.length - 1)];
    return `${100 - snapPercentage}%`;
  }, [snapPoints]);

  // Initialize controls
  useEffect(() => {
    if (isOpen) {
      // Ensure starting position is set before animating (controls state may be
      // uninitialized, causing Framer Motion to see no delta and skip the animation)
      controls.set({ y: '100%' });
      controls.start({ y: snapPoints.length > 0 ? getSnapPosition(currentSnapIndex) : 0 });
    }
  }, [isOpen, currentSnapIndex, snapPoints.length, controls, getSnapPosition]);

  useEffect(() => {
    if (isOpen) {
      previousActiveElement.current = document.activeElement as HTMLElement;

      // Lock body scroll
      let unlockScroll: (() => void) | undefined;
      if (!disableScrollLock) {
        unlockScroll = lockBodyScroll();
      }

      // Set up focus trap
      let cleanupFocus: (() => void) | undefined;
      if (!disableFocusTrap && sheetRef.current) {
        // Delay focus trap to allow animation to start
        const timeoutId = setTimeout(() => {
          if (sheetRef.current) {
            cleanupFocus = trapFocus(sheetRef.current);
          }
        }, 100);

        return () => {
          clearTimeout(timeoutId);
          cleanupFocus?.();
          unlockScroll?.();
        };
      }

      return () => {
        unlockScroll?.();
      };
    } else {
      // Restore focus when closing
      restoreFocus(previousActiveElement.current);
    }
  }, [isOpen, disableFocusTrap, disableScrollLock]);

  // Handle keyboard events
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Handle drag end
  const handleDragEnd = (_event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    if (!dragToClose) return;

    const shouldClose = info.velocity.y > 20 || (info.velocity.y >= 0 && info.offset.y > 100);

    if (shouldClose) {
      onClose();
    } else if (snapPoints.length > 0) {
      // Snap to nearest point
      const draggedPercentage = (info.offset.y / window.innerHeight) * 100;
      let nearestSnapIndex = 0;
      let minDistance = Infinity;

      snapPoints.forEach((point, index) => {
        const distance = Math.abs(draggedPercentage - (100 - point));
        if (distance < minDistance) {
          minDistance = distance;
          nearestSnapIndex = index;
        }
      });

      setCurrentSnapIndex(nearestSnapIndex);
      controls.start({ y: getSnapPosition(nearestSnapIndex) });
    } else {
      // Return to original position
      controls.start({ y: 0 });
    }
  };

  const sheet = (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-black/50"
            style={{ zIndex }}
            onClick={closeOnOutsideClick ? onClose : undefined}
            aria-hidden="true"
          />

          {/* Sheet container for drag constraints */}
          <div
            ref={dragConstraintsRef}
            className="fixed inset-x-0 bottom-0"
            style={{ zIndex: zIndex + 1, height: '100vh' }}
          >
            {/* Sheet */}
            <motion.div
              ref={sheetRef}
              initial={{ y: '100%' }}
              animate={controls}
              exit={{ y: '100%' }}
              transition={{
                type: 'spring',
                damping: 30,
                stiffness: 300,
              }}
              drag={dragToClose ? 'y' : false}
              dragConstraints={dragConstraintsRef}
              dragElastic={{ top: 0, bottom: 0.5 }}
              onDragEnd={handleDragEnd}
              className={cn(
                'absolute bottom-0 left-0 right-0 bg-white rounded-t-2xl shadow-2xl overflow-hidden',
                'flex flex-col',
                className
              )}
              style={{
                maxHeight: getHeight(),
                height: height === 'auto' ? 'auto' : getHeight(),
              }}
              role="dialog"
              aria-modal="true"
              aria-labelledby={title ? 'bottom-sheet-title' : undefined}
              aria-describedby={description ? 'bottom-sheet-description' : undefined}
            >
              {/* Drag handle */}
              {showHandle && (
                <div className="flex justify-center py-3 cursor-grab active:cursor-grabbing">
                  <div className="w-12 h-1.5 bg-gray-300 rounded-full" />
                </div>
              )}

              {/* Header */}
              {(title || showCloseButton) && (
                <div className="flex items-center justify-between px-6 py-4 border-b">
                  <div>
                    {title && (
                      <h2 id="bottom-sheet-title" className="text-lg font-semibold">
                        {title}
                      </h2>
                    )}
                    {description && (
                      <p id="bottom-sheet-description" className="text-sm text-gray-600 mt-1">
                        {description}
                      </p>
                    )}
                  </div>
                  {showCloseButton && (
                    closeButton || (
                      <button
                        onClick={onClose}
                        className="p-2 rounded-full hover:bg-gray-100 transition-colors"
                        aria-label="Close bottom sheet"
                      >
                        <X className="h-5 w-5" />
                      </button>
                    )
                  )}
                </div>
              )}

              {/* Content */}
              <div className="flex-1 overflow-y-auto overscroll-contain px-6 py-4">
                {children}
              </div>

              {/* Footer */}
              {footer && (
                <div className="border-t px-6 py-4">
                  {footer}
                </div>
              )}
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );

  // Portal to body
  if (typeof document === 'undefined') return null;
  return createPortal(sheet, document.body);
}

/**
 * BottomSheetHeader component for consistent header styling
 */
interface BottomSheetHeaderProps {
  title: string;
  description?: string;
  onClose?: () => void;
  className?: string;
}

export function BottomSheetHeader({
  title,
  description,
  onClose,
  className
}: BottomSheetHeaderProps) {
  return (
    <div className={cn('flex items-center justify-between pb-4', className)}>
      <div>
        <h3 className="text-lg font-semibold">{title}</h3>
        {description && (
          <p className="text-sm text-gray-600 mt-1">{description}</p>
        )}
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="p-2 rounded-full hover:bg-gray-100 transition-colors"
          aria-label="Close"
        >
          <X className="h-5 w-5" />
        </button>
      )}
    </div>
  );
}

/**
 * BottomSheetFooter component for action buttons
 */
interface BottomSheetFooterProps {
  children: React.ReactNode;
  className?: string;
}

export function BottomSheetFooter({ children, className }: BottomSheetFooterProps) {
  return (
    <div className={cn('flex gap-3 pt-4', className)}>
      {children}
    </div>
  );
}

/**
 * SimpleBottomSheet - A simpler bottom sheet without drag functionality
 */
interface SimpleBottomSheetProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export function SimpleBottomSheet({
  isOpen,
  onClose,
  title,
  children,
  className
}: SimpleBottomSheetProps) {
  return (
    <BottomSheet
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      height="auto"
      showHandle={false}
      dragToClose={false}
      className={className}
    >
      {children}
    </BottomSheet>
  );
}

/**
 * ActionSheet - iOS-style action sheet
 */
interface ActionSheetOption {
  label: string;
  onClick: () => void;
  variant?: 'default' | 'danger';
  icon?: React.ReactNode;
}

interface ActionSheetProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  message?: string;
  options: ActionSheetOption[];
  cancelLabel?: string;
}

export function ActionSheet({
  isOpen,
  onClose,
  title,
  message,
  options,
  cancelLabel = 'Cancel'
}: ActionSheetProps) {
  return (
    <BottomSheet
      isOpen={isOpen}
      onClose={onClose}
      height="auto"
      showHandle
      showCloseButton={false}
    >
      {(title || message) && (
        <div className="text-center pb-4">
          {title && <h3 className="font-semibold">{title}</h3>}
          {message && <p className="text-sm text-gray-600 mt-1">{message}</p>}
        </div>
      )}

      <div className="space-y-2">
        {options.map((option, index) => (
          <button
            key={index}
            onClick={() => {
              option.onClick();
              onClose();
            }}
            className={cn(
              'w-full p-4 rounded-lg text-left flex items-center gap-3 transition-colors',
              option.variant === 'danger'
                ? 'text-red-600 hover:bg-red-50'
                : 'hover:bg-gray-50'
            )}
          >
            {option.icon && <span>{option.icon}</span>}
            <span className="font-medium">{option.label}</span>
          </button>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t">
        <Button
          variant="outline"
          fullWidth
          onClick={onClose}
        >
          {cancelLabel}
        </Button>
      </div>
    </BottomSheet>
  );
}
