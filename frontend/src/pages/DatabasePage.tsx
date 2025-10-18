import { BookOpen, Network, GraduationCap, Search, Database, FileText } from 'lucide-react';

export default function DatabasePage() {

  return (
    <div className="space-y-8">
      {/* Header */}
      <section className="academic-card">
        <div className="flex items-start gap-4">
          <Database className="w-12 h-12 text-primary-600 flex-shrink-0 mt-1" />
          <div>
            <h1 className="text-3xl font-serif font-bold mb-3">Database Sources</h1>
            <p className="text-lg text-academic-muted leading-relaxed">
              EleutherIA integrates three complementary data sources: a curated knowledge graph,
              a comprehensive corpus of ancient texts, and an extensive bibliography of modern scholarship.
              All sources are FAIR-compliant and available under CC BY 4.0.
            </p>
          </div>
        </div>
      </section>

      {/* Primary Corpus - Ancient Texts */}
      <section className="academic-card">
        <div className="flex items-start gap-4 mb-6">
          <BookOpen className="w-8 h-8 text-primary-600 flex-shrink-0" />
          <div>
            <h2 className="text-2xl font-serif font-bold mb-2">Primary Corpus: Ancient Texts</h2>
            <p className="text-academic-muted leading-relaxed">
              Complete collection of Greek and Latin philosophical texts from the 4th century BCE to the 6th century CE
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <StatCard number="289" label="Ancient Texts" icon={<FileText className="w-5 h-5" />} />
          <StatCard number="109" label="Lemmatized Texts" icon={<Search className="w-5 h-5" />} />
          <StatCard number="2" label="Languages" sublabel="Greek & Latin" icon={<BookOpen className="w-5 h-5" />} />
        </div>

        <div className="bg-academic-bg rounded-lg p-6">
          <h3 className="font-semibold text-lg mb-4">Features & Capabilities</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FeatureItem
              title="Full-Text Search"
              description="PostgreSQL full-text search (ts_rank) across all 289 texts with ranking and relevance scoring"
            />
            <FeatureItem
              title="Lemmatic Search"
              description="Morphological analysis on 109 texts enables search by dictionary form, capturing all inflections"
            />
            <FeatureItem
              title="Complete Texts"
              description="Full original texts preserved with proper encoding for Greek (polytonic) and Latin characters"
            />
            <FeatureItem
              title="Structured Metadata"
              description="Author, title, date, language, text type, and canonical citations for each text"
            />
          </div>

          <div className="mt-6 pt-6 border-t border-academic-border">
            <h4 className="font-semibold mb-3">Text Coverage by Period</h4>
            <div className="space-y-2 text-sm">
              <PeriodBar period="Classical Greek (5th-4th c. BCE)" percentage={15} />
              <PeriodBar period="Hellenistic Greek (3rd-1st c. BCE)" percentage={25} />
              <PeriodBar period="Roman Imperial (1st-3rd c. CE)" percentage={30} />
              <PeriodBar period="Patristic & Late Antiquity (2nd-6th c. CE)" percentage={30} />
            </div>
          </div>
        </div>

        <div className="mt-6 p-4 bg-primary-50 border border-primary-200 rounded-lg">
          <p className="text-sm text-academic-text">
            <span className="font-semibold">Access:</span> All ancient texts are available through the{' '}
            <a href="/texts" className="text-primary-600 hover:underline font-medium">Ancient Texts</a> browser
            and searchable via the{' '}
            <a href="/search" className="text-primary-600 hover:underline font-medium">Hybrid Search</a> interface.
          </p>
        </div>
      </section>

      {/* Knowledge Graph */}
      <section className="academic-card">
        <div className="flex items-start gap-4 mb-6">
          <Network className="w-8 h-8 text-primary-600 flex-shrink-0" />
          <div>
            <h2 className="text-2xl font-serif font-bold mb-2">Knowledge Graph</h2>
            <p className="text-academic-muted leading-relaxed">
              Structured semantic network documenting philosophical debates, arguments, and conceptual developments
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <StatCard number="465" label="Nodes" sublabel="Entities & Concepts" icon={<Network className="w-5 h-5" />} />
          <StatCard number="745" label="Edges" sublabel="Relationships" icon={<Network className="w-5 h-5" />} />
          <StatCard number="11" label="Node Types" icon={<Database className="w-5 h-5" />} />
        </div>

        <div className="bg-academic-bg rounded-lg p-6">
          <h3 className="font-semibold text-lg mb-4">Node Types Distribution</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <NodeTypeItem type="Persons" count={156} description="Philosophers, theologians, authors" />
            <NodeTypeItem type="Arguments" count={113} description="Specific philosophical arguments" />
            <NodeTypeItem type="Concepts" count={80} description="Key philosophical terms and ideas" />
            <NodeTypeItem type="Works" count={48} description="Treatises, dialogues, letters" />
            <NodeTypeItem type="Reformulations" count={53} description="Conceptual redefinitions" />
            <NodeTypeItem type="Other" count={15} description="Debates, schools, events, frameworks" />
          </div>

          <div className="mt-6 pt-6 border-t border-academic-border">
            <h4 className="font-semibold mb-3">Relationship Types</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <div className="font-medium text-primary-600 mb-2">Authorship & Creation</div>
                <ul className="space-y-1 text-academic-muted">
                  <li>• formulated, authored, developed</li>
                </ul>
              </div>
              <div>
                <div className="font-medium text-primary-600 mb-2">Intellectual Influence</div>
                <ul className="space-y-1 text-academic-muted">
                  <li>• influenced, transmitted, adapted</li>
                </ul>
              </div>
              <div>
                <div className="font-medium text-primary-600 mb-2">Dialectical Relations</div>
                <ul className="space-y-1 text-academic-muted">
                  <li>• refutes, supports, opposes, targets</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 p-4 bg-primary-50 border border-primary-200 rounded-lg">
          <p className="text-sm text-academic-text">
            <span className="font-semibold">Visualization:</span> Explore the knowledge graph interactively through the{' '}
            <a href="/visualizer" className="text-primary-600 hover:underline font-medium">Knowledge Graph Visualizer</a>
            {' '}or query it semantically via{' '}
            <a href="/graphrag" className="text-primary-600 hover:underline font-medium">GraphRAG Q&A</a>.
          </p>
        </div>
      </section>

      {/* Modern Scholarship */}
      <section className="academic-card">
        <div className="flex items-start gap-4 mb-6">
          <GraduationCap className="w-8 h-8 text-primary-600 flex-shrink-0" />
          <div>
            <h2 className="text-2xl font-serif font-bold mb-2">Modern Scholarship</h2>
            <p className="text-academic-muted leading-relaxed">
              Comprehensive bibliography of secondary literature supporting knowledge graph annotations
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <StatCard number="200+" label="Bibliography References" icon={<GraduationCap className="w-5 h-5" />} />
          <StatCard number="100%" label="Citation Coverage" sublabel="All KG nodes cited" icon={<FileText className="w-5 h-5" />} />
        </div>

        <div className="bg-academic-bg rounded-lg p-6">
          <h3 className="font-semibold text-lg mb-4">Scholarly Sources</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FeatureItem
              title="Monographs & Edited Volumes"
              description="Specialized studies on ancient philosophy, ethics, and intellectual history"
            />
            <FeatureItem
              title="Journal Articles"
              description="Peer-reviewed research from leading philosophy and classics journals"
            />
            <FeatureItem
              title="Reference Works"
              description="Stanford Encyclopedia of Philosophy, Cambridge Companions, and authoritative handbooks"
            />
            <FeatureItem
              title="Critical Editions"
              description="Modern editions with commentaries of ancient texts (OCT, Teubner, Budé, Loeb)"
            />
          </div>

          <div className="mt-6 pt-6 border-t border-academic-border">
            <h4 className="font-semibold mb-3">Citation Format</h4>
            <div className="space-y-3 text-sm">
              <div className="bg-white p-3 rounded border border-academic-border">
                <div className="font-mono text-xs text-academic-muted mb-1">Ancient Sources:</div>
                <div className="text-academic-text">
                  "Aristotle, <span className="italic">Nicomachean Ethics</span> III.1-5, 1109b30-1115a3"
                </div>
              </div>
              <div className="bg-white p-3 rounded border border-academic-border">
                <div className="font-mono text-xs text-academic-muted mb-1">Modern Scholarship:</div>
                <div className="text-academic-text">
                  "Bobzien, Susanne. <span className="italic">Determinism and Freedom in Stoic Philosophy</span>.
                  Oxford: Clarendon Press, 1998, pp. 234-267."
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 p-4 bg-primary-50 border border-primary-200 rounded-lg">
          <p className="text-sm text-academic-text">
            <span className="font-semibold">Access:</span> View the complete bibliography at{' '}
            <a href="/bibliography" className="text-primary-600 hover:underline font-medium">Bibliography</a> page.
          </p>
        </div>
      </section>

      {/* Data Standards */}
      <section className="academic-card bg-academic-bg">
        <h2 className="text-2xl font-serif font-bold mb-6">FAIR Compliance & Data Standards</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-semibold text-primary-600 mb-3">Findable</h3>
            <ul className="space-y-2 text-sm text-academic-text">
              <li>• Unique persistent identifiers for all nodes</li>
              <li>• Rich metadata with controlled vocabularies</li>
              <li>• DOI: <a href="https://doi.org/10.5281/zenodo.17379490" className="text-primary-600 hover:underline">10.5281/zenodo.17379490</a></li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-primary-600 mb-3">Accessible</h3>
            <ul className="space-y-2 text-sm text-academic-text">
              <li>• Open JSON format (13 MB)</li>
              <li>• RESTful API with full documentation</li>
              <li>• CC BY 4.0 license</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-primary-600 mb-3">Interoperable</h3>
            <ul className="space-y-2 text-sm text-academic-text">
              <li>• JSON Schema validation (Draft 07)</li>
              <li>• Standard philosophical taxonomies</li>
              <li>• Compatible with Cytoscape, Gephi, Neo4j</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-primary-600 mb-3">Reusable</h3>
            <ul className="space-y-2 text-sm text-academic-text">
              <li>• Complete provenance documentation</li>
              <li>• Semantic versioning (v1.0.0)</li>
              <li>• Extensive examples and documentation</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Technical Infrastructure */}
      <section className="academic-card">
        <h2 className="text-2xl font-serif font-bold mb-6">Technical Infrastructure</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <TechItem
            title="PostgreSQL"
            description="Relational database with full-text search, lemmatic matching, and JSON support"
          />
          <TechItem
            title="Qdrant Cloud"
            description="Vector database storing 3072-dimensional embeddings for semantic search"
          />
          <TechItem
            title="Gemini API"
            description="Text embedding (text-embedding-004) and LLM synthesis (Gemini 2.0 Flash)"
          />
        </div>
      </section>
    </div>
  );
}

