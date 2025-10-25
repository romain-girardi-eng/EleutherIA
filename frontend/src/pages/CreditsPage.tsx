export default function CreditsPage() {
  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Page Header */}
      <section className="academic-card">
        <h1 className="text-4xl font-serif font-bold mb-4">Credits and Licensing</h1>
        <p className="text-academic-muted leading-relaxed">
          EleutherIA builds upon the work of many open-source projects and digital humanities initiatives.
          This page acknowledges all data sources, tools, and libraries that make this project possible.
        </p>
      </section>

      {/* Primary Data Sources */}
      <section className="academic-card">
        <h2 className="text-3xl font-serif font-bold mb-6">Primary Data Sources</h2>

        <div className="space-y-6">
          {/* Perseus Digital Library */}
          <div className="border-l-4 border-primary-500 pl-6 py-2">
            <h3 className="text-xl font-semibold mb-2">Perseus Digital Library</h3>
            <p className="text-sm text-academic-muted mb-3">
              The foundational source for Greek and Latin classical texts used throughout this database.
            </p>
            <ul className="text-sm space-y-2">
              <li>
                <strong>canonical-greekLit:</strong>{' '}
                <a
                  href="https://github.com/PerseusDL/canonical-greekLit"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline"
                >
                  https://github.com/PerseusDL/canonical-greekLit
                </a>
              </li>
              <li>
                <strong>canonical-latinLit:</strong>{' '}
                <a
                  href="https://github.com/PerseusDL/canonical-latinLit"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline"
                >
                  https://github.com/PerseusDL/canonical-latinLit
                </a>
              </li>
              <li>
                <strong>License:</strong> CC BY-SA 3.0 (
                <a
                  href="https://creativecommons.org/licenses/by-sa/3.0/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline"
                >
                  Creative Commons Attribution-ShareAlike 3.0
                </a>
                )
              </li>
              <li>
                <strong>Works accessed:</strong> Aristotle (Nicomachean Ethics, De Interpretatione, Eudemian Ethics),
                Cicero (De Fato, Academica, De Divinatione), Epictetus (Discourses), Plotinus (Enneads),
                Plutarch, Aulus Gellius (Noctes Atticae), Lucretius (De Rerum Natura), and many others
              </li>
              <li className="text-academic-muted italic">
                Citation: Crane, G. R. (Ed.). (1987-). Perseus Digital Library. Tufts University.{' '}
                <a
                  href="http://www.perseus.tufts.edu"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline"
                >
                  http://www.perseus.tufts.edu
                </a>
              </li>
            </ul>
          </div>

          {/* Scaife Viewer CTS API */}
          <div className="border-l-4 border-primary-500 pl-6 py-2">
            <h3 className="text-xl font-semibold mb-2">Scaife Viewer (CTS API)</h3>
            <p className="text-sm text-academic-muted mb-3">
              Canonical Text Services (CTS) API providing standardized access to classical texts via URN-based citation system.
            </p>
            <ul className="text-sm space-y-2">
              <li>
                <strong>Website:</strong>{' '}
                <a
                  href="https://scaife.perseus.org"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline"
                >
                  https://scaife.perseus.org
                </a>
              </li>
              <li>
                <strong>API:</strong>{' '}
                <a
                  href="https://scaife.perseus.org/library/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline"
                >
                  CTS URN Library
                </a>
              </li>
              <li>
                <strong>Provider:</strong> Perseus Digital Library / Scaife Collaborative
              </li>
              <li>
                <strong>License:</strong> CC BY-SA 3.0 (texts inherited from Perseus)
              </li>
            </ul>
          </div>

          {/* Open Greek and Latin - CSEL */}
          <div className="border-l-4 border-primary-500 pl-6 py-2">
            <h3 className="text-xl font-semibold mb-2">Open Greek and Latin Project - CSEL Corpus</h3>
            <p className="text-sm text-academic-muted mb-3">
              TEI-XML encoded Latin patristic texts from the Corpus Scriptorum Ecclesiasticorum Latinorum (CSEL),
              particularly important for Augustine's works on free will and grace.
            </p>
            <ul className="text-sm space-y-2">
              <li>
                <strong>GitHub Repository:</strong>{' '}
                <a
                  href="https://github.com/OpenGreekAndLatin/csel-dev"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline"
                >
                  https://github.com/OpenGreekAndLatin/csel-dev
                </a>
              </li>
              <li>
                <strong>Works accessed:</strong> Augustine (De Libero Arbitrio, De Gratia et Libero Arbitrio,
                De Civitate Dei, Confessiones, De Correptione et Gratia, De Spiritu et Littera, Contra Academicos,
                Retractationes, and other works)
              </li>
              <li>
                <strong>License:</strong> CC0 1.0 Universal (Public Domain Dedication)
              </li>
              <li className="text-academic-muted italic">
                Citation: Almas, B., Cayless, H., Clérice, T., Liuzzo, P. M., Romanello, M., & Stoyanova, R. (Eds.).
                Open Greek and Latin Project. Leipzig University.{' '}
                <a
                  href="https://github.com/OpenGreekAndLatin"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline"
                >
                  https://github.com/OpenGreekAndLatin
                </a>
              </li>
            </ul>
          </div>

          {/* TEI (Text Encoding Initiative) */}
          <div className="border-l-4 border-primary-500 pl-6 py-2">
            <h3 className="text-xl font-semibold mb-2">TEI (Text Encoding Initiative)</h3>
            <p className="text-sm text-academic-muted mb-3">
              Standard markup language for digital texts, used for parsing and processing all TEI-XML sources.
            </p>
            <ul className="text-sm space-y-2">
              <li>
                <strong>Website:</strong>{' '}
                <a
                  href="https://tei-c.org/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline"
                >
                  https://tei-c.org/
                </a>
              </li>
              <li>
                <strong>License:</strong> CC BY-SA 4.0 for Guidelines
              </li>
            </ul>
          </div>

          {/* Sematika MVP */}
          <div className="border-l-4 border-primary-500 pl-6 py-2">
            <h3 className="text-xl font-semibold mb-2">Sematika MVP</h3>
            <p className="text-sm text-academic-muted mb-3">
              Previous research database providing foundational texts that were migrated into this expanded system.
            </p>
            <ul className="text-sm space-y-2">
              <li>
                <strong>Content:</strong> New Testament, Patristic texts (Origen, Clement, Tertullian, Irenaeus, Apologists)
              </li>
              <li>
                <strong>Status:</strong> Internal research database, texts now integrated with full TEI-XML and embeddings
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* Technical Infrastructure */}
      <section className="academic-card">
        <h2 className="text-3xl font-serif font-bold mb-6">Technical Infrastructure</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Visualization Libraries */}
          <div>
            <h3 className="text-lg font-semibold mb-3">Visualization and Graph Tools</h3>
            <ul className="text-sm space-y-2">
              <li>
                <strong>Cytoscape.js</strong> ({' '}
                <a
                  href="https://js.cytoscape.org/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline"
                >
                  js.cytoscape.org
                </a>
                ) - Knowledge graph visualization - MIT License
              </li>
              <li>
                <strong>D3.js</strong> ({' '}
                <a
                  href="https://d3js.org/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline"
                >
                  d3js.org
                </a>
                ) - Data visualization and timeline components - ISC License
              </li>
              <li>
                <strong>Recharts</strong> - React charts for statistics - MIT License
              </li>
            </ul>
          </div>

          {/* Frontend Framework */}
          <div>
            <h3 className="text-lg font-semibold mb-3">Frontend Framework</h3>
            <ul className="text-sm space-y-2">
              <li>
                <strong>React</strong> ({' '}
                <a
                  href="https://react.dev/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline"
                >
                  react.dev
                </a>
                ) - UI framework - MIT License
              </li>
              <li>
                <strong>Vite</strong> - Build tool and development server - MIT License
              </li>
              <li>
                <strong>TypeScript</strong> - Type-safe JavaScript - Apache 2.0 License
              </li>
              <li>
                <strong>TailwindCSS</strong> ({' '}
                <a
                  href="https://tailwindcss.com/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline"
                >
                  tailwindcss.com
                </a>
                ) - CSS framework - MIT License
              </li>
              <li>
                <strong>Framer Motion</strong> - Animation library - MIT License
              </li>
            </ul>
          </div>

          {/* Backend Services */}
          <div>
            <h3 className="text-lg font-semibold mb-3">Backend Services</h3>
            <ul className="text-sm space-y-2">
              <li>
                <strong>FastAPI</strong> - Python web framework - MIT License
              </li>
              <li>
                <strong>PostgreSQL</strong> ({' '}
                <a
                  href="https://www.postgresql.org/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline"
                >
                  postgresql.org
                </a>
                ) - Relational database for full-text search - PostgreSQL License
              </li>
              <li>
                <strong>Qdrant</strong> ({' '}
                <a
                  href="https://qdrant.tech/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline"
                >
                  qdrant.tech
                </a>
                ) - Vector database for semantic search - Apache 2.0 License
              </li>
              <li>
                <strong>Google Gemini</strong> - Embedding model for semantic search
              </li>
            </ul>
          </div>

          {/* UI Components */}
          <div>
            <h3 className="text-lg font-semibold mb-3">UI Components and Utilities</h3>
            <ul className="text-sm space-y-2">
              <li>
                <strong>Radix UI</strong> ({' '}
                <a
                  href="https://www.radix-ui.com/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline"
                >
                  radix-ui.com
                </a>
                ) - Accessible UI components - MIT License
              </li>
              <li>
                <strong>Lucide React</strong> - Icon library - ISC License
              </li>
              <li>
                <strong>React Markdown</strong> - Markdown rendering - MIT License
              </li>
              <li>
                <strong>Axios</strong> - HTTP client - MIT License
              </li>
              <li>
                <strong>TourGuide.js</strong> - Interactive tour system - MIT License
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* Development Tools */}
      <section className="academic-card">
        <h2 className="text-3xl font-serif font-bold mb-6">Development Tools and Services</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-semibold mb-3">Version Control and Hosting</h3>
            <ul className="text-sm space-y-2">
              <li>
                <strong>GitHub</strong> ({' '}
                <a
                  href="https://github.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline"
                >
                  github.com
                </a>
                ) - Source code repository
              </li>
              <li>
                <strong>Git LFS</strong> - Large file storage for database files
              </li>
              <li>
                <strong>Render</strong> - Backend hosting platform
              </li>
              <li>
                <strong>Cloudflare</strong> - CDN and static site hosting
              </li>
            </ul>
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-3">Data Archival and Persistence</h3>
            <ul className="text-sm space-y-2">
              <li>
                <strong>Zenodo</strong> ({' '}
                <a
                  href="https://zenodo.org"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline"
                >
                  zenodo.org
                </a>
                ) - Long-term research data preservation
              </li>
              <li>
                <strong>DOI:</strong>{' '}
                <a
                  href="https://doi.org/10.5281/zenodo.17379490"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline"
                >
                  10.5281/zenodo.17379490
                </a>
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* Standards and Protocols */}
      <section className="academic-card">
        <h2 className="text-3xl font-serif font-bold mb-6">Standards and Protocols</h2>

        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold mb-2">Canonical Text Services (CTS)</h3>
            <p className="text-sm text-academic-muted mb-2">
              Standard for citing and retrieving ancient texts using URN-based identifiers.
            </p>
            <ul className="text-sm space-y-1">
              <li>
                <strong>Documentation:</strong>{' '}
                <a
                  href="http://cite-architecture.github.io/cts/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline"
                >
                  cite-architecture.github.io/cts/
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-2">FAIR Data Principles</h3>
            <p className="text-sm text-academic-muted mb-2">
              This database adheres to FAIR principles: Findable, Accessible, Interoperable, Reusable.
            </p>
            <ul className="text-sm space-y-1">
              <li>
                <strong>Reference:</strong>{' '}
                <a
                  href="https://www.go-fair.org/fair-principles/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline"
                >
                  go-fair.org/fair-principles/
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-2">JSON Schema</h3>
            <p className="text-sm text-academic-muted mb-2">
              Database structure validated against JSON Schema Draft 07 specification.
            </p>
            <ul className="text-sm space-y-1">
              <li>
                <strong>Specification:</strong>{' '}
                <a
                  href="https://json-schema.org/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline"
                >
                  json-schema.org
                </a>
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* License Information */}
      <section className="academic-card">
        <h2 className="text-3xl font-serif font-bold mb-6">EleutherIA License</h2>

        <div className="bg-academic-bg p-6 rounded-lg">
          <div className="flex items-start gap-4 mb-4">
            <img
              src="https://mirrors.creativecommons.org/presskit/buttons/88x31/svg/by.svg"
              alt="CC BY 4.0"
              className="w-24 h-auto"
            />
            <div>
              <h3 className="font-semibold text-lg mb-2">Creative Commons Attribution 4.0 International (CC BY 4.0)</h3>
              <p className="text-sm text-academic-muted">
                The EleutherIA database and all original content are licensed under CC BY 4.0.
              </p>
            </div>
          </div>

          <div className="space-y-3 text-sm">
            <p>
              <strong>You are free to:</strong>
            </p>
            <ul className="list-disc list-inside space-y-1 ml-4">
              <li><strong>Share</strong> — copy and redistribute the material in any medium or format</li>
              <li><strong>Adapt</strong> — remix, transform, and build upon the material for any purpose, even commercially</li>
            </ul>

            <p className="mt-4">
              <strong>Under the following terms:</strong>
            </p>
            <ul className="list-disc list-inside space-y-1 ml-4">
              <li>
                <strong>Attribution</strong> — You must give appropriate credit, provide a link to the license,
                and indicate if changes were made
              </li>
            </ul>

            <p className="mt-4">
              <strong>Suggested Citation:</strong>
            </p>
            <p className="italic bg-white p-3 rounded border border-academic-border">
              Girardi, R. (2025). <em>EleutherIA: Ancient Free Will Database</em> (Version 3.0.0) [Data set].
              Zenodo.{' '}
              <a
                href="https://doi.org/10.5281/zenodo.17379490"
                className="text-primary-600 hover:underline"
                target="_blank"
                rel="noopener noreferrer"
              >
                https://doi.org/10.5281/zenodo.17379490
              </a>
            </p>

            <p className="mt-4 text-academic-muted">
              Full license text:{' '}
              <a
                href="https://creativecommons.org/licenses/by/4.0/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary-600 hover:underline"
              >
                https://creativecommons.org/licenses/by/4.0/
              </a>
            </p>
          </div>
        </div>
      </section>

      {/* Acknowledgments */}
      <section className="academic-card">
        <h2 className="text-3xl font-serif font-bold mb-6">Acknowledgments</h2>

        <div className="space-y-4 text-sm leading-relaxed">
          <p>
            This project would not be possible without the dedication of the digital classics and humanities communities,
            particularly:
          </p>

          <ul className="space-y-2 list-disc list-inside ml-4">
            <li>
              <strong>Perseus Digital Library</strong> at Tufts University for decades of work digitizing ancient texts
              and making them freely available
            </li>
            <li>
              <strong>Open Greek and Latin Project</strong> at Leipzig University for high-quality TEI-XML editions
              of patristic and classical texts
            </li>
            <li>
              <strong>Text Encoding Initiative (TEI)</strong> for establishing standards that enable interoperability
              across digital text projects
            </li>
            <li>
              <strong>Scaife Viewer</strong> for implementing CTS protocol and providing modern infrastructure for
              classical text access
            </li>
            <li>
              The maintainers of all open-source libraries and frameworks listed above
            </li>
          </ul>

          <p className="mt-6 text-academic-muted italic">
            Special thanks to the supervisors of this doctoral research: Prof. Arnaud Zucker (Université Côte d'Azur, CEPAM)
            and Prof. Andreas Dettwiler (Université de Genève, Faculté de Théologie Jean Calvin).
          </p>
        </div>
      </section>

      {/* Contact for Corrections */}
      <section className="academic-card bg-primary-50 border-primary-200">
        <h2 className="text-2xl font-serif font-bold mb-4">Report Issues or Suggest Corrections</h2>
        <p className="text-sm leading-relaxed mb-4">
          If you notice any errors in attribution, licensing information, or missing acknowledgments,
          please contact us or open an issue on GitHub.
        </p>
        <div className="flex flex-wrap gap-4">
          <a
            href="mailto:romain.girardi@univ-cotedazur.fr"
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 transition-colors"
          >
            Contact via Email
          </a>
          <a
            href="https://github.com/romain-girardi-eng/EleutherIA/issues"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 bg-academic-text text-white rounded hover:bg-opacity-90 transition-colors"
          >
            Open GitHub Issue
          </a>
        </div>
      </section>
    </div>
  );
}
