# Scholar-RAG — Known flaws & weaknesses (audit 2026-06-17)

Catalogue of every flaw observed while shipping GOAL-7 (grounding) + GOAL-8 (citations).
Each entry: **evidence** (how it was observed) · **impact** · **proposed fix** · **severity**.
P0 = correctness/broken feature · P1 = quality/robustness · P2 = architectural debt.

---

## P0 — Correctness / broken features

### F1. Verifier-v2 (citation auditor) cannot parse its own LLM output — citation verification is effectively dead
- **Evidence:** prod logs, every query: `Verifier could not parse LLM output for <node> (attempt 1/3 … 2/3). Raw output: 'The user wants me to act as an adversarial citation auditor … Wait, the claim is just "Susanne Bobzien"? That seems odd …'`. The auditor model (kimi-k2p7-code, a non-reasoning code model) rambles a meta-monologue instead of emitting the required JSON verdict; all 3 attempts fail.
- **Impact:** the adversarial citation-faithfulness gate (M5) silently no-ops. `citation_verified` events fire but the verdicts are unreliable; the `verified`/confidence on passage_citations is not trustworthy. The whole anti-hallucination promise of the verifier layer is hollow.
- **Also:** the claim handed to the auditor is sometimes just a bare name ("Susanne Bobzien") or "Robert F. Dobbin, 121" — the auditor input itself is malformed (it should receive a full claim+passage pair, not a label).
- **Proposed fix:** (a) move the verifier to a model that returns structured output reliably (deepseek-v4-pro reasoning + JSON, or enforce a tool/function-call JSON schema); (b) make the parser robust to a reasoning-then-JSON response (extract the last JSON object); (c) fix the claim payload so the auditor gets the actual claim sentence + the grounding passage, not a bare node label; (d) if a verdict can't be parsed after retries, FAIL CLOSED (mark unverified) not silently pass.
- **Severity: P0** — a scholarly tool whose citation verifier doesn't run is a credibility risk.

### F2. Frede mischaracterised as incompatibilist (content-accuracy regression under fallback)
- **Evidence:** Romain flagged a live answer asserting "Frede argues Epictetus is incompatibilist/libertarian, opposing Bobzien" — Frede actually holds Epictetus *originated* free will but a **compatibilist** one; the KG node is accurate, the error came from the gemini fallback. With deepseek restored it should improve, but it has NOT been re-verified on a fresh post-fix answer.
- **Impact:** factual misattribution of a scholar's position = the worst failure mode for this tool.
- **Proposed fix:** re-verify the final answer's scholar characterisations on a fresh run; consider a lightweight "scholar-position fidelity" check in the verifier that flags an attributed claim that contradicts the holder's KG node description.
- **Severity: P0** — accuracy of named-scholar attribution is the core value.

---

## P1 — Quality / robustness

### F3. Only ~1 primary passage actually quoted per answer
- **Evidence:** final verified run: `[passage_]=3` markers but `ancient=1` resolved primary source; the synthesis quotes one Epictetus passage. The map carries more contested passages than reach the prose.
- **Impact:** thin primary grounding for a corpus that holds ~560 Epictetus passages.
- **Proposed fix:** raise the contested-passage budget that reaches the synthesis; ensure ≥2 quotable-Greek passages per dominant fault line; have the synthesis prompt require quoting the *strongest* primary passage per position, not just one overall.
- **Severity: P1**

### F4. deepseek-v4-pro empties intermittently (reasoning eats the shared max_tokens) — fallback masks but does not cure
- **Evidence:** identical query streamed 31 answer_chunks once, 0 another time; deepseek emits 2189+ reasoning deltas then sometimes zero content (finish_reason=length). Now caught by the kimi-k2p7-code fallback + deterministic hedge, but when those fire the answer quality drops (kimi < deepseek; the hedge is a deterministic serialization).
- **Impact:** non-deterministic answer quality; the "guarantee" is a floor, not consistent excellence.
- **Proposed fix:** bound deepseek's reasoning relative to content on Fireworks — pass a reasoning cap / `reasoning_effort` if supported, or a larger total `max_tokens` (raise clamp) with an enforced answer reserve; instrument how often the fallback/hedge fires (it should be rare). Confirm whether Fireworks deepseek-v4-pro honours `max_completion_tokens` separate from reasoning.
- **Severity: P1**