// Stat Card Component
function StatCard({
  number,
  label,
  sublabel,
  icon,
}: {
  number: string;
  label: string;
  sublabel?: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="academic-card bg-academic-bg text-center">
      <div className="flex justify-center mb-2 text-primary-600">{icon}</div>
      <div className="text-3xl font-bold text-primary-600 mb-1">{number}</div>
      <div className="text-sm font-medium text-academic-text">{label}</div>
      {sublabel && <div className="text-xs text-academic-muted mt-1">{sublabel}</div>}
    </div>
  );
}

// Feature Item Component
function FeatureItem({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex gap-3">
      <div className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-primary-600 mt-2"></div>
      <div>
        <div className="font-medium text-academic-text mb-1">{title}</div>
        <div className="text-sm text-academic-muted leading-relaxed">{description}</div>
      </div>
    </div>
  );
}

// Period Bar Component
function PeriodBar({ period, percentage }: { period: string; percentage: number }) {
  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-academic-text">{period}</span>
        <span className="text-academic-muted">{percentage}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className="bg-primary-600 h-2 rounded-full transition-all duration-500"
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
    </div>
  );
}

// Node Type Item Component
function NodeTypeItem({
  type,
  count,
  description,
}: {
  type: string;
  count: number;
  description: string;
}) {
  return (
    <div className="flex justify-between items-start p-3 bg-white rounded border border-academic-border">
      <div>
        <div className="font-medium text-academic-text">{type}</div>
        <div className="text-xs text-academic-muted mt-0.5">{description}</div>
      </div>
      <div className="text-lg font-bold text-primary-600">{count}</div>
    </div>
  );
}

// Tech Item Component
function TechItem({ title, description }: { title: string; description: string }) {
  return (
    <div className="academic-card bg-academic-bg">
      <h3 className="font-semibold text-primary-600 mb-2">{title}</h3>
      <p className="text-sm text-academic-muted leading-relaxed">{description}</p>
    </div>
  );
}
