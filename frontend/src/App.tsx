import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { LogOut, User, Loader2, Menu, X } from 'lucide-react';
import { useState, useEffect, lazy, Suspense } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { AuthProvider, useAuth } from './context/AuthContext';
import { DeviceProvider } from './context/DeviceContext';
import { useKeepAlive } from './hooks/useKeepAlive';
import { AriaLiveProvider, useAriaLive } from './components/AriaLive';
import { ToastProvider } from './components/ui/Toast';
import ErrorBoundary from './components/ErrorBoundary';
// HomePage - lazy loaded below
import LoginPage from './pages/LoginPage';
import DatabasePage from './pages/DatabasePage';
import AboutPage from './pages/AboutPage';
import CreditsPage from './pages/CreditsPage';
import ReportErrorPage from './pages/ReportErrorPage';
import { NotFoundPage } from './components/ui/not-found-page';
import { SkipLinks } from './components/ui/SkipLinks';
import { Button } from './components/ui/button';
import LanguageSwitcher from './components/LanguageSwitcher';
import './index.css';

// Lazy load heavy components for better initial bundle size
// These pages contain large dependencies (Cosmograph, D3, etc.)
const CosmographPage = lazy(() => import('./pages/CosmographPage'));
const SearchPage = lazy(() => import('./pages/SearchPage'));
const GraphRAGPage = lazy(() => import('./pages/GraphRAGPage'));
const GraphRAGShowcase = lazy(() => import('./pages/GraphRAGShowcase'));
const AncientWorksListingPage = lazy(() => import('./pages/AncientWorksListingPage'));
const SimpleTextReader = lazy(() => import('./pages/SimpleTextReader'));
const CanonicalTextReader = lazy(() => import('./pages/CanonicalTextReader'));
const BibliographyPage = lazy(() => import('./pages/BibliographyPage'));

// Phase 6: New pages for analytics, admin, and community features
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'));
const SubmitCorrectionPage = lazy(() => import('./pages/SubmitCorrectionPage'));
const UserProfilePage = lazy(() => import('./pages/UserProfilePage'));

// HowItWorksPage - Explains the system architecture and pipeline
const HowItWorksPage = lazy(() => import('./pages/HowItWorksPage'));

// HomePage - Main landing page with educational content and features overview
const HomePage = lazy(() => import('./pages/HomePage'));

// HowItWorksPage - Scroll-snap redesigned landing
const HowItWorksPage = lazy(() => import('./pages/HowItWorksPage'));

// Helper function to get page titles for screen reader announcements
function getPageTitle(pathname: string): string {
  const routes: Record<string, string> = {
    '/': 'Home',
    '/database': 'Database',
    '/visualizer': 'Knowledge Graph Visualizer',
    '/search': 'Search',
    '/graphrag': 'GraphRAG Q&A',
    '/graphrag-showcase': 'GraphRAG Showcase',
    '/texts': 'Ancient Texts',
    '/bibliography': 'Bibliography',
    '/about': 'About',
    '/how-it-works': 'How It Works',
    '/credits': 'Credits',
    '/login': 'Login',
    '/report-error': 'Report Error',
  };
  return routes[pathname] || 'Page';
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
  return (
    <div className="flex items-center justify-center min-h-[60vh] w-full">
      <div className="text-center space-y-4">
        <Loader2 className="w-12 h-12 animate-spin text-primary-600 mx-auto" />
        <p className="text-academic-muted font-medium">Loading page...</p>
      </div>
    </div>
  );
}

