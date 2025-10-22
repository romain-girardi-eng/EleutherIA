import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { HelpCircle, LogOut, User } from 'lucide-react';
import { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import KGVisualizerPage from './pages/KGVisualizerPage';
import SearchPage from './pages/SearchPage';
import GraphRAGPage from './pages/GraphRAGPage';
import TextExplorerPage from './pages/TextExplorerPage';
import DatabasePage from './pages/DatabasePage';
import BibliographyPage from './pages/BibliographyPage';
import AboutPage from './pages/AboutPage';
import ReportErrorPage from './pages/ReportErrorPage';
import InteractiveTour from './components/InteractiveTour';
import './index.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <AppContent />
      </Router>
    </AuthProvider>
  );
}

// Page-specific tour configurations
const pageTours: Record<string, { title: string; steps: Array<{ title: string; content: string; target: string }> }> = {
  '/': {
    title: 'Welcome to EleutherIA',
    steps: [
      {
        title: 'Welcome to EleutherIA',
        content: 'A comprehensive knowledge graph documenting ancient debates on free will from Aristotle to Boethius. Let us guide you through the key features.',
        target: 'body'
      },
      {
        title: 'Knowledge Graph',
        content: 'Start here to explore the network of 505 philosophical concepts, arguments, and thinkers. Visualize complex relationships in an interactive graph.',
        target: '[data-tour="kg-card"]'
      },
      {
        title: 'Hybrid Search',
        content: 'Search across 289 ancient texts using full-text, lemmatic, or AI-powered semantic search to find exactly what you need.',
        target: '[data-tour="search-card"]'
      },
      {
        title: 'GraphRAG Q&A',
        content: 'Ask questions in natural language and receive scholarly answers grounded in the knowledge graph with proper citations.',
        target: '[data-tour="graphrag-card"]'
      },
      {
        title: 'Ancient Texts',
        content: 'Browse and read 289 ancient Greek and Latin texts with advanced lemmatization for deeper textual analysis.',
        target: '[data-tour="texts-card"]'
      },
      {
        title: 'Database Statistics',
        content: 'Our database contains over 860 verified citations from ancient sources and modern scholarship, ensuring academic rigor.',
        target: '[data-tour="stats"]'
      }
    ]
  },
  '/visualizer': {
    title: 'Knowledge Graph Visualizer',
    steps: [
      {
        title: 'Interactive Knowledge Graph',
        content: 'Explore 505 nodes and 870 relationships representing ancient philosophical debates on free will.',
        target: 'body'
      },
      {
        title: 'Graph Controls',
        content: 'Use these controls to filter nodes by type, change layout algorithms, and customize the visualization.',
        target: '[data-tour="graph-controls"]'
      },
      {
        title: 'Node Details',
        content: 'Click any node to see detailed information including ancient sources, modern scholarship, and terminology.',
        target: '[data-tour="graph-canvas"]'
      },
      {
        title: 'Export Tools',
        content: 'Export the graph as PNG, SVG, CSV, or generate a bibliography of visible sources.',
        target: '[data-tour="export-tools"]'
      },
      {
        title: 'Keyboard Shortcuts',
        content: 'Press H for help, R to reset view, F to fit screen, C to center selected node, and ESC to deselect.',
        target: 'body'
      }
    ]
  },
  '/search': {
    title: 'Hybrid Search',
    steps: [
      {
        title: 'Multi-Modal Search',
        content: 'Search across 289 ancient texts using three different search modes: full-text, lemmatic, and semantic.',
        target: 'body'
      },
      {
        title: 'Search Modes',
        content: 'Full-text finds exact matches, lemmatic finds word forms, and semantic uses AI to understand meaning.',
        target: '[data-tour="search-modes"]'
      },
      {
        title: 'Advanced Filters',
        content: 'Filter results by author, time period, philosophical school, or work type.',
        target: '[data-tour="filters"]'
      },
      {
        title: 'View Results',
        content: 'Click any result to see the full passage with highlighting and context.',
        target: '[data-tour="results"]'
      }
    ]
  },
  '/graphrag': {
    title: 'GraphRAG Question Answering',
    steps: [
      {
        title: 'Ask Questions',
        content: 'Ask natural language questions about ancient debates on free will and get scholarly answers with citations.',
        target: 'body'
      },
      {
        title: 'Question Input',
        content: 'Type your question here. Be specific for best results, e.g., "What was Aristotle\'s view on moral responsibility?"',
        target: '[data-tour="question-input"]'
      },
      {
        title: 'AI-Powered Answers',
        content: 'Answers are grounded in the knowledge graph and include citations to ancient sources and modern scholarship.',
        target: '[data-tour="answer-area"]'
      },
      {
        title: 'Suggested Questions',
        content: 'Not sure what to ask? Try one of these suggested questions to get started.',
        target: '[data-tour="suggestions"]'
      }
    ]
  },
  '/texts': {
    title: 'Ancient Texts Explorer',
    steps: [
      {
        title: 'Browse Ancient Texts',
        content: 'Access 289 ancient Greek and Latin texts with advanced search and lemmatization.',
        target: 'body'
      },
      {
        title: 'Text List',
        content: 'Browse texts by author, period, or philosophical school.',
        target: '[data-tour="text-list"]'
      },
      {
        title: 'Reader View',
        content: 'Read texts with original language, translation, and lemmatic analysis.',
        target: '[data-tour="reader"]'
      },
      {
        title: 'Lemmatization',
        content: 'Click any word to see its dictionary form, grammatical analysis, and related passages.',
        target: '[data-tour="lemma"]'
      }
    ]
  },
  '/database': {
    title: 'Database Overview',
    steps: [
      {
        title: 'Database Documentation',
        content: 'Comprehensive technical documentation for the EleutherIA knowledge graph.',
        target: 'body'
      },
      {
        title: 'Schema & Structure',
        content: 'Learn about node types, edge relationships, and data organization.',
        target: '[data-tour="schema"]'
      },
      {
        title: 'API Access',
        content: 'Access the database programmatically via REST API or download the complete dataset.',
        target: '[data-tour="api"]'
      }
    ]
  }
};

