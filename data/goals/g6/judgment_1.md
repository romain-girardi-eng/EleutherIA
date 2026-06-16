# Judgment #1 — Adversarial Judge (Scholar-RAG design panel)

Scoring each of the three proposals 0–10 on six axes, then attacking each proposal's weakest
point, then naming the overall winner and the must-graft ideas.

Axes:
- **SF** Scholarly fidelity (attribute, weigh primary vs reception, represent disagreement, hedge)
- **VA** Vectorless + agentic adherence (no embeddings; model-driven iterative retrieval)
- **FE** Feasibility on the existing codebase (concrete file/line surgery, not hand-wavy)
- **GE** Use of the graph's edges (kills the 0-edge failure)
- **VE** Verifiability (measurable by the G2 eval harness)
- **NO** Novelty

---

## Scorecard

| Axis | P1 (DMap / DF-QuAD oracle) | P2 (Controversy Graph as unit-of-synthesis) | P3 (Dialectical Dossier, DF-QuAD internal-only) |
|------|---------------------------|----------------------------------------------|-------------------------------------------------|
| SF   | 8 | 8 | **9** |
| VA   | 9 | 9 | 9 |
| FE   | 8 | **9** | **9** |
| GE   | **9** | 9 | 9 |
| VE   | **9** | 8 | 8 |
| NO   | **9** | 7 | 7 |
| **Total / 60** | **52** | **50** | **51** |

The three converge on the same correct spine (the disagreement layer becomes the unit of both
retrieval and synthesis; the facet template is *deleted*, not patched; the ledger is reversed to a
byproduct; edges survive ingestion via a typed store; two relational tools; a two-tier model split
with a single synthesis seam). They are genuinely close. The differences that matter are at the
margins — and those margins are exactly where each one is attackable.

---

## Per-axis reasoning

### Scholarly fidelity (SF)

- **P3 (9)** wins the axis on one decisive judgment call: it **refuses to put DF-QuAD strength
  numbers in the answer** (§0.2). It adopts the *bipolar structure* (supporters/attackers,
  recursive) as a retrieval shape and an internal completeness signal, but argues — correctly —
  that a surfaced "Frede 0.62 vs Dihle 0.38" is itself a *manufactured, anachronistic assertion*,
  antithetical to "attribute, never assert." That is the most scholar-literate sentence in the
  whole panel. A real historian of philosophy does not score Frede-vs-Dihle on a [0,1] scale; she
  reports who holds what and who attacks whom and lets it stand. P3 also has the most concrete
  hedging machinery (its 5-step reasoning procedure forces "weigh, don't decide" + "primary anchor
  or hedge harder" per position) and the most faithful worked example (the actual Dihle/Frede/
  Bobzien frame with real publication page-ranges in §4.2).

- **P1 (8)** and **P2 (8)** both lean on DF-QuAD as a *load-bearing* mechanism. P1 is careful —
  its `contestedness` is explicitly "never *which side is correct*" and drives *presentation order*
  only (§3.3) — so it is defensible. But it still computes a per-position aggregate strength and
  feeds it into the synthesis prompt as a signal the model "reports." P2 is the most exposed:
  §4a calls DF-QuAD "the load-bearing mechanism for attribute-never-assert" and seeds
  `base_strength` from citation count + recency, then tells the model to "hedge accordingly" from
  the strengths. Seeding scholarly weight from *citation count* is a citation-popularity proxy for
  truth — precisely the bibliometric fallacy a scholar would reject (a heavily-cited 1982 thesis
  is not thereby stronger than a 2011 rebuttal). That is a fidelity liability, not an asset.

### Vectorless + agentic (VA)

