/**
 * MobileMenu — full-screen drawer for the mobile navigation.
 *
 * Replaces the previous inline-strip menu that just dumped 14 nav links
 * into a vertical list. This one is organized:
 *   - 4 semantic sections (Découvrir / Bibliothèque / Recherche /
 *     Communauté) each with an icon and an uppercase header
 *   - Each row is touch-friendly (≥ 48 px), with an icon on the left
 *     and a chevron on the right
 *   - Always-visible language chips at the bottom
 *   - User footer with avatar + logout when authenticated
 *
 * Visually consistent with the scholarly parchment palette; backdrop
 * blur dims the page behind. Animated entrance with Framer Motion
 * (slide from right + staggered children).
 */

import { useEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  ChevronRight,
  Compass,
  Library,
  Brain,
  Users,
  HelpCircle,
  Info,
  BookA,
  MessageCircleQuestion,
  Database as DatabaseIcon,
  BookOpenText,
  BookMarked,
  ScrollText,
  MessageSquare,
  Sparkles,
  Network,
  Swords,
  GitPullRequest,
  UploadCloud,
  LogOut,
  User as UserIcon,
} from 'lucide-react';
import { cn } from '../lib/utils';
import { LanguageChips } from './LanguageChips';
import { Button } from './ui/button';

interface MobileMenuProps {
  open: boolean;
  onClose: () => void;
  isAuthenticated: boolean;
  username?: string;
  onLogout: () => void;
}

interface MenuItem {
  to: string;
  labelKey: string;
  Icon: typeof Compass;
  /** When set, item only appears if the user is authenticated. */
  authOnly?: boolean;
}

interface MenuGroup {
  titleKey: string;
  Icon: typeof Compass;
  items: MenuItem[];
}

const GROUPS: MenuGroup[] = [
  {
    titleKey: 'nav.groups.discover',
    Icon: Compass,
    items: [
      { to: '/how-it-works', labelKey: 'nav.howItWorks', Icon: HelpCircle },
      { to: '/about', labelKey: 'nav.about', Icon: Info },
      { to: '/glossary', labelKey: 'nav.glossary', Icon: BookA },
      { to: '/faq', labelKey: 'nav.faq', Icon: MessageCircleQuestion },
    ],
  },
  {
    titleKey: 'nav.groups.library',
    Icon: Library,
    items: [
      { to: '/database', labelKey: 'nav.database', Icon: DatabaseIcon },
      { to: '/texts', labelKey: 'nav.texts', Icon: BookOpenText },
      { to: '/bibliography', labelKey: 'nav.bibliography', Icon: BookMarked },
    ],
  },
  {
    titleKey: 'nav.groups.research',
    Icon: Brain,
    items: [
      { to: '/graphrag', labelKey: 'nav.graphrag', Icon: MessageSquare },
      { to: '/the-debate', labelKey: 'nav.theDebate', Icon: Swords },
      { to: '/research', labelKey: 'nav.research', Icon: Sparkles },
      { to: '/visualizer', labelKey: 'nav.visualizer', Icon: Network },
      { to: '/passages-canoniques', labelKey: 'nav.canonicalPassages', Icon: ScrollText },
    ],
  },
  {
    titleKey: 'nav.groups.community',
    Icon: Users,
    items: [
      { to: '/recherches', labelKey: 'nav.recherches', Icon: GitPullRequest },
      { to: '/contributions', labelKey: 'nav.contributions', Icon: BookMarked },
      { to: '/contribuer', labelKey: 'nav.contribute', Icon: UploadCloud, authOnly: true },
    ],
  },
];

const drawerVariants = {
  hidden: { x: '100%' },
  visible: { x: 0 },
} as const;

const backdropVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
} as const;

const listVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.04, delayChildren: 0.08 } },
} as const;

const rowVariants = {
  hidden: { x: 20, opacity: 0 },
  visible: { x: 0, opacity: 1, transition: { duration: 0.24, ease: 'easeOut' } },
} as const;

