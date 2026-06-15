# EleutherIA — Next-Level Roadmap (2026-06-15)

Five goals to take EleutherIA from "impressive platform" to "reference scholarly instrument."
Each goal is driven by a **dynamic workflow** (self-paced, multi-agent) that produces **reviewable
artifacts** — never auto-writes to the KG/corpus. All KG/corpus mutations follow the standing rule:
stage proposals → verify each → human review → apply → deploy.

Source of analysis: parallel exploration 2026-06-15 (product/UX · graphrag/eval · semantic/LOD · scholarly-modeling).

| # | Goal | Core value | Writes? | First artifact |
|---|------|-----------|---------|----------------|
| [G1](GOAL-1-thesis-engine.md) | **Thesis engine** | Corpus as quantifiable arbiter; serves the dissertation + papers | read-only analyses; staged enrichment | αὐτεξούσιον emergence curve |
| [G2](GOAL-2-provable-quality.md) | **Provable quality** | Annotated gold set + baselines → publishable benchmark | eval data + report | citation-F1 + faithfulness numbers |
| [G3](GOAL-3-prod-pipeline.md) | **Fix prod divergence** | Users hit the verified, cited pipeline | diagnosis + fix | root-cause report |
| [G4](GOAL-4-reveal-ip.md) | **Reveal the IP (product)** | 12-century debate navigable; scholars return & cite | frontend (wiring existing components) | interactive argument-map route |
| [G5](GOAL-5-literature-mapping.md) | **Secondary-lit mapping & arbitration** | Map scholarly agreements/disagreements; arbitrate debates | staged KG enrichment + arbitration reports | consensus/contested matrix per locus |

## Cross-cutting principles
- **No auto-fix**: workflows emit JSONL proposals + markdown reports under `data/goals/<gN>/`; I verify each, then apply.
- **Provenance everywhere**: every generated claim traces to passage_id + edge chain + (where reception) scholar + confidence.
- **Anti-anachronism**: keep modern labels ("libertarian", "compatibilism", "invention of the will") attributed, never asserted (see memory).
- **Critical editions only** for any new primary text; original + English citation.

## Sequencing
G1 + G2 are read-only / data-only and shippable on the current snapshot → start here.
G3 is a contained bugfix (can run in parallel).
G4 is near-zero-backend frontend wiring.
G5 is the deepest (reading more scholarship) → runs continuously, feeds G1's reception layer.