All three are clean: pure ts_rank + lemmatic + tree-nav + KG adjacency + `has_translation` join,
no embeddings anywhere, model-driven ReAct escalation retained, the two new tools are SQL/adjacency.
Tie at 9. (None earns a 10 because none stress-tests the *agentic* claim hard: all three make the
debate-first behaviour primarily a *system-prompt instruction* plus a planner DAG; the model is
strongly railroaded toward `find_debates → map/build → read_passages`. That is good for
reliability but it is closer to a planned program than to open-ended model-driven search. P1's
anaphora-chained hops (§2.4) is the most genuinely agentic touch.)

### Feasibility (FE)

- **P2 (9)** and **P3 (9)** both ship a per-stage migration table with file:line targets, risk
  ratings, and an explicit "S0/M0 ships edges surviving *before* the synthesis rewrite" early win.
  P3's table (M0–M7) is the most surgically precise (it names `state.py:387`, the exact
  `DialecticalSynthesis` node replacing `DraftClaimLedger`+`RenderGroundedAnswer`, the
  `build_provenance_ledger` post-pass, and the dead-ref repoint). P2's S0–S8 is equally concrete
  and adds the streaming-cap = blocking-cap reconciliation explicitly.

- **P1 (8)** is concrete too (4 stages, all the right file:lines) but it carries the heaviest *new
  machinery* per shipped stage — the DMap assembler + DF-QuAD scorer + the orphan/coverage-gap
  bookkeeping + RARR span-edit — which raises the implementation surface and the risk that Stage 3
  becomes a big-bang. It loses a point purely on build-cost-vs-payload.

### Graph edges (GE)

Tie at 9. All three apply the identical *correct* root fix: `_ingest_get_neighbors` keeps
`relation` + `direction`, a typed `DialecticalEdge` store lands on `RAGState`, the context pack
gets a top-level edges/controversy layer so the prompt is *structurally* unable to be edge-blind.
P3 is marginally the most explicit about the relation whitelist (`DIALECTICAL_RELATIONS` set
enumerated, incl. `participates_in`/`contributes_to`/`advanced_in`/`interprets`) and about
retaining edges in `_ingest_explore_subgraph` too, not just `get_neighbors`. None earns a 10
because none of them resolves the **structural gaps the affordance inventory flags**: e.g.
`debate_origins_notion_of_will_modern_paradigm` has *no* `has_position`/participant out-edges, and
`debate_carneadean_antiastrology_tradition` has *0 grounded passages*. A tool that walks edges
from a debate node with no out-edges returns an empty frame — and none of the three plans a
fallback (lexical-match the participants, or hop via the `argument_cafma_*` cluster). This is a
silent failure waiting on exactly two of the four headline debates in the trigger question.

### Verifiability (VE)

- **P1 (9)** wins because its **completeness critic has a real denominator**: "fault-line coverage
  = |fault lines addressed| / |fault lines in the DMap|." It states the DMap-as-oracle property
  explicitly — completeness is *mechanically checkable* because the map *is* the set of edges the
  answer must cover — and it adds a regression-test fixture (≥3 distinct fault lines, >0
  opposes/critiques in the DMap, 0 occurrences of the `"frames the issue as"` template string).
  That last one is the single best test in the panel: it asserts the template can *never silently
  return*.

- **P2 (8)** and **P3 (8)** both wire the eval well (old-vs-new capture, the three new metrics —
  edge-use count, attribution rate, counter-evidence coverage — and crucially **adding the missing
  survey/comparison cases to `queries.yaml`**, which P2 spells out most concretely with the exact
  expected debate-node IDs and `gold_claims`). P2's point about "the harness *cannot see* the
  improvement without these cases" is sharp and true. But neither frames completeness as a
  ratio-with-denominator as cleanly as P1; their completeness critic is an LLM "what did you miss?"
  call rather than a deterministic set-diff, which is softer to measure.

### Novelty (NO)

- **P1 (9)** — the **DMap as a single typed object that is simultaneously the retrieval target,
  the synthesis context, *and* the verification oracle** is the one genuinely new idea in the
  panel. "One object kills F1–F12 because it is structurally unable to be edge-blind: it has no
  rows except edges." That tri-purpose framing (esp. oracle-for-the-completeness-critic) is more
  than a rename of "controversy graph"; it gives the verifier a denominator for free.