function AppContent() {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user, logout, isAuthenticated } = useAuth();
  const { announce } = useAriaLive();
  const { t } = useTranslation();

  // Enable keep-alive to prevent backend from sleeping (Render free tier)
  useKeepAlive();




  // Global keyboard shortcuts - DISABLED to allow normal typing
  // Commenting out all keyboard shortcuts as they interfere with user input
  // especially shift+? which prevents typing the ? character
  /*
  useKeyboardShortcuts({
    shortcuts: [
      {
        key: 'k',
        ctrl: true,
        callback: () => {
          navigate('/search');
          announce('Navigated to search page', 'polite');
        },
      },
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

  // Reset mobile menu when location changes
  useEffect(() => {
    setMobileMenuOpen(false);

    // Announce page changes to screen readers
    const pageTitle = getPageTitle(location.pathname);
    if (pageTitle) {
      announce(`Navigated to ${pageTitle}`, 'polite');
    }
  }, [location.pathname, announce]);

  // Check if current page should hide footer (full-screen pages)
  const hideFooter = location.pathname === '/' || location.pathname === '/how-it-works' || ['/visualizer', '/graph'].some(path =>
    location.pathname === path || location.pathname.startsWith(`${path}/`)
  );

  return (
    <div className="min-h-screen bg-academic-bg m-0 p-0">
      {/* Skip Links for Accessibility */}
      <SkipLinks />

      {/* Keyboard Shortcuts Help - DISABLED */}
      {/*
      <KeyboardShortcutsHelp
        isOpen={showKeyboardHelp}
        onClose={() => setShowKeyboardHelp(false)}
      />
      */}

      {/* Header / Navigation */}
      <header className="bg-academic-paper border-b border-academic-border shadow-sm fixed top-0 left-0 right-0 z-50 m-0" id="navigation" style={{ marginTop: 0, paddingTop: 0 }}>
        <nav className="academic-container" style={{ marginTop: 0, paddingTop: 0 }}>
          <div className="flex items-center justify-between py-1 sm:py-0 sm:h-12">
            {/* Logo */}
            <Link
              to="/"
              className="hover:opacity-80 transition-opacity flex-shrink-0 group"
              aria-label="EleutherIA Home"
            >
              <img
                src="/logo.svg"
                alt="EleutherIA - Ancient Free Will Database"
                className="h-10 sm:h-20 w-auto transition-transform group-hover:scale-105"
              />
            </Link>

            {/* Navigation Links - Hidden on mobile */}
            <div className="hidden lg:flex items-center space-x-6">
              <NavLink to="/how-it-works">How it works</NavLink>
              <NavLink to="/database">{t('nav.database')}</NavLink>
              <NavLink to="/visualizer">{t('nav.visualizer')}</NavLink>
              <NavLink to="/search">{t('nav.search')}</NavLink>
              <NavLink to="/graphrag">{t('nav.graphrag')}</NavLink>
              <NavLink to="/texts">{t('nav.texts')}</NavLink>
              <NavLink to="/bibliography">{t('nav.bibliography')}</NavLink>
              <NavLink to="/about">{t('nav.about')}</NavLink>
              <NavLink to="/how-it-works">{t('nav.howItWorks')}</NavLink>

              {/* Language Switcher */}
              <LanguageSwitcher variant="dropdown" />


              {/* User Menu - Only show when authenticated */}
              {isAuthenticated && (
                <div className="flex items-center space-x-2">
                  <div className="flex items-center space-x-2 text-sm text-academic-muted">
                    <User className="w-4 h-4" />
                    <span>{user?.username}</span>
                  </div>
                  <Button
                    onClick={logout}
                    variant="ghost"
                    size="sm"
                    aria-label={t('nav.logout')}
                  >
                    <LogOut className="w-4 h-4 mr-1" />
                    {t('nav.logout')}
                  </Button>
                </div>
              )}
            </div>

            {/* Mobile Menu Button with Animation */}
            <button
              className="lg:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-expanded={mobileMenuOpen}
              aria-controls="mobile-menu"
              aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
            >
              <AnimatePresence mode="wait">
                {mobileMenuOpen ? (
                  <motion.div
                    key="close"
                    initial={{ rotate: -90, opacity: 0 }}
                    animate={{ rotate: 0, opacity: 1 }}
                    exit={{ rotate: 90, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <X className="w-5 h-5" />
                  </motion.div>
                ) : (
                  <motion.div
                    key="menu"
                    initial={{ rotate: 90, opacity: 0 }}
                    animate={{ rotate: 0, opacity: 1 }}
                    exit={{ rotate: -90, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <Menu className="w-5 h-5" />
                  </motion.div>
                )}
              </AnimatePresence>
            </button>
          </div>

          {/* Enhanced Mobile Menu with Animation */}
          <AnimatePresence>
            {mobileMenuOpen && (
              <motion.div
                id="mobile-menu"
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.3, ease: 'easeInOut' }}
                className="lg:hidden border-t border-academic-border overflow-hidden"
              >
                <div className="py-2 space-y-1">
                  {[
                    { to: '/how-it-works', label: 'How it works' },
                    { to: '/database', label: t('nav.database') },
                    { to: '/visualizer', label: t('nav.visualizer') },
                    { to: '/search', label: t('nav.search') },
                    { to: '/graphrag', label: t('nav.graphrag') },
                    { to: '/texts', label: t('nav.texts') },
                    { to: '/bibliography', label: t('nav.bibliography') },
                    { to: '/about', label: t('nav.about') },
                    { to: '/how-it-works', label: t('nav.howItWorks') },
                    { to: '/credits', label: t('nav.credits') },
                  ].map((item, index) => (
                    <motion.div
                      key={item.to}
                      initial={{ x: -20, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      transition={{ delay: index * 0.05 }}
                    >
                      <NavLink to={item.to}>{item.label}</NavLink>
                    </motion.div>
                  ))}

                  {/* Language Switcher - Mobile */}
                  <motion.div
                    initial={{ x: -20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: 0.45 }}
                    className="pt-2 px-2"
                  >
                    <LanguageSwitcher variant="inline" />
                  </motion.div>

                  {/* Mobile User Menu */}
                  {isAuthenticated && (
                    <motion.div
                      initial={{ x: -20, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      transition={{ delay: 0.45 }}
                      className="flex items-center justify-between pt-2 border-t border-academic-border"
                    >
                      <div className="flex items-center space-x-2 text-sm text-academic-muted">
                        <User className="w-4 h-4" />
                        <span>{user?.username}</span>
                      </div>
                      <Button
                        onClick={logout}
                        variant="ghost"
                        size="sm"
                      >
                        <LogOut className="w-4 h-4 mr-1" />
                        Logout
                      </Button>
                    </motion.div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </nav>
      </header>

        {/* Main Content */}
        <main id="main-content" className="w-full">
          <ErrorBoundary>
            <Suspense fallback={<PageLoadingFallback />}>
              <Routes>
              <Route path="/" element={<Suspense fallback={<PageLoadingFallback />}><HomePage /></Suspense>} />
              <Route path="/how-it-works" element={<Suspense fallback={<PageLoadingFallback />}><HowItWorksPage /></Suspense>} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/database" element={<DatabasePage />} />
              <Route path="/visualizer" element={<CosmographPage />} />
              <Route path="/visualizer/:nodeId" element={<CosmographPage />} />
              <Route path="/graph" element={<CosmographPage />} />
              <Route path="/graph/:nodeId" element={<CosmographPage />} />
              <Route path="/search" element={<SearchPage />} />
              <Route path="/graphrag" element={<GraphRAGPage />} />
              <Route path="/graphrag-showcase" element={<GraphRAGShowcase />} />
              <Route path="/texts" element={<AncientWorksListingPage />} />
              <Route path="/texts/:textId" element={<CanonicalTextReader />} />
              <Route path="/simple/:textId" element={<SimpleTextReader />} />
              <Route path="/bibliography" element={<BibliographyPage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="/how-it-works" element={<Suspense fallback={<PageLoadingFallback />}><HowItWorksPage /></Suspense>} />
              <Route path="/credits" element={<CreditsPage />} />
              <Route path="/report-error" element={<ReportErrorPage />} />
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

        {/* Footer - Hidden on full-screen pages */}
        {!hideFooter && (
        <footer className="bg-academic-paper border-t border-academic-border mt-2">
          <div className="academic-container py-2">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="pb-2 sm:pb-0">
                <h3 className="font-semibold text-sm mb-2">About EleutherIA</h3>
                <p className="text-xs text-academic-muted leading-relaxed">
                  A FAIR-compliant knowledge graph documenting ancient debates on free will, fate,
                  and moral responsibility from Classical Greek philosophy (6th c. BCE) through Late Antiquity (6th c. CE).
                </p>
              </div>

              <div className="pb-2 sm:pb-0">
                <h3 className="font-semibold text-sm mb-2">Data</h3>
                <ul className="text-xs text-academic-muted space-y-1">
                  <li>2,193 Knowledge Graph Nodes</li>
                  <li>8,616 Edges & Relationships</li>
                  <li>189 Ancient Works</li>
                  <li>16,968 Passages</li>
                </ul>
              </div>

              <div className="pb-2 sm:pb-0">
                <h3 className="font-semibold text-sm mb-2">Citation</h3>
                <p className="text-xs text-academic-muted leading-relaxed break-words">
                  Girardi, R. (2025). <span className="italic">EleutherIA: Ancient Free Will Database</span>.
                  Zenodo. <a href="https://doi.org/10.5281/zenodo.17379490" className="text-primary-600 hover:underline break-all">
                    https://doi.org/10.5281/zenodo.17379490
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
                  <span>GitHub</span>
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
                  <span>LinkedIn</span>
                </a>
              </div>
              <p className="px-4">
                © 2025 Romain Girardi | Licensed under{' '}
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

// Navigation Link Component
function NavLink({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <Link
      to={to}
      className="text-academic-text hover:text-primary-600 font-medium text-sm transition-colors block lg:inline-block py-0.5 lg:py-0 rounded px-2 lg:px-0 hover:bg-gray-50 lg:hover:bg-transparent"
    >
      {children}
    </Link>
  );
}

export default App;
