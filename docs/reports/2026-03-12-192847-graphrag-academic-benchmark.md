# GraphRAG Academic Benchmark - 2026-03-12T19:22:34Z

- Cases: 4
- Passed: 0
- Failed: 4
- Prefer cloud Qdrant: True

| Case | Category | Pass | Query Type | Badge | Citations | Provider | Model | Issues |
| --- | --- | --- | --- | --- | ---: | --- | --- | --- |
| doctrinal_stoics | doctrinal | no | global_abstract | Low | 8 | gemini | gemini-3.1-pro-preview | pipeline_degraded |
| comparative_stoic_epicurean | comparative | no | comparative | Low | 8 | gemini | gemini-3.1-pro-preview | pipeline_degraded |
| philology_alexander_de_fato_1 | philological | no | global_abstract | High | 1 | gemini | gemini-3.1-pro-preview | missing_greek, translation_not_detected |
| insufficient_parmenides_liberum_arbitrium | insufficiency | no | global_abstract | High | 2 | gemini | gemini-3.1-pro-preview | insufficiency_not_triggered |

## Notes

### doctrinal_stoics
- Query: What did the Stoics believe about fate and moral responsibility?
- Passed: no
- Issues: pipeline_degraded

### comparative_stoic_epicurean
- Query: Compare Stoic and Epicurean views on determinism and free choice.
- Passed: no
- Issues: pipeline_degraded

### philology_alexander_de_fato_1
- Query: Quote Alexander of Aphrodisias, De Fato 1 in Greek and English.
- Passed: no
- Issues: missing_greek, translation_not_detected

### insufficient_parmenides_liberum_arbitrium
- Query: Quote a passage where Parmenides uses the phrase liberum arbitrium.
- Passed: no
- Issues: insufficiency_not_triggered

