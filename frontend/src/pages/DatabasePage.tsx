import { ChevronDown, ChevronRight, ExternalLink, Database, BookOpen, Network, GraduationCap, ChevronsUpDown, ArrowRight, Shield, Globe, Layers, RefreshCw, Languages, Sparkles } from 'lucide-react';
import { Typewriter } from '../components/ui/typewriter';
import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../api/client';
import { motion, AnimatePresence } from 'framer-motion';
import { useKgStats, formatCount } from '../hooks/useKgStats';

export default function DatabasePage() {
  const { t, i18n } = useTranslation();
  const [nodeTypeData, setNodeTypeData] = useState<Record<string, Array<{ id: string; label: string }>>>({});
  const [expandedTypes, setExpandedTypes] = useState<Set<string>>(new Set());

  // Single source of truth for KG/corpus counts — fetches /api/kg/stats + /api/works/stats once.
  const stats = useKgStats();
  const fmt = (n: number) => formatCount(n, i18n.language);
  const kgStats = { nodes: stats.nodes, edges: stats.edges, sources: stats.passages };

  useEffect(() => {
    const listedTypes = ['person', 'argument', 'concept', 'work', 'reformulation'];
    Promise.all(
      listedTypes.map((type) =>
        apiClient.getNodes({ type, limit: 50000 })
          .then((data) => {
            const nodes = Array.isArray(data) ? data : (data?.nodes || []);
            const entries = nodes
              .map((node: { id: string; label?: string }) => ({ id: node.id, label: node.label || 'Unnamed' }))
              .sort((a, b) => a.label.toLowerCase().localeCompare(b.label.toLowerCase()));
            return [type, entries] as const;
          })
      )
    )
      .then((pairs) => setNodeTypeData(Object.fromEntries(pairs)))
      .catch(error => console.error('Error loading node type data:', error));
  }, []);

  const toggleType = (type: string) => {
    const next = new Set(expandedTypes);
    if (next.has(type)) next.delete(type); else next.add(type);
    setExpandedTypes(next);
  };

  const nodeTypes = [
    { key: 'person', label: 'Persons', desc: 'Philosophers, theologians, authors', count: 161 },
    { key: 'argument', label: 'Arguments', desc: 'Specific philosophical arguments', count: 117 },
    { key: 'concept', label: 'Concepts', desc: 'Key philosophical terms', count: 105 },
    { key: 'work', label: 'Works', desc: 'Treatises, dialogues, letters', count: 57 },
    { key: 'reformulation', label: 'Reformulations', desc: 'Conceptual redefinitions', count: 53 },
  ];

  // Live count per node type: prefer /api/kg/stats.node_types, then the
  // per-node listing from getNodes(), then the static fallback.
  const liveCount = (nt: { key: string; count: number }) => {
    const fromStats = stats.nodeTypes[nt.key];
    if (Number.isFinite(fromStats)) return fromStats;
    const listed = (nodeTypeData[nt.key] || []).length;
    return listed || nt.count;
  };
  const maxNodeTypeCount = Math.max(...nodeTypes.map(liveCount), 1);

  const fairPrinciples = [
    {
      letter: 'F',
      title: 'Findable',
      icon: Shield,
      items: ['Unique persistent identifiers for all nodes', 'Rich metadata with controlled vocabularies', 'DOI: 10.5281/zenodo.17379489'],
    },
    {
      letter: 'A',
      title: 'Accessible',
      icon: Globe,
      items: ['Open JSON format (13 MB)', 'RESTful API with full documentation', 'CC BY 4.0 license'],
    },
    {
      letter: 'I',
      title: 'Interoperable',
      icon: Layers,
      items: ['JSON Schema validation (Draft 07)', 'Standard philosophical taxonomies', 'Compatible with Cytoscape, Gephi, Neo4j'],
    },
    {
      letter: 'R',
      title: 'Reusable',
      icon: RefreshCw,
      items: ['Complete provenance documentation', 'Semantic versioning (v1.0.0)', 'Extensive examples and documentation'],
    },
  ];

  return (
    <div className="min-h-screen w-full bg-transparent">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">

        {/* ── Hero ── */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="pt-28 pb-10 text-center"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-stone-800/5 border border-stone-300/30 text-xs font-medium text-stone-500 tracking-wide uppercase mb-5">
            <Database className="w-3.5 h-3.5" />
            Knowledge Architecture
          </div>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-display font-semibold text-stone-800 tracking-tight mb-3">
            <Typewriter
              text={["Database Overview", "Knowledge Architecture", "Data Structure"]}
              speed={80}
              waitTime={3000}
              deleteSpeed={50}
              className="text-stone-800"
              cursorChar="_"
            />
          </h1>
          <p className="text-base sm:text-lg text-stone-500 max-w-xl mx-auto leading-relaxed">
            {t('database.subtitle')}
          </p>
        </motion.div>

        {/* ── Hero illustration: Scroll devient Graphe ── */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.7 }}
          className="max-w-5xl mx-auto mb-16"
        >
          <img
            src="/scroll-devient-graphe.webp"
            alt="An ancient Greek papyrus on the left, its inked verses transforming into a luminous network of golden knowledge-graph nodes on the right"
            className="w-full h-auto rounded-2xl shadow-xl"
          />
        </motion.div>

        {/* ── Les Voix — schools tracked in the corpus ── */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15, duration: 0.6 }}
          className="max-w-5xl mx-auto mb-16"
        >
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-stone-800/5 border border-stone-300/30 text-xs font-medium text-stone-500 tracking-wide uppercase mb-3">
              Les Voix
            </div>
            <h2 className="text-2xl sm:text-3xl font-display font-semibold text-stone-800 tracking-tight mb-2">
              Philosophical traditions in the corpus
            </h2>
            <p className="text-sm text-stone-500 max-w-xl mx-auto">
              Twelve centuries, four traditions — one luminous map.
            </p>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            {[
              { src: '/voice-01-stoicien.webp', label: 'Stoïcien', caption: 'εἱμαρμένη — fate' },
              { src: '/voice-02-epicurien.webp', label: 'Épicurien', caption: 'κλίνωμα — atomic swerve' },
              { src: '/voice-03-pere-eglise.webp', label: 'Père de l’Église', caption: 'providentia — providence' },
              { src: '/voice-04-sceptique.webp', label: 'Sceptique', caption: 'ἐποχή — suspension of judgment' },
            ].map((v) => (
              <figure key={v.src} className="group">
                <img
                  src={v.src}
                  alt={v.label}
                  loading="lazy"
                  className="w-full aspect-square object-cover rounded-xl shadow-md group-hover:shadow-lg transition-shadow"
                />
                <figcaption className="mt-2 text-center">
                  <div className="text-sm font-display font-semibold text-stone-800">{v.label}</div>
                  <div className="text-xs text-stone-500 italic">{v.caption}</div>
                </figcaption>
              </figure>
            ))}
          </div>
        </motion.div>

        {/* ── Key metrics ── */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mb-16"
        >
          {[
            { value: fmt(kgStats.nodes), label: 'KG Nodes' },
            { value: fmt(kgStats.edges), label: 'Relationships' },
            { value: fmt(stats.works), label: 'Ancient Texts' },
            { value: fmt(kgStats.sources), label: 'Passages' },
          ].map((m, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 + i * 0.06 }}
                className="py-5 px-4 bg-white/50 backdrop-blur-sm border border-stone-200/50 rounded-xl text-center hover:border-stone-300/60 hover:shadow-sm transition-all duration-300"
              >
                <div className="text-2xl sm:text-3xl font-semibold text-stone-800 leading-tight">{m.value}</div>
                <div className="text-xs text-stone-400 mt-1">{m.label}</div>
              </motion.div>
          ))}
        </motion.div>

        {/* ══════════════════════════════════════════════════
            Section 1: Ancient Texts Corpus
        ══════════════════════════════════════════════════ */}
        <motion.section
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mb-16"
        >
          <div className="flex items-center gap-3 mb-5">
            <div className="w-9 h-9 rounded-xl bg-stone-100 border border-stone-200/50 flex items-center justify-center">
              <BookOpen className="w-4.5 h-4.5 text-stone-500" />
            </div>
            <h2 className="text-xl sm:text-2xl font-display font-semibold text-stone-800">Ancient Texts Corpus</h2>
          </div>

          <p className="text-sm sm:text-[15px] text-stone-500 leading-relaxed mb-6 max-w-2xl">
            Complete collection of Greek and Latin philosophical texts from the 4th century BCE to the 6th century CE, with full-text and lemmatic search capabilities.
          </p>

          {/* Inline stats */}
          <div className="flex flex-wrap gap-3 mb-6">
            {[
              { val: fmt(stats.works), label: 'texts', icon: BookOpen },
              { val: fmt(stats.passages), label: 'passages', icon: Languages },
              { val: fmt(stats.languagesCount), label: 'languages', icon: Globe },
            ].map((s) => {
              const SIcon = s.icon;
              return (
                <div key={s.label} className="inline-flex items-center gap-2 px-3 py-1.5 bg-stone-100/60 border border-stone-200/40 rounded-lg">
                  <SIcon className="w-3.5 h-3.5 text-stone-400" />
                  <span className="text-sm"><strong className="text-stone-700 font-semibold">{s.val}</strong> <span className="text-stone-500">{s.label}</span></span>
                </div>
              );
            })}
          </div>

          {/* Features */}
          <div className="bg-stone-50/50 rounded-xl border border-stone-200/40 p-5 mb-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {[
                ['Full-Text Search', 'PostgreSQL ts_rank across the entire corpus'],
                ['Lemmatic Search', 'Morphological analysis on Greek and Latin lemmas'],
                ['Complete Texts', 'Full texts with proper encoding'],
                ['Structured Metadata', 'Author, title, date, language, citations'],
              ].map(([title, desc]) => (
                <div key={title} className="flex gap-3">
                  <div className="w-1.5 h-1.5 rounded-full bg-stone-300 mt-1.5 flex-shrink-0" />
                  <div>
                    <div className="text-sm font-medium text-stone-700">{title}</div>
                    <div className="text-xs text-stone-400">{desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex gap-4">
            <Link to="/texts" className="inline-flex items-center gap-1.5 text-sm font-medium text-stone-600 hover:text-stone-800 transition-colors">
              Browse texts <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </motion.section>

        <div className="border-t border-stone-200/40 mb-16" />

        {/* ══════════════════════════════════════════════════
            Section 2: Knowledge Graph
        ══════════════════════════════════════════════════ */}
        <motion.section
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mb-8"
        >
          <div className="flex items-center gap-3 mb-5">
            <div className="w-9 h-9 rounded-xl bg-stone-100 border border-stone-200/50 flex items-center justify-center">
              <Network className="w-4.5 h-4.5 text-stone-500" />
            </div>
            <h2 className="text-xl sm:text-2xl font-display font-semibold text-stone-800">Knowledge Graph</h2>
          </div>

          <p className="text-sm sm:text-[15px] text-stone-500 leading-relaxed mb-6 max-w-2xl">
            Structured semantic network documenting philosophical debates, arguments, and conceptual developments across 13 node types.
          </p>

          {/* Inline stats */}
          <div className="flex flex-wrap gap-3 mb-6">
            {[
              { val: fmt(kgStats.nodes), label: 'nodes' },
              { val: fmt(kgStats.edges), label: 'edges' },
              { val: fmt(Object.keys(stats.nodeTypes).length || Number.NaN), label: 'node types' },
            ].map((s) => (
              <div key={s.label} className="inline-flex items-center gap-2 px-3 py-1.5 bg-stone-100/50 border border-stone-200/30 rounded-lg">
                <span className="text-sm"><strong className="text-stone-700 font-semibold">{s.val}</strong> <span className="text-stone-500">{s.label}</span></span>
              </div>
            ))}
          </div>

          {/* Node types — expandable list */}
          <div className="bg-stone-50/50 rounded-xl border border-stone-200/40 p-4 sm:p-5 mb-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium text-stone-400 uppercase tracking-wider">Node Types</span>
              <button
                onClick={() => expandedTypes.size > 0 ? setExpandedTypes(new Set()) : setExpandedTypes(new Set(nodeTypes.map(n => n.key)))}
                className="inline-flex items-center gap-1 text-xs text-stone-400 hover:text-stone-600 transition-colors"
              >
                <ChevronsUpDown className="w-3 h-3" />
                {expandedTypes.size > 0 ? 'Collapse' : 'Expand'} all
              </button>
            </div>

            <div className="space-y-0.5">
              {nodeTypes.map((nt) => {
                const isExpanded = expandedTypes.has(nt.key);
                const items = nodeTypeData[nt.key] || [];
                const actualCount = liveCount(nt);
                // Bar width proportional to the largest live node-type count.
                const barWidth = Math.round((actualCount / maxNodeTypeCount) * 100);

                return (
                  <div key={nt.key}>
                    <button
                      onClick={() => toggleType(nt.key)}
                      className="w-full flex items-center gap-3 py-2.5 px-2 group hover:bg-white/60 rounded-lg transition-colors"
                    >
                      {isExpanded
                        ? <ChevronDown className="w-3.5 h-3.5 text-stone-400 flex-shrink-0" />
                        : <ChevronRight className="w-3.5 h-3.5 text-stone-400 flex-shrink-0" />
                      }
                      <div className="flex-1 min-w-0">
                        <div className="flex items-baseline gap-2 mb-1">
                          <span className="text-sm font-medium text-stone-700">{nt.label}</span>
                          <span className="text-[11px] text-stone-400 hidden sm:inline">{nt.desc}</span>
                        </div>
                        {/* Mini bar chart */}
                        <div className="h-1 rounded-full bg-stone-200/60 overflow-hidden">
                          <div
                            className="h-full rounded-full bg-stone-300/60 transition-all duration-500"
                            style={{ width: `${barWidth}%` }}
                          />
                        </div>
                      </div>
                      <span className="text-sm font-semibold text-stone-500 tabular-nums ml-2">{actualCount}</span>
                    </button>

                    <AnimatePresence>
                      {isExpanded && items.length > 0 && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
                          className="overflow-hidden"
                        >
                          <div className="ml-7 border-l border-stone-200/60 mb-2 max-h-72 overflow-y-auto">
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-px">
                              {items.map((item, idx) => (
                                <WorkItemWithLink key={idx} item={item} typeKey={nt.key} />
                              ))}
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="flex gap-4">
            <Link to="/visualizer" className="inline-flex items-center gap-1.5 text-sm font-medium text-stone-600 hover:text-stone-800 transition-colors">
              Explore graph <ArrowRight className="w-3.5 h-3.5" />
            </Link>
            <Link to="/graphrag" className="inline-flex items-center gap-1.5 text-sm font-medium text-stone-500 hover:text-stone-700 transition-colors">
              Query with AI <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </motion.section>

        <div className="border-t border-stone-200/40 mb-16" />

        {/* ══════════════════════════════════════════════════
            Section 3: Modern Scholarship
        ══════════════════════════════════════════════════ */}
        <motion.section
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mb-16"
        >
          <div className="flex items-center gap-3 mb-5">
            <div className="w-9 h-9 rounded-xl bg-stone-100 border border-stone-200/50 flex items-center justify-center">
              <GraduationCap className="w-4.5 h-4.5 text-stone-500" />
            </div>
            <h2 className="text-xl sm:text-2xl font-display font-semibold text-stone-800">Modern Scholarship</h2>
          </div>

          <p className="text-sm sm:text-[15px] text-stone-500 leading-relaxed mb-6 max-w-2xl">
            Comprehensive bibliography of secondary literature supporting knowledge graph annotations with full provenance tracking.
          </p>

          <div className="flex flex-wrap gap-3 mb-5">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-stone-100/50 border border-stone-200/30 rounded-lg">
              <span className="text-sm"><strong className="text-stone-700 font-semibold">1,125+</strong> <span className="text-stone-500">references</span></span>
            </div>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-stone-100/50 border border-stone-200/30 rounded-lg">
              <span className="text-sm"><span className="text-stone-500">Confidence-scored</span> <strong className="text-stone-700 font-semibold">citation coverage</strong></span>
            </div>
          </div>

          <Link to="/bibliography" className="inline-flex items-center gap-1.5 text-sm font-medium text-stone-600 hover:text-stone-800 transition-colors">
            View bibliography <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </motion.section>

        <div className="border-t border-stone-200/40 mb-16" />

        {/* ══════════════════════════════════════════════════
            Section 4: FAIR Principles
        ══════════════════════════════════════════════════ */}
        <motion.section
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mb-16"
        >
          <h2 className="text-sm font-medium text-stone-400 uppercase tracking-wider mb-6">FAIR Compliance</h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {fairPrinciples.map((fp) => {
              const Icon = fp.icon;
              return (
                <div key={fp.letter} className="bg-stone-50/50 rounded-xl border border-stone-200/40 p-5 hover:border-stone-300/50 transition-colors">
                  <div className="flex items-center gap-2.5 mb-3">
                    <div className="w-8 h-8 rounded-lg bg-stone-100 border border-stone-200/40 flex items-center justify-center">
                      <Icon className="w-3.5 h-3.5 text-stone-400" />
                    </div>
                    <h3 className="text-sm font-semibold text-stone-700">{fp.title}</h3>
                  </div>
                  <ul className="space-y-2">
                    {fp.items.map((item, j) => (
                      <li key={j} className="text-[13px] text-stone-500 leading-relaxed flex gap-2.5">
                        <div className="w-1 h-1 rounded-full bg-stone-300 mt-1.5 flex-shrink-0" />
                        {item.includes('10.5281') ? (
                          <span>
                            DOI:{' '}
                            <a
                              href="https://doi.org/10.5281/zenodo.17379489"
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-stone-600 hover:text-stone-800 underline underline-offset-2 decoration-stone-300 hover:decoration-stone-500 transition-colors"
                            >
                              10.5281/zenodo.17379489
                            </a>
                          </span>
                        ) : item}
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </motion.section>

        <div className="border-t border-stone-200/40 mb-16" />

        {/* ══════════════════════════════════════════════════
            Section 5: Technical Stack
        ══════════════════════════════════════════════════ */}
        <motion.section
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="pb-20"
        >
          <h2 className="text-sm font-medium text-stone-400 uppercase tracking-wider mb-5">Technical Stack</h2>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { name: 'PostgreSQL', desc: 'Full-text search, lemmatic matching, JSON support', icon: Database },
              { name: 'GraphRAG SQLStrategy', desc: 'Lemma expansion, tree routing, and passage citations', icon: Network },
              { name: 'Gemini / Kimi', desc: 'Cited synthesis and extended reasoning', icon: Sparkles },
            ].map((tech) => {
              const TIcon = tech.icon;
              return (
                <div key={tech.name} className="bg-stone-50/50 rounded-xl border border-stone-200/40 p-4 hover:border-stone-300/50 transition-colors">
                  <div className="flex items-center gap-2 mb-2">
                    <TIcon className="w-3.5 h-3.5 text-stone-400" />
                    <span className="text-sm font-medium text-stone-700">{tech.name}</span>
                  </div>
                  <p className="text-xs text-stone-400 leading-relaxed">{tech.desc}</p>
                </div>
              );
            })}
          </div>
        </motion.section>
      </div>
    </div>
  );
}


/* ─── Expandable node item with optional link ─── */

function WorkItemWithLink({
  item,
  typeKey,
}: {
  item: { id: string; label: string };
  typeKey: string;
}) {
  const navigate = useNavigate();
  const [textId, setTextId] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    if (typeKey === 'work') {
      setChecking(true);
      apiClient.getWork(item.id)
        .then((work) => { if (work) setTextId(work.work_id); })
        .catch(() => {})
        .finally(() => setChecking(false));
    }
  }, [item.id, typeKey]);

  return (
    <div className="group/item flex items-center gap-2 py-1.5 pl-4 pr-2 hover:bg-white/60 rounded-r-lg transition-colors -ml-px border-l-2 border-transparent hover:border-stone-300">
      <span className="text-[13px] text-stone-600 flex-1 truncate">{item.label}</span>
      {typeKey === 'work' && !checking && textId && (
        <button
          onClick={() => navigate(`/texts/${textId}`)}
          className="flex-shrink-0 opacity-60 md:opacity-0 md:group-hover/item:opacity-100 text-stone-500 hover:text-stone-700 transition-all p-2 md:p-0 -m-2 md:m-0"
          title={`Read ${item.label}`}
          aria-label={`Read ${item.label}`}
        >
          <ExternalLink className="w-4 h-4 md:w-3 md:h-3" />
        </button>
      )}
    </div>
  );
}
