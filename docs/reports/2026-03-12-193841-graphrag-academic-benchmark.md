# GraphRAG Academic Benchmark - 2026-03-12T19:33:01Z

- Cases: 4
- Passed: 2
- Failed: 2
- Prefer cloud Qdrant: True

| Case | Category | Pass | Query Type | Badge | Citations | Provider | Model | Issues |
| --- | --- | --- | --- | --- | ---: | --- | --- | --- |
| doctrinal_stoics | doctrinal | no | global_abstract | Low | 8 | gemini | gemini-3.1-pro-preview | pipeline_degraded |
| comparative_stoic_epicurean | comparative | yes | comparative | High | 13 | gemini | gemini-3.1-pro-preview | - |
| philology_alexander_de_fato_1 | philological | no | global_abstract | High | 1 | gemini | gemini-3.1-pro-preview | missing_greek, translation_not_detected |
| insufficient_parmenides_liberum_arbitrium | insufficiency | yes | global_abstract | Low | 3 | gemini | gemini-3.1-pro-preview | - |

## Notes

### doctrinal_stoics
- Query: What did the Stoics believe about fate and moral responsibility?
- Passed: no
- Issues: pipeline_degraded

### comparative_stoic_epicurean
- Query: Compare Stoic and Epicurean views on determinism and free choice.
- Passed: yes
- Issues: none

### philology_alexander_de_fato_1
- Query: Quote Alexander of Aphrodisias, De Fato 1 in Greek and English.
- Passed: no
- Issues: missing_greek, translation_not_detected

### insufficient_parmenides_liberum_arbitrium
- Query: Quote a passage where Parmenides uses the phrase liberum arbitrium.
- Passed: yes
- Issues: none

