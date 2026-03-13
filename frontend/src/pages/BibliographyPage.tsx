import { useState, useEffect, useRef } from 'react';
import { Search, ChevronDown, ChevronRight, ExternalLink, MoreVertical, BookOpen, RotateCcw, ChevronsUpDown, Library } from 'lucide-react';
import { Typewriter } from '../components/ui/typewriter';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../api/client';
import { motion, AnimatePresence } from 'framer-motion';

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

/* ─── Minimal skeleton loader ─── */
function BibSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-stone-200/60" />
            <div className="h-3 w-24 rounded-full bg-stone-200/60" />
          </div>
          {Array.from({ length: 3 }).map((_, j) => (
            <div key={j} className="ml-11 flex gap-3">
              <div className="w-6 h-3 rounded bg-stone-100" />
              <div className="flex-1 h-3 rounded-full bg-stone-100" style={{ width: `${60 + (j * 12)}%` }} />
            </div>
          ))}
        </div>
      ))}
    </div>
  );
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadBibliography = async (isRetry = false) => {
    try {
      setLoading(true);
      setError(null);

      if (!isRetry) {
        setLoadingMessage(t('common.loading'));
      } else {
        setLoadingMessage(`Retrying (attempt ${retryCount + 1})...`);
      }

      const nodesResponse = await apiClient.getNodes();
      const nodes = nodesResponse.nodes || [];

      const bibSet = new Set<string>();
      type NodeType = {
        modern_scholarship?: Array<string | { citation?: string; text?: string; title?: string }>;
        metadata?: {
          modern_scholarship?: string | Array<string | { citation?: string; text?: string; title?: string }>;
        };
      };

      nodes.forEach((node: NodeType) => {
        let modernScholarship = node.modern_scholarship;
        if (!modernScholarship && node.metadata?.modern_scholarship) {
          const metadataMS = node.metadata.modern_scholarship;
          if (typeof metadataMS === 'string') {
            try {
              modernScholarship = JSON.parse(metadataMS);
            } catch {
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
        // Online access data not available
      }
    } catch (error) {
      console.error('Error loading bibliography:', error);

      if (retryCount < 2) {
        const delay = 15000;
        setLoadingMessage(`Backend is starting up. Retrying in ${delay / 1000}s...`);

        if (retryTimeoutRef.current !== null) {
          clearTimeout(retryTimeoutRef.current);
        }

        retryTimeoutRef.current = window.setTimeout(() => {
          retryTimeoutRef.current = null;
          setRetryCount(prev => prev + 1);
          loadBibliography(true);
        }, delay);
      } else {
        setError('Failed to load bibliography. The backend may still be starting up.');
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
    if (searchQuery && !ref.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    if (filterType !== 'all' && getReferenceType(ref) !== filterType) return false;
    if (filterYear !== 'all') {
      const refYear = extractYear(ref);
      if (filterYear === '2000+' && (!refYear || parseInt(refYear) < 2000)) return false;
      if (filterYear === '1990-1999' && (!refYear || parseInt(refYear) < 1990 || parseInt(refYear) >= 2000)) return false;
      if (filterYear === '1980-1989' && (!refYear || parseInt(refYear) < 1980 || parseInt(refYear) >= 1990)) return false;
      if (filterYear === 'pre-1980' && (!refYear || parseInt(refYear) >= 1980)) return false;
    }
    if (filterPublisher !== 'all' && extractPublisher(ref) !== filterPublisher) return false;
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
  const isFiltered = searchQuery || filterType !== 'all' || filterYear !== 'all' || filterPublisher !== 'all';

  return (
    <div className="min-h-screen w-full bg-transparent">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">

        {/* ── Hero ── */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="pt-28 pb-8 text-center"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-stone-800/5 border border-stone-300/30 text-xs font-medium text-stone-500 tracking-wide uppercase mb-5">
            <Library className="w-3.5 h-3.5" />
            Modern Scholarship
          </div>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-display font-semibold text-stone-800 tracking-tight mb-3">
            <Typewriter
              text={["Bibliography", "Modern Scholarship", "Academic Sources"]}
              speed={80}
              waitTime={3000}
              deleteSpeed={50}
              className="text-stone-800"
              cursorChar="_"
            />
          </h1>
          <p className="text-base sm:text-lg text-stone-500 max-w-xl mx-auto leading-relaxed">
            {t('bibliography.subtitle')}
          </p>
        </motion.div>

        {/* ── Stats ── */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.15 }}
          className="flex items-center justify-center gap-6 text-sm text-stone-400 mb-8"
        >
          <span><strong className="text-stone-700 font-semibold">{bibliography.length}</strong> references</span>
          <span className="w-1 h-1 rounded-full bg-stone-300" />
          <span><strong className="text-stone-700 font-semibold">100%</strong> citation coverage</span>
          {isFiltered && (
            <>
              <span className="w-1 h-1 rounded-full bg-stone-300" />
              <span><strong className="text-stone-700 font-semibold">{filteredBibliography.length}</strong> matching</span>
            </>
          )}
        </motion.div>

        {/* ── Search + filters ── */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.4 }}
          className="mb-10 space-y-3"
        >
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-400" />
            <input
              type="text"
              placeholder="Search by author, title, or keyword..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-11 pr-4 py-3 text-sm bg-white/60 backdrop-blur-sm border border-stone-200/60 rounded-xl text-stone-700 placeholder:text-stone-400 focus:outline-none focus:border-stone-400 focus:ring-1 focus:ring-stone-400/20 transition-all"
            />
          </div>

          {/* Filter row */}
          <div className="flex flex-wrap gap-2 items-center">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-2 text-sm bg-stone-50 border border-stone-200/80 rounded-lg text-stone-600 focus:outline-none focus:border-stone-400 focus:ring-1 focus:ring-stone-400/20 transition-colors"
            >
              <option value="all">All Types</option>
              <option value="monograph">Monographs</option>
              <option value="edited-volume">Edited Volumes</option>
              <option value="journal">Journal Articles</option>
              <option value="translation">Translations</option>
              <option value="encyclopedia">Encyclopedia</option>
            </select>

            <select
              value={filterYear}
              onChange={(e) => setFilterYear(e.target.value)}
              className="px-3 py-2 text-sm bg-stone-50 border border-stone-200/80 rounded-lg text-stone-600 focus:outline-none focus:border-stone-400 focus:ring-1 focus:ring-stone-400/20 transition-colors"
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
              className="px-3 py-2 text-sm bg-stone-50 border border-stone-200/80 rounded-lg text-stone-600 focus:outline-none focus:border-stone-400 focus:ring-1 focus:ring-stone-400/20 transition-colors"
            >
              <option value="all">All Publishers</option>
              {uniquePublishers.map(pub => (
                <option key={pub} value={pub}>{pub}</option>
              ))}
            </select>

            {isFiltered && (
              <button
                onClick={() => {
                  setSearchQuery('');
                  setFilterType('all');
                  setFilterYear('all');
                  setFilterPublisher('all');
                }}
                className="inline-flex items-center gap-1.5 px-3 py-2 text-sm text-stone-500 hover:text-stone-700 transition-colors"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Reset
              </button>
            )}

            {/* Spacer */}
            <div className="flex-1" />

            {/* Expand/Collapse */}
            {!loading && !error && filteredBibliography.length > 0 && (
              <button
                onClick={expandedLetters.size > 0 ? collapseAll : expandAll}
                className="inline-flex items-center gap-1.5 px-3 py-2 text-sm text-stone-500 hover:text-stone-700 transition-colors"
              >
                <ChevronsUpDown className="w-3.5 h-3.5" />
                {expandedLetters.size > 0 ? 'Collapse' : 'Expand'} all
              </button>
            )}
          </div>
        </motion.div>

        {/* ── Divider ── */}
        <div className="border-t border-stone-200/50 mb-8" />

        {/* ── Content ── */}
        {error ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-20"
          >
            <p className="text-stone-600 mb-4">{error}</p>
            <button
              onClick={() => { setRetryCount(0); loadBibliography(false); }}
              className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium bg-stone-800 text-white rounded-lg hover:bg-stone-700 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Retry
            </button>
          </motion.div>
        ) : loading ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="py-8"
          >
            <BibSkeleton />
            <p className="text-center text-sm text-stone-400 mt-8">{loadingMessage}</p>
            {retryCount > 0 && (
              <p className="text-center text-xs text-stone-400 mt-2">
                Backend may take up to 30 seconds to start.
              </p>
            )}
          </motion.div>
        ) : filteredBibliography.length === 0 ? (
          <div className="text-center py-20">
            <BookOpen className="w-10 h-10 text-stone-300 mx-auto mb-4" />
            <p className="text-stone-500">
              {isFiltered ? 'No references match your filters.' : 'No references available.'}
            </p>
            {isFiltered && (
              <button
                onClick={() => { setSearchQuery(''); setFilterType('all'); setFilterYear('all'); setFilterPublisher('all'); }}
                className="mt-3 text-sm text-stone-500 hover:text-stone-700 underline underline-offset-2 transition-colors"
              >
                Clear filters
              </button>
            )}
          </div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="space-y-1 pb-16"
          >
            {letters.map((letter, letterIdx) => {
              const isExpanded = expandedLetters.has(letter);
              const refs = groupedBibliography[letter];

              return (
                <motion.div
                  key={letter}
                  initial={{ opacity: 0, y: 8 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: '-20px' }}
                  transition={{ duration: 0.35, delay: letterIdx * 0.02 }}
                >
                  {/* Letter header */}
                  <button
                    onClick={() => toggleLetter(letter)}
                    className="w-full flex items-center gap-3 py-3 px-1 group hover:bg-stone-50/50 rounded-lg transition-colors"
                  >
                    <span className="w-8 h-8 rounded-lg bg-stone-100 group-hover:bg-stone-200/80 flex items-center justify-center text-sm font-display font-bold text-stone-600 transition-colors">
                      {letter}
                    </span>
                    <span className="text-xs text-stone-400 font-medium">
                      {refs.length} {refs.length === 1 ? 'reference' : 'references'}
                    </span>
                    <div className="flex-1" />
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4 text-stone-400" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-stone-400" />
                    )}
                  </button>

                  {/* Expanded references */}
                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
                        className="overflow-hidden"
                      >
                        <div className="ml-11 border-l border-stone-200/60 mb-4">
                          {refs.map((ref, index) => {
                            const entry = bibliographyData.get(ref);
                            const hasAccess = entry && entry.verified_links && entry.verified_links.length > 0;
                            const multipleLinks = hasAccess && entry.verified_links!.length > 1;
                            const globalIndex = filteredBibliography.indexOf(ref) + 1;

                            return (
                              <div
                                key={index}
                                className="group/ref flex items-start gap-3 py-2.5 pl-4 pr-2 hover:bg-stone-50/50 rounded-r-lg transition-colors -ml-px border-l-2 border-transparent hover:border-stone-300"
                              >
                                {/* Index number */}
                                <span className="flex-shrink-0 text-[11px] text-stone-300 font-mono tabular-nums pt-0.5 w-6 text-right">
                                  {globalIndex}
                                </span>

                                {/* Citation text */}
                                <p className="flex-1 text-[13px] text-stone-600 leading-relaxed">
                                  {ref}
                                </p>

                                {/* Access links */}
                                {hasAccess && (
                                  <div className="flex-shrink-0 flex items-center gap-1 opacity-0 group-hover/ref:opacity-100 transition-opacity">
                                    <a
                                      href={entry.verified_links![0].url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="inline-flex items-center gap-1 px-2 py-1 text-[11px] font-medium text-stone-500 hover:text-stone-700 bg-stone-100 hover:bg-stone-200 rounded-md transition-colors"
                                      title={entry.verified_links![0].label}
                                    >
                                      <ExternalLink className="w-3 h-3" />
                                      Open
                                    </a>
                                    {multipleLinks && (
                                      <div className="relative group/more">
                                        <button
                                          className="inline-flex items-center p-1 text-stone-400 hover:text-stone-600 hover:bg-stone-100 rounded-md transition-colors"
                                          title="More access options"
                                        >
                                          <MoreVertical className="w-3 h-3" />
                                        </button>
                                        <div className="absolute right-0 top-full mt-1 w-52 bg-white border border-stone-200/80 rounded-lg shadow-lg opacity-0 invisible group-hover/more:opacity-100 group-hover/more:visible transition-all z-10">
                                          {entry.verified_links!.map((link, linkIdx) => (
                                            <a
                                              key={linkIdx}
                                              href={link.url}
                                              target="_blank"
                                              rel="noopener noreferrer"
                                              className="flex items-center gap-2 px-3 py-2 text-xs text-stone-600 hover:bg-stone-50 first:rounded-t-lg last:rounded-b-lg transition-colors"
                                            >
                                              <ExternalLink className="w-3 h-3 flex-shrink-0 text-stone-400" />
                                              <span className="truncate">{link.label}</span>
                                            </a>
                                          ))}
                                        </div>
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              );
            })}
          </motion.div>
        )}

        {/* ── How to cite ── */}
        {!loading && bibliography.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="border-t border-stone-200/50 pt-10 pb-16"
          >
            <h2 className="text-sm font-medium text-stone-400 uppercase tracking-wider mb-4">How to Cite</h2>
            <div className="bg-stone-50/60 rounded-xl p-5 border border-stone-200/40">
              <p className="font-mono text-[13px] leading-relaxed text-stone-600">
                Girardi, R. (2026). <span className="italic font-serif text-stone-700">EleutherIA: Ancient Free Will Database</span>. Zenodo.{" "}
                <a
                  href="https://doi.org/10.5281/zenodo.17379489"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-stone-500 hover:text-stone-700 underline underline-offset-2 decoration-stone-300 hover:decoration-stone-500 transition-colors"
                >
                  https://doi.org/10.5281/zenodo.17379489
                </a>
              </p>
            </div>
            <p className="text-xs text-stone-400 mt-3">
              All {bibliography.length} references are cited in the knowledge graph with full provenance tracking.
            </p>
          </motion.div>
        )}
      </div>
    </div>
  );
}