### F5. answer_cache invalidation is a manual constant — stale answers silently mask fixes
- **Evidence:** `_CACHE_SCHEMA_VERSION` had to be hand-bumped v2→v3; mid-session, cached pre-grounding answers were served and looked like the fix had failed (cost ~30 min of confusion + wasted verification runs).
- **Impact:** every prompt/grounding/citation change risks serving stale answers until someone remembers to bump the constant; users see outdated answers.
- **Proposed fix:** derive the cache-version segment from a hash of the synthesis prompt + the scholar-RAG code/version (or the git SHA at build), so any change auto-invalidates. Or add a TTL + a `force_refresh` affordance in the UI.
- **Severity: P1**

### F6. Observability is invisible in prod (INFO logs dropped) — grounding can't be debugged live
- **Evidence:** the `ControversyMap assembled: N frames, … authors=…` logger.info never appeared in prod logs (prod log level = WARNING). Diagnosing GOAL-7 required adding/removing logs + in-container probes.
- **Impact:** no way to see, per query, how many primary passages by author reached the synthesis, how often the hedge fires, or why a passage was dropped.
- **Proposed fix:** emit a structured per-query diagnostics object (frames, contested-passage author histogram, passages-with-quotable-Greek count, synthesis model used, fallback/hedge fired?) into `state.metadata` and surface it in the SSE `complete.metadata` (and/or a trace event) — visible without changing the prod log level. Gate verbose logs behind an env flag.
- **Severity: P1**

### F7. Direct external verification is impossible (CF tunnel cuts the stream) — only in-container probes work
- **Evidence:** every direct `curl https://free-will.app/.../query/stream` was severed mid-retrieval; only `http://localhost:8000` from inside the container completes. The UI survives via CF-worker keep-alive pings.
- **Impact:** no reliable external/E2E test of the full pipeline; CI can't smoke-test the live answer path.
- **Proposed fix:** a small authenticated internal health/smoke endpoint that runs one canned query end-to-end and returns the metrics (non-empty, greek≥1, ancient≥1, no leaked ids) — callable from CI/cron; OR document the in-container probe as the official E2E harness.
- **Severity: P1**

### F8. Inline footnote-style citation badges — requested, not end-to-end verified
- **Evidence:** Romain asked for "badges inline cliquables comme des notes de bas de page qui ouvrent direct la ref"; CitationRenderer produces `[P#]`/scholar/passage badges, and the double-open bug was fixed, but the full "click inline badge → opens the resolved reference / in-context passage" flow with the NEW resolved labels was not visually verified post-fix.
- **Impact:** the marquee UX may be partially working.
- **Proposed fix:** verify (and fix if needed) that every inline badge shows the RESOLVED label (not an id), and a single click opens exactly one surface: primary → in-context passage reader; scholar → the bibliography entry / node detail.
- **Severity: P1**

### F9. Corpus passage text quality is uneven (data hygiene)
- **Evidence:** Epictetus passages variously hold clean Greek, `**Reference:** **Author:** **Work:**` markdown metadata blocks (no quotable text), or `Greek: • ἐφ' ἡμῖν - gloss` bullet formats. `_greek_quality` routes around the bad ones but they remain and pollute other retrieval paths (hybrid search, read_passages, the passage reader).
- **Impact:** grounding and the passage reader sometimes show metadata/gloss instead of running text.
- **Proposed fix (audit-only here):** quantify how many corpus passages are reference-blocks/gloss vs clean text (per author/work); flag the worst works for clean re-ingestion (separate data project — do NOT auto-rewrite text; academic-integrity policy). This file should carry the audit numbers.
- **Severity: P1 (audit) / P2 (re-ingestion)**

---

## P2 — Architectural debt (flag; likely out of scope for a code spawn)

### F10. Synthesis latency ~5–10 min on the synchronous SSE request
- **Evidence:** deepseek deep reasoning 200–400s; `MAX_TOOL_CALLS=18` is a band-aid to keep retrieval inside the Cloudflare connection window (unbounded → 67 calls → stream cut before synthesis).
- **Proposed fix:** move synthesis off the request — enqueue a job, stream/poll results — so retrieval depth and synthesis time are decoupled from the connection window. Then `MAX_TOOL_CALLS` can be raised / governed by the completeness critic ("laisse décider" becomes safe).
- **Severity: P2** — real architectural change; needs Romain's go.

---

## Fix order for the rigor spawn
P0 first (F1 verifier, F2 Frede/accuracy), then P1 code fixes (F3 more passages, F4 deepseek budget, F5 cache hash, F6 observability, F7 smoke endpoint, F8 inline badges), F9 as an audit (numbers only, no text rewrite). F10 documented, not auto-fixed.
Each fix: investigate → implement → ADVERSARIALLY verify (a second agent tries to break it) → live-verify in-container. Maximum rigor, opus.
