import DatabaseWithRestApi from '../components/ui/database-with-rest-api';

export default function AboutPage() {
  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* About the Project */}
      <section className="academic-card">
        <h2 className="text-3xl font-serif font-bold mb-6">About the Project</h2>

        <div className="space-y-4 text-academic-text leading-relaxed">
          <p>
            <strong>EleutherIA</strong> (Ἐλευθερία = freedom + IA = Intelligence Artificielle) emerged from
            the need for a comprehensive, structured database documenting ancient philosophical debates on free will,
            fate, and moral responsibility. This research infrastructure was developed as part of doctoral research
            at Université Côte d'Azur, investigating how early Christian authors conceptualized human freedom and agency.
          </p>

          <p>
            When examining the notion of free will among the first Christian authors, it became clear that existing
            resources lacked the systematic structure necessary for computational analysis and cross-referential research.
            The philosophical landscape spanning from Classical Greek thought (4th c. BCE) through Late Antiquity (6th c. CE)
            is incredibly rich, with complex networks of influence, argumentation, and conceptual evolution that traditional
            bibliographic approaches struggle to capture.
          </p>

          <p>
            This database represents an independent effort to address that gap. Every node, edge, and citation has been
            meticulously researched and verified against ancient sources and modern scholarship. The project integrates
            508 philosophical entities (persons, works, concepts, arguments) connected through 831 relationships, alongside
            289 ancient texts with full lemmatization support.
          </p>

          <p>
            The goal is to provide researchers, students, and anyone interested in ancient philosophy with a FAIR-compliant
            (Findable, Accessible, Interoperable, Reusable) resource that combines traditional philological rigor with
            modern computational capabilities. The integration of GraphRAG (Graph-based Retrieval-Augmented Generation)
            enables semantic search and question-answering while maintaining complete provenance and citation tracking.
          </p>

          <p className="text-sm text-academic-muted italic">
            Note: This database represents a personal research initiative. All aspects—from conceptualization and
            philological work to data curation, technical implementation, and interface design—were undertaken
            individually to support doctoral research needs.
          </p>
        </div>
      </section>

      {/* About the Author */}
      <section className="academic-card">
        <h2 className="text-3xl font-serif font-bold mb-6">About the Author</h2>

        <div className="space-y-4 text-academic-text leading-relaxed">
          <div className="flex items-start gap-6">
            <div className="flex-shrink-0">
              <img
                src="/romain-girardi.jpg"
                alt="Romain Girardi"
                className="w-40 h-40 rounded-full object-cover shadow-lg"
                style={{ objectPosition: 'center 30%' }}
              />
            </div>
            <div className="flex-grow">
              <h3 className="text-xl font-semibold mb-2">Romain Girardi</h3>
              <p className="text-academic-muted mb-4">PhD Candidate in Ancient Languages and Literature / Theology</p>
            </div>
          </div>

          <p>
            Romain Girardi is a doctoral candidate in a joint PhD program (cotutelle internationale) between
            <strong> Université Côte d'Azur</strong> and <strong>Université de Genève</strong> (since January 2024),
            working under the supervision of Prof. Arnaud Zucker (CEPAM, UMR 7264) and Prof. Andreas Dettwiler
            (Faculté de Théologie Jean Calvin). His dissertation examines the emergence and conceptualization of
            free will among early Christian authors, exploring why references to human freedom proliferate in
            2nd-century CE Christian literature despite being absent from biblical texts and relatively rare in
            earlier philosophical works.
          </p>

          <div className="bg-academic-bg p-4 rounded">
            <h4 className="font-semibold mb-2">Research Interests</h4>
            <ul className="list-disc list-inside space-y-1 text-sm">
              <li>Ancient philosophy of action and moral responsibility</li>
              <li>Stoic and Peripatetic theories of determinism and freedom</li>
              <li>Early Christian theological anthropology</li>
              <li>Pauline exegesis and patristic reception</li>
              <li>Conceptual history and terminology evolution (Greek to Latin)</li>
              <li>Digital humanities and knowledge graph approaches to ancient texts</li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-2">Academic Background</h4>
            <ul className="space-y-1 text-sm">
              <li>• Joint PhD in Ancient Languages and Literature (UniCA) / Theology (UNIGE) (2024–present)</li>
              <li>• Agrégation preparation diploma (2020)</li>
              <li>• Master's degree in Classical Letters, distinction (2019)</li>
              <li>• Bachelor's degree in Classical Letters, distinction (2017)</li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-2">Institutional Affiliations</h4>
            <ul className="space-y-1 text-sm">
              <li>
                • <strong>Université Côte d'Azur</strong> — CEPAM (Cultures et Environnements. Préhistoire, Antiquité, Moyen Âge), UMR 7264, CNRS
              </li>
              <li>
                • <strong>Université de Genève</strong> — Faculté de Théologie Jean Calvin
              </li>
            </ul>
          </div>

          <div className="flex flex-wrap gap-4 pt-4">
            <a
              href="https://orcid.org/0000-0002-5310-5346"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-sm text-primary-600 hover:underline"
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
              className="inline-flex items-center gap-2 text-sm text-primary-600 hover:underline"
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
              className="inline-flex items-center gap-2 text-sm text-primary-600 hover:underline"
            >
              CEPAM Profile
            </a>

            <a
              href="mailto:romain.girardi@univ-cotedazur.fr"
              className="inline-flex items-center gap-2 text-sm text-primary-600 hover:underline"
            >
              romain.girardi@univ-cotedazur.fr
            </a>
          </div>
        </div>
      </section>

      {/* Technical Details */}
      <section className="academic-card">
        <h2 className="text-3xl font-serif font-bold mb-6">Implementation</h2>

        <div className="space-y-6 text-academic-text leading-relaxed">
          <p>
            The database combines traditional philological expertise with modern computational infrastructure:
          </p>

          {/* Data Exchange Visualization */}
          <div className="flex justify-center py-8">
            <DatabaseWithRestApi
              circleText="REST"
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

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-academic-bg p-4 rounded">
              <h4 className="font-semibold mb-2">Philological Work</h4>
              <ul className="text-sm space-y-1">
                <li>• 508 entities verified against ancient sources</li>
                <li>• 831 relationships documented with citations</li>
                <li>• 289 texts with lemmatization (Greek/Latin)</li>
                <li>• 860+ ancient sources & modern scholarship</li>
                <li>• Controlled vocabularies & terminology</li>
                <li>• Complete provenance tracking</li>
              </ul>
            </div>

            <div className="bg-academic-bg p-4 rounded">
              <h4 className="font-semibold mb-2">Technical Infrastructure</h4>
              <ul className="text-sm space-y-1">
                <li>• JSON knowledge graph (13 MB)</li>
                <li>• PostgreSQL with full-text search</li>
                <li>• Qdrant vector database</li>
                <li>• Google Gemini embeddings</li>
                <li>• Interactive network visualization</li>
                <li>• GraphRAG question answering</li>
              </ul>
            </div>
          </div>

          <p className="text-sm">
            The codebase is open source and available on{' '}
            <a
              href="https://github.com/romain-girardi-eng/EleutherIA"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-600 hover:underline"
            >
              GitHub
            </a>.
            All data is licensed under{' '}
            <a href="https://creativecommons.org/licenses/by/4.0/" className="text-primary-600 hover:underline">
              CC BY 4.0
            </a>
            {' '}and permanently archived at{' '}
            <a href="https://doi.org/10.5281/zenodo.17379490" className="text-primary-600 hover:underline">
              DOI: 10.5281/zenodo.17379490
            </a>.
          </p>
        </div>
      </section>
    </div>
  );
}
