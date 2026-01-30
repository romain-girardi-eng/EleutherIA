import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import DatabaseWithRestApi from '../components/ui/database-with-rest-api';
import HiRAGImplementationDetails from '../components/HiRAGImplementationDetails';
import { AuroraBackground } from '../components/ui/aurora-background';
import { motion } from 'framer-motion';
import { Typewriter } from '../components/ui/typewriter';

export default function AboutPage() {
  const { t } = useTranslation();

  return (
    <AuroraBackground className="!min-h-screen !h-auto !w-full pt-20 pb-12">
      <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">

        {/* Modern Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-4">
            About{" "}
            <Typewriter
              text={["EleutherIA", "the Project", "the Database"]}
              speed={100}
              waitTime={3000}
              deleteSpeed={60}
              className="text-gray-900"
              cursorChar="_"
            />
          </h1>
          <p className="text-lg text-gray-700 max-w-2xl mx-auto">
            A FAIR-compliant knowledge graph documenting ancient debates on free will
          </p>
        </motion.div>

        {/* About the Project */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white/95 backdrop-blur-sm rounded-2xl p-8 shadow-sm"
        >
          <h2 className="text-3xl font-bold text-gray-900 mb-6">{t('about.projectTitle')}</h2>

          <div className="space-y-4 text-gray-700 leading-relaxed">
            <p>
              <strong className="text-gray-900">EleutherIA</strong> {t('about.projectIntro')}
            </p>

            <p>{t('about.projectContext')}</p>
            <p>{t('about.projectDetails')}</p>
            <p>{t('about.projectGoal')}</p>

            <p className="text-sm text-gray-600 italic">
              {t('about.projectNote')}
            </p>
          </div>
        </motion.div>

        {/* About the Author */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white/95 backdrop-blur-sm rounded-2xl p-8 shadow-sm"
        >
          <h2 className="text-3xl font-bold text-gray-900 mb-6">{t('about.authorTitle')}</h2>

          <div className="space-y-6 text-gray-700 leading-relaxed">
            <div className="flex flex-col md:flex-row items-start gap-6">
              <div className="flex-shrink-0">
                <img
                  src="/romain-girardi.jpg"
                  alt={t('about.authorName')}
                  className="w-40 h-40 rounded-full object-cover shadow-lg border-4 border-white"
                  style={{ objectPosition: 'center 30%' }}
                />
              </div>
              <div className="flex-grow">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{t('about.authorName')}</h3>
                <p className="text-gray-600 mb-4">{t('about.authorTitle2')}</p>
                <p>{t('about.authorBio')}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200">
                <h4 className="font-bold text-lg text-gray-900 mb-3">{t('about.researchInterests')}</h4>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 font-bold">•</span>
                    <span>{t('about.interest1')}</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 font-bold">•</span>
                    <span>{t('about.interest2')}</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 font-bold">•</span>
                    <span>{t('about.interest3')}</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 font-bold">•</span>
                    <span>{t('about.interest4')}</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 font-bold">•</span>
                    <span>{t('about.interest5')}</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 font-bold">•</span>
                    <span>{t('about.interest6')}</span>
                  </li>
                </ul>
              </div>

              <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-6 rounded-xl border border-purple-200">
                <h4 className="font-bold text-lg text-gray-900 mb-3">{t('about.academicBackground')}</h4>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-start gap-2">
                    <span className="text-purple-600 font-bold">•</span>
                    <span>{t('about.degree1')}</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-purple-600 font-bold">•</span>
                    <span>{t('about.degree2')}</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-purple-600 font-bold">•</span>
                    <span>{t('about.degree3')}</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-purple-600 font-bold">•</span>
                    <span>{t('about.degree4')}</span>
                  </li>
                </ul>
              </div>
            </div>

            <div className="bg-white/60 backdrop-blur-md p-6 rounded-xl border border-gray-200">
              <h4 className="font-bold text-lg text-gray-900 mb-3">Institutional Affiliations</h4>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <span className="text-gray-600 font-bold">•</span>
                  <span><strong>Université Côte d'Azur</strong> — CEPAM (Cultures et Environnements. Préhistoire, Antiquité, Moyen Âge), UMR 7264, CNRS</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-gray-600 font-bold">•</span>
                  <span><strong>Université de Genève</strong> — Faculté autonome de théologie protestante</span>
                </li>
              </ul>
            </div>

            <div className="flex flex-wrap gap-4">
              <a
                href="https://orcid.org/0000-0002-5310-5346"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 bg-white/80 backdrop-blur-sm text-blue-600 rounded-full border border-blue-200 hover:shadow-md transition-all text-sm"
              >
                <svg className="w-4 h-4" viewBox="0 0 256 256" fill="currentColor">
                  <path d="M256,128c0,70.7-57.3,128-128,128C57.3,256,0,198.7,0,128C0,57.3,57.3,0,128,0C198.7,0,256,57.3,256,128z M86.3,186.2H70.9V79.1h15.4v48.4V186.2z M108.9,79.1h41.6c39.6,0,57,28.3,57,53.6c0,27.5-21.5,53.6-56.8,53.6h-41.8V79.1z M124.3,172.4h24.5c34.9,0,42.9-26.5,42.9-39.7c0-21.5-13.7-39.7-43.7-39.7h-23.7V172.4z M78.2,59.1c5.1,0,9.2,4.1,9.2,9.2c0,5.1-4.1,9.2-9.2,9.2c-5.1,0-9.2-4.1-9.2-9.2C69,63.2,73.1,59.1,78.2,59.1z"/>
                </svg>
                ORCID: 0000-0002-5310-5346
              </a>

              <a
                href="https://www.linkedin.com/in/romain-girardi"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 bg-white/80 backdrop-blur-sm text-blue-600 rounded-full border border-blue-200 hover:shadow-md transition-all text-sm"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                </svg>
                LinkedIn
              </a>

              <a
                href="https://www.cepam.cnrs.fr/contact/romain-girardi/"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 bg-white/80 backdrop-blur-sm text-blue-600 rounded-full border border-blue-200 hover:shadow-md transition-all text-sm"
              >
                CEPAM Profile
              </a>

              <a
                href="mailto:romain.girardi@univ-cotedazur.fr"
                className="inline-flex items-center gap-2 px-4 py-2 bg-white/80 backdrop-blur-sm text-blue-600 rounded-full border border-blue-200 hover:shadow-md transition-all text-sm"
              >
                romain.girardi@univ-cotedazur.fr
              </a>
            </div>
          </div>
        </motion.div>

        {/* Technical Details */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white/95 backdrop-blur-sm rounded-2xl p-8 shadow-sm"
        >
          <h2 className="text-3xl font-bold text-gray-900 mb-6">{t('about.implementationTitle')}</h2>

          <div className="space-y-8 text-gray-700 leading-relaxed">
            <p>{t('about.hiragDesc')}</p>

            {/* Data Exchange Visualization */}
            <div className="flex flex-col items-center py-10">
              <div className="w-full max-w-[800px]">
                <DatabaseWithRestApi
                  className="h-[500px] max-w-[800px]"
                  circleText="API"
                  badgeTexts={{
                    first: "Question",
                    second: "Context",
                    third: "Synthesis",
                    fourth: "Answer"
                  }}
                  buttonTexts={{
                    first: "Knowledge Graph",
                    second: "AI Model"
                  }}
                  title="GraphRAG Pipeline: Database to AI-Generated Responses"
                  lightColor="#769687"
                />
              </div>
              <p className="text-sm text-gray-600 text-center mt-8 max-w-3xl leading-relaxed">
                The API (Application Programming Interface) allows the AI model to communicate with the Knowledge Graph database.
                When you ask a question, it retrieves relevant context from ancient sources and modern scholarship through a
                hierarchical retrieval process, which the AI then synthesizes into a scholarly answer with full citation tracking.
              </p>
            </div>

            {/* HiRAG Technology Highlight */}
            <div className="bg-gradient-to-br from-purple-50 to-indigo-50 p-8 rounded-2xl border-2 border-purple-200 shadow-md">
              <h3 className="text-2xl font-bold text-purple-900 mb-4 flex items-center gap-2">
                {t('about.poweredByHiRAG')}
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-200 text-purple-800">
                  EMNLP 2025
                </span>
              </h3>
              <p className="text-gray-800 mb-4 leading-relaxed">
                EleutherIA implements <strong>HiRAG (Hierarchical Retrieval-Augmented Generation)</strong>, a cutting-edge
                approach that organizes knowledge in hierarchical layers—from detailed textual evidence to high-level conceptual
                summaries. This mirrors how scholars naturally organize information and enables simultaneous access to precise
                citations and broad thematic patterns.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm mb-4">
                <div className="bg-white/70 p-4 rounded-xl">
                  <span className="font-semibold text-purple-900">Performance:</span> HiRAG outperforms traditional RAG by
                  <strong className="text-purple-700"> 87.6% vs 12.4%</strong> and standard GraphRAG by
                  <strong className="text-purple-700"> 64.1% vs 35.9%</strong>
                </div>
                <div className="bg-white/70 p-4 rounded-xl">
                  <span className="font-semibold text-purple-900">Source:</span> Huang et al. (2025).{' '}
                  <a
                    href="https://arxiv.org/abs/2503.10150"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-purple-600 hover:text-purple-800 underline"
                  >
                    arXiv:2503.10150
                  </a>
                  {' '}(EMNLP 2025 Findings)
                </div>
              </div>

              <div className="flex justify-center pt-2">
                <Link
                  to="/graphrag-showcase"
                  className="inline-flex items-center gap-2 px-8 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-semibold rounded-full shadow-md hover:shadow-xl hover:from-purple-700 hover:to-indigo-700 transition-all duration-300 transform hover:scale-105"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  See HiRAG in Action
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </Link>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Philological Work */}
              <div className="bg-gradient-to-br from-teal-50 to-cyan-50 p-6 rounded-xl border-2 border-teal-200 shadow-sm">
                <h4 className="text-lg font-bold mb-4 text-teal-800">{t('about.philologicalWork')}</h4>
                <ul className="text-sm space-y-2">
                  <li className="flex items-start gap-2">
                    <span className="text-teal-600 font-bold">•</span>
                    <span><strong>2,193 entities</strong> verified against ancient sources</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-teal-600 font-bold">•</span>
                    <span><strong>8,616 relationships</strong> with full citations</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-teal-600 font-bold">•</span>
                    <span><strong>189 ancient works</strong> with lemmatization</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-teal-600 font-bold">•</span>
                    <span><strong>16,968 passages</strong> hierarchically structured</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-teal-600 font-bold">•</span>
                    <span><strong>1,413 bibliography entries</strong></span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-teal-600 font-bold">•</span>
                    <span><strong>CTS URN canonical references</strong></span>
                  </li>
                </ul>
              </div>

              {/* Technical Infrastructure */}
              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-xl border-2 border-blue-200 shadow-sm">
                <h4 className="text-lg font-bold mb-4 text-blue-800">{t('about.technicalInfra')}</h4>
                <ul className="text-sm space-y-2">
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 font-bold">•</span>
                    <span><strong>HiRAG Architecture</strong></span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 font-bold">•</span>
                    <span><strong>Hybrid Search:</strong> RRF fusion</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 font-bold">•</span>
                    <span><strong>Vector Database:</strong> Qdrant</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 font-bold">•</span>
                    <span><strong>PostgreSQL</strong> with GIN indexes</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 font-bold">•</span>
                    <span><strong>FastAPI</strong> backend</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 font-bold">•</span>
                    <span><strong>React 19</strong> + TypeScript frontend</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 font-bold">•</span>
                    <span><strong>Streaming Responses</strong></span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </motion.div>

        {/* HiRAG Implementation Details */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-white/95 backdrop-blur-sm rounded-2xl p-8 shadow-sm"
        >
          <HiRAGImplementationDetails />
        </motion.div>

        {/* Open Source Info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-gradient-to-br from-green-50 to-emerald-50 backdrop-blur-sm rounded-2xl p-6 border border-green-200 shadow-sm"
        >
          <p className="text-sm text-gray-800 leading-relaxed">
            <strong className="text-green-700">Open Source & FAIR Compliant:</strong> The entire codebase is open source on{' '}
            <a
              href="https://github.com/romain-girardi-eng/EleutherIA"
              target="_blank"
              rel="noopener noreferrer"
              className="text-green-600 hover:underline font-semibold"
            >
              GitHub
            </a>.
            All data follows FAIR principles (Findable, Accessible, Interoperable, Reusable) and is licensed under{' '}
            <a href="https://creativecommons.org/licenses/by/4.0/" className="text-green-600 hover:underline font-semibold">
              CC BY 4.0
            </a>
            , permanently archived at{' '}
            <a href="https://doi.org/10.5281/zenodo.17379490" className="text-green-600 hover:underline font-semibold">
              DOI: 10.5281/zenodo.17379490
            </a>.
          </p>
        </motion.div>
      </div>
    </AuroraBackground>
  );
}
