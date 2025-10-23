import { Link } from 'react-router-dom';
import { Network, Search, MessageSquare, BookOpen } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';

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
          description="Explore 505 nodes and 870 relationships in an interactive network visualization"
          icon={<Network className="w-12 h-12" />}
          dataTour="kg-card"
        />

        <FeatureCard
          to="/search"
          title="Hybrid Search"
          description="Full-text, lemmatic, and semantic search across 289 ancient texts"
          icon={<Search className="w-12 h-12" />}
          dataTour="search-card"
        />

        <FeatureCard
          to="/graphrag"
          title="GraphRAG Q&A"
          description="Ask questions and get scholarly answers grounded in the knowledge graph"
          icon={<MessageSquare className="w-12 h-12" />}
          dataTour="graphrag-card"
        />

        <FeatureCard
          to="/texts"
          title="Ancient Texts"
          description="Browse and read 289 ancient Greek and Latin texts with lemmatization"
          icon={<BookOpen className="w-12 h-12" />}
          dataTour="texts-card"
        />
      </section>

      {/* Statistics */}
      <section className="academic-card relative overflow-hidden" data-tour="stats">
        <div className="absolute inset-0 bg-gradient-to-br from-transparent via-academic-bg to-transparent opacity-50"></div>
        <div className="relative z-10">
          <h3 className="text-2xl font-serif font-bold mb-6">Database Statistics</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <StatItem label="KG Nodes" value="505" delay={0} />
            <StatItem label="Edges" value="870" delay={100} />
            <StatItem label="Ancient Texts" value="289" delay={200} />
            <StatItem label="Citations" value="860+" delay={300} />
          </div>
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

        <div className="mt-6 flex justify-center">
          <Link
            to="/about"
            className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition-colors shadow-sm hover:shadow-md"
          >
            To know more
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </Link>
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
  dataTour,
}: {
  to: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  dataTour?: string;
}) {
  return (
    <Link
      to={to}
      className="academic-card transition-all duration-300 hover:shadow-xl hover:-translate-y-2 group"
      style={{
        ['--hover-border-color' as any]: '#769687'
      }}
      onMouseEnter={(e) => e.currentTarget.style.borderColor = '#769687'}
      onMouseLeave={(e) => e.currentTarget.style.borderColor = ''}
      data-tour={dataTour}
    >
      <div className="flex gap-4">
        <div className="flex-shrink-0 transition-all duration-300 group-hover:scale-110" style={{ color: '#769687' }}>
          {icon}
        </div>
        <div className="flex-grow">
          <h3 className="text-xl font-semibold mb-2 transition-colors group-hover:text-[#769687]" style={{ ['--hover-color' as any]: '#769687' }}>{title}</h3>
          <p className="text-sm text-academic-muted">{description}</p>
        </div>
      </div>
    </Link>
  );
}

// Animated Stat Item Component
function StatItem({ label, value, delay = 0 }: { label: string; value: string; delay?: number }) {
  const [displayValue, setDisplayValue] = useState(0);
  const [hasAnimated, setHasAnimated] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const elementRef = useRef<HTMLDivElement>(null);

  // Parse the target value (handle "200+" format)
  const targetValue = parseInt(value.replace(/\D/g, '')) || 0;
  const suffix = value.match(/\D+$/)?.[0] || '';

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasAnimated) {
          setIsVisible(true);
          setHasAnimated(true);

          // Start animation after delay
          setTimeout(() => {
            // Animation parameters
            const duration = 2000; // 2 seconds
            const steps = 60;
            const stepDuration = duration / steps;
            const increment = targetValue / steps;

            let currentStep = 0;

            const timer = setInterval(() => {
              currentStep++;
              const newValue = Math.min(
                Math.floor(increment * currentStep),
                targetValue
              );
              setDisplayValue(newValue);

              if (currentStep >= steps) {
                clearInterval(timer);
                setDisplayValue(targetValue);
              }
            }, stepDuration);

            return () => clearInterval(timer);
          }, delay);
        }
      },
      { threshold: 0.3 }
    );

    if (elementRef.current) {
      observer.observe(elementRef.current);
    }

    return () => {
      if (elementRef.current) {
        observer.unobserve(elementRef.current);
      }
    };
  }, [targetValue, hasAnimated, delay]);

  return (
    <div
      ref={elementRef}
      className={`text-center transition-all duration-700 ${
        isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
      }`}
    >
      <div
        className="text-3xl font-bold mb-1 transition-all duration-300 hover:scale-110 cursor-default"
        style={{ color: '#b61b21' }}
      >
        {displayValue}{suffix}
      </div>
      <div className="text-sm text-academic-muted">{label}</div>
    </div>
  );
}
