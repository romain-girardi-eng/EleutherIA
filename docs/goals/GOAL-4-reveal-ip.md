# G4 — Reveal the IP (Product / UX)

**Objective:** Make EleutherIA's unique asset — the navigable 12-century argument graph + bilingual corpus —
*visible and usable*, so scholars return and cite it. Almost zero backend work; mostly wiring components that
already exist.

**Why (from analysis):** The best assets are orphaned or buried:
- `ConceptEvolutionTimeline.tsx` and `ArgumentMapper.tsx` are built but **wired to no route**.
- `BookReaderPage` (bilingual spread, EB Garamond, KG-passage badges) is the best DH reader in the stack but
  reachable only via a tiny "Mode livre" link.
- `CitationGenerator` (APA/MLA/Chicago/BibTeX) is mounted on **no** passage/answer page.
- The homepage is an opaque particle canvas; a stranger learns nothing about the debate.
- `GraphRAGPage` still has a `window.prompt()` model selector (debug vestige).

**Deliverables (frontend; data via existing `/api`):**
1. **Interactive 12-century debate map** — new `/debate/:conceptId` route wiring `ConceptEvolutionTimeline` +
   `ArgumentMapper` to the `argues_for`/`responds_to`/`precedes` subgraph. Seed: Chrysippus cylinder → Alexander
   refutation → Augustine response.
2. **Bilingual close-reading as default** — make `BookReaderPage` the default `/texts/:textId`; `KGPassageLink` click
   opens the node panel; "Open in GraphRAG" pre-fills a question with the passage URN.
3. **Citation export everywhere** — mount `CitationGenerator` on passage reader, passage detail, and GraphRAG answers
   ("Export bibliography" over the answer's ancient + modern citations).
4. **Scrollytelling entry `/the-debate`** — reuse the HowItWorks `ScrollSection`/`DotNavigator` architecture: five
   moments (Chrysippus→Alexander→Origen→Augustin→Boèce), each a portrait + one live corpus passage + a mini who-responds graph.
5. **Polish** — remove the `window.prompt()` model selector; surface the book reader & debate map in nav.

**First increment:** the `/debate/:conceptId` argument-map route (highest "wow", reuses built components + existing API).

**Success criteria:** A newcomer can walk the debate as a narrative; a scholar can read bilingually + export a citation
in two clicks; the timeline/argument-map components are live, not dead code.

**Dynamic workflow design:** Load the `frontend-design` + `arrange`/`typeset`/`animate` skills. Phase 1: parallel agents
build each route/feature against the existing API + components. Phase 2: `audit`/`critique`/`polish` pass + browser-use
verification. Self-paced per feature.
