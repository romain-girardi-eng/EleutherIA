# Academic Integrity Policy

EleutherIA is a scholarly database of ancient philosophical texts. Its value
rests entirely on the authenticity of the Greek and Latin it serves. This
document states the project's integrity rules and the automated gates that
enforce them.

## Ancient Text Authenticity Policy

**Zero tolerance for fabrication.** Composed, reconstructed, or paraphrased
ancient Greek or Latin presented as a source text is academic fraud, whatever
tool or person produced it.

The following are prohibited everywhere in the project — database records,
knowledge-graph nodes, documentation, API responses, and generated answers:

1. Composing or fabricating ancient Greek or Latin text
2. Reconstructing what an ancient author "might have said"
3. Paraphrasing ancient sources in Greek or Latin
4. Translating modern ideas into ancient languages
5. Completing fragmentary quotations with plausible-sounding text

### Required instead

1. Quote only text that exists in the corpus (`passages` table) or in a
   verifiable critical edition
2. Attribute every quotation with a CTS URN or `passage_id`
3. Preserve the exact original text, including polytonic diacritics
4. When no verifiable source text is available, paraphrase in English and
   say so

**The golden rule: if it is not in the database with a verifiable source, it
does not exist. Use English instead.**

## Ancient loci and modern page references

For ancient texts, an exact conventional reference (author, work, book/chapter/
section, fragment number, Bekker or Stephanus reference) is sufficient citation.
A missing printed or PDF page is not evidence of inauthenticity. The edition and
witness identify the wording used and any variants; they do not replace the
conventional locus. Another edition of the same locus may be checked against its
own retrieved text, while a different work or passage cannot silently substitute
for it. Actual uncertainty about authorship, work identity or contaminated text
must be stated separately from a pagination issue.

For modern scholarship, page references usually locate specific claims and
quotations; a stable section or equivalent locator is appropriate for unpaginated
publications. Unverified file offsets must never be presented as printed pages.

## Source standards

- Ancient texts are ingested from **critical editions only** (Sources
  Chrétiennes, GCS, CCSL, PTS, Bibliotheca Teubneriana, Loeb, Migne PG/PL as
  a fallback) — never from uncontrolled web transcriptions or manuscripts.
- Every passage carries edition provenance and a SHA-256 tamper-evidence
  hash.
- Knowledge-graph claims cite primary sources or modern scholarship with
  confidence scores (0.0–1.0); citation records link to anchored passages.

## Enforcement gates

These checks run in pre-commit and CI; a failure blocks the commit or merge:

| Gate | Script | What it blocks |
|------|--------|----------------|
| Greek attestation gate | `scripts/check_greek_gate.py` | Greek strings in the KG that are not attested in the corpus or a registered edition |
| Citation gate | `scripts/check_citations_gate.py` | Bibliographic references that fail verification against the registry |
| SHACL invariants | `scripts/validate_kg_shacl.py` | Structural violations of the ontology (dangling edges, type mismatches) |
| Golden evaluation harness | CI (`fabrication must-never-appear` suite) | Known past fabrications reappearing in generated answers |

At answer time, the GraphRAG pipeline enforces a deterministic quote-fidelity
gate: every quoted ancient-language span is verified verbatim against the
cited passage before the answer is released.

## Reporting a problem

If you find a passage, node, or citation you believe is fabricated,
misattributed, or textually corrupt, please open a GitHub issue with the
node/passage ID and the edition you checked against. Every report is triaged
item by item; bulk automated "fixes" are deliberately avoided.
