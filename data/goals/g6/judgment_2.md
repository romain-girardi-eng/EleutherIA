# Judgment #2 — Adversarial Judge Panel, Scholar-RAG Design Proposals

Judge: adversarial reviewer #2. Brief: score 0–10 on six axes, attack each proposal's weakest
point, name the strongest overall, name the must-graft ideas from the others. Method: I read the
proposals against the failure map, the KG affordance inventory, and the goal doc — and I treated
every claim as a hostile witness. The three proposals are *close siblings* (all three converge on
"a bipolar controversy object is the unit of retrieval and synthesis; delete the template; cite-as-
you-write; ledger as byproduct"). The judgment therefore turns on the **differences**, which are
fewer than the surface volume suggests, and on which weakest points are fatal vs. cosmetic.

---

## Scorecard

| Axis | P1 (DMap dialectician) | P2 (Controversy Graph) | P3 (Dialectical Dossier) |
|------|:---:|:---:|:---:|
| Scholarly fidelity | 8 | 7 | **9** |
| Vectorless + agentic adherence | 8 | 8 | 8 |
| Feasibility on the codebase | 8 | **9** | 8 |
| Use of the graph's edges (0-edge fix) | **9** | 8 | 8 |
| Verifiability (G2-measurable) | 8 | **9** | 8 |
| Novelty | **8** | 6 | 7 |
| **Weighted total** | **49** | **47** | **48** |

(Unweighted sums; fidelity and edge-use are the goal's own headline criteria, so I let those break
ties in the verdict below rather than inflating their column weight here.)

---

## Per-proposal verdict + the attack on its weakest point

### Proposal #1 — "The Argument-Graph-Walking Dialectician" (DMap)

**Strengths.** The single best *conceptual* framing: the Dialectical Map is explicitly cast as one
object playing three roles — retrieval target, synthesis context, **and verification oracle**. That
third role is the proposal's real contribution: §5.2 makes "completeness" a *ratio with a
denominator* (fault lines in the DMap vs fault lines addressed), which is the only place in any of
the three proposals where the completeness critic stops being a vibe-check LLM call and becomes a
mechanical diff. It is also the most disciplined on the F-table: the appendix maps every F1–F12 to a
named fix, and the stage plan (Stage 1 = "stop the bleeding, edges survive even on the old template")
is the smartest migration ordering of the three — it ships success-criterion (b) before touching the
risky synthesis core.

**Weakest point (attacked).** **DF-QuAD is load-bearing here and it shouldn't be.** P1 elevates the
gradual-semantics pass to a structural guarantee ("the formal guarantee behind attribute-never-
assert," §3.3) and uses `contestedness` to drive *presentation order* (§3.3) and the completeness
critic's prioritisation (§5.2). But the KG has **11 `opposes` edges total** and most debate nodes
have *zero* `has_position` out-edges (the inventory says `debate_origins_notion_of_will_modern_paradigm`
has "No outgoing edges," `debate_carneadean` has "0 grounded passages"). Running DF-QuAD over a
3-edge fault line produces strength numbers with no statistical meaning — `base_strength` seeded from
"citation count / recency" on a 252-scholar reception layer is noise dressed as a score. Worse, P1
half-admits this ("never a winner… only a contestedness score") yet still feeds those numbers into
ordering and the oracle. **P3 detected exactly this trap and refused it** (P3 §0.2: "DF-QuAD would
manufacture false precision… itself a kind of anachronistic assertion"). On *this* graph, with *this*
edge sparsity, P3 is right and P1 is over-engineered. The DMap-as-oracle idea is excellent; the
DF-QuAD scoring under it is a liability that adds false precision to a fidelity-critical system.

Secondary attack: P1's `map_dialectic` returns nodes tagged `{pro|con|neutral}` *relative to the
seed* — but `opposes` edges in this graph run argument→position and position→position
asymmetrically (inventory §5 cluster A), and `critiques` frequently runs scholar→scholar with no
debate anchor. The pro/con bipolarisation will mislabel a large fraction of the 244 `critiques`
edges, which are not bipolar at all (Bobzien critiques Long, Sedley, Frede simultaneously — that's a
star, not a pole). P3's flat `DialecticalLink{relation, from_holder, to_holder, gloss}` is the more
honest representation of a star-shaped critique topology.

### Proposal #2 — "The Controversy Graph as the unit of synthesis"

**Strengths.** The most *operationally concrete* on two things the other two underspecify. (1) The
retrieval tools are specified as **actual SQL**: `query_controversies` is "a SQL query over
`kg_nodes WHERE type IN ('debate','controversy','position')` joined to an edge-degree subquery"
(§2a) — that is the only proposal that tells the implementer how the vectorless ranking is computed,
not just that it is. (2) The **G2 eval section is the best of the three**: it names the actual
harness file (`tests/eval/run_eval.py`), the actual scoring function (`eval_lib/scoring.py:
citation_prf`), the `must_not_appear.jsonl` fabrication scan, and — critically — it notices that
**the eval harness has no debate-survey case and cannot reward edge usage until one is added** (§7
step 4). That observation is correct and the other two miss it. P2 also has the cleanest single
sentence on why attribution becomes *mechanically* enforceable: "the label only ever appears inside
an attributed position object" (§0.1).

**Weakest point (attacked).** **`get_controversy_structure(debate_id)` returns the whole frame in
one call — and that is a feasibility lie dressed as a feature.** The inventory is brutal here:
`debate_origins_notion_of_will_modern_paradigm` has its positions connected by `contributes_to`, not
`has_position`; `debate_discovery_of_will` has 31 incoming edges of mixed type; the `opposes` edges
that constitute the actual fault line (Frede⟂Dihle⟂Bobzien) **do not hang off the debate node at
all** — they hang off `scholar_position_*` nodes that are not linked to the debate node by any single
traversable relation. So a one-call `get_controversy_structure(debate_id)` will return participants
and *miss the opposes edges entirely*, because the opposes edges are a hop away on the position nodes,
reached only by the union of `participates_in`-reverse + position-to-position `opposes`. P2's tool
contract promises a clean bipolar object the graph topology cannot deliver in one hop. P1's two-step
(`find_debates` → `map_dialectic` *on each surfaced position*, §2.4 anaphora-chained) and P3's
explicit "traverse one hop of dialectical edges in both directions" from *either a debate OR a
position node* (P3 §2.2) both correctly model that the fault line is reached from the position, not
the debate. P2's single-call abstraction will silently reproduce a milder F1 (it'll get participants
but not the sharp `opposes`).

Secondary attack: P2 scores lowest on novelty because, stripped of its prose, it is "P1's idea minus
the oracle, minus the anaphora-chaining, plus better SQL." Its one genuinely distinct move — DF-QuAD
as *load-bearing* for attribution (§4a, §4c "load-bearing mechanism") — inherits P1's sparsity
problem *and* commits harder to it. And P2 defaults `SCHOLAR_SYNTH_MODEL` to Moonshot direct (§6),
in direct violation of the goal doc's hard "do NOT use Moonshot direct" line — it argues the case
well and gates it, but it ships the violation as the default, where P1 ships the goal-compliant
Fireworks default and makes Moonshot opt-in. On a stated *hard constraint*, P1's reconciliation is
the safer reading.

### Proposal #3 — "The Dialectical Dossier"

**Strengths.** **The most scholar-faithful of the three, and the fidelity edge is not cosmetic.**
Three concrete judgment calls separate it: (1) it *rejects* DF-QuAD strength numbers as false
precision and keeps dialectic as *structure for retrieval/critique* but *prose for the answer* (§0.2)
— exactly correct for a graph with 11 `opposes` edges and for a project whose MEMORY rule is "never
assert modern labels"; numeric strengths are a label asserted as fact. (2) Its synthesis prompt is
the most genuinely *dialectical*: step 3 "**Weigh, don't decide** — note where positions genuinely
conflict vs talk past each other (different `object_of_choice`, different dating)" captures the
single most important scholarly move in *this* literature (the Frede/Dihle dispute is substantially a
talking-past about what "will" denotes), which neither P1 nor P2 articulates. (3) Its degraded mode
(§4.5) is the best of the three: "a shorter reasoned answer over whatever frames did assemble,
explicitly stating coverage limits" — a real scholar's hedge, not P1/P2's "re-synthesise with a
tightened prompt" which can loop. P3 also handles the star-vs-pole topology problem correctly
(flat `DialecticalLink`, build from debate *or* position node).

**Weakest point (attacked).** **The completeness critic's denominator is hand-wavier than P1's.**
P3 §5.2 diffs "planned frames (§1.2) and the debate nodes `find_debates` returned" against "fault
lines actually present in the prose (parsed from `[edge:]`/frame markers)." But the *planned frames*
in P3 are LLM-emitted *hints* ("discovery/origin of the will") that are only resolved to real debate
ids at retrieval time (§1.2: "the planner cannot know which debate nodes exist"). So the
completeness denominator is partly a *model's guess at what debates should exist*, not the graph's
actual debate set — which means the critic can pass an answer that missed a real graph debate the
planner never guessed, and can flag a "gap" for a hallucinated frame the graph can't fill. P1's
denominator is strictly the DMap's *retrieved* fault lines (graph-grounded, no guessing) — tighter.
P3 should adopt P1's rule: the completeness denominator is the set `find_debates` actually returned
(graph-real), with planned-frame hints used only to *seed retrieval*, never to *score completeness*.

Secondary attack: P3's `build_controversy_frame` does a great deal in "one tool call" (positions +
publications + page grounding + contested passages + `_en` join) — like P2's `get_controversy_
structure`, this is a heavy primitive whose internal traversal is under-specified relative to P2's
SQL. P3 *describes* the right edges to follow but, unlike P2, doesn't say how the ranking/limit is
computed, so it inherits a milder version of P2's "the contract is cleaner than the topology" risk.
And P3's planner-hints-not-ids design, while honest about graph ignorance, means the *plan* itself
isn't inspectable-against-the-graph until after the first retrieval round — a weaker audit surface
than P1's fully-typed `ResearchPlan.patterns` (edge programs named up front).

---

## Cross-cutting findings (true of all three, worth flagging)

1. **All three under-test their own central premise: that the fault-line edges are reachable.** None
   of the three actually traces, on a real debate node, the *exact* sequence of edges that gets from
   `debate_discovery_of_will` to the `Frede OPPOSES Dihle` edge. The inventory strongly implies that
   sequence is *not a clean one- or two-hop walk* (positions aren't linked to debates by a uniform
   relation; some debate nodes have zero out-edges). **Whichever proposal is implemented, Stage M1/S1
   must begin with a graph-reachability probe** confirming that `find_debates` → frame assembly
   actually surfaces the 11 `opposes` edges, or the whole edifice retrieves participants and misses
   the disagreement (a subtler F1). This is the highest-risk unverified assumption across all three.

2. **All three remove the char-floor gate and replace it with a content gate — correct and unanimous.**
   This is the right call (F9/F10) and not contested.

3. **All three split retrieval (Fireworks tool-calling) from synthesis (best reasoner) at one seam —
   correct and unanimous.** The only disagreement is the *default*: P1 ships Fireworks (goal-
   compliant), P2/P3 ship Moonshot (empirically-best, goal-violating-but-gated). On a *hard
   constraint*, ship P1's default; keep P2/P3's reasoning as the documented opt-in rationale.

---

## VERDICT

**Strongest overall: Proposal #1 (the DMap dialectician) — but only with two amputations.**

P1 wins because it is the only proposal whose verification step has a *mechanical denominator* (the
DMap-as-oracle), because its migration ordering ships the cheapest win first, and because it ships
the goal-compliant Fireworks default. It is also the most novel (the three-roles-one-object framing
is genuinely the cleanest synthesis of the SOTA the goal asked for). It edges out P3 (the most
scholar-faithful) and P2 (the most concrete) because *verifiability with a real denominator* and
*goal-constraint compliance* are the two things the goal doc weights as hard success criteria, and P1
owns both.

**The two amputations P1 must undergo before implementation:**
- **Kill DF-QuAD as load-bearing.** Demote gradual-semantics to *at most* an internal, advisory
  completeness signal (a fault line with attackers but no defenders is incomplete → expand), and
  **never** emit or order by a numeric strength. This is P3's §0.2 judgment, and it is correct for an
  11-`opposes`-edge graph. Numeric position strengths are a false-precision anachronism in a system
  whose first commandment is "attribute, never assert."
- **Replace pro/con bipolar tagging with P3's flat, star-tolerant `DialecticalLink`.** The 244
  `critiques` edges are star-shaped, not bipolar; P1's `{pro|con|neutral}` tagging will mislabel them.

If Romain prefers minimal conceptual surface area over P1's oracle machinery, **P3 is the safe
runner-up** and loses almost nothing — it is the more *scholarly* design and the closest in spirit to
the project's anti-anachronism ethos. The choice between P1-amputated and P3 is essentially: do you
want P1's tighter verification denominator (yes, graft it into P3 — see below), or do you accept
P3's looser one for less machinery? Either is defensible; I rank P1-amputated first by a hair on
verifiability.

---

## MUST-GRAFT IDEAS (the 2–3 ideas from the OTHERS to import into the winner)

Into **P1 (the chosen base)**, graft:

1. **From P3 — "Weigh, don't decide" + the talking-past detector (P3 §4.2 step 3).** P1's synthesis
   prompt mandates "report contestedness, hedge the conclusion," but P3's instruction to distinguish
   *genuine conflict* from *positions talking past each other* (different `object_of_choice`,
   different dating of "the will") is the single most scholar-authentic move for *this* corpus, where
   the headline dispute is substantially terminological. Without it, the synthesis will narrate
   Frede⟂Dihle as a flat contradiction when the scholarship's actual content is that they
   disagree about what "will" *means*. This is a fidelity upgrade P1 lacks. **Non-negotiable graft.**

2. **From P2 — the explicit G2-eval wiring, especially the missing-debate-case observation (P2 §7).**
   P1's measurement section is good but generic; P2 alone names `tests/eval/run_eval.py`,
   `eval_lib/scoring.py:citation_prf`, `must_not_appear.jsonl`, and — decisively — notices that **the
   eval harness currently has no debate-survey case and therefore cannot reward edge usage until one
   is added to `queries.yaml` with the exact debate-node IDs as `expected_entities` and the fault
   lines as `gold_claims`.** Without this graft, P1's success criterion (b) "edges > 0" is unmeasurable
   on the existing harness — the eval would be blind to the exact thing being fixed. Graft P2's §7
   steps 4–5 wholesale.

3. **From P2 — the SQL-concrete vectorless ranking for the debate-entry tool (P2 §2a).** P1's
   `find_debates` says "pure ts_rank + label match … ranked by opposing_edge_count" but doesn't say
   how. P2's "SQL over `kg_nodes WHERE type IN (debate,controversy,position)` joined to an edge-degree
   subquery" is the implementable spec. Graft it so `find_debates` is buildable on day one.

And one **graft from P3 into P1's verification** (this is the resolution of P1's own weakest point,
above): **use P1's graph-real denominator (the set `find_debates`/`map_dialectic` actually returned)
for the completeness critic — but adopt P3's degraded-mode (§4.5): when frames are thin, return a
shorter reasoned answer that *names its own coverage gap in prose* ("the graph holds rich material on
discovery-of-will; the Carneadean-transmission dispute was thin in this run") rather than looping
re-synthesis.** That hedge-in-prose is more scholar-faithful than any silent retry and is the correct
behaviour when the graph genuinely lacks an edge.

---

## One-line bottom line

**Implement P1, amputate its DF-QuAD scoring and pro/con tagging (replace with P3's flat
star-tolerant links), and graft in P3's "weigh-don't-decide / talking-past" synthesis step + P3's
prose-stated degraded mode + P2's concrete G2-eval-harness wiring and SQL-grounded `find_debates`.**
The result keeps P1's unique strength (the controversy object as verification oracle with a real
denominator) and the goal-compliant Fireworks default, while curing its one fidelity liability with
P3's restraint and its one measurability gap with P2's concreteness. The single highest-risk
unverified assumption shared by all three — that the `opposes`/`critiques` fault-line edges are
actually reachable from the debate nodes in ≤2 hops — must be settled by a reachability probe in the
first migration stage, before any synthesis work.
