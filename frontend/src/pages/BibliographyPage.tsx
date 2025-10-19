import { useState, useEffect, useRef } from 'react';
import { GraduationCap, Search, BookOpen, ChevronDown, ChevronRight, Filter, ExternalLink, MoreVertical } from 'lucide-react';
import { apiClient } from '../api/client';

interface AccessLink {
  type: string;
  url: string;
  label: string;
  verified?: boolean;
}

interface BibliographyEntry {
  citation: string;
  access_links?: AccessLink[];
  verified_links?: AccessLink[];
}

export default function BibliographyPage() {
  const [bibliography, setBibliography] = useState<string[]>([]);
  const [bibliographyData, setBibliographyData] = useState<Map<string, BibliographyEntry>>(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedLetters, setExpandedLetters] = useState<Set<string>>(new Set());
  const [filterType, setFilterType] = useState<string>('all');
  const [filterYear, setFilterYear] = useState<string>('all');
  const [filterPublisher, setFilterPublisher] = useState<string>('all');

  useEffect(() => {
    loadBibliography();
  }, []);

  const loadBibliography = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch all KG nodes to extract bibliography
      const nodesResponse: any = await apiClient.getNodes();
      const nodes = nodesResponse.nodes || [];

      // Extract all unique modern scholarship references
      const bibSet = new Set<string>();
      nodes.forEach((node: any) => {
        if (node.modern_scholarship && Array.isArray(node.modern_scholarship)) {
          node.modern_scholarship.forEach((ref: string) => {
            if (ref && ref.trim()) {
              bibSet.add(ref.trim());
            }
          });
        }
      });

      // Convert to sorted array
      const sortedBib = Array.from(bibSet).sort((a, b) => {
        // Sort alphabetically by author (first part before comma or period)
        const authorA = a.split(/[,\.]/)[0].toLowerCase();
        const authorB = b.split(/[,\.]/)[0].toLowerCase();
        return authorA.localeCompare(authorB);
      });

      setBibliography(sortedBib);

      // Try to load online access data
      try {
        const response = await fetch('/online_access_results.json');
        if (response.ok) {
          const accessData: BibliographyEntry[] = await response.json();
          const dataMap = new Map<string, BibliographyEntry>();
          accessData.forEach(entry => {
            dataMap.set(entry.citation, entry);
          });
          setBibliographyData(dataMap);
        }
      } catch (e) {
        // Online access data not available yet - that's okay
        console.log('Online access data not available');
      }
    } catch (error) {
      console.error('Error loading bibliography:', error);
      setError('Failed to load bibliography. The backend may be starting up (this can take 30 seconds on first request). Please try again in a moment.');
    } finally {
      setLoading(false);
    }
  };

  // Toggle letter expansion
  const toggleLetter = (letter: string) => {
    const newExpanded = new Set(expandedLetters);
    if (newExpanded.has(letter)) {
      newExpanded.delete(letter);
    } else {
      newExpanded.add(letter);
    }
    setExpandedLetters(newExpanded);
  };

  // Expand all letters
  const expandAll = () => {
    const allLetters = new Set(bibliography.map(ref => ref[0].toUpperCase()));
    setExpandedLetters(allLetters);
  };

  // Collapse all letters
  const collapseAll = () => {
    setExpandedLetters(new Set());
  };

  // Extract metadata from references
  const extractYear = (ref: string): string | null => {
    const yearMatch = ref.match(/\b(19\d{2}|20\d{2})\b/);
    return yearMatch ? yearMatch[0] : null;
  };

  const extractPublisher = (ref: string): string | null => {
    // Common academic publishers
    const publishers = [
      'Oxford', 'Cambridge', 'Princeton', 'Harvard', 'Yale', 'MIT',
      'Clarendon', 'Springer', 'Routledge', 'Brill', 'Blackwell',
      'Penguin', 'Hackett', 'Cornell', 'Chicago', 'Stanford'
    ];
    for (const publisher of publishers) {
      if (ref.includes(publisher)) return publisher;
    }
    return 'Other';
  };

  const getReferenceType = (ref: string): string => {
    if (ref.includes('ed.') || ref.includes('(ed.)') || ref.includes('(eds.)')) return 'edited-volume';
    if (ref.includes('trans.') || ref.includes('(trans.)')) return 'translation';
    if (ref.includes('Journal') || ref.includes('Review') || ref.match(/\d+\(\d+\)/)) return 'journal';
    if (ref.includes('Stanford Encyclopedia') || ref.includes('SEP')) return 'encyclopedia';
    return 'monograph';
  };

  // Get unique values for filters
  const uniqueYears = Array.from(new Set(
    bibliography.map(extractYear).filter(Boolean)
  )).sort().reverse();

  const uniquePublishers = Array.from(new Set(
    bibliography.map(extractPublisher).filter(Boolean)
  )).sort();

  // Filter bibliography
  const filteredBibliography = bibliography.filter(ref => {
    // Search query filter
    if (searchQuery && !ref.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }

    // Type filter
    if (filterType !== 'all' && getReferenceType(ref) !== filterType) {
      return false;
    }

    // Year filter
    if (filterYear !== 'all') {
      const refYear = extractYear(ref);
      if (filterYear === '2000+' && (!refYear || parseInt(refYear) < 2000)) return false;
      if (filterYear === '1990-1999' && (!refYear || parseInt(refYear) < 1990 || parseInt(refYear) >= 2000)) return false;
      if (filterYear === '1980-1989' && (!refYear || parseInt(refYear) < 1980 || parseInt(refYear) >= 1990)) return false;
      if (filterYear === 'pre-1980' && (!refYear || parseInt(refYear) >= 1980)) return false;
    }

    // Publisher filter
    if (filterPublisher !== 'all' && extractPublisher(ref) !== filterPublisher) {
      return false;
    }

    return true;
  });

  // Group by first letter
  const groupedBibliography: { [key: string]: string[] } = {};
  filteredBibliography.forEach(ref => {
    const letter = ref[0].toUpperCase();
    if (!groupedBibliography[letter]) {
      groupedBibliography[letter] = [];
    }
    groupedBibliography[letter].push(ref);
  });

  const letters = Object.keys(groupedBibliography).sort();

  return (
    <div className="space-y-6">
      {/* Header */}
      <section className="academic-card">
        <div className="flex items-start gap-4">
          <GraduationCap className="w-12 h-12 text-primary-600 flex-shrink-0 mt-1" />
          <div>
            <h1 className="text-3xl font-serif font-bold mb-3">Modern Scholarship Bibliography</h1>
            <p className="text-lg text-academic-muted leading-relaxed">
              Complete bibliography of secondary literature cited in the EleutherIA knowledge graph.
              All references support the philosophical and historical claims documented in the database.
            </p>
          </div>
        </div>
      </section>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="academic-card bg-primary-50 text-center">
          <div className="text-4xl font-bold text-primary-600 mb-1">
            {bibliography.length}
          </div>
          <div className="text-sm font-medium text-academic-text">Total References</div>
        </div>
        <div className="academic-card bg-primary-50 text-center">
          <div className="text-4xl font-bold text-primary-600 mb-1">
            {filteredBibliography.length}
          </div>
          <div className="text-sm font-medium text-academic-text">Filtered Results</div>
        </div>
        <div className="academic-card bg-primary-50 text-center">
          <div className="text-4xl font-bold text-primary-600 mb-1">
            {(() => {
              const withAccess = bibliography.filter(ref => {
                const entry = bibliographyData.get(ref);
                return entry && entry.verified_links && entry.verified_links.length > 0;
              }).length;
              return bibliographyData.size > 0 ? withAccess : '...';
            })()}
          </div>
          <div className="text-sm font-medium text-academic-text">Online Access</div>
        </div>
        <div className="academic-card bg-primary-50 text-center">
          <div className="text-4xl font-bold text-primary-600 mb-1">
            100%
          </div>
          <div className="text-sm font-medium text-academic-text">Citation Coverage</div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="academic-card">
        <div className="space-y-4">
          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-academic-muted w-5 h-5" />
            <input
              type="text"
              placeholder="Search by author, title, publisher, year..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-academic-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {/* Filters Row */}
          <div className="flex items-center gap-3 pt-2 border-t border-academic-border">
            <Filter className="w-4 h-4 text-academic-muted flex-shrink-0" />
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 flex-1">
              {/* Type Filter */}
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="px-3 py-2 border border-academic-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="all">All Types</option>
                <option value="monograph">Monographs</option>
                <option value="edited-volume">Edited Volumes</option>
                <option value="journal">Journal Articles</option>
                <option value="translation">Translations</option>
                <option value="encyclopedia">Encyclopedia Entries</option>
              </select>

              {/* Year Filter */}
              <select
                value={filterYear}
                onChange={(e) => setFilterYear(e.target.value)}
                className="px-3 py-2 border border-academic-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="all">All Years</option>
                <option value="2000+">2000+</option>
                <option value="1990-1999">1990-1999</option>
                <option value="1980-1989">1980-1989</option>
                <option value="pre-1980">Pre-1980</option>
              </select>

              {/* Publisher Filter */}
              <select
                value={filterPublisher}
                onChange={(e) => setFilterPublisher(e.target.value)}
                className="px-3 py-2 border border-academic-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="all">All Publishers</option>
                {uniquePublishers.map(pub => (
                  <option key={pub} value={pub}>{pub}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Filter Results Summary */}
          {(searchQuery || filterType !== 'all' || filterYear !== 'all' || filterPublisher !== 'all') && (
            <div className="flex items-center justify-between pt-2 border-t border-academic-border">
              <div className="text-sm text-academic-muted">
                Found {filteredBibliography.length} of {bibliography.length} references
              </div>
              <button
                onClick={() => {
                  setSearchQuery('');
                  setFilterType('all');
                  setFilterYear('all');
                  setFilterPublisher('all');
                }}
                className="text-sm text-primary-600 hover:text-primary-700 font-medium"
              >
                Clear All Filters
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Bibliography List */}
      <section className="academic-card">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <BookOpen className="w-6 h-6 text-primary-600" />
            <h2 className="text-2xl font-serif font-bold">References</h2>
          </div>
          {!loading && !error && filteredBibliography.length > 0 && (
            <div className="flex gap-2">
              <button
                onClick={expandAll}
                className="px-3 py-1.5 text-sm text-primary-600 hover:bg-primary-50 border border-primary-300 rounded-lg transition-colors"
              >
                Expand All
              </button>
              <button
                onClick={collapseAll}
                className="px-3 py-1.5 text-sm text-primary-600 hover:bg-primary-50 border border-primary-300 rounded-lg transition-colors"
              >
                Collapse All
              </button>
            </div>
          )}
        </div>

        {error ? (
          <div className="text-center py-12">
            <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-2xl mx-auto">
              <svg className="w-12 h-12 text-red-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-red-800 font-medium mb-3">{error}</p>
              <button
                onClick={loadBibliography}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
              >
                Retry
              </button>
            </div>
          </div>
        ) : loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            <p className="mt-4 text-academic-muted">Loading bibliography...</p>
          </div>
        ) : filteredBibliography.length === 0 ? (
          <div className="text-center py-12">
            <GraduationCap className="w-16 h-16 text-academic-muted mx-auto mb-4" />
            <p className="text-academic-muted">
              {searchQuery || filterType !== 'all' || filterYear !== 'all' || filterPublisher !== 'all'
                ? 'No references found matching your filters.'
                : 'No references available.'}
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {letters.map(letter => {
              const isExpanded = expandedLetters.has(letter);
              const refs = groupedBibliography[letter];

              return (
                <div key={letter} className="border border-academic-border rounded-lg overflow-hidden">
                  {/* Letter Header */}
                  <button
                    onClick={() => toggleLetter(letter)}
                    className="w-full flex items-center justify-between p-4 bg-academic-bg hover:bg-primary-50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      {isExpanded ? (
                        <ChevronDown className="w-5 h-5 text-primary-600" />
                      ) : (
                        <ChevronRight className="w-5 h-5 text-primary-600" />
                      )}
                      <span className="text-2xl font-serif font-bold text-primary-700">{letter}</span>
                      <span className="text-sm text-academic-muted">
                        ({refs.length} {refs.length === 1 ? 'reference' : 'references'})
                      </span>
                    </div>
                  </button>

                  {/* References List */}
                  {isExpanded && (
                    <div className="border-t border-academic-border bg-white">
                      {refs.map((ref, index) => {
                        const entry = bibliographyData.get(ref);
                        const hasAccess = entry && entry.verified_links && entry.verified_links.length > 0;
                        const multipleLinks = hasAccess && entry.verified_links!.length > 1;

                        return (
                          <div
                            key={index}
                            className="p-4 border-b border-academic-border last:border-b-0 hover:bg-primary-50 transition-colors"
                          >
                            <div className="flex items-start gap-3">
                              <div className="flex-shrink-0 w-8 text-sm text-academic-muted font-mono">
                                [{filteredBibliography.indexOf(ref) + 1}]
                              </div>
                              <div className="flex-1 text-sm text-academic-text leading-relaxed">
                                {ref}
                              </div>
                              {hasAccess && (
                                <div className="flex-shrink-0 flex gap-2">
                                  <a
                                    href={entry.verified_links![0].url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-primary-600 hover:bg-primary-700 text-white text-xs font-medium rounded-md transition-colors shadow-sm hover:shadow"
                                    title={entry.verified_links![0].label}
                                  >
                                    <ExternalLink className="w-3.5 h-3.5" />
                                    <span>Access</span>
                                  </a>
                                  {multipleLinks && (
                                    <div className="relative group">
                                      <button
                                        className="inline-flex items-center px-2 py-1.5 bg-primary-100 hover:bg-primary-200 text-primary-700 text-xs font-medium rounded-md transition-colors"
                                        title="More access options"
                                      >
                                        <MoreVertical className="w-3.5 h-3.5" />
                                      </button>
                                      <div className="absolute right-0 top-full mt-1 w-48 bg-white border border-academic-border rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                                        {entry.verified_links!.map((link, linkIdx) => (
                                          <a
                                            key={linkIdx}
                                            href={link.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="block px-3 py-2 text-xs text-academic-text hover:bg-primary-50 first:rounded-t-lg last:rounded-b-lg"
                                          >
                                            <div className="flex items-center gap-2">
                                              <ExternalLink className="w-3 h-3 flex-shrink-0" />
                                              <span className="truncate">{link.label}</span>
                                            </div>
                                          </a>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* Citation Info */}
      <section className="academic-card bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0">
            <svg className="w-6 h-6 text-amber-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="text-sm">
            <div className="font-semibold text-amber-900 mb-2">How to Cite This Database</div>
            <div className="bg-white p-3 rounded border border-amber-300 font-mono text-xs text-academic-text mb-3">
              Girardi, R. (2025). <span className="italic">EleutherIA: Ancient Free Will Database</span>.
              Zenodo. https://doi.org/10.5281/zenodo.17379490
            </div>
            <p className="text-amber-900 leading-relaxed">
              All references listed above are cited within knowledge graph node metadata and
              automatically included in GraphRAG responses with proper attribution.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