export function MobileMenu({
  open,
  onClose,
  isAuthenticated,
  username,
  onLogout,
}: MobileMenuProps) {
  const { t } = useTranslation();
  const location = useLocation();

  // Lock body scroll while the drawer is open. Restore on unmount/close.
  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  // Close on route change (when user taps a link).
  //
  // CRITICAL: useEffect runs on mount too, and this component mounts the
  // moment `mobileMenuOpen` flips to true. Without the ref guard below,
  // mount calls `onClose()` immediately and the drawer slams shut a frame
  // after opening — the bug that masqueraded as "burger doesn't work".
  // Snapshot the pathname at mount and only close when it actually changes.
  const initialPathnameRef = useRef(location.pathname);
  useEffect(() => {
    if (!open) return;
    if (location.pathname === initialPathnameRef.current) return;
    onClose();
    // We intentionally depend only on location.pathname.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            key="mm-backdrop"
            variants={backdropVariants}
            initial="hidden"
            animate="visible"
            exit="hidden"
            transition={{ duration: 0.18 }}
            onClick={onClose}
            className="fixed inset-0 z-[60] bg-stone-950/40 backdrop-blur-sm lg:hidden"
            aria-hidden="true"
          />

          {/* Drawer */}
          <motion.aside
            key="mm-drawer"
            id="mobile-menu"
            role="dialog"
            aria-modal="true"
            aria-label={t('nav.menuTitle')}
            variants={drawerVariants}
            initial="hidden"
            animate="visible"
            exit="hidden"
            transition={{ type: 'spring', stiffness: 320, damping: 36 }}
            className={cn(
              'fixed top-0 right-0 z-[61] h-[100dvh] w-[88vw] max-w-[420px] lg:hidden',
              'bg-gradient-to-b from-parchment-50 via-parchment-50 to-amber-50/40',
              'border-l border-amber-200/60 shadow-[0_24px_80px_-32px_rgba(120,53,15,0.45)]',
              'flex flex-col overflow-hidden',
            )}
          >
            {/* Header */}
            <header className="shrink-0 flex items-center justify-between px-5 py-4 border-b border-amber-200/40">
              <div className="flex items-center gap-3">
                <img src="/logo-880.webp" alt="EleutherIA" className="h-9 w-9" />
                <div className="leading-tight">
                  <div className="font-display text-base font-semibold text-stone-900">
                    EleutherIA
                  </div>
                  <div className="text-[11px] uppercase tracking-[0.14em] text-amber-700/80">
                    {t('nav.menuSubtitle')}
                  </div>
                </div>
              </div>
              <button
                type="button"
                onClick={onClose}
                aria-label={t('nav.closeMenu')}
                className="h-10 w-10 inline-flex items-center justify-center rounded-full text-stone-500 hover:bg-amber-100/60 hover:text-amber-900 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </header>

            {/* Scrollable groups */}
            <motion.div
              variants={listVariants}
              initial="hidden"
              animate="visible"
              className="flex-1 min-h-0 overflow-y-auto px-3 py-3 space-y-4"
            >
              {GROUPS.map((group) => {
                const visibleItems = group.items.filter(
                  (it) => !it.authOnly || isAuthenticated,
                );
                if (visibleItems.length === 0) return null;
                const Icon = group.Icon;
                return (
                  <section key={group.titleKey} aria-labelledby={`grp-${group.titleKey}`}>
                    <motion.h2
                      variants={rowVariants}
                      id={`grp-${group.titleKey}`}
                      className="flex items-center gap-2 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.16em] text-amber-800/90"
                    >
                      <Icon className="h-3.5 w-3.5" aria-hidden="true" />
                      {t(group.titleKey)}
                    </motion.h2>
                    <ul className="space-y-0.5">
                      {visibleItems.map((item) => {
                        const ItemIcon = item.Icon;
                        const active = location.pathname === item.to;
                        return (
                          <motion.li key={item.to} variants={rowVariants}>
                            <Link
                              to={item.to}
                              onClick={onClose}
                              className={cn(
                                'group flex items-center gap-3 px-3 py-3 rounded-xl transition-colors',
                                'min-h-[48px]',
                                active
                                  ? 'bg-amber-100/70 text-amber-900 ring-1 ring-amber-300/70'
                                  : 'text-stone-700 hover:bg-amber-50/80 hover:text-amber-900',
                              )}
                            >
                              <span
                                className={cn(
                                  'h-9 w-9 inline-flex items-center justify-center rounded-lg shrink-0',
                                  active
                                    ? 'bg-amber-200/60 text-amber-900'
                                    : 'bg-white/70 text-amber-700 group-hover:bg-amber-100/70',
                                )}
                              >
                                <ItemIcon className="h-4 w-4" />
                              </span>
                              <span className="flex-1 text-[15px] font-medium leading-tight">
                                {t(item.labelKey)}
                              </span>
                              <ChevronRight
                                className={cn(
                                  'h-4 w-4 shrink-0 transition-transform',
                                  active ? 'text-amber-700' : 'text-stone-300 group-hover:text-amber-600 group-hover:translate-x-0.5',
                                )}
                                aria-hidden="true"
                              />
                            </Link>
                          </motion.li>
                        );
                      })}
                    </ul>
                  </section>
                );
              })}
            </motion.div>

            {/* Footer: language + user actions */}
            <footer className="shrink-0 border-t border-amber-200/40 bg-white/60 backdrop-blur-sm px-3 py-3 space-y-3">
              <div>
                <div className="px-1 pb-1.5 text-[11px] font-semibold uppercase tracking-[0.16em] text-amber-800/80">
                  {t('common.selectLanguage')}
                </div>
                {/* Compact chips inside the drawer — the `large` variant
                    stretched each chip with native names and overflowed
                    on phones (Français/Italiano/Ελληνικά too wide). */}
                <LanguageChips size="compact" className="flex-wrap gap-1.5" />
              </div>

              {isAuthenticated && (
                <div className="flex items-center justify-between gap-2 pt-2 border-t border-amber-100/60">
                  <div className="flex items-center gap-2 text-sm text-stone-700 px-2">
                    <span className="h-7 w-7 inline-flex items-center justify-center rounded-full bg-amber-100 text-amber-800">
                      <UserIcon className="h-3.5 w-3.5" />
                    </span>
                    <span className="font-medium truncate max-w-[160px]">
                      {username}
                    </span>
                  </div>
                  <Button
                    onClick={() => {
                      onLogout();
                      onClose();
                    }}
                    variant="ghost"
                    size="sm"
                    className="text-stone-600 hover:text-amber-900"
                  >
                    <LogOut className="h-4 w-4 mr-1.5" />
                    {t('nav.logout')}
                  </Button>
                </div>
              )}
            </footer>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}

export default MobileMenu;
