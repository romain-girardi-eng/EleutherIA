import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import HomePage from './pages/HomePage';
import KGVisualizerPage from './pages/KGVisualizerPage';
import SearchPage from './pages/SearchPage';
import GraphRAGPage from './pages/GraphRAGPage';
import TextExplorerPage from './pages/TextExplorerPage';
import AboutPage from './pages/AboutPage';
import './index.css';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-academic-bg">
        {/* Header / Navigation */}
        <header className="bg-academic-paper border-b border-academic-border shadow-sm">
          <nav className="academic-container">
            <div className="flex items-center justify-between h-12">
              {/* Logo */}
              <Link to="/" className="hover:opacity-80 transition-opacity">
                <img
                  src="/logo.svg"
                  alt="EleutherIA - Ancient Free Will Database"
                  className="h-20 w-auto"
                />
              </Link>

              {/* Navigation Links */}
              <div className="flex items-center space-x-6">
                <NavLink to="/visualizer">Knowledge Graph</NavLink>
                <NavLink to="/search">Search</NavLink>
                <NavLink to="/graphrag">GraphRAG Q&A</NavLink>
                <NavLink to="/texts">Ancient Texts</NavLink>
                <NavLink to="/about">About</NavLink>
              </div>
            </div>
          </nav>
        </header>

        {/* Main Content */}
        <main className="academic-container pt-0 pb-8">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/visualizer" element={<KGVisualizerPage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/graphrag" element={<GraphRAGPage />} />
            <Route path="/texts" element={<TextExplorerPage />} />
            <Route path="/about" element={<AboutPage />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="bg-academic-paper border-t border-academic-border mt-12">
          <div className="academic-container py-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <h3 className="font-semibold text-sm mb-2">About EleutherIA</h3>
                <p className="text-xs text-academic-muted leading-relaxed">
                  A FAIR-compliant knowledge graph documenting ancient debates on free will, fate,
                  and moral responsibility from Aristotle (4th c. BCE) to Boethius (6th c. CE).
                </p>
              </div>

              <div>
                <h3 className="font-semibold text-sm mb-2">Data</h3>
                <ul className="text-xs text-academic-muted space-y-1">
                  <li>465 Knowledge Graph Nodes</li>
                  <li>740 Edges & Relationships</li>
                  <li>289 Ancient Texts</li>
                  <li>200+ Bibliography References</li>
                </ul>
              </div>

              <div>
                <h3 className="font-semibold text-sm mb-2">Citation</h3>
                <p className="text-xs text-academic-muted leading-relaxed">
                  Girardi, R. (2025). <span className="italic">EleutherIA: Ancient Free Will Database</span>.
                  Zenodo. <a href="https://doi.org/10.5281/zenodo.17379490" className="text-primary-600 hover:underline">
                    https://doi.org/10.5281/zenodo.17379490
                  </a>
                </p>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-academic-border text-center text-xs text-academic-muted">
              <div className="flex justify-center items-center gap-4 mb-2">
                <a
                  href="https://github.com/romain-girardi-eng/EleutherIA"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline inline-flex items-center gap-1"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <path fillRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.17 6.839 9.49.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.167 22 16.418 22 12c0-5.523-4.477-10-10-10z" clipRule="evenodd" />
                  </svg>
                  GitHub
                </a>
                <a
                  href="https://orcid.org/0000-0002-5310-5346"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline inline-flex items-center gap-1"
                >
                  <svg className="w-4 h-4" viewBox="0 0 256 256" fill="currentColor">
                    <path d="M256,128c0,70.7-57.3,128-128,128C57.3,256,0,198.7,0,128C0,57.3,57.3,0,128,0C198.7,0,256,57.3,256,128z M86.3,186.2H70.9V79.1h15.4v48.4V186.2z M108.9,79.1h41.6c39.6,0,57,28.3,57,53.6c0,27.5-21.5,53.6-56.8,53.6h-41.8V79.1z M124.3,172.4h24.5c34.9,0,42.9-26.5,42.9-39.7c0-21.5-13.7-39.7-43.7-39.7h-23.7V172.4z M78.2,59.1c5.1,0,9.2,4.1,9.2,9.2c0,5.1-4.1,9.2-9.2,9.2c-5.1,0-9.2-4.1-9.2-9.2C69,63.2,73.1,59.1,78.2,59.1z"/>
                  </svg>
                  ORCID
                </a>
                <a
                  href="https://www.linkedin.com/in/romain-girardi"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline inline-flex items-center gap-1"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                  </svg>
                  LinkedIn
                </a>
              </div>
              <p>
                © 2025 Romain Girardi | Licensed under{' '}
                <a href="https://creativecommons.org/licenses/by/4.0/" className="text-primary-600 hover:underline">
                  CC BY 4.0
                </a>
              </p>
            </div>
          </div>
        </footer>
      </div>
    </Router>
  );
}

// Navigation Link Component
function NavLink({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <Link
      to={to}
      className="text-academic-text hover:text-primary-600 font-medium text-sm transition-colors"
    >
      {children}
    </Link>
  );
}

export default App;
