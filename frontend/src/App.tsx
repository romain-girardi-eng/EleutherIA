import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Loader2, Menu, X } from 'lucide-react';
import { cn } from './lib/utils';
import { useState, useEffect, useLayoutEffect, lazy, Suspense } from 'react';
import { useTranslation } from 'react-i18next';
import type { TFunction } from 'i18next';
import { AuthProvider, useAuth } from './context/AuthContext';
import { DeviceProvider } from './context/DeviceContext';
import { useKeepAlive } from './hooks/useKeepAlive';
import { useKgStats, formatCount } from './hooks/useKgStats';
import { AriaLiveProvider, useAriaLive } from './components/AriaLive';
import { ToastProvider } from './components/ui/Toast';
import ErrorBoundary from './components/ErrorBoundary';
import ProtectedRoute from './components/ProtectedRoute';
import { Glow } from './components/ui/glow';
import { PremiumBackground } from './components/ui/premium-background';
import { CandlelightCursor } from './components/ui/candlelight-cursor';
import { ShaderBackground } from './components/ui/shader-background';
import { NotFoundPage } from './components/ui/not-found-page';
import { SkipLinks } from './components/ui/SkipLinks';
import { DesktopNav } from './components/DesktopNav';
import { SeoManager } from './components/SeoManager';
import './index.css';

const FULL_SCREEN_EXCLUDED_SKIP_TARGETS = ['footer'];
const ALL_SKIP_TARGETS: string[] = [];

