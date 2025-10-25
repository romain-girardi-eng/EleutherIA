import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import {
  Brain,
  Network,
  Search,
  BookOpen,
  Sparkles,
  ArrowRight,
  CheckCircle,
  Zap,
  Target,
  TrendingUp
} from 'lucide-react';

interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  example: string;
  delay: number;
  color?: 'primary' | 'sage' | 'terracotta';
}

const FeatureCard: React.FC<FeatureCardProps> = ({ icon, title, description, example, delay, color = 'primary' }) => {
  const bgColorClass = color === 'sage'
    ? 'bg-[#769687]/10'
    : color === 'terracotta'
    ? 'bg-[#b61b21]/10'
    : 'bg-primary-100';

  const textColorClass = color === 'sage'
    ? 'text-[#769687]'
    : color === 'terracotta'
    ? 'text-[#b61b21]'
    : 'text-primary-700';

  const borderColorClass = color === 'sage'
    ? 'hover:border-[#769687]/30'
    : color === 'terracotta'
    ? 'hover:border-[#b61b21]/30'
    : 'hover:border-primary-300';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5 }}
      className={`bg-white rounded-xl shadow-md p-6 border border-gray-200 ${borderColorClass} hover:shadow-xl transition-all duration-300`}
    >
      <div className="flex items-start gap-4">
        <div className={`p-3 ${bgColorClass} rounded-lg`}>
          <div className={textColorClass}>{icon}</div>
        </div>
        <div className="flex-1">
          <h3 className="text-xl font-bold text-gray-900 mb-2">{title}</h3>
          <p className="text-gray-600 mb-3">{description}</p>
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
            <p className="text-sm text-gray-700 italic">"{example}"</p>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

interface StatCardProps {
  label: string;
  value: string;
  icon: React.ReactNode;
  delay: number;
  color?: 'primary' | 'sage' | 'terracotta';
}

const StatCard: React.FC<StatCardProps> = ({ label, value, icon, delay, color = 'primary' }) => {
  const colorClasses = color === 'sage'
    ? 'text-[#769687]'
    : color === 'terracotta'
    ? 'text-[#b61b21]'
    : 'text-primary-500';

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay, duration: 0.5 }}
      className="bg-white rounded-xl shadow-md hover:shadow-xl p-6 border border-gray-200 transition-shadow duration-300"
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-600">{label}</span>
        <div className={colorClasses}>{icon}</div>
      </div>
      <div className="text-3xl font-bold text-gray-900">{value}</div>
    </motion.div>
  );
};

