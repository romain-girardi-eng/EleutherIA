export function BenefitsContent() {
  return (
    <>
      {/* Benefit 1: Relationship Discovery */}
      <div className="bg-white/80 rounded-lg p-2.5 border border-green-100">
        <div className="font-semibold text-green-800 mb-1.5">
          Discovers Hidden Relationships
        </div>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>Traditional search:</strong> "Augustine free will" → finds Augustine's writings.
        </p>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>HiRAG:</strong> Finds Augustine → traverses to Pelagius (opponent) →
          discovers the Pelagian Controversy → connects to earlier Stoic concepts Augustine adapted
          → reveals the complete debate context.
        </p>
        <p className="text-green-700 text-xs font-medium italic">
          → You understand Augustine's position through his intellectual battles and sources.
        </p>
      </div>

      {/* Benefit 2: Contextual Understanding */}
      <div className="bg-white/80 rounded-lg p-2.5 border border-green-100">
        <div className="font-semibold text-green-800 mb-1.5">
          Provides Rich Historical Context
        </div>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>Simple RAG:</strong> Retrieves isolated text chunks about "ἐφ' ἡμῖν" (in our power).
        </p>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>HiRAG:</strong> Shows how the concept evolved from Aristotle (4th c. BCE) →
          adopted by Stoics → critiqued by Carneades → reformulated by Epictetus →
          transmitted to Latin as "in nostra potestate" → influenced Christian theology.
        </p>
        <p className="text-green-700 text-xs font-medium italic">
          → You see the intellectual genealogy spanning 800 years.
        </p>
      </div>

      {/* Benefit 3: Argument Networks */}
      <div className="bg-white/80 rounded-lg p-2.5 border border-green-100">
        <div className="font-semibold text-green-800 mb-1.5">
          Maps Complete Argument Networks
        </div>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>Keyword search:</strong> "Chrysippus determinism" → scattered mentions.
        </p>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>HiRAG:</strong> Retrieves Chrysippus's arguments → follows "refutes" edges to
          Carneades's counter-arguments → finds Cicero's synthesis → discovers later Neoplatonic
          responses → extracts all cited sources.
        </p>
        <p className="text-green-700 text-xs font-medium italic">
          → You get the full dialectical landscape, not isolated opinions.
        </p>
      </div>

      {/* Benefit 4: Automatic Citations */}
      <div className="bg-white/80 rounded-lg p-2.5 border border-green-100">
        <div className="font-semibold text-green-800 mb-1.5">
          Grounds Every Claim in Sources
        </div>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>Standard LLM:</strong> Might hallucinate "Plato discussed compatibilism in Republic X."
        </p>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>HiRAG:</strong> Only uses information from retrieved nodes. Automatically extracts
          ancient sources (e.g., "Aristotle, <em>EN</em> III.1, 1110a1-4") and modern scholarship
          (e.g., "Bobzien 1998, Frede 2011") from node metadata.
        </p>
        <p className="text-green-700 text-xs font-medium italic">
          → Verifiable, academically rigorous answers you can cite in your own research.
        </p>
      </div>

      {/* Benefit 5: Multi-hop Reasoning */}
      <div className="bg-white/80 rounded-lg p-2.5 border border-green-100">
        <div className="font-semibold text-green-800 mb-1.5">
          Enables Multi-Hop Reasoning
        </div>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>Question:</strong> "How did Aristotelian ethics influence Christian theology?"
        </p>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>HiRAG path:</strong> Aristotle → "influenced" → Alexander of Aphrodisias →
          "transmitted_by" → Arabic commentators → "influenced" → Thomas Aquinas →
          "synthesized_with" → Augustine's theology.
        </p>
        <p className="text-green-700 text-xs font-medium italic">
          → Traces intellectual transmission across cultures and centuries in a single query.
        </p>
      </div>
    </>
  );
}
