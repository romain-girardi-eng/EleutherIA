import { Link } from 'react-router-dom';

export default function HomePage() {
  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="text-center -mt-4 pt-0 pb-12">
        <div className="flex justify-center mb-4">
          <img
            src="/logo.svg"
            alt="EleutherIA - Ancient Free Will Database"
            className="h-80 w-auto"
          />
        </div>
        <p className="text-lg text-academic-text max-w-3xl mx-auto leading-relaxed">
          A FAIR-compliant knowledge graph documenting ancient debates on free will, fate, and moral responsibility
          from Aristotle (4th c. BCE) to Boethius (6th c. CE).
        </p>
      </section>

      {/* Feature Cards */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <FeatureCard
          to="/visualizer"
          title="Knowledge Graph"
          description="Explore 465 nodes and 740 relationships in an interactive network visualization"
          icon="🕸️"
        />

        <FeatureCard
          to="/search"
          title="Hybrid Search"
          description="Full-text, lemmatic, and semantic search across 289 ancient texts"
          icon="🔍"
        />

        <FeatureCard
          to="/graphrag"
          title="GraphRAG Q&A"
          description="Ask questions and get scholarly answers grounded in the knowledge graph"
          icon="💬"
        />

        <FeatureCard
          to="/texts"
          title="Ancient Texts"
          description="Browse and read 289 ancient Greek and Latin texts with lemmatization"
          icon="📜"
        />
      </section>

      {/* Statistics */}
      <section className="academic-card">
        <h3 className="text-2xl font-serif font-bold mb-6">Database Statistics</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <StatItem label="KG Nodes" value="465" />
          <StatItem label="Edges" value="740" />
          <StatItem label="Ancient Texts" value="289" />
          <StatItem label="Citations" value="200+" />
        </div>
      </section>

      {/* About Section */}
      <section className="academic-card">
        <h3 className="text-2xl font-serif font-bold mb-4">About This Database</h3>
        <div className="prose max-w-none text-academic-text space-y-4">
          <p>
            <strong>EleutherIA</strong> (Ἐλευθερία = freedom + IA = Intelligence Artificielle) documents
            the historical development of ancient debates on free will, determinism, and moral responsibility,
            spanning from Classical Greek philosophy through Late Antiquity.
          </p>

          <p>
            The database combines a comprehensive knowledge graph with 289 ancient texts, enabling advanced
            research through:
          </p>

          <ul className="list-disc list-inside space-y-2 ml-4">
            <li>Interactive network visualization with Cytoscape.js</li>
            <li>Hybrid search combining full-text, lemmatic, and semantic approaches</li>
            <li>GraphRAG question answering with citation tracking</li>
            <li>FAIR-compliant data with complete provenance</li>
          </ul>

          <p>
            All data is licensed under{' '}
            <a href="https://creativecommons.org/licenses/by/4.0/" className="text-primary-600 hover:underline">
              CC BY 4.0
            </a>{' '}
            and available at{' '}
            <a href="https://doi.org/10.5281/zenodo.17379490" className="text-primary-600 hover:underline">
              DOI: 10.5281/zenodo.17379490
            </a>
          </p>
        </div>
      </section>
    </div>
  );
}

// Feature Card Component
function FeatureCard({
  to,
  title,
  description,
  icon,
}: {
  to: string;
  title: string;
  description: string;
  icon: string;
}) {
  return (
    <Link
      to={to}
      className="academic-card transition-all duration-300 hover:shadow-xl hover:-translate-y-2 hover:border-primary-400 group"
    >
      <div className="text-4xl mb-4 transition-transform duration-300 group-hover:scale-110">{icon}</div>
      <h3 className="text-xl font-semibold mb-2 group-hover:text-primary-600 transition-colors">{title}</h3>
      <p className="text-sm text-academic-muted">{description}</p>
    </Link>
  );
}

// Stat Item Component
function StatItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-center">
      <div className="text-3xl font-bold text-primary-600 mb-1">{value}</div>
      <div className="text-sm text-academic-muted">{label}</div>
    </div>
  );
}
