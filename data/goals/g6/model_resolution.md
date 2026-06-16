# G6 — Model Resolution: Kimi K2.7 for Scholar-RAG Synthesis

Tested 2026-06-16 from prod container `eleutheria-api` (deploy-host) against `api.moonshot.ai/v1`.

---

## (a) Is there a general (non-code) K2.7 model on Moonshot?

**No.** The full `/v1/models` list contains exactly these K2.x entries:

| id | context | reasoning | temp constraint |
|----|---------|-----------|----------------|
| `kimi-k2.5` | 262,144 | yes | `temperature=1` only |
| `kimi-k2.6` | 262,144 | yes | `temperature=1` only |
| `kimi-k2.7-code` | 262,144 | yes | `temperature=1` only |
| `kimi-k2.7-code-highspeed` | 262,144 | yes | `temperature=1` only |
| `kimi-latest` | 131,072 | no | any |
| `moonshot-v1-{8k,32k,128k,auto}` | 8k–131k | no | any |

There is no `kimi-k2.7`, `kimi-k2.7-instruct`, `kimi-k2.7-plus`, or any general-purpose K2.7 variant.
The only K2.7 models are code-specialised. Confirmed by direct API call — not documentation.

Also confirmed that **Fireworks has no K2.7** (`accounts/fireworks/models/kimi-k2p7` → 404 NOT_FOUND).
Fireworks carries `kimi-k2p6` and `kimi-k2p5` only.

---

## (b) Candidate evaluation

### Temperature constraint
All `kimi-k2.x` models (K2.5, K2.6, K2.7-code, K2.7-code-highspeed) enforce `temperature=1`.
Any value ≠ 1 returns:
```json
{"error": {"message": "invalid temperature: only 1 is allowed for this model", "type": "invalid_request_error"}}
```

The legacy `moonshot-v1-*` and `kimi-latest` accept arbitrary temperatures but are NOT reasoning models
(`supports_reasoning: false`, context ≤ 131k).

### Token budget for reasoning models
All K2.x reasoning models produce a `reasoning_content` field (chain-of-thought) before `content` (final answer).
For a scholarly synthesis (~500-word output), the reasoning phase consumes ~7,000–14,000 chars of scratch.
At 1000–3000 `max_tokens`, the model runs out during reasoning and returns `content: ""`.
**Minimum safe `max_tokens` for scholarly synthesis: 5,000.**

### Scholarly prose quality (tested with the G6 trigger question)

**kimi-k2.5** (tested at 4000 tokens): Produces solid, well-structured scholarly prose. Uses Greek
terminology, Bobzien/Frede/Long positions accurately attributed, hedging correct. Output: ~4,600 chars.
Clean stop. Time: ~60s.

**kimi-k2.7-code** (tested at 5000 tokens): Superior scholarly prose. Uses polytonic Greek diacritics
(`τὸ ἐφ᾽ ἡμῖν`, `εἱμαρμένη`, `συγκατάθεσις`), section-structured, richer nuance in citing Bobzien 1998
and Frede 2011 with accurate page-level characterisation. Reasoning_content 14k chars. Output: ~4,200 chars.
Clean stop. Time: ~95s.

**kimi-k2.7-code-highspeed** (tested at 4000 tokens): Matches k2.7-code quality, ~40% faster. Uses
Greek, attributed positions, hedging. ~4,670 chars output. Clean stop. Time: ~55s.

**Verdict**: Despite the "code" name, K2.7 produces **genuinely excellent scholarly prose** — better than
K2.5. The reasoning step is an advantage for dialectical synthesis (it weighs evidence before writing).
The "code" designation refers to training emphasis, not output-type limitation.

### Context window
All K2.x models: **262,144 tokens**. Sufficient for a full evidence dossier + synthesis prompt.

---

## (c) Recommended model id + params

### Primary: `kimi-k2.7-code-highspeed` on Moonshot

```python
ModelProvider.KIMI: {
    "base_url": "https://api.moonshot.ai/v1",
    "model": "kimi-k2.7-code-highspeed",    # primary synthesis
    "thinking_model": "kimi-k2.7-code",     # deeper reasoning for hard queries (slower, richer)
    "env_key": "MOONSHOT_API_KEY",
    "base_url_env": "MOONSHOT_BASE_URL",
    "rate_limit": 20,
}
```

**Parameters for synthesis calls:**
```python
temperature = 1         # mandatory — any other value → 400 error
max_tokens  = 8000      # safe upper bound; typical synthesis uses 4-5k; reasoning eats the rest
```

**Critical wiring note in `_openai_compatible_payload`:**
The current code passes `temperature` as a caller argument. For the KIMI provider, the synthesiser call
site must hardcode `temperature=1.0` (or the service must clamp it). The service should detect
`provider == ModelProvider.KIMI` and override temperature:

```python
if provider == ModelProvider.KIMI:
    payload["temperature"] = 1.0   # enforce Moonshot constraint
```

### Accessing `reasoning_content`
The API returns both `choices[0].message.reasoning_content` (chain-of-thought) and
`choices[0].message.content` (final answer). The current `_openai_compatible_payload` / response
parser already handles this (grep shows `reasoning_content` extracted in existing service code).
No change needed there.

---

## Fallback chain (recommended)

```
kimi-k2.7-code-highspeed (Moonshot, 262k, temp=1, fast)
    → kimi-k2.6 (Moonshot, 262k, temp=1, if highspeed degraded)
        → accounts/fireworks/models/kimi-k2p6 (Fireworks, temp flexible, K2.6 via different infra)
            → gemini-3.1-pro-preview (Gemini, 1M ctx, temp flexible, last resort)
```

Rationale:
- K2.7-highspeed: best speed/quality for synthesis; first choice
- K2.6 Moonshot: same infra, same constraints, lower capability
- Fireworks K2p6: independent infra (no Moonshot outage risk), no temp=1 constraint, older model
- Gemini: entirely different provider + model family, true last-resort

In `llm_service.py`, the `_provider_attempt_order` for the KIMI provider should try highspeed first,
then fall through to the existing FIREWORKS→GEMINI chain. Since there is only one `ModelProvider.KIMI`,
the highspeed-vs-standard distinction is best handled by a `MOONSHOT_MODEL` env var (already wired as
`"model"` in PROVIDER_CONFIGS, overridable via `MOONSHOT_MODEL` env var — **add this**).

Recommended env var defaults:
```env
MOONSHOT_MODEL=kimi-k2.7-code-highspeed
MOONSHOT_THINKING_MODEL=kimi-k2.7-code
```

---

## Summary

| Question | Answer |
|----------|--------|
| General K2.7 on Moonshot? | No — only `kimi-k2.7-code` and `kimi-k2.7-code-highspeed` |
| Temperature constraint? | All K2.x: `temperature=1` mandatory (enforced server-side) |
| Context window? | 262,144 tokens for all K2.x models |
| Min max_tokens for synthesis? | 5,000 (reasoning phase consumes majority of token budget) |
| Scholarly prose quality? | Excellent — K2.7-code produces polytonic Greek, attributed positions, hedging |
| Recommended model id? | `kimi-k2.7-code-highspeed` (synthesis) + `kimi-k2.7-code` (thinking_model) |
| Fireworks K2.7? | 404 NOT_FOUND — does not exist |
| Fallback chain? | kimi-k2.7-code-highspeed → kimi-k2.6 → fireworks/kimi-k2p6 → gemini-3.1-pro-preview |
