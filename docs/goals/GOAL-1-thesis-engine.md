# G1 — The Thesis Engine

**Objective:** Generalize the Amand-vs-Bobzien arbitration (a structured corpus used as a *quantifiable
arbiter* of a historiographical dispute) into reusable, read-only graph instruments that directly serve
the dissertation and generate paper figures.

**Why (from analysis):** The KG already contains the thesis backbone *in the edges, not just in prose*:
`Heimarmenê` spans 9 periods, `to eph' hēmin` 7, `Prohairesis` 7, `Autexousion` Hellenistic→Contemporary;
255-person giant influence component with real chains (Alexander→Origen, Averroes→Aquinas). But nobody has
wired these traversals into reusable queries. Weaknesses to address: 6 duplicate `autexousion` concept nodes
fragment any emergence curve; only 39% of ancient arguments are passage-grounded; only 16% have dialectical edges.

**Deliverables (artifacts under `data/goals/g1/`):**
1. **Concept-emergence timelines** — for each free-will core concept, a dated attestation curve (period-bucketed,
   earliest grounded passage per period, every point cited). Figure-ready JSON + markdown.
2. **Transmission-path queries** — `transmission_path(A, B)`: shortest grounded influence chain with the passage
   licensing each hop (e.g. Carneades→Cicero→Origen→Nemesius). Reusable script.
3. **Research-leads report** — mechanically surfaced unexplored questions: high-concept-degree arguments with 0
   grounding; argument pairs sharing ≥2 concepts but no dialectical edge (candidate debates); concepts attested in
   period N and N+2 but missing N+1 (transmission gaps). Ranked by centrality.
4. **Prereq cleanup (staged)**: merge the 6 `autexousion` duplicates (preserve variants via `has_variant`).

**First increment:** αὐτεξούσιον emergence curve — merge duplicates (proposal), then compute the dated, cited curve
from `discusses`/`employs`/`advanced_in`/`defines` neighbors. Reuse `scripts/analyze_amand_stoic_provenance.py` as template.

**Success criteria:** A reviewer can regenerate any emergence curve / transmission path from the snapshot; each data
point carries a passage_id; the αὐτεξούσιον curve is defensible as a thesis figure.

**Dynamic workflow design:** Phase 1 (read-only analysis): parallel agents compute emergence curves, transmission
paths, research-leads from `data/kg/*.jsonl`. Phase 2 (staged enrichment): propose concept-dedup + grounding fills as
JSONL for review. Self-paced: re-run as the reception layer (G5) grows.
