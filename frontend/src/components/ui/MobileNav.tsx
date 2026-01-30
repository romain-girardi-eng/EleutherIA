import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import {
  Home,
  Search,
  Network,
  MessageSquare,
  BookOpen,
  Menu,
  Plus,
  type LucideIcon
} from 'lucide-react';
import { cn } from '../../utils/cn';
import { useIsMobile } from '../../hooks/useMediaQuery';

export interface MobileNavItem {
  /** Route path */
  to: string;
  /** Icon component */
  icon: React.ReactNode | LucideIcon;
  /** Label text (can be a translation key) */
  label: string;
  /** Badge count */
  badge?: number | string;
  /** Whether to show a dot indicator */
  dot?: boolean;
  /** Custom active check function */
  isActive?: (pathname: string) => boolean;
  /** Whether this is the primary action */
  isPrimary?: boolean;
}

interface MobileNavProps {
  /** Navigation items */
  items?: MobileNavItem[];
  /** Additional CSS classes */
  className?: string;
  /** Whether to hide on desktop */
  hideOnDesktop?: boolean;
  /** Whether to show labels */
  showLabels?: boolean;
  /** Maximum number of items (rest go to menu) */
  maxItems?: number;
  /** Custom more menu component */
  moreMenu?: React.ReactNode;
  /** Z-index for the nav */
  zIndex?: number;
  /** Background blur */
  blur?: boolean;
  /** Custom height */
  height?: string;
}

/**
 * Get default navigation items with translations
 */
const useDefaultItems = (): MobileNavItem[] => {
  const { t } = useTranslation();

  return [
    { to: '/', icon: Home, label: t('mobileNav.home') },
    { to: '/search', icon: Search, label: t('mobileNav.search') },
    { to: '/visualizer', icon: Network, label: t('mobileNav.graph') },
    { to: '/graphrag', icon: MessageSquare, label: t('mobileNav.qa') },
    { to: '/texts', icon: BookOpen, label: t('mobileNav.texts') },
  ];
};

/**
 * MobileNav component for bottom navigation on mobile devices
 *
 * @example
 * <MobileNav />
 *
 * @example
 * // With custom items
 * <MobileNav
 *   items={[
 *     { to: '/', icon: Home, label: 'Home', badge: 3 },
 *     { to: '/search', icon: Search, label: 'Search' },
 *   ]}
 * />
 */
export function MobileNav({
  items,
  className,
  hideOnDesktop = true,
  showLabels = true,
  maxItems = 5,
  moreMenu,
  zIndex = 50,
  blur = true,
  height = '4rem',
}: MobileNavProps) {
  const location = useLocation();
  const isMobile = useIsMobile();
  const { t } = useTranslation();
  const defaultItems = useDefaultItems();
  const navItems = items || defaultItems;

  // Don't render on desktop if hideOnDesktop is true
  if (hideOnDesktop && !isMobile) {
    return null;
  }

  // Split items if there are too many
  const visibleItems = navItems.slice(0, maxItems);
  const overflowItems = navItems.slice(maxItems);

  const renderIcon = (icon: React.ReactNode | LucideIcon) => {
    if (React.isValidElement(icon)) {
      return icon;
    }
    const IconComponent = icon as LucideIcon;
    return <IconComponent className="h-5 w-5" />;
  };

  return (
    <nav
      className={cn(
        'fixed bottom-0 left-0 right-0',
        'bg-white border-t border-gray-200',
        blur && 'backdrop-blur-lg bg-white/95',
        hideOnDesktop && 'lg:hidden',
        className
      )}
      style={{ zIndex, height }}
      role="navigation"
      aria-label={t('mobileNav.ariaLabel')}
    >
      <div className={cn('grid h-full', `grid-cols-${visibleItems.length}`)}>
        {visibleItems.map((item) => {
          const isActive = item.isActive
            ? item.isActive(location.pathname)
            : location.pathname === item.to;

          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive: routeActive }) =>
                cn(
                  'relative flex flex-col items-center justify-center gap-1 transition-colors',
                  'hover:bg-gray-50 active:bg-gray-100',
                  (routeActive || isActive)
                    ? 'text-primary-600'
                    : 'text-gray-500 hover:text-gray-700'
                )
              }
            >
              {({ isActive: routeActive }) => (
                <>
                  {/* Active indicator */}
                  {(routeActive || isActive) && (
                    <motion.div
                      layoutId="mobile-nav-indicator"
                      className="absolute top-0 left-1/2 -translate-x-1/2 w-12 h-0.5 bg-primary-600"
                      initial={false}
                      transition={{
                        type: 'spring',
                        stiffness: 300,
                        damping: 30,
                      }}
                    />
                  )}

                  {/* Icon with badge */}
                  <div className="relative">
                    {renderIcon(item.icon)}

                    {/* Badge */}
                    {item.badge !== undefined && (
                      <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] flex items-center justify-center bg-red-600 text-white text-xs font-bold rounded-full px-1">
                        {typeof item.badge === 'number' && item.badge > 99 ? '99+' : item.badge}
                      </span>
                    )}

                    {/* Dot indicator */}
                    {item.dot && (
                      <span className="absolute -top-1 -right-1 w-2 h-2 bg-red-600 rounded-full" />
                    )}
                  </div>

                  {/* Label */}
                  {showLabels && (
                    <span className="text-xs font-medium">{item.label}</span>
                  )}

                  {/* Primary action indicator */}
                  {item.isPrimary && (
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                      <div className="absolute w-14 h-14 bg-primary-600 rounded-full -top-4 shadow-lg" />
                      <div className="relative text-white z-10">
                        {renderIcon(item.icon)}
                      </div>
                    </div>
                  )}
                </>
              )}
            </NavLink>
          );
        })}

        {/* More menu if there are overflow items */}
        {overflowItems.length > 0 && (
          moreMenu || (
            <button
              className="flex flex-col items-center justify-center gap-1 text-gray-500 hover:text-gray-700 hover:bg-gray-50 transition-colors"
              aria-label={t('mobileNav.moreOptions')}
            >
              <Menu className="h-5 w-5" />
              {showLabels && <span className="text-xs">{t('mobileNav.more')}</span>}
            </button>
          )
        )}
      </div>
    </nav>
  );
}

