import { useState, useEffect, useRef } from 'react';
import { GraduationCap, Search, BookOpen, ChevronDown, ChevronRight, ExternalLink, MoreVertical } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../api/client';
import { AILoader } from '../components/ui/ai-loader';
import { motion } from 'framer-motion';
import { Typewriter } from '../components/ui/typewriter';
import { ShineBorder } from '../components/ui/shine-border';

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
  const { t } = useTranslation();
  const [bibliography, setBibliography] = useState<string[]>([]);
  const [bibliographyData, setBibliographyData] = useState<Map<string, BibliographyEntry>>(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const [loadingMessage, setLoadingMessage] = useState(t('common.loading'));
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedLetters, setExpandedLetters] = useState<Set<string>>(new Set());
  const [filterType, setFilterType] = useState<string>('all');
  const [filterYear, setFilterYear] = useState<string>('all');
  const [filterPublisher, setFilterPublisher] = useState<string>('all');
  const retryTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    loadBibliography();

    return () => {
      if (retryTimeoutRef.current !== null) {
        clearTimeout(retryTimeoutRef.current);
        retryTimeoutRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- Intentionally mount-only: loadBibliography handles its own retry logic internally
  }, []);

  const loadBibliography = async (isRetry = false) => {
    try {
      setLoading(true);
      setError(null);

      if (!isRetry) {
        setLoadingMessage(t('common.loading'));
      } else {
        setLoadingMessage(`Retrying (attempt ${retryCount + 1})... Backend may be starting up.`);
      }

      const nodesResponse = await apiClient.getNodes();
      const nodes = nodesResponse.nodes || [];

      const bibSet = new Set<string>();
      // Define node type with both direct and metadata-nested modern_scholarship
      type NodeType = {
        modern_scholarship?: Array<string | { citation?: string; text?: string; title?: string }>;
        metadata?: {
          modern_scholarship?: string | Array<string | { citation?: string; text?: string; title?: string }>;
        };
      };

      nodes.forEach((node: NodeType) => {
        // Try direct property first, then metadata.modern_scholarship
        let modernScholarship = node.modern_scholarship;

        // If not found directly, check in metadata (where it's stored in Supabase)
        if (!modernScholarship && node.metadata?.modern_scholarship) {
          const metadataMS = node.metadata.modern_scholarship;
          // It might be a JSON string in metadata, so parse it
          if (typeof metadataMS === 'string') {
            try {
              modernScholarship = JSON.parse(metadataMS);
            } catch {
              // If not valid JSON, treat as a single reference
              modernScholarship = [metadataMS];
            }
          } else if (Array.isArray(metadataMS)) {
            modernScholarship = metadataMS;
          }
        }

        if (modernScholarship && Array.isArray(modernScholarship)) {
          modernScholarship.forEach((ref: string | { citation?: string; text?: string; title?: string }) => {
            let refStr = '';
            if (typeof ref === 'string') {
              refStr = ref;
            } else if (ref && typeof ref === 'object') {
              refStr = ref.citation || ref.text || ref.title || JSON.stringify(ref);
            }
            if (refStr && typeof refStr === 'string' && refStr.trim()) {
              bibSet.add(refStr.trim());
            }
          });
        }
      });

      const sortedBib = Array.from(bibSet).sort((a, b) => {
        const authorA = a.split(/[,.]/)[0].toLowerCase();
        const authorB = b.split(/[,.]/)[0].toLowerCase();
        return authorA.localeCompare(authorB);
      });

      setBibliography(sortedBib);
      setRetryCount(0);
      setLoading(false);

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
      } catch (_e) {
        // Online access data not available - continue without it
      }
    } catch (error) {
      console.error('Error loading bibliography:', error);

      if (retryCount < 2) {
        const delay = retryCount === 0 ? 15000 : 15000;
        setLoadingMessage(`Backend is starting up. Retrying in ${delay / 1000} seconds...`);

        if (retryTimeoutRef.current !== null) {
          clearTimeout(retryTimeoutRef.current);
        }

        retryTimeoutRef.current = window.setTimeout(() => {
          retryTimeoutRef.current = null;
          setRetryCount(prev => prev + 1);
          loadBibliography(true);
        }, delay);
      } else {
        setError('Failed to load bibliography. The backend may still be starting up. Please try again in a moment.');
        setLoading(false);
      }
    }
  };

  const toggleLetter = (letter: string) => {
    const newExpanded = new Set(expandedLetters);
    if (newExpanded.has(letter)) {
      newExpanded.delete(letter);
    } else {
      newExpanded.add(letter);
    }
    setExpandedLetters(newExpanded);
  };

  const expandAll = () => {
    const allLetters = new Set(bibliography.map(ref => ref[0].toUpperCase()));
    setExpandedLetters(allLetters);
  };

  const collapseAll = () => {
    setExpandedLetters(new Set());
  };

  const extractYear = (ref: string): string | null => {
    const yearMatch = ref.match(/\b(19\d{2}|20\d{2})\b/);
    return yearMatch ? yearMatch[0] : null;
  };

  const extractPublisher = (ref: string): string | null => {
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

  const uniquePublishers = Array.from(new Set(
    bibliography.map(extractPublisher).filter((p): p is string => p !== null)
  )).sort();

  const filteredBibliography = bibliography.filter(ref => {
    if (searchQuery && !ref.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }

    if (filterType !== 'all' && getReferenceType(ref) !== filterType) {
      return false;
    }

    if (filterYear !== 'all') {
      const refYear = extractYear(ref);
      if (filterYear === '2000+' && (!refYear || parseInt(refYear) < 2000)) return false;
      if (filterYear === '1990-1999' && (!refYear || parseInt(refYear) < 1990 || parseInt(refYear) >= 2000)) return false;
      if (filterYear === '1980-1989' && (!refYear || parseInt(refYear) < 1980 || parseInt(refYear) >= 1990)) return false;
      if (filterYear === 'pre-1980' && (!refYear || parseInt(refYear) >= 1980)) return false;
    }

    if (filterPublisher !== 'all' && extractPublisher(ref) !== filterPublisher) {
      return false;
    }

    return true;
  });

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
    <div className="min-h-screen w-full pt-20 pb-12 bg-parchment-50">
      <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Modern Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <h1 className="text-5xl md:text-6xl font-display font-bold text-stone-800 mb-4">
            <Typewriter
              text={["Bibliography", "Modern Scholarship", "Academic Sources"]}
              speed={100}
              waitTime={3000}
              deleteSpeed={60}
              className="text-stone-800"
              cursorChar="_"
            />
          </h1>
          <p className="text-lg text-stone-600 max-w-2xl mx-auto">
            {t('bibliography.subtitle')}
          </p>
        </motion.div>

        {/* Stats Badges */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="flex flex-wrap justify-center gap-3"
        >
          <span className="px-4 py-2 bg-parchment-100/70 backdrop-blur-sm rounded-full text-sm font-medium text-stone-600 shadow-sm border border-amber-200/40">
            {bibliography.length} Total References
          </span>
          <span className="px-4 py-2 bg-parchment-100/70 backdrop-blur-sm rounded-full text-sm font-medium text-stone-600 shadow-sm border border-amber-200/40">
            {filteredBibliography.length} Filtered
          </span>
          <span className="px-4 py-2 bg-orange-50 backdrop-blur-sm rounded-full text-sm font-medium text-orange-600 shadow-sm border border-orange-200">
            100% Citation Coverage
          </span>
        </motion.div>

        {/* Unified Search & Filter Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <ShineBorder
            className="!p-0 bg-parchment-100/70 backdrop-blur-sm"
            borderRadius={24}
            color={["#f97316", "#ea580c", "#fdba74"]}
          >
            <div className="p-6 space-y-4">
              {/* Search Bar */}
              <div className="relative w-full">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-stone-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Search by author, title, or keyword..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 bg-parchment-50/60 backdrop-blur-md border border-amber-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all"
                />
              </div>

              {/* Filters */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="px-4 py-2 bg-parchment-50/60 backdrop-blur-md border border-amber-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
                >
                  <option value="all">All Types</option>
                  <option value="monograph">Monographs</option>
                  <option value="edited-volume">Edited Volumes</option>
                  <option value="journal">Journal Articles</option>
                  <option value="translation">Translations</option>
                  <option value="encyclopedia">Encyclopedia Entries</option>
                </select>

                <select
                  value={filterYear}
                  onChange={(e) => setFilterYear(e.target.value)}
                  className="px-4 py-2 bg-parchment-50/60 backdrop-blur-md border border-amber-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
                >
                  <option value="all">All Years</option>
                  <option value="2000+">2000+</option>
                  <option value="1990-1999">1990-1999</option>
                  <option value="1980-1989">1980-1989</option>
                  <option value="pre-1980">Pre-1980</option>
                </select>

                <select
                  value={filterPublisher}
                  onChange={(e) => setFilterPublisher(e.target.value)}
                  className="px-4 py-2 bg-parchment-50/60 backdrop-blur-md border border-amber-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
                >
                  <option value="all">All Publishers</option>
                  {uniquePublishers.map(pub => (
                    <option key={pub} value={pub}>{pub}</option>
                  ))}
                </select>
              </div>

              {/* Filter Actions */}
              {(searchQuery || filterType !== 'all' || filterYear !== 'all' || filterPublisher !== 'all') && (
                <div className="flex items-center justify-between pt-2 border-t border-amber-200/40">
                  <div className="text-sm text-stone-600">
                    Showing {filteredBibliography.length} of {bibliography.length} references
                  </div>
                  <button
                    onClick={() => {
                      setSearchQuery('');
                      setFilterType('all');
                      setFilterYear('all');
                      setFilterPublisher('all');
                    }}
                    className="text-sm text-orange-600 hover:text-orange-700 font-medium transition-colors"
                  >
                    Reset Filters
                  </button>
                </div>
              )}
            </div>
          </ShineBorder>
        </motion.div>

        {/* Bibliography List */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-parchment-100/70 backdrop-blur-sm rounded-2xl p-6 shadow-sm"
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <BookOpen className="w-6 h-6 text-orange-600" />
              <h2 className="text-2xl font-display font-bold text-stone-800">References</h2>
            </div>
            {!loading && !error && filteredBibliography.length > 0 && (
              <div className="flex gap-2">
                <button
                  onClick={expandAll}
                  className="px-4 py-2 text-sm text-orange-600 hover:bg-orange-50 border border-orange-300 rounded-xl transition-colors"
                >
                  Expand All
                </button>
                <button
                  onClick={collapseAll}
                  className="px-4 py-2 text-sm text-orange-600 hover:bg-orange-50 border border-orange-300 rounded-xl transition-colors"
                >
                  Collapse All
                </button>
              </div>
            )}
          </div>

          {error ? (
            <div className="text-center py-12">
              <div className="bg-red-50 border border-red-200 rounded-2xl p-6 max-w-2xl mx-auto">
                <p className="text-red-800 font-medium mb-3">{error}</p>
                <button
                  onClick={() => {
                    setRetryCount(0);
                    loadBibliography(false);
                  }}
                  className="px-6 py-3 bg-gradient-to-br from-stone-900 to-stone-800 text-white rounded-full hover:shadow-lg transition-all"
                >
                  Retry
                </button>
              </div>
            </div>
          ) : loading ? (
            <div className="text-center py-12">
              <AILoader text="Loading" size="md" />
              <p className="mt-6 text-stone-600">{loadingMessage}</p>
              {retryCount > 0 && (
                <p className="mt-2 text-sm text-amber-600">
                  This is normal on first request. The backend may take up to 30 seconds to start.
                </p>
              )}
            </div>
          ) : filteredBibliography.length === 0 ? (
            <div className="text-center py-12">
              <GraduationCap className="w-16 h-16 text-stone-400 mx-auto mb-4" />
              <p className="text-stone-600">
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
                  <div key={letter} className="border border-amber-200/40 rounded-xl overflow-hidden bg-parchment-50/40">
                    <button
                      onClick={() => toggleLetter(letter)}
                      className="w-full flex items-center justify-between p-4 hover:bg-parchment-100/50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        {isExpanded ? (
                          <ChevronDown className="w-5 h-5 text-orange-600" />
                        ) : (
                          <ChevronRight className="w-5 h-5 text-orange-600" />
                        )}
                        <span className="text-2xl font-bold text-orange-600">{letter}</span>
                        <span className="text-sm text-stone-600">
                          ({refs.length} {refs.length === 1 ? 'reference' : 'references'})
                        </span>
                      </div>
                    </button>

                    {isExpanded && (
                      <div className="border-t border-amber-200/40 bg-parchment-50/30">
                        {refs.map((ref, index) => {
                          const entry = bibliographyData.get(ref);
                          const hasAccess = entry && entry.verified_links && entry.verified_links.length > 0;
                          const multipleLinks = hasAccess && entry.verified_links!.length > 1;

                          return (
                            <div
                              key={index}
                              className="p-4 border-b border-amber-200/40 last:border-b-0 hover:bg-parchment-50/40 transition-colors"
                            >
                              <div className="flex items-start gap-3">
                                <div className="flex-shrink-0 w-8 text-sm text-stone-400 font-mono">
                                  [{filteredBibliography.indexOf(ref) + 1}]
                                </div>
                                <div className="flex-1 text-sm text-stone-700 leading-relaxed">
                                  {ref}
                                </div>
                                {hasAccess && (
                                  <div className="flex-shrink-0 flex gap-2">
                                    <a
                                      href={entry.verified_links![0].url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-orange-600 hover:bg-orange-700 text-white text-xs font-medium rounded-lg transition-colors shadow-sm hover:shadow"
                                      title={entry.verified_links![0].label}
                                    >
                                      <ExternalLink className="w-3.5 h-3.5" />
                                      <span>Access</span>
                                    </a>
                                    {multipleLinks && (
                                      <div className="relative group">
                                        <button
                                          className="inline-flex items-center px-2 py-1.5 bg-orange-100 hover:bg-orange-200 text-orange-700 text-xs font-medium rounded-lg transition-colors"
                                          title="More access options"
                                        >
                                          <MoreVertical className="w-3.5 h-3.5" />
                                        </button>
                                        <div className="absolute right-0 top-full mt-1 w-48 bg-parchment-50 border border-amber-200/40 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                                          {entry.verified_links!.map((link, linkIdx) => (
                                            <a
                                              key={linkIdx}
                                              href={link.url}
                                              target="_blank"
                                              rel="noopener noreferrer"
                                              className="block px-3 py-2 text-xs text-stone-600 hover:bg-orange-50 first:rounded-t-lg last:rounded-b-lg"
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
        </motion.div>

        {/* Citation Info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <ShineBorder
            className="!p-0 bg-parchment-100/70 backdrop-blur-sm"
            borderRadius={24}
            color={["#f97316", "#ea580c", "#fdba74"]}
          >
            <div className="p-8">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-gradient-to-br from-orange-500 to-amber-600 rounded-lg">
                  <GraduationCap className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-2xl font-display font-bold text-stone-800">How to Cite EleutherIA</h3>
              </div>

              <div className="bg-parchment-50/60 p-6 rounded-xl border border-amber-200/40 mb-4">
                <p className="font-mono text-sm leading-relaxed text-stone-700">
                  Girardi, R. (2025). <span className="italic font-serif">EleutherIA: Ancient Free Will Database</span>. Zenodo.{" "}
                  <a
                    href="https://doi.org/10.5281/zenodo.17379490"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-orange-600 hover:text-orange-700 underline decoration-2 underline-offset-2 transition-colors"
                  >
                    https://doi.org/10.5281/zenodo.17379490
                  </a>
                </p>
              </div>

              <div className="flex items-start gap-3 text-sm text-stone-600 bg-orange-50 border border-orange-200 rounded-xl p-4">
                <div className="flex-shrink-0 w-1 h-full bg-orange-500 rounded-full"></div>
                <p className="leading-relaxed">
                  All {bibliography.length} references in this bibliography are cited in the knowledge graph with full provenance tracking and academic rigor.
                </p>
              </div>
            </div>
          </ShineBorder>
        </motion.div>
      </div>
    </div>
  );
}
