import React from 'react';
import { AlertCircle, RefreshCw, Home, ArrowLeft, XCircle, WifiOff, Lock, FileX, Server } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Button } from './button';
import { cn } from '../../utils/cn';

interface ErrorStateProps {
  /** Error object or message */
  error?: Error | string;
  /** Title for the error state */
  title?: string;
  /** Description or details about the error */
  description?: string;
  /** Callback to retry the failed action */
  onRetry?: () => void;
  /** Whether to show home button */
  showHomeButton?: boolean;
  /** Whether to show back button */
  showBackButton?: boolean;
  /** Custom icon to display */
  icon?: React.ReactNode;
  /** Additional CSS classes */
  className?: string;
  /** Error type for specialized messages */
  type?: 'general' | 'network' | 'permission' | 'notFound' | 'server';
  /** Additional actions to display */
  actions?: React.ReactNode;
}

/**
 * ErrorState component for displaying error messages and recovery actions
 *
 * @example
 * <ErrorState
 *   error="Failed to load data"
 *   onRetry={handleRetry}
 *   showHomeButton
 * />
 */
export function ErrorState({
  error,
  title,
  description,
  onRetry,
  showHomeButton = false,
  showBackButton = false,
  icon,
  className,
  type = 'general',
  actions,
}: ErrorStateProps) {
  const navigate = useNavigate();
  const { t } = useTranslation();

  // Extract error message if Error object
  const errorMessage = error instanceof Error ? error.message : error;

  // Determine title based on type if not provided
  const displayTitle = title || {
    general: t('errors.general.title'),
    network: t('errors.network.title'),
    permission: t('errors.permission.title'),
    notFound: t('errors.notFound.title'),
    server: t('errors.server.title'),
  }[type];

  // Determine description based on type if not provided
  const displayDescription = description || errorMessage || {
    general: t('errors.general.description'),
    network: t('errors.network.description'),
    permission: t('errors.permission.description'),
    notFound: t('errors.notFound.description'),
    server: t('errors.server.description'),
  }[type];

  // Determine icon based on type if not provided
  const displayIcon = icon || {
    general: <AlertCircle className="h-8 w-8" />,
    network: <WifiOff className="h-8 w-8" />,
    permission: <Lock className="h-8 w-8" />,
    notFound: <FileX className="h-8 w-8" />,
    server: <Server className="h-8 w-8" />,
  }[type];

  // Icon color based on type
  const iconColorClass = {
    general: 'text-red-600 bg-red-50',
    network: 'text-amber-600 bg-amber-50',
    permission: 'text-orange-600 bg-orange-50',
    notFound: 'text-blue-600 bg-blue-50',
    server: 'text-purple-600 bg-purple-50',
  }[type];

  return (
    <div className={cn(
      'flex flex-col items-center justify-center p-8 text-center',
      className
    )}>
      {/* Icon */}
      <div className={cn(
        'mb-4 p-3 rounded-full',
        iconColorClass
      )}>
        {displayIcon}
      </div>

      {/* Title */}
      <h2 className="text-xl font-semibold mb-2 text-gray-900">
        {displayTitle}
      </h2>

      {/* Description */}
      <p className="text-academic-muted max-w-md mb-6">
        {displayDescription}
      </p>

      {/* Error details in development */}
      {process.env.NODE_ENV === 'development' && errorMessage && (
        <details className="mb-6 max-w-2xl w-full">
          <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-800">
            {t('errors.errorDetails')}
          </summary>
          <pre className="mt-2 p-3 bg-gray-100 rounded text-xs text-left overflow-auto">
            {errorMessage}
            {error instanceof Error && error.stack && (
              <>
                {'\n\n'}{t('errors.stackTrace')}:\n
                {error.stack}
              </>
            )}
          </pre>
        </details>
      )}

      {/* Actions */}
      <div className="flex flex-wrap gap-3 justify-center">
        {showBackButton && (
          <Button
            variant="outline"
            onClick={() => navigate(-1)}
            leftIcon={<ArrowLeft className="h-4 w-4" />}
          >
            {t('errors.actions.goBack')}
          </Button>
        )}

        {onRetry && (
          <Button
            onClick={onRetry}
            leftIcon={<RefreshCw className="h-4 w-4" />}
          >
            {t('errors.actions.tryAgain')}
          </Button>
        )}

        {showHomeButton && (
          <Button
            variant="outline"
            onClick={() => navigate('/')}
            leftIcon={<Home className="h-4 w-4" />}
          >
            {t('errors.actions.goHome')}
          </Button>
        )}

        {actions}
      </div>
    </div>
  );
}

