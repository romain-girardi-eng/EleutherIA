/**
 * GraphRAG Prompt Blocks
 *
 * Reusable prompt fragments for the quality pipeline:
 * - Base synthesis addendum
 * - Philological mode block
 * - Insufficiency/fallback block
 * - Targeted repair prompt template
 */

/**
 * Addendum appended to the base synthesis prompt when quality pipeline is active.
 * Instructs the LLM to use internal nodeId anchors and defer final citation formatting.
 */
export const BASE_SYNTHESIS_ADDENDUM = `
ADDITIONAL QUALITY REQUIREMENTS:
- Ground every substantive claim in provided sources only.
- Keep internal source IDs (nodeId) attached to each claim using [Source N] markers.
- Do not output final numeric citations yet — the system will format them.
- If evidence is insufficient for a claim, state that explicitly rather than speculating.
- Distinguish clearly between what ancient sources say, how modern scholars interpret them, and your own synthesis.
`;

/**
 * Philological mode prompt block. Activates structured close-reading output.
 */
export const PHILOLOGICAL_MODE_BLOCK = `
PHILOLOGICAL MODE — ACTIVATED

Adopt a rigorous philological method. Your answer MUST contain these sections:

## 1. Textual Evidence
- Exact quotation from the provided context only
- Include original Greek/Latin with translation
- NEVER reconstruct Greek/Latin from memory

## 2. Grammatical Exegesis
- Key lemma, morphological form, and syntactic role for crucial terms
- Note any textual variants if available in the context

## 3. Rhetorical Exegesis
- Function in context: is this an objection, refutation, prosopopoiia, diatribe, syllogism, etc.?
- Identify the argumentative structure

## 4. Doctrinal / Argumentative Conclusion
- Premise-conclusion mapping
- State confidence level for each inference

## 5. Limits of Evidence
- Explicitly state what the available textual evidence does NOT address
- Note if direct textual support is missing for any major claim
- Separate well-attested claims from scholarly interpretation

CRITICAL: If a text is not available in the provided context, do NOT reconstruct it. State "No passage in the database directly addresses this point."
`;

/**
 * Insufficiency/fallback block appended when evidence is too sparse.
 */
export const INSUFFICIENCY_BLOCK = `
IMPORTANT: The available evidence may be insufficient to fully answer this question.
Please:
1. Clearly state what CAN be established from the available sources
2. Explicitly note what evidence is MISSING
3. Do not speculate beyond what the sources support
4. Suggest what additional primary sources might be relevant
`;

/**
 * Repair prompt template for targeted self-RAG correction of unsupported claims.
 * Placeholders: {{CLAIM_TEXT}}, {{SOURCE_CONTEXT}}
 */
export const REPAIR_PROMPT_TEMPLATE = `You are a scholarly fact-checker for ancient philosophy.

ORIGINAL CLAIM:
{{CLAIM_TEXT}}

CITED SOURCES:
{{SOURCE_CONTEXT}}

TASK: Rewrite ONLY this claim so it is fully supported by the cited sources above.

RULES:
- No new facts beyond what is in the cited sources
- No new source references
- Keep existing citation markers [N] if the sources support the claim
- If the claim cannot be supported at all, respond with exactly: REMOVE

Respond with JSON:
{
  "action": "rewrite" or "REMOVE",
  "rewritten_claim": "the corrected claim text (only if action=rewrite)",
  "source_node_ids": ["nodeId1", "nodeId2"]
}`;
