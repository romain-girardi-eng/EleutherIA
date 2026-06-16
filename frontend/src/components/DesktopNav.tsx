/**
 * DesktopNav — premium scholarly navigation bar for >= lg viewports.
 *
 * Mirrors the semantic grouping of MobileMenu (Discover / Library /
 * Research / Community) but renders them as four dropdown triggers,
 * a single CTA pill to the Knowledge Graph, a compact language
 * switcher (current locale → 5-row popover), and a collapsed user
 * slot. The whole thing breathes — one row, generous whitespace,
 * parchment palette, no neon.
 *
 * Strictly client-side: this component is always rendered behind a
 * `hidden lg:flex` parent, so the desktop bar never appears at mobile
 * breakpoints. Mobile burger + drawer are intentionally untouched.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { AnimatePresence, motion } from 'framer-motion';
import { useKgStats } from '../hooks/useKgStats';
import { formatCompact } from '../lib/formatCompact';
import {
  ChevronDown,
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
  FolderOpen,
  LogOut,
  User as UserIcon,
  Globe2,
  Check,
  LogIn,
} from 'lucide-react';
import { cn } from '../lib/utils';
import { languages } from '../i18n/config';
import { Button } from './ui/button';

interface DesktopNavProps {
  inverted: boolean;
  isAuthenticated: boolean;
  username?: string;
  onLogout: () => void;
}

interface NavItem {
  to: string;
  labelKey: string;
  descKey: string;
  Icon: typeof Compass;
  authOnly?: boolean;
}

interface NavGroup {
  id: 'discover' | 'library' | 'research' | 'community';
  titleKey: string;
  Icon: typeof Compass;
  items: NavItem[];
}

const GROUPS: NavGroup[] = [
  {
    id: 'discover',
    titleKey: 'nav.groups.discover',
    Icon: Compass,
    items: [
      { to: '/how-it-works', labelKey: 'nav.howItWorks', descKey: 'nav.descriptions.howItWorks', Icon: HelpCircle },
      { to: '/about', labelKey: 'nav.about', descKey: 'nav.descriptions.about', Icon: Info },
      { to: '/glossary', labelKey: 'nav.glossary', descKey: 'nav.descriptions.glossary', Icon: BookA },
      { to: '/faq', labelKey: 'nav.faq', descKey: 'nav.descriptions.faq', Icon: MessageCircleQuestion },
    ],
  },
  {
    id: 'library',
    titleKey: 'nav.groups.library',
    Icon: Library,
    items: [
      { to: '/database', labelKey: 'nav.database', descKey: 'nav.descriptions.database', Icon: DatabaseIcon },
      { to: '/texts', labelKey: 'nav.texts', descKey: 'nav.descriptions.texts', Icon: BookOpenText },
      { to: '/bibliography', labelKey: 'nav.bibliography', descKey: 'nav.descriptions.bibliography', Icon: BookMarked },
    ],
  },
  {
    id: 'research',
    titleKey: 'nav.groups.research',
    Icon: Brain,
    items: [
      { to: '/graphrag', labelKey: 'nav.graphrag', descKey: 'nav.descriptions.graphrag', Icon: MessageSquare },
      { to: '/the-debate', labelKey: 'nav.theDebate', descKey: 'nav.descriptions.theDebate', Icon: Swords },
      { to: '/research', labelKey: 'nav.research', descKey: 'nav.descriptions.research', Icon: Sparkles },
      { to: '/passages-canoniques', labelKey: 'nav.canonicalPassages', descKey: 'nav.descriptions.canonicalPassages', Icon: ScrollText },
    ],
  },
  {
    id: 'community',
    titleKey: 'nav.groups.community',
    Icon: Users,
    items: [
      { to: '/recherches', labelKey: 'nav.recherches', descKey: 'nav.descriptions.recherches', Icon: GitPullRequest },
      { to: '/contributions', labelKey: 'nav.contributions', descKey: 'nav.descriptions.contributions', Icon: BookMarked },
      { to: '/contribuer', labelKey: 'nav.contribute', descKey: 'nav.descriptions.contribute', Icon: UploadCloud, authOnly: true },
      { to: '/projects', labelKey: 'nav.projects', descKey: 'nav.descriptions.projects', Icon: FolderOpen, authOnly: true },
    ],
  },
];

const CTA_PATH = '/visualizer';

const panelVariants = {
  hidden: { opacity: 0, y: -6, scale: 0.98 },
  visible: { opacity: 1, y: 0, scale: 1 },
} as const;

type OpenKey = NavGroup['id'] | 'lang' | 'user' | null;

/** Returns interpolation vars for nav description keys that embed live counts. */
function navDescVars(
  descKey: string,
  nodes: string,
  edges: string,
  works: string,
): Record<string, string> | undefined {
  if (descKey === 'nav.descriptions.database') return { nodes, edges };
  if (descKey === 'nav.descriptions.texts') return { works };
  return undefined;
}

