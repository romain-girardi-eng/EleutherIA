import React from 'react';
import { cn } from '../../utils/cn';

interface SkipLink {
  /** Target element ID to skip to */
  target: string;
  /** Label for the skip link */
  label: string;
  /** Optional keyboard shortcut */
  shortcut?: string;
}

interface SkipLinksProps {
  /** Array of skip links */
  links?: SkipLink[];
  /** Additional CSS classes */
  className?: string;
  /** Position of the skip links container */
  position?: 'top' | 'left';
  /** Z-index for the skip links */
  zIndex?: number;
  /** Targets intentionally absent from this page shell */
  excludeTargets?: string[];
}

/**
 * Default skip links for common page sections
 */
const defaultLinks: SkipLink[] = [
  { target: 'main-content', label: 'Skip to main content', shortcut: '1' },
  { target: 'navigation', label: 'Skip to navigation', shortcut: '2' },
  { target: 'search', label: 'Skip to search', shortcut: '3' },
  { target: 'footer', label: 'Skip to footer', shortcut: '4' },
];
const noExcludedTargets: string[] = [];

/**
 * SkipLinks component for accessibility navigation
 * Provides keyboard-accessible links to jump to page sections
 *
 * @example
 * <SkipLinks />
 *
 * @example
 * // With custom links
 * <SkipLinks
 *   links={[
 *     { target: 'main', label: 'Skip to content' },
 *     { target: 'sidebar', label: 'Skip to sidebar' }
 *   ]}
 * />
 */