/**
 * TabBar - Alternative tab-style navigation
 */
interface TabBarItem {
  key: string;
  label: string;
  icon?: React.ReactNode;
  badge?: number | string;
}

interface TabBarProps {
  items: TabBarItem[];
  activeKey: string;
  onChange: (key: string) => void;
  className?: string;
  variant?: 'default' | 'pills' | 'underline';
}

export function TabBar({
  items,
  activeKey,
  onChange,
  className,
  variant = 'default'
}: TabBarProps) {
  return (
    <div
      className={cn(
        'flex',
        variant === 'pills' && 'gap-2 p-1 bg-gray-100 rounded-lg',
        variant === 'underline' && 'border-b',
        className
      )}
      role="tablist"
    >
      {items.map((item) => {
        const isActive = item.key === activeKey;

        return (
          <button
            key={item.key}
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(item.key)}
            className={cn(
              'flex-1 flex items-center justify-center gap-2 px-4 py-2 font-medium transition-colors',
              variant === 'default' && [
                isActive
                  ? 'text-primary-600 bg-primary-50'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              ],
              variant === 'pills' && [
                'rounded-md',
                isActive
                  ? 'bg-white text-primary-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              ],
              variant === 'underline' && [
                'relative',
                isActive
                  ? 'text-primary-600'
                  : 'text-gray-600 hover:text-gray-900'
              ]
            )}
          >
            {item.icon}
            <span>{item.label}</span>
            {item.badge !== undefined && (
              <span className="ml-1 px-2 py-0.5 text-xs bg-gray-200 rounded-full">
                {item.badge}
              </span>
            )}

            {/* Underline indicator */}
            {variant === 'underline' && isActive && (
              <motion.div
                layoutId="tab-indicator"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-600"
                initial={false}
                transition={{
                  type: 'spring',
                  stiffness: 300,
                  damping: 30,
                }}
              />
            )}
          </button>
        );
      })}
    </div>
  );
}

/**
 * FloatingActionButton - FAB for primary actions
 */
interface FloatingActionButtonProps {
  onClick: () => void;
  icon?: React.ReactNode;
  label?: string;
  position?: 'bottom-right' | 'bottom-center' | 'bottom-left';
  offset?: { bottom?: string; right?: string; left?: string };
  size?: 'sm' | 'md' | 'lg';
  variant?: 'primary' | 'secondary' | 'accent';
  className?: string;
  hideOnDesktop?: boolean;
}

export function FloatingActionButton({
  onClick,
  icon = <Plus className="h-6 w-6" />,
  label,
  position = 'bottom-right',
  offset = { bottom: '5rem', right: '1rem' },
  size = 'md',
  variant = 'primary',
  className,
  hideOnDesktop = true
}: FloatingActionButtonProps) {
  const isMobile = useIsMobile();
  const { t } = useTranslation();

  if (hideOnDesktop && !isMobile) {
    return null;
  }

  const sizeClasses = {
    sm: 'h-12 w-12',
    md: 'h-14 w-14',
    lg: 'h-16 w-16',
  };

  const variantClasses = {
    primary: 'bg-primary-600 text-white hover:bg-primary-700 active:bg-primary-800',
    secondary: 'bg-gray-800 text-white hover:bg-gray-900',
    accent: 'bg-accent-600 text-white hover:bg-accent-700',
  };

  const positionStyles = {
    'bottom-right': { bottom: offset.bottom, right: offset.right },
    'bottom-center': { bottom: offset.bottom, left: '50%', transform: 'translateX(-50%)' },
    'bottom-left': { bottom: offset.bottom, left: offset.left },
  };

  return (
    <motion.button
      onClick={onClick}
      className={cn(
        'fixed z-50 rounded-full shadow-lg flex items-center justify-center transition-all',
        'hover:shadow-xl active:scale-95',
        sizeClasses[size],
        variantClasses[variant],
        hideOnDesktop && 'lg:hidden',
        className
      )}
      style={positionStyles[position]}
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.9 }}
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{
        type: 'spring',
        stiffness: 300,
        damping: 20,
      }}
      aria-label={label || t('mobileNav.fab')}
    >
      {icon}
      {label && (
        <span className="sr-only">{label}</span>
      )}
    </motion.button>
  );
}

/**
 * MobileToolbar - Top toolbar for mobile screens
 */
interface MobileToolbarProps {
  title?: string;
  leftAction?: React.ReactNode;
  rightAction?: React.ReactNode;
  className?: string;
  transparent?: boolean;
  blur?: boolean;
}

export function MobileToolbar({
  title,
  leftAction,
  rightAction,
  className,
  transparent = false,
  blur = false
}: MobileToolbarProps) {
  return (
    <div
      className={cn(
        'flex items-center justify-between h-14 px-4',
        !transparent && 'bg-white border-b',
        blur && 'backdrop-blur-lg bg-white/95',
        className
      )}
    >
      <div className="flex-shrink-0">
        {leftAction}
      </div>

      {title && (
        <h1 className="flex-1 text-center text-lg font-semibold truncate px-4">
          {title}
        </h1>
      )}

      <div className="flex-shrink-0">
        {rightAction}
      </div>
    </div>
  );
}