function AppContent() {
  const location = useLocation();
  const [showTour, setShowTour] = useState(false);
  const { user, logout, isAuthenticated } = useAuth();

  const currentTour = pageTours[location.pathname] || pageTours['/'];

  const handleTourComplete = () => {
    setShowTour(false);
  };

  return (
    <div className="min-h-screen bg-academic-bg">
      {/* Global Tour Button - Visible on all pages */}
      <button
        onClick={() => setShowTour(true)}
        className="fixed bottom-6 right-6 z-50 bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 text-white rounded-full shadow-2xl transition-all duration-300 hover:scale-110 active:scale-95 cursor-pointer touch-manipulation"
        style={{
          WebkitTapHighlightColor: 'transparent'
        }}
        title="Start Interactive Tour"
        aria-label="Start Interactive Tour"
      >
        {/* Mobile: Icon only, centered - Fixed 56x56px circle */}
        <div className="sm:hidden w-14 h-14 flex items-center justify-center">
          <HelpCircle className="w-6 h-6 animate-pulse" />
        </div>

        {/* Desktop: Icon + Text - Auto-width pill shape */}
        <div className="hidden sm:flex items-center gap-2 px-4 py-3">
          <HelpCircle className="w-6 h-6 animate-pulse" />
          <span className="font-medium whitespace-nowrap">Take a Tour</span>
        </div>
      </button>

      {/* Interactive Tour Component */}
      {showTour && <InteractiveTour autoStart={true} onComplete={handleTourComplete} tourSteps={currentTour.steps} />}
      {/* Header / Navigation */}
      <header className="bg-academic-paper border-b border-academic-border shadow-sm sticky top-0 z-50">
        <nav className="academic-container">
          <div className="flex items-center justify-between py-1 sm:py-0 sm:h-12">
            {/* Logo */}
            <Link to="/" className="hover:opacity-80 transition-opacity flex-shrink-0">
              <img
                src="/logo.svg"
                alt="EleutherIA - Ancient Free Will Database"
                className="h-10 sm:h-20 w-auto"
              />
            </Link>

            {/* Navigation Links - Hidden on mobile */}
            <div className="hidden lg:flex items-center space-x-6">
              <NavLink to="/database">Database</NavLink>
              <NavLink to="/visualizer">Knowledge Graph</NavLink>
              <NavLink to="/search">Search</NavLink>
              <NavLink to="/graphrag">GraphRAG Q&A</NavLink>
              <NavLink to="/texts">Ancient Texts</NavLink>
              <NavLink to="/bibliography">Bibliography</NavLink>
              <NavLink to="/about">About</NavLink>
              
              {/* User Menu - Only show when authenticated */}
              {isAuthenticated && (
                <div className="flex items-center space-x-2">
                  <div className="flex items-center space-x-2 text-sm text-academic-muted">
                    <User className="w-4 h-4" />
                    <span>{user?.username}</span>
                  </div>
                  <button
                    onClick={logout}
                    className="flex items-center space-x-1 text-academic-text hover:text-primary-600 transition-colors"
                    title="Logout"
                  >
                    <LogOut className="w-4 h-4" />
                    <span className="text-sm">Logout</span>
                  </button>
                </div>
              )}
            </div>

              {/* Mobile Menu Button */}
              <button
                className="lg:hidden p-1.5 text-academic-text hover:text-primary-600"
                onClick={() => {
                  const mobileMenu = document.getElementById('mobile-menu');
                  mobileMenu?.classList.toggle('hidden');
                }}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            </div>

            {/* Mobile Menu */}
            <div id="mobile-menu" className="hidden lg:hidden pb-2 pt-1.5 border-t border-academic-border mt-1">
              <div className="flex flex-col space-y-1.5">
                <NavLink to="/database">Database</NavLink>
                <NavLink to="/visualizer">Knowledge Graph</NavLink>
                <NavLink to="/search">Search</NavLink>
                <NavLink to="/graphrag">GraphRAG Q&A</NavLink>
                <NavLink to="/texts">Ancient Texts</NavLink>
                <NavLink to="/bibliography">Bibliography</NavLink>
                <NavLink to="/about">About</NavLink>
                
                {/* Mobile Login/User Menu */}
                {isAuthenticated && (
                  <div className="flex items-center justify-between pt-2 border-t border-academic-border">
                    <div className="flex items-center space-x-2 text-sm text-academic-muted">
                      <User className="w-4 h-4" />
                      <span>{user?.username}</span>
                    </div>
                    <button
                      onClick={logout}
                      className="flex items-center space-x-1 text-academic-text hover:text-primary-600 transition-colors text-sm"
                    >
                      <LogOut className="w-4 h-4" />
                      <span>Logout</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          </nav>
        </header>

        {/* Main Content */}
        <main className="academic-container pt-0 pb-12 sm:pb-8">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/database" element={<DatabasePage />} />
            <Route path="/visualizer" element={<KGVisualizerPage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/graphrag" element={<GraphRAGPage />} />
            <Route path="/texts" element={<TextExplorerPage />} />
            <Route path="/bibliography" element={<BibliographyPage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/report-error" element={<ReportErrorPage />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="bg-academic-paper border-t border-academic-border mt-12 sm:mt-16">
          <div className="academic-container py-6 sm:py-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-4">
              <div className="pb-4 sm:pb-0">
                <h3 className="font-semibold text-sm mb-3">About EleutherIA</h3>
                <p className="text-xs text-academic-muted leading-relaxed">
                  A FAIR-compliant knowledge graph documenting ancient debates on free will, fate,
                  and moral responsibility from Aristotle (4th c. BCE) to Boethius (6th c. CE).
                </p>
              </div>

              <div className="pb-4 sm:pb-0">
                <h3 className="font-semibold text-sm mb-3">Data</h3>
                <ul className="text-xs text-academic-muted space-y-1">
                  <li>505 Knowledge Graph Nodes</li>
                  <li>870 Edges & Relationships</li>
                  <li>289 Ancient Texts</li>
                  <li>860+ Bibliography References</li>
                </ul>
              </div>

              <div className="pb-4 sm:pb-0">
                <h3 className="font-semibold text-sm mb-3">Citation</h3>
                <p className="text-xs text-academic-muted leading-relaxed break-words">
                  Girardi, R. (2025). <span className="italic">EleutherIA: Ancient Free Will Database</span>.
                  Zenodo. <a href="https://doi.org/10.5281/zenodo.17379490" className="text-primary-600 hover:underline break-all">
                    https://doi.org/10.5281/zenodo.17379490
                  </a>
                </p>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-academic-border text-center text-xs text-academic-muted">
              <div className="flex flex-wrap justify-center items-center gap-3 sm:gap-4 mb-3">
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
      </div>
  );
}

// Navigation Link Component
function NavLink({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <Link
      to={to}
      className="text-academic-text hover:text-primary-600 font-medium text-sm transition-colors block lg:inline-block py-0.5 lg:py-0"
      onClick={() => {
        // Close mobile menu when clicking a link
        const mobileMenu = document.getElementById('mobile-menu');
        mobileMenu?.classList.add('hidden');
      }}
    >
      {children}
    </Link>
  );
}

export default App;