export function SkipLinks({
  links = defaultLinks,
  className,
  position = 'top',
  zIndex = 1050,
  excludeTargets = noExcludedTargets,
}: SkipLinksProps) {
  const visibleLinks = React.useMemo(
    () => links.filter((link) => !excludeTargets.includes(link.target)),
    [excludeTargets, links],
  );
  const handleClick = (e: React.MouseEvent<HTMLAnchorElement>, target: string) => {
    e.preventDefault();
    const element = document.getElementById(target);

    if (element) {
      // Focus the element
      element.focus();

      // If the element can't receive focus, add tabindex
      if (document.activeElement !== element) {
        element.setAttribute('tabindex', '-1');
        element.focus();
      }

      // Scroll to the element
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });

      // Announce to screen readers
      const announcement = document.createElement('div');
      announcement.setAttribute('role', 'status');
      announcement.setAttribute('aria-live', 'polite');
      announcement.className = 'sr-only';
      announcement.textContent = `Navigated to ${target.replace('-', ' ')}`;
      document.body.appendChild(announcement);

      setTimeout(() => {
        document.body.removeChild(announcement);
      }, 1000);
    }
  };

  // Handle keyboard shortcuts
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Keep skip navigation on its advertised Alt+number chord. Workspace
      // modes use Alt+Shift+number, so the two command sets never double-fire.
      if (e.altKey && !e.shiftKey && !e.ctrlKey && !e.metaKey) {
        const link = visibleLinks.find((candidate) => (
          candidate.shortcut ? e.code === `Digit${candidate.shortcut}` : false
        ));
        if (link) {
          e.preventDefault();
          const element = document.getElementById(link.target);
          if (element) {
            element.focus();
            if (document.activeElement !== element) {
              element.setAttribute('tabindex', '-1');
              element.focus();
            }
            element.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [visibleLinks]);

  const positionClasses = {
    top: 'top-0 left-0 right-0 flex-row justify-center',
    left: 'top-20 left-0 flex-col',
  };

  return (
    <nav
      className={cn(
        'fixed flex gap-2 p-2',
        positionClasses[position],
        // Initially hidden, shown on focus
        'opacity-0 focus-within:opacity-100',
        'pointer-events-none focus-within:pointer-events-auto',
        'transition-opacity duration-200',
        className
      )}
      style={{ zIndex }}
      aria-label="Skip navigation"
    >
      {visibleLinks.map((link) => (
        <a
          key={link.target}
          href={`#${link.target}`}
          onClick={(e) => handleClick(e, link.target)}
          className={cn(
            'px-4 py-2 bg-primary-600 text-white rounded-md',
            'hover:bg-primary-700 focus:bg-primary-700',
            'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
            'shadow-lg transform -translate-y-full focus:translate-y-0',
            'transition-all duration-200',
            'text-sm font-medium whitespace-nowrap'
          )}
          aria-label={
            link.shortcut
              ? `${link.label} (Alt+${link.shortcut})`
              : link.label
          }
        >
          {link.label}
          {link.shortcut && (
            <kbd className="ml-2 px-1.5 py-0.5 text-xs bg-white/20 rounded">
              Alt+{link.shortcut}
            </kbd>
          )}
        </a>
      ))}
    </nav>
  );
}

/**
 * Main content wrapper with proper landmark and focus management
 */
interface MainContentProps {
  children: React.ReactNode;
  id?: string;
  className?: string;
  role?: string;
}

export function MainContent({
  children,
  id = 'main-content',
  className,
  role = 'main',
}: MainContentProps) {
  return (
    <main
      id={id}
      role={role}
      tabIndex={-1}
      className={cn('focus:outline-none', className)}
      aria-label="Main content"
    >
      {children}
    </main>
  );
}

/**
 * Navigation wrapper with proper landmark
 */
interface NavigationProps {
  children: React.ReactNode;
  id?: string;
  className?: string;
  label?: string;
}

export function Navigation({
  children,
  id = 'navigation',
  className,
  label = 'Main navigation',
}: NavigationProps) {
  return (
    <nav
      id={id}
      tabIndex={-1}
      className={cn('focus:outline-none', className)}
      aria-label={label}
    >
      {children}
    </nav>
  );
}

/**
 * Search region wrapper
 */
interface SearchRegionProps {
  children: React.ReactNode;
  id?: string;
  className?: string;
  label?: string;
}

export function SearchRegion({
  children,
  id = 'search',
  className,
  label = 'Search',
}: SearchRegionProps) {
  return (
    <search
      id={id}
      role="search"
      tabIndex={-1}
      className={cn('focus:outline-none', className)}
      aria-label={label}
    >
      {children}
    </search>
  );
}

/**
 * Footer wrapper with proper landmark
 */
interface FooterProps {
  children: React.ReactNode;
  id?: string;
  className?: string;
}

export function Footer({
  children,
  id = 'footer',
  className,
}: FooterProps) {
  return (
    <footer
      id={id}
      tabIndex={-1}
      className={cn('focus:outline-none', className)}
      aria-label="Footer"
    >
      {children}
    </footer>
  );
}

/**
 * Breadcrumb navigation with proper ARIA attributes
 */
interface BreadcrumbItem {
  label: string;
  href?: string;
  current?: boolean;
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
  separator?: React.ReactNode;
  className?: string;
}

export function Breadcrumbs({
  items,
  separator = '/',
  className,
}: BreadcrumbsProps) {
  return (
    <nav
      aria-label="Breadcrumb"
      className={cn('flex items-center space-x-2 text-sm', className)}
    >
      <ol className="flex items-center space-x-2">
        {items.map((item, index) => (
          <li key={index} className="flex items-center">
            {index > 0 && (
              <span className="mx-2 text-gray-400" aria-hidden="true">
                {separator}
              </span>
            )}
            {item.href && !item.current ? (
              <a
                href={item.href}
                className="text-gray-600 hover:text-gray-900 transition-colors"
                aria-current={item.current ? 'page' : undefined}
              >
                {item.label}
              </a>
            ) : (
              <span
                className={cn(
                  item.current ? 'text-gray-900 font-medium' : 'text-gray-600'
                )}
                aria-current={item.current ? 'page' : undefined}
              >
                {item.label}
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}

/**
 * Section with heading for better document structure
 */
interface SectionProps {
  children: React.ReactNode;
  title?: string;
  level?: 1 | 2 | 3 | 4 | 5 | 6;
  id?: string;
  className?: string;
}

export function Section({
  children,
  title,
  level = 2,
  id,
  className,
}: SectionProps) {
  const HeadingTag = `h${level}` as 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';

  return (
    <section
      id={id}
      className={cn('focus:outline-none', className)}
      aria-labelledby={title ? `${id}-heading` : undefined}
      tabIndex={-1}
    >
      {title && React.createElement(
        HeadingTag,
        {
          id: `${id}-heading`,
          className: 'text-xl font-semibold mb-4'
        },
        title
      )}
      {children}
    </section>
  );
}

/**
 * Announcement region for live updates
 */
interface AnnouncementProps {
  message: string;
  politeness?: 'polite' | 'assertive';
  atomic?: boolean;
  relevant?: 'additions' | 'removals' | 'text' | 'all';
}

export function Announcement({
  message,
  politeness = 'polite',
  atomic = true,
  relevant = 'additions',
}: AnnouncementProps) {
  return (
    <div
      role="status"
      aria-live={politeness}
      aria-atomic={atomic}
      aria-relevant={relevant}
      className="sr-only"
    >
      {message}
    </div>
  );
}
