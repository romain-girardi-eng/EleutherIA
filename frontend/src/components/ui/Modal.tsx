import React, { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { cn } from '../../utils/cn';
import { trapFocus, restoreFocus, lockBodyScroll, announce } from '../../utils/focus';
import { Button } from './button';

interface ModalProps {
  /** Whether the modal is open */
  isOpen: boolean;
  /** Callback when the modal should close */
  onClose: () => void;
  /** Modal title */
  title?: string;
  /** Modal description */
  description?: string;
  /** Modal content */
  children: React.ReactNode;
  /** Additional CSS classes */
  className?: string;
  /** Size of the modal */
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  /** Whether clicking outside closes the modal */
  closeOnOutsideClick?: boolean;
  /** Whether pressing Escape closes the modal */
  closeOnEscape?: boolean;
  /** Whether to show the close button */
  showCloseButton?: boolean;
  /** Footer content */
  footer?: React.ReactNode;
  /** Whether to center the modal vertically */
  centered?: boolean;
  /** Custom z-index */
  zIndex?: number;
  /** Whether to disable focus trap */
  disableFocusTrap?: boolean;
  /** Whether to disable body scroll lock */
  disableScrollLock?: boolean;
  /** Animation variant */
  animation?: 'fade' | 'scale' | 'slide' | 'none';
  /** Custom close button */
  closeButton?: React.ReactNode;
  /** ARIA label for the modal */
  ariaLabel?: string;
  /** ARIA labelledby ID */
  ariaLabelledBy?: string;
  /** ARIA describedby ID */
  ariaDescribedBy?: string;
}

/**
 * Modal component with accessibility features
 *
 * @example
 * <Modal
 *   isOpen={isOpen}
 *   onClose={handleClose}
 *   title="Confirm Action"
 *   description="Are you sure you want to proceed?"
 * >
 *   <p>This action cannot be undone.</p>
 * </Modal>
 */
export function Modal({
  isOpen,
  onClose,
  title,
  description,
  children,
  className,
  size = 'md',
  closeOnOutsideClick = true,
  closeOnEscape = true,
  showCloseButton = true,
  footer,
  centered = true,
  zIndex = 1030,
  disableFocusTrap = false,
  disableScrollLock = false,
  animation = 'scale',
  closeButton,
  ariaLabel,
  ariaLabelledBy,
  ariaDescribedBy,
}: ModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);

  // Size classes
  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    full: 'max-w-[90vw] w-full',
  };

  // Animation variants
  const animationVariants = {
    fade: {
      initial: { opacity: 0 },
      animate: { opacity: 1 },
      exit: { opacity: 0 },
    },
    scale: {
      initial: { opacity: 0, scale: 0.95 },
      animate: { opacity: 1, scale: 1 },
      exit: { opacity: 0, scale: 0.95 },
    },
    slide: {
      initial: { opacity: 0, y: 20 },
      animate: { opacity: 1, y: 0 },
      exit: { opacity: 0, y: 20 },
    },
    none: {
      initial: {},
      animate: {},
      exit: {},
    },
  };

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
      if (!disableFocusTrap && modalRef.current) {
        // Delay focus trap to allow animation
        const timeoutId = setTimeout(() => {
          if (modalRef.current) {
            cleanupFocus = trapFocus(modalRef.current);
          }
        }, 100);

        return () => {
          clearTimeout(timeoutId);
          cleanupFocus?.();
          unlockScroll?.();
        };
      }

      // Announce modal opening to screen readers
      announce(`${title || 'Modal'} opened`, 'assertive');

      return () => {
        unlockScroll?.();
      };
    } else {
      // Restore focus when closing
      restoreFocus(previousActiveElement.current);

      // Announce modal closing
      announce('Modal closed', 'assertive');
    }
  }, [isOpen, disableFocusTrap, disableScrollLock, title]);

  // Handle Escape key
  useEffect(() => {
    if (!isOpen || !closeOnEscape) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose, closeOnEscape]);

  const modalContent = (
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

          {/* Modal container */}
          <div
            className={cn(
              'fixed inset-0 flex p-4',
              centered ? 'items-center' : 'items-start pt-20',
              'justify-center overflow-y-auto'
            )}
            style={{ zIndex: zIndex + 1 }}
          >
            <motion.div
              ref={modalRef}
              {...animationVariants[animation]}
              transition={{ duration: 0.2 }}
              role="dialog"
              aria-modal="true"
              aria-label={ariaLabel}
              aria-labelledby={ariaLabelledBy || (title ? 'modal-title' : undefined)}
              aria-describedby={ariaDescribedBy || (description ? 'modal-description' : undefined)}
              className={cn(
                'bg-white rounded-lg shadow-xl w-full max-h-[90vh] overflow-hidden flex flex-col',
                sizeClasses[size],
                className
              )}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              {(title || showCloseButton) && (
                <div className="flex items-start justify-between px-6 py-4 border-b">
                  <div>
                    {title && (
                      <h2 id="modal-title" className="text-xl font-semibold">
                        {title}
                      </h2>
                    )}
                    {description && (
                      <p id="modal-description" className="text-sm text-gray-600 mt-1">
                        {description}
                      </p>
                    )}
                  </div>
                  {showCloseButton && (
                    closeButton || (
                      <button
                        onClick={onClose}
                        className="ml-4 p-2 rounded-full hover:bg-gray-100 transition-colors"
                        aria-label="Close modal"
                      >
                        <X className="h-5 w-5" />
                      </button>
                    )
                  )}
                </div>
              )}

              {/* Content */}
              <div className="flex-1 px-6 py-4 overflow-y-auto">
                {children}
              </div>

              {/* Footer */}
              {footer && (
                <div className="px-6 py-4 border-t">
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
  return createPortal(modalContent, document.body);
}

/**
 * Modal header component
 */
interface ModalHeaderProps {
  title: string;
  description?: string;
  onClose?: () => void;
  className?: string;
}

export function ModalHeader({
  title,
  description,
  onClose,
  className
}: ModalHeaderProps) {
  return (
    <div className={cn('flex items-start justify-between pb-4', className)}>
      <div>
        <h2 className="text-xl font-semibold">{title}</h2>
        {description && (
          <p className="text-sm text-gray-600 mt-1">{description}</p>
        )}
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="ml-4 p-2 rounded-full hover:bg-gray-100 transition-colors"
          aria-label="Close"
        >
          <X className="h-5 w-5" />
        </button>
      )}
    </div>
  );
}