/**
 * Specific error state variations
 */

export function NotFoundError({ className }: { className?: string }) {
  const { t } = useTranslation();

  return (
    <ErrorState
      type="notFound"
      title={t('errors.notFound.pageTitle')}
      description={t('errors.notFound.pageDescription')}
      showHomeButton
      showBackButton
      className={className}
    />
  );
}

export function NetworkError({
  onRetry,
  className
}: {
  onRetry?: () => void;
  className?: string;
}) {
  const { t } = useTranslation();

  return (
    <ErrorState
      type="network"
      title={t('errors.network.connectionTitle')}
      description={t('errors.network.connectionDescription')}
      onRetry={onRetry}
      className={className}
    />
  );
}

export function PermissionError({ className }: { className?: string }) {
  const navigate = useNavigate();
  const { t } = useTranslation();

  return (
    <ErrorState
      type="permission"
      title={t('errors.permission.accessTitle')}
      description={t('errors.permission.accessDescription')}
      showHomeButton
      actions={
        <Button
          variant="primary"
          onClick={() => navigate('/login')}
        >
          {t('errors.actions.logIn')}
        </Button>
      }
      className={className}
    />
  );
}

export function ServerError({
  onRetry,
  className
}: {
  onRetry?: () => void;
  className?: string;
}) {
  const { t } = useTranslation();

  return (
    <ErrorState
      type="server"
      title={t('errors.server.serverTitle')}
      description={t('errors.server.serverDescription')}
      onRetry={onRetry}
      showHomeButton
      className={className}
    />
  );
}

/**
 * Error boundary fallback component
 */
interface ErrorBoundaryFallbackProps {
  error: Error;
  resetErrorBoundary?: () => void;
}

export function ErrorBoundaryFallback({
  error,
  resetErrorBoundary
}: ErrorBoundaryFallbackProps) {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <ErrorState
          error={error}
          title={t('errors.boundary.title')}
          description={t('errors.boundary.description')}
          onRetry={resetErrorBoundary}
          showHomeButton
        />
      </div>
    </div>
  );
}

/**
 * Inline error message component
 */
interface InlineErrorProps {
  message: string;
  className?: string;
}

export function InlineError({ message, className }: InlineErrorProps) {
  return (
    <div className={cn(
      'flex items-center gap-2 text-sm text-red-600 p-3 bg-red-50 rounded-md',
      className
    )}>
      <XCircle className="h-4 w-4 flex-shrink-0" />
      <span>{message}</span>
    </div>
  );
}

/**
 * Toast error notification
 */
interface ErrorToastProps {
  title?: string;
  message: string;
  onClose?: () => void;
  className?: string;
}

export function ErrorToast({
  title,
  message,
  onClose,
  className
}: ErrorToastProps) {
  const { t } = useTranslation();
  const displayTitle = title || t('errors.toast.defaultTitle');

  return (
    <div className={cn(
      'flex items-start gap-3 p-4 bg-white border border-red-200 rounded-lg shadow-lg',
      className
    )}>
      <div className="flex-shrink-0">
        <div className="p-2 bg-red-100 rounded-full">
          <AlertCircle className="h-4 w-4 text-red-600" />
        </div>
      </div>
      <div className="flex-1">
        <h4 className="font-semibold text-gray-900">{displayTitle}</h4>
        <p className="text-sm text-gray-600 mt-1">{message}</p>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="flex-shrink-0 text-gray-400 hover:text-gray-600"
          aria-label={t('errors.toast.closeLabel')}
        >
          <XCircle className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
