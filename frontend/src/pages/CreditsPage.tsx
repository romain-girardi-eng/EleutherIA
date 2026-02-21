import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { Typewriter } from '../components/ui/typewriter';
import { BookOpen, Code, Database, Award } from 'lucide-react';

export default function CreditsPage() {
  const { t } = useTranslation();

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
              text={["Credits & Attributions", "Acknowledgments", "Data Sources"]}
              speed={100}
              waitTime={3000}
              deleteSpeed={60}
              className="text-stone-800"
              cursorChar="_"
            />
          </h1>
          <p className="text-lg text-stone-600 max-w-2xl mx-auto">
            {t('credits.intro')}
          </p>
        </motion.div>

        {/* Primary Data Sources */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-parchment-100/70 rounded-2xl p-8 shadow-sm"
        >
          <div className="flex items-center gap-3 mb-6">
            <BookOpen className="w-8 h-8 text-orange-600" />
            <h2 className="text-3xl font-display font-bold text-stone-800">{t('credits.dataSources')}</h2>
          </div>

          <div className="space-y-6">
            {/* Perseus Digital Library */}
            <div className="bg-gradient-to-br from-parchment-50 to-amber-50 rounded-xl p-6 border border-amber-200/60">
              <h3 className="text-xl font-display font-bold text-stone-800 mb-3">{t('credits.perseus')}</h3>
              <p className="text-sm text-stone-600 mb-4">
                {t('credits.perseusDesc')}
              </p>
              <div className="space-y-2 text-sm">
                <div className="flex items-start gap-2">
                  <span className="text-orange-600 font-bold">•</span>
                  <div>
                    <strong>canonical-greekLit:</strong>{' '}
                    <a href="https://github.com/PerseusDL/canonical-greekLit" target="_blank" rel="noopener noreferrer" className="text-orange-600 hover:underline">
                      github.com/PerseusDL/canonical-greekLit
                    </a>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-orange-600 font-bold">•</span>
                  <div>
                    <strong>canonical-latinLit:</strong>{' '}
                    <a href="https://github.com/PerseusDL/canonical-latinLit" target="_blank" rel="noopener noreferrer" className="text-orange-600 hover:underline">
                      github.com/PerseusDL/canonical-latinLit
                    </a>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-orange-600 font-bold">•</span>
                  <span><strong>License:</strong> CC BY-SA 3.0</span>
                </div>
              </div>
            </div>

            {/* Scaife Viewer */}
            <div className="bg-gradient-to-br from-amber-50 to-parchment-50 rounded-xl p-6 border border-amber-200/60">
              <h3 className="text-xl font-display font-bold text-stone-800 mb-3">{t('credits.scaife')}</h3>
              <p className="text-sm text-stone-600 mb-4">
                {t('credits.scaifeDesc')}
              </p>
              <div className="space-y-2 text-sm">
                <div className="flex items-start gap-2">
                  <span className="text-orange-600 font-bold">•</span>
                  <div>
                    <strong>Website:</strong>{' '}
                    <a href="https://scaife.perseus.org" target="_blank" rel="noopener noreferrer" className="text-orange-600 hover:underline">
                      scaife.perseus.org
                    </a>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-orange-600 font-bold">•</span>
                  <span><strong>Provider:</strong> Perseus Digital Library / Scaife Collaborative</span>
                </div>
              </div>
            </div>

            {/* Open Greek and Latin */}
            <div className="bg-gradient-to-br from-parchment-50 to-amber-50 rounded-xl p-6 border border-amber-200/60">
              <h3 className="text-xl font-display font-bold text-stone-800 mb-3">Open Greek and Latin Project - CSEL Corpus</h3>
              <p className="text-sm text-stone-600 mb-4">
                TEI-XML encoded Latin patristic texts from the Corpus Scriptorum Ecclesiasticorum Latinorum (CSEL)
              </p>
              <div className="space-y-2 text-sm">
                <div className="flex items-start gap-2">
                  <span className="text-orange-600 font-bold">•</span>
                  <div>
                    <strong>Repository:</strong>{' '}
                    <a href="https://github.com/OpenGreekAndLatin/csel-dev" target="_blank" rel="noopener noreferrer" className="text-orange-600 hover:underline">
                      github.com/OpenGreekAndLatin/csel-dev
                    </a>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-orange-600 font-bold">•</span>
                  <span><strong>License:</strong> CC0 1.0 Universal (Public Domain)</span>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Technical Infrastructure */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-parchment-100/70 rounded-2xl p-8 shadow-sm"
        >
          <div className="flex items-center gap-3 mb-6">
            <Code className="w-8 h-8 text-orange-600" />
            <h2 className="text-3xl font-display font-bold text-stone-800">{t('credits.techInfra')}</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Visualization */}
            <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl p-6 border border-orange-200/60">
              <h3 className="text-lg font-display font-bold text-stone-800 mb-3">{t('credits.vizTools')}</h3>
              <ul className="space-y-2 text-sm text-stone-600">
                <li className="flex items-start gap-2">
                  <span className="text-orange-600">•</span>
                  <span><strong>Cytoscape.js</strong> - Knowledge graph visualization (MIT)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-orange-600">•</span>
                  <span><strong>D3.js</strong> - Data visualization (ISC)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-orange-600">•</span>
                  <span><strong>Recharts</strong> - React charts (MIT)</span>
                </li>
              </ul>
            </div>

            {/* Frontend */}
            <div className="bg-gradient-to-br from-orange-50 to-parchment-50 rounded-xl p-6 border border-amber-200/60">
              <h3 className="text-lg font-display font-bold text-stone-800 mb-3">{t('credits.frontendFramework')}</h3>
              <ul className="space-y-2 text-sm text-stone-600">
                <li className="flex items-start gap-2">
                  <span className="text-orange-600">•</span>
                  <span><strong>React 19</strong> - UI framework (MIT)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-orange-600">•</span>
                  <span><strong>TypeScript</strong> - Type-safe JavaScript (Apache 2.0)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-orange-600">•</span>
                  <span><strong>TailwindCSS</strong> - CSS framework (MIT)</span>
                </li>
              </ul>
            </div>

            {/* Backend */}
            <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl p-6 border border-orange-200/60">
              <h3 className="text-lg font-display font-bold text-stone-800 mb-3">{t('credits.backendServices')}</h3>
              <ul className="space-y-2 text-sm text-stone-600">
                <li className="flex items-start gap-2">
                  <span className="text-orange-600">•</span>
                  <span><strong>FastAPI</strong> - Python web framework (MIT)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-orange-600">•</span>
                  <span><strong>PostgreSQL</strong> - Relational database</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-orange-600">•</span>
                  <span><strong>Qdrant</strong> - Vector database (Apache 2.0)</span>
                </li>
              </ul>
            </div>

            {/* UI Components */}
            <div className="bg-gradient-to-br from-orange-50 to-parchment-50 rounded-xl p-6 border border-amber-200/60">
              <h3 className="text-lg font-display font-bold text-stone-800 mb-3">UI Components</h3>
              <ul className="space-y-2 text-sm text-stone-600">
                <li className="flex items-start gap-2">
                  <span className="text-orange-600">•</span>
                  <span><strong>Radix UI</strong> - Accessible components (MIT)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-orange-600">•</span>
                  <span><strong>Lucide React</strong> - Icon library (ISC)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-orange-600">•</span>
                  <span><strong>Framer Motion</strong> - Animation library (MIT)</span>
                </li>
              </ul>
            </div>
          </div>
        </motion.div>

        {/* Standards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-parchment-100/70 rounded-2xl p-8 shadow-sm"
        >
          <div className="flex items-center gap-3 mb-6">
            <Database className="w-8 h-8 text-orange-600" />
            <h2 className="text-3xl font-display font-bold text-stone-800">{t('credits.standards')}</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-gradient-to-br from-parchment-50 to-amber-50 rounded-xl p-6 border border-amber-200/60">
              <h3 className="text-lg font-display font-bold text-stone-800 mb-2">Canonical Text Services (CTS)</h3>
              <p className="text-sm text-stone-600 mb-3">
                Standard for citing and retrieving ancient texts using URN-based identifiers
              </p>
              <a href="http://cite-architecture.github.io/cts/" target="_blank" rel="noopener noreferrer" className="text-orange-600 hover:underline text-sm">
                cite-architecture.github.io/cts/
              </a>
            </div>

            <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl p-6 border border-orange-200/60">
              <h3 className="text-lg font-display font-bold text-stone-800 mb-2">FAIR Data Principles</h3>
              <p className="text-sm text-stone-600 mb-3">
                Findable, Accessible, Interoperable, Reusable
              </p>
              <a href="https://www.go-fair.org/fair-principles/" target="_blank" rel="noopener noreferrer" className="text-orange-600 hover:underline text-sm">
                go-fair.org/fair-principles/
              </a>
            </div>

            <div className="bg-gradient-to-br from-orange-50 to-parchment-50 rounded-xl p-6 border border-amber-200/60">
              <h3 className="text-lg font-display font-bold text-stone-800 mb-2">JSON Schema</h3>
              <p className="text-sm text-stone-600 mb-3">
                Database structure validated against JSON Schema Draft 07
              </p>
              <a href="https://json-schema.org/" target="_blank" rel="noopener noreferrer" className="text-orange-600 hover:underline text-sm">
                json-schema.org
              </a>
            </div>

            <div className="bg-gradient-to-br from-parchment-50 to-amber-50 rounded-xl p-6 border border-amber-200/60">
              <h3 className="text-lg font-display font-bold text-stone-800 mb-2">TEI (Text Encoding Initiative)</h3>
              <p className="text-sm text-stone-600 mb-3">
                Standard markup language for digital texts
              </p>
              <a href="https://tei-c.org/" target="_blank" rel="noopener noreferrer" className="text-orange-600 hover:underline text-sm">
                tei-c.org
              </a>
            </div>
          </div>
        </motion.div>

        {/* License */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-parchment-100/70 rounded-2xl p-8 shadow-sm"
        >
          <div className="flex items-center gap-3 mb-6">
            <Award className="w-8 h-8 text-orange-600" />
            <h2 className="text-3xl font-display font-bold text-stone-800">{t('credits.projectLicense')}</h2>
          </div>

          <div className="bg-gradient-to-br from-parchment-50 to-amber-50 p-8 rounded-xl border border-amber-200/60">
            <div className="flex items-start gap-4 mb-6">
              <img
                src="https://mirrors.creativecommons.org/presskit/buttons/88x31/svg/by.svg"
                alt="CC BY 4.0"
                className="w-24 h-auto"
              />
              <div>
                <h3 className="font-display font-bold text-2xl text-stone-800 mb-2">{t('credits.ccBy4')}</h3>
                <p className="text-sm text-stone-600">
                  {t('credits.ccByDesc')}
                </p>
              </div>
            </div>

            <div className="space-y-4 text-sm text-stone-700">
              <div>
                <strong className="text-stone-800">You are free to:</strong>
                <ul className="list-disc list-inside space-y-1 ml-4 mt-2">
                  <li><strong>Share</strong> — Copy and redistribute in any medium</li>
                  <li><strong>Adapt</strong> — Remix, transform, and build upon the material</li>
                </ul>
              </div>

              <div>
                <strong className="text-stone-800">Under these terms:</strong>
                <ul className="list-disc list-inside space-y-1 ml-4 mt-2">
                  <li><strong>Attribution</strong> — You must give appropriate credit</li>
                </ul>
              </div>

              <div className="mt-6 pt-4 border-t border-amber-200/60">
                <strong className="text-stone-800">Suggested Citation:</strong>
                <div className="mt-2 bg-parchment-50 p-4 rounded-lg border border-stone-200 font-mono text-xs">
                  {t('credits.citationText')}
                </div>
              </div>

              <p className="text-stone-500 pt-2">
                Full license:{' '}
                <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener noreferrer" className="text-orange-600 hover:underline">
                  creativecommons.org/licenses/by/4.0/
                </a>
              </p>
            </div>
          </div>
        </motion.div>

        {/* Acknowledgments */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-parchment-100/70 rounded-2xl p-8 shadow-sm"
        >
          <h2 className="text-3xl font-display font-bold text-stone-800 mb-6">{t('credits.acknowledgments')}</h2>

          <div className="space-y-4 text-stone-600 leading-relaxed">
            <p>{t('credits.thanksIntro')}</p>

            <ul className="space-y-3">
              <li className="flex items-start gap-3">
                <span className="text-orange-600 font-bold text-xl">•</span>
                <span><strong>Perseus Digital Library</strong> at Tufts University for decades of work digitizing ancient texts</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-orange-600 font-bold text-xl">•</span>
                <span><strong>Open Greek and Latin Project</strong> at Leipzig University for high-quality TEI-XML editions</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-orange-600 font-bold text-xl">•</span>
                <span><strong>Text Encoding Initiative (TEI)</strong> for establishing interoperability standards</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-orange-600 font-bold text-xl">•</span>
                <span><strong>Scaife Viewer</strong> for implementing CTS protocol and modern infrastructure</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-orange-600 font-bold text-xl">•</span>
                <span>The maintainers of all open-source libraries and frameworks listed above</span>
              </li>
            </ul>

            <p className="mt-6 text-stone-500 italic bg-amber-50 p-4 rounded-xl border border-amber-200/60">
              Special thanks to the supervisors of this doctoral research: Prof. Arnaud Zucker (Université Côte d'Azur, CEPAM)
              and Prof. Andreas Dettwiler (Université de Genève, Faculté autonome de théologie protestante).
            </p>
          </div>
        </motion.div>

        {/* Contact */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-2xl p-6 border border-amber-200/60 shadow-sm"
        >
          <h2 className="text-2xl font-display font-bold text-stone-800 mb-4">Report Issues or Suggest Corrections</h2>
          <p className="text-sm text-stone-600 leading-relaxed mb-4">
            If you notice any errors in attribution, licensing information, or missing acknowledgments,
            please contact us or open an issue on GitHub.
          </p>
          <div className="flex flex-wrap gap-4">
            <a
              href="mailto:romain.girardi@univ-cotedazur.fr"
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-br from-stone-800 to-stone-700 text-white rounded-full hover:shadow-lg transition-all"
            >
              Contact via Email
            </a>
            <a
              href="https://github.com/romain-girardi-eng/EleutherIA/issues"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-6 py-3 bg-parchment-50 text-stone-700 rounded-full border border-stone-200 hover:shadow-md transition-all"
            >
              Open GitHub Issue
            </a>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