- **P2 (7)** / **P3 (7)** — "controversy graph as unit of synthesis" is the same core insight,
  well-argued, but P1 already subsumes it and pushes it one structural step further. P3's
  novelty is in *restraint* (DF-QuAD internal-only) rather than in a new construct.

---

## Adversarial attack on each proposal's weakest point

### Attack on P1 — the DF-QuAD scorer is dead weight it then has to apologise for

P1's signature object is great, but it bolts on **deterministic DF-QuAD gradual semantics** (§3.3)
and then spends the rest of the document defending it ("never a winner," "structurally hedged,"
"the formal guarantee"). This is a self-inflicted wound. The `contestedness` score it computes is
used for exactly one thing the answer surfaces: *presentation order* ("most contested first").
You do not need a propagated argumentation-semantics calculus to sort fault lines by contestedness
— `len(opposes ∪ critiques edges incident to the frame)` gives the same ordering, deterministically,
with zero risk of leaking a spurious strength number into the prose. P1 has imported a heavyweight
formal apparatus (DF-QuAD, base-strength seeding, support/attack propagation) whose only
load-bearing output is a sort key, while creating a standing fidelity hazard (a `base_strength` and
per-position aggregate that *must not* reach the reader, enforced only by prompt discipline). **P3
already saw this and cut it.** P1's most novel asset (the oracle) is independent of DF-QuAD; the
DF-QuAD is the part most likely to be quietly ripped out in week two.

### Attack on P2 — it seeds scholarly strength from citation count, and is the most schedule-fragile

Two punches. (1) **Fidelity:** §4a seeds `base_strength` from "citation count of its publication,
number of grounding passages, recency." This operationalises *popularity = strength* and *recency
= strength*, then instructs the model to "hedge accordingly." For a project whose entire reason for
existing is to *not* let the field's loudest voice stand as the verdict, baking citation-count into
the dialectical weighting is the wrong primitive — and it is more exposed than P1 because P2 calls
this weighting "the load-bearing mechanism for attribute-never-assert" (it is the opposite: it is a
mechanism for asserting). (2) **Schedule:** P2's S5 is described as "high; the heart" and bundles
the DF-QuAD pass + new prompt + template deletion + ledger inversion into one stage, and S5 is the
cutover. P3 splits the same work so the irreversible core (M4) does *not* also carry the DF-QuAD
risk (P3 has no DF-QuAD to carry). P2 is the proposal most likely to have its single highest-risk
stage stall on the part that matters least.

### Attack on P3 — it is the safe synthesis of the other two, and under-specifies its own retrieval fallback

P3's weakness is the flip side of its strength: it is largely **the intersection of P1 and P2 with
the riskiest bits removed** — it borrows the controversy-frame-as-unit (P2), the two-tier model
seam (all), the edge store (all), and earns its distinctiveness mostly by *subtracting* DF-QuAD.
That is the correct call, but it means P3 contributes little net-new machinery the others lack.
Concretely, its one genuinely independent move — making the bipolar structure an *internal
completeness signal* ("attackers but no surfaced defenders ⇒ incomplete frame ⇒ expand") — is
asserted but **not given a denominator or a stop rule** the way P1's coverage ratio is; "incomplete"
is checked by an LLM, not a set-diff. And like the others, P3's `build_controversy_frame` walks
`participates_in`/`has_position`/`contributes_to` from the debate node — but the affordance
inventory says two of the four trigger debates (`origins_notion_of_will_modern_paradigm`,
`carneadean_antiastrology_tradition`) have **no out-edges / 0 grounded passages**. P3 names those
debates in its own worked plan (§1.2 frames f1/f4) yet provides no fallback for the case where the
frame-builder hits a structurally-empty debate node — so its showcase example would, on the real
graph, return two empty frames and silently under-deliver exactly the Frede/Dihle and Amand/Ramelli
fault lines it promises.

