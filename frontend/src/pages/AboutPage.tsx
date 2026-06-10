import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { Typewriter } from '../components/ui/typewriter';
import { useKgStats, formatCount } from '../hooks/useKgStats';

export default function AboutPage() {
  const { t, i18n } = useTranslation();
  const stats = useKgStats();
  const fmt = (n: number) => formatCount(n, i18n.language);

  return (
    <div className="min-h-screen w-full pt-28 pb-12 bg-transparent">
      <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">

        {/* Modern Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <h1 className="text-3xl sm:text-5xl md:text-6xl font-display font-bold text-stone-800 mb-4">
            About{" "}
            <Typewriter
              text={["EleutherIA", "the Project", "the Database"]}
              speed={100}
              waitTime={3000}
              deleteSpeed={60}
              className="text-stone-800"
              cursorChar="_"
            />
          </h1>
          <p className="text-base sm:text-lg text-stone-600 max-w-2xl mx-auto">
            A FAIR-compliant knowledge graph documenting ancient debates on free will
          </p>
        </motion.div>

        {/* About the Author */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-parchment-100/70 backdrop-blur-sm rounded-2xl p-5 sm:p-8 shadow-sm"
        >
          <h2 className="text-2xl sm:text-3xl font-display font-bold text-stone-800 mb-6">{t('about.authorTitle')}</h2>

          <div className="space-y-6 text-stone-600 leading-relaxed">
            <div className="flex flex-col md:flex-row items-start gap-6">
              <div className="flex-shrink-0 mx-auto md:mx-0">
                <img
                  src="/romain-girardi-painted.webp"
                  alt={t('about.authorName')}
                  className="w-40 h-40 sm:w-48 sm:h-48 rounded-2xl object-cover shadow-lg"
                />
              </div>
              <div className="flex-grow min-w-0">
                <h3 className="text-xl sm:text-2xl font-display font-bold text-stone-800 mb-2">{t('about.authorName')}</h3>
                <p className="text-stone-500 mb-4">{t('about.authorTitle2')}</p>
                <p>{t('about.authorBio')}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
              <div className="bg-gradient-to-br from-parchment-50 to-amber-50 p-4 sm:p-6 rounded-xl border border-amber-200/60">
                <h4 className="font-display font-bold text-lg text-stone-800 mb-3">{t('about.researchInterests')}</h4>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-start gap-2">
                    <span className="text-orange-600 font-bold">•</span>
                    <span>{t('about.interest1')}</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-orange-600 font-bold">•</span>
                    <span>{t('about.interest2')}</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-orange-600 font-bold">•</span>
                    <span>{t('about.interest3')}</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-orange-600 font-bold">•</span>
                    <span>{t('about.interest4')}</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-orange-600 font-bold">•</span>
                    <span>{t('about.interest5')}</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-orange-600 font-bold">•</span>
                    <span>{t('about.interest6')}</span>
                  </li>
                </ul>
              </div>

              <div className="bg-gradient-to-br from-amber-50 to-orange-50 p-4 sm:p-6 rounded-xl border border-orange-200/60">
                <h4 className="font-display font-bold text-lg text-stone-800 mb-3">{t('about.academicBackground')}</h4>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-start gap-2">
                    <span className="text-orange-600 font-bold">•</span>
                    <span>{t('about.degree1')}</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-orange-600 font-bold">•</span>
                    <span>{t('about.degree2')}</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-orange-600 font-bold">•</span>
                    <span>{t('about.degree3')}</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-orange-600 font-bold">•</span>
                    <span>{t('about.degree4')}</span>
                  </li>
                </ul>
              </div>
            </div>

            <div className="bg-parchment-50 backdrop-blur-md p-4 sm:p-6 rounded-xl border border-stone-200">
              <h4 className="font-display font-bold text-lg text-stone-800 mb-3">Institutional Affiliations</h4>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <span className="text-stone-500 font-bold">•</span>
                  <span><strong>Université Côte d'Azur</strong> — CEPAM (Cultures et Environnements. Préhistoire, Antiquité, Moyen Âge), UMR 7264, CNRS</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-stone-500 font-bold">•</span>
                  <span><strong>Université de Genève</strong> — Faculté autonome de théologie protestante</span>
                </li>
              </ul>
            </div>

            <div className="flex flex-wrap gap-4">
              <a
                href="https://orcid.org/0000-0002-5310-5346"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 bg-parchment-50 backdrop-blur-sm text-orange-600 rounded-full border border-amber-200 hover:shadow-md transition-all text-sm"
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
                className="inline-flex items-center gap-2 px-4 py-2 bg-parchment-50 backdrop-blur-sm text-orange-600 rounded-full border border-amber-200 hover:shadow-md transition-all text-sm"
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
                className="inline-flex items-center gap-2 px-4 py-2 bg-parchment-50 backdrop-blur-sm text-orange-600 rounded-full border border-amber-200 hover:shadow-md transition-all text-sm"
              >
                CEPAM Profile
              </a>

              <a
                href="mailto:romain.girardi@univ-cotedazur.fr"
                className="inline-flex items-center gap-2 px-4 py-2 bg-parchment-50 backdrop-blur-sm text-orange-600 rounded-full border border-amber-200 hover:shadow-md transition-all text-sm"
              >
                romain.girardi@univ-cotedazur.fr
              </a>
            </div>
          </div>
        </motion.div>

        {/* About the Project */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-parchment-100/70 backdrop-blur-sm rounded-2xl p-5 sm:p-8 shadow-sm"
        >
          <h2 className="text-2xl sm:text-3xl font-display font-bold text-stone-800 mb-6">{t('about.projectTitle')}</h2>

          <div className="space-y-4 text-stone-600 leading-relaxed">
            <p>
              <strong className="text-stone-800">EleutherIA</strong> {t('about.projectIntro')}
            </p>

            <p>{t('about.projectContext')}</p>
            <p>
              {t('about.projectDetails', {
                nodes: fmt(stats.nodes),
                edges: fmt(stats.edges),
                works: fmt(stats.works),
                passages: fmt(stats.passages),
              })}
            </p>
            <p>{t('about.projectGoal')}</p>

            <p className="text-sm text-stone-500 italic">
              {t('about.projectNote')}
            </p>
          </div>
        </motion.div>

        {/* Open Source Info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-gradient-to-br from-amber-50 to-orange-50 backdrop-blur-sm rounded-2xl p-6 border border-amber-200/60 shadow-sm"
        >
          <p className="text-sm text-stone-700 leading-relaxed">
            <strong className="text-orange-700">Open Source & FAIR Compliant:</strong> The entire codebase is open source on{' '}
            <a
              href="https://github.com/romain-girardi-eng/EleutherIA"
              target="_blank"
              rel="noopener noreferrer"
              className="text-orange-600 hover:text-orange-800 hover:underline font-semibold"
            >
              GitHub
            </a>.
            All data follows FAIR principles (Findable, Accessible, Interoperable, Reusable) and is licensed under{' '}
            <a href="https://creativecommons.org/licenses/by/4.0/" className="text-orange-600 hover:text-orange-800 hover:underline font-semibold">
              CC BY 4.0
            </a>
            , permanently archived at{' '}
            <a href="https://doi.org/10.5281/zenodo.17379489" className="text-orange-600 hover:text-orange-800 hover:underline font-semibold">
              DOI: 10.5281/zenodo.17379489
            </a>.
          </p>
        </motion.div>
      </div>
    </div>
  );
}
