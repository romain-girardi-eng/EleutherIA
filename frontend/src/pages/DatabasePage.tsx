import { BookOpen, Network, GraduationCap, ChevronDown, ChevronRight, ExternalLink } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../api/client';
import { motion } from 'framer-motion';
import { Typewriter } from '../components/ui/typewriter';

export default function DatabasePage() {
  const { t } = useTranslation();
  const [nodeTypeData, setNodeTypeData] = useState<Record<string, Array<{ id: string; label: string }>>>({});
  const [expandedTypes, setExpandedTypes] = useState<Set<string>>(new Set());

  // Dynamic KG stats state
  const [kgStats, setKgStats] = useState({
    nodes: 0,
    edges: 0,
    sources: 0
  });

  // Fetch KG stats on mount
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const kgStatsResponse = await apiClient.getKGStats();
        const worksStatsResponse = await apiClient.getWorksStats();

        setKgStats({
          nodes: kgStatsResponse.totalNodes || 0,
          edges: kgStatsResponse.totalEdges || 0,
          sources: worksStatsResponse.total_passages || 0
        });
      } catch (err) {
        console.error('Failed to fetch KG stats:', err);
      }
    };
    fetchStats();
  }, []);

  useEffect(() => {
    apiClient.getNodes()
      .then((data) => {
        const nodes = Array.isArray(data) ? data : (data?.nodes || []);
        const typeData: Record<string, Array<{ id: string; label: string }>> = {};
        nodes.forEach((node: { id: string; type?: string; label?: string }) => {
          const type = node.type || 'unknown';
          if (!typeData[type]) {
            typeData[type] = [];
          }
          typeData[type].push({
            id: node.id,
            label: node.label || 'Unnamed'
          });
        });

        Object.keys(typeData).forEach(type => {
          typeData[type].sort((a, b) => a.label.toLowerCase().localeCompare(b.label.toLowerCase()));
        });

        setNodeTypeData(typeData);
      })
      .catch(error => {
        console.error('Error loading node type data:', error);
      });
  }, []);

  const toggleType = (type: string) => {
    const newExpanded = new Set(expandedTypes);
    if (newExpanded.has(type)) {
      newExpanded.delete(type);
    } else {
      newExpanded.add(type);
    }
    setExpandedTypes(newExpanded);
  };

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
              text={["Database Overview", "Knowledge Architecture", "Data Structure"]}
              speed={100}
              waitTime={3000}
              deleteSpeed={60}
              className="text-stone-800"
              cursorChar="_"
            />
          </h1>
          <p className="text-lg text-stone-600 max-w-2xl mx-auto">
            {t('database.subtitle')}
          </p>
        </motion.div>

        {/* Stats Pills */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="flex flex-wrap justify-center gap-3"
        >
          <span className="px-4 py-2 bg-parchment-100/70 backdrop-blur-sm rounded-full text-sm font-medium text-stone-600 shadow-sm border border-amber-200/60">
            {kgStats.nodes.toLocaleString()} Knowledge Graph Nodes
          </span>
          <span className="px-4 py-2 bg-parchment-100/70 backdrop-blur-sm rounded-full text-sm font-medium text-stone-600 shadow-sm border border-amber-200/60">
            {kgStats.edges.toLocaleString()} Relationships
          </span>
          <span className="px-4 py-2 bg-parchment-100/70 backdrop-blur-sm rounded-full text-sm font-medium text-stone-600 shadow-sm border border-amber-200/60">
            376 Ancient Texts
          </span>
          <span className="px-4 py-2 bg-amber-50 backdrop-blur-sm rounded-full text-sm font-medium text-orange-700 shadow-sm border border-amber-200/60">
            FAIR Compliant
          </span>
        </motion.div>

        {/* Ancient Texts Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-parchment-100/70 backdrop-blur-sm rounded-2xl p-8 shadow-sm"
        >
          <div className="flex items-start gap-4 mb-6">
            <BookOpen className="w-8 h-8 text-orange-600 flex-shrink-0" />
            <div>
              <h2 className="text-3xl font-display font-bold text-stone-800 mb-2">{t('nav.texts')}</h2>
              <p className="text-stone-600 leading-relaxed">
                Complete collection of Greek and Latin philosophical texts from the 4th century BCE to the 6th century CE
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-gradient-to-br from-parchment-50 to-amber-50 p-6 rounded-xl text-center border border-amber-200/60">
              <div className="text-4xl font-bold text-orange-600 mb-2">376</div>
              <div className="text-sm font-medium text-stone-600">Ancient Texts</div>
            </div>
            <div className="bg-gradient-to-br from-amber-50 to-orange-50 p-6 rounded-xl text-center border border-orange-200/60">
              <div className="text-4xl font-bold text-orange-600 mb-2">109</div>
              <div className="text-sm font-medium text-stone-600">Lemmatized Texts</div>
            </div>
            <div className="bg-gradient-to-br from-orange-50 to-parchment-50 p-6 rounded-xl text-center border border-amber-200/60">
              <div className="text-4xl font-bold text-orange-600 mb-2">2</div>
              <div className="text-sm font-medium text-stone-600">Languages (Greek & Latin)</div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-parchment-50 to-amber-50 rounded-xl p-6 border border-amber-200/60">
            <h3 className="font-display font-bold text-lg text-stone-800 mb-4">Features & Capabilities</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex gap-3">
                <div className="flex-shrink-0 w-2 h-2 rounded-full bg-orange-600 mt-2"></div>
                <div>
                  <div className="font-semibold text-stone-800 mb-1">Full-Text Search</div>
                  <div className="text-sm text-stone-600">PostgreSQL full-text search across all 376 texts</div>
                </div>
              </div>
              <div className="flex gap-3">
                <div className="flex-shrink-0 w-2 h-2 rounded-full bg-orange-600 mt-2"></div>
                <div>
                  <div className="font-semibold text-stone-800 mb-1">Lemmatic Search</div>
                  <div className="text-sm text-stone-600">Morphological analysis on 109 texts</div>
                </div>
              </div>
              <div className="flex gap-3">
                <div className="flex-shrink-0 w-2 h-2 rounded-full bg-orange-600 mt-2"></div>
                <div>
                  <div className="font-semibold text-stone-800 mb-1">Complete Texts</div>
                  <div className="text-sm text-stone-600">Full texts with proper encoding</div>
                </div>
              </div>
              <div className="flex gap-3">
                <div className="flex-shrink-0 w-2 h-2 rounded-full bg-orange-600 mt-2"></div>
                <div>
                  <div className="font-semibold text-stone-800 mb-1">Structured Metadata</div>
                  <div className="text-sm text-stone-600">Author, title, date, language, citations</div>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 p-4 bg-amber-50 border border-amber-200/60 rounded-xl">
            <p className="text-sm text-stone-800">
              <span className="font-semibold">Access:</span> All ancient texts are available through the{' '}
              <a href="/texts" className="text-orange-600 hover:underline font-medium">Ancient Texts</a> browser
              and searchable via the{' '}
              <a href="/search" className="text-orange-600 hover:underline font-medium">Hybrid Search</a> interface.
            </p>
          </div>
        </motion.div>

        {/* Knowledge Graph Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-parchment-100/70 backdrop-blur-sm rounded-2xl p-8 shadow-sm"
        >
          <div className="flex items-start gap-4 mb-6">
            <Network className="w-8 h-8 text-orange-600 flex-shrink-0" />
            <div>
              <h2 className="text-3xl font-display font-bold text-stone-800 mb-2">{t('nav.visualizer')}</h2>
              <p className="text-stone-600 leading-relaxed">
                Structured semantic network documenting philosophical debates, arguments, and conceptual developments
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-gradient-to-br from-parchment-50 to-amber-50 p-6 rounded-xl text-center border border-amber-200/60">
              <div className="text-4xl font-bold text-orange-600 mb-2">{kgStats.nodes.toLocaleString()}</div>
              <div className="text-sm font-medium text-stone-600">{t('kg.nodes')}</div>
            </div>
            <div className="bg-gradient-to-br from-amber-50 to-orange-50 p-6 rounded-xl text-center border border-orange-200/60">
              <div className="text-4xl font-bold text-orange-600 mb-2">{kgStats.edges.toLocaleString()}</div>
              <div className="text-sm font-medium text-stone-600">{t('kg.edges')}</div>
            </div>
            <div className="bg-gradient-to-br from-orange-50 to-parchment-50 p-6 rounded-xl text-center border border-amber-200/60">
              <div className="text-4xl font-bold text-orange-600 mb-2">13</div>
              <div className="text-sm font-medium text-stone-600">Node Types</div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-parchment-50 to-amber-50 rounded-xl p-6 border border-amber-200/60">
            <h3 className="font-display font-bold text-lg text-stone-800 mb-4">Node Types Distribution</h3>
            <p className="text-sm text-stone-500 mb-4">Click on any node type to view all items in alphabetical order</p>
            <div className="space-y-2">
              <NodeTypeItem type="Persons" typeKey="person" count={161} description="Philosophers, theologians, authors" items={nodeTypeData['person'] || []} expanded={expandedTypes.has('person')} onToggle={() => toggleType('person')} />
              <NodeTypeItem type="Arguments" typeKey="argument" count={117} description="Specific philosophical arguments" items={nodeTypeData['argument'] || []} expanded={expandedTypes.has('argument')} onToggle={() => toggleType('argument')} />
              <NodeTypeItem type="Concepts" typeKey="concept" count={105} description="Key philosophical terms" items={nodeTypeData['concept'] || []} expanded={expandedTypes.has('concept')} onToggle={() => toggleType('concept')} />
              <NodeTypeItem type="Works" typeKey="work" count={57} description="Treatises, dialogues, letters" items={nodeTypeData['work'] || []} expanded={expandedTypes.has('work')} onToggle={() => toggleType('work')} />
              <NodeTypeItem type="Reformulations" typeKey="reformulation" count={53} description="Conceptual redefinitions" items={nodeTypeData['reformulation'] || []} expanded={expandedTypes.has('reformulation')} onToggle={() => toggleType('reformulation')} />
            </div>
          </div>

          <div className="mt-6 p-4 bg-amber-50 border border-amber-200/60 rounded-xl">
            <p className="text-sm text-stone-800">
              <span className="font-semibold">Visualization:</span> Explore the knowledge graph interactively through the{' '}
              <a href="/visualizer" className="text-orange-600 hover:underline font-medium">{t('nav.visualizer')}</a>
              {' '}or query it semantically via{' '}
              <a href="/graphrag" className="text-orange-600 hover:underline font-medium">{t('nav.graphrag')}</a>.
            </p>
          </div>
        </motion.div>

        {/* Modern Scholarship */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-parchment-100/70 backdrop-blur-sm rounded-2xl p-8 shadow-sm"
        >
          <div className="flex items-start gap-4 mb-6">
            <GraduationCap className="w-8 h-8 text-orange-600 flex-shrink-0" />
            <div>
              <h2 className="text-3xl font-display font-bold text-stone-800 mb-2">{t('nav.bibliography')}</h2>
              <p className="text-stone-600 leading-relaxed">
                Comprehensive bibliography of secondary literature supporting knowledge graph annotations
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div className="bg-gradient-to-br from-amber-50 to-orange-50 p-6 rounded-xl text-center border border-amber-200/60">
              <div className="text-4xl font-bold text-orange-600 mb-2">1125+</div>
              <div className="text-sm font-medium text-stone-600">Bibliography References</div>
            </div>
            <div className="bg-gradient-to-br from-orange-50 to-parchment-50 p-6 rounded-xl text-center border border-amber-200/60">
              <div className="text-4xl font-bold text-orange-600 mb-2">91.8%</div>
              <div className="text-sm font-medium text-stone-600">Citation Coverage</div>
            </div>
          </div>

          <div className="mt-6 p-4 bg-amber-50 border border-amber-200/60 rounded-xl">
            <p className="text-sm text-stone-800">
              <span className="font-semibold">Access:</span> View the complete bibliography at{' '}
              <a href="/bibliography" className="text-orange-600 hover:underline font-medium">{t('nav.bibliography')}</a> page.
            </p>
          </div>
        </motion.div>

        {/* FAIR Principles */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-parchment-100/70 backdrop-blur-sm rounded-2xl p-8 shadow-sm"
        >
          <h2 className="text-3xl font-display font-bold text-stone-800 mb-6">{t('database.schema')}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-gradient-to-br from-parchment-50 to-amber-50 p-6 rounded-xl border border-amber-200/60">
              <h3 className="font-display font-bold text-lg text-orange-800 mb-3">Findable</h3>
              <ul className="space-y-2 text-sm text-stone-600">
                <li className="flex items-start gap-2">
                  <span className="text-orange-600">•</span>
                  <span>Unique persistent identifiers for all nodes</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-orange-600">•</span>
                  <span>Rich metadata with controlled vocabularies</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-orange-600">•</span>
                  <span>DOI: <a href="https://doi.org/10.5281/zenodo.17379490" className="text-orange-600 hover:underline">10.5281/zenodo.17379490</a></span>
                </li>
              </ul>
            </div>
            <div className="bg-gradient-to-br from-amber-50 to-orange-50 p-6 rounded-xl border border-orange-200/60">
              <h3 className="font-display font-bold text-lg text-orange-800 mb-3">Accessible</h3>
              <ul className="space-y-2 text-sm text-stone-600">
                <li className="flex items-start gap-2">
                  <span className="text-orange-600">•</span>
                  <span>Open JSON format (13 MB)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-orange-600">•</span>
                  <span>RESTful API with full documentation</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-orange-600">•</span>
                  <span>CC BY 4.0 license</span>
                </li>
              </ul>
            </div>
            <div className="bg-gradient-to-br from-orange-50 to-parchment-50 p-6 rounded-xl border border-amber-200/60">
              <h3 className="font-display font-bold text-lg text-orange-800 mb-3">Interoperable</h3>
              <ul className="space-y-2 text-sm text-stone-600">
                <li className="flex items-start gap-2">
                  <span className="text-orange-600">•</span>
                  <span>JSON Schema validation (Draft 07)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-orange-600">•</span>
                  <span>Standard philosophical taxonomies</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-orange-600">•</span>
                  <span>Compatible with Cytoscape, Gephi, Neo4j</span>
                </li>
              </ul>
            </div>
            <div className="bg-gradient-to-br from-parchment-50 to-amber-50 p-6 rounded-xl border border-amber-200/60">
              <h3 className="font-display font-bold text-lg text-orange-800 mb-3">Reusable</h3>
              <ul className="space-y-2 text-sm text-stone-600">
                <li className="flex items-start gap-2">
                  <span className="text-orange-600">•</span>
                  <span>Complete provenance documentation</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-orange-600">•</span>
                  <span>Semantic versioning (v1.0.0)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-orange-600">•</span>
                  <span>Extensive examples and documentation</span>
                </li>
              </ul>
            </div>
          </div>
        </motion.div>

        {/* Technical Infrastructure */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="bg-parchment-100/70 backdrop-blur-sm rounded-2xl p-8 shadow-sm"
        >
          <h2 className="text-3xl font-display font-bold text-stone-800 mb-6">Technical Infrastructure</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gradient-to-br from-parchment-50 to-amber-50 p-6 rounded-xl border border-amber-200/60">
              <h3 className="font-display font-bold text-orange-800 mb-2">PostgreSQL</h3>
              <p className="text-sm text-stone-600">Relational database with full-text search, lemmatic matching, and JSON support</p>
            </div>
            <div className="bg-gradient-to-br from-amber-50 to-orange-50 p-6 rounded-xl border border-orange-200/60">
              <h3 className="font-display font-bold text-orange-800 mb-2">Qdrant Cloud</h3>
              <p className="text-sm text-stone-600">Vector database storing 3072-dimensional embeddings for semantic search</p>
            </div>
            <div className="bg-gradient-to-br from-orange-50 to-parchment-50 p-6 rounded-xl border border-amber-200/60">
              <h3 className="font-display font-bold text-orange-800 mb-2">Gemini API</h3>
              <p className="text-sm text-stone-600">Text embedding (text-embedding-004) and LLM synthesis (Gemini 2.0 Flash)</p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

function NodeTypeItem({
  type,
  typeKey,
  count,
  description,
  items,
  expanded,
  onToggle,
}: {
  type: string;
  typeKey: string;
  count: number;
  description: string;
  items: Array<{ id: string; label: string }>;
  expanded: boolean;
  onToggle: () => void;
}) {
  const navigate = useNavigate();

  return (
    <div className="border border-amber-200/60 rounded-xl overflow-hidden bg-parchment-50">
      <button
        onClick={onToggle}
        className="w-full flex justify-between items-start p-4 hover:bg-parchment-100/70 transition-colors cursor-pointer text-left"
      >
        <div className="flex items-start gap-2 flex-1">
          {expanded ? (
            <ChevronDown className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
          ) : (
            <ChevronRight className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
          )}
          <div>
            <div className="font-semibold text-stone-800">{type}</div>
            <div className="text-xs text-stone-500 mt-0.5">{description}</div>
          </div>
        </div>
        <div className="text-lg font-bold text-orange-600 ml-4">{count}</div>
      </button>

      {expanded && items.length > 0 && (
        <div className="border-t border-amber-200/60 bg-parchment-50 p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 max-h-96 overflow-y-auto">
            {items.map((item, index) => (
              <WorkItemWithLink
                key={`${typeKey}-${index}`}
                item={item}
                typeKey={typeKey}
                navigate={navigate}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function WorkItemWithLink({
  item,
  typeKey,
  navigate,
}: {
  item: { id: string; label: string };
  typeKey: string;
  navigate: (path: string) => void;
}) {
  const [textId, setTextId] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    if (typeKey === 'work') {
      setChecking(true);
      apiClient.getWork(item.id)
        .then((work) => {
          if (work) {
            setTextId(work.work_id);
          }
        })
        .catch((error) => {
          console.error('Error checking for linked work:', error);
        })
        .finally(() => {
          setChecking(false);
        });
    }
  }, [item.id, typeKey]);

  return (
    <div className="text-sm text-stone-800 p-2 bg-parchment-50 rounded border border-amber-200/60 hover:border-orange-300 transition-colors">
      <div className="flex items-start justify-between gap-2">
        <span className="flex-1">{item.label}</span>
        {typeKey === 'work' && (
          <>
            {checking ? (
              <span className="text-xs text-stone-400 flex-shrink-0">...</span>
            ) : textId ? (
              <button
                onClick={() => navigate(`/texts/${textId}`)}
                className="flex-shrink-0 text-orange-600 hover:text-orange-700 transition-colors"
                title={`Read ${item.label} in text viewer`}
              >
                <ExternalLink className="w-4 h-4" />
              </button>
            ) : null}
          </>
        )}
      </div>
    </div>
  );
}