---

## Verdict — strongest overall

**P1 ("Argument-Graph-Walking Dialectician") is the strongest overall**, by a nose (52 vs 51 vs 50).

It wins for one reason that outranks the close numbers: the **Dialectical Map as a tri-purpose typed
object — retrieval target, synthesis context, *and* verification oracle** — is the only idea in the
panel that gives the completeness critic a real *denominator* and makes "the template can never
silently return" a one-line regression assertion. That is the most direct, most measurable kill of
the actual G6 trigger failure ("0 edges, garbage, no real answer"), and it is the most novel. P1
also has the strongest eval section and the only explicit anti-template regression fixture.

P1's losing margin on SF (its DF-QuAD baggage) is **fixable by deletion**, whereas P3's deficit
(no net-new machinery; under-specified completeness denominator) and P2's deficits (citation-count
weighting; bundled high-risk cutover) are more structural. The right move is to take P1 as the base
spec and graft P3's restraint onto it.

---

## Must-graft ideas from the other two (the merge instruction)

1. **From P3 — kill DF-QuAD; keep only the bipolar *structure*, never the numbers (the single most
   important graft).** Replace P1's DF-QuAD `contestedness`/`base_strength` calculus with P3's
   restraint: adopt supporters/attackers as the frame's *shape* and as an *internal completeness
   signal only* (attackers-with-no-defender ⇒ expand), sort fault lines by raw incident-edge count,
   and **emit no strength scalar into the prose**. This removes P1's only real fidelity hazard at
   zero cost to its oracle (the oracle is independent of DF-QuAD) and resolves the strongest attack
   against the winner. It simultaneously neutralises P2's citation-count-weighting liability by
   making the whole scoring layer go away.

2. **From P2 — make the G2 eval *able to see* the win: add the survey/comparison cases to
   `queries.yaml` with the exact expected debate-node IDs and `gold_claims`, and add the three
   metrics (edge-use count, attribution rate, counter-evidence coverage).** P1's regression fixture
   is excellent but its eval still leans on the existing entity-heavy harness; P2 correctly observes
   the harness is structurally blind to relational improvement until the debate-survey cases exist.
   Graft P2's concrete queries.yaml additions (trigger question + kin, `expected_entities` =
   `debate_discovery_of_will` / `scholar_position_frede_will_originates_epictetus` / etc.) on top of
   P1's denominator-based coverage metric and anti-template snapshot test.

3. **From P3 (and partly P2) — the explicit two-tier model seam wording + the structurally-empty
   debate-node fallback.** Adopt P3's cleaner statement of the model split (planner + ReAct
   retrieval + subagents + verifier all on Fireworks `kimi-k2p6`; *only* the single dialectical-
   synthesis call routes to the swap-point), with the `temperature=1.0` KIMI clamp and the fallback
   chain. **Critically, add the fallback none of the three specified:** when `find_debates` /
   `build_controversy_frame` lands on a debate node with no out-edges or 0 grounded passages
   (true for `origins_notion_of_will_modern_paradigm` and `carneadean_antiastrology_tradition`),
   the frame-builder must fall back to lexical-matching participants and hopping via the
   `argument_*`/`argument_cafma_*` clusters and the `contributes_to` arguments — otherwise the
   winner's own showcase trigger returns two empty frames.

### Bonus graft (cheap, high-value)
From **P1**, keep its **anaphora-chained hops** (§2.4: `map_dialectic` returns IDs the model binds
into the next call) — it is the most genuinely *agentic* mechanism in the panel and should survive
into the merged spec to keep the design honest to the "model-driven, not a fixed program" constraint.

---

## One-line synthesis

Build **P1's tri-purpose Dialectical-Map-as-oracle**, **delete its DF-QuAD** in favour of **P3's
numbers-free bipolar restraint**, wire **P2's queries.yaml + metrics** so the eval can actually
score the win, and add the **empty-debate-node retrieval fallback all three missed**.