export default function GraphRAGShowcase() {
  const navigate = useNavigate();
  const [activeDemo, setActiveDemo] = useState<number>(0);

  const demoQueries = [
    {
      query: "What is Aristotle's concept of voluntary action?",
      highlight: "Single philosopher deep dive",
    },
    {
      query: "How did the Stoics reconcile fate with moral responsibility?",
      highlight: "School-wide doctrinal analysis",
    },
    {
      query: "What arguments did Carneades use against Stoic determinism?",
      highlight: "Dialectical relationships",
    },
    {
      query: "How does Augustine's view of grace relate to free will?",
      highlight: "Cross-period conceptual evolution",
    },
  ];

  const handleQueryClick = (query: string) => {
    navigate('/graphrag', { state: { initialQuery: query } });
  };

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveDemo((prev) => (prev + 1) % demoQueries.length);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-slate-50 to-stone-50">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-12 lg:py-20">
        <motion.div
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
          className="text-center mb-16"
        >
          <div className="inline-flex items-center gap-2 bg-slate-100 border border-slate-300 rounded-full px-4 py-2 mb-6">
            <Sparkles className="w-4 h-4 text-slate-600" />
            <span className="text-sm font-semibold text-slate-700">
              Advanced AI-Powered Research
            </span>
          </div>

          <h1 className="text-4xl lg:text-6xl font-serif font-bold text-gray-900 mb-6">
            GraphRAG Question Answering
          </h1>

          <p className="text-xl lg:text-2xl text-gray-600 max-w-3xl mx-auto mb-8 leading-relaxed">
            The world's first <span className="font-bold text-primary-700">Graph-based Retrieval-Augmented Generation</span> system
            for ancient debates on free will. Get scholarly answers grounded in 509 nodes, 820 relationships, and 1,706 sources.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link
              to="/graphrag"
              className="inline-flex items-center gap-2 px-8 py-4 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300"
            >
              <Brain className="w-5 h-5" />
              Try GraphRAG Now
              <ArrowRight className="w-5 h-5" />
            </Link>

            <a
              href="#how-it-works"
              className="inline-flex items-center gap-2 px-8 py-4 bg-white text-primary-700 font-semibold rounded-xl border-2 border-primary-300 hover:border-primary-500 hover:bg-primary-50 hover:shadow-lg transition-all duration-300"
            >
              See How It Works
            </a>
          </div>
        </motion.div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          <StatCard
            label="Knowledge Graph Nodes"
            value="509"
            icon={<Network className="w-6 h-6" />}
            delay={0.1}
            color="sage"
          />
          <StatCard
            label="Relationships Mapped"
            value="820"
            icon={<TrendingUp className="w-6 h-6" />}
            delay={0.2}
            color="sage"
          />
          <StatCard
            label="Ancient Sources"
            value="785"
            icon={<BookOpen className="w-6 h-6" />}
            delay={0.3}
            color="sage"
          />
          <StatCard
            label="Modern Scholarship"
            value="921"
            icon={<Sparkles className="w-6 h-6" />}
            delay={0.4}
            color="sage"
          />
        </div>

        {/* Live Demo Queries */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5, duration: 0.7 }}
          className="bg-white rounded-2xl shadow-2xl p-8 mb-16 border border-gray-200"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-[#769687]/10 rounded-lg">
              <Search className="w-6 h-6 text-[#769687]" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900">Example Questions</h2>
          </div>

          <div className="space-y-3">
            {demoQueries.map((demo, idx) => (
              <motion.div
                key={idx}
                animate={{
                  scale: activeDemo === idx ? 1.02 : 1,
                  backgroundColor: activeDemo === idx ? '#f1f5f9' : '#ffffff',
                }}
                transition={{ duration: 0.3 }}
                className="p-4 rounded-xl border-2 cursor-pointer hover:shadow-lg transition-shadow"
                style={{
                  borderColor: activeDemo === idx ? '#64748b' : '#e5e7eb',
                }}
                onClick={() => handleQueryClick(demo.query)}
              >
                <div className="flex items-start gap-3">
                  <CheckCircle
                    className={`w-5 h-5 mt-0.5 ${
                      activeDemo === idx ? 'text-[#769687]' : 'text-gray-400'
                    }`}
                  />
                  <div className="flex-1">
                    <p className="text-gray-900 font-medium italic mb-1">"{demo.query}"</p>
                    <p className="text-sm text-gray-600">
                      <span className="font-semibold text-[#769687]">Demonstrates:</span> {demo.highlight}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          <div className="mt-6 pt-6 border-t border-gray-200 text-center">
            <Link
              to="/graphrag"
              className="inline-flex items-center gap-2 text-[#769687] hover:text-[#5a7366] font-semibold"
            >
              Ask your own question
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </motion.div>

        {/* Features Grid */}
        <div id="how-it-works" className="mb-16">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7 }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl lg:text-4xl font-serif font-bold text-gray-900 mb-4">
              Why GraphRAG is Revolutionary
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Traditional search finds keywords. GraphRAG understands relationships,
              traces intellectual genealogies, and synthesizes scholarly answers.
            </p>
          </motion.div>

          <div className="space-y-6">
            <FeatureCard
              icon={<Network className="w-8 h-8" />}
              title="Discovers Hidden Relationships"
              description="GraphRAG doesn't just find isolated facts—it traverses the knowledge graph to reveal how ideas influenced each other across centuries."
              example="Find Augustine → discover his opponent Pelagius → trace back to Stoic concepts Augustine adapted → reveal the complete intellectual debate"
              delay={0.1}
              color="terracotta"
            />

            <FeatureCard
              icon={<Brain className="w-8 h-8" />}
              title="Multi-Hop Reasoning"
              description="Follow chains of influence across philosophers, schools, and time periods to answer complex historical questions."
              example="Trace how Aristotelian ethics influenced Christian theology through Alexander of Aphrodisias, Arabic commentators, and Thomas Aquinas"
              delay={0.2}
              color="terracotta"
            />

            <FeatureCard
              icon={<BookOpen className="w-8 h-8" />}
              title="Automatic Citation Extraction"
              description="Every claim is grounded in ancient sources and modern scholarship, automatically extracted from the knowledge graph."
              example="Get precise citations like 'Aristotle, EN III.1, 1110a1-4' and 'Bobzien 1998, Frede 2011' with zero hallucination"
              delay={0.3}
              color="terracotta"
            />

            <FeatureCard
              icon={<Zap className="w-8 h-8" />}
              title="Dialectical Mapping"
              description="See the full landscape of arguments, counter-arguments, and responses—not just isolated opinions."
              example="Chrysippus's determinism → Carneades's refutations → Cicero's synthesis → Neoplatonic responses"
              delay={0.4}
              color="terracotta"
            />

            <FeatureCard
              icon={<Target className="w-8 h-8" />}
              title="Conceptual Evolution Tracking"
              description="Watch how philosophical terms evolved across 800 years, from Greek to Latin to Christian theology."
              example="ἐφ' ἡμῖn (Aristotle, 4th c. BCE) → Stoic adoption → Carneades's critique → in nostra potestate (Latin) → Christian free will"
              delay={0.5}
              color="terracotta"
            />
          </div>
        </div>

        {/* Technical Pipeline */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
          className="bg-gradient-to-br from-primary-50 to-primary-100 rounded-2xl shadow-xl p-8 border border-primary-200 mb-16"
        >
          <h2 className="text-3xl font-bold mb-8 text-center text-primary-900">How GraphRAG Works</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              {
                step: 1,
                title: "Vector Search",
                description: "Query embedded with Gemini, compared against 509 node embeddings in Qdrant vector DB",
              },
              {
                step: 2,
                title: "Graph Traversal",
                description: "Breadth-first search expands from starting nodes via relationships (authored, influenced, refutes)",
              },
              {
                step: 3,
                title: "Context Building",
                description: "Ancient sources and modern scholarship extracted from retrieved nodes",
              },
              {
                step: 4,
                title: "LLM Synthesis",
                description: "Gemini generates scholarly answer grounded exclusively in KG context",
              },
              {
                step: 5,
                title: "Citation Extraction",
                description: "Automatic extraction of ancient sources and modern scholarship",
              },
              {
                step: 6,
                title: "Reasoning Path",
                description: "Full transparency: see which nodes and relationships were used",
              },
            ].map((item, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.1, duration: 0.5 }}
                className="bg-white/80 backdrop-blur-sm rounded-xl p-6 border border-primary-200 shadow-md hover:shadow-lg transition-shadow"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 bg-primary-200 text-primary-800 rounded-full flex items-center justify-center font-bold text-xl">
                    {item.step}
                  </div>
                  <h3 className="text-xl font-bold text-primary-900">{item.title}</h3>
                </div>
                <p className="text-gray-700 leading-relaxed">{item.description}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Final CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
          className="text-center"
        >
          <h2 className="text-3xl lg:text-4xl font-serif font-bold text-gray-900 mb-6">
            Ready to Explore Ancient Free Will Debates?
          </h2>
          <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
            Experience the future of philosophical research. Ask questions about free will, fate, and moral responsibility,
            and get answers backed by 1,706 scholarly sources.
          </p>
          <Link
            to="/graphrag"
            className="inline-flex items-center gap-3 px-10 py-5 bg-primary-600 hover:bg-primary-700 text-white text-lg font-bold rounded-xl shadow-2xl hover:shadow-3xl hover:scale-105 transition-all duration-300"
          >
            <Brain className="w-6 h-6" />
            Start Using GraphRAG
            <ArrowRight className="w-6 h-6" />
          </Link>
        </motion.div>
      </div>
    </div>
  );
}
