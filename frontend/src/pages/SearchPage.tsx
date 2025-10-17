import { useState } from 'react';
import { apiClient } from '../api/client';
import type { SearchResult, HybridSearchResponse } from '../types';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<HybridSearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Search mode toggles
  const [enableFulltext, setEnableFulltext] = useState(true);
  const [enableLemmatic, setEnableLemmatic] = useState(true);
  const [enableSemantic, setEnableSemantic] = useState(true);
  const [limit, setLimit] = useState(10);

  // Active tab
  const [activeTab, setActiveTab] = useState<'combined' | 'fulltext' | 'lemmatic' | 'semantic'>('combined');

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await apiClient.hybridSearch({
        query: query.trim(),
        limit,
        enable_fulltext: enableFulltext,
        enable_lemmatic: enableLemmatic,
        enable_semantic: enableSemantic,
      });

      setResults(response);
    } catch (err: any) {
      console.error('Search error:', err);
      setError(err.message || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const getCurrentResults = () => {
    if (!results) return [];
    switch (activeTab) {
      case 'combined':
        return results.combined_results;
      case 'fulltext':
        return results.fulltext_results;
      case 'lemmatic':
        return results.lemmatic_results;
      case 'semantic':
        return results.semantic_results;
      default:
        return results.combined_results;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="academic-card">
        <h1 className="text-3xl font-serif font-bold mb-2">Hybrid Search</h1>
        <p className="text-academic-muted">
          Search across 289 ancient texts using full-text, lemmatic, and semantic approaches
        </p>
      </div>

      {/* Search Form */}
      <div className="academic-card">
        <form onSubmit={handleSearch} className="space-y-4">
          {/* Search Input */}
          <div>
            <label htmlFor="query" className="block text-sm font-medium mb-2">
              Search Query
            </label>
            <input
              type="text"
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g., ἐφ' ἡμῖν, liberum arbitrium, voluntary action..."
              className="w-full px-4 py-2 border border-academic-border rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <p className="text-xs text-academic-muted mt-1">
              Supports Greek, Latin, and English terms
            </p>
          </div>

          {/* Search Options */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Mode Toggles */}
            <div>
              <label className="block text-sm font-medium mb-2">Search Modes</label>
              <div className="space-y-2">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={enableFulltext}
                    onChange={(e) => setEnableFulltext(e.target.checked)}
                    className="rounded"
                  />
                  <span className="text-sm">Full-text (PostgreSQL ts_rank)</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={enableLemmatic}
                    onChange={(e) => setEnableLemmatic(e.target.checked)}
                    className="rounded"
                  />
                  <span className="text-sm">Lemmatic (109 lemmatized texts)</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={enableSemantic}
                    onChange={(e) => setEnableSemantic(e.target.checked)}
                    className="rounded"
                  />
                  <span className="text-sm">Semantic (Qdrant vectors)</span>
                </label>
              </div>
            </div>

            {/* Result Limit */}
            <div>
              <label htmlFor="limit" className="block text-sm font-medium mb-2">
                Results Limit
              </label>
              <select
                id="limit"
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
                className="w-full px-4 py-2 border border-academic-border rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value={5}>5 results</option>
                <option value={10}>10 results</option>
                <option value={20}>20 results</option>
                <option value={50}>50 results</option>
              </select>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="academic-button disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>
      </div>

      {/* Error */}
      {error && (
        <div className="academic-card bg-red-50 border-red-200 text-red-800">
          <p className="font-medium">Error: {error}</p>
        </div>
      )}

      {/* Results */}
      {results && (
        <>
          {/* Result Tabs */}
          <div className="academic-card">
            <div className="flex items-center space-x-4 border-b border-academic-border pb-2">
              <TabButton
                active={activeTab === 'combined'}
                onClick={() => setActiveTab('combined')}
                label="Combined (RRF)"
                count={results.combined_results.length}
              />
              <TabButton
                active={activeTab === 'fulltext'}
                onClick={() => setActiveTab('fulltext')}
                label="Full-text"
                count={results.fulltext_results.length}
              />
              <TabButton
                active={activeTab === 'lemmatic'}
                onClick={() => setActiveTab('lemmatic')}
                label="Lemmatic"
                count={results.lemmatic_results.length}
              />
              <TabButton
                active={activeTab === 'semantic'}
                onClick={() => setActiveTab('semantic')}
                label="Semantic"
                count={results.semantic_results.length}
              />
            </div>

            {/* Result Count */}
            <div className="mt-4 text-sm text-academic-muted">
              Found <strong className="text-academic-text">{results.total_found}</strong> results
            </div>
          </div>

          {/* Result List */}
          <div className="space-y-4">
            {getCurrentResults().length > 0 ? (
              getCurrentResults().map((result, index) => (
                <SearchResultCard key={result.id} result={result} index={index} />
              ))
            ) : (
              <div className="academic-card text-center py-12">
                <p className="text-academic-muted">No results found for this search mode</p>
              </div>
            )}
          </div>
        </>
      )}

      {/* Help Section */}
      {!results && !loading && (
        <div className="academic-card bg-blue-50 border-blue-200">
          <h3 className="font-semibold mb-2">Search Tips</h3>
          <ul className="text-sm text-academic-text space-y-1 list-disc list-inside">
            <li><strong>Greek text:</strong> Try "ἐφ' ἡμῖν", "ἑκούσιον", "προαίρεσις"</li>
            <li><strong>Latin text:</strong> Try "liberum arbitrium", "in nostra potestate", "voluntarium"</li>
            <li><strong>English:</strong> Try "voluntary action", "free will", "moral responsibility"</li>
            <li><strong>Hybrid search</strong> combines all three modes using Reciprocal Rank Fusion (RRF)</li>
          </ul>
        </div>
      )}
    </div>
  );
}

// Tab Button Component
function TabButton({
  active,
  onClick,
  label,
  count,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
  count: number;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 text-sm font-medium rounded transition-colors ${
        active
          ? 'bg-primary-100 text-primary-700'
          : 'text-academic-muted hover:text-academic-text hover:bg-gray-50'
      }`}
    >
      {label} <span className="ml-1 text-xs">({count})</span>
    </button>
  );
}

// Search Result Card Component
function SearchResultCard({ result, index }: { result: SearchResult; index: number }) {
  return (
    <div className="academic-card hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {/* Result Number & Title */}
          <div className="flex items-start space-x-3">
            <span className="flex-shrink-0 text-sm font-medium text-primary-600">
              #{index + 1}
            </span>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-academic-text mb-1">
                {result.title}
              </h3>

              {/* Metadata */}
              <div className="flex flex-wrap gap-3 text-sm text-academic-muted mb-2">
                <span>
                  <strong>Author:</strong> {result.author}
                </span>
                <span>•</span>
                <span>
                  <strong>Category:</strong> {result.category}
                </span>
                <span>•</span>
                <span>
                  <strong>Language:</strong> {result.language}
                </span>
              </div>

              {/* Snippet */}
              {result.snippet && (
                <div
                  className="text-sm text-academic-text bg-gray-50 border-l-4 border-primary-200 p-3 mt-2"
                  dangerouslySetInnerHTML={{ __html: result.snippet }}
                />
              )}

              {/* Scores */}
              <div className="flex gap-4 mt-3 text-xs">
                {result.rrf_score !== undefined && (
                  <span className="text-primary-600 font-medium">
                    RRF Score: {result.rrf_score.toFixed(4)}
                  </span>
                )}
                {result.rank !== undefined && (
                  <span className="text-academic-muted">
                    Rank: {result.rank.toFixed(4)}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* View Button */}
        <button className="academic-button-outline ml-4">View Text</button>
      </div>
    </div>
  );
}
