import React from 'react';
import {
  Search,
  Inbox,
  FileText,
  FolderOpen,
  Users,
  MessageSquare,
  Calendar,
  BookOpen,
  Database,
  Filter,
  AlertCircle
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Button } from './button';
import { cn } from '../../utils/cn';

interface EmptyStateProps {
  /** Icon to display */
  icon?: React.ReactNode;
  /** Title for the empty state */
  title: string;
  /** Description or additional information */
  description?: string;
  /** Primary action */
  action?: {
    label: string;
    onClick: () => void;
    variant?: 'primary' | 'secondary' | 'outline';
  };
  /** Secondary action */
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
  /** Additional CSS classes */
  className?: string;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Type of empty state for specialized messages */
  type?: 'general' | 'search' | 'filter' | 'data' | 'content';
}

/**
 * EmptyState component for displaying empty content messages
 *
 * @example
 * <EmptyState
 *   icon={<Search className="h-12 w-12" />}
 *   title="No results found"
 *   description="Try adjusting your search terms"
 *   action={{ label: 'Clear search', onClick: clearSearch }}
 * />
 */
export function EmptyState({
  icon,
  title,
  description,
  action,
  secondaryAction,
  className,
  size = 'md',
  type = 'general',
}: EmptyStateProps) {
  const sizeClasses = {
    sm: {
      icon: 'h-8 w-8',
      title: 'text-base',
      description: 'text-sm',
      spacing: 'space-y-2',
      padding: 'p-6',
    },
    md: {
      icon: 'h-12 w-12',
      title: 'text-lg',
      description: 'text-sm',
      spacing: 'space-y-3',
      padding: 'p-8',
    },
    lg: {
      icon: 'h-16 w-16',
      title: 'text-xl',
      description: 'text-base',
      spacing: 'space-y-4',
      padding: 'p-12',
    },
  };

  const sizes = sizeClasses[size];

  // Default icon based on type
  const displayIcon = icon || {
    general: <Inbox className={sizes.icon} />,
    search: <Search className={sizes.icon} />,
    filter: <Filter className={sizes.icon} />,
    data: <Database className={sizes.icon} />,
    content: <FileText className={sizes.icon} />,
  }[type];

  return (
    <div className={cn(
      'flex flex-col items-center justify-center text-center',
      sizes.padding,
      sizes.spacing,
      className
    )}>
      {/* Icon */}
      {displayIcon && (
        <div className="text-academic-muted">
          {displayIcon}
        </div>
      )}

      {/* Title */}
      <h3 className={cn('font-semibold text-gray-900', sizes.title)}>
        {title}
      </h3>

      {/* Description */}
      {description && (
        <p className={cn('text-academic-muted max-w-md', sizes.description)}>
          {description}
        </p>
      )}

      {/* Actions */}
      {(action || secondaryAction) && (
        <div className="flex flex-wrap gap-3 justify-center mt-2">
          {action && (
            <Button
              variant={action.variant || 'primary'}
              onClick={action.onClick}
              size={size === 'sm' ? 'sm' : size === 'lg' ? 'lg' : 'md'}
            >
              {action.label}
            </Button>
          )}

          {secondaryAction && (
            <Button
              variant="outline"
              onClick={secondaryAction.onClick}
              size={size === 'sm' ? 'sm' : size === 'lg' ? 'lg' : 'md'}
            >
              {secondaryAction.label}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Specific empty state variations
 */

export function NoSearchResults({
  query,
  onClear,
  className
}: {
  query?: string;
  onClear?: () => void;
  className?: string;
}) {
  const { t } = useTranslation();

  return (
    <EmptyState
      type="search"
      icon={
        <div className="relative">
          <Search className="h-12 w-12 text-gray-400" />
          <div className="absolute -bottom-1 -right-1 h-5 w-5 bg-red-100 rounded-full flex items-center justify-center">
            <span className="text-red-600 text-xs font-bold">0</span>
          </div>
        </div>
      }
      title={t('empty.noResults.title')}
      description={
        query
          ? t('empty.noResults.withQuery', { query })
          : t('empty.noResults.withoutQuery')
      }
      action={
        onClear
          ? { label: t('empty.actions.clearSearch'), onClick: onClear, variant: 'outline' }
          : undefined
      }
      className={className}
    />
  );
}

export function NoDataYet({
  entity = 'items',
  onCreate,
  className
}: {
  entity?: string;
  onCreate?: () => void;
  className?: string;
}) {
  const { t } = useTranslation();

  return (
    <EmptyState
      type="data"
      title={t('empty.noData.title', { entity })}
      description={t('empty.noData.description', { entity })}
      action={
        onCreate
          ? { label: t('empty.actions.addEntity', { entity }), onClick: onCreate }
          : undefined
      }
      className={className}
    />
  );
}

export function EmptyInbox({ className }: { className?: string }) {
  const { t } = useTranslation();

  return (
    <EmptyState
      icon={<Inbox className="h-12 w-12" />}
      title={t('empty.inbox.title')}
      description={t('empty.inbox.description')}
      className={className}
    />
  );
}

export function NoContent({
  type = 'content',
  onAdd,
  className
}: {
  type?: string;
  onAdd?: () => void;
  className?: string;
}) {
  const { t } = useTranslation();

  return (
    <EmptyState
      icon={<FileText className="h-12 w-12" />}
      title={t('empty.noContent.title', { type })}
      description={t('empty.noContent.description', { type })}
      action={
        onAdd
          ? { label: t('empty.actions.addType', { type }), onClick: onAdd }
          : undefined
      }
      className={className}
    />
  );
}

export function EmptyFolder({
  folderName,
  onUpload,
  className
}: {
  folderName?: string;
  onUpload?: () => void;
  className?: string;
}) {
  const { t } = useTranslation();

  return (
    <EmptyState
      icon={<FolderOpen className="h-12 w-12" />}
      title={folderName ? t('empty.folder.titleWithName', { folderName }) : t('empty.folder.titleDefault')}
      description={t('empty.folder.description')}
      action={
        onUpload
          ? { label: t('empty.actions.uploadFiles'), onClick: onUpload }
          : undefined
      }
      className={className}
    />
  );
}

export function NoMembers({
  onInvite,
  className
}: {
  onInvite?: () => void;
  className?: string;
}) {
  const { t } = useTranslation();

  return (
    <EmptyState
      icon={<Users className="h-12 w-12" />}
      title={t('empty.members.title')}
      description={t('empty.members.description')}
      action={
        onInvite
          ? { label: t('empty.actions.inviteMembers'), onClick: onInvite }
          : undefined
      }
      className={className}
    />
  );
}

export function NoComments({
  onComment,
  className
}: {
  onComment?: () => void;
  className?: string;
}) {
  const { t } = useTranslation();

  return (
    <EmptyState
      icon={<MessageSquare className="h-12 w-12" />}
      title={t('empty.comments.title')}
      description={t('empty.comments.description')}
      action={
        onComment
          ? { label: t('empty.actions.addComment'), onClick: onComment, variant: 'outline' }
          : undefined
      }
      className={className}
    />
  );
}

export function NoEvents({
  onCreate,
  className
}: {
  onCreate?: () => void;
  className?: string;
}) {
  const { t } = useTranslation();

  return (
    <EmptyState
      icon={<Calendar className="h-12 w-12" />}
      title={t('empty.events.title')}
      description={t('empty.events.description')}
      action={
        onCreate
          ? { label: t('empty.actions.createEvent'), onClick: onCreate }
          : undefined
      }
      className={className}
    />
  );
}

/**
 * Academic specific empty states for EleutherIA
 */

export function NoTexts({
  onExplore,
  className
}: {
  onExplore?: () => void;
  className?: string;
}) {
  const { t } = useTranslation();

  return (
    <EmptyState
      icon={<BookOpen className="h-12 w-12" />}
      title={t('empty.texts.title')}
      description={t('empty.texts.description')}
      action={
        onExplore
          ? { label: t('empty.actions.exploreTexts'), onClick: onExplore, variant: 'outline' }
          : undefined
      }
      className={className}
    />
  );
}

export function NoPhilosophers({
  period,
  onClear,
  className
}: {
  period?: string;
  onClear?: () => void;
  className?: string;
}) {
  const { t } = useTranslation();

  return (
    <EmptyState
      icon={
        <div className="relative">
          <Users className="h-12 w-12 text-gray-400" />
          <BookOpen className="h-6 w-6 absolute -bottom-1 -right-1 text-gray-500" />
        </div>
      }
      title={t('empty.philosophers.title')}
      description={
        period
          ? t('empty.philosophers.withPeriod', { period })
          : t('empty.philosophers.withoutPeriod')
      }
      action={
        onClear
          ? { label: t('empty.actions.clearFilters'), onClick: onClear, variant: 'outline' }
          : undefined
      }
      className={className}
    />
  );
}

export function NoCitations({
  onSearch,
  className
}: {
  onSearch?: () => void;
  className?: string;
}) {
  const { t } = useTranslation();

  return (
    <EmptyState
      icon={
        <div className="relative">
          <FileText className="h-12 w-12 text-gray-400" />
          <Search className="h-5 w-5 absolute -bottom-1 -right-1 text-gray-500" />
        </div>
      }
      title={t('empty.citations.title')}
      description={t('empty.citations.description')}
      action={
        onSearch
          ? { label: t('empty.actions.searchTexts'), onClick: onSearch, variant: 'outline' }
          : undefined
      }
      className={className}
    />
  );
}

/**
 * Error state component
 */
interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title,
  message,
  onRetry,
  className,
}: ErrorStateProps) {
  const { t } = useTranslation();
  const displayTitle = title || t('errors.general.title');
  const displayMessage = message || t('errors.general.description');

  return (
    <EmptyState
      icon={
        <div className="text-red-500">
          <AlertCircle className="h-12 w-12" />
        </div>
      }
      title={displayTitle}
      description={displayMessage}
      action={
        onRetry
          ? { label: t('errors.actions.tryAgain'), onClick: onRetry, variant: 'primary' }
          : undefined
      }
      className={className}
    />
  );
}

/**
 * Inline empty message for smaller contexts
 */
interface InlineEmptyProps {
  message: string;
  className?: string;
}

export function InlineEmpty({ message, className }: InlineEmptyProps) {
  return (
    <div className={cn(
      'text-center text-sm text-academic-muted py-8',
      className
    )}>
      {message}
    </div>
  );
}