// Lazy load heavy components for better initial bundle size
// These pages contain large dependencies (Cosmograph, D3, etc.)
const CosmographPage = lazy(() => import('./pages/CosmographPage'));
const GraphRAGPage = lazy(() => import('./pages/GraphRAGPage'));
const GraphRAGShowcase = lazy(() => import('./pages/GraphRAGShowcase'));
const ResearchPage = lazy(() => import('./pages/Research'));
const AncientWorksListingPage = lazy(() => import('./pages/AncientWorksListingPage'));
const SimpleTextReader = lazy(() => import('./pages/SimpleTextReader'));
const CanonicalTextReader = lazy(() => import('./pages/CanonicalTextReader'));
const BibliographyPage = lazy(() => import('./pages/BibliographyPage'));
const BookReaderPage = lazy(() => import('./components/book-reader/BookReaderPage'));
const DatabasePage = lazy(() => import('./pages/DatabasePage'));
const AboutPage = lazy(() => import('./pages/AboutPage'));
const CreditsPage = lazy(() => import('./pages/CreditsPage'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
const AccountRequestPage = lazy(() => import('./pages/AccountRequestPage'));
const ReportErrorPage = lazy(() => import('./pages/ReportErrorPage'));
const MobileMenu = lazy(() =>
  import('./components/MobileMenu').then((module) => ({ default: module.MobileMenu })),
);

// Shared trace read-only page
const SharedTracePage = lazy(() => import('./pages/SharedTracePage'));

// Phase 6: New pages for analytics, admin, and community features
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'));
const SubmitCorrectionPage = lazy(() => import('./pages/SubmitCorrectionPage'));
const UserProfilePage = lazy(() => import('./pages/UserProfilePage'));

// Community Q&A gallery — public researches
const CommunityPage = lazy(() => import('./pages/CommunityPage'));
const CommunityDetailPage = lazy(() => import('./pages/CommunityDetailPage'));

// Canonical passages — reception map of the corpus
const CanonicalPassagesPage = lazy(() => import('./pages/CanonicalPassagesPage'));
const CanonicalPassageDetailPage = lazy(() => import('./pages/CanonicalPassageDetailPage'));

// HowItWorksPage - Scroll-snap redesigned landing
const HowItWorksPage = lazy(() => import('./pages/HowItWorksPage'));

// Contribute Page - PDF upload + extraction review for community contributions
const ContributePage = lazy(() => import('./pages/ContributePage'));

// Community contributions gallery + moderation dashboard
const ContributionsListPage = lazy(() => import('./pages/ContributionsListPage'));
const ContributionDetailPage = lazy(() => import('./pages/ContributionDetailPage'));

// HomePage - Main landing page with educational content and features overview
const HomePage = lazy(() => import('./pages/HomePage'));

// Research Projects — personal document workspace (authenticated)
const ProjectsPage = lazy(() => import('./pages/ProjectsPage'));
const ProjectDetailPage = lazy(() => import('./pages/ProjectDetailPage'));

// The Debate - scrollytelling narrative of the ancient free-will debate
const TheDebatePage = lazy(() => import('./pages/TheDebatePage'));
// Debate Map - argument map for a single concept (timeline + argument mapper)
const DebateMapPage = lazy(() => import('./pages/DebateMapPage'));

// Glossary + FAQ - grounded scholarly reference pages (GEO/SEO content)
const GlossaryPage = lazy(() => import('./pages/GlossaryPage'));
const FAQPage = lazy(() => import('./pages/FAQPage'));

// Helper function to get page titles for screen reader announcements
function getPageTitle(pathname: string, t: TFunction): string {
  const routes: Record<string, string> = {
    '/': t('appShell.pageTitles.home'),
    '/database': t('appShell.pageTitles.database'),
    '/visualizer': t('appShell.pageTitles.visualizer'),
    '/graphrag': t('appShell.pageTitles.graphrag'),
    '/graphrag-showcase': t('appShell.pageTitles.graphragShowcase'),
    '/recherches': t('appShell.pageTitles.recherches'),
    '/contributions': t('appShell.pageTitles.contributions'),
    '/passages-canoniques': t('appShell.pageTitles.canonicalPassages'),
    '/research': t('appShell.pageTitles.research'),
    '/texts': t('appShell.pageTitles.texts'),
    '/bibliography': t('appShell.pageTitles.bibliography'),
    '/about': t('appShell.pageTitles.about'),
    '/glossary': t('nav.glossary'),
    '/faq': t('nav.faq'),
    '/how-it-works': t('appShell.pageTitles.howItWorks'),
    '/the-debate': t('nav.theDebate'),
    '/credits': t('appShell.pageTitles.credits'),
    '/login': t('appShell.pageTitles.login'),
    '/request-account': t('appShell.pageTitles.requestAccount'),
    '/report-error': t('appShell.pageTitles.reportError'),
  };
  return routes[pathname] || t('appShell.pageTitles.default');
}

function App() {
  return (
    <DeviceProvider>
      <AuthProvider>
        <ToastProvider>
          <AriaLiveProvider>
            <Router>
              <AppContent />
            </Router>
          </AriaLiveProvider>
        </ToastProvider>
      </AuthProvider>
    </DeviceProvider>
  );
}



// Loading fallback component for lazy-loaded pages
function PageLoadingFallback() {
  const { t } = useTranslation();

  return (
    <div className="flex items-center justify-center min-h-[60vh] w-full">
      <div className="text-center space-y-4">
        <Loader2 className="w-12 h-12 animate-spin text-primary-600 mx-auto" />
        <p className="text-academic-muted font-medium">{t('appShell.loadingPage')}</p>
      </div>
    </div>
  );
}

function AppContent() {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user, logout, isAuthenticated } = useAuth();
  const { announce } = useAriaLive();
  const { t, i18n } = useTranslation();
  const stats = useKgStats();
  const fmt = (n: number) => formatCount(n, i18n.language);

  // Enable keep-alive to prevent backend from sleeping (Render free tier)
  useKeepAlive();




  // Global keyboard shortcuts - DISABLED to allow normal typing
  // Commenting out all keyboard shortcuts as they interfere with user input
  // especially shift+? which prevents typing the ? character
  /*
  useKeyboardShortcuts({
    shortcuts: [
      {
        key: 'Escape',
        callback: () => {
          if (mobileMenuOpen) {
            setMobileMenuOpen(false);
            announce('Menu closed', 'polite');
          }
        },
      },
      {
        key: 'h',
        ctrl: true,
        callback: () => {
          navigate('/');
          announce('Navigated to home page', 'polite');
        },
      },
      {
        key: '?',
        shift: true,
        callback: () => {
          setShowKeyboardHelp(!showKeyboardHelp);
          announce(showKeyboardHelp ? 'Keyboard shortcuts help closed' : 'Keyboard shortcuts help opened', 'polite');
        },
      },
    ],
  });
  */

  // Reset mobile menu when location changes.
  //
  // CRITICAL: do NOT depend on `announce` or `t`. `t` (react-i18next) often
  // returns a new function reference on render and `announce` comes through
  // a context value object that gets re-created on every provider render.
  // Listing them here re-fires this effect within a few hundred ms of every
  // render, which would re-set `mobileMenuOpen = false` and slam the burger
  // drawer shut the moment the user opens it — that's exactly the bug we
  // chased through three rounds of touch/z-index fixes.
  useEffect(() => {
    setMobileMenuOpen(false);

    // Announce page changes to screen readers
    const pageTitle = getPageTitle(location.pathname, t);
    if (pageTitle) {
      announce(`Navigated to ${pageTitle}`, 'polite');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  const isHomePage = location.pathname === '/';

  // Scroll-lock the homepage at the App shell level.
  //
  // Mid-2025+ iOS Safari (iPhone 16 + iOS 18) ignores body{position:fixed;
  // overflow:hidden} *alone* — the user reported being able to scroll
  // even in private-tab mode after every CSS-only attempt. The only
  // bulletproof recipe is the CSS belt-and-braces PLUS a non-passive
  // `touchmove` listener at the document level that calls
  // preventDefault() while we're on the homepage. Together they kill
  // the rubber-band gesture AND the document scroll itself.
  useLayoutEffect(() => {
    if (!isHomePage) return;
    const html = document.documentElement;
    const body = document.body;
    const prev = {
      htmlHeight: html.style.height,
      htmlOverflow: html.style.overflow,
      htmlOverscroll: html.style.overscrollBehavior,
      bodyHeight: body.style.height,
      bodyOverflow: body.style.overflow,
      bodyPosition: body.style.position,
      bodyTop: body.style.top,
      bodyLeft: body.style.left,
      bodyRight: body.style.right,
      bodyWidth: body.style.width,
      bodyOverscroll: body.style.overscrollBehavior,
      bodyTouchAction: body.style.touchAction,
    };
    window.scrollTo(0, 0);
    html.style.height = '100dvh';
    html.style.overflow = 'hidden';
    html.style.overscrollBehavior = 'none';
    body.style.height = '100dvh';
    body.style.overflow = 'hidden';
    body.style.position = 'fixed';
    body.style.top = '0';
    body.style.left = '0';
    body.style.right = '0';
    body.style.width = '100%';
    body.style.overscrollBehavior = 'none';
    // NOTE: do NOT set `body.style.touchAction = 'none'`. Per the Pointer
    // Events spec the effective touch-action of any descendant is computed
    // from the whole hit-test chain — a `none` on body cascades down and
    // suppresses tap→click conversion on buttons, even when those buttons
    // declare `touch-action: manipulation` themselves. The touchmove
    // swallow listener below already kills rubber-band/scroll on iOS 18
    // without needing the body-level CSS hammer.

    // iOS 18 Safari hard lock: swallow touchmove at the document level.
    // `passive: false` is required for preventDefault to take effect.
    //
    // The subtle bit: we cannot rely on `event.target` of the *touchmove*,
    // because a 1-2px finger jitter can shift the target from the button
    // onto a parent that isn't interactive. preventDefault then cancels
    // the tap gesture and the click never fires — that's why the burger
    // would mute under iOS even though the button is on top of the stack.
    // Anchor the decision on touchstart instead: if the gesture *began*
    // on an interactive element, it stays interactive for its full life.
    const INTERACTIVE_SELECTOR =
      'button, a, input, textarea, select, [contenteditable="true"], [data-allow-touch="true"]';
    let gestureIsInteractive = false;
    const onTouchStart = (event: TouchEvent) => {
      const target = event.target as HTMLElement | null;
      gestureIsInteractive = !!target?.closest(INTERACTIVE_SELECTOR);
    };
    const endGesture = () => {
      gestureIsInteractive = false;
    };
    const swallow = (event: TouchEvent) => {
      if (gestureIsInteractive) return;
      const target = event.target as HTMLElement | null;
      if (target?.closest(INTERACTIVE_SELECTOR)) return;
      event.preventDefault();
    };
    document.addEventListener('touchstart', onTouchStart, { passive: true });
    document.addEventListener('touchend', endGesture, { passive: true });
    document.addEventListener('touchcancel', endGesture, { passive: true });
    document.addEventListener('touchmove', swallow, { passive: false });

    return () => {
      document.removeEventListener('touchstart', onTouchStart);
      document.removeEventListener('touchend', endGesture);
      document.removeEventListener('touchcancel', endGesture);
      document.removeEventListener('touchmove', swallow);
      html.style.height = prev.htmlHeight;
      html.style.overflow = prev.htmlOverflow;
      html.style.overscrollBehavior = prev.htmlOverscroll;
      body.style.height = prev.bodyHeight;
      body.style.overflow = prev.bodyOverflow;
      body.style.position = prev.bodyPosition;
      body.style.top = prev.bodyTop;
      body.style.left = prev.bodyLeft;
      body.style.right = prev.bodyRight;
      body.style.width = prev.bodyWidth;
      body.style.overscrollBehavior = prev.bodyOverscroll;
      body.style.touchAction = prev.bodyTouchAction;
    };
  }, [isHomePage]);

  // Dark-themed pages where the glow should be hidden
  const isDarkPage = isHomePage || location.pathname === '/how-it-works' || location.pathname === '/the-debate' || ['/visualizer', '/graph'].some(path =>
    location.pathname === path || location.pathname.startsWith(`${path}/`)
  );

  // Check if current page should hide footer (full-screen pages)
  const hideFooter = isDarkPage;

  return (
    <div className="min-h-screen bg-transparent m-0 p-0">
      <SeoManager />

      {/* Skip Links for Accessibility */}
      <SkipLinks
        excludeTargets={hideFooter ? FULL_SCREEN_EXCLUDED_SKIP_TARGETS : ALL_SKIP_TARGETS}
      />

      {/* Premium animated background — warm drifting orbs + glow */}
      {!isDarkPage && (
        <>
          <ShaderBackground />
          <PremiumBackground />
          <CandlelightCursor />
          <div className="fixed inset-0 pointer-events-none overflow-hidden" style={{ zIndex: 0 }}>
            <Glow variant="top" className="opacity-25" />
          </div>
        </>
      )}

      {/* Keyboard Shortcuts Help - DISABLED */}
      {/*
      <KeyboardShortcutsHelp
        isOpen={showKeyboardHelp}
        onClose={() => setShowKeyboardHelp(false)}
      />
      */}

      {/* Header / Navigation */}
      <header
        className={cn(
          "fixed top-0 left-0 right-0 z-50 m-0 pointer-events-auto touch-manipulation pt-safe",
          // Desktop (lg+): warm parchment on inner pages, white on homepage
          isHomePage
            ? "lg:bg-academic-paper lg:border-b lg:border-academic-border lg:shadow-sm"
            : "lg:bg-parchment-50 lg:border-b lg:border-amber-200/40 lg:shadow-sm",
          // Mobile: transparent overlay on homepage, warm parchment otherwise
          isHomePage ? "bg-transparent" : "bg-parchment-50 border-b border-amber-200/40 shadow-sm"
        )}
        id="navigation"
      >
        <nav className="academic-container" style={{ marginTop: 0, paddingTop: 0 }}>
          <div className="flex items-center justify-between py-1 sm:py-0 sm:h-12">
            {/* Logo */}
            <Link
              to="/"
              className={cn(
                "hover:opacity-80 transition-opacity flex-shrink-0 group",
                // On homepage mobile, hide the header logo — it's shown in the hero section
                isHomePage ? "hidden lg:block" : ""
              )}
              aria-label={t('appShell.logoHomeAria')}
            >
              <img
                src="/logo-880.webp"
                alt={t('appShell.logoAlt')}
                width={220}
                height={96}
                className="h-10 sm:h-20 w-auto transition-transform group-hover:scale-105"
              />
            </Link>

            {/* Desktop nav — grouped dropdowns, CTA, lang & user (>= lg). */}
            <DesktopNav
              inverted={false}
              isAuthenticated={isAuthenticated}
              username={user?.username}
              userRole={user?.role}
              onLogout={logout}
            />

            {/* Mobile Menu Button with Animation */}
            <button
              className={cn(
                "lg:hidden relative z-[55] min-h-11 min-w-11 flex items-center justify-center -m-1 rounded-lg transition-colors touch-manipulation",
                // Mobile = parchment palette on every page (incl. home).
                // Desktop on home stays on the dark-friendly white variant.
                isHomePage
                  ? "text-stone-700 hover:bg-amber-100/60 ml-auto lg:text-white lg:hover:bg-white/10"
                  : "text-stone-600 hover:bg-stone-100"
              )}
              data-allow-touch="true"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-expanded={mobileMenuOpen}
              aria-controls="mobile-menu"
              aria-label={mobileMenuOpen ? t('nav.closeMenu') : t('nav.openMenu')}
            >
              <span
                className={cn(
                  "inline-flex transition-transform duration-200 pointer-events-none",
                  mobileMenuOpen ? "rotate-90" : "rotate-0",
                )}
                aria-hidden="true"
              >
                {mobileMenuOpen ? (
                  <X className="w-5 h-5 pointer-events-none" />
                ) : (
                  <Menu className="w-5 h-5 pointer-events-none" />
                )}
              </span>
            </button>
          </div>

        </nav>

        {/* Full-screen mobile drawer — replaces the inline strip menu */}
        {mobileMenuOpen && (
          <Suspense fallback={null}>
            <MobileMenu
              open={mobileMenuOpen}
              onClose={() => setMobileMenuOpen(false)}
              isAuthenticated={isAuthenticated}
              username={user?.username}
              userRole={user?.role}
              onLogout={logout}
            />
          </Suspense>
        )}
      </header>

        {/* Main Content */}
        <main id="main-content" className="w-full">
          <ErrorBoundary>
            <Suspense fallback={<PageLoadingFallback />}>
              <Routes>
              <Route path="/" element={<Suspense fallback={<PageLoadingFallback />}><HomePage /></Suspense>} />
              <Route path="/how-it-works" element={<Suspense fallback={<PageLoadingFallback />}><HowItWorksPage /></Suspense>} />
              <Route path="/the-debate" element={<TheDebatePage />} />
              <Route path="/debate/:conceptId" element={<DebateMapPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/request-account" element={<AccountRequestPage />} />
              <Route path="/database" element={<DatabasePage />} />
              <Route path="/visualizer/:nodeId?" element={<CosmographPage />} />
              <Route path="/graph/:nodeId?" element={<CosmographPage />} />
              <Route path="/graphrag" element={<GraphRAGPage />} />
              <Route path="/graphrag-showcase" element={<GraphRAGShowcase />} />
              <Route path="/research" element={<ResearchPage />} />
              <Route path="/texts" element={<AncientWorksListingPage />} />
              <Route path="/texts/:textId" element={<BookReaderPage />} />
              <Route path="/texts/:textId/scroll" element={<CanonicalTextReader />} />
              <Route path="/simple/:textId" element={<SimpleTextReader />} />
              <Route path="/bibliography" element={<BibliographyPage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="/glossary" element={<GlossaryPage />} />
              <Route path="/faq" element={<FAQPage />} />
              <Route path="/credits" element={<CreditsPage />} />
              <Route path="/report-error" element={<ReportErrorPage />} />
              {/* Public shared trace */}
              <Route path="/share/:token" element={<SharedTracePage />} />
              {/* Public community researches gallery */}
              <Route path="/recherches" element={<CommunityPage />} />
              <Route path="/recherches/:slug" element={<CommunityDetailPage />} />
              {/* Community contributions gallery + moderation dashboard */}
              <Route path="/contributions" element={<ContributionsListPage />} />
              <Route path="/contributions/:id" element={<ContributionDetailPage />} />
              {/* Canonical passages — reception map */}
              <Route path="/passages-canoniques" element={<CanonicalPassagesPage />} />
              <Route
                path="/passages-canoniques/:passage_id"
                element={<CanonicalPassageDetailPage />}
              />
              {/* Community PDF contribution (authenticated) */}
              <Route
                path="/contribuer"
                element={
                  <ProtectedRoute>
                    <ContributePage />
                  </ProtectedRoute>
                }
              />
              {/* Research project space (authenticated) */}
              <Route
                path="/projects"
                element={
                  <ProtectedRoute>
                    <ProjectsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/projects/:projectId"
                element={
                  <ProtectedRoute>
                    <ProjectDetailPage />
                  </ProtectedRoute>
                }
              />
              {/* Admin and Community Features */}
              <Route path="/admin" element={<AdminDashboard />} />
              <Route path="/community/contribute" element={<SubmitCorrectionPage />} />
              <Route path="/profile" element={<UserProfilePage />} />
              <Route path="/profile/:userId" element={<UserProfilePage />} />
              {/* 404 - Catch all unmatched routes */}
              <Route path="*" element={<NotFoundPage />} />
              </Routes>
            </Suspense>
          </ErrorBoundary>
        </main>

        {/* Footer - Hidden on full-screen pages.
            Mobile (< md): a single compact line — no 3-column grid, no
            social-icon row. The vertical space the full footer ate on
            phones wasn't worth its content. */}
        {!hideFooter && (
        <footer id="footer" className="bg-academic-paper border-t border-academic-border mt-2">
          {/* Compact mobile footer */}
          <div className="md:hidden academic-container py-3 text-center text-[11px] text-academic-muted">
            <p className="break-words">
              © 2025 Romain Girardi ·{' '}
              <a href="https://creativecommons.org/licenses/by/4.0/" className="text-primary-600 hover:underline">
                CC BY 4.0
              </a>{' '}
              ·{' '}
              <a
                href="https://github.com/romain-girardi-eng/EleutherIA"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary-600 hover:underline"
              >
                GitHub
              </a>
            </p>
          </div>
          {/* Full footer (md+) */}
          <div className="hidden md:block academic-container py-2">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="pb-2 sm:pb-0">
                <h3 className="font-semibold text-sm mb-2">{t('appShell.footer.aboutTitle')}</h3>
                <p className="text-xs text-academic-muted leading-relaxed">
                  {t('appShell.footer.aboutBody')}
                </p>
              </div>

              <div className="pb-2 sm:pb-0">
                <h3 className="font-semibold text-sm mb-2">{t('appShell.footer.dataTitle')}</h3>
                <ul className="text-xs text-academic-muted space-y-1">
                  <li>{t('appShell.footer.stats.nodes', { nodes: fmt(stats.nodes) })}</li>
                  <li>{t('appShell.footer.stats.edges', { edges: fmt(stats.edges) })}</li>
                  <li>{t('appShell.footer.stats.works', { works: fmt(stats.works) })}</li>
                  <li>{t('appShell.footer.stats.passages', { passages: fmt(stats.passages) })}</li>
                </ul>
              </div>

              <div className="pb-2 sm:pb-0">
                <h3 className="font-semibold text-sm mb-2">{t('appShell.footer.citationTitle')}</h3>
                <p className="text-xs text-academic-muted leading-relaxed break-words">
                  Girardi, R. (2025). <span className="italic">EleutherIA: Ancient Free Will Database</span>.
                  Zenodo. <a href="https://doi.org/10.5281/zenodo.17379489" className="text-primary-600 hover:underline break-all">
                    https://doi.org/10.5281/zenodo.17379489
                  </a>
                </p>
              </div>
            </div>

            <div className="mt-3 pt-2 border-t border-academic-border text-center text-xs text-academic-muted">
              <div className="flex flex-wrap justify-center items-center gap-2 mb-2">
                <a
                  href="https://github.com/romain-girardi-eng/EleutherIA"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline inline-flex items-center gap-1"
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
                    <path fillRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.17 6.839 9.49.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.167 22 16.418 22 12c0-5.523-4.477-10-10-10z" clipRule="evenodd" />
                  </svg>
                  <span>{t('appShell.footer.github')}</span>
                </a>
                <a
                  href="https://orcid.org/0000-0002-5310-5346"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline inline-flex items-center gap-1"
                >
                  <svg className="w-4 h-4 flex-shrink-0" viewBox="0 0 256 256" fill="currentColor">
                    <path d="M256,128c0,70.7-57.3,128-128,128C57.3,256,0,198.7,0,128C0,57.3,57.3,0,128,0C198.7,0,256,57.3,256,128z M86.3,186.2H70.9V79.1h15.4v48.4V186.2z M108.9,79.1h41.6c39.6,0,57,28.3,57,53.6c0,27.5-21.5,53.6-56.8,53.6h-41.8V79.1z M124.3,172.4h24.5c34.9,0,42.9-26.5,42.9-39.7c0-21.5-13.7-39.7-43.7-39.7h-23.7V172.4z M78.2,59.1c5.1,0,9.2,4.1,9.2,9.2c0,5.1-4.1,9.2-9.2,9.2c-5.1,0-9.2-4.1-9.2-9.2C69,63.2,73.1,59.1,78.2,59.1z"/>
                  </svg>
                  <span>ORCID</span>
                </a>
                <a
                  href="https://www.linkedin.com/in/romain-girardi"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline inline-flex items-center gap-1"
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                  </svg>
                  <span>{t('appShell.footer.linkedIn')}</span>
                </a>
              </div>
              <p className="px-4">
                © 2025 Romain Girardi | {t('appShell.footer.licensedUnder')}{' '}
                <a href="https://creativecommons.org/licenses/by/4.0/" className="text-primary-600 hover:underline">
                  CC BY 4.0
                </a>
              </p>
            </div>
          </div>
        </footer>
        )}
      </div>
  );
}

export default App;