export function DesktopNav({ inverted, isAuthenticated, username, onLogout }: DesktopNavProps) {
  const { t, i18n } = useTranslation();
  const kgStats = useKgStats();
  const nodesCompact = formatCompact(kgStats.nodes, i18n.language);
  const edgesCompact = formatCompact(kgStats.edges, i18n.language);
  const worksCompact = formatCompact(kgStats.works, i18n.language);
  const location = useLocation();
  const [open, setOpen] = useState<OpenKey>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const closeTimerRef = useRef<number | null>(null);

  const activeGroupId = useMemo<NavGroup['id'] | null>(() => {
    const match = GROUPS.find((g) => g.items.some((it) => it.to === location.pathname));
    return match?.id ?? null;
  }, [location.pathname]);

  const isCtaActive = location.pathname === CTA_PATH || location.pathname.startsWith(`${CTA_PATH}/`);

  // Close on outside click, ESC, or route change.
  useEffect(() => setOpen(null), [location.pathname]);

  useEffect(() => {
    if (open === null) return;
    const handlePointer = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(null);
    };
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(null);
    };
    document.addEventListener('mousedown', handlePointer);
    document.addEventListener('keydown', handleKey);
    return () => {
      document.removeEventListener('mousedown', handlePointer);
      document.removeEventListener('keydown', handleKey);
    };
  }, [open]);

  // Hover with grace period so the cursor can travel from trigger to panel.
  const scheduleClose = useCallback(() => {
    if (closeTimerRef.current !== null) window.clearTimeout(closeTimerRef.current);
    closeTimerRef.current = window.setTimeout(() => setOpen(null), 140);
  }, []);
  const cancelClose = useCallback(() => {
    if (closeTimerRef.current !== null) {
      window.clearTimeout(closeTimerRef.current);
      closeTimerRef.current = null;
    }
  }, []);

  const triggerBase = cn(
    'group inline-flex items-center gap-1.5 h-9 px-3 rounded-full text-sm font-medium',
    'transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400/60',
  );
  const triggerIdle = inverted
    ? 'text-white/80 hover:text-white hover:bg-white/10'
    : 'text-stone-700 hover:text-amber-900 hover:bg-amber-50/70';
  const triggerActive = inverted
    ? 'text-white bg-white/10'
    : 'text-amber-900 bg-amber-50';

  const currentLang = languages.find((l) => l.code === i18n.language) ?? languages[0];

  return (
    <div ref={rootRef} className="hidden lg:flex items-center gap-1.5 relative" onMouseLeave={scheduleClose}>
      {GROUPS.map((group) => {
        const visible = group.items.filter((it) => !it.authOnly || isAuthenticated);
        if (visible.length === 0) return null;
        const isOpen = open === group.id;
        const isActive = activeGroupId === group.id;

        return (
          <div
            key={group.id}
            className="relative"
            onMouseEnter={() => {
              cancelClose();
              setOpen(group.id);
            }}
          >
            <button
              type="button"
              aria-haspopup="menu"
              aria-expanded={isOpen}
              onClick={() => setOpen(isOpen ? null : group.id)}
              onFocus={() => setOpen(group.id)}
              className={cn(triggerBase, isActive || isOpen ? triggerActive : triggerIdle)}
            >
              <span>{t(group.titleKey)}</span>
              <ChevronDown
                className={cn(
                  'h-3.5 w-3.5 transition-transform duration-200',
                  isOpen && 'rotate-180',
                )}
                aria-hidden="true"
              />
            </button>

            {isActive && (
              <motion.span
                layoutId="nav-active-pill"
                className={cn(
                  'absolute inset-x-2 -bottom-1 h-[2px] rounded-full',
                  inverted ? 'bg-amber-300/90' : 'bg-amber-600',
                )}
                transition={{ type: 'spring', stiffness: 380, damping: 32 }}
                aria-hidden="true"
              />
            )}

            <AnimatePresence>
              {isOpen && (
                <motion.div
                  role="menu"
                  aria-label={t(group.titleKey)}
                  variants={panelVariants}
                  initial="hidden"
                  animate="visible"
                  exit="hidden"
                  transition={{ duration: 0.16, ease: [0.16, 1, 0.3, 1] }}
                  className={cn(
                    'absolute left-0 top-[calc(100%+10px)] w-[320px] z-[60] origin-top',
                    'rounded-2xl border border-amber-200/60 bg-parchment-50/95 backdrop-blur-md',
                    'shadow-[0_24px_60px_-28px_rgba(120,53,15,0.45)]',
                    'p-2',
                  )}
                  onMouseEnter={cancelClose}
                  onMouseLeave={scheduleClose}
                >
                  <div className="px-3 pt-2 pb-1.5 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-amber-800/80">
                    <group.Icon className="h-3.5 w-3.5" aria-hidden="true" />
                    {t(group.titleKey)}
                  </div>
                  <ul className="space-y-0.5">
                    {visible.map((item) => {
                      const ItemIcon = item.Icon;
                      const itemActive = location.pathname === item.to;
                      return (
                        <li key={item.to}>
                          <Link
                            to={item.to}
                            role="menuitem"
                            onClick={() => setOpen(null)}
                            aria-current={itemActive ? 'page' : undefined}
                            className={cn(
                              'flex items-start gap-3 px-3 py-2.5 rounded-xl transition-colors',
                              itemActive
                                ? 'bg-amber-100/70 text-amber-900'
                                : 'text-stone-700 hover:bg-amber-50 hover:text-amber-900',
                            )}
                          >
                            <span
                              className={cn(
                                'mt-0.5 h-8 w-8 inline-flex items-center justify-center rounded-lg shrink-0',
                                itemActive ? 'bg-amber-200/60 text-amber-900' : 'bg-white/80 text-amber-700',
                              )}
                            >
                              <ItemIcon className="h-4 w-4" />
                            </span>
                            <span className="min-w-0 flex-1">
                              <span className="block text-[14px] font-semibold leading-tight">
                                {t(item.labelKey)}
                              </span>
                              <span className="block text-[12px] text-stone-500 leading-snug mt-0.5">
                                {t(item.descKey, navDescVars(item.descKey, nodesCompact, edgesCompact, worksCompact))}
                              </span>
                            </span>
                          </Link>
                        </li>
                      );
                    })}
                  </ul>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      })}

      {/* Primary CTA — Knowledge Graph */}
      <Link
        to={CTA_PATH}
        aria-current={isCtaActive ? 'page' : undefined}
        className={cn(
          'ml-2 inline-flex items-center gap-1.5 h-9 px-3.5 rounded-full text-sm font-semibold',
          'transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400/60',
          inverted
            ? 'bg-amber-300/90 text-stone-900 hover:bg-amber-200 shadow-[0_8px_20px_-8px_rgba(251,191,36,0.7)]'
            : 'bg-stone-900 text-amber-50 hover:bg-stone-800 shadow-[0_8px_20px_-10px_rgba(28,25,23,0.6)]',
        )}
      >
        <Network className="h-4 w-4" aria-hidden="true" />
        <span>{t('nav.cta.label')}</span>
      </Link>

      {/* Divider */}
      <span
        className={cn(
          'mx-2 h-5 w-px',
          inverted ? 'bg-white/15' : 'bg-amber-200/70',
        )}
        aria-hidden="true"
      />

      {/* Language switcher */}
      <div
        className="relative"
        onMouseEnter={() => {
          cancelClose();
          setOpen('lang');
        }}
      >
        <button
          type="button"
          aria-haspopup="menu"
          aria-expanded={open === 'lang'}
          aria-label={t('common.selectLanguage')}
          onClick={() => setOpen(open === 'lang' ? null : 'lang')}
          className={cn(triggerBase, 'gap-1.5', open === 'lang' ? triggerActive : triggerIdle)}
        >
          <Globe2 className="h-3.5 w-3.5" aria-hidden="true" />
          <span className="text-base leading-none" aria-hidden="true">{currentLang.flag}</span>
          <span className="uppercase tracking-wide leading-none text-[12px]">{currentLang.code}</span>
        </button>

        <AnimatePresence>
          {open === 'lang' && (
            <motion.div
              role="menu"
              aria-label={t('common.selectLanguage')}
              variants={panelVariants}
              initial="hidden"
              animate="visible"
              exit="hidden"
              transition={{ duration: 0.16, ease: [0.16, 1, 0.3, 1] }}
              className={cn(
                'absolute right-0 top-[calc(100%+10px)] w-[200px] z-[60] origin-top',
                'rounded-2xl border border-amber-200/60 bg-parchment-50/95 backdrop-blur-md',
                'shadow-[0_24px_60px_-28px_rgba(120,53,15,0.45)] p-1.5',
              )}
              onMouseEnter={cancelClose}
              onMouseLeave={scheduleClose}
            >
              {languages.map((lang) => {
                const active = i18n.language === lang.code;
                return (
                  <button
                    key={lang.code}
                    type="button"
                    role="menuitemradio"
                    aria-checked={active}
                    onClick={() => {
                      if (lang.code !== i18n.language) void i18n.changeLanguage(lang.code);
                      setOpen(null);
                    }}
                    className={cn(
                      'w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm transition-colors',
                      active ? 'bg-amber-100/70 text-amber-900' : 'text-stone-700 hover:bg-amber-50',
                    )}
                  >
                    <span className="text-base leading-none" aria-hidden="true">{lang.flag}</span>
                    <span className="flex-1 text-left font-medium">{lang.nativeName}</span>
                    {active && <Check className="h-3.5 w-3.5 text-amber-700" aria-hidden="true" />}
                  </button>
                );
              })}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* User slot */}
      {isAuthenticated ? (
        <div
          className="relative"
          onMouseEnter={() => {
            cancelClose();
            setOpen('user');
          }}
        >
          <button
            type="button"
            aria-haspopup="menu"
            aria-expanded={open === 'user'}
            aria-label={username ?? t('nav.profile')}
            onClick={() => setOpen(open === 'user' ? null : 'user')}
            className={cn(
              'inline-flex items-center justify-center h-9 w-9 rounded-full transition-colors',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400/60',
              open === 'user'
                ? inverted ? 'bg-white/15 text-white' : 'bg-amber-100 text-amber-900'
                : inverted
                  ? 'bg-white/10 text-white/85 hover:bg-white/15'
                  : 'bg-amber-50 text-amber-800 hover:bg-amber-100/80',
            )}
          >
            <UserIcon className="h-4 w-4" />
          </button>

          <AnimatePresence>
            {open === 'user' && (
              <motion.div
                role="menu"
                variants={panelVariants}
                initial="hidden"
                animate="visible"
                exit="hidden"
                transition={{ duration: 0.16, ease: [0.16, 1, 0.3, 1] }}
                className={cn(
                  'absolute right-0 top-[calc(100%+10px)] w-[220px] z-[60] origin-top',
                  'rounded-2xl border border-amber-200/60 bg-parchment-50/95 backdrop-blur-md',
                  'shadow-[0_24px_60px_-28px_rgba(120,53,15,0.45)] p-2',
                )}
                onMouseEnter={cancelClose}
                onMouseLeave={scheduleClose}
              >
                <div className="px-3 py-2 flex items-center gap-2 border-b border-amber-100/70 mb-1">
                  <span className="h-8 w-8 inline-flex items-center justify-center rounded-full bg-amber-100 text-amber-800">
                    <UserIcon className="h-4 w-4" />
                  </span>
                  <span className="text-sm font-medium text-stone-800 truncate">{username}</span>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    onLogout();
                    setOpen(null);
                  }}
                  role="menuitem"
                  className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-sm text-stone-700 hover:bg-amber-50 hover:text-amber-900 transition-colors"
                >
                  <LogOut className="h-4 w-4" />
                  <span>{t('nav.logout')}</span>
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      ) : (
        <Button
          asChild
          variant="ghost"
          size="sm"
          className={cn(
            'h-9 rounded-full px-3',
            inverted ? 'text-white/85 hover:bg-white/10 hover:text-white' : 'text-stone-700 hover:bg-amber-50',
          )}
        >
          <Link to="/login">
            <LogIn className="h-4 w-4 mr-1.5" />
            {t('nav.login')}
          </Link>
        </Button>
      )}
    </div>
  );
}

export default DesktopNav;