/**
 * Modal body component
 */
interface ModalBodyProps {
  children: React.ReactNode;
  className?: string;
}

export function ModalBody({ children, className }: ModalBodyProps) {
  return (
    <div className={cn('py-4', className)}>
      {children}
    </div>
  );
}

/**
 * Modal footer component
 */
interface ModalFooterProps {
  children: React.ReactNode;
  className?: string;
  align?: 'left' | 'center' | 'right' | 'between';
}

export function ModalFooter({
  children,
  className,
  align = 'right'
}: ModalFooterProps) {
  const alignClasses = {
    left: 'justify-start',
    center: 'justify-center',
    right: 'justify-end',
    between: 'justify-between',
  };

  return (
    <div className={cn('flex gap-3 pt-4', alignClasses[align], className)}>
      {children}
    </div>
  );
}

/**
 * Confirm Modal - Pre-configured modal for confirmations
 */
interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'warning' | 'info';
  loading?: boolean;
}

export function ConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'danger',
  loading = false
}: ConfirmModalProps) {
  const variantColors = {
    danger: 'danger',
    warning: 'warning',
    info: 'primary',
  } as const;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      size="sm"
      footer={
        <ModalFooter>
          <Button
            variant="outline"
            onClick={onClose}
            disabled={loading}
          >
            {cancelLabel}
          </Button>
          <Button
            variant={variantColors[variant]}
            onClick={() => {
              onConfirm();
              onClose();
            }}
            loading={loading}
          >
            {confirmLabel}
          </Button>
        </ModalFooter>
      }
    >
      <p className="text-gray-600">{message}</p>
    </Modal>
  );
}

/**
 * Alert Modal - Simple alert dialog
 */
interface AlertModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  message: string;
  buttonLabel?: string;
}

export function AlertModal({
  isOpen,
  onClose,
  title,
  message,
  buttonLabel = 'OK'
}: AlertModalProps) {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      size="sm"
      showCloseButton={false}
      closeOnOutsideClick={false}
      footer={
        <ModalFooter align="center">
          <Button onClick={onClose}>
            {buttonLabel}
          </Button>
        </ModalFooter>
      }
    >
      <p className="text-center text-gray-600">{message}</p>
    </Modal>
  );
}

/**
 * Form Modal - Modal with form layout
 */
interface FormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: Record<string, unknown>) => void;
  title: string;
  children: React.ReactNode;
  submitLabel?: string;
  cancelLabel?: string;
  loading?: boolean;
}

export function FormModal({
  isOpen,
  onClose,
  onSubmit,
  title,
  children,
  submitLabel = 'Submit',
  cancelLabel = 'Cancel',
  loading = false
}: FormModalProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const formData = new FormData(e.target as HTMLFormElement);
    const data = Object.fromEntries(formData);
    onSubmit(data);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      footer={
        <ModalFooter>
          <Button
            variant="outline"
            onClick={onClose}
            disabled={loading}
          >
            {cancelLabel}
          </Button>
          <Button
            type="submit"
            form="modal-form"
            loading={loading}
          >
            {submitLabel}
          </Button>
        </ModalFooter>
      }
    >
      <form id="modal-form" onSubmit={handleSubmit}>
        {children}
      </form>
    </Modal>
  );
}
