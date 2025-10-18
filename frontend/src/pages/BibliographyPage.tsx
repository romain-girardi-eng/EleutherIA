import { useState, useEffect } from 'react';
import { GraduationCap, Search, BookOpen } from 'lucide-react';
import { apiClient } from '../api/client';

export default function BibliographyPage() {
  const [bibliography, setBibliography] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadBibliography();
  }, []);

  const loadBibliography = async () => {
    try {
      setLoading(true);

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
    } catch (error) {
      console.error('Error loading bibliography:', error);
    } finally {
      setLoading(false);
    }
  };

  // Filter bibliography by search query
  const filteredBibliography = bibliography.filter(ref =>
    !searchQuery || ref.toLowerCase().includes(searchQuery.toLowerCase())
  );

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
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
            100%
          </div>
          <div className="text-sm font-medium text-academic-text">Citation Coverage</div>
        </div>
      </div>

      {/* Search */}
      <div className="academic-card">
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
        {searchQuery && (
          <div className="mt-3 text-sm text-academic-muted">
            Found {filteredBibliography.length} of {bibliography.length} references
          </div>
        )}
      </div>

      {/* Bibliography List */}
      <section className="academic-card">
        <div className="flex items-center gap-3 mb-6">
          <BookOpen className="w-6 h-6 text-primary-600" />
          <h2 className="text-2xl font-serif font-bold">References</h2>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            <p className="mt-4 text-academic-muted">Loading bibliography...</p>
          </div>
        ) : filteredBibliography.length === 0 ? (
          <div className="text-center py-12">
            <GraduationCap className="w-16 h-16 text-academic-muted mx-auto mb-4" />
            <p className="text-academic-muted">
              {searchQuery ? 'No references found matching your search.' : 'No references available.'}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredBibliography.map((ref, index) => (
              <div
                key={index}
                className="p-4 bg-academic-bg border border-academic-border rounded-lg hover:border-primary-300 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-8 text-sm text-academic-muted font-mono">
                    [{index + 1}]
                  </div>
                  <div className="flex-1 text-sm text-academic-text leading-relaxed">
                    {ref}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Citation Info */}
      <section className="academic-card bg-blue-50 border border-blue-200">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0">
            <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="text-sm">
            <div className="font-semibold text-blue-900 mb-2">How to Cite This Database</div>
            <div className="bg-white p-3 rounded border border-blue-300 font-mono text-xs text-academic-text mb-3">
              Girardi, R. (2025). <span className="italic">EleutherIA: Ancient Free Will Database</span>.
              Zenodo. https://doi.org/10.5281/zenodo.17379490
            </div>
            <p className="text-blue-800 leading-relaxed">
              All references listed above are cited within knowledge graph node metadata and
              automatically included in GraphRAG responses with proper attribution.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
