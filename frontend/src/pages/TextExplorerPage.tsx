import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import type { AncientText } from '../types';

export default function TextExplorerPage() {
  const [texts, setTexts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<any>(null);

  // Filters
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [authorFilter, setAuthorFilter] = useState<string>('');
  const [languageFilter, setLanguageFilter] = useState<string>('');

  // Pagination
  const [offset, setOffset] = useState(0);
  const [limit] = useState(20);
  const [totalCount, setTotalCount] = useState(0);

  // Selected text for detail view
  const [selectedText, setSelectedText] = useState<AncientText | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    loadTexts();
    loadStats();
  }, [categoryFilter, authorFilter, languageFilter, offset]);

  const loadTexts = async () => {
    try {
      setLoading(true);
      setError(null);

      const filters: any = { offset, limit };
      if (categoryFilter) filters.category = categoryFilter;
      if (authorFilter) filters.author = authorFilter;
      if (languageFilter) filters.language = languageFilter;

      const response = await apiClient.listTexts(filters);
      setTexts(response.texts || response);
      setTotalCount(response.total || response.length);
    } catch (err: any) {
      console.error('Error loading texts:', err);
      setError(err.message || 'Failed to load texts');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const statsData = await apiClient.getTextStats();
      setStats(statsData);
    } catch (err) {
      console.error('Error loading stats:', err);
    }
  };

  const handleTextClick = async (textId: string) => {
    try {
      setLoadingDetail(true);
      const textData = await apiClient.getText(textId);
      setSelectedText(textData);
    } catch (err: any) {
      console.error('Error loading text detail:', err);
      setError(err.message || 'Failed to load text details');
    } finally {
      setLoadingDetail(false);
    }
  };

  const resetFilters = () => {
    setCategoryFilter('');
    setAuthorFilter('');
    setLanguageFilter('');
    setOffset(0);
  };

  const nextPage = () => {
    if (offset + limit < totalCount) {
      setOffset(offset + limit);
    }
  };

  const prevPage = () => {
    if (offset >= limit) {
      setOffset(offset - limit);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="academic-card">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-serif font-bold mb-2">Ancient Texts Explorer</h1>
            <p className="text-academic-muted">
              Browse and search {totalCount || 289} ancient philosophical texts
            </p>
          </div>

          {stats && (
            <div className="flex space-x-6 text-center">
              <div>
                <div className="text-2xl font-bold text-primary-600">{stats.total_texts || 289}</div>
                <div className="text-sm text-academic-muted">Total Texts</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-primary-600">{stats.lemmatized_count || 109}</div>
                <div className="text-sm text-academic-muted">Lemmatized</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="academic-card">
        <h3 className="font-semibold mb-3">Filter Texts</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Category Filter */}
          <div>
            <label className="block text-sm font-medium mb-1">Category</label>
            <select
              value={categoryFilter}
              onChange={(e) => {
                setCategoryFilter(e.target.value);
                setOffset(0);
              }}
              className="w-full px-3 py-2 border border-academic-border rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">All Categories</option>
              <option value="New Testament">New Testament</option>
              <option value="Origen">Origen</option>
              <option value="Tertullian">Tertullian</option>
              <option value="Original Works">Original Works</option>
              <option value="Augustine">Augustine</option>
              <option value="Chrysostom">Chrysostom</option>
            </select>
          </div>

          {/* Author Filter */}
          <div>
            <label className="block text-sm font-medium mb-1">Author</label>
            <input
              type="text"
              value={authorFilter}
              onChange={(e) => {
                setAuthorFilter(e.target.value);
                setOffset(0);
              }}
              placeholder="e.g., Aristotle, Paul..."
              className="w-full px-3 py-2 border border-academic-border rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          {/* Language Filter */}
          <div>
            <label className="block text-sm font-medium mb-1">Language</label>
            <select
              value={languageFilter}
              onChange={(e) => {
                setLanguageFilter(e.target.value);
                setOffset(0);
              }}
              className="w-full px-3 py-2 border border-academic-border rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">All Languages</option>
              <option value="Greek">Greek</option>
              <option value="Latin">Latin</option>
              <option value="English">English</option>
            </select>
          </div>

          {/* Reset Button */}
          <div className="flex items-end">
            <button onClick={resetFilters} className="academic-button-outline w-full">
              Reset Filters
            </button>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="academic-card bg-red-50 border-red-200 text-red-800">
          <p className="font-medium">Error: {error}</p>
        </div>
      )}

      {/* Loading */}
      {loading ? (
        <div className="academic-card text-center py-12">
          <div className="spinner w-16 h-16 mx-auto mb-4"></div>
          <p className="text-academic-muted">Loading texts...</p>
        </div>
      ) : (
        <>
          {/* Pagination Info */}
          <div className="academic-card">
            <div className="flex items-center justify-between">
              <p className="text-sm text-academic-muted">
                Showing {offset + 1} - {Math.min(offset + limit, totalCount)} of {totalCount} texts
              </p>
              <div className="flex space-x-2">
                <button
                  onClick={prevPage}
                  disabled={offset === 0}
                  className="academic-button-outline disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  ← Previous
                </button>
                <button
                  onClick={nextPage}
                  disabled={offset + limit >= totalCount}
                  className="academic-button-outline disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next →
                </button>
              </div>
            </div>
          </div>

          {/* Text Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {texts.map((text) => (
              <TextCard key={text.id} text={text} onClick={() => handleTextClick(text.id)} />
            ))}
          </div>

          {texts.length === 0 && (
            <div className="academic-card text-center py-12">
              <p className="text-academic-muted">No texts found with current filters</p>
            </div>
          )}
        </>
      )}

      {/* Text Detail Modal */}
      {selectedText && (
        <TextDetailModal
          text={selectedText}
          loading={loadingDetail}
          onClose={() => setSelectedText(null)}
        />
      )}
    </div>
  );
}

// Text Card Component
function TextCard({ text, onClick }: { text: any; onClick: () => void }) {
  return (
    <div
      onClick={onClick}
      className="academic-card hover:shadow-md transition-shadow cursor-pointer"
    >
      <h3 className="text-lg font-semibold mb-2 line-clamp-2">{text.title}</h3>

      <div className="space-y-1 text-sm text-academic-muted mb-3">
        <div>
          <strong>Author:</strong> {text.author}
        </div>
        <div>
          <strong>Category:</strong> {text.category}
        </div>
        <div>
          <strong>Language:</strong> {text.language}
        </div>
        {text.lemmatized && (
          <div className="inline-block bg-primary-100 text-primary-700 px-2 py-1 rounded text-xs font-medium">
            Lemmatized
          </div>
        )}
      </div>

      {text.excerpt && (
        <p className="text-sm text-academic-text line-clamp-3">{text.excerpt}</p>
      )}
    </div>
  );
}

// Text Detail Modal Component
function TextDetailModal({
  text,
  loading,
  onClose,
}: {
  text: AncientText;
  loading: boolean;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-academic-paper rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="border-b border-academic-border p-6">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-2xl font-serif font-bold mb-2">{text.title}</h2>
              <div className="flex flex-wrap gap-3 text-sm text-academic-muted">
                <span>
                  <strong>Author:</strong> {text.author}
                </span>
                <span>•</span>
                <span>
                  <strong>Category:</strong> {text.category}
                </span>
                <span>•</span>
                <span>
                  <strong>Language:</strong> {text.language}
                </span>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-academic-muted hover:text-academic-text text-2xl"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto" style={{ maxHeight: 'calc(90vh - 180px)' }}>
          {loading ? (
            <div className="text-center py-12">
              <div className="spinner w-12 h-12 mx-auto mb-4"></div>
              <p className="text-academic-muted">Loading text...</p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Metadata */}
              {text.source && (
                <div className="bg-blue-50 border border-blue-200 rounded p-4">
                  <h3 className="font-semibold mb-2">Source</h3>
                  <p className="text-sm">{text.source}</p>
                </div>
              )}

              {/* Text Content */}
              {text.raw_text && (
                <div>
                  <h3 className="font-semibold mb-2">Text</h3>
                  <div
                    className={`text-academic-text leading-relaxed whitespace-pre-wrap ${
                      text.language === 'Greek' ? 'greek-text' : text.language === 'Latin' ? 'latin-text' : ''
                    }`}
                  >
                    {text.raw_text.substring(0, 5000)}
                    {text.raw_text.length > 5000 && (
                      <span className="text-academic-muted italic"> ... (truncated)</span>
                    )}
                  </div>
                </div>
              )}

              {/* Lemmas */}
              {text.lemmas && text.lemmas.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-2">Lemmas ({text.lemmas.length})</h3>
                  <div className="bg-gray-50 border border-academic-border rounded p-4 max-h-64 overflow-y-auto">
                    <div className="flex flex-wrap gap-2">
                      {text.lemmas.slice(0, 100).map((lemma: string, index: number) => (
                        <span
                          key={index}
                          className="inline-block bg-white border border-academic-border px-2 py-1 rounded text-sm"
                        >
                          {lemma}
                        </span>
                      ))}
                      {text.lemmas.length > 100 && (
                        <span className="text-xs text-academic-muted self-center">
                          ...and {text.lemmas.length - 100} more
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-academic-border p-4 flex justify-end">
          <button onClick={onClose} className="academic-button">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
