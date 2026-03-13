# Passages Needing English Translation

## Why translate?

GraphRAG embeds queries in English and matches them against KG node descriptions via semantic search (Qdrant vectors).
When a passage is stored only in Greek or Latin, the embedding similarity between an English query and the ancient-language text is poor.
An English translation node (`{node_id}_en`) linked via `translation_of` gives GraphRAG a high-quality semantic match,
while the original-language node preserves the authentic source text for citation.

## Summary

- **Passages needing translation:** 9,856
- **Already translated (_en nodes):** 2,815
- **Total source characters:** 9,779,755 (~9,779k)
- **Works:** 49

### By language

| Language | Passages | Characters |
|----------|----------|------------|
| Greek | 6,695 | 7,546,269 |
| Latin | 3,161 | 2,233,486 |

## Works

### Seneca — Epistulae Morales ad Lucilium

- **Language:** Latin
- **Passages:** 2135
- **Characters:** 800,836
- **Canonical ID:** `urn:cts:latinLit:phi1017.phi015`

| node_id | label | chars |
|---------|-------|-------|
| `passage_sen_ep_1_1_1` | Seneca, Epistulae Morales ad Lucilium, 1.1 | 413 |
| `passage_sen_ep_1_1_2` | Seneca, Epistulae Morales ad Lucilium, 1.2 | 393 |
| `passage_sen_ep_1_1_3` | Seneca, Epistulae Morales ad Lucilium, 1.3 | 403 |
| `passage_sen_ep_1_1_4` | Seneca, Epistulae Morales ad Lucilium, 1.4 | 370 |
| `passage_sen_ep_1_1_5` | Seneca, Epistulae Morales ad Lucilium, 1.5 | 251 |
| `passage_sen_ep_1_10_1` | Seneca, Epistulae Morales ad Lucilium, 10.1 | 475 |
| `passage_sen_ep_1_10_2` | Seneca, Epistulae Morales ad Lucilium, 10.2 | 607 |
| `passage_sen_ep_1_10_3` | Seneca, Epistulae Morales ad Lucilium, 10.3 | 239 |
| `passage_sen_ep_1_10_4` | Seneca, Epistulae Morales ad Lucilium, 10.4 | 283 |
| `passage_sen_ep_1_10_5` | Seneca, Epistulae Morales ad Lucilium, 10.5 | 517 |
| `passage_sen_ep_1_11_1` | Seneca, Epistulae Morales ad Lucilium, 11.1 | 591 |
| `passage_sen_ep_1_11_10` | Seneca, Epistulae Morales ad Lucilium, 11.10 | 340 |
| `passage_sen_ep_1_11_2` | Seneca, Epistulae Morales ad Lucilium, 11.2 | 333 |
| `passage_sen_ep_1_11_3` | Seneca, Epistulae Morales ad Lucilium, 11.3 | 295 |
| `passage_sen_ep_1_11_4` | Seneca, Epistulae Morales ad Lucilium, 11.4 | 253 |
| `passage_sen_ep_1_11_5` | Seneca, Epistulae Morales ad Lucilium, 11.5 | 242 |
| `passage_sen_ep_1_11_6` | Seneca, Epistulae Morales ad Lucilium, 11.6 | 273 |
| `passage_sen_ep_1_11_7` | Seneca, Epistulae Morales ad Lucilium, 11.7 | 403 |
| `passage_sen_ep_1_11_8` | Seneca, Epistulae Morales ad Lucilium, 11.8 | 249 |
| `passage_sen_ep_1_11_9` | Seneca, Epistulae Morales ad Lucilium, 11.9 | 459 |
| `passage_sen_ep_1_12_1` | Seneca, Epistulae Morales ad Lucilium, 12.1 | 317 |
| `passage_sen_ep_1_12_10` | Seneca, Epistulae Morales ad Lucilium, 12.10 | 464 |
| `passage_sen_ep_1_12_11` | Seneca, Epistulae Morales ad Lucilium, 12.11 | 228 |
| `passage_sen_ep_1_12_2` | Seneca, Epistulae Morales ad Lucilium, 12.2 | 419 |
| `passage_sen_ep_1_12_3` | Seneca, Epistulae Morales ad Lucilium, 12.3 | 454 |
| `passage_sen_ep_1_12_4` | Seneca, Epistulae Morales ad Lucilium, 12.4 | 316 |
| `passage_sen_ep_1_12_5` | Seneca, Epistulae Morales ad Lucilium, 12.5 | 309 |
| `passage_sen_ep_1_12_6` | Seneca, Epistulae Morales ad Lucilium, 12.6 | 700 |
| `passage_sen_ep_1_12_7` | Seneca, Epistulae Morales ad Lucilium, 12.7 | 533 |
| `passage_sen_ep_1_12_8` | Seneca, Epistulae Morales ad Lucilium, 12.8 | 295 |
| `passage_sen_ep_1_12_9` | Seneca, Epistulae Morales ad Lucilium, 12.9 | 323 |
| `passage_sen_ep_1_2_1` | Seneca, Epistulae Morales ad Lucilium, 2.1 | 236 |
| `passage_sen_ep_1_2_2` | Seneca, Epistulae Morales ad Lucilium, 2.2 | 462 |
| `passage_sen_ep_1_2_3` | Seneca, Epistulae Morales ad Lucilium, 2.3 | 399 |
| `passage_sen_ep_1_2_4` | Seneca, Epistulae Morales ad Lucilium, 2.4 | 422 |
| `passage_sen_ep_1_2_5` | Seneca, Epistulae Morales ad Lucilium, 2.5 | 206 |
| `passage_sen_ep_1_2_6` | Seneca, Epistulae Morales ad Lucilium, 2.6 | 395 |
| `passage_sen_ep_1_3_1` | Seneca, Epistulae Morales ad Lucilium, 3.1 | 425 |
| `passage_sen_ep_1_3_2` | Seneca, Epistulae Morales ad Lucilium, 3.2 | 521 |
| `passage_sen_ep_1_3_3` | Seneca, Epistulae Morales ad Lucilium, 3.3 | 432 |
| `passage_sen_ep_1_3_4` | Seneca, Epistulae Morales ad Lucilium, 3.4 | 467 |
| `passage_sen_ep_1_3_5` | Seneca, Epistulae Morales ad Lucilium, 3.5 | 164 |
| `passage_sen_ep_1_3_6` | Seneca, Epistulae Morales ad Lucilium, 3.6 | 299 |
| `passage_sen_ep_1_4_1` | Seneca, Epistulae Morales ad Lucilium, 4.1 | 259 |
| `passage_sen_ep_1_4_10` | Seneca, Epistulae Morales ad Lucilium, 4.10 | 506 |
| `passage_sen_ep_1_4_11` | Seneca, Epistulae Morales ad Lucilium, 4.11 | 207 |
| `passage_sen_ep_1_4_2` | Seneca, Epistulae Morales ad Lucilium, 4.2 | 427 |
| `passage_sen_ep_1_4_3` | Seneca, Epistulae Morales ad Lucilium, 4.3 | 225 |
| `passage_sen_ep_1_4_4` | Seneca, Epistulae Morales ad Lucilium, 4.4 | 467 |
| `passage_sen_ep_1_4_5` | Seneca, Epistulae Morales ad Lucilium, 4.5 | 253 |
| `passage_sen_ep_1_4_6` | Seneca, Epistulae Morales ad Lucilium, 4.6 | 318 |
| `passage_sen_ep_1_4_7` | Seneca, Epistulae Morales ad Lucilium, 4.7 | 363 |
| `passage_sen_ep_1_4_8` | Seneca, Epistulae Morales ad Lucilium, 4.8 | 440 |
| `passage_sen_ep_1_4_9` | Seneca, Epistulae Morales ad Lucilium, 4.9 | 329 |
| `passage_sen_ep_1_5_1` | Seneca, Epistulae Morales ad Lucilium, 5.1 | 305 |
| `passage_sen_ep_1_5_2` | Seneca, Epistulae Morales ad Lucilium, 5.2 | 361 |
| `passage_sen_ep_1_5_3` | Seneca, Epistulae Morales ad Lucilium, 5.3 | 392 |
| `passage_sen_ep_1_5_4` | Seneca, Epistulae Morales ad Lucilium, 5.4 | 416 |
| `passage_sen_ep_1_5_5` | Seneca, Epistulae Morales ad Lucilium, 5.5 | 309 |
| `passage_sen_ep_1_5_6` | Seneca, Epistulae Morales ad Lucilium, 5.6 | 392 |
| `passage_sen_ep_1_5_7` | Seneca, Epistulae Morales ad Lucilium, 5.7 | 524 |
| `passage_sen_ep_1_5_8` | Seneca, Epistulae Morales ad Lucilium, 5.8 | 184 |
| `passage_sen_ep_1_5_9` | Seneca, Epistulae Morales ad Lucilium, 5.9 | 242 |
| `passage_sen_ep_1_6_1` | Seneca, Epistulae Morales ad Lucilium, 6.1 | 376 |
| `passage_sen_ep_1_6_2` | Seneca, Epistulae Morales ad Lucilium, 6.2 | 249 |
| `passage_sen_ep_1_6_3` | Seneca, Epistulae Morales ad Lucilium, 6.3 | 309 |
| `passage_sen_ep_1_6_4` | Seneca, Epistulae Morales ad Lucilium, 6.4 | 371 |
| `passage_sen_ep_1_6_5` | Seneca, Epistulae Morales ad Lucilium, 6.5 | 387 |
| `passage_sen_ep_1_6_6` | Seneca, Epistulae Morales ad Lucilium, 6.6 | 451 |
| `passage_sen_ep_1_6_7` | Seneca, Epistulae Morales ad Lucilium, 6.7 | 234 |
| `passage_sen_ep_1_7_1` | Seneca, Epistulae Morales ad Lucilium, 7.1 | 400 |
| `passage_sen_ep_1_7_10` | Seneca, Epistulae Morales ad Lucilium, 7.10 | 258 |
| `passage_sen_ep_1_7_11` | Seneca, Epistulae Morales ad Lucilium, 7.11 | 391 |
| `passage_sen_ep_1_7_12` | Seneca, Epistulae Morales ad Lucilium, 7.12 | 218 |
| `passage_sen_ep_1_7_2` | Seneca, Epistulae Morales ad Lucilium, 7.2 | 308 |
| `passage_sen_ep_1_7_3` | Seneca, Epistulae Morales ad Lucilium, 7.3 | 451 |
| `passage_sen_ep_1_7_4` | Seneca, Epistulae Morales ad Lucilium, 7.4 | 414 |
| `passage_sen_ep_1_7_5` | Seneca, Epistulae Morales ad Lucilium, 7.5 | 590 |
| `passage_sen_ep_1_7_6` | Seneca, Epistulae Morales ad Lucilium, 7.6 | 282 |
| `passage_sen_ep_1_7_7` | Seneca, Epistulae Morales ad Lucilium, 7.7 | 319 |
| `passage_sen_ep_1_7_8` | Seneca, Epistulae Morales ad Lucilium, 7.8 | 295 |
| `passage_sen_ep_1_7_9` | Seneca, Epistulae Morales ad Lucilium, 7.9 | 395 |
| `passage_sen_ep_1_8_1` | Seneca, Epistulae Morales ad Lucilium, 8.1 | 392 |
| `passage_sen_ep_1_8_10` | Seneca, Epistulae Morales ad Lucilium, 8.10 | 156 |
| `passage_sen_ep_1_8_2` | Seneca, Epistulae Morales ad Lucilium, 8.2 | 330 |
| `passage_sen_ep_1_8_3` | Seneca, Epistulae Morales ad Lucilium, 8.3 | 451 |
| `passage_sen_ep_1_8_4` | Seneca, Epistulae Morales ad Lucilium, 8.4 | 231 |
| `passage_sen_ep_1_8_5` | Seneca, Epistulae Morales ad Lucilium, 8.5 | 543 |
| `passage_sen_ep_1_8_6` | Seneca, Epistulae Morales ad Lucilium, 8.6 | 299 |
| `passage_sen_ep_1_8_7` | Seneca, Epistulae Morales ad Lucilium, 8.7 | 360 |
| `passage_sen_ep_1_8_8` | Seneca, Epistulae Morales ad Lucilium, 8.8 | 492 |
| `passage_sen_ep_1_8_9` | Seneca, Epistulae Morales ad Lucilium, 8.9 | 139 |
| `passage_sen_ep_1_9_1` | Seneca, Epistulae Morales ad Lucilium, 9.1 | 238 |
| `passage_sen_ep_1_9_10` | Seneca, Epistulae Morales ad Lucilium, 9.10 | 237 |
| `passage_sen_ep_1_9_11` | Seneca, Epistulae Morales ad Lucilium, 9.11 | 349 |
| `passage_sen_ep_1_9_12` | Seneca, Epistulae Morales ad Lucilium, 9.12 | 392 |
| `passage_sen_ep_1_9_13` | Seneca, Epistulae Morales ad Lucilium, 9.13 | 356 |
| `passage_sen_ep_1_9_14` | Seneca, Epistulae Morales ad Lucilium, 9.14 | 349 |
| `passage_sen_ep_1_9_15` | Seneca, Epistulae Morales ad Lucilium, 9.15 | 293 |
| `passage_sen_ep_1_9_16` | Seneca, Epistulae Morales ad Lucilium, 9.16 | 387 |
| `passage_sen_ep_1_9_17` | Seneca, Epistulae Morales ad Lucilium, 9.17 | 499 |
| `passage_sen_ep_1_9_18` | Seneca, Epistulae Morales ad Lucilium, 9.18 | 433 |
| `passage_sen_ep_1_9_19` | Seneca, Epistulae Morales ad Lucilium, 9.19 | 599 |
| `passage_sen_ep_1_9_2` | Seneca, Epistulae Morales ad Lucilium, 9.2 | 371 |
| `passage_sen_ep_1_9_20` | Seneca, Epistulae Morales ad Lucilium, 9.20 | 443 |
| `passage_sen_ep_1_9_21` | Seneca, Epistulae Morales ad Lucilium, 9.21 | 163 |
| `passage_sen_ep_1_9_22` | Seneca, Epistulae Morales ad Lucilium, 9.22 | 362 |
| `passage_sen_ep_1_9_3` | Seneca, Epistulae Morales ad Lucilium, 9.3 | 274 |
| `passage_sen_ep_1_9_4` | Seneca, Epistulae Morales ad Lucilium, 9.4 | 309 |
| `passage_sen_ep_1_9_5` | Seneca, Epistulae Morales ad Lucilium, 9.5 | 352 |
| `passage_sen_ep_1_9_6` | Seneca, Epistulae Morales ad Lucilium, 9.6 | 402 |
| `passage_sen_ep_1_9_7` | Seneca, Epistulae Morales ad Lucilium, 9.7 | 504 |
| `passage_sen_ep_1_9_8` | Seneca, Epistulae Morales ad Lucilium, 9.8 | 573 |
| `passage_sen_ep_1_9_9` | Seneca, Epistulae Morales ad Lucilium, 9.9 | 525 |
| `passage_sen_ep_10_81_1` | Seneca, Epistulae Morales ad Lucilium, 81.1 | 440 |
| `passage_sen_ep_10_81_10` | Seneca, Epistulae Morales ad Lucilium, 81.10 | 386 |
| `passage_sen_ep_10_81_11` | Seneca, Epistulae Morales ad Lucilium, 81.11 | 390 |
| `passage_sen_ep_10_81_12` | Seneca, Epistulae Morales ad Lucilium, 81.12 | 367 |
| `passage_sen_ep_10_81_13` | Seneca, Epistulae Morales ad Lucilium, 81.13 | 320 |
| `passage_sen_ep_10_81_14` | Seneca, Epistulae Morales ad Lucilium, 81.14 | 473 |
| `passage_sen_ep_10_81_15` | Seneca, Epistulae Morales ad Lucilium, 81.15 | 202 |
| `passage_sen_ep_10_81_16` | Seneca, Epistulae Morales ad Lucilium, 81.16 | 411 |
| `passage_sen_ep_10_81_17` | Seneca, Epistulae Morales ad Lucilium, 81.17 | 435 |
| `passage_sen_ep_10_81_18` | Seneca, Epistulae Morales ad Lucilium, 81.18 | 336 |
| `passage_sen_ep_10_81_19` | Seneca, Epistulae Morales ad Lucilium, 81.19 | 585 |
| `passage_sen_ep_10_81_2` | Seneca, Epistulae Morales ad Lucilium, 81.2 | 424 |
| `passage_sen_ep_10_81_20` | Seneca, Epistulae Morales ad Lucilium, 81.20 | 514 |
| `passage_sen_ep_10_81_21` | Seneca, Epistulae Morales ad Lucilium, 81.21 | 526 |
| `passage_sen_ep_10_81_22` | Seneca, Epistulae Morales ad Lucilium, 81.22 | 425 |
| `passage_sen_ep_10_81_23` | Seneca, Epistulae Morales ad Lucilium, 81.23 | 297 |
| `passage_sen_ep_10_81_24` | Seneca, Epistulae Morales ad Lucilium, 81.24 | 278 |
| `passage_sen_ep_10_81_25` | Seneca, Epistulae Morales ad Lucilium, 81.25 | 564 |
| `passage_sen_ep_10_81_26` | Seneca, Epistulae Morales ad Lucilium, 81.26 | 265 |
| `passage_sen_ep_10_81_27` | Seneca, Epistulae Morales ad Lucilium, 81.27 | 244 |
| `passage_sen_ep_10_81_28` | Seneca, Epistulae Morales ad Lucilium, 81.28 | 369 |
| `passage_sen_ep_10_81_29` | Seneca, Epistulae Morales ad Lucilium, 81.29 | 355 |
| `passage_sen_ep_10_81_3` | Seneca, Epistulae Morales ad Lucilium, 81.3 | 313 |
| `passage_sen_ep_10_81_30` | Seneca, Epistulae Morales ad Lucilium, 81.30 | 206 |
| `passage_sen_ep_10_81_31` | Seneca, Epistulae Morales ad Lucilium, 81.31 | 556 |
| `passage_sen_ep_10_81_32` | Seneca, Epistulae Morales ad Lucilium, 81.32 | 288 |
| `passage_sen_ep_10_81_4` | Seneca, Epistulae Morales ad Lucilium, 81.4 | 241 |
| `passage_sen_ep_10_81_5` | Seneca, Epistulae Morales ad Lucilium, 81.5 | 251 |
| `passage_sen_ep_10_81_6` | Seneca, Epistulae Morales ad Lucilium, 81.6 | 405 |
| `passage_sen_ep_10_81_7` | Seneca, Epistulae Morales ad Lucilium, 81.7 | 363 |
| `passage_sen_ep_10_81_8` | Seneca, Epistulae Morales ad Lucilium, 81.8 | 486 |
| `passage_sen_ep_10_81_9` | Seneca, Epistulae Morales ad Lucilium, 81.9 | 451 |
| `passage_sen_ep_10_82_1` | Seneca, Epistulae Morales ad Lucilium, 82.1 | 345 |
| `passage_sen_ep_10_82_10` | Seneca, Epistulae Morales ad Lucilium, 82.10 | 558 |
| `passage_sen_ep_10_82_11` | Seneca, Epistulae Morales ad Lucilium, 82.11 | 340 |
| `passage_sen_ep_10_82_12` | Seneca, Epistulae Morales ad Lucilium, 82.12 | 636 |
| `passage_sen_ep_10_82_13` | Seneca, Epistulae Morales ad Lucilium, 82.13 | 237 |
| `passage_sen_ep_10_82_14` | Seneca, Epistulae Morales ad Lucilium, 82.14 | 475 |
| `passage_sen_ep_10_82_15` | Seneca, Epistulae Morales ad Lucilium, 82.15 | 611 |
| `passage_sen_ep_10_82_16` | Seneca, Epistulae Morales ad Lucilium, 82.16 | 635 |
| `passage_sen_ep_10_82_17` | Seneca, Epistulae Morales ad Lucilium, 82.17 | 455 |
| `passage_sen_ep_10_82_18` | Seneca, Epistulae Morales ad Lucilium, 82.18 | 501 |
| `passage_sen_ep_10_82_19` | Seneca, Epistulae Morales ad Lucilium, 82.19 | 570 |
| `passage_sen_ep_10_82_2` | Seneca, Epistulae Morales ad Lucilium, 82.2 | 477 |
| `passage_sen_ep_10_82_20` | Seneca, Epistulae Morales ad Lucilium, 82.20 | 406 |
| `passage_sen_ep_10_82_21` | Seneca, Epistulae Morales ad Lucilium, 82.21 | 543 |
| `passage_sen_ep_10_82_22` | Seneca, Epistulae Morales ad Lucilium, 82.22 | 452 |
| `passage_sen_ep_10_82_23` | Seneca, Epistulae Morales ad Lucilium, 82.23 | 493 |
| `passage_sen_ep_10_82_24` | Seneca, Epistulae Morales ad Lucilium, 82.24 | 475 |
| `passage_sen_ep_10_82_3` | Seneca, Epistulae Morales ad Lucilium, 82.3 | 280 |
| `passage_sen_ep_10_82_4` | Seneca, Epistulae Morales ad Lucilium, 82.4 | 396 |
| `passage_sen_ep_10_82_5` | Seneca, Epistulae Morales ad Lucilium, 82.5 | 296 |
| `passage_sen_ep_10_82_6` | Seneca, Epistulae Morales ad Lucilium, 82.6 | 308 |
| `passage_sen_ep_10_82_7` | Seneca, Epistulae Morales ad Lucilium, 82.7 | 385 |
| `passage_sen_ep_10_82_8` | Seneca, Epistulae Morales ad Lucilium, 82.8 | 329 |
| `passage_sen_ep_10_82_9` | Seneca, Epistulae Morales ad Lucilium, 82.9 | 421 |
| `passage_sen_ep_10_83_1` | Seneca, Epistulae Morales ad Lucilium, 83.1 | 441 |
| `passage_sen_ep_10_83_10` | Seneca, Epistulae Morales ad Lucilium, 83.10 | 304 |
| `passage_sen_ep_10_83_11` | Seneca, Epistulae Morales ad Lucilium, 83.11 | 639 |
| `passage_sen_ep_10_83_12` | Seneca, Epistulae Morales ad Lucilium, 83.12 | 525 |
| `passage_sen_ep_10_83_13` | Seneca, Epistulae Morales ad Lucilium, 83.13 | 225 |
| `passage_sen_ep_10_83_14` | Seneca, Epistulae Morales ad Lucilium, 83.14 | 435 |
| `passage_sen_ep_10_83_15` | Seneca, Epistulae Morales ad Lucilium, 83.15 | 396 |
| `passage_sen_ep_10_83_16` | Seneca, Epistulae Morales ad Lucilium, 83.16 | 422 |
| `passage_sen_ep_10_83_17` | Seneca, Epistulae Morales ad Lucilium, 83.17 | 501 |
| `passage_sen_ep_10_83_18` | Seneca, Epistulae Morales ad Lucilium, 83.18 | 445 |
| `passage_sen_ep_10_83_19` | Seneca, Epistulae Morales ad Lucilium, 83.19 | 356 |
| `passage_sen_ep_10_83_2` | Seneca, Epistulae Morales ad Lucilium, 83.2 | 275 |
| `passage_sen_ep_10_83_20` | Seneca, Epistulae Morales ad Lucilium, 83.20 | 380 |
| `passage_sen_ep_10_83_21` | Seneca, Epistulae Morales ad Lucilium, 83.21 | 407 |
| `passage_sen_ep_10_83_22` | Seneca, Epistulae Morales ad Lucilium, 83.22 | 265 |
| `passage_sen_ep_10_83_23` | Seneca, Epistulae Morales ad Lucilium, 83.23 | 267 |
| `passage_sen_ep_10_83_24` | Seneca, Epistulae Morales ad Lucilium, 83.24 | 240 |
| `passage_sen_ep_10_83_25` | Seneca, Epistulae Morales ad Lucilium, 83.25 | 560 |
| `passage_sen_ep_10_83_26` | Seneca, Epistulae Morales ad Lucilium, 83.26 | 312 |
| `passage_sen_ep_10_83_27` | Seneca, Epistulae Morales ad Lucilium, 83.27 | 712 |
| `passage_sen_ep_10_83_3` | Seneca, Epistulae Morales ad Lucilium, 83.3 | 287 |
| `passage_sen_ep_10_83_4` | Seneca, Epistulae Morales ad Lucilium, 83.4 | 528 |
| `passage_sen_ep_10_83_5` | Seneca, Epistulae Morales ad Lucilium, 83.5 | 527 |
| `passage_sen_ep_10_83_6` | Seneca, Epistulae Morales ad Lucilium, 83.6 | 244 |
| `passage_sen_ep_10_83_7` | Seneca, Epistulae Morales ad Lucilium, 83.7 | 293 |
| `passage_sen_ep_10_83_8` | Seneca, Epistulae Morales ad Lucilium, 83.8 | 241 |
| `passage_sen_ep_10_83_9` | Seneca, Epistulae Morales ad Lucilium, 83.9 | 469 |
| `passage_sen_ep_11_84_1` | Seneca, Epistulae Morales ad Lucilium, 84.1 | 514 |
| `passage_sen_ep_11_84_10` | Seneca, Epistulae Morales ad Lucilium, 84.10 | 477 |
| `passage_sen_ep_11_84_11` | Seneca, Epistulae Morales ad Lucilium, 84.11 | 534 |
| `passage_sen_ep_11_84_12` | Seneca, Epistulae Morales ad Lucilium, 84.12 | 347 |
| `passage_sen_ep_11_84_13` | Seneca, Epistulae Morales ad Lucilium, 84.13 | 369 |
| `passage_sen_ep_11_84_2` | Seneca, Epistulae Morales ad Lucilium, 84.2 | 258 |
| `passage_sen_ep_11_84_3` | Seneca, Epistulae Morales ad Lucilium, 84.3 | 237 |
| `passage_sen_ep_11_84_4` | Seneca, Epistulae Morales ad Lucilium, 84.4 | 711 |
| `passage_sen_ep_11_84_5` | Seneca, Epistulae Morales ad Lucilium, 84.5 | 429 |
| `passage_sen_ep_11_84_6` | Seneca, Epistulae Morales ad Lucilium, 84.6 | 303 |
| `passage_sen_ep_11_84_7` | Seneca, Epistulae Morales ad Lucilium, 84.7 | 339 |
| `passage_sen_ep_11_84_8` | Seneca, Epistulae Morales ad Lucilium, 84.8 | 478 |
| `passage_sen_ep_11_84_9` | Seneca, Epistulae Morales ad Lucilium, 84.9 | 130 |
| `passage_sen_ep_11_85_1` | Seneca, Epistulae Morales ad Lucilium, 85.1 | 493 |
| `passage_sen_ep_11_85_10` | Seneca, Epistulae Morales ad Lucilium, 85.10 | 279 |
| `passage_sen_ep_11_85_11` | Seneca, Epistulae Morales ad Lucilium, 85.11 | 396 |
| `passage_sen_ep_11_85_12` | Seneca, Epistulae Morales ad Lucilium, 85.12 | 353 |
| `passage_sen_ep_11_85_13` | Seneca, Epistulae Morales ad Lucilium, 85.13 | 259 |
| `passage_sen_ep_11_85_14` | Seneca, Epistulae Morales ad Lucilium, 85.14 | 284 |
| `passage_sen_ep_11_85_15` | Seneca, Epistulae Morales ad Lucilium, 85.15 | 315 |
| `passage_sen_ep_11_85_16` | Seneca, Epistulae Morales ad Lucilium, 85.16 | 190 |
| `passage_sen_ep_11_85_17` | Seneca, Epistulae Morales ad Lucilium, 85.17 | 425 |
| `passage_sen_ep_11_85_18` | Seneca, Epistulae Morales ad Lucilium, 85.18 | 503 |
| `passage_sen_ep_11_85_19` | Seneca, Epistulae Morales ad Lucilium, 85.19 | 370 |
| `passage_sen_ep_11_85_2` | Seneca, Epistulae Morales ad Lucilium, 85.2 | 249 |
| `passage_sen_ep_11_85_20` | Seneca, Epistulae Morales ad Lucilium, 85.20 | 516 |
| `passage_sen_ep_11_85_21` | Seneca, Epistulae Morales ad Lucilium, 85.21 | 467 |
| `passage_sen_ep_11_85_22` | Seneca, Epistulae Morales ad Lucilium, 85.22 | 393 |
| `passage_sen_ep_11_85_23` | Seneca, Epistulae Morales ad Lucilium, 85.23 | 364 |
| `passage_sen_ep_11_85_24` | Seneca, Epistulae Morales ad Lucilium, 85.24 | 460 |
| `passage_sen_ep_11_85_25` | Seneca, Epistulae Morales ad Lucilium, 85.25 | 495 |
| `passage_sen_ep_11_85_26` | Seneca, Epistulae Morales ad Lucilium, 85.26 | 307 |
| `passage_sen_ep_11_85_27` | Seneca, Epistulae Morales ad Lucilium, 85.27 | 271 |
| `passage_sen_ep_11_85_28` | Seneca, Epistulae Morales ad Lucilium, 85.28 | 515 |
| `passage_sen_ep_11_85_29` | Seneca, Epistulae Morales ad Lucilium, 85.29 | 461 |
| `passage_sen_ep_11_85_3` | Seneca, Epistulae Morales ad Lucilium, 85.3 | 479 |
| `passage_sen_ep_11_85_30` | Seneca, Epistulae Morales ad Lucilium, 85.30 | 283 |
| `passage_sen_ep_11_85_31` | Seneca, Epistulae Morales ad Lucilium, 85.31 | 411 |
| `passage_sen_ep_11_85_32` | Seneca, Epistulae Morales ad Lucilium, 85.32 | 380 |
| `passage_sen_ep_11_85_33` | Seneca, Epistulae Morales ad Lucilium, 85.33 | 419 |
| `passage_sen_ep_11_85_34` | Seneca, Epistulae Morales ad Lucilium, 85.34 | 413 |
| `passage_sen_ep_11_85_35` | Seneca, Epistulae Morales ad Lucilium, 85.35 | 209 |
| `passage_sen_ep_11_85_36` | Seneca, Epistulae Morales ad Lucilium, 85.36 | 366 |
| `passage_sen_ep_11_85_37` | Seneca, Epistulae Morales ad Lucilium, 85.37 | 238 |
| `passage_sen_ep_11_85_38` | Seneca, Epistulae Morales ad Lucilium, 85.38 | 427 |
| `passage_sen_ep_11_85_39` | Seneca, Epistulae Morales ad Lucilium, 85.39 | 255 |
| `passage_sen_ep_11_85_4` | Seneca, Epistulae Morales ad Lucilium, 85.4 | 608 |
| `passage_sen_ep_11_85_40` | Seneca, Epistulae Morales ad Lucilium, 85.40 | 455 |
| `passage_sen_ep_11_85_41` | Seneca, Epistulae Morales ad Lucilium, 85.41 | 453 |
| `passage_sen_ep_11_85_5` | Seneca, Epistulae Morales ad Lucilium, 85.5 | 363 |
| `passage_sen_ep_11_85_6` | Seneca, Epistulae Morales ad Lucilium, 85.6 | 239 |
| `passage_sen_ep_11_85_7` | Seneca, Epistulae Morales ad Lucilium, 85.7 | 294 |
| `passage_sen_ep_11_85_8` | Seneca, Epistulae Morales ad Lucilium, 85.8 | 448 |
| `passage_sen_ep_11_85_9` | Seneca, Epistulae Morales ad Lucilium, 85.9 | 298 |
| `passage_sen_ep_11_86_1` | Seneca, Epistulae Morales ad Lucilium, 86.1 | 468 |
| `passage_sen_ep_11_86_10` | Seneca, Epistulae Morales ad Lucilium, 86.10 | 524 |
| `passage_sen_ep_11_86_11` | Seneca, Epistulae Morales ad Lucilium, 86.11 | 425 |
| `passage_sen_ep_11_86_12` | Seneca, Epistulae Morales ad Lucilium, 86.12 | 479 |
| `passage_sen_ep_11_86_13` | Seneca, Epistulae Morales ad Lucilium, 86.13 | 323 |
| `passage_sen_ep_11_86_14` | Seneca, Epistulae Morales ad Lucilium, 86.14 | 354 |
| `passage_sen_ep_11_86_15` | Seneca, Epistulae Morales ad Lucilium, 86.15 | 171 |
| `passage_sen_ep_11_86_16` | Seneca, Epistulae Morales ad Lucilium, 86.16 | 282 |
| `passage_sen_ep_11_86_17` | Seneca, Epistulae Morales ad Lucilium, 86.17 | 321 |
| `passage_sen_ep_11_86_18` | Seneca, Epistulae Morales ad Lucilium, 86.18 | 563 |
| `passage_sen_ep_11_86_19` | Seneca, Epistulae Morales ad Lucilium, 86.19 | 230 |
| `passage_sen_ep_11_86_2` | Seneca, Epistulae Morales ad Lucilium, 86.2 | 216 |
| `passage_sen_ep_11_86_20` | Seneca, Epistulae Morales ad Lucilium, 86.20 | 300 |
| `passage_sen_ep_11_86_21` | Seneca, Epistulae Morales ad Lucilium, 86.21 | 262 |
| `passage_sen_ep_11_86_3` | Seneca, Epistulae Morales ad Lucilium, 86.3 | 318 |
| `passage_sen_ep_11_86_4` | Seneca, Epistulae Morales ad Lucilium, 86.4 | 396 |
| `passage_sen_ep_11_86_5` | Seneca, Epistulae Morales ad Lucilium, 86.5 | 278 |
| `passage_sen_ep_11_86_6` | Seneca, Epistulae Morales ad Lucilium, 86.6 | 489 |
| `passage_sen_ep_11_86_7` | Seneca, Epistulae Morales ad Lucilium, 86.7 | 294 |
| `passage_sen_ep_11_86_8` | Seneca, Epistulae Morales ad Lucilium, 86.8 | 502 |
| `passage_sen_ep_11_86_9` | Seneca, Epistulae Morales ad Lucilium, 86.9 | 268 |
| `passage_sen_ep_11_87_1` | Seneca, Epistulae Morales ad Lucilium, 87.1 | 402 |
| `passage_sen_ep_11_87_10` | Seneca, Epistulae Morales ad Lucilium, 87.10 | 327 |
| `passage_sen_ep_11_87_11` | Seneca, Epistulae Morales ad Lucilium, 87.11 | 346 |
| `passage_sen_ep_11_87_12` | Seneca, Epistulae Morales ad Lucilium, 87.12 | 413 |
| `passage_sen_ep_11_87_13` | Seneca, Epistulae Morales ad Lucilium, 87.13 | 262 |
| `passage_sen_ep_11_87_14` | Seneca, Epistulae Morales ad Lucilium, 87.14 | 373 |
| `passage_sen_ep_11_87_15` | Seneca, Epistulae Morales ad Lucilium, 87.15 | 285 |
| `passage_sen_ep_11_87_16` | Seneca, Epistulae Morales ad Lucilium, 87.16 | 583 |
| `passage_sen_ep_11_87_17` | Seneca, Epistulae Morales ad Lucilium, 87.17 | 398 |
| `passage_sen_ep_11_87_18` | Seneca, Epistulae Morales ad Lucilium, 87.18 | 376 |
| `passage_sen_ep_11_87_19` | Seneca, Epistulae Morales ad Lucilium, 87.19 | 313 |
| `passage_sen_ep_11_87_2` | Seneca, Epistulae Morales ad Lucilium, 87.2 | 273 |
| `passage_sen_ep_11_87_21` | Seneca, Epistulae Morales ad Lucilium, 87.21 | 307 |
| `passage_sen_ep_11_87_22` | Seneca, Epistulae Morales ad Lucilium, 87.22 | 361 |
| `passage_sen_ep_11_87_23` | Seneca, Epistulae Morales ad Lucilium, 87.23 | 426 |
| `passage_sen_ep_11_87_24` | Seneca, Epistulae Morales ad Lucilium, 87.24 | 420 |
| `passage_sen_ep_11_87_25` | Seneca, Epistulae Morales ad Lucilium, 87.25 | 333 |
| `passage_sen_ep_11_87_26` | Seneca, Epistulae Morales ad Lucilium, 87.26 | 614 |
| `passage_sen_ep_11_87_27` | Seneca, Epistulae Morales ad Lucilium, 87.27 | 206 |
| `passage_sen_ep_11_87_28` | Seneca, Epistulae Morales ad Lucilium, 87.28 | 422 |
| `passage_sen_ep_11_87_29` | Seneca, Epistulae Morales ad Lucilium, 87.29 | 496 |
| `passage_sen_ep_11_87_3` | Seneca, Epistulae Morales ad Lucilium, 87.3 | 414 |
| `passage_sen_ep_11_87_30` | Seneca, Epistulae Morales ad Lucilium, 87.30 | 275 |
| `passage_sen_ep_11_87_31` | Seneca, Epistulae Morales ad Lucilium, 87.31 | 388 |
| `passage_sen_ep_11_87_32` | Seneca, Epistulae Morales ad Lucilium, 87.32 | 313 |
| `passage_sen_ep_11_87_33` | Seneca, Epistulae Morales ad Lucilium, 87.33 | 296 |
| `passage_sen_ep_11_87_34` | Seneca, Epistulae Morales ad Lucilium, 87.34 | 304 |
| `passage_sen_ep_11_87_35` | Seneca, Epistulae Morales ad Lucilium, 87.35 | 454 |
| `passage_sen_ep_11_87_36` | Seneca, Epistulae Morales ad Lucilium, 87.36 | 263 |
| `passage_sen_ep_11_87_37` | Seneca, Epistulae Morales ad Lucilium, 87.37 | 235 |
| `passage_sen_ep_11_87_38` | Seneca, Epistulae Morales ad Lucilium, 87.38 | 447 |
| `passage_sen_ep_11_87_39` | Seneca, Epistulae Morales ad Lucilium, 87.39 | 358 |
| `passage_sen_ep_11_87_4` | Seneca, Epistulae Morales ad Lucilium, 87.4 | 435 |
| `passage_sen_ep_11_87_40` | Seneca, Epistulae Morales ad Lucilium, 87.40 | 439 |
| `passage_sen_ep_11_87_41` | Seneca, Epistulae Morales ad Lucilium, 87.41 | 626 |
| `passage_sen_ep_11_87_5` | Seneca, Epistulae Morales ad Lucilium, 87.5 | 401 |
| `passage_sen_ep_11_87_6` | Seneca, Epistulae Morales ad Lucilium, 87.6 | 284 |
| `passage_sen_ep_11_87_7` | Seneca, Epistulae Morales ad Lucilium, 87.7 | 386 |
| `passage_sen_ep_11_87_8` | Seneca, Epistulae Morales ad Lucilium, 87.8 | 140 |
| `passage_sen_ep_11_87_9` | Seneca, Epistulae Morales ad Lucilium, 87.9 | 498 |
| `passage_sen_ep_11_88_1` | Seneca, Epistulae Morales ad Lucilium, 88.1 | 302 |
| `passage_sen_ep_11_88_10` | Seneca, Epistulae Morales ad Lucilium, 88.10 | 375 |
| `passage_sen_ep_11_88_11` | Seneca, Epistulae Morales ad Lucilium, 88.11 | 343 |
| `passage_sen_ep_11_88_12` | Seneca, Epistulae Morales ad Lucilium, 88.12 | 362 |
| `passage_sen_ep_11_88_13` | Seneca, Epistulae Morales ad Lucilium, 88.13 | 324 |
| `passage_sen_ep_11_88_14` | Seneca, Epistulae Morales ad Lucilium, 88.14 | 281 |
| `passage_sen_ep_11_88_15` | Seneca, Epistulae Morales ad Lucilium, 88.15 | 465 |
| `passage_sen_ep_11_88_16` | Seneca, Epistulae Morales ad Lucilium, 88.16 | 66 |
| `passage_sen_ep_11_88_17` | Seneca, Epistulae Morales ad Lucilium, 88.17 | 370 |
| `passage_sen_ep_11_88_18` | Seneca, Epistulae Morales ad Lucilium, 88.18 | 511 |
| `passage_sen_ep_11_88_19` | Seneca, Epistulae Morales ad Lucilium, 88.19 | 443 |
| `passage_sen_ep_11_88_2` | Seneca, Epistulae Morales ad Lucilium, 88.2 | 505 |
| `passage_sen_ep_11_88_20` | Seneca, Epistulae Morales ad Lucilium, 88.20 | 578 |
| `passage_sen_ep_11_88_21` | Seneca, Epistulae Morales ad Lucilium, 88.21 | 248 |
| `passage_sen_ep_11_88_22` | Seneca, Epistulae Morales ad Lucilium, 88.22 | 430 |
| `passage_sen_ep_11_88_23` | Seneca, Epistulae Morales ad Lucilium, 88.23 | 203 |
| `passage_sen_ep_11_88_24` | Seneca, Epistulae Morales ad Lucilium, 88.24 | 293 |
| `passage_sen_ep_11_88_25` | Seneca, Epistulae Morales ad Lucilium, 88.25 | 287 |
| `passage_sen_ep_11_88_26` | Seneca, Epistulae Morales ad Lucilium, 88.26 | 403 |
| `passage_sen_ep_11_88_27` | Seneca, Epistulae Morales ad Lucilium, 88.27 | 405 |
| `passage_sen_ep_11_88_28` | Seneca, Epistulae Morales ad Lucilium, 88.28 | 475 |
| `passage_sen_ep_11_88_29` | Seneca, Epistulae Morales ad Lucilium, 88.29 | 698 |
| `passage_sen_ep_11_88_3` | Seneca, Epistulae Morales ad Lucilium, 88.3 | 339 |
| `passage_sen_ep_11_88_30` | Seneca, Epistulae Morales ad Lucilium, 88.30 | 488 |
| `passage_sen_ep_11_88_31` | Seneca, Epistulae Morales ad Lucilium, 88.31 | 357 |
| `passage_sen_ep_11_88_32` | Seneca, Epistulae Morales ad Lucilium, 88.32 | 358 |
| `passage_sen_ep_11_88_33` | Seneca, Epistulae Morales ad Lucilium, 88.33 | 358 |
| `passage_sen_ep_11_88_34` | Seneca, Epistulae Morales ad Lucilium, 88.34 | 492 |
| `passage_sen_ep_11_88_35` | Seneca, Epistulae Morales ad Lucilium, 88.35 | 330 |
| `passage_sen_ep_11_88_36` | Seneca, Epistulae Morales ad Lucilium, 88.36 | 342 |
| `passage_sen_ep_11_88_37` | Seneca, Epistulae Morales ad Lucilium, 88.37 | 460 |
| `passage_sen_ep_11_88_38` | Seneca, Epistulae Morales ad Lucilium, 88.38 | 262 |
| `passage_sen_ep_11_88_39` | Seneca, Epistulae Morales ad Lucilium, 88.39 | 405 |
| `passage_sen_ep_11_88_4` | Seneca, Epistulae Morales ad Lucilium, 88.4 | 254 |
| `passage_sen_ep_11_88_40` | Seneca, Epistulae Morales ad Lucilium, 88.40 | 376 |
| `passage_sen_ep_11_88_41` | Seneca, Epistulae Morales ad Lucilium, 88.41 | 242 |
| `passage_sen_ep_11_88_42` | Seneca, Epistulae Morales ad Lucilium, 88.42 | 369 |
| `passage_sen_ep_11_88_43` | Seneca, Epistulae Morales ad Lucilium, 88.43 | 284 |
| `passage_sen_ep_11_88_44` | Seneca, Epistulae Morales ad Lucilium, 88.44 | 254 |
| `passage_sen_ep_11_88_45` | Seneca, Epistulae Morales ad Lucilium, 88.45 | 451 |
| `passage_sen_ep_11_88_46` | Seneca, Epistulae Morales ad Lucilium, 88.46 | 269 |
| `passage_sen_ep_11_88_5` | Seneca, Epistulae Morales ad Lucilium, 88.5 | 668 |
| `passage_sen_ep_11_88_6` | Seneca, Epistulae Morales ad Lucilium, 88.6 | 258 |
| `passage_sen_ep_11_88_7` | Seneca, Epistulae Morales ad Lucilium, 88.7 | 600 |
| `passage_sen_ep_11_88_8` | Seneca, Epistulae Morales ad Lucilium, 88.8 | 228 |
| `passage_sen_ep_11_88_9` | Seneca, Epistulae Morales ad Lucilium, 88.9 | 319 |
| `passage_sen_ep_14_89_1` | Seneca, Epistulae Morales ad Lucilium, 89.1 | 540 |
| `passage_sen_ep_14_89_10` | Seneca, Epistulae Morales ad Lucilium, 89.10 | 343 |
| `passage_sen_ep_14_89_11` | Seneca, Epistulae Morales ad Lucilium, 89.11 | 338 |
| `passage_sen_ep_14_89_12` | Seneca, Epistulae Morales ad Lucilium, 89.12 | 443 |
| `passage_sen_ep_14_89_13` | Seneca, Epistulae Morales ad Lucilium, 89.13 | 208 |
| `passage_sen_ep_14_89_14` | Seneca, Epistulae Morales ad Lucilium, 89.14 | 530 |
| `passage_sen_ep_14_89_15` | Seneca, Epistulae Morales ad Lucilium, 89.15 | 581 |
| `passage_sen_ep_14_89_16` | Seneca, Epistulae Morales ad Lucilium, 89.16 | 351 |
| `passage_sen_ep_14_89_17` | Seneca, Epistulae Morales ad Lucilium, 89.17 | 487 |
| `passage_sen_ep_14_89_18` | Seneca, Epistulae Morales ad Lucilium, 89.18 | 335 |
| `passage_sen_ep_14_89_19` | Seneca, Epistulae Morales ad Lucilium, 89.19 | 323 |
| `passage_sen_ep_14_89_2` | Seneca, Epistulae Morales ad Lucilium, 89.2 | 438 |
| `passage_sen_ep_14_89_20` | Seneca, Epistulae Morales ad Lucilium, 89.20 | 662 |
| `passage_sen_ep_14_89_21` | Seneca, Epistulae Morales ad Lucilium, 89.21 | 791 |
| `passage_sen_ep_14_89_22` | Seneca, Epistulae Morales ad Lucilium, 89.22 | 550 |
| `passage_sen_ep_14_89_23` | Seneca, Epistulae Morales ad Lucilium, 89.23 | 185 |
| `passage_sen_ep_14_89_3` | Seneca, Epistulae Morales ad Lucilium, 89.3 | 291 |
| `passage_sen_ep_14_89_4` | Seneca, Epistulae Morales ad Lucilium, 89.4 | 287 |
| `passage_sen_ep_14_89_5` | Seneca, Epistulae Morales ad Lucilium, 89.5 | 426 |
| `passage_sen_ep_14_89_6` | Seneca, Epistulae Morales ad Lucilium, 89.6 | 386 |
| `passage_sen_ep_14_89_7` | Seneca, Epistulae Morales ad Lucilium, 89.7 | 155 |
| `passage_sen_ep_14_89_8` | Seneca, Epistulae Morales ad Lucilium, 89.8 | 615 |
| `passage_sen_ep_14_89_9` | Seneca, Epistulae Morales ad Lucilium, 89.9 | 337 |
| `passage_sen_ep_14_90_1` | Seneca, Epistulae Morales ad Lucilium, 90.1 | 320 |
| `passage_sen_ep_14_90_10` | Seneca, Epistulae Morales ad Lucilium, 90.10 | 307 |
| `passage_sen_ep_14_90_11` | Seneca, Epistulae Morales ad Lucilium, 90.11 | 111 |
| `passage_sen_ep_14_90_12` | Seneca, Epistulae Morales ad Lucilium, 90.12 | 199 |
| `passage_sen_ep_14_90_13` | Seneca, Epistulae Morales ad Lucilium, 90.13 | 361 |
| `passage_sen_ep_14_90_14` | Seneca, Epistulae Morales ad Lucilium, 90.14 | 352 |
| `passage_sen_ep_14_90_15` | Seneca, Epistulae Morales ad Lucilium, 90.15 | 697 |
| `passage_sen_ep_14_90_16` | Seneca, Epistulae Morales ad Lucilium, 90.16 | 615 |
| `passage_sen_ep_14_90_17` | Seneca, Epistulae Morales ad Lucilium, 90.17 | 558 |
| `passage_sen_ep_14_90_18` | Seneca, Epistulae Morales ad Lucilium, 90.18 | 679 |
| `passage_sen_ep_14_90_19` | Seneca, Epistulae Morales ad Lucilium, 90.19 | 706 |
| `passage_sen_ep_14_90_2` | Seneca, Epistulae Morales ad Lucilium, 90.2 | 342 |
| `passage_sen_ep_14_90_20` | Seneca, Epistulae Morales ad Lucilium, 90.20 | 720 |
| `passage_sen_ep_14_90_21` | Seneca, Epistulae Morales ad Lucilium, 90.21 | 376 |
| `passage_sen_ep_14_90_22` | Seneca, Epistulae Morales ad Lucilium, 90.22 | 429 |
| `passage_sen_ep_14_90_23` | Seneca, Epistulae Morales ad Lucilium, 90.23 | 522 |
| `passage_sen_ep_14_90_24` | Seneca, Epistulae Morales ad Lucilium, 90.24 | 407 |
| `passage_sen_ep_14_90_25` | Seneca, Epistulae Morales ad Lucilium, 90.25 | 736 |
| `passage_sen_ep_14_90_26` | Seneca, Epistulae Morales ad Lucilium, 90.26 | 343 |
| `passage_sen_ep_14_90_27` | Seneca, Epistulae Morales ad Lucilium, 90.27 | 267 |
| `passage_sen_ep_14_90_28` | Seneca, Epistulae Morales ad Lucilium, 90.28 | 636 |
| `passage_sen_ep_14_90_29` | Seneca, Epistulae Morales ad Lucilium, 90.29 | 387 |
| `passage_sen_ep_14_90_3` | Seneca, Epistulae Morales ad Lucilium, 90.3 | 468 |
| `passage_sen_ep_14_90_30` | Seneca, Epistulae Morales ad Lucilium, 90.30 | 209 |
| `passage_sen_ep_14_90_31` | Seneca, Epistulae Morales ad Lucilium, 90.31 | 743 |
| `passage_sen_ep_14_90_32` | Seneca, Epistulae Morales ad Lucilium, 90.32 | 233 |
| `passage_sen_ep_14_90_33` | Seneca, Epistulae Morales ad Lucilium, 90.33 | 358 |
| `passage_sen_ep_14_90_34` | Seneca, Epistulae Morales ad Lucilium, 90.34 | 556 |
| `passage_sen_ep_14_90_35` | Seneca, Epistulae Morales ad Lucilium, 90.35 | 393 |
| `passage_sen_ep_14_90_36` | Seneca, Epistulae Morales ad Lucilium, 90.36 | 249 |
| `passage_sen_ep_14_90_37` | Seneca, Epistulae Morales ad Lucilium, 90.37 | 357 |
| `passage_sen_ep_14_90_38` | Seneca, Epistulae Morales ad Lucilium, 90.38 | 473 |
| `passage_sen_ep_14_90_39` | Seneca, Epistulae Morales ad Lucilium, 90.39 | 329 |
| `passage_sen_ep_14_90_4` | Seneca, Epistulae Morales ad Lucilium, 90.4 | 626 |
| `passage_sen_ep_14_90_40` | Seneca, Epistulae Morales ad Lucilium, 90.40 | 409 |
| `passage_sen_ep_14_90_41` | Seneca, Epistulae Morales ad Lucilium, 90.41 | 378 |
| `passage_sen_ep_14_90_42` | Seneca, Epistulae Morales ad Lucilium, 90.42 | 332 |
| `passage_sen_ep_14_90_43` | Seneca, Epistulae Morales ad Lucilium, 90.43 | 585 |
| `passage_sen_ep_14_90_44` | Seneca, Epistulae Morales ad Lucilium, 90.44 | 431 |
| `passage_sen_ep_14_90_45` | Seneca, Epistulae Morales ad Lucilium, 90.45 | 294 |
| `passage_sen_ep_14_90_46` | Seneca, Epistulae Morales ad Lucilium, 90.46 | 460 |
| `passage_sen_ep_14_90_5` | Seneca, Epistulae Morales ad Lucilium, 90.5 | 606 |
| `passage_sen_ep_14_90_6` | Seneca, Epistulae Morales ad Lucilium, 90.6 | 492 |
| `passage_sen_ep_14_90_7` | Seneca, Epistulae Morales ad Lucilium, 90.7 | 588 |
| `passage_sen_ep_14_90_8` | Seneca, Epistulae Morales ad Lucilium, 90.8 | 368 |
| `passage_sen_ep_14_90_9` | Seneca, Epistulae Morales ad Lucilium, 90.9 | 358 |
| `passage_sen_ep_14_91_1` | Seneca, Epistulae Morales ad Lucilium, 91.1 | 783 |
| `passage_sen_ep_14_91_10` | Seneca, Epistulae Morales ad Lucilium, 91.10 | 371 |
| `passage_sen_ep_14_91_11` | Seneca, Epistulae Morales ad Lucilium, 91.11 | 415 |
| `passage_sen_ep_14_91_12` | Seneca, Epistulae Morales ad Lucilium, 91.12 | 498 |
| `passage_sen_ep_14_91_13` | Seneca, Epistulae Morales ad Lucilium, 91.13 | 377 |
| `passage_sen_ep_14_91_14` | Seneca, Epistulae Morales ad Lucilium, 91.14 | 396 |
| `passage_sen_ep_14_91_15` | Seneca, Epistulae Morales ad Lucilium, 91.15 | 593 |
| `passage_sen_ep_14_91_16` | Seneca, Epistulae Morales ad Lucilium, 91.16 | 512 |
| `passage_sen_ep_14_91_17` | Seneca, Epistulae Morales ad Lucilium, 91.17 | 496 |
| `passage_sen_ep_14_91_18` | Seneca, Epistulae Morales ad Lucilium, 91.18 | 326 |
| `passage_sen_ep_14_91_19` | Seneca, Epistulae Morales ad Lucilium, 91.19 | 383 |
| `passage_sen_ep_14_91_2` | Seneca, Epistulae Morales ad Lucilium, 91.2 | 536 |
| `passage_sen_ep_14_91_20` | Seneca, Epistulae Morales ad Lucilium, 91.20 | 220 |
| `passage_sen_ep_14_91_21` | Seneca, Epistulae Morales ad Lucilium, 91.21 | 340 |
| `passage_sen_ep_14_91_3` | Seneca, Epistulae Morales ad Lucilium, 91.3 | 238 |
| `passage_sen_ep_14_91_4` | Seneca, Epistulae Morales ad Lucilium, 91.4 | 309 |
| `passage_sen_ep_14_91_5` | Seneca, Epistulae Morales ad Lucilium, 91.5 | 664 |
| `passage_sen_ep_14_91_6` | Seneca, Epistulae Morales ad Lucilium, 91.6 | 377 |
| `passage_sen_ep_14_91_7` | Seneca, Epistulae Morales ad Lucilium, 91.7 | 402 |
| `passage_sen_ep_14_91_8` | Seneca, Epistulae Morales ad Lucilium, 91.8 | 433 |
| `passage_sen_ep_14_91_9` | Seneca, Epistulae Morales ad Lucilium, 91.9 | 429 |
| `passage_sen_ep_14_92_1` | Seneca, Epistulae Morales ad Lucilium, 92.1 | 448 |
| `passage_sen_ep_14_92_10` | Seneca, Epistulae Morales ad Lucilium, 92.10 | 683 |
| `passage_sen_ep_14_92_11` | Seneca, Epistulae Morales ad Lucilium, 92.11 | 365 |
| `passage_sen_ep_14_92_12` | Seneca, Epistulae Morales ad Lucilium, 92.12 | 283 |
| `passage_sen_ep_14_92_13` | Seneca, Epistulae Morales ad Lucilium, 92.13 | 386 |
| `passage_sen_ep_14_92_14` | Seneca, Epistulae Morales ad Lucilium, 92.14 | 286 |
| `passage_sen_ep_14_92_15` | Seneca, Epistulae Morales ad Lucilium, 92.15 | 485 |
| `passage_sen_ep_14_92_16` | Seneca, Epistulae Morales ad Lucilium, 92.16 | 424 |
| `passage_sen_ep_14_92_17` | Seneca, Epistulae Morales ad Lucilium, 92.17 | 440 |
| `passage_sen_ep_14_92_18` | Seneca, Epistulae Morales ad Lucilium, 92.18 | 292 |
| `passage_sen_ep_14_92_19` | Seneca, Epistulae Morales ad Lucilium, 92.19 | 476 |
| `passage_sen_ep_14_92_2` | Seneca, Epistulae Morales ad Lucilium, 92.2 | 575 |
| `passage_sen_ep_14_92_20` | Seneca, Epistulae Morales ad Lucilium, 92.20 | 460 |
| `passage_sen_ep_14_92_21` | Seneca, Epistulae Morales ad Lucilium, 92.21 | 433 |
| `passage_sen_ep_14_92_22` | Seneca, Epistulae Morales ad Lucilium, 92.22 | 256 |
| `passage_sen_ep_14_92_23` | Seneca, Epistulae Morales ad Lucilium, 92.23 | 313 |
| `passage_sen_ep_14_92_24` | Seneca, Epistulae Morales ad Lucilium, 92.24 | 577 |
| `passage_sen_ep_14_92_25` | Seneca, Epistulae Morales ad Lucilium, 92.25 | 601 |
| `passage_sen_ep_14_92_26` | Seneca, Epistulae Morales ad Lucilium, 92.26 | 535 |
| `passage_sen_ep_14_92_27` | Seneca, Epistulae Morales ad Lucilium, 92.27 | 251 |
| `passage_sen_ep_14_92_28` | Seneca, Epistulae Morales ad Lucilium, 92.28 | 320 |
| `passage_sen_ep_14_92_29` | Seneca, Epistulae Morales ad Lucilium, 92.29 | 364 |
| `passage_sen_ep_14_92_3` | Seneca, Epistulae Morales ad Lucilium, 92.3 | 443 |
| `passage_sen_ep_14_92_30` | Seneca, Epistulae Morales ad Lucilium, 92.30 | 544 |
| `passage_sen_ep_14_92_31` | Seneca, Epistulae Morales ad Lucilium, 92.31 | 425 |
| `passage_sen_ep_14_92_32` | Seneca, Epistulae Morales ad Lucilium, 92.32 | 260 |
| `passage_sen_ep_14_92_33` | Seneca, Epistulae Morales ad Lucilium, 92.33 | 293 |
| `passage_sen_ep_14_92_34` | Seneca, Epistulae Morales ad Lucilium, 92.34 | 482 |
| `passage_sen_ep_14_92_35` | Seneca, Epistulae Morales ad Lucilium, 92.35 | 505 |
| `passage_sen_ep_14_92_4` | Seneca, Epistulae Morales ad Lucilium, 92.4 | 248 |
| `passage_sen_ep_14_92_5` | Seneca, Epistulae Morales ad Lucilium, 92.5 | 341 |
| `passage_sen_ep_14_92_6` | Seneca, Epistulae Morales ad Lucilium, 92.6 | 463 |
| `passage_sen_ep_14_92_7` | Seneca, Epistulae Morales ad Lucilium, 92.7 | 219 |
| `passage_sen_ep_14_92_8` | Seneca, Epistulae Morales ad Lucilium, 92.8 | 304 |
| `passage_sen_ep_14_92_9` | Seneca, Epistulae Morales ad Lucilium, 92.9 | 336 |
| `passage_sen_ep_15_100_1` | Seneca, Epistulae Morales ad Lucilium, 100.1 | 576 |
| `passage_sen_ep_15_100_10` | Seneca, Epistulae Morales ad Lucilium, 100.10 | 534 |
| `passage_sen_ep_15_100_11` | Seneca, Epistulae Morales ad Lucilium, 100.11 | 461 |
| `passage_sen_ep_15_100_12` | Seneca, Epistulae Morales ad Lucilium, 100.12 | 559 |
| `passage_sen_ep_15_100_2` | Seneca, Epistulae Morales ad Lucilium, 100.2 | 169 |
| `passage_sen_ep_15_100_3` | Seneca, Epistulae Morales ad Lucilium, 100.3 | 261 |
| `passage_sen_ep_15_100_4` | Seneca, Epistulae Morales ad Lucilium, 100.4 | 262 |
| `passage_sen_ep_15_100_5` | Seneca, Epistulae Morales ad Lucilium, 100.5 | 454 |
| `passage_sen_ep_15_100_6` | Seneca, Epistulae Morales ad Lucilium, 100.6 | 428 |
| `passage_sen_ep_15_100_7` | Seneca, Epistulae Morales ad Lucilium, 100.7 | 429 |
| `passage_sen_ep_15_100_8` | Seneca, Epistulae Morales ad Lucilium, 100.8 | 388 |
| `passage_sen_ep_15_100_9` | Seneca, Epistulae Morales ad Lucilium, 100.9 | 546 |
| `passage_sen_ep_15_93_1` | Seneca, Epistulae Morales ad Lucilium, 93.1 | 442 |
| `passage_sen_ep_15_93_10` | Seneca, Epistulae Morales ad Lucilium, 93.10 | 323 |
| `passage_sen_ep_15_93_11` | Seneca, Epistulae Morales ad Lucilium, 93.11 | 228 |
| `passage_sen_ep_15_93_12` | Seneca, Epistulae Morales ad Lucilium, 93.12 | 415 |
| `passage_sen_ep_15_93_2` | Seneca, Epistulae Morales ad Lucilium, 93.2 | 350 |
| `passage_sen_ep_15_93_3` | Seneca, Epistulae Morales ad Lucilium, 93.3 | 191 |
| `passage_sen_ep_15_93_4` | Seneca, Epistulae Morales ad Lucilium, 93.4 | 678 |
| `passage_sen_ep_15_93_5` | Seneca, Epistulae Morales ad Lucilium, 93.5 | 362 |
| `passage_sen_ep_15_93_6` | Seneca, Epistulae Morales ad Lucilium, 93.6 | 313 |
| `passage_sen_ep_15_93_7` | Seneca, Epistulae Morales ad Lucilium, 93.7 | 315 |
| `passage_sen_ep_15_93_8` | Seneca, Epistulae Morales ad Lucilium, 93.8 | 418 |
| `passage_sen_ep_15_93_9` | Seneca, Epistulae Morales ad Lucilium, 93.9 | 562 |
| `passage_sen_ep_15_94_1` | Seneca, Epistulae Morales ad Lucilium, 94.1 | 394 |
| `passage_sen_ep_15_94_10` | Seneca, Epistulae Morales ad Lucilium, 94.10 | 313 |
| `passage_sen_ep_15_94_11` | Seneca, Epistulae Morales ad Lucilium, 94.11 | 480 |
| `passage_sen_ep_15_94_12` | Seneca, Epistulae Morales ad Lucilium, 94.12 | 335 |
| `passage_sen_ep_15_94_13` | Seneca, Epistulae Morales ad Lucilium, 94.13 | 436 |
| `passage_sen_ep_15_94_14` | Seneca, Epistulae Morales ad Lucilium, 94.14 | 206 |
| `passage_sen_ep_15_94_15` | Seneca, Epistulae Morales ad Lucilium, 94.15 | 454 |
| `passage_sen_ep_15_94_16` | Seneca, Epistulae Morales ad Lucilium, 94.16 | 291 |
| `passage_sen_ep_15_94_17` | Seneca, Epistulae Morales ad Lucilium, 94.17 | 526 |
| `passage_sen_ep_15_94_18` | Seneca, Epistulae Morales ad Lucilium, 94.18 | 381 |
| `passage_sen_ep_15_94_19` | Seneca, Epistulae Morales ad Lucilium, 94.19 | 412 |
| `passage_sen_ep_15_94_2` | Seneca, Epistulae Morales ad Lucilium, 94.2 | 703 |
| `passage_sen_ep_15_94_20` | Seneca, Epistulae Morales ad Lucilium, 94.20 | 401 |
| `passage_sen_ep_15_94_21` | Seneca, Epistulae Morales ad Lucilium, 94.21 | 509 |
| `passage_sen_ep_15_94_22` | Seneca, Epistulae Morales ad Lucilium, 94.22 | 326 |
| `passage_sen_ep_15_94_23` | Seneca, Epistulae Morales ad Lucilium, 94.23 | 501 |
| `passage_sen_ep_15_94_24` | Seneca, Epistulae Morales ad Lucilium, 94.24 | 339 |
| `passage_sen_ep_15_94_25` | Seneca, Epistulae Morales ad Lucilium, 94.25 | 468 |
| `passage_sen_ep_15_94_26` | Seneca, Epistulae Morales ad Lucilium, 94.26 | 496 |
| `passage_sen_ep_15_94_27` | Seneca, Epistulae Morales ad Lucilium, 94.27 | 588 |
| `passage_sen_ep_15_94_28` | Seneca, Epistulae Morales ad Lucilium, 94.28 | 155 |
| `passage_sen_ep_15_94_29` | Seneca, Epistulae Morales ad Lucilium, 94.29 | 459 |
| `passage_sen_ep_15_94_3` | Seneca, Epistulae Morales ad Lucilium, 94.3 | 49 |
| `passage_sen_ep_15_94_30` | Seneca, Epistulae Morales ad Lucilium, 94.30 | 323 |
| `passage_sen_ep_15_94_31` | Seneca, Epistulae Morales ad Lucilium, 94.31 | 635 |
| `passage_sen_ep_15_94_32` | Seneca, Epistulae Morales ad Lucilium, 94.32 | 414 |
| `passage_sen_ep_15_94_33` | Seneca, Epistulae Morales ad Lucilium, 94.33 | 372 |
| `passage_sen_ep_15_94_34` | Seneca, Epistulae Morales ad Lucilium, 94.34 | 256 |
| `passage_sen_ep_15_94_35` | Seneca, Epistulae Morales ad Lucilium, 94.35 | 223 |
| `passage_sen_ep_15_94_36` | Seneca, Epistulae Morales ad Lucilium, 94.36 | 522 |
| `passage_sen_ep_15_94_37` | Seneca, Epistulae Morales ad Lucilium, 94.37 | 369 |
| `passage_sen_ep_15_94_38` | Seneca, Epistulae Morales ad Lucilium, 94.38 | 464 |
| `passage_sen_ep_15_94_39` | Seneca, Epistulae Morales ad Lucilium, 94.39 | 396 |
| `passage_sen_ep_15_94_4` | Seneca, Epistulae Morales ad Lucilium, 94.4 | 324 |
| `passage_sen_ep_15_94_40` | Seneca, Epistulae Morales ad Lucilium, 94.40 | 341 |
| `passage_sen_ep_15_94_41` | Seneca, Epistulae Morales ad Lucilium, 94.41 | 393 |
| `passage_sen_ep_15_94_42` | Seneca, Epistulae Morales ad Lucilium, 94.42 | 240 |
| `passage_sen_ep_15_94_43` | Seneca, Epistulae Morales ad Lucilium, 94.43 | 271 |
| `passage_sen_ep_15_94_44` | Seneca, Epistulae Morales ad Lucilium, 94.44 | 446 |
| `passage_sen_ep_15_94_45` | Seneca, Epistulae Morales ad Lucilium, 94.45 | 345 |
| `passage_sen_ep_15_94_46` | Seneca, Epistulae Morales ad Lucilium, 94.46 | 506 |
| `passage_sen_ep_15_94_47` | Seneca, Epistulae Morales ad Lucilium, 94.47 | 382 |
| `passage_sen_ep_15_94_48` | Seneca, Epistulae Morales ad Lucilium, 94.48 | 347 |
| `passage_sen_ep_15_94_49` | Seneca, Epistulae Morales ad Lucilium, 94.49 | 304 |
| `passage_sen_ep_15_94_5` | Seneca, Epistulae Morales ad Lucilium, 94.5 | 539 |
| `passage_sen_ep_15_94_50` | Seneca, Epistulae Morales ad Lucilium, 94.50 | 423 |
| `passage_sen_ep_15_94_51` | Seneca, Epistulae Morales ad Lucilium, 94.51 | 446 |
| `passage_sen_ep_15_94_52` | Seneca, Epistulae Morales ad Lucilium, 94.52 | 285 |
| `passage_sen_ep_15_94_53` | Seneca, Epistulae Morales ad Lucilium, 94.53 | 275 |
| `passage_sen_ep_15_94_54` | Seneca, Epistulae Morales ad Lucilium, 94.54 | 477 |
| `passage_sen_ep_15_94_55` | Seneca, Epistulae Morales ad Lucilium, 94.55 | 150 |
| `passage_sen_ep_15_94_56` | Seneca, Epistulae Morales ad Lucilium, 94.56 | 880 |
| `passage_sen_ep_15_94_57` | Seneca, Epistulae Morales ad Lucilium, 94.57 | 411 |
| `passage_sen_ep_15_94_58` | Seneca, Epistulae Morales ad Lucilium, 94.58 | 348 |
| `passage_sen_ep_15_94_59` | Seneca, Epistulae Morales ad Lucilium, 94.59 | 374 |
| `passage_sen_ep_15_94_6` | Seneca, Epistulae Morales ad Lucilium, 94.6 | 423 |
| `passage_sen_ep_15_94_60` | Seneca, Epistulae Morales ad Lucilium, 94.60 | 405 |
| `passage_sen_ep_15_94_61` | Seneca, Epistulae Morales ad Lucilium, 94.61 | 526 |
| `passage_sen_ep_15_94_62` | Seneca, Epistulae Morales ad Lucilium, 94.62 | 463 |
| `passage_sen_ep_15_94_63` | Seneca, Epistulae Morales ad Lucilium, 94.63 | 367 |
| `passage_sen_ep_15_94_64` | Seneca, Epistulae Morales ad Lucilium, 94.64 | 219 |
| `passage_sen_ep_15_94_65` | Seneca, Epistulae Morales ad Lucilium, 94.65 | 351 |
| `passage_sen_ep_15_94_66` | Seneca, Epistulae Morales ad Lucilium, 94.66 | 321 |
| `passage_sen_ep_15_94_67` | Seneca, Epistulae Morales ad Lucilium, 94.67 | 338 |
| `passage_sen_ep_15_94_68` | Seneca, Epistulae Morales ad Lucilium, 94.68 | 386 |
| `passage_sen_ep_15_94_69` | Seneca, Epistulae Morales ad Lucilium, 94.69 | 360 |
| `passage_sen_ep_15_94_7` | Seneca, Epistulae Morales ad Lucilium, 94.7 | 564 |
| `passage_sen_ep_15_94_70` | Seneca, Epistulae Morales ad Lucilium, 94.70 | 317 |
| `passage_sen_ep_15_94_71` | Seneca, Epistulae Morales ad Lucilium, 94.71 | 213 |
| `passage_sen_ep_15_94_72` | Seneca, Epistulae Morales ad Lucilium, 94.72 | 289 |
| `passage_sen_ep_15_94_73` | Seneca, Epistulae Morales ad Lucilium, 94.73 | 359 |
| `passage_sen_ep_15_94_74` | Seneca, Epistulae Morales ad Lucilium, 94.74 | 387 |
| `passage_sen_ep_15_94_8` | Seneca, Epistulae Morales ad Lucilium, 94.8 | 494 |
| `passage_sen_ep_15_94_9` | Seneca, Epistulae Morales ad Lucilium, 94.9 | 287 |
| `passage_sen_ep_15_95_1` | Seneca, Epistulae Morales ad Lucilium, 95.1 | 367 |
| `passage_sen_ep_15_95_10` | Seneca, Epistulae Morales ad Lucilium, 95.10 | 495 |
| `passage_sen_ep_15_95_11` | Seneca, Epistulae Morales ad Lucilium, 95.11 | 78 |
| `passage_sen_ep_15_95_12` | Seneca, Epistulae Morales ad Lucilium, 95.12 | 572 |
| `passage_sen_ep_15_95_13` | Seneca, Epistulae Morales ad Lucilium, 95.13 | 269 |
| `passage_sen_ep_15_95_14` | Seneca, Epistulae Morales ad Lucilium, 95.14 | 406 |
| `passage_sen_ep_15_95_15` | Seneca, Epistulae Morales ad Lucilium, 95.15 | 486 |
| `passage_sen_ep_15_95_16` | Seneca, Epistulae Morales ad Lucilium, 95.16 | 523 |
| `passage_sen_ep_15_95_17` | Seneca, Epistulae Morales ad Lucilium, 95.17 | 334 |
| `passage_sen_ep_15_95_18` | Seneca, Epistulae Morales ad Lucilium, 95.18 | 542 |
| `passage_sen_ep_15_95_19` | Seneca, Epistulae Morales ad Lucilium, 95.19 | 390 |
| `passage_sen_ep_15_95_2` | Seneca, Epistulae Morales ad Lucilium, 95.2 | 511 |
| `passage_sen_ep_15_95_20` | Seneca, Epistulae Morales ad Lucilium, 95.20 | 290 |
| `passage_sen_ep_15_95_21` | Seneca, Epistulae Morales ad Lucilium, 95.21 | 574 |
| `passage_sen_ep_15_95_22` | Seneca, Epistulae Morales ad Lucilium, 95.22 | 345 |
| `passage_sen_ep_15_95_23` | Seneca, Epistulae Morales ad Lucilium, 95.23 | 393 |
| `passage_sen_ep_15_95_24` | Seneca, Epistulae Morales ad Lucilium, 95.24 | 588 |
| `passage_sen_ep_15_95_25` | Seneca, Epistulae Morales ad Lucilium, 95.25 | 564 |
| `passage_sen_ep_15_95_26` | Seneca, Epistulae Morales ad Lucilium, 95.26 | 324 |
| `passage_sen_ep_15_95_27` | Seneca, Epistulae Morales ad Lucilium, 95.27 | 420 |
| `passage_sen_ep_15_95_28` | Seneca, Epistulae Morales ad Lucilium, 95.28 | 282 |
| `passage_sen_ep_15_95_29` | Seneca, Epistulae Morales ad Lucilium, 95.29 | 411 |
| `passage_sen_ep_15_95_3` | Seneca, Epistulae Morales ad Lucilium, 95.3 | 564 |
| `passage_sen_ep_15_95_30` | Seneca, Epistulae Morales ad Lucilium, 95.30 | 349 |
| `passage_sen_ep_15_95_31` | Seneca, Epistulae Morales ad Lucilium, 95.31 | 219 |
| `passage_sen_ep_15_95_32` | Seneca, Epistulae Morales ad Lucilium, 95.32 | 315 |
| `passage_sen_ep_15_95_33` | Seneca, Epistulae Morales ad Lucilium, 95.33 | 400 |
| `passage_sen_ep_15_95_34` | Seneca, Epistulae Morales ad Lucilium, 95.34 | 277 |
| `passage_sen_ep_15_95_35` | Seneca, Epistulae Morales ad Lucilium, 95.35 | 526 |
| `passage_sen_ep_15_95_36` | Seneca, Epistulae Morales ad Lucilium, 95.36 | 627 |
| `passage_sen_ep_15_95_37` | Seneca, Epistulae Morales ad Lucilium, 95.37 | 782 |
| `passage_sen_ep_15_95_38` | Seneca, Epistulae Morales ad Lucilium, 95.38 | 244 |
| `passage_sen_ep_15_95_39` | Seneca, Epistulae Morales ad Lucilium, 95.39 | 297 |
| `passage_sen_ep_15_95_4` | Seneca, Epistulae Morales ad Lucilium, 95.4 | 149 |
| `passage_sen_ep_15_95_40` | Seneca, Epistulae Morales ad Lucilium, 95.40 | 278 |
| `passage_sen_ep_15_95_41` | Seneca, Epistulae Morales ad Lucilium, 95.41 | 364 |
| `passage_sen_ep_15_95_42` | Seneca, Epistulae Morales ad Lucilium, 95.42 | 652 |
| `passage_sen_ep_15_95_43` | Seneca, Epistulae Morales ad Lucilium, 95.43 | 320 |
| `passage_sen_ep_15_95_44` | Seneca, Epistulae Morales ad Lucilium, 95.44 | 252 |
| `passage_sen_ep_15_95_45` | Seneca, Epistulae Morales ad Lucilium, 95.45 | 340 |
| `passage_sen_ep_15_95_46` | Seneca, Epistulae Morales ad Lucilium, 95.46 | 311 |
| `passage_sen_ep_15_95_47` | Seneca, Epistulae Morales ad Lucilium, 95.47 | 454 |
| `passage_sen_ep_15_95_48` | Seneca, Epistulae Morales ad Lucilium, 95.48 | 263 |
| `passage_sen_ep_15_95_49` | Seneca, Epistulae Morales ad Lucilium, 95.49 | 233 |
| `passage_sen_ep_15_95_5` | Seneca, Epistulae Morales ad Lucilium, 95.5 | 334 |
| `passage_sen_ep_15_95_50` | Seneca, Epistulae Morales ad Lucilium, 95.50 | 458 |
| `passage_sen_ep_15_95_51` | Seneca, Epistulae Morales ad Lucilium, 95.51 | 542 |
| `passage_sen_ep_15_95_52` | Seneca, Epistulae Morales ad Lucilium, 95.52 | 252 |
| `passage_sen_ep_15_95_53` | Seneca, Epistulae Morales ad Lucilium, 95.53 | 184 |
| `passage_sen_ep_15_95_54` | Seneca, Epistulae Morales ad Lucilium, 95.54 | 319 |
| `passage_sen_ep_15_95_55` | Seneca, Epistulae Morales ad Lucilium, 95.55 | 326 |
| `passage_sen_ep_15_95_56` | Seneca, Epistulae Morales ad Lucilium, 95.56 | 279 |
| `passage_sen_ep_15_95_57` | Seneca, Epistulae Morales ad Lucilium, 95.57 | 479 |
| `passage_sen_ep_15_95_58` | Seneca, Epistulae Morales ad Lucilium, 95.58 | 471 |
| `passage_sen_ep_15_95_59` | Seneca, Epistulae Morales ad Lucilium, 95.59 | 412 |
| `passage_sen_ep_15_95_6` | Seneca, Epistulae Morales ad Lucilium, 95.6 | 201 |
| `passage_sen_ep_15_95_60` | Seneca, Epistulae Morales ad Lucilium, 95.60 | 438 |
| `passage_sen_ep_15_95_61` | Seneca, Epistulae Morales ad Lucilium, 95.61 | 536 |
| `passage_sen_ep_15_95_62` | Seneca, Epistulae Morales ad Lucilium, 95.62 | 170 |
| `passage_sen_ep_15_95_63` | Seneca, Epistulae Morales ad Lucilium, 95.63 | 304 |
| `passage_sen_ep_15_95_64` | Seneca, Epistulae Morales ad Lucilium, 95.64 | 516 |
| `passage_sen_ep_15_95_65` | Seneca, Epistulae Morales ad Lucilium, 95.65 | 525 |
| `passage_sen_ep_15_95_66` | Seneca, Epistulae Morales ad Lucilium, 95.66 | 379 |
| `passage_sen_ep_15_95_67` | Seneca, Epistulae Morales ad Lucilium, 95.67 | 216 |
| `passage_sen_ep_15_95_69` | Seneca, Epistulae Morales ad Lucilium, 95.69 | 321 |
| `passage_sen_ep_15_95_7` | Seneca, Epistulae Morales ad Lucilium, 95.7 | 372 |
| `passage_sen_ep_15_95_70` | Seneca, Epistulae Morales ad Lucilium, 95.70 | 534 |
| `passage_sen_ep_15_95_71` | Seneca, Epistulae Morales ad Lucilium, 95.71 | 313 |
| `passage_sen_ep_15_95_72` | Seneca, Epistulae Morales ad Lucilium, 95.72 | 632 |
| `passage_sen_ep_15_95_73` | Seneca, Epistulae Morales ad Lucilium, 95.73 | 280 |
| `passage_sen_ep_15_95_8` | Seneca, Epistulae Morales ad Lucilium, 95.8 | 456 |
| `passage_sen_ep_15_95_9` | Seneca, Epistulae Morales ad Lucilium, 95.9 | 460 |
| `passage_sen_ep_15_96_1` | Seneca, Epistulae Morales ad Lucilium, 96.1 | 434 |
| `passage_sen_ep_15_96_2` | Seneca, Epistulae Morales ad Lucilium, 96.2 | 464 |
| `passage_sen_ep_15_96_3` | Seneca, Epistulae Morales ad Lucilium, 96.3 | 264 |
| `passage_sen_ep_15_96_4` | Seneca, Epistulae Morales ad Lucilium, 96.4 | 242 |
| `passage_sen_ep_15_96_5` | Seneca, Epistulae Morales ad Lucilium, 96.5 | 422 |
| `passage_sen_ep_15_97_1` | Seneca, Epistulae Morales ad Lucilium, 97.1 | 318 |
| `passage_sen_ep_15_97_10` | Seneca, Epistulae Morales ad Lucilium, 97.10 | 350 |
| `passage_sen_ep_15_97_11` | Seneca, Epistulae Morales ad Lucilium, 97.11 | 353 |
| `passage_sen_ep_15_97_12` | Seneca, Epistulae Morales ad Lucilium, 97.12 | 279 |
| `passage_sen_ep_15_97_13` | Seneca, Epistulae Morales ad Lucilium, 97.13 | 331 |
| `passage_sen_ep_15_97_14` | Seneca, Epistulae Morales ad Lucilium, 97.14 | 488 |
| `passage_sen_ep_15_97_15` | Seneca, Epistulae Morales ad Lucilium, 97.15 | 476 |
| `passage_sen_ep_15_97_16` | Seneca, Epistulae Morales ad Lucilium, 97.16 | 544 |
| `passage_sen_ep_15_97_2` | Seneca, Epistulae Morales ad Lucilium, 97.2 | 469 |
| `passage_sen_ep_15_97_3` | Seneca, Epistulae Morales ad Lucilium, 97.3 | 282 |
| `passage_sen_ep_15_97_4` | Seneca, Epistulae Morales ad Lucilium, 97.4 | 212 |
| `passage_sen_ep_15_97_5` | Seneca, Epistulae Morales ad Lucilium, 97.5 | 396 |
| `passage_sen_ep_15_97_6` | Seneca, Epistulae Morales ad Lucilium, 97.6 | 362 |
| `passage_sen_ep_15_97_7` | Seneca, Epistulae Morales ad Lucilium, 97.7 | 326 |
| `passage_sen_ep_15_97_8` | Seneca, Epistulae Morales ad Lucilium, 97.8 | 348 |
| `passage_sen_ep_15_97_9` | Seneca, Epistulae Morales ad Lucilium, 97.9 | 424 |
| `passage_sen_ep_15_98_1` | Seneca, Epistulae Morales ad Lucilium, 98.1 | 401 |
| `passage_sen_ep_15_98_10` | Seneca, Epistulae Morales ad Lucilium, 98.10 | 380 |
| `passage_sen_ep_15_98_11` | Seneca, Epistulae Morales ad Lucilium, 98.11 | 346 |
| `passage_sen_ep_15_98_12` | Seneca, Epistulae Morales ad Lucilium, 98.12 | 211 |
| `passage_sen_ep_15_98_13` | Seneca, Epistulae Morales ad Lucilium, 98.13 | 554 |
| `passage_sen_ep_15_98_14` | Seneca, Epistulae Morales ad Lucilium, 98.14 | 381 |
| `passage_sen_ep_15_98_15` | Seneca, Epistulae Morales ad Lucilium, 98.15 | 309 |
| `passage_sen_ep_15_98_16` | Seneca, Epistulae Morales ad Lucilium, 98.16 | 255 |
| `passage_sen_ep_15_98_17` | Seneca, Epistulae Morales ad Lucilium, 98.17 | 328 |
| `passage_sen_ep_15_98_18` | Seneca, Epistulae Morales ad Lucilium, 98.18 | 246 |
| `passage_sen_ep_15_98_2` | Seneca, Epistulae Morales ad Lucilium, 98.2 | 428 |
| `passage_sen_ep_15_98_3` | Seneca, Epistulae Morales ad Lucilium, 98.3 | 432 |
| `passage_sen_ep_15_98_4` | Seneca, Epistulae Morales ad Lucilium, 98.4 | 341 |
| `passage_sen_ep_15_98_5` | Seneca, Epistulae Morales ad Lucilium, 98.5 | 569 |
| `passage_sen_ep_15_98_6` | Seneca, Epistulae Morales ad Lucilium, 98.6 | 158 |
| `passage_sen_ep_15_98_7` | Seneca, Epistulae Morales ad Lucilium, 98.7 | 440 |
| `passage_sen_ep_15_98_8` | Seneca, Epistulae Morales ad Lucilium, 98.8 | 492 |
| `passage_sen_ep_15_98_9` | Seneca, Epistulae Morales ad Lucilium, 98.9 | 320 |
| `passage_sen_ep_15_99_1` | Seneca, Epistulae Morales ad Lucilium, 99.1 | 445 |
| `passage_sen_ep_15_99_10` | Seneca, Epistulae Morales ad Lucilium, 99.10 | 265 |
| `passage_sen_ep_15_99_11` | Seneca, Epistulae Morales ad Lucilium, 99.11 | 243 |
| `passage_sen_ep_15_99_12` | Seneca, Epistulae Morales ad Lucilium, 99.12 | 358 |
| `passage_sen_ep_15_99_13` | Seneca, Epistulae Morales ad Lucilium, 99.13 | 360 |
| `passage_sen_ep_15_99_14` | Seneca, Epistulae Morales ad Lucilium, 99.14 | 277 |
| `passage_sen_ep_15_99_15` | Seneca, Epistulae Morales ad Lucilium, 99.15 | 356 |
| `passage_sen_ep_15_99_16` | Seneca, Epistulae Morales ad Lucilium, 99.16 | 549 |
| `passage_sen_ep_15_99_17` | Seneca, Epistulae Morales ad Lucilium, 99.17 | 387 |
| `passage_sen_ep_15_99_18` | Seneca, Epistulae Morales ad Lucilium, 99.18 | 483 |
| `passage_sen_ep_15_99_19` | Seneca, Epistulae Morales ad Lucilium, 99.19 | 314 |
| `passage_sen_ep_15_99_2` | Seneca, Epistulae Morales ad Lucilium, 99.2 | 173 |
| `passage_sen_ep_15_99_20` | Seneca, Epistulae Morales ad Lucilium, 99.20 | 379 |
| `passage_sen_ep_15_99_21` | Seneca, Epistulae Morales ad Lucilium, 99.21 | 316 |
| `passage_sen_ep_15_99_22` | Seneca, Epistulae Morales ad Lucilium, 99.22 | 331 |
| `passage_sen_ep_15_99_23` | Seneca, Epistulae Morales ad Lucilium, 99.23 | 373 |
| `passage_sen_ep_15_99_24` | Seneca, Epistulae Morales ad Lucilium, 99.24 | 306 |
| `passage_sen_ep_15_99_25` | Seneca, Epistulae Morales ad Lucilium, 99.25 | 294 |
| `passage_sen_ep_15_99_26` | Seneca, Epistulae Morales ad Lucilium, 99.26 | 447 |
| `passage_sen_ep_15_99_27` | Seneca, Epistulae Morales ad Lucilium, 99.27 | 535 |
| `passage_sen_ep_15_99_28` | Seneca, Epistulae Morales ad Lucilium, 99.28 | 318 |
| `passage_sen_ep_15_99_29` | Seneca, Epistulae Morales ad Lucilium, 99.29 | 352 |
| `passage_sen_ep_15_99_3` | Seneca, Epistulae Morales ad Lucilium, 99.3 | 407 |
| `passage_sen_ep_15_99_30` | Seneca, Epistulae Morales ad Lucilium, 99.30 | 297 |
| `passage_sen_ep_15_99_31` | Seneca, Epistulae Morales ad Lucilium, 99.31 | 369 |
| `passage_sen_ep_15_99_32` | Seneca, Epistulae Morales ad Lucilium, 99.32 | 349 |
| `passage_sen_ep_15_99_4` | Seneca, Epistulae Morales ad Lucilium, 99.4 | 540 |
| `passage_sen_ep_15_99_5` | Seneca, Epistulae Morales ad Lucilium, 99.5 | 502 |
| `passage_sen_ep_15_99_6` | Seneca, Epistulae Morales ad Lucilium, 99.6 | 473 |
| `passage_sen_ep_15_99_7` | Seneca, Epistulae Morales ad Lucilium, 99.7 | 449 |
| `passage_sen_ep_15_99_8` | Seneca, Epistulae Morales ad Lucilium, 99.8 | 183 |
| `passage_sen_ep_15_99_9` | Seneca, Epistulae Morales ad Lucilium, 99.9 | 554 |
| `passage_sen_ep_17_101_1` | Seneca, Epistulae Morales ad Lucilium, 101.1 | 353 |
| `passage_sen_ep_17_101_10` | Seneca, Epistulae Morales ad Lucilium, 101.10 | 427 |
| `passage_sen_ep_17_101_12` | Seneca, Epistulae Morales ad Lucilium, 101.12 | 509 |
| `passage_sen_ep_17_101_13` | Seneca, Epistulae Morales ad Lucilium, 101.13 | 347 |
| `passage_sen_ep_17_101_14` | Seneca, Epistulae Morales ad Lucilium, 101.14 | 701 |
| `passage_sen_ep_17_101_15` | Seneca, Epistulae Morales ad Lucilium, 101.15 | 80 |
| `passage_sen_ep_17_101_2` | Seneca, Epistulae Morales ad Lucilium, 101.2 | 291 |
| `passage_sen_ep_17_101_3` | Seneca, Epistulae Morales ad Lucilium, 101.3 | 423 |
| `passage_sen_ep_17_101_4` | Seneca, Epistulae Morales ad Lucilium, 101.4 | 471 |
| `passage_sen_ep_17_101_5` | Seneca, Epistulae Morales ad Lucilium, 101.5 | 297 |
| `passage_sen_ep_17_101_6` | Seneca, Epistulae Morales ad Lucilium, 101.6 | 348 |
| `passage_sen_ep_17_101_7` | Seneca, Epistulae Morales ad Lucilium, 101.7 | 316 |
| `passage_sen_ep_17_101_8` | Seneca, Epistulae Morales ad Lucilium, 101.8 | 376 |
| `passage_sen_ep_17_101_9` | Seneca, Epistulae Morales ad Lucilium, 101.9 | 458 |
| `passage_sen_ep_17_102_1` | Seneca, Epistulae Morales ad Lucilium, 102.1 | 248 |
| `passage_sen_ep_17_102_10` | Seneca, Epistulae Morales ad Lucilium, 102.10 | 304 |
| `passage_sen_ep_17_102_11` | Seneca, Epistulae Morales ad Lucilium, 102.11 | 254 |
| `passage_sen_ep_17_102_12` | Seneca, Epistulae Morales ad Lucilium, 102.12 | 519 |
| `passage_sen_ep_17_102_13` | Seneca, Epistulae Morales ad Lucilium, 102.13 | 464 |
| `passage_sen_ep_17_102_14` | Seneca, Epistulae Morales ad Lucilium, 102.14 | 256 |
| `passage_sen_ep_17_102_15` | Seneca, Epistulae Morales ad Lucilium, 102.15 | 316 |
| `passage_sen_ep_17_102_16` | Seneca, Epistulae Morales ad Lucilium, 102.16 | 445 |
| `passage_sen_ep_17_102_17` | Seneca, Epistulae Morales ad Lucilium, 102.17 | 333 |
| `passage_sen_ep_17_102_18` | Seneca, Epistulae Morales ad Lucilium, 102.18 | 330 |
| `passage_sen_ep_17_102_19` | Seneca, Epistulae Morales ad Lucilium, 102.19 | 432 |
| `passage_sen_ep_17_102_2` | Seneca, Epistulae Morales ad Lucilium, 102.2 | 453 |
| `passage_sen_ep_17_102_20` | Seneca, Epistulae Morales ad Lucilium, 102.20 | 368 |
| `passage_sen_ep_17_102_21` | Seneca, Epistulae Morales ad Lucilium, 102.21 | 528 |
| `passage_sen_ep_17_102_22` | Seneca, Epistulae Morales ad Lucilium, 102.22 | 336 |
| `passage_sen_ep_17_102_23` | Seneca, Epistulae Morales ad Lucilium, 102.23 | 504 |
| `passage_sen_ep_17_102_24` | Seneca, Epistulae Morales ad Lucilium, 102.24 | 89 |
| `passage_sen_ep_17_102_25` | Seneca, Epistulae Morales ad Lucilium, 102.25 | 338 |
| `passage_sen_ep_17_102_26` | Seneca, Epistulae Morales ad Lucilium, 102.26 | 512 |
| `passage_sen_ep_17_102_27` | Seneca, Epistulae Morales ad Lucilium, 102.27 | 382 |
| `passage_sen_ep_17_102_28` | Seneca, Epistulae Morales ad Lucilium, 102.28 | 679 |
| `passage_sen_ep_17_102_29` | Seneca, Epistulae Morales ad Lucilium, 102.29 | 295 |
| `passage_sen_ep_17_102_3` | Seneca, Epistulae Morales ad Lucilium, 102.3 | 280 |
| `passage_sen_ep_17_102_30` | Seneca, Epistulae Morales ad Lucilium, 102.30 | 347 |
| `passage_sen_ep_17_102_4` | Seneca, Epistulae Morales ad Lucilium, 102.4 | 497 |
| `passage_sen_ep_17_102_5` | Seneca, Epistulae Morales ad Lucilium, 102.5 | 231 |
| `passage_sen_ep_17_102_6` | Seneca, Epistulae Morales ad Lucilium, 102.6 | 498 |
| `passage_sen_ep_17_102_7` | Seneca, Epistulae Morales ad Lucilium, 102.7 | 245 |
| `passage_sen_ep_17_102_8` | Seneca, Epistulae Morales ad Lucilium, 102.8 | 382 |
| `passage_sen_ep_17_102_9` | Seneca, Epistulae Morales ad Lucilium, 102.9 | 377 |
| `passage_sen_ep_17_103_1` | Seneca, Epistulae Morales ad Lucilium, 103.1 | 454 |
| `passage_sen_ep_17_103_2` | Seneca, Epistulae Morales ad Lucilium, 103.2 | 484 |
| `passage_sen_ep_17_103_3` | Seneca, Epistulae Morales ad Lucilium, 103.3 | 234 |
| `passage_sen_ep_17_103_4` | Seneca, Epistulae Morales ad Lucilium, 103.4 | 344 |
| `passage_sen_ep_17_103_5` | Seneca, Epistulae Morales ad Lucilium, 103.5 | 174 |
| `passage_sen_ep_17_104_1` | Seneca, Epistulae Morales ad Lucilium, 104.1 | 426 |
| `passage_sen_ep_17_104_10` | Seneca, Epistulae Morales ad Lucilium, 104.10 | 439 |
| `passage_sen_ep_17_104_11` | Seneca, Epistulae Morales ad Lucilium, 104.11 | 458 |
| `passage_sen_ep_17_104_12` | Seneca, Epistulae Morales ad Lucilium, 104.12 | 420 |
| `passage_sen_ep_17_104_13` | Seneca, Epistulae Morales ad Lucilium, 104.13 | 321 |
| `passage_sen_ep_17_104_14` | Seneca, Epistulae Morales ad Lucilium, 104.14 | 224 |
| `passage_sen_ep_17_104_15` | Seneca, Epistulae Morales ad Lucilium, 104.15 | 516 |
| `passage_sen_ep_17_104_16` | Seneca, Epistulae Morales ad Lucilium, 104.16 | 332 |
| `passage_sen_ep_17_104_17` | Seneca, Epistulae Morales ad Lucilium, 104.17 | 270 |
| `passage_sen_ep_17_104_18` | Seneca, Epistulae Morales ad Lucilium, 104.18 | 294 |
| `passage_sen_ep_17_104_19` | Seneca, Epistulae Morales ad Lucilium, 104.19 | 388 |
| `passage_sen_ep_17_104_2` | Seneca, Epistulae Morales ad Lucilium, 104.2 | 412 |
| `passage_sen_ep_17_104_20` | Seneca, Epistulae Morales ad Lucilium, 104.20 | 442 |
| `passage_sen_ep_17_104_21` | Seneca, Epistulae Morales ad Lucilium, 104.21 | 594 |
| `passage_sen_ep_17_104_22` | Seneca, Epistulae Morales ad Lucilium, 104.22 | 178 |
| `passage_sen_ep_17_104_23` | Seneca, Epistulae Morales ad Lucilium, 104.23 | 360 |
| `passage_sen_ep_17_104_24` | Seneca, Epistulae Morales ad Lucilium, 104.24 | 420 |
| `passage_sen_ep_17_104_25` | Seneca, Epistulae Morales ad Lucilium, 104.25 | 213 |
| `passage_sen_ep_17_104_26` | Seneca, Epistulae Morales ad Lucilium, 104.26 | 250 |
| `passage_sen_ep_17_104_27` | Seneca, Epistulae Morales ad Lucilium, 104.27 | 601 |
| `passage_sen_ep_17_104_28` | Seneca, Epistulae Morales ad Lucilium, 104.28 | 468 |
| `passage_sen_ep_17_104_29` | Seneca, Epistulae Morales ad Lucilium, 104.29 | 463 |
| `passage_sen_ep_17_104_3` | Seneca, Epistulae Morales ad Lucilium, 104.3 | 551 |
| `passage_sen_ep_17_104_30` | Seneca, Epistulae Morales ad Lucilium, 104.30 | 471 |
| `passage_sen_ep_17_104_31` | Seneca, Epistulae Morales ad Lucilium, 104.31 | 280 |
| `passage_sen_ep_17_104_32` | Seneca, Epistulae Morales ad Lucilium, 104.32 | 333 |
| `passage_sen_ep_17_104_33` | Seneca, Epistulae Morales ad Lucilium, 104.33 | 600 |
| `passage_sen_ep_17_104_34` | Seneca, Epistulae Morales ad Lucilium, 104.34 | 423 |
| `passage_sen_ep_17_104_4` | Seneca, Epistulae Morales ad Lucilium, 104.4 | 286 |
| `passage_sen_ep_17_104_5` | Seneca, Epistulae Morales ad Lucilium, 104.5 | 226 |
| `passage_sen_ep_17_104_6` | Seneca, Epistulae Morales ad Lucilium, 104.6 | 453 |
| `passage_sen_ep_17_104_7` | Seneca, Epistulae Morales ad Lucilium, 104.7 | 357 |
| `passage_sen_ep_17_104_8` | Seneca, Epistulae Morales ad Lucilium, 104.8 | 362 |
| `passage_sen_ep_17_104_9` | Seneca, Epistulae Morales ad Lucilium, 104.9 | 409 |
| `passage_sen_ep_17_105_1` | Seneca, Epistulae Morales ad Lucilium, 105.1 | 293 |
| `passage_sen_ep_17_105_2` | Seneca, Epistulae Morales ad Lucilium, 105.2 | 259 |
| `passage_sen_ep_17_105_3` | Seneca, Epistulae Morales ad Lucilium, 105.3 | 291 |
| `passage_sen_ep_17_105_4` | Seneca, Epistulae Morales ad Lucilium, 105.4 | 551 |
| `passage_sen_ep_17_105_5` | Seneca, Epistulae Morales ad Lucilium, 105.5 | 316 |
| `passage_sen_ep_17_105_6` | Seneca, Epistulae Morales ad Lucilium, 105.6 | 494 |
| `passage_sen_ep_17_105_7` | Seneca, Epistulae Morales ad Lucilium, 105.7 | 327 |
| `passage_sen_ep_17_105_8` | Seneca, Epistulae Morales ad Lucilium, 105.8 | 317 |
| `passage_sen_ep_17_106_1` | Seneca, Epistulae Morales ad Lucilium, 106.1 | 342 |
| `passage_sen_ep_17_106_10` | Seneca, Epistulae Morales ad Lucilium, 106.10 | 223 |
| `passage_sen_ep_17_106_11` | Seneca, Epistulae Morales ad Lucilium, 106.11 | 335 |
| `passage_sen_ep_17_106_12` | Seneca, Epistulae Morales ad Lucilium, 106.12 | 110 |
| `passage_sen_ep_17_106_2` | Seneca, Epistulae Morales ad Lucilium, 106.2 | 259 |
| `passage_sen_ep_17_106_3` | Seneca, Epistulae Morales ad Lucilium, 106.3 | 229 |
| `passage_sen_ep_17_106_4` | Seneca, Epistulae Morales ad Lucilium, 106.4 | 196 |
| `passage_sen_ep_17_106_5` | Seneca, Epistulae Morales ad Lucilium, 106.5 | 545 |
| `passage_sen_ep_17_106_6` | Seneca, Epistulae Morales ad Lucilium, 106.6 | 282 |
| `passage_sen_ep_17_106_7` | Seneca, Epistulae Morales ad Lucilium, 106.7 | 447 |
| `passage_sen_ep_17_106_8` | Seneca, Epistulae Morales ad Lucilium, 106.8 | 102 |
| `passage_sen_ep_17_106_9` | Seneca, Epistulae Morales ad Lucilium, 106.9 | 273 |
| `passage_sen_ep_17_107_1` | Seneca, Epistulae Morales ad Lucilium, 107.1 | 393 |
| `passage_sen_ep_17_107_10` | Seneca, Epistulae Morales ad Lucilium, 107.10 | 438 |
| `passage_sen_ep_17_107_12` | Seneca, Epistulae Morales ad Lucilium, 107.12 | 236 |
| `passage_sen_ep_17_107_2` | Seneca, Epistulae Morales ad Lucilium, 107.2 | 511 |
| `passage_sen_ep_17_107_3` | Seneca, Epistulae Morales ad Lucilium, 107.3 | 245 |
| `passage_sen_ep_17_107_4` | Seneca, Epistulae Morales ad Lucilium, 107.4 | 293 |
| `passage_sen_ep_17_107_5` | Seneca, Epistulae Morales ad Lucilium, 107.5 | 366 |
| `passage_sen_ep_17_107_6` | Seneca, Epistulae Morales ad Lucilium, 107.6 | 304 |
| `passage_sen_ep_17_107_7` | Seneca, Epistulae Morales ad Lucilium, 107.7 | 393 |
| `passage_sen_ep_17_107_8` | Seneca, Epistulae Morales ad Lucilium, 107.8 | 235 |
| `passage_sen_ep_17_107_9` | Seneca, Epistulae Morales ad Lucilium, 107.9 | 301 |
| `passage_sen_ep_17_108_1` | Seneca, Epistulae Morales ad Lucilium, 108.1 | 356 |
| `passage_sen_ep_17_108_10` | Seneca, Epistulae Morales ad Lucilium, 108.10 | 450 |
| `passage_sen_ep_17_108_11` | Seneca, Epistulae Morales ad Lucilium, 108.11 | 283 |
| `passage_sen_ep_17_108_12` | Seneca, Epistulae Morales ad Lucilium, 108.12 | 691 |
| `passage_sen_ep_17_108_13` | Seneca, Epistulae Morales ad Lucilium, 108.13 | 272 |
| `passage_sen_ep_17_108_14` | Seneca, Epistulae Morales ad Lucilium, 108.14 | 361 |
| `passage_sen_ep_17_108_15` | Seneca, Epistulae Morales ad Lucilium, 108.15 | 367 |
| `passage_sen_ep_17_108_16` | Seneca, Epistulae Morales ad Lucilium, 108.16 | 438 |
| `passage_sen_ep_17_108_17` | Seneca, Epistulae Morales ad Lucilium, 108.17 | 290 |
| `passage_sen_ep_17_108_18` | Seneca, Epistulae Morales ad Lucilium, 108.18 | 273 |
| `passage_sen_ep_17_108_19` | Seneca, Epistulae Morales ad Lucilium, 108.19 | 509 |
| `passage_sen_ep_17_108_2` | Seneca, Epistulae Morales ad Lucilium, 108.2 | 305 |
| `passage_sen_ep_17_108_20` | Seneca, Epistulae Morales ad Lucilium, 108.20 | 455 |
| `passage_sen_ep_17_108_21` | Seneca, Epistulae Morales ad Lucilium, 108.21 | 241 |
| `passage_sen_ep_17_108_22` | Seneca, Epistulae Morales ad Lucilium, 108.22 | 572 |
| `passage_sen_ep_17_108_23` | Seneca, Epistulae Morales ad Lucilium, 108.23 | 501 |
| `passage_sen_ep_17_108_24` | Seneca, Epistulae Morales ad Lucilium, 108.24 | 400 |
| `passage_sen_ep_17_108_25` | Seneca, Epistulae Morales ad Lucilium, 108.25 | 328 |
| `passage_sen_ep_17_108_26` | Seneca, Epistulae Morales ad Lucilium, 108.26 | 279 |
| `passage_sen_ep_17_108_27` | Seneca, Epistulae Morales ad Lucilium, 108.27 | 585 |
| `passage_sen_ep_17_108_28` | Seneca, Epistulae Morales ad Lucilium, 108.28 | 346 |
| `passage_sen_ep_17_108_29` | Seneca, Epistulae Morales ad Lucilium, 108.29 | 232 |
| `passage_sen_ep_17_108_3` | Seneca, Epistulae Morales ad Lucilium, 108.3 | 318 |
| `passage_sen_ep_17_108_30` | Seneca, Epistulae Morales ad Lucilium, 108.30 | 412 |
| `passage_sen_ep_17_108_31` | Seneca, Epistulae Morales ad Lucilium, 108.31 | 406 |
| `passage_sen_ep_17_108_32` | Seneca, Epistulae Morales ad Lucilium, 108.32 | 416 |
| `passage_sen_ep_17_108_33` | Seneca, Epistulae Morales ad Lucilium, 108.33 | 273 |
| `passage_sen_ep_17_108_34` | Seneca, Epistulae Morales ad Lucilium, 108.34 | 160 |
| `passage_sen_ep_17_108_35` | Seneca, Epistulae Morales ad Lucilium, 108.35 | 391 |
| `passage_sen_ep_17_108_36` | Seneca, Epistulae Morales ad Lucilium, 108.36 | 270 |
| `passage_sen_ep_17_108_37` | Seneca, Epistulae Morales ad Lucilium, 108.37 | 354 |
| `passage_sen_ep_17_108_38` | Seneca, Epistulae Morales ad Lucilium, 108.38 | 233 |
| `passage_sen_ep_17_108_39` | Seneca, Epistulae Morales ad Lucilium, 108.39 | 222 |
| `passage_sen_ep_17_108_4` | Seneca, Epistulae Morales ad Lucilium, 108.4 | 497 |
| `passage_sen_ep_17_108_5` | Seneca, Epistulae Morales ad Lucilium, 108.5 | 227 |
| `passage_sen_ep_17_108_6` | Seneca, Epistulae Morales ad Lucilium, 108.6 | 1,095 |
| `passage_sen_ep_17_108_8` | Seneca, Epistulae Morales ad Lucilium, 108.8 | 336 |
| `passage_sen_ep_17_108_9` | Seneca, Epistulae Morales ad Lucilium, 108.9 | 249 |
| `passage_sen_ep_17_109_1` | Seneca, Epistulae Morales ad Lucilium, 109.1 | 311 |
| `passage_sen_ep_17_109_10` | Seneca, Epistulae Morales ad Lucilium, 109.10 | 213 |
| `passage_sen_ep_17_109_11` | Seneca, Epistulae Morales ad Lucilium, 109.11 | 239 |
| `passage_sen_ep_17_109_12` | Seneca, Epistulae Morales ad Lucilium, 109.12 | 367 |
| `passage_sen_ep_17_109_13` | Seneca, Epistulae Morales ad Lucilium, 109.13 | 268 |
| `passage_sen_ep_17_109_14` | Seneca, Epistulae Morales ad Lucilium, 109.14 | 553 |
| `passage_sen_ep_17_109_15` | Seneca, Epistulae Morales ad Lucilium, 109.15 | 489 |
| `passage_sen_ep_17_109_16` | Seneca, Epistulae Morales ad Lucilium, 109.16 | 426 |
| `passage_sen_ep_17_109_17` | Seneca, Epistulae Morales ad Lucilium, 109.17 | 349 |
| `passage_sen_ep_17_109_18` | Seneca, Epistulae Morales ad Lucilium, 109.18 | 443 |
| `passage_sen_ep_17_109_2` | Seneca, Epistulae Morales ad Lucilium, 109.2 | 168 |
| `passage_sen_ep_17_109_3` | Seneca, Epistulae Morales ad Lucilium, 109.3 | 254 |
| `passage_sen_ep_17_109_4` | Seneca, Epistulae Morales ad Lucilium, 109.4 | 253 |
| `passage_sen_ep_17_109_5` | Seneca, Epistulae Morales ad Lucilium, 109.5 | 308 |
| `passage_sen_ep_17_109_6` | Seneca, Epistulae Morales ad Lucilium, 109.6 | 300 |
| `passage_sen_ep_17_109_7` | Seneca, Epistulae Morales ad Lucilium, 109.7 | 329 |
| `passage_sen_ep_17_109_8` | Seneca, Epistulae Morales ad Lucilium, 109.8 | 351 |
| `passage_sen_ep_17_109_9` | Seneca, Epistulae Morales ad Lucilium, 109.9 | 408 |
| `passage_sen_ep_19_110_1` | Seneca, Epistulae Morales ad Lucilium, 110.1 | 444 |
| `passage_sen_ep_19_110_10` | Seneca, Epistulae Morales ad Lucilium, 110.10 | 395 |
| `passage_sen_ep_19_110_11` | Seneca, Epistulae Morales ad Lucilium, 110.11 | 254 |
| `passage_sen_ep_19_110_12` | Seneca, Epistulae Morales ad Lucilium, 110.12 | 759 |
| `passage_sen_ep_19_110_13` | Seneca, Epistulae Morales ad Lucilium, 110.13 | 390 |
| `passage_sen_ep_19_110_14` | Seneca, Epistulae Morales ad Lucilium, 110.14 | 586 |
| `passage_sen_ep_19_110_15` | Seneca, Epistulae Morales ad Lucilium, 110.15 | 368 |
| `passage_sen_ep_19_110_16` | Seneca, Epistulae Morales ad Lucilium, 110.16 | 167 |
| `passage_sen_ep_19_110_17` | Seneca, Epistulae Morales ad Lucilium, 110.17 | 279 |
| `passage_sen_ep_19_110_18` | Seneca, Epistulae Morales ad Lucilium, 110.18 | 321 |
| `passage_sen_ep_19_110_19` | Seneca, Epistulae Morales ad Lucilium, 110.19 | 232 |
| `passage_sen_ep_19_110_2` | Seneca, Epistulae Morales ad Lucilium, 110.2 | 407 |
| `passage_sen_ep_19_110_20` | Seneca, Epistulae Morales ad Lucilium, 110.20 | 340 |
| `passage_sen_ep_19_110_3` | Seneca, Epistulae Morales ad Lucilium, 110.3 | 371 |
| `passage_sen_ep_19_110_4` | Seneca, Epistulae Morales ad Lucilium, 110.4 | 423 |
| `passage_sen_ep_19_110_5` | Seneca, Epistulae Morales ad Lucilium, 110.5 | 356 |
| `passage_sen_ep_19_110_6` | Seneca, Epistulae Morales ad Lucilium, 110.6 | 225 |
| `passage_sen_ep_19_110_7` | Seneca, Epistulae Morales ad Lucilium, 110.7 | 395 |
| `passage_sen_ep_19_110_8` | Seneca, Epistulae Morales ad Lucilium, 110.8 | 366 |
| `passage_sen_ep_19_110_9` | Seneca, Epistulae Morales ad Lucilium, 110.9 | 410 |
| `passage_sen_ep_19_111_1` | Seneca, Epistulae Morales ad Lucilium, 111.1 | 274 |
| `passage_sen_ep_19_111_2` | Seneca, Epistulae Morales ad Lucilium, 111.2 | 272 |
| `passage_sen_ep_19_111_3` | Seneca, Epistulae Morales ad Lucilium, 111.3 | 429 |
| `passage_sen_ep_19_111_4` | Seneca, Epistulae Morales ad Lucilium, 111.4 | 389 |
| `passage_sen_ep_19_111_5` | Seneca, Epistulae Morales ad Lucilium, 111.5 | 390 |
| `passage_sen_ep_19_112_1` | Seneca, Epistulae Morales ad Lucilium, 112.1 | 225 |
| `passage_sen_ep_19_112_2` | Seneca, Epistulae Morales ad Lucilium, 112.2 | 327 |
| `passage_sen_ep_19_112_3` | Seneca, Epistulae Morales ad Lucilium, 112.3 | 289 |
| `passage_sen_ep_19_112_4` | Seneca, Epistulae Morales ad Lucilium, 112.4 | 246 |
| `passage_sen_ep_19_113_1` | Seneca, Epistulae Morales ad Lucilium, 113.1 | 529 |
| `passage_sen_ep_19_113_10` | Seneca, Epistulae Morales ad Lucilium, 113.10 | 185 |
| `passage_sen_ep_19_113_11` | Seneca, Epistulae Morales ad Lucilium, 113.11 | 439 |
| `passage_sen_ep_19_113_12` | Seneca, Epistulae Morales ad Lucilium, 113.12 | 228 |
| `passage_sen_ep_19_113_13` | Seneca, Epistulae Morales ad Lucilium, 113.13 | 211 |
| `passage_sen_ep_19_113_14` | Seneca, Epistulae Morales ad Lucilium, 113.14 | 351 |
| `passage_sen_ep_19_113_15` | Seneca, Epistulae Morales ad Lucilium, 113.15 | 315 |
| `passage_sen_ep_19_113_16` | Seneca, Epistulae Morales ad Lucilium, 113.16 | 472 |
| `passage_sen_ep_19_113_17` | Seneca, Epistulae Morales ad Lucilium, 113.17 | 260 |
| `passage_sen_ep_19_113_18` | Seneca, Epistulae Morales ad Lucilium, 113.18 | 333 |
| `passage_sen_ep_19_113_19` | Seneca, Epistulae Morales ad Lucilium, 113.19 | 274 |
| `passage_sen_ep_19_113_2` | Seneca, Epistulae Morales ad Lucilium, 113.2 | 367 |
| `passage_sen_ep_19_113_20` | Seneca, Epistulae Morales ad Lucilium, 113.20 | 465 |
| `passage_sen_ep_19_113_21` | Seneca, Epistulae Morales ad Lucilium, 113.21 | 250 |
| `passage_sen_ep_19_113_22` | Seneca, Epistulae Morales ad Lucilium, 113.22 | 408 |
| `passage_sen_ep_19_113_23` | Seneca, Epistulae Morales ad Lucilium, 113.23 | 407 |
| `passage_sen_ep_19_113_24` | Seneca, Epistulae Morales ad Lucilium, 113.24 | 288 |
| `passage_sen_ep_19_113_25` | Seneca, Epistulae Morales ad Lucilium, 113.25 | 476 |
| `passage_sen_ep_19_113_26` | Seneca, Epistulae Morales ad Lucilium, 113.26 | 488 |
| `passage_sen_ep_19_113_27` | Seneca, Epistulae Morales ad Lucilium, 113.27 | 348 |
| `passage_sen_ep_19_113_28` | Seneca, Epistulae Morales ad Lucilium, 113.28 | 217 |
| `passage_sen_ep_19_113_29` | Seneca, Epistulae Morales ad Lucilium, 113.29 | 357 |
| `passage_sen_ep_19_113_3` | Seneca, Epistulae Morales ad Lucilium, 113.3 | 500 |
| `passage_sen_ep_19_113_30` | Seneca, Epistulae Morales ad Lucilium, 113.30 | 235 |
| `passage_sen_ep_19_113_31` | Seneca, Epistulae Morales ad Lucilium, 113.31 | 603 |
| `passage_sen_ep_19_113_32` | Seneca, Epistulae Morales ad Lucilium, 113.32 | 212 |
| `passage_sen_ep_19_113_4` | Seneca, Epistulae Morales ad Lucilium, 113.4 | 361 |
| `passage_sen_ep_19_113_5` | Seneca, Epistulae Morales ad Lucilium, 113.5 | 311 |
| `passage_sen_ep_19_113_6` | Seneca, Epistulae Morales ad Lucilium, 113.6 | 340 |
| `passage_sen_ep_19_113_7` | Seneca, Epistulae Morales ad Lucilium, 113.7 | 296 |
| `passage_sen_ep_19_113_8` | Seneca, Epistulae Morales ad Lucilium, 113.8 | 233 |
| `passage_sen_ep_19_113_9` | Seneca, Epistulae Morales ad Lucilium, 113.9 | 473 |
| `passage_sen_ep_19_114_1` | Seneca, Epistulae Morales ad Lucilium, 114.1 | 553 |
| `passage_sen_ep_19_114_10` | Seneca, Epistulae Morales ad Lucilium, 114.10 | 299 |
| `passage_sen_ep_19_114_11` | Seneca, Epistulae Morales ad Lucilium, 114.11 | 559 |
| `passage_sen_ep_19_114_12` | Seneca, Epistulae Morales ad Lucilium, 114.12 | 641 |
| `passage_sen_ep_19_114_13` | Seneca, Epistulae Morales ad Lucilium, 114.13 | 367 |
| `passage_sen_ep_19_114_14` | Seneca, Epistulae Morales ad Lucilium, 114.14 | 280 |
| `passage_sen_ep_19_114_15` | Seneca, Epistulae Morales ad Lucilium, 114.15 | 347 |
| `passage_sen_ep_19_114_16` | Seneca, Epistulae Morales ad Lucilium, 114.16 | 451 |
| `passage_sen_ep_19_114_17` | Seneca, Epistulae Morales ad Lucilium, 114.17 | 616 |
| `passage_sen_ep_19_114_18` | Seneca, Epistulae Morales ad Lucilium, 114.18 | 275 |
| `passage_sen_ep_19_114_19` | Seneca, Epistulae Morales ad Lucilium, 114.19 | 535 |
| `passage_sen_ep_19_114_2` | Seneca, Epistulae Morales ad Lucilium, 114.2 | 292 |
| `passage_sen_ep_19_114_20` | Seneca, Epistulae Morales ad Lucilium, 114.20 | 277 |
| `passage_sen_ep_19_114_21` | Seneca, Epistulae Morales ad Lucilium, 114.21 | 427 |
| `passage_sen_ep_19_114_22` | Seneca, Epistulae Morales ad Lucilium, 114.22 | 420 |
| `passage_sen_ep_19_114_23` | Seneca, Epistulae Morales ad Lucilium, 114.23 | 232 |
| `passage_sen_ep_19_114_24` | Seneca, Epistulae Morales ad Lucilium, 114.24 | 471 |
| `passage_sen_ep_19_114_25` | Seneca, Epistulae Morales ad Lucilium, 114.25 | 545 |
| `passage_sen_ep_19_114_26` | Seneca, Epistulae Morales ad Lucilium, 114.26 | 560 |
| `passage_sen_ep_19_114_27` | Seneca, Epistulae Morales ad Lucilium, 114.27 | 313 |
| `passage_sen_ep_19_114_3` | Seneca, Epistulae Morales ad Lucilium, 114.3 | 571 |
| `passage_sen_ep_19_114_4` | Seneca, Epistulae Morales ad Lucilium, 114.4 | 525 |
| `passage_sen_ep_19_114_5` | Seneca, Epistulae Morales ad Lucilium, 114.5 | 433 |
| `passage_sen_ep_19_114_6` | Seneca, Epistulae Morales ad Lucilium, 114.6 | 755 |
| `passage_sen_ep_19_114_7` | Seneca, Epistulae Morales ad Lucilium, 114.7 | 207 |
| `passage_sen_ep_19_114_8` | Seneca, Epistulae Morales ad Lucilium, 114.8 | 277 |
| `passage_sen_ep_19_114_9` | Seneca, Epistulae Morales ad Lucilium, 114.9 | 527 |
| `passage_sen_ep_19_115_1` | Seneca, Epistulae Morales ad Lucilium, 115.1 | 347 |
| `passage_sen_ep_19_115_10` | Seneca, Epistulae Morales ad Lucilium, 115.10 | 397 |
| `passage_sen_ep_19_115_11` | Seneca, Epistulae Morales ad Lucilium, 115.11 | 387 |
| `passage_sen_ep_19_115_12` | Seneca, Epistulae Morales ad Lucilium, 115.12 | 207 |
| `passage_sen_ep_19_115_13` | Seneca, Epistulae Morales ad Lucilium, 115.13 | 85 |
| `passage_sen_ep_19_115_14` | Seneca, Epistulae Morales ad Lucilium, 115.14 | 89 |
| `passage_sen_ep_19_115_15` | Seneca, Epistulae Morales ad Lucilium, 115.15 | 321 |
| `passage_sen_ep_19_115_16` | Seneca, Epistulae Morales ad Lucilium, 115.16 | 446 |
| `passage_sen_ep_19_115_17` | Seneca, Epistulae Morales ad Lucilium, 115.17 | 574 |
| `passage_sen_ep_19_115_18` | Seneca, Epistulae Morales ad Lucilium, 115.18 | 468 |
| `passage_sen_ep_19_115_2` | Seneca, Epistulae Morales ad Lucilium, 115.2 | 382 |
| `passage_sen_ep_19_115_3` | Seneca, Epistulae Morales ad Lucilium, 115.3 | 609 |
| `passage_sen_ep_19_115_4` | Seneca, Epistulae Morales ad Lucilium, 115.4 | 476 |
| `passage_sen_ep_19_115_5` | Seneca, Epistulae Morales ad Lucilium, 115.5 | 192 |
| `passage_sen_ep_19_115_6` | Seneca, Epistulae Morales ad Lucilium, 115.6 | 497 |
| `passage_sen_ep_19_115_7` | Seneca, Epistulae Morales ad Lucilium, 115.7 | 199 |
| `passage_sen_ep_19_115_8` | Seneca, Epistulae Morales ad Lucilium, 115.8 | 540 |
| `passage_sen_ep_19_115_9` | Seneca, Epistulae Morales ad Lucilium, 115.9 | 433 |
| `passage_sen_ep_19_116_1` | Seneca, Epistulae Morales ad Lucilium, 116.1 | 615 |
| `passage_sen_ep_19_116_2` | Seneca, Epistulae Morales ad Lucilium, 116.2 | 391 |
| `passage_sen_ep_19_116_3` | Seneca, Epistulae Morales ad Lucilium, 116.3 | 677 |
| `passage_sen_ep_19_116_4` | Seneca, Epistulae Morales ad Lucilium, 116.4 | 163 |
| `passage_sen_ep_19_116_5` | Seneca, Epistulae Morales ad Lucilium, 116.5 | 624 |
| `passage_sen_ep_19_116_6` | Seneca, Epistulae Morales ad Lucilium, 116.6 | 162 |
| `passage_sen_ep_19_116_7` | Seneca, Epistulae Morales ad Lucilium, 116.7 | 275 |
| `passage_sen_ep_19_116_8` | Seneca, Epistulae Morales ad Lucilium, 116.8 | 320 |
| `passage_sen_ep_19_117_1` | Seneca, Epistulae Morales ad Lucilium, 117.1 | 386 |
| `passage_sen_ep_19_117_10` | Seneca, Epistulae Morales ad Lucilium, 117.10 | 264 |
| `passage_sen_ep_19_117_11` | Seneca, Epistulae Morales ad Lucilium, 117.11 | 228 |
| `passage_sen_ep_19_117_12` | Seneca, Epistulae Morales ad Lucilium, 117.12 | 588 |
| `passage_sen_ep_19_117_13` | Seneca, Epistulae Morales ad Lucilium, 117.13 | 634 |
| `passage_sen_ep_19_117_14` | Seneca, Epistulae Morales ad Lucilium, 117.14 | 389 |
| `passage_sen_ep_19_117_15` | Seneca, Epistulae Morales ad Lucilium, 117.15 | 556 |
| `passage_sen_ep_19_117_16` | Seneca, Epistulae Morales ad Lucilium, 117.16 | 517 |
| `passage_sen_ep_19_117_17` | Seneca, Epistulae Morales ad Lucilium, 117.17 | 402 |
| `passage_sen_ep_19_117_18` | Seneca, Epistulae Morales ad Lucilium, 117.18 | 319 |
| `passage_sen_ep_19_117_19` | Seneca, Epistulae Morales ad Lucilium, 117.19 | 600 |
| `passage_sen_ep_19_117_2` | Seneca, Epistulae Morales ad Lucilium, 117.2 | 275 |
| `passage_sen_ep_19_117_20` | Seneca, Epistulae Morales ad Lucilium, 117.20 | 343 |
| `passage_sen_ep_19_117_21` | Seneca, Epistulae Morales ad Lucilium, 117.21 | 498 |
| `passage_sen_ep_19_117_22` | Seneca, Epistulae Morales ad Lucilium, 117.22 | 269 |
| `passage_sen_ep_19_117_23` | Seneca, Epistulae Morales ad Lucilium, 117.23 | 471 |
| `passage_sen_ep_19_117_24` | Seneca, Epistulae Morales ad Lucilium, 117.24 | 307 |
| `passage_sen_ep_19_117_25` | Seneca, Epistulae Morales ad Lucilium, 117.25 | 470 |
| `passage_sen_ep_19_117_26` | Seneca, Epistulae Morales ad Lucilium, 117.26 | 469 |
| `passage_sen_ep_19_117_27` | Seneca, Epistulae Morales ad Lucilium, 117.27 | 312 |
| `passage_sen_ep_19_117_28` | Seneca, Epistulae Morales ad Lucilium, 117.28 | 323 |
| `passage_sen_ep_19_117_29` | Seneca, Epistulae Morales ad Lucilium, 117.29 | 264 |
| `passage_sen_ep_19_117_3` | Seneca, Epistulae Morales ad Lucilium, 117.3 | 271 |
| `passage_sen_ep_19_117_30` | Seneca, Epistulae Morales ad Lucilium, 117.30 | 314 |
| `passage_sen_ep_19_117_31` | Seneca, Epistulae Morales ad Lucilium, 117.31 | 382 |
| `passage_sen_ep_19_117_32` | Seneca, Epistulae Morales ad Lucilium, 117.32 | 374 |
| `passage_sen_ep_19_117_33` | Seneca, Epistulae Morales ad Lucilium, 117.33 | 500 |
| `passage_sen_ep_19_117_4` | Seneca, Epistulae Morales ad Lucilium, 117.4 | 245 |
| `passage_sen_ep_19_117_5` | Seneca, Epistulae Morales ad Lucilium, 117.5 | 423 |
| `passage_sen_ep_19_117_6` | Seneca, Epistulae Morales ad Lucilium, 117.6 | 628 |
| `passage_sen_ep_19_117_7` | Seneca, Epistulae Morales ad Lucilium, 117.7 | 574 |
| `passage_sen_ep_19_117_8` | Seneca, Epistulae Morales ad Lucilium, 117.8 | 464 |
| `passage_sen_ep_19_117_9` | Seneca, Epistulae Morales ad Lucilium, 117.9 | 531 |
| `passage_sen_ep_2_13_1` | Seneca, Epistulae Morales ad Lucilium, 13.1 | 436 |
| `passage_sen_ep_2_13_10` | Seneca, Epistulae Morales ad Lucilium, 13.10 | 293 |
| `passage_sen_ep_2_13_11` | Seneca, Epistulae Morales ad Lucilium, 13.11 | 398 |
| `passage_sen_ep_2_13_12` | Seneca, Epistulae Morales ad Lucilium, 13.12 | 594 |
| `passage_sen_ep_2_13_13` | Seneca, Epistulae Morales ad Lucilium, 13.13 | 504 |
| `passage_sen_ep_2_13_14` | Seneca, Epistulae Morales ad Lucilium, 13.14 | 420 |
| `passage_sen_ep_2_13_15` | Seneca, Epistulae Morales ad Lucilium, 13.15 | 187 |
| `passage_sen_ep_2_13_16` | Seneca, Epistulae Morales ad Lucilium, 13.16 | 381 |
| `passage_sen_ep_2_13_17` | Seneca, Epistulae Morales ad Lucilium, 13.17 | 313 |
| `passage_sen_ep_2_13_2` | Seneca, Epistulae Morales ad Lucilium, 13.2 | 338 |
| `passage_sen_ep_2_13_3` | Seneca, Epistulae Morales ad Lucilium, 13.3 | 247 |
| `passage_sen_ep_2_13_4` | Seneca, Epistulae Morales ad Lucilium, 13.4 | 429 |
| `passage_sen_ep_2_13_5` | Seneca, Epistulae Morales ad Lucilium, 13.5 | 458 |
| `passage_sen_ep_2_13_6` | Seneca, Epistulae Morales ad Lucilium, 13.6 | 495 |
| `passage_sen_ep_2_13_7` | Seneca, Epistulae Morales ad Lucilium, 13.7 | 279 |
| `passage_sen_ep_2_13_8` | Seneca, Epistulae Morales ad Lucilium, 13.8 | 504 |
| `passage_sen_ep_2_13_9` | Seneca, Epistulae Morales ad Lucilium, 13.9 | 264 |
| `passage_sen_ep_2_14_1` | Seneca, Epistulae Morales ad Lucilium, 14.1 | 224 |
| `passage_sen_ep_2_14_10` | Seneca, Epistulae Morales ad Lucilium, 14.10 | 380 |
| `passage_sen_ep_2_14_11` | Seneca, Epistulae Morales ad Lucilium, 14.11 | 502 |
| `passage_sen_ep_2_14_12` | Seneca, Epistulae Morales ad Lucilium, 14.12 | 222 |
| `passage_sen_ep_2_14_13` | Seneca, Epistulae Morales ad Lucilium, 14.13 | 694 |
| `passage_sen_ep_2_14_14` | Seneca, Epistulae Morales ad Lucilium, 14.14 | 296 |
| `passage_sen_ep_2_14_15` | Seneca, Epistulae Morales ad Lucilium, 14.15 | 472 |
| `passage_sen_ep_2_14_16` | Seneca, Epistulae Morales ad Lucilium, 14.16 | 230 |
| `passage_sen_ep_2_14_17` | Seneca, Epistulae Morales ad Lucilium, 14.17 | 366 |
| `passage_sen_ep_2_14_18` | Seneca, Epistulae Morales ad Lucilium, 14.18 | 278 |
| `passage_sen_ep_2_14_2` | Seneca, Epistulae Morales ad Lucilium, 14.2 | 358 |
| `passage_sen_ep_2_14_3` | Seneca, Epistulae Morales ad Lucilium, 14.3 | 273 |
| `passage_sen_ep_2_14_4` | Seneca, Epistulae Morales ad Lucilium, 14.4 | 362 |
| `passage_sen_ep_2_14_5` | Seneca, Epistulae Morales ad Lucilium, 14.5 | 271 |
| `passage_sen_ep_2_14_6` | Seneca, Epistulae Morales ad Lucilium, 14.6 | 557 |
| `passage_sen_ep_2_14_7` | Seneca, Epistulae Morales ad Lucilium, 14.7 | 426 |
| `passage_sen_ep_2_14_8` | Seneca, Epistulae Morales ad Lucilium, 14.8 | 545 |
| `passage_sen_ep_2_14_9` | Seneca, Epistulae Morales ad Lucilium, 14.9 | 408 |
| `passage_sen_ep_2_15_1` | Seneca, Epistulae Morales ad Lucilium, 15.1 | 316 |
| `passage_sen_ep_2_15_10` | Seneca, Epistulae Morales ad Lucilium, 15.10 | 256 |
| `passage_sen_ep_2_15_11` | Seneca, Epistulae Morales ad Lucilium, 15.11 | 506 |
| `passage_sen_ep_2_15_2` | Seneca, Epistulae Morales ad Lucilium, 15.2 | 504 |
| `passage_sen_ep_2_15_3` | Seneca, Epistulae Morales ad Lucilium, 15.3 | 465 |
| `passage_sen_ep_2_15_4` | Seneca, Epistulae Morales ad Lucilium, 15.4 | 370 |
| `passage_sen_ep_2_15_5` | Seneca, Epistulae Morales ad Lucilium, 15.5 | 222 |
| `passage_sen_ep_2_15_6` | Seneca, Epistulae Morales ad Lucilium, 15.6 | 298 |
| `passage_sen_ep_2_15_7` | Seneca, Epistulae Morales ad Lucilium, 15.7 | 546 |
| `passage_sen_ep_2_15_8` | Seneca, Epistulae Morales ad Lucilium, 15.8 | 341 |
| `passage_sen_ep_2_15_9` | Seneca, Epistulae Morales ad Lucilium, 15.9 | 540 |
| `passage_sen_ep_2_16_1` | Seneca, Epistulae Morales ad Lucilium, 16.1 | 430 |
| `passage_sen_ep_2_16_2` | Seneca, Epistulae Morales ad Lucilium, 16.2 | 408 |
| `passage_sen_ep_2_16_3` | Seneca, Epistulae Morales ad Lucilium, 16.3 | 488 |
| `passage_sen_ep_2_16_4` | Seneca, Epistulae Morales ad Lucilium, 16.4 | 311 |
| `passage_sen_ep_2_16_5` | Seneca, Epistulae Morales ad Lucilium, 16.5 | 362 |
| `passage_sen_ep_2_16_6` | Seneca, Epistulae Morales ad Lucilium, 16.6 | 353 |
| `passage_sen_ep_2_16_7` | Seneca, Epistulae Morales ad Lucilium, 16.7 | 367 |
| `passage_sen_ep_2_16_8` | Seneca, Epistulae Morales ad Lucilium, 16.8 | 395 |
| `passage_sen_ep_2_16_9` | Seneca, Epistulae Morales ad Lucilium, 16.9 | 400 |
| `passage_sen_ep_2_17_1` | Seneca, Epistulae Morales ad Lucilium, 17.1 | 296 |
| `passage_sen_ep_2_17_10` | Seneca, Epistulae Morales ad Lucilium, 17.10 | 305 |
| `passage_sen_ep_2_17_11` | Seneca, Epistulae Morales ad Lucilium, 17.11 | 260 |
| `passage_sen_ep_2_17_12` | Seneca, Epistulae Morales ad Lucilium, 17.12 | 380 |
| `passage_sen_ep_2_17_2` | Seneca, Epistulae Morales ad Lucilium, 17.2 | 388 |
| `passage_sen_ep_2_17_3` | Seneca, Epistulae Morales ad Lucilium, 17.3 | 481 |
| `passage_sen_ep_2_17_4` | Seneca, Epistulae Morales ad Lucilium, 17.4 | 341 |
| `passage_sen_ep_2_17_5` | Seneca, Epistulae Morales ad Lucilium, 17.5 | 449 |
| `passage_sen_ep_2_17_6` | Seneca, Epistulae Morales ad Lucilium, 17.6 | 384 |
| `passage_sen_ep_2_17_7` | Seneca, Epistulae Morales ad Lucilium, 17.7 | 316 |
| `passage_sen_ep_2_17_8` | Seneca, Epistulae Morales ad Lucilium, 17.8 | 263 |
| `passage_sen_ep_2_17_9` | Seneca, Epistulae Morales ad Lucilium, 17.9 | 490 |
| `passage_sen_ep_2_18_1` | Seneca, Epistulae Morales ad Lucilium, 18.1 | 281 |
| `passage_sen_ep_2_18_10` | Seneca, Epistulae Morales ad Lucilium, 18.10 | 341 |
| `passage_sen_ep_2_18_11` | Seneca, Epistulae Morales ad Lucilium, 18.11 | 252 |
| `passage_sen_ep_2_18_12` | Seneca, Epistulae Morales ad Lucilium, 18.12 | 175 |
| `passage_sen_ep_2_18_13` | Seneca, Epistulae Morales ad Lucilium, 18.13 | 267 |
| `passage_sen_ep_2_18_14` | Seneca, Epistulae Morales ad Lucilium, 18.14 | 234 |
| `passage_sen_ep_2_18_15` | Seneca, Epistulae Morales ad Lucilium, 18.15 | 493 |
| `passage_sen_ep_2_18_2` | Seneca, Epistulae Morales ad Lucilium, 18.2 | 339 |
| `passage_sen_ep_2_18_3` | Seneca, Epistulae Morales ad Lucilium, 18.3 | 361 |
| `passage_sen_ep_2_18_4` | Seneca, Epistulae Morales ad Lucilium, 18.4 | 223 |
| `passage_sen_ep_2_18_5` | Seneca, Epistulae Morales ad Lucilium, 18.5 | 246 |
| `passage_sen_ep_2_18_6` | Seneca, Epistulae Morales ad Lucilium, 18.6 | 419 |
| `passage_sen_ep_2_18_7` | Seneca, Epistulae Morales ad Lucilium, 18.7 | 442 |
| `passage_sen_ep_2_18_8` | Seneca, Epistulae Morales ad Lucilium, 18.8 | 403 |
| `passage_sen_ep_2_18_9` | Seneca, Epistulae Morales ad Lucilium, 18.9 | 387 |
| `passage_sen_ep_2_19_1` | Seneca, Epistulae Morales ad Lucilium, 19.1 | 346 |
| `passage_sen_ep_2_19_10` | Seneca, Epistulae Morales ad Lucilium, 19.10 | 350 |
| `passage_sen_ep_2_19_11` | Seneca, Epistulae Morales ad Lucilium, 19.11 | 449 |
| `passage_sen_ep_2_19_12` | Seneca, Epistulae Morales ad Lucilium, 19.12 | 261 |
| `passage_sen_ep_2_19_2` | Seneca, Epistulae Morales ad Lucilium, 19.2 | 311 |
| `passage_sen_ep_2_19_3` | Seneca, Epistulae Morales ad Lucilium, 19.3 | 312 |
| `passage_sen_ep_2_19_4` | Seneca, Epistulae Morales ad Lucilium, 19.4 | 485 |
| `passage_sen_ep_2_19_5` | Seneca, Epistulae Morales ad Lucilium, 19.5 | 275 |
| `passage_sen_ep_2_19_6` | Seneca, Epistulae Morales ad Lucilium, 19.6 | 388 |
| `passage_sen_ep_2_19_7` | Seneca, Epistulae Morales ad Lucilium, 19.7 | 287 |
| `passage_sen_ep_2_19_8` | Seneca, Epistulae Morales ad Lucilium, 19.8 | 504 |
| `passage_sen_ep_2_19_9` | Seneca, Epistulae Morales ad Lucilium, 19.9 | 490 |
| `passage_sen_ep_2_20_1` | Seneca, Epistulae Morales ad Lucilium, 20.1 | 358 |
| `passage_sen_ep_2_20_10` | Seneca, Epistulae Morales ad Lucilium, 20.10 | 310 |
| `passage_sen_ep_2_20_11` | Seneca, Epistulae Morales ad Lucilium, 20.11 | 413 |
| `passage_sen_ep_2_20_12` | Seneca, Epistulae Morales ad Lucilium, 20.12 | 242 |
| `passage_sen_ep_2_20_13` | Seneca, Epistulae Morales ad Lucilium, 20.13 | 480 |
| `passage_sen_ep_2_20_2` | Seneca, Epistulae Morales ad Lucilium, 20.2 | 589 |
| `passage_sen_ep_2_20_3` | Seneca, Epistulae Morales ad Lucilium, 20.3 | 374 |
| `passage_sen_ep_2_20_4` | Seneca, Epistulae Morales ad Lucilium, 20.4 | 242 |
| `passage_sen_ep_2_20_5` | Seneca, Epistulae Morales ad Lucilium, 20.5 | 300 |
| `passage_sen_ep_2_20_6` | Seneca, Epistulae Morales ad Lucilium, 20.6 | 312 |
| `passage_sen_ep_2_20_7` | Seneca, Epistulae Morales ad Lucilium, 20.7 | 412 |
| `passage_sen_ep_2_20_8` | Seneca, Epistulae Morales ad Lucilium, 20.8 | 321 |
| `passage_sen_ep_2_20_9` | Seneca, Epistulae Morales ad Lucilium, 20.9 | 341 |
| `passage_sen_ep_2_21_1` | Seneca, Epistulae Morales ad Lucilium, 21.1 | 506 |
| `passage_sen_ep_2_21_10` | Seneca, Epistulae Morales ad Lucilium, 21.10 | 442 |
| `passage_sen_ep_2_21_11` | Seneca, Epistulae Morales ad Lucilium, 21.11 | 457 |
| `passage_sen_ep_2_21_2` | Seneca, Epistulae Morales ad Lucilium, 21.2 | 357 |
| `passage_sen_ep_2_21_3` | Seneca, Epistulae Morales ad Lucilium, 21.3 | 298 |
| `passage_sen_ep_2_21_4` | Seneca, Epistulae Morales ad Lucilium, 21.4 | 414 |
| `passage_sen_ep_2_21_5` | Seneca, Epistulae Morales ad Lucilium, 21.5 | 356 |
| `passage_sen_ep_2_21_6` | Seneca, Epistulae Morales ad Lucilium, 21.6 | 300 |
| `passage_sen_ep_2_21_7` | Seneca, Epistulae Morales ad Lucilium, 21.7 | 302 |
| `passage_sen_ep_2_21_8` | Seneca, Epistulae Morales ad Lucilium, 21.8 | 503 |
| `passage_sen_ep_2_21_9` | Seneca, Epistulae Morales ad Lucilium, 21.9 | 441 |
| `passage_sen_ep_20_118_1` | Seneca, Epistulae Morales ad Lucilium, 118.1 | 354 |
| `passage_sen_ep_20_118_10` | Seneca, Epistulae Morales ad Lucilium, 118.10 | 329 |
| `passage_sen_ep_20_118_11` | Seneca, Epistulae Morales ad Lucilium, 118.11 | 363 |
| `passage_sen_ep_20_118_12` | Seneca, Epistulae Morales ad Lucilium, 118.12 | 489 |
| `passage_sen_ep_20_118_13` | Seneca, Epistulae Morales ad Lucilium, 118.13 | 308 |
| `passage_sen_ep_20_118_14` | Seneca, Epistulae Morales ad Lucilium, 118.14 | 235 |
| `passage_sen_ep_20_118_15` | Seneca, Epistulae Morales ad Lucilium, 118.15 | 266 |
| `passage_sen_ep_20_118_16` | Seneca, Epistulae Morales ad Lucilium, 118.16 | 358 |
| `passage_sen_ep_20_118_17` | Seneca, Epistulae Morales ad Lucilium, 118.17 | 532 |
| `passage_sen_ep_20_118_2` | Seneca, Epistulae Morales ad Lucilium, 118.2 | 444 |
| `passage_sen_ep_20_118_3` | Seneca, Epistulae Morales ad Lucilium, 118.3 | 447 |
| `passage_sen_ep_20_118_4` | Seneca, Epistulae Morales ad Lucilium, 118.4 | 518 |
| `passage_sen_ep_20_118_5` | Seneca, Epistulae Morales ad Lucilium, 118.5 | 233 |
| `passage_sen_ep_20_118_6` | Seneca, Epistulae Morales ad Lucilium, 118.6 | 330 |
| `passage_sen_ep_20_118_7` | Seneca, Epistulae Morales ad Lucilium, 118.7 | 248 |
| `passage_sen_ep_20_118_8` | Seneca, Epistulae Morales ad Lucilium, 118.8 | 488 |
| `passage_sen_ep_20_118_9` | Seneca, Epistulae Morales ad Lucilium, 118.9 | 397 |
| `passage_sen_ep_20_119_1` | Seneca, Epistulae Morales ad Lucilium, 119.1 | 427 |
| `passage_sen_ep_20_119_10` | Seneca, Epistulae Morales ad Lucilium, 119.10 | 264 |
| `passage_sen_ep_20_119_11` | Seneca, Epistulae Morales ad Lucilium, 119.11 | 310 |
| `passage_sen_ep_20_119_12` | Seneca, Epistulae Morales ad Lucilium, 119.12 | 441 |
| `passage_sen_ep_20_119_13` | Seneca, Epistulae Morales ad Lucilium, 119.13 | 128 |
| `passage_sen_ep_20_119_14` | Seneca, Epistulae Morales ad Lucilium, 119.14 | 471 |
| `passage_sen_ep_20_119_15` | Seneca, Epistulae Morales ad Lucilium, 119.15 | 385 |
| `passage_sen_ep_20_119_16` | Seneca, Epistulae Morales ad Lucilium, 119.16 | 200 |
| `passage_sen_ep_20_119_2` | Seneca, Epistulae Morales ad Lucilium, 119.2 | 418 |
| `passage_sen_ep_20_119_3` | Seneca, Epistulae Morales ad Lucilium, 119.3 | 427 |
| `passage_sen_ep_20_119_4` | Seneca, Epistulae Morales ad Lucilium, 119.4 | 152 |
| `passage_sen_ep_20_119_5` | Seneca, Epistulae Morales ad Lucilium, 119.5 | 632 |
| `passage_sen_ep_20_119_6` | Seneca, Epistulae Morales ad Lucilium, 119.6 | 400 |
| `passage_sen_ep_20_119_7` | Seneca, Epistulae Morales ad Lucilium, 119.7 | 387 |
| `passage_sen_ep_20_119_8` | Seneca, Epistulae Morales ad Lucilium, 119.8 | 253 |
| `passage_sen_ep_20_119_9` | Seneca, Epistulae Morales ad Lucilium, 119.9 | 398 |
| `passage_sen_ep_20_120_1` | Seneca, Epistulae Morales ad Lucilium, 120.1 | 208 |
| `passage_sen_ep_20_120_10` | Seneca, Epistulae Morales ad Lucilium, 120.10 | 561 |
| `passage_sen_ep_20_120_11` | Seneca, Epistulae Morales ad Lucilium, 120.11 | 459 |
| `passage_sen_ep_20_120_12` | Seneca, Epistulae Morales ad Lucilium, 120.12 | 416 |
| `passage_sen_ep_20_120_13` | Seneca, Epistulae Morales ad Lucilium, 120.13 | 273 |
| `passage_sen_ep_20_120_14` | Seneca, Epistulae Morales ad Lucilium, 120.14 | 381 |
| `passage_sen_ep_20_120_15` | Seneca, Epistulae Morales ad Lucilium, 120.15 | 295 |
| `passage_sen_ep_20_120_16` | Seneca, Epistulae Morales ad Lucilium, 120.16 | 280 |
| `passage_sen_ep_20_120_17` | Seneca, Epistulae Morales ad Lucilium, 120.17 | 418 |
| `passage_sen_ep_20_120_18` | Seneca, Epistulae Morales ad Lucilium, 120.18 | 577 |
| `passage_sen_ep_20_120_19` | Seneca, Epistulae Morales ad Lucilium, 120.19 | 433 |
| `passage_sen_ep_20_120_2` | Seneca, Epistulae Morales ad Lucilium, 120.2 | 412 |
| `passage_sen_ep_20_120_20` | Seneca, Epistulae Morales ad Lucilium, 120.20 | 129 |
| `passage_sen_ep_20_120_21` | Seneca, Epistulae Morales ad Lucilium, 120.21 | 452 |
| `passage_sen_ep_20_120_22` | Seneca, Epistulae Morales ad Lucilium, 120.22 | 565 |
| `passage_sen_ep_20_120_3` | Seneca, Epistulae Morales ad Lucilium, 120.3 | 397 |
| `passage_sen_ep_20_120_4` | Seneca, Epistulae Morales ad Lucilium, 120.4 | 509 |
| `passage_sen_ep_20_120_5` | Seneca, Epistulae Morales ad Lucilium, 120.5 | 494 |
| `passage_sen_ep_20_120_6` | Seneca, Epistulae Morales ad Lucilium, 120.6 | 631 |
| `passage_sen_ep_20_120_7` | Seneca, Epistulae Morales ad Lucilium, 120.7 | 507 |
| `passage_sen_ep_20_120_8` | Seneca, Epistulae Morales ad Lucilium, 120.8 | 530 |
| `passage_sen_ep_20_120_9` | Seneca, Epistulae Morales ad Lucilium, 120.9 | 388 |
| `passage_sen_ep_20_121_1` | Seneca, Epistulae Morales ad Lucilium, 121.1 | 313 |
| `passage_sen_ep_20_121_10` | Seneca, Epistulae Morales ad Lucilium, 121.10 | 426 |
| `passage_sen_ep_20_121_11` | Seneca, Epistulae Morales ad Lucilium, 121.11 | 173 |
| `passage_sen_ep_20_121_12` | Seneca, Epistulae Morales ad Lucilium, 121.12 | 425 |
| `passage_sen_ep_20_121_13` | Seneca, Epistulae Morales ad Lucilium, 121.13 | 256 |
| `passage_sen_ep_20_121_14` | Seneca, Epistulae Morales ad Lucilium, 121.14 | 458 |
| `passage_sen_ep_20_121_15` | Seneca, Epistulae Morales ad Lucilium, 121.15 | 438 |
| `passage_sen_ep_20_121_16` | Seneca, Epistulae Morales ad Lucilium, 121.16 | 488 |
| `passage_sen_ep_20_121_17` | Seneca, Epistulae Morales ad Lucilium, 121.17 | 311 |
| `passage_sen_ep_20_121_18` | Seneca, Epistulae Morales ad Lucilium, 121.18 | 395 |
| `passage_sen_ep_20_121_19` | Seneca, Epistulae Morales ad Lucilium, 121.19 | 521 |
| `passage_sen_ep_20_121_2` | Seneca, Epistulae Morales ad Lucilium, 121.2 | 303 |
| `passage_sen_ep_20_121_20` | Seneca, Epistulae Morales ad Lucilium, 121.20 | 382 |
| `passage_sen_ep_20_121_21` | Seneca, Epistulae Morales ad Lucilium, 121.21 | 521 |
| `passage_sen_ep_20_121_22` | Seneca, Epistulae Morales ad Lucilium, 121.22 | 391 |
| `passage_sen_ep_20_121_23` | Seneca, Epistulae Morales ad Lucilium, 121.23 | 346 |
| `passage_sen_ep_20_121_24` | Seneca, Epistulae Morales ad Lucilium, 121.24 | 468 |
| `passage_sen_ep_20_121_3` | Seneca, Epistulae Morales ad Lucilium, 121.3 | 344 |
| `passage_sen_ep_20_121_4` | Seneca, Epistulae Morales ad Lucilium, 121.4 | 544 |
| `passage_sen_ep_20_121_5` | Seneca, Epistulae Morales ad Lucilium, 121.5 | 551 |
| `passage_sen_ep_20_121_6` | Seneca, Epistulae Morales ad Lucilium, 121.6 | 320 |
| `passage_sen_ep_20_121_7` | Seneca, Epistulae Morales ad Lucilium, 121.7 | 372 |
| `passage_sen_ep_20_121_8` | Seneca, Epistulae Morales ad Lucilium, 121.8 | 448 |
| `passage_sen_ep_20_121_9` | Seneca, Epistulae Morales ad Lucilium, 121.9 | 207 |
| `passage_sen_ep_20_122_1` | Seneca, Epistulae Morales ad Lucilium, 122.1 | 317 |
| `passage_sen_ep_20_122_10` | Seneca, Epistulae Morales ad Lucilium, 122.10 | 321 |
| `passage_sen_ep_20_122_11` | Seneca, Epistulae Morales ad Lucilium, 122.11 | 330 |
| `passage_sen_ep_20_122_12` | Seneca, Epistulae Morales ad Lucilium, 122.12 | 197 |
| `passage_sen_ep_20_122_13` | Seneca, Epistulae Morales ad Lucilium, 122.13 | 173 |
| `passage_sen_ep_20_122_14` | Seneca, Epistulae Morales ad Lucilium, 122.14 | 633 |
| `passage_sen_ep_20_122_15` | Seneca, Epistulae Morales ad Lucilium, 122.15 | 452 |
| `passage_sen_ep_20_122_16` | Seneca, Epistulae Morales ad Lucilium, 122.16 | 357 |
| `passage_sen_ep_20_122_17` | Seneca, Epistulae Morales ad Lucilium, 122.17 | 371 |
| `passage_sen_ep_20_122_18` | Seneca, Epistulae Morales ad Lucilium, 122.18 | 332 |
| `passage_sen_ep_20_122_19` | Seneca, Epistulae Morales ad Lucilium, 122.19 | 215 |
| `passage_sen_ep_20_122_2` | Seneca, Epistulae Morales ad Lucilium, 122.2 | 393 |
| `passage_sen_ep_20_122_3` | Seneca, Epistulae Morales ad Lucilium, 122.3 | 545 |
| `passage_sen_ep_20_122_4` | Seneca, Epistulae Morales ad Lucilium, 122.4 | 555 |
| `passage_sen_ep_20_122_5` | Seneca, Epistulae Morales ad Lucilium, 122.5 | 303 |
| `passage_sen_ep_20_122_6` | Seneca, Epistulae Morales ad Lucilium, 122.6 | 562 |
| `passage_sen_ep_20_122_7` | Seneca, Epistulae Morales ad Lucilium, 122.7 | 321 |
| `passage_sen_ep_20_122_8` | Seneca, Epistulae Morales ad Lucilium, 122.8 | 485 |
| `passage_sen_ep_20_122_9` | Seneca, Epistulae Morales ad Lucilium, 122.9 | 376 |
| `passage_sen_ep_20_123_1` | Seneca, Epistulae Morales ad Lucilium, 123.1 | 313 |
| `passage_sen_ep_20_123_10` | Seneca, Epistulae Morales ad Lucilium, 123.10 | 647 |
| `passage_sen_ep_20_123_11` | Seneca, Epistulae Morales ad Lucilium, 123.11 | 329 |
| `passage_sen_ep_20_123_12` | Seneca, Epistulae Morales ad Lucilium, 123.12 | 320 |
| `passage_sen_ep_20_123_13` | Seneca, Epistulae Morales ad Lucilium, 123.13 | 374 |
| `passage_sen_ep_20_123_14` | Seneca, Epistulae Morales ad Lucilium, 123.14 | 355 |
| `passage_sen_ep_20_123_15` | Seneca, Epistulae Morales ad Lucilium, 123.15 | 444 |
| `passage_sen_ep_20_123_16` | Seneca, Epistulae Morales ad Lucilium, 123.16 | 539 |
| `passage_sen_ep_20_123_17` | Seneca, Epistulae Morales ad Lucilium, 123.17 | 167 |
| `passage_sen_ep_20_123_2` | Seneca, Epistulae Morales ad Lucilium, 123.2 | 320 |
| `passage_sen_ep_20_123_3` | Seneca, Epistulae Morales ad Lucilium, 123.3 | 328 |
| `passage_sen_ep_20_123_4` | Seneca, Epistulae Morales ad Lucilium, 123.4 | 257 |
| `passage_sen_ep_20_123_5` | Seneca, Epistulae Morales ad Lucilium, 123.5 | 442 |
| `passage_sen_ep_20_123_6` | Seneca, Epistulae Morales ad Lucilium, 123.6 | 501 |
| `passage_sen_ep_20_123_7` | Seneca, Epistulae Morales ad Lucilium, 123.7 | 560 |
| `passage_sen_ep_20_123_8` | Seneca, Epistulae Morales ad Lucilium, 123.8 | 342 |
| `passage_sen_ep_20_123_9` | Seneca, Epistulae Morales ad Lucilium, 123.9 | 432 |
| `passage_sen_ep_20_124_1` | Seneca, Epistulae Morales ad Lucilium, 124.1 | 371 |
| `passage_sen_ep_20_124_10` | Seneca, Epistulae Morales ad Lucilium, 124.10 | 260 |
| `passage_sen_ep_20_124_11` | Seneca, Epistulae Morales ad Lucilium, 124.11 | 408 |
| `passage_sen_ep_20_124_12` | Seneca, Epistulae Morales ad Lucilium, 124.12 | 286 |
| `passage_sen_ep_20_124_13` | Seneca, Epistulae Morales ad Lucilium, 124.13 | 410 |
| `passage_sen_ep_20_124_14` | Seneca, Epistulae Morales ad Lucilium, 124.14 | 497 |
| `passage_sen_ep_20_124_15` | Seneca, Epistulae Morales ad Lucilium, 124.15 | 209 |
| `passage_sen_ep_20_124_16` | Seneca, Epistulae Morales ad Lucilium, 124.16 | 304 |
| `passage_sen_ep_20_124_17` | Seneca, Epistulae Morales ad Lucilium, 124.17 | 302 |
| `passage_sen_ep_20_124_18` | Seneca, Epistulae Morales ad Lucilium, 124.18 | 299 |
| `passage_sen_ep_20_124_19` | Seneca, Epistulae Morales ad Lucilium, 124.19 | 406 |
| `passage_sen_ep_20_124_2` | Seneca, Epistulae Morales ad Lucilium, 124.2 | 299 |
| `passage_sen_ep_20_124_20` | Seneca, Epistulae Morales ad Lucilium, 124.20 | 287 |
| `passage_sen_ep_20_124_21` | Seneca, Epistulae Morales ad Lucilium, 124.21 | 352 |
| `passage_sen_ep_20_124_22` | Seneca, Epistulae Morales ad Lucilium, 124.22 | 552 |
| `passage_sen_ep_20_124_23` | Seneca, Epistulae Morales ad Lucilium, 124.23 | 429 |
| `passage_sen_ep_20_124_24` | Seneca, Epistulae Morales ad Lucilium, 124.24 | 144 |
| `passage_sen_ep_20_124_3` | Seneca, Epistulae Morales ad Lucilium, 124.3 | 346 |
| `passage_sen_ep_20_124_4` | Seneca, Epistulae Morales ad Lucilium, 124.4 | 305 |
| `passage_sen_ep_20_124_5` | Seneca, Epistulae Morales ad Lucilium, 124.5 | 506 |
| `passage_sen_ep_20_124_6` | Seneca, Epistulae Morales ad Lucilium, 124.6 | 64 |
| `passage_sen_ep_20_124_7` | Seneca, Epistulae Morales ad Lucilium, 124.7 | 325 |
| `passage_sen_ep_20_124_8` | Seneca, Epistulae Morales ad Lucilium, 124.8 | 764 |
| `passage_sen_ep_20_124_9` | Seneca, Epistulae Morales ad Lucilium, 124.9 | 234 |
| `passage_sen_ep_3_22_1` | Seneca, Epistulae Morales ad Lucilium, 22.1 | 402 |
| `passage_sen_ep_3_22_10` | Seneca, Epistulae Morales ad Lucilium, 22.10 | 304 |
| `passage_sen_ep_3_22_11` | Seneca, Epistulae Morales ad Lucilium, 22.11 | 329 |
| `passage_sen_ep_3_22_12` | Seneca, Epistulae Morales ad Lucilium, 22.12 | 382 |
| `passage_sen_ep_3_22_13` | Seneca, Epistulae Morales ad Lucilium, 22.13 | 302 |
| `passage_sen_ep_3_22_14` | Seneca, Epistulae Morales ad Lucilium, 22.14 | 242 |
| `passage_sen_ep_3_22_15` | Seneca, Epistulae Morales ad Lucilium, 22.15 | 323 |
| `passage_sen_ep_3_22_16` | Seneca, Epistulae Morales ad Lucilium, 22.16 | 248 |
| `passage_sen_ep_3_22_17` | Seneca, Epistulae Morales ad Lucilium, 22.17 | 262 |
| `passage_sen_ep_3_22_2` | Seneca, Epistulae Morales ad Lucilium, 22.2 | 249 |
| `passage_sen_ep_3_22_3` | Seneca, Epistulae Morales ad Lucilium, 22.3 | 499 |
| `passage_sen_ep_3_22_4` | Seneca, Epistulae Morales ad Lucilium, 22.4 | 428 |
| `passage_sen_ep_3_22_5` | Seneca, Epistulae Morales ad Lucilium, 22.5 | 341 |
| `passage_sen_ep_3_22_6` | Seneca, Epistulae Morales ad Lucilium, 22.6 | 287 |
| `passage_sen_ep_3_22_7` | Seneca, Epistulae Morales ad Lucilium, 22.7 | 339 |
| `passage_sen_ep_3_22_8` | Seneca, Epistulae Morales ad Lucilium, 22.8 | 448 |
| `passage_sen_ep_3_22_9` | Seneca, Epistulae Morales ad Lucilium, 22.9 | 334 |
| `passage_sen_ep_3_23_1` | Seneca, Epistulae Morales ad Lucilium, 23.1 | 396 |
| `passage_sen_ep_3_23_10` | Seneca, Epistulae Morales ad Lucilium, 23.10 | 242 |
| `passage_sen_ep_3_23_11` | Seneca, Epistulae Morales ad Lucilium, 23.11 | 214 |
| `passage_sen_ep_3_23_2` | Seneca, Epistulae Morales ad Lucilium, 23.2 | 245 |
| `passage_sen_ep_3_23_3` | Seneca, Epistulae Morales ad Lucilium, 23.3 | 464 |
| `passage_sen_ep_3_23_4` | Seneca, Epistulae Morales ad Lucilium, 23.4 | 383 |
| `passage_sen_ep_3_23_5` | Seneca, Epistulae Morales ad Lucilium, 23.5 | 348 |
| `passage_sen_ep_3_23_6` | Seneca, Epistulae Morales ad Lucilium, 23.6 | 642 |
| `passage_sen_ep_3_23_7` | Seneca, Epistulae Morales ad Lucilium, 23.7 | 380 |
| `passage_sen_ep_3_23_8` | Seneca, Epistulae Morales ad Lucilium, 23.8 | 340 |
| `passage_sen_ep_3_23_9` | Seneca, Epistulae Morales ad Lucilium, 23.9 | 238 |
| `passage_sen_ep_3_24_1` | Seneca, Epistulae Morales ad Lucilium, 24.1 | 403 |
| `passage_sen_ep_3_24_10` | Seneca, Epistulae Morales ad Lucilium, 24.10 | 251 |
| `passage_sen_ep_3_24_11` | Seneca, Epistulae Morales ad Lucilium, 24.11 | 388 |
| `passage_sen_ep_3_24_12` | Seneca, Epistulae Morales ad Lucilium, 24.12 | 304 |
| `passage_sen_ep_3_24_13` | Seneca, Epistulae Morales ad Lucilium, 24.13 | 237 |
| `passage_sen_ep_3_24_14` | Seneca, Epistulae Morales ad Lucilium, 24.14 | 718 |
| `passage_sen_ep_3_24_15` | Seneca, Epistulae Morales ad Lucilium, 24.15 | 349 |
| `passage_sen_ep_3_24_16` | Seneca, Epistulae Morales ad Lucilium, 24.16 | 503 |
| `passage_sen_ep_3_24_17` | Seneca, Epistulae Morales ad Lucilium, 24.17 | 259 |
| `passage_sen_ep_3_24_18` | Seneca, Epistulae Morales ad Lucilium, 24.18 | 451 |
| `passage_sen_ep_3_24_19` | Seneca, Epistulae Morales ad Lucilium, 24.19 | 326 |
| `passage_sen_ep_3_24_2` | Seneca, Epistulae Morales ad Lucilium, 24.2 | 230 |
| `passage_sen_ep_3_24_20` | Seneca, Epistulae Morales ad Lucilium, 24.20 | 461 |
| `passage_sen_ep_3_24_21` | Seneca, Epistulae Morales ad Lucilium, 24.21 | 231 |
| `passage_sen_ep_3_24_22` | Seneca, Epistulae Morales ad Lucilium, 24.22 | 370 |
| `passage_sen_ep_3_24_23` | Seneca, Epistulae Morales ad Lucilium, 24.23 | 248 |
| `passage_sen_ep_3_24_24` | Seneca, Epistulae Morales ad Lucilium, 24.24 | 261 |
| `passage_sen_ep_3_24_25` | Seneca, Epistulae Morales ad Lucilium, 24.25 | 350 |
| `passage_sen_ep_3_24_26` | Seneca, Epistulae Morales ad Lucilium, 24.26 | 579 |
| `passage_sen_ep_3_24_3` | Seneca, Epistulae Morales ad Lucilium, 24.3 | 473 |
| `passage_sen_ep_3_24_4` | Seneca, Epistulae Morales ad Lucilium, 24.4 | 438 |
| `passage_sen_ep_3_24_5` | Seneca, Epistulae Morales ad Lucilium, 24.5 | 637 |
| `passage_sen_ep_3_24_6` | Seneca, Epistulae Morales ad Lucilium, 24.6 | 473 |
| `passage_sen_ep_3_24_7` | Seneca, Epistulae Morales ad Lucilium, 24.7 | 342 |
| `passage_sen_ep_3_24_8` | Seneca, Epistulae Morales ad Lucilium, 24.8 | 271 |
| `passage_sen_ep_3_24_9` | Seneca, Epistulae Morales ad Lucilium, 24.9 | 522 |
| `passage_sen_ep_3_25_1` | Seneca, Epistulae Morales ad Lucilium, 25.1 | 297 |
| `passage_sen_ep_3_25_2` | Seneca, Epistulae Morales ad Lucilium, 25.2 | 488 |
| `passage_sen_ep_3_25_3` | Seneca, Epistulae Morales ad Lucilium, 25.3 | 308 |
| `passage_sen_ep_3_25_4` | Seneca, Epistulae Morales ad Lucilium, 25.4 | 401 |
| `passage_sen_ep_3_25_5` | Seneca, Epistulae Morales ad Lucilium, 25.5 | 404 |
| `passage_sen_ep_3_25_6` | Seneca, Epistulae Morales ad Lucilium, 25.6 | 473 |
| `passage_sen_ep_3_25_7` | Seneca, Epistulae Morales ad Lucilium, 25.7 | 338 |
| `passage_sen_ep_3_26_1` | Seneca, Epistulae Morales ad Lucilium, 26.1 | 271 |
| `passage_sen_ep_3_26_10` | Seneca, Epistulae Morales ad Lucilium, 26.10 | 445 |
| `passage_sen_ep_3_26_2` | Seneca, Epistulae Morales ad Lucilium, 26.2 | 307 |
| `passage_sen_ep_3_26_3` | Seneca, Epistulae Morales ad Lucilium, 26.3 | 357 |
| `passage_sen_ep_3_26_4` | Seneca, Epistulae Morales ad Lucilium, 26.4 | 485 |
| `passage_sen_ep_3_26_5` | Seneca, Epistulae Morales ad Lucilium, 26.5 | 396 |
| `passage_sen_ep_3_26_6` | Seneca, Epistulae Morales ad Lucilium, 26.6 | 419 |
| `passage_sen_ep_3_26_7` | Seneca, Epistulae Morales ad Lucilium, 26.7 | 178 |
| `passage_sen_ep_3_26_8` | Seneca, Epistulae Morales ad Lucilium, 26.8 | 337 |
| `passage_sen_ep_3_26_9` | Seneca, Epistulae Morales ad Lucilium, 26.9 | 219 |
| `passage_sen_ep_3_27_1` | Seneca, Epistulae Morales ad Lucilium, 27.1 | 346 |
| `passage_sen_ep_3_27_2` | Seneca, Epistulae Morales ad Lucilium, 27.2 | 480 |
| `passage_sen_ep_3_27_3` | Seneca, Epistulae Morales ad Lucilium, 27.3 | 238 |
| `passage_sen_ep_3_27_4` | Seneca, Epistulae Morales ad Lucilium, 27.4 | 223 |
| `passage_sen_ep_3_27_5` | Seneca, Epistulae Morales ad Lucilium, 27.5 | 478 |
| `passage_sen_ep_3_27_6` | Seneca, Epistulae Morales ad Lucilium, 27.6 | 414 |
| `passage_sen_ep_3_27_7` | Seneca, Epistulae Morales ad Lucilium, 27.7 | 365 |
| `passage_sen_ep_3_27_8` | Seneca, Epistulae Morales ad Lucilium, 27.8 | 356 |
| `passage_sen_ep_3_27_9` | Seneca, Epistulae Morales ad Lucilium, 27.9 | 254 |
| `passage_sen_ep_3_28_1` | Seneca, Epistulae Morales ad Lucilium, 28.1 | 303 |
| `passage_sen_ep_3_28_10` | Seneca, Epistulae Morales ad Lucilium, 28.10 | 262 |
| `passage_sen_ep_3_28_2` | Seneca, Epistulae Morales ad Lucilium, 28.2 | 371 |
| `passage_sen_ep_3_28_3` | Seneca, Epistulae Morales ad Lucilium, 28.3 | 422 |
| `passage_sen_ep_3_28_4` | Seneca, Epistulae Morales ad Lucilium, 28.4 | 365 |
| `passage_sen_ep_3_28_5` | Seneca, Epistulae Morales ad Lucilium, 28.5 | 298 |
| `passage_sen_ep_3_28_6` | Seneca, Epistulae Morales ad Lucilium, 28.6 | 323 |
| `passage_sen_ep_3_28_7` | Seneca, Epistulae Morales ad Lucilium, 28.7 | 276 |
| `passage_sen_ep_3_28_8` | Seneca, Epistulae Morales ad Lucilium, 28.8 | 209 |
| `passage_sen_ep_3_28_9` | Seneca, Epistulae Morales ad Lucilium, 28.9 | 222 |
| `passage_sen_ep_3_29_1` | Seneca, Epistulae Morales ad Lucilium, 29.1 | 329 |
| `passage_sen_ep_3_29_10` | Seneca, Epistulae Morales ad Lucilium, 29.10 | 248 |
| `passage_sen_ep_3_29_11` | Seneca, Epistulae Morales ad Lucilium, 29.11 | 440 |
| `passage_sen_ep_3_29_12` | Seneca, Epistulae Morales ad Lucilium, 29.12 | 487 |
| `passage_sen_ep_3_29_2` | Seneca, Epistulae Morales ad Lucilium, 29.2 | 303 |
| `passage_sen_ep_3_29_3` | Seneca, Epistulae Morales ad Lucilium, 29.3 | 417 |
| `passage_sen_ep_3_29_4` | Seneca, Epistulae Morales ad Lucilium, 29.4 | 272 |
| `passage_sen_ep_3_29_5` | Seneca, Epistulae Morales ad Lucilium, 29.5 | 305 |
| `passage_sen_ep_3_29_6` | Seneca, Epistulae Morales ad Lucilium, 29.6 | 383 |
| `passage_sen_ep_3_29_7` | Seneca, Epistulae Morales ad Lucilium, 29.7 | 404 |
| `passage_sen_ep_3_29_8` | Seneca, Epistulae Morales ad Lucilium, 29.8 | 339 |
| `passage_sen_ep_3_29_9` | Seneca, Epistulae Morales ad Lucilium, 29.9 | 469 |
| `passage_sen_ep_4_30_1` | Seneca, Epistulae Morales ad Lucilium, 30.1 | 289 |
| `passage_sen_ep_4_30_10` | Seneca, Epistulae Morales ad Lucilium, 30.10 | 352 |
| `passage_sen_ep_4_30_11` | Seneca, Epistulae Morales ad Lucilium, 30.11 | 321 |
| `passage_sen_ep_4_30_12` | Seneca, Epistulae Morales ad Lucilium, 30.12 | 627 |
| `passage_sen_ep_4_30_13` | Seneca, Epistulae Morales ad Lucilium, 30.13 | 294 |
| `passage_sen_ep_4_30_14` | Seneca, Epistulae Morales ad Lucilium, 30.14 | 599 |
| `passage_sen_ep_4_30_15` | Seneca, Epistulae Morales ad Lucilium, 30.15 | 264 |
| `passage_sen_ep_4_30_16` | Seneca, Epistulae Morales ad Lucilium, 30.16 | 373 |
| `passage_sen_ep_4_30_17` | Seneca, Epistulae Morales ad Lucilium, 30.17 | 250 |
| `passage_sen_ep_4_30_18` | Seneca, Epistulae Morales ad Lucilium, 30.18 | 144 |
| `passage_sen_ep_4_30_2` | Seneca, Epistulae Morales ad Lucilium, 30.2 | 369 |
| `passage_sen_ep_4_30_3` | Seneca, Epistulae Morales ad Lucilium, 30.3 | 386 |
| `passage_sen_ep_4_30_4` | Seneca, Epistulae Morales ad Lucilium, 30.4 | 470 |
| `passage_sen_ep_4_30_5` | Seneca, Epistulae Morales ad Lucilium, 30.5 | 331 |
| `passage_sen_ep_4_30_6` | Seneca, Epistulae Morales ad Lucilium, 30.6 | 255 |
| `passage_sen_ep_4_30_7` | Seneca, Epistulae Morales ad Lucilium, 30.7 | 250 |
| `passage_sen_ep_4_30_8` | Seneca, Epistulae Morales ad Lucilium, 30.8 | 405 |
| `passage_sen_ep_4_30_9` | Seneca, Epistulae Morales ad Lucilium, 30.9 | 391 |
| `passage_sen_ep_4_31_1` | Seneca, Epistulae Morales ad Lucilium, 31.1 | 322 |
| `passage_sen_ep_4_31_10` | Seneca, Epistulae Morales ad Lucilium, 31.10 | 440 |
| `passage_sen_ep_4_31_11` | Seneca, Epistulae Morales ad Lucilium, 31.11 | 593 |
| `passage_sen_ep_4_31_2` | Seneca, Epistulae Morales ad Lucilium, 31.2 | 508 |
| `passage_sen_ep_4_31_3` | Seneca, Epistulae Morales ad Lucilium, 31.3 | 354 |
| `passage_sen_ep_4_31_4` | Seneca, Epistulae Morales ad Lucilium, 31.4 | 302 |
| `passage_sen_ep_4_31_5` | Seneca, Epistulae Morales ad Lucilium, 31.5 | 618 |
| `passage_sen_ep_4_31_6` | Seneca, Epistulae Morales ad Lucilium, 31.6 | 310 |
| `passage_sen_ep_4_31_7` | Seneca, Epistulae Morales ad Lucilium, 31.7 | 252 |
| `passage_sen_ep_4_31_8` | Seneca, Epistulae Morales ad Lucilium, 31.8 | 304 |
| `passage_sen_ep_4_31_9` | Seneca, Epistulae Morales ad Lucilium, 31.9 | 321 |
| `passage_sen_ep_4_32_1` | Seneca, Epistulae Morales ad Lucilium, 32.1 | 341 |
| `passage_sen_ep_4_32_2` | Seneca, Epistulae Morales ad Lucilium, 32.2 | 446 |
| `passage_sen_ep_4_32_3` | Seneca, Epistulae Morales ad Lucilium, 32.3 | 440 |
| `passage_sen_ep_4_32_4` | Seneca, Epistulae Morales ad Lucilium, 32.4 | 442 |
| `passage_sen_ep_4_32_5` | Seneca, Epistulae Morales ad Lucilium, 32.5 | 305 |
| `passage_sen_ep_4_33_1` | Seneca, Epistulae Morales ad Lucilium, 33.1 | 303 |
| `passage_sen_ep_4_33_10` | Seneca, Epistulae Morales ad Lucilium, 33.10 | 289 |
| `passage_sen_ep_4_33_11` | Seneca, Epistulae Morales ad Lucilium, 33.11 | 276 |
| `passage_sen_ep_4_33_2` | Seneca, Epistulae Morales ad Lucilium, 33.2 | 455 |
| `passage_sen_ep_4_33_3` | Seneca, Epistulae Morales ad Lucilium, 33.3 | 290 |
| `passage_sen_ep_4_33_4` | Seneca, Epistulae Morales ad Lucilium, 33.4 | 567 |
| `passage_sen_ep_4_33_5` | Seneca, Epistulae Morales ad Lucilium, 33.5 | 419 |
| `passage_sen_ep_4_33_6` | Seneca, Epistulae Morales ad Lucilium, 33.6 | 356 |
| `passage_sen_ep_4_33_7` | Seneca, Epistulae Morales ad Lucilium, 33.7 | 502 |
| `passage_sen_ep_4_33_8` | Seneca, Epistulae Morales ad Lucilium, 33.8 | 418 |
| `passage_sen_ep_4_33_9` | Seneca, Epistulae Morales ad Lucilium, 33.9 | 264 |
| `passage_sen_ep_4_34_1` | Seneca, Epistulae Morales ad Lucilium, 34.1 | 433 |
| `passage_sen_ep_4_34_2` | Seneca, Epistulae Morales ad Lucilium, 34.2 | 222 |
| `passage_sen_ep_4_34_3` | Seneca, Epistulae Morales ad Lucilium, 34.3 | 299 |
| `passage_sen_ep_4_34_4` | Seneca, Epistulae Morales ad Lucilium, 34.4 | 219 |
| `passage_sen_ep_4_35_1` | Seneca, Epistulae Morales ad Lucilium, 35.1 | 405 |
| `passage_sen_ep_4_35_2` | Seneca, Epistulae Morales ad Lucilium, 35.2 | 227 |
| `passage_sen_ep_4_35_3` | Seneca, Epistulae Morales ad Lucilium, 35.3 | 349 |
| `passage_sen_ep_4_35_4` | Seneca, Epistulae Morales ad Lucilium, 35.4 | 496 |
| `passage_sen_ep_4_36_1` | Seneca, Epistulae Morales ad Lucilium, 36.1 | 514 |
| `passage_sen_ep_4_36_10` | Seneca, Epistulae Morales ad Lucilium, 36.10 | 369 |
| `passage_sen_ep_4_36_11` | Seneca, Epistulae Morales ad Lucilium, 36.11 | 442 |
| `passage_sen_ep_4_36_12` | Seneca, Epistulae Morales ad Lucilium, 36.12 | 198 |
| `passage_sen_ep_4_36_2` | Seneca, Epistulae Morales ad Lucilium, 36.2 | 296 |
| `passage_sen_ep_4_36_3` | Seneca, Epistulae Morales ad Lucilium, 36.3 | 533 |
| `passage_sen_ep_4_36_4` | Seneca, Epistulae Morales ad Lucilium, 36.4 | 422 |
| `passage_sen_ep_4_36_5` | Seneca, Epistulae Morales ad Lucilium, 36.5 | 289 |
| `passage_sen_ep_4_36_6` | Seneca, Epistulae Morales ad Lucilium, 36.6 | 326 |
| `passage_sen_ep_4_36_7` | Seneca, Epistulae Morales ad Lucilium, 36.7 | 261 |
| `passage_sen_ep_4_36_8` | Seneca, Epistulae Morales ad Lucilium, 36.8 | 378 |
| `passage_sen_ep_4_36_9` | Seneca, Epistulae Morales ad Lucilium, 36.9 | 364 |
| `passage_sen_ep_4_37_1` | Seneca, Epistulae Morales ad Lucilium, 37.1 | 244 |
| `passage_sen_ep_4_37_2` | Seneca, Epistulae Morales ad Lucilium, 37.2 | 404 |
| `passage_sen_ep_4_37_3` | Seneca, Epistulae Morales ad Lucilium, 37.3 | 268 |
| `passage_sen_ep_4_37_4` | Seneca, Epistulae Morales ad Lucilium, 37.4 | 442 |
| `passage_sen_ep_4_37_5` | Seneca, Epistulae Morales ad Lucilium, 37.5 | 294 |
| `passage_sen_ep_4_38_1` | Seneca, Epistulae Morales ad Lucilium, 38.1 | 549 |
| `passage_sen_ep_4_38_2` | Seneca, Epistulae Morales ad Lucilium, 38.2 | 515 |
| `passage_sen_ep_4_39_1` | Seneca, Epistulae Morales ad Lucilium, 39.1 | 435 |
| `passage_sen_ep_4_39_2` | Seneca, Epistulae Morales ad Lucilium, 39.2 | 436 |
| `passage_sen_ep_4_39_3` | Seneca, Epistulae Morales ad Lucilium, 39.3 | 328 |
| `passage_sen_ep_4_39_4` | Seneca, Epistulae Morales ad Lucilium, 39.4 | 377 |
| `passage_sen_ep_4_39_5` | Seneca, Epistulae Morales ad Lucilium, 39.5 | 372 |
| `passage_sen_ep_4_39_6` | Seneca, Epistulae Morales ad Lucilium, 39.6 | 498 |
| `passage_sen_ep_4_40_1` | Seneca, Epistulae Morales ad Lucilium, 40.1 | 452 |
| `passage_sen_ep_4_40_10` | Seneca, Epistulae Morales ad Lucilium, 40.10 | 298 |
| `passage_sen_ep_4_40_11` | Seneca, Epistulae Morales ad Lucilium, 40.11 | 287 |
| `passage_sen_ep_4_40_12` | Seneca, Epistulae Morales ad Lucilium, 40.12 | 307 |
| `passage_sen_ep_4_40_13` | Seneca, Epistulae Morales ad Lucilium, 40.13 | 387 |
| `passage_sen_ep_4_40_14` | Seneca, Epistulae Morales ad Lucilium, 40.14 | 246 |
| `passage_sen_ep_4_40_2` | Seneca, Epistulae Morales ad Lucilium, 40.2 | 507 |
| `passage_sen_ep_4_40_3` | Seneca, Epistulae Morales ad Lucilium, 40.3 | 443 |
| `passage_sen_ep_4_40_4` | Seneca, Epistulae Morales ad Lucilium, 40.4 | 383 |
| `passage_sen_ep_4_40_5` | Seneca, Epistulae Morales ad Lucilium, 40.5 | 361 |
| `passage_sen_ep_4_40_6` | Seneca, Epistulae Morales ad Lucilium, 40.6 | 264 |
| `passage_sen_ep_4_40_7` | Seneca, Epistulae Morales ad Lucilium, 40.7 | 291 |
| `passage_sen_ep_4_40_8` | Seneca, Epistulae Morales ad Lucilium, 40.8 | 484 |
| `passage_sen_ep_4_40_9` | Seneca, Epistulae Morales ad Lucilium, 40.9 | 371 |
| `passage_sen_ep_4_41_1` | Seneca, Epistulae Morales ad Lucilium, 41.1 | 308 |
| `passage_sen_ep_4_41_2` | Seneca, Epistulae Morales ad Lucilium, 41.2 | 321 |
| `passage_sen_ep_4_41_3` | Seneca, Epistulae Morales ad Lucilium, 41.3 | 847 |
| `passage_sen_ep_4_41_4` | Seneca, Epistulae Morales ad Lucilium, 41.4 | 129 |
| `passage_sen_ep_4_41_5` | Seneca, Epistulae Morales ad Lucilium, 41.5 | 515 |
| `passage_sen_ep_4_41_6` | Seneca, Epistulae Morales ad Lucilium, 41.6 | 538 |
| `passage_sen_ep_4_41_7` | Seneca, Epistulae Morales ad Lucilium, 41.7 | 422 |
| `passage_sen_ep_4_41_8` | Seneca, Epistulae Morales ad Lucilium, 41.8 | 220 |
| `passage_sen_ep_4_41_9` | Seneca, Epistulae Morales ad Lucilium, 41.9 | 257 |
| `passage_sen_ep_5_42_1` | Seneca, Epistulae Morales ad Lucilium, 42.1 | 372 |
| `passage_sen_ep_5_42_10` | Seneca, Epistulae Morales ad Lucilium, 42.10 | 314 |
| `passage_sen_ep_5_42_2` | Seneca, Epistulae Morales ad Lucilium, 42.2 | 277 |
| `passage_sen_ep_5_42_3` | Seneca, Epistulae Morales ad Lucilium, 42.3 | 229 |
| `passage_sen_ep_5_42_4` | Seneca, Epistulae Morales ad Lucilium, 42.4 | 310 |
| `passage_sen_ep_5_42_5` | Seneca, Epistulae Morales ad Lucilium, 42.5 | 406 |
| `passage_sen_ep_5_42_6` | Seneca, Epistulae Morales ad Lucilium, 42.6 | 266 |
| `passage_sen_ep_5_42_7` | Seneca, Epistulae Morales ad Lucilium, 42.7 | 400 |
| `passage_sen_ep_5_42_8` | Seneca, Epistulae Morales ad Lucilium, 42.8 | 352 |
| `passage_sen_ep_5_42_9` | Seneca, Epistulae Morales ad Lucilium, 42.9 | 296 |
| `passage_sen_ep_5_43_1` | Seneca, Epistulae Morales ad Lucilium, 43.1 | 278 |
| `passage_sen_ep_5_43_2` | Seneca, Epistulae Morales ad Lucilium, 43.2 | 253 |
| `passage_sen_ep_5_43_3` | Seneca, Epistulae Morales ad Lucilium, 43.3 | 364 |
| `passage_sen_ep_5_43_4` | Seneca, Epistulae Morales ad Lucilium, 43.4 | 262 |
| `passage_sen_ep_5_43_5` | Seneca, Epistulae Morales ad Lucilium, 43.5 | 226 |
| `passage_sen_ep_5_44_1` | Seneca, Epistulae Morales ad Lucilium, 44.1 | 295 |
| `passage_sen_ep_5_44_2` | Seneca, Epistulae Morales ad Lucilium, 44.2 | 323 |
| `passage_sen_ep_5_44_3` | Seneca, Epistulae Morales ad Lucilium, 44.3 | 324 |
| `passage_sen_ep_5_44_4` | Seneca, Epistulae Morales ad Lucilium, 44.4 | 230 |
| `passage_sen_ep_5_44_5` | Seneca, Epistulae Morales ad Lucilium, 44.5 | 448 |
| `passage_sen_ep_5_44_6` | Seneca, Epistulae Morales ad Lucilium, 44.6 | 294 |
| `passage_sen_ep_5_44_7` | Seneca, Epistulae Morales ad Lucilium, 44.7 | 556 |
| `passage_sen_ep_5_45_1` | Seneca, Epistulae Morales ad Lucilium, 45.1 | 234 |
| `passage_sen_ep_5_45_10` | Seneca, Epistulae Morales ad Lucilium, 45.10 | 490 |
| `passage_sen_ep_5_45_11` | Seneca, Epistulae Morales ad Lucilium, 45.11 | 220 |
| `passage_sen_ep_5_45_12` | Seneca, Epistulae Morales ad Lucilium, 45.12 | 247 |
| `passage_sen_ep_5_45_13` | Seneca, Epistulae Morales ad Lucilium, 45.13 | 417 |
| `passage_sen_ep_5_45_2` | Seneca, Epistulae Morales ad Lucilium, 45.2 | 460 |
| `passage_sen_ep_5_45_3` | Seneca, Epistulae Morales ad Lucilium, 45.3 | 221 |
| `passage_sen_ep_5_45_4` | Seneca, Epistulae Morales ad Lucilium, 45.4 | 351 |
| `passage_sen_ep_5_45_5` | Seneca, Epistulae Morales ad Lucilium, 45.5 | 324 |
| `passage_sen_ep_5_45_6` | Seneca, Epistulae Morales ad Lucilium, 45.6 | 238 |
| `passage_sen_ep_5_45_7` | Seneca, Epistulae Morales ad Lucilium, 45.7 | 480 |
| `passage_sen_ep_5_45_8` | Seneca, Epistulae Morales ad Lucilium, 45.8 | 463 |
| `passage_sen_ep_5_45_9` | Seneca, Epistulae Morales ad Lucilium, 45.9 | 813 |
| `passage_sen_ep_5_46_1` | Seneca, Epistulae Morales ad Lucilium, 46.1 | 489 |
| `passage_sen_ep_5_46_2` | Seneca, Epistulae Morales ad Lucilium, 46.2 | 406 |
| `passage_sen_ep_5_46_3` | Seneca, Epistulae Morales ad Lucilium, 46.3 | 340 |
| `passage_sen_ep_5_47_1` | Seneca, Epistulae Morales ad Lucilium, 47.1 | 308 |
| `passage_sen_ep_5_47_10` | Seneca, Epistulae Morales ad Lucilium, 47.10 | 422 |
| `passage_sen_ep_5_47_11` | Seneca, Epistulae Morales ad Lucilium, 47.11 | 341 |
| `passage_sen_ep_5_47_12` | Seneca, Epistulae Morales ad Lucilium, 47.12 | 176 |
| `passage_sen_ep_5_47_13` | Seneca, Epistulae Morales ad Lucilium, 47.13 | 256 |
| `passage_sen_ep_5_47_14` | Seneca, Epistulae Morales ad Lucilium, 47.14 | 388 |
| `passage_sen_ep_5_47_15` | Seneca, Epistulae Morales ad Lucilium, 47.15 | 433 |
| `passage_sen_ep_5_47_16` | Seneca, Epistulae Morales ad Lucilium, 47.16 | 381 |
| `passage_sen_ep_5_47_17` | Seneca, Epistulae Morales ad Lucilium, 47.17 | 475 |
| `passage_sen_ep_5_47_18` | Seneca, Epistulae Morales ad Lucilium, 47.18 | 334 |
| `passage_sen_ep_5_47_19` | Seneca, Epistulae Morales ad Lucilium, 47.19 | 267 |
| `passage_sen_ep_5_47_2` | Seneca, Epistulae Morales ad Lucilium, 47.2 | 380 |
| `passage_sen_ep_5_47_20` | Seneca, Epistulae Morales ad Lucilium, 47.20 | 317 |
| `passage_sen_ep_5_47_21` | Seneca, Epistulae Morales ad Lucilium, 47.21 | 190 |
| `passage_sen_ep_5_47_3` | Seneca, Epistulae Morales ad Lucilium, 47.3 | 198 |
| `passage_sen_ep_5_47_4` | Seneca, Epistulae Morales ad Lucilium, 47.4 | 309 |
| `passage_sen_ep_5_47_5` | Seneca, Epistulae Morales ad Lucilium, 47.5 | 331 |
| `passage_sen_ep_5_47_6` | Seneca, Epistulae Morales ad Lucilium, 47.6 | 255 |
| `passage_sen_ep_5_47_7` | Seneca, Epistulae Morales ad Lucilium, 47.7 | 290 |
| `passage_sen_ep_5_47_8` | Seneca, Epistulae Morales ad Lucilium, 47.8 | 499 |
| `passage_sen_ep_5_47_9` | Seneca, Epistulae Morales ad Lucilium, 47.9 | 405 |
| `passage_sen_ep_5_48_1` | Seneca, Epistulae Morales ad Lucilium, 48.1 | 390 |
| `passage_sen_ep_5_48_10` | Seneca, Epistulae Morales ad Lucilium, 48.10 | 407 |
| `passage_sen_ep_5_48_11` | Seneca, Epistulae Morales ad Lucilium, 48.11 | 382 |
| `passage_sen_ep_5_48_12` | Seneca, Epistulae Morales ad Lucilium, 48.12 | 301 |
| `passage_sen_ep_5_48_2` | Seneca, Epistulae Morales ad Lucilium, 48.2 | 359 |
| `passage_sen_ep_5_48_3` | Seneca, Epistulae Morales ad Lucilium, 48.3 | 286 |
| `passage_sen_ep_5_48_4` | Seneca, Epistulae Morales ad Lucilium, 48.4 | 405 |
| `passage_sen_ep_5_48_5` | Seneca, Epistulae Morales ad Lucilium, 48.5 | 191 |
| `passage_sen_ep_5_48_6` | Seneca, Epistulae Morales ad Lucilium, 48.6 | 417 |
| `passage_sen_ep_5_48_7` | Seneca, Epistulae Morales ad Lucilium, 48.7 | 375 |
| `passage_sen_ep_5_48_8` | Seneca, Epistulae Morales ad Lucilium, 48.8 | 528 |
| `passage_sen_ep_5_48_9` | Seneca, Epistulae Morales ad Lucilium, 48.9 | 524 |
| `passage_sen_ep_5_49_1` | Seneca, Epistulae Morales ad Lucilium, 49.1 | 655 |
| `passage_sen_ep_5_49_10` | Seneca, Epistulae Morales ad Lucilium, 49.10 | 448 |
| `passage_sen_ep_5_49_11` | Seneca, Epistulae Morales ad Lucilium, 49.11 | 742 |
| `passage_sen_ep_5_49_2` | Seneca, Epistulae Morales ad Lucilium, 49.2 | 299 |
| `passage_sen_ep_5_49_3` | Seneca, Epistulae Morales ad Lucilium, 49.3 | 516 |
| `passage_sen_ep_5_49_4` | Seneca, Epistulae Morales ad Lucilium, 49.4 | 287 |
| `passage_sen_ep_5_49_5` | Seneca, Epistulae Morales ad Lucilium, 49.5 | 371 |
| `passage_sen_ep_5_49_6` | Seneca, Epistulae Morales ad Lucilium, 49.6 | 424 |
| `passage_sen_ep_5_49_7` | Seneca, Epistulae Morales ad Lucilium, 49.7 | 158 |
| `passage_sen_ep_5_49_8` | Seneca, Epistulae Morales ad Lucilium, 49.8 | 449 |
| `passage_sen_ep_5_49_9` | Seneca, Epistulae Morales ad Lucilium, 49.9 | 326 |
| `passage_sen_ep_5_50_1` | Seneca, Epistulae Morales ad Lucilium, 50.1 | 474 |
| `passage_sen_ep_5_50_2` | Seneca, Epistulae Morales ad Lucilium, 50.2 | 363 |
| `passage_sen_ep_5_50_3` | Seneca, Epistulae Morales ad Lucilium, 50.3 | 402 |
| `passage_sen_ep_5_50_4` | Seneca, Epistulae Morales ad Lucilium, 50.4 | 392 |
| `passage_sen_ep_5_50_5` | Seneca, Epistulae Morales ad Lucilium, 50.5 | 410 |
| `passage_sen_ep_5_50_6` | Seneca, Epistulae Morales ad Lucilium, 50.6 | 428 |
| `passage_sen_ep_5_50_7` | Seneca, Epistulae Morales ad Lucilium, 50.7 | 246 |
| `passage_sen_ep_5_50_8` | Seneca, Epistulae Morales ad Lucilium, 50.8 | 313 |
| `passage_sen_ep_5_50_9` | Seneca, Epistulae Morales ad Lucilium, 50.9 | 392 |
| `passage_sen_ep_5_51_1` | Seneca, Epistulae Morales ad Lucilium, 51.1 | 522 |
| `passage_sen_ep_5_51_10` | Seneca, Epistulae Morales ad Lucilium, 51.10 | 464 |
| `passage_sen_ep_5_51_11` | Seneca, Epistulae Morales ad Lucilium, 51.11 | 554 |
| `passage_sen_ep_5_51_12` | Seneca, Epistulae Morales ad Lucilium, 51.12 | 374 |
| `passage_sen_ep_5_51_13` | Seneca, Epistulae Morales ad Lucilium, 51.13 | 409 |
| `passage_sen_ep_5_51_2` | Seneca, Epistulae Morales ad Lucilium, 51.2 | 326 |
| `passage_sen_ep_5_51_3` | Seneca, Epistulae Morales ad Lucilium, 51.3 | 247 |
| `passage_sen_ep_5_51_4` | Seneca, Epistulae Morales ad Lucilium, 51.4 | 341 |
| `passage_sen_ep_5_51_5` | Seneca, Epistulae Morales ad Lucilium, 51.5 | 243 |
| `passage_sen_ep_5_51_6` | Seneca, Epistulae Morales ad Lucilium, 51.6 | 485 |
| `passage_sen_ep_5_51_7` | Seneca, Epistulae Morales ad Lucilium, 51.7 | 333 |
| `passage_sen_ep_5_51_8` | Seneca, Epistulae Morales ad Lucilium, 51.8 | 338 |
| `passage_sen_ep_5_51_9` | Seneca, Epistulae Morales ad Lucilium, 51.9 | 255 |
| `passage_sen_ep_5_52_1` | Seneca, Epistulae Morales ad Lucilium, 52.1 | 260 |
| `passage_sen_ep_5_52_10` | Seneca, Epistulae Morales ad Lucilium, 52.10 | 408 |
| `passage_sen_ep_5_52_11` | Seneca, Epistulae Morales ad Lucilium, 52.11 | 355 |
| `passage_sen_ep_5_52_12` | Seneca, Epistulae Morales ad Lucilium, 52.12 | 481 |
| `passage_sen_ep_5_52_13` | Seneca, Epistulae Morales ad Lucilium, 52.13 | 256 |
| `passage_sen_ep_5_52_14` | Seneca, Epistulae Morales ad Lucilium, 52.14 | 356 |
| `passage_sen_ep_5_52_15` | Seneca, Epistulae Morales ad Lucilium, 52.15 | 344 |
| `passage_sen_ep_5_52_2` | Seneca, Epistulae Morales ad Lucilium, 52.2 | 196 |
| `passage_sen_ep_5_52_3` | Seneca, Epistulae Morales ad Lucilium, 52.3 | 515 |
| `passage_sen_ep_5_52_4` | Seneca, Epistulae Morales ad Lucilium, 52.4 | 458 |
| `passage_sen_ep_5_52_5` | Seneca, Epistulae Morales ad Lucilium, 52.5 | 358 |
| `passage_sen_ep_5_52_6` | Seneca, Epistulae Morales ad Lucilium, 52.6 | 295 |
| `passage_sen_ep_5_52_7` | Seneca, Epistulae Morales ad Lucilium, 52.7 | 280 |
| `passage_sen_ep_5_52_8` | Seneca, Epistulae Morales ad Lucilium, 52.8 | 378 |
| `passage_sen_ep_5_52_9` | Seneca, Epistulae Morales ad Lucilium, 52.9 | 305 |
| `passage_sen_ep_6_53_1` | Seneca, Epistulae Morales ad Lucilium, 53.1 | 355 |
| `passage_sen_ep_6_53_10` | Seneca, Epistulae Morales ad Lucilium, 53.10 | 328 |
| `passage_sen_ep_6_53_11` | Seneca, Epistulae Morales ad Lucilium, 53.11 | 421 |
| `passage_sen_ep_6_53_12` | Seneca, Epistulae Morales ad Lucilium, 53.12 | 306 |
| `passage_sen_ep_6_53_2` | Seneca, Epistulae Morales ad Lucilium, 53.2 | 396 |
| `passage_sen_ep_6_53_3` | Seneca, Epistulae Morales ad Lucilium, 53.3 | 400 |
| `passage_sen_ep_6_53_4` | Seneca, Epistulae Morales ad Lucilium, 53.4 | 335 |
| `passage_sen_ep_6_53_5` | Seneca, Epistulae Morales ad Lucilium, 53.5 | 275 |
| `passage_sen_ep_6_53_6` | Seneca, Epistulae Morales ad Lucilium, 53.6 | 404 |
| `passage_sen_ep_6_53_7` | Seneca, Epistulae Morales ad Lucilium, 53.7 | 364 |
| `passage_sen_ep_6_53_8` | Seneca, Epistulae Morales ad Lucilium, 53.8 | 416 |
| `passage_sen_ep_6_53_9` | Seneca, Epistulae Morales ad Lucilium, 53.9 | 452 |
| `passage_sen_ep_6_54_1` | Seneca, Epistulae Morales ad Lucilium, 54.1 | 344 |
| `passage_sen_ep_6_54_2` | Seneca, Epistulae Morales ad Lucilium, 54.2 | 298 |
| `passage_sen_ep_6_54_3` | Seneca, Epistulae Morales ad Lucilium, 54.3 | 267 |
| `passage_sen_ep_6_54_4` | Seneca, Epistulae Morales ad Lucilium, 54.4 | 336 |
| `passage_sen_ep_6_54_5` | Seneca, Epistulae Morales ad Lucilium, 54.5 | 464 |
| `passage_sen_ep_6_54_6` | Seneca, Epistulae Morales ad Lucilium, 54.6 | 366 |
| `passage_sen_ep_6_54_7` | Seneca, Epistulae Morales ad Lucilium, 54.7 | 431 |
| `passage_sen_ep_6_55_1` | Seneca, Epistulae Morales ad Lucilium, 55.1 | 314 |
| `passage_sen_ep_6_55_10` | Seneca, Epistulae Morales ad Lucilium, 55.10 | 269 |
| `passage_sen_ep_6_55_11` | Seneca, Epistulae Morales ad Lucilium, 55.11 | 325 |
| `passage_sen_ep_6_55_2` | Seneca, Epistulae Morales ad Lucilium, 55.2 | 542 |
| `passage_sen_ep_6_55_3` | Seneca, Epistulae Morales ad Lucilium, 55.3 | 466 |
| `passage_sen_ep_6_55_4` | Seneca, Epistulae Morales ad Lucilium, 55.4 | 448 |
| `passage_sen_ep_6_55_5` | Seneca, Epistulae Morales ad Lucilium, 55.5 | 474 |
| `passage_sen_ep_6_55_6` | Seneca, Epistulae Morales ad Lucilium, 55.6 | 632 |
| `passage_sen_ep_6_55_7` | Seneca, Epistulae Morales ad Lucilium, 55.7 | 213 |
| `passage_sen_ep_6_55_8` | Seneca, Epistulae Morales ad Lucilium, 55.8 | 320 |
| `passage_sen_ep_6_55_9` | Seneca, Epistulae Morales ad Lucilium, 55.9 | 294 |
| `passage_sen_ep_6_56_1` | Seneca, Epistulae Morales ad Lucilium, 56.1 | 638 |
| `passage_sen_ep_6_56_10` | Seneca, Epistulae Morales ad Lucilium, 56.10 | 466 |
| `passage_sen_ep_6_56_11` | Seneca, Epistulae Morales ad Lucilium, 56.11 | 240 |
| `passage_sen_ep_6_56_12` | Seneca, Epistulae Morales ad Lucilium, 56.12 | 217 |
| `passage_sen_ep_6_56_13` | Seneca, Epistulae Morales ad Lucilium, 56.13 | 314 |
| `passage_sen_ep_6_56_14` | Seneca, Epistulae Morales ad Lucilium, 56.14 | 304 |
| `passage_sen_ep_6_56_15` | Seneca, Epistulae Morales ad Lucilium, 56.15 | 245 |
| `passage_sen_ep_6_56_2` | Seneca, Epistulae Morales ad Lucilium, 56.2 | 513 |
| `passage_sen_ep_6_56_3` | Seneca, Epistulae Morales ad Lucilium, 56.3 | 364 |
| `passage_sen_ep_6_56_4` | Seneca, Epistulae Morales ad Lucilium, 56.4 | 314 |
| `passage_sen_ep_6_56_5` | Seneca, Epistulae Morales ad Lucilium, 56.5 | 487 |
| `passage_sen_ep_6_56_6` | Seneca, Epistulae Morales ad Lucilium, 56.6 | 244 |
| `passage_sen_ep_6_56_7` | Seneca, Epistulae Morales ad Lucilium, 56.7 | 246 |
| `passage_sen_ep_6_56_8` | Seneca, Epistulae Morales ad Lucilium, 56.8 | 347 |
| `passage_sen_ep_6_56_9` | Seneca, Epistulae Morales ad Lucilium, 56.9 | 470 |
| `passage_sen_ep_6_57_1` | Seneca, Epistulae Morales ad Lucilium, 57.1 | 275 |
| `passage_sen_ep_6_57_2` | Seneca, Epistulae Morales ad Lucilium, 57.2 | 441 |
| `passage_sen_ep_6_57_3` | Seneca, Epistulae Morales ad Lucilium, 57.3 | 339 |
| `passage_sen_ep_6_57_4` | Seneca, Epistulae Morales ad Lucilium, 57.4 | 299 |
| `passage_sen_ep_6_57_5` | Seneca, Epistulae Morales ad Lucilium, 57.5 | 247 |
| `passage_sen_ep_6_57_6` | Seneca, Epistulae Morales ad Lucilium, 57.6 | 478 |
| `passage_sen_ep_6_57_7` | Seneca, Epistulae Morales ad Lucilium, 57.7 | 216 |
| `passage_sen_ep_6_57_8` | Seneca, Epistulae Morales ad Lucilium, 57.8 | 492 |
| `passage_sen_ep_6_57_9` | Seneca, Epistulae Morales ad Lucilium, 57.9 | 251 |
| `passage_sen_ep_6_58_1` | Seneca, Epistulae Morales ad Lucilium, 58.1 | 252 |
| `passage_sen_ep_6_58_10` | Seneca, Epistulae Morales ad Lucilium, 58.10 | 381 |
| `passage_sen_ep_6_58_11` | Seneca, Epistulae Morales ad Lucilium, 58.11 | 295 |
| `passage_sen_ep_6_58_12` | Seneca, Epistulae Morales ad Lucilium, 58.12 | 444 |
| `passage_sen_ep_6_58_13` | Seneca, Epistulae Morales ad Lucilium, 58.13 | 191 |
| `passage_sen_ep_6_58_14` | Seneca, Epistulae Morales ad Lucilium, 58.14 | 424 |
| `passage_sen_ep_6_58_15` | Seneca, Epistulae Morales ad Lucilium, 58.15 | 353 |
| `passage_sen_ep_6_58_16` | Seneca, Epistulae Morales ad Lucilium, 58.16 | 367 |
| `passage_sen_ep_6_58_17` | Seneca, Epistulae Morales ad Lucilium, 58.17 | 323 |
| `passage_sen_ep_6_58_18` | Seneca, Epistulae Morales ad Lucilium, 58.18 | 244 |
| `passage_sen_ep_6_58_19` | Seneca, Epistulae Morales ad Lucilium, 58.19 | 556 |
| `passage_sen_ep_6_58_2` | Seneca, Epistulae Morales ad Lucilium, 58.2 | 172 |
| `passage_sen_ep_6_58_20` | Seneca, Epistulae Morales ad Lucilium, 58.20 | 375 |
| `passage_sen_ep_6_58_21` | Seneca, Epistulae Morales ad Lucilium, 58.21 | 396 |
| `passage_sen_ep_6_58_22` | Seneca, Epistulae Morales ad Lucilium, 58.22 | 589 |
| `passage_sen_ep_6_58_23` | Seneca, Epistulae Morales ad Lucilium, 58.23 | 443 |
| `passage_sen_ep_6_58_24` | Seneca, Epistulae Morales ad Lucilium, 58.24 | 203 |
| `passage_sen_ep_6_58_25` | Seneca, Epistulae Morales ad Lucilium, 58.25 | 380 |
| `passage_sen_ep_6_58_26` | Seneca, Epistulae Morales ad Lucilium, 58.26 | 438 |
| `passage_sen_ep_6_58_27` | Seneca, Epistulae Morales ad Lucilium, 58.27 | 480 |
| `passage_sen_ep_6_58_28` | Seneca, Epistulae Morales ad Lucilium, 58.28 | 249 |
| `passage_sen_ep_6_58_29` | Seneca, Epistulae Morales ad Lucilium, 58.29 | 262 |
| `passage_sen_ep_6_58_3` | Seneca, Epistulae Morales ad Lucilium, 58.3 | 239 |
| `passage_sen_ep_6_58_30` | Seneca, Epistulae Morales ad Lucilium, 58.30 | 330 |
| `passage_sen_ep_6_58_31` | Seneca, Epistulae Morales ad Lucilium, 58.31 | 425 |
| `passage_sen_ep_6_58_32` | Seneca, Epistulae Morales ad Lucilium, 58.32 | 435 |
| `passage_sen_ep_6_58_33` | Seneca, Epistulae Morales ad Lucilium, 58.33 | 253 |
| `passage_sen_ep_6_58_34` | Seneca, Epistulae Morales ad Lucilium, 58.34 | 482 |
| `passage_sen_ep_6_58_35` | Seneca, Epistulae Morales ad Lucilium, 58.35 | 322 |
| `passage_sen_ep_6_58_36` | Seneca, Epistulae Morales ad Lucilium, 58.36 | 362 |
| `passage_sen_ep_6_58_37` | Seneca, Epistulae Morales ad Lucilium, 58.37 | 198 |
| `passage_sen_ep_6_58_4` | Seneca, Epistulae Morales ad Lucilium, 58.4 | 87 |
| `passage_sen_ep_6_58_5` | Seneca, Epistulae Morales ad Lucilium, 58.5 | 245 |
| `passage_sen_ep_6_58_6` | Seneca, Epistulae Morales ad Lucilium, 58.6 | 578 |
| `passage_sen_ep_6_58_7` | Seneca, Epistulae Morales ad Lucilium, 58.7 | 393 |
| `passage_sen_ep_6_58_8` | Seneca, Epistulae Morales ad Lucilium, 58.8 | 427 |
| `passage_sen_ep_6_58_9` | Seneca, Epistulae Morales ad Lucilium, 58.9 | 283 |
| `passage_sen_ep_6_59_1` | Seneca, Epistulae Morales ad Lucilium, 59.1 | 239 |
| `passage_sen_ep_6_59_10` | Seneca, Epistulae Morales ad Lucilium, 59.10 | 246 |
| `passage_sen_ep_6_59_11` | Seneca, Epistulae Morales ad Lucilium, 59.11 | 624 |
| `passage_sen_ep_6_59_12` | Seneca, Epistulae Morales ad Lucilium, 59.12 | 458 |
| `passage_sen_ep_6_59_13` | Seneca, Epistulae Morales ad Lucilium, 59.13 | 310 |
| `passage_sen_ep_6_59_14` | Seneca, Epistulae Morales ad Lucilium, 59.14 | 694 |
| `passage_sen_ep_6_59_15` | Seneca, Epistulae Morales ad Lucilium, 59.15 | 496 |
| `passage_sen_ep_6_59_16` | Seneca, Epistulae Morales ad Lucilium, 59.16 | 272 |
| `passage_sen_ep_6_59_17` | Seneca, Epistulae Morales ad Lucilium, 59.17 | 358 |
| `passage_sen_ep_6_59_18` | Seneca, Epistulae Morales ad Lucilium, 59.18 | 299 |
| `passage_sen_ep_6_59_2` | Seneca, Epistulae Morales ad Lucilium, 59.2 | 426 |
| `passage_sen_ep_6_59_3` | Seneca, Epistulae Morales ad Lucilium, 59.3 | 206 |
| `passage_sen_ep_6_59_4` | Seneca, Epistulae Morales ad Lucilium, 59.4 | 424 |
| `passage_sen_ep_6_59_5` | Seneca, Epistulae Morales ad Lucilium, 59.5 | 297 |
| `passage_sen_ep_6_59_6` | Seneca, Epistulae Morales ad Lucilium, 59.6 | 518 |
| `passage_sen_ep_6_59_7` | Seneca, Epistulae Morales ad Lucilium, 59.7 | 644 |
| `passage_sen_ep_6_59_8` | Seneca, Epistulae Morales ad Lucilium, 59.8 | 469 |
| `passage_sen_ep_6_59_9` | Seneca, Epistulae Morales ad Lucilium, 59.9 | 477 |
| `passage_sen_ep_6_60_1` | Seneca, Epistulae Morales ad Lucilium, 60.1 | 382 |
| `passage_sen_ep_6_60_2` | Seneca, Epistulae Morales ad Lucilium, 60.2 | 362 |
| `passage_sen_ep_6_60_3` | Seneca, Epistulae Morales ad Lucilium, 60.3 | 284 |
| `passage_sen_ep_6_60_4` | Seneca, Epistulae Morales ad Lucilium, 60.4 | 351 |
| `passage_sen_ep_6_61_1` | Seneca, Epistulae Morales ad Lucilium, 61.1 | 333 |
| `passage_sen_ep_6_61_2` | Seneca, Epistulae Morales ad Lucilium, 61.2 | 325 |
| `passage_sen_ep_6_61_3` | Seneca, Epistulae Morales ad Lucilium, 61.3 | 349 |
| `passage_sen_ep_6_61_4` | Seneca, Epistulae Morales ad Lucilium, 61.4 | 297 |
| `passage_sen_ep_6_62_1` | Seneca, Epistulae Morales ad Lucilium, 62.1 | 358 |
| `passage_sen_ep_6_62_2` | Seneca, Epistulae Morales ad Lucilium, 62.2 | 238 |
| `passage_sen_ep_6_62_3` | Seneca, Epistulae Morales ad Lucilium, 62.3 | 375 |
| `passage_sen_ep_7_63_1` | Seneca, Epistulae Morales ad Lucilium, 63.1 | 458 |
| `passage_sen_ep_7_63_10` | Seneca, Epistulae Morales ad Lucilium, 63.10 | 232 |
| `passage_sen_ep_7_63_11` | Seneca, Epistulae Morales ad Lucilium, 63.11 | 295 |
| `passage_sen_ep_7_63_12` | Seneca, Epistulae Morales ad Lucilium, 63.12 | 414 |
| `passage_sen_ep_7_63_13` | Seneca, Epistulae Morales ad Lucilium, 63.13 | 455 |
| `passage_sen_ep_7_63_14` | Seneca, Epistulae Morales ad Lucilium, 63.14 | 365 |
| `passage_sen_ep_7_63_15` | Seneca, Epistulae Morales ad Lucilium, 63.15 | 347 |
| `passage_sen_ep_7_63_16` | Seneca, Epistulae Morales ad Lucilium, 63.16 | 209 |
| `passage_sen_ep_7_63_2` | Seneca, Epistulae Morales ad Lucilium, 63.2 | 369 |
| `passage_sen_ep_7_63_3` | Seneca, Epistulae Morales ad Lucilium, 63.3 | 436 |
| `passage_sen_ep_7_63_4` | Seneca, Epistulae Morales ad Lucilium, 63.4 | 266 |
| `passage_sen_ep_7_63_5` | Seneca, Epistulae Morales ad Lucilium, 63.5 | 279 |
| `passage_sen_ep_7_63_6` | Seneca, Epistulae Morales ad Lucilium, 63.6 | 234 |
| `passage_sen_ep_7_63_7` | Seneca, Epistulae Morales ad Lucilium, 63.7 | 252 |
| `passage_sen_ep_7_63_8` | Seneca, Epistulae Morales ad Lucilium, 63.8 | 262 |
| `passage_sen_ep_7_63_9` | Seneca, Epistulae Morales ad Lucilium, 63.9 | 219 |
| `passage_sen_ep_7_64_1` | Seneca, Epistulae Morales ad Lucilium, 64.1 | 275 |
| `passage_sen_ep_7_64_10` | Seneca, Epistulae Morales ad Lucilium, 64.10 | 346 |
| `passage_sen_ep_7_64_2` | Seneca, Epistulae Morales ad Lucilium, 64.2 | 211 |
| `passage_sen_ep_7_64_3` | Seneca, Epistulae Morales ad Lucilium, 64.3 | 334 |
| `passage_sen_ep_7_64_4` | Seneca, Epistulae Morales ad Lucilium, 64.4 | 330 |
| `passage_sen_ep_7_64_5` | Seneca, Epistulae Morales ad Lucilium, 64.5 | 235 |
| `passage_sen_ep_7_64_6` | Seneca, Epistulae Morales ad Lucilium, 64.6 | 253 |
| `passage_sen_ep_7_64_7` | Seneca, Epistulae Morales ad Lucilium, 64.7 | 374 |
| `passage_sen_ep_7_64_8` | Seneca, Epistulae Morales ad Lucilium, 64.8 | 552 |
| `passage_sen_ep_7_64_9` | Seneca, Epistulae Morales ad Lucilium, 64.9 | 367 |
| `passage_sen_ep_7_65_1` | Seneca, Epistulae Morales ad Lucilium, 65.1 | 413 |
| `passage_sen_ep_7_65_10` | Seneca, Epistulae Morales ad Lucilium, 65.10 | 371 |
| `passage_sen_ep_7_65_11` | Seneca, Epistulae Morales ad Lucilium, 65.11 | 416 |
| `passage_sen_ep_7_65_12` | Seneca, Epistulae Morales ad Lucilium, 65.12 | 278 |
| `passage_sen_ep_7_65_13` | Seneca, Epistulae Morales ad Lucilium, 65.13 | 301 |
| `passage_sen_ep_7_65_14` | Seneca, Epistulae Morales ad Lucilium, 65.14 | 357 |
| `passage_sen_ep_7_65_15` | Seneca, Epistulae Morales ad Lucilium, 65.15 | 329 |
| `passage_sen_ep_7_65_16` | Seneca, Epistulae Morales ad Lucilium, 65.16 | 527 |
| `passage_sen_ep_7_65_17` | Seneca, Epistulae Morales ad Lucilium, 65.17 | 349 |
| `passage_sen_ep_7_65_18` | Seneca, Epistulae Morales ad Lucilium, 65.18 | 308 |
| `passage_sen_ep_7_65_19` | Seneca, Epistulae Morales ad Lucilium, 65.19 | 475 |
| `passage_sen_ep_7_65_2` | Seneca, Epistulae Morales ad Lucilium, 65.2 | 513 |
| `passage_sen_ep_7_65_20` | Seneca, Epistulae Morales ad Lucilium, 65.20 | 258 |
| `passage_sen_ep_7_65_21` | Seneca, Epistulae Morales ad Lucilium, 65.21 | 334 |
| `passage_sen_ep_7_65_22` | Seneca, Epistulae Morales ad Lucilium, 65.22 | 307 |
| `passage_sen_ep_7_65_23` | Seneca, Epistulae Morales ad Lucilium, 65.23 | 299 |
| `passage_sen_ep_7_65_24` | Seneca, Epistulae Morales ad Lucilium, 65.24 | 391 |
| `passage_sen_ep_7_65_3` | Seneca, Epistulae Morales ad Lucilium, 65.3 | 333 |
| `passage_sen_ep_7_65_4` | Seneca, Epistulae Morales ad Lucilium, 65.4 | 351 |
| `passage_sen_ep_7_65_5` | Seneca, Epistulae Morales ad Lucilium, 65.5 | 442 |
| `passage_sen_ep_7_65_6` | Seneca, Epistulae Morales ad Lucilium, 65.6 | 321 |
| `passage_sen_ep_7_65_7` | Seneca, Epistulae Morales ad Lucilium, 65.7 | 615 |
| `passage_sen_ep_7_65_8` | Seneca, Epistulae Morales ad Lucilium, 65.8 | 395 |
| `passage_sen_ep_7_65_9` | Seneca, Epistulae Morales ad Lucilium, 65.9 | 232 |
| `passage_sen_ep_7_66_1` | Seneca, Epistulae Morales ad Lucilium, 66.1 | 425 |
| `passage_sen_ep_7_66_10` | Seneca, Epistulae Morales ad Lucilium, 66.10 | 227 |
| `passage_sen_ep_7_66_11` | Seneca, Epistulae Morales ad Lucilium, 66.11 | 282 |
| `passage_sen_ep_7_66_12` | Seneca, Epistulae Morales ad Lucilium, 66.12 | 556 |
| `passage_sen_ep_7_66_13` | Seneca, Epistulae Morales ad Lucilium, 66.13 | 560 |
| `passage_sen_ep_7_66_14` | Seneca, Epistulae Morales ad Lucilium, 66.14 | 344 |
| `passage_sen_ep_7_66_15` | Seneca, Epistulae Morales ad Lucilium, 66.15 | 374 |
| `passage_sen_ep_7_66_16` | Seneca, Epistulae Morales ad Lucilium, 66.16 | 446 |
| `passage_sen_ep_7_66_17` | Seneca, Epistulae Morales ad Lucilium, 66.17 | 415 |
| `passage_sen_ep_7_66_18` | Seneca, Epistulae Morales ad Lucilium, 66.18 | 476 |
| `passage_sen_ep_7_66_19` | Seneca, Epistulae Morales ad Lucilium, 66.19 | 306 |
| `passage_sen_ep_7_66_2` | Seneca, Epistulae Morales ad Lucilium, 66.2 | 222 |
| `passage_sen_ep_7_66_20` | Seneca, Epistulae Morales ad Lucilium, 66.20 | 384 |
| `passage_sen_ep_7_66_21` | Seneca, Epistulae Morales ad Lucilium, 66.21 | 406 |
| `passage_sen_ep_7_66_22` | Seneca, Epistulae Morales ad Lucilium, 66.22 | 311 |
| `passage_sen_ep_7_66_23` | Seneca, Epistulae Morales ad Lucilium, 66.23 | 494 |
| `passage_sen_ep_7_66_24` | Seneca, Epistulae Morales ad Lucilium, 66.24 | 272 |
| `passage_sen_ep_7_66_25` | Seneca, Epistulae Morales ad Lucilium, 66.25 | 451 |
| `passage_sen_ep_7_66_26` | Seneca, Epistulae Morales ad Lucilium, 66.26 | 392 |
| `passage_sen_ep_7_66_27` | Seneca, Epistulae Morales ad Lucilium, 66.27 | 353 |
| `passage_sen_ep_7_66_28` | Seneca, Epistulae Morales ad Lucilium, 66.28 | 200 |
| `passage_sen_ep_7_66_29` | Seneca, Epistulae Morales ad Lucilium, 66.29 | 342 |
| `passage_sen_ep_7_66_3` | Seneca, Epistulae Morales ad Lucilium, 66.3 | 355 |
| `passage_sen_ep_7_66_30` | Seneca, Epistulae Morales ad Lucilium, 66.30 | 242 |
| `passage_sen_ep_7_66_31` | Seneca, Epistulae Morales ad Lucilium, 66.31 | 338 |
| `passage_sen_ep_7_66_32` | Seneca, Epistulae Morales ad Lucilium, 66.32 | 381 |
| `passage_sen_ep_7_66_33` | Seneca, Epistulae Morales ad Lucilium, 66.33 | 423 |
| `passage_sen_ep_7_66_34` | Seneca, Epistulae Morales ad Lucilium, 66.34 | 342 |
| `passage_sen_ep_7_66_35` | Seneca, Epistulae Morales ad Lucilium, 66.35 | 493 |
| `passage_sen_ep_7_66_36` | Seneca, Epistulae Morales ad Lucilium, 66.36 | 414 |
| `passage_sen_ep_7_66_37` | Seneca, Epistulae Morales ad Lucilium, 66.37 | 220 |
| `passage_sen_ep_7_66_38` | Seneca, Epistulae Morales ad Lucilium, 66.38 | 277 |
| `passage_sen_ep_7_66_39` | Seneca, Epistulae Morales ad Lucilium, 66.39 | 275 |
| `passage_sen_ep_7_66_4` | Seneca, Epistulae Morales ad Lucilium, 66.4 | 261 |
| `passage_sen_ep_7_66_40` | Seneca, Epistulae Morales ad Lucilium, 66.40 | 377 |
| `passage_sen_ep_7_66_41` | Seneca, Epistulae Morales ad Lucilium, 66.41 | 414 |
| `passage_sen_ep_7_66_42` | Seneca, Epistulae Morales ad Lucilium, 66.42 | 274 |
| `passage_sen_ep_7_66_43` | Seneca, Epistulae Morales ad Lucilium, 66.43 | 463 |
| `passage_sen_ep_7_66_44` | Seneca, Epistulae Morales ad Lucilium, 66.44 | 352 |
| `passage_sen_ep_7_66_45` | Seneca, Epistulae Morales ad Lucilium, 66.45 | 398 |
| `passage_sen_ep_7_66_46` | Seneca, Epistulae Morales ad Lucilium, 66.46 | 449 |
| `passage_sen_ep_7_66_47` | Seneca, Epistulae Morales ad Lucilium, 66.47 | 678 |
| `passage_sen_ep_7_66_48` | Seneca, Epistulae Morales ad Lucilium, 66.48 | 267 |
| `passage_sen_ep_7_66_49` | Seneca, Epistulae Morales ad Lucilium, 66.49 | 257 |
| `passage_sen_ep_7_66_5` | Seneca, Epistulae Morales ad Lucilium, 66.5 | 453 |
| `passage_sen_ep_7_66_50` | Seneca, Epistulae Morales ad Lucilium, 66.50 | 387 |
| `passage_sen_ep_7_66_51` | Seneca, Epistulae Morales ad Lucilium, 66.51 | 287 |
| `passage_sen_ep_7_66_52` | Seneca, Epistulae Morales ad Lucilium, 66.52 | 269 |
| `passage_sen_ep_7_66_53` | Seneca, Epistulae Morales ad Lucilium, 66.53 | 371 |
| `passage_sen_ep_7_66_6` | Seneca, Epistulae Morales ad Lucilium, 66.6 | 727 |
| `passage_sen_ep_7_66_7` | Seneca, Epistulae Morales ad Lucilium, 66.7 | 353 |
| `passage_sen_ep_7_66_8` | Seneca, Epistulae Morales ad Lucilium, 66.8 | 377 |
| `passage_sen_ep_7_66_9` | Seneca, Epistulae Morales ad Lucilium, 66.9 | 505 |
| `passage_sen_ep_7_67_1` | Seneca, Epistulae Morales ad Lucilium, 67.1 | 424 |
| `passage_sen_ep_7_67_10` | Seneca, Epistulae Morales ad Lucilium, 67.10 | 621 |
| `passage_sen_ep_7_67_11` | Seneca, Epistulae Morales ad Lucilium, 67.11 | 242 |
| `passage_sen_ep_7_67_12` | Seneca, Epistulae Morales ad Lucilium, 67.12 | 267 |
| `passage_sen_ep_7_67_13` | Seneca, Epistulae Morales ad Lucilium, 67.13 | 203 |
| `passage_sen_ep_7_67_14` | Seneca, Epistulae Morales ad Lucilium, 67.14 | 296 |
| `passage_sen_ep_7_67_15` | Seneca, Epistulae Morales ad Lucilium, 67.15 | 257 |
| `passage_sen_ep_7_67_16` | Seneca, Epistulae Morales ad Lucilium, 67.16 | 209 |
| `passage_sen_ep_7_67_2` | Seneca, Epistulae Morales ad Lucilium, 67.2 | 414 |
| `passage_sen_ep_7_67_3` | Seneca, Epistulae Morales ad Lucilium, 67.3 | 325 |
| `passage_sen_ep_7_67_4` | Seneca, Epistulae Morales ad Lucilium, 67.4 | 525 |
| `passage_sen_ep_7_67_5` | Seneca, Epistulae Morales ad Lucilium, 67.5 | 443 |
| `passage_sen_ep_7_67_6` | Seneca, Epistulae Morales ad Lucilium, 67.6 | 499 |
| `passage_sen_ep_7_67_7` | Seneca, Epistulae Morales ad Lucilium, 67.7 | 466 |
| `passage_sen_ep_7_67_8` | Seneca, Epistulae Morales ad Lucilium, 67.8 | 61 |
| `passage_sen_ep_7_67_9` | Seneca, Epistulae Morales ad Lucilium, 67.9 | 364 |
| `passage_sen_ep_7_68_1` | Seneca, Epistulae Morales ad Lucilium, 68.1 | 210 |
| `passage_sen_ep_7_68_10` | Seneca, Epistulae Morales ad Lucilium, 68.10 | 306 |
| `passage_sen_ep_7_68_11` | Seneca, Epistulae Morales ad Lucilium, 68.11 | 229 |
| `passage_sen_ep_7_68_12` | Seneca, Epistulae Morales ad Lucilium, 68.12 | 242 |
| `passage_sen_ep_7_68_13` | Seneca, Epistulae Morales ad Lucilium, 68.13 | 240 |
| `passage_sen_ep_7_68_14` | Seneca, Epistulae Morales ad Lucilium, 68.14 | 397 |
| `passage_sen_ep_7_68_2` | Seneca, Epistulae Morales ad Lucilium, 68.2 | 455 |
| `passage_sen_ep_7_68_3` | Seneca, Epistulae Morales ad Lucilium, 68.3 | 247 |
| `passage_sen_ep_7_68_4` | Seneca, Epistulae Morales ad Lucilium, 68.4 | 415 |
| `passage_sen_ep_7_68_5` | Seneca, Epistulae Morales ad Lucilium, 68.5 | 232 |
| `passage_sen_ep_7_68_6` | Seneca, Epistulae Morales ad Lucilium, 68.6 | 286 |
| `passage_sen_ep_7_68_7` | Seneca, Epistulae Morales ad Lucilium, 68.7 | 372 |
| `passage_sen_ep_7_68_8` | Seneca, Epistulae Morales ad Lucilium, 68.8 | 382 |
| `passage_sen_ep_7_68_9` | Seneca, Epistulae Morales ad Lucilium, 68.9 | 418 |
| `passage_sen_ep_7_69_1` | Seneca, Epistulae Morales ad Lucilium, 69.1 | 229 |
| `passage_sen_ep_7_69_2` | Seneca, Epistulae Morales ad Lucilium, 69.2 | 264 |
| `passage_sen_ep_7_69_3` | Seneca, Epistulae Morales ad Lucilium, 69.3 | 291 |
| `passage_sen_ep_7_69_4` | Seneca, Epistulae Morales ad Lucilium, 69.4 | 314 |
| `passage_sen_ep_7_69_5` | Seneca, Epistulae Morales ad Lucilium, 69.5 | 220 |
| `passage_sen_ep_7_69_6` | Seneca, Epistulae Morales ad Lucilium, 69.6 | 419 |
| `passage_sen_ep_8_70_1` | Seneca, Epistulae Morales ad Lucilium, 70.1 | 177 |
| `passage_sen_ep_8_70_10` | Seneca, Epistulae Morales ad Lucilium, 70.10 | 592 |
| `passage_sen_ep_8_70_11` | Seneca, Epistulae Morales ad Lucilium, 70.11 | 351 |
| `passage_sen_ep_8_70_12` | Seneca, Epistulae Morales ad Lucilium, 70.12 | 343 |
| `passage_sen_ep_8_70_13` | Seneca, Epistulae Morales ad Lucilium, 70.13 | 342 |
| `passage_sen_ep_8_70_14` | Seneca, Epistulae Morales ad Lucilium, 70.14 | 314 |
| `passage_sen_ep_8_70_15` | Seneca, Epistulae Morales ad Lucilium, 70.15 | 290 |
| `passage_sen_ep_8_70_16` | Seneca, Epistulae Morales ad Lucilium, 70.16 | 415 |
| `passage_sen_ep_8_70_17` | Seneca, Epistulae Morales ad Lucilium, 70.17 | 229 |
| `passage_sen_ep_8_70_18` | Seneca, Epistulae Morales ad Lucilium, 70.18 | 436 |
| `passage_sen_ep_8_70_19` | Seneca, Epistulae Morales ad Lucilium, 70.19 | 437 |
| `passage_sen_ep_8_70_2` | Seneca, Epistulae Morales ad Lucilium, 70.2 | 354 |
| `passage_sen_ep_8_70_20` | Seneca, Epistulae Morales ad Lucilium, 70.20 | 418 |
| `passage_sen_ep_8_70_21` | Seneca, Epistulae Morales ad Lucilium, 70.21 | 440 |
| `passage_sen_ep_8_70_22` | Seneca, Epistulae Morales ad Lucilium, 70.22 | 353 |
| `passage_sen_ep_8_70_23` | Seneca, Epistulae Morales ad Lucilium, 70.23 | 285 |
| `passage_sen_ep_8_70_24` | Seneca, Epistulae Morales ad Lucilium, 70.24 | 390 |
| `passage_sen_ep_8_70_25` | Seneca, Epistulae Morales ad Lucilium, 70.25 | 240 |
| `passage_sen_ep_8_70_26` | Seneca, Epistulae Morales ad Lucilium, 70.26 | 225 |
| `passage_sen_ep_8_70_27` | Seneca, Epistulae Morales ad Lucilium, 70.27 | 351 |
| `passage_sen_ep_8_70_28` | Seneca, Epistulae Morales ad Lucilium, 70.28 | 219 |
| `passage_sen_ep_8_70_3` | Seneca, Epistulae Morales ad Lucilium, 70.3 | 329 |
| `passage_sen_ep_8_70_4` | Seneca, Epistulae Morales ad Lucilium, 70.4 | 263 |
| `passage_sen_ep_8_70_5` | Seneca, Epistulae Morales ad Lucilium, 70.5 | 482 |
| `passage_sen_ep_8_70_6` | Seneca, Epistulae Morales ad Lucilium, 70.6 | 365 |
| `passage_sen_ep_8_70_7` | Seneca, Epistulae Morales ad Lucilium, 70.7 | 260 |
| `passage_sen_ep_8_70_8` | Seneca, Epistulae Morales ad Lucilium, 70.8 | 302 |
| `passage_sen_ep_8_70_9` | Seneca, Epistulae Morales ad Lucilium, 70.9 | 365 |
| `passage_sen_ep_8_71_1` | Seneca, Epistulae Morales ad Lucilium, 71.1 | 427 |
| `passage_sen_ep_8_71_10` | Seneca, Epistulae Morales ad Lucilium, 71.10 | 269 |
| `passage_sen_ep_8_71_11` | Seneca, Epistulae Morales ad Lucilium, 71.11 | 297 |
| `passage_sen_ep_8_71_12` | Seneca, Epistulae Morales ad Lucilium, 71.12 | 276 |
| `passage_sen_ep_8_71_13` | Seneca, Epistulae Morales ad Lucilium, 71.13 | 318 |
| `passage_sen_ep_8_71_14` | Seneca, Epistulae Morales ad Lucilium, 71.14 | 323 |
| `passage_sen_ep_8_71_15` | Seneca, Epistulae Morales ad Lucilium, 71.15 | 590 |
| `passage_sen_ep_8_71_16` | Seneca, Epistulae Morales ad Lucilium, 71.16 | 477 |
| `passage_sen_ep_8_71_17` | Seneca, Epistulae Morales ad Lucilium, 71.17 | 522 |
| `passage_sen_ep_8_71_18` | Seneca, Epistulae Morales ad Lucilium, 71.18 | 421 |
| `passage_sen_ep_8_71_19` | Seneca, Epistulae Morales ad Lucilium, 71.19 | 368 |
| `passage_sen_ep_8_71_2` | Seneca, Epistulae Morales ad Lucilium, 71.2 | 407 |
| `passage_sen_ep_8_71_20` | Seneca, Epistulae Morales ad Lucilium, 71.20 | 295 |
| `passage_sen_ep_8_71_21` | Seneca, Epistulae Morales ad Lucilium, 71.21 | 317 |
| `passage_sen_ep_8_71_22` | Seneca, Epistulae Morales ad Lucilium, 71.22 | 346 |
| `passage_sen_ep_8_71_23` | Seneca, Epistulae Morales ad Lucilium, 71.23 | 419 |
| `passage_sen_ep_8_71_24` | Seneca, Epistulae Morales ad Lucilium, 71.24 | 293 |
| `passage_sen_ep_8_71_25` | Seneca, Epistulae Morales ad Lucilium, 71.25 | 302 |
| `passage_sen_ep_8_71_26` | Seneca, Epistulae Morales ad Lucilium, 71.26 | 405 |
| `passage_sen_ep_8_71_27` | Seneca, Epistulae Morales ad Lucilium, 71.27 | 447 |
| `passage_sen_ep_8_71_28` | Seneca, Epistulae Morales ad Lucilium, 71.28 | 501 |
| `passage_sen_ep_8_71_29` | Seneca, Epistulae Morales ad Lucilium, 71.29 | 342 |
| `passage_sen_ep_8_71_3` | Seneca, Epistulae Morales ad Lucilium, 71.3 | 273 |
| `passage_sen_ep_8_71_30` | Seneca, Epistulae Morales ad Lucilium, 71.30 | 343 |
| `passage_sen_ep_8_71_31` | Seneca, Epistulae Morales ad Lucilium, 71.31 | 283 |
| `passage_sen_ep_8_71_32` | Seneca, Epistulae Morales ad Lucilium, 71.32 | 319 |
| `passage_sen_ep_8_71_33` | Seneca, Epistulae Morales ad Lucilium, 71.33 | 309 |
| `passage_sen_ep_8_71_34` | Seneca, Epistulae Morales ad Lucilium, 71.34 | 320 |
| `passage_sen_ep_8_71_35` | Seneca, Epistulae Morales ad Lucilium, 71.35 | 282 |
| `passage_sen_ep_8_71_36` | Seneca, Epistulae Morales ad Lucilium, 71.36 | 405 |
| `passage_sen_ep_8_71_37` | Seneca, Epistulae Morales ad Lucilium, 71.37 | 331 |
| `passage_sen_ep_8_71_4` | Seneca, Epistulae Morales ad Lucilium, 71.4 | 506 |
| `passage_sen_ep_8_71_5` | Seneca, Epistulae Morales ad Lucilium, 71.5 | 503 |
| `passage_sen_ep_8_71_6` | Seneca, Epistulae Morales ad Lucilium, 71.6 | 456 |
| `passage_sen_ep_8_71_7` | Seneca, Epistulae Morales ad Lucilium, 71.7 | 536 |
| `passage_sen_ep_8_71_8` | Seneca, Epistulae Morales ad Lucilium, 71.8 | 401 |
| `passage_sen_ep_8_71_9` | Seneca, Epistulae Morales ad Lucilium, 71.9 | 365 |
| `passage_sen_ep_8_72_1` | Seneca, Epistulae Morales ad Lucilium, 72.1 | 479 |
| `passage_sen_ep_8_72_10` | Seneca, Epistulae Morales ad Lucilium, 72.10 | 215 |
| `passage_sen_ep_8_72_11` | Seneca, Epistulae Morales ad Lucilium, 72.11 | 329 |
| `passage_sen_ep_8_72_2` | Seneca, Epistulae Morales ad Lucilium, 72.2 | 394 |
| `passage_sen_ep_8_72_3` | Seneca, Epistulae Morales ad Lucilium, 72.3 | 590 |
| `passage_sen_ep_8_72_4` | Seneca, Epistulae Morales ad Lucilium, 72.4 | 394 |
| `passage_sen_ep_8_72_5` | Seneca, Epistulae Morales ad Lucilium, 72.5 | 336 |
| `passage_sen_ep_8_72_6` | Seneca, Epistulae Morales ad Lucilium, 72.6 | 458 |
| `passage_sen_ep_8_72_7` | Seneca, Epistulae Morales ad Lucilium, 72.7 | 578 |
| `passage_sen_ep_8_72_8` | Seneca, Epistulae Morales ad Lucilium, 72.8 | 425 |
| `passage_sen_ep_8_72_9` | Seneca, Epistulae Morales ad Lucilium, 72.9 | 322 |
| `passage_sen_ep_8_73_1` | Seneca, Epistulae Morales ad Lucilium, 73.1 | 314 |
| `passage_sen_ep_8_73_10` | Seneca, Epistulae Morales ad Lucilium, 73.10 | 219 |
| `passage_sen_ep_8_73_11` | Seneca, Epistulae Morales ad Lucilium, 73.11 | 146 |
| `passage_sen_ep_8_73_12` | Seneca, Epistulae Morales ad Lucilium, 73.12 | 344 |
| `passage_sen_ep_8_73_13` | Seneca, Epistulae Morales ad Lucilium, 73.13 | 329 |
| `passage_sen_ep_8_73_14` | Seneca, Epistulae Morales ad Lucilium, 73.14 | 309 |
| `passage_sen_ep_8_73_15` | Seneca, Epistulae Morales ad Lucilium, 73.15 | 248 |
| `passage_sen_ep_8_73_16` | Seneca, Epistulae Morales ad Lucilium, 73.16 | 380 |
| `passage_sen_ep_8_73_2` | Seneca, Epistulae Morales ad Lucilium, 73.2 | 486 |
| `passage_sen_ep_8_73_3` | Seneca, Epistulae Morales ad Lucilium, 73.3 | 314 |
| `passage_sen_ep_8_73_4` | Seneca, Epistulae Morales ad Lucilium, 73.4 | 403 |
| `passage_sen_ep_8_73_5` | Seneca, Epistulae Morales ad Lucilium, 73.5 | 496 |
| `passage_sen_ep_8_73_6` | Seneca, Epistulae Morales ad Lucilium, 73.6 | 451 |
| `passage_sen_ep_8_73_7` | Seneca, Epistulae Morales ad Lucilium, 73.7 | 335 |
| `passage_sen_ep_8_73_8` | Seneca, Epistulae Morales ad Lucilium, 73.8 | 341 |
| `passage_sen_ep_8_73_9` | Seneca, Epistulae Morales ad Lucilium, 73.9 | 293 |
| `passage_sen_ep_8_74_1` | Seneca, Epistulae Morales ad Lucilium, 74.1 | 372 |
| `passage_sen_ep_8_74_10` | Seneca, Epistulae Morales ad Lucilium, 74.10 | 273 |
| `passage_sen_ep_8_74_11` | Seneca, Epistulae Morales ad Lucilium, 74.11 | 444 |
| `passage_sen_ep_8_74_12` | Seneca, Epistulae Morales ad Lucilium, 74.12 | 317 |
| `passage_sen_ep_8_74_13` | Seneca, Epistulae Morales ad Lucilium, 74.13 | 276 |
| `passage_sen_ep_8_74_14` | Seneca, Epistulae Morales ad Lucilium, 74.14 | 394 |
| `passage_sen_ep_8_74_15` | Seneca, Epistulae Morales ad Lucilium, 74.15 | 374 |
| `passage_sen_ep_8_74_16` | Seneca, Epistulae Morales ad Lucilium, 74.16 | 399 |
| `passage_sen_ep_8_74_17` | Seneca, Epistulae Morales ad Lucilium, 74.17 | 443 |
| `passage_sen_ep_8_74_18` | Seneca, Epistulae Morales ad Lucilium, 74.18 | 499 |
| `passage_sen_ep_8_74_19` | Seneca, Epistulae Morales ad Lucilium, 74.19 | 515 |
| `passage_sen_ep_8_74_2` | Seneca, Epistulae Morales ad Lucilium, 74.2 | 223 |
| `passage_sen_ep_8_74_20` | Seneca, Epistulae Morales ad Lucilium, 74.20 | 425 |
| `passage_sen_ep_8_74_21` | Seneca, Epistulae Morales ad Lucilium, 74.21 | 416 |
| `passage_sen_ep_8_74_22` | Seneca, Epistulae Morales ad Lucilium, 74.22 | 324 |
| `passage_sen_ep_8_74_23` | Seneca, Epistulae Morales ad Lucilium, 74.23 | 565 |
| `passage_sen_ep_8_74_24` | Seneca, Epistulae Morales ad Lucilium, 74.24 | 379 |
| `passage_sen_ep_8_74_25` | Seneca, Epistulae Morales ad Lucilium, 74.25 | 548 |
| `passage_sen_ep_8_74_26` | Seneca, Epistulae Morales ad Lucilium, 74.26 | 311 |
| `passage_sen_ep_8_74_27` | Seneca, Epistulae Morales ad Lucilium, 74.27 | 427 |
| `passage_sen_ep_8_74_28` | Seneca, Epistulae Morales ad Lucilium, 74.28 | 346 |
| `passage_sen_ep_8_74_29` | Seneca, Epistulae Morales ad Lucilium, 74.29 | 318 |
| `passage_sen_ep_8_74_3` | Seneca, Epistulae Morales ad Lucilium, 74.3 | 333 |
| `passage_sen_ep_8_74_30` | Seneca, Epistulae Morales ad Lucilium, 74.30 | 529 |
| `passage_sen_ep_8_74_31` | Seneca, Epistulae Morales ad Lucilium, 74.31 | 375 |
| `passage_sen_ep_8_74_32` | Seneca, Epistulae Morales ad Lucilium, 74.32 | 414 |
| `passage_sen_ep_8_74_33` | Seneca, Epistulae Morales ad Lucilium, 74.33 | 378 |
| `passage_sen_ep_8_74_34` | Seneca, Epistulae Morales ad Lucilium, 74.34 | 507 |
| `passage_sen_ep_8_74_4` | Seneca, Epistulae Morales ad Lucilium, 74.4 | 573 |
| `passage_sen_ep_8_74_5` | Seneca, Epistulae Morales ad Lucilium, 74.5 | 302 |
| `passage_sen_ep_8_74_6` | Seneca, Epistulae Morales ad Lucilium, 74.6 | 334 |
| `passage_sen_ep_8_74_7` | Seneca, Epistulae Morales ad Lucilium, 74.7 | 659 |
| `passage_sen_ep_8_74_8` | Seneca, Epistulae Morales ad Lucilium, 74.8 | 265 |
| `passage_sen_ep_8_74_9` | Seneca, Epistulae Morales ad Lucilium, 74.9 | 284 |
| `passage_sen_ep_9_75_1` | Seneca, Epistulae Morales ad Lucilium, 75.1 | 264 |
| `passage_sen_ep_9_75_10` | Seneca, Epistulae Morales ad Lucilium, 75.10 | 294 |
| `passage_sen_ep_9_75_11` | Seneca, Epistulae Morales ad Lucilium, 75.11 | 487 |
| `passage_sen_ep_9_75_12` | Seneca, Epistulae Morales ad Lucilium, 75.12 | 284 |
| `passage_sen_ep_9_75_13` | Seneca, Epistulae Morales ad Lucilium, 75.13 | 165 |
| `passage_sen_ep_9_75_14` | Seneca, Epistulae Morales ad Lucilium, 75.14 | 304 |
| `passage_sen_ep_9_75_15` | Seneca, Epistulae Morales ad Lucilium, 75.15 | 442 |
| `passage_sen_ep_9_75_16` | Seneca, Epistulae Morales ad Lucilium, 75.16 | 348 |
| `passage_sen_ep_9_75_17` | Seneca, Epistulae Morales ad Lucilium, 75.17 | 200 |
| `passage_sen_ep_9_75_18` | Seneca, Epistulae Morales ad Lucilium, 75.18 | 303 |
| `passage_sen_ep_9_75_2` | Seneca, Epistulae Morales ad Lucilium, 75.2 | 254 |
| `passage_sen_ep_9_75_3` | Seneca, Epistulae Morales ad Lucilium, 75.3 | 397 |
| `passage_sen_ep_9_75_4` | Seneca, Epistulae Morales ad Lucilium, 75.4 | 187 |
| `passage_sen_ep_9_75_5` | Seneca, Epistulae Morales ad Lucilium, 75.5 | 326 |
| `passage_sen_ep_9_75_6` | Seneca, Epistulae Morales ad Lucilium, 75.6 | 300 |
| `passage_sen_ep_9_75_7` | Seneca, Epistulae Morales ad Lucilium, 75.7 | 531 |
| `passage_sen_ep_9_75_8` | Seneca, Epistulae Morales ad Lucilium, 75.8 | 360 |
| `passage_sen_ep_9_75_9` | Seneca, Epistulae Morales ad Lucilium, 75.9 | 464 |
| `passage_sen_ep_9_76_1` | Seneca, Epistulae Morales ad Lucilium, 76.1 | 357 |
| `passage_sen_ep_9_76_10` | Seneca, Epistulae Morales ad Lucilium, 76.10 | 338 |
| `passage_sen_ep_9_76_11` | Seneca, Epistulae Morales ad Lucilium, 76.11 | 359 |
| `passage_sen_ep_9_76_12` | Seneca, Epistulae Morales ad Lucilium, 76.12 | 520 |
| `passage_sen_ep_9_76_13` | Seneca, Epistulae Morales ad Lucilium, 76.13 | 369 |
| `passage_sen_ep_9_76_14` | Seneca, Epistulae Morales ad Lucilium, 76.14 | 278 |
| `passage_sen_ep_9_76_15` | Seneca, Epistulae Morales ad Lucilium, 76.15 | 277 |
| `passage_sen_ep_9_76_16` | Seneca, Epistulae Morales ad Lucilium, 76.16 | 337 |
| `passage_sen_ep_9_76_17` | Seneca, Epistulae Morales ad Lucilium, 76.17 | 356 |
| `passage_sen_ep_9_76_18` | Seneca, Epistulae Morales ad Lucilium, 76.18 | 452 |
| `passage_sen_ep_9_76_19` | Seneca, Epistulae Morales ad Lucilium, 76.19 | 392 |
| `passage_sen_ep_9_76_2` | Seneca, Epistulae Morales ad Lucilium, 76.2 | 310 |
| `passage_sen_ep_9_76_20` | Seneca, Epistulae Morales ad Lucilium, 76.20 | 465 |
| `passage_sen_ep_9_76_21` | Seneca, Epistulae Morales ad Lucilium, 76.21 | 215 |
| `passage_sen_ep_9_76_22` | Seneca, Epistulae Morales ad Lucilium, 76.22 | 302 |
| `passage_sen_ep_9_76_23` | Seneca, Epistulae Morales ad Lucilium, 76.23 | 370 |
| `passage_sen_ep_9_76_24` | Seneca, Epistulae Morales ad Lucilium, 76.24 | 190 |
| `passage_sen_ep_9_76_25` | Seneca, Epistulae Morales ad Lucilium, 76.25 | 410 |
| `passage_sen_ep_9_76_26` | Seneca, Epistulae Morales ad Lucilium, 76.26 | 344 |
| `passage_sen_ep_9_76_27` | Seneca, Epistulae Morales ad Lucilium, 76.27 | 441 |
| `passage_sen_ep_9_76_28` | Seneca, Epistulae Morales ad Lucilium, 76.28 | 392 |
| `passage_sen_ep_9_76_29` | Seneca, Epistulae Morales ad Lucilium, 76.29 | 420 |
| `passage_sen_ep_9_76_3` | Seneca, Epistulae Morales ad Lucilium, 76.3 | 259 |
| `passage_sen_ep_9_76_30` | Seneca, Epistulae Morales ad Lucilium, 76.30 | 531 |
| `passage_sen_ep_9_76_31` | Seneca, Epistulae Morales ad Lucilium, 76.31 | 250 |
| `passage_sen_ep_9_76_32` | Seneca, Epistulae Morales ad Lucilium, 76.32 | 355 |
| `passage_sen_ep_9_76_33` | Seneca, Epistulae Morales ad Lucilium, 76.33 | 386 |
| `passage_sen_ep_9_76_34` | Seneca, Epistulae Morales ad Lucilium, 76.34 | 244 |
| `passage_sen_ep_9_76_35` | Seneca, Epistulae Morales ad Lucilium, 76.35 | 264 |
| `passage_sen_ep_9_76_4` | Seneca, Epistulae Morales ad Lucilium, 76.4 | 590 |
| `passage_sen_ep_9_76_5` | Seneca, Epistulae Morales ad Lucilium, 76.5 | 204 |
| `passage_sen_ep_9_76_6` | Seneca, Epistulae Morales ad Lucilium, 76.6 | 381 |
| `passage_sen_ep_9_76_7` | Seneca, Epistulae Morales ad Lucilium, 76.7 | 194 |
| `passage_sen_ep_9_76_8` | Seneca, Epistulae Morales ad Lucilium, 76.8 | 338 |
| `passage_sen_ep_9_76_9` | Seneca, Epistulae Morales ad Lucilium, 76.9 | 514 |
| `passage_sen_ep_9_77_1` | Seneca, Epistulae Morales ad Lucilium, 77.1 | 363 |
| `passage_sen_ep_9_77_10` | Seneca, Epistulae Morales ad Lucilium, 77.10 | 324 |
| `passage_sen_ep_9_77_11` | Seneca, Epistulae Morales ad Lucilium, 77.11 | 330 |
| `passage_sen_ep_9_77_12` | Seneca, Epistulae Morales ad Lucilium, 77.12 | 397 |
| `passage_sen_ep_9_77_13` | Seneca, Epistulae Morales ad Lucilium, 77.13 | 342 |
| `passage_sen_ep_9_77_14` | Seneca, Epistulae Morales ad Lucilium, 77.14 | 333 |
| `passage_sen_ep_9_77_15` | Seneca, Epistulae Morales ad Lucilium, 77.15 | 400 |
| `passage_sen_ep_9_77_16` | Seneca, Epistulae Morales ad Lucilium, 77.16 | 431 |
| `passage_sen_ep_9_77_17` | Seneca, Epistulae Morales ad Lucilium, 77.17 | 366 |
| `passage_sen_ep_9_77_18` | Seneca, Epistulae Morales ad Lucilium, 77.18 | 383 |
| `passage_sen_ep_9_77_19` | Seneca, Epistulae Morales ad Lucilium, 77.19 | 265 |
| `passage_sen_ep_9_77_2` | Seneca, Epistulae Morales ad Lucilium, 77.2 | 325 |
| `passage_sen_ep_9_77_20` | Seneca, Epistulae Morales ad Lucilium, 77.20 | 446 |
| `passage_sen_ep_9_77_3` | Seneca, Epistulae Morales ad Lucilium, 77.3 | 465 |
| `passage_sen_ep_9_77_4` | Seneca, Epistulae Morales ad Lucilium, 77.4 | 269 |
| `passage_sen_ep_9_77_5` | Seneca, Epistulae Morales ad Lucilium, 77.5 | 530 |
| `passage_sen_ep_9_77_6` | Seneca, Epistulae Morales ad Lucilium, 77.6 | 355 |
| `passage_sen_ep_9_77_7` | Seneca, Epistulae Morales ad Lucilium, 77.7 | 254 |
| `passage_sen_ep_9_77_8` | Seneca, Epistulae Morales ad Lucilium, 77.8 | 342 |
| `passage_sen_ep_9_77_9` | Seneca, Epistulae Morales ad Lucilium, 77.9 | 315 |
| `passage_sen_ep_9_78_1` | Seneca, Epistulae Morales ad Lucilium, 78.1 | 377 |
| `passage_sen_ep_9_78_10` | Seneca, Epistulae Morales ad Lucilium, 78.10 | 379 |
| `passage_sen_ep_9_78_11` | Seneca, Epistulae Morales ad Lucilium, 78.11 | 360 |
| `passage_sen_ep_9_78_12` | Seneca, Epistulae Morales ad Lucilium, 78.12 | 273 |
| `passage_sen_ep_9_78_13` | Seneca, Epistulae Morales ad Lucilium, 78.13 | 400 |
| `passage_sen_ep_9_78_14` | Seneca, Epistulae Morales ad Lucilium, 78.14 | 653 |
| `passage_sen_ep_9_78_15` | Seneca, Epistulae Morales ad Lucilium, 78.15 | 363 |
| `passage_sen_ep_9_78_16` | Seneca, Epistulae Morales ad Lucilium, 78.16 | 433 |
| `passage_sen_ep_9_78_17` | Seneca, Epistulae Morales ad Lucilium, 78.17 | 582 |
| `passage_sen_ep_9_78_18` | Seneca, Epistulae Morales ad Lucilium, 78.18 | 495 |
| `passage_sen_ep_9_78_19` | Seneca, Epistulae Morales ad Lucilium, 78.19 | 483 |
| `passage_sen_ep_9_78_2` | Seneca, Epistulae Morales ad Lucilium, 78.2 | 257 |
| `passage_sen_ep_9_78_20` | Seneca, Epistulae Morales ad Lucilium, 78.20 | 385 |
| `passage_sen_ep_9_78_21` | Seneca, Epistulae Morales ad Lucilium, 78.21 | 362 |
| `passage_sen_ep_9_78_22` | Seneca, Epistulae Morales ad Lucilium, 78.22 | 396 |
| `passage_sen_ep_9_78_23` | Seneca, Epistulae Morales ad Lucilium, 78.23 | 428 |
| `passage_sen_ep_9_78_24` | Seneca, Epistulae Morales ad Lucilium, 78.24 | 282 |
| `passage_sen_ep_9_78_25` | Seneca, Epistulae Morales ad Lucilium, 78.25 | 305 |
| `passage_sen_ep_9_78_26` | Seneca, Epistulae Morales ad Lucilium, 78.26 | 215 |
| `passage_sen_ep_9_78_27` | Seneca, Epistulae Morales ad Lucilium, 78.27 | 295 |
| `passage_sen_ep_9_78_28` | Seneca, Epistulae Morales ad Lucilium, 78.28 | 280 |
| `passage_sen_ep_9_78_29` | Seneca, Epistulae Morales ad Lucilium, 78.29 | 212 |
| `passage_sen_ep_9_78_3` | Seneca, Epistulae Morales ad Lucilium, 78.3 | 336 |
| `passage_sen_ep_9_78_4` | Seneca, Epistulae Morales ad Lucilium, 78.4 | 564 |
| `passage_sen_ep_9_78_5` | Seneca, Epistulae Morales ad Lucilium, 78.5 | 525 |
| `passage_sen_ep_9_78_6` | Seneca, Epistulae Morales ad Lucilium, 78.6 | 369 |
| `passage_sen_ep_9_78_7` | Seneca, Epistulae Morales ad Lucilium, 78.7 | 283 |
| `passage_sen_ep_9_78_8` | Seneca, Epistulae Morales ad Lucilium, 78.8 | 451 |
| `passage_sen_ep_9_78_9` | Seneca, Epistulae Morales ad Lucilium, 78.9 | 419 |
| `passage_sen_ep_9_79_1` | Seneca, Epistulae Morales ad Lucilium, 79.1 | 567 |
| `passage_sen_ep_9_79_10` | Seneca, Epistulae Morales ad Lucilium, 79.10 | 339 |
| `passage_sen_ep_9_79_11` | Seneca, Epistulae Morales ad Lucilium, 79.11 | 270 |
| `passage_sen_ep_9_79_12` | Seneca, Epistulae Morales ad Lucilium, 79.12 | 400 |
| `passage_sen_ep_9_79_13` | Seneca, Epistulae Morales ad Lucilium, 79.13 | 353 |
| `passage_sen_ep_9_79_14` | Seneca, Epistulae Morales ad Lucilium, 79.14 | 445 |
| `passage_sen_ep_9_79_15` | Seneca, Epistulae Morales ad Lucilium, 79.15 | 436 |
| `passage_sen_ep_9_79_16` | Seneca, Epistulae Morales ad Lucilium, 79.16 | 278 |
| `passage_sen_ep_9_79_17` | Seneca, Epistulae Morales ad Lucilium, 79.17 | 510 |
| `passage_sen_ep_9_79_18` | Seneca, Epistulae Morales ad Lucilium, 79.18 | 407 |
| `passage_sen_ep_9_79_2` | Seneca, Epistulae Morales ad Lucilium, 79.2 | 599 |
| `passage_sen_ep_9_79_3` | Seneca, Epistulae Morales ad Lucilium, 79.3 | 254 |
| `passage_sen_ep_9_79_4` | Seneca, Epistulae Morales ad Lucilium, 79.4 | 261 |
| `passage_sen_ep_9_79_5` | Seneca, Epistulae Morales ad Lucilium, 79.5 | 363 |
| `passage_sen_ep_9_79_6` | Seneca, Epistulae Morales ad Lucilium, 79.6 | 264 |
| `passage_sen_ep_9_79_7` | Seneca, Epistulae Morales ad Lucilium, 79.7 | 303 |
| `passage_sen_ep_9_79_8` | Seneca, Epistulae Morales ad Lucilium, 79.8 | 299 |
| `passage_sen_ep_9_79_9` | Seneca, Epistulae Morales ad Lucilium, 79.9 | 310 |
| `passage_sen_ep_9_80_1` | Seneca, Epistulae Morales ad Lucilium, 80.1 | 470 |
| `passage_sen_ep_9_80_10` | Seneca, Epistulae Morales ad Lucilium, 80.10 | 302 |
| `passage_sen_ep_9_80_2` | Seneca, Epistulae Morales ad Lucilium, 80.2 | 427 |
| `passage_sen_ep_9_80_3` | Seneca, Epistulae Morales ad Lucilium, 80.3 | 624 |
| `passage_sen_ep_9_80_4` | Seneca, Epistulae Morales ad Lucilium, 80.4 | 374 |
| `passage_sen_ep_9_80_5` | Seneca, Epistulae Morales ad Lucilium, 80.5 | 269 |
| `passage_sen_ep_9_80_6` | Seneca, Epistulae Morales ad Lucilium, 80.6 | 418 |
| `passage_sen_ep_9_80_7` | Seneca, Epistulae Morales ad Lucilium, 80.7 | 322 |
| `passage_sen_ep_9_80_8` | Seneca, Epistulae Morales ad Lucilium, 80.8 | 267 |
| `passage_sen_ep_9_80_9` | Seneca, Epistulae Morales ad Lucilium, 80.9 | 332 |

### Plotinus — Enneades

- **Language:** Greek
- **Passages:** 1355
- **Characters:** 1,753,081
- **Canonical ID:** `urn:cts:greekLit:tlg2000.tlg001`

| node_id | label | chars |
|---------|-------|-------|
| `passage_plotinus_i_1_1` | Plotinus, Enneades, Enn. I.1.1 | 1,337 |
| `passage_plotinus_i_1_10` | Plotinus, Enneades, Enn. I.1.10 | 1,019 |
| `passage_plotinus_i_1_11` | Plotinus, Enneades, Enn. I.1.11 | 1,387 |
| `passage_plotinus_i_1_12` | Plotinus, Enneades, Enn. I.1.12 | 1,491 |
| `passage_plotinus_i_1_13` | Plotinus, Enneades, Enn. I.1.13 | 1,480 |
| `passage_plotinus_i_1_2` | Plotinus, Enneades, Enn. I.1.2 | 1,487 |
| `passage_plotinus_i_1_3` | Plotinus, Enneades, Enn. I.1.3 | 1,429 |
| `passage_plotinus_i_1_4` | Plotinus, Enneades, Enn. I.1.4 | 1,374 |
| `passage_plotinus_i_1_5` | Plotinus, Enneades, Enn. I.1.5 | 1,364 |
| `passage_plotinus_i_1_6` | Plotinus, Enneades, Enn. I.1.6 | 1,040 |
| `passage_plotinus_i_1_7` | Plotinus, Enneades, Enn. I.1.7 | 1,444 |
| `passage_plotinus_i_1_8` | Plotinus, Enneades, Enn. I.1.8 | 1,391 |
| `passage_plotinus_i_1_9` | Plotinus, Enneades, Enn. I.1.9 | 1,482 |
| `passage_plotinus_i_2_1` | Plotinus, Enneades, Enn. I.2.1 | 1,362 |
| `passage_plotinus_i_2_2` | Plotinus, Enneades, Enn. I.2.2 | 1,357 |
| `passage_plotinus_i_2_3` | Plotinus, Enneades, Enn. I.2.3 | 1,428 |
| `passage_plotinus_i_2_4` | Plotinus, Enneades, Enn. I.2.4 | 1,347 |
| `passage_plotinus_i_2_5` | Plotinus, Enneades, Enn. I.2.5 | 1,371 |
| `passage_plotinus_i_2_6` | Plotinus, Enneades, Enn. I.2.6 | 1,131 |
| `passage_plotinus_i_2_7` | Plotinus, Enneades, Enn. I.2.7 | 1,331 |
| `passage_plotinus_i_3_1` | Plotinus, Enneades, Enn. I.3.1 | 1,303 |
| `passage_plotinus_i_3_2` | Plotinus, Enneades, Enn. I.3.2 | 1,368 |
| `passage_plotinus_i_3_3` | Plotinus, Enneades, Enn. I.3.3 | 1,449 |
| `passage_plotinus_i_3_4` | Plotinus, Enneades, Enn. I.3.4 | 1,344 |
| `passage_plotinus_i_3_5` | Plotinus, Enneades, Enn. I.3.5 | 1,499 |
| `passage_plotinus_i_3_6` | Plotinus, Enneades, Enn. I.3.6 | 1,312 |
| `passage_plotinus_i_4_1` | Plotinus, Enneades, Enn. I.4.1 | 1,459 |
| `passage_plotinus_i_4_10` | Plotinus, Enneades, Enn. I.4.10 | 1,448 |
| `passage_plotinus_i_4_11` | Plotinus, Enneades, Enn. I.4.11 | 1,131 |
| `passage_plotinus_i_4_12` | Plotinus, Enneades, Enn. I.4.12 | 1,313 |
| `passage_plotinus_i_4_13` | Plotinus, Enneades, Enn. I.4.13 | 1,202 |
| `passage_plotinus_i_4_14` | Plotinus, Enneades, Enn. I.4.14 | 1,486 |
| `passage_plotinus_i_4_15` | Plotinus, Enneades, Enn. I.4.15 | 926 |
| `passage_plotinus_i_4_16` | Plotinus, Enneades, Enn. I.4.16 | 1,053 |
| `passage_plotinus_i_4_2` | Plotinus, Enneades, Enn. I.4.2 | 1,337 |
| `passage_plotinus_i_4_3` | Plotinus, Enneades, Enn. I.4.3 | 1,417 |
| `passage_plotinus_i_4_4` | Plotinus, Enneades, Enn. I.4.4 | 1,460 |
| `passage_plotinus_i_4_5` | Plotinus, Enneades, Enn. I.4.5 | 1,413 |
| `passage_plotinus_i_4_6` | Plotinus, Enneades, Enn. I.4.6 | 1,397 |
| `passage_plotinus_i_4_7` | Plotinus, Enneades, Enn. I.4.7 | 1,228 |
| `passage_plotinus_i_4_8` | Plotinus, Enneades, Enn. I.4.8 | 1,189 |
| `passage_plotinus_i_4_9` | Plotinus, Enneades, Enn. I.4.9 | 1,160 |
| `passage_plotinus_i_5_1` | Plotinus, Enneades, Enn. I.5.1 | 1,249 |
| `passage_plotinus_i_5_10` | Plotinus, Enneades, Enn. I.5.10 | 1,441 |
| `passage_plotinus_i_5_2` | Plotinus, Enneades, Enn. I.5.2 | 1,214 |
| `passage_plotinus_i_5_3` | Plotinus, Enneades, Enn. I.5.3 | 1,349 |
| `passage_plotinus_i_5_4` | Plotinus, Enneades, Enn. I.5.4 | 1,405 |
| `passage_plotinus_i_5_5` | Plotinus, Enneades, Enn. I.5.5 | 1,375 |
| `passage_plotinus_i_5_6` | Plotinus, Enneades, Enn. I.5.6 | 1,023 |
| `passage_plotinus_i_5_7` | Plotinus, Enneades, Enn. I.5.7 | 1,416 |
| `passage_plotinus_i_5_8` | Plotinus, Enneades, Enn. I.5.8 | 1,094 |
| `passage_plotinus_i_5_9` | Plotinus, Enneades, Enn. I.5.9 | 1,076 |
| `passage_plotinus_i_6_1` | Plotinus, Enneades, Enn. I.6.1 | 1,330 |
| `passage_plotinus_i_6_2` | Plotinus, Enneades, Enn. I.6.2 | 1,264 |
| `passage_plotinus_i_6_3` | Plotinus, Enneades, Enn. I.6.3 | 1,470 |
| `passage_plotinus_i_6_4` | Plotinus, Enneades, Enn. I.6.4 | 661 |
| `passage_plotinus_i_6_5` | Plotinus, Enneades, Enn. I.6.5 | 1,497 |
| `passage_plotinus_i_6_6` | Plotinus, Enneades, Enn. I.6.6 | 1,402 |
| `passage_plotinus_i_6_7` | Plotinus, Enneades, Enn. I.6.7 | 1,419 |
| `passage_plotinus_i_6_8` | Plotinus, Enneades, Enn. I.6.8 | 1,473 |
| `passage_plotinus_i_6_9` | Plotinus, Enneades, Enn. I.6.9 | 1,119 |
| `passage_plotinus_i_7_1` | Plotinus, Enneades, Enn. I.7.1 | 1,307 |
| `passage_plotinus_i_7_2` | Plotinus, Enneades, Enn. I.7.2 | 1,473 |
| `passage_plotinus_i_7_3` | Plotinus, Enneades, Enn. I.7.3 | 1,253 |
| `passage_plotinus_i_8_1` | Plotinus, Enneades, Enn. I.8.1 | 966 |
| `passage_plotinus_i_8_10` | Plotinus, Enneades, Enn. I.8.10 | 1,270 |
| `passage_plotinus_i_8_11` | Plotinus, Enneades, Enn. I.8.11 | 1,314 |
| `passage_plotinus_i_8_12` | Plotinus, Enneades, Enn. I.8.12 | 1,443 |
| `passage_plotinus_i_8_13` | Plotinus, Enneades, Enn. I.8.13 | 1,495 |
| `passage_plotinus_i_8_14` | Plotinus, Enneades, Enn. I.8.14 | 1,168 |
| `passage_plotinus_i_8_15` | Plotinus, Enneades, Enn. I.8.15 | 1,478 |
| `passage_plotinus_i_8_2` | Plotinus, Enneades, Enn. I.8.2 | 1,321 |
| `passage_plotinus_i_8_3` | Plotinus, Enneades, Enn. I.8.3 | 1,339 |
| `passage_plotinus_i_8_4` | Plotinus, Enneades, Enn. I.8.4 | 1,244 |
| `passage_plotinus_i_8_5` | Plotinus, Enneades, Enn. I.8.5 | 1,386 |
| `passage_plotinus_i_8_6` | Plotinus, Enneades, Enn. I.8.6 | 1,463 |
| `passage_plotinus_i_8_7` | Plotinus, Enneades, Enn. I.8.7 | 1,190 |
| `passage_plotinus_i_8_8` | Plotinus, Enneades, Enn. I.8.8 | 1,480 |
| `passage_plotinus_i_8_9` | Plotinus, Enneades, Enn. I.8.9 | 1,347 |
| `passage_plotinus_i_9_1` | Plotinus, Enneades, Enn. I.9.1 | 1,201 |
| `passage_plotinus_ii_1_1` | Plotinus, Enneades, Enn. II.1.1 | 1,451 |
| `passage_plotinus_ii_1_2` | Plotinus, Enneades, Enn. II.1.2 | 1,462 |
| `passage_plotinus_ii_1_3` | Plotinus, Enneades, Enn. II.1.3 | 869 |
| `passage_plotinus_ii_1_4` | Plotinus, Enneades, Enn. II.1.4 | 1,352 |
| `passage_plotinus_ii_1_5` | Plotinus, Enneades, Enn. II.1.5 | 1,491 |
| `passage_plotinus_ii_1_6` | Plotinus, Enneades, Enn. II.1.6 | 1,500 |
| `passage_plotinus_ii_1_7` | Plotinus, Enneades, Enn. II.1.7 | 1,154 |
| `passage_plotinus_ii_1_8` | Plotinus, Enneades, Enn. II.1.8 | 1,455 |
| `passage_plotinus_ii_2_1` | Plotinus, Enneades, Enn. II.2.1 | 1,311 |
| `passage_plotinus_ii_2_2` | Plotinus, Enneades, Enn. II.2.2 | 1,055 |
| `passage_plotinus_ii_2_3` | Plotinus, Enneades, Enn. II.2.3 | 868 |
| `passage_plotinus_ii_3_1` | Plotinus, Enneades, Enn. II.3.1 | 717 |
| `passage_plotinus_ii_3_10` | Plotinus, Enneades, Enn. II.3.10 | 1,322 |
| `passage_plotinus_ii_3_11` | Plotinus, Enneades, Enn. II.3.11 | 1,429 |
| `passage_plotinus_ii_3_12` | Plotinus, Enneades, Enn. II.3.12 | 1,260 |
| `passage_plotinus_ii_3_13` | Plotinus, Enneades, Enn. II.3.13 | 1,217 |
| `passage_plotinus_ii_3_14` | Plotinus, Enneades, Enn. II.3.14 | 1,439 |
| `passage_plotinus_ii_3_15` | Plotinus, Enneades, Enn. II.3.15 | 1,370 |
| `passage_plotinus_ii_3_16` | Plotinus, Enneades, Enn. II.3.16 | 1,321 |
| `passage_plotinus_ii_3_17` | Plotinus, Enneades, Enn. II.3.17 | 1,193 |
| `passage_plotinus_ii_3_18` | Plotinus, Enneades, Enn. II.3.18 | 1,419 |
| `passage_plotinus_ii_3_2` | Plotinus, Enneades, Enn. II.3.2 | 1,499 |
| `passage_plotinus_ii_3_3` | Plotinus, Enneades, Enn. II.3.3 | 1,341 |
| `passage_plotinus_ii_3_4` | Plotinus, Enneades, Enn. II.3.4 | 1,315 |
| `passage_plotinus_ii_3_5` | Plotinus, Enneades, Enn. II.3.5 | 1,276 |
| `passage_plotinus_ii_3_6` | Plotinus, Enneades, Enn. II.3.6 | 1,486 |
| `passage_plotinus_ii_3_7` | Plotinus, Enneades, Enn. II.3.7 | 1,299 |
| `passage_plotinus_ii_3_8` | Plotinus, Enneades, Enn. II.3.8 | 1,488 |
| `passage_plotinus_ii_3_9` | Plotinus, Enneades, Enn. II.3.9 | 1,483 |
| `passage_plotinus_ii_4_1` | Plotinus, Enneades, Enn. II.4.1 | 1,446 |
| `passage_plotinus_ii_4_10` | Plotinus, Enneades, Enn. II.4.10 | 1,414 |
| `passage_plotinus_ii_4_11` | Plotinus, Enneades, Enn. II.4.11 | 1,481 |
| `passage_plotinus_ii_4_12` | Plotinus, Enneades, Enn. II.4.12 | 1,447 |
| `passage_plotinus_ii_4_13` | Plotinus, Enneades, Enn. II.4.13 | 1,390 |
| `passage_plotinus_ii_4_14` | Plotinus, Enneades, Enn. II.4.14 | 1,393 |
| `passage_plotinus_ii_4_15` | Plotinus, Enneades, Enn. II.4.15 | 982 |
| `passage_plotinus_ii_4_16` | Plotinus, Enneades, Enn. II.4.16 | 1,371 |
| `passage_plotinus_ii_4_2` | Plotinus, Enneades, Enn. II.4.2 | 1,492 |
| `passage_plotinus_ii_4_3` | Plotinus, Enneades, Enn. II.4.3 | 1,441 |
| `passage_plotinus_ii_4_4` | Plotinus, Enneades, Enn. II.4.4 | 1,089 |
| `passage_plotinus_ii_4_5` | Plotinus, Enneades, Enn. II.4.5 | 1,402 |
| `passage_plotinus_ii_4_6` | Plotinus, Enneades, Enn. II.4.6 | 1,303 |
| `passage_plotinus_ii_4_7` | Plotinus, Enneades, Enn. II.4.7 | 1,452 |
| `passage_plotinus_ii_4_8` | Plotinus, Enneades, Enn. II.4.8 | 1,410 |
| `passage_plotinus_ii_4_9` | Plotinus, Enneades, Enn. II.4.9 | 1,315 |
| `passage_plotinus_ii_5_1` | Plotinus, Enneades, Enn. II.5.1 | 1,482 |
| `passage_plotinus_ii_5_2` | Plotinus, Enneades, Enn. II.5.2 | 1,496 |
| `passage_plotinus_ii_5_3` | Plotinus, Enneades, Enn. II.5.3 | 1,204 |
| `passage_plotinus_ii_5_4` | Plotinus, Enneades, Enn. II.5.4 | 1,355 |
| `passage_plotinus_ii_5_5` | Plotinus, Enneades, Enn. II.5.5 | 1,330 |
| `passage_plotinus_ii_6_1` | Plotinus, Enneades, Enn. II.6.1 | 1,304 |
| `passage_plotinus_ii_6_2` | Plotinus, Enneades, Enn. II.6.2 | 1,282 |
| `passage_plotinus_ii_6_3` | Plotinus, Enneades, Enn. II.6.3 | 1,279 |
| `passage_plotinus_ii_7_1` | Plotinus, Enneades, Enn. II.7.1 | 1,448 |
| `passage_plotinus_ii_7_2` | Plotinus, Enneades, Enn. II.7.2 | 1,451 |
| `passage_plotinus_ii_7_3` | Plotinus, Enneades, Enn. II.7.3 | 1,170 |
| `passage_plotinus_ii_8_1` | Plotinus, Enneades, Enn. II.8.1 | 1,417 |
| `passage_plotinus_ii_9_1` | Plotinus, Enneades, Enn. II.9.1 | 1,092 |
| `passage_plotinus_ii_9_10` | Plotinus, Enneades, Enn. II.9.10 | 809 |
| `passage_plotinus_ii_9_11` | Plotinus, Enneades, Enn. II.9.11 | 1,654 |
| `passage_plotinus_ii_9_12` | Plotinus, Enneades, Enn. II.9.12 | 1,394 |
| `passage_plotinus_ii_9_13` | Plotinus, Enneades, Enn. II.9.13 | 1,459 |
| `passage_plotinus_ii_9_14` | Plotinus, Enneades, Enn. II.9.14 | 1,097 |
| `passage_plotinus_ii_9_15` | Plotinus, Enneades, Enn. II.9.15 | 907 |
| `passage_plotinus_ii_9_16` | Plotinus, Enneades, Enn. II.9.16 | 1,283 |
| `passage_plotinus_ii_9_17` | Plotinus, Enneades, Enn. II.9.17 | 1,245 |
| `passage_plotinus_ii_9_18` | Plotinus, Enneades, Enn. II.9.18 | 865 |
| `passage_plotinus_ii_9_2` | Plotinus, Enneades, Enn. II.9.2 | 1,293 |
| `passage_plotinus_ii_9_3` | Plotinus, Enneades, Enn. II.9.3 | 1,437 |
| `passage_plotinus_ii_9_4` | Plotinus, Enneades, Enn. II.9.4 | 1,376 |
| `passage_plotinus_ii_9_5` | Plotinus, Enneades, Enn. II.9.5 | 1,398 |
| `passage_plotinus_ii_9_6` | Plotinus, Enneades, Enn. II.9.6 | 1,399 |
| `passage_plotinus_ii_9_7` | Plotinus, Enneades, Enn. II.9.7 | 1,443 |
| `passage_plotinus_ii_9_8` | Plotinus, Enneades, Enn. II.9.8 | 1,235 |
| `passage_plotinus_ii_9_9` | Plotinus, Enneades, Enn. II.9.9 | 1,311 |
| `passage_plotinus_iii_1_1` | Plotinus, Enneades, Enn. III.1.1 | 1,380 |
| `passage_plotinus_iii_1_10` | Plotinus, Enneades, Enn. III.1.10 | 1,401 |
| `passage_plotinus_iii_1_2` | Plotinus, Enneades, Enn. III.1.2 | 1,342 |
| `passage_plotinus_iii_1_3` | Plotinus, Enneades, Enn. III.1.3 | 1,377 |
| `passage_plotinus_iii_1_4` | Plotinus, Enneades, Enn. III.1.4 | 1,344 |
| `passage_plotinus_iii_1_5` | Plotinus, Enneades, Enn. III.1.5 | 1,344 |
| `passage_plotinus_iii_1_6` | Plotinus, Enneades, Enn. III.1.6 | 1,478 |
| `passage_plotinus_iii_1_7` | Plotinus, Enneades, Enn. III.1.7 | 1,020 |
| `passage_plotinus_iii_1_8` | Plotinus, Enneades, Enn. III.1.8 | 1,431 |
| `passage_plotinus_iii_1_9` | Plotinus, Enneades, Enn. III.1.9 | 1,266 |
| `passage_plotinus_iii_2_1` | Plotinus, Enneades, Enn. III.2.1 | 1,195 |
| `passage_plotinus_iii_2_10` | Plotinus, Enneades, Enn. III.2.10 | 1,458 |
| `passage_plotinus_iii_2_11` | Plotinus, Enneades, Enn. III.2.11 | 1,248 |
| `passage_plotinus_iii_2_12` | Plotinus, Enneades, Enn. III.2.12 | 1,218 |
| `passage_plotinus_iii_2_13` | Plotinus, Enneades, Enn. III.2.13 | 1,440 |
| `passage_plotinus_iii_2_14` | Plotinus, Enneades, Enn. III.2.14 | 1,460 |
| `passage_plotinus_iii_2_15` | Plotinus, Enneades, Enn. III.2.15 | 1,466 |
| `passage_plotinus_iii_2_16` | Plotinus, Enneades, Enn. III.2.16 | 1,415 |
| `passage_plotinus_iii_2_17` | Plotinus, Enneades, Enn. III.2.17 | 1,391 |
| `passage_plotinus_iii_2_18` | Plotinus, Enneades, Enn. III.2.18 | 1,184 |
| `passage_plotinus_iii_2_2` | Plotinus, Enneades, Enn. III.2.2 | 1,450 |
| `passage_plotinus_iii_2_3` | Plotinus, Enneades, Enn. III.2.3 | 1,394 |
| `passage_plotinus_iii_2_4` | Plotinus, Enneades, Enn. III.2.4 | 990 |
| `passage_plotinus_iii_2_5` | Plotinus, Enneades, Enn. III.2.5 | 1,229 |
| `passage_plotinus_iii_2_6` | Plotinus, Enneades, Enn. III.2.6 | 1,441 |
| `passage_plotinus_iii_2_7` | Plotinus, Enneades, Enn. III.2.7 | 1,338 |
| `passage_plotinus_iii_2_8` | Plotinus, Enneades, Enn. III.2.8 | 1,426 |
| `passage_plotinus_iii_2_9` | Plotinus, Enneades, Enn. III.2.9 | 1,365 |
| `passage_plotinus_iii_3_1` | Plotinus, Enneades, Enn. III.3.1 | 1,241 |
| `passage_plotinus_iii_3_2` | Plotinus, Enneades, Enn. III.3.2 | 1,433 |
| `passage_plotinus_iii_3_3` | Plotinus, Enneades, Enn. III.3.3 | 1,161 |
| `passage_plotinus_iii_3_4` | Plotinus, Enneades, Enn. III.3.4 | 1,431 |
| `passage_plotinus_iii_3_5` | Plotinus, Enneades, Enn. III.3.5 | 1,390 |
| `passage_plotinus_iii_3_6` | Plotinus, Enneades, Enn. III.3.6 | 900 |
| `passage_plotinus_iii_3_7` | Plotinus, Enneades, Enn. III.3.7 | 1,297 |
| `passage_plotinus_iii_4_1` | Plotinus, Enneades, Enn. III.4.1 | 1,359 |
| `passage_plotinus_iii_4_2` | Plotinus, Enneades, Enn. III.4.2 | 1,392 |
| `passage_plotinus_iii_4_3` | Plotinus, Enneades, Enn. III.4.3 | 1,405 |
| `passage_plotinus_iii_4_4` | Plotinus, Enneades, Enn. III.4.4 | 1,383 |
| `passage_plotinus_iii_4_5` | Plotinus, Enneades, Enn. III.4.5 | 1,390 |
| `passage_plotinus_iii_4_6` | Plotinus, Enneades, Enn. III.4.6 | 1,154 |
| `passage_plotinus_iii_5_1` | Plotinus, Enneades, Enn. III.5.1 | 1,279 |
| `passage_plotinus_iii_5_2` | Plotinus, Enneades, Enn. III.5.2 | 1,327 |
| `passage_plotinus_iii_5_3` | Plotinus, Enneades, Enn. III.5.3 | 1,404 |
| `passage_plotinus_iii_5_4` | Plotinus, Enneades, Enn. III.5.4 | 1,355 |
| `passage_plotinus_iii_5_5` | Plotinus, Enneades, Enn. III.5.5 | 1,072 |
| `passage_plotinus_iii_5_6` | Plotinus, Enneades, Enn. III.5.6 | 1,451 |
| `passage_plotinus_iii_5_7` | Plotinus, Enneades, Enn. III.5.7 | 994 |
| `passage_plotinus_iii_5_8` | Plotinus, Enneades, Enn. III.5.8 | 1,428 |
| `passage_plotinus_iii_5_9` | Plotinus, Enneades, Enn. III.5.9 | 1,336 |
| `passage_plotinus_iii_6_1` | Plotinus, Enneades, Enn. III.6.1 | 1,440 |
| `passage_plotinus_iii_6_10` | Plotinus, Enneades, Enn. III.6.10 | 1,397 |
| `passage_plotinus_iii_6_11` | Plotinus, Enneades, Enn. III.6.11 | 1,148 |
| `passage_plotinus_iii_6_12` | Plotinus, Enneades, Enn. III.6.12 | 1,072 |
| `passage_plotinus_iii_6_13` | Plotinus, Enneades, Enn. III.6.13 | 1,492 |
| `passage_plotinus_iii_6_14` | Plotinus, Enneades, Enn. III.6.14 | 1,397 |
| `passage_plotinus_iii_6_15` | Plotinus, Enneades, Enn. III.6.15 | 1,457 |
| `passage_plotinus_iii_6_16` | Plotinus, Enneades, Enn. III.6.16 | 1,379 |
| `passage_plotinus_iii_6_17` | Plotinus, Enneades, Enn. III.6.17 | 1,335 |
| `passage_plotinus_iii_6_18` | Plotinus, Enneades, Enn. III.6.18 | 709 |
| `passage_plotinus_iii_6_19` | Plotinus, Enneades, Enn. III.6.19 | 1,451 |
| `passage_plotinus_iii_6_2` | Plotinus, Enneades, Enn. III.6.2 | 1,496 |
| `passage_plotinus_iii_6_3` | Plotinus, Enneades, Enn. III.6.3 | 1,257 |
| `passage_plotinus_iii_6_4` | Plotinus, Enneades, Enn. III.6.4 | 1,287 |
| `passage_plotinus_iii_6_5` | Plotinus, Enneades, Enn. III.6.5 | 1,055 |
| `passage_plotinus_iii_6_6` | Plotinus, Enneades, Enn. III.6.6 | 1,302 |
| `passage_plotinus_iii_6_7` | Plotinus, Enneades, Enn. III.6.7 | 1,209 |
| `passage_plotinus_iii_6_8` | Plotinus, Enneades, Enn. III.6.8 | 1,486 |
| `passage_plotinus_iii_6_9` | Plotinus, Enneades, Enn. III.6.9 | 1,397 |
| `passage_plotinus_iii_7_1` | Plotinus, Enneades, Enn. III.7.1 | 806 |
| `passage_plotinus_iii_7_10` | Plotinus, Enneades, Enn. III.7.10 | 1,440 |
| `passage_plotinus_iii_7_11` | Plotinus, Enneades, Enn. III.7.11 | 1,446 |
| `passage_plotinus_iii_7_12` | Plotinus, Enneades, Enn. III.7.12 | 1,310 |
| `passage_plotinus_iii_7_13` | Plotinus, Enneades, Enn. III.7.13 | 507 |
| `passage_plotinus_iii_7_2` | Plotinus, Enneades, Enn. III.7.2 | 1,461 |
| `passage_plotinus_iii_7_3` | Plotinus, Enneades, Enn. III.7.3 | 1,440 |
| `passage_plotinus_iii_7_4` | Plotinus, Enneades, Enn. III.7.4 | 1,332 |
| `passage_plotinus_iii_7_5` | Plotinus, Enneades, Enn. III.7.5 | 1,162 |
| `passage_plotinus_iii_7_6` | Plotinus, Enneades, Enn. III.7.6 | 1,420 |
| `passage_plotinus_iii_7_7` | Plotinus, Enneades, Enn. III.7.7 | 1,197 |
| `passage_plotinus_iii_7_8` | Plotinus, Enneades, Enn. III.7.8 | 1,474 |
| `passage_plotinus_iii_7_9` | Plotinus, Enneades, Enn. III.7.9 | 1,155 |
| `passage_plotinus_iii_8_1` | Plotinus, Enneades, Enn. III.8.1 | 1,700 |
| `passage_plotinus_iii_8_10` | Plotinus, Enneades, Enn. III.8.10 | 1,405 |
| `passage_plotinus_iii_8_11` | Plotinus, Enneades, Enn. III.8.11 | 1,027 |
| `passage_plotinus_iii_8_2` | Plotinus, Enneades, Enn. III.8.2 | 1,330 |
| `passage_plotinus_iii_8_3` | Plotinus, Enneades, Enn. III.8.3 | 1,396 |
| `passage_plotinus_iii_8_4` | Plotinus, Enneades, Enn. III.8.4 | 1,125 |
| `passage_plotinus_iii_8_5` | Plotinus, Enneades, Enn. III.8.5 | 1,176 |
| `passage_plotinus_iii_8_6` | Plotinus, Enneades, Enn. III.8.6 | 725 |
| `passage_plotinus_iii_8_7` | Plotinus, Enneades, Enn. III.8.7 | 1,461 |
| `passage_plotinus_iii_8_8` | Plotinus, Enneades, Enn. III.8.8 | 1,447 |
| `passage_plotinus_iii_8_9` | Plotinus, Enneades, Enn. III.8.9 | 1,327 |
| `passage_plotinus_iii_9_1` | Plotinus, Enneades, Enn. III.9.1 | 480 |
| `passage_plotinus_iii_9_2` | Plotinus, Enneades, Enn. III.9.2 | 1,208 |
| `passage_plotinus_iii_9_3` | Plotinus, Enneades, Enn. III.9.3 | 1,189 |
| `passage_plotinus_iii_9_4` | Plotinus, Enneades, Enn. III.9.4 | 1,277 |
| `passage_plotinus_iii_9_5` | Plotinus, Enneades, Enn. III.9.5 | 1,401 |
| `passage_plotinus_iii_9_6` | Plotinus, Enneades, Enn. III.9.6 | 832 |
| `passage_plotinus_iii_9_7` | Plotinus, Enneades, Enn. III.9.7 | 1,408 |
| `passage_plotinus_iii_9_8` | Plotinus, Enneades, Enn. III.9.8 | 1,087 |
| `passage_plotinus_iii_9_9` | Plotinus, Enneades, Enn. III.9.9 | 1,169 |
| `passage_plotinus_iv_1_1` | Plotinus, Enneades, Enn. IV.1.1 | 1,323 |
| `passage_plotinus_iv_2_1` | Plotinus, Enneades, Enn. IV.2.1 | 1,132 |
| `passage_plotinus_iv_2_2` | Plotinus, Enneades, Enn. IV.2.2 | 1,471 |
| `passage_plotinus_iv_3_1` | Plotinus, Enneades, Enn. IV.3.1 | 1,490 |
| `passage_plotinus_iv_3_10` | Plotinus, Enneades, Enn. IV.3.10 | 1,395 |
| `passage_plotinus_iv_3_11` | Plotinus, Enneades, Enn. IV.3.11 | 963 |
| `passage_plotinus_iv_3_12` | Plotinus, Enneades, Enn. IV.3.12 | 1,301 |
| `passage_plotinus_iv_3_13` | Plotinus, Enneades, Enn. IV.3.13 | 1,061 |
| `passage_plotinus_iv_3_14` | Plotinus, Enneades, Enn. IV.3.14 | 1,124 |
| `passage_plotinus_iv_3_15` | Plotinus, Enneades, Enn. IV.3.15 | 1,117 |
| `passage_plotinus_iv_3_16` | Plotinus, Enneades, Enn. IV.3.16 | 1,167 |
| `passage_plotinus_iv_3_17` | Plotinus, Enneades, Enn. IV.3.17 | 1,075 |
| `passage_plotinus_iv_3_18` | Plotinus, Enneades, Enn. IV.3.18 | 1,448 |
| `passage_plotinus_iv_3_19` | Plotinus, Enneades, Enn. IV.3.19 | 1,470 |
| `passage_plotinus_iv_3_2` | Plotinus, Enneades, Enn. IV.3.2 | 1,377 |
| `passage_plotinus_iv_3_20` | Plotinus, Enneades, Enn. IV.3.20 | 1,282 |
| `passage_plotinus_iv_3_21` | Plotinus, Enneades, Enn. IV.3.21 | 1,410 |
| `passage_plotinus_iv_3_22` | Plotinus, Enneades, Enn. IV.3.22 | 1,431 |
| `passage_plotinus_iv_3_23` | Plotinus, Enneades, Enn. IV.3.23 | 1,486 |
| `passage_plotinus_iv_3_24` | Plotinus, Enneades, Enn. IV.3.24 | 920 |
| `passage_plotinus_iv_3_25` | Plotinus, Enneades, Enn. IV.3.25 | 1,346 |
| `passage_plotinus_iv_3_26` | Plotinus, Enneades, Enn. IV.3.26 | 821 |
| `passage_plotinus_iv_3_27` | Plotinus, Enneades, Enn. IV.3.27 | 1,290 |
| `passage_plotinus_iv_3_28` | Plotinus, Enneades, Enn. IV.3.28 | 1,465 |
| `passage_plotinus_iv_3_29` | Plotinus, Enneades, Enn. IV.3.29 | 1,407 |
| `passage_plotinus_iv_3_3` | Plotinus, Enneades, Enn. IV.3.3 | 1,341 |
| `passage_plotinus_iv_3_30` | Plotinus, Enneades, Enn. IV.3.30 | 1,450 |
| `passage_plotinus_iv_3_31` | Plotinus, Enneades, Enn. IV.3.31 | 1,424 |
| `passage_plotinus_iv_3_32` | Plotinus, Enneades, Enn. IV.3.32 | 1,265 |
| `passage_plotinus_iv_3_4` | Plotinus, Enneades, Enn. IV.3.4 | 982 |
| `passage_plotinus_iv_3_5` | Plotinus, Enneades, Enn. IV.3.5 | 1,402 |
| `passage_plotinus_iv_3_6` | Plotinus, Enneades, Enn. IV.3.6 | 1,365 |
| `passage_plotinus_iv_3_7` | Plotinus, Enneades, Enn. IV.3.7 | 1,329 |
| `passage_plotinus_iv_3_8` | Plotinus, Enneades, Enn. IV.3.8 | 1,336 |
| `passage_plotinus_iv_3_9` | Plotinus, Enneades, Enn. IV.3.9 | 1,176 |
| `passage_plotinus_iv_4_1` | Plotinus, Enneades, Enn. IV.4.1 | 1,223 |
| `passage_plotinus_iv_4_10` | Plotinus, Enneades, Enn. IV.4.10 | 1,380 |
| `passage_plotinus_iv_4_11` | Plotinus, Enneades, Enn. IV.4.11 | 1,437 |
| `passage_plotinus_iv_4_12` | Plotinus, Enneades, Enn. IV.4.12 | 1,361 |
| `passage_plotinus_iv_4_13` | Plotinus, Enneades, Enn. IV.4.13 | 1,200 |
| `passage_plotinus_iv_4_14` | Plotinus, Enneades, Enn. IV.4.14 | 1,298 |
| `passage_plotinus_iv_4_15` | Plotinus, Enneades, Enn. IV.4.15 | 1,243 |
| `passage_plotinus_iv_4_16` | Plotinus, Enneades, Enn. IV.4.16 | 1,429 |
| `passage_plotinus_iv_4_17` | Plotinus, Enneades, Enn. IV.4.17 | 1,483 |
| `passage_plotinus_iv_4_18` | Plotinus, Enneades, Enn. IV.4.18 | 1,405 |
| `passage_plotinus_iv_4_19` | Plotinus, Enneades, Enn. IV.4.19 | 854 |
| `passage_plotinus_iv_4_2` | Plotinus, Enneades, Enn. IV.4.2 | 1,341 |
| `passage_plotinus_iv_4_20` | Plotinus, Enneades, Enn. IV.4.20 | 1,124 |
| `passage_plotinus_iv_4_21` | Plotinus, Enneades, Enn. IV.4.21 | 1,065 |
| `passage_plotinus_iv_4_22` | Plotinus, Enneades, Enn. IV.4.22 | 1,240 |
| `passage_plotinus_iv_4_23` | Plotinus, Enneades, Enn. IV.4.23 | 1,068 |
| `passage_plotinus_iv_4_24` | Plotinus, Enneades, Enn. IV.4.24 | 1,259 |
| `passage_plotinus_iv_4_25` | Plotinus, Enneades, Enn. IV.4.25 | 1,480 |
| `passage_plotinus_iv_4_26` | Plotinus, Enneades, Enn. IV.4.26 | 804 |
| `passage_plotinus_iv_4_27` | Plotinus, Enneades, Enn. IV.4.27 | 761 |
| `passage_plotinus_iv_4_28` | Plotinus, Enneades, Enn. IV.4.28 | 1,413 |
| `passage_plotinus_iv_4_29` | Plotinus, Enneades, Enn. IV.4.29 | 1,390 |
| `passage_plotinus_iv_4_3` | Plotinus, Enneades, Enn. IV.4.3 | 1,482 |
| `passage_plotinus_iv_4_30` | Plotinus, Enneades, Enn. IV.4.30 | 1,384 |
| `passage_plotinus_iv_4_31` | Plotinus, Enneades, Enn. IV.4.31 | 897 |
| `passage_plotinus_iv_4_32` | Plotinus, Enneades, Enn. IV.4.32 | 1,301 |
| `passage_plotinus_iv_4_33` | Plotinus, Enneades, Enn. IV.4.33 | 1,144 |
| `passage_plotinus_iv_4_34` | Plotinus, Enneades, Enn. IV.4.34 | 1,414 |
| `passage_plotinus_iv_4_35` | Plotinus, Enneades, Enn. IV.4.35 | 1,450 |
| `passage_plotinus_iv_4_36` | Plotinus, Enneades, Enn. IV.4.36 | 1,316 |
| `passage_plotinus_iv_4_37` | Plotinus, Enneades, Enn. IV.4.37 | 1,201 |
| `passage_plotinus_iv_4_38` | Plotinus, Enneades, Enn. IV.4.38 | 1,489 |
| `passage_plotinus_iv_4_39` | Plotinus, Enneades, Enn. IV.4.39 | 1,154 |
| `passage_plotinus_iv_4_4` | Plotinus, Enneades, Enn. IV.4.4 | 1,090 |
| `passage_plotinus_iv_4_40` | Plotinus, Enneades, Enn. IV.4.40 | 1,339 |
| `passage_plotinus_iv_4_41` | Plotinus, Enneades, Enn. IV.4.41 | 996 |
| `passage_plotinus_iv_4_42` | Plotinus, Enneades, Enn. IV.4.42 | 1,317 |
| `passage_plotinus_iv_4_43` | Plotinus, Enneades, Enn. IV.4.43 | 1,214 |
| `passage_plotinus_iv_4_44` | Plotinus, Enneades, Enn. IV.4.44 | 924 |
| `passage_plotinus_iv_4_45` | Plotinus, Enneades, Enn. IV.4.45 | 1,051 |
| `passage_plotinus_iv_4_5` | Plotinus, Enneades, Enn. IV.4.5 | 1,139 |
| `passage_plotinus_iv_4_6` | Plotinus, Enneades, Enn. IV.4.6 | 380 |
| `passage_plotinus_iv_4_7` | Plotinus, Enneades, Enn. IV.4.7 | 1,328 |
| `passage_plotinus_iv_4_8` | Plotinus, Enneades, Enn. IV.4.8 | 1,425 |
| `passage_plotinus_iv_4_9` | Plotinus, Enneades, Enn. IV.4.9 | 654 |
| `passage_plotinus_iv_5_1` | Plotinus, Enneades, Enn. IV.5.1 | 994 |
| `passage_plotinus_iv_5_2` | Plotinus, Enneades, Enn. IV.5.2 | 804 |
| `passage_plotinus_iv_5_3` | Plotinus, Enneades, Enn. IV.5.3 | 804 |
| `passage_plotinus_iv_5_4` | Plotinus, Enneades, Enn. IV.5.4 | 1,494 |
| `passage_plotinus_iv_5_5` | Plotinus, Enneades, Enn. IV.5.5 | 1,095 |
| `passage_plotinus_iv_5_6` | Plotinus, Enneades, Enn. IV.5.6 | 1,345 |
| `passage_plotinus_iv_5_7` | Plotinus, Enneades, Enn. IV.5.7 | 969 |
| `passage_plotinus_iv_5_8` | Plotinus, Enneades, Enn. IV.5.8 | 1,060 |
| `passage_plotinus_iv_6_1` | Plotinus, Enneades, Enn. IV.6.1 | 878 |
| `passage_plotinus_iv_6_2` | Plotinus, Enneades, Enn. IV.6.2 | 1,392 |
| `passage_plotinus_iv_6_3` | Plotinus, Enneades, Enn. IV.6.3 | 1,314 |
| `passage_plotinus_iv_7_1` | Plotinus, Enneades, Enn. IV.7.1 | 1,497 |
| `passage_plotinus_iv_7_10` | Plotinus, Enneades, Enn. IV.7.10 | 1,451 |
| `passage_plotinus_iv_7_11` | Plotinus, Enneades, Enn. IV.7.11 | 1,469 |
| `passage_plotinus_iv_7_12` | Plotinus, Enneades, Enn. IV.7.12 | 1,239 |
| `passage_plotinus_iv_7_13` | Plotinus, Enneades, Enn. IV.7.13 | 1,320 |
| `passage_plotinus_iv_7_14` | Plotinus, Enneades, Enn. IV.7.14 | 1,181 |
| `passage_plotinus_iv_7_15` | Plotinus, Enneades, Enn. IV.7.15 | 1,458 |
| `passage_plotinus_iv_7_2` | Plotinus, Enneades, Enn. IV.7.2 | 1,381 |
| `passage_plotinus_iv_7_3` | Plotinus, Enneades, Enn. IV.7.3 | 1,347 |
| `passage_plotinus_iv_7_4` | Plotinus, Enneades, Enn. IV.7.4 | 1,476 |
| `passage_plotinus_iv_7_5` | Plotinus, Enneades, Enn. IV.7.5 | 1,001 |
| `passage_plotinus_iv_7_6` | Plotinus, Enneades, Enn. IV.7.6 | 1,445 |
| `passage_plotinus_iv_7_7` | Plotinus, Enneades, Enn. IV.7.7 | 1,435 |
| `passage_plotinus_iv_7_8` | Plotinus, Enneades, Enn. IV.7.8 | 1,014 |
| `passage_plotinus_iv_7_9` | Plotinus, Enneades, Enn. IV.7.9 | 1,479 |
| `passage_plotinus_iv_8_1` | Plotinus, Enneades, Enn. IV.8.1 | 1,211 |
| `passage_plotinus_iv_8_2` | Plotinus, Enneades, Enn. IV.8.2 | 1,340 |
| `passage_plotinus_iv_8_3` | Plotinus, Enneades, Enn. IV.8.3 | 1,245 |
| `passage_plotinus_iv_8_4` | Plotinus, Enneades, Enn. IV.8.4 | 1,375 |
| `passage_plotinus_iv_8_5` | Plotinus, Enneades, Enn. IV.8.5 | 1,083 |
| `passage_plotinus_iv_8_6` | Plotinus, Enneades, Enn. IV.8.6 | 1,495 |
| `passage_plotinus_iv_8_7` | Plotinus, Enneades, Enn. IV.8.7 | 1,316 |
| `passage_plotinus_iv_8_8` | Plotinus, Enneades, Enn. IV.8.8 | 1,469 |
| `passage_plotinus_iv_9_1` | Plotinus, Enneades, Enn. IV.9.1 | 1,403 |
| `passage_plotinus_iv_9_2` | Plotinus, Enneades, Enn. IV.9.2 | 1,285 |
| `passage_plotinus_iv_9_3` | Plotinus, Enneades, Enn. IV.9.3 | 1,382 |
| `passage_plotinus_iv_9_4` | Plotinus, Enneades, Enn. IV.9.4 | 1,494 |
| `passage_plotinus_iv_9_5` | Plotinus, Enneades, Enn. IV.9.5 | 1,224 |
| `passage_plotinus_v_1_1` | Plotinus, Enneades, Enn. V.1.1 | 1,225 |
| `passage_plotinus_v_1_10` | Plotinus, Enneades, Enn. V.1.10 | 1,220 |
| `passage_plotinus_v_1_11` | Plotinus, Enneades, Enn. V.1.11 | 1,368 |
| `passage_plotinus_v_1_12` | Plotinus, Enneades, Enn. V.1.12 | 1,475 |
| `passage_plotinus_v_1_2` | Plotinus, Enneades, Enn. V.1.2 | 1,304 |
| `passage_plotinus_v_1_3` | Plotinus, Enneades, Enn. V.1.3 | 1,354 |
| `passage_plotinus_v_1_4` | Plotinus, Enneades, Enn. V.1.4 | 1,321 |
| `passage_plotinus_v_1_5` | Plotinus, Enneades, Enn. V.1.5 | 1,348 |
| `passage_plotinus_v_1_6` | Plotinus, Enneades, Enn. V.1.6 | 1,393 |
| `passage_plotinus_v_1_7` | Plotinus, Enneades, Enn. V.1.7 | 1,415 |
| `passage_plotinus_v_1_8` | Plotinus, Enneades, Enn. V.1.8 | 1,340 |
| `passage_plotinus_v_1_9` | Plotinus, Enneades, Enn. V.1.9 | 1,177 |
| `passage_plotinus_v_2_1` | Plotinus, Enneades, Enn. V.2.1 | 1,371 |
| `passage_plotinus_v_2_2` | Plotinus, Enneades, Enn. V.2.2 | 1,432 |
| `passage_plotinus_v_3_1` | Plotinus, Enneades, Enn. V.3.1 | 1,476 |
| `passage_plotinus_v_3_10` | Plotinus, Enneades, Enn. V.3.10 | 1,347 |
| `passage_plotinus_v_3_11` | Plotinus, Enneades, Enn. V.3.11 | 1,372 |
| `passage_plotinus_v_3_12` | Plotinus, Enneades, Enn. V.3.12 | 664 |
| `passage_plotinus_v_3_13` | Plotinus, Enneades, Enn. V.3.13 | 1,364 |
| `passage_plotinus_v_3_14` | Plotinus, Enneades, Enn. V.3.14 | 1,476 |
| `passage_plotinus_v_3_15` | Plotinus, Enneades, Enn. V.3.15 | 1,045 |
| `passage_plotinus_v_3_16` | Plotinus, Enneades, Enn. V.3.16 | 1,430 |
| `passage_plotinus_v_3_17` | Plotinus, Enneades, Enn. V.3.17 | 646 |
| `passage_plotinus_v_3_2` | Plotinus, Enneades, Enn. V.3.2 | 1,075 |
| `passage_plotinus_v_3_3` | Plotinus, Enneades, Enn. V.3.3 | 866 |
| `passage_plotinus_v_3_4` | Plotinus, Enneades, Enn. V.3.4 | 1,477 |
| `passage_plotinus_v_3_5` | Plotinus, Enneades, Enn. V.3.5 | 1,343 |
| `passage_plotinus_v_3_6` | Plotinus, Enneades, Enn. V.3.6 | 1,466 |
| `passage_plotinus_v_3_7` | Plotinus, Enneades, Enn. V.3.7 | 1,328 |
| `passage_plotinus_v_3_8` | Plotinus, Enneades, Enn. V.3.8 | 1,232 |
| `passage_plotinus_v_3_9` | Plotinus, Enneades, Enn. V.3.9 | 1,287 |
| `passage_plotinus_v_4_1` | Plotinus, Enneades, Enn. V.4.1 | 1,491 |
| `passage_plotinus_v_4_2` | Plotinus, Enneades, Enn. V.4.2 | 1,130 |
| `passage_plotinus_v_5_1` | Plotinus, Enneades, Enn. V.5.1 | 1,084 |
| `passage_plotinus_v_5_10` | Plotinus, Enneades, Enn. V.5.10 | 1,417 |
| `passage_plotinus_v_5_11` | Plotinus, Enneades, Enn. V.5.11 | 739 |
| `passage_plotinus_v_5_12` | Plotinus, Enneades, Enn. V.5.12 | 1,150 |
| `passage_plotinus_v_5_13` | Plotinus, Enneades, Enn. V.5.13 | 1,282 |
| `passage_plotinus_v_5_2` | Plotinus, Enneades, Enn. V.5.2 | 998 |
| `passage_plotinus_v_5_3` | Plotinus, Enneades, Enn. V.5.3 | 1,274 |
| `passage_plotinus_v_5_4` | Plotinus, Enneades, Enn. V.5.4 | 1,089 |
| `passage_plotinus_v_5_5` | Plotinus, Enneades, Enn. V.5.5 | 1,400 |
| `passage_plotinus_v_5_6` | Plotinus, Enneades, Enn. V.5.6 | 1,470 |
| `passage_plotinus_v_5_7` | Plotinus, Enneades, Enn. V.5.7 | 1,299 |
| `passage_plotinus_v_5_8` | Plotinus, Enneades, Enn. V.5.8 | 1,386 |
| `passage_plotinus_v_5_9` | Plotinus, Enneades, Enn. V.5.9 | 1,346 |
| `passage_plotinus_v_6_1` | Plotinus, Enneades, Enn. V.6.1 | 1,108 |
| `passage_plotinus_v_6_2` | Plotinus, Enneades, Enn. V.6.2 | 1,332 |
| `passage_plotinus_v_6_3` | Plotinus, Enneades, Enn. V.6.3 | 1,458 |
| `passage_plotinus_v_6_4` | Plotinus, Enneades, Enn. V.6.4 | 1,280 |
| `passage_plotinus_v_6_5` | Plotinus, Enneades, Enn. V.6.5 | 1,275 |
| `passage_plotinus_v_6_6` | Plotinus, Enneades, Enn. V.6.6 | 1,445 |
| `passage_plotinus_v_7_1` | Plotinus, Enneades, Enn. V.7.1 | 1,388 |
| `passage_plotinus_v_7_2` | Plotinus, Enneades, Enn. V.7.2 | 1,342 |
| `passage_plotinus_v_7_3` | Plotinus, Enneades, Enn. V.7.3 | 1,465 |
| `passage_plotinus_v_8_1` | Plotinus, Enneades, Enn. V.8.1 | 1,428 |
| `passage_plotinus_v_8_10` | Plotinus, Enneades, Enn. V.8.10 | 1,403 |
| `passage_plotinus_v_8_11` | Plotinus, Enneades, Enn. V.8.11 | 1,408 |
| `passage_plotinus_v_8_12` | Plotinus, Enneades, Enn. V.8.12 | 1,287 |
| `passage_plotinus_v_8_13` | Plotinus, Enneades, Enn. V.8.13 | 795 |
| `passage_plotinus_v_8_2` | Plotinus, Enneades, Enn. V.8.2 | 1,192 |
| `passage_plotinus_v_8_3` | Plotinus, Enneades, Enn. V.8.3 | 1,351 |
| `passage_plotinus_v_8_4` | Plotinus, Enneades, Enn. V.8.4 | 1,484 |
| `passage_plotinus_v_8_5` | Plotinus, Enneades, Enn. V.8.5 | 1,424 |
| `passage_plotinus_v_8_6` | Plotinus, Enneades, Enn. V.8.6 | 1,280 |
| `passage_plotinus_v_8_7` | Plotinus, Enneades, Enn. V.8.7 | 1,265 |
| `passage_plotinus_v_8_8` | Plotinus, Enneades, Enn. V.8.8 | 945 |
| `passage_plotinus_v_8_9` | Plotinus, Enneades, Enn. V.8.9 | 1,333 |
| `passage_plotinus_v_9_1` | Plotinus, Enneades, Enn. V.9.1 | 1,399 |
| `passage_plotinus_v_9_10` | Plotinus, Enneades, Enn. V.9.10 | 1,341 |
| `passage_plotinus_v_9_11` | Plotinus, Enneades, Enn. V.9.11 | 1,343 |
| `passage_plotinus_v_9_12` | Plotinus, Enneades, Enn. V.9.12 | 1,437 |
| `passage_plotinus_v_9_13` | Plotinus, Enneades, Enn. V.9.13 | 1,269 |
| `passage_plotinus_v_9_14` | Plotinus, Enneades, Enn. V.9.14 | 1,285 |
| `passage_plotinus_v_9_2` | Plotinus, Enneades, Enn. V.9.2 | 1,291 |
| `passage_plotinus_v_9_3` | Plotinus, Enneades, Enn. V.9.3 | 1,305 |
| `passage_plotinus_v_9_4` | Plotinus, Enneades, Enn. V.9.4 | 1,096 |
| `passage_plotinus_v_9_5` | Plotinus, Enneades, Enn. V.9.5 | 939 |
| `passage_plotinus_v_9_6` | Plotinus, Enneades, Enn. V.9.6 | 1,486 |
| `passage_plotinus_v_9_7` | Plotinus, Enneades, Enn. V.9.7 | 1,485 |
| `passage_plotinus_v_9_8` | Plotinus, Enneades, Enn. V.9.8 | 1,431 |
| `passage_plotinus_v_9_9` | Plotinus, Enneades, Enn. V.9.9 | 1,350 |
| `passage_plotinus_vi_1_1` | Plotinus, Enneades, Enn. VI.1.1 | 1,389 |
| `passage_plotinus_vi_1_10` | Plotinus, Enneades, Enn. VI.1.10 | 646 |
| `passage_plotinus_vi_1_11` | Plotinus, Enneades, Enn. VI.1.11 | 1,277 |
| `passage_plotinus_vi_1_12` | Plotinus, Enneades, Enn. VI.1.12 | 1,455 |
| `passage_plotinus_vi_1_13` | Plotinus, Enneades, Enn. VI.1.13 | 1,327 |
| `passage_plotinus_vi_1_14` | Plotinus, Enneades, Enn. VI.1.14 | 1,300 |
| `passage_plotinus_vi_1_15` | Plotinus, Enneades, Enn. VI.1.15 | 976 |
| `passage_plotinus_vi_1_16` | Plotinus, Enneades, Enn. VI.1.16 | 1,332 |
| `passage_plotinus_vi_1_17` | Plotinus, Enneades, Enn. VI.1.17 | 928 |
| `passage_plotinus_vi_1_18` | Plotinus, Enneades, Enn. VI.1.18 | 1,463 |
| `passage_plotinus_vi_1_19` | Plotinus, Enneades, Enn. VI.1.19 | 1,475 |
| `passage_plotinus_vi_1_2` | Plotinus, Enneades, Enn. VI.1.2 | 1,363 |
| `passage_plotinus_vi_1_20` | Plotinus, Enneades, Enn. VI.1.20 | 1,483 |
| `passage_plotinus_vi_1_21` | Plotinus, Enneades, Enn. VI.1.21 | 1,093 |
| `passage_plotinus_vi_1_22` | Plotinus, Enneades, Enn. VI.1.22 | 1,283 |
| `passage_plotinus_vi_1_23` | Plotinus, Enneades, Enn. VI.1.23 | 1,405 |
| `passage_plotinus_vi_1_24` | Plotinus, Enneades, Enn. VI.1.24 | 1,279 |
| `passage_plotinus_vi_1_25` | Plotinus, Enneades, Enn. VI.1.25 | 1,376 |
| `passage_plotinus_vi_1_26` | Plotinus, Enneades, Enn. VI.1.26 | 1,372 |
| `passage_plotinus_vi_1_27` | Plotinus, Enneades, Enn. VI.1.27 | 1,300 |
| `passage_plotinus_vi_1_28` | Plotinus, Enneades, Enn. VI.1.28 | 1,223 |
| `passage_plotinus_vi_1_29` | Plotinus, Enneades, Enn. VI.1.29 | 1,355 |
| `passage_plotinus_vi_1_3` | Plotinus, Enneades, Enn. VI.1.3 | 1,203 |
| `passage_plotinus_vi_1_30` | Plotinus, Enneades, Enn. VI.1.30 | 1,496 |
| `passage_plotinus_vi_1_4` | Plotinus, Enneades, Enn. VI.1.4 | 1,476 |
| `passage_plotinus_vi_1_5` | Plotinus, Enneades, Enn. VI.1.5 | 1,042 |
| `passage_plotinus_vi_1_6` | Plotinus, Enneades, Enn. VI.1.6 | 1,481 |
| `passage_plotinus_vi_1_7` | Plotinus, Enneades, Enn. VI.1.7 | 1,412 |
| `passage_plotinus_vi_1_8` | Plotinus, Enneades, Enn. VI.1.8 | 1,110 |
| `passage_plotinus_vi_1_9` | Plotinus, Enneades, Enn. VI.1.9 | 1,136 |
| `passage_plotinus_vi_2_1` | Plotinus, Enneades, Enn. VI.2.1 | 1,105 |
| `passage_plotinus_vi_2_10` | Plotinus, Enneades, Enn. VI.2.10 | 1,443 |
| `passage_plotinus_vi_2_11` | Plotinus, Enneades, Enn. VI.2.11 | 1,431 |
| `passage_plotinus_vi_2_12` | Plotinus, Enneades, Enn. VI.2.12 | 1,174 |
| `passage_plotinus_vi_2_13` | Plotinus, Enneades, Enn. VI.2.13 | 973 |
| `passage_plotinus_vi_2_14` | Plotinus, Enneades, Enn. VI.2.14 | 1,113 |
| `passage_plotinus_vi_2_15` | Plotinus, Enneades, Enn. VI.2.15 | 940 |
| `passage_plotinus_vi_2_16` | Plotinus, Enneades, Enn. VI.2.16 | 1,364 |
| `passage_plotinus_vi_2_17` | Plotinus, Enneades, Enn. VI.2.17 | 1,413 |
| `passage_plotinus_vi_2_18` | Plotinus, Enneades, Enn. VI.2.18 | 1,316 |
| `passage_plotinus_vi_2_19` | Plotinus, Enneades, Enn. VI.2.19 | 1,441 |
| `passage_plotinus_vi_2_2` | Plotinus, Enneades, Enn. VI.2.2 | 1,350 |
| `passage_plotinus_vi_2_20` | Plotinus, Enneades, Enn. VI.2.20 | 1,464 |
| `passage_plotinus_vi_2_21` | Plotinus, Enneades, Enn. VI.2.21 | 1,379 |
| `passage_plotinus_vi_2_22` | Plotinus, Enneades, Enn. VI.2.22 | 1,477 |
| `passage_plotinus_vi_2_3` | Plotinus, Enneades, Enn. VI.2.3 | 1,420 |
| `passage_plotinus_vi_2_4` | Plotinus, Enneades, Enn. VI.2.4 | 1,290 |
| `passage_plotinus_vi_2_5` | Plotinus, Enneades, Enn. VI.2.5 | 1,473 |
| `passage_plotinus_vi_2_6` | Plotinus, Enneades, Enn. VI.2.6 | 1,281 |
| `passage_plotinus_vi_2_7` | Plotinus, Enneades, Enn. VI.2.7 | 1,359 |
| `passage_plotinus_vi_2_8` | Plotinus, Enneades, Enn. VI.2.8 | 1,475 |
| `passage_plotinus_vi_2_9` | Plotinus, Enneades, Enn. VI.2.9 | 1,418 |
| `passage_plotinus_vi_3_1` | Plotinus, Enneades, Enn. VI.3.1 | 974 |
| `passage_plotinus_vi_3_10` | Plotinus, Enneades, Enn. VI.3.10 | 1,405 |
| `passage_plotinus_vi_3_11` | Plotinus, Enneades, Enn. VI.3.11 | 1,394 |
| `passage_plotinus_vi_3_12` | Plotinus, Enneades, Enn. VI.3.12 | 1,104 |
| `passage_plotinus_vi_3_13` | Plotinus, Enneades, Enn. VI.3.13 | 1,098 |
| `passage_plotinus_vi_3_14` | Plotinus, Enneades, Enn. VI.3.14 | 999 |
| `passage_plotinus_vi_3_15` | Plotinus, Enneades, Enn. VI.3.15 | 1,305 |
| `passage_plotinus_vi_3_16` | Plotinus, Enneades, Enn. VI.3.16 | 524 |
| `passage_plotinus_vi_3_17` | Plotinus, Enneades, Enn. VI.3.17 | 2,327 |
| `passage_plotinus_vi_3_18` | Plotinus, Enneades, Enn. VI.3.18 | 1,388 |
| `passage_plotinus_vi_3_19` | Plotinus, Enneades, Enn. VI.3.19 | 1,490 |
| `passage_plotinus_vi_3_2` | Plotinus, Enneades, Enn. VI.3.2 | 975 |
| `passage_plotinus_vi_3_20` | Plotinus, Enneades, Enn. VI.3.20 | 1,392 |
| `passage_plotinus_vi_3_21` | Plotinus, Enneades, Enn. VI.3.21 | 1,428 |
| `passage_plotinus_vi_3_22` | Plotinus, Enneades, Enn. VI.3.22 | 1,321 |
| `passage_plotinus_vi_3_23` | Plotinus, Enneades, Enn. VI.3.23 | 1,087 |
| `passage_plotinus_vi_3_24` | Plotinus, Enneades, Enn. VI.3.24 | 1,112 |
| `passage_plotinus_vi_3_25` | Plotinus, Enneades, Enn. VI.3.25 | 1,213 |
| `passage_plotinus_vi_3_26` | Plotinus, Enneades, Enn. VI.3.26 | 1,336 |
| `passage_plotinus_vi_3_27` | Plotinus, Enneades, Enn. VI.3.27 | 1,327 |
| `passage_plotinus_vi_3_3` | Plotinus, Enneades, Enn. VI.3.3 | 1,226 |
| `passage_plotinus_vi_3_4` | Plotinus, Enneades, Enn. VI.3.4 | 1,489 |
| `passage_plotinus_vi_3_5` | Plotinus, Enneades, Enn. VI.3.5 | 988 |
| `passage_plotinus_vi_3_6` | Plotinus, Enneades, Enn. VI.3.6 | 1,307 |
| `passage_plotinus_vi_3_7` | Plotinus, Enneades, Enn. VI.3.7 | 1,390 |
| `passage_plotinus_vi_3_8` | Plotinus, Enneades, Enn. VI.3.8 | 1,406 |
| `passage_plotinus_vi_3_9` | Plotinus, Enneades, Enn. VI.3.9 | 1,350 |
| `passage_plotinus_vi_4_1` | Plotinus, Enneades, Enn. VI.4.1 | 1,350 |
| `passage_plotinus_vi_4_10` | Plotinus, Enneades, Enn. VI.4.10 | 1,269 |
| `passage_plotinus_vi_4_11` | Plotinus, Enneades, Enn. VI.4.11 | 1,314 |
| `passage_plotinus_vi_4_12` | Plotinus, Enneades, Enn. VI.4.12 | 1,158 |
| `passage_plotinus_vi_4_13` | Plotinus, Enneades, Enn. VI.4.13 | 1,454 |
| `passage_plotinus_vi_4_14` | Plotinus, Enneades, Enn. VI.4.14 | 1,448 |
| `passage_plotinus_vi_4_15` | Plotinus, Enneades, Enn. VI.4.15 | 1,194 |
| `passage_plotinus_vi_4_16` | Plotinus, Enneades, Enn. VI.4.16 | 1,424 |
| `passage_plotinus_vi_4_2` | Plotinus, Enneades, Enn. VI.4.2 | 1,294 |
| `passage_plotinus_vi_4_3` | Plotinus, Enneades, Enn. VI.4.3 | 1,486 |
| `passage_plotinus_vi_4_4` | Plotinus, Enneades, Enn. VI.4.4 | 1,304 |
| `passage_plotinus_vi_4_5` | Plotinus, Enneades, Enn. VI.4.5 | 1,496 |
| `passage_plotinus_vi_4_6` | Plotinus, Enneades, Enn. VI.4.6 | 1,396 |
| `passage_plotinus_vi_4_7` | Plotinus, Enneades, Enn. VI.4.7 | 1,333 |
| `passage_plotinus_vi_4_8` | Plotinus, Enneades, Enn. VI.4.8 | 326 |
| `passage_plotinus_vi_4_9` | Plotinus, Enneades, Enn. VI.4.9 | 1,277 |
| `passage_plotinus_vi_5_1` | Plotinus, Enneades, Enn. VI.5.1 | 1,163 |
| `passage_plotinus_vi_5_10` | Plotinus, Enneades, Enn. VI.5.10 | 1,413 |
| `passage_plotinus_vi_5_11` | Plotinus, Enneades, Enn. VI.5.11 | 1,464 |
| `passage_plotinus_vi_5_12` | Plotinus, Enneades, Enn. VI.5.12 | 1,452 |
| `passage_plotinus_vi_5_2` | Plotinus, Enneades, Enn. VI.5.2 | 1,392 |
| `passage_plotinus_vi_5_3` | Plotinus, Enneades, Enn. VI.5.3 | 1,340 |
| `passage_plotinus_vi_5_4` | Plotinus, Enneades, Enn. VI.5.4 | 1,436 |
| `passage_plotinus_vi_5_5` | Plotinus, Enneades, Enn. VI.5.5 | 1,357 |
| `passage_plotinus_vi_5_6` | Plotinus, Enneades, Enn. VI.5.6 | 906 |
| `passage_plotinus_vi_5_7` | Plotinus, Enneades, Enn. VI.5.7 | 1,090 |
| `passage_plotinus_vi_5_8` | Plotinus, Enneades, Enn. VI.5.8 | 1,438 |
| `passage_plotinus_vi_5_9` | Plotinus, Enneades, Enn. VI.5.9 | 1,038 |
| `passage_plotinus_vi_6_1` | Plotinus, Enneades, Enn. VI.6.1 | 1,379 |
| `passage_plotinus_vi_6_10` | Plotinus, Enneades, Enn. VI.6.10 | 1,417 |
| `passage_plotinus_vi_6_11` | Plotinus, Enneades, Enn. VI.6.11 | 1,283 |
| `passage_plotinus_vi_6_12` | Plotinus, Enneades, Enn. VI.6.12 | 1,345 |
| `passage_plotinus_vi_6_13` | Plotinus, Enneades, Enn. VI.6.13 | 1,381 |
| `passage_plotinus_vi_6_14` | Plotinus, Enneades, Enn. VI.6.14 | 1,484 |
| `passage_plotinus_vi_6_15` | Plotinus, Enneades, Enn. VI.6.15 | 1,081 |
| `passage_plotinus_vi_6_16` | Plotinus, Enneades, Enn. VI.6.16 | 1,464 |
| `passage_plotinus_vi_6_17` | Plotinus, Enneades, Enn. VI.6.17 | 1,234 |
| `passage_plotinus_vi_6_18` | Plotinus, Enneades, Enn. VI.6.18 | 1,341 |
| `passage_plotinus_vi_6_2` | Plotinus, Enneades, Enn. VI.6.2 | 1,327 |
| `passage_plotinus_vi_6_3` | Plotinus, Enneades, Enn. VI.6.3 | 1,470 |
| `passage_plotinus_vi_6_4` | Plotinus, Enneades, Enn. VI.6.4 | 1,252 |
| `passage_plotinus_vi_6_5` | Plotinus, Enneades, Enn. VI.6.5 | 1,223 |
| `passage_plotinus_vi_6_6` | Plotinus, Enneades, Enn. VI.6.6 | 1,373 |
| `passage_plotinus_vi_6_7` | Plotinus, Enneades, Enn. VI.6.7 | 1,458 |
| `passage_plotinus_vi_6_8` | Plotinus, Enneades, Enn. VI.6.8 | 1,376 |
| `passage_plotinus_vi_6_9` | Plotinus, Enneades, Enn. VI.6.9 | 1,252 |
| `passage_plotinus_vi_7_1` | Plotinus, Enneades, Enn. VI.7.1 | 1,420 |
| `passage_plotinus_vi_7_10` | Plotinus, Enneades, Enn. VI.7.10 | 1,448 |
| `passage_plotinus_vi_7_11` | Plotinus, Enneades, Enn. VI.7.11 | 1,076 |
| `passage_plotinus_vi_7_12` | Plotinus, Enneades, Enn. VI.7.12 | 655 |
| `passage_plotinus_vi_7_13` | Plotinus, Enneades, Enn. VI.7.13 | 1,465 |
| `passage_plotinus_vi_7_14` | Plotinus, Enneades, Enn. VI.7.14 | 1,398 |
| `passage_plotinus_vi_7_15` | Plotinus, Enneades, Enn. VI.7.15 | 1,359 |
| `passage_plotinus_vi_7_16` | Plotinus, Enneades, Enn. VI.7.16 | 1,266 |
| `passage_plotinus_vi_7_17` | Plotinus, Enneades, Enn. VI.7.17 | 1,492 |
| `passage_plotinus_vi_7_18` | Plotinus, Enneades, Enn. VI.7.18 | 1,350 |
| `passage_plotinus_vi_7_19` | Plotinus, Enneades, Enn. VI.7.19 | 1,460 |
| `passage_plotinus_vi_7_2` | Plotinus, Enneades, Enn. VI.7.2 | 1,443 |
| `passage_plotinus_vi_7_20` | Plotinus, Enneades, Enn. VI.7.20 | 1,392 |
| `passage_plotinus_vi_7_21` | Plotinus, Enneades, Enn. VI.7.21 | 1,413 |
| `passage_plotinus_vi_7_22` | Plotinus, Enneades, Enn. VI.7.22 | 1,185 |
| `passage_plotinus_vi_7_23` | Plotinus, Enneades, Enn. VI.7.23 | 1,496 |
| `passage_plotinus_vi_7_24` | Plotinus, Enneades, Enn. VI.7.24 | 1,460 |
| `passage_plotinus_vi_7_25` | Plotinus, Enneades, Enn. VI.7.25 | 1,456 |
| `passage_plotinus_vi_7_26` | Plotinus, Enneades, Enn. VI.7.26 | 1,401 |
| `passage_plotinus_vi_7_27` | Plotinus, Enneades, Enn. VI.7.27 | 1,485 |
| `passage_plotinus_vi_7_28` | Plotinus, Enneades, Enn. VI.7.28 | 1,450 |
| `passage_plotinus_vi_7_29` | Plotinus, Enneades, Enn. VI.7.29 | 808 |
| `passage_plotinus_vi_7_3` | Plotinus, Enneades, Enn. VI.7.3 | 1,440 |
| `passage_plotinus_vi_7_30` | Plotinus, Enneades, Enn. VI.7.30 | 1,399 |
| `passage_plotinus_vi_7_31` | Plotinus, Enneades, Enn. VI.7.31 | 1,340 |
| `passage_plotinus_vi_7_32` | Plotinus, Enneades, Enn. VI.7.32 | 1,194 |
| `passage_plotinus_vi_7_33` | Plotinus, Enneades, Enn. VI.7.33 | 1,499 |
| `passage_plotinus_vi_7_34` | Plotinus, Enneades, Enn. VI.7.34 | 1,452 |
| `passage_plotinus_vi_7_35` | Plotinus, Enneades, Enn. VI.7.35 | 1,391 |
| `passage_plotinus_vi_7_36` | Plotinus, Enneades, Enn. VI.7.36 | 1,148 |
| `passage_plotinus_vi_7_37` | Plotinus, Enneades, Enn. VI.7.37 | 1,086 |
| `passage_plotinus_vi_7_38` | Plotinus, Enneades, Enn. VI.7.38 | 1,068 |
| `passage_plotinus_vi_7_39` | Plotinus, Enneades, Enn. VI.7.39 | 1,489 |
| `passage_plotinus_vi_7_4` | Plotinus, Enneades, Enn. VI.7.4 | 1,351 |
| `passage_plotinus_vi_7_40` | Plotinus, Enneades, Enn. VI.7.40 | 1,493 |
| `passage_plotinus_vi_7_41` | Plotinus, Enneades, Enn. VI.7.41 | 1,097 |
| `passage_plotinus_vi_7_42` | Plotinus, Enneades, Enn. VI.7.42 | 1,353 |
| `passage_plotinus_vi_7_5` | Plotinus, Enneades, Enn. VI.7.5 | 1,473 |
| `passage_plotinus_vi_7_6` | Plotinus, Enneades, Enn. VI.7.6 | 1,104 |
| `passage_plotinus_vi_7_7` | Plotinus, Enneades, Enn. VI.7.7 | 1,204 |
| `passage_plotinus_vi_7_8` | Plotinus, Enneades, Enn. VI.7.8 | 1,432 |
| `passage_plotinus_vi_7_9` | Plotinus, Enneades, Enn. VI.7.9 | 1,364 |
| `passage_plotinus_vi_8_1` | Plotinus, Enneades, Enn. VI.8.1 | 1,481 |
| `passage_plotinus_vi_8_10` | Plotinus, Enneades, Enn. VI.8.10 | 1,411 |
| `passage_plotinus_vi_8_11` | Plotinus, Enneades, Enn. VI.8.11 | 1,194 |
| `passage_plotinus_vi_8_12` | Plotinus, Enneades, Enn. VI.8.12 | 1,062 |
| `passage_plotinus_vi_8_13` | Plotinus, Enneades, Enn. VI.8.13 | 852 |
| `passage_plotinus_vi_8_14` | Plotinus, Enneades, Enn. VI.8.14 | 1,387 |
| `passage_plotinus_vi_8_15` | Plotinus, Enneades, Enn. VI.8.15 | 1,243 |
| `passage_plotinus_vi_8_16` | Plotinus, Enneades, Enn. VI.8.16 | 1,152 |
| `passage_plotinus_vi_8_17` | Plotinus, Enneades, Enn. VI.8.17 | 990 |
| `passage_plotinus_vi_8_18` | Plotinus, Enneades, Enn. VI.8.18 | 678 |
| `passage_plotinus_vi_8_19` | Plotinus, Enneades, Enn. VI.8.19 | 1,254 |
| `passage_plotinus_vi_8_2` | Plotinus, Enneades, Enn. VI.8.2 | 1,319 |
| `passage_plotinus_vi_8_20` | Plotinus, Enneades, Enn. VI.8.20 | 701 |
| `passage_plotinus_vi_8_21` | Plotinus, Enneades, Enn. VI.8.21 | 1,238 |
| `passage_plotinus_vi_8_3` | Plotinus, Enneades, Enn. VI.8.3 | 1,444 |
| `passage_plotinus_vi_8_4` | Plotinus, Enneades, Enn. VI.8.4 | 1,614 |
| `passage_plotinus_vi_8_5` | Plotinus, Enneades, Enn. VI.8.5 | 1,461 |
| `passage_plotinus_vi_8_6` | Plotinus, Enneades, Enn. VI.8.6 | 1,370 |
| `passage_plotinus_vi_8_7` | Plotinus, Enneades, Enn. VI.8.7 | 1,434 |
| `passage_plotinus_vi_8_8` | Plotinus, Enneades, Enn. VI.8.8 | 1,291 |
| `passage_plotinus_vi_8_9` | Plotinus, Enneades, Enn. VI.8.9 | 1,486 |
| `passage_plotinus_vi_9_1` | Plotinus, Enneades, Enn. VI.9.1 | 1,490 |
| `passage_plotinus_vi_9_10` | Plotinus, Enneades, Enn. VI.9.10 | 1,471 |
| `passage_plotinus_vi_9_100` | Plotinus, Enneades, Enn. VI.9.100 | 899 |
| `passage_plotinus_vi_9_101` | Plotinus, Enneades, Enn. VI.9.101 | 1,454 |
| `passage_plotinus_vi_9_102` | Plotinus, Enneades, Enn. VI.9.102 | 1,480 |
| `passage_plotinus_vi_9_103` | Plotinus, Enneades, Enn. VI.9.103 | 1,259 |
| `passage_plotinus_vi_9_104` | Plotinus, Enneades, Enn. VI.9.104 | 1,074 |
| `passage_plotinus_vi_9_105` | Plotinus, Enneades, Enn. VI.9.105 | 1,332 |
| `passage_plotinus_vi_9_106` | Plotinus, Enneades, Enn. VI.9.106 | 838 |
| `passage_plotinus_vi_9_107` | Plotinus, Enneades, Enn. VI.9.107 | 1,266 |
| `passage_plotinus_vi_9_108` | Plotinus, Enneades, Enn. VI.9.108 | 1,164 |
| `passage_plotinus_vi_9_109` | Plotinus, Enneades, Enn. VI.9.109 | 1,182 |
| `passage_plotinus_vi_9_11` | Plotinus, Enneades, Enn. VI.9.11 | 1,349 |
| `passage_plotinus_vi_9_110` | Plotinus, Enneades, Enn. VI.9.110 | 1,434 |
| `passage_plotinus_vi_9_111` | Plotinus, Enneades, Enn. VI.9.111 | 1,476 |
| `passage_plotinus_vi_9_112` | Plotinus, Enneades, Enn. VI.9.112 | 1,244 |
| `passage_plotinus_vi_9_113` | Plotinus, Enneades, Enn. VI.9.113 | 1,393 |
| `passage_plotinus_vi_9_114` | Plotinus, Enneades, Enn. VI.9.114 | 1,487 |
| `passage_plotinus_vi_9_115` | Plotinus, Enneades, Enn. VI.9.115 | 1,083 |
| `passage_plotinus_vi_9_116` | Plotinus, Enneades, Enn. VI.9.116 | 1,332 |
| `passage_plotinus_vi_9_117` | Plotinus, Enneades, Enn. VI.9.117 | 1,257 |
| `passage_plotinus_vi_9_118` | Plotinus, Enneades, Enn. VI.9.118 | 1,291 |
| `passage_plotinus_vi_9_119` | Plotinus, Enneades, Enn. VI.9.119 | 1,116 |
| `passage_plotinus_vi_9_12` | Plotinus, Enneades, Enn. VI.9.12 | 1,411 |
| `passage_plotinus_vi_9_120` | Plotinus, Enneades, Enn. VI.9.120 | 1,494 |
| `passage_plotinus_vi_9_121` | Plotinus, Enneades, Enn. VI.9.121 | 1,392 |
| `passage_plotinus_vi_9_122` | Plotinus, Enneades, Enn. VI.9.122 | 1,176 |
| `passage_plotinus_vi_9_123` | Plotinus, Enneades, Enn. VI.9.123 | 1,488 |
| `passage_plotinus_vi_9_124` | Plotinus, Enneades, Enn. VI.9.124 | 1,113 |
| `passage_plotinus_vi_9_125` | Plotinus, Enneades, Enn. VI.9.125 | 1,427 |
| `passage_plotinus_vi_9_126` | Plotinus, Enneades, Enn. VI.9.126 | 1,462 |
| `passage_plotinus_vi_9_127` | Plotinus, Enneades, Enn. VI.9.127 | 1,455 |
| `passage_plotinus_vi_9_128` | Plotinus, Enneades, Enn. VI.9.128 | 1,444 |
| `passage_plotinus_vi_9_129` | Plotinus, Enneades, Enn. VI.9.129 | 1,232 |
| `passage_plotinus_vi_9_13` | Plotinus, Enneades, Enn. VI.9.13 | 903 |
| `passage_plotinus_vi_9_130` | Plotinus, Enneades, Enn. VI.9.130 | 1,126 |
| `passage_plotinus_vi_9_131` | Plotinus, Enneades, Enn. VI.9.131 | 1,489 |
| `passage_plotinus_vi_9_132` | Plotinus, Enneades, Enn. VI.9.132 | 1,243 |
| `passage_plotinus_vi_9_133` | Plotinus, Enneades, Enn. VI.9.133 | 1,287 |
| `passage_plotinus_vi_9_134` | Plotinus, Enneades, Enn. VI.9.134 | 1,388 |
| `passage_plotinus_vi_9_135` | Plotinus, Enneades, Enn. VI.9.135 | 1,499 |
| `passage_plotinus_vi_9_136` | Plotinus, Enneades, Enn. VI.9.136 | 1,129 |
| `passage_plotinus_vi_9_137` | Plotinus, Enneades, Enn. VI.9.137 | 1,359 |
| `passage_plotinus_vi_9_138` | Plotinus, Enneades, Enn. VI.9.138 | 1,479 |
| `passage_plotinus_vi_9_139` | Plotinus, Enneades, Enn. VI.9.139 | 1,159 |
| `passage_plotinus_vi_9_14` | Plotinus, Enneades, Enn. VI.9.14 | 1,354 |
| `passage_plotinus_vi_9_140` | Plotinus, Enneades, Enn. VI.9.140 | 1,455 |
| `passage_plotinus_vi_9_141` | Plotinus, Enneades, Enn. VI.9.141 | 1,198 |
| `passage_plotinus_vi_9_142` | Plotinus, Enneades, Enn. VI.9.142 | 1,462 |
| `passage_plotinus_vi_9_143` | Plotinus, Enneades, Enn. VI.9.143 | 1,326 |
| `passage_plotinus_vi_9_144` | Plotinus, Enneades, Enn. VI.9.144 | 1,263 |
| `passage_plotinus_vi_9_145` | Plotinus, Enneades, Enn. VI.9.145 | 1,375 |
| `passage_plotinus_vi_9_146` | Plotinus, Enneades, Enn. VI.9.146 | 1,378 |
| `passage_plotinus_vi_9_147` | Plotinus, Enneades, Enn. VI.9.147 | 1,439 |
| `passage_plotinus_vi_9_148` | Plotinus, Enneades, Enn. VI.9.148 | 1,321 |
| `passage_plotinus_vi_9_149` | Plotinus, Enneades, Enn. VI.9.149 | 1,335 |
| `passage_plotinus_vi_9_15` | Plotinus, Enneades, Enn. VI.9.15 | 1,445 |
| `passage_plotinus_vi_9_150` | Plotinus, Enneades, Enn. VI.9.150 | 1,468 |
| `passage_plotinus_vi_9_151` | Plotinus, Enneades, Enn. VI.9.151 | 804 |
| `passage_plotinus_vi_9_152` | Plotinus, Enneades, Enn. VI.9.152 | 1,428 |
| `passage_plotinus_vi_9_153` | Plotinus, Enneades, Enn. VI.9.153 | 1,462 |
| `passage_plotinus_vi_9_154` | Plotinus, Enneades, Enn. VI.9.154 | 828 |
| `passage_plotinus_vi_9_155` | Plotinus, Enneades, Enn. VI.9.155 | 1,455 |
| `passage_plotinus_vi_9_156` | Plotinus, Enneades, Enn. VI.9.156 | 1,332 |
| `passage_plotinus_vi_9_157` | Plotinus, Enneades, Enn. VI.9.157 | 1,405 |
| `passage_plotinus_vi_9_158` | Plotinus, Enneades, Enn. VI.9.158 | 1,102 |
| `passage_plotinus_vi_9_159` | Plotinus, Enneades, Enn. VI.9.159 | 1,354 |
| `passage_plotinus_vi_9_16` | Plotinus, Enneades, Enn. VI.9.16 | 1,452 |
| `passage_plotinus_vi_9_160` | Plotinus, Enneades, Enn. VI.9.160 | 1,277 |
| `passage_plotinus_vi_9_161` | Plotinus, Enneades, Enn. VI.9.161 | 1,328 |
| `passage_plotinus_vi_9_162` | Plotinus, Enneades, Enn. VI.9.162 | 918 |
| `passage_plotinus_vi_9_163` | Plotinus, Enneades, Enn. VI.9.163 | 1,574 |
| `passage_plotinus_vi_9_164` | Plotinus, Enneades, Enn. VI.9.164 | 1,379 |
| `passage_plotinus_vi_9_165` | Plotinus, Enneades, Enn. VI.9.165 | 1,425 |
| `passage_plotinus_vi_9_166` | Plotinus, Enneades, Enn. VI.9.166 | 1,335 |
| `passage_plotinus_vi_9_167` | Plotinus, Enneades, Enn. VI.9.167 | 1,287 |
| `passage_plotinus_vi_9_168` | Plotinus, Enneades, Enn. VI.9.168 | 1,451 |
| `passage_plotinus_vi_9_169` | Plotinus, Enneades, Enn. VI.9.169 | 1,374 |
| `passage_plotinus_vi_9_17` | Plotinus, Enneades, Enn. VI.9.17 | 1,282 |
| `passage_plotinus_vi_9_170` | Plotinus, Enneades, Enn. VI.9.170 | 1,428 |
| `passage_plotinus_vi_9_171` | Plotinus, Enneades, Enn. VI.9.171 | 1,084 |
| `passage_plotinus_vi_9_172` | Plotinus, Enneades, Enn. VI.9.172 | 1,444 |
| `passage_plotinus_vi_9_173` | Plotinus, Enneades, Enn. VI.9.173 | 1,165 |
| `passage_plotinus_vi_9_174` | Plotinus, Enneades, Enn. VI.9.174 | 1,200 |
| `passage_plotinus_vi_9_175` | Plotinus, Enneades, Enn. VI.9.175 | 1,378 |
| `passage_plotinus_vi_9_176` | Plotinus, Enneades, Enn. VI.9.176 | 819 |
| `passage_plotinus_vi_9_177` | Plotinus, Enneades, Enn. VI.9.177 | 927 |
| `passage_plotinus_vi_9_178` | Plotinus, Enneades, Enn. VI.9.178 | 1,314 |
| `passage_plotinus_vi_9_179` | Plotinus, Enneades, Enn. VI.9.179 | 1,434 |
| `passage_plotinus_vi_9_18` | Plotinus, Enneades, Enn. VI.9.18 | 1,245 |
| `passage_plotinus_vi_9_180` | Plotinus, Enneades, Enn. VI.9.180 | 1,405 |
| `passage_plotinus_vi_9_181` | Plotinus, Enneades, Enn. VI.9.181 | 1,429 |
| `passage_plotinus_vi_9_182` | Plotinus, Enneades, Enn. VI.9.182 | 1,338 |
| `passage_plotinus_vi_9_183` | Plotinus, Enneades, Enn. VI.9.183 | 1,083 |
| `passage_plotinus_vi_9_184` | Plotinus, Enneades, Enn. VI.9.184 | 1,432 |
| `passage_plotinus_vi_9_185` | Plotinus, Enneades, Enn. VI.9.185 | 1,412 |
| `passage_plotinus_vi_9_186` | Plotinus, Enneades, Enn. VI.9.186 | 1,324 |
| `passage_plotinus_vi_9_187` | Plotinus, Enneades, Enn. VI.9.187 | 1,500 |
| `passage_plotinus_vi_9_188` | Plotinus, Enneades, Enn. VI.9.188 | 1,111 |
| `passage_plotinus_vi_9_189` | Plotinus, Enneades, Enn. VI.9.189 | 1,407 |
| `passage_plotinus_vi_9_19` | Plotinus, Enneades, Enn. VI.9.19 | 1,484 |
| `passage_plotinus_vi_9_190` | Plotinus, Enneades, Enn. VI.9.190 | 1,104 |
| `passage_plotinus_vi_9_191` | Plotinus, Enneades, Enn. VI.9.191 | 1,493 |
| `passage_plotinus_vi_9_192` | Plotinus, Enneades, Enn. VI.9.192 | 1,282 |
| `passage_plotinus_vi_9_193` | Plotinus, Enneades, Enn. VI.9.193 | 1,429 |
| `passage_plotinus_vi_9_194` | Plotinus, Enneades, Enn. VI.9.194 | 1,411 |
| `passage_plotinus_vi_9_195` | Plotinus, Enneades, Enn. VI.9.195 | 1,405 |
| `passage_plotinus_vi_9_196` | Plotinus, Enneades, Enn. VI.9.196 | 1,435 |
| `passage_plotinus_vi_9_197` | Plotinus, Enneades, Enn. VI.9.197 | 1,216 |
| `passage_plotinus_vi_9_198` | Plotinus, Enneades, Enn. VI.9.198 | 1,345 |
| `passage_plotinus_vi_9_199` | Plotinus, Enneades, Enn. VI.9.199 | 1,464 |
| `passage_plotinus_vi_9_2` | Plotinus, Enneades, Enn. VI.9.2 | 1,389 |
| `passage_plotinus_vi_9_20` | Plotinus, Enneades, Enn. VI.9.20 | 1,496 |
| `passage_plotinus_vi_9_200` | Plotinus, Enneades, Enn. VI.9.200 | 1,404 |
| `passage_plotinus_vi_9_201` | Plotinus, Enneades, Enn. VI.9.201 | 1,458 |
| `passage_plotinus_vi_9_202` | Plotinus, Enneades, Enn. VI.9.202 | 1,092 |
| `passage_plotinus_vi_9_203` | Plotinus, Enneades, Enn. VI.9.203 | 1,221 |
| `passage_plotinus_vi_9_204` | Plotinus, Enneades, Enn. VI.9.204 | 1,427 |
| `passage_plotinus_vi_9_205` | Plotinus, Enneades, Enn. VI.9.205 | 1,500 |
| `passage_plotinus_vi_9_206` | Plotinus, Enneades, Enn. VI.9.206 | 1,210 |
| `passage_plotinus_vi_9_207` | Plotinus, Enneades, Enn. VI.9.207 | 1,314 |
| `passage_plotinus_vi_9_208` | Plotinus, Enneades, Enn. VI.9.208 | 1,201 |
| `passage_plotinus_vi_9_209` | Plotinus, Enneades, Enn. VI.9.209 | 1,422 |
| `passage_plotinus_vi_9_21` | Plotinus, Enneades, Enn. VI.9.21 | 1,287 |
| `passage_plotinus_vi_9_210` | Plotinus, Enneades, Enn. VI.9.210 | 919 |
| `passage_plotinus_vi_9_211` | Plotinus, Enneades, Enn. VI.9.211 | 1,491 |
| `passage_plotinus_vi_9_212` | Plotinus, Enneades, Enn. VI.9.212 | 1,487 |
| `passage_plotinus_vi_9_213` | Plotinus, Enneades, Enn. VI.9.213 | 1,030 |
| `passage_plotinus_vi_9_214` | Plotinus, Enneades, Enn. VI.9.214 | 1,441 |
| `passage_plotinus_vi_9_215` | Plotinus, Enneades, Enn. VI.9.215 | 1,491 |
| `passage_plotinus_vi_9_216` | Plotinus, Enneades, Enn. VI.9.216 | 1,498 |
| `passage_plotinus_vi_9_217` | Plotinus, Enneades, Enn. VI.9.217 | 1,387 |
| `passage_plotinus_vi_9_218` | Plotinus, Enneades, Enn. VI.9.218 | 1,423 |
| `passage_plotinus_vi_9_219` | Plotinus, Enneades, Enn. VI.9.219 | 1,482 |
| `passage_plotinus_vi_9_22` | Plotinus, Enneades, Enn. VI.9.22 | 1,073 |
| `passage_plotinus_vi_9_220` | Plotinus, Enneades, Enn. VI.9.220 | 1,416 |
| `passage_plotinus_vi_9_221` | Plotinus, Enneades, Enn. VI.9.221 | 1,425 |
| `passage_plotinus_vi_9_222` | Plotinus, Enneades, Enn. VI.9.222 | 1,500 |
| `passage_plotinus_vi_9_223` | Plotinus, Enneades, Enn. VI.9.223 | 1,410 |
| `passage_plotinus_vi_9_224` | Plotinus, Enneades, Enn. VI.9.224 | 1,498 |
| `passage_plotinus_vi_9_225` | Plotinus, Enneades, Enn. VI.9.225 | 1,345 |
| `passage_plotinus_vi_9_226` | Plotinus, Enneades, Enn. VI.9.226 | 1,293 |
| `passage_plotinus_vi_9_227` | Plotinus, Enneades, Enn. VI.9.227 | 1,348 |
| `passage_plotinus_vi_9_228` | Plotinus, Enneades, Enn. VI.9.228 | 1,278 |
| `passage_plotinus_vi_9_229` | Plotinus, Enneades, Enn. VI.9.229 | 1,274 |
| `passage_plotinus_vi_9_23` | Plotinus, Enneades, Enn. VI.9.23 | 1,314 |
| `passage_plotinus_vi_9_230` | Plotinus, Enneades, Enn. VI.9.230 | 1,231 |
| `passage_plotinus_vi_9_231` | Plotinus, Enneades, Enn. VI.9.231 | 946 |
| `passage_plotinus_vi_9_232` | Plotinus, Enneades, Enn. VI.9.232 | 1,341 |
| `passage_plotinus_vi_9_233` | Plotinus, Enneades, Enn. VI.9.233 | 1,395 |
| `passage_plotinus_vi_9_234` | Plotinus, Enneades, Enn. VI.9.234 | 1,116 |
| `passage_plotinus_vi_9_235` | Plotinus, Enneades, Enn. VI.9.235 | 1,244 |
| `passage_plotinus_vi_9_236` | Plotinus, Enneades, Enn. VI.9.236 | 1,144 |
| `passage_plotinus_vi_9_237` | Plotinus, Enneades, Enn. VI.9.237 | 1,156 |
| `passage_plotinus_vi_9_238` | Plotinus, Enneades, Enn. VI.9.238 | 1,455 |
| `passage_plotinus_vi_9_239` | Plotinus, Enneades, Enn. VI.9.239 | 1,412 |
| `passage_plotinus_vi_9_24` | Plotinus, Enneades, Enn. VI.9.24 | 1,390 |
| `passage_plotinus_vi_9_240` | Plotinus, Enneades, Enn. VI.9.240 | 1,332 |
| `passage_plotinus_vi_9_241` | Plotinus, Enneades, Enn. VI.9.241 | 1,385 |
| `passage_plotinus_vi_9_242` | Plotinus, Enneades, Enn. VI.9.242 | 1,410 |
| `passage_plotinus_vi_9_243` | Plotinus, Enneades, Enn. VI.9.243 | 1,346 |
| `passage_plotinus_vi_9_244` | Plotinus, Enneades, Enn. VI.9.244 | 1,264 |
| `passage_plotinus_vi_9_245` | Plotinus, Enneades, Enn. VI.9.245 | 1,442 |
| `passage_plotinus_vi_9_246` | Plotinus, Enneades, Enn. VI.9.246 | 1,418 |
| `passage_plotinus_vi_9_247` | Plotinus, Enneades, Enn. VI.9.247 | 1,366 |
| `passage_plotinus_vi_9_248` | Plotinus, Enneades, Enn. VI.9.248 | 1,134 |
| `passage_plotinus_vi_9_249` | Plotinus, Enneades, Enn. VI.9.249 | 1,112 |
| `passage_plotinus_vi_9_25` | Plotinus, Enneades, Enn. VI.9.25 | 1,340 |
| `passage_plotinus_vi_9_250` | Plotinus, Enneades, Enn. VI.9.250 | 993 |
| `passage_plotinus_vi_9_251` | Plotinus, Enneades, Enn. VI.9.251 | 1,332 |
| `passage_plotinus_vi_9_252` | Plotinus, Enneades, Enn. VI.9.252 | 1,332 |
| `passage_plotinus_vi_9_253` | Plotinus, Enneades, Enn. VI.9.253 | 1,421 |
| `passage_plotinus_vi_9_254` | Plotinus, Enneades, Enn. VI.9.254 | 1,303 |
| `passage_plotinus_vi_9_255` | Plotinus, Enneades, Enn. VI.9.255 | 1,356 |
| `passage_plotinus_vi_9_256` | Plotinus, Enneades, Enn. VI.9.256 | 1,110 |
| `passage_plotinus_vi_9_257` | Plotinus, Enneades, Enn. VI.9.257 | 1,303 |
| `passage_plotinus_vi_9_258` | Plotinus, Enneades, Enn. VI.9.258 | 1,185 |
| `passage_plotinus_vi_9_259` | Plotinus, Enneades, Enn. VI.9.259 | 1,453 |
| `passage_plotinus_vi_9_26` | Plotinus, Enneades, Enn. VI.9.26 | 1,335 |
| `passage_plotinus_vi_9_260` | Plotinus, Enneades, Enn. VI.9.260 | 1,324 |
| `passage_plotinus_vi_9_261` | Plotinus, Enneades, Enn. VI.9.261 | 1,067 |
| `passage_plotinus_vi_9_262` | Plotinus, Enneades, Enn. VI.9.262 | 1,499 |
| `passage_plotinus_vi_9_263` | Plotinus, Enneades, Enn. VI.9.263 | 1,456 |
| `passage_plotinus_vi_9_264` | Plotinus, Enneades, Enn. VI.9.264 | 1,479 |
| `passage_plotinus_vi_9_265` | Plotinus, Enneades, Enn. VI.9.265 | 1,230 |
| `passage_plotinus_vi_9_266` | Plotinus, Enneades, Enn. VI.9.266 | 1,242 |
| `passage_plotinus_vi_9_267` | Plotinus, Enneades, Enn. VI.9.267 | 1,044 |
| `passage_plotinus_vi_9_268` | Plotinus, Enneades, Enn. VI.9.268 | 1,474 |
| `passage_plotinus_vi_9_269` | Plotinus, Enneades, Enn. VI.9.269 | 1,435 |
| `passage_plotinus_vi_9_27` | Plotinus, Enneades, Enn. VI.9.27 | 1,006 |
| `passage_plotinus_vi_9_270` | Plotinus, Enneades, Enn. VI.9.270 | 1,460 |
| `passage_plotinus_vi_9_271` | Plotinus, Enneades, Enn. VI.9.271 | 1,398 |
| `passage_plotinus_vi_9_272` | Plotinus, Enneades, Enn. VI.9.272 | 1,214 |
| `passage_plotinus_vi_9_273` | Plotinus, Enneades, Enn. VI.9.273 | 1,150 |
| `passage_plotinus_vi_9_274` | Plotinus, Enneades, Enn. VI.9.274 | 1,425 |
| `passage_plotinus_vi_9_275` | Plotinus, Enneades, Enn. VI.9.275 | 1,221 |
| `passage_plotinus_vi_9_276` | Plotinus, Enneades, Enn. VI.9.276 | 1,089 |
| `passage_plotinus_vi_9_277` | Plotinus, Enneades, Enn. VI.9.277 | 1,349 |
| `passage_plotinus_vi_9_278` | Plotinus, Enneades, Enn. VI.9.278 | 1,353 |
| `passage_plotinus_vi_9_279` | Plotinus, Enneades, Enn. VI.9.279 | 1,408 |
| `passage_plotinus_vi_9_28` | Plotinus, Enneades, Enn. VI.9.28 | 1,398 |
| `passage_plotinus_vi_9_280` | Plotinus, Enneades, Enn. VI.9.280 | 1,386 |
| `passage_plotinus_vi_9_281` | Plotinus, Enneades, Enn. VI.9.281 | 1,377 |
| `passage_plotinus_vi_9_282` | Plotinus, Enneades, Enn. VI.9.282 | 1,480 |
| `passage_plotinus_vi_9_283` | Plotinus, Enneades, Enn. VI.9.283 | 1,438 |
| `passage_plotinus_vi_9_284` | Plotinus, Enneades, Enn. VI.9.284 | 1,471 |
| `passage_plotinus_vi_9_285` | Plotinus, Enneades, Enn. VI.9.285 | 1,305 |
| `passage_plotinus_vi_9_286` | Plotinus, Enneades, Enn. VI.9.286 | 1,489 |
| `passage_plotinus_vi_9_287` | Plotinus, Enneades, Enn. VI.9.287 | 379 |
| `passage_plotinus_vi_9_288` | Plotinus, Enneades, Enn. VI.9.288 | 1,853 |
| `passage_plotinus_vi_9_289` | Plotinus, Enneades, Enn. VI.9.289 | 1,382 |
| `passage_plotinus_vi_9_29` | Plotinus, Enneades, Enn. VI.9.29 | 1,090 |
| `passage_plotinus_vi_9_290` | Plotinus, Enneades, Enn. VI.9.290 | 1,246 |
| `passage_plotinus_vi_9_291` | Plotinus, Enneades, Enn. VI.9.291 | 1,061 |
| `passage_plotinus_vi_9_292` | Plotinus, Enneades, Enn. VI.9.292 | 1,421 |
| `passage_plotinus_vi_9_293` | Plotinus, Enneades, Enn. VI.9.293 | 1,411 |
| `passage_plotinus_vi_9_294` | Plotinus, Enneades, Enn. VI.9.294 | 1,168 |
| `passage_plotinus_vi_9_295` | Plotinus, Enneades, Enn. VI.9.295 | 1,201 |
| `passage_plotinus_vi_9_296` | Plotinus, Enneades, Enn. VI.9.296 | 1,428 |
| `passage_plotinus_vi_9_297` | Plotinus, Enneades, Enn. VI.9.297 | 1,384 |
| `passage_plotinus_vi_9_298` | Plotinus, Enneades, Enn. VI.9.298 | 1,122 |
| `passage_plotinus_vi_9_299` | Plotinus, Enneades, Enn. VI.9.299 | 1,446 |
| `passage_plotinus_vi_9_3` | Plotinus, Enneades, Enn. VI.9.3 | 168 |
| `passage_plotinus_vi_9_30` | Plotinus, Enneades, Enn. VI.9.30 | 1,014 |
| `passage_plotinus_vi_9_300` | Plotinus, Enneades, Enn. VI.9.300 | 1,195 |
| `passage_plotinus_vi_9_301` | Plotinus, Enneades, Enn. VI.9.301 | 1,494 |
| `passage_plotinus_vi_9_302` | Plotinus, Enneades, Enn. VI.9.302 | 1,308 |
| `passage_plotinus_vi_9_303` | Plotinus, Enneades, Enn. VI.9.303 | 1,353 |
| `passage_plotinus_vi_9_304` | Plotinus, Enneades, Enn. VI.9.304 | 1,169 |
| `passage_plotinus_vi_9_305` | Plotinus, Enneades, Enn. VI.9.305 | 1,188 |
| `passage_plotinus_vi_9_306` | Plotinus, Enneades, Enn. VI.9.306 | 1,224 |
| `passage_plotinus_vi_9_307` | Plotinus, Enneades, Enn. VI.9.307 | 948 |
| `passage_plotinus_vi_9_308` | Plotinus, Enneades, Enn. VI.9.308 | 1,364 |
| `passage_plotinus_vi_9_309` | Plotinus, Enneades, Enn. VI.9.309 | 1,357 |
| `passage_plotinus_vi_9_31` | Plotinus, Enneades, Enn. VI.9.31 | 1,492 |
| `passage_plotinus_vi_9_310` | Plotinus, Enneades, Enn. VI.9.310 | 1,015 |
| `passage_plotinus_vi_9_311` | Plotinus, Enneades, Enn. VI.9.311 | 1,486 |
| `passage_plotinus_vi_9_312` | Plotinus, Enneades, Enn. VI.9.312 | 1,293 |
| `passage_plotinus_vi_9_313` | Plotinus, Enneades, Enn. VI.9.313 | 1,409 |
| `passage_plotinus_vi_9_314` | Plotinus, Enneades, Enn. VI.9.314 | 1,500 |
| `passage_plotinus_vi_9_315` | Plotinus, Enneades, Enn. VI.9.315 | 1,428 |
| `passage_plotinus_vi_9_316` | Plotinus, Enneades, Enn. VI.9.316 | 289 |
| `passage_plotinus_vi_9_317` | Plotinus, Enneades, Enn. VI.9.317 | 1,520 |
| `passage_plotinus_vi_9_318` | Plotinus, Enneades, Enn. VI.9.318 | 1,191 |
| `passage_plotinus_vi_9_319` | Plotinus, Enneades, Enn. VI.9.319 | 1,462 |
| `passage_plotinus_vi_9_32` | Plotinus, Enneades, Enn. VI.9.32 | 1,267 |
| `passage_plotinus_vi_9_320` | Plotinus, Enneades, Enn. VI.9.320 | 841 |
| `passage_plotinus_vi_9_321` | Plotinus, Enneades, Enn. VI.9.321 | 1,433 |
| `passage_plotinus_vi_9_322` | Plotinus, Enneades, Enn. VI.9.322 | 1,310 |
| `passage_plotinus_vi_9_323` | Plotinus, Enneades, Enn. VI.9.323 | 1,196 |
| `passage_plotinus_vi_9_324` | Plotinus, Enneades, Enn. VI.9.324 | 1,410 |
| `passage_plotinus_vi_9_325` | Plotinus, Enneades, Enn. VI.9.325 | 1,271 |
| `passage_plotinus_vi_9_326` | Plotinus, Enneades, Enn. VI.9.326 | 1,178 |
| `passage_plotinus_vi_9_327` | Plotinus, Enneades, Enn. VI.9.327 | 1,441 |
| `passage_plotinus_vi_9_328` | Plotinus, Enneades, Enn. VI.9.328 | 1,440 |
| `passage_plotinus_vi_9_329` | Plotinus, Enneades, Enn. VI.9.329 | 1,127 |
| `passage_plotinus_vi_9_33` | Plotinus, Enneades, Enn. VI.9.33 | 1,415 |
| `passage_plotinus_vi_9_330` | Plotinus, Enneades, Enn. VI.9.330 | 1,236 |
| `passage_plotinus_vi_9_331` | Plotinus, Enneades, Enn. VI.9.331 | 1,199 |
| `passage_plotinus_vi_9_332` | Plotinus, Enneades, Enn. VI.9.332 | 1,487 |
| `passage_plotinus_vi_9_333` | Plotinus, Enneades, Enn. VI.9.333 | 1,340 |
| `passage_plotinus_vi_9_334` | Plotinus, Enneades, Enn. VI.9.334 | 1,140 |
| `passage_plotinus_vi_9_335` | Plotinus, Enneades, Enn. VI.9.335 | 1,286 |
| `passage_plotinus_vi_9_336` | Plotinus, Enneades, Enn. VI.9.336 | 1,416 |
| `passage_plotinus_vi_9_337` | Plotinus, Enneades, Enn. VI.9.337 | 1,304 |
| `passage_plotinus_vi_9_338` | Plotinus, Enneades, Enn. VI.9.338 | 1,375 |
| `passage_plotinus_vi_9_339` | Plotinus, Enneades, Enn. VI.9.339 | 1,328 |
| `passage_plotinus_vi_9_34` | Plotinus, Enneades, Enn. VI.9.34 | 1,453 |
| `passage_plotinus_vi_9_340` | Plotinus, Enneades, Enn. VI.9.340 | 1,435 |
| `passage_plotinus_vi_9_341` | Plotinus, Enneades, Enn. VI.9.341 | 1,375 |
| `passage_plotinus_vi_9_342` | Plotinus, Enneades, Enn. VI.9.342 | 1,295 |
| `passage_plotinus_vi_9_343` | Plotinus, Enneades, Enn. VI.9.343 | 1,046 |
| `passage_plotinus_vi_9_344` | Plotinus, Enneades, Enn. VI.9.344 | 1,058 |
| `passage_plotinus_vi_9_345` | Plotinus, Enneades, Enn. VI.9.345 | 1,269 |
| `passage_plotinus_vi_9_346` | Plotinus, Enneades, Enn. VI.9.346 | 1,268 |
| `passage_plotinus_vi_9_347` | Plotinus, Enneades, Enn. VI.9.347 | 1,319 |
| `passage_plotinus_vi_9_348` | Plotinus, Enneades, Enn. VI.9.348 | 1,412 |
| `passage_plotinus_vi_9_349` | Plotinus, Enneades, Enn. VI.9.349 | 1,369 |
| `passage_plotinus_vi_9_35` | Plotinus, Enneades, Enn. VI.9.35 | 1,412 |
| `passage_plotinus_vi_9_350` | Plotinus, Enneades, Enn. VI.9.350 | 1,355 |
| `passage_plotinus_vi_9_351` | Plotinus, Enneades, Enn. VI.9.351 | 1,419 |
| `passage_plotinus_vi_9_352` | Plotinus, Enneades, Enn. VI.9.352 | 1,468 |
| `passage_plotinus_vi_9_353` | Plotinus, Enneades, Enn. VI.9.353 | 289 |
| `passage_plotinus_vi_9_354` | Plotinus, Enneades, Enn. VI.9.354 | 1,395 |
| `passage_plotinus_vi_9_355` | Plotinus, Enneades, Enn. VI.9.355 | 1,375 |
| `passage_plotinus_vi_9_356` | Plotinus, Enneades, Enn. VI.9.356 | 1,339 |
| `passage_plotinus_vi_9_357` | Plotinus, Enneades, Enn. VI.9.357 | 1,412 |
| `passage_plotinus_vi_9_358` | Plotinus, Enneades, Enn. VI.9.358 | 1,270 |
| `passage_plotinus_vi_9_359` | Plotinus, Enneades, Enn. VI.9.359 | 1,434 |
| `passage_plotinus_vi_9_36` | Plotinus, Enneades, Enn. VI.9.36 | 999 |
| `passage_plotinus_vi_9_360` | Plotinus, Enneades, Enn. VI.9.360 | 1,358 |
| `passage_plotinus_vi_9_361` | Plotinus, Enneades, Enn. VI.9.361 | 1,376 |
| `passage_plotinus_vi_9_362` | Plotinus, Enneades, Enn. VI.9.362 | 1,494 |
| `passage_plotinus_vi_9_363` | Plotinus, Enneades, Enn. VI.9.363 | 1,467 |
| `passage_plotinus_vi_9_364` | Plotinus, Enneades, Enn. VI.9.364 | 1,449 |
| `passage_plotinus_vi_9_365` | Plotinus, Enneades, Enn. VI.9.365 | 1,161 |
| `passage_plotinus_vi_9_366` | Plotinus, Enneades, Enn. VI.9.366 | 1,500 |
| `passage_plotinus_vi_9_367` | Plotinus, Enneades, Enn. VI.9.367 | 1,446 |
| `passage_plotinus_vi_9_368` | Plotinus, Enneades, Enn. VI.9.368 | 1,479 |
| `passage_plotinus_vi_9_369` | Plotinus, Enneades, Enn. VI.9.369 | 1,352 |
| `passage_plotinus_vi_9_37` | Plotinus, Enneades, Enn. VI.9.37 | 1,327 |
| `passage_plotinus_vi_9_370` | Plotinus, Enneades, Enn. VI.9.370 | 1,273 |
| `passage_plotinus_vi_9_371` | Plotinus, Enneades, Enn. VI.9.371 | 1,169 |
| `passage_plotinus_vi_9_372` | Plotinus, Enneades, Enn. VI.9.372 | 1,107 |
| `passage_plotinus_vi_9_373` | Plotinus, Enneades, Enn. VI.9.373 | 1,809 |
| `passage_plotinus_vi_9_374` | Plotinus, Enneades, Enn. VI.9.374 | 1,260 |
| `passage_plotinus_vi_9_375` | Plotinus, Enneades, Enn. VI.9.375 | 1,356 |
| `passage_plotinus_vi_9_376` | Plotinus, Enneades, Enn. VI.9.376 | 1,291 |
| `passage_plotinus_vi_9_377` | Plotinus, Enneades, Enn. VI.9.377 | 1,426 |
| `passage_plotinus_vi_9_378` | Plotinus, Enneades, Enn. VI.9.378 | 1,355 |
| `passage_plotinus_vi_9_379` | Plotinus, Enneades, Enn. VI.9.379 | 1,232 |
| `passage_plotinus_vi_9_38` | Plotinus, Enneades, Enn. VI.9.38 | 1,445 |
| `passage_plotinus_vi_9_380` | Plotinus, Enneades, Enn. VI.9.380 | 1,356 |
| `passage_plotinus_vi_9_381` | Plotinus, Enneades, Enn. VI.9.381 | 1,146 |
| `passage_plotinus_vi_9_382` | Plotinus, Enneades, Enn. VI.9.382 | 1,062 |
| `passage_plotinus_vi_9_383` | Plotinus, Enneades, Enn. VI.9.383 | 960 |
| `passage_plotinus_vi_9_384` | Plotinus, Enneades, Enn. VI.9.384 | 1,412 |
| `passage_plotinus_vi_9_385` | Plotinus, Enneades, Enn. VI.9.385 | 1,472 |
| `passage_plotinus_vi_9_386` | Plotinus, Enneades, Enn. VI.9.386 | 1,359 |
| `passage_plotinus_vi_9_387` | Plotinus, Enneades, Enn. VI.9.387 | 1,246 |
| `passage_plotinus_vi_9_388` | Plotinus, Enneades, Enn. VI.9.388 | 1,352 |
| `passage_plotinus_vi_9_389` | Plotinus, Enneades, Enn. VI.9.389 | 1,342 |
| `passage_plotinus_vi_9_39` | Plotinus, Enneades, Enn. VI.9.39 | 1,374 |
| `passage_plotinus_vi_9_390` | Plotinus, Enneades, Enn. VI.9.390 | 1,400 |
| `passage_plotinus_vi_9_391` | Plotinus, Enneades, Enn. VI.9.391 | 1,408 |
| `passage_plotinus_vi_9_392` | Plotinus, Enneades, Enn. VI.9.392 | 1,477 |
| `passage_plotinus_vi_9_393` | Plotinus, Enneades, Enn. VI.9.393 | 1,244 |
| `passage_plotinus_vi_9_394` | Plotinus, Enneades, Enn. VI.9.394 | 1,157 |
| `passage_plotinus_vi_9_395` | Plotinus, Enneades, Enn. VI.9.395 | 1,423 |
| `passage_plotinus_vi_9_396` | Plotinus, Enneades, Enn. VI.9.396 | 1,485 |
| `passage_plotinus_vi_9_397` | Plotinus, Enneades, Enn. VI.9.397 | 561 |
| `passage_plotinus_vi_9_398` | Plotinus, Enneades, Enn. VI.9.398 | 1,431 |
| `passage_plotinus_vi_9_399` | Plotinus, Enneades, Enn. VI.9.399 | 1,222 |
| `passage_plotinus_vi_9_4` | Plotinus, Enneades, Enn. VI.9.4 | 1,470 |
| `passage_plotinus_vi_9_40` | Plotinus, Enneades, Enn. VI.9.40 | 1,316 |
| `passage_plotinus_vi_9_400` | Plotinus, Enneades, Enn. VI.9.400 | 1,387 |
| `passage_plotinus_vi_9_401` | Plotinus, Enneades, Enn. VI.9.401 | 1,440 |
| `passage_plotinus_vi_9_402` | Plotinus, Enneades, Enn. VI.9.402 | 1,315 |
| `passage_plotinus_vi_9_403` | Plotinus, Enneades, Enn. VI.9.403 | 1,202 |
| `passage_plotinus_vi_9_404` | Plotinus, Enneades, Enn. VI.9.404 | 1,458 |
| `passage_plotinus_vi_9_405` | Plotinus, Enneades, Enn. VI.9.405 | 1,332 |
| `passage_plotinus_vi_9_406` | Plotinus, Enneades, Enn. VI.9.406 | 1,443 |
| `passage_plotinus_vi_9_407` | Plotinus, Enneades, Enn. VI.9.407 | 1,394 |
| `passage_plotinus_vi_9_408` | Plotinus, Enneades, Enn. VI.9.408 | 1,180 |
| `passage_plotinus_vi_9_409` | Plotinus, Enneades, Enn. VI.9.409 | 1,375 |
| `passage_plotinus_vi_9_41` | Plotinus, Enneades, Enn. VI.9.41 | 1,161 |
| `passage_plotinus_vi_9_410` | Plotinus, Enneades, Enn. VI.9.410 | 981 |
| `passage_plotinus_vi_9_411` | Plotinus, Enneades, Enn. VI.9.411 | 1,162 |
| `passage_plotinus_vi_9_412` | Plotinus, Enneades, Enn. VI.9.412 | 1,375 |
| `passage_plotinus_vi_9_413` | Plotinus, Enneades, Enn. VI.9.413 | 1,211 |
| `passage_plotinus_vi_9_414` | Plotinus, Enneades, Enn. VI.9.414 | 1,185 |
| `passage_plotinus_vi_9_415` | Plotinus, Enneades, Enn. VI.9.415 | 1,318 |
| `passage_plotinus_vi_9_416` | Plotinus, Enneades, Enn. VI.9.416 | 1,306 |
| `passage_plotinus_vi_9_417` | Plotinus, Enneades, Enn. VI.9.417 | 1,134 |
| `passage_plotinus_vi_9_418` | Plotinus, Enneades, Enn. VI.9.418 | 1,492 |
| `passage_plotinus_vi_9_419` | Plotinus, Enneades, Enn. VI.9.419 | 1,441 |
| `passage_plotinus_vi_9_42` | Plotinus, Enneades, Enn. VI.9.42 | 1,253 |
| `passage_plotinus_vi_9_420` | Plotinus, Enneades, Enn. VI.9.420 | 1,407 |
| `passage_plotinus_vi_9_421` | Plotinus, Enneades, Enn. VI.9.421 | 1,175 |
| `passage_plotinus_vi_9_422` | Plotinus, Enneades, Enn. VI.9.422 | 1,231 |
| `passage_plotinus_vi_9_423` | Plotinus, Enneades, Enn. VI.9.423 | 1,404 |
| `passage_plotinus_vi_9_424` | Plotinus, Enneades, Enn. VI.9.424 | 1,350 |
| `passage_plotinus_vi_9_425` | Plotinus, Enneades, Enn. VI.9.425 | 1,169 |
| `passage_plotinus_vi_9_426` | Plotinus, Enneades, Enn. VI.9.426 | 1,495 |
| `passage_plotinus_vi_9_427` | Plotinus, Enneades, Enn. VI.9.427 | 1,423 |
| `passage_plotinus_vi_9_428` | Plotinus, Enneades, Enn. VI.9.428 | 1,316 |
| `passage_plotinus_vi_9_429` | Plotinus, Enneades, Enn. VI.9.429 | 1,187 |
| `passage_plotinus_vi_9_43` | Plotinus, Enneades, Enn. VI.9.43 | 1,412 |
| `passage_plotinus_vi_9_430` | Plotinus, Enneades, Enn. VI.9.430 | 1,011 |
| `passage_plotinus_vi_9_431` | Plotinus, Enneades, Enn. VI.9.431 | 579 |
| `passage_plotinus_vi_9_432` | Plotinus, Enneades, Enn. VI.9.432 | 1,039 |
| `passage_plotinus_vi_9_433` | Plotinus, Enneades, Enn. VI.9.433 | 1,163 |
| `passage_plotinus_vi_9_434` | Plotinus, Enneades, Enn. VI.9.434 | 574 |
| `passage_plotinus_vi_9_435` | Plotinus, Enneades, Enn. VI.9.435 | 1,230 |
| `passage_plotinus_vi_9_436` | Plotinus, Enneades, Enn. VI.9.436 | 1,275 |
| `passage_plotinus_vi_9_437` | Plotinus, Enneades, Enn. VI.9.437 | 1,431 |
| `passage_plotinus_vi_9_438` | Plotinus, Enneades, Enn. VI.9.438 | 1,381 |
| `passage_plotinus_vi_9_439` | Plotinus, Enneades, Enn. VI.9.439 | 1,383 |
| `passage_plotinus_vi_9_44` | Plotinus, Enneades, Enn. VI.9.44 | 1,288 |
| `passage_plotinus_vi_9_440` | Plotinus, Enneades, Enn. VI.9.440 | 1,467 |
| `passage_plotinus_vi_9_441` | Plotinus, Enneades, Enn. VI.9.441 | 1,356 |
| `passage_plotinus_vi_9_442` | Plotinus, Enneades, Enn. VI.9.442 | 1,423 |
| `passage_plotinus_vi_9_443` | Plotinus, Enneades, Enn. VI.9.443 | 1,192 |
| `passage_plotinus_vi_9_444` | Plotinus, Enneades, Enn. VI.9.444 | 1,359 |
| `passage_plotinus_vi_9_445` | Plotinus, Enneades, Enn. VI.9.445 | 1,198 |
| `passage_plotinus_vi_9_446` | Plotinus, Enneades, Enn. VI.9.446 | 1,393 |
| `passage_plotinus_vi_9_447` | Plotinus, Enneades, Enn. VI.9.447 | 1,291 |
| `passage_plotinus_vi_9_448` | Plotinus, Enneades, Enn. VI.9.448 | 1,139 |
| `passage_plotinus_vi_9_449` | Plotinus, Enneades, Enn. VI.9.449 | 1,178 |
| `passage_plotinus_vi_9_45` | Plotinus, Enneades, Enn. VI.9.45 | 1,270 |
| `passage_plotinus_vi_9_450` | Plotinus, Enneades, Enn. VI.9.450 | 1,497 |
| `passage_plotinus_vi_9_451` | Plotinus, Enneades, Enn. VI.9.451 | 1,482 |
| `passage_plotinus_vi_9_452` | Plotinus, Enneades, Enn. VI.9.452 | 1,380 |
| `passage_plotinus_vi_9_453` | Plotinus, Enneades, Enn. VI.9.453 | 1,122 |
| `passage_plotinus_vi_9_454` | Plotinus, Enneades, Enn. VI.9.454 | 699 |
| `passage_plotinus_vi_9_455` | Plotinus, Enneades, Enn. VI.9.455 | 1,955 |
| `passage_plotinus_vi_9_456` | Plotinus, Enneades, Enn. VI.9.456 | 1,270 |
| `passage_plotinus_vi_9_457` | Plotinus, Enneades, Enn. VI.9.457 | 1,439 |
| `passage_plotinus_vi_9_458` | Plotinus, Enneades, Enn. VI.9.458 | 1,353 |
| `passage_plotinus_vi_9_459` | Plotinus, Enneades, Enn. VI.9.459 | 1,055 |
| `passage_plotinus_vi_9_46` | Plotinus, Enneades, Enn. VI.9.46 | 1,278 |
| `passage_plotinus_vi_9_460` | Plotinus, Enneades, Enn. VI.9.460 | 1,488 |
| `passage_plotinus_vi_9_461` | Plotinus, Enneades, Enn. VI.9.461 | 711 |
| `passage_plotinus_vi_9_462` | Plotinus, Enneades, Enn. VI.9.462 | 1,302 |
| `passage_plotinus_vi_9_463` | Plotinus, Enneades, Enn. VI.9.463 | 1,018 |
| `passage_plotinus_vi_9_464` | Plotinus, Enneades, Enn. VI.9.464 | 1,357 |
| `passage_plotinus_vi_9_465` | Plotinus, Enneades, Enn. VI.9.465 | 1,459 |
| `passage_plotinus_vi_9_466` | Plotinus, Enneades, Enn. VI.9.466 | 1,209 |
| `passage_plotinus_vi_9_467` | Plotinus, Enneades, Enn. VI.9.467 | 1,471 |
| `passage_plotinus_vi_9_468` | Plotinus, Enneades, Enn. VI.9.468 | 1,410 |
| `passage_plotinus_vi_9_469` | Plotinus, Enneades, Enn. VI.9.469 | 1,468 |
| `passage_plotinus_vi_9_47` | Plotinus, Enneades, Enn. VI.9.47 | 1,066 |
| `passage_plotinus_vi_9_470` | Plotinus, Enneades, Enn. VI.9.470 | 1,127 |
| `passage_plotinus_vi_9_471` | Plotinus, Enneades, Enn. VI.9.471 | 1,352 |
| `passage_plotinus_vi_9_472` | Plotinus, Enneades, Enn. VI.9.472 | 1,411 |
| `passage_plotinus_vi_9_473` | Plotinus, Enneades, Enn. VI.9.473 | 1,073 |
| `passage_plotinus_vi_9_474` | Plotinus, Enneades, Enn. VI.9.474 | 511 |
| `passage_plotinus_vi_9_475` | Plotinus, Enneades, Enn. VI.9.475 | 1,187 |
| `passage_plotinus_vi_9_476` | Plotinus, Enneades, Enn. VI.9.476 | 1,407 |
| `passage_plotinus_vi_9_477` | Plotinus, Enneades, Enn. VI.9.477 | 1,407 |
| `passage_plotinus_vi_9_478` | Plotinus, Enneades, Enn. VI.9.478 | 1,488 |
| `passage_plotinus_vi_9_479` | Plotinus, Enneades, Enn. VI.9.479 | 1,393 |
| `passage_plotinus_vi_9_48` | Plotinus, Enneades, Enn. VI.9.48 | 1,374 |
| `passage_plotinus_vi_9_480` | Plotinus, Enneades, Enn. VI.9.480 | 1,375 |
| `passage_plotinus_vi_9_481` | Plotinus, Enneades, Enn. VI.9.481 | 1,371 |
| `passage_plotinus_vi_9_482` | Plotinus, Enneades, Enn. VI.9.482 | 1,499 |
| `passage_plotinus_vi_9_483` | Plotinus, Enneades, Enn. VI.9.483 | 1,309 |
| `passage_plotinus_vi_9_484` | Plotinus, Enneades, Enn. VI.9.484 | 1,320 |
| `passage_plotinus_vi_9_485` | Plotinus, Enneades, Enn. VI.9.485 | 1,449 |
| `passage_plotinus_vi_9_486` | Plotinus, Enneades, Enn. VI.9.486 | 1,284 |
| `passage_plotinus_vi_9_487` | Plotinus, Enneades, Enn. VI.9.487 | 1,419 |
| `passage_plotinus_vi_9_488` | Plotinus, Enneades, Enn. VI.9.488 | 1,493 |
| `passage_plotinus_vi_9_489` | Plotinus, Enneades, Enn. VI.9.489 | 1,355 |
| `passage_plotinus_vi_9_49` | Plotinus, Enneades, Enn. VI.9.49 | 1,356 |
| `passage_plotinus_vi_9_490` | Plotinus, Enneades, Enn. VI.9.490 | 1,425 |
| `passage_plotinus_vi_9_491` | Plotinus, Enneades, Enn. VI.9.491 | 1,339 |
| `passage_plotinus_vi_9_492` | Plotinus, Enneades, Enn. VI.9.492 | 1,430 |
| `passage_plotinus_vi_9_493` | Plotinus, Enneades, Enn. VI.9.493 | 1,248 |
| `passage_plotinus_vi_9_494` | Plotinus, Enneades, Enn. VI.9.494 | 1,495 |
| `passage_plotinus_vi_9_495` | Plotinus, Enneades, Enn. VI.9.495 | 1,035 |
| `passage_plotinus_vi_9_496` | Plotinus, Enneades, Enn. VI.9.496 | 1,152 |
| `passage_plotinus_vi_9_497` | Plotinus, Enneades, Enn. VI.9.497 | 1,262 |
| `passage_plotinus_vi_9_498` | Plotinus, Enneades, Enn. VI.9.498 | 1,313 |
| `passage_plotinus_vi_9_499` | Plotinus, Enneades, Enn. VI.9.499 | 1,333 |
| `passage_plotinus_vi_9_5` | Plotinus, Enneades, Enn. VI.9.5 | 915 |
| `passage_plotinus_vi_9_50` | Plotinus, Enneades, Enn. VI.9.50 | 1,461 |
| `passage_plotinus_vi_9_500` | Plotinus, Enneades, Enn. VI.9.500 | 1,480 |
| `passage_plotinus_vi_9_501` | Plotinus, Enneades, Enn. VI.9.501 | 1,060 |
| `passage_plotinus_vi_9_502` | Plotinus, Enneades, Enn. VI.9.502 | 1,333 |
| `passage_plotinus_vi_9_503` | Plotinus, Enneades, Enn. VI.9.503 | 1,346 |
| `passage_plotinus_vi_9_504` | Plotinus, Enneades, Enn. VI.9.504 | 1,267 |
| `passage_plotinus_vi_9_505` | Plotinus, Enneades, Enn. VI.9.505 | 817 |
| `passage_plotinus_vi_9_506` | Plotinus, Enneades, Enn. VI.9.506 | 1,068 |
| `passage_plotinus_vi_9_507` | Plotinus, Enneades, Enn. VI.9.507 | 1,287 |
| `passage_plotinus_vi_9_508` | Plotinus, Enneades, Enn. VI.9.508 | 1,397 |
| `passage_plotinus_vi_9_509` | Plotinus, Enneades, Enn. VI.9.509 | 1,287 |
| `passage_plotinus_vi_9_51` | Plotinus, Enneades, Enn. VI.9.51 | 1,329 |
| `passage_plotinus_vi_9_510` | Plotinus, Enneades, Enn. VI.9.510 | 1,442 |
| `passage_plotinus_vi_9_511` | Plotinus, Enneades, Enn. VI.9.511 | 990 |
| `passage_plotinus_vi_9_512` | Plotinus, Enneades, Enn. VI.9.512 | 1,452 |
| `passage_plotinus_vi_9_513` | Plotinus, Enneades, Enn. VI.9.513 | 1,451 |
| `passage_plotinus_vi_9_514` | Plotinus, Enneades, Enn. VI.9.514 | 1,196 |
| `passage_plotinus_vi_9_515` | Plotinus, Enneades, Enn. VI.9.515 | 1,276 |
| `passage_plotinus_vi_9_516` | Plotinus, Enneades, Enn. VI.9.516 | 1,433 |
| `passage_plotinus_vi_9_517` | Plotinus, Enneades, Enn. VI.9.517 | 1,496 |
| `passage_plotinus_vi_9_518` | Plotinus, Enneades, Enn. VI.9.518 | 1,202 |
| `passage_plotinus_vi_9_519` | Plotinus, Enneades, Enn. VI.9.519 | 1,443 |
| `passage_plotinus_vi_9_52` | Plotinus, Enneades, Enn. VI.9.52 | 1,488 |
| `passage_plotinus_vi_9_520` | Plotinus, Enneades, Enn. VI.9.520 | 1,193 |
| `passage_plotinus_vi_9_521` | Plotinus, Enneades, Enn. VI.9.521 | 931 |
| `passage_plotinus_vi_9_522` | Plotinus, Enneades, Enn. VI.9.522 | 1,461 |
| `passage_plotinus_vi_9_523` | Plotinus, Enneades, Enn. VI.9.523 | 1,478 |
| `passage_plotinus_vi_9_524` | Plotinus, Enneades, Enn. VI.9.524 | 1,474 |
| `passage_plotinus_vi_9_525` | Plotinus, Enneades, Enn. VI.9.525 | 1,207 |
| `passage_plotinus_vi_9_526` | Plotinus, Enneades, Enn. VI.9.526 | 1,279 |
| `passage_plotinus_vi_9_527` | Plotinus, Enneades, Enn. VI.9.527 | 1,377 |
| `passage_plotinus_vi_9_528` | Plotinus, Enneades, Enn. VI.9.528 | 1,461 |
| `passage_plotinus_vi_9_529` | Plotinus, Enneades, Enn. VI.9.529 | 1,390 |
| `passage_plotinus_vi_9_53` | Plotinus, Enneades, Enn. VI.9.53 | 1,208 |
| `passage_plotinus_vi_9_530` | Plotinus, Enneades, Enn. VI.9.530 | 1,172 |
| `passage_plotinus_vi_9_531` | Plotinus, Enneades, Enn. VI.9.531 | 1,390 |
| `passage_plotinus_vi_9_532` | Plotinus, Enneades, Enn. VI.9.532 | 1,397 |
| `passage_plotinus_vi_9_533` | Plotinus, Enneades, Enn. VI.9.533 | 1,431 |
| `passage_plotinus_vi_9_534` | Plotinus, Enneades, Enn. VI.9.534 | 1,469 |
| `passage_plotinus_vi_9_535` | Plotinus, Enneades, Enn. VI.9.535 | 1,475 |
| `passage_plotinus_vi_9_536` | Plotinus, Enneades, Enn. VI.9.536 | 1,432 |
| `passage_plotinus_vi_9_537` | Plotinus, Enneades, Enn. VI.9.537 | 1,482 |
| `passage_plotinus_vi_9_538` | Plotinus, Enneades, Enn. VI.9.538 | 1,205 |
| `passage_plotinus_vi_9_539` | Plotinus, Enneades, Enn. VI.9.539 | 1,484 |
| `passage_plotinus_vi_9_54` | Plotinus, Enneades, Enn. VI.9.54 | 1,117 |
| `passage_plotinus_vi_9_540` | Plotinus, Enneades, Enn. VI.9.540 | 1,482 |
| `passage_plotinus_vi_9_541` | Plotinus, Enneades, Enn. VI.9.541 | 1,429 |
| `passage_plotinus_vi_9_542` | Plotinus, Enneades, Enn. VI.9.542 | 1,337 |
| `passage_plotinus_vi_9_543` | Plotinus, Enneades, Enn. VI.9.543 | 1,438 |
| `passage_plotinus_vi_9_544` | Plotinus, Enneades, Enn. VI.9.544 | 1,465 |
| `passage_plotinus_vi_9_545` | Plotinus, Enneades, Enn. VI.9.545 | 1,170 |
| `passage_plotinus_vi_9_546` | Plotinus, Enneades, Enn. VI.9.546 | 933 |
| `passage_plotinus_vi_9_547` | Plotinus, Enneades, Enn. VI.9.547 | 1,274 |
| `passage_plotinus_vi_9_548` | Plotinus, Enneades, Enn. VI.9.548 | 1,461 |
| `passage_plotinus_vi_9_549` | Plotinus, Enneades, Enn. VI.9.549 | 1,014 |
| `passage_plotinus_vi_9_55` | Plotinus, Enneades, Enn. VI.9.55 | 1,314 |
| `passage_plotinus_vi_9_550` | Plotinus, Enneades, Enn. VI.9.550 | 1,289 |
| `passage_plotinus_vi_9_551` | Plotinus, Enneades, Enn. VI.9.551 | 1,181 |
| `passage_plotinus_vi_9_552` | Plotinus, Enneades, Enn. VI.9.552 | 1,389 |
| `passage_plotinus_vi_9_553` | Plotinus, Enneades, Enn. VI.9.553 | 706 |
| `passage_plotinus_vi_9_554` | Plotinus, Enneades, Enn. VI.9.554 | 1,467 |
| `passage_plotinus_vi_9_555` | Plotinus, Enneades, Enn. VI.9.555 | 1,413 |
| `passage_plotinus_vi_9_556` | Plotinus, Enneades, Enn. VI.9.556 | 1,481 |
| `passage_plotinus_vi_9_557` | Plotinus, Enneades, Enn. VI.9.557 | 1,098 |
| `passage_plotinus_vi_9_558` | Plotinus, Enneades, Enn. VI.9.558 | 1,117 |
| `passage_plotinus_vi_9_559` | Plotinus, Enneades, Enn. VI.9.559 | 1,416 |
| `passage_plotinus_vi_9_56` | Plotinus, Enneades, Enn. VI.9.56 | 1,480 |
| `passage_plotinus_vi_9_560` | Plotinus, Enneades, Enn. VI.9.560 | 1,303 |
| `passage_plotinus_vi_9_561` | Plotinus, Enneades, Enn. VI.9.561 | 1,300 |
| `passage_plotinus_vi_9_562` | Plotinus, Enneades, Enn. VI.9.562 | 1,461 |
| `passage_plotinus_vi_9_563` | Plotinus, Enneades, Enn. VI.9.563 | 1,471 |
| `passage_plotinus_vi_9_564` | Plotinus, Enneades, Enn. VI.9.564 | 1,485 |
| `passage_plotinus_vi_9_565` | Plotinus, Enneades, Enn. VI.9.565 | 1,491 |
| `passage_plotinus_vi_9_566` | Plotinus, Enneades, Enn. VI.9.566 | 1,376 |
| `passage_plotinus_vi_9_567` | Plotinus, Enneades, Enn. VI.9.567 | 1,128 |
| `passage_plotinus_vi_9_568` | Plotinus, Enneades, Enn. VI.9.568 | 1,048 |
| `passage_plotinus_vi_9_569` | Plotinus, Enneades, Enn. VI.9.569 | 1,269 |
| `passage_plotinus_vi_9_57` | Plotinus, Enneades, Enn. VI.9.57 | 1,329 |
| `passage_plotinus_vi_9_570` | Plotinus, Enneades, Enn. VI.9.570 | 1,151 |
| `passage_plotinus_vi_9_571` | Plotinus, Enneades, Enn. VI.9.571 | 1,378 |
| `passage_plotinus_vi_9_572` | Plotinus, Enneades, Enn. VI.9.572 | 1,459 |
| `passage_plotinus_vi_9_573` | Plotinus, Enneades, Enn. VI.9.573 | 1,244 |
| `passage_plotinus_vi_9_574` | Plotinus, Enneades, Enn. VI.9.574 | 1,266 |
| `passage_plotinus_vi_9_575` | Plotinus, Enneades, Enn. VI.9.575 | 1,445 |
| `passage_plotinus_vi_9_576` | Plotinus, Enneades, Enn. VI.9.576 | 1,398 |
| `passage_plotinus_vi_9_577` | Plotinus, Enneades, Enn. VI.9.577 | 1,041 |
| `passage_plotinus_vi_9_578` | Plotinus, Enneades, Enn. VI.9.578 | 1,431 |
| `passage_plotinus_vi_9_579` | Plotinus, Enneades, Enn. VI.9.579 | 1,357 |
| `passage_plotinus_vi_9_58` | Plotinus, Enneades, Enn. VI.9.58 | 1,392 |
| `passage_plotinus_vi_9_580` | Plotinus, Enneades, Enn. VI.9.580 | 1,399 |
| `passage_plotinus_vi_9_581` | Plotinus, Enneades, Enn. VI.9.581 | 730 |
| `passage_plotinus_vi_9_582` | Plotinus, Enneades, Enn. VI.9.582 | 1,455 |
| `passage_plotinus_vi_9_583` | Plotinus, Enneades, Enn. VI.9.583 | 1,443 |
| `passage_plotinus_vi_9_584` | Plotinus, Enneades, Enn. VI.9.584 | 1,472 |
| `passage_plotinus_vi_9_585` | Plotinus, Enneades, Enn. VI.9.585 | 1,207 |
| `passage_plotinus_vi_9_586` | Plotinus, Enneades, Enn. VI.9.586 | 1,418 |
| `passage_plotinus_vi_9_587` | Plotinus, Enneades, Enn. VI.9.587 | 1,331 |
| `passage_plotinus_vi_9_588` | Plotinus, Enneades, Enn. VI.9.588 | 1,211 |
| `passage_plotinus_vi_9_589` | Plotinus, Enneades, Enn. VI.9.589 | 1,322 |
| `passage_plotinus_vi_9_59` | Plotinus, Enneades, Enn. VI.9.59 | 1,044 |
| `passage_plotinus_vi_9_590` | Plotinus, Enneades, Enn. VI.9.590 | 1,470 |
| `passage_plotinus_vi_9_591` | Plotinus, Enneades, Enn. VI.9.591 | 1,105 |
| `passage_plotinus_vi_9_592` | Plotinus, Enneades, Enn. VI.9.592 | 1,303 |
| `passage_plotinus_vi_9_593` | Plotinus, Enneades, Enn. VI.9.593 | 1,043 |
| `passage_plotinus_vi_9_594` | Plotinus, Enneades, Enn. VI.9.594 | 1,385 |
| `passage_plotinus_vi_9_595` | Plotinus, Enneades, Enn. VI.9.595 | 1,424 |
| `passage_plotinus_vi_9_596` | Plotinus, Enneades, Enn. VI.9.596 | 1,157 |
| `passage_plotinus_vi_9_597` | Plotinus, Enneades, Enn. VI.9.597 | 1,353 |
| `passage_plotinus_vi_9_598` | Plotinus, Enneades, Enn. VI.9.598 | 1,277 |
| `passage_plotinus_vi_9_599` | Plotinus, Enneades, Enn. VI.9.599 | 1,471 |
| `passage_plotinus_vi_9_6` | Plotinus, Enneades, Enn. VI.9.6 | 1,483 |
| `passage_plotinus_vi_9_60` | Plotinus, Enneades, Enn. VI.9.60 | 1,108 |
| `passage_plotinus_vi_9_600` | Plotinus, Enneades, Enn. VI.9.600 | 1,437 |
| `passage_plotinus_vi_9_601` | Plotinus, Enneades, Enn. VI.9.601 | 1,476 |
| `passage_plotinus_vi_9_602` | Plotinus, Enneades, Enn. VI.9.602 | 1,414 |
| `passage_plotinus_vi_9_603` | Plotinus, Enneades, Enn. VI.9.603 | 1,370 |
| `passage_plotinus_vi_9_604` | Plotinus, Enneades, Enn. VI.9.604 | 1,072 |
| `passage_plotinus_vi_9_605` | Plotinus, Enneades, Enn. VI.9.605 | 1,410 |
| `passage_plotinus_vi_9_606` | Plotinus, Enneades, Enn. VI.9.606 | 1,482 |
| `passage_plotinus_vi_9_607` | Plotinus, Enneades, Enn. VI.9.607 | 1,293 |
| `passage_plotinus_vi_9_608` | Plotinus, Enneades, Enn. VI.9.608 | 1,148 |
| `passage_plotinus_vi_9_609` | Plotinus, Enneades, Enn. VI.9.609 | 1,470 |
| `passage_plotinus_vi_9_61` | Plotinus, Enneades, Enn. VI.9.61 | 1,302 |
| `passage_plotinus_vi_9_610` | Plotinus, Enneades, Enn. VI.9.610 | 1,268 |
| `passage_plotinus_vi_9_611` | Plotinus, Enneades, Enn. VI.9.611 | 1,331 |
| `passage_plotinus_vi_9_612` | Plotinus, Enneades, Enn. VI.9.612 | 1,369 |
| `passage_plotinus_vi_9_613` | Plotinus, Enneades, Enn. VI.9.613 | 1,270 |
| `passage_plotinus_vi_9_614` | Plotinus, Enneades, Enn. VI.9.614 | 1,388 |
| `passage_plotinus_vi_9_615` | Plotinus, Enneades, Enn. VI.9.615 | 1,373 |
| `passage_plotinus_vi_9_616` | Plotinus, Enneades, Enn. VI.9.616 | 1,179 |
| `passage_plotinus_vi_9_617` | Plotinus, Enneades, Enn. VI.9.617 | 1,222 |
| `passage_plotinus_vi_9_618` | Plotinus, Enneades, Enn. VI.9.618 | 1,230 |
| `passage_plotinus_vi_9_619` | Plotinus, Enneades, Enn. VI.9.619 | 1,447 |
| `passage_plotinus_vi_9_62` | Plotinus, Enneades, Enn. VI.9.62 | 1,266 |
| `passage_plotinus_vi_9_620` | Plotinus, Enneades, Enn. VI.9.620 | 1,404 |
| `passage_plotinus_vi_9_621` | Plotinus, Enneades, Enn. VI.9.621 | 1,492 |
| `passage_plotinus_vi_9_622` | Plotinus, Enneades, Enn. VI.9.622 | 1,468 |
| `passage_plotinus_vi_9_623` | Plotinus, Enneades, Enn. VI.9.623 | 1,473 |
| `passage_plotinus_vi_9_624` | Plotinus, Enneades, Enn. VI.9.624 | 1,111 |
| `passage_plotinus_vi_9_625` | Plotinus, Enneades, Enn. VI.9.625 | 1,382 |
| `passage_plotinus_vi_9_626` | Plotinus, Enneades, Enn. VI.9.626 | 1,350 |
| `passage_plotinus_vi_9_627` | Plotinus, Enneades, Enn. VI.9.627 | 1,306 |
| `passage_plotinus_vi_9_628` | Plotinus, Enneades, Enn. VI.9.628 | 1,240 |
| `passage_plotinus_vi_9_629` | Plotinus, Enneades, Enn. VI.9.629 | 1,315 |
| `passage_plotinus_vi_9_63` | Plotinus, Enneades, Enn. VI.9.63 | 610 |
| `passage_plotinus_vi_9_630` | Plotinus, Enneades, Enn. VI.9.630 | 767 |
| `passage_plotinus_vi_9_631` | Plotinus, Enneades, Enn. VI.9.631 | 1,421 |
| `passage_plotinus_vi_9_632` | Plotinus, Enneades, Enn. VI.9.632 | 1,263 |
| `passage_plotinus_vi_9_633` | Plotinus, Enneades, Enn. VI.9.633 | 1,385 |
| `passage_plotinus_vi_9_634` | Plotinus, Enneades, Enn. VI.9.634 | 645 |
| `passage_plotinus_vi_9_635` | Plotinus, Enneades, Enn. VI.9.635 | 863 |
| `passage_plotinus_vi_9_636` | Plotinus, Enneades, Enn. VI.9.636 | 1,243 |
| `passage_plotinus_vi_9_637` | Plotinus, Enneades, Enn. VI.9.637 | 1,394 |
| `passage_plotinus_vi_9_638` | Plotinus, Enneades, Enn. VI.9.638 | 1,321 |
| `passage_plotinus_vi_9_639` | Plotinus, Enneades, Enn. VI.9.639 | 929 |
| `passage_plotinus_vi_9_64` | Plotinus, Enneades, Enn. VI.9.64 | 1,668 |
| `passage_plotinus_vi_9_640` | Plotinus, Enneades, Enn. VI.9.640 | 1,074 |
| `passage_plotinus_vi_9_641` | Plotinus, Enneades, Enn. VI.9.641 | 955 |
| `passage_plotinus_vi_9_642` | Plotinus, Enneades, Enn. VI.9.642 | 1,495 |
| `passage_plotinus_vi_9_643` | Plotinus, Enneades, Enn. VI.9.643 | 1,445 |
| `passage_plotinus_vi_9_644` | Plotinus, Enneades, Enn. VI.9.644 | 647 |
| `passage_plotinus_vi_9_645` | Plotinus, Enneades, Enn. VI.9.645 | 1,428 |
| `passage_plotinus_vi_9_646` | Plotinus, Enneades, Enn. VI.9.646 | 1,433 |
| `passage_plotinus_vi_9_647` | Plotinus, Enneades, Enn. VI.9.647 | 1,346 |
| `passage_plotinus_vi_9_648` | Plotinus, Enneades, Enn. VI.9.648 | 1,389 |
| `passage_plotinus_vi_9_649` | Plotinus, Enneades, Enn. VI.9.649 | 1,334 |
| `passage_plotinus_vi_9_65` | Plotinus, Enneades, Enn. VI.9.65 | 1,394 |
| `passage_plotinus_vi_9_650` | Plotinus, Enneades, Enn. VI.9.650 | 809 |
| `passage_plotinus_vi_9_651` | Plotinus, Enneades, Enn. VI.9.651 | 1,299 |
| `passage_plotinus_vi_9_652` | Plotinus, Enneades, Enn. VI.9.652 | 949 |
| `passage_plotinus_vi_9_653` | Plotinus, Enneades, Enn. VI.9.653 | 1,266 |
| `passage_plotinus_vi_9_654` | Plotinus, Enneades, Enn. VI.9.654 | 1,363 |
| `passage_plotinus_vi_9_655` | Plotinus, Enneades, Enn. VI.9.655 | 1,199 |
| `passage_plotinus_vi_9_656` | Plotinus, Enneades, Enn. VI.9.656 | 1,188 |
| `passage_plotinus_vi_9_657` | Plotinus, Enneades, Enn. VI.9.657 | 1,352 |
| `passage_plotinus_vi_9_658` | Plotinus, Enneades, Enn. VI.9.658 | 1,325 |
| `passage_plotinus_vi_9_659` | Plotinus, Enneades, Enn. VI.9.659 | 1,266 |
| `passage_plotinus_vi_9_66` | Plotinus, Enneades, Enn. VI.9.66 | 1,204 |
| `passage_plotinus_vi_9_660` | Plotinus, Enneades, Enn. VI.9.660 | 1,247 |
| `passage_plotinus_vi_9_661` | Plotinus, Enneades, Enn. VI.9.661 | 1,393 |
| `passage_plotinus_vi_9_662` | Plotinus, Enneades, Enn. VI.9.662 | 1,371 |
| `passage_plotinus_vi_9_663` | Plotinus, Enneades, Enn. VI.9.663 | 1,411 |
| `passage_plotinus_vi_9_664` | Plotinus, Enneades, Enn. VI.9.664 | 1,264 |
| `passage_plotinus_vi_9_665` | Plotinus, Enneades, Enn. VI.9.665 | 1,339 |
| `passage_plotinus_vi_9_666` | Plotinus, Enneades, Enn. VI.9.666 | 197 |
| `passage_plotinus_vi_9_667` | Plotinus, Enneades, Enn. VI.9.667 | 1,511 |
| `passage_plotinus_vi_9_668` | Plotinus, Enneades, Enn. VI.9.668 | 1,251 |
| `passage_plotinus_vi_9_669` | Plotinus, Enneades, Enn. VI.9.669 | 1,224 |
| `passage_plotinus_vi_9_67` | Plotinus, Enneades, Enn. VI.9.67 | 1,411 |
| `passage_plotinus_vi_9_670` | Plotinus, Enneades, Enn. VI.9.670 | 1,141 |
| `passage_plotinus_vi_9_671` | Plotinus, Enneades, Enn. VI.9.671 | 1,324 |
| `passage_plotinus_vi_9_672` | Plotinus, Enneades, Enn. VI.9.672 | 1,258 |
| `passage_plotinus_vi_9_673` | Plotinus, Enneades, Enn. VI.9.673 | 1,371 |
| `passage_plotinus_vi_9_674` | Plotinus, Enneades, Enn. VI.9.674 | 1,324 |
| `passage_plotinus_vi_9_675` | Plotinus, Enneades, Enn. VI.9.675 | 1,313 |
| `passage_plotinus_vi_9_676` | Plotinus, Enneades, Enn. VI.9.676 | 1,189 |
| `passage_plotinus_vi_9_677` | Plotinus, Enneades, Enn. VI.9.677 | 1,487 |
| `passage_plotinus_vi_9_678` | Plotinus, Enneades, Enn. VI.9.678 | 1,451 |
| `passage_plotinus_vi_9_679` | Plotinus, Enneades, Enn. VI.9.679 | 1,262 |
| `passage_plotinus_vi_9_68` | Plotinus, Enneades, Enn. VI.9.68 | 1,334 |
| `passage_plotinus_vi_9_680` | Plotinus, Enneades, Enn. VI.9.680 | 1,470 |
| `passage_plotinus_vi_9_681` | Plotinus, Enneades, Enn. VI.9.681 | 858 |
| `passage_plotinus_vi_9_682` | Plotinus, Enneades, Enn. VI.9.682 | 1,370 |
| `passage_plotinus_vi_9_683` | Plotinus, Enneades, Enn. VI.9.683 | 1,263 |
| `passage_plotinus_vi_9_684` | Plotinus, Enneades, Enn. VI.9.684 | 1,422 |
| `passage_plotinus_vi_9_685` | Plotinus, Enneades, Enn. VI.9.685 | 1,374 |
| `passage_plotinus_vi_9_686` | Plotinus, Enneades, Enn. VI.9.686 | 1,368 |
| `passage_plotinus_vi_9_687` | Plotinus, Enneades, Enn. VI.9.687 | 1,468 |
| `passage_plotinus_vi_9_688` | Plotinus, Enneades, Enn. VI.9.688 | 1,404 |
| `passage_plotinus_vi_9_689` | Plotinus, Enneades, Enn. VI.9.689 | 1,402 |
| `passage_plotinus_vi_9_69` | Plotinus, Enneades, Enn. VI.9.69 | 1,201 |
| `passage_plotinus_vi_9_690` | Plotinus, Enneades, Enn. VI.9.690 | 1,503 |
| `passage_plotinus_vi_9_691` | Plotinus, Enneades, Enn. VI.9.691 | 1,353 |
| `passage_plotinus_vi_9_692` | Plotinus, Enneades, Enn. VI.9.692 | 541 |
| `passage_plotinus_vi_9_693` | Plotinus, Enneades, Enn. VI.9.693 | 1,757 |
| `passage_plotinus_vi_9_694` | Plotinus, Enneades, Enn. VI.9.694 | 1,480 |
| `passage_plotinus_vi_9_695` | Plotinus, Enneades, Enn. VI.9.695 | 1,487 |
| `passage_plotinus_vi_9_696` | Plotinus, Enneades, Enn. VI.9.696 | 1,450 |
| `passage_plotinus_vi_9_697` | Plotinus, Enneades, Enn. VI.9.697 | 1,307 |
| `passage_plotinus_vi_9_698` | Plotinus, Enneades, Enn. VI.9.698 | 1,385 |
| `passage_plotinus_vi_9_699` | Plotinus, Enneades, Enn. VI.9.699 | 1,169 |
| `passage_plotinus_vi_9_7` | Plotinus, Enneades, Enn. VI.9.7 | 1,159 |
| `passage_plotinus_vi_9_70` | Plotinus, Enneades, Enn. VI.9.70 | 1,431 |
| `passage_plotinus_vi_9_700` | Plotinus, Enneades, Enn. VI.9.700 | 1,356 |
| `passage_plotinus_vi_9_701` | Plotinus, Enneades, Enn. VI.9.701 | 1,391 |
| `passage_plotinus_vi_9_702` | Plotinus, Enneades, Enn. VI.9.702 | 1,492 |
| `passage_plotinus_vi_9_703` | Plotinus, Enneades, Enn. VI.9.703 | 1,359 |
| `passage_plotinus_vi_9_704` | Plotinus, Enneades, Enn. VI.9.704 | 1,422 |
| `passage_plotinus_vi_9_705` | Plotinus, Enneades, Enn. VI.9.705 | 1,276 |
| `passage_plotinus_vi_9_706` | Plotinus, Enneades, Enn. VI.9.706 | 648 |
| `passage_plotinus_vi_9_707` | Plotinus, Enneades, Enn. VI.9.707 | 1,451 |
| `passage_plotinus_vi_9_708` | Plotinus, Enneades, Enn. VI.9.708 | 1,312 |
| `passage_plotinus_vi_9_709` | Plotinus, Enneades, Enn. VI.9.709 | 600 |
| `passage_plotinus_vi_9_71` | Plotinus, Enneades, Enn. VI.9.71 | 1,458 |
| `passage_plotinus_vi_9_72` | Plotinus, Enneades, Enn. VI.9.72 | 1,094 |
| `passage_plotinus_vi_9_73` | Plotinus, Enneades, Enn. VI.9.73 | 1,283 |
| `passage_plotinus_vi_9_74` | Plotinus, Enneades, Enn. VI.9.74 | 1,499 |
| `passage_plotinus_vi_9_75` | Plotinus, Enneades, Enn. VI.9.75 | 1,295 |
| `passage_plotinus_vi_9_76` | Plotinus, Enneades, Enn. VI.9.76 | 1,351 |
| `passage_plotinus_vi_9_77` | Plotinus, Enneades, Enn. VI.9.77 | 1,248 |
| `passage_plotinus_vi_9_78` | Plotinus, Enneades, Enn. VI.9.78 | 759 |
| `passage_plotinus_vi_9_79` | Plotinus, Enneades, Enn. VI.9.79 | 1,404 |
| `passage_plotinus_vi_9_8` | Plotinus, Enneades, Enn. VI.9.8 | 1,037 |
| `passage_plotinus_vi_9_80` | Plotinus, Enneades, Enn. VI.9.80 | 1,487 |
| `passage_plotinus_vi_9_81` | Plotinus, Enneades, Enn. VI.9.81 | 1,150 |
| `passage_plotinus_vi_9_82` | Plotinus, Enneades, Enn. VI.9.82 | 1,462 |
| `passage_plotinus_vi_9_83` | Plotinus, Enneades, Enn. VI.9.83 | 1,195 |
| `passage_plotinus_vi_9_84` | Plotinus, Enneades, Enn. VI.9.84 | 1,436 |
| `passage_plotinus_vi_9_85` | Plotinus, Enneades, Enn. VI.9.85 | 1,362 |
| `passage_plotinus_vi_9_86` | Plotinus, Enneades, Enn. VI.9.86 | 1,382 |
| `passage_plotinus_vi_9_87` | Plotinus, Enneades, Enn. VI.9.87 | 1,415 |
| `passage_plotinus_vi_9_88` | Plotinus, Enneades, Enn. VI.9.88 | 1,242 |
| `passage_plotinus_vi_9_89` | Plotinus, Enneades, Enn. VI.9.89 | 1,480 |
| `passage_plotinus_vi_9_9` | Plotinus, Enneades, Enn. VI.9.9 | 1,300 |
| `passage_plotinus_vi_9_90` | Plotinus, Enneades, Enn. VI.9.90 | 1,479 |
| `passage_plotinus_vi_9_91` | Plotinus, Enneades, Enn. VI.9.91 | 1,395 |
| `passage_plotinus_vi_9_92` | Plotinus, Enneades, Enn. VI.9.92 | 1,286 |
| `passage_plotinus_vi_9_93` | Plotinus, Enneades, Enn. VI.9.93 | 1,452 |
| `passage_plotinus_vi_9_94` | Plotinus, Enneades, Enn. VI.9.94 | 992 |
| `passage_plotinus_vi_9_95` | Plotinus, Enneades, Enn. VI.9.95 | 1,388 |
| `passage_plotinus_vi_9_96` | Plotinus, Enneades, Enn. VI.9.96 | 948 |
| `passage_plotinus_vi_9_97` | Plotinus, Enneades, Enn. VI.9.97 | 1,500 |
| `passage_plotinus_vi_9_98` | Plotinus, Enneades, Enn. VI.9.98 | 1,332 |
| `passage_plotinus_vi_9_99` | Plotinus, Enneades, Enn. VI.9.99 | 1,406 |

### Diogenes Laertius — Vitae Philosophorum (Lives of Eminent Philosophers)

- **Language:** Greek
- **Passages:** 1203
- **Characters:** 656,961
- **Canonical ID:** `urn:cts:greekLit:tlg0004.tlg001`

| node_id | label | chars |
|---------|-------|-------|
| `passage_dl_lives_1_1_22` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.1.22 | 514 |
| `passage_dl_lives_1_1_23` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.1.23 | 593 |
| `passage_dl_lives_1_1_24` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.1.24 | 648 |
| `passage_dl_lives_1_1_25` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.1.25 | 441 |
| `passage_dl_lives_1_1_26` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.1.26 | 528 |
| `passage_dl_lives_1_1_27` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.1.27 | 548 |
| `passage_dl_lives_1_1_28` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.1.28 | 519 |
| `passage_dl_lives_1_1_29` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.1.29 | 473 |
| `passage_dl_lives_1_1_30` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.1.30 | 506 |
| `passage_dl_lives_1_1_31` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.1.31 | 339 |
| `passage_dl_lives_1_1_32` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.1.32 | 696 |
| `passage_dl_lives_1_1_33` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.1.33 | 345 |
| `passage_dl_lives_1_1_34` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.1.34 | 408 |
| `passage_dl_lives_1_1_35` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.1.35 | 180 |
| `passage_dl_lives_1_1_36` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.1.36 | 620 |
| `passage_dl_lives_1_1_37` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.1.37 | 569 |
| `passage_dl_lives_1_1_38` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.1.38 | 544 |
| `passage_dl_lives_1_1_39` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.1.39 | 227 |
| `passage_dl_lives_1_1_40` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.1.40 | 651 |
| `passage_dl_lives_1_1_41` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.1.41 | 616 |
| `passage_dl_lives_1_1_42` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.1.42 | 531 |
| `passage_dl_lives_1_1_43` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.1.43 | 582 |
| `passage_dl_lives_1_1_44` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.1.44 | 610 |
| `passage_dl_lives_1_10_109` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.10.109 | 703 |
| `passage_dl_lives_1_10_110` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.10.110 | 825 |
| `passage_dl_lives_1_10_111` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.10.111 | 592 |
| `passage_dl_lives_1_10_112` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.10.112 | 710 |
| `passage_dl_lives_1_10_113` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.10.113 | 644 |
| `passage_dl_lives_1_10_114` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.10.114 | 652 |
| `passage_dl_lives_1_10_115` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.10.115 | 595 |
| `passage_dl_lives_1_11_116` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.11.116 | 571 |
| `passage_dl_lives_1_11_117` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.11.117 | 559 |
| `passage_dl_lives_1_11_118` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.11.118 | 613 |
| `passage_dl_lives_1_11_119` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.11.119 | 524 |
| `passage_dl_lives_1_11_120` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.11.120 | 81 |
| `passage_dl_lives_1_11_121` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.11.121 | 72 |
| `passage_dl_lives_1_11_122` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.11.122 | 965 |
| `passage_dl_lives_1_2_45` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.2.45 | 439 |
| `passage_dl_lives_1_2_46` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.2.46 | 470 |
| `passage_dl_lives_1_2_47` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.2.47 | 123 |
| `passage_dl_lives_1_2_48` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.2.48 | 360 |
| `passage_dl_lives_1_2_49` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.2.49 | 611 |
| `passage_dl_lives_1_2_50` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.2.50 | 380 |
| `passage_dl_lives_1_2_51` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.2.51 | 549 |
| `passage_dl_lives_1_2_52` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.2.52 | 79 |
| `passage_dl_lives_1_2_53` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.2.53 | 691 |
| `passage_dl_lives_1_2_54` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.2.54 | 554 |
| `passage_dl_lives_1_2_55` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.2.55 | 656 |
| `passage_dl_lives_1_2_56` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.2.56 | 565 |
| `passage_dl_lives_1_2_57` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.2.57 | 492 |
| `passage_dl_lives_1_2_58` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.2.58 | 570 |
| `passage_dl_lives_1_2_59` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.2.59 | 621 |
| `passage_dl_lives_1_2_60` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.2.60 | 441 |
| `passage_dl_lives_1_2_61` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.2.61 | 236 |
| `passage_dl_lives_1_2_62` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.2.62 | 405 |
| `passage_dl_lives_1_2_63` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.2.63 | 458 |
| `passage_dl_lives_1_2_64` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.2.64 | 842 |
| `passage_dl_lives_1_2_65` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.2.65 | 719 |
| `passage_dl_lives_1_2_66` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.2.66 | 671 |
| `passage_dl_lives_1_2_67` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.2.67 | 559 |
| `passage_dl_lives_1_3_68` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.3.68 | 682 |
| `passage_dl_lives_1_3_69` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.3.69 | 429 |
| `passage_dl_lives_1_3_70` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.3.70 | 601 |
| `passage_dl_lives_1_3_71` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.3.71 | 601 |
| `passage_dl_lives_1_3_72` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.3.72 | 771 |
| `passage_dl_lives_1_3_73` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.3.73 | 314 |
| `passage_dl_lives_1_4_74` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.4.74 | 613 |
| `passage_dl_lives_1_4_75` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.4.75 | 495 |
| `passage_dl_lives_1_4_76` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.4.76 | 587 |
| `passage_dl_lives_1_4_77` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.4.77 | 562 |
| `passage_dl_lives_1_4_78` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.4.78 | 360 |
| `passage_dl_lives_1_4_79` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.4.79 | 596 |
| `passage_dl_lives_1_4_80` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.4.80 | 674 |
| `passage_dl_lives_1_4_81` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.4.81 | 874 |
| `passage_dl_lives_1_5_82` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.5.82 | 631 |
| `passage_dl_lives_1_5_83` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.5.83 | 638 |
| `passage_dl_lives_1_5_84` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.5.84 | 543 |
| `passage_dl_lives_1_5_85` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.5.85 | 186 |
| `passage_dl_lives_1_5_86` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.5.86 | 658 |
| `passage_dl_lives_1_5_87` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.5.87 | 452 |
| `passage_dl_lives_1_5_88` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.5.88 | 546 |
| `passage_dl_lives_1_6_89` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.6.89 | 484 |
| `passage_dl_lives_1_6_90` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.6.90 | 186 |
| `passage_dl_lives_1_6_91` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.6.91 | 434 |
| `passage_dl_lives_1_6_92` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.6.92 | 650 |
| `passage_dl_lives_1_6_93` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.6.93 | 554 |
| `passage_dl_lives_1_7_100` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.7.100 | 705 |
| `passage_dl_lives_1_7_94` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.7.94 | 630 |
| `passage_dl_lives_1_7_95` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.7.95 | 505 |
| `passage_dl_lives_1_7_96` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.7.96 | 820 |
| `passage_dl_lives_1_7_97` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.7.97 | 482 |
| `passage_dl_lives_1_7_98` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.7.98 | 588 |
| `passage_dl_lives_1_7_99` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.7.99 | 621 |
| `passage_dl_lives_1_8_101` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.8.101 | 626 |
| `passage_dl_lives_1_8_102` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.8.102 | 614 |
| `passage_dl_lives_1_8_103` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.8.103 | 514 |
| `passage_dl_lives_1_8_104` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.8.104 | 788 |
| `passage_dl_lives_1_8_105` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.8.105 | 658 |
| `passage_dl_lives_1_9_106` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.9.106 | 505 |
| `passage_dl_lives_1_9_107` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.9.107 | 481 |
| `passage_dl_lives_1_9_108` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.9.108 | 638 |
| `passage_dl_lives_1_prol_1` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.prol.1 | 503 |
| `passage_dl_lives_1_prol_10` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.prol.1 | 521 |
| `passage_dl_lives_1_prol_11` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.prol.1 | 540 |
| `passage_dl_lives_1_prol_12` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.prol.1 | 529 |
| `passage_dl_lives_1_prol_13` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.prol.1 | 550 |
| `passage_dl_lives_1_prol_14` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.prol.1 | 508 |
| `passage_dl_lives_1_prol_15` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.prol.1 | 461 |
| `passage_dl_lives_1_prol_16` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.prol.1 | 564 |
| `passage_dl_lives_1_prol_17` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.prol.1 | 578 |
| `passage_dl_lives_1_prol_18` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.prol.1 | 467 |
| `passage_dl_lives_1_prol_19` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.prol.1 | 662 |
| `passage_dl_lives_1_prol_2` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.prol.2 | 608 |
| `passage_dl_lives_1_prol_20` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.prol.2 | 542 |
| `passage_dl_lives_1_prol_21` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.prol.2 | 607 |
| `passage_dl_lives_1_prol_3` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.prol.3 | 475 |
| `passage_dl_lives_1_prol_4` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.prol.4 | 434 |
| `passage_dl_lives_1_prol_5` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.prol.5 | 482 |
| `passage_dl_lives_1_prol_6` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.prol.6 | 649 |
| `passage_dl_lives_1_prol_7` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.prol.7 | 555 |
| `passage_dl_lives_1_prol_8` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.prol.8 | 532 |
| `passage_dl_lives_1_prol_9` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 1.prol.9 | 585 |
| `passage_dl_lives_10_1_1` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.1 | 477 |
| `passage_dl_lives_10_1_10` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.10 | 646 |
| `passage_dl_lives_10_1_100` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.100 | 530 |
| `passage_dl_lives_10_1_101` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.101 | 759 |
| `passage_dl_lives_10_1_102` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.102 | 575 |
| `passage_dl_lives_10_1_103` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.103 | 651 |
| `passage_dl_lives_10_1_104` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.104 | 583 |
| `passage_dl_lives_10_1_105` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.105 | 635 |
| `passage_dl_lives_10_1_106` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.106 | 604 |
| `passage_dl_lives_10_1_107` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.107 | 689 |
| `passage_dl_lives_10_1_108` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.108 | 560 |
| `passage_dl_lives_10_1_109` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.109 | 711 |
| `passage_dl_lives_10_1_11` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.11 | 574 |
| `passage_dl_lives_10_1_110` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.110 | 591 |
| `passage_dl_lives_10_1_111` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.111 | 540 |
| `passage_dl_lives_10_1_112` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.112 | 553 |
| `passage_dl_lives_10_1_113` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.113 | 628 |
| `passage_dl_lives_10_1_114` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.114 | 570 |
| `passage_dl_lives_10_1_115` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.115 | 669 |
| `passage_dl_lives_10_1_116` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.116 | 611 |
| `passage_dl_lives_10_1_117` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.117 | 538 |
| `passage_dl_lives_10_1_118` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.118 | 635 |
| `passage_dl_lives_10_1_119` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.119 | 412 |
| `passage_dl_lives_10_1_12` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.12 | 284 |
| `passage_dl_lives_10_1_120` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.120 | 1,232 |
| `passage_dl_lives_10_1_121` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.121 | 205 |
| `passage_dl_lives_10_1_122` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.122 | 610 |
| `passage_dl_lives_10_1_123` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.123 | 605 |
| `passage_dl_lives_10_1_124` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.124 | 588 |
| `passage_dl_lives_10_1_125` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.125 | 629 |
| `passage_dl_lives_10_1_126` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.126 | 509 |
| `passage_dl_lives_10_1_127` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.127 | 573 |
| `passage_dl_lives_10_1_128` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.128 | 614 |
| `passage_dl_lives_10_1_129` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.129 | 610 |
| `passage_dl_lives_10_1_13` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.13 | 540 |
| `passage_dl_lives_10_1_130` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.130 | 568 |
| `passage_dl_lives_10_1_131` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.131 | 600 |
| `passage_dl_lives_10_1_132` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.132 | 639 |
| `passage_dl_lives_10_1_133` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.133 | 592 |
| `passage_dl_lives_10_1_134` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.134 | 446 |
| `passage_dl_lives_10_1_135` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.135 | 593 |
| `passage_dl_lives_10_1_136` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.136 | 634 |
| `passage_dl_lives_10_1_137` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.137 | 529 |
| `passage_dl_lives_10_1_138` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.138 | 511 |
| `passage_dl_lives_10_1_139` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.139 | 605 |
| `passage_dl_lives_10_1_14` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.14 | 534 |
| `passage_dl_lives_10_1_140` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.140 | 481 |
| `passage_dl_lives_10_1_141` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.141 | 520 |
| `passage_dl_lives_10_1_142` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.142 | 676 |
| `passage_dl_lives_10_1_143` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.143 | 514 |
| `passage_dl_lives_10_1_144` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.144 | 589 |
| `passage_dl_lives_10_1_145` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.145 | 538 |
| `passage_dl_lives_10_1_146` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.146 | 463 |
| `passage_dl_lives_10_1_147` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.147 | 472 |
| `passage_dl_lives_10_1_148` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.148 | 686 |
| `passage_dl_lives_10_1_149` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.149 | 663 |
| `passage_dl_lives_10_1_15` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.15 | 567 |
| `passage_dl_lives_10_1_150` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.150 | 527 |
| `passage_dl_lives_10_1_151` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.151 | 527 |
| `passage_dl_lives_10_1_152` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.152 | 538 |
| `passage_dl_lives_10_1_153` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.153 | 390 |
| `passage_dl_lives_10_1_154` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.154 | 491 |
| `passage_dl_lives_10_1_16` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.16 | 313 |
| `passage_dl_lives_10_1_17` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.17 | 637 |
| `passage_dl_lives_10_1_18` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.18 | 576 |
| `passage_dl_lives_10_1_19` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.19 | 523 |
| `passage_dl_lives_10_1_2` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.2 | 621 |
| `passage_dl_lives_10_1_20` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.20 | 636 |
| `passage_dl_lives_10_1_21` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.21 | 486 |
| `passage_dl_lives_10_1_22` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.22 | 652 |
| `passage_dl_lives_10_1_23` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.23 | 609 |
| `passage_dl_lives_10_1_24` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.24 | 533 |
| `passage_dl_lives_10_1_25` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.25 | 602 |
| `passage_dl_lives_10_1_26` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.26 | 638 |
| `passage_dl_lives_10_1_27` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.27 | 544 |
| `passage_dl_lives_10_1_28` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.28 | 628 |
| `passage_dl_lives_10_1_29` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.29 | 494 |
| `passage_dl_lives_10_1_3` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.3 | 487 |
| `passage_dl_lives_10_1_30` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.30 | 580 |
| `passage_dl_lives_10_1_31` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.31 | 541 |
| `passage_dl_lives_10_1_32` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.32 | 669 |
| `passage_dl_lives_10_1_33` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.33 | 734 |
| `passage_dl_lives_10_1_34` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.34 | 642 |
| `passage_dl_lives_10_1_35` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.35 | 568 |
| `passage_dl_lives_10_1_36` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.36 | 579 |
| `passage_dl_lives_10_1_37` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.37 | 471 |
| `passage_dl_lives_10_1_38` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.38 | 543 |
| `passage_dl_lives_10_1_39` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.39 | 522 |
| `passage_dl_lives_10_1_4` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.4 | 650 |
| `passage_dl_lives_10_1_40` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.40 | 480 |
| `passage_dl_lives_10_1_41` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.41 | 579 |
| `passage_dl_lives_10_1_42` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.42 | 582 |
| `passage_dl_lives_10_1_43` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.43 | 522 |
| `passage_dl_lives_10_1_44` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.44 | 578 |
| `passage_dl_lives_10_1_45` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.45 | 495 |
| `passage_dl_lives_10_1_46` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.46 | 578 |
| `passage_dl_lives_10_1_47` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.47 | 663 |
| `passage_dl_lives_10_1_48` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.48 | 575 |
| `passage_dl_lives_10_1_49` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.49 | 450 |
| `passage_dl_lives_10_1_5` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.5 | 614 |
| `passage_dl_lives_10_1_50` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.50 | 705 |
| `passage_dl_lives_10_1_51` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.51 | 538 |
| `passage_dl_lives_10_1_52` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.52 | 570 |
| `passage_dl_lives_10_1_53` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.53 | 681 |
| `passage_dl_lives_10_1_54` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.54 | 599 |
| `passage_dl_lives_10_1_55` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.55 | 592 |
| `passage_dl_lives_10_1_56` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.56 | 574 |
| `passage_dl_lives_10_1_57` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.57 | 499 |
| `passage_dl_lives_10_1_58` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.58 | 536 |
| `passage_dl_lives_10_1_59` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.59 | 605 |
| `passage_dl_lives_10_1_6` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.6 | 704 |
| `passage_dl_lives_10_1_60` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.60 | 617 |
| `passage_dl_lives_10_1_61` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.61 | 534 |
| `passage_dl_lives_10_1_62` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.62 | 547 |
| `passage_dl_lives_10_1_63` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.63 | 597 |
| `passage_dl_lives_10_1_64` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.64 | 548 |
| `passage_dl_lives_10_1_65` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.65 | 522 |
| `passage_dl_lives_10_1_66` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.66 | 625 |
| `passage_dl_lives_10_1_67` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.67 | 480 |
| `passage_dl_lives_10_1_68` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.68 | 470 |
| `passage_dl_lives_10_1_69` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.69 | 570 |
| `passage_dl_lives_10_1_7` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.7 | 699 |
| `passage_dl_lives_10_1_70` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.70 | 430 |
| `passage_dl_lives_10_1_71` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.71 | 560 |
| `passage_dl_lives_10_1_72` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.72 | 585 |
| `passage_dl_lives_10_1_73` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.73 | 829 |
| `passage_dl_lives_10_1_74` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.74 | 564 |
| `passage_dl_lives_10_1_75` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.75 | 615 |
| `passage_dl_lives_10_1_76` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.76 | 559 |
| `passage_dl_lives_10_1_77` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.77 | 629 |
| `passage_dl_lives_10_1_78` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.78 | 472 |
| `passage_dl_lives_10_1_79` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.79 | 585 |
| `passage_dl_lives_10_1_8` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.8 | 633 |
| `passage_dl_lives_10_1_80` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.80 | 608 |
| `passage_dl_lives_10_1_81` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.81 | 551 |
| `passage_dl_lives_10_1_82` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.82 | 544 |
| `passage_dl_lives_10_1_83` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.83 | 799 |
| `passage_dl_lives_10_1_84` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.84 | 487 |
| `passage_dl_lives_10_1_85` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.85 | 549 |
| `passage_dl_lives_10_1_86` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.86 | 430 |
| `passage_dl_lives_10_1_87` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.87 | 682 |
| `passage_dl_lives_10_1_88` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.88 | 575 |
| `passage_dl_lives_10_1_89` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.89 | 574 |
| `passage_dl_lives_10_1_9` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.9 | 517 |
| `passage_dl_lives_10_1_90` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.90 | 579 |
| `passage_dl_lives_10_1_91` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.91 | 575 |
| `passage_dl_lives_10_1_92` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.92 | 570 |
| `passage_dl_lives_10_1_93` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.93 | 657 |
| `passage_dl_lives_10_1_94` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.94 | 522 |
| `passage_dl_lives_10_1_95` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.95 | 524 |
| `passage_dl_lives_10_1_96` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.96 | 610 |
| `passage_dl_lives_10_1_97` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.97 | 617 |
| `passage_dl_lives_10_1_98` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.98 | 559 |
| `passage_dl_lives_10_1_99` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 10.1.99 | 447 |
| `passage_dl_lives_2_1_1` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.1.1 | 532 |
| `passage_dl_lives_2_1_2` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.1.2 | 570 |
| `passage_dl_lives_2_10_106` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.10.106 | 646 |
| `passage_dl_lives_2_10_107` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.10.107 | 367 |
| `passage_dl_lives_2_10_108` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.10.108 | 407 |
| `passage_dl_lives_2_10_109` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.10.109 | 655 |
| `passage_dl_lives_2_10_110` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.10.110 | 445 |
| `passage_dl_lives_2_10_111` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.10.111 | 487 |
| `passage_dl_lives_2_10_112` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.10.112 | 391 |
| `passage_dl_lives_2_11_113` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.11.113 | 686 |
| `passage_dl_lives_2_11_114` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.11.114 | 565 |
| `passage_dl_lives_2_11_115` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.11.115 | 551 |
| `passage_dl_lives_2_11_116` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.11.116 | 697 |
| `passage_dl_lives_2_11_117` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.11.117 | 406 |
| `passage_dl_lives_2_11_118` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.11.118 | 362 |
| `passage_dl_lives_2_11_119` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.11.119 | 725 |
| `passage_dl_lives_2_11_120` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.11.120 | 444 |
| `passage_dl_lives_2_12_121` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.12.121 | 685 |
| `passage_dl_lives_2_13_122` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.13.122 | 537 |
| `passage_dl_lives_2_13_123` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.13.123 | 438 |
| `passage_dl_lives_2_13_124` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.13.124 | 122 |
| `passage_dl_lives_2_14_124` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.14.124 | 217 |
| `passage_dl_lives_2_15_124` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.15.124 | 430 |
| `passage_dl_lives_2_16_125` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.16.125 | 77 |
| `passage_dl_lives_2_17_125` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.17.125 | 459 |
| `passage_dl_lives_2_17_126` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.17.126 | 427 |
| `passage_dl_lives_2_17_127` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.17.127 | 541 |
| `passage_dl_lives_2_17_128` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.17.128 | 644 |
| `passage_dl_lives_2_17_129` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.17.129 | 609 |
| `passage_dl_lives_2_17_130` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.17.130 | 639 |
| `passage_dl_lives_2_17_131` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.17.131 | 558 |
| `passage_dl_lives_2_17_132` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.17.132 | 598 |
| `passage_dl_lives_2_17_133` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.17.133 | 430 |
| `passage_dl_lives_2_17_134` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.17.134 | 685 |
| `passage_dl_lives_2_17_135` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.17.135 | 580 |
| `passage_dl_lives_2_17_136` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.17.136 | 553 |
| `passage_dl_lives_2_17_137` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.17.137 | 643 |
| `passage_dl_lives_2_17_138` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.17.138 | 567 |
| `passage_dl_lives_2_17_139` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.17.139 | 587 |
| `passage_dl_lives_2_17_140` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.17.140 | 551 |
| `passage_dl_lives_2_17_141` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.17.141 | 416 |
| `passage_dl_lives_2_17_142` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.17.142 | 590 |
| `passage_dl_lives_2_17_143` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.17.143 | 562 |
| `passage_dl_lives_2_17_144` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.17.144 | 425 |
| `passage_dl_lives_2_2_3` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.2.3 | 508 |
| `passage_dl_lives_2_2_4` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.2.4 | 464 |
| `passage_dl_lives_2_2_5` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.2.5 | 588 |
| `passage_dl_lives_2_3_10` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.3.10 | 621 |
| `passage_dl_lives_2_3_11` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.3.11 | 506 |
| `passage_dl_lives_2_3_12` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.3.12 | 567 |
| `passage_dl_lives_2_3_13` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.3.13 | 710 |
| `passage_dl_lives_2_3_14` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.3.14 | 525 |
| `passage_dl_lives_2_3_15` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.3.15 | 260 |
| `passage_dl_lives_2_3_6` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.3.6 | 418 |
| `passage_dl_lives_2_3_7` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.3.7 | 666 |
| `passage_dl_lives_2_3_8` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.3.8 | 556 |
| `passage_dl_lives_2_3_9` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.3.9 | 607 |
| `passage_dl_lives_2_4_16` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.4.16 | 591 |
| `passage_dl_lives_2_4_17` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.4.17 | 660 |
| `passage_dl_lives_2_5_18` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.18 | 267 |
| `passage_dl_lives_2_5_19` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.19 | 489 |
| `passage_dl_lives_2_5_20` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.20 | 553 |
| `passage_dl_lives_2_5_21` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.21 | 440 |
| `passage_dl_lives_2_5_22` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.22 | 552 |
| `passage_dl_lives_2_5_23` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.23 | 568 |
| `passage_dl_lives_2_5_24` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.24 | 629 |
| `passage_dl_lives_2_5_25` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.25 | 387 |
| `passage_dl_lives_2_5_26` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.26 | 515 |
| `passage_dl_lives_2_5_27` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.27 | 390 |
| `passage_dl_lives_2_5_28` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.28 | 253 |
| `passage_dl_lives_2_5_29` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.29 | 569 |
| `passage_dl_lives_2_5_30` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.30 | 566 |
| `passage_dl_lives_2_5_31` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.31 | 582 |
| `passage_dl_lives_2_5_32` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.32 | 600 |
| `passage_dl_lives_2_5_33` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.33 | 523 |
| `passage_dl_lives_2_5_34` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.34 | 597 |
| `passage_dl_lives_2_5_35` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.35 | 500 |
| `passage_dl_lives_2_5_36` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.36 | 592 |
| `passage_dl_lives_2_5_37` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.37 | 626 |
| `passage_dl_lives_2_5_38` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.38 | 593 |
| `passage_dl_lives_2_5_39` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.39 | 551 |
| `passage_dl_lives_2_5_40` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.40 | 511 |
| `passage_dl_lives_2_5_41` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.41 | 587 |
| `passage_dl_lives_2_5_42` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.42 | 456 |
| `passage_dl_lives_2_5_43` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.43 | 571 |
| `passage_dl_lives_2_5_44` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.44 | 591 |
| `passage_dl_lives_2_5_45` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.45 | 622 |
| `passage_dl_lives_2_5_46` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.46 | 466 |
| `passage_dl_lives_2_5_47` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.5.47 | 614 |
| `passage_dl_lives_2_6_48` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.6.48 | 619 |
| `passage_dl_lives_2_6_49` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.6.49 | 609 |
| `passage_dl_lives_2_6_50` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.6.50 | 571 |
| `passage_dl_lives_2_6_51` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.6.51 | 648 |
| `passage_dl_lives_2_6_52` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.6.52 | 608 |
| `passage_dl_lives_2_6_53` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.6.53 | 589 |
| `passage_dl_lives_2_6_54` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.6.54 | 609 |
| `passage_dl_lives_2_6_55` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.6.55 | 508 |
| `passage_dl_lives_2_6_56` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.6.56 | 557 |
| `passage_dl_lives_2_6_57` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.6.57 | 607 |
| `passage_dl_lives_2_6_58` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.6.58 | 84 |
| `passage_dl_lives_2_6_59` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.6.59 | 529 |
| `passage_dl_lives_2_7_60` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.7.60 | 634 |
| `passage_dl_lives_2_7_61` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.7.61 | 567 |
| `passage_dl_lives_2_7_62` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.7.62 | 500 |
| `passage_dl_lives_2_7_63` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.7.63 | 590 |
| `passage_dl_lives_2_7_64` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.7.64 | 558 |
| `passage_dl_lives_2_8_100` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.100 | 534 |
| `passage_dl_lives_2_8_101` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.101 | 426 |
| `passage_dl_lives_2_8_102` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.102 | 861 |
| `passage_dl_lives_2_8_103` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.103 | 715 |
| `passage_dl_lives_2_8_104` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.104 | 740 |
| `passage_dl_lives_2_8_65` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.65 | 599 |
| `passage_dl_lives_2_8_66` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.66 | 568 |
| `passage_dl_lives_2_8_67` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.67 | 536 |
| `passage_dl_lives_2_8_68` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.68 | 497 |
| `passage_dl_lives_2_8_69` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.69 | 631 |
| `passage_dl_lives_2_8_70` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.70 | 544 |
| `passage_dl_lives_2_8_71` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.71 | 583 |
| `passage_dl_lives_2_8_72` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.72 | 586 |
| `passage_dl_lives_2_8_73` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.73 | 553 |
| `passage_dl_lives_2_8_74` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.74 | 582 |
| `passage_dl_lives_2_8_75` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.75 | 491 |
| `passage_dl_lives_2_8_76` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.76 | 543 |
| `passage_dl_lives_2_8_77` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.77 | 581 |
| `passage_dl_lives_2_8_78` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.78 | 435 |
| `passage_dl_lives_2_8_79` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.79 | 610 |
| `passage_dl_lives_2_8_80` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.80 | 510 |
| `passage_dl_lives_2_8_81` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.81 | 553 |
| `passage_dl_lives_2_8_82` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.82 | 453 |
| `passage_dl_lives_2_8_83` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.83 | 615 |
| `passage_dl_lives_2_8_84` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.84 | 651 |
| `passage_dl_lives_2_8_85` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.85 | 530 |
| `passage_dl_lives_2_8_86` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.86 | 510 |
| `passage_dl_lives_2_8_87` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.87 | 530 |
| `passage_dl_lives_2_8_88` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.88 | 474 |
| `passage_dl_lives_2_8_89` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.89 | 574 |
| `passage_dl_lives_2_8_90` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.90 | 680 |
| `passage_dl_lives_2_8_91` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.91 | 601 |
| `passage_dl_lives_2_8_92` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.92 | 531 |
| `passage_dl_lives_2_8_93` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.93 | 540 |
| `passage_dl_lives_2_8_94` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.94 | 582 |
| `passage_dl_lives_2_8_95` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.95 | 617 |
| `passage_dl_lives_2_8_96` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.96 | 572 |
| `passage_dl_lives_2_8_97` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.97 | 574 |
| `passage_dl_lives_2_8_98` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.98 | 618 |
| `passage_dl_lives_2_8_99` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.8.99 | 662 |
| `passage_dl_lives_2_9_105` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 2.9.105 | 797 |
| `passage_dl_lives_3_1_1` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.1 | 429 |
| `passage_dl_lives_3_1_10` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.10 | 352 |
| `passage_dl_lives_3_1_100` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.100 | 485 |
| `passage_dl_lives_3_1_101` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.101 | 500 |
| `passage_dl_lives_3_1_102` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.102 | 441 |
| `passage_dl_lives_3_1_103` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.103 | 558 |
| `passage_dl_lives_3_1_104` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.104 | 604 |
| `passage_dl_lives_3_1_105` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.105 | 698 |
| `passage_dl_lives_3_1_106` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.106 | 519 |
| `passage_dl_lives_3_1_107` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.107 | 605 |
| `passage_dl_lives_3_1_108` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.108 | 511 |
| `passage_dl_lives_3_1_109` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.109 | 577 |
| `passage_dl_lives_3_1_12` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.12 | 465 |
| `passage_dl_lives_3_1_13` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.13 | 557 |
| `passage_dl_lives_3_1_15` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.15 | 498 |
| `passage_dl_lives_3_1_16` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.16 | 10 |
| `passage_dl_lives_3_1_17` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.17 | 250 |
| `passage_dl_lives_3_1_18` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.18 | 531 |
| `passage_dl_lives_3_1_19` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.19 | 784 |
| `passage_dl_lives_3_1_2` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.2 | 616 |
| `passage_dl_lives_3_1_20` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.20 | 540 |
| `passage_dl_lives_3_1_21` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.21 | 557 |
| `passage_dl_lives_3_1_22` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.22 | 583 |
| `passage_dl_lives_3_1_23` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.23 | 495 |
| `passage_dl_lives_3_1_24` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.24 | 639 |
| `passage_dl_lives_3_1_25` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.25 | 631 |
| `passage_dl_lives_3_1_26` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.26 | 269 |
| `passage_dl_lives_3_1_27` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.27 | 52 |
| `passage_dl_lives_3_1_28` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.28 | 144 |
| `passage_dl_lives_3_1_29` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.29 | 273 |
| `passage_dl_lives_3_1_3` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.3 | 594 |
| `passage_dl_lives_3_1_30` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.30 | 21 |
| `passage_dl_lives_3_1_31` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.31 | 201 |
| `passage_dl_lives_3_1_32` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.32 | 43 |
| `passage_dl_lives_3_1_33` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.33 | 84 |
| `passage_dl_lives_3_1_34` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.34 | 520 |
| `passage_dl_lives_3_1_35` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.35 | 541 |
| `passage_dl_lives_3_1_36` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.36 | 516 |
| `passage_dl_lives_3_1_37` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.37 | 606 |
| `passage_dl_lives_3_1_38` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.38 | 495 |
| `passage_dl_lives_3_1_39` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.39 | 535 |
| `passage_dl_lives_3_1_4` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.4 | 538 |
| `passage_dl_lives_3_1_40` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.40 | 486 |
| `passage_dl_lives_3_1_41` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.41 | 544 |
| `passage_dl_lives_3_1_42` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.42 | 477 |
| `passage_dl_lives_3_1_43` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.43 | 239 |
| `passage_dl_lives_3_1_44` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.44 | 29 |
| `passage_dl_lives_3_1_45` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.45 | 82 |
| `passage_dl_lives_3_1_46` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.46 | 567 |
| `passage_dl_lives_3_1_47` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.47 | 510 |
| `passage_dl_lives_3_1_48` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.48 | 600 |
| `passage_dl_lives_3_1_49` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.49 | 478 |
| `passage_dl_lives_3_1_5` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.5 | 625 |
| `passage_dl_lives_3_1_50` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.50 | 586 |
| `passage_dl_lives_3_1_51` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.51 | 530 |
| `passage_dl_lives_3_1_52` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.52 | 604 |
| `passage_dl_lives_3_1_53` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.53 | 581 |
| `passage_dl_lives_3_1_54` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.54 | 674 |
| `passage_dl_lives_3_1_55` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.55 | 648 |
| `passage_dl_lives_3_1_56` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.56 | 654 |
| `passage_dl_lives_3_1_57` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.57 | 573 |
| `passage_dl_lives_3_1_58` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.58 | 555 |
| `passage_dl_lives_3_1_59` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.59 | 514 |
| `passage_dl_lives_3_1_6` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.6 | 594 |
| `passage_dl_lives_3_1_60` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.60 | 480 |
| `passage_dl_lives_3_1_61` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.61 | 388 |
| `passage_dl_lives_3_1_62` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.62 | 743 |
| `passage_dl_lives_3_1_63` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.63 | 561 |
| `passage_dl_lives_3_1_64` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.64 | 511 |
| `passage_dl_lives_3_1_65` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.65 | 502 |
| `passage_dl_lives_3_1_66` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.66 | 508 |
| `passage_dl_lives_3_1_67` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.67 | 385 |
| `passage_dl_lives_3_1_68` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.68 | 512 |
| `passage_dl_lives_3_1_69` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.69 | 516 |
| `passage_dl_lives_3_1_7` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.7 | 364 |
| `passage_dl_lives_3_1_70` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.70 | 520 |
| `passage_dl_lives_3_1_71` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.71 | 569 |
| `passage_dl_lives_3_1_72` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.72 | 541 |
| `passage_dl_lives_3_1_73` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.73 | 537 |
| `passage_dl_lives_3_1_74` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.74 | 541 |
| `passage_dl_lives_3_1_75` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.75 | 468 |
| `passage_dl_lives_3_1_76` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.76 | 469 |
| `passage_dl_lives_3_1_77` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.77 | 467 |
| `passage_dl_lives_3_1_78` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.78 | 542 |
| `passage_dl_lives_3_1_79` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.79 | 546 |
| `passage_dl_lives_3_1_8` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.8 | 521 |
| `passage_dl_lives_3_1_80` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.80 | 568 |
| `passage_dl_lives_3_1_81` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.81 | 584 |
| `passage_dl_lives_3_1_82` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.82 | 605 |
| `passage_dl_lives_3_1_83` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.83 | 712 |
| `passage_dl_lives_3_1_84` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.84 | 678 |
| `passage_dl_lives_3_1_85` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.85 | 521 |
| `passage_dl_lives_3_1_86` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.86 | 506 |
| `passage_dl_lives_3_1_87` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.87 | 610 |
| `passage_dl_lives_3_1_88` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.88 | 709 |
| `passage_dl_lives_3_1_89` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.89 | 574 |
| `passage_dl_lives_3_1_9` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.9 | 616 |
| `passage_dl_lives_3_1_90` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.90 | 587 |
| `passage_dl_lives_3_1_91` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.91 | 562 |
| `passage_dl_lives_3_1_92` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.92 | 757 |
| `passage_dl_lives_3_1_93` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.93 | 513 |
| `passage_dl_lives_3_1_94` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.94 | 569 |
| `passage_dl_lives_3_1_95` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.95 | 546 |
| `passage_dl_lives_3_1_96` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.96 | 665 |
| `passage_dl_lives_3_1_97` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.97 | 734 |
| `passage_dl_lives_3_1_98` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.98 | 656 |
| `passage_dl_lives_3_1_99` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 3.1.99 | 676 |
| `passage_dl_lives_4_1_1` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.1.1 | 626 |
| `passage_dl_lives_4_1_2` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.1.2 | 538 |
| `passage_dl_lives_4_1_3` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.1.3 | 441 |
| `passage_dl_lives_4_1_4` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.1.4 | 573 |
| `passage_dl_lives_4_1_5` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.1.5 | 704 |
| `passage_dl_lives_4_10_67` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.10.67 | 684 |
| `passage_dl_lives_4_2_10` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.2.10 | 469 |
| `passage_dl_lives_4_2_11` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.2.11 | 543 |
| `passage_dl_lives_4_2_12` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.2.12 | 668 |
| `passage_dl_lives_4_2_13` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.2.13 | 778 |
| `passage_dl_lives_4_2_14` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.2.14 | 640 |
| `passage_dl_lives_4_2_15` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.2.15 | 517 |
| `passage_dl_lives_4_2_6` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.2.6 | 519 |
| `passage_dl_lives_4_2_7` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.2.7 | 588 |
| `passage_dl_lives_4_2_8` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.2.8 | 645 |
| `passage_dl_lives_4_2_9` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.2.9 | 600 |
| `passage_dl_lives_4_3_16` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.3.16 | 684 |
| `passage_dl_lives_4_3_17` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.3.17 | 552 |
| `passage_dl_lives_4_3_18` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.3.18 | 660 |
| `passage_dl_lives_4_3_19` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.3.19 | 534 |
| `passage_dl_lives_4_3_20` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.3.20 | 292 |
| `passage_dl_lives_4_4_21` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.4.21 | 367 |
| `passage_dl_lives_4_4_22` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.4.22 | 615 |
| `passage_dl_lives_4_4_23` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.4.23 | 747 |
| `passage_dl_lives_4_5_24` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.5.24 | 582 |
| `passage_dl_lives_4_5_25` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.5.25 | 353 |
| `passage_dl_lives_4_5_26` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.5.26 | 264 |
| `passage_dl_lives_4_5_27` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.5.27 | 340 |
| `passage_dl_lives_4_6_28` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.6.28 | 550 |
| `passage_dl_lives_4_6_29` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.6.29 | 439 |
| `passage_dl_lives_4_6_30` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.6.30 | 354 |
| `passage_dl_lives_4_6_31` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.6.31 | 281 |
| `passage_dl_lives_4_6_32` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.6.32 | 566 |
| `passage_dl_lives_4_6_33` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.6.33 | 331 |
| `passage_dl_lives_4_6_34` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.6.34 | 572 |
| `passage_dl_lives_4_6_35` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.6.35 | 268 |
| `passage_dl_lives_4_6_36` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.6.36 | 520 |
| `passage_dl_lives_4_6_37` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.6.37 | 633 |
| `passage_dl_lives_4_6_38` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.6.38 | 624 |
| `passage_dl_lives_4_6_39` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.6.39 | 607 |
| `passage_dl_lives_4_6_40` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.6.40 | 521 |
| `passage_dl_lives_4_6_41` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.6.41 | 596 |
| `passage_dl_lives_4_6_42` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.6.42 | 536 |
| `passage_dl_lives_4_6_43` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.6.43 | 689 |
| `passage_dl_lives_4_6_44` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.6.44 | 706 |
| `passage_dl_lives_4_6_45` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.6.45 | 292 |
| `passage_dl_lives_4_7_46` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.7.46 | 585 |
| `passage_dl_lives_4_7_47` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.7.47 | 582 |
| `passage_dl_lives_4_7_48` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.7.48 | 581 |
| `passage_dl_lives_4_7_49` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.7.49 | 596 |
| `passage_dl_lives_4_7_50` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.7.50 | 634 |
| `passage_dl_lives_4_7_51` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.7.51 | 539 |
| `passage_dl_lives_4_7_52` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.7.52 | 480 |
| `passage_dl_lives_4_7_53` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.7.53 | 582 |
| `passage_dl_lives_4_7_54` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.7.54 | 621 |
| `passage_dl_lives_4_7_58` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.7.58 | 647 |
| `passage_dl_lives_4_8_59` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.8.59 | 615 |
| `passage_dl_lives_4_8_60` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.8.60 | 481 |
| `passage_dl_lives_4_8_61` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.8.61 | 235 |
| `passage_dl_lives_4_9_62` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.9.62 | 509 |
| `passage_dl_lives_4_9_63` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.9.63 | 509 |
| `passage_dl_lives_4_9_64` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.9.64 | 410 |
| `passage_dl_lives_4_9_65` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.9.65 | 365 |
| `passage_dl_lives_4_9_66` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 4.9.66 | 316 |
| `passage_dl_lives_5_1_1` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.1 | 494 |
| `passage_dl_lives_5_1_10` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.10 | 626 |
| `passage_dl_lives_5_1_11` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.11 | 358 |
| `passage_dl_lives_5_1_12` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.12 | 710 |
| `passage_dl_lives_5_1_13` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.13 | 573 |
| `passage_dl_lives_5_1_14` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.14 | 571 |
| `passage_dl_lives_5_1_15` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.15 | 609 |
| `passage_dl_lives_5_1_16` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.16 | 701 |
| `passage_dl_lives_5_1_17` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.17 | 566 |
| `passage_dl_lives_5_1_18` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.18 | 565 |
| `passage_dl_lives_5_1_19` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.19 | 658 |
| `passage_dl_lives_5_1_2` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.2 | 525 |
| `passage_dl_lives_5_1_20` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.20 | 609 |
| `passage_dl_lives_5_1_21` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.21 | 600 |
| `passage_dl_lives_5_1_22` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.22 | 662 |
| `passage_dl_lives_5_1_23` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.23 | 612 |
| `passage_dl_lives_5_1_24` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.24 | 719 |
| `passage_dl_lives_5_1_25` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.25 | 571 |
| `passage_dl_lives_5_1_26` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.26 | 594 |
| `passage_dl_lives_5_1_27` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.27 | 548 |
| `passage_dl_lives_5_1_28` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.28 | 652 |
| `passage_dl_lives_5_1_29` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.29 | 576 |
| `passage_dl_lives_5_1_3` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.3 | 556 |
| `passage_dl_lives_5_1_30` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.30 | 600 |
| `passage_dl_lives_5_1_31` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.31 | 583 |
| `passage_dl_lives_5_1_32` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.32 | 609 |
| `passage_dl_lives_5_1_33` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.33 | 574 |
| `passage_dl_lives_5_1_34` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.34 | 530 |
| `passage_dl_lives_5_1_35` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.35 | 569 |
| `passage_dl_lives_5_1_4` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.4 | 569 |
| `passage_dl_lives_5_1_5` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.5 | 547 |
| `passage_dl_lives_5_1_6` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.6 | 365 |
| `passage_dl_lives_5_1_8` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.8 | 43 |
| `passage_dl_lives_5_1_9` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.1.9 | 522 |
| `passage_dl_lives_5_2_36` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.2.36 | 582 |
| `passage_dl_lives_5_2_37` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.2.37 | 608 |
| `passage_dl_lives_5_2_38` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.2.38 | 589 |
| `passage_dl_lives_5_2_39` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.2.39 | 672 |
| `passage_dl_lives_5_2_40` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.2.40 | 436 |
| `passage_dl_lives_5_2_41` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.2.41 | 610 |
| `passage_dl_lives_5_2_42` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.2.42 | 655 |
| `passage_dl_lives_5_2_43` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.2.43 | 677 |
| `passage_dl_lives_5_2_44` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.2.44 | 602 |
| `passage_dl_lives_5_2_45` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.2.45 | 713 |
| `passage_dl_lives_5_2_46` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.2.46 | 717 |
| `passage_dl_lives_5_2_47` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.2.47 | 608 |
| `passage_dl_lives_5_2_48` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.2.48 | 616 |
| `passage_dl_lives_5_2_49` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.2.49 | 636 |
| `passage_dl_lives_5_2_50` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.2.50 | 606 |
| `passage_dl_lives_5_2_51` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.2.51 | 632 |
| `passage_dl_lives_5_2_52` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.2.52 | 603 |
| `passage_dl_lives_5_2_53` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.2.53 | 675 |
| `passage_dl_lives_5_2_54` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.2.54 | 674 |
| `passage_dl_lives_5_2_55` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.2.55 | 617 |
| `passage_dl_lives_5_2_56` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.2.56 | 609 |
| `passage_dl_lives_5_2_57` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.2.57 | 570 |
| `passage_dl_lives_5_3_58` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.3.58 | 454 |
| `passage_dl_lives_5_3_59` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.3.59 | 683 |
| `passage_dl_lives_5_3_60` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.3.60 | 342 |
| `passage_dl_lives_5_3_61` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.3.61 | 691 |
| `passage_dl_lives_5_3_62` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.3.62 | 527 |
| `passage_dl_lives_5_3_63` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.3.63 | 684 |
| `passage_dl_lives_5_3_64` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.3.64 | 603 |
| `passage_dl_lives_5_4_65` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.4.65 | 624 |
| `passage_dl_lives_5_4_66` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.4.66 | 654 |
| `passage_dl_lives_5_4_67` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.4.67 | 472 |
| `passage_dl_lives_5_4_68` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.4.68 | 463 |
| `passage_dl_lives_5_4_69` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.4.69 | 482 |
| `passage_dl_lives_5_4_70` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.4.70 | 638 |
| `passage_dl_lives_5_4_71` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.4.71 | 605 |
| `passage_dl_lives_5_4_72` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.4.72 | 749 |
| `passage_dl_lives_5_4_73` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.4.73 | 596 |
| `passage_dl_lives_5_4_74` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.4.74 | 657 |
| `passage_dl_lives_5_5_75` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.5.75 | 543 |
| `passage_dl_lives_5_5_76` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.5.76 | 568 |
| `passage_dl_lives_5_5_77` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.5.77 | 467 |
| `passage_dl_lives_5_5_78` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.5.78 | 545 |
| `passage_dl_lives_5_5_79` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.5.79 | 395 |
| `passage_dl_lives_5_5_80` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.5.80 | 489 |
| `passage_dl_lives_5_5_81` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.5.81 | 639 |
| `passage_dl_lives_5_5_82` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.5.82 | 688 |
| `passage_dl_lives_5_5_83` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.5.83 | 660 |
| `passage_dl_lives_5_5_84` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.5.84 | 488 |
| `passage_dl_lives_5_5_85` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.5.85 | 380 |
| `passage_dl_lives_5_6_86` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.6.86 | 596 |
| `passage_dl_lives_5_6_87` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.6.87 | 544 |
| `passage_dl_lives_5_6_88` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.6.88 | 560 |
| `passage_dl_lives_5_6_89` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.6.89 | 602 |
| `passage_dl_lives_5_6_90` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.6.90 | 308 |
| `passage_dl_lives_5_6_91` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.6.91 | 634 |
| `passage_dl_lives_5_6_92` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.6.92 | 430 |
| `passage_dl_lives_5_6_93` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.6.93 | 448 |
| `passage_dl_lives_5_6_94` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 5.6.94 | 625 |
| `passage_dl_lives_6_1_1` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.1.1 | 569 |
| `passage_dl_lives_6_1_10` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.1.10 | 512 |
| `passage_dl_lives_6_1_11` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.1.11 | 483 |
| `passage_dl_lives_6_1_12` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.1.12 | 508 |
| `passage_dl_lives_6_1_13` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.1.13 | 521 |
| `passage_dl_lives_6_1_14` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.1.14 | 298 |
| `passage_dl_lives_6_1_15` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.1.15 | 483 |
| `passage_dl_lives_6_1_16` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.1.16 | 625 |
| `passage_dl_lives_6_1_17` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.1.17 | 589 |
| `passage_dl_lives_6_1_18` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.1.18 | 648 |
| `passage_dl_lives_6_1_19` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.1.19 | 333 |
| `passage_dl_lives_6_1_2` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.1.2 | 612 |
| `passage_dl_lives_6_1_3` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.1.3 | 523 |
| `passage_dl_lives_6_1_4` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.1.4 | 622 |
| `passage_dl_lives_6_1_5` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.1.5 | 525 |
| `passage_dl_lives_6_1_6` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.1.6 | 567 |
| `passage_dl_lives_6_1_7` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.1.7 | 481 |
| `passage_dl_lives_6_1_8` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.1.8 | 574 |
| `passage_dl_lives_6_1_9` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.1.9 | 526 |
| `passage_dl_lives_6_2_20` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.20 | 635 |
| `passage_dl_lives_6_2_21` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.21 | 574 |
| `passage_dl_lives_6_2_22` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.22 | 489 |
| `passage_dl_lives_6_2_23` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.23 | 485 |
| `passage_dl_lives_6_2_24` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.24 | 553 |
| `passage_dl_lives_6_2_25` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.25 | 533 |
| `passage_dl_lives_6_2_26` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.26 | 607 |
| `passage_dl_lives_6_2_27` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.27 | 582 |
| `passage_dl_lives_6_2_28` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.28 | 549 |
| `passage_dl_lives_6_2_29` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.29 | 625 |
| `passage_dl_lives_6_2_30` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.30 | 506 |
| `passage_dl_lives_6_2_31` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.31 | 618 |
| `passage_dl_lives_6_2_32` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.32 | 572 |
| `passage_dl_lives_6_2_33` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.33 | 493 |
| `passage_dl_lives_6_2_34` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.34 | 559 |
| `passage_dl_lives_6_2_35` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.35 | 528 |
| `passage_dl_lives_6_2_36` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.36 | 575 |
| `passage_dl_lives_6_2_37` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.37 | 611 |
| `passage_dl_lives_6_2_38` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.38 | 520 |
| `passage_dl_lives_6_2_39` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.39 | 603 |
| `passage_dl_lives_6_2_40` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.40 | 579 |
| `passage_dl_lives_6_2_41` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.41 | 620 |
| `passage_dl_lives_6_2_42` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.42 | 608 |
| `passage_dl_lives_6_2_43` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.43 | 545 |
| `passage_dl_lives_6_2_44` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.44 | 571 |
| `passage_dl_lives_6_2_45` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.45 | 568 |
| `passage_dl_lives_6_2_46` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.46 | 561 |
| `passage_dl_lives_6_2_47` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.47 | 577 |
| `passage_dl_lives_6_2_48` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.48 | 627 |
| `passage_dl_lives_6_2_49` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.49 | 595 |
| `passage_dl_lives_6_2_50` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.50 | 450 |
| `passage_dl_lives_6_2_51` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.51 | 611 |
| `passage_dl_lives_6_2_52` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.52 | 415 |
| `passage_dl_lives_6_2_53` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.53 | 402 |
| `passage_dl_lives_6_2_54` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.54 | 628 |
| `passage_dl_lives_6_2_55` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.55 | 519 |
| `passage_dl_lives_6_2_56` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.56 | 532 |
| `passage_dl_lives_6_2_57` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.57 | 600 |
| `passage_dl_lives_6_2_58` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.58 | 570 |
| `passage_dl_lives_6_2_59` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.59 | 541 |
| `passage_dl_lives_6_2_60` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.60 | 585 |
| `passage_dl_lives_6_2_61` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.61 | 562 |
| `passage_dl_lives_6_2_62` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.62 | 554 |
| `passage_dl_lives_6_2_63` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.63 | 548 |
| `passage_dl_lives_6_2_64` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.64 | 566 |
| `passage_dl_lives_6_2_65` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.65 | 592 |
| `passage_dl_lives_6_2_66` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.66 | 496 |
| `passage_dl_lives_6_2_67` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.67 | 481 |
| `passage_dl_lives_6_2_68` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.68 | 611 |
| `passage_dl_lives_6_2_69` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.69 | 576 |
| `passage_dl_lives_6_2_70` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.70 | 708 |
| `passage_dl_lives_6_2_71` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.71 | 620 |
| `passage_dl_lives_6_2_72` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.72 | 637 |
| `passage_dl_lives_6_2_73` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.73 | 678 |
| `passage_dl_lives_6_2_74` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.74 | 613 |
| `passage_dl_lives_6_2_75` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.75 | 637 |
| `passage_dl_lives_6_2_76` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.76 | 503 |
| `passage_dl_lives_6_2_77` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.77 | 539 |
| `passage_dl_lives_6_2_78` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.78 | 355 |
| `passage_dl_lives_6_2_79` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.79 | 435 |
| `passage_dl_lives_6_2_80` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.80 | 665 |
| `passage_dl_lives_6_2_81` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.2.81 | 494 |
| `passage_dl_lives_6_3_82` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.3.82 | 551 |
| `passage_dl_lives_6_3_83` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.3.83 | 296 |
| `passage_dl_lives_6_4_84` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.4.84 | 587 |
| `passage_dl_lives_6_5_85` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.5.85 | 179 |
| `passage_dl_lives_6_5_86` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.5.86 | 209 |
| `passage_dl_lives_6_5_87` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.5.87 | 540 |
| `passage_dl_lives_6_5_88` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.5.88 | 586 |
| `passage_dl_lives_6_5_89` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.5.89 | 626 |
| `passage_dl_lives_6_5_90` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.5.90 | 504 |
| `passage_dl_lives_6_5_91` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.5.91 | 506 |
| `passage_dl_lives_6_5_92` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.5.92 | 461 |
| `passage_dl_lives_6_5_93` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.5.93 | 306 |
| `passage_dl_lives_6_6_94` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.6.94 | 565 |
| `passage_dl_lives_6_6_95` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.6.95 | 606 |
| `passage_dl_lives_6_7_96` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.7.96 | 616 |
| `passage_dl_lives_6_7_97` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.7.97 | 524 |
| `passage_dl_lives_6_7_98` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.7.98 | 459 |
| `passage_dl_lives_6_8_100` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.8.100 | 274 |
| `passage_dl_lives_6_8_101` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.8.101 | 473 |
| `passage_dl_lives_6_8_99` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.8.99 | 497 |
| `passage_dl_lives_6_9_102` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.9.102 | 446 |
| `passage_dl_lives_6_9_103` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.9.103 | 555 |
| `passage_dl_lives_6_9_104` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.9.104 | 809 |
| `passage_dl_lives_6_9_105` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 6.9.105 | 370 |
| `passage_dl_lives_7_1_1` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.1 | 497 |
| `passage_dl_lives_7_1_10` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.10 | 581 |
| `passage_dl_lives_7_1_100` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.100 | 567 |
| `passage_dl_lives_7_1_101` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.101 | 513 |
| `passage_dl_lives_7_1_102` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.102 | 511 |
| `passage_dl_lives_7_1_103` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.103 | 555 |
| `passage_dl_lives_7_1_104` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.104 | 590 |
| `passage_dl_lives_7_1_105` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.105 | 612 |
| `passage_dl_lives_7_1_106` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.106 | 526 |
| `passage_dl_lives_7_1_107` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.107 | 554 |
| `passage_dl_lives_7_1_108` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.108 | 565 |
| `passage_dl_lives_7_1_109` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.109 | 615 |
| `passage_dl_lives_7_1_11` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.11 | 647 |
| `passage_dl_lives_7_1_110` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.110 | 602 |
| `passage_dl_lives_7_1_111` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.111 | 531 |
| `passage_dl_lives_7_1_112` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.112 | 506 |
| `passage_dl_lives_7_1_113` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.113 | 614 |
| `passage_dl_lives_7_1_114` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.114 | 431 |
| `passage_dl_lives_7_1_115` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.115 | 403 |
| `passage_dl_lives_7_1_116` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.116 | 555 |
| `passage_dl_lives_7_1_117` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.117 | 545 |
| `passage_dl_lives_7_1_118` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.118 | 618 |
| `passage_dl_lives_7_1_119` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.119 | 609 |
| `passage_dl_lives_7_1_12` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.12 | 542 |
| `passage_dl_lives_7_1_120` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.120 | 558 |
| `passage_dl_lives_7_1_121` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.121 | 651 |
| `passage_dl_lives_7_1_122` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.122 | 591 |
| `passage_dl_lives_7_1_123` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.123 | 591 |
| `passage_dl_lives_7_1_124` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.124 | 570 |
| `passage_dl_lives_7_1_125` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.125 | 519 |
| `passage_dl_lives_7_1_126` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.126 | 652 |
| `passage_dl_lives_7_1_127` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.127 | 669 |
| `passage_dl_lives_7_1_128` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.128 | 582 |
| `passage_dl_lives_7_1_129` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.129 | 575 |
| `passage_dl_lives_7_1_13` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.13 | 534 |
| `passage_dl_lives_7_1_130` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.130 | 646 |
| `passage_dl_lives_7_1_131` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.131 | 547 |
| `passage_dl_lives_7_1_132` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.132 | 556 |
| `passage_dl_lives_7_1_133` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.133 | 688 |
| `passage_dl_lives_7_1_134` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.134 | 650 |
| `passage_dl_lives_7_1_135` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.135 | 536 |
| `passage_dl_lives_7_1_136` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.136 | 534 |
| `passage_dl_lives_7_1_137` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.137 | 660 |
| `passage_dl_lives_7_1_138` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.138 | 636 |
| `passage_dl_lives_7_1_139` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.139 | 612 |
| `passage_dl_lives_7_1_14` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.14 | 702 |
| `passage_dl_lives_7_1_140` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.140 | 702 |
| `passage_dl_lives_7_1_141` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.141 | 493 |
| `passage_dl_lives_7_1_142` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.142 | 665 |
| `passage_dl_lives_7_1_143` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.143 | 559 |
| `passage_dl_lives_7_1_144` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.144 | 650 |
| `passage_dl_lives_7_1_145` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.145 | 579 |
| `passage_dl_lives_7_1_146` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.146 | 611 |
| `passage_dl_lives_7_1_147` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.147 | 714 |
| `passage_dl_lives_7_1_148` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.148 | 531 |
| `passage_dl_lives_7_1_149` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.149 | 664 |
| `passage_dl_lives_7_1_15` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.15 | 408 |
| `passage_dl_lives_7_1_150` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.150 | 699 |
| `passage_dl_lives_7_1_151` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.151 | 494 |
| `passage_dl_lives_7_1_152` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.152 | 692 |
| `passage_dl_lives_7_1_153` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.153 | 534 |
| `passage_dl_lives_7_1_154` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.154 | 534 |
| `passage_dl_lives_7_1_155` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.155 | 535 |
| `passage_dl_lives_7_1_156` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.156 | 551 |
| `passage_dl_lives_7_1_157` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.157 | 663 |
| `passage_dl_lives_7_1_158` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.158 | 550 |
| `passage_dl_lives_7_1_159` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.159 | 572 |
| `passage_dl_lives_7_1_16` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.16 | 492 |
| `passage_dl_lives_7_1_160` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.160 | 151 |
| `passage_dl_lives_7_1_17` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.17 | 650 |
| `passage_dl_lives_7_1_18` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.18 | 633 |
| `passage_dl_lives_7_1_19` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.19 | 742 |
| `passage_dl_lives_7_1_2` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.2 | 670 |
| `passage_dl_lives_7_1_20` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.20 | 648 |
| `passage_dl_lives_7_1_21` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.21 | 530 |
| `passage_dl_lives_7_1_22` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.22 | 668 |
| `passage_dl_lives_7_1_23` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.23 | 715 |
| `passage_dl_lives_7_1_24` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.24 | 584 |
| `passage_dl_lives_7_1_25` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.25 | 579 |
| `passage_dl_lives_7_1_26` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.26 | 528 |
| `passage_dl_lives_7_1_27` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.27 | 338 |
| `passage_dl_lives_7_1_28` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.28 | 557 |
| `passage_dl_lives_7_1_29` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.29 | 169 |
| `passage_dl_lives_7_1_3` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.3 | 514 |
| `passage_dl_lives_7_1_30` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.30 | 130 |
| `passage_dl_lives_7_1_31` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.31 | 341 |
| `passage_dl_lives_7_1_32` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.32 | 586 |
| `passage_dl_lives_7_1_33` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.33 | 541 |
| `passage_dl_lives_7_1_34` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.34 | 532 |
| `passage_dl_lives_7_1_35` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.35 | 575 |
| `passage_dl_lives_7_1_36` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.36 | 606 |
| `passage_dl_lives_7_1_37` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.37 | 506 |
| `passage_dl_lives_7_1_38` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.38 | 470 |
| `passage_dl_lives_7_1_39` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.39 | 467 |
| `passage_dl_lives_7_1_4` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.4 | 723 |
| `passage_dl_lives_7_1_40` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.40 | 696 |
| `passage_dl_lives_7_1_41` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.41 | 594 |
| `passage_dl_lives_7_1_42` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.42 | 590 |
| `passage_dl_lives_7_1_43` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.43 | 594 |
| `passage_dl_lives_7_1_44` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.44 | 497 |
| `passage_dl_lives_7_1_45` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.45 | 540 |
| `passage_dl_lives_7_1_46` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.46 | 539 |
| `passage_dl_lives_7_1_47` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.47 | 491 |
| `passage_dl_lives_7_1_48` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.48 | 637 |
| `passage_dl_lives_7_1_5` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.5 | 772 |
| `passage_dl_lives_7_1_50` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.50 | 487 |
| `passage_dl_lives_7_1_51` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.51 | 661 |
| `passage_dl_lives_7_1_52` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.52 | 554 |
| `passage_dl_lives_7_1_53` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.53 | 601 |
| `passage_dl_lives_7_1_54` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.54 | 541 |
| `passage_dl_lives_7_1_55` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.55 | 519 |
| `passage_dl_lives_7_1_56` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.56 | 543 |
| `passage_dl_lives_7_1_57` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.57 | 611 |
| `passage_dl_lives_7_1_58` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.58 | 526 |
| `passage_dl_lives_7_1_59` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.59 | 521 |
| `passage_dl_lives_7_1_6` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.6 | 684 |
| `passage_dl_lives_7_1_60` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.60 | 605 |
| `passage_dl_lives_7_1_61` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.61 | 733 |
| `passage_dl_lives_7_1_62` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.62 | 611 |
| `passage_dl_lives_7_1_63` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.63 | 635 |
| `passage_dl_lives_7_1_64` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.64 | 660 |
| `passage_dl_lives_7_1_65` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.65 | 504 |
| `passage_dl_lives_7_1_66` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.66 | 572 |
| `passage_dl_lives_7_1_67` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.67 | 293 |
| `passage_dl_lives_7_1_68` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.68 | 513 |
| `passage_dl_lives_7_1_69` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.69 | 602 |
| `passage_dl_lives_7_1_7` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.7 | 669 |
| `passage_dl_lives_7_1_70` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.70 | 517 |
| `passage_dl_lives_7_1_71` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.71 | 547 |
| `passage_dl_lives_7_1_72` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.72 | 603 |
| `passage_dl_lives_7_1_73` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.73 | 621 |
| `passage_dl_lives_7_1_74` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.74 | 648 |
| `passage_dl_lives_7_1_75` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.75 | 706 |
| `passage_dl_lives_7_1_76` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.76 | 608 |
| `passage_dl_lives_7_1_77` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.77 | 528 |
| `passage_dl_lives_7_1_78` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.78 | 645 |
| `passage_dl_lives_7_1_79` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.79 | 613 |
| `passage_dl_lives_7_1_8` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.8 | 469 |
| `passage_dl_lives_7_1_80` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.80 | 717 |
| `passage_dl_lives_7_1_81` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.81 | 698 |
| `passage_dl_lives_7_1_82` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.82 | 521 |
| `passage_dl_lives_7_1_83` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.83 | 498 |
| `passage_dl_lives_7_1_84` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.84 | 547 |
| `passage_dl_lives_7_1_85` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.85 | 551 |
| `passage_dl_lives_7_1_86` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.86 | 635 |
| `passage_dl_lives_7_1_87` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.87 | 414 |
| `passage_dl_lives_7_1_88` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.88 | 575 |
| `passage_dl_lives_7_1_89` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.89 | 577 |
| `passage_dl_lives_7_1_9` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.9 | 516 |
| `passage_dl_lives_7_1_90` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.90 | 530 |
| `passage_dl_lives_7_1_91` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.91 | 556 |
| `passage_dl_lives_7_1_92` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.92 | 583 |
| `passage_dl_lives_7_1_93` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.93 | 690 |
| `passage_dl_lives_7_1_94` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.94 | 574 |
| `passage_dl_lives_7_1_95` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.95 | 531 |
| `passage_dl_lives_7_1_96` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.96 | 522 |
| `passage_dl_lives_7_1_97` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.97 | 605 |
| `passage_dl_lives_7_1_98` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.98 | 475 |
| `passage_dl_lives_7_1_99` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.1.99 | 514 |
| `passage_dl_lives_7_2_160` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.2.160 | 475 |
| `passage_dl_lives_7_2_161` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.2.161 | 443 |
| `passage_dl_lives_7_2_162` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.2.162 | 450 |
| `passage_dl_lives_7_2_163` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.2.163 | 540 |
| `passage_dl_lives_7_2_164` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.2.164 | 309 |
| `passage_dl_lives_7_3_165` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.3.165 | 628 |
| `passage_dl_lives_7_3_166` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.3.166 | 305 |
| `passage_dl_lives_7_4_166` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.4.166 | 297 |
| `passage_dl_lives_7_4_167` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.4.167 | 590 |
| `passage_dl_lives_7_5_168` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.5.168 | 563 |
| `passage_dl_lives_7_5_169` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.5.169 | 636 |
| `passage_dl_lives_7_5_170` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.5.170 | 510 |
| `passage_dl_lives_7_5_171` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.5.171 | 603 |
| `passage_dl_lives_7_5_172` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.5.172 | 497 |
| `passage_dl_lives_7_5_173` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.5.173 | 789 |
| `passage_dl_lives_7_5_174` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.5.174 | 678 |
| `passage_dl_lives_7_5_175` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.5.175 | 685 |
| `passage_dl_lives_7_5_176` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.5.176 | 416 |
| `passage_dl_lives_7_6_177` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.6.177 | 734 |
| `passage_dl_lives_7_6_178` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.6.178 | 600 |
| `passage_dl_lives_7_7_179` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.7.179 | 546 |
| `passage_dl_lives_7_7_180` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.7.180 | 661 |
| `passage_dl_lives_7_7_181` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.7.181 | 546 |
| `passage_dl_lives_7_7_182` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.7.182 | 590 |
| `passage_dl_lives_7_7_183` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.7.183 | 418 |
| `passage_dl_lives_7_7_184` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.7.184 | 464 |
| `passage_dl_lives_7_7_185` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.7.185 | 614 |
| `passage_dl_lives_7_7_186` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.7.186 | 631 |
| `passage_dl_lives_7_7_187` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.7.187 | 618 |
| `passage_dl_lives_7_7_188` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.7.188 | 599 |
| `passage_dl_lives_7_7_189` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.7.189 | 650 |
| `passage_dl_lives_7_7_190` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.7.190 | 638 |
| `passage_dl_lives_7_7_191` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.7.191 | 376 |
| `passage_dl_lives_7_7_192` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.7.192 | 811 |
| `passage_dl_lives_7_7_193` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.7.193 | 584 |
| `passage_dl_lives_7_7_194` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.7.194 | 624 |
| `passage_dl_lives_7_7_195` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.7.195 | 592 |
| `passage_dl_lives_7_7_196` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.7.196 | 613 |
| `passage_dl_lives_7_7_197` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.7.197 | 647 |
| `passage_dl_lives_7_7_198` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.7.198 | 722 |
| `passage_dl_lives_7_7_199` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.7.199 | 565 |
| `passage_dl_lives_7_7_200` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.7.200 | 472 |
| `passage_dl_lives_7_7_201` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.7.201 | 513 |
| `passage_dl_lives_7_7_202` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 7.7.202 | 569 |
| `passage_dl_lives_8_1_1` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.1 | 470 |
| `passage_dl_lives_8_1_10` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.10 | 710 |
| `passage_dl_lives_8_1_11` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.11 | 541 |
| `passage_dl_lives_8_1_12` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.12 | 582 |
| `passage_dl_lives_8_1_13` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.13 | 686 |
| `passage_dl_lives_8_1_14` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.14 | 544 |
| `passage_dl_lives_8_1_15` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.15 | 567 |
| `passage_dl_lives_8_1_16` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.16 | 391 |
| `passage_dl_lives_8_1_17` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.17 | 569 |
| `passage_dl_lives_8_1_18` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.18 | 586 |
| `passage_dl_lives_8_1_19` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.19 | 488 |
| `passage_dl_lives_8_1_2` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.2 | 560 |
| `passage_dl_lives_8_1_20` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.20 | 522 |
| `passage_dl_lives_8_1_21` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.21 | 539 |
| `passage_dl_lives_8_1_22` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.22 | 384 |
| `passage_dl_lives_8_1_23` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.23 | 526 |
| `passage_dl_lives_8_1_24` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.24 | 400 |
| `passage_dl_lives_8_1_25` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.25 | 528 |
| `passage_dl_lives_8_1_26` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.26 | 626 |
| `passage_dl_lives_8_1_27` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.27 | 564 |
| `passage_dl_lives_8_1_28` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.28 | 661 |
| `passage_dl_lives_8_1_29` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.29 | 695 |
| `passage_dl_lives_8_1_3` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.3 | 623 |
| `passage_dl_lives_8_1_30` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.30 | 541 |
| `passage_dl_lives_8_1_31` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.31 | 544 |
| `passage_dl_lives_8_1_32` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.32 | 545 |
| `passage_dl_lives_8_1_33` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.33 | 675 |
| `passage_dl_lives_8_1_34` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.34 | 787 |
| `passage_dl_lives_8_1_35` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.35 | 538 |
| `passage_dl_lives_8_1_36` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.36 | 340 |
| `passage_dl_lives_8_1_37` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.37 | 135 |
| `passage_dl_lives_8_1_38` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.38 | 38 |
| `passage_dl_lives_8_1_39` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.39 | 647 |
| `passage_dl_lives_8_1_4` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.4 | 619 |
| `passage_dl_lives_8_1_40` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.40 | 718 |
| `passage_dl_lives_8_1_41` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.41 | 655 |
| `passage_dl_lives_8_1_42` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.42 | 567 |
| `passage_dl_lives_8_1_43` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.43 | 551 |
| `passage_dl_lives_8_1_44` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.44 | 220 |
| `passage_dl_lives_8_1_45` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.45 | 136 |
| `passage_dl_lives_8_1_46` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.46 | 584 |
| `passage_dl_lives_8_1_47` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.47 | 604 |
| `passage_dl_lives_8_1_48` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.48 | 344 |
| `passage_dl_lives_8_1_49` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.49 | 488 |
| `passage_dl_lives_8_1_5` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.5 | 591 |
| `passage_dl_lives_8_1_50` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.50 | 518 |
| `passage_dl_lives_8_1_6` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.6 | 527 |
| `passage_dl_lives_8_1_7` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.7 | 530 |
| `passage_dl_lives_8_1_8` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.8 | 630 |
| `passage_dl_lives_8_1_9` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.1.9 | 536 |
| `passage_dl_lives_8_2_51` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.2.51 | 499 |
| `passage_dl_lives_8_2_52` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.2.52 | 255 |
| `passage_dl_lives_8_2_53` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.2.53 | 472 |
| `passage_dl_lives_8_2_54` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.2.54 | 354 |
| `passage_dl_lives_8_2_55` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.2.55 | 542 |
| `passage_dl_lives_8_2_56` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.2.56 | 444 |
| `passage_dl_lives_8_2_57` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.2.57 | 512 |
| `passage_dl_lives_8_2_58` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.2.58 | 497 |
| `passage_dl_lives_8_2_59` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.2.59 | 575 |
| `passage_dl_lives_8_2_60` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.2.60 | 499 |
| `passage_dl_lives_8_2_61` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.2.61 | 233 |
| `passage_dl_lives_8_2_63` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.2.63 | 557 |
| `passage_dl_lives_8_2_64` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.2.64 | 652 |
| `passage_dl_lives_8_2_65` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.2.65 | 340 |
| `passage_dl_lives_8_2_66` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.2.66 | 517 |
| `passage_dl_lives_8_2_67` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.2.67 | 480 |
| `passage_dl_lives_8_2_68` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.2.68 | 649 |
| `passage_dl_lives_8_2_69` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.2.69 | 497 |
| `passage_dl_lives_8_2_70` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.2.70 | 623 |
| `passage_dl_lives_8_2_71` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.2.71 | 554 |
| `passage_dl_lives_8_2_72` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.2.72 | 651 |
| `passage_dl_lives_8_2_73` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.2.73 | 619 |
| `passage_dl_lives_8_2_74` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.2.74 | 476 |
| `passage_dl_lives_8_2_75` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.2.75 | 9 |
| `passage_dl_lives_8_2_76` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.2.76 | 327 |
| `passage_dl_lives_8_2_77` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.2.77 | 341 |
| `passage_dl_lives_8_3_78` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.3.78 | 444 |
| `passage_dl_lives_8_4_79` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.4.79 | 453 |
| `passage_dl_lives_8_4_80` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.4.80 | 487 |
| `passage_dl_lives_8_4_81` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.4.81 | 567 |
| `passage_dl_lives_8_4_82` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.4.82 | 542 |
| `passage_dl_lives_8_4_83` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.4.83 | 295 |
| `passage_dl_lives_8_5_83` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.5.83 | 627 |
| `passage_dl_lives_8_6_84` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.6.84 | 323 |
| `passage_dl_lives_8_7_84` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.7.84 | 171 |
| `passage_dl_lives_8_7_85` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.7.85 | 739 |
| `passage_dl_lives_8_8_86` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.8.86 | 530 |
| `passage_dl_lives_8_8_87` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.8.87 | 572 |
| `passage_dl_lives_8_8_88` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.8.88 | 511 |
| `passage_dl_lives_8_8_89` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.8.89 | 512 |
| `passage_dl_lives_8_8_90` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.8.90 | 752 |
| `passage_dl_lives_8_8_91` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 8.8.91 | 243 |
| `passage_dl_lives_9_1_1` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.1.1 | 482 |
| `passage_dl_lives_9_1_10` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.1.10 | 648 |
| `passage_dl_lives_9_1_11` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.1.11 | 542 |
| `passage_dl_lives_9_1_12` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.1.12 | 477 |
| `passage_dl_lives_9_1_13` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.1.13 | 613 |
| `passage_dl_lives_9_1_14` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.1.14 | 695 |
| `passage_dl_lives_9_1_15` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.1.15 | 569 |
| `passage_dl_lives_9_1_16` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.1.16 | 181 |
| `passage_dl_lives_9_1_17` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.1.17 | 303 |
| `passage_dl_lives_9_1_2` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.1.2 | 506 |
| `passage_dl_lives_9_1_3` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.1.3 | 579 |
| `passage_dl_lives_9_1_4` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.1.4 | 423 |
| `passage_dl_lives_9_1_5` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.1.5 | 532 |
| `passage_dl_lives_9_1_6` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.1.6 | 503 |
| `passage_dl_lives_9_1_7` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.1.7 | 645 |
| `passage_dl_lives_9_1_8` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.1.8 | 584 |
| `passage_dl_lives_9_1_9` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.1.9 | 662 |
| `passage_dl_lives_9_10_58` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.10.58 | 510 |
| `passage_dl_lives_9_10_59` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.10.59 | 471 |
| `passage_dl_lives_9_10_60` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.10.60 | 413 |
| `passage_dl_lives_9_11_100` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.100 | 427 |
| `passage_dl_lives_9_11_101` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.101 | 632 |
| `passage_dl_lives_9_11_102` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.102 | 501 |
| `passage_dl_lives_9_11_103` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.103 | 559 |
| `passage_dl_lives_9_11_104` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.104 | 480 |
| `passage_dl_lives_9_11_105` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.105 | 499 |
| `passage_dl_lives_9_11_106` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.106 | 503 |
| `passage_dl_lives_9_11_107` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.107 | 567 |
| `passage_dl_lives_9_11_108` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.108 | 592 |
| `passage_dl_lives_9_11_61` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.61 | 604 |
| `passage_dl_lives_9_11_62` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.62 | 600 |
| `passage_dl_lives_9_11_63` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.63 | 590 |
| `passage_dl_lives_9_11_64` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.64 | 686 |
| `passage_dl_lives_9_11_65` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.65 | 125 |
| `passage_dl_lives_9_11_66` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.66 | 608 |
| `passage_dl_lives_9_11_67` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.67 | 511 |
| `passage_dl_lives_9_11_68` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.68 | 488 |
| `passage_dl_lives_9_11_69` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.69 | 573 |
| `passage_dl_lives_9_11_70` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.70 | 609 |
| `passage_dl_lives_9_11_71` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.71 | 414 |
| `passage_dl_lives_9_11_72` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.72 | 485 |
| `passage_dl_lives_9_11_73` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.73 | 227 |
| `passage_dl_lives_9_11_74` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.74 | 535 |
| `passage_dl_lives_9_11_75` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.75 | 486 |
| `passage_dl_lives_9_11_76` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.76 | 604 |
| `passage_dl_lives_9_11_77` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.77 | 548 |
| `passage_dl_lives_9_11_78` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.78 | 543 |
| `passage_dl_lives_9_11_79` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.79 | 605 |
| `passage_dl_lives_9_11_80` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.80 | 507 |
| `passage_dl_lives_9_11_81` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.81 | 459 |
| `passage_dl_lives_9_11_82` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.82 | 522 |
| `passage_dl_lives_9_11_83` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.83 | 594 |
| `passage_dl_lives_9_11_84` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.84 | 565 |
| `passage_dl_lives_9_11_85` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.85 | 516 |
| `passage_dl_lives_9_11_86` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.86 | 506 |
| `passage_dl_lives_9_11_87` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.87 | 554 |
| `passage_dl_lives_9_11_88` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.88 | 596 |
| `passage_dl_lives_9_11_89` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.89 | 522 |
| `passage_dl_lives_9_11_90` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.90 | 601 |
| `passage_dl_lives_9_11_91` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.91 | 608 |
| `passage_dl_lives_9_11_92` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.92 | 671 |
| `passage_dl_lives_9_11_93` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.93 | 459 |
| `passage_dl_lives_9_11_94` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.94 | 618 |
| `passage_dl_lives_9_11_95` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.95 | 441 |
| `passage_dl_lives_9_11_96` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.96 | 552 |
| `passage_dl_lives_9_11_97` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.97 | 440 |
| `passage_dl_lives_9_11_98` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.98 | 612 |
| `passage_dl_lives_9_11_99` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.11.99 | 640 |
| `passage_dl_lives_9_12_109` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.12.109 | 507 |
| `passage_dl_lives_9_12_110` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.12.110 | 600 |
| `passage_dl_lives_9_12_111` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.12.111 | 576 |
| `passage_dl_lives_9_12_112` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.12.112 | 592 |
| `passage_dl_lives_9_12_113` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.12.113 | 468 |
| `passage_dl_lives_9_12_114` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.12.114 | 642 |
| `passage_dl_lives_9_12_115` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.12.115 | 609 |
| `passage_dl_lives_9_12_116` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.12.116 | 517 |
| `passage_dl_lives_9_2_18` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.2.18 | 586 |
| `passage_dl_lives_9_2_19` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.2.19 | 398 |
| `passage_dl_lives_9_2_20` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.2.20 | 788 |
| `passage_dl_lives_9_3_21` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.3.21 | 577 |
| `passage_dl_lives_9_3_22` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.3.22 | 498 |
| `passage_dl_lives_9_3_23` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.3.23 | 549 |
| `passage_dl_lives_9_4_24` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.4.24 | 614 |
| `passage_dl_lives_9_5_25` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.5.25 | 490 |
| `passage_dl_lives_9_5_26` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.5.26 | 512 |
| `passage_dl_lives_9_5_27` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.5.27 | 546 |
| `passage_dl_lives_9_5_28` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.5.28 | 381 |
| `passage_dl_lives_9_5_29` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.5.29 | 629 |
| `passage_dl_lives_9_6_30` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.6.30 | 581 |
| `passage_dl_lives_9_6_31` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.6.31 | 652 |
| `passage_dl_lives_9_6_32` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.6.32 | 598 |
| `passage_dl_lives_9_6_33` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.6.33 | 655 |
| `passage_dl_lives_9_7_34` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.7.34 | 567 |
| `passage_dl_lives_9_7_35` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.7.35 | 616 |
| `passage_dl_lives_9_7_36` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.7.36 | 545 |
| `passage_dl_lives_9_7_37` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.7.37 | 653 |
| `passage_dl_lives_9_7_38` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.7.38 | 561 |
| `passage_dl_lives_9_7_39` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.7.39 | 641 |
| `passage_dl_lives_9_7_40` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.7.40 | 640 |
| `passage_dl_lives_9_7_41` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.7.41 | 589 |
| `passage_dl_lives_9_7_42` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.7.42 | 548 |
| `passage_dl_lives_9_7_43` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.7.43 | 583 |
| `passage_dl_lives_9_7_44` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.7.44 | 622 |
| `passage_dl_lives_9_7_45` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.7.45 | 538 |
| `passage_dl_lives_9_7_46` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.7.46 | 603 |
| `passage_dl_lives_9_7_47` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.7.47 | 623 |
| `passage_dl_lives_9_7_48` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.7.48 | 573 |
| `passage_dl_lives_9_7_49` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.7.49 | 734 |
| `passage_dl_lives_9_8_50` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.8.50 | 444 |
| `passage_dl_lives_9_8_51` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.8.51 | 533 |
| `passage_dl_lives_9_8_52` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.8.52 | 465 |
| `passage_dl_lives_9_8_53` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.8.53 | 602 |
| `passage_dl_lives_9_8_54` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.8.54 | 511 |
| `passage_dl_lives_9_8_55` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.8.55 | 544 |
| `passage_dl_lives_9_8_56` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.8.56 | 462 |
| `passage_dl_lives_9_9_57` | Diogenes Laertius, Vitae Philosophorum (Lives of Eminent Philosophers), 9.9.57 | 742 |

### Justin Martyr — Dialogus cum Tryphone

- **Language:** Greek
- **Passages:** 750
- **Characters:** 341,077
- **Canonical ID:** `urn:cts:greekLit:tlg0645.tlg003`

| node_id | label | chars |
|---------|-------|-------|
| `passage_just_tryph_1_1` | Justin Martyr, Dialogus cum Tryphone, 1_1 | 251 |
| `passage_just_tryph_1_2` | Justin Martyr, Dialogus cum Tryphone, 1_2 | 504 |
| `passage_just_tryph_1_3` | Justin Martyr, Dialogus cum Tryphone, 1_3 | 598 |
| `passage_just_tryph_1_4` | Justin Martyr, Dialogus cum Tryphone, 1_4 | 442 |
| `passage_just_tryph_1_5` | Justin Martyr, Dialogus cum Tryphone, 1_5 | 538 |
| `passage_just_tryph_1_6` | Justin Martyr, Dialogus cum Tryphone, 1_6 | 131 |
| `passage_just_tryph_10_1` | Justin Martyr, Dialogus cum Tryphone, 10_1 | 561 |
| `passage_just_tryph_10_2` | Justin Martyr, Dialogus cum Tryphone, 10_2 | 328 |
| `passage_just_tryph_10_3` | Justin Martyr, Dialogus cum Tryphone, 10_3 | 584 |
| `passage_just_tryph_10_4` | Justin Martyr, Dialogus cum Tryphone, 10_4 | 368 |
| `passage_just_tryph_100_1` | Justin Martyr, Dialogus cum Tryphone, 100_1 | 607 |
| `passage_just_tryph_100_2` | Justin Martyr, Dialogus cum Tryphone, 100_2 | 341 |
| `passage_just_tryph_100_3` | Justin Martyr, Dialogus cum Tryphone, 100_3 | 618 |
| `passage_just_tryph_100_4` | Justin Martyr, Dialogus cum Tryphone, 100_4 | 829 |
| `passage_just_tryph_100_5` | Justin Martyr, Dialogus cum Tryphone, 100_5 | 456 |
| `passage_just_tryph_100_6` | Justin Martyr, Dialogus cum Tryphone, 100_6 | 260 |
| `passage_just_tryph_101_1` | Justin Martyr, Dialogus cum Tryphone, 101_1 | 560 |
| `passage_just_tryph_101_2` | Justin Martyr, Dialogus cum Tryphone, 101_2 | 547 |
| `passage_just_tryph_101_3` | Justin Martyr, Dialogus cum Tryphone, 101_3 | 655 |
| `passage_just_tryph_102_1` | Justin Martyr, Dialogus cum Tryphone, 102_1 | 533 |
| `passage_just_tryph_102_2` | Justin Martyr, Dialogus cum Tryphone, 102_2 | 399 |
| `passage_just_tryph_102_3` | Justin Martyr, Dialogus cum Tryphone, 102_3 | 345 |
| `passage_just_tryph_102_4` | Justin Martyr, Dialogus cum Tryphone, 102_4 | 560 |
| `passage_just_tryph_102_5` | Justin Martyr, Dialogus cum Tryphone, 102_5 | 741 |
| `passage_just_tryph_102_6` | Justin Martyr, Dialogus cum Tryphone, 102_6 | 424 |
| `passage_just_tryph_102_7` | Justin Martyr, Dialogus cum Tryphone, 102_7 | 432 |
| `passage_just_tryph_103_1` | Justin Martyr, Dialogus cum Tryphone, 103_1 | 614 |
| `passage_just_tryph_103_2` | Justin Martyr, Dialogus cum Tryphone, 103_2 | 638 |
| `passage_just_tryph_103_3` | Justin Martyr, Dialogus cum Tryphone, 103_3 | 826 |
| `passage_just_tryph_103_4` | Justin Martyr, Dialogus cum Tryphone, 103_4 | 303 |
| `passage_just_tryph_103_5` | Justin Martyr, Dialogus cum Tryphone, 103_5 | 466 |
| `passage_just_tryph_103_6` | Justin Martyr, Dialogus cum Tryphone, 103_6 | 516 |
| `passage_just_tryph_103_7` | Justin Martyr, Dialogus cum Tryphone, 103_7 | 253 |
| `passage_just_tryph_103_8` | Justin Martyr, Dialogus cum Tryphone, 103_8 | 597 |
| `passage_just_tryph_103_9` | Justin Martyr, Dialogus cum Tryphone, 103_9 | 208 |
| `passage_just_tryph_104_1` | Justin Martyr, Dialogus cum Tryphone, 104_1 | 653 |
| `passage_just_tryph_104_2` | Justin Martyr, Dialogus cum Tryphone, 104_2 | 98 |
| `passage_just_tryph_105_1` | Justin Martyr, Dialogus cum Tryphone, 105_1 | 571 |
| `passage_just_tryph_105_2` | Justin Martyr, Dialogus cum Tryphone, 105_2 | 368 |
| `passage_just_tryph_105_3` | Justin Martyr, Dialogus cum Tryphone, 105_3 | 298 |
| `passage_just_tryph_105_4` | Justin Martyr, Dialogus cum Tryphone, 105_4 | 327 |
| `passage_just_tryph_105_5` | Justin Martyr, Dialogus cum Tryphone, 105_5 | 351 |
| `passage_just_tryph_105_6` | Justin Martyr, Dialogus cum Tryphone, 105_6 | 306 |
| `passage_just_tryph_106_1` | Justin Martyr, Dialogus cum Tryphone, 106_1 | 885 |
| `passage_just_tryph_106_2` | Justin Martyr, Dialogus cum Tryphone, 106_2 | 228 |
| `passage_just_tryph_106_3` | Justin Martyr, Dialogus cum Tryphone, 106_3 | 545 |
| `passage_just_tryph_106_4` | Justin Martyr, Dialogus cum Tryphone, 106_4 | 483 |
| `passage_just_tryph_107_1` | Justin Martyr, Dialogus cum Tryphone, 107_1 | 460 |
| `passage_just_tryph_107_2` | Justin Martyr, Dialogus cum Tryphone, 107_2 | 728 |
| `passage_just_tryph_107_3` | Justin Martyr, Dialogus cum Tryphone, 107_3 | 452 |
| `passage_just_tryph_107_4` | Justin Martyr, Dialogus cum Tryphone, 107_4 | 345 |
| `passage_just_tryph_108_1` | Justin Martyr, Dialogus cum Tryphone, 108_1 | 368 |
| `passage_just_tryph_108_2` | Justin Martyr, Dialogus cum Tryphone, 108_2 | 743 |
| `passage_just_tryph_108_3` | Justin Martyr, Dialogus cum Tryphone, 108_3 | 353 |
| `passage_just_tryph_109_1` | Justin Martyr, Dialogus cum Tryphone, 109_1 | 249 |
| `passage_just_tryph_109_2` | Justin Martyr, Dialogus cum Tryphone, 109_2 | 632 |
| `passage_just_tryph_109_3` | Justin Martyr, Dialogus cum Tryphone, 109_3 | 542 |
| `passage_just_tryph_11_1` | Justin Martyr, Dialogus cum Tryphone, 11_1 | 523 |
| `passage_just_tryph_11_2` | Justin Martyr, Dialogus cum Tryphone, 11_2 | 523 |
| `passage_just_tryph_11_3` | Justin Martyr, Dialogus cum Tryphone, 11_3 | 604 |
| `passage_just_tryph_11_4` | Justin Martyr, Dialogus cum Tryphone, 11_4 | 518 |
| `passage_just_tryph_11_5` | Justin Martyr, Dialogus cum Tryphone, 11_5 | 392 |
| `passage_just_tryph_110_1` | Justin Martyr, Dialogus cum Tryphone, 110_1 | 357 |
| `passage_just_tryph_110_2` | Justin Martyr, Dialogus cum Tryphone, 110_2 | 806 |
| `passage_just_tryph_110_3` | Justin Martyr, Dialogus cum Tryphone, 110_3 | 529 |
| `passage_just_tryph_110_4` | Justin Martyr, Dialogus cum Tryphone, 110_4 | 717 |
| `passage_just_tryph_110_5` | Justin Martyr, Dialogus cum Tryphone, 110_5 | 327 |
| `passage_just_tryph_110_6` | Justin Martyr, Dialogus cum Tryphone, 110_6 | 470 |
| `passage_just_tryph_111_1` | Justin Martyr, Dialogus cum Tryphone, 111_1 | 481 |
| `passage_just_tryph_111_2` | Justin Martyr, Dialogus cum Tryphone, 111_2 | 494 |
| `passage_just_tryph_111_3` | Justin Martyr, Dialogus cum Tryphone, 111_3 | 514 |
| `passage_just_tryph_111_4` | Justin Martyr, Dialogus cum Tryphone, 111_4 | 620 |
| `passage_just_tryph_112_1` | Justin Martyr, Dialogus cum Tryphone, 112_1 | 461 |
| `passage_just_tryph_112_2` | Justin Martyr, Dialogus cum Tryphone, 112_2 | 458 |
| `passage_just_tryph_112_3` | Justin Martyr, Dialogus cum Tryphone, 112_3 | 403 |
| `passage_just_tryph_112_4` | Justin Martyr, Dialogus cum Tryphone, 112_4 | 728 |
| `passage_just_tryph_112_5` | Justin Martyr, Dialogus cum Tryphone, 112_5 | 331 |
| `passage_just_tryph_113_1` | Justin Martyr, Dialogus cum Tryphone, 113_1 | 442 |
| `passage_just_tryph_113_2` | Justin Martyr, Dialogus cum Tryphone, 113_2 | 245 |
| `passage_just_tryph_113_3` | Justin Martyr, Dialogus cum Tryphone, 113_3 | 480 |
| `passage_just_tryph_113_4` | Justin Martyr, Dialogus cum Tryphone, 113_4 | 494 |
| `passage_just_tryph_113_5` | Justin Martyr, Dialogus cum Tryphone, 113_5 | 302 |
| `passage_just_tryph_113_6` | Justin Martyr, Dialogus cum Tryphone, 113_6 | 488 |
| `passage_just_tryph_113_7` | Justin Martyr, Dialogus cum Tryphone, 113_7 | 394 |
| `passage_just_tryph_114_1` | Justin Martyr, Dialogus cum Tryphone, 114_1 | 433 |
| `passage_just_tryph_114_2` | Justin Martyr, Dialogus cum Tryphone, 114_2 | 486 |
| `passage_just_tryph_114_3` | Justin Martyr, Dialogus cum Tryphone, 114_3 | 373 |
| `passage_just_tryph_114_4` | Justin Martyr, Dialogus cum Tryphone, 114_4 | 778 |
| `passage_just_tryph_114_5` | Justin Martyr, Dialogus cum Tryphone, 114_5 | 435 |
| `passage_just_tryph_115_1` | Justin Martyr, Dialogus cum Tryphone, 115_1 | 425 |
| `passage_just_tryph_115_2` | Justin Martyr, Dialogus cum Tryphone, 115_2 | 504 |
| `passage_just_tryph_115_3` | Justin Martyr, Dialogus cum Tryphone, 115_3 | 527 |
| `passage_just_tryph_115_4` | Justin Martyr, Dialogus cum Tryphone, 115_4 | 389 |
| `passage_just_tryph_115_5` | Justin Martyr, Dialogus cum Tryphone, 115_5 | 310 |
| `passage_just_tryph_115_6` | Justin Martyr, Dialogus cum Tryphone, 115_6 | 498 |
| `passage_just_tryph_116_1` | Justin Martyr, Dialogus cum Tryphone, 116_1 | 674 |
| `passage_just_tryph_116_2` | Justin Martyr, Dialogus cum Tryphone, 116_2 | 410 |
| `passage_just_tryph_116_3` | Justin Martyr, Dialogus cum Tryphone, 116_3 | 847 |
| `passage_just_tryph_117_1` | Justin Martyr, Dialogus cum Tryphone, 117_1 | 515 |
| `passage_just_tryph_117_2` | Justin Martyr, Dialogus cum Tryphone, 117_2 | 425 |
| `passage_just_tryph_117_3` | Justin Martyr, Dialogus cum Tryphone, 117_3 | 609 |
| `passage_just_tryph_117_4` | Justin Martyr, Dialogus cum Tryphone, 117_4 | 455 |
| `passage_just_tryph_117_5` | Justin Martyr, Dialogus cum Tryphone, 117_5 | 475 |
| `passage_just_tryph_118_1` | Justin Martyr, Dialogus cum Tryphone, 118_1 | 730 |
| `passage_just_tryph_118_2` | Justin Martyr, Dialogus cum Tryphone, 118_2 | 654 |
| `passage_just_tryph_118_3` | Justin Martyr, Dialogus cum Tryphone, 118_3 | 401 |
| `passage_just_tryph_118_4` | Justin Martyr, Dialogus cum Tryphone, 118_4 | 390 |
| `passage_just_tryph_118_5` | Justin Martyr, Dialogus cum Tryphone, 118_5 | 121 |
| `passage_just_tryph_119_1` | Justin Martyr, Dialogus cum Tryphone, 119_1 | 195 |
| `passage_just_tryph_119_2` | Justin Martyr, Dialogus cum Tryphone, 119_2 | 803 |
| `passage_just_tryph_119_3` | Justin Martyr, Dialogus cum Tryphone, 119_3 | 454 |
| `passage_just_tryph_119_4` | Justin Martyr, Dialogus cum Tryphone, 119_4 | 636 |
| `passage_just_tryph_119_5` | Justin Martyr, Dialogus cum Tryphone, 119_5 | 486 |
| `passage_just_tryph_119_6` | Justin Martyr, Dialogus cum Tryphone, 119_6 | 488 |
| `passage_just_tryph_12_1` | Justin Martyr, Dialogus cum Tryphone, 12_1 | 378 |
| `passage_just_tryph_12_2` | Justin Martyr, Dialogus cum Tryphone, 12_2 | 435 |
| `passage_just_tryph_12_3` | Justin Martyr, Dialogus cum Tryphone, 12_3 | 541 |
| `passage_just_tryph_120_1` | Justin Martyr, Dialogus cum Tryphone, 120_1 | 432 |
| `passage_just_tryph_120_2` | Justin Martyr, Dialogus cum Tryphone, 120_2 | 668 |
| `passage_just_tryph_120_3` | Justin Martyr, Dialogus cum Tryphone, 120_3 | 478 |
| `passage_just_tryph_120_4` | Justin Martyr, Dialogus cum Tryphone, 120_4 | 450 |
| `passage_just_tryph_120_5` | Justin Martyr, Dialogus cum Tryphone, 120_5 | 829 |
| `passage_just_tryph_120_6` | Justin Martyr, Dialogus cum Tryphone, 120_6 | 636 |
| `passage_just_tryph_121_1` | Justin Martyr, Dialogus cum Tryphone, 121_1 | 445 |
| `passage_just_tryph_121_2` | Justin Martyr, Dialogus cum Tryphone, 121_2 | 701 |
| `passage_just_tryph_121_3` | Justin Martyr, Dialogus cum Tryphone, 121_3 | 549 |
| `passage_just_tryph_121_4` | Justin Martyr, Dialogus cum Tryphone, 121_4 | 363 |
| `passage_just_tryph_122_1` | Justin Martyr, Dialogus cum Tryphone, 122_1 | 524 |
| `passage_just_tryph_122_2` | Justin Martyr, Dialogus cum Tryphone, 122_2 | 273 |
| `passage_just_tryph_122_3` | Justin Martyr, Dialogus cum Tryphone, 122_3 | 393 |
| `passage_just_tryph_122_4` | Justin Martyr, Dialogus cum Tryphone, 122_4 | 168 |
| `passage_just_tryph_122_5` | Justin Martyr, Dialogus cum Tryphone, 122_5 | 548 |
| `passage_just_tryph_122_6` | Justin Martyr, Dialogus cum Tryphone, 122_6 | 271 |
| `passage_just_tryph_123_1` | Justin Martyr, Dialogus cum Tryphone, 123_1 | 510 |
| `passage_just_tryph_123_2` | Justin Martyr, Dialogus cum Tryphone, 123_2 | 292 |
| `passage_just_tryph_123_3` | Justin Martyr, Dialogus cum Tryphone, 123_3 | 403 |
| `passage_just_tryph_123_4` | Justin Martyr, Dialogus cum Tryphone, 123_4 | 607 |
| `passage_just_tryph_123_5` | Justin Martyr, Dialogus cum Tryphone, 123_5 | 389 |
| `passage_just_tryph_123_6` | Justin Martyr, Dialogus cum Tryphone, 123_6 | 479 |
| `passage_just_tryph_123_7` | Justin Martyr, Dialogus cum Tryphone, 123_7 | 399 |
| `passage_just_tryph_123_8` | Justin Martyr, Dialogus cum Tryphone, 123_8 | 653 |
| `passage_just_tryph_123_9` | Justin Martyr, Dialogus cum Tryphone, 123_9 | 355 |
| `passage_just_tryph_124_1` | Justin Martyr, Dialogus cum Tryphone, 124_1 | 329 |
| `passage_just_tryph_124_2` | Justin Martyr, Dialogus cum Tryphone, 124_2 | 591 |
| `passage_just_tryph_124_3` | Justin Martyr, Dialogus cum Tryphone, 124_3 | 308 |
| `passage_just_tryph_124_4` | Justin Martyr, Dialogus cum Tryphone, 124_4 | 656 |
| `passage_just_tryph_125_1` | Justin Martyr, Dialogus cum Tryphone, 125_1 | 519 |
| `passage_just_tryph_125_2` | Justin Martyr, Dialogus cum Tryphone, 125_2 | 415 |
| `passage_just_tryph_125_3` | Justin Martyr, Dialogus cum Tryphone, 125_3 | 373 |
| `passage_just_tryph_125_4` | Justin Martyr, Dialogus cum Tryphone, 125_4 | 553 |
| `passage_just_tryph_125_5` | Justin Martyr, Dialogus cum Tryphone, 125_5 | 678 |
| `passage_just_tryph_126_1` | Justin Martyr, Dialogus cum Tryphone, 126_1 | 645 |
| `passage_just_tryph_126_2` | Justin Martyr, Dialogus cum Tryphone, 126_2 | 419 |
| `passage_just_tryph_126_3` | Justin Martyr, Dialogus cum Tryphone, 126_3 | 296 |
| `passage_just_tryph_126_4` | Justin Martyr, Dialogus cum Tryphone, 126_4 | 583 |
| `passage_just_tryph_126_5` | Justin Martyr, Dialogus cum Tryphone, 126_5 | 534 |
| `passage_just_tryph_126_6` | Justin Martyr, Dialogus cum Tryphone, 126_6 | 647 |
| `passage_just_tryph_127_1` | Justin Martyr, Dialogus cum Tryphone, 127_1 | 449 |
| `passage_just_tryph_127_2` | Justin Martyr, Dialogus cum Tryphone, 127_2 | 379 |
| `passage_just_tryph_127_3` | Justin Martyr, Dialogus cum Tryphone, 127_3 | 467 |
| `passage_just_tryph_127_4` | Justin Martyr, Dialogus cum Tryphone, 127_4 | 421 |
| `passage_just_tryph_127_5` | Justin Martyr, Dialogus cum Tryphone, 127_5 | 516 |
| `passage_just_tryph_128_1` | Justin Martyr, Dialogus cum Tryphone, 128_1 | 391 |
| `passage_just_tryph_128_2` | Justin Martyr, Dialogus cum Tryphone, 128_2 | 583 |
| `passage_just_tryph_128_3` | Justin Martyr, Dialogus cum Tryphone, 128_3 | 388 |
| `passage_just_tryph_128_4` | Justin Martyr, Dialogus cum Tryphone, 128_4 | 761 |
| `passage_just_tryph_129_1` | Justin Martyr, Dialogus cum Tryphone, 129_1 | 418 |
| `passage_just_tryph_129_2` | Justin Martyr, Dialogus cum Tryphone, 129_2 | 292 |
| `passage_just_tryph_129_3` | Justin Martyr, Dialogus cum Tryphone, 129_3 | 375 |
| `passage_just_tryph_129_4` | Justin Martyr, Dialogus cum Tryphone, 129_4 | 263 |
| `passage_just_tryph_13_1` | Justin Martyr, Dialogus cum Tryphone, 13_1 | 490 |
| `passage_just_tryph_13_2` | Justin Martyr, Dialogus cum Tryphone, 13_2 | 478 |
| `passage_just_tryph_13_3` | Justin Martyr, Dialogus cum Tryphone, 13_3 | 377 |
| `passage_just_tryph_13_4` | Justin Martyr, Dialogus cum Tryphone, 13_4 | 387 |
| `passage_just_tryph_13_5` | Justin Martyr, Dialogus cum Tryphone, 13_5 | 428 |
| `passage_just_tryph_13_6` | Justin Martyr, Dialogus cum Tryphone, 13_6 | 430 |
| `passage_just_tryph_13_7` | Justin Martyr, Dialogus cum Tryphone, 13_7 | 398 |
| `passage_just_tryph_13_8` | Justin Martyr, Dialogus cum Tryphone, 13_8 | 394 |
| `passage_just_tryph_13_9` | Justin Martyr, Dialogus cum Tryphone, 13_9 | 347 |
| `passage_just_tryph_130_1` | Justin Martyr, Dialogus cum Tryphone, 130_1 | 592 |
| `passage_just_tryph_130_2` | Justin Martyr, Dialogus cum Tryphone, 130_2 | 461 |
| `passage_just_tryph_130_3` | Justin Martyr, Dialogus cum Tryphone, 130_3 | 598 |
| `passage_just_tryph_130_4` | Justin Martyr, Dialogus cum Tryphone, 130_4 | 413 |
| `passage_just_tryph_131_1` | Justin Martyr, Dialogus cum Tryphone, 131_1 | 589 |
| `passage_just_tryph_131_2` | Justin Martyr, Dialogus cum Tryphone, 131_2 | 507 |
| `passage_just_tryph_131_3` | Justin Martyr, Dialogus cum Tryphone, 131_3 | 724 |
| `passage_just_tryph_131_4` | Justin Martyr, Dialogus cum Tryphone, 131_4 | 592 |
| `passage_just_tryph_131_5` | Justin Martyr, Dialogus cum Tryphone, 131_5 | 476 |
| `passage_just_tryph_131_6` | Justin Martyr, Dialogus cum Tryphone, 131_6 | 582 |
| `passage_just_tryph_132_1` | Justin Martyr, Dialogus cum Tryphone, 132_1 | 714 |
| `passage_just_tryph_132_2` | Justin Martyr, Dialogus cum Tryphone, 132_2 | 347 |
| `passage_just_tryph_132_3` | Justin Martyr, Dialogus cum Tryphone, 132_3 | 575 |
| `passage_just_tryph_133_1` | Justin Martyr, Dialogus cum Tryphone, 133_1 | 352 |
| `passage_just_tryph_133_2` | Justin Martyr, Dialogus cum Tryphone, 133_2 | 419 |
| `passage_just_tryph_133_3` | Justin Martyr, Dialogus cum Tryphone, 133_3 | 405 |
| `passage_just_tryph_133_4` | Justin Martyr, Dialogus cum Tryphone, 133_4 | 470 |
| `passage_just_tryph_133_5` | Justin Martyr, Dialogus cum Tryphone, 133_5 | 678 |
| `passage_just_tryph_133_6` | Justin Martyr, Dialogus cum Tryphone, 133_6 | 561 |
| `passage_just_tryph_134_1` | Justin Martyr, Dialogus cum Tryphone, 134_1 | 446 |
| `passage_just_tryph_134_2` | Justin Martyr, Dialogus cum Tryphone, 134_2 | 373 |
| `passage_just_tryph_134_3` | Justin Martyr, Dialogus cum Tryphone, 134_3 | 421 |
| `passage_just_tryph_134_4` | Justin Martyr, Dialogus cum Tryphone, 134_4 | 471 |
| `passage_just_tryph_134_5` | Justin Martyr, Dialogus cum Tryphone, 134_5 | 543 |
| `passage_just_tryph_134_6` | Justin Martyr, Dialogus cum Tryphone, 134_6 | 272 |
| `passage_just_tryph_135_1` | Justin Martyr, Dialogus cum Tryphone, 135_1 | 330 |
| `passage_just_tryph_135_2` | Justin Martyr, Dialogus cum Tryphone, 135_2 | 429 |
| `passage_just_tryph_135_3` | Justin Martyr, Dialogus cum Tryphone, 135_3 | 284 |
| `passage_just_tryph_135_4` | Justin Martyr, Dialogus cum Tryphone, 135_4 | 643 |
| `passage_just_tryph_135_5` | Justin Martyr, Dialogus cum Tryphone, 135_5 | 342 |
| `passage_just_tryph_135_6` | Justin Martyr, Dialogus cum Tryphone, 135_6 | 434 |
| `passage_just_tryph_136_1` | Justin Martyr, Dialogus cum Tryphone, 136_1 | 462 |
| `passage_just_tryph_136_2` | Justin Martyr, Dialogus cum Tryphone, 136_2 | 559 |
| `passage_just_tryph_136_3` | Justin Martyr, Dialogus cum Tryphone, 136_3 | 487 |
| `passage_just_tryph_137_1` | Justin Martyr, Dialogus cum Tryphone, 137_1 | 368 |
| `passage_just_tryph_137_2` | Justin Martyr, Dialogus cum Tryphone, 137_2 | 396 |
| `passage_just_tryph_137_3` | Justin Martyr, Dialogus cum Tryphone, 137_3 | 552 |
| `passage_just_tryph_137_4` | Justin Martyr, Dialogus cum Tryphone, 137_4 | 313 |
| `passage_just_tryph_138_1` | Justin Martyr, Dialogus cum Tryphone, 138_1 | 580 |
| `passage_just_tryph_138_2` | Justin Martyr, Dialogus cum Tryphone, 138_2 | 475 |
| `passage_just_tryph_138_3` | Justin Martyr, Dialogus cum Tryphone, 138_3 | 516 |
| `passage_just_tryph_139_1` | Justin Martyr, Dialogus cum Tryphone, 139_1 | 456 |
| `passage_just_tryph_139_2` | Justin Martyr, Dialogus cum Tryphone, 139_2 | 313 |
| `passage_just_tryph_139_3` | Justin Martyr, Dialogus cum Tryphone, 139_3 | 666 |
| `passage_just_tryph_139_4` | Justin Martyr, Dialogus cum Tryphone, 139_4 | 545 |
| `passage_just_tryph_139_5` | Justin Martyr, Dialogus cum Tryphone, 139_5 | 245 |
| `passage_just_tryph_14_1` | Justin Martyr, Dialogus cum Tryphone, 14_1 | 512 |
| `passage_just_tryph_14_2` | Justin Martyr, Dialogus cum Tryphone, 14_2 | 366 |
| `passage_just_tryph_14_3` | Justin Martyr, Dialogus cum Tryphone, 14_3 | 348 |
| `passage_just_tryph_14_4` | Justin Martyr, Dialogus cum Tryphone, 14_4 | 336 |
| `passage_just_tryph_14_5` | Justin Martyr, Dialogus cum Tryphone, 14_5 | 448 |
| `passage_just_tryph_14_6` | Justin Martyr, Dialogus cum Tryphone, 14_6 | 305 |
| `passage_just_tryph_14_7` | Justin Martyr, Dialogus cum Tryphone, 14_7 | 348 |
| `passage_just_tryph_14_8` | Justin Martyr, Dialogus cum Tryphone, 14_8 | 473 |
| `passage_just_tryph_140_1` | Justin Martyr, Dialogus cum Tryphone, 140_1 | 520 |
| `passage_just_tryph_140_2` | Justin Martyr, Dialogus cum Tryphone, 140_2 | 472 |
| `passage_just_tryph_140_3` | Justin Martyr, Dialogus cum Tryphone, 140_3 | 595 |
| `passage_just_tryph_140_4` | Justin Martyr, Dialogus cum Tryphone, 140_4 | 533 |
| `passage_just_tryph_141_1` | Justin Martyr, Dialogus cum Tryphone, 141_1 | 582 |
| `passage_just_tryph_141_2` | Justin Martyr, Dialogus cum Tryphone, 141_2 | 686 |
| `passage_just_tryph_141_3` | Justin Martyr, Dialogus cum Tryphone, 141_3 | 493 |
| `passage_just_tryph_141_4` | Justin Martyr, Dialogus cum Tryphone, 141_4 | 517 |
| `passage_just_tryph_142_1` | Justin Martyr, Dialogus cum Tryphone, 142_1 | 487 |
| `passage_just_tryph_142_2` | Justin Martyr, Dialogus cum Tryphone, 142_2 | 307 |
| `passage_just_tryph_142_3` | Justin Martyr, Dialogus cum Tryphone, 142_3 | 333 |
| `passage_just_tryph_15_1` | Justin Martyr, Dialogus cum Tryphone, 15_1 | 95 |
| `passage_just_tryph_15_2` | Justin Martyr, Dialogus cum Tryphone, 15_2 | 308 |
| `passage_just_tryph_15_3` | Justin Martyr, Dialogus cum Tryphone, 15_3 | 407 |
| `passage_just_tryph_15_4` | Justin Martyr, Dialogus cum Tryphone, 15_4 | 414 |
| `passage_just_tryph_15_5` | Justin Martyr, Dialogus cum Tryphone, 15_5 | 403 |
| `passage_just_tryph_15_6` | Justin Martyr, Dialogus cum Tryphone, 15_6 | 421 |
| `passage_just_tryph_15_7` | Justin Martyr, Dialogus cum Tryphone, 15_7 | 107 |
| `passage_just_tryph_16_1` | Justin Martyr, Dialogus cum Tryphone, 16_1 | 557 |
| `passage_just_tryph_16_2` | Justin Martyr, Dialogus cum Tryphone, 16_2 | 337 |
| `passage_just_tryph_16_3` | Justin Martyr, Dialogus cum Tryphone, 16_3 | 283 |
| `passage_just_tryph_16_4` | Justin Martyr, Dialogus cum Tryphone, 16_4 | 463 |
| `passage_just_tryph_16_5` | Justin Martyr, Dialogus cum Tryphone, 16_5 | 379 |
| `passage_just_tryph_17_1` | Justin Martyr, Dialogus cum Tryphone, 17_1 | 854 |
| `passage_just_tryph_17_2` | Justin Martyr, Dialogus cum Tryphone, 17_2 | 743 |
| `passage_just_tryph_17_3` | Justin Martyr, Dialogus cum Tryphone, 17_3 | 380 |
| `passage_just_tryph_17_4` | Justin Martyr, Dialogus cum Tryphone, 17_4 | 469 |
| `passage_just_tryph_18_1` | Justin Martyr, Dialogus cum Tryphone, 18_1 | 193 |
| `passage_just_tryph_18_2` | Justin Martyr, Dialogus cum Tryphone, 18_2 | 403 |
| `passage_just_tryph_18_3` | Justin Martyr, Dialogus cum Tryphone, 18_3 | 394 |
| `passage_just_tryph_19_1` | Justin Martyr, Dialogus cum Tryphone, 19_1 | 129 |
| `passage_just_tryph_19_2` | Justin Martyr, Dialogus cum Tryphone, 19_2 | 383 |
| `passage_just_tryph_19_3` | Justin Martyr, Dialogus cum Tryphone, 19_3 | 408 |
| `passage_just_tryph_19_4` | Justin Martyr, Dialogus cum Tryphone, 19_4 | 465 |
| `passage_just_tryph_19_5` | Justin Martyr, Dialogus cum Tryphone, 19_5 | 375 |
| `passage_just_tryph_19_6` | Justin Martyr, Dialogus cum Tryphone, 19_6 | 372 |
| `passage_just_tryph_2_1` | Justin Martyr, Dialogus cum Tryphone, 2_1 | 439 |
| `passage_just_tryph_2_2` | Justin Martyr, Dialogus cum Tryphone, 2_2 | 455 |
| `passage_just_tryph_2_3` | Justin Martyr, Dialogus cum Tryphone, 2_3 | 534 |
| `passage_just_tryph_2_4` | Justin Martyr, Dialogus cum Tryphone, 2_4 | 526 |
| `passage_just_tryph_2_5` | Justin Martyr, Dialogus cum Tryphone, 2_5 | 304 |
| `passage_just_tryph_2_6` | Justin Martyr, Dialogus cum Tryphone, 2_6 | 521 |
| `passage_just_tryph_20_1` | Justin Martyr, Dialogus cum Tryphone, 20_1 | 634 |
| `passage_just_tryph_20_2` | Justin Martyr, Dialogus cum Tryphone, 20_2 | 325 |
| `passage_just_tryph_20_3` | Justin Martyr, Dialogus cum Tryphone, 20_3 | 442 |
| `passage_just_tryph_20_4` | Justin Martyr, Dialogus cum Tryphone, 20_4 | 336 |
| `passage_just_tryph_21_1` | Justin Martyr, Dialogus cum Tryphone, 21_1 | 339 |
| `passage_just_tryph_21_2` | Justin Martyr, Dialogus cum Tryphone, 21_2 | 522 |
| `passage_just_tryph_21_3` | Justin Martyr, Dialogus cum Tryphone, 21_3 | 504 |
| `passage_just_tryph_21_4` | Justin Martyr, Dialogus cum Tryphone, 21_4 | 207 |
| `passage_just_tryph_22_1` | Justin Martyr, Dialogus cum Tryphone, 22_1 | 216 |
| `passage_just_tryph_22_10` | Justin Martyr, Dialogus cum Tryphone, 22_10 | 540 |
| `passage_just_tryph_22_11` | Justin Martyr, Dialogus cum Tryphone, 22_11 | 413 |
| `passage_just_tryph_22_2` | Justin Martyr, Dialogus cum Tryphone, 22_2 | 467 |
| `passage_just_tryph_22_3` | Justin Martyr, Dialogus cum Tryphone, 22_3 | 454 |
| `passage_just_tryph_22_4` | Justin Martyr, Dialogus cum Tryphone, 22_4 | 471 |
| `passage_just_tryph_22_5` | Justin Martyr, Dialogus cum Tryphone, 22_5 | 608 |
| `passage_just_tryph_22_6` | Justin Martyr, Dialogus cum Tryphone, 22_6 | 233 |
| `passage_just_tryph_22_7` | Justin Martyr, Dialogus cum Tryphone, 22_7 | 541 |
| `passage_just_tryph_22_8` | Justin Martyr, Dialogus cum Tryphone, 22_8 | 397 |
| `passage_just_tryph_22_9` | Justin Martyr, Dialogus cum Tryphone, 22_9 | 454 |
| `passage_just_tryph_23_1` | Justin Martyr, Dialogus cum Tryphone, 23_1 | 390 |
| `passage_just_tryph_23_2` | Justin Martyr, Dialogus cum Tryphone, 23_2 | 284 |
| `passage_just_tryph_23_3` | Justin Martyr, Dialogus cum Tryphone, 23_3 | 487 |
| `passage_just_tryph_23_4` | Justin Martyr, Dialogus cum Tryphone, 23_4 | 469 |
| `passage_just_tryph_23_5` | Justin Martyr, Dialogus cum Tryphone, 23_5 | 433 |
| `passage_just_tryph_24_1` | Justin Martyr, Dialogus cum Tryphone, 24_1 | 442 |
| `passage_just_tryph_24_2` | Justin Martyr, Dialogus cum Tryphone, 24_2 | 233 |
| `passage_just_tryph_24_3` | Justin Martyr, Dialogus cum Tryphone, 24_3 | 422 |
| `passage_just_tryph_24_4` | Justin Martyr, Dialogus cum Tryphone, 24_4 | 254 |
| `passage_just_tryph_25_1` | Justin Martyr, Dialogus cum Tryphone, 25_1 | 252 |
| `passage_just_tryph_25_2` | Justin Martyr, Dialogus cum Tryphone, 25_2 | 416 |
| `passage_just_tryph_25_3` | Justin Martyr, Dialogus cum Tryphone, 25_3 | 425 |
| `passage_just_tryph_25_4` | Justin Martyr, Dialogus cum Tryphone, 25_4 | 464 |
| `passage_just_tryph_25_5` | Justin Martyr, Dialogus cum Tryphone, 25_5 | 528 |
| `passage_just_tryph_25_6` | Justin Martyr, Dialogus cum Tryphone, 25_6 | 121 |
| `passage_just_tryph_26_1` | Justin Martyr, Dialogus cum Tryphone, 26_1 | 438 |
| `passage_just_tryph_26_2` | Justin Martyr, Dialogus cum Tryphone, 26_2 | 294 |
| `passage_just_tryph_26_3` | Justin Martyr, Dialogus cum Tryphone, 26_3 | 488 |
| `passage_just_tryph_26_4` | Justin Martyr, Dialogus cum Tryphone, 26_4 | 559 |
| `passage_just_tryph_27_1` | Justin Martyr, Dialogus cum Tryphone, 27_1 | 559 |
| `passage_just_tryph_27_2` | Justin Martyr, Dialogus cum Tryphone, 27_2 | 587 |
| `passage_just_tryph_27_3` | Justin Martyr, Dialogus cum Tryphone, 27_3 | 462 |
| `passage_just_tryph_27_4` | Justin Martyr, Dialogus cum Tryphone, 27_4 | 559 |
| `passage_just_tryph_27_5` | Justin Martyr, Dialogus cum Tryphone, 27_5 | 630 |
| `passage_just_tryph_28_1` | Justin Martyr, Dialogus cum Tryphone, 28_1 | 266 |
| `passage_just_tryph_28_2` | Justin Martyr, Dialogus cum Tryphone, 28_2 | 476 |
| `passage_just_tryph_28_3` | Justin Martyr, Dialogus cum Tryphone, 28_3 | 416 |
| `passage_just_tryph_28_4` | Justin Martyr, Dialogus cum Tryphone, 28_4 | 425 |
| `passage_just_tryph_28_5` | Justin Martyr, Dialogus cum Tryphone, 28_5 | 482 |
| `passage_just_tryph_28_6` | Justin Martyr, Dialogus cum Tryphone, 28_6 | 112 |
| `passage_just_tryph_29_1` | Justin Martyr, Dialogus cum Tryphone, 29_1 | 366 |
| `passage_just_tryph_29_2` | Justin Martyr, Dialogus cum Tryphone, 29_2 | 442 |
| `passage_just_tryph_29_3` | Justin Martyr, Dialogus cum Tryphone, 29_3 | 468 |
| `passage_just_tryph_3_1` | Justin Martyr, Dialogus cum Tryphone, 3_1 | 439 |
| `passage_just_tryph_3_2` | Justin Martyr, Dialogus cum Tryphone, 3_2 | 502 |
| `passage_just_tryph_3_3` | Justin Martyr, Dialogus cum Tryphone, 3_3 | 673 |
| `passage_just_tryph_3_4` | Justin Martyr, Dialogus cum Tryphone, 3_4 | 324 |
| `passage_just_tryph_3_5` | Justin Martyr, Dialogus cum Tryphone, 3_5 | 587 |
| `passage_just_tryph_3_6` | Justin Martyr, Dialogus cum Tryphone, 3_6 | 515 |
| `passage_just_tryph_3_7` | Justin Martyr, Dialogus cum Tryphone, 3_7 | 298 |
| `passage_just_tryph_30_1` | Justin Martyr, Dialogus cum Tryphone, 30_1 | 473 |
| `passage_just_tryph_30_2` | Justin Martyr, Dialogus cum Tryphone, 30_2 | 505 |
| `passage_just_tryph_30_3` | Justin Martyr, Dialogus cum Tryphone, 30_3 | 671 |
| `passage_just_tryph_31_1` | Justin Martyr, Dialogus cum Tryphone, 31_1 | 239 |
| `passage_just_tryph_31_2` | Justin Martyr, Dialogus cum Tryphone, 31_2 | 408 |
| `passage_just_tryph_31_3` | Justin Martyr, Dialogus cum Tryphone, 31_3 | 455 |
| `passage_just_tryph_31_4` | Justin Martyr, Dialogus cum Tryphone, 31_4 | 585 |
| `passage_just_tryph_31_5` | Justin Martyr, Dialogus cum Tryphone, 31_5 | 685 |
| `passage_just_tryph_31_6` | Justin Martyr, Dialogus cum Tryphone, 31_6 | 545 |
| `passage_just_tryph_31_7` | Justin Martyr, Dialogus cum Tryphone, 31_7 | 460 |
| `passage_just_tryph_32_1` | Justin Martyr, Dialogus cum Tryphone, 32_1 | 412 |
| `passage_just_tryph_32_2` | Justin Martyr, Dialogus cum Tryphone, 32_2 | 889 |
| `passage_just_tryph_32_3` | Justin Martyr, Dialogus cum Tryphone, 32_3 | 664 |
| `passage_just_tryph_32_4` | Justin Martyr, Dialogus cum Tryphone, 32_4 | 345 |
| `passage_just_tryph_32_5` | Justin Martyr, Dialogus cum Tryphone, 32_5 | 465 |
| `passage_just_tryph_32_6` | Justin Martyr, Dialogus cum Tryphone, 32_6 | 623 |
| `passage_just_tryph_33_1` | Justin Martyr, Dialogus cum Tryphone, 33_1 | 580 |
| `passage_just_tryph_33_2` | Justin Martyr, Dialogus cum Tryphone, 33_2 | 891 |
| `passage_just_tryph_34_1` | Justin Martyr, Dialogus cum Tryphone, 34_1 | 576 |
| `passage_just_tryph_34_2` | Justin Martyr, Dialogus cum Tryphone, 34_2 | 559 |
| `passage_just_tryph_34_3` | Justin Martyr, Dialogus cum Tryphone, 34_3 | 504 |
| `passage_just_tryph_34_4` | Justin Martyr, Dialogus cum Tryphone, 34_4 | 504 |
| `passage_just_tryph_34_5` | Justin Martyr, Dialogus cum Tryphone, 34_5 | 428 |
| `passage_just_tryph_34_6` | Justin Martyr, Dialogus cum Tryphone, 34_6 | 480 |
| `passage_just_tryph_34_7` | Justin Martyr, Dialogus cum Tryphone, 34_7 | 356 |
| `passage_just_tryph_34_8` | Justin Martyr, Dialogus cum Tryphone, 34_8 | 359 |
| `passage_just_tryph_35_1` | Justin Martyr, Dialogus cum Tryphone, 35_1 | 160 |
| `passage_just_tryph_35_2` | Justin Martyr, Dialogus cum Tryphone, 35_2 | 504 |
| `passage_just_tryph_35_3` | Justin Martyr, Dialogus cum Tryphone, 35_3 | 490 |
| `passage_just_tryph_35_4` | Justin Martyr, Dialogus cum Tryphone, 35_4 | 250 |
| `passage_just_tryph_35_5` | Justin Martyr, Dialogus cum Tryphone, 35_5 | 320 |
| `passage_just_tryph_35_6` | Justin Martyr, Dialogus cum Tryphone, 35_6 | 499 |
| `passage_just_tryph_35_7` | Justin Martyr, Dialogus cum Tryphone, 35_7 | 366 |
| `passage_just_tryph_35_8` | Justin Martyr, Dialogus cum Tryphone, 35_8 | 463 |
| `passage_just_tryph_36_1` | Justin Martyr, Dialogus cum Tryphone, 36_1 | 347 |
| `passage_just_tryph_36_2` | Justin Martyr, Dialogus cum Tryphone, 36_2 | 478 |
| `passage_just_tryph_36_3` | Justin Martyr, Dialogus cum Tryphone, 36_3 | 390 |
| `passage_just_tryph_36_4` | Justin Martyr, Dialogus cum Tryphone, 36_4 | 524 |
| `passage_just_tryph_36_5` | Justin Martyr, Dialogus cum Tryphone, 36_5 | 414 |
| `passage_just_tryph_36_6` | Justin Martyr, Dialogus cum Tryphone, 36_6 | 602 |
| `passage_just_tryph_37_1` | Justin Martyr, Dialogus cum Tryphone, 37_1 | 429 |
| `passage_just_tryph_37_2` | Justin Martyr, Dialogus cum Tryphone, 37_2 | 204 |
| `passage_just_tryph_37_3` | Justin Martyr, Dialogus cum Tryphone, 37_3 | 456 |
| `passage_just_tryph_37_4` | Justin Martyr, Dialogus cum Tryphone, 37_4 | 470 |
| `passage_just_tryph_38_1` | Justin Martyr, Dialogus cum Tryphone, 38_1 | 431 |
| `passage_just_tryph_38_2` | Justin Martyr, Dialogus cum Tryphone, 38_2 | 645 |
| `passage_just_tryph_38_3` | Justin Martyr, Dialogus cum Tryphone, 38_3 | 622 |
| `passage_just_tryph_38_4` | Justin Martyr, Dialogus cum Tryphone, 38_4 | 637 |
| `passage_just_tryph_38_5` | Justin Martyr, Dialogus cum Tryphone, 38_5 | 571 |
| `passage_just_tryph_39_1` | Justin Martyr, Dialogus cum Tryphone, 39_1 | 445 |
| `passage_just_tryph_39_2` | Justin Martyr, Dialogus cum Tryphone, 39_2 | 538 |
| `passage_just_tryph_39_3` | Justin Martyr, Dialogus cum Tryphone, 39_3 | 86 |
| `passage_just_tryph_39_4` | Justin Martyr, Dialogus cum Tryphone, 39_4 | 353 |
| `passage_just_tryph_39_5` | Justin Martyr, Dialogus cum Tryphone, 39_5 | 416 |
| `passage_just_tryph_39_6` | Justin Martyr, Dialogus cum Tryphone, 39_6 | 417 |
| `passage_just_tryph_39_7` | Justin Martyr, Dialogus cum Tryphone, 39_7 | 412 |
| `passage_just_tryph_39_8` | Justin Martyr, Dialogus cum Tryphone, 39_8 | 282 |
| `passage_just_tryph_4_1` | Justin Martyr, Dialogus cum Tryphone, 4_1 | 661 |
| `passage_just_tryph_4_2` | Justin Martyr, Dialogus cum Tryphone, 4_2 | 445 |
| `passage_just_tryph_4_3` | Justin Martyr, Dialogus cum Tryphone, 4_3 | 382 |
| `passage_just_tryph_4_4` | Justin Martyr, Dialogus cum Tryphone, 4_4 | 360 |
| `passage_just_tryph_4_5` | Justin Martyr, Dialogus cum Tryphone, 4_5 | 364 |
| `passage_just_tryph_4_6` | Justin Martyr, Dialogus cum Tryphone, 4_6 | 248 |
| `passage_just_tryph_4_7` | Justin Martyr, Dialogus cum Tryphone, 4_7 | 407 |
| `passage_just_tryph_40_1` | Justin Martyr, Dialogus cum Tryphone, 40_1 | 470 |
| `passage_just_tryph_40_2` | Justin Martyr, Dialogus cum Tryphone, 40_2 | 294 |
| `passage_just_tryph_40_3` | Justin Martyr, Dialogus cum Tryphone, 40_3 | 378 |
| `passage_just_tryph_40_4` | Justin Martyr, Dialogus cum Tryphone, 40_4 | 752 |
| `passage_just_tryph_40_5` | Justin Martyr, Dialogus cum Tryphone, 40_5 | 146 |
| `passage_just_tryph_41_1` | Justin Martyr, Dialogus cum Tryphone, 41_1 | 651 |
| `passage_just_tryph_41_2` | Justin Martyr, Dialogus cum Tryphone, 41_2 | 450 |
| `passage_just_tryph_41_3` | Justin Martyr, Dialogus cum Tryphone, 41_3 | 220 |
| `passage_just_tryph_41_4` | Justin Martyr, Dialogus cum Tryphone, 41_4 | 437 |
| `passage_just_tryph_42_1` | Justin Martyr, Dialogus cum Tryphone, 42_1 | 393 |
| `passage_just_tryph_42_2` | Justin Martyr, Dialogus cum Tryphone, 42_2 | 358 |
| `passage_just_tryph_42_3` | Justin Martyr, Dialogus cum Tryphone, 42_3 | 483 |
| `passage_just_tryph_42_4` | Justin Martyr, Dialogus cum Tryphone, 42_4 | 369 |
| `passage_just_tryph_43_1` | Justin Martyr, Dialogus cum Tryphone, 43_1 | 530 |
| `passage_just_tryph_43_2` | Justin Martyr, Dialogus cum Tryphone, 43_2 | 310 |
| `passage_just_tryph_43_3` | Justin Martyr, Dialogus cum Tryphone, 43_3 | 466 |
| `passage_just_tryph_43_4` | Justin Martyr, Dialogus cum Tryphone, 43_4 | 176 |
| `passage_just_tryph_43_5` | Justin Martyr, Dialogus cum Tryphone, 43_5 | 456 |
| `passage_just_tryph_43_6` | Justin Martyr, Dialogus cum Tryphone, 43_6 | 590 |
| `passage_just_tryph_43_7` | Justin Martyr, Dialogus cum Tryphone, 43_7 | 169 |
| `passage_just_tryph_43_8` | Justin Martyr, Dialogus cum Tryphone, 43_8 | 395 |
| `passage_just_tryph_44_1` | Justin Martyr, Dialogus cum Tryphone, 44_1 | 476 |
| `passage_just_tryph_44_2` | Justin Martyr, Dialogus cum Tryphone, 44_2 | 497 |
| `passage_just_tryph_44_3` | Justin Martyr, Dialogus cum Tryphone, 44_3 | 253 |
| `passage_just_tryph_44_4` | Justin Martyr, Dialogus cum Tryphone, 44_4 | 346 |
| `passage_just_tryph_45_1` | Justin Martyr, Dialogus cum Tryphone, 45_1 | 318 |
| `passage_just_tryph_45_2` | Justin Martyr, Dialogus cum Tryphone, 45_2 | 175 |
| `passage_just_tryph_45_3` | Justin Martyr, Dialogus cum Tryphone, 45_3 | 534 |
| `passage_just_tryph_45_4` | Justin Martyr, Dialogus cum Tryphone, 45_4 | 888 |
| `passage_just_tryph_46_1` | Justin Martyr, Dialogus cum Tryphone, 46_1 | 313 |
| `passage_just_tryph_46_2` | Justin Martyr, Dialogus cum Tryphone, 46_2 | 627 |
| `passage_just_tryph_46_3` | Justin Martyr, Dialogus cum Tryphone, 46_3 | 477 |
| `passage_just_tryph_46_4` | Justin Martyr, Dialogus cum Tryphone, 46_4 | 439 |
| `passage_just_tryph_46_5` | Justin Martyr, Dialogus cum Tryphone, 46_5 | 660 |
| `passage_just_tryph_46_6` | Justin Martyr, Dialogus cum Tryphone, 46_6 | 335 |
| `passage_just_tryph_46_7` | Justin Martyr, Dialogus cum Tryphone, 46_7 | 349 |
| `passage_just_tryph_47_1` | Justin Martyr, Dialogus cum Tryphone, 47_1 | 575 |
| `passage_just_tryph_47_2` | Justin Martyr, Dialogus cum Tryphone, 47_2 | 767 |
| `passage_just_tryph_47_3` | Justin Martyr, Dialogus cum Tryphone, 47_3 | 304 |
| `passage_just_tryph_47_4` | Justin Martyr, Dialogus cum Tryphone, 47_4 | 733 |
| `passage_just_tryph_47_5` | Justin Martyr, Dialogus cum Tryphone, 47_5 | 448 |
| `passage_just_tryph_48_1` | Justin Martyr, Dialogus cum Tryphone, 48_1 | 385 |
| `passage_just_tryph_48_2` | Justin Martyr, Dialogus cum Tryphone, 48_2 | 443 |
| `passage_just_tryph_48_3` | Justin Martyr, Dialogus cum Tryphone, 48_3 | 408 |
| `passage_just_tryph_48_4` | Justin Martyr, Dialogus cum Tryphone, 48_4 | 362 |
| `passage_just_tryph_49_1` | Justin Martyr, Dialogus cum Tryphone, 49_1 | 465 |
| `passage_just_tryph_49_2` | Justin Martyr, Dialogus cum Tryphone, 49_2 | 663 |
| `passage_just_tryph_49_3` | Justin Martyr, Dialogus cum Tryphone, 49_3 | 865 |
| `passage_just_tryph_49_4` | Justin Martyr, Dialogus cum Tryphone, 49_4 | 424 |
| `passage_just_tryph_49_5` | Justin Martyr, Dialogus cum Tryphone, 49_5 | 353 |
| `passage_just_tryph_49_6` | Justin Martyr, Dialogus cum Tryphone, 49_6 | 440 |
| `passage_just_tryph_49_7` | Justin Martyr, Dialogus cum Tryphone, 49_7 | 365 |
| `passage_just_tryph_49_8` | Justin Martyr, Dialogus cum Tryphone, 49_8 | 429 |
| `passage_just_tryph_5_1` | Justin Martyr, Dialogus cum Tryphone, 5_1 | 360 |
| `passage_just_tryph_5_2` | Justin Martyr, Dialogus cum Tryphone, 5_2 | 470 |
| `passage_just_tryph_5_3` | Justin Martyr, Dialogus cum Tryphone, 5_3 | 372 |
| `passage_just_tryph_5_4` | Justin Martyr, Dialogus cum Tryphone, 5_4 | 510 |
| `passage_just_tryph_5_5` | Justin Martyr, Dialogus cum Tryphone, 5_5 | 408 |
| `passage_just_tryph_5_6` | Justin Martyr, Dialogus cum Tryphone, 5_6 | 355 |
| `passage_just_tryph_50_1` | Justin Martyr, Dialogus cum Tryphone, 50_1 | 329 |
| `passage_just_tryph_50_2` | Justin Martyr, Dialogus cum Tryphone, 50_2 | 241 |
| `passage_just_tryph_50_3` | Justin Martyr, Dialogus cum Tryphone, 50_3 | 745 |
| `passage_just_tryph_50_4` | Justin Martyr, Dialogus cum Tryphone, 50_4 | 595 |
| `passage_just_tryph_50_5` | Justin Martyr, Dialogus cum Tryphone, 50_5 | 574 |
| `passage_just_tryph_51_1` | Justin Martyr, Dialogus cum Tryphone, 51_1 | 332 |
| `passage_just_tryph_51_2` | Justin Martyr, Dialogus cum Tryphone, 51_2 | 830 |
| `passage_just_tryph_51_3` | Justin Martyr, Dialogus cum Tryphone, 51_3 | 454 |
| `passage_just_tryph_52_1` | Justin Martyr, Dialogus cum Tryphone, 52_1 | 380 |
| `passage_just_tryph_52_2` | Justin Martyr, Dialogus cum Tryphone, 52_2 | 644 |
| `passage_just_tryph_52_3` | Justin Martyr, Dialogus cum Tryphone, 52_3 | 735 |
| `passage_just_tryph_52_4` | Justin Martyr, Dialogus cum Tryphone, 52_4 | 588 |
| `passage_just_tryph_53_1` | Justin Martyr, Dialogus cum Tryphone, 53_1 | 526 |
| `passage_just_tryph_53_2` | Justin Martyr, Dialogus cum Tryphone, 53_2 | 508 |
| `passage_just_tryph_53_3` | Justin Martyr, Dialogus cum Tryphone, 53_3 | 273 |
| `passage_just_tryph_53_4` | Justin Martyr, Dialogus cum Tryphone, 53_4 | 481 |
| `passage_just_tryph_53_5` | Justin Martyr, Dialogus cum Tryphone, 53_5 | 441 |
| `passage_just_tryph_53_6` | Justin Martyr, Dialogus cum Tryphone, 53_6 | 425 |
| `passage_just_tryph_54_1` | Justin Martyr, Dialogus cum Tryphone, 54_1 | 429 |
| `passage_just_tryph_54_2` | Justin Martyr, Dialogus cum Tryphone, 54_2 | 464 |
| `passage_just_tryph_55_1` | Justin Martyr, Dialogus cum Tryphone, 55_1 | 585 |
| `passage_just_tryph_55_2` | Justin Martyr, Dialogus cum Tryphone, 55_2 | 420 |
| `passage_just_tryph_55_3` | Justin Martyr, Dialogus cum Tryphone, 55_3 | 784 |
| `passage_just_tryph_56_1` | Justin Martyr, Dialogus cum Tryphone, 56_1 | 355 |
| `passage_just_tryph_56_10` | Justin Martyr, Dialogus cum Tryphone, 56_10 | 519 |
| `passage_just_tryph_56_11` | Justin Martyr, Dialogus cum Tryphone, 56_11 | 394 |
| `passage_just_tryph_56_12` | Justin Martyr, Dialogus cum Tryphone, 56_12 | 499 |
| `passage_just_tryph_56_13` | Justin Martyr, Dialogus cum Tryphone, 56_13 | 206 |
| `passage_just_tryph_56_14` | Justin Martyr, Dialogus cum Tryphone, 56_14 | 648 |
| `passage_just_tryph_56_15` | Justin Martyr, Dialogus cum Tryphone, 56_15 | 348 |
| `passage_just_tryph_56_16` | Justin Martyr, Dialogus cum Tryphone, 56_16 | 389 |
| `passage_just_tryph_56_17` | Justin Martyr, Dialogus cum Tryphone, 56_17 | 541 |
| `passage_just_tryph_56_18` | Justin Martyr, Dialogus cum Tryphone, 56_18 | 583 |
| `passage_just_tryph_56_19` | Justin Martyr, Dialogus cum Tryphone, 56_19 | 582 |
| `passage_just_tryph_56_2` | Justin Martyr, Dialogus cum Tryphone, 56_2 | 691 |
| `passage_just_tryph_56_20` | Justin Martyr, Dialogus cum Tryphone, 56_20 | 417 |
| `passage_just_tryph_56_21` | Justin Martyr, Dialogus cum Tryphone, 56_21 | 580 |
| `passage_just_tryph_56_22` | Justin Martyr, Dialogus cum Tryphone, 56_22 | 355 |
| `passage_just_tryph_56_23` | Justin Martyr, Dialogus cum Tryphone, 56_23 | 337 |
| `passage_just_tryph_56_3` | Justin Martyr, Dialogus cum Tryphone, 56_3 | 177 |
| `passage_just_tryph_56_4` | Justin Martyr, Dialogus cum Tryphone, 56_4 | 429 |
| `passage_just_tryph_56_5` | Justin Martyr, Dialogus cum Tryphone, 56_5 | 377 |
| `passage_just_tryph_56_6` | Justin Martyr, Dialogus cum Tryphone, 56_6 | 333 |
| `passage_just_tryph_56_7` | Justin Martyr, Dialogus cum Tryphone, 56_7 | 548 |
| `passage_just_tryph_56_8` | Justin Martyr, Dialogus cum Tryphone, 56_8 | 340 |
| `passage_just_tryph_56_9` | Justin Martyr, Dialogus cum Tryphone, 56_9 | 288 |
| `passage_just_tryph_57_1` | Justin Martyr, Dialogus cum Tryphone, 57_1 | 249 |
| `passage_just_tryph_57_2` | Justin Martyr, Dialogus cum Tryphone, 57_2 | 695 |
| `passage_just_tryph_57_3` | Justin Martyr, Dialogus cum Tryphone, 57_3 | 348 |
| `passage_just_tryph_57_4` | Justin Martyr, Dialogus cum Tryphone, 57_4 | 280 |
| `passage_just_tryph_58_1` | Justin Martyr, Dialogus cum Tryphone, 58_1 | 423 |
| `passage_just_tryph_58_10` | Justin Martyr, Dialogus cum Tryphone, 58_10 | 342 |
| `passage_just_tryph_58_11` | Justin Martyr, Dialogus cum Tryphone, 58_11 | 418 |
| `passage_just_tryph_58_12` | Justin Martyr, Dialogus cum Tryphone, 58_12 | 506 |
| `passage_just_tryph_58_13` | Justin Martyr, Dialogus cum Tryphone, 58_13 | 504 |
| `passage_just_tryph_58_2` | Justin Martyr, Dialogus cum Tryphone, 58_2 | 314 |
| `passage_just_tryph_58_3` | Justin Martyr, Dialogus cum Tryphone, 58_3 | 333 |
| `passage_just_tryph_58_4` | Justin Martyr, Dialogus cum Tryphone, 58_4 | 387 |
| `passage_just_tryph_58_5` | Justin Martyr, Dialogus cum Tryphone, 58_5 | 456 |
| `passage_just_tryph_58_6` | Justin Martyr, Dialogus cum Tryphone, 58_6 | 540 |
| `passage_just_tryph_58_7` | Justin Martyr, Dialogus cum Tryphone, 58_7 | 532 |
| `passage_just_tryph_58_8` | Justin Martyr, Dialogus cum Tryphone, 58_8 | 685 |
| `passage_just_tryph_59_1` | Justin Martyr, Dialogus cum Tryphone, 59_1 | 376 |
| `passage_just_tryph_59_2` | Justin Martyr, Dialogus cum Tryphone, 59_2 | 445 |
| `passage_just_tryph_59_3` | Justin Martyr, Dialogus cum Tryphone, 59_3 | 214 |
| `passage_just_tryph_6_1` | Justin Martyr, Dialogus cum Tryphone, 6_1 | 477 |
| `passage_just_tryph_6_2` | Justin Martyr, Dialogus cum Tryphone, 6_2 | 459 |
| `passage_just_tryph_60_1` | Justin Martyr, Dialogus cum Tryphone, 60_1 | 259 |
| `passage_just_tryph_60_2` | Justin Martyr, Dialogus cum Tryphone, 60_2 | 670 |
| `passage_just_tryph_60_3` | Justin Martyr, Dialogus cum Tryphone, 60_3 | 537 |
| `passage_just_tryph_60_4` | Justin Martyr, Dialogus cum Tryphone, 60_4 | 480 |
| `passage_just_tryph_60_5` | Justin Martyr, Dialogus cum Tryphone, 60_5 | 687 |
| `passage_just_tryph_61_1` | Justin Martyr, Dialogus cum Tryphone, 61_1 | 624 |
| `passage_just_tryph_61_2` | Justin Martyr, Dialogus cum Tryphone, 61_2 | 376 |
| `passage_just_tryph_61_3` | Justin Martyr, Dialogus cum Tryphone, 61_3 | 522 |
| `passage_just_tryph_61_4` | Justin Martyr, Dialogus cum Tryphone, 61_4 | 461 |
| `passage_just_tryph_61_5` | Justin Martyr, Dialogus cum Tryphone, 61_5 | 356 |
| `passage_just_tryph_62_1` | Justin Martyr, Dialogus cum Tryphone, 62_1 | 605 |
| `passage_just_tryph_62_2` | Justin Martyr, Dialogus cum Tryphone, 62_2 | 525 |
| `passage_just_tryph_62_3` | Justin Martyr, Dialogus cum Tryphone, 62_3 | 408 |
| `passage_just_tryph_62_4` | Justin Martyr, Dialogus cum Tryphone, 62_4 | 458 |
| `passage_just_tryph_62_5` | Justin Martyr, Dialogus cum Tryphone, 62_5 | 700 |
| `passage_just_tryph_63_1` | Justin Martyr, Dialogus cum Tryphone, 63_1 | 280 |
| `passage_just_tryph_63_2` | Justin Martyr, Dialogus cum Tryphone, 63_2 | 733 |
| `passage_just_tryph_63_3` | Justin Martyr, Dialogus cum Tryphone, 63_3 | 312 |
| `passage_just_tryph_63_4` | Justin Martyr, Dialogus cum Tryphone, 63_4 | 721 |
| `passage_just_tryph_63_5` | Justin Martyr, Dialogus cum Tryphone, 63_5 | 698 |
| `passage_just_tryph_64_1` | Justin Martyr, Dialogus cum Tryphone, 64_1 | 313 |
| `passage_just_tryph_64_2` | Justin Martyr, Dialogus cum Tryphone, 64_2 | 591 |
| `passage_just_tryph_64_3` | Justin Martyr, Dialogus cum Tryphone, 64_3 | 371 |
| `passage_just_tryph_64_4` | Justin Martyr, Dialogus cum Tryphone, 64_4 | 746 |
| `passage_just_tryph_64_5` | Justin Martyr, Dialogus cum Tryphone, 64_5 | 302 |
| `passage_just_tryph_64_6` | Justin Martyr, Dialogus cum Tryphone, 64_6 | 769 |
| `passage_just_tryph_64_7` | Justin Martyr, Dialogus cum Tryphone, 64_7 | 360 |
| `passage_just_tryph_64_8` | Justin Martyr, Dialogus cum Tryphone, 64_8 | 618 |
| `passage_just_tryph_65_1` | Justin Martyr, Dialogus cum Tryphone, 65_1 | 275 |
| `passage_just_tryph_65_2` | Justin Martyr, Dialogus cum Tryphone, 65_2 | 624 |
| `passage_just_tryph_65_3` | Justin Martyr, Dialogus cum Tryphone, 65_3 | 437 |
| `passage_just_tryph_65_4` | Justin Martyr, Dialogus cum Tryphone, 65_4 | 422 |
| `passage_just_tryph_65_5` | Justin Martyr, Dialogus cum Tryphone, 65_5 | 326 |
| `passage_just_tryph_65_6` | Justin Martyr, Dialogus cum Tryphone, 65_6 | 372 |
| `passage_just_tryph_65_7` | Justin Martyr, Dialogus cum Tryphone, 65_7 | 294 |
| `passage_just_tryph_66_1` | Justin Martyr, Dialogus cum Tryphone, 66_1 | 190 |
| `passage_just_tryph_66_2` | Justin Martyr, Dialogus cum Tryphone, 66_2 | 471 |
| `passage_just_tryph_66_3` | Justin Martyr, Dialogus cum Tryphone, 66_3 | 578 |
| `passage_just_tryph_66_4` | Justin Martyr, Dialogus cum Tryphone, 66_4 | 178 |
| `passage_just_tryph_67_1` | Justin Martyr, Dialogus cum Tryphone, 67_1 | 287 |
| `passage_just_tryph_67_10` | Justin Martyr, Dialogus cum Tryphone, 67_10 | 333 |
| `passage_just_tryph_67_11` | Justin Martyr, Dialogus cum Tryphone, 67_11 | 214 |
| `passage_just_tryph_67_2` | Justin Martyr, Dialogus cum Tryphone, 67_2 | 535 |
| `passage_just_tryph_67_3` | Justin Martyr, Dialogus cum Tryphone, 67_3 | 333 |
| `passage_just_tryph_67_4` | Justin Martyr, Dialogus cum Tryphone, 67_4 | 306 |
| `passage_just_tryph_67_5` | Justin Martyr, Dialogus cum Tryphone, 67_5 | 129 |
| `passage_just_tryph_67_6` | Justin Martyr, Dialogus cum Tryphone, 67_6 | 366 |
| `passage_just_tryph_67_7` | Justin Martyr, Dialogus cum Tryphone, 67_7 | 253 |
| `passage_just_tryph_67_8` | Justin Martyr, Dialogus cum Tryphone, 67_8 | 296 |
| `passage_just_tryph_67_9` | Justin Martyr, Dialogus cum Tryphone, 67_9 | 412 |
| `passage_just_tryph_68_1` | Justin Martyr, Dialogus cum Tryphone, 68_1 | 556 |
| `passage_just_tryph_68_2` | Justin Martyr, Dialogus cum Tryphone, 68_2 | 377 |
| `passage_just_tryph_68_3` | Justin Martyr, Dialogus cum Tryphone, 68_3 | 465 |
| `passage_just_tryph_68_4` | Justin Martyr, Dialogus cum Tryphone, 68_4 | 455 |
| `passage_just_tryph_68_5` | Justin Martyr, Dialogus cum Tryphone, 68_5 | 236 |
| `passage_just_tryph_68_6` | Justin Martyr, Dialogus cum Tryphone, 68_6 | 610 |
| `passage_just_tryph_68_7` | Justin Martyr, Dialogus cum Tryphone, 68_7 | 384 |
| `passage_just_tryph_68_8` | Justin Martyr, Dialogus cum Tryphone, 68_8 | 476 |
| `passage_just_tryph_68_9` | Justin Martyr, Dialogus cum Tryphone, 68_9 | 559 |
| `passage_just_tryph_69_1` | Justin Martyr, Dialogus cum Tryphone, 69_1 | 310 |
| `passage_just_tryph_69_2` | Justin Martyr, Dialogus cum Tryphone, 69_2 | 393 |
| `passage_just_tryph_69_3` | Justin Martyr, Dialogus cum Tryphone, 69_3 | 438 |
| `passage_just_tryph_69_4` | Justin Martyr, Dialogus cum Tryphone, 69_4 | 443 |
| `passage_just_tryph_69_5` | Justin Martyr, Dialogus cum Tryphone, 69_5 | 736 |
| `passage_just_tryph_69_6` | Justin Martyr, Dialogus cum Tryphone, 69_6 | 413 |
| `passage_just_tryph_69_7` | Justin Martyr, Dialogus cum Tryphone, 69_7 | 491 |
| `passage_just_tryph_7_1` | Justin Martyr, Dialogus cum Tryphone, 7_1 | 520 |
| `passage_just_tryph_7_2` | Justin Martyr, Dialogus cum Tryphone, 7_2 | 382 |
| `passage_just_tryph_7_3` | Justin Martyr, Dialogus cum Tryphone, 7_3 | 570 |
| `passage_just_tryph_70_1` | Justin Martyr, Dialogus cum Tryphone, 70_1 | 456 |
| `passage_just_tryph_70_2` | Justin Martyr, Dialogus cum Tryphone, 70_2 | 541 |
| `passage_just_tryph_70_3` | Justin Martyr, Dialogus cum Tryphone, 70_3 | 419 |
| `passage_just_tryph_70_4` | Justin Martyr, Dialogus cum Tryphone, 70_4 | 416 |
| `passage_just_tryph_70_5` | Justin Martyr, Dialogus cum Tryphone, 70_5 | 381 |
| `passage_just_tryph_71_1` | Justin Martyr, Dialogus cum Tryphone, 71_1 | 201 |
| `passage_just_tryph_71_2` | Justin Martyr, Dialogus cum Tryphone, 71_2 | 446 |
| `passage_just_tryph_71_3` | Justin Martyr, Dialogus cum Tryphone, 71_3 | 344 |
| `passage_just_tryph_71_4` | Justin Martyr, Dialogus cum Tryphone, 71_4 | 98 |
| `passage_just_tryph_72_1` | Justin Martyr, Dialogus cum Tryphone, 72_1 | 539 |
| `passage_just_tryph_72_2` | Justin Martyr, Dialogus cum Tryphone, 72_2 | 270 |
| `passage_just_tryph_72_3` | Justin Martyr, Dialogus cum Tryphone, 72_3 | 525 |
| `passage_just_tryph_72_4` | Justin Martyr, Dialogus cum Tryphone, 72_4 | 255 |
| `passage_just_tryph_73_1` | Justin Martyr, Dialogus cum Tryphone, 73_1 | 271 |
| `passage_just_tryph_73_2` | Justin Martyr, Dialogus cum Tryphone, 73_2 | 344 |
| `passage_just_tryph_73_3` | Justin Martyr, Dialogus cum Tryphone, 73_3 | 682 |
| `passage_just_tryph_73_4` | Justin Martyr, Dialogus cum Tryphone, 73_4 | 589 |
| `passage_just_tryph_73_5` | Justin Martyr, Dialogus cum Tryphone, 73_5 | 141 |
| `passage_just_tryph_73_6` | Justin Martyr, Dialogus cum Tryphone, 73_6 | 417 |
| `passage_just_tryph_74_1` | Justin Martyr, Dialogus cum Tryphone, 74_1 | 338 |
| `passage_just_tryph_74_2` | Justin Martyr, Dialogus cum Tryphone, 74_2 | 492 |
| `passage_just_tryph_74_3` | Justin Martyr, Dialogus cum Tryphone, 74_3 | 440 |
| `passage_just_tryph_74_4` | Justin Martyr, Dialogus cum Tryphone, 74_4 | 532 |
| `passage_just_tryph_75_1` | Justin Martyr, Dialogus cum Tryphone, 75_1 | 526 |
| `passage_just_tryph_75_2` | Justin Martyr, Dialogus cum Tryphone, 75_2 | 419 |
| `passage_just_tryph_75_3` | Justin Martyr, Dialogus cum Tryphone, 75_3 | 274 |
| `passage_just_tryph_75_4` | Justin Martyr, Dialogus cum Tryphone, 75_4 | 352 |
| `passage_just_tryph_76_1` | Justin Martyr, Dialogus cum Tryphone, 76_1 | 500 |
| `passage_just_tryph_76_2` | Justin Martyr, Dialogus cum Tryphone, 76_2 | 475 |
| `passage_just_tryph_76_3` | Justin Martyr, Dialogus cum Tryphone, 76_3 | 364 |
| `passage_just_tryph_76_4` | Justin Martyr, Dialogus cum Tryphone, 76_4 | 202 |
| `passage_just_tryph_76_5` | Justin Martyr, Dialogus cum Tryphone, 76_5 | 412 |
| `passage_just_tryph_76_6` | Justin Martyr, Dialogus cum Tryphone, 76_6 | 571 |
| `passage_just_tryph_76_7` | Justin Martyr, Dialogus cum Tryphone, 76_7 | 443 |
| `passage_just_tryph_77_1` | Justin Martyr, Dialogus cum Tryphone, 77_1 | 337 |
| `passage_just_tryph_77_2` | Justin Martyr, Dialogus cum Tryphone, 77_2 | 525 |
| `passage_just_tryph_77_3` | Justin Martyr, Dialogus cum Tryphone, 77_3 | 605 |
| `passage_just_tryph_77_4` | Justin Martyr, Dialogus cum Tryphone, 77_4 | 468 |
| `passage_just_tryph_78_1` | Justin Martyr, Dialogus cum Tryphone, 78_1 | 517 |
| `passage_just_tryph_78_10` | Justin Martyr, Dialogus cum Tryphone, 78_10 | 426 |
| `passage_just_tryph_78_11` | Justin Martyr, Dialogus cum Tryphone, 78_11 | 427 |
| `passage_just_tryph_78_2` | Justin Martyr, Dialogus cum Tryphone, 78_2 | 275 |
| `passage_just_tryph_78_3` | Justin Martyr, Dialogus cum Tryphone, 78_3 | 317 |
| `passage_just_tryph_78_4` | Justin Martyr, Dialogus cum Tryphone, 78_4 | 449 |
| `passage_just_tryph_78_5` | Justin Martyr, Dialogus cum Tryphone, 78_5 | 364 |
| `passage_just_tryph_78_6` | Justin Martyr, Dialogus cum Tryphone, 78_6 | 439 |
| `passage_just_tryph_78_7` | Justin Martyr, Dialogus cum Tryphone, 78_7 | 395 |
| `passage_just_tryph_78_8` | Justin Martyr, Dialogus cum Tryphone, 78_8 | 673 |
| `passage_just_tryph_78_9` | Justin Martyr, Dialogus cum Tryphone, 78_9 | 496 |
| `passage_just_tryph_79_1` | Justin Martyr, Dialogus cum Tryphone, 79_1 | 309 |
| `passage_just_tryph_79_2` | Justin Martyr, Dialogus cum Tryphone, 79_2 | 640 |
| `passage_just_tryph_79_3` | Justin Martyr, Dialogus cum Tryphone, 79_3 | 535 |
| `passage_just_tryph_79_4` | Justin Martyr, Dialogus cum Tryphone, 79_4 | 752 |
| `passage_just_tryph_8_1` | Justin Martyr, Dialogus cum Tryphone, 8_1 | 347 |
| `passage_just_tryph_8_2` | Justin Martyr, Dialogus cum Tryphone, 8_2 | 475 |
| `passage_just_tryph_8_3` | Justin Martyr, Dialogus cum Tryphone, 8_3 | 532 |
| `passage_just_tryph_8_4` | Justin Martyr, Dialogus cum Tryphone, 8_4 | 553 |
| `passage_just_tryph_80_1` | Justin Martyr, Dialogus cum Tryphone, 80_1 | 496 |
| `passage_just_tryph_80_2` | Justin Martyr, Dialogus cum Tryphone, 80_2 | 296 |
| `passage_just_tryph_80_3` | Justin Martyr, Dialogus cum Tryphone, 80_3 | 481 |
| `passage_just_tryph_80_4` | Justin Martyr, Dialogus cum Tryphone, 80_4 | 711 |
| `passage_just_tryph_80_5` | Justin Martyr, Dialogus cum Tryphone, 80_5 | 292 |
| `passage_just_tryph_81_1` | Justin Martyr, Dialogus cum Tryphone, 81_1 | 631 |
| `passage_just_tryph_81_2` | Justin Martyr, Dialogus cum Tryphone, 81_2 | 759 |
| `passage_just_tryph_81_3` | Justin Martyr, Dialogus cum Tryphone, 81_3 | 446 |
| `passage_just_tryph_81_4` | Justin Martyr, Dialogus cum Tryphone, 81_4 | 513 |
| `passage_just_tryph_82_1` | Justin Martyr, Dialogus cum Tryphone, 82_1 | 488 |
| `passage_just_tryph_82_2` | Justin Martyr, Dialogus cum Tryphone, 82_2 | 236 |
| `passage_just_tryph_82_3` | Justin Martyr, Dialogus cum Tryphone, 82_3 | 631 |
| `passage_just_tryph_82_4` | Justin Martyr, Dialogus cum Tryphone, 82_4 | 491 |
| `passage_just_tryph_83_1` | Justin Martyr, Dialogus cum Tryphone, 83_1 | 679 |
| `passage_just_tryph_83_2` | Justin Martyr, Dialogus cum Tryphone, 83_2 | 407 |
| `passage_just_tryph_83_3` | Justin Martyr, Dialogus cum Tryphone, 83_3 | 358 |
| `passage_just_tryph_83_4` | Justin Martyr, Dialogus cum Tryphone, 83_4 | 538 |
| `passage_just_tryph_84_1` | Justin Martyr, Dialogus cum Tryphone, 84_1 | 454 |
| `passage_just_tryph_84_2` | Justin Martyr, Dialogus cum Tryphone, 84_2 | 491 |
| `passage_just_tryph_84_3` | Justin Martyr, Dialogus cum Tryphone, 84_3 | 436 |
| `passage_just_tryph_84_4` | Justin Martyr, Dialogus cum Tryphone, 84_4 | 462 |
| `passage_just_tryph_85_1` | Justin Martyr, Dialogus cum Tryphone, 85_1 | 797 |
| `passage_just_tryph_85_2` | Justin Martyr, Dialogus cum Tryphone, 85_2 | 342 |
| `passage_just_tryph_85_3` | Justin Martyr, Dialogus cum Tryphone, 85_3 | 385 |
| `passage_just_tryph_85_4` | Justin Martyr, Dialogus cum Tryphone, 85_4 | 376 |
| `passage_just_tryph_85_5` | Justin Martyr, Dialogus cum Tryphone, 85_5 | 605 |
| `passage_just_tryph_85_6` | Justin Martyr, Dialogus cum Tryphone, 85_6 | 422 |
| `passage_just_tryph_85_7` | Justin Martyr, Dialogus cum Tryphone, 85_7 | 348 |
| `passage_just_tryph_85_8` | Justin Martyr, Dialogus cum Tryphone, 85_8 | 401 |
| `passage_just_tryph_85_9` | Justin Martyr, Dialogus cum Tryphone, 85_9 | 511 |
| `passage_just_tryph_86_1` | Justin Martyr, Dialogus cum Tryphone, 86_1 | 665 |
| `passage_just_tryph_86_2` | Justin Martyr, Dialogus cum Tryphone, 86_2 | 583 |
| `passage_just_tryph_86_3` | Justin Martyr, Dialogus cum Tryphone, 86_3 | 557 |
| `passage_just_tryph_86_4` | Justin Martyr, Dialogus cum Tryphone, 86_4 | 413 |
| `passage_just_tryph_86_5` | Justin Martyr, Dialogus cum Tryphone, 86_5 | 282 |
| `passage_just_tryph_86_6` | Justin Martyr, Dialogus cum Tryphone, 86_6 | 575 |
| `passage_just_tryph_87_1` | Justin Martyr, Dialogus cum Tryphone, 87_1 | 193 |
| `passage_just_tryph_87_2` | Justin Martyr, Dialogus cum Tryphone, 87_2 | 670 |
| `passage_just_tryph_87_3` | Justin Martyr, Dialogus cum Tryphone, 87_3 | 518 |
| `passage_just_tryph_87_4` | Justin Martyr, Dialogus cum Tryphone, 87_4 | 526 |
| `passage_just_tryph_87_5` | Justin Martyr, Dialogus cum Tryphone, 87_5 | 348 |
| `passage_just_tryph_87_6` | Justin Martyr, Dialogus cum Tryphone, 87_6 | 437 |
| `passage_just_tryph_88_1` | Justin Martyr, Dialogus cum Tryphone, 88_1 | 423 |
| `passage_just_tryph_88_2` | Justin Martyr, Dialogus cum Tryphone, 88_2 | 392 |
| `passage_just_tryph_88_3` | Justin Martyr, Dialogus cum Tryphone, 88_3 | 333 |
| `passage_just_tryph_88_4` | Justin Martyr, Dialogus cum Tryphone, 88_4 | 357 |
| `passage_just_tryph_88_5` | Justin Martyr, Dialogus cum Tryphone, 88_5 | 324 |
| `passage_just_tryph_88_6` | Justin Martyr, Dialogus cum Tryphone, 88_6 | 305 |
| `passage_just_tryph_88_7` | Justin Martyr, Dialogus cum Tryphone, 88_7 | 517 |
| `passage_just_tryph_88_8` | Justin Martyr, Dialogus cum Tryphone, 88_8 | 834 |
| `passage_just_tryph_89_1` | Justin Martyr, Dialogus cum Tryphone, 89_1 | 257 |
| `passage_just_tryph_89_2` | Justin Martyr, Dialogus cum Tryphone, 89_2 | 358 |
| `passage_just_tryph_89_3` | Justin Martyr, Dialogus cum Tryphone, 89_3 | 600 |
| `passage_just_tryph_9_1` | Justin Martyr, Dialogus cum Tryphone, 9_1 | 526 |
| `passage_just_tryph_9_2` | Justin Martyr, Dialogus cum Tryphone, 9_2 | 443 |
| `passage_just_tryph_9_3` | Justin Martyr, Dialogus cum Tryphone, 9_3 | 389 |
| `passage_just_tryph_90_1` | Justin Martyr, Dialogus cum Tryphone, 90_1 | 346 |
| `passage_just_tryph_90_2` | Justin Martyr, Dialogus cum Tryphone, 90_2 | 283 |
| `passage_just_tryph_90_3` | Justin Martyr, Dialogus cum Tryphone, 90_3 | 147 |
| `passage_just_tryph_90_4` | Justin Martyr, Dialogus cum Tryphone, 90_4 | 479 |
| `passage_just_tryph_90_5` | Justin Martyr, Dialogus cum Tryphone, 90_5 | 461 |
| `passage_just_tryph_91_1` | Justin Martyr, Dialogus cum Tryphone, 91_1 | 635 |
| `passage_just_tryph_91_2` | Justin Martyr, Dialogus cum Tryphone, 91_2 | 500 |
| `passage_just_tryph_91_3` | Justin Martyr, Dialogus cum Tryphone, 91_3 | 563 |
| `passage_just_tryph_91_4` | Justin Martyr, Dialogus cum Tryphone, 91_4 | 644 |
| `passage_just_tryph_92_1` | Justin Martyr, Dialogus cum Tryphone, 92_1 | 310 |
| `passage_just_tryph_92_2` | Justin Martyr, Dialogus cum Tryphone, 92_2 | 631 |
| `passage_just_tryph_92_3` | Justin Martyr, Dialogus cum Tryphone, 92_3 | 340 |
| `passage_just_tryph_92_4` | Justin Martyr, Dialogus cum Tryphone, 92_4 | 529 |
| `passage_just_tryph_92_5` | Justin Martyr, Dialogus cum Tryphone, 92_5 | 547 |
| `passage_just_tryph_92_6` | Justin Martyr, Dialogus cum Tryphone, 92_6 | 247 |
| `passage_just_tryph_93_1` | Justin Martyr, Dialogus cum Tryphone, 93_1 | 471 |
| `passage_just_tryph_93_2` | Justin Martyr, Dialogus cum Tryphone, 93_2 | 847 |
| `passage_just_tryph_93_3` | Justin Martyr, Dialogus cum Tryphone, 93_3 | 397 |
| `passage_just_tryph_93_4` | Justin Martyr, Dialogus cum Tryphone, 93_4 | 514 |
| `passage_just_tryph_93_5` | Justin Martyr, Dialogus cum Tryphone, 93_5 | 262 |
| `passage_just_tryph_94_1` | Justin Martyr, Dialogus cum Tryphone, 94_1 | 347 |
| `passage_just_tryph_94_2` | Justin Martyr, Dialogus cum Tryphone, 94_2 | 380 |
| `passage_just_tryph_94_3` | Justin Martyr, Dialogus cum Tryphone, 94_3 | 236 |
| `passage_just_tryph_94_4` | Justin Martyr, Dialogus cum Tryphone, 94_4 | 307 |
| `passage_just_tryph_94_5` | Justin Martyr, Dialogus cum Tryphone, 94_5 | 274 |
| `passage_just_tryph_95_1` | Justin Martyr, Dialogus cum Tryphone, 95_1 | 567 |
| `passage_just_tryph_95_2` | Justin Martyr, Dialogus cum Tryphone, 95_2 | 562 |
| `passage_just_tryph_95_3` | Justin Martyr, Dialogus cum Tryphone, 95_3 | 341 |
| `passage_just_tryph_95_4` | Justin Martyr, Dialogus cum Tryphone, 95_4 | 245 |
| `passage_just_tryph_96_1` | Justin Martyr, Dialogus cum Tryphone, 96_1 | 446 |
| `passage_just_tryph_96_2` | Justin Martyr, Dialogus cum Tryphone, 96_2 | 581 |
| `passage_just_tryph_96_3` | Justin Martyr, Dialogus cum Tryphone, 96_3 | 461 |
| `passage_just_tryph_97_1` | Justin Martyr, Dialogus cum Tryphone, 97_1 | 511 |
| `passage_just_tryph_97_2` | Justin Martyr, Dialogus cum Tryphone, 97_2 | 350 |
| `passage_just_tryph_97_3` | Justin Martyr, Dialogus cum Tryphone, 97_3 | 621 |
| `passage_just_tryph_97_4` | Justin Martyr, Dialogus cum Tryphone, 97_4 | 276 |
| `passage_just_tryph_98_1` | Justin Martyr, Dialogus cum Tryphone, 98_1 | 317 |
| `passage_just_tryph_98_2` | Justin Martyr, Dialogus cum Tryphone, 98_2 | 406 |
| `passage_just_tryph_98_3` | Justin Martyr, Dialogus cum Tryphone, 98_3 | 432 |
| `passage_just_tryph_98_4` | Justin Martyr, Dialogus cum Tryphone, 98_4 | 523 |
| `passage_just_tryph_98_5` | Justin Martyr, Dialogus cum Tryphone, 98_5 | 537 |
| `passage_just_tryph_99_1` | Justin Martyr, Dialogus cum Tryphone, 99_1 | 359 |
| `passage_just_tryph_99_2` | Justin Martyr, Dialogus cum Tryphone, 99_2 | 608 |
| `passage_just_tryph_99_3` | Justin Martyr, Dialogus cum Tryphone, 99_3 | 496 |

### Marcus Aurelius — Meditations (Ta eis heauton)

- **Language:** Greek
- **Passages:** 577
- **Characters:** 180,177
- **Canonical ID:** `urn:cts:greekLit:tlg0562.tlg001`

| node_id | label | chars |
|---------|-------|-------|
| `passage_marc_aur_1_1_1` | Marcus Aurelius, Meditations (Ta eis heauton), 1.1.1 | 48 |
| `passage_marc_aur_1_10_1` | Marcus Aurelius, Meditations (Ta eis heauton), 1.10.1 | 354 |
| `passage_marc_aur_1_11_1` | Marcus Aurelius, Meditations (Ta eis heauton), 1.11.1 | 162 |
| `passage_marc_aur_1_12_1` | Marcus Aurelius, Meditations (Ta eis heauton), 1.12.1 | 260 |
| `passage_marc_aur_1_13_1` | Marcus Aurelius, Meditations (Ta eis heauton), 1.13.1 | 272 |
| `passage_marc_aur_1_14_1` | Marcus Aurelius, Meditations (Ta eis heauton), 1.14.1 | 290 |
| `passage_marc_aur_1_14_2` | Marcus Aurelius, Meditations (Ta eis heauton), 1.14.2 | 337 |
| `passage_marc_aur_1_15_1` | Marcus Aurelius, Meditations (Ta eis heauton), 1.15.1 | 230 |
| `passage_marc_aur_1_15_2` | Marcus Aurelius, Meditations (Ta eis heauton), 1.15.2 | 239 |
| `passage_marc_aur_1_15_3` | Marcus Aurelius, Meditations (Ta eis heauton), 1.15.3 | 244 |
| `passage_marc_aur_1_16_1` | Marcus Aurelius, Meditations (Ta eis heauton), 1.16.1 | 322 |
| `passage_marc_aur_1_16_10` | Marcus Aurelius, Meditations (Ta eis heauton), 1.16.10 | 126 |
| `passage_marc_aur_1_16_2` | Marcus Aurelius, Meditations (Ta eis heauton), 1.16.2 | 470 |
| `passage_marc_aur_1_16_3` | Marcus Aurelius, Meditations (Ta eis heauton), 1.16.3 | 432 |
| `passage_marc_aur_1_16_4` | Marcus Aurelius, Meditations (Ta eis heauton), 1.16.4 | 355 |
| `passage_marc_aur_1_16_5` | Marcus Aurelius, Meditations (Ta eis heauton), 1.16.5 | 377 |
| `passage_marc_aur_1_16_6` | Marcus Aurelius, Meditations (Ta eis heauton), 1.16.6 | 314 |
| `passage_marc_aur_1_16_7` | Marcus Aurelius, Meditations (Ta eis heauton), 1.16.7 | 504 |
| `passage_marc_aur_1_16_8` | Marcus Aurelius, Meditations (Ta eis heauton), 1.16.8 | 274 |
| `passage_marc_aur_1_16_9` | Marcus Aurelius, Meditations (Ta eis heauton), 1.16.9 | 378 |
| `passage_marc_aur_1_17_1` | Marcus Aurelius, Meditations (Ta eis heauton), 1.17.1 | 355 |
| `passage_marc_aur_1_17_2` | Marcus Aurelius, Meditations (Ta eis heauton), 1.17.2 | 146 |
| `passage_marc_aur_1_17_3` | Marcus Aurelius, Meditations (Ta eis heauton), 1.17.3 | 400 |
| `passage_marc_aur_1_17_4` | Marcus Aurelius, Meditations (Ta eis heauton), 1.17.4 | 344 |
| `passage_marc_aur_1_17_5` | Marcus Aurelius, Meditations (Ta eis heauton), 1.17.5 | 193 |
| `passage_marc_aur_1_17_6` | Marcus Aurelius, Meditations (Ta eis heauton), 1.17.6 | 323 |
| `passage_marc_aur_1_17_7` | Marcus Aurelius, Meditations (Ta eis heauton), 1.17.7 | 304 |
| `passage_marc_aur_1_17_8` | Marcus Aurelius, Meditations (Ta eis heauton), 1.17.8 | 339 |
| `passage_marc_aur_1_17_9` | Marcus Aurelius, Meditations (Ta eis heauton), 1.17.9 | 351 |
| `passage_marc_aur_1_2_1` | Marcus Aurelius, Meditations (Ta eis heauton), 1.2.1 | 76 |
| `passage_marc_aur_1_3_1` | Marcus Aurelius, Meditations (Ta eis heauton), 1.3.1 | 194 |
| `passage_marc_aur_1_4_1` | Marcus Aurelius, Meditations (Ta eis heauton), 1.4.1 | 161 |
| `passage_marc_aur_1_5_1` | Marcus Aurelius, Meditations (Ta eis heauton), 1.5.1 | 191 |
| `passage_marc_aur_1_6_1` | Marcus Aurelius, Meditations (Ta eis heauton), 1.6.1 | 455 |
| `passage_marc_aur_1_7_1` | Marcus Aurelius, Meditations (Ta eis heauton), 1.7.1 | 271 |
| `passage_marc_aur_1_7_2` | Marcus Aurelius, Meditations (Ta eis heauton), 1.7.2 | 219 |
| `passage_marc_aur_1_7_3` | Marcus Aurelius, Meditations (Ta eis heauton), 1.7.3 | 316 |
| `passage_marc_aur_1_8_1` | Marcus Aurelius, Meditations (Ta eis heauton), 1.8.1 | 297 |
| `passage_marc_aur_1_8_2` | Marcus Aurelius, Meditations (Ta eis heauton), 1.8.2 | 300 |
| `passage_marc_aur_1_9_1` | Marcus Aurelius, Meditations (Ta eis heauton), 1.9.1 | 230 |
| `passage_marc_aur_1_9_2` | Marcus Aurelius, Meditations (Ta eis heauton), 1.9.2 | 253 |
| `passage_marc_aur_1_9_3` | Marcus Aurelius, Meditations (Ta eis heauton), 1.9.3 | 171 |
| `passage_marc_aur_10_1_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.1.1 | 889 |
| `passage_marc_aur_10_10_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.10.1 | 173 |
| `passage_marc_aur_10_11_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.11.1 | 691 |
| `passage_marc_aur_10_12_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.12.1 | 461 |
| `passage_marc_aur_10_13_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.13.1 | 479 |
| `passage_marc_aur_10_14_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.14.1 | 181 |
| `passage_marc_aur_10_15_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.15.1 | 253 |
| `passage_marc_aur_10_16_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.16.1 | 87 |
| `passage_marc_aur_10_17_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.17.1 | 152 |
| `passage_marc_aur_10_18_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.18.1 | 160 |
| `passage_marc_aur_10_19_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.19.1 | 239 |
| `passage_marc_aur_10_2_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.2.1 | 374 |
| `passage_marc_aur_10_20_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.20.1 | 84 |
| `passage_marc_aur_10_21_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.21.1 | 181 |
| `passage_marc_aur_10_22_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.22.1 | 137 |
| `passage_marc_aur_10_23_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.23.1 | 240 |
| `passage_marc_aur_10_24_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.24.1 | 230 |
| `passage_marc_aur_10_25_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.25.1 | 317 |
| `passage_marc_aur_10_26_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.26.1 | 422 |
| `passage_marc_aur_10_27_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.27.1 | 359 |
| `passage_marc_aur_10_28_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.28.1 | 296 |
| `passage_marc_aur_10_29_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.29.1 | 103 |
| `passage_marc_aur_10_3_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.3.1 | 410 |
| `passage_marc_aur_10_30_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.30.1 | 301 |
| `passage_marc_aur_10_31_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.31.1 | 823 |
| `passage_marc_aur_10_32_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.32.1 | 279 |
| `passage_marc_aur_10_33_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.33.1 | 426 |
| `passage_marc_aur_10_33_2` | Marcus Aurelius, Meditations (Ta eis heauton), 10.33.2 | 305 |
| `passage_marc_aur_10_33_3` | Marcus Aurelius, Meditations (Ta eis heauton), 10.33.3 | 307 |
| `passage_marc_aur_10_33_4` | Marcus Aurelius, Meditations (Ta eis heauton), 10.33.4 | 505 |
| `passage_marc_aur_10_34_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.34.1 | 642 |
| `passage_marc_aur_10_35_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.35.1 | 512 |
| `passage_marc_aur_10_36_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.36.1 | 1,124 |
| `passage_marc_aur_10_37_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.37.1 | 155 |
| `passage_marc_aur_10_38_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.38.1 | 464 |
| `passage_marc_aur_10_4_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.4.1 | 116 |
| `passage_marc_aur_10_5_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.5.1 | 150 |
| `passage_marc_aur_10_6_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.6.1 | 464 |
| `passage_marc_aur_10_6_2` | Marcus Aurelius, Meditations (Ta eis heauton), 10.6.2 | 466 |
| `passage_marc_aur_10_7_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.7.1 | 474 |
| `passage_marc_aur_10_7_2` | Marcus Aurelius, Meditations (Ta eis heauton), 10.7.2 | 525 |
| `passage_marc_aur_10_7_3` | Marcus Aurelius, Meditations (Ta eis heauton), 10.7.3 | 323 |
| `passage_marc_aur_10_8_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.8.1 | 495 |
| `passage_marc_aur_10_8_2` | Marcus Aurelius, Meditations (Ta eis heauton), 10.8.2 | 455 |
| `passage_marc_aur_10_8_3` | Marcus Aurelius, Meditations (Ta eis heauton), 10.8.3 | 365 |
| `passage_marc_aur_10_8_4` | Marcus Aurelius, Meditations (Ta eis heauton), 10.8.4 | 286 |
| `passage_marc_aur_10_9_1` | Marcus Aurelius, Meditations (Ta eis heauton), 10.9.1 | 604 |
| `passage_marc_aur_11_1_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.1.1 | 482 |
| `passage_marc_aur_11_1_2` | Marcus Aurelius, Meditations (Ta eis heauton), 11.1.2 | 581 |
| `passage_marc_aur_11_10_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.10.1 | 475 |
| `passage_marc_aur_11_11_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.11.1 | 214 |
| `passage_marc_aur_11_12_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.12.1 | 165 |
| `passage_marc_aur_11_13_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.13.1 | 621 |
| `passage_marc_aur_11_14_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.14.1 | 102 |
| `passage_marc_aur_11_15_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.15.1 | 583 |
| `passage_marc_aur_11_16_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.16.1 | 696 |
| `passage_marc_aur_11_17_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.17.1 | 131 |
| `passage_marc_aur_11_18_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.18.1 | 452 |
| `passage_marc_aur_11_18_2` | Marcus Aurelius, Meditations (Ta eis heauton), 11.18.2 | 525 |
| `passage_marc_aur_11_18_3` | Marcus Aurelius, Meditations (Ta eis heauton), 11.18.3 | 632 |
| `passage_marc_aur_11_18_4` | Marcus Aurelius, Meditations (Ta eis heauton), 11.18.4 | 780 |
| `passage_marc_aur_11_18_5` | Marcus Aurelius, Meditations (Ta eis heauton), 11.18.5 | 579 |
| `passage_marc_aur_11_18_6` | Marcus Aurelius, Meditations (Ta eis heauton), 11.18.6 | 229 |
| `passage_marc_aur_11_19_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.19.1 | 482 |
| `passage_marc_aur_11_2_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.2.1 | 452 |
| `passage_marc_aur_11_20_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.20.1 | 433 |
| `passage_marc_aur_11_20_2` | Marcus Aurelius, Meditations (Ta eis heauton), 11.20.2 | 613 |
| `passage_marc_aur_11_21_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.21.1 | 510 |
| `passage_marc_aur_11_22_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.22.1 | 77 |
| `passage_marc_aur_11_23_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.23.1 | 66 |
| `passage_marc_aur_11_24_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.24.1 | 109 |
| `passage_marc_aur_11_25_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.25.1 | 144 |
| `passage_marc_aur_11_26_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.26.1 | 114 |
| `passage_marc_aur_11_27_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.27.1 | 209 |
| `passage_marc_aur_11_28_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.28.1 | 185 |
| `passage_marc_aur_11_29_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.29.1 | 92 |
| `passage_marc_aur_11_3_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.3.1 | 269 |
| `passage_marc_aur_11_30_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.30.1 | 37 |
| `passage_marc_aur_11_31_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.31.1 | 27 |
| `passage_marc_aur_11_32_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.32.1 | 46 |
| `passage_marc_aur_11_33_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.33.1 | 82 |
| `passage_marc_aur_11_34_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.34.1 | 201 |
| `passage_marc_aur_11_35_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.35.1 | 81 |
| `passage_marc_aur_11_36_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.36.1 | 48 |
| `passage_marc_aur_11_37_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.37.1 | 245 |
| `passage_marc_aur_11_38_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.38.1 | 74 |
| `passage_marc_aur_11_39_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.39.1 | 167 |
| `passage_marc_aur_11_4_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.4.1 | 91 |
| `passage_marc_aur_11_5_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.5.1 | 155 |
| `passage_marc_aur_11_6_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.6.1 | 513 |
| `passage_marc_aur_11_6_2` | Marcus Aurelius, Meditations (Ta eis heauton), 11.6.2 | 504 |
| `passage_marc_aur_11_7_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.7.1 | 123 |
| `passage_marc_aur_11_8_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.8.1 | 769 |
| `passage_marc_aur_11_9_1` | Marcus Aurelius, Meditations (Ta eis heauton), 11.9.1 | 537 |
| `passage_marc_aur_12_1_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.1.1 | 554 |
| `passage_marc_aur_12_1_2` | Marcus Aurelius, Meditations (Ta eis heauton), 12.1.2 | 360 |
| `passage_marc_aur_12_10_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.10.1 | 64 |
| `passage_marc_aur_12_11_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.11.1 | 131 |
| `passage_marc_aur_12_12_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.12.1 | 123 |
| `passage_marc_aur_12_13_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.13.1 | 64 |
| `passage_marc_aur_12_14_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.14.1 | 434 |
| `passage_marc_aur_12_15_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.15.1 | 139 |
| `passage_marc_aur_12_16_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.16.1 | 422 |
| `passage_marc_aur_12_17_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.17.1 | 272 |
| `passage_marc_aur_12_19_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.19.1 | 202 |
| `passage_marc_aur_12_2_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.2.1 | 389 |
| `passage_marc_aur_12_20_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.20.1 | 114 |
| `passage_marc_aur_12_21_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.21.1 | 185 |
| `passage_marc_aur_12_22_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.22.1 | 139 |
| `passage_marc_aur_12_23_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.23.1 | 841 |
| `passage_marc_aur_12_24_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.24.1 | 630 |
| `passage_marc_aur_12_25_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.25.1 | 59 |
| `passage_marc_aur_12_26_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.26.1 | 583 |
| `passage_marc_aur_12_27_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.27.1 | 628 |
| `passage_marc_aur_12_28_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.28.1 | 305 |
| `passage_marc_aur_12_29_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.29.1 | 254 |
| `passage_marc_aur_12_3_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.3.1 | 573 |
| `passage_marc_aur_12_3_2` | Marcus Aurelius, Meditations (Ta eis heauton), 12.3.2 | 355 |
| `passage_marc_aur_12_30_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.30.1 | 481 |
| `passage_marc_aur_12_31_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.31.1 | 322 |
| `passage_marc_aur_12_32_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.32.1 | 311 |
| `passage_marc_aur_12_33_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.33.1 | 121 |
| `passage_marc_aur_12_34_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.34.1 | 124 |
| `passage_marc_aur_12_35_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.35.1 | 199 |
| `passage_marc_aur_12_36_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.36.1 | 542 |
| `passage_marc_aur_12_4_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.4.1 | 386 |
| `passage_marc_aur_12_5_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.5.1 | 814 |
| `passage_marc_aur_12_6_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.6.1 | 159 |
| `passage_marc_aur_12_7_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.7.1 | 151 |
| `passage_marc_aur_12_8_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.8.1 | 188 |
| `passage_marc_aur_12_9_1` | Marcus Aurelius, Meditations (Ta eis heauton), 12.9.1 | 191 |
| `passage_marc_aur_2_1_1` | Marcus Aurelius, Meditations (Ta eis heauton), 2.1.1 | 691 |
| `passage_marc_aur_2_10_1` | Marcus Aurelius, Meditations (Ta eis heauton), 2.10.1 | 641 |
| `passage_marc_aur_2_11_1` | Marcus Aurelius, Meditations (Ta eis heauton), 2.11.1 | 281 |
| `passage_marc_aur_2_11_2` | Marcus Aurelius, Meditations (Ta eis heauton), 2.11.2 | 301 |
| `passage_marc_aur_2_11_3` | Marcus Aurelius, Meditations (Ta eis heauton), 2.11.3 | 276 |
| `passage_marc_aur_2_11_4` | Marcus Aurelius, Meditations (Ta eis heauton), 2.11.4 | 205 |
| `passage_marc_aur_2_12_1` | Marcus Aurelius, Meditations (Ta eis heauton), 2.12.1 | 735 |
| `passage_marc_aur_2_13_1` | Marcus Aurelius, Meditations (Ta eis heauton), 2.13.1 | 592 |
| `passage_marc_aur_2_14_1` | Marcus Aurelius, Meditations (Ta eis heauton), 2.14.1 | 406 |
| `passage_marc_aur_2_14_2` | Marcus Aurelius, Meditations (Ta eis heauton), 2.14.2 | 380 |
| `passage_marc_aur_2_15_1` | Marcus Aurelius, Meditations (Ta eis heauton), 2.15.1 | 161 |
| `passage_marc_aur_2_16_1` | Marcus Aurelius, Meditations (Ta eis heauton), 2.16.1 | 729 |
| `passage_marc_aur_2_17_1` | Marcus Aurelius, Meditations (Ta eis heauton), 2.17.1 | 335 |
| `passage_marc_aur_2_17_2` | Marcus Aurelius, Meditations (Ta eis heauton), 2.17.2 | 663 |
| `passage_marc_aur_2_2_1` | Marcus Aurelius, Meditations (Ta eis heauton), 2.2.1 | 549 |
| `passage_marc_aur_2_3_1` | Marcus Aurelius, Meditations (Ta eis heauton), 2.3.1 | 514 |
| `passage_marc_aur_2_4_1` | Marcus Aurelius, Meditations (Ta eis heauton), 2.4.1 | 313 |
| `passage_marc_aur_2_5_1` | Marcus Aurelius, Meditations (Ta eis heauton), 2.5.1 | 571 |
| `passage_marc_aur_2_6_1` | Marcus Aurelius, Meditations (Ta eis heauton), 2.6.1 | 205 |
| `passage_marc_aur_2_7_1` | Marcus Aurelius, Meditations (Ta eis heauton), 2.7.1 | 281 |
| `passage_marc_aur_2_8_1` | Marcus Aurelius, Meditations (Ta eis heauton), 2.8.1 | 168 |
| `passage_marc_aur_2_9_1` | Marcus Aurelius, Meditations (Ta eis heauton), 2.9.1 | 221 |
| `passage_marc_aur_3_1_1` | Marcus Aurelius, Meditations (Ta eis heauton), 3.1.1 | 825 |
| `passage_marc_aur_3_10_1` | Marcus Aurelius, Meditations (Ta eis heauton), 3.10.1 | 373 |
| `passage_marc_aur_3_11_1` | Marcus Aurelius, Meditations (Ta eis heauton), 3.11.1 | 294 |
| `passage_marc_aur_3_11_2` | Marcus Aurelius, Meditations (Ta eis heauton), 3.11.2 | 572 |
| `passage_marc_aur_3_11_3` | Marcus Aurelius, Meditations (Ta eis heauton), 3.11.3 | 407 |
| `passage_marc_aur_3_12_1` | Marcus Aurelius, Meditations (Ta eis heauton), 3.12.1 | 369 |
| `passage_marc_aur_3_13_1` | Marcus Aurelius, Meditations (Ta eis heauton), 3.13.1 | 331 |
| `passage_marc_aur_3_14_1` | Marcus Aurelius, Meditations (Ta eis heauton), 3.14.1 | 281 |
| `passage_marc_aur_3_15_1` | Marcus Aurelius, Meditations (Ta eis heauton), 3.15.1 | 143 |
| `passage_marc_aur_3_16_1` | Marcus Aurelius, Meditations (Ta eis heauton), 3.16.1 | 372 |
| `passage_marc_aur_3_16_2` | Marcus Aurelius, Meditations (Ta eis heauton), 3.16.2 | 589 |
| `passage_marc_aur_3_2_1` | Marcus Aurelius, Meditations (Ta eis heauton), 3.2.1 | 301 |
| `passage_marc_aur_3_2_2` | Marcus Aurelius, Meditations (Ta eis heauton), 3.2.2 | 381 |
| `passage_marc_aur_3_2_3` | Marcus Aurelius, Meditations (Ta eis heauton), 3.2.3 | 506 |
| `passage_marc_aur_3_3_1` | Marcus Aurelius, Meditations (Ta eis heauton), 3.3.1 | 772 |
| `passage_marc_aur_3_4_1` | Marcus Aurelius, Meditations (Ta eis heauton), 3.4.1 | 335 |
| `passage_marc_aur_3_4_2` | Marcus Aurelius, Meditations (Ta eis heauton), 3.4.2 | 505 |
| `passage_marc_aur_3_4_3` | Marcus Aurelius, Meditations (Ta eis heauton), 3.4.3 | 766 |
| `passage_marc_aur_3_4_4` | Marcus Aurelius, Meditations (Ta eis heauton), 3.4.4 | 441 |
| `passage_marc_aur_3_5_1` | Marcus Aurelius, Meditations (Ta eis heauton), 3.5.1 | 535 |
| `passage_marc_aur_3_6_1` | Marcus Aurelius, Meditations (Ta eis heauton), 3.6.1 | 359 |
| `passage_marc_aur_3_6_2` | Marcus Aurelius, Meditations (Ta eis heauton), 3.6.2 | 467 |
| `passage_marc_aur_3_6_3` | Marcus Aurelius, Meditations (Ta eis heauton), 3.6.3 | 459 |
| `passage_marc_aur_3_7_1` | Marcus Aurelius, Meditations (Ta eis heauton), 3.7.1 | 760 |
| `passage_marc_aur_3_8_1` | Marcus Aurelius, Meditations (Ta eis heauton), 3.8.1 | 341 |
| `passage_marc_aur_3_9_1` | Marcus Aurelius, Meditations (Ta eis heauton), 3.9.1 | 246 |
| `passage_marc_aur_4_1_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.1.1 | 460 |
| `passage_marc_aur_4_10_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.10.1 | 325 |
| `passage_marc_aur_4_11_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.11.1 | 112 |
| `passage_marc_aur_4_12_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.12.1 | 380 |
| `passage_marc_aur_4_13_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.13.1 | 85 |
| `passage_marc_aur_4_14_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.14.1 | 120 |
| `passage_marc_aur_4_15_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.15.1 | 99 |
| `passage_marc_aur_4_16_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.16.1 | 129 |
| `passage_marc_aur_4_17_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.17.1 | 83 |
| `passage_marc_aur_4_18_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.18.1 | 242 |
| `passage_marc_aur_4_19_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.19.1 | 491 |
| `passage_marc_aur_4_2_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.2.1 | 82 |
| `passage_marc_aur_4_20_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.20.1 | 568 |
| `passage_marc_aur_4_21_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.21.1 | 510 |
| `passage_marc_aur_4_21_2` | Marcus Aurelius, Meditations (Ta eis heauton), 4.21.2 | 414 |
| `passage_marc_aur_4_22_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.22.1 | 108 |
| `passage_marc_aur_4_23_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.23.1 | 267 |
| `passage_marc_aur_4_24_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.24.1 | 554 |
| `passage_marc_aur_4_25_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.25.1 | 163 |
| `passage_marc_aur_4_26_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.26.1 | 287 |
| `passage_marc_aur_4_27_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.27.1 | 202 |
| `passage_marc_aur_4_28_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.28.1 | 130 |
| `passage_marc_aur_4_29_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.29.1 | 474 |
| `passage_marc_aur_4_3_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.3.1 | 619 |
| `passage_marc_aur_4_3_2` | Marcus Aurelius, Meditations (Ta eis heauton), 4.3.2 | 679 |
| `passage_marc_aur_4_3_3` | Marcus Aurelius, Meditations (Ta eis heauton), 4.3.3 | 356 |
| `passage_marc_aur_4_3_4` | Marcus Aurelius, Meditations (Ta eis heauton), 4.3.4 | 557 |
| `passage_marc_aur_4_30_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.30.1 | 170 |
| `passage_marc_aur_4_31_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.31.1 | 205 |
| `passage_marc_aur_4_32_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.32.1 | 406 |
| `passage_marc_aur_4_32_2` | Marcus Aurelius, Meditations (Ta eis heauton), 4.32.2 | 580 |
| `passage_marc_aur_4_33_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.33.1 | 710 |
| `passage_marc_aur_4_34_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.34.1 | 84 |
| `passage_marc_aur_4_35_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.35.1 | 54 |
| `passage_marc_aur_4_36_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.36.1 | 296 |
| `passage_marc_aur_4_37_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.37.1 | 159 |
| `passage_marc_aur_4_38_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.38.1 | 84 |
| `passage_marc_aur_4_39_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.39.1 | 537 |
| `passage_marc_aur_4_4_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.4.1 | 717 |
| `passage_marc_aur_4_40_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.40.1 | 242 |
| `passage_marc_aur_4_41_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.41.1 | 49 |
| `passage_marc_aur_4_42_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.42.1 | 92 |
| `passage_marc_aur_4_43_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.43.1 | 138 |
| `passage_marc_aur_4_44_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.44.1 | 190 |
| `passage_marc_aur_4_45_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.45.1 | 280 |
| `passage_marc_aur_4_46_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.46.1 | 491 |
| `passage_marc_aur_4_47_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.47.1 | 257 |
| `passage_marc_aur_4_48_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.48.1 | 450 |
| `passage_marc_aur_4_48_2` | Marcus Aurelius, Meditations (Ta eis heauton), 4.48.2 | 401 |
| `passage_marc_aur_4_49_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.49.1 | 599 |
| `passage_marc_aur_4_49_2` | Marcus Aurelius, Meditations (Ta eis heauton), 4.49.2 | 356 |
| `passage_marc_aur_4_5_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.5.1 | 208 |
| `passage_marc_aur_4_50_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.50.1 | 505 |
| `passage_marc_aur_4_51_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.51.1 | 192 |
| `passage_marc_aur_4_6_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.6.1 | 234 |
| `passage_marc_aur_4_7_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.7.1 | 72 |
| `passage_marc_aur_4_8_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.8.1 | 116 |
| `passage_marc_aur_4_9_1` | Marcus Aurelius, Meditations (Ta eis heauton), 4.9.1 | 48 |
| `passage_marc_aur_5_1_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.1.1 | 556 |
| `passage_marc_aur_5_1_2` | Marcus Aurelius, Meditations (Ta eis heauton), 5.1.2 | 305 |
| `passage_marc_aur_5_1_3` | Marcus Aurelius, Meditations (Ta eis heauton), 5.1.3 | 435 |
| `passage_marc_aur_5_10_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.10.1 | 511 |
| `passage_marc_aur_5_10_2` | Marcus Aurelius, Meditations (Ta eis heauton), 5.10.2 | 511 |
| `passage_marc_aur_5_11_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.11.1 | 273 |
| `passage_marc_aur_5_12_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.12.1 | 777 |
| `passage_marc_aur_5_13_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.13.1 | 446 |
| `passage_marc_aur_5_14_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.14.1 | 251 |
| `passage_marc_aur_5_15_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.15.1 | 673 |
| `passage_marc_aur_5_16_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.16.1 | 649 |
| `passage_marc_aur_5_17_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.17.1 | 82 |
| `passage_marc_aur_5_18_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.18.1 | 223 |
| `passage_marc_aur_5_19_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.19.1 | 227 |
| `passage_marc_aur_5_2_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.2.1 | 106 |
| `passage_marc_aur_5_20_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.20.1 | 539 |
| `passage_marc_aur_5_21_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.21.1 | 250 |
| `passage_marc_aur_5_22_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.22.1 | 270 |
| `passage_marc_aur_5_23_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.23.1 | 423 |
| `passage_marc_aur_5_24_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.24.1 | 164 |
| `passage_marc_aur_5_25_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.25.1 | 171 |
| `passage_marc_aur_5_26_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.26.1 | 436 |
| `passage_marc_aur_5_27_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.27.1 | 247 |
| `passage_marc_aur_5_28_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.28.1 | 414 |
| `passage_marc_aur_5_29_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.29.1 | 315 |
| `passage_marc_aur_5_3_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.3.1 | 348 |
| `passage_marc_aur_5_30_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.30.1 | 226 |
| `passage_marc_aur_5_31_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.31.1 | 460 |
| `passage_marc_aur_5_32_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.32.1 | 246 |
| `passage_marc_aur_5_33_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.33.1 | 800 |
| `passage_marc_aur_5_34_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.34.1 | 281 |
| `passage_marc_aur_5_35_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.35.1 | 136 |
| `passage_marc_aur_5_36_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.36.1 | 569 |
| `passage_marc_aur_5_4_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.4.1 | 332 |
| `passage_marc_aur_5_5_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.5.1 | 805 |
| `passage_marc_aur_5_6_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.6.1 | 357 |
| `passage_marc_aur_5_6_2` | Marcus Aurelius, Meditations (Ta eis heauton), 5.6.2 | 670 |
| `passage_marc_aur_5_7_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.7.1 | 134 |
| `passage_marc_aur_5_8_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.8.1 | 383 |
| `passage_marc_aur_5_8_2` | Marcus Aurelius, Meditations (Ta eis heauton), 5.8.2 | 344 |
| `passage_marc_aur_5_8_3` | Marcus Aurelius, Meditations (Ta eis heauton), 5.8.3 | 256 |
| `passage_marc_aur_5_8_4` | Marcus Aurelius, Meditations (Ta eis heauton), 5.8.4 | 375 |
| `passage_marc_aur_5_8_5` | Marcus Aurelius, Meditations (Ta eis heauton), 5.8.5 | 512 |
| `passage_marc_aur_5_9_1` | Marcus Aurelius, Meditations (Ta eis heauton), 5.9.1 | 819 |
| `passage_marc_aur_6_1_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.1.1 | 228 |
| `passage_marc_aur_6_10_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.10.1 | 351 |
| `passage_marc_aur_6_11_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.11.1 | 201 |
| `passage_marc_aur_6_12_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.12.1 | 272 |
| `passage_marc_aur_6_13_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.13.1 | 803 |
| `passage_marc_aur_6_14_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.14.1 | 570 |
| `passage_marc_aur_6_15_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.15.1 | 716 |
| `passage_marc_aur_6_16_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.16.1 | 252 |
| `passage_marc_aur_6_16_2` | Marcus Aurelius, Meditations (Ta eis heauton), 6.16.2 | 282 |
| `passage_marc_aur_6_16_3` | Marcus Aurelius, Meditations (Ta eis heauton), 6.16.3 | 274 |
| `passage_marc_aur_6_16_4` | Marcus Aurelius, Meditations (Ta eis heauton), 6.16.4 | 372 |
| `passage_marc_aur_6_16_5` | Marcus Aurelius, Meditations (Ta eis heauton), 6.16.5 | 184 |
| `passage_marc_aur_6_17_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.17.1 | 135 |
| `passage_marc_aur_6_18_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.18.1 | 311 |
| `passage_marc_aur_6_19_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.19.1 | 144 |
| `passage_marc_aur_6_2_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.2.1 | 295 |
| `passage_marc_aur_6_20_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.20.1 | 418 |
| `passage_marc_aur_6_21_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.21.1 | 212 |
| `passage_marc_aur_6_22_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.22.1 | 112 |
| `passage_marc_aur_6_23_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.23.1 | 292 |
| `passage_marc_aur_6_24_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.24.1 | 185 |
| `passage_marc_aur_6_25_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.25.1 | 234 |
| `passage_marc_aur_6_26_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.26.1 | 388 |
| `passage_marc_aur_6_27_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.27.1 | 302 |
| `passage_marc_aur_6_28_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.28.1 | 127 |
| `passage_marc_aur_6_29_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.29.1 | 77 |
| `passage_marc_aur_6_3_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.3.1 | 76 |
| `passage_marc_aur_6_30_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.30.1 | 370 |
| `passage_marc_aur_6_30_2` | Marcus Aurelius, Meditations (Ta eis heauton), 6.30.2 | 227 |
| `passage_marc_aur_6_30_3` | Marcus Aurelius, Meditations (Ta eis heauton), 6.30.3 | 388 |
| `passage_marc_aur_6_30_4` | Marcus Aurelius, Meditations (Ta eis heauton), 6.30.4 | 417 |
| `passage_marc_aur_6_31_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.31.1 | 137 |
| `passage_marc_aur_6_32_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.32.1 | 332 |
| `passage_marc_aur_6_33_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.33.1 | 260 |
| `passage_marc_aur_6_34_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.34.1 | 61 |
| `passage_marc_aur_6_35_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.35.1 | 314 |
| `passage_marc_aur_6_36_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.36.1 | 479 |
| `passage_marc_aur_6_37_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.37.1 | 114 |
| `passage_marc_aur_6_38_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.38.1 | 258 |
| `passage_marc_aur_6_39_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.39.1 | 113 |
| `passage_marc_aur_6_4_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.4.1 | 101 |
| `passage_marc_aur_6_40_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.40.1 | 361 |
| `passage_marc_aur_6_41_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.41.1 | 448 |
| `passage_marc_aur_6_42_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.42.1 | 631 |
| `passage_marc_aur_6_43_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.43.1 | 143 |
| `passage_marc_aur_6_44_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.44.1 | 418 |
| `passage_marc_aur_6_44_2` | Marcus Aurelius, Meditations (Ta eis heauton), 6.44.2 | 550 |
| `passage_marc_aur_6_45_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.45.1 | 193 |
| `passage_marc_aur_6_46_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.46.1 | 232 |
| `passage_marc_aur_6_47_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.47.1 | 799 |
| `passage_marc_aur_6_48_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.48.1 | 309 |
| `passage_marc_aur_6_49_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.49.1 | 210 |
| `passage_marc_aur_6_5_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.5.1 | 69 |
| `passage_marc_aur_6_50_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.50.1 | 374 |
| `passage_marc_aur_6_51_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.51.1 | 119 |
| `passage_marc_aur_6_52_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.52.1 | 131 |
| `passage_marc_aur_6_53_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.53.1 | 111 |
| `passage_marc_aur_6_54_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.54.1 | 50 |
| `passage_marc_aur_6_55_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.55.1 | 170 |
| `passage_marc_aur_6_56_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.56.1 | 57 |
| `passage_marc_aur_6_57_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.57.1 | 211 |
| `passage_marc_aur_6_58_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.58.1 | 109 |
| `passage_marc_aur_6_59_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.59.1 | 135 |
| `passage_marc_aur_6_6_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.6.1 | 48 |
| `passage_marc_aur_6_7_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.7.1 | 104 |
| `passage_marc_aur_6_8_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.8.1 | 145 |
| `passage_marc_aur_6_9_1` | Marcus Aurelius, Meditations (Ta eis heauton), 6.9.1 | 140 |
| `passage_marc_aur_7_1_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.1.1 | 303 |
| `passage_marc_aur_7_10_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.10.1 | 162 |
| `passage_marc_aur_7_11_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.11.1 | 59 |
| `passage_marc_aur_7_12_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.12.1 | 21 |
| `passage_marc_aur_7_13_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.13.1 | 450 |
| `passage_marc_aur_7_14_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.14.1 | 214 |
| `passage_marc_aur_7_15_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.15.1 | 185 |
| `passage_marc_aur_7_16_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.16.1 | 556 |
| `passage_marc_aur_7_17_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.17.1 | 200 |
| `passage_marc_aur_7_18_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.18.1 | 375 |
| `passage_marc_aur_7_19_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.19.1 | 284 |
| `passage_marc_aur_7_2_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.2.1 | 362 |
| `passage_marc_aur_7_20_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.20.1 | 109 |
| `passage_marc_aur_7_21_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.21.1 | 65 |
| `passage_marc_aur_7_22_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.22.1 | 270 |
| `passage_marc_aur_7_23_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.23.1 | 284 |
| `passage_marc_aur_7_24_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.24.1 | 269 |
| `passage_marc_aur_7_25_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.25.1 | 161 |
| `passage_marc_aur_7_26_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.26.1 | 321 |
| `passage_marc_aur_7_27_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.27.1 | 258 |
| `passage_marc_aur_7_28_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.28.1 | 121 |
| `passage_marc_aur_7_29_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.29.1 | 265 |
| `passage_marc_aur_7_3_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.3.1 | 395 |
| `passage_marc_aur_7_30_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.30.1 | 93 |
| `passage_marc_aur_7_31_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.31.1 | 263 |
| `passage_marc_aur_7_32_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.32.1 | 77 |
| `passage_marc_aur_7_33_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.33.1 | 225 |
| `passage_marc_aur_7_34_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.34.1 | 223 |
| `passage_marc_aur_7_35_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.35.1 | 225 |
| `passage_marc_aur_7_36_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.36.1 | 46 |
| `passage_marc_aur_7_37_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.37.1 | 159 |
| `passage_marc_aur_7_38_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.38.1 | 64 |
| `passage_marc_aur_7_39_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.39.1 | 42 |
| `passage_marc_aur_7_4_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.4.1 | 197 |
| `passage_marc_aur_7_40_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.40.1 | 64 |
| `passage_marc_aur_7_41_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.41.1 | 59 |
| `passage_marc_aur_7_42_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.42.1 | 35 |
| `passage_marc_aur_7_43_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.43.1 | 29 |
| `passage_marc_aur_7_44_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.44.1 | 272 |
| `passage_marc_aur_7_45_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.45.1 | 232 |
| `passage_marc_aur_7_46_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.46.1 | 378 |
| `passage_marc_aur_7_47_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.47.1 | 170 |
| `passage_marc_aur_7_48_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.48.1 | 325 |
| `passage_marc_aur_7_49_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.49.1 | 280 |
| `passage_marc_aur_7_5_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.5.1 | 479 |
| `passage_marc_aur_7_50_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.50.1 | 201 |
| `passage_marc_aur_7_51_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.51.1 | 159 |
| `passage_marc_aur_7_52_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.52.1 | 150 |
| `passage_marc_aur_7_53_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.53.1 | 220 |
| `passage_marc_aur_7_54_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.54.1 | 208 |
| `passage_marc_aur_7_55_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.55.1 | 852 |
| `passage_marc_aur_7_56_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.56.1 | 92 |
| `passage_marc_aur_7_57_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.57.1 | 71 |
| `passage_marc_aur_7_58_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.58.1 | 458 |
| `passage_marc_aur_7_59_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.59.1 | 82 |
| `passage_marc_aur_7_6_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.6.1 | 95 |
| `passage_marc_aur_7_60_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.60.1 | 253 |
| `passage_marc_aur_7_61_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.61.1 | 125 |
| `passage_marc_aur_7_62_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.62.1 | 213 |
| `passage_marc_aur_7_63_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.63.1 | 203 |
| `passage_marc_aur_7_64_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.64.1 | 499 |
| `passage_marc_aur_7_65_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.65.1 | 91 |
| `passage_marc_aur_7_66_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.66.1 | 703 |
| `passage_marc_aur_7_67_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.67.1 | 395 |
| `passage_marc_aur_7_68_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.68.1 | 652 |
| `passage_marc_aur_7_69_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.69.1 | 121 |
| `passage_marc_aur_7_7_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.7.1 | 189 |
| `passage_marc_aur_7_70_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.70.1 | 246 |
| `passage_marc_aur_7_71_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.71.1 | 106 |
| `passage_marc_aur_7_72_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.72.1 | 108 |
| `passage_marc_aur_7_73_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.73.1 | 143 |
| `passage_marc_aur_7_74_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.74.1 | 95 |
| `passage_marc_aur_7_75_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.75.1 | 242 |
| `passage_marc_aur_7_8_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.8.1 | 105 |
| `passage_marc_aur_7_9_1` | Marcus Aurelius, Meditations (Ta eis heauton), 7.9.1 | 349 |
| `passage_marc_aur_8_1_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.1.1 | 956 |
| `passage_marc_aur_8_10_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.10.1 | 262 |
| `passage_marc_aur_8_11_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.11.1 | 156 |
| `passage_marc_aur_8_12_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.12.1 | 270 |
| `passage_marc_aur_8_13_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.13.1 | 88 |
| `passage_marc_aur_8_14_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.14.1 | 308 |
| `passage_marc_aur_8_15_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.15.1 | 205 |
| `passage_marc_aur_8_16_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.16.1 | 168 |
| `passage_marc_aur_8_17_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.17.1 | 275 |
| `passage_marc_aur_8_18_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.18.1 | 171 |
| `passage_marc_aur_8_19_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.19.1 | 168 |
| `passage_marc_aur_8_2_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.2.1 | 196 |
| `passage_marc_aur_8_20_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.20.1 | 275 |
| `passage_marc_aur_8_21_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.21.1 | 290 |
| `passage_marc_aur_8_22_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.22.1 | 146 |
| `passage_marc_aur_8_23_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.23.1 | 159 |
| `passage_marc_aur_8_24_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.24.1 | 134 |
| `passage_marc_aur_8_25_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.25.1 | 597 |
| `passage_marc_aur_8_26_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.26.1 | 217 |
| `passage_marc_aur_8_27_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.27.1 | 138 |
| `passage_marc_aur_8_28_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.28.1 | 232 |
| `passage_marc_aur_8_29_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.29.1 | 233 |
| `passage_marc_aur_8_3_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.3.1 | 211 |
| `passage_marc_aur_8_30_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.30.1 | 90 |
| `passage_marc_aur_8_31_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.31.1 | 430 |
| `passage_marc_aur_8_32_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.32.1 | 434 |
| `passage_marc_aur_8_33_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.33.1 | 38 |
| `passage_marc_aur_8_34_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.34.1 | 670 |
| `passage_marc_aur_8_35_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.35.1 | 348 |
| `passage_marc_aur_8_36_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.36.1 | 428 |
| `passage_marc_aur_8_37_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.37.1 | 421 |
| `passage_marc_aur_8_38_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.38.1 | 55 |
| `passage_marc_aur_8_39_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.39.1 | 107 |
| `passage_marc_aur_8_4_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.4.1 | 52 |
| `passage_marc_aur_8_40_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.40.1 | 238 |
| `passage_marc_aur_8_41_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.41.1 | 599 |
| `passage_marc_aur_8_42_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.42.1 | 66 |
| `passage_marc_aur_8_43_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.43.1 | 214 |
| `passage_marc_aur_8_44_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.44.1 | 279 |
| `passage_marc_aur_8_45_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.45.1 | 294 |
| `passage_marc_aur_8_46_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.46.1 | 276 |
| `passage_marc_aur_8_47_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.47.1 | 515 |
| `passage_marc_aur_8_48_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.48.1 | 403 |
| `passage_marc_aur_8_49_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.49.1 | 384 |
| `passage_marc_aur_8_5_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.5.1 | 368 |
| `passage_marc_aur_8_50_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.50.1 | 704 |
| `passage_marc_aur_8_51_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.51.1 | 610 |
| `passage_marc_aur_8_52_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.52.1 | 310 |
| `passage_marc_aur_8_53_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.53.1 | 165 |
| `passage_marc_aur_8_54_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.54.1 | 210 |
| `passage_marc_aur_8_55_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.55.1 | 179 |
| `passage_marc_aur_8_56_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.56.1 | 330 |
| `passage_marc_aur_8_57_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.57.1 | 716 |
| `passage_marc_aur_8_58_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.58.1 | 196 |
| `passage_marc_aur_8_59_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.59.1 | 59 |
| `passage_marc_aur_8_6_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.6.1 | 199 |
| `passage_marc_aur_8_60_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.60.1 | 155 |
| `passage_marc_aur_8_61_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.61.1 | 98 |
| `passage_marc_aur_8_7_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.7.1 | 769 |
| `passage_marc_aur_8_8_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.8.1 | 219 |
| `passage_marc_aur_8_9_1` | Marcus Aurelius, Meditations (Ta eis heauton), 8.9.1 | 73 |
| `passage_marc_aur_9_1_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.1.1 | 434 |
| `passage_marc_aur_9_1_2` | Marcus Aurelius, Meditations (Ta eis heauton), 9.1.2 | 668 |
| `passage_marc_aur_9_1_3` | Marcus Aurelius, Meditations (Ta eis heauton), 9.1.3 | 514 |
| `passage_marc_aur_9_1_4` | Marcus Aurelius, Meditations (Ta eis heauton), 9.1.4 | 334 |
| `passage_marc_aur_9_10_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.10.1 | 270 |
| `passage_marc_aur_9_11_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.11.1 | 258 |
| `passage_marc_aur_9_12_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.12.1 | 129 |
| `passage_marc_aur_9_13_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.13.1 | 118 |
| `passage_marc_aur_9_14_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.14.1 | 114 |
| `passage_marc_aur_9_15_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.15.1 | 140 |
| `passage_marc_aur_9_16_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.16.1 | 139 |
| `passage_marc_aur_9_17_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.17.1 | 75 |
| `passage_marc_aur_9_18_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.18.1 | 100 |
| `passage_marc_aur_9_19_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.19.1 | 94 |
| `passage_marc_aur_9_2_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.2.1 | 469 |
| `passage_marc_aur_9_20_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.20.1 | 38 |
| `passage_marc_aur_9_21_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.21.1 | 459 |
| `passage_marc_aur_9_22_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.22.1 | 242 |
| `passage_marc_aur_9_23_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.23.1 | 351 |
| `passage_marc_aur_9_24_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.24.1 | 107 |
| `passage_marc_aur_9_25_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.25.1 | 160 |
| `passage_marc_aur_9_26_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.26.1 | 95 |
| `passage_marc_aur_9_27_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.27.1 | 339 |
| `passage_marc_aur_9_28_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.28.1 | 540 |
| `passage_marc_aur_9_29_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.29.1 | 754 |
| `passage_marc_aur_9_3_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.3.1 | 644 |
| `passage_marc_aur_9_3_2` | Marcus Aurelius, Meditations (Ta eis heauton), 9.3.2 | 600 |
| `passage_marc_aur_9_30_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.30.1 | 461 |
| `passage_marc_aur_9_31_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.31.1 | 210 |
| `passage_marc_aur_9_32_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.32.1 | 393 |
| `passage_marc_aur_9_33_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.33.1 | 156 |
| `passage_marc_aur_9_34_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.34.1 | 185 |
| `passage_marc_aur_9_35_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.35.1 | 375 |
| `passage_marc_aur_9_36_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.36.1 | 271 |
| `passage_marc_aur_9_37_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.37.1 | 287 |
| `passage_marc_aur_9_38_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.38.1 | 51 |
| `passage_marc_aur_9_39_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.39.1 | 266 |
| `passage_marc_aur_9_4_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.4.1 | 80 |
| `passage_marc_aur_9_40_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.40.1 | 899 |
| `passage_marc_aur_9_41_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.41.1 | 670 |
| `passage_marc_aur_9_42_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.42.1 | 447 |
| `passage_marc_aur_9_42_2` | Marcus Aurelius, Meditations (Ta eis heauton), 9.42.2 | 445 |
| `passage_marc_aur_9_42_3` | Marcus Aurelius, Meditations (Ta eis heauton), 9.42.3 | 369 |
| `passage_marc_aur_9_42_4` | Marcus Aurelius, Meditations (Ta eis heauton), 9.42.4 | 734 |
| `passage_marc_aur_9_5_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.5.1 | 51 |
| `passage_marc_aur_9_6_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.6.1 | 146 |
| `passage_marc_aur_9_7_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.7.1 | 80 |
| `passage_marc_aur_9_8_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.8.1 | 194 |
| `passage_marc_aur_9_9_1` | Marcus Aurelius, Meditations (Ta eis heauton), 9.9.1 | 584 |
| `passage_marc_aur_9_9_2` | Marcus Aurelius, Meditations (Ta eis heauton), 9.9.2 | 499 |
| `passage_marc_aur_9_9_3` | Marcus Aurelius, Meditations (Ta eis heauton), 9.9.3 | 335 |

### Sextus Empiricus — Against the Professors and Outlines of Pyrrhonism

- **Language:** Greek
- **Passages:** 534
- **Characters:** 1,120,366
- **Canonical ID:** `urn:cts:greekLit:tlg0544`

| node_id | label | chars |
|---------|-------|-------|
| `passage_sext_1` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 1 | 2,102 |
| `passage_sext_10` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 10 | 2,070 |
| `passage_sext_100` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 100 | 2,093 |
| `passage_sext_101` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 101 | 2,121 |
| `passage_sext_102` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 102 | 2,082 |
| `passage_sext_103` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 103 | 2,120 |
| `passage_sext_104` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 104 | 2,111 |
| `passage_sext_105` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 105 | 2,087 |
| `passage_sext_106` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 106 | 2,082 |
| `passage_sext_107` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 107 | 2,113 |
| `passage_sext_108` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 108 | 2,119 |
| `passage_sext_109` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 109 | 2,109 |
| `passage_sext_11` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 11 | 2,078 |
| `passage_sext_110` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 110 | 2,088 |
| `passage_sext_111` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 111 | 2,116 |
| `passage_sext_112` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 112 | 2,079 |
| `passage_sext_113` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 113 | 2,114 |
| `passage_sext_114` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 114 | 2,112 |
| `passage_sext_115` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 115 | 2,124 |
| `passage_sext_116` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 116 | 2,107 |
| `passage_sext_117` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 117 | 2,095 |
| `passage_sext_118` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 118 | 2,097 |
| `passage_sext_119` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 119 | 2,099 |
| `passage_sext_12` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 12 | 2,090 |
| `passage_sext_120` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 120 | 2,103 |
| `passage_sext_121` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 121 | 2,110 |
| `passage_sext_122` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 122 | 2,110 |
| `passage_sext_123` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 123 | 2,105 |
| `passage_sext_124` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 124 | 2,084 |
| `passage_sext_125` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 125 | 2,056 |
| `passage_sext_126` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 126 | 2,113 |
| `passage_sext_127` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 127 | 2,108 |
| `passage_sext_128` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 128 | 2,111 |
| `passage_sext_129` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 129 | 2,082 |
| `passage_sext_13` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 13 | 2,094 |
| `passage_sext_130` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 130 | 2,107 |
| `passage_sext_131` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 131 | 2,113 |
| `passage_sext_132` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 132 | 2,112 |
| `passage_sext_133` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 133 | 2,083 |
| `passage_sext_134` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 134 | 2,087 |
| `passage_sext_135` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 135 | 2,105 |
| `passage_sext_136` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 136 | 2,103 |
| `passage_sext_137` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 137 | 2,096 |
| `passage_sext_138` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 138 | 2,102 |
| `passage_sext_139` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 139 | 2,115 |
| `passage_sext_14` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 14 | 2,059 |
| `passage_sext_140` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 140 | 2,081 |
| `passage_sext_141` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 141 | 2,086 |
| `passage_sext_142` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 142 | 2,092 |
| `passage_sext_143` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 143 | 2,119 |
| `passage_sext_144` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 144 | 2,101 |
| `passage_sext_145` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 145 | 2,114 |
| `passage_sext_146` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 146 | 2,090 |
| `passage_sext_147` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 147 | 2,121 |
| `passage_sext_148` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 148 | 2,130 |
| `passage_sext_149` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 149 | 2,090 |
| `passage_sext_15` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 15 | 2,092 |
| `passage_sext_150` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 150 | 2,075 |
| `passage_sext_151` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 151 | 2,116 |
| `passage_sext_152` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 152 | 2,093 |
| `passage_sext_153` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 153 | 2,103 |
| `passage_sext_154` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 154 | 2,097 |
| `passage_sext_155` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 155 | 2,110 |
| `passage_sext_156` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 156 | 2,088 |
| `passage_sext_157` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 157 | 2,092 |
| `passage_sext_158` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 158 | 2,075 |
| `passage_sext_159` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 159 | 2,057 |
| `passage_sext_16` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 16 | 2,109 |
| `passage_sext_160` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 160 | 2,105 |
| `passage_sext_161` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 161 | 2,103 |
| `passage_sext_162` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 162 | 2,107 |
| `passage_sext_163` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 163 | 2,102 |
| `passage_sext_164` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 164 | 2,084 |
| `passage_sext_165` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 165 | 2,085 |
| `passage_sext_166` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 166 | 2,105 |
| `passage_sext_167` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 167 | 2,094 |
| `passage_sext_168` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 168 | 2,103 |
| `passage_sext_169` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 169 | 2,075 |
| `passage_sext_17` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 17 | 2,088 |
| `passage_sext_170` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 170 | 2,095 |
| `passage_sext_171` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 171 | 2,058 |
| `passage_sext_172` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 172 | 2,102 |
| `passage_sext_173` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 173 | 2,078 |
| `passage_sext_174` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 174 | 2,120 |
| `passage_sext_175` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 175 | 2,088 |
| `passage_sext_176` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 176 | 2,095 |
| `passage_sext_177` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 177 | 2,110 |
| `passage_sext_178` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 178 | 2,102 |
| `passage_sext_179` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 179 | 2,115 |
| `passage_sext_18` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 18 | 2,104 |
| `passage_sext_180` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 180 | 2,102 |
| `passage_sext_181` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 181 | 2,086 |
| `passage_sext_182` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 182 | 2,115 |
| `passage_sext_183` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 183 | 2,083 |
| `passage_sext_184` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 184 | 2,099 |
| `passage_sext_185` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 185 | 2,106 |
| `passage_sext_186` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 186 | 2,087 |
| `passage_sext_187` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 187 | 2,073 |
| `passage_sext_188` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 188 | 2,087 |
| `passage_sext_189` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 189 | 2,118 |
| `passage_sext_19` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 19 | 2,120 |
| `passage_sext_190` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 190 | 2,125 |
| `passage_sext_191` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 191 | 2,082 |
| `passage_sext_192` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 192 | 2,087 |
| `passage_sext_193` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 193 | 2,069 |
| `passage_sext_194` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 194 | 2,085 |
| `passage_sext_195` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 195 | 2,102 |
| `passage_sext_196` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 196 | 2,125 |
| `passage_sext_197` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 197 | 2,056 |
| `passage_sext_198` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 198 | 2,103 |
| `passage_sext_199` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 199 | 2,097 |
| `passage_sext_2` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 2 | 2,101 |
| `passage_sext_20` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 20 | 2,060 |
| `passage_sext_200` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 200 | 2,097 |
| `passage_sext_201` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 201 | 2,109 |
| `passage_sext_202` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 202 | 2,122 |
| `passage_sext_203` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 203 | 2,103 |
| `passage_sext_204` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 204 | 2,098 |
| `passage_sext_205` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 205 | 2,077 |
| `passage_sext_206` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 206 | 2,108 |
| `passage_sext_207` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 207 | 2,120 |
| `passage_sext_208` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 208 | 2,128 |
| `passage_sext_209` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 209 | 2,110 |
| `passage_sext_21` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 21 | 2,112 |
| `passage_sext_210` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 210 | 2,099 |
| `passage_sext_211` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 211 | 2,108 |
| `passage_sext_212` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 212 | 2,102 |
| `passage_sext_213` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 213 | 2,091 |
| `passage_sext_214` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 214 | 2,116 |
| `passage_sext_215` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 215 | 2,095 |
| `passage_sext_216` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 216 | 2,085 |
| `passage_sext_217` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 217 | 2,086 |
| `passage_sext_218` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 218 | 2,110 |
| `passage_sext_219` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 219 | 2,112 |
| `passage_sext_22` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 22 | 2,073 |
| `passage_sext_220` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 220 | 2,077 |
| `passage_sext_221` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 221 | 2,096 |
| `passage_sext_222` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 222 | 2,097 |
| `passage_sext_223` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 223 | 2,110 |
| `passage_sext_224` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 224 | 2,084 |
| `passage_sext_225` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 225 | 2,108 |
| `passage_sext_226` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 226 | 2,105 |
| `passage_sext_227` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 227 | 2,087 |
| `passage_sext_228` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 228 | 2,104 |
| `passage_sext_229` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 229 | 2,106 |
| `passage_sext_23` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 23 | 2,091 |
| `passage_sext_230` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 230 | 2,110 |
| `passage_sext_231` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 231 | 2,103 |
| `passage_sext_232` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 232 | 2,117 |
| `passage_sext_233` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 233 | 2,092 |
| `passage_sext_234` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 234 | 2,099 |
| `passage_sext_235` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 235 | 2,135 |
| `passage_sext_236` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 236 | 2,111 |
| `passage_sext_237` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 237 | 2,108 |
| `passage_sext_238` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 238 | 2,124 |
| `passage_sext_239` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 239 | 2,083 |
| `passage_sext_24` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 24 | 2,100 |
| `passage_sext_240` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 240 | 2,083 |
| `passage_sext_241` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 241 | 2,145 |
| `passage_sext_242` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 242 | 2,113 |
| `passage_sext_243` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 243 | 2,095 |
| `passage_sext_244` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 244 | 2,131 |
| `passage_sext_245` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 245 | 2,118 |
| `passage_sext_246` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 246 | 2,119 |
| `passage_sext_247` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 247 | 2,098 |
| `passage_sext_248` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 248 | 2,100 |
| `passage_sext_249` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 249 | 2,126 |
| `passage_sext_25` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 25 | 2,109 |
| `passage_sext_250` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 250 | 2,076 |
| `passage_sext_251` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 251 | 2,087 |
| `passage_sext_252` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 252 | 2,104 |
| `passage_sext_253` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 253 | 2,104 |
| `passage_sext_254` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 254 | 2,120 |
| `passage_sext_255` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 255 | 2,099 |
| `passage_sext_256` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 256 | 2,113 |
| `passage_sext_257` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 257 | 2,064 |
| `passage_sext_258` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 258 | 2,072 |
| `passage_sext_259` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 259 | 2,078 |
| `passage_sext_26` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 26 | 2,103 |
| `passage_sext_260` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 260 | 2,111 |
| `passage_sext_261` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 261 | 2,128 |
| `passage_sext_262` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 262 | 2,096 |
| `passage_sext_263` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 263 | 2,100 |
| `passage_sext_264` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 264 | 2,114 |
| `passage_sext_265` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 265 | 2,099 |
| `passage_sext_266` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 266 | 2,114 |
| `passage_sext_267` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 267 | 2,111 |
| `passage_sext_268` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 268 | 2,102 |
| `passage_sext_269` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 269 | 2,112 |
| `passage_sext_27` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 27 | 2,085 |
| `passage_sext_270` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 270 | 2,078 |
| `passage_sext_271` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 271 | 2,107 |
| `passage_sext_272` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 272 | 2,116 |
| `passage_sext_273` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 273 | 2,117 |
| `passage_sext_274` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 274 | 2,120 |
| `passage_sext_275` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 275 | 2,105 |
| `passage_sext_276` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 276 | 2,111 |
| `passage_sext_277` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 277 | 2,105 |
| `passage_sext_278` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 278 | 2,055 |
| `passage_sext_279` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 279 | 2,070 |
| `passage_sext_28` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 28 | 2,114 |
| `passage_sext_280` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 280 | 2,084 |
| `passage_sext_281` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 281 | 2,096 |
| `passage_sext_282` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 282 | 2,100 |
| `passage_sext_283` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 283 | 2,095 |
| `passage_sext_284` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 284 | 2,106 |
| `passage_sext_285` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 285 | 2,084 |
| `passage_sext_286` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 286 | 2,113 |
| `passage_sext_287` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 287 | 2,106 |
| `passage_sext_288` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 288 | 2,089 |
| `passage_sext_289` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 289 | 2,115 |
| `passage_sext_29` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 29 | 2,086 |
| `passage_sext_290` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 290 | 2,105 |
| `passage_sext_291` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 291 | 2,113 |
| `passage_sext_292` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 292 | 2,079 |
| `passage_sext_293` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 293 | 2,073 |
| `passage_sext_294` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 294 | 2,078 |
| `passage_sext_295` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 295 | 2,080 |
| `passage_sext_296` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 296 | 2,092 |
| `passage_sext_297` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 297 | 2,108 |
| `passage_sext_298` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 298 | 2,096 |
| `passage_sext_299` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 299 | 2,115 |
| `passage_sext_3` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 3 | 2,110 |
| `passage_sext_30` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 30 | 2,096 |
| `passage_sext_300` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 300 | 2,122 |
| `passage_sext_301` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 301 | 2,108 |
| `passage_sext_302` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 302 | 2,133 |
| `passage_sext_303` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 303 | 2,108 |
| `passage_sext_304` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 304 | 2,117 |
| `passage_sext_305` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 305 | 2,119 |
| `passage_sext_306` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 306 | 2,120 |
| `passage_sext_307` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 307 | 2,098 |
| `passage_sext_308` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 308 | 2,097 |
| `passage_sext_309` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 309 | 2,088 |
| `passage_sext_31` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 31 | 2,104 |
| `passage_sext_310` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 310 | 2,102 |
| `passage_sext_311` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 311 | 2,097 |
| `passage_sext_312` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 312 | 2,112 |
| `passage_sext_313` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 313 | 2,125 |
| `passage_sext_314` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 314 | 2,119 |
| `passage_sext_315` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 315 | 2,101 |
| `passage_sext_316` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 316 | 2,091 |
| `passage_sext_317` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 317 | 2,130 |
| `passage_sext_318` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 318 | 2,120 |
| `passage_sext_319` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 319 | 2,098 |
| `passage_sext_32` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 32 | 2,092 |
| `passage_sext_320` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 320 | 2,112 |
| `passage_sext_321` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 321 | 2,110 |
| `passage_sext_322` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 322 | 2,118 |
| `passage_sext_323` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 323 | 2,113 |
| `passage_sext_324` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 324 | 2,131 |
| `passage_sext_325` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 325 | 2,101 |
| `passage_sext_326` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 326 | 2,076 |
| `passage_sext_327` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 327 | 2,116 |
| `passage_sext_328` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 328 | 2,099 |
| `passage_sext_329` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 329 | 2,125 |
| `passage_sext_33` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 33 | 2,114 |
| `passage_sext_330` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 330 | 2,081 |
| `passage_sext_331` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 331 | 2,122 |
| `passage_sext_332` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 332 | 2,101 |
| `passage_sext_333` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 333 | 2,101 |
| `passage_sext_334` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 334 | 2,089 |
| `passage_sext_335` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 335 | 2,134 |
| `passage_sext_336` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 336 | 2,091 |
| `passage_sext_337` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 337 | 2,095 |
| `passage_sext_338` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 338 | 2,104 |
| `passage_sext_339` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 339 | 2,122 |
| `passage_sext_34` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 34 | 2,080 |
| `passage_sext_340` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 340 | 2,101 |
| `passage_sext_341` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 341 | 2,109 |
| `passage_sext_342` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 342 | 2,113 |
| `passage_sext_343` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 343 | 2,064 |
| `passage_sext_344` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 344 | 2,097 |
| `passage_sext_345` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 345 | 2,084 |
| `passage_sext_346` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 346 | 2,092 |
| `passage_sext_347` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 347 | 2,084 |
| `passage_sext_348` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 348 | 2,126 |
| `passage_sext_349` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 349 | 2,115 |
| `passage_sext_35` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 35 | 2,089 |
| `passage_sext_350` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 350 | 2,118 |
| `passage_sext_351` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 351 | 2,123 |
| `passage_sext_352` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 352 | 2,108 |
| `passage_sext_353` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 353 | 2,127 |
| `passage_sext_354` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 354 | 2,083 |
| `passage_sext_355` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 355 | 2,099 |
| `passage_sext_356` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 356 | 2,107 |
| `passage_sext_357` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 357 | 2,111 |
| `passage_sext_358` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 358 | 2,105 |
| `passage_sext_359` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 359 | 2,101 |
| `passage_sext_36` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 36 | 2,085 |
| `passage_sext_360` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 360 | 2,093 |
| `passage_sext_361` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 361 | 2,062 |
| `passage_sext_362` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 362 | 2,116 |
| `passage_sext_363` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 363 | 2,119 |
| `passage_sext_364` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 364 | 2,107 |
| `passage_sext_365` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 365 | 2,120 |
| `passage_sext_366` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 366 | 2,120 |
| `passage_sext_367` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 367 | 2,070 |
| `passage_sext_368` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 368 | 2,097 |
| `passage_sext_369` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 369 | 2,078 |
| `passage_sext_37` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 37 | 2,083 |
| `passage_sext_370` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 370 | 2,085 |
| `passage_sext_371` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 371 | 2,088 |
| `passage_sext_372` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 372 | 2,081 |
| `passage_sext_373` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 373 | 2,099 |
| `passage_sext_374` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 374 | 2,120 |
| `passage_sext_375` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 375 | 2,122 |
| `passage_sext_376` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 376 | 2,121 |
| `passage_sext_377` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 377 | 2,096 |
| `passage_sext_378` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 378 | 2,098 |
| `passage_sext_379` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 379 | 2,103 |
| `passage_sext_38` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 38 | 2,086 |
| `passage_sext_380` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 380 | 2,115 |
| `passage_sext_381` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 381 | 2,091 |
| `passage_sext_382` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 382 | 2,130 |
| `passage_sext_383` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 383 | 2,112 |
| `passage_sext_384` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 384 | 2,133 |
| `passage_sext_385` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 385 | 2,084 |
| `passage_sext_386` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 386 | 2,108 |
| `passage_sext_387` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 387 | 2,097 |
| `passage_sext_388` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 388 | 2,079 |
| `passage_sext_389` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 389 | 2,109 |
| `passage_sext_39` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 39 | 2,115 |
| `passage_sext_390` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 390 | 2,118 |
| `passage_sext_391` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 391 | 2,067 |
| `passage_sext_392` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 392 | 2,090 |
| `passage_sext_393` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 393 | 2,121 |
| `passage_sext_394` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 394 | 2,098 |
| `passage_sext_395` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 395 | 2,110 |
| `passage_sext_396` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 396 | 2,120 |
| `passage_sext_397` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 397 | 2,115 |
| `passage_sext_398` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 398 | 2,101 |
| `passage_sext_399` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 399 | 2,105 |
| `passage_sext_4` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 4 | 2,109 |
| `passage_sext_40` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 40 | 2,098 |
| `passage_sext_400` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 400 | 2,103 |
| `passage_sext_401` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 401 | 2,102 |
| `passage_sext_402` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 402 | 2,086 |
| `passage_sext_403` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 403 | 2,120 |
| `passage_sext_404` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 404 | 2,129 |
| `passage_sext_405` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 405 | 2,087 |
| `passage_sext_406` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 406 | 2,112 |
| `passage_sext_407` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 407 | 2,103 |
| `passage_sext_408` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 408 | 2,117 |
| `passage_sext_409` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 409 | 2,116 |
| `passage_sext_41` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 41 | 2,078 |
| `passage_sext_410` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 410 | 2,108 |
| `passage_sext_411` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 411 | 2,109 |
| `passage_sext_412` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 412 | 2,107 |
| `passage_sext_413` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 413 | 2,086 |
| `passage_sext_414` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 414 | 2,063 |
| `passage_sext_415` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 415 | 2,107 |
| `passage_sext_416` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 416 | 2,113 |
| `passage_sext_417` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 417 | 2,094 |
| `passage_sext_418` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 418 | 2,093 |
| `passage_sext_419` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 419 | 2,101 |
| `passage_sext_42` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 42 | 2,100 |
| `passage_sext_420` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 420 | 2,069 |
| `passage_sext_421` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 421 | 2,080 |
| `passage_sext_422` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 422 | 2,078 |
| `passage_sext_423` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 423 | 2,121 |
| `passage_sext_424` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 424 | 2,111 |
| `passage_sext_425` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 425 | 2,091 |
| `passage_sext_426` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 426 | 2,099 |
| `passage_sext_427` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 427 | 2,105 |
| `passage_sext_428` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 428 | 2,102 |
| `passage_sext_429` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 429 | 2,092 |
| `passage_sext_43` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 43 | 2,109 |
| `passage_sext_430` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 430 | 2,085 |
| `passage_sext_431` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 431 | 2,077 |
| `passage_sext_432` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 432 | 2,119 |
| `passage_sext_433` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 433 | 2,094 |
| `passage_sext_434` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 434 | 2,087 |
| `passage_sext_435` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 435 | 2,054 |
| `passage_sext_436` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 436 | 2,108 |
| `passage_sext_437` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 437 | 2,102 |
| `passage_sext_438` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 438 | 2,101 |
| `passage_sext_439` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 439 | 2,115 |
| `passage_sext_44` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 44 | 2,102 |
| `passage_sext_440` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 440 | 2,113 |
| `passage_sext_441` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 441 | 2,124 |
| `passage_sext_442` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 442 | 2,108 |
| `passage_sext_443` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 443 | 2,087 |
| `passage_sext_444` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 444 | 2,113 |
| `passage_sext_445` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 445 | 2,074 |
| `passage_sext_446` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 446 | 2,099 |
| `passage_sext_447` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 447 | 2,099 |
| `passage_sext_448` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 448 | 2,102 |
| `passage_sext_449` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 449 | 2,091 |
| `passage_sext_45` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 45 | 2,115 |
| `passage_sext_450` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 450 | 2,090 |
| `passage_sext_451` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 451 | 2,099 |
| `passage_sext_452` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 452 | 2,068 |
| `passage_sext_453` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 453 | 2,076 |
| `passage_sext_454` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 454 | 2,059 |
| `passage_sext_455` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 455 | 2,097 |
| `passage_sext_456` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 456 | 2,083 |
| `passage_sext_457` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 457 | 2,107 |
| `passage_sext_458` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 458 | 2,108 |
| `passage_sext_459` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 459 | 2,111 |
| `passage_sext_46` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 46 | 2,098 |
| `passage_sext_460` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 460 | 2,097 |
| `passage_sext_461` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 461 | 2,092 |
| `passage_sext_462` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 462 | 2,102 |
| `passage_sext_463` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 463 | 2,097 |
| `passage_sext_464` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 464 | 2,095 |
| `passage_sext_465` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 465 | 2,082 |
| `passage_sext_466` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 466 | 2,102 |
| `passage_sext_467` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 467 | 2,083 |
| `passage_sext_468` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 468 | 2,099 |
| `passage_sext_469` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 469 | 2,110 |
| `passage_sext_47` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 47 | 2,105 |
| `passage_sext_470` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 470 | 2,096 |
| `passage_sext_471` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 471 | 2,073 |
| `passage_sext_472` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 472 | 2,096 |
| `passage_sext_473` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 473 | 2,062 |
| `passage_sext_474` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 474 | 2,104 |
| `passage_sext_475` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 475 | 2,087 |
| `passage_sext_476` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 476 | 2,106 |
| `passage_sext_477` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 477 | 2,112 |
| `passage_sext_478` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 478 | 2,110 |
| `passage_sext_479` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 479 | 2,099 |
| `passage_sext_48` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 48 | 2,079 |
| `passage_sext_480` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 480 | 2,111 |
| `passage_sext_481` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 481 | 2,108 |
| `passage_sext_482` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 482 | 2,104 |
| `passage_sext_483` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 483 | 2,090 |
| `passage_sext_484` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 484 | 2,093 |
| `passage_sext_485` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 485 | 2,093 |
| `passage_sext_486` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 486 | 2,104 |
| `passage_sext_487` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 487 | 2,112 |
| `passage_sext_488` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 488 | 2,112 |
| `passage_sext_489` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 489 | 2,089 |
| `passage_sext_49` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 49 | 2,102 |
| `passage_sext_490` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 490 | 2,104 |
| `passage_sext_491` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 491 | 2,107 |
| `passage_sext_492` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 492 | 2,091 |
| `passage_sext_493` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 493 | 2,106 |
| `passage_sext_494` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 494 | 2,065 |
| `passage_sext_495` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 495 | 2,122 |
| `passage_sext_496` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 496 | 2,108 |
| `passage_sext_497` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 497 | 2,104 |
| `passage_sext_498` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 498 | 2,100 |
| `passage_sext_499` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 499 | 2,118 |
| `passage_sext_5` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 5 | 2,073 |
| `passage_sext_50` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 50 | 2,103 |
| `passage_sext_500` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 500 | 2,094 |
| `passage_sext_501` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 501 | 2,100 |
| `passage_sext_502` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 502 | 2,116 |
| `passage_sext_503` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 503 | 2,104 |
| `passage_sext_504` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 504 | 2,096 |
| `passage_sext_505` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 505 | 2,116 |
| `passage_sext_506` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 506 | 2,079 |
| `passage_sext_507` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 507 | 2,074 |
| `passage_sext_508` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 508 | 2,120 |
| `passage_sext_509` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 509 | 2,126 |
| `passage_sext_51` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 51 | 2,095 |
| `passage_sext_510` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 510 | 2,117 |
| `passage_sext_511` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 511 | 2,097 |
| `passage_sext_512` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 512 | 2,083 |
| `passage_sext_513` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 513 | 2,088 |
| `passage_sext_514` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 514 | 2,084 |
| `passage_sext_515` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 515 | 2,105 |
| `passage_sext_516` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 516 | 2,090 |
| `passage_sext_517` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 517 | 2,077 |
| `passage_sext_518` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 518 | 2,053 |
| `passage_sext_519` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 519 | 2,060 |
| `passage_sext_52` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 52 | 2,104 |
| `passage_sext_520` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 520 | 2,077 |
| `passage_sext_521` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 521 | 2,104 |
| `passage_sext_522` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 522 | 2,083 |
| `passage_sext_523` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 523 | 2,090 |
| `passage_sext_524` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 524 | 2,098 |
| `passage_sext_525` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 525 | 2,079 |
| `passage_sext_526` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 526 | 2,108 |
| `passage_sext_527` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 527 | 2,103 |
| `passage_sext_528` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 528 | 2,100 |
| `passage_sext_529` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 529 | 2,104 |
| `passage_sext_53` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 53 | 2,113 |
| `passage_sext_530` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 530 | 2,069 |
| `passage_sext_531` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 531 | 2,107 |
| `passage_sext_532` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 532 | 2,088 |
| `passage_sext_533` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 533 | 2,119 |
| `passage_sext_534` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 534 | 1,131 |
| `passage_sext_54` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 54 | 2,086 |
| `passage_sext_55` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 55 | 2,102 |
| `passage_sext_56` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 56 | 2,119 |
| `passage_sext_57` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 57 | 2,118 |
| `passage_sext_58` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 58 | 2,120 |
| `passage_sext_59` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 59 | 2,095 |
| `passage_sext_6` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 6 | 2,082 |
| `passage_sext_60` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 60 | 2,103 |
| `passage_sext_61` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 61 | 2,092 |
| `passage_sext_62` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 62 | 2,120 |
| `passage_sext_63` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 63 | 2,115 |
| `passage_sext_64` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 64 | 2,111 |
| `passage_sext_65` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 65 | 2,105 |
| `passage_sext_66` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 66 | 2,096 |
| `passage_sext_67` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 67 | 2,115 |
| `passage_sext_68` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 68 | 2,118 |
| `passage_sext_69` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 69 | 2,118 |
| `passage_sext_7` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 7 | 2,098 |
| `passage_sext_70` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 70 | 2,072 |
| `passage_sext_71` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 71 | 2,094 |
| `passage_sext_72` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 72 | 2,115 |
| `passage_sext_73` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 73 | 2,131 |
| `passage_sext_74` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 74 | 2,110 |
| `passage_sext_75` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 75 | 2,091 |
| `passage_sext_76` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 76 | 2,090 |
| `passage_sext_77` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 77 | 2,085 |
| `passage_sext_78` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 78 | 2,101 |
| `passage_sext_79` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 79 | 2,095 |
| `passage_sext_8` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 8 | 2,073 |
| `passage_sext_80` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 80 | 2,118 |
| `passage_sext_81` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 81 | 2,125 |
| `passage_sext_82` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 82 | 2,089 |
| `passage_sext_83` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 83 | 2,103 |
| `passage_sext_84` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 84 | 2,100 |
| `passage_sext_85` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 85 | 2,096 |
| `passage_sext_86` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 86 | 2,054 |
| `passage_sext_87` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 87 | 2,106 |
| `passage_sext_88` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 88 | 2,108 |
| `passage_sext_89` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 89 | 2,083 |
| `passage_sext_9` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 9 | 2,082 |
| `passage_sext_90` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 90 | 2,109 |
| `passage_sext_91` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 91 | 2,070 |
| `passage_sext_92` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 92 | 2,119 |
| `passage_sext_93` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 93 | 2,093 |
| `passage_sext_94` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 94 | 2,074 |
| `passage_sext_95` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 95 | 2,126 |
| `passage_sext_96` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 96 | 2,087 |
| `passage_sext_97` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 97 | 2,115 |
| `passage_sext_98` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 98 | 2,107 |
| `passage_sext_99` | Sextus Empiricus, Against the Professors and Outlines of Pyrrhonism, M. 99 | 2,115 |

### Aristotle — Magna Moralia

- **Language:** Greek
- **Passages:** 434
- **Characters:** 134,924
- **Canonical ID:** `first1k:tlg0086.tlg022.1st1K-grc1`

| node_id | label | chars |
|---------|-------|-------|
| `passage_arist_mm_1_1_1` | Aristotle, Magna Moralia, 1.1.1 | 316 |
| `passage_arist_mm_1_1_10` | Aristotle, Magna Moralia, 1.1.10 | 339 |
| `passage_arist_mm_1_1_11` | Aristotle, Magna Moralia, 1.1.11 | 296 |
| `passage_arist_mm_1_1_12` | Aristotle, Magna Moralia, 1.1.12 | 329 |
| `passage_arist_mm_1_1_13` | Aristotle, Magna Moralia, 1.1.13 | 349 |
| `passage_arist_mm_1_1_14` | Aristotle, Magna Moralia, 1.1.14 | 285 |
| `passage_arist_mm_1_1_15` | Aristotle, Magna Moralia, 1.1.15 | 265 |
| `passage_arist_mm_1_1_16` | Aristotle, Magna Moralia, 1.1.16 | 407 |
| `passage_arist_mm_1_1_17` | Aristotle, Magna Moralia, 1.1.17 | 259 |
| `passage_arist_mm_1_1_18` | Aristotle, Magna Moralia, 1.1.18 | 256 |
| `passage_arist_mm_1_1_19` | Aristotle, Magna Moralia, 1.1.19 | 416 |
| `passage_arist_mm_1_1_2` | Aristotle, Magna Moralia, 1.1.2 | 83 |
| `passage_arist_mm_1_1_20` | Aristotle, Magna Moralia, 1.1.20 | 293 |
| `passage_arist_mm_1_1_21` | Aristotle, Magna Moralia, 1.1.21 | 258 |
| `passage_arist_mm_1_1_22` | Aristotle, Magna Moralia, 1.1.22 | 212 |
| `passage_arist_mm_1_1_23` | Aristotle, Magna Moralia, 1.1.23 | 322 |
| `passage_arist_mm_1_1_24` | Aristotle, Magna Moralia, 1.1.24 | 254 |
| `passage_arist_mm_1_1_25` | Aristotle, Magna Moralia, 1.1.25 | 155 |
| `passage_arist_mm_1_1_26` | Aristotle, Magna Moralia, 1.1.26 | 690 |
| `passage_arist_mm_1_1_3` | Aristotle, Magna Moralia, 1.1.3 | 171 |
| `passage_arist_mm_1_1_4` | Aristotle, Magna Moralia, 1.1.4 | 370 |
| `passage_arist_mm_1_1_5` | Aristotle, Magna Moralia, 1.1.5 | 218 |
| `passage_arist_mm_1_1_6` | Aristotle, Magna Moralia, 1.1.6 | 199 |
| `passage_arist_mm_1_1_7` | Aristotle, Magna Moralia, 1.1.7 | 453 |
| `passage_arist_mm_1_1_8` | Aristotle, Magna Moralia, 1.1.8 | 441 |
| `passage_arist_mm_1_1_9` | Aristotle, Magna Moralia, 1.1.9 | 277 |
| `passage_arist_mm_1_10_1` | Aristotle, Magna Moralia, 1.10.1 | 393 |
| `passage_arist_mm_1_10_2` | Aristotle, Magna Moralia, 1.10.2 | 348 |
| `passage_arist_mm_1_11_1` | Aristotle, Magna Moralia, 1.11.1 | 313 |
| `passage_arist_mm_1_11_2` | Aristotle, Magna Moralia, 1.11.2 | 267 |
| `passage_arist_mm_1_11_3` | Aristotle, Magna Moralia, 1.11.3 | 304 |
| `passage_arist_mm_1_11_4` | Aristotle, Magna Moralia, 1.11.4 | 424 |
| `passage_arist_mm_1_11_5` | Aristotle, Magna Moralia, 1.11.5 | 139 |
| `passage_arist_mm_1_12_1` | Aristotle, Magna Moralia, 1.12.1 | 294 |
| `passage_arist_mm_1_12_2` | Aristotle, Magna Moralia, 1.12.2 | 476 |
| `passage_arist_mm_1_12_3` | Aristotle, Magna Moralia, 1.12.3 | 264 |
| `passage_arist_mm_1_12_4` | Aristotle, Magna Moralia, 1.12.4 | 344 |
| `passage_arist_mm_1_13_1` | Aristotle, Magna Moralia, 1.13.1 | 386 |
| `passage_arist_mm_1_13_2` | Aristotle, Magna Moralia, 1.13.2 | 167 |
| `passage_arist_mm_1_13_3` | Aristotle, Magna Moralia, 1.13.3 | 367 |
| `passage_arist_mm_1_13_4` | Aristotle, Magna Moralia, 1.13.4 | 230 |
| `passage_arist_mm_1_14_1` | Aristotle, Magna Moralia, 1.14.1 | 258 |
| `passage_arist_mm_1_14_2` | Aristotle, Magna Moralia, 1.14.2 | 269 |
| `passage_arist_mm_1_14_3` | Aristotle, Magna Moralia, 1.14.3 | 110 |
| `passage_arist_mm_1_15_1` | Aristotle, Magna Moralia, 1.15.1 | 370 |
| `passage_arist_mm_1_15_2` | Aristotle, Magna Moralia, 1.15.2 | 273 |
| `passage_arist_mm_1_16_1` | Aristotle, Magna Moralia, 1.16.1 | 374 |
| `passage_arist_mm_1_16_2` | Aristotle, Magna Moralia, 1.16.2 | 398 |
| `passage_arist_mm_1_17_1` | Aristotle, Magna Moralia, 1.17.1 | 242 |
| `passage_arist_mm_1_17_10` | Aristotle, Magna Moralia, 1.17.10 | 408 |
| `passage_arist_mm_1_17_11` | Aristotle, Magna Moralia, 1.17.11 | 384 |
| `passage_arist_mm_1_17_2` | Aristotle, Magna Moralia, 1.17.2 | 318 |
| `passage_arist_mm_1_17_3` | Aristotle, Magna Moralia, 1.17.3 | 352 |
| `passage_arist_mm_1_17_4` | Aristotle, Magna Moralia, 1.17.4 | 279 |
| `passage_arist_mm_1_17_5` | Aristotle, Magna Moralia, 1.17.5 | 586 |
| `passage_arist_mm_1_17_6` | Aristotle, Magna Moralia, 1.17.6 | 293 |
| `passage_arist_mm_1_17_7` | Aristotle, Magna Moralia, 1.17.7 | 301 |
| `passage_arist_mm_1_17_8` | Aristotle, Magna Moralia, 1.17.8 | 189 |
| `passage_arist_mm_1_17_9` | Aristotle, Magna Moralia, 1.17.9 | 470 |
| `passage_arist_mm_1_18_1` | Aristotle, Magna Moralia, 1.18.1 | 271 |
| `passage_arist_mm_1_18_2` | Aristotle, Magna Moralia, 1.18.2 | 350 |
| `passage_arist_mm_1_18_3` | Aristotle, Magna Moralia, 1.18.3 | 115 |
| `passage_arist_mm_1_18_4` | Aristotle, Magna Moralia, 1.18.4 | 277 |
| `passage_arist_mm_1_18_5` | Aristotle, Magna Moralia, 1.18.5 | 478 |
| `passage_arist_mm_1_18_6` | Aristotle, Magna Moralia, 1.18.6 | 210 |
| `passage_arist_mm_1_19_1` | Aristotle, Magna Moralia, 1.19.1 | 930 |
| `passage_arist_mm_1_2_1` | Aristotle, Magna Moralia, 1.2.1 | 411 |
| `passage_arist_mm_1_2_10` | Aristotle, Magna Moralia, 1.2.10 | 351 |
| `passage_arist_mm_1_2_11` | Aristotle, Magna Moralia, 1.2.11 | 181 |
| `passage_arist_mm_1_2_2` | Aristotle, Magna Moralia, 1.2.2 | 198 |
| `passage_arist_mm_1_2_3` | Aristotle, Magna Moralia, 1.2.3 | 304 |
| `passage_arist_mm_1_2_4` | Aristotle, Magna Moralia, 1.2.4 | 113 |
| `passage_arist_mm_1_2_5` | Aristotle, Magna Moralia, 1.2.5 | 263 |
| `passage_arist_mm_1_2_6` | Aristotle, Magna Moralia, 1.2.6 | 310 |
| `passage_arist_mm_1_2_7` | Aristotle, Magna Moralia, 1.2.7 | 353 |
| `passage_arist_mm_1_2_8` | Aristotle, Magna Moralia, 1.2.8 | 466 |
| `passage_arist_mm_1_2_9` | Aristotle, Magna Moralia, 1.2.9 | 299 |
| `passage_arist_mm_1_20_1` | Aristotle, Magna Moralia, 1.20.1 | 385 |
| `passage_arist_mm_1_20_10` | Aristotle, Magna Moralia, 1.20.10 | 377 |
| `passage_arist_mm_1_20_11` | Aristotle, Magna Moralia, 1.20.11 | 272 |
| `passage_arist_mm_1_20_12` | Aristotle, Magna Moralia, 1.20.12 | 360 |
| `passage_arist_mm_1_20_2` | Aristotle, Magna Moralia, 1.20.2 | 303 |
| `passage_arist_mm_1_20_3` | Aristotle, Magna Moralia, 1.20.3 | 376 |
| `passage_arist_mm_1_20_4` | Aristotle, Magna Moralia, 1.20.4 | 289 |
| `passage_arist_mm_1_20_5` | Aristotle, Magna Moralia, 1.20.5 | 160 |
| `passage_arist_mm_1_20_6` | Aristotle, Magna Moralia, 1.20.6 | 229 |
| `passage_arist_mm_1_20_7` | Aristotle, Magna Moralia, 1.20.7 | 159 |
| `passage_arist_mm_1_20_8` | Aristotle, Magna Moralia, 1.20.8 | 499 |
| `passage_arist_mm_1_20_9` | Aristotle, Magna Moralia, 1.20.9 | 302 |
| `passage_arist_mm_1_21_1` | Aristotle, Magna Moralia, 1.21.1 | 428 |
| `passage_arist_mm_1_21_2` | Aristotle, Magna Moralia, 1.21.2 | 288 |
| `passage_arist_mm_1_21_3` | Aristotle, Magna Moralia, 1.21.3 | 316 |
| `passage_arist_mm_1_21_4` | Aristotle, Magna Moralia, 1.21.4 | 366 |
| `passage_arist_mm_1_22_1` | Aristotle, Magna Moralia, 1.22.1 | 370 |
| `passage_arist_mm_1_22_2` | Aristotle, Magna Moralia, 1.22.2 | 266 |
| `passage_arist_mm_1_22_3` | Aristotle, Magna Moralia, 1.22.3 | 305 |
| `passage_arist_mm_1_23_1` | Aristotle, Magna Moralia, 1.23.1 | 256 |
| `passage_arist_mm_1_23_2` | Aristotle, Magna Moralia, 1.23.2 | 211 |
| `passage_arist_mm_1_24_1` | Aristotle, Magna Moralia, 1.24.1 | 681 |
| `passage_arist_mm_1_25_1` | Aristotle, Magna Moralia, 1.25.1 | 426 |
| `passage_arist_mm_1_25_2` | Aristotle, Magna Moralia, 1.25.2 | 185 |
| `passage_arist_mm_1_25_3` | Aristotle, Magna Moralia, 1.25.3 | 213 |
| `passage_arist_mm_1_26_1` | Aristotle, Magna Moralia, 1.26.1 | 333 |
| `passage_arist_mm_1_26_2` | Aristotle, Magna Moralia, 1.26.2 | 168 |
| `passage_arist_mm_1_26_3` | Aristotle, Magna Moralia, 1.26.3 | 516 |
| `passage_arist_mm_1_27_1` | Aristotle, Magna Moralia, 1.27.1 | 611 |
| `passage_arist_mm_1_28_1` | Aristotle, Magna Moralia, 1.28.1 | 264 |
| `passage_arist_mm_1_28_2` | Aristotle, Magna Moralia, 1.28.2 | 235 |
| `passage_arist_mm_1_29_1` | Aristotle, Magna Moralia, 1.29.1 | 320 |
| `passage_arist_mm_1_29_2` | Aristotle, Magna Moralia, 1.29.2 | 221 |
| `passage_arist_mm_1_3_1` | Aristotle, Magna Moralia, 1.3.1 | 224 |
| `passage_arist_mm_1_3_2` | Aristotle, Magna Moralia, 1.3.2 | 240 |
| `passage_arist_mm_1_3_3` | Aristotle, Magna Moralia, 1.3.3 | 257 |
| `passage_arist_mm_1_3_4` | Aristotle, Magna Moralia, 1.3.4 | 193 |
| `passage_arist_mm_1_3_5` | Aristotle, Magna Moralia, 1.3.5 | 243 |
| `passage_arist_mm_1_30_1` | Aristotle, Magna Moralia, 1.30.1 | 226 |
| `passage_arist_mm_1_30_2` | Aristotle, Magna Moralia, 1.30.2 | 242 |
| `passage_arist_mm_1_31_1` | Aristotle, Magna Moralia, 1.31.1 | 266 |
| `passage_arist_mm_1_31_2` | Aristotle, Magna Moralia, 1.31.2 | 149 |
| `passage_arist_mm_1_32_1` | Aristotle, Magna Moralia, 1.32.1 | 338 |
| `passage_arist_mm_1_32_2` | Aristotle, Magna Moralia, 1.32.2 | 297 |
| `passage_arist_mm_1_33_1` | Aristotle, Magna Moralia, 1.33.1 | 179 |
| `passage_arist_mm_1_33_10` | Aristotle, Magna Moralia, 1.33.10 | 360 |
| `passage_arist_mm_1_33_11` | Aristotle, Magna Moralia, 1.33.11 | 338 |
| `passage_arist_mm_1_33_12` | Aristotle, Magna Moralia, 1.33.12 | 395 |
| `passage_arist_mm_1_33_13` | Aristotle, Magna Moralia, 1.33.13 | 312 |
| `passage_arist_mm_1_33_14` | Aristotle, Magna Moralia, 1.33.14 | 633 |
| `passage_arist_mm_1_33_15` | Aristotle, Magna Moralia, 1.33.15 | 307 |
| `passage_arist_mm_1_33_16` | Aristotle, Magna Moralia, 1.33.16 | 544 |
| `passage_arist_mm_1_33_17` | Aristotle, Magna Moralia, 1.33.17 | 299 |
| `passage_arist_mm_1_33_18` | Aristotle, Magna Moralia, 1.33.18 | 315 |
| `passage_arist_mm_1_33_19` | Aristotle, Magna Moralia, 1.33.19 | 259 |
| `passage_arist_mm_1_33_2` | Aristotle, Magna Moralia, 1.33.2 | 420 |
| `passage_arist_mm_1_33_20` | Aristotle, Magna Moralia, 1.33.20 | 389 |
| `passage_arist_mm_1_33_21` | Aristotle, Magna Moralia, 1.33.21 | 414 |
| `passage_arist_mm_1_33_22` | Aristotle, Magna Moralia, 1.33.22 | 346 |
| `passage_arist_mm_1_33_23` | Aristotle, Magna Moralia, 1.33.23 | 481 |
| `passage_arist_mm_1_33_24` | Aristotle, Magna Moralia, 1.33.24 | 273 |
| `passage_arist_mm_1_33_25` | Aristotle, Magna Moralia, 1.33.25 | 416 |
| `passage_arist_mm_1_33_26` | Aristotle, Magna Moralia, 1.33.26 | 474 |
| `passage_arist_mm_1_33_27` | Aristotle, Magna Moralia, 1.33.27 | 287 |
| `passage_arist_mm_1_33_28` | Aristotle, Magna Moralia, 1.33.28 | 442 |
| `passage_arist_mm_1_33_29` | Aristotle, Magna Moralia, 1.33.29 | 416 |
| `passage_arist_mm_1_33_3` | Aristotle, Magna Moralia, 1.33.3 | 495 |
| `passage_arist_mm_1_33_30` | Aristotle, Magna Moralia, 1.33.30 | 552 |
| `passage_arist_mm_1_33_31` | Aristotle, Magna Moralia, 1.33.31 | 501 |
| `passage_arist_mm_1_33_32` | Aristotle, Magna Moralia, 1.33.32 | 416 |
| `passage_arist_mm_1_33_33` | Aristotle, Magna Moralia, 1.33.33 | 228 |
| `passage_arist_mm_1_33_34` | Aristotle, Magna Moralia, 1.33.34 | 422 |
| `passage_arist_mm_1_33_35` | Aristotle, Magna Moralia, 1.33.35 | 369 |
| `passage_arist_mm_1_33_36` | Aristotle, Magna Moralia, 1.33.36 | 557 |
| `passage_arist_mm_1_33_4` | Aristotle, Magna Moralia, 1.33.4 | 229 |
| `passage_arist_mm_1_33_5` | Aristotle, Magna Moralia, 1.33.5 | 185 |
| `passage_arist_mm_1_33_6` | Aristotle, Magna Moralia, 1.33.6 | 233 |
| `passage_arist_mm_1_33_7` | Aristotle, Magna Moralia, 1.33.7 | 119 |
| `passage_arist_mm_1_33_8` | Aristotle, Magna Moralia, 1.33.8 | 225 |
| `passage_arist_mm_1_33_9` | Aristotle, Magna Moralia, 1.33.9 | 429 |
| `passage_arist_mm_1_34_1` | Aristotle, Magna Moralia, 1.34.1 | 379 |
| `passage_arist_mm_1_34_10` | Aristotle, Magna Moralia, 1.34.10 | 328 |
| `passage_arist_mm_1_34_11` | Aristotle, Magna Moralia, 1.34.11 | 136 |
| `passage_arist_mm_1_34_12` | Aristotle, Magna Moralia, 1.34.12 | 405 |
| `passage_arist_mm_1_34_14` | Aristotle, Magna Moralia, 1.34.14 | 384 |
| `passage_arist_mm_1_34_15` | Aristotle, Magna Moralia, 1.34.15 | 93 |
| `passage_arist_mm_1_34_16` | Aristotle, Magna Moralia, 1.34.16 | 554 |
| `passage_arist_mm_1_34_17` | Aristotle, Magna Moralia, 1.34.17 | 448 |
| `passage_arist_mm_1_34_18` | Aristotle, Magna Moralia, 1.34.18 | 308 |
| `passage_arist_mm_1_34_19` | Aristotle, Magna Moralia, 1.34.19 | 138 |
| `passage_arist_mm_1_34_2` | Aristotle, Magna Moralia, 1.34.2 | 142 |
| `passage_arist_mm_1_34_20` | Aristotle, Magna Moralia, 1.34.20 | 384 |
| `passage_arist_mm_1_34_21` | Aristotle, Magna Moralia, 1.34.21 | 310 |
| `passage_arist_mm_1_34_22` | Aristotle, Magna Moralia, 1.34.22 | 153 |
| `passage_arist_mm_1_34_23` | Aristotle, Magna Moralia, 1.34.23 | 248 |
| `passage_arist_mm_1_34_24` | Aristotle, Magna Moralia, 1.34.24 | 370 |
| `passage_arist_mm_1_34_25` | Aristotle, Magna Moralia, 1.34.25 | 383 |
| `passage_arist_mm_1_34_26` | Aristotle, Magna Moralia, 1.34.26 | 393 |
| `passage_arist_mm_1_34_27` | Aristotle, Magna Moralia, 1.34.27 | 525 |
| `passage_arist_mm_1_34_28` | Aristotle, Magna Moralia, 1.34.28 | 508 |
| `passage_arist_mm_1_34_29` | Aristotle, Magna Moralia, 1.34.29 | 315 |
| `passage_arist_mm_1_34_3` | Aristotle, Magna Moralia, 1.34.3 | 297 |
| `passage_arist_mm_1_34_30` | Aristotle, Magna Moralia, 1.34.30 | 205 |
| `passage_arist_mm_1_34_31` | Aristotle, Magna Moralia, 1.34.31 | 253 |
| `passage_arist_mm_1_34_32` | Aristotle, Magna Moralia, 1.34.32 | 171 |
| `passage_arist_mm_1_34_4` | Aristotle, Magna Moralia, 1.34.4 | 338 |
| `passage_arist_mm_1_34_5` | Aristotle, Magna Moralia, 1.34.5 | 237 |
| `passage_arist_mm_1_34_6` | Aristotle, Magna Moralia, 1.34.6 | 274 |
| `passage_arist_mm_1_34_7` | Aristotle, Magna Moralia, 1.34.7 | 197 |
| `passage_arist_mm_1_34_8` | Aristotle, Magna Moralia, 1.34.8 | 185 |
| `passage_arist_mm_1_34_9` | Aristotle, Magna Moralia, 1.34.9 | 282 |
| `passage_arist_mm_1_4_1` | Aristotle, Magna Moralia, 1.4.1 | 287 |
| `passage_arist_mm_1_4_10` | Aristotle, Magna Moralia, 1.4.10 | 223 |
| `passage_arist_mm_1_4_2` | Aristotle, Magna Moralia, 1.4.2 | 218 |
| `passage_arist_mm_1_4_3` | Aristotle, Magna Moralia, 1.4.3 | 300 |
| `passage_arist_mm_1_4_4` | Aristotle, Magna Moralia, 1.4.4 | 168 |
| `passage_arist_mm_1_4_5` | Aristotle, Magna Moralia, 1.4.5 | 440 |
| `passage_arist_mm_1_4_6` | Aristotle, Magna Moralia, 1.4.6 | 256 |
| `passage_arist_mm_1_4_7` | Aristotle, Magna Moralia, 1.4.7 | 305 |
| `passage_arist_mm_1_4_8` | Aristotle, Magna Moralia, 1.4.8 | 240 |
| `passage_arist_mm_1_4_9` | Aristotle, Magna Moralia, 1.4.9 | 708 |
| `passage_arist_mm_1_5_1` | Aristotle, Magna Moralia, 1.5.1 | 426 |
| `passage_arist_mm_1_5_2` | Aristotle, Magna Moralia, 1.5.2 | 264 |
| `passage_arist_mm_1_5_3` | Aristotle, Magna Moralia, 1.5.3 | 444 |
| `passage_arist_mm_1_5_4` | Aristotle, Magna Moralia, 1.5.4 | 316 |
| `passage_arist_mm_1_5_5` | Aristotle, Magna Moralia, 1.5.5 | 261 |
| `passage_arist_mm_1_6_1` | Aristotle, Magna Moralia, 1.6.1 | 228 |
| `passage_arist_mm_1_6_2` | Aristotle, Magna Moralia, 1.6.2 | 205 |
| `passage_arist_mm_1_6_3` | Aristotle, Magna Moralia, 1.6.3 | 357 |
| `passage_arist_mm_1_7_1` | Aristotle, Magna Moralia, 1.7.1 | 190 |
| `passage_arist_mm_1_7_2` | Aristotle, Magna Moralia, 1.7.2 | 227 |
| `passage_arist_mm_1_7_3` | Aristotle, Magna Moralia, 1.7.3 | 270 |
| `passage_arist_mm_1_7_4` | Aristotle, Magna Moralia, 1.7.4 | 325 |
| `passage_arist_mm_1_8_1` | Aristotle, Magna Moralia, 1.8.1 | 178 |
| `passage_arist_mm_1_8_2` | Aristotle, Magna Moralia, 1.8.2 | 305 |
| `passage_arist_mm_1_8_3` | Aristotle, Magna Moralia, 1.8.3 | 315 |
| `passage_arist_mm_1_9_1` | Aristotle, Magna Moralia, 1.9.1 | 390 |
| `passage_arist_mm_1_9_10` | Aristotle, Magna Moralia, 1.9.10 | 293 |
| `passage_arist_mm_1_9_11` | Aristotle, Magna Moralia, 1.9.11 | 369 |
| `passage_arist_mm_1_9_2` | Aristotle, Magna Moralia, 1.9.2 | 367 |
| `passage_arist_mm_1_9_3` | Aristotle, Magna Moralia, 1.9.3 | 321 |
| `passage_arist_mm_1_9_4` | Aristotle, Magna Moralia, 1.9.4 | 491 |
| `passage_arist_mm_1_9_5` | Aristotle, Magna Moralia, 1.9.5 | 210 |
| `passage_arist_mm_1_9_6` | Aristotle, Magna Moralia, 1.9.6 | 358 |
| `passage_arist_mm_1_9_7` | Aristotle, Magna Moralia, 1.9.7 | 278 |
| `passage_arist_mm_1_9_8` | Aristotle, Magna Moralia, 1.9.8 | 164 |
| `passage_arist_mm_1_9_9` | Aristotle, Magna Moralia, 1.9.9 | 273 |
| `passage_arist_mm_2_1_1` | Aristotle, Magna Moralia, 2.1.1 | 554 |
| `passage_arist_mm_2_10_1` | Aristotle, Magna Moralia, 2.10.1 | 271 |
| `passage_arist_mm_2_10_2` | Aristotle, Magna Moralia, 2.10.2 | 508 |
| `passage_arist_mm_2_10_3` | Aristotle, Magna Moralia, 2.10.3 | 211 |
| `passage_arist_mm_2_10_4` | Aristotle, Magna Moralia, 2.10.4 | 352 |
| `passage_arist_mm_2_10_5` | Aristotle, Magna Moralia, 2.10.5 | 92 |
| `passage_arist_mm_2_10_6` | Aristotle, Magna Moralia, 2.10.6 | 443 |
| `passage_arist_mm_2_10_7` | Aristotle, Magna Moralia, 2.10.7 | 149 |
| `passage_arist_mm_2_11_1` | Aristotle, Magna Moralia, 2.11.1 | 195 |
| `passage_arist_mm_2_11_10` | Aristotle, Magna Moralia, 2.11.10 | 229 |
| `passage_arist_mm_2_11_11` | Aristotle, Magna Moralia, 2.11.11 | 113 |
| `passage_arist_mm_2_11_12` | Aristotle, Magna Moralia, 2.11.12 | 198 |
| `passage_arist_mm_2_11_13` | Aristotle, Magna Moralia, 2.11.13 | 250 |
| `passage_arist_mm_2_11_14` | Aristotle, Magna Moralia, 2.11.14 | 86 |
| `passage_arist_mm_2_11_15` | Aristotle, Magna Moralia, 2.11.15 | 450 |
| `passage_arist_mm_2_11_16` | Aristotle, Magna Moralia, 2.11.16 | 211 |
| `passage_arist_mm_2_11_17` | Aristotle, Magna Moralia, 2.11.17 | 331 |
| `passage_arist_mm_2_11_18` | Aristotle, Magna Moralia, 2.11.18 | 251 |
| `passage_arist_mm_2_11_19` | Aristotle, Magna Moralia, 2.11.19 | 202 |
| `passage_arist_mm_2_11_2` | Aristotle, Magna Moralia, 2.11.2 | 443 |
| `passage_arist_mm_2_11_20` | Aristotle, Magna Moralia, 2.11.20 | 250 |
| `passage_arist_mm_2_11_21` | Aristotle, Magna Moralia, 2.11.21 | 319 |
| `passage_arist_mm_2_11_22` | Aristotle, Magna Moralia, 2.11.22 | 178 |
| `passage_arist_mm_2_11_23` | Aristotle, Magna Moralia, 2.11.23 | 221 |
| `passage_arist_mm_2_11_24` | Aristotle, Magna Moralia, 2.11.24 | 389 |
| `passage_arist_mm_2_11_25` | Aristotle, Magna Moralia, 2.11.25 | 383 |
| `passage_arist_mm_2_11_26` | Aristotle, Magna Moralia, 2.11.26 | 197 |
| `passage_arist_mm_2_11_27` | Aristotle, Magna Moralia, 2.11.27 | 169 |
| `passage_arist_mm_2_11_28` | Aristotle, Magna Moralia, 2.11.28 | 439 |
| `passage_arist_mm_2_11_29` | Aristotle, Magna Moralia, 2.11.29 | 260 |
| `passage_arist_mm_2_11_3` | Aristotle, Magna Moralia, 2.11.3 | 301 |
| `passage_arist_mm_2_11_30` | Aristotle, Magna Moralia, 2.11.30 | 311 |
| `passage_arist_mm_2_11_31` | Aristotle, Magna Moralia, 2.11.31 | 321 |
| `passage_arist_mm_2_11_32` | Aristotle, Magna Moralia, 2.11.32 | 270 |
| `passage_arist_mm_2_11_33` | Aristotle, Magna Moralia, 2.11.33 | 409 |
| `passage_arist_mm_2_11_34` | Aristotle, Magna Moralia, 2.11.34 | 112 |
| `passage_arist_mm_2_11_35` | Aristotle, Magna Moralia, 2.11.35 | 154 |
| `passage_arist_mm_2_11_36` | Aristotle, Magna Moralia, 2.11.36 | 158 |
| `passage_arist_mm_2_11_37` | Aristotle, Magna Moralia, 2.11.37 | 110 |
| `passage_arist_mm_2_11_38` | Aristotle, Magna Moralia, 2.11.38 | 207 |
| `passage_arist_mm_2_11_39` | Aristotle, Magna Moralia, 2.11.39 | 316 |
| `passage_arist_mm_2_11_4` | Aristotle, Magna Moralia, 2.11.4 | 146 |
| `passage_arist_mm_2_11_40` | Aristotle, Magna Moralia, 2.11.40 | 214 |
| `passage_arist_mm_2_11_41` | Aristotle, Magna Moralia, 2.11.41 | 325 |
| `passage_arist_mm_2_11_42` | Aristotle, Magna Moralia, 2.11.42 | 262 |
| `passage_arist_mm_2_11_43` | Aristotle, Magna Moralia, 2.11.43 | 168 |
| `passage_arist_mm_2_11_44` | Aristotle, Magna Moralia, 2.11.44 | 274 |
| `passage_arist_mm_2_11_45` | Aristotle, Magna Moralia, 2.11.45 | 266 |
| `passage_arist_mm_2_11_46` | Aristotle, Magna Moralia, 2.11.46 | 214 |
| `passage_arist_mm_2_11_47` | Aristotle, Magna Moralia, 2.11.47 | 541 |
| `passage_arist_mm_2_11_48` | Aristotle, Magna Moralia, 2.11.48 | 274 |
| `passage_arist_mm_2_11_49` | Aristotle, Magna Moralia, 2.11.49 | 335 |
| `passage_arist_mm_2_11_5` | Aristotle, Magna Moralia, 2.11.5 | 193 |
| `passage_arist_mm_2_11_50` | Aristotle, Magna Moralia, 2.11.50 | 390 |
| `passage_arist_mm_2_11_51` | Aristotle, Magna Moralia, 2.11.51 | 262 |
| `passage_arist_mm_2_11_52` | Aristotle, Magna Moralia, 2.11.52 | 198 |
| `passage_arist_mm_2_11_53` | Aristotle, Magna Moralia, 2.11.53 | 280 |
| `passage_arist_mm_2_11_6` | Aristotle, Magna Moralia, 2.11.6 | 302 |
| `passage_arist_mm_2_11_7` | Aristotle, Magna Moralia, 2.11.7 | 260 |
| `passage_arist_mm_2_11_8` | Aristotle, Magna Moralia, 2.11.8 | 175 |
| `passage_arist_mm_2_11_9` | Aristotle, Magna Moralia, 2.11.9 | 200 |
| `passage_arist_mm_2_12_1` | Aristotle, Magna Moralia, 2.12.1 | 330 |
| `passage_arist_mm_2_12_10` | Aristotle, Magna Moralia, 2.12.10 | 81 |
| `passage_arist_mm_2_12_11` | Aristotle, Magna Moralia, 2.12.11 | 238 |
| `passage_arist_mm_2_12_12` | Aristotle, Magna Moralia, 2.12.12 | 347 |
| `passage_arist_mm_2_12_13` | Aristotle, Magna Moralia, 2.12.13 | 142 |
| `passage_arist_mm_2_12_2` | Aristotle, Magna Moralia, 2.12.2 | 148 |
| `passage_arist_mm_2_12_3` | Aristotle, Magna Moralia, 2.12.3 | 261 |
| `passage_arist_mm_2_12_4` | Aristotle, Magna Moralia, 2.12.4 | 292 |
| `passage_arist_mm_2_12_5` | Aristotle, Magna Moralia, 2.12.5 | 143 |
| `passage_arist_mm_2_12_6` | Aristotle, Magna Moralia, 2.12.6 | 116 |
| `passage_arist_mm_2_12_7` | Aristotle, Magna Moralia, 2.12.7 | 272 |
| `passage_arist_mm_2_12_8` | Aristotle, Magna Moralia, 2.12.8 | 171 |
| `passage_arist_mm_2_12_9` | Aristotle, Magna Moralia, 2.12.9 | 172 |
| `passage_arist_mm_2_13_1` | Aristotle, Magna Moralia, 2.13.1 | 342 |
| `passage_arist_mm_2_13_2` | Aristotle, Magna Moralia, 2.13.2 | 398 |
| `passage_arist_mm_2_13_3` | Aristotle, Magna Moralia, 2.13.3 | 189 |
| `passage_arist_mm_2_13_4` | Aristotle, Magna Moralia, 2.13.4 | 137 |
| `passage_arist_mm_2_14_1` | Aristotle, Magna Moralia, 2.14.1 | 239 |
| `passage_arist_mm_2_14_2` | Aristotle, Magna Moralia, 2.14.2 | 308 |
| `passage_arist_mm_2_14_3` | Aristotle, Magna Moralia, 2.14.3 | 256 |
| `passage_arist_mm_2_15_1` | Aristotle, Magna Moralia, 2.15.1 | 416 |
| `passage_arist_mm_2_15_2` | Aristotle, Magna Moralia, 2.15.2 | 94 |
| `passage_arist_mm_2_15_3` | Aristotle, Magna Moralia, 2.15.3 | 203 |
| `passage_arist_mm_2_15_4` | Aristotle, Magna Moralia, 2.15.4 | 504 |
| `passage_arist_mm_2_15_5` | Aristotle, Magna Moralia, 2.15.5 | 352 |
| `passage_arist_mm_2_15_6` | Aristotle, Magna Moralia, 2.15.6 | 280 |
| `passage_arist_mm_2_15_7` | Aristotle, Magna Moralia, 2.15.7 | 312 |
| `passage_arist_mm_2_15_8` | Aristotle, Magna Moralia, 2.15.8 | 136 |
| `passage_arist_mm_2_15_9` | Aristotle, Magna Moralia, 2.15.9 | 312 |
| `passage_arist_mm_2_16_1` | Aristotle, Magna Moralia, 2.16.1 | 421 |
| `passage_arist_mm_2_16_2` | Aristotle, Magna Moralia, 2.16.2 | 154 |
| `passage_arist_mm_2_16_3` | Aristotle, Magna Moralia, 2.16.3 | 244 |
| `passage_arist_mm_2_17_1` | Aristotle, Magna Moralia, 2.17.1 | 326 |
| `passage_arist_mm_2_17_2` | Aristotle, Magna Moralia, 2.17.2 | 362 |
| `passage_arist_mm_2_2_1` | Aristotle, Magna Moralia, 2.2.1 | 432 |
| `passage_arist_mm_2_3_1` | Aristotle, Magna Moralia, 2.3.1 | 284 |
| `passage_arist_mm_2_3_10` | Aristotle, Magna Moralia, 2.3.10 | 348 |
| `passage_arist_mm_2_3_11` | Aristotle, Magna Moralia, 2.3.11 | 504 |
| `passage_arist_mm_2_3_12` | Aristotle, Magna Moralia, 2.3.12 | 411 |
| `passage_arist_mm_2_3_13` | Aristotle, Magna Moralia, 2.3.13 | 332 |
| `passage_arist_mm_2_3_14` | Aristotle, Magna Moralia, 2.3.14 | 314 |
| `passage_arist_mm_2_3_15` | Aristotle, Magna Moralia, 2.3.15 | 368 |
| `passage_arist_mm_2_3_16` | Aristotle, Magna Moralia, 2.3.16 | 378 |
| `passage_arist_mm_2_3_17` | Aristotle, Magna Moralia, 2.3.17 | 243 |
| `passage_arist_mm_2_3_2` | Aristotle, Magna Moralia, 2.3.2 | 280 |
| `passage_arist_mm_2_3_3` | Aristotle, Magna Moralia, 2.3.3 | 339 |
| `passage_arist_mm_2_3_4` | Aristotle, Magna Moralia, 2.3.4 | 361 |
| `passage_arist_mm_2_3_5` | Aristotle, Magna Moralia, 2.3.5 | 150 |
| `passage_arist_mm_2_3_6` | Aristotle, Magna Moralia, 2.3.6 | 548 |
| `passage_arist_mm_2_3_7` | Aristotle, Magna Moralia, 2.3.7 | 499 |
| `passage_arist_mm_2_3_8` | Aristotle, Magna Moralia, 2.3.8 | 387 |
| `passage_arist_mm_2_3_9` | Aristotle, Magna Moralia, 2.3.9 | 159 |
| `passage_arist_mm_2_4_1` | Aristotle, Magna Moralia, 2.4.1 | 249 |
| `passage_arist_mm_2_4_2` | Aristotle, Magna Moralia, 2.4.2 | 200 |
| `passage_arist_mm_2_4_3` | Aristotle, Magna Moralia, 2.4.3 | 218 |
| `passage_arist_mm_2_5_1` | Aristotle, Magna Moralia, 2.5.1 | 152 |
| `passage_arist_mm_2_5_2` | Aristotle, Magna Moralia, 2.5.2 | 277 |
| `passage_arist_mm_2_5_3` | Aristotle, Magna Moralia, 2.5.3 | 202 |
| `passage_arist_mm_2_6_1` | Aristotle, Magna Moralia, 2.6.1 | 292 |
| `passage_arist_mm_2_6_10` | Aristotle, Magna Moralia, 2.6.10 | 308 |
| `passage_arist_mm_2_6_11` | Aristotle, Magna Moralia, 2.6.11 | 111 |
| `passage_arist_mm_2_6_12` | Aristotle, Magna Moralia, 2.6.12 | 289 |
| `passage_arist_mm_2_6_13` | Aristotle, Magna Moralia, 2.6.13 | 330 |
| `passage_arist_mm_2_6_14` | Aristotle, Magna Moralia, 2.6.14 | 361 |
| `passage_arist_mm_2_6_15` | Aristotle, Magna Moralia, 2.6.15 | 517 |
| `passage_arist_mm_2_6_16` | Aristotle, Magna Moralia, 2.6.16 | 468 |
| `passage_arist_mm_2_6_17` | Aristotle, Magna Moralia, 2.6.17 | 472 |
| `passage_arist_mm_2_6_18` | Aristotle, Magna Moralia, 2.6.18 | 505 |
| `passage_arist_mm_2_6_19` | Aristotle, Magna Moralia, 2.6.19 | 131 |
| `passage_arist_mm_2_6_2` | Aristotle, Magna Moralia, 2.6.2 | 260 |
| `passage_arist_mm_2_6_20` | Aristotle, Magna Moralia, 2.6.20 | 501 |
| `passage_arist_mm_2_6_21` | Aristotle, Magna Moralia, 2.6.21 | 388 |
| `passage_arist_mm_2_6_22` | Aristotle, Magna Moralia, 2.6.22 | 432 |
| `passage_arist_mm_2_6_23` | Aristotle, Magna Moralia, 2.6.23 | 318 |
| `passage_arist_mm_2_6_24` | Aristotle, Magna Moralia, 2.6.24 | 434 |
| `passage_arist_mm_2_6_25` | Aristotle, Magna Moralia, 2.6.25 | 200 |
| `passage_arist_mm_2_6_26` | Aristotle, Magna Moralia, 2.6.26 | 464 |
| `passage_arist_mm_2_6_27` | Aristotle, Magna Moralia, 2.6.27 | 223 |
| `passage_arist_mm_2_6_28` | Aristotle, Magna Moralia, 2.6.28 | 261 |
| `passage_arist_mm_2_6_29` | Aristotle, Magna Moralia, 2.6.29 | 342 |
| `passage_arist_mm_2_6_3` | Aristotle, Magna Moralia, 2.6.3 | 159 |
| `passage_arist_mm_2_6_30` | Aristotle, Magna Moralia, 2.6.30 | 281 |
| `passage_arist_mm_2_6_31` | Aristotle, Magna Moralia, 2.6.31 | 248 |
| `passage_arist_mm_2_6_32` | Aristotle, Magna Moralia, 2.6.32 | 155 |
| `passage_arist_mm_2_6_33` | Aristotle, Magna Moralia, 2.6.33 | 427 |
| `passage_arist_mm_2_6_34` | Aristotle, Magna Moralia, 2.6.34 | 216 |
| `passage_arist_mm_2_6_35` | Aristotle, Magna Moralia, 2.6.35 | 469 |
| `passage_arist_mm_2_6_36` | Aristotle, Magna Moralia, 2.6.36 | 529 |
| `passage_arist_mm_2_6_37` | Aristotle, Magna Moralia, 2.6.37 | 288 |
| `passage_arist_mm_2_6_38` | Aristotle, Magna Moralia, 2.6.38 | 416 |
| `passage_arist_mm_2_6_39` | Aristotle, Magna Moralia, 2.6.39 | 298 |
| `passage_arist_mm_2_6_4` | Aristotle, Magna Moralia, 2.6.4 | 322 |
| `passage_arist_mm_2_6_40` | Aristotle, Magna Moralia, 2.6.40 | 171 |
| `passage_arist_mm_2_6_41` | Aristotle, Magna Moralia, 2.6.41 | 282 |
| `passage_arist_mm_2_6_42` | Aristotle, Magna Moralia, 2.6.42 | 167 |
| `passage_arist_mm_2_6_43` | Aristotle, Magna Moralia, 2.6.43 | 541 |
| `passage_arist_mm_2_6_44` | Aristotle, Magna Moralia, 2.6.44 | 264 |
| `passage_arist_mm_2_6_5` | Aristotle, Magna Moralia, 2.6.5 | 364 |
| `passage_arist_mm_2_6_6` | Aristotle, Magna Moralia, 2.6.6 | 206 |
| `passage_arist_mm_2_6_7` | Aristotle, Magna Moralia, 2.6.7 | 366 |
| `passage_arist_mm_2_6_8` | Aristotle, Magna Moralia, 2.6.8 | 577 |
| `passage_arist_mm_2_6_9` | Aristotle, Magna Moralia, 2.6.9 | 426 |
| `passage_arist_mm_2_7_1` | Aristotle, Magna Moralia, 2.7.1 | 301 |
| `passage_arist_mm_2_7_10` | Aristotle, Magna Moralia, 2.7.10 | 507 |
| `passage_arist_mm_2_7_11` | Aristotle, Magna Moralia, 2.7.11 | 478 |
| `passage_arist_mm_2_7_12` | Aristotle, Magna Moralia, 2.7.12 | 557 |
| `passage_arist_mm_2_7_13` | Aristotle, Magna Moralia, 2.7.13 | 324 |
| `passage_arist_mm_2_7_14` | Aristotle, Magna Moralia, 2.7.14 | 350 |
| `passage_arist_mm_2_7_15` | Aristotle, Magna Moralia, 2.7.15 | 300 |
| `passage_arist_mm_2_7_16` | Aristotle, Magna Moralia, 2.7.16 | 404 |
| `passage_arist_mm_2_7_17` | Aristotle, Magna Moralia, 2.7.17 | 421 |
| `passage_arist_mm_2_7_18` | Aristotle, Magna Moralia, 2.7.18 | 451 |
| `passage_arist_mm_2_7_19` | Aristotle, Magna Moralia, 2.7.19 | 302 |
| `passage_arist_mm_2_7_2` | Aristotle, Magna Moralia, 2.7.2 | 405 |
| `passage_arist_mm_2_7_20` | Aristotle, Magna Moralia, 2.7.20 | 191 |
| `passage_arist_mm_2_7_21` | Aristotle, Magna Moralia, 2.7.21 | 282 |
| `passage_arist_mm_2_7_22` | Aristotle, Magna Moralia, 2.7.22 | 217 |
| `passage_arist_mm_2_7_23` | Aristotle, Magna Moralia, 2.7.23 | 422 |
| `passage_arist_mm_2_7_24` | Aristotle, Magna Moralia, 2.7.24 | 345 |
| `passage_arist_mm_2_7_25` | Aristotle, Magna Moralia, 2.7.25 | 152 |
| `passage_arist_mm_2_7_26` | Aristotle, Magna Moralia, 2.7.26 | 298 |
| `passage_arist_mm_2_7_27` | Aristotle, Magna Moralia, 2.7.27 | 280 |
| `passage_arist_mm_2_7_28` | Aristotle, Magna Moralia, 2.7.28 | 606 |
| `passage_arist_mm_2_7_29` | Aristotle, Magna Moralia, 2.7.29 | 388 |
| `passage_arist_mm_2_7_3` | Aristotle, Magna Moralia, 2.7.3 | 603 |
| `passage_arist_mm_2_7_30` | Aristotle, Magna Moralia, 2.7.30 | 812 |
| `passage_arist_mm_2_7_4` | Aristotle, Magna Moralia, 2.7.4 | 460 |
| `passage_arist_mm_2_7_5` | Aristotle, Magna Moralia, 2.7.5 | 223 |
| `passage_arist_mm_2_7_6` | Aristotle, Magna Moralia, 2.7.6 | 256 |
| `passage_arist_mm_2_7_7` | Aristotle, Magna Moralia, 2.7.7 | 276 |
| `passage_arist_mm_2_7_8` | Aristotle, Magna Moralia, 2.7.8 | 360 |
| `passage_arist_mm_2_7_9` | Aristotle, Magna Moralia, 2.7.9 | 249 |
| `passage_arist_mm_2_8_1` | Aristotle, Magna Moralia, 2.8.1 | 351 |
| `passage_arist_mm_2_8_10` | Aristotle, Magna Moralia, 2.8.10 | 326 |
| `passage_arist_mm_2_8_11` | Aristotle, Magna Moralia, 2.8.11 | 300 |
| `passage_arist_mm_2_8_12` | Aristotle, Magna Moralia, 2.8.12 | 140 |
| `passage_arist_mm_2_8_2` | Aristotle, Magna Moralia, 2.8.2 | 507 |
| `passage_arist_mm_2_8_3` | Aristotle, Magna Moralia, 2.8.3 | 347 |
| `passage_arist_mm_2_8_4` | Aristotle, Magna Moralia, 2.8.4 | 285 |
| `passage_arist_mm_2_8_5` | Aristotle, Magna Moralia, 2.8.5 | 515 |
| `passage_arist_mm_2_8_6` | Aristotle, Magna Moralia, 2.8.6 | 240 |
| `passage_arist_mm_2_8_7` | Aristotle, Magna Moralia, 2.8.7 | 275 |
| `passage_arist_mm_2_8_8` | Aristotle, Magna Moralia, 2.8.8 | 213 |
| `passage_arist_mm_2_8_9` | Aristotle, Magna Moralia, 2.8.9 | 218 |
| `passage_arist_mm_2_9_1` | Aristotle, Magna Moralia, 2.9.1 | 157 |
| `passage_arist_mm_2_9_2` | Aristotle, Magna Moralia, 2.9.2 | 263 |
| `passage_arist_mm_2_9_3` | Aristotle, Magna Moralia, 2.9.3 | 315 |
| `passage_arist_mm_2_9_4` | Aristotle, Magna Moralia, 2.9.4 | 296 |
| `passage_arist_mm_2_9_5` | Aristotle, Magna Moralia, 2.9.5 | 232 |

### Titus Lucretius Carus — De Rerum Natura

- **Language:** Latin
- **Passages:** 300
- **Characters:** 329,775
- **Canonical ID:** `urn:cts:latinLit:phi0550.phi001`

| node_id | label | chars |
|---------|-------|-------|
| `passage_lucr_drn_10001024` | Titus Lucretius Carus, De Rerum Natura, 1.1000-1024 | 1,084 |
| `passage_lucr_drn_10011025` | Titus Lucretius Carus, De Rerum Natura, 3.1001-1025 | 1,145 |
| `passage_lucr_drn_10011025_s178` | Titus Lucretius Carus, De Rerum Natura, 4.1001-1025 | 1,101 |
| `passage_lucr_drn_10011025_s230` | Titus Lucretius Carus, De Rerum Natura, 5.1001-1025 | 1,097 |
| `passage_lucr_drn_10011025_s289` | Titus Lucretius Carus, De Rerum Natura, 6.1001-1025 | 1,131 |
| `passage_lucr_drn_101125` | Titus Lucretius Carus, De Rerum Natura, 1.101-125 | 1,082 |
| `passage_lucr_drn_101125_s142` | Titus Lucretius Carus, De Rerum Natura, 4.101-125 | 1,141 |
| `passage_lucr_drn_101125_s194` | Titus Lucretius Carus, De Rerum Natura, 5.101-125 | 1,086 |
| `passage_lucr_drn_101125_s253` | Titus Lucretius Carus, De Rerum Natura, 6.101-125 | 1,131 |
| `passage_lucr_drn_101125_s50` | Titus Lucretius Carus, De Rerum Natura, 2.101-125 | 1,064 |
| `passage_lucr_drn_101125_s98` | Titus Lucretius Carus, De Rerum Natura, 3.101-125 | 1,120 |
| `passage_lucr_drn_10221046` | Titus Lucretius Carus, De Rerum Natura, 2.1022-1046 | 1,124 |
| `passage_lucr_drn_10251049` | Titus Lucretius Carus, De Rerum Natura, 1.1025-1049 | 1,052 |
| `passage_lucr_drn_10261050` | Titus Lucretius Carus, De Rerum Natura, 3.1026-1050 | 1,126 |
| `passage_lucr_drn_10261050_s179` | Titus Lucretius Carus, De Rerum Natura, 4.1026-1050 | 1,120 |
| `passage_lucr_drn_10261050_s231` | Titus Lucretius Carus, De Rerum Natura, 5.1026-1050 | 1,127 |
| `passage_lucr_drn_10261050_s290` | Titus Lucretius Carus, De Rerum Natura, 6.1026-1050 | 1,143 |
| `passage_lucr_drn_10471071` | Titus Lucretius Carus, De Rerum Natura, 2.1047-1071 | 1,096 |
| `passage_lucr_drn_10501074` | Titus Lucretius Carus, De Rerum Natura, 1.1050-1074 | 1,060 |
| `passage_lucr_drn_10511075` | Titus Lucretius Carus, De Rerum Natura, 3.1051-1075 | 1,165 |
| `passage_lucr_drn_10511075_s180` | Titus Lucretius Carus, De Rerum Natura, 4.1051-1075 | 1,114 |
| `passage_lucr_drn_10511075_s232` | Titus Lucretius Carus, De Rerum Natura, 5.1051-1075 | 1,125 |
| `passage_lucr_drn_10511075_s291` | Titus Lucretius Carus, De Rerum Natura, 6.1051-1075 | 1,122 |
| `passage_lucr_drn_10721096` | Titus Lucretius Carus, De Rerum Natura, 2.1072-1096 | 1,145 |
| `passage_lucr_drn_10751107` | Titus Lucretius Carus, De Rerum Natura, 1.1075-1107 | 1,090 |
| `passage_lucr_drn_10761094` | Titus Lucretius Carus, De Rerum Natura, 3.1076-1094 | 843 |
| `passage_lucr_drn_10761100` | Titus Lucretius Carus, De Rerum Natura, 4.1076-1100 | 1,157 |
| `passage_lucr_drn_10761100_s233` | Titus Lucretius Carus, De Rerum Natura, 5.1076-1100 | 1,094 |
| `passage_lucr_drn_10761100_s292` | Titus Lucretius Carus, De Rerum Natura, 6.1076-1100 | 1,113 |
| `passage_lucr_drn_10971121` | Titus Lucretius Carus, De Rerum Natura, 2.1097-1121 | 1,116 |
| `passage_lucr_drn_11011125` | Titus Lucretius Carus, De Rerum Natura, 4.1101-1125 | 1,128 |
| `passage_lucr_drn_11011125_s234` | Titus Lucretius Carus, De Rerum Natura, 5.1101-1125 | 1,102 |
| `passage_lucr_drn_11011125_s293` | Titus Lucretius Carus, De Rerum Natura, 6.1101-1125 | 1,145 |
| `passage_lucr_drn_11081117` | Titus Lucretius Carus, De Rerum Natura, 1.1108-1117 | 431 |
| `passage_lucr_drn_11221146` | Titus Lucretius Carus, De Rerum Natura, 2.1122-1146 | 1,133 |
| `passage_lucr_drn_11261150` | Titus Lucretius Carus, De Rerum Natura, 4.1126-1150 | 1,140 |
| `passage_lucr_drn_11261150_s235` | Titus Lucretius Carus, De Rerum Natura, 5.1126-1150 | 1,117 |
| `passage_lucr_drn_11261150_s294` | Titus Lucretius Carus, De Rerum Natura, 6.1126-1150 | 1,090 |
| `passage_lucr_drn_11471171` | Titus Lucretius Carus, De Rerum Natura, 2.1147-1171 | 1,117 |
| `passage_lucr_drn_11511175` | Titus Lucretius Carus, De Rerum Natura, 4.1151-1175 | 1,153 |
| `passage_lucr_drn_11511175_s236` | Titus Lucretius Carus, De Rerum Natura, 5.1151-1175 | 1,096 |
| `passage_lucr_drn_11511175_s295` | Titus Lucretius Carus, De Rerum Natura, 6.1151-1175 | 1,105 |
| `passage_lucr_drn_11721174` | Titus Lucretius Carus, De Rerum Natura, 2.1172-1174 | 131 |
| `passage_lucr_drn_11761200` | Titus Lucretius Carus, De Rerum Natura, 4.1176-1200 | 1,136 |
| `passage_lucr_drn_11761200_s237` | Titus Lucretius Carus, De Rerum Natura, 5.1176-1200 | 1,102 |
| `passage_lucr_drn_11761200_s296` | Titus Lucretius Carus, De Rerum Natura, 6.1176-1200 | 1,087 |
| `passage_lucr_drn_12011225` | Titus Lucretius Carus, De Rerum Natura, 4.1201-1225 | 1,141 |
| `passage_lucr_drn_12011225_s238` | Titus Lucretius Carus, De Rerum Natura, 5.1201-1225 | 1,077 |
| `passage_lucr_drn_12011225_s297` | Titus Lucretius Carus, De Rerum Natura, 6.1201-1225 | 1,091 |
| `passage_lucr_drn_12261250` | Titus Lucretius Carus, De Rerum Natura, 4.1226-1250 | 1,131 |
| `passage_lucr_drn_12261250_s239` | Titus Lucretius Carus, De Rerum Natura, 5.1226-1250 | 1,112 |
| `passage_lucr_drn_12261250_s298` | Titus Lucretius Carus, De Rerum Natura, 6.1226-1250 | 1,081 |
| `passage_lucr_drn_125` | Titus Lucretius Carus, De Rerum Natura, 1.1-25 | 1,100 |
| `passage_lucr_drn_125_s138` | Titus Lucretius Carus, De Rerum Natura, 4.1-25 | 1,077 |
| `passage_lucr_drn_125_s190` | Titus Lucretius Carus, De Rerum Natura, 5.1-25 | 1,109 |
| `passage_lucr_drn_125_s249` | Titus Lucretius Carus, De Rerum Natura, 6.1-25 | 1,085 |
| `passage_lucr_drn_125_s46` | Titus Lucretius Carus, De Rerum Natura, 2.1-25 | 1,097 |
| `passage_lucr_drn_125_s94` | Titus Lucretius Carus, De Rerum Natura, 3.1-25 | 1,094 |
| `passage_lucr_drn_12511275` | Titus Lucretius Carus, De Rerum Natura, 4.1251-1275 | 1,107 |
| `passage_lucr_drn_12511275_s240` | Titus Lucretius Carus, De Rerum Natura, 5.1251-1275 | 1,100 |
| `passage_lucr_drn_12511275_s299` | Titus Lucretius Carus, De Rerum Natura, 6.1251-1275 | 1,103 |
| `passage_lucr_drn_126150` | Titus Lucretius Carus, De Rerum Natura, 1.126-150 | 1,100 |
| `passage_lucr_drn_126150_s143` | Titus Lucretius Carus, De Rerum Natura, 4.126-150 | 1,117 |
| `passage_lucr_drn_126150_s195` | Titus Lucretius Carus, De Rerum Natura, 5.126-150 | 1,152 |
| `passage_lucr_drn_126150_s254` | Titus Lucretius Carus, De Rerum Natura, 6.126-150 | 1,140 |
| `passage_lucr_drn_126150_s51` | Titus Lucretius Carus, De Rerum Natura, 2.126-150 | 1,097 |
| `passage_lucr_drn_126150_s99` | Titus Lucretius Carus, De Rerum Natura, 3.126-150 | 1,148 |
| `passage_lucr_drn_12761286` | Titus Lucretius Carus, De Rerum Natura, 6.1276-1286 | 492 |
| `passage_lucr_drn_12761287` | Titus Lucretius Carus, De Rerum Natura, 4.1276-1287 | 530 |
| `passage_lucr_drn_12761300` | Titus Lucretius Carus, De Rerum Natura, 5.1276-1300 | 1,110 |
| `passage_lucr_drn_13011325` | Titus Lucretius Carus, De Rerum Natura, 5.1301-1325 | 1,100 |
| `passage_lucr_drn_13261350` | Titus Lucretius Carus, De Rerum Natura, 5.1326-1350 | 1,109 |
| `passage_lucr_drn_13511375` | Titus Lucretius Carus, De Rerum Natura, 5.1351-1375 | 1,096 |
| `passage_lucr_drn_13761400` | Titus Lucretius Carus, De Rerum Natura, 5.1376-1400 | 1,088 |
| `passage_lucr_drn_14011425` | Titus Lucretius Carus, De Rerum Natura, 5.1401-1425 | 1,118 |
| `passage_lucr_drn_14261450` | Titus Lucretius Carus, De Rerum Natura, 5.1426-1450 | 1,108 |
| `passage_lucr_drn_14511457` | Titus Lucretius Carus, De Rerum Natura, 5.1451-1457 | 299 |
| `passage_lucr_drn_151174` | Titus Lucretius Carus, De Rerum Natura, 2.151-174 | 1,038 |
| `passage_lucr_drn_151175` | Titus Lucretius Carus, De Rerum Natura, 1.151-175 | 1,103 |
| `passage_lucr_drn_151175_s100` | Titus Lucretius Carus, De Rerum Natura, 3.151-175 | 1,133 |
| `passage_lucr_drn_151175_s144` | Titus Lucretius Carus, De Rerum Natura, 4.151-175 | 1,127 |
| `passage_lucr_drn_151175_s196` | Titus Lucretius Carus, De Rerum Natura, 5.151-175 | 1,105 |
| `passage_lucr_drn_151175_s255` | Titus Lucretius Carus, De Rerum Natura, 6.151-175 | 1,118 |
| `passage_lucr_drn_175199` | Titus Lucretius Carus, De Rerum Natura, 2.175-199 | 1,131 |
| `passage_lucr_drn_176200` | Titus Lucretius Carus, De Rerum Natura, 1.176-200 | 1,098 |
| `passage_lucr_drn_176200_s101` | Titus Lucretius Carus, De Rerum Natura, 3.176-200 | 1,118 |
| `passage_lucr_drn_176200_s145` | Titus Lucretius Carus, De Rerum Natura, 4.176-200 | 1,148 |
| `passage_lucr_drn_176200_s197` | Titus Lucretius Carus, De Rerum Natura, 5.176-200 | 1,096 |
| `passage_lucr_drn_176200_s256` | Titus Lucretius Carus, De Rerum Natura, 6.176-200 | 1,129 |
| `passage_lucr_drn_200224` | Titus Lucretius Carus, De Rerum Natura, 2.200-224 | 1,135 |
| `passage_lucr_drn_201225` | Titus Lucretius Carus, De Rerum Natura, 1.201-225 | 1,108 |
| `passage_lucr_drn_201225_s102` | Titus Lucretius Carus, De Rerum Natura, 3.201-225 | 1,111 |
| `passage_lucr_drn_201225_s146` | Titus Lucretius Carus, De Rerum Natura, 4.201-225 | 1,119 |
| `passage_lucr_drn_201225_s198` | Titus Lucretius Carus, De Rerum Natura, 5.201-225 | 1,078 |
| `passage_lucr_drn_201225_s257` | Titus Lucretius Carus, De Rerum Natura, 6.201-225 | 1,145 |
| `passage_lucr_drn_225249` | Titus Lucretius Carus, De Rerum Natura, 2.225-249 | 1,140 |
| `passage_lucr_drn_226250` | Titus Lucretius Carus, De Rerum Natura, 1.226-250 | 1,113 |
| `passage_lucr_drn_226250_s103` | Titus Lucretius Carus, De Rerum Natura, 3.226-250 | 1,150 |
| `passage_lucr_drn_226250_s147` | Titus Lucretius Carus, De Rerum Natura, 4.226-250 | 1,131 |
| `passage_lucr_drn_226250_s199` | Titus Lucretius Carus, De Rerum Natura, 5.226-250 | 1,107 |
| `passage_lucr_drn_226250_s258` | Titus Lucretius Carus, De Rerum Natura, 6.226-250 | 1,113 |
| `passage_lucr_drn_250274` | Titus Lucretius Carus, De Rerum Natura, 2.250-274 | 1,081 |
| `passage_lucr_drn_251275` | Titus Lucretius Carus, De Rerum Natura, 1.251-275 | 1,106 |
| `passage_lucr_drn_251275_s104` | Titus Lucretius Carus, De Rerum Natura, 3.251-275 | 1,138 |
| `passage_lucr_drn_251275_s148` | Titus Lucretius Carus, De Rerum Natura, 4.251-275 | 1,149 |
| `passage_lucr_drn_251275_s200` | Titus Lucretius Carus, De Rerum Natura, 5.251-275 | 1,107 |
| `passage_lucr_drn_251275_s259` | Titus Lucretius Carus, De Rerum Natura, 6.251-275 | 1,126 |
| `passage_lucr_drn_2650` | Titus Lucretius Carus, De Rerum Natura, 1.26-50 | 1,091 |
| `passage_lucr_drn_2650_s139` | Titus Lucretius Carus, De Rerum Natura, 4.26-50 | 1,133 |
| `passage_lucr_drn_2650_s191` | Titus Lucretius Carus, De Rerum Natura, 5.26-50 | 1,142 |
| `passage_lucr_drn_2650_s250` | Titus Lucretius Carus, De Rerum Natura, 6.26-50 | 1,113 |
| `passage_lucr_drn_2650_s47` | Titus Lucretius Carus, De Rerum Natura, 2.26-50 | 1,107 |
| `passage_lucr_drn_2650_s95` | Titus Lucretius Carus, De Rerum Natura, 3.26-50 | 1,100 |
| `passage_lucr_drn_275299` | Titus Lucretius Carus, De Rerum Natura, 2.275-299 | 1,089 |
| `passage_lucr_drn_276300` | Titus Lucretius Carus, De Rerum Natura, 1.276-300 | 1,122 |
| `passage_lucr_drn_276300_s105` | Titus Lucretius Carus, De Rerum Natura, 3.276-300 | 1,146 |
| `passage_lucr_drn_276300_s149` | Titus Lucretius Carus, De Rerum Natura, 4.276-300 | 1,153 |
| `passage_lucr_drn_276300_s201` | Titus Lucretius Carus, De Rerum Natura, 5.276-300 | 1,132 |
| `passage_lucr_drn_276300_s260` | Titus Lucretius Carus, De Rerum Natura, 6.276-300 | 1,122 |
| `passage_lucr_drn_300324` | Titus Lucretius Carus, De Rerum Natura, 2.300-324 | 1,096 |
| `passage_lucr_drn_301325` | Titus Lucretius Carus, De Rerum Natura, 1.301-325 | 1,092 |
| `passage_lucr_drn_301325_s106` | Titus Lucretius Carus, De Rerum Natura, 3.301-325 | 1,090 |
| `passage_lucr_drn_301325_s150` | Titus Lucretius Carus, De Rerum Natura, 4.301-325 | 1,159 |
| `passage_lucr_drn_301325_s202` | Titus Lucretius Carus, De Rerum Natura, 5.301-325 | 1,086 |
| `passage_lucr_drn_301325_s261` | Titus Lucretius Carus, De Rerum Natura, 6.301-325 | 1,118 |
| `passage_lucr_drn_325349` | Titus Lucretius Carus, De Rerum Natura, 2.325-349 | 1,114 |
| `passage_lucr_drn_326350` | Titus Lucretius Carus, De Rerum Natura, 1.326-350 | 1,125 |
| `passage_lucr_drn_326350_s107` | Titus Lucretius Carus, De Rerum Natura, 3.326-350 | 1,118 |
| `passage_lucr_drn_326350_s151` | Titus Lucretius Carus, De Rerum Natura, 4.326-350 | 1,106 |
| `passage_lucr_drn_326350_s203` | Titus Lucretius Carus, De Rerum Natura, 5.326-350 | 1,117 |
| `passage_lucr_drn_326350_s262` | Titus Lucretius Carus, De Rerum Natura, 6.326-350 | 1,138 |
| `passage_lucr_drn_350374` | Titus Lucretius Carus, De Rerum Natura, 2.350-374 | 1,101 |
| `passage_lucr_drn_351375` | Titus Lucretius Carus, De Rerum Natura, 1.351-375 | 1,124 |
| `passage_lucr_drn_351375_s108` | Titus Lucretius Carus, De Rerum Natura, 3.351-375 | 1,146 |
| `passage_lucr_drn_351375_s152` | Titus Lucretius Carus, De Rerum Natura, 4.351-375 | 1,112 |
| `passage_lucr_drn_351375_s204` | Titus Lucretius Carus, De Rerum Natura, 5.351-375 | 1,128 |
| `passage_lucr_drn_351375_s263` | Titus Lucretius Carus, De Rerum Natura, 6.351-375 | 1,129 |
| `passage_lucr_drn_375399` | Titus Lucretius Carus, De Rerum Natura, 2.375-399 | 1,102 |
| `passage_lucr_drn_376400` | Titus Lucretius Carus, De Rerum Natura, 1.376-400 | 1,112 |
| `passage_lucr_drn_376400_s109` | Titus Lucretius Carus, De Rerum Natura, 3.376-400 | 1,115 |
| `passage_lucr_drn_376400_s153` | Titus Lucretius Carus, De Rerum Natura, 4.376-400 | 1,116 |
| `passage_lucr_drn_376400_s205` | Titus Lucretius Carus, De Rerum Natura, 5.376-400 | 1,086 |
| `passage_lucr_drn_376400_s264` | Titus Lucretius Carus, De Rerum Natura, 6.376-400 | 1,114 |
| `passage_lucr_drn_400424` | Titus Lucretius Carus, De Rerum Natura, 2.400-424 | 1,100 |
| `passage_lucr_drn_401425` | Titus Lucretius Carus, De Rerum Natura, 1.401-425 | 1,086 |
| `passage_lucr_drn_401425_s110` | Titus Lucretius Carus, De Rerum Natura, 3.401-425 | 1,113 |
| `passage_lucr_drn_401425_s154` | Titus Lucretius Carus, De Rerum Natura, 4.401-425 | 1,104 |
| `passage_lucr_drn_401425_s206` | Titus Lucretius Carus, De Rerum Natura, 5.401-425 | 1,087 |
| `passage_lucr_drn_401425_s265` | Titus Lucretius Carus, De Rerum Natura, 6.401-425 | 1,126 |
| `passage_lucr_drn_425449` | Titus Lucretius Carus, De Rerum Natura, 2.425-449 | 1,103 |
| `passage_lucr_drn_426450` | Titus Lucretius Carus, De Rerum Natura, 1.426-450 | 1,159 |
| `passage_lucr_drn_426450_s111` | Titus Lucretius Carus, De Rerum Natura, 3.426-450 | 1,140 |
| `passage_lucr_drn_426450_s155` | Titus Lucretius Carus, De Rerum Natura, 4.426-450 | 1,102 |
| `passage_lucr_drn_426450_s207` | Titus Lucretius Carus, De Rerum Natura, 5.426-450 | 1,081 |
| `passage_lucr_drn_426450_s266` | Titus Lucretius Carus, De Rerum Natura, 6.426-450 | 1,124 |
| `passage_lucr_drn_450473` | Titus Lucretius Carus, De Rerum Natura, 2.450-473 | 1,123 |
| `passage_lucr_drn_451475` | Titus Lucretius Carus, De Rerum Natura, 1.451-475 | 1,118 |
| `passage_lucr_drn_451475_s112` | Titus Lucretius Carus, De Rerum Natura, 3.451-475 | 1,108 |
| `passage_lucr_drn_451475_s156` | Titus Lucretius Carus, De Rerum Natura, 4.451-475 | 1,127 |
| `passage_lucr_drn_451475_s208` | Titus Lucretius Carus, De Rerum Natura, 5.451-475 | 1,106 |
| `passage_lucr_drn_451475_s267` | Titus Lucretius Carus, De Rerum Natura, 6.451-475 | 1,083 |
| `passage_lucr_drn_474498` | Titus Lucretius Carus, De Rerum Natura, 2.474-498 | 1,072 |
| `passage_lucr_drn_476500` | Titus Lucretius Carus, De Rerum Natura, 1.476-500 | 1,113 |
| `passage_lucr_drn_476500_s113` | Titus Lucretius Carus, De Rerum Natura, 3.476-500 | 1,120 |
| `passage_lucr_drn_476500_s157` | Titus Lucretius Carus, De Rerum Natura, 4.476-500 | 1,133 |
| `passage_lucr_drn_476500_s209` | Titus Lucretius Carus, De Rerum Natura, 5.476-500 | 1,121 |
| `passage_lucr_drn_476500_s268` | Titus Lucretius Carus, De Rerum Natura, 6.476-500 | 1,133 |
| `passage_lucr_drn_499523` | Titus Lucretius Carus, De Rerum Natura, 2.499-523 | 1,098 |
| `passage_lucr_drn_501525` | Titus Lucretius Carus, De Rerum Natura, 1.501-525 | 1,121 |
| `passage_lucr_drn_501525_s114` | Titus Lucretius Carus, De Rerum Natura, 3.501-525 | 1,109 |
| `passage_lucr_drn_501525_s158` | Titus Lucretius Carus, De Rerum Natura, 4.501-525 | 1,150 |
| `passage_lucr_drn_501525_s210` | Titus Lucretius Carus, De Rerum Natura, 5.501-525 | 1,141 |
| `passage_lucr_drn_501525_s269` | Titus Lucretius Carus, De Rerum Natura, 6.501-525 | 1,106 |
| `passage_lucr_drn_5175` | Titus Lucretius Carus, De Rerum Natura, 1.51-75 | 1,087 |
| `passage_lucr_drn_5175_s140` | Titus Lucretius Carus, De Rerum Natura, 4.51-75 | 1,097 |
| `passage_lucr_drn_5175_s192` | Titus Lucretius Carus, De Rerum Natura, 5.51-75 | 1,087 |
| `passage_lucr_drn_5175_s251` | Titus Lucretius Carus, De Rerum Natura, 6.51-75 | 1,089 |
| `passage_lucr_drn_5175_s48` | Titus Lucretius Carus, De Rerum Natura, 2.51-75 | 1,123 |
| `passage_lucr_drn_5175_s96` | Titus Lucretius Carus, De Rerum Natura, 3.51-75 | 1,083 |
| `passage_lucr_drn_524547` | Titus Lucretius Carus, De Rerum Natura, 2.524-547 | 1,039 |
| `passage_lucr_drn_526550` | Titus Lucretius Carus, De Rerum Natura, 1.526-550 | 1,106 |
| `passage_lucr_drn_526550_s115` | Titus Lucretius Carus, De Rerum Natura, 3.526-550 | 1,121 |
| `passage_lucr_drn_526550_s159` | Titus Lucretius Carus, De Rerum Natura, 4.526-550 | 1,093 |
| `passage_lucr_drn_526550_s211` | Titus Lucretius Carus, De Rerum Natura, 5.526-550 | 1,138 |
| `passage_lucr_drn_526550_s270` | Titus Lucretius Carus, De Rerum Natura, 6.526-550 | 1,114 |
| `passage_lucr_drn_548572` | Titus Lucretius Carus, De Rerum Natura, 2.548-572 | 1,088 |
| `passage_lucr_drn_551575` | Titus Lucretius Carus, De Rerum Natura, 1.551-575 | 1,060 |
| `passage_lucr_drn_551575_s116` | Titus Lucretius Carus, De Rerum Natura, 3.551-575 | 1,136 |
| `passage_lucr_drn_551575_s160` | Titus Lucretius Carus, De Rerum Natura, 4.551-575 | 1,103 |
| `passage_lucr_drn_551575_s212` | Titus Lucretius Carus, De Rerum Natura, 5.551-575 | 1,155 |
| `passage_lucr_drn_551575_s271` | Titus Lucretius Carus, De Rerum Natura, 6.551-575 | 1,107 |
| `passage_lucr_drn_573597` | Titus Lucretius Carus, De Rerum Natura, 2.573-597 | 1,089 |
| `passage_lucr_drn_576600` | Titus Lucretius Carus, De Rerum Natura, 1.576-600 | 1,106 |
| `passage_lucr_drn_576600_s117` | Titus Lucretius Carus, De Rerum Natura, 3.576-600 | 1,112 |
| `passage_lucr_drn_576600_s161` | Titus Lucretius Carus, De Rerum Natura, 4.576-600 | 1,119 |
| `passage_lucr_drn_576600_s213` | Titus Lucretius Carus, De Rerum Natura, 5.576-600 | 1,137 |
| `passage_lucr_drn_576600_s272` | Titus Lucretius Carus, De Rerum Natura, 6.576-600 | 1,087 |
| `passage_lucr_drn_598622` | Titus Lucretius Carus, De Rerum Natura, 2.598-622 | 1,079 |
| `passage_lucr_drn_601625` | Titus Lucretius Carus, De Rerum Natura, 1.601-625 | 1,111 |
| `passage_lucr_drn_601625_s118` | Titus Lucretius Carus, De Rerum Natura, 3.601-625 | 1,138 |
| `passage_lucr_drn_601625_s162` | Titus Lucretius Carus, De Rerum Natura, 4.601-625 | 1,135 |
| `passage_lucr_drn_601625_s214` | Titus Lucretius Carus, De Rerum Natura, 5.601-625 | 1,095 |
| `passage_lucr_drn_601625_s273` | Titus Lucretius Carus, De Rerum Natura, 6.601-625 | 1,085 |
| `passage_lucr_drn_623647` | Titus Lucretius Carus, De Rerum Natura, 2.623-647 | 1,070 |
| `passage_lucr_drn_626650` | Titus Lucretius Carus, De Rerum Natura, 1.626-650 | 1,108 |
| `passage_lucr_drn_626650_s119` | Titus Lucretius Carus, De Rerum Natura, 3.626-650 | 1,133 |
| `passage_lucr_drn_626650_s163` | Titus Lucretius Carus, De Rerum Natura, 4.626-650 | 1,134 |
| `passage_lucr_drn_626650_s215` | Titus Lucretius Carus, De Rerum Natura, 5.626-650 | 1,102 |
| `passage_lucr_drn_626650_s274` | Titus Lucretius Carus, De Rerum Natura, 6.626-650 | 1,069 |
| `passage_lucr_drn_648671` | Titus Lucretius Carus, De Rerum Natura, 2.648-671 | 1,090 |
| `passage_lucr_drn_651675` | Titus Lucretius Carus, De Rerum Natura, 1.651-675 | 1,096 |
| `passage_lucr_drn_651675_s120` | Titus Lucretius Carus, De Rerum Natura, 3.651-675 | 1,108 |
| `passage_lucr_drn_651675_s164` | Titus Lucretius Carus, De Rerum Natura, 4.651-675 | 1,141 |
| `passage_lucr_drn_651675_s216` | Titus Lucretius Carus, De Rerum Natura, 5.651-675 | 1,096 |
| `passage_lucr_drn_651675_s275` | Titus Lucretius Carus, De Rerum Natura, 6.651-675 | 1,099 |
| `passage_lucr_drn_672697` | Titus Lucretius Carus, De Rerum Natura, 2.672-697 | 1,118 |
| `passage_lucr_drn_676700` | Titus Lucretius Carus, De Rerum Natura, 1.676-700 | 1,124 |
| `passage_lucr_drn_676700_s121` | Titus Lucretius Carus, De Rerum Natura, 3.676-700 | 1,133 |
| `passage_lucr_drn_676700_s165` | Titus Lucretius Carus, De Rerum Natura, 4.676-700 | 1,130 |
| `passage_lucr_drn_676700_s217` | Titus Lucretius Carus, De Rerum Natura, 5.676-700 | 1,100 |
| `passage_lucr_drn_676700_s276` | Titus Lucretius Carus, De Rerum Natura, 6.676-700 | 1,118 |
| `passage_lucr_drn_698722` | Titus Lucretius Carus, De Rerum Natura, 2.698-722 | 1,077 |
| `passage_lucr_drn_701725` | Titus Lucretius Carus, De Rerum Natura, 1.701-725 | 1,093 |
| `passage_lucr_drn_701725_s122` | Titus Lucretius Carus, De Rerum Natura, 3.701-725 | 1,115 |
| `passage_lucr_drn_701725_s166` | Titus Lucretius Carus, De Rerum Natura, 4.701-725 | 1,123 |
| `passage_lucr_drn_701725_s218` | Titus Lucretius Carus, De Rerum Natura, 5.701-725 | 1,094 |
| `passage_lucr_drn_701725_s277` | Titus Lucretius Carus, De Rerum Natura, 6.701-725 | 1,128 |
| `passage_lucr_drn_723747` | Titus Lucretius Carus, De Rerum Natura, 2.723-747 | 1,103 |
| `passage_lucr_drn_726750` | Titus Lucretius Carus, De Rerum Natura, 1.726-750 | 1,083 |
| `passage_lucr_drn_726750_s123` | Titus Lucretius Carus, De Rerum Natura, 3.726-750 | 1,133 |
| `passage_lucr_drn_726750_s167` | Titus Lucretius Carus, De Rerum Natura, 4.726-750 | 1,142 |
| `passage_lucr_drn_726750_s219` | Titus Lucretius Carus, De Rerum Natura, 5.726-750 | 1,115 |
| `passage_lucr_drn_726750_s278` | Titus Lucretius Carus, De Rerum Natura, 6.726-750 | 1,129 |
| `passage_lucr_drn_748772` | Titus Lucretius Carus, De Rerum Natura, 2.748-772 | 1,107 |
| `passage_lucr_drn_751775` | Titus Lucretius Carus, De Rerum Natura, 1.751-775 | 1,117 |
| `passage_lucr_drn_751775_s124` | Titus Lucretius Carus, De Rerum Natura, 3.751-775 | 1,131 |
| `passage_lucr_drn_751775_s168` | Titus Lucretius Carus, De Rerum Natura, 4.751-775 | 1,143 |
| `passage_lucr_drn_751775_s220` | Titus Lucretius Carus, De Rerum Natura, 5.751-775 | 1,102 |
| `passage_lucr_drn_751775_s279` | Titus Lucretius Carus, De Rerum Natura, 6.751-775 | 1,089 |
| `passage_lucr_drn_76100` | Titus Lucretius Carus, De Rerum Natura, 1.76-100 | 1,072 |
| `passage_lucr_drn_76100_s141` | Titus Lucretius Carus, De Rerum Natura, 4.76-100 | 1,098 |
| `passage_lucr_drn_76100_s193` | Titus Lucretius Carus, De Rerum Natura, 5.76-100 | 1,111 |
| `passage_lucr_drn_76100_s252` | Titus Lucretius Carus, De Rerum Natura, 6.76-100 | 1,107 |
| `passage_lucr_drn_76100_s49` | Titus Lucretius Carus, De Rerum Natura, 2.76-100 | 1,099 |
| `passage_lucr_drn_76100_s97` | Titus Lucretius Carus, De Rerum Natura, 3.76-100 | 1,130 |
| `passage_lucr_drn_773797` | Titus Lucretius Carus, De Rerum Natura, 2.773-797 | 1,113 |
| `passage_lucr_drn_776800` | Titus Lucretius Carus, De Rerum Natura, 1.776-800 | 1,093 |
| `passage_lucr_drn_776800_s125` | Titus Lucretius Carus, De Rerum Natura, 3.776-800 | 1,150 |
| `passage_lucr_drn_776800_s169` | Titus Lucretius Carus, De Rerum Natura, 4.776-800 | 1,126 |
| `passage_lucr_drn_776800_s221` | Titus Lucretius Carus, De Rerum Natura, 5.776-800 | 1,107 |
| `passage_lucr_drn_776800_s280` | Titus Lucretius Carus, De Rerum Natura, 6.776-800 | 1,112 |
| `passage_lucr_drn_798822` | Titus Lucretius Carus, De Rerum Natura, 2.798-822 | 1,105 |
| `passage_lucr_drn_801825` | Titus Lucretius Carus, De Rerum Natura, 1.801-825 | 1,103 |
| `passage_lucr_drn_801825_s126` | Titus Lucretius Carus, De Rerum Natura, 3.801-825 | 1,137 |
| `passage_lucr_drn_801825_s170` | Titus Lucretius Carus, De Rerum Natura, 4.801-825 | 1,145 |
| `passage_lucr_drn_801825_s222` | Titus Lucretius Carus, De Rerum Natura, 5.801-825 | 1,116 |
| `passage_lucr_drn_801825_s281` | Titus Lucretius Carus, De Rerum Natura, 6.801-825 | 1,109 |
| `passage_lucr_drn_823847` | Titus Lucretius Carus, De Rerum Natura, 2.823-847 | 1,106 |
| `passage_lucr_drn_826850` | Titus Lucretius Carus, De Rerum Natura, 1.826-850 | 1,099 |
| `passage_lucr_drn_826850_s127` | Titus Lucretius Carus, De Rerum Natura, 3.826-850 | 1,145 |
| `passage_lucr_drn_826850_s171` | Titus Lucretius Carus, De Rerum Natura, 4.826-850 | 1,099 |
| `passage_lucr_drn_826850_s223` | Titus Lucretius Carus, De Rerum Natura, 5.826-850 | 1,121 |
| `passage_lucr_drn_826850_s282` | Titus Lucretius Carus, De Rerum Natura, 6.826-850 | 1,138 |
| `passage_lucr_drn_848872` | Titus Lucretius Carus, De Rerum Natura, 2.848-872 | 1,135 |
| `passage_lucr_drn_851874` | Titus Lucretius Carus, De Rerum Natura, 1.851-874 | 1,079 |
| `passage_lucr_drn_851875` | Titus Lucretius Carus, De Rerum Natura, 3.851-875 | 1,149 |
| `passage_lucr_drn_851875_s172` | Titus Lucretius Carus, De Rerum Natura, 4.851-875 | 1,139 |
| `passage_lucr_drn_851875_s224` | Titus Lucretius Carus, De Rerum Natura, 5.851-875 | 1,108 |
| `passage_lucr_drn_851875_s283` | Titus Lucretius Carus, De Rerum Natura, 6.851-875 | 1,109 |
| `passage_lucr_drn_873897` | Titus Lucretius Carus, De Rerum Natura, 2.873-897 | 1,115 |
| `passage_lucr_drn_875899` | Titus Lucretius Carus, De Rerum Natura, 1.875-899 | 1,121 |
| `passage_lucr_drn_876900` | Titus Lucretius Carus, De Rerum Natura, 3.876-900 | 1,114 |
| `passage_lucr_drn_876900_s173` | Titus Lucretius Carus, De Rerum Natura, 4.876-900 | 1,146 |
| `passage_lucr_drn_876900_s225` | Titus Lucretius Carus, De Rerum Natura, 5.876-900 | 1,117 |
| `passage_lucr_drn_876900_s284` | Titus Lucretius Carus, De Rerum Natura, 6.876-900 | 1,136 |
| `passage_lucr_drn_898921` | Titus Lucretius Carus, De Rerum Natura, 2.898-921 | 1,067 |
| `passage_lucr_drn_900924` | Titus Lucretius Carus, De Rerum Natura, 1.900-924 | 1,088 |
| `passage_lucr_drn_901925` | Titus Lucretius Carus, De Rerum Natura, 3.901-925 | 1,148 |
| `passage_lucr_drn_901925_s174` | Titus Lucretius Carus, De Rerum Natura, 4.901-925 | 1,119 |
| `passage_lucr_drn_901925_s226` | Titus Lucretius Carus, De Rerum Natura, 5.901-925 | 1,113 |
| `passage_lucr_drn_901925_s285` | Titus Lucretius Carus, De Rerum Natura, 6.901-925 | 1,120 |
| `passage_lucr_drn_922946` | Titus Lucretius Carus, De Rerum Natura, 2.922-946 | 1,098 |
| `passage_lucr_drn_925949` | Titus Lucretius Carus, De Rerum Natura, 1.925-949 | 1,081 |
| `passage_lucr_drn_926950` | Titus Lucretius Carus, De Rerum Natura, 3.926-950 | 1,150 |
| `passage_lucr_drn_926950_s175` | Titus Lucretius Carus, De Rerum Natura, 4.926-950 | 1,112 |
| `passage_lucr_drn_926950_s227` | Titus Lucretius Carus, De Rerum Natura, 5.926-950 | 1,089 |
| `passage_lucr_drn_926950_s286` | Titus Lucretius Carus, De Rerum Natura, 6.926-950 | 1,138 |
| `passage_lucr_drn_947971` | Titus Lucretius Carus, De Rerum Natura, 2.947-971 | 1,087 |
| `passage_lucr_drn_950974` | Titus Lucretius Carus, De Rerum Natura, 1.950-974 | 1,096 |
| `passage_lucr_drn_951975` | Titus Lucretius Carus, De Rerum Natura, 3.951-975 | 1,146 |
| `passage_lucr_drn_951975_s176` | Titus Lucretius Carus, De Rerum Natura, 4.951-975 | 1,123 |
| `passage_lucr_drn_951975_s228` | Titus Lucretius Carus, De Rerum Natura, 5.951-975 | 1,102 |
| `passage_lucr_drn_951975_s287` | Titus Lucretius Carus, De Rerum Natura, 6.951-975 | 1,146 |
| `passage_lucr_drn_972996` | Titus Lucretius Carus, De Rerum Natura, 2.972-996 | 1,143 |
| `passage_lucr_drn_975999` | Titus Lucretius Carus, De Rerum Natura, 1.975-999 | 1,080 |
| `passage_lucr_drn_9761000` | Titus Lucretius Carus, De Rerum Natura, 3.976-1000 | 1,131 |
| `passage_lucr_drn_9761000_s177` | Titus Lucretius Carus, De Rerum Natura, 4.976-1000 | 1,094 |
| `passage_lucr_drn_9761000_s229` | Titus Lucretius Carus, De Rerum Natura, 5.976-1000 | 1,062 |
| `passage_lucr_drn_9761000_s288` | Titus Lucretius Carus, De Rerum Natura, 6.976-1000 | 1,104 |
| `passage_lucr_drn_9971021` | Titus Lucretius Carus, De Rerum Natura, 2.997-1021 | 1,079 |

### Plato — Φαῖδρος

- **Language:** Greek
- **Passages:** 261
- **Characters:** 101,653
- **Canonical ID:** `urn:cts:greekLit:tlg0059.tlg012`

| node_id | label | chars |
|---------|-------|-------|
| `passage_plato_phdr_227a` | Plato, Φαῖδρος, 227a | 298 |
| `passage_plato_phdr_227b` | Plato, Φαῖδρος, 227b | 390 |
| `passage_plato_phdr_227c` | Plato, Φαῖδρος, 227c | 414 |
| `passage_plato_phdr_227d` | Plato, Φαῖδρος, 227d | 287 |
| `passage_plato_phdr_228a` | Plato, Φαῖδρος, 228a | 415 |
| `passage_plato_phdr_228b` | Plato, Φαῖδρος, 228b | 380 |
| `passage_plato_phdr_228c` | Plato, Φαῖδρος, 228c | 388 |
| `passage_plato_phdr_228d` | Plato, Φαῖδρος, 228d | 398 |
| `passage_plato_phdr_228e` | Plato, Φαῖδρος, 228e | 237 |
| `passage_plato_phdr_229a` | Plato, Φαῖδρος, 229a | 395 |
| `passage_plato_phdr_229b` | Plato, Φαῖδρος, 229b | 351 |
| `passage_plato_phdr_229c` | Plato, Φαῖδρος, 229c | 429 |
| `passage_plato_phdr_229d` | Plato, Φαῖδρος, 229d | 388 |
| `passage_plato_phdr_229e` | Plato, Φαῖδρος, 229e | 327 |
| `passage_plato_phdr_230a` | Plato, Φαῖδρος, 230a | 395 |
| `passage_plato_phdr_230b` | Plato, Φαῖδρος, 230b | 398 |
| `passage_plato_phdr_230c` | Plato, Φαῖδρος, 230c | 377 |
| `passage_plato_phdr_230d` | Plato, Φαῖδρος, 230d | 434 |
| `passage_plato_phdr_230e` | Plato, Φαῖδρος, 230e | 335 |
| `passage_plato_phdr_231a` | Plato, Φαῖδρος, 231a | 438 |
| `passage_plato_phdr_231b` | Plato, Φαῖδρος, 231b | 381 |
| `passage_plato_phdr_231c` | Plato, Φαῖδρος, 231c | 403 |
| `passage_plato_phdr_231d` | Plato, Φαῖδρος, 231d | 444 |
| `passage_plato_phdr_231e` | Plato, Φαῖδρος, 231e | 175 |
| `passage_plato_phdr_232a` | Plato, Φαῖδρος, 232a | 437 |
| `passage_plato_phdr_232b` | Plato, Φαῖδρος, 232b | 383 |
| `passage_plato_phdr_232c` | Plato, Φαῖδρος, 232c | 430 |
| `passage_plato_phdr_232d` | Plato, Φαῖδρος, 232d | 391 |
| `passage_plato_phdr_232e` | Plato, Φαῖδρος, 232e | 284 |
| `passage_plato_phdr_233a` | Plato, Φαῖδρος, 233a | 382 |
| `passage_plato_phdr_233b` | Plato, Φαῖδρος, 233b | 384 |
| `passage_plato_phdr_233c` | Plato, Φαῖδρος, 233c | 389 |
| `passage_plato_phdr_233d` | Plato, Φαῖδρος, 233d | 415 |
| `passage_plato_phdr_233e` | Plato, Φαῖδρος, 233e | 392 |
| `passage_plato_phdr_234a` | Plato, Φαῖδρος, 234a | 440 |
| `passage_plato_phdr_234b` | Plato, Φαῖδρος, 234b | 414 |
| `passage_plato_phdr_234c` | Plato, Φαῖδρος, 234c | 364 |
| `passage_plato_phdr_234d` | Plato, Φαῖδρος, 234d | 376 |
| `passage_plato_phdr_234e` | Plato, Φαῖδρος, 234e | 428 |
| `passage_plato_phdr_235a` | Plato, Φαῖδρος, 235a | 410 |
| `passage_plato_phdr_235b` | Plato, Φαῖδρος, 235b | 402 |
| `passage_plato_phdr_235c` | Plato, Φαῖδρος, 235c | 428 |
| `passage_plato_phdr_235d` | Plato, Φαῖδρος, 235d | 449 |
| `passage_plato_phdr_235e` | Plato, Φαῖδρος, 235e | 355 |
| `passage_plato_phdr_236a` | Plato, Φαῖδρος, 236a | 371 |
| `passage_plato_phdr_236b` | Plato, Φαῖδρος, 236b | 386 |
| `passage_plato_phdr_236c` | Plato, Φαῖδρος, 236c | 419 |
| `passage_plato_phdr_236d` | Plato, Φαῖδρος, 236d | 449 |
| `passage_plato_phdr_236e` | Plato, Φαῖδρος, 236e | 356 |
| `passage_plato_phdr_237a` | Plato, Φαῖδρος, 237a | 421 |
| `passage_plato_phdr_237b` | Plato, Φαῖδρος, 237b | 367 |
| `passage_plato_phdr_237c` | Plato, Φαῖδρος, 237c | 448 |
| `passage_plato_phdr_237d` | Plato, Φαῖδρος, 237d | 475 |
| `passage_plato_phdr_237e` | Plato, Φαῖδρος, 237e | 159 |
| `passage_plato_phdr_238a` | Plato, Φαῖδρος, 238a | 369 |
| `passage_plato_phdr_238b` | Plato, Φαῖδρος, 238b | 435 |
| `passage_plato_phdr_238c` | Plato, Φαῖδρος, 238c | 368 |
| `passage_plato_phdr_238d` | Plato, Φαῖδρος, 238d | 424 |
| `passage_plato_phdr_238e` | Plato, Φαῖδρος, 238e | 266 |
| `passage_plato_phdr_239a` | Plato, Φαῖδρος, 239a | 366 |
| `passage_plato_phdr_239b` | Plato, Φαῖδρος, 239b | 433 |
| `passage_plato_phdr_239c` | Plato, Φαῖδρος, 239c | 401 |
| `passage_plato_phdr_239d` | Plato, Φαῖδρος, 239d | 389 |
| `passage_plato_phdr_239e` | Plato, Φαῖδρος, 239e | 334 |
| `passage_plato_phdr_240a` | Plato, Φαῖδρος, 240a | 474 |
| `passage_plato_phdr_240b` | Plato, Φαῖδρος, 240b | 345 |
| `passage_plato_phdr_240c` | Plato, Φαῖδρος, 240c | 386 |
| `passage_plato_phdr_240d` | Plato, Φαῖδρος, 240d | 392 |
| `passage_plato_phdr_240e` | Plato, Φαῖδρος, 240e | 504 |
| `passage_plato_phdr_241a` | Plato, Φαῖδρος, 241a | 452 |
| `passage_plato_phdr_241b` | Plato, Φαῖδρος, 241b | 384 |
| `passage_plato_phdr_241c` | Plato, Φαῖδρος, 241c | 440 |
| `passage_plato_phdr_241d` | Plato, Φαῖδρος, 241d | 316 |
| `passage_plato_phdr_241e` | Plato, Φαῖδρος, 241e | 436 |
| `passage_plato_phdr_242a` | Plato, Φαῖδρος, 242a | 405 |
| `passage_plato_phdr_242b` | Plato, Φαῖδρος, 242b | 395 |
| `passage_plato_phdr_242c` | Plato, Φαῖδρος, 242c | 445 |
| `passage_plato_phdr_242d` | Plato, Φαῖδρος, 242d | 418 |
| `passage_plato_phdr_242e` | Plato, Φαῖδρος, 242e | 292 |
| `passage_plato_phdr_243a` | Plato, Φαῖδρος, 243a | 435 |
| `passage_plato_phdr_243b` | Plato, Φαῖδρος, 243b | 392 |
| `passage_plato_phdr_243c` | Plato, Φαῖδρος, 243c | 448 |
| `passage_plato_phdr_243d` | Plato, Φαῖδρος, 243d | 398 |
| `passage_plato_phdr_243e` | Plato, Φαῖδρος, 243e | 334 |
| `passage_plato_phdr_244a` | Plato, Φαῖδρος, 244a | 448 |
| `passage_plato_phdr_244b` | Plato, Φαῖδρος, 244b | 392 |
| `passage_plato_phdr_244c` | Plato, Φαῖδρος, 244c | 425 |
| `passage_plato_phdr_244d` | Plato, Φαῖδρος, 244d | 387 |
| `passage_plato_phdr_244e` | Plato, Φαῖδρος, 244e | 220 |
| `passage_plato_phdr_245a` | Plato, Φαῖδρος, 245a | 429 |
| `passage_plato_phdr_245b` | Plato, Φαῖδρος, 245b | 395 |
| `passage_plato_phdr_245c` | Plato, Φαῖδρος, 245c | 488 |
| `passage_plato_phdr_245d` | Plato, Φαῖδρος, 245d | 436 |
| `passage_plato_phdr_245e` | Plato, Φαῖδρος, 245e | 384 |
| `passage_plato_phdr_246a` | Plato, Φαῖδρος, 246a | 394 |
| `passage_plato_phdr_246b` | Plato, Φαῖδρος, 246b | 400 |
| `passage_plato_phdr_246c` | Plato, Φαῖδρος, 246c | 388 |
| `passage_plato_phdr_246d` | Plato, Φαῖδρος, 246d | 404 |
| `passage_plato_phdr_246e` | Plato, Φαῖδρος, 246e | 333 |
| `passage_plato_phdr_247a` | Plato, Φαῖδρος, 247a | 439 |
| `passage_plato_phdr_247b` | Plato, Φαῖδρος, 247b | 388 |
| `passage_plato_phdr_247c` | Plato, Φαῖδρος, 247c | 403 |
| `passage_plato_phdr_247d` | Plato, Φαῖδρος, 247d | 380 |
| `passage_plato_phdr_247e` | Plato, Φαῖδρος, 247e | 315 |
| `passage_plato_phdr_248a` | Plato, Φαῖδρος, 248a | 445 |
| `passage_plato_phdr_248b` | Plato, Φαῖδρος, 248b | 381 |
| `passage_plato_phdr_248c` | Plato, Φαῖδρος, 248c | 432 |
| `passage_plato_phdr_248d` | Plato, Φαῖδρος, 248d | 386 |
| `passage_plato_phdr_248e` | Plato, Φαῖδρος, 248e | 343 |
| `passage_plato_phdr_249a` | Plato, Φαῖδρος, 249a | 446 |
| `passage_plato_phdr_249b` | Plato, Φαῖδρος, 249b | 382 |
| `passage_plato_phdr_249c` | Plato, Φαῖδρος, 249c | 440 |
| `passage_plato_phdr_249d` | Plato, Φαῖδρος, 249d | 411 |
| `passage_plato_phdr_249e` | Plato, Φαῖδρος, 249e | 260 |
| `passage_plato_phdr_250a` | Plato, Φαῖδρος, 250a | 392 |
| `passage_plato_phdr_250b` | Plato, Φαῖδρος, 250b | 436 |
| `passage_plato_phdr_250c` | Plato, Φαῖδρος, 250c | 417 |
| `passage_plato_phdr_250d` | Plato, Φαῖδρος, 250d | 390 |
| `passage_plato_phdr_250e` | Plato, Φαῖδρος, 250e | 279 |
| `passage_plato_phdr_251a` | Plato, Φαῖδρος, 251a | 378 |
| `passage_plato_phdr_251b` | Plato, Φαῖδρος, 251b | 379 |
| `passage_plato_phdr_251c` | Plato, Φαῖδρος, 251c | 443 |
| `passage_plato_phdr_251d` | Plato, Φαῖδρος, 251d | 438 |
| `passage_plato_phdr_251e` | Plato, Φαῖδρος, 251e | 283 |
| `passage_plato_phdr_252a` | Plato, Φαῖδρος, 252a | 392 |
| `passage_plato_phdr_252b` | Plato, Φαῖδρος, 252b | 336 |
| `passage_plato_phdr_252c` | Plato, Φαῖδρος, 252c | 490 |
| `passage_plato_phdr_252d` | Plato, Φαῖδρος, 252d | 385 |
| `passage_plato_phdr_252e` | Plato, Φαῖδρος, 252e | 390 |
| `passage_plato_phdr_253a` | Plato, Φαῖδρος, 253a | 382 |
| `passage_plato_phdr_253b` | Plato, Φαῖδρος, 253b | 452 |
| `passage_plato_phdr_253c` | Plato, Φαῖδρος, 253c | 429 |
| `passage_plato_phdr_253d` | Plato, Φαῖδρος, 253d | 387 |
| `passage_plato_phdr_253e` | Plato, Φαῖδρος, 253e | 340 |
| `passage_plato_phdr_254a` | Plato, Φαῖδρος, 254a | 378 |
| `passage_plato_phdr_254b` | Plato, Φαῖδρος, 254b | 434 |
| `passage_plato_phdr_254c` | Plato, Φαῖδρος, 254c | 431 |
| `passage_plato_phdr_254d` | Plato, Φαῖδρος, 254d | 379 |
| `passage_plato_phdr_254e` | Plato, Φαῖδρος, 254e | 496 |
| `passage_plato_phdr_255a` | Plato, Φαῖδρος, 255a | 371 |
| `passage_plato_phdr_255b` | Plato, Φαῖδρος, 255b | 439 |
| `passage_plato_phdr_255c` | Plato, Φαῖδρος, 255c | 376 |
| `passage_plato_phdr_255d` | Plato, Φαῖδρος, 255d | 420 |
| `passage_plato_phdr_255e` | Plato, Φαῖδρος, 255e | 341 |
| `passage_plato_phdr_256a` | Plato, Φαῖδρος, 256a | 438 |
| `passage_plato_phdr_256b` | Plato, Φαῖδρος, 256b | 380 |
| `passage_plato_phdr_256c` | Plato, Φαῖδρος, 256c | 380 |
| `passage_plato_phdr_256d` | Plato, Φαῖδρος, 256d | 442 |
| `passage_plato_phdr_256e` | Plato, Φαῖδρος, 256e | 296 |
| `passage_plato_phdr_257a` | Plato, Φαῖδρος, 257a | 486 |
| `passage_plato_phdr_257b` | Plato, Φαῖδρος, 257b | 374 |
| `passage_plato_phdr_257c` | Plato, Φαῖδρος, 257c | 430 |
| `passage_plato_phdr_257d` | Plato, Φαῖδρος, 257d | 423 |
| `passage_plato_phdr_257e` | Plato, Φαῖδρος, 257e | 340 |
| `passage_plato_phdr_258a` | Plato, Φαῖδρος, 258a | 409 |
| `passage_plato_phdr_258b` | Plato, Φαῖδρος, 258b | 377 |
| `passage_plato_phdr_258c` | Plato, Φαῖδρος, 258c | 434 |
| `passage_plato_phdr_258d` | Plato, Φαῖδρος, 258d | 432 |
| `passage_plato_phdr_258e` | Plato, Φαῖδρος, 258e | 355 |
| `passage_plato_phdr_259a` | Plato, Φαῖδρος, 259a | 378 |
| `passage_plato_phdr_259b` | Plato, Φαῖδρος, 259b | 366 |
| `passage_plato_phdr_259c` | Plato, Φαῖδρος, 259c | 385 |
| `passage_plato_phdr_259d` | Plato, Φαῖδρος, 259d | 439 |
| `passage_plato_phdr_259e` | Plato, Φαῖδρος, 259e | 307 |
| `passage_plato_phdr_260a` | Plato, Φαῖδρος, 260a | 397 |
| `passage_plato_phdr_260b` | Plato, Φαῖδρος, 260b | 452 |
| `passage_plato_phdr_260c` | Plato, Φαῖδρος, 260c | 428 |
| `passage_plato_phdr_260d` | Plato, Φαῖδρος, 260d | 403 |
| `passage_plato_phdr_260e` | Plato, Φαῖδρος, 260e | 330 |
| `passage_plato_phdr_261a` | Plato, Φαῖδρος, 261a | 439 |
| `passage_plato_phdr_261b` | Plato, Φαῖδρος, 261b | 423 |
| `passage_plato_phdr_261c` | Plato, Φαῖδρος, 261c | 361 |
| `passage_plato_phdr_261d` | Plato, Φαῖδρος, 261d | 399 |
| `passage_plato_phdr_261e` | Plato, Φαῖδρος, 261e | 347 |
| `passage_plato_phdr_262a` | Plato, Φαῖδρος, 262a | 408 |
| `passage_plato_phdr_262b` | Plato, Φαῖδρος, 262b | 360 |
| `passage_plato_phdr_262c` | Plato, Φαῖδρος, 262c | 401 |
| `passage_plato_phdr_262d` | Plato, Φαῖδρος, 262d | 394 |
| `passage_plato_phdr_262e` | Plato, Φαῖδρος, 262e | 277 |
| `passage_plato_phdr_263a` | Plato, Φαῖδρος, 263a | 401 |
| `passage_plato_phdr_263b` | Plato, Φαῖδρος, 263b | 357 |
| `passage_plato_phdr_263c` | Plato, Φαῖδρος, 263c | 461 |
| `passage_plato_phdr_263d` | Plato, Φαῖδρος, 263d | 379 |
| `passage_plato_phdr_263e` | Plato, Φαῖδρος, 263e | 320 |
| `passage_plato_phdr_264a` | Plato, Φαῖδρος, 264a | 393 |
| `passage_plato_phdr_264b` | Plato, Φαῖδρος, 264b | 443 |
| `passage_plato_phdr_264c` | Plato, Φαῖδρος, 264c | 411 |
| `passage_plato_phdr_264d` | Plato, Φαῖδρος, 264d | 244 |
| `passage_plato_phdr_264e` | Plato, Φαῖδρος, 264e | 400 |
| `passage_plato_phdr_265a` | Plato, Φαῖδρος, 265a | 391 |
| `passage_plato_phdr_265b` | Plato, Φαῖδρος, 265b | 398 |
| `passage_plato_phdr_265c` | Plato, Φαῖδρος, 265c | 392 |
| `passage_plato_phdr_265d` | Plato, Φαῖδρος, 265d | 398 |
| `passage_plato_phdr_265e` | Plato, Φαῖδρος, 265e | 221 |
| `passage_plato_phdr_266a` | Plato, Φαῖδρος, 266a | 399 |
| `passage_plato_phdr_266b` | Plato, Φαῖδρος, 266b | 402 |
| `passage_plato_phdr_266c` | Plato, Φαῖδρος, 266c | 448 |
| `passage_plato_phdr_266d` | Plato, Φαῖδρος, 266d | 412 |
| `passage_plato_phdr_266e` | Plato, Φαῖδρος, 266e | 224 |
| `passage_plato_phdr_267a` | Plato, Φαῖδρος, 267a | 432 |
| `passage_plato_phdr_267b` | Plato, Φαῖδρος, 267b | 413 |
| `passage_plato_phdr_267c` | Plato, Φαῖδρος, 267c | 383 |
| `passage_plato_phdr_267d` | Plato, Φαῖδρος, 267d | 421 |
| `passage_plato_phdr_268a` | Plato, Φαῖδρος, 268a | 448 |
| `passage_plato_phdr_268b` | Plato, Φαῖδρος, 268b | 402 |
| `passage_plato_phdr_268c` | Plato, Φαῖδρος, 268c | 424 |
| `passage_plato_phdr_268d` | Plato, Φαῖδρος, 268d | 395 |
| `passage_plato_phdr_268e` | Plato, Φαῖδρος, 268e | 326 |
| `passage_plato_phdr_269a` | Plato, Φαῖδρος, 269a | 384 |
| `passage_plato_phdr_269b` | Plato, Φαῖδρος, 269b | 440 |
| `passage_plato_phdr_269c` | Plato, Φαῖδρος, 269c | 456 |
| `passage_plato_phdr_269d` | Plato, Φαῖδρος, 269d | 411 |
| `passage_plato_phdr_269e` | Plato, Φαῖδρος, 269e | 148 |
| `passage_plato_phdr_270a` | Plato, Φαῖδρος, 270a | 413 |
| `passage_plato_phdr_270b` | Plato, Φαῖδρος, 270b | 398 |
| `passage_plato_phdr_270c` | Plato, Φαῖδρος, 270c | 416 |
| `passage_plato_phdr_270d` | Plato, Φαῖδρος, 270d | 457 |
| `passage_plato_phdr_270e` | Plato, Φαῖδρος, 270e | 240 |
| `passage_plato_phdr_271a` | Plato, Φαῖδρος, 271a | 438 |
| `passage_plato_phdr_271b` | Plato, Φαῖδρος, 271b | 367 |
| `passage_plato_phdr_271c` | Plato, Φαῖδρος, 271c | 423 |
| `passage_plato_phdr_271d` | Plato, Φαῖδρος, 271d | 454 |
| `passage_plato_phdr_271e` | Plato, Φαῖδρος, 271e | 219 |
| `passage_plato_phdr_272a` | Plato, Φαῖδρος, 272a | 432 |
| `passage_plato_phdr_272b` | Plato, Φαῖδρος, 272b | 382 |
| `passage_plato_phdr_272c` | Plato, Φαῖδρος, 272c | 410 |
| `passage_plato_phdr_272d` | Plato, Φαῖδρος, 272d | 416 |
| `passage_plato_phdr_272e` | Plato, Φαῖδρος, 272e | 283 |
| `passage_plato_phdr_273a` | Plato, Φαῖδρος, 273a | 374 |
| `passage_plato_phdr_273b` | Plato, Φαῖδρος, 273b | 388 |
| `passage_plato_phdr_273c` | Plato, Φαῖδρος, 273c | 421 |
| `passage_plato_phdr_273d` | Plato, Φαῖδρος, 273d | 404 |
| `passage_plato_phdr_273e` | Plato, Φαῖδρος, 273e | 486 |
| `passage_plato_phdr_274a` | Plato, Φαῖδρος, 274a | 377 |
| `passage_plato_phdr_274b` | Plato, Φαῖδρος, 274b | 331 |
| `passage_plato_phdr_274c` | Plato, Φαῖδρος, 274c | 408 |
| `passage_plato_phdr_274d` | Plato, Φαῖδρος, 274d | 387 |
| `passage_plato_phdr_274e` | Plato, Φαῖδρος, 274e | 493 |
| `passage_plato_phdr_275a` | Plato, Φαῖδρος, 275a | 385 |
| `passage_plato_phdr_275b` | Plato, Φαῖδρος, 275b | 399 |
| `passage_plato_phdr_275c` | Plato, Φαῖδρος, 275c | 416 |
| `passage_plato_phdr_275d` | Plato, Φαῖδρος, 275d | 404 |
| `passage_plato_phdr_275e` | Plato, Φαῖδρος, 275e | 316 |
| `passage_plato_phdr_276a` | Plato, Φαῖδρος, 276a | 399 |
| `passage_plato_phdr_276b` | Plato, Φαῖδρος, 276b | 412 |
| `passage_plato_phdr_276c` | Plato, Φαῖδρος, 276c | 386 |
| `passage_plato_phdr_276d` | Plato, Φαῖδρος, 276d | 416 |
| `passage_plato_phdr_276e` | Plato, Φαῖδρος, 276e | 360 |
| `passage_plato_phdr_277a` | Plato, Φαῖδρος, 277a | 426 |
| `passage_plato_phdr_277b` | Plato, Φαῖδρος, 277b | 392 |
| `passage_plato_phdr_277c` | Plato, Φαῖδρος, 277c | 372 |
| `passage_plato_phdr_277d` | Plato, Φαῖδρος, 277d | 456 |
| `passage_plato_phdr_277e` | Plato, Φαῖδρος, 277e | 411 |
| `passage_plato_phdr_278a` | Plato, Φαῖδρος, 278a | 393 |
| `passage_plato_phdr_278b` | Plato, Φαῖδρος, 278b | 425 |
| `passage_plato_phdr_278c` | Plato, Φαῖδρος, 278c | 383 |
| `passage_plato_phdr_278d` | Plato, Φαῖδρος, 278d | 394 |
| `passage_plato_phdr_278e` | Plato, Φαῖδρος, 278e | 357 |
| `passage_plato_phdr_279a` | Plato, Φαῖδρος, 279a | 426 |
| `passage_plato_phdr_279b` | Plato, Φαῖδρος, 279b | 369 |
| `passage_plato_phdr_279c` | Plato, Φαῖδρος, 279c | 258 |

### Epicurus — Letters and Fragments

- **Language:** Greek
- **Passages:** 193
- **Characters:** 73,582
- **Canonical ID:** `usener:epicurus`

| node_id | label | chars |
|---------|-------|-------|
| `passage_epicur_1` | Epicurus, Letters and Fragments, SV 1 | 136 |
| `passage_epicur_10` | Epicurus, Letters and Fragments, SV 10 | 179 |
| `passage_epicur_100` | Epicurus, Letters and Fragments, Ep. Pyth. 100 | 536 |
| `passage_epicur_101` | Epicurus, Letters and Fragments, Ep. Pyth. 101 | 762 |
| `passage_epicur_102` | Epicurus, Letters and Fragments, Ep. Pyth. 102 | 547 |
| `passage_epicur_103` | Epicurus, Letters and Fragments, Ep. Pyth. 103 | 677 |
| `passage_epicur_104` | Epicurus, Letters and Fragments, Ep. Pyth. 104 | 559 |
| `passage_epicur_105` | Epicurus, Letters and Fragments, Ep. Pyth. 105 | 666 |
| `passage_epicur_106` | Epicurus, Letters and Fragments, Ep. Pyth. 106 | 590 |
| `passage_epicur_107` | Epicurus, Letters and Fragments, Ep. Pyth. 107 | 688 |
| `passage_epicur_108` | Epicurus, Letters and Fragments, Ep. Pyth. 108 | 559 |
| `passage_epicur_109` | Epicurus, Letters and Fragments, Ep. Pyth. 109 | 703 |
| `passage_epicur_11` | Epicurus, Letters and Fragments, SV 11 | 68 |
| `passage_epicur_110` | Epicurus, Letters and Fragments, Ep. Pyth. 110 | 650 |
| `passage_epicur_111` | Epicurus, Letters and Fragments, Ep. Pyth. 111 | 540 |
| `passage_epicur_112` | Epicurus, Letters and Fragments, Ep. Pyth. 112 | 471 |
| `passage_epicur_113` | Epicurus, Letters and Fragments, Ep. Pyth. 113 | 718 |
| `passage_epicur_114` | Epicurus, Letters and Fragments, Ep. Pyth. 114 | 576 |
| `passage_epicur_115` | Epicurus, Letters and Fragments, Ep. Pyth. 115 | 681 |
| `passage_epicur_116` | Epicurus, Letters and Fragments, Ep. Pyth. 116 | 607 |
| `passage_epicur_12` | Epicurus, Letters and Fragments, SV 12 | 65 |
| `passage_epicur_122` | Epicurus, Letters and Fragments, Ep. Men. 122 | 600 |
| `passage_epicur_123` | Epicurus, Letters and Fragments, Ep. Men. 123 | 608 |
| `passage_epicur_124` | Epicurus, Letters and Fragments, Ep. Men. 124 | 579 |
| `passage_epicur_125` | Epicurus, Letters and Fragments, Ep. Men. 125 | 629 |
| `passage_epicur_126` | Epicurus, Letters and Fragments, Ep. Men. 126 | 552 |
| `passage_epicur_127` | Epicurus, Letters and Fragments, Ep. Men. 127 | 584 |
| `passage_epicur_128` | Epicurus, Letters and Fragments, Ep. Men. 128 | 544 |
| `passage_epicur_129` | Epicurus, Letters and Fragments, Ep. Men. 129 | 678 |
| `passage_epicur_13` | Epicurus, Letters and Fragments, SV 13 | 101 |
| `passage_epicur_130` | Epicurus, Letters and Fragments, Ep. Men. 130 | 526 |
| `passage_epicur_131` | Epicurus, Letters and Fragments, Ep. Men. 131 | 642 |
| `passage_epicur_132` | Epicurus, Letters and Fragments, Ep. Men. 132 | 641 |
| `passage_epicur_133` | Epicurus, Letters and Fragments, Ep. Men. 133 | 585 |
| `passage_epicur_134` | Epicurus, Letters and Fragments, Ep. Men. 134 | 441 |
| `passage_epicur_135` | Epicurus, Letters and Fragments, Ep. Men. 135 | 404 |
| `passage_epicur_139` | Epicurus, Letters and Fragments, KD 139 | 586 |
| `passage_epicur_14` | Epicurus, Letters and Fragments, SV 14 | 204 |
| `passage_epicur_140` | Epicurus, Letters and Fragments, KD 140 | 585 |
| `passage_epicur_141` | Epicurus, Letters and Fragments, KD 141 | 378 |
| `passage_epicur_142` | Epicurus, Letters and Fragments, KD 142 | 610 |
| `passage_epicur_143` | Epicurus, Letters and Fragments, KD 143 | 494 |
| `passage_epicur_144` | Epicurus, Letters and Fragments, KD 144 | 566 |
| `passage_epicur_145` | Epicurus, Letters and Fragments, KD 145 | 520 |
| `passage_epicur_146` | Epicurus, Letters and Fragments, KD 146 | 439 |
| `passage_epicur_147` | Epicurus, Letters and Fragments, KD 147 | 471 |
| `passage_epicur_148` | Epicurus, Letters and Fragments, KD 148 | 652 |
| `passage_epicur_149` | Epicurus, Letters and Fragments, KD 149 | 654 |
| `passage_epicur_15` | Epicurus, Letters and Fragments, SV 15 | 147 |
| `passage_epicur_150` | Epicurus, Letters and Fragments, KD 150 | 502 |
| `passage_epicur_151` | Epicurus, Letters and Fragments, KD 151 | 501 |
| `passage_epicur_152` | Epicurus, Letters and Fragments, KD 152 | 524 |
| `passage_epicur_153` | Epicurus, Letters and Fragments, KD 153 | 378 |
| `passage_epicur_154` | Epicurus, Letters and Fragments, KD 154 | 479 |
| `passage_epicur_16` | Epicurus, Letters and Fragments, SV 16 | 129 |
| `passage_epicur_17` | Epicurus, Letters and Fragments, SV 17 | 222 |
| `passage_epicur_18` | Epicurus, Letters and Fragments, SV 18 | 80 |
| `passage_epicur_19` | Epicurus, Letters and Fragments, SV 19 | 53 |
| `passage_epicur_2` | Epicurus, Letters and Fragments, SV 2 | 89 |
| `passage_epicur_20` | Epicurus, Letters and Fragments, SV 20 | 151 |
| `passage_epicur_21` | Epicurus, Letters and Fragments, SV 21 | 152 |
| `passage_epicur_22` | Epicurus, Letters and Fragments, SV 22 | 111 |
| `passage_epicur_23` | Epicurus, Letters and Fragments, SV 23 | 64 |
| `passage_epicur_24` | Epicurus, Letters and Fragments, SV 24 | 88 |
| `passage_epicur_25` | Epicurus, Letters and Fragments, SV 25 | 102 |
| `passage_epicur_26` | Epicurus, Letters and Fragments, SV 26 | 71 |
| `passage_epicur_27` | Epicurus, Letters and Fragments, SV 27 | 181 |
| `passage_epicur_28` | Epicurus, Letters and Fragments, SV 28 | 111 |
| `passage_epicur_29` | Epicurus, Letters and Fragments, SV 29 | 217 |
| `passage_epicur_3` | Epicurus, Letters and Fragments, SV 3 | 246 |
| `passage_epicur_30` | Epicurus, Letters and Fragments, SV 30 | 119 |
| `passage_epicur_31` | Epicurus, Letters and Fragments, SV 31 | 104 |
| `passage_epicur_32` | Epicurus, Letters and Fragments, SV 32 | 50 |
| `passage_epicur_33` | Epicurus, Letters and Fragments, SV 33 | 127 |
| `passage_epicur_34` | Epicurus, Letters and Fragments, SV 34 | 85 |
| `passage_epicur_35` | Epicurus, Letters and Fragments, Ep. Hdt. 35 | 565 |
| `passage_epicur_35_s147` | Epicurus, Letters and Fragments, SV 35 | 102 |
| `passage_epicur_36` | Epicurus, Letters and Fragments, Ep. Hdt. 36 | 573 |
| `passage_epicur_36_s148` | Epicurus, Letters and Fragments, SV 36 | 98 |
| `passage_epicur_37` | Epicurus, Letters and Fragments, Ep. Hdt. 37 | 471 |
| `passage_epicur_37_s149` | Epicurus, Letters and Fragments, SV 37 | 102 |
| `passage_epicur_38` | Epicurus, Letters and Fragments, Ep. Hdt. 38 | 548 |
| `passage_epicur_38_s150` | Epicurus, Letters and Fragments, SV 38 | 61 |
| `passage_epicur_39` | Epicurus, Letters and Fragments, Ep. Hdt. 39 | 554 |
| `passage_epicur_39_s151` | Epicurus, Letters and Fragments, SV 39 | 163 |
| `passage_epicur_4` | Epicurus, Letters and Fragments, SV 4 | 142 |
| `passage_epicur_40` | Epicurus, Letters and Fragments, Ep. Hdt. 40 | 481 |
| `passage_epicur_40_s152` | Epicurus, Letters and Fragments, SV 40 | 141 |
| `passage_epicur_41` | Epicurus, Letters and Fragments, Ep. Hdt. 41 | 530 |
| `passage_epicur_41_s153` | Epicurus, Letters and Fragments, SV 41 | 141 |
| `passage_epicur_42` | Epicurus, Letters and Fragments, Ep. Hdt. 42 | 671 |
| `passage_epicur_42_s154` | Epicurus, Letters and Fragments, SV 42 | 63 |
| `passage_epicur_43` | Epicurus, Letters and Fragments, Ep. Hdt. 43 | 430 |
| `passage_epicur_43_s155` | Epicurus, Letters and Fragments, SV 43 | 100 |
| `passage_epicur_44` | Epicurus, Letters and Fragments, Ep. Hdt. 44 | 576 |
| `passage_epicur_44_s156` | Epicurus, Letters and Fragments, SV 44 | 120 |
| `passage_epicur_45` | Epicurus, Letters and Fragments, Ep. Hdt. 45 | 494 |
| `passage_epicur_45_s157` | Epicurus, Letters and Fragments, SV 45 | 225 |
| `passage_epicur_46` | Epicurus, Letters and Fragments, Ep. Hdt. 46 | 581 |
| `passage_epicur_46_s158` | Epicurus, Letters and Fragments, SV 46 | 90 |
| `passage_epicur_47` | Epicurus, Letters and Fragments, Ep. Hdt. 47 | 659 |
| `passage_epicur_47_s159` | Epicurus, Letters and Fragments, SV 47 | 302 |
| `passage_epicur_48` | Epicurus, Letters and Fragments, Ep. Hdt. 48 | 578 |
| `passage_epicur_48_s160` | Epicurus, Letters and Fragments, SV 48 | 121 |
| `passage_epicur_49` | Epicurus, Letters and Fragments, Ep. Hdt. 49 | 461 |
| `passage_epicur_49_s161` | Epicurus, Letters and Fragments, SV 49 | 191 |
| `passage_epicur_5` | Epicurus, Letters and Fragments, SV 5 | 107 |
| `passage_epicur_50` | Epicurus, Letters and Fragments, Ep. Hdt. 50 | 689 |
| `passage_epicur_50_s162` | Epicurus, Letters and Fragments, SV 50 | 99 |
| `passage_epicur_51` | Epicurus, Letters and Fragments, Ep. Hdt. 51 | 593 |
| `passage_epicur_51_s163` | Epicurus, Letters and Fragments, SV 51 | 400 |
| `passage_epicur_52` | Epicurus, Letters and Fragments, Ep. Hdt. 52 | 575 |
| `passage_epicur_52_s164` | Epicurus, Letters and Fragments, SV 52 | 90 |
| `passage_epicur_53` | Epicurus, Letters and Fragments, Ep. Hdt. 53 | 683 |
| `passage_epicur_53_s165` | Epicurus, Letters and Fragments, SV 53 | 116 |
| `passage_epicur_54` | Epicurus, Letters and Fragments, Ep. Hdt. 54 | 602 |
| `passage_epicur_54_s166` | Epicurus, Letters and Fragments, SV 54 | 130 |
| `passage_epicur_55` | Epicurus, Letters and Fragments, Ep. Hdt. 55 | 595 |
| `passage_epicur_55_s167` | Epicurus, Letters and Fragments, SV 55 | 110 |
| `passage_epicur_56` | Epicurus, Letters and Fragments, Ep. Hdt. 56 | 575 |
| `passage_epicur_56_s168` | Epicurus, Letters and Fragments, SV 56 | 70 |
| `passage_epicur_57` | Epicurus, Letters and Fragments, Ep. Hdt. 57 | 509 |
| `passage_epicur_57_s169` | Epicurus, Letters and Fragments, SV 57 | 70 |
| `passage_epicur_58` | Epicurus, Letters and Fragments, Ep. Hdt. 58 | 603 |
| `passage_epicur_58_s170` | Epicurus, Letters and Fragments, SV 58 | 66 |
| `passage_epicur_59` | Epicurus, Letters and Fragments, Ep. Hdt. 59 | 537 |
| `passage_epicur_59_s171` | Epicurus, Letters and Fragments, SV 59 | 103 |
| `passage_epicur_6` | Epicurus, Letters and Fragments, SV 6 | 193 |
| `passage_epicur_60` | Epicurus, Letters and Fragments, Ep. Hdt. 60 | 617 |
| `passage_epicur_60_s172` | Epicurus, Letters and Fragments, SV 60 | 44 |
| `passage_epicur_61` | Epicurus, Letters and Fragments, Ep. Hdt. 61 | 532 |
| `passage_epicur_61_s173` | Epicurus, Letters and Fragments, SV 61 | 109 |
| `passage_epicur_62` | Epicurus, Letters and Fragments, Ep. Hdt. 62 | 548 |
| `passage_epicur_62_s174` | Epicurus, Letters and Fragments, SV 62 | 300 |
| `passage_epicur_63` | Epicurus, Letters and Fragments, Ep. Hdt. 63 | 594 |
| `passage_epicur_63_s175` | Epicurus, Letters and Fragments, SV 63 | 103 |
| `passage_epicur_64` | Epicurus, Letters and Fragments, Ep. Hdt. 64 | 546 |
| `passage_epicur_64_s176` | Epicurus, Letters and Fragments, SV 64 | 93 |
| `passage_epicur_65` | Epicurus, Letters and Fragments, Ep. Hdt. 65 | 521 |
| `passage_epicur_65_s177` | Epicurus, Letters and Fragments, SV 65 | 67 |
| `passage_epicur_66` | Epicurus, Letters and Fragments, Ep. Hdt. 66 | 641 |
| `passage_epicur_66_s178` | Epicurus, Letters and Fragments, SV 66 | 55 |
| `passage_epicur_67` | Epicurus, Letters and Fragments, Ep. Hdt. 67 | 461 |
| `passage_epicur_67_s179` | Epicurus, Letters and Fragments, SV 67 | 251 |
| `passage_epicur_68` | Epicurus, Letters and Fragments, Ep. Hdt. 68 | 445 |
| `passage_epicur_68_s180` | Epicurus, Letters and Fragments, SV 68 | 32 |
| `passage_epicur_69` | Epicurus, Letters and Fragments, Ep. Hdt. 69 | 607 |
| `passage_epicur_69_s181` | Epicurus, Letters and Fragments, SV 69 | 84 |
| `passage_epicur_7` | Epicurus, Letters and Fragments, SV 7 | 73 |
| `passage_epicur_70` | Epicurus, Letters and Fragments, Ep. Hdt. 70 | 356 |
| `passage_epicur_70_s182` | Epicurus, Letters and Fragments, SV 70 | 73 |
| `passage_epicur_71` | Epicurus, Letters and Fragments, Ep. Hdt. 71 | 635 |
| `passage_epicur_71_s183` | Epicurus, Letters and Fragments, SV 71 | 143 |
| `passage_epicur_72` | Epicurus, Letters and Fragments, Ep. Hdt. 72 | 585 |
| `passage_epicur_72_s184` | Epicurus, Letters and Fragments, SV 72 | 131 |
| `passage_epicur_73` | Epicurus, Letters and Fragments, Ep. Hdt. 73 | 714 |
| `passage_epicur_73_s185` | Epicurus, Letters and Fragments, SV 73 | 78 |
| `passage_epicur_74` | Epicurus, Letters and Fragments, Ep. Hdt. 74 | 708 |
| `passage_epicur_74_s186` | Epicurus, Letters and Fragments, SV 74 | 66 |
| `passage_epicur_75` | Epicurus, Letters and Fragments, Ep. Hdt. 75 | 635 |
| `passage_epicur_75_s187` | Epicurus, Letters and Fragments, SV 75 | 71 |
| `passage_epicur_76` | Epicurus, Letters and Fragments, Ep. Hdt. 76 | 563 |
| `passage_epicur_76_s188` | Epicurus, Letters and Fragments, SV 76 | 124 |
| `passage_epicur_77` | Epicurus, Letters and Fragments, Ep. Hdt. 77 | 614 |
| `passage_epicur_77_s189` | Epicurus, Letters and Fragments, SV 77 | 41 |
| `passage_epicur_78` | Epicurus, Letters and Fragments, Ep. Hdt. 78 | 492 |
| `passage_epicur_78_s190` | Epicurus, Letters and Fragments, SV 78 | 96 |
| `passage_epicur_79` | Epicurus, Letters and Fragments, Ep. Hdt. 79 | 578 |
| `passage_epicur_79_s191` | Epicurus, Letters and Fragments, SV 79 | 36 |
| `passage_epicur_8` | Epicurus, Letters and Fragments, SV 8 | 114 |
| `passage_epicur_80` | Epicurus, Letters and Fragments, Ep. Hdt. 80 | 649 |
| `passage_epicur_80_s192` | Epicurus, Letters and Fragments, SV 80 | 109 |
| `passage_epicur_81` | Epicurus, Letters and Fragments, Ep. Hdt. 81 | 547 |
| `passage_epicur_81_s193` | Epicurus, Letters and Fragments, SV 81 | 191 |
| `passage_epicur_82` | Epicurus, Letters and Fragments, Ep. Hdt. 82 | 565 |
| `passage_epicur_83` | Epicurus, Letters and Fragments, Ep. Hdt. 83 | 698 |
| `passage_epicur_84` | Epicurus, Letters and Fragments, Ep. Pyth. 84 | 486 |
| `passage_epicur_85` | Epicurus, Letters and Fragments, Ep. Pyth. 85 | 553 |
| `passage_epicur_86` | Epicurus, Letters and Fragments, Ep. Pyth. 86 | 528 |
| `passage_epicur_87` | Epicurus, Letters and Fragments, Ep. Pyth. 87 | 591 |
| `passage_epicur_88` | Epicurus, Letters and Fragments, Ep. Pyth. 88 | 579 |
| `passage_epicur_89` | Epicurus, Letters and Fragments, Ep. Pyth. 89 | 537 |
| `passage_epicur_9` | Epicurus, Letters and Fragments, SV 9 | 51 |
| `passage_epicur_90` | Epicurus, Letters and Fragments, Ep. Pyth. 90 | 616 |
| `passage_epicur_91` | Epicurus, Letters and Fragments, Ep. Pyth. 91 | 592 |
| `passage_epicur_92` | Epicurus, Letters and Fragments, Ep. Pyth. 92 | 484 |
| `passage_epicur_93` | Epicurus, Letters and Fragments, Ep. Pyth. 93 | 749 |
| `passage_epicur_94` | Epicurus, Letters and Fragments, Ep. Pyth. 94 | 526 |
| `passage_epicur_95` | Epicurus, Letters and Fragments, Ep. Pyth. 95 | 521 |
| `passage_epicur_96` | Epicurus, Letters and Fragments, Ep. Pyth. 96 | 608 |
| `passage_epicur_97` | Epicurus, Letters and Fragments, Ep. Pyth. 97 | 610 |
| `passage_epicur_98` | Epicurus, Letters and Fragments, Ep. Pyth. 98 | 539 |
| `passage_epicur_99` | Epicurus, Letters and Fragments, Ep. Pyth. 99 | 494 |

### Epictetus — Discourses and Enchiridion

- **Language:** Greek
- **Passages:** 185
- **Characters:** 390,997
- **Canonical ID:** `urn:cts:greekLit:tlg0557`

| node_id | label | chars |
|---------|-------|-------|
| `passage_epict_1_s1` | Epictetus, Discourses and Enchiridion, Epict. 1 | 2,088 |
| `passage_epict_10_s10` | Epictetus, Discourses and Enchiridion, Epict. 10 | 2,090 |
| `passage_epict_100_s100` | Epictetus, Discourses and Enchiridion, Epict. 100 | 2,137 |
| `passage_epict_101_s101` | Epictetus, Discourses and Enchiridion, Epict. 101 | 2,130 |
| `passage_epict_102_s102` | Epictetus, Discourses and Enchiridion, Epict. 102 | 2,096 |
| `passage_epict_103_s103` | Epictetus, Discourses and Enchiridion, Epict. 103 | 2,155 |
| `passage_epict_104_s104` | Epictetus, Discourses and Enchiridion, Epict. 104 | 2,103 |
| `passage_epict_105_s105` | Epictetus, Discourses and Enchiridion, Epict. 105 | 2,135 |
| `passage_epict_106_s106` | Epictetus, Discourses and Enchiridion, Epict. 106 | 2,118 |
| `passage_epict_107_s107` | Epictetus, Discourses and Enchiridion, Epict. 107 | 2,117 |
| `passage_epict_108_s108` | Epictetus, Discourses and Enchiridion, Epict. 108 | 2,115 |
| `passage_epict_109_s109` | Epictetus, Discourses and Enchiridion, Epict. 109 | 2,147 |
| `passage_epict_11_s11` | Epictetus, Discourses and Enchiridion, Epict. 11 | 2,077 |
| `passage_epict_110_s110` | Epictetus, Discourses and Enchiridion, Epict. 110 | 2,113 |
| `passage_epict_111_s111` | Epictetus, Discourses and Enchiridion, Epict. 111 | 2,118 |
| `passage_epict_112_s112` | Epictetus, Discourses and Enchiridion, Epict. 112 | 2,105 |
| `passage_epict_113_s113` | Epictetus, Discourses and Enchiridion, Epict. 113 | 2,125 |
| `passage_epict_114_s114` | Epictetus, Discourses and Enchiridion, Epict. 114 | 2,144 |
| `passage_epict_115_s115` | Epictetus, Discourses and Enchiridion, Epict. 115 | 2,114 |
| `passage_epict_116_s116` | Epictetus, Discourses and Enchiridion, Epict. 116 | 2,106 |
| `passage_epict_117_s117` | Epictetus, Discourses and Enchiridion, Epict. 117 | 2,117 |
| `passage_epict_118_s118` | Epictetus, Discourses and Enchiridion, Epict. 118 | 2,129 |
| `passage_epict_119_s119` | Epictetus, Discourses and Enchiridion, Epict. 119 | 2,123 |
| `passage_epict_12_s12` | Epictetus, Discourses and Enchiridion, Epict. 12 | 2,093 |
| `passage_epict_120_s120` | Epictetus, Discourses and Enchiridion, Epict. 120 | 2,126 |
| `passage_epict_121_s121` | Epictetus, Discourses and Enchiridion, Epict. 121 | 2,101 |
| `passage_epict_122_s122` | Epictetus, Discourses and Enchiridion, Epict. 122 | 2,136 |
| `passage_epict_123_s123` | Epictetus, Discourses and Enchiridion, Epict. 123 | 2,141 |
| `passage_epict_124_s124` | Epictetus, Discourses and Enchiridion, Epict. 124 | 2,133 |
| `passage_epict_125_s125` | Epictetus, Discourses and Enchiridion, Epict. 125 | 2,107 |
| `passage_epict_126_s126` | Epictetus, Discourses and Enchiridion, Epict. 126 | 2,125 |
| `passage_epict_127_s127` | Epictetus, Discourses and Enchiridion, Epict. 127 | 2,127 |
| `passage_epict_128_s128` | Epictetus, Discourses and Enchiridion, Epict. 128 | 2,124 |
| `passage_epict_129_s129` | Epictetus, Discourses and Enchiridion, Epict. 129 | 2,119 |
| `passage_epict_13_s13` | Epictetus, Discourses and Enchiridion, Epict. 13 | 2,113 |
| `passage_epict_130_s130` | Epictetus, Discourses and Enchiridion, Epict. 130 | 2,122 |
| `passage_epict_131_s131` | Epictetus, Discourses and Enchiridion, Epict. 131 | 2,148 |
| `passage_epict_132_s132` | Epictetus, Discourses and Enchiridion, Epict. 132 | 2,138 |
| `passage_epict_133_s133` | Epictetus, Discourses and Enchiridion, Epict. 133 | 2,114 |
| `passage_epict_134_s134` | Epictetus, Discourses and Enchiridion, Epict. 134 | 2,133 |
| `passage_epict_135_s135` | Epictetus, Discourses and Enchiridion, Epict. 135 | 2,156 |
| `passage_epict_136_s136` | Epictetus, Discourses and Enchiridion, Epict. 136 | 2,134 |
| `passage_epict_137_s137` | Epictetus, Discourses and Enchiridion, Epict. 137 | 2,131 |
| `passage_epict_138_s138` | Epictetus, Discourses and Enchiridion, Epict. 138 | 2,107 |
| `passage_epict_139_s139` | Epictetus, Discourses and Enchiridion, Epict. 139 | 2,125 |
| `passage_epict_14_s14` | Epictetus, Discourses and Enchiridion, Epict. 14 | 2,092 |
| `passage_epict_140_s140` | Epictetus, Discourses and Enchiridion, Epict. 140 | 2,155 |
| `passage_epict_141_s141` | Epictetus, Discourses and Enchiridion, Epict. 141 | 2,139 |
| `passage_epict_142_s142` | Epictetus, Discourses and Enchiridion, Epict. 142 | 2,158 |
| `passage_epict_143_s143` | Epictetus, Discourses and Enchiridion, Epict. 143 | 2,123 |
| `passage_epict_144_s144` | Epictetus, Discourses and Enchiridion, Epict. 144 | 2,133 |
| `passage_epict_145_s145` | Epictetus, Discourses and Enchiridion, Epict. 145 | 2,137 |
| `passage_epict_146_s146` | Epictetus, Discourses and Enchiridion, Epict. 146 | 2,126 |
| `passage_epict_147_s147` | Epictetus, Discourses and Enchiridion, Epict. 147 | 2,145 |
| `passage_epict_148_s148` | Epictetus, Discourses and Enchiridion, Epict. 148 | 2,141 |
| `passage_epict_149_s149` | Epictetus, Discourses and Enchiridion, Epict. 149 | 2,135 |
| `passage_epict_15_s15` | Epictetus, Discourses and Enchiridion, Epict. 15 | 2,122 |
| `passage_epict_150_s150` | Epictetus, Discourses and Enchiridion, Epict. 150 | 2,125 |
| `passage_epict_151_s151` | Epictetus, Discourses and Enchiridion, Epict. 151 | 2,142 |
| `passage_epict_152_s152` | Epictetus, Discourses and Enchiridion, Epict. 152 | 2,141 |
| `passage_epict_153_s153` | Epictetus, Discourses and Enchiridion, Epict. 153 | 2,137 |
| `passage_epict_154_s154` | Epictetus, Discourses and Enchiridion, Epict. 154 | 2,125 |
| `passage_epict_155_s155` | Epictetus, Discourses and Enchiridion, Epict. 155 | 2,149 |
| `passage_epict_156_s156` | Epictetus, Discourses and Enchiridion, Epict. 156 | 2,146 |
| `passage_epict_157_s157` | Epictetus, Discourses and Enchiridion, Epict. 157 | 2,124 |
| `passage_epict_158_s158` | Epictetus, Discourses and Enchiridion, Epict. 158 | 2,113 |
| `passage_epict_159_s159` | Epictetus, Discourses and Enchiridion, Epict. 159 | 2,128 |
| `passage_epict_16_s16` | Epictetus, Discourses and Enchiridion, Epict. 16 | 2,097 |
| `passage_epict_160_s160` | Epictetus, Discourses and Enchiridion, Epict. 160 | 2,132 |
| `passage_epict_161_s161` | Epictetus, Discourses and Enchiridion, Epict. 161 | 2,125 |
| `passage_epict_162_s162` | Epictetus, Discourses and Enchiridion, Epict. 162 | 2,119 |
| `passage_epict_163_s163` | Epictetus, Discourses and Enchiridion, Epict. 163 | 2,149 |
| `passage_epict_164_s164` | Epictetus, Discourses and Enchiridion, Epict. 164 | 2,134 |
| `passage_epict_165_s165` | Epictetus, Discourses and Enchiridion, Epict. 165 | 2,138 |
| `passage_epict_166_s166` | Epictetus, Discourses and Enchiridion, Epict. 166 | 2,109 |
| `passage_epict_167_s167` | Epictetus, Discourses and Enchiridion, Epict. 167 | 2,129 |
| `passage_epict_168_s168` | Epictetus, Discourses and Enchiridion, Epict. 168 | 2,131 |
| `passage_epict_169_s169` | Epictetus, Discourses and Enchiridion, Epict. 169 | 2,096 |
| `passage_epict_17_s17` | Epictetus, Discourses and Enchiridion, Epict. 17 | 2,123 |
| `passage_epict_170_s170` | Epictetus, Discourses and Enchiridion, Epict. 170 | 2,112 |
| `passage_epict_171_s171` | Epictetus, Discourses and Enchiridion, Epict. 171 | 2,113 |
| `passage_epict_172_s172` | Epictetus, Discourses and Enchiridion, Epict. 172 | 2,143 |
| `passage_epict_173_s173` | Epictetus, Discourses and Enchiridion, Epict. 173 | 2,128 |
| `passage_epict_174_s174` | Epictetus, Discourses and Enchiridion, Epict. 174 | 2,133 |
| `passage_epict_175_s175` | Epictetus, Discourses and Enchiridion, Epict. 175 | 2,088 |
| `passage_epict_176_s176` | Epictetus, Discourses and Enchiridion, Epict. 176 | 2,103 |
| `passage_epict_177_s177` | Epictetus, Discourses and Enchiridion, Epict. 177 | 2,117 |
| `passage_epict_178_s178` | Epictetus, Discourses and Enchiridion, Epict. 178 | 2,109 |
| `passage_epict_179_s179` | Epictetus, Discourses and Enchiridion, Epict. 179 | 2,071 |
| `passage_epict_18_s18` | Epictetus, Discourses and Enchiridion, Epict. 18 | 2,089 |
| `passage_epict_180_s180` | Epictetus, Discourses and Enchiridion, Epict. 180 | 2,103 |
| `passage_epict_181_s181` | Epictetus, Discourses and Enchiridion, Epict. 181 | 2,085 |
| `passage_epict_182_s182` | Epictetus, Discourses and Enchiridion, Epict. 182 | 2,110 |
| `passage_epict_183_s183` | Epictetus, Discourses and Enchiridion, Epict. 183 | 2,087 |
| `passage_epict_184_s184` | Epictetus, Discourses and Enchiridion, Epict. 184 | 2,112 |
| `passage_epict_185_s185` | Epictetus, Discourses and Enchiridion, Epict. 185 | 374 |
| `passage_epict_19_s19` | Epictetus, Discourses and Enchiridion, Epict. 19 | 2,111 |
| `passage_epict_2_s2` | Epictetus, Discourses and Enchiridion, Epict. 2 | 2,140 |
| `passage_epict_20_s20` | Epictetus, Discourses and Enchiridion, Epict. 20 | 2,122 |
| `passage_epict_21_s21` | Epictetus, Discourses and Enchiridion, Epict. 21 | 2,102 |
| `passage_epict_22_s22` | Epictetus, Discourses and Enchiridion, Epict. 22 | 2,133 |
| `passage_epict_23_s23` | Epictetus, Discourses and Enchiridion, Epict. 23 | 2,116 |
| `passage_epict_24_s24` | Epictetus, Discourses and Enchiridion, Epict. 24 | 2,098 |
| `passage_epict_25_s25` | Epictetus, Discourses and Enchiridion, Epict. 25 | 2,129 |
| `passage_epict_26_s26` | Epictetus, Discourses and Enchiridion, Epict. 26 | 2,141 |
| `passage_epict_27_s27` | Epictetus, Discourses and Enchiridion, Epict. 27 | 2,100 |
| `passage_epict_28_s28` | Epictetus, Discourses and Enchiridion, Epict. 28 | 2,117 |
| `passage_epict_29_s29` | Epictetus, Discourses and Enchiridion, Epict. 29 | 2,138 |
| `passage_epict_3_s3` | Epictetus, Discourses and Enchiridion, Epict. 3 | 2,102 |
| `passage_epict_30_s30` | Epictetus, Discourses and Enchiridion, Epict. 30 | 2,136 |
| `passage_epict_31_s31` | Epictetus, Discourses and Enchiridion, Epict. 31 | 2,147 |
| `passage_epict_32_s32` | Epictetus, Discourses and Enchiridion, Epict. 32 | 2,156 |
| `passage_epict_33_s33` | Epictetus, Discourses and Enchiridion, Epict. 33 | 2,124 |
| `passage_epict_34_s34` | Epictetus, Discourses and Enchiridion, Epict. 34 | 2,102 |
| `passage_epict_35_s35` | Epictetus, Discourses and Enchiridion, Epict. 35 | 2,136 |
| `passage_epict_36_s36` | Epictetus, Discourses and Enchiridion, Epict. 36 | 2,108 |
| `passage_epict_37_s37` | Epictetus, Discourses and Enchiridion, Epict. 37 | 2,110 |
| `passage_epict_38_s38` | Epictetus, Discourses and Enchiridion, Epict. 38 | 2,140 |
| `passage_epict_39_s39` | Epictetus, Discourses and Enchiridion, Epict. 39 | 2,121 |
| `passage_epict_4_s4` | Epictetus, Discourses and Enchiridion, Epict. 4 | 2,121 |
| `passage_epict_40_s40` | Epictetus, Discourses and Enchiridion, Epict. 40 | 2,132 |
| `passage_epict_41_s41` | Epictetus, Discourses and Enchiridion, Epict. 41 | 2,124 |
| `passage_epict_42_s42` | Epictetus, Discourses and Enchiridion, Epict. 42 | 2,106 |
| `passage_epict_43_s43` | Epictetus, Discourses and Enchiridion, Epict. 43 | 2,104 |
| `passage_epict_44_s44` | Epictetus, Discourses and Enchiridion, Epict. 44 | 2,144 |
| `passage_epict_45_s45` | Epictetus, Discourses and Enchiridion, Epict. 45 | 2,129 |
| `passage_epict_46_s46` | Epictetus, Discourses and Enchiridion, Epict. 46 | 2,131 |
| `passage_epict_47_s47` | Epictetus, Discourses and Enchiridion, Epict. 47 | 2,141 |
| `passage_epict_48_s48` | Epictetus, Discourses and Enchiridion, Epict. 48 | 2,143 |
| `passage_epict_49_s49` | Epictetus, Discourses and Enchiridion, Epict. 49 | 2,118 |
| `passage_epict_5_s5` | Epictetus, Discourses and Enchiridion, Epict. 5 | 2,132 |
| `passage_epict_50_s50` | Epictetus, Discourses and Enchiridion, Epict. 50 | 2,135 |
| `passage_epict_51_s51` | Epictetus, Discourses and Enchiridion, Epict. 51 | 2,119 |
| `passage_epict_52_s52` | Epictetus, Discourses and Enchiridion, Epict. 52 | 2,122 |
| `passage_epict_53_s53` | Epictetus, Discourses and Enchiridion, Epict. 53 | 2,145 |
| `passage_epict_54_s54` | Epictetus, Discourses and Enchiridion, Epict. 54 | 2,121 |
| `passage_epict_55_s55` | Epictetus, Discourses and Enchiridion, Epict. 55 | 2,099 |
| `passage_epict_56_s56` | Epictetus, Discourses and Enchiridion, Epict. 56 | 2,129 |
| `passage_epict_57_s57` | Epictetus, Discourses and Enchiridion, Epict. 57 | 2,114 |
| `passage_epict_58_s58` | Epictetus, Discourses and Enchiridion, Epict. 58 | 2,122 |
| `passage_epict_59_s59` | Epictetus, Discourses and Enchiridion, Epict. 59 | 2,089 |
| `passage_epict_6_s6` | Epictetus, Discourses and Enchiridion, Epict. 6 | 2,106 |
| `passage_epict_60_s60` | Epictetus, Discourses and Enchiridion, Epict. 60 | 2,112 |
| `passage_epict_61_s61` | Epictetus, Discourses and Enchiridion, Epict. 61 | 2,126 |
| `passage_epict_62_s62` | Epictetus, Discourses and Enchiridion, Epict. 62 | 2,146 |
| `passage_epict_63_s63` | Epictetus, Discourses and Enchiridion, Epict. 63 | 2,103 |
| `passage_epict_64_s64` | Epictetus, Discourses and Enchiridion, Epict. 64 | 2,113 |
| `passage_epict_65_s65` | Epictetus, Discourses and Enchiridion, Epict. 65 | 2,129 |
| `passage_epict_66_s66` | Epictetus, Discourses and Enchiridion, Epict. 66 | 2,124 |
| `passage_epict_67_s67` | Epictetus, Discourses and Enchiridion, Epict. 67 | 2,139 |
| `passage_epict_68_s68` | Epictetus, Discourses and Enchiridion, Epict. 68 | 2,126 |
| `passage_epict_69_s69` | Epictetus, Discourses and Enchiridion, Epict. 69 | 2,108 |
| `passage_epict_7_s7` | Epictetus, Discourses and Enchiridion, Epict. 7 | 2,132 |
| `passage_epict_70_s70` | Epictetus, Discourses and Enchiridion, Epict. 70 | 2,116 |
| `passage_epict_71_s71` | Epictetus, Discourses and Enchiridion, Epict. 71 | 2,127 |
| `passage_epict_72_s72` | Epictetus, Discourses and Enchiridion, Epict. 72 | 2,104 |
| `passage_epict_73_s73` | Epictetus, Discourses and Enchiridion, Epict. 73 | 2,113 |
| `passage_epict_74_s74` | Epictetus, Discourses and Enchiridion, Epict. 74 | 2,091 |
| `passage_epict_75_s75` | Epictetus, Discourses and Enchiridion, Epict. 75 | 2,112 |
| `passage_epict_76_s76` | Epictetus, Discourses and Enchiridion, Epict. 76 | 2,112 |
| `passage_epict_77_s77` | Epictetus, Discourses and Enchiridion, Epict. 77 | 2,117 |
| `passage_epict_78_s78` | Epictetus, Discourses and Enchiridion, Epict. 78 | 2,115 |
| `passage_epict_79_s79` | Epictetus, Discourses and Enchiridion, Epict. 79 | 2,106 |
| `passage_epict_8_s8` | Epictetus, Discourses and Enchiridion, Epict. 8 | 2,108 |
| `passage_epict_80_s80` | Epictetus, Discourses and Enchiridion, Epict. 80 | 2,119 |
| `passage_epict_81_s81` | Epictetus, Discourses and Enchiridion, Epict. 81 | 2,124 |
| `passage_epict_82_s82` | Epictetus, Discourses and Enchiridion, Epict. 82 | 2,118 |
| `passage_epict_83_s83` | Epictetus, Discourses and Enchiridion, Epict. 83 | 2,116 |
| `passage_epict_84_s84` | Epictetus, Discourses and Enchiridion, Epict. 84 | 2,141 |
| `passage_epict_85_s85` | Epictetus, Discourses and Enchiridion, Epict. 85 | 2,145 |
| `passage_epict_86_s86` | Epictetus, Discourses and Enchiridion, Epict. 86 | 2,146 |
| `passage_epict_87_s87` | Epictetus, Discourses and Enchiridion, Epict. 87 | 2,147 |
| `passage_epict_88_s88` | Epictetus, Discourses and Enchiridion, Epict. 88 | 2,144 |
| `passage_epict_89_s89` | Epictetus, Discourses and Enchiridion, Epict. 89 | 2,135 |
| `passage_epict_9_s9` | Epictetus, Discourses and Enchiridion, Epict. 9 | 2,117 |
| `passage_epict_90_s90` | Epictetus, Discourses and Enchiridion, Epict. 90 | 2,138 |
| `passage_epict_91_s91` | Epictetus, Discourses and Enchiridion, Epict. 91 | 2,114 |
| `passage_epict_92_s92` | Epictetus, Discourses and Enchiridion, Epict. 92 | 2,141 |
| `passage_epict_93_s93` | Epictetus, Discourses and Enchiridion, Epict. 93 | 2,143 |
| `passage_epict_94_s94` | Epictetus, Discourses and Enchiridion, Epict. 94 | 2,139 |
| `passage_epict_95_s95` | Epictetus, Discourses and Enchiridion, Epict. 95 | 2,139 |
| `passage_epict_96_s96` | Epictetus, Discourses and Enchiridion, Epict. 96 | 2,138 |
| `passage_epict_97_s97` | Epictetus, Discourses and Enchiridion, Epict. 97 | 2,160 |
| `passage_epict_98_s98` | Epictetus, Discourses and Enchiridion, Epict. 98 | 2,117 |
| `passage_epict_99_s99` | Epictetus, Discourses and Enchiridion, Epict. 99 | 2,132 |

### Augustine — De Libero Arbitrio

- **Language:** Latin
- **Passages:** 170
- **Characters:** 251,666
- **Canonical ID:** `urn:cts:latinLit:stoa0040.stoa003`

| node_id | label | chars |
|---------|-------|-------|
| `passage_aug_dla_1_1_1` | Augustine, De Libero Arbitrio, 1.1.1 | 1,140 |
| `passage_aug_dla_1_1_2` | Augustine, De Libero Arbitrio, 1.1.2 | 1,202 |
| `passage_aug_dla_1_1_3` | Augustine, De Libero Arbitrio, 1.1.3 | 1,155 |
| `passage_aug_dla_1_10_20` | Augustine, De Libero Arbitrio, 1.10.20 | 1,508 |
| `passage_aug_dla_1_10_21` | Augustine, De Libero Arbitrio, 1.10.21 | 432 |
| `passage_aug_dla_1_11_21` | Augustine, De Libero Arbitrio, 1.11.21 | 720 |
| `passage_aug_dla_1_11_22` | Augustine, De Libero Arbitrio, 1.11.22 | 1,430 |
| `passage_aug_dla_1_11_23` | Augustine, De Libero Arbitrio, 1.11.23 | 629 |
| `passage_aug_dla_1_12_24` | Augustine, De Libero Arbitrio, 1.12.24 | 773 |
| `passage_aug_dla_1_12_25` | Augustine, De Libero Arbitrio, 1.12.25 | 1,692 |
| `passage_aug_dla_1_12_26` | Augustine, De Libero Arbitrio, 1.12.26 | 1,086 |
| `passage_aug_dla_1_13_27` | Augustine, De Libero Arbitrio, 1.13.27 | 2,703 |
| `passage_aug_dla_1_13_28` | Augustine, De Libero Arbitrio, 1.13.28 | 1,430 |
| `passage_aug_dla_1_13_29` | Augustine, De Libero Arbitrio, 1.13.29 | 1,057 |
| `passage_aug_dla_1_14_30` | Augustine, De Libero Arbitrio, 1.14.30 | 1,772 |
| `passage_aug_dla_1_15_31` | Augustine, De Libero Arbitrio, 1.15.31 | 1,987 |
| `passage_aug_dla_1_15_32` | Augustine, De Libero Arbitrio, 1.15.32 | 2,069 |
| `passage_aug_dla_1_15_33` | Augustine, De Libero Arbitrio, 1.15.33 | 1,304 |
| `passage_aug_dla_1_16_34` | Augustine, De Libero Arbitrio, 1.16.34 | 1,288 |
| `passage_aug_dla_1_16_35` | Augustine, De Libero Arbitrio, 1.16.35 | 1,592 |
| `passage_aug_dla_1_2_4` | Augustine, De Libero Arbitrio, 1.2.4 | 1,120 |
| `passage_aug_dla_1_2_5` | Augustine, De Libero Arbitrio, 1.2.5 | 980 |
| `passage_aug_dla_1_3_6` | Augustine, De Libero Arbitrio, 1.3.6 | 1,697 |
| `passage_aug_dla_1_3_7` | Augustine, De Libero Arbitrio, 1.3.7 | 721 |
| `passage_aug_dla_1_3_8` | Augustine, De Libero Arbitrio, 1.3.8 | 689 |
| `passage_aug_dla_1_4_10` | Augustine, De Libero Arbitrio, 1.4.10 | 1,806 |
| `passage_aug_dla_1_4_9` | Augustine, De Libero Arbitrio, 1.4.9 | 1,844 |
| `passage_aug_dla_1_5_11` | Augustine, De Libero Arbitrio, 1.5.11 | 1,005 |
| `passage_aug_dla_1_5_12` | Augustine, De Libero Arbitrio, 1.5.12 | 2,195 |
| `passage_aug_dla_1_5_13` | Augustine, De Libero Arbitrio, 1.5.13 | 1,172 |
| `passage_aug_dla_1_6_14` | Augustine, De Libero Arbitrio, 1.6.14 | 2,201 |
| `passage_aug_dla_1_6_15` | Augustine, De Libero Arbitrio, 1.6.15 | 1,553 |
| `passage_aug_dla_1_7_16` | Augustine, De Libero Arbitrio, 1.7.16 | 2,698 |
| `passage_aug_dla_1_7_17` | Augustine, De Libero Arbitrio, 1.7.17 | 1,045 |
| `passage_aug_dla_1_8_18` | Augustine, De Libero Arbitrio, 1.8.18 | 1,937 |
| `passage_aug_dla_1_9_19` | Augustine, De Libero Arbitrio, 1.9.19 | 2,267 |
| `passage_aug_dla_2_1_1` | Augustine, De Libero Arbitrio, 2.1.1 | 1,089 |
| `passage_aug_dla_2_1_2` | Augustine, De Libero Arbitrio, 2.1.2 | 760 |
| `passage_aug_dla_2_1_3` | Augustine, De Libero Arbitrio, 2.1.3 | 1,377 |
| `passage_aug_dla_2_10_28` | Augustine, De Libero Arbitrio, 2.10.28 | 2,178 |
| `passage_aug_dla_2_10_29` | Augustine, De Libero Arbitrio, 2.10.29 | 2,098 |
| `passage_aug_dla_2_11_30` | Augustine, De Libero Arbitrio, 2.11.30 | 2,045 |
| `passage_aug_dla_2_11_31` | Augustine, De Libero Arbitrio, 2.11.31 | 1,111 |
| `passage_aug_dla_2_11_32` | Augustine, De Libero Arbitrio, 2.11.32 | 1,444 |
| `passage_aug_dla_2_12_33` | Augustine, De Libero Arbitrio, 2.12.33 | 1,128 |
| `passage_aug_dla_2_12_34` | Augustine, De Libero Arbitrio, 2.12.34 | 1,851 |
| `passage_aug_dla_2_13_35` | Augustine, De Libero Arbitrio, 2.13.35 | 1,916 |
| `passage_aug_dla_2_13_36` | Augustine, De Libero Arbitrio, 2.13.36 | 975 |
| `passage_aug_dla_2_13_37` | Augustine, De Libero Arbitrio, 2.13.37 | 486 |
| `passage_aug_dla_2_14_37` | Augustine, De Libero Arbitrio, 2.14.37 | 1,051 |
| `passage_aug_dla_2_14_38` | Augustine, De Libero Arbitrio, 2.14.38 | 2,053 |
| `passage_aug_dla_2_15_39` | Augustine, De Libero Arbitrio, 2.15.39 | 1,351 |
| `passage_aug_dla_2_15_40` | Augustine, De Libero Arbitrio, 2.15.40 | 1,672 |
| `passage_aug_dla_2_16_41` | Augustine, De Libero Arbitrio, 2.16.41 | 1,439 |
| `passage_aug_dla_2_16_42` | Augustine, De Libero Arbitrio, 2.16.42 | 1,820 |
| `passage_aug_dla_2_16_43` | Augustine, De Libero Arbitrio, 2.16.43 | 1,445 |
| `passage_aug_dla_2_16_44` | Augustine, De Libero Arbitrio, 2.16.44 | 598 |
| `passage_aug_dla_2_17_45` | Augustine, De Libero Arbitrio, 2.17.45 | 1,730 |
| `passage_aug_dla_2_17_46` | Augustine, De Libero Arbitrio, 2.17.46 | 1,549 |
| `passage_aug_dla_2_18_47` | Augustine, De Libero Arbitrio, 2.18.47 | 1,825 |
| `passage_aug_dla_2_18_48` | Augustine, De Libero Arbitrio, 2.18.48 | 1,590 |
| `passage_aug_dla_2_18_49` | Augustine, De Libero Arbitrio, 2.18.49 | 1,583 |
| `passage_aug_dla_2_18_50` | Augustine, De Libero Arbitrio, 2.18.50 | 416 |
| `passage_aug_dla_2_19_50` | Augustine, De Libero Arbitrio, 2.19.50 | 1,016 |
| `passage_aug_dla_2_19_51` | Augustine, De Libero Arbitrio, 2.19.51 | 983 |
| `passage_aug_dla_2_19_52` | Augustine, De Libero Arbitrio, 2.19.52 | 1,228 |
| `passage_aug_dla_2_19_53` | Augustine, De Libero Arbitrio, 2.19.53 | 1,118 |
| `passage_aug_dla_2_2_4` | Augustine, De Libero Arbitrio, 2.2.4 | 1,216 |
| `passage_aug_dla_2_2_5` | Augustine, De Libero Arbitrio, 2.2.5 | 2,518 |
| `passage_aug_dla_2_2_6` | Augustine, De Libero Arbitrio, 2.2.6 | 1,667 |
| `passage_aug_dla_2_20_54` | Augustine, De Libero Arbitrio, 2.20.54 | 2,393 |
| `passage_aug_dla_2_3_7` | Augustine, De Libero Arbitrio, 2.3.7 | 1,778 |
| `passage_aug_dla_2_3_8` | Augustine, De Libero Arbitrio, 2.3.8 | 2,075 |
| `passage_aug_dla_2_3_9` | Augustine, De Libero Arbitrio, 2.3.9 | 3,369 |
| `passage_aug_dla_2_4_10` | Augustine, De Libero Arbitrio, 2.4.10 | 1,697 |
| `passage_aug_dla_2_5_11` | Augustine, De Libero Arbitrio, 2.5.11 | 1,129 |
| `passage_aug_dla_2_5_12` | Augustine, De Libero Arbitrio, 2.5.12 | 2,806 |
| `passage_aug_dla_2_6_13` | Augustine, De Libero Arbitrio, 2.6.13 | 1,487 |
| `passage_aug_dla_2_6_14` | Augustine, De Libero Arbitrio, 2.6.14 | 1,640 |
| `passage_aug_dla_2_7_15` | Augustine, De Libero Arbitrio, 2.7.15 | 1,243 |
| `passage_aug_dla_2_7_16` | Augustine, De Libero Arbitrio, 2.7.16 | 933 |
| `passage_aug_dla_2_7_17` | Augustine, De Libero Arbitrio, 2.7.17 | 1,615 |
| `passage_aug_dla_2_7_18` | Augustine, De Libero Arbitrio, 2.7.18 | 1,043 |
| `passage_aug_dla_2_7_19` | Augustine, De Libero Arbitrio, 2.7.19 | 2,364 |
| `passage_aug_dla_2_8_20` | Augustine, De Libero Arbitrio, 2.8.20 | 989 |
| `passage_aug_dla_2_8_21` | Augustine, De Libero Arbitrio, 2.8.21 | 1,050 |
| `passage_aug_dla_2_8_22` | Augustine, De Libero Arbitrio, 2.8.22 | 2,278 |
| `passage_aug_dla_2_8_23` | Augustine, De Libero Arbitrio, 2.8.23 | 1,623 |
| `passage_aug_dla_2_8_24` | Augustine, De Libero Arbitrio, 2.8.24 | 969 |
| `passage_aug_dla_2_9_25` | Augustine, De Libero Arbitrio, 2.9.25 | 1,706 |
| `passage_aug_dla_2_9_26` | Augustine, De Libero Arbitrio, 2.9.26 | 1,632 |
| `passage_aug_dla_2_9_27` | Augustine, De Libero Arbitrio, 2.9.27 | 2,714 |
| `passage_aug_dla_3_1_1` | Augustine, De Libero Arbitrio, 3.1.1 | 2,161 |
| `passage_aug_dla_3_1_2` | Augustine, De Libero Arbitrio, 3.1.2 | 2,494 |
| `passage_aug_dla_3_1_3` | Augustine, De Libero Arbitrio, 3.1.3 | 962 |
| `passage_aug_dla_3_10_29` | Augustine, De Libero Arbitrio, 3.10.29 | 1,763 |
| `passage_aug_dla_3_10_30` | Augustine, De Libero Arbitrio, 3.10.30 | 1,186 |
| `passage_aug_dla_3_10_31` | Augustine, De Libero Arbitrio, 3.10.31 | 1,398 |
| `passage_aug_dla_3_11_32` | Augustine, De Libero Arbitrio, 3.11.32 | 1,047 |
| `passage_aug_dla_3_11_33` | Augustine, De Libero Arbitrio, 3.11.33 | 1,258 |
| `passage_aug_dla_3_11_34` | Augustine, De Libero Arbitrio, 3.11.34 | 858 |
| `passage_aug_dla_3_12_35` | Augustine, De Libero Arbitrio, 3.12.35 | 2,277 |
| `passage_aug_dla_3_12_36` | Augustine, De Libero Arbitrio, 3.12.36 | 276 |
| `passage_aug_dla_3_13_36` | Augustine, De Libero Arbitrio, 3.13.36 | 1,091 |
| `passage_aug_dla_3_13_37` | Augustine, De Libero Arbitrio, 3.13.37 | 1,331 |
| `passage_aug_dla_3_13_38` | Augustine, De Libero Arbitrio, 3.13.38 | 1,425 |
| `passage_aug_dla_3_14_39` | Augustine, De Libero Arbitrio, 3.14.39 | 1,176 |
| `passage_aug_dla_3_14_40` | Augustine, De Libero Arbitrio, 3.14.40 | 1,635 |
| `passage_aug_dla_3_14_41` | Augustine, De Libero Arbitrio, 3.14.41 | 890 |
| `passage_aug_dla_3_15_42` | Augustine, De Libero Arbitrio, 3.15.42 | 1,901 |
| `passage_aug_dla_3_15_43` | Augustine, De Libero Arbitrio, 3.15.43 | 1,203 |
| `passage_aug_dla_3_15_44` | Augustine, De Libero Arbitrio, 3.15.44 | 1,252 |
| `passage_aug_dla_3_16_45` | Augustine, De Libero Arbitrio, 3.16.45 | 961 |
| `passage_aug_dla_3_16_46` | Augustine, De Libero Arbitrio, 3.16.46 | 1,930 |
| `passage_aug_dla_3_17_47` | Augustine, De Libero Arbitrio, 3.17.47 | 921 |
| `passage_aug_dla_3_17_48` | Augustine, De Libero Arbitrio, 3.17.48 | 1,610 |
| `passage_aug_dla_3_17_49` | Augustine, De Libero Arbitrio, 3.17.49 | 635 |
| `passage_aug_dla_3_18_50` | Augustine, De Libero Arbitrio, 3.18.50 | 628 |
| `passage_aug_dla_3_18_51` | Augustine, De Libero Arbitrio, 3.18.51 | 2,273 |
| `passage_aug_dla_3_18_52` | Augustine, De Libero Arbitrio, 3.18.52 | 1,034 |
| `passage_aug_dla_3_19_53` | Augustine, De Libero Arbitrio, 3.19.53 | 1,308 |
| `passage_aug_dla_3_19_54` | Augustine, De Libero Arbitrio, 3.19.54 | 1,086 |
| `passage_aug_dla_3_2_4` | Augustine, De Libero Arbitrio, 3.2.4 | 916 |
| `passage_aug_dla_3_2_5` | Augustine, De Libero Arbitrio, 3.2.5 | 2,148 |
| `passage_aug_dla_3_20_55` | Augustine, De Libero Arbitrio, 3.20.55 | 997 |
| `passage_aug_dla_3_20_56` | Augustine, De Libero Arbitrio, 3.20.56 | 2,099 |
| `passage_aug_dla_3_20_57` | Augustine, De Libero Arbitrio, 3.20.57 | 2,039 |
| `passage_aug_dla_3_20_58` | Augustine, De Libero Arbitrio, 3.20.58 | 978 |
| `passage_aug_dla_3_21_59` | Augustine, De Libero Arbitrio, 3.21.59 | 1,173 |
| `passage_aug_dla_3_21_60` | Augustine, De Libero Arbitrio, 3.21.60 | 2,843 |
| `passage_aug_dla_3_21_61` | Augustine, De Libero Arbitrio, 3.21.61 | 2,099 |
| `passage_aug_dla_3_21_62` | Augustine, De Libero Arbitrio, 3.21.62 | 808 |
| `passage_aug_dla_3_22_63` | Augustine, De Libero Arbitrio, 3.22.63 | 484 |
| `passage_aug_dla_3_22_64` | Augustine, De Libero Arbitrio, 3.22.64 | 1,599 |
| `passage_aug_dla_3_22_65` | Augustine, De Libero Arbitrio, 3.22.65 | 1,923 |
| `passage_aug_dla_3_23_66` | Augustine, De Libero Arbitrio, 3.23.66 | 890 |
| `passage_aug_dla_3_23_67` | Augustine, De Libero Arbitrio, 3.23.67 | 825 |
| `passage_aug_dla_3_23_68` | Augustine, De Libero Arbitrio, 3.23.68 | 1,439 |
| `passage_aug_dla_3_23_69` | Augustine, De Libero Arbitrio, 3.23.69 | 1,687 |
| `passage_aug_dla_3_23_70` | Augustine, De Libero Arbitrio, 3.23.70 | 1,345 |
| `passage_aug_dla_3_24_71` | Augustine, De Libero Arbitrio, 3.24.71 | 1,550 |
| `passage_aug_dla_3_24_72` | Augustine, De Libero Arbitrio, 3.24.72 | 2,851 |
| `passage_aug_dla_3_24_73` | Augustine, De Libero Arbitrio, 3.24.73 | 1,591 |
| `passage_aug_dla_3_25_74` | Augustine, De Libero Arbitrio, 3.25.74 | 923 |
| `passage_aug_dla_3_25_75` | Augustine, De Libero Arbitrio, 3.25.75 | 1,285 |
| `passage_aug_dla_3_25_76` | Augustine, De Libero Arbitrio, 3.25.76 | 1,617 |
| `passage_aug_dla_3_25_77` | Augustine, De Libero Arbitrio, 3.25.77 | 1,644 |
| `passage_aug_dla_3_3_6` | Augustine, De Libero Arbitrio, 3.3.6 | 2,284 |
| `passage_aug_dla_3_3_7` | Augustine, De Libero Arbitrio, 3.3.7 | 1,832 |
| `passage_aug_dla_3_3_8` | Augustine, De Libero Arbitrio, 3.3.8 | 2,196 |
| `passage_aug_dla_3_4_10` | Augustine, De Libero Arbitrio, 3.4.10 | 1,015 |
| `passage_aug_dla_3_4_11` | Augustine, De Libero Arbitrio, 3.4.11 | 993 |
| `passage_aug_dla_3_4_9` | Augustine, De Libero Arbitrio, 3.4.9 | 669 |
| `passage_aug_dla_3_5_12` | Augustine, De Libero Arbitrio, 3.5.12 | 1,095 |
| `passage_aug_dla_3_5_13` | Augustine, De Libero Arbitrio, 3.5.13 | 2,411 |
| `passage_aug_dla_3_5_14` | Augustine, De Libero Arbitrio, 3.5.14 | 1,353 |
| `passage_aug_dla_3_5_15` | Augustine, De Libero Arbitrio, 3.5.15 | 1,478 |
| `passage_aug_dla_3_5_16` | Augustine, De Libero Arbitrio, 3.5.16 | 1,451 |
| `passage_aug_dla_3_5_17` | Augustine, De Libero Arbitrio, 3.5.17 | 1,284 |
| `passage_aug_dla_3_6_18` | Augustine, De Libero Arbitrio, 3.6.18 | 1,022 |
| `passage_aug_dla_3_6_19` | Augustine, De Libero Arbitrio, 3.6.19 | 1,325 |
| `passage_aug_dla_3_7_20` | Augustine, De Libero Arbitrio, 3.7.20 | 1,145 |
| `passage_aug_dla_3_7_21` | Augustine, De Libero Arbitrio, 3.7.21 | 1,811 |
| `passage_aug_dla_3_8_22` | Augustine, De Libero Arbitrio, 3.8.22 | 1,279 |
| `passage_aug_dla_3_8_23` | Augustine, De Libero Arbitrio, 3.8.23 | 2,057 |
| `passage_aug_dla_3_9_24` | Augustine, De Libero Arbitrio, 3.9.24 | 1,580 |
| `passage_aug_dla_3_9_25` | Augustine, De Libero Arbitrio, 3.9.25 | 1,355 |
| `passage_aug_dla_3_9_26` | Augustine, De Libero Arbitrio, 3.9.26 | 1,542 |
| `passage_aug_dla_3_9_27` | Augustine, De Libero Arbitrio, 3.9.27 | 1,493 |
| `passage_aug_dla_3_9_28` | Augustine, De Libero Arbitrio, 3.9.28 | 2,515 |

### Augustine — De Civitate Dei (Books V, XII, XIV - Fate and Free Will)

- **Language:** Latin
- **Passages:** 158
- **Characters:** 243,027
- **Canonical ID:** `urn:cts:latinLit:stoa0040.stoa001:v-xii-xiv`

| node_id | label | chars |
|---------|-------|-------|
| `passage_aug_civ_v_i` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.I.1 | 3,172 |
| `passage_aug_civ_v_ii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.II.1 | 2,630 |
| `passage_aug_civ_v_iii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.III.1 | 1,518 |
| `passage_aug_civ_v_iv` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.IV.1 | 1,271 |
| `passage_aug_civ_v_ix` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.IX.1 | 1,971 |
| `passage_aug_civ_v_ix_s16` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.IX.2 | 2,418 |
| `passage_aug_civ_v_ix_s17` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.IX.3 | 1,578 |
| `passage_aug_civ_v_ix_s18` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.IX.4 | 3,788 |
| `passage_aug_civ_v_pr` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.Pr.1 | 578 |
| `passage_aug_civ_v_v` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.V.1 | 4,018 |
| `passage_aug_civ_v_vi` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.VI.1 | 2,273 |
| `passage_aug_civ_v_vii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.VII.1 | 3,207 |
| `passage_aug_civ_v_viii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.VIII.1 | 712 |
| `passage_aug_civ_v_viii_s10` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.VIII.2 | 168 |
| `passage_aug_civ_v_viii_s11` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.VIII.3 | 227 |
| `passage_aug_civ_v_viii_s12` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.VIII.4 | 128 |
| `passage_aug_civ_v_viii_s13` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.VIII.5 | 43 |
| `passage_aug_civ_v_viii_s14` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.VIII.6 | 471 |
| `passage_aug_civ_v_x` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.X.1 | 2,277 |
| `passage_aug_civ_v_x_s20` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.X.2 | 1,451 |
| `passage_aug_civ_v_xi` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XI.1 | 1,400 |
| `passage_aug_civ_v_xii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XII.1 | 2,021 |
| `passage_aug_civ_v_xii_s23` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XII.2 | 786 |
| `passage_aug_civ_v_xii_s24` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XII.3 | 89 |
| `passage_aug_civ_v_xii_s25` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XII.4 | 303 |
| `passage_aug_civ_v_xii_s26` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XII.5 | 243 |
| `passage_aug_civ_v_xii_s27` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XII.6 | 483 |
| `passage_aug_civ_v_xii_s28` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XII.7 | 296 |
| `passage_aug_civ_v_xii_s29` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XII.8 | 1,439 |
| `passage_aug_civ_v_xii_s30` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XII.9 | 853 |
| `passage_aug_civ_v_xii_s31` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XII.10 | 1,023 |
| `passage_aug_civ_v_xii_s32` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XII.11 | 2,083 |
| `passage_aug_civ_v_xiii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XIII.1 | 602 |
| `passage_aug_civ_v_xiii_s34` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XIII.2 | 47 |
| `passage_aug_civ_v_xiii_s35` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XIII.3 | 116 |
| `passage_aug_civ_v_xiii_s36` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XIII.4 | 95 |
| `passage_aug_civ_v_xiii_s37` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XIII.5 | 1,023 |
| `passage_aug_civ_v_xiv` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XIV.1 | 3,033 |
| `passage_aug_civ_v_xix` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XIX.1 | 2,608 |
| `passage_aug_civ_v_xix_s50` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XIX.2 | 1,507 |
| `passage_aug_civ_v_xv` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XV.1 | 1,104 |
| `passage_aug_civ_v_xvi` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XVI.1 | 918 |
| `passage_aug_civ_v_xvii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XVII.1 | 1,083 |
| `passage_aug_civ_v_xvii_s42` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XVII.2 | 1,699 |
| `passage_aug_civ_v_xviii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XVIII.1 | 797 |
| `passage_aug_civ_v_xviii_s44` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XVIII.2 | 74 |
| `passage_aug_civ_v_xviii_s45` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XVIII.3 | 87 |
| `passage_aug_civ_v_xviii_s46` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XVIII.4 | 568 |
| `passage_aug_civ_v_xviii_s47` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XVIII.5 | 5,782 |
| `passage_aug_civ_v_xviii_s48` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XVIII.6 | 1,379 |
| `passage_aug_civ_v_xx` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XX.1 | 2,473 |
| `passage_aug_civ_v_xxi` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XXI.1 | 1,966 |
| `passage_aug_civ_v_xxii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XXII.1 | 2,387 |
| `passage_aug_civ_v_xxiv` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XXIV.1 | 1,690 |
| `passage_aug_civ_v_xxv` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XXV.1 | 1,376 |
| `passage_aug_civ_v_xxvi` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XXVI.1 | 1,599 |
| `passage_aug_civ_v_xxvi_s58` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XXVI.2 | 41 |
| `passage_aug_civ_v_xxvi_s59` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XXVI.3 | 2,155 |
| `passage_aug_civ_v_xxvi_s60` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XXVI.4 | 1,858 |
| `passage_aug_civ_v_xxvi_s61` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XXVI.5 | 61 |
| `passage_aug_civ_v_xxxiii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), V.XXXIII.1 | 2,526 |
| `passage_aug_civ_xii_i` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.I.1 | 583 |
| `passage_aug_civ_xii_i_s63` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.I.2 | 1,480 |
| `passage_aug_civ_xii_i_s64` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.I.3 | 2,203 |
| `passage_aug_civ_xii_ii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.II.1 | 1,234 |
| `passage_aug_civ_xii_iii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.III.1 | 2,150 |
| `passage_aug_civ_xii_iv` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.IV.1 | 2,605 |
| `passage_aug_civ_xii_ix` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.IX.1 | 2,025 |
| `passage_aug_civ_xii_ix_s73` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.IX.2 | 2,178 |
| `passage_aug_civ_xii_v` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.V.1 | 934 |
| `passage_aug_civ_xii_vi` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.VI.1 | 5,777 |
| `passage_aug_civ_xii_vii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.VII.1 | 1,209 |
| `passage_aug_civ_xii_viii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.VIII.1 | 1,385 |
| `passage_aug_civ_xii_x` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.X.1 | 1,087 |
| `passage_aug_civ_xii_xi` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.XI.1 | 2,207 |
| `passage_aug_civ_xii_xii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.XII.1 | 734 |
| `passage_aug_civ_xii_xiii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.XIII.1 | 3,251 |
| `passage_aug_civ_xii_xiv` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.XIV.1 | 1,167 |
| `passage_aug_civ_xii_xiv_s79` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.XIV.2 | 2,224 |
| `passage_aug_civ_xii_xix` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.XIX.1 | 2,405 |
| `passage_aug_civ_xii_xv` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.XV.1 | 1,684 |
| `passage_aug_civ_xii_xvi` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.XVI.1 | 2,781 |
| `passage_aug_civ_xii_xvi_s82` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.XVI.2 | 2,535 |
| `passage_aug_civ_xii_xvi_s83` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.XVI.3 | 1,349 |
| `passage_aug_civ_xii_xvii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.XVII.1 | 898 |
| `passage_aug_civ_xii_xviii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.XVIII.1 | 1,908 |
| `passage_aug_civ_xii_xviii_s86` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.XVIII.2 | 2,154 |
| `passage_aug_civ_xii_xx` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.XX.1 | 1,752 |
| `passage_aug_civ_xii_xxi` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.XXI.1 | 1,754 |
| `passage_aug_civ_xii_xxi_s90` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.XXI.2 | 1,435 |
| `passage_aug_civ_xii_xxi_s91` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.XXI.3 | 3,368 |
| `passage_aug_civ_xii_xxi_s92` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.XXI.4 | 1,139 |
| `passage_aug_civ_xii_xxii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.XXII.1 | 1,565 |
| `passage_aug_civ_xii_xxiii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.XXIII.1 | 820 |
| `passage_aug_civ_xii_xxiv` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.XXIV.1 | 1,343 |
| `passage_aug_civ_xii_xxv` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.XXV.1 | 4,516 |
| `passage_aug_civ_xii_xxvii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.XXVII.1 | 1,885 |
| `passage_aug_civ_xii_xxviii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.XXVIII. | 1,364 |
| `passage_aug_civ_xii_xxviii_s100` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.XXVIII. | 61 |
| `passage_aug_civ_xii_xxviii_s99` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XII.XXVIII. | 513 |
| `passage_aug_civ_xiv_i` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.I.1 | 1,246 |
| `passage_aug_civ_xiv_ii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.II.1 | 1,915 |
| `passage_aug_civ_xiv_ii_s103` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.II.2 | 2,179 |
| `passage_aug_civ_xiv_iii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.III.1 | 1,212 |
| `passage_aug_civ_xiv_iii_s105` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.III.2 | 91 |
| `passage_aug_civ_xiv_iii_s106` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.III.3 | 41 |
| `passage_aug_civ_xiv_iii_s107` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.III.4 | 44 |
| `passage_aug_civ_xiv_iii_s108` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.III.5 | 251 |
| `passage_aug_civ_xiv_iii_s109` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.III.6 | 43 |
| `passage_aug_civ_xiv_iii_s110` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.III.7 | 1,798 |
| `passage_aug_civ_xiv_iv` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.IV.1 | 1,483 |
| `passage_aug_civ_xiv_iv_s112` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.IV.2 | 2,285 |
| `passage_aug_civ_xiv_ix` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.IX.1 | 1,857 |
| `passage_aug_civ_xiv_ix_s128` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.IX.2 | 1,528 |
| `passage_aug_civ_xiv_ix_s129` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.IX.3 | 1,006 |
| `passage_aug_civ_xiv_ix_s130` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.IX.4 | 2,212 |
| `passage_aug_civ_xiv_ix_s131` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.IX.5 | 2,849 |
| `passage_aug_civ_xiv_v` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.V.1 | 1,325 |
| `passage_aug_civ_xiv_v_s114` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.V.2 | 96 |
| `passage_aug_civ_xiv_v_s115` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.V.3 | 937 |
| `passage_aug_civ_xiv_vi` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.VI.1 | 1,294 |
| `passage_aug_civ_xiv_vii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.VII.1 | 1,103 |
| `passage_aug_civ_xiv_vii_s118` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.VII.2 | 2,505 |
| `passage_aug_civ_xiv_viii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.VIII.1 | 2,109 |
| `passage_aug_civ_xiv_viii_s120` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.VIII.2 | 1,743 |
| `passage_aug_civ_xiv_viii_s121` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.VIII.3 | 165 |
| `passage_aug_civ_xiv_viii_s122` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.VIII.4 | 76 |
| `passage_aug_civ_xiv_viii_s123` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.VIII.5 | 196 |
| `passage_aug_civ_xiv_viii_s124` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.VIII.6 | 43 |
| `passage_aug_civ_xiv_viii_s125` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.VIII.7 | 24 |
| `passage_aug_civ_xiv_viii_s126` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.VIII.8 | 1,697 |
| `passage_aug_civ_xiv_x` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.X.1 | 2,252 |
| `passage_aug_civ_xiv_xi` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.XI.1 | 2,743 |
| `passage_aug_civ_xiv_xi_s134` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.XI.2 | 2,895 |
| `passage_aug_civ_xiv_xii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.XII.1 | 1,247 |
| `passage_aug_civ_xiv_xiii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.XIII.1 | 3,216 |
| `passage_aug_civ_xiv_xiii_s137` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.XIII.2 | 1,652 |
| `passage_aug_civ_xiv_xiv` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.XIV.1 | 780 |
| `passage_aug_civ_xiv_xix` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.XIX.1 | 2,100 |
| `passage_aug_civ_xiv_xv` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.XV.1 | 1,751 |
| `passage_aug_civ_xiv_xv_s140` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.XV.2 | 3,039 |
| `passage_aug_civ_xiv_xvi` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.XVI.1 | 1,603 |
| `passage_aug_civ_xiv_xvii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.XVII.1 | 2,929 |
| `passage_aug_civ_xiv_xviii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.XVIII.1 | 1,637 |
| `passage_aug_civ_xiv_xx` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.XX.1 | 3,607 |
| `passage_aug_civ_xiv_xxii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.XXII.1 | 2,044 |
| `passage_aug_civ_xiv_xxiii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.XXIII.1 | 644 |
| `passage_aug_civ_xiv_xxiii_s148` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.XXIII.2 | 2,206 |
| `passage_aug_civ_xiv_xxiii_s149` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.XXIII.3 | 1,747 |
| `passage_aug_civ_xiv_xxiv` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.XXIV.1 | 1,400 |
| `passage_aug_civ_xiv_xxiv_s151` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.XXIV.2 | 2,279 |
| `passage_aug_civ_xiv_xxv` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.XXV.1 | 868 |
| `passage_aug_civ_xiv_xxv_s153` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.XXV.2 | 37 |
| `passage_aug_civ_xiv_xxv_s154` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.XXV.3 | 478 |
| `passage_aug_civ_xiv_xxvi` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.XXVI.1 | 3,581 |
| `passage_aug_civ_xiv_xxvii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.XXVII.1 | 2,085 |
| `passage_aug_civ_xiv_xxviii` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.XXVIII. | 1,559 |
| `passage_aug_civ_xiv_xxviii_s158` | Augustine, De Civitate Dei (Books V, XII, XIV - Fate and Free Will), XIV.XXVIII. | 61 |

### Aristotle — τὰ Μετὰ τὰ Φυσικά

- **Language:** Greek
- **Passages:** 142
- **Characters:** 439,507
- **Canonical ID:** `oga:tlg0086.tlg025.perseus-grc2`

| node_id | label | chars |
|---------|-------|-------|
| `passage_arist_met_1_1` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 1.1 | 4,545 |
| `passage_arist_met_1_10` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 1.10 | 917 |
| `passage_arist_met_1_2` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 1.2 | 4,694 |
| `passage_arist_met_1_3` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 1.3 | 5,482 |
| `passage_arist_met_1_4` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 1.4 | 3,680 |
| `passage_arist_met_1_5` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 1.5 | 6,012 |
| `passage_arist_met_1_6` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 1.6 | 3,146 |
| `passage_arist_met_1_7` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 1.7 | 2,213 |
| `passage_arist_met_1_8` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 1.8 | 6,378 |
| `passage_arist_met_1_9` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 1.9 | 9,811 |
| `passage_arist_met_10_1` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 10.1 | 5,655 |
| `passage_arist_met_10_10` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 10.10 | 1,428 |
| `passage_arist_met_10_2` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 10.2 | 2,610 |
| `passage_arist_met_10_3` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 10.3 | 2,948 |
| `passage_arist_met_10_4` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 10.4 | 3,634 |
| `passage_arist_met_10_5` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 10.5 | 2,582 |
| `passage_arist_met_10_6` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 10.6 | 2,776 |
| `passage_arist_met_10_7` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 10.7 | 3,058 |
| `passage_arist_met_10_8` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 10.8 | 1,802 |
| `passage_arist_met_10_9` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 10.9 | 1,940 |
| `passage_arist_met_11_1` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 11.1 | 3,543 |
| `passage_arist_met_11_10` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 11.10 | 4,247 |
| `passage_arist_met_11_11` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 11.11 | 2,401 |
| `passage_arist_met_11_12` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 11.12 | 4,225 |
| `passage_arist_met_11_2` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 11.2 | 3,652 |
| `passage_arist_met_11_3` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 11.3 | 3,347 |
| `passage_arist_met_11_4` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 11.4 | 886 |
| `passage_arist_met_11_5` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 11.5 | 2,789 |
| `passage_arist_met_11_6` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 11.6 | 5,451 |
| `passage_arist_met_11_7` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 11.7 | 2,946 |
| `passage_arist_met_11_8` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 11.8 | 3,489 |
| `passage_arist_met_11_9` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 11.9 | 3,746 |
| `passage_arist_met_12_1` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 12.1 | 1,350 |
| `passage_arist_met_12_10` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 12.10 | 3,958 |
| `passage_arist_met_12_2` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 12.2 | 1,486 |
| `passage_arist_met_12_3` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 12.3 | 1,699 |
| `passage_arist_met_12_4` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 12.4 | 2,278 |
| `passage_arist_met_12_5` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 12.5 | 2,168 |
| `passage_arist_met_12_6` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 12.6 | 2,895 |
| `passage_arist_met_12_7` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 12.7 | 3,644 |
| `passage_arist_met_12_8` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 12.8 | 6,360 |
| `passage_arist_met_12_9` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 12.9 | 1,933 |
| `passage_arist_met_13_1` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 13.1 | 1,645 |
| `passage_arist_met_13_10` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 13.10 | 2,686 |
| `passage_arist_met_13_2` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 13.2 | 5,166 |
| `passage_arist_met_13_3` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 13.3 | 3,403 |
| `passage_arist_met_13_4` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 13.4 | 4,197 |
| `passage_arist_met_13_5` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 13.5 | 1,944 |
| `passage_arist_met_13_6` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 13.6 | 3,413 |
| `passage_arist_met_13_7` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 13.7 | 8,210 |
| `passage_arist_met_13_8` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 13.8 | 8,317 |
| `passage_arist_met_13_9` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 13.9 | 6,696 |
| `passage_arist_met_14_1` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 14.1 | 5,295 |
| `passage_arist_met_14_2` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 14.2 | 6,141 |
| `passage_arist_met_14_3` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 14.3 | 4,507 |
| `passage_arist_met_14_4` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 14.4 | 3,359 |
| `passage_arist_met_14_5` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 14.5 | 2,908 |
| `passage_arist_met_14_6` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 14.6 | 3,788 |
| `passage_arist_met_2_1` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 2.1 | 1,816 |
| `passage_arist_met_2_2` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 2.2 | 3,621 |
| `passage_arist_met_2_3` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 2.3 | 1,134 |
| `passage_arist_met_3_1` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 3.1 | 3,666 |
| `passage_arist_met_3_2` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 3.2 | 7,980 |
| `passage_arist_met_3_3` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 3.3 | 3,746 |
| `passage_arist_met_3_4` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 3.4 | 9,234 |
| `passage_arist_met_3_5` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 3.5 | 2,845 |
| `passage_arist_met_3_6` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 3.6 | 2,134 |
| `passage_arist_met_4_1` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 4.1 | 595 |
| `passage_arist_met_4_2` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 4.2 | 6,879 |
| `passage_arist_met_4_3` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 4.3 | 2,772 |
| `passage_arist_met_4_4` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 4.4 | 11,770 |
| `passage_arist_met_4_5` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 4.5 | 8,078 |
| `passage_arist_met_4_6` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 4.6 | 3,000 |
| `passage_arist_met_4_7` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 4.7 | 2,242 |
| `passage_arist_met_4_8` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 4.8 | 2,068 |
| `passage_arist_met_5_1` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.1 | 1,315 |
| `passage_arist_met_5_10` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.10 | 1,453 |
| `passage_arist_met_5_11` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.11 | 2,461 |
| `passage_arist_met_5_12` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.12 | 3,383 |
| `passage_arist_met_5_13` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.13 | 1,409 |
| `passage_arist_met_5_14` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.14 | 1,532 |
| `passage_arist_met_5_15` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.15 | 3,005 |
| `passage_arist_met_5_16` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.16 | 1,376 |
| `passage_arist_met_5_17` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.17 | 525 |
| `passage_arist_met_5_18` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.18 | 1,237 |
| `passage_arist_met_5_19` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.19 | 143 |
| `passage_arist_met_5_2` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.2 | 3,989 |
| `passage_arist_met_5_20` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.20 | 606 |
| `passage_arist_met_5_21` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.21 | 352 |
| `passage_arist_met_5_22` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.22 | 1,142 |
| `passage_arist_met_5_23` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.23 | 931 |
| `passage_arist_met_5_24` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.24 | 1,198 |
| `passage_arist_met_5_25` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.25 | 761 |
| `passage_arist_met_5_26` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.26 | 1,157 |
| `passage_arist_met_5_27` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.27 | 992 |
| `passage_arist_met_5_28` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.28 | 1,312 |
| `passage_arist_met_5_29` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.29 | 1,743 |
| `passage_arist_met_5_3` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.3 | 1,423 |
| `passage_arist_met_5_30` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.30 | 1,133 |
| `passage_arist_met_5_4` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.4 | 2,211 |
| `passage_arist_met_5_5` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.5 | 1,706 |
| `passage_arist_met_5_6` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.6 | 5,476 |
| `passage_arist_met_5_7` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.7 | 2,054 |
| `passage_arist_met_5_8` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.8 | 904 |
| `passage_arist_met_5_9` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 5.9 | 1,519 |
| `passage_arist_met_6_1` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 6.1 | 3,575 |
| `passage_arist_met_6_2` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 6.2 | 3,868 |
| `passage_arist_met_6_3` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 6.3 | 1,202 |
| `passage_arist_met_6_4` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 6.4 | 1,273 |
| `passage_arist_met_7_1` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 7.1 | 1,949 |
| `passage_arist_met_7_10` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 7.10 | 5,992 |
| `passage_arist_met_7_11` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 7.11 | 4,628 |
| `passage_arist_met_7_12` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 7.12 | 3,348 |
| `passage_arist_met_7_13` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 7.13 | 3,213 |
| `passage_arist_met_7_14` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 7.14 | 1,608 |
| `passage_arist_met_7_15` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 7.15 | 2,893 |
| `passage_arist_met_7_16` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 7.16 | 1,874 |
| `passage_arist_met_7_17` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 7.17 | 3,387 |
| `passage_arist_met_7_2` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 7.2 | 1,393 |
| `passage_arist_met_7_3` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 7.3 | 2,727 |
| `passage_arist_met_7_4` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 7.4 | 4,056 |
| `passage_arist_met_7_5` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 7.5 | 2,030 |
| `passage_arist_met_7_6` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 7.6 | 3,408 |
| `passage_arist_met_7_7` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 7.7 | 4,263 |
| `passage_arist_met_7_8` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 7.8 | 3,014 |
| `passage_arist_met_7_9` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 7.9 | 2,488 |
| `passage_arist_met_8_1` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 8.1 | 2,277 |
| `passage_arist_met_8_2` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 8.2 | 3,108 |
| `passage_arist_met_8_3` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 8.3 | 3,461 |
| `passage_arist_met_8_4` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 8.4 | 2,251 |
| `passage_arist_met_8_5` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 8.5 | 1,167 |
| `passage_arist_met_8_6` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 8.6 | 2,941 |
| `passage_arist_met_9_1` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 9.1 | 2,404 |
| `passage_arist_met_9_10` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 9.10 | 2,682 |
| `passage_arist_met_9_2` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 9.2 | 1,567 |
| `passage_arist_met_9_3` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 9.3 | 2,502 |
| `passage_arist_met_9_4` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 9.4 | 1,527 |
| `passage_arist_met_9_5` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 9.5 | 1,540 |
| `passage_arist_met_9_6` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 9.6 | 2,673 |
| `passage_arist_met_9_7` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 9.7 | 2,142 |
| `passage_arist_met_9_8` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 9.8 | 5,979 |
| `passage_arist_met_9_9` | Aristotle, τὰ Μετὰ τὰ Φυσικά, 9.9 | 1,590 |

### Boethius d. 524 — De consolatione philosophiae

- **Language:** Latin
- **Passages:** 129
- **Characters:** 182,051
- **Canonical ID:** `urn:cts:latinLit:phi2089.phi002`

| node_id | label | chars |
|---------|-------|-------|
| `passage_boeth_cons_1` | Boethius d. 524, De consolatione philosophiae, Cons. 1 | 1,305 |
| `passage_boeth_cons_10` | Boethius d. 524, De consolatione philosophiae, Cons. 10 | 1,410 |
| `passage_boeth_cons_100` | Boethius d. 524, De consolatione philosophiae, Cons. 100 | 1,486 |
| `passage_boeth_cons_101` | Boethius d. 524, De consolatione philosophiae, Cons. 101 | 1,496 |
| `passage_boeth_cons_102` | Boethius d. 524, De consolatione philosophiae, Cons. 102 | 1,465 |
| `passage_boeth_cons_103` | Boethius d. 524, De consolatione philosophiae, Cons. 103 | 1,460 |
| `passage_boeth_cons_104` | Boethius d. 524, De consolatione philosophiae, Cons. 104 | 1,482 |
| `passage_boeth_cons_105` | Boethius d. 524, De consolatione philosophiae, Cons. 105 | 1,463 |
| `passage_boeth_cons_106` | Boethius d. 524, De consolatione philosophiae, Cons. 106 | 1,378 |
| `passage_boeth_cons_107` | Boethius d. 524, De consolatione philosophiae, Cons. 107 | 1,483 |
| `passage_boeth_cons_108` | Boethius d. 524, De consolatione philosophiae, Cons. 108 | 1,495 |
| `passage_boeth_cons_109` | Boethius d. 524, De consolatione philosophiae, Cons. 109 | 1,444 |
| `passage_boeth_cons_11` | Boethius d. 524, De consolatione philosophiae, Cons. 11 | 1,491 |
| `passage_boeth_cons_110` | Boethius d. 524, De consolatione philosophiae, Cons. 110 | 1,393 |
| `passage_boeth_cons_111` | Boethius d. 524, De consolatione philosophiae, Cons. 111 | 1,348 |
| `passage_boeth_cons_112` | Boethius d. 524, De consolatione philosophiae, Cons. 112 | 1,478 |
| `passage_boeth_cons_113` | Boethius d. 524, De consolatione philosophiae, Cons. 113 | 1,201 |
| `passage_boeth_cons_114` | Boethius d. 524, De consolatione philosophiae, Cons. 114 | 1,381 |
| `passage_boeth_cons_115` | Boethius d. 524, De consolatione philosophiae, Cons. 115 | 1,445 |
| `passage_boeth_cons_116` | Boethius d. 524, De consolatione philosophiae, Cons. 116 | 1,493 |
| `passage_boeth_cons_117` | Boethius d. 524, De consolatione philosophiae, Cons. 117 | 1,464 |
| `passage_boeth_cons_118` | Boethius d. 524, De consolatione philosophiae, Cons. 118 | 1,346 |
| `passage_boeth_cons_119` | Boethius d. 524, De consolatione philosophiae, Cons. 119 | 1,385 |
| `passage_boeth_cons_12` | Boethius d. 524, De consolatione philosophiae, Cons. 12 | 1,407 |
| `passage_boeth_cons_120` | Boethius d. 524, De consolatione philosophiae, Cons. 120 | 1,387 |
| `passage_boeth_cons_121` | Boethius d. 524, De consolatione philosophiae, Cons. 121 | 1,314 |
| `passage_boeth_cons_122` | Boethius d. 524, De consolatione philosophiae, Cons. 122 | 1,385 |
| `passage_boeth_cons_123` | Boethius d. 524, De consolatione philosophiae, Cons. 123 | 1,291 |
| `passage_boeth_cons_124` | Boethius d. 524, De consolatione philosophiae, Cons. 124 | 1,497 |
| `passage_boeth_cons_125` | Boethius d. 524, De consolatione philosophiae, Cons. 125 | 1,491 |
| `passage_boeth_cons_126` | Boethius d. 524, De consolatione philosophiae, Cons. 126 | 1,431 |
| `passage_boeth_cons_127` | Boethius d. 524, De consolatione philosophiae, Cons. 127 | 1,275 |
| `passage_boeth_cons_128` | Boethius d. 524, De consolatione philosophiae, Cons. 128 | 1,426 |
| `passage_boeth_cons_129` | Boethius d. 524, De consolatione philosophiae, Cons. 129 | 797 |
| `passage_boeth_cons_13` | Boethius d. 524, De consolatione philosophiae, Cons. 13 | 1,395 |
| `passage_boeth_cons_14` | Boethius d. 524, De consolatione philosophiae, Cons. 14 | 1,355 |
| `passage_boeth_cons_15` | Boethius d. 524, De consolatione philosophiae, Cons. 15 | 1,414 |
| `passage_boeth_cons_16` | Boethius d. 524, De consolatione philosophiae, Cons. 16 | 1,428 |
| `passage_boeth_cons_17` | Boethius d. 524, De consolatione philosophiae, Cons. 17 | 1,340 |
| `passage_boeth_cons_18` | Boethius d. 524, De consolatione philosophiae, Cons. 18 | 1,478 |
| `passage_boeth_cons_19` | Boethius d. 524, De consolatione philosophiae, Cons. 19 | 1,458 |
| `passage_boeth_cons_2` | Boethius d. 524, De consolatione philosophiae, Cons. 2 | 1,353 |
| `passage_boeth_cons_20` | Boethius d. 524, De consolatione philosophiae, Cons. 20 | 1,455 |
| `passage_boeth_cons_21` | Boethius d. 524, De consolatione philosophiae, Cons. 21 | 1,429 |
| `passage_boeth_cons_22` | Boethius d. 524, De consolatione philosophiae, Cons. 22 | 1,398 |
| `passage_boeth_cons_23` | Boethius d. 524, De consolatione philosophiae, Cons. 23 | 1,398 |
| `passage_boeth_cons_24` | Boethius d. 524, De consolatione philosophiae, Cons. 24 | 1,480 |
| `passage_boeth_cons_25` | Boethius d. 524, De consolatione philosophiae, Cons. 25 | 1,486 |
| `passage_boeth_cons_26` | Boethius d. 524, De consolatione philosophiae, Cons. 26 | 1,441 |
| `passage_boeth_cons_27` | Boethius d. 524, De consolatione philosophiae, Cons. 27 | 1,426 |
| `passage_boeth_cons_28` | Boethius d. 524, De consolatione philosophiae, Cons. 28 | 1,478 |
| `passage_boeth_cons_29` | Boethius d. 524, De consolatione philosophiae, Cons. 29 | 1,470 |
| `passage_boeth_cons_3` | Boethius d. 524, De consolatione philosophiae, Cons. 3 | 1,282 |
| `passage_boeth_cons_30` | Boethius d. 524, De consolatione philosophiae, Cons. 30 | 1,439 |
| `passage_boeth_cons_31` | Boethius d. 524, De consolatione philosophiae, Cons. 31 | 1,440 |
| `passage_boeth_cons_32` | Boethius d. 524, De consolatione philosophiae, Cons. 32 | 1,487 |
| `passage_boeth_cons_33` | Boethius d. 524, De consolatione philosophiae, Cons. 33 | 1,454 |
| `passage_boeth_cons_34` | Boethius d. 524, De consolatione philosophiae, Cons. 34 | 1,294 |
| `passage_boeth_cons_35` | Boethius d. 524, De consolatione philosophiae, Cons. 35 | 1,482 |
| `passage_boeth_cons_36` | Boethius d. 524, De consolatione philosophiae, Cons. 36 | 1,416 |
| `passage_boeth_cons_37` | Boethius d. 524, De consolatione philosophiae, Cons. 37 | 1,381 |
| `passage_boeth_cons_38` | Boethius d. 524, De consolatione philosophiae, Cons. 38 | 1,422 |
| `passage_boeth_cons_39` | Boethius d. 524, De consolatione philosophiae, Cons. 39 | 1,351 |
| `passage_boeth_cons_4` | Boethius d. 524, De consolatione philosophiae, Cons. 4 | 1,392 |
| `passage_boeth_cons_40` | Boethius d. 524, De consolatione philosophiae, Cons. 40 | 1,337 |
| `passage_boeth_cons_41` | Boethius d. 524, De consolatione philosophiae, Cons. 41 | 1,337 |
| `passage_boeth_cons_42` | Boethius d. 524, De consolatione philosophiae, Cons. 42 | 1,455 |
| `passage_boeth_cons_43` | Boethius d. 524, De consolatione philosophiae, Cons. 43 | 1,391 |
| `passage_boeth_cons_44` | Boethius d. 524, De consolatione philosophiae, Cons. 44 | 1,494 |
| `passage_boeth_cons_45` | Boethius d. 524, De consolatione philosophiae, Cons. 45 | 1,455 |
| `passage_boeth_cons_46` | Boethius d. 524, De consolatione philosophiae, Cons. 46 | 1,443 |
| `passage_boeth_cons_47` | Boethius d. 524, De consolatione philosophiae, Cons. 47 | 1,477 |
| `passage_boeth_cons_48` | Boethius d. 524, De consolatione philosophiae, Cons. 48 | 1,346 |
| `passage_boeth_cons_49` | Boethius d. 524, De consolatione philosophiae, Cons. 49 | 1,396 |
| `passage_boeth_cons_5` | Boethius d. 524, De consolatione philosophiae, Cons. 5 | 1,450 |
| `passage_boeth_cons_50` | Boethius d. 524, De consolatione philosophiae, Cons. 50 | 1,460 |
| `passage_boeth_cons_51` | Boethius d. 524, De consolatione philosophiae, Cons. 51 | 1,466 |
| `passage_boeth_cons_52` | Boethius d. 524, De consolatione philosophiae, Cons. 52 | 1,285 |
| `passage_boeth_cons_53` | Boethius d. 524, De consolatione philosophiae, Cons. 53 | 1,380 |
| `passage_boeth_cons_54` | Boethius d. 524, De consolatione philosophiae, Cons. 54 | 1,280 |
| `passage_boeth_cons_55` | Boethius d. 524, De consolatione philosophiae, Cons. 55 | 1,463 |
| `passage_boeth_cons_56` | Boethius d. 524, De consolatione philosophiae, Cons. 56 | 1,481 |
| `passage_boeth_cons_57` | Boethius d. 524, De consolatione philosophiae, Cons. 57 | 1,385 |
| `passage_boeth_cons_58` | Boethius d. 524, De consolatione philosophiae, Cons. 58 | 1,359 |
| `passage_boeth_cons_59` | Boethius d. 524, De consolatione philosophiae, Cons. 59 | 1,453 |
| `passage_boeth_cons_6` | Boethius d. 524, De consolatione philosophiae, Cons. 6 | 1,469 |
| `passage_boeth_cons_60` | Boethius d. 524, De consolatione philosophiae, Cons. 60 | 1,165 |
| `passage_boeth_cons_61` | Boethius d. 524, De consolatione philosophiae, Cons. 61 | 1,488 |
| `passage_boeth_cons_62` | Boethius d. 524, De consolatione philosophiae, Cons. 62 | 1,332 |
| `passage_boeth_cons_63` | Boethius d. 524, De consolatione philosophiae, Cons. 63 | 1,474 |
| `passage_boeth_cons_64` | Boethius d. 524, De consolatione philosophiae, Cons. 64 | 1,500 |
| `passage_boeth_cons_65` | Boethius d. 524, De consolatione philosophiae, Cons. 65 | 1,482 |
| `passage_boeth_cons_66` | Boethius d. 524, De consolatione philosophiae, Cons. 66 | 1,476 |
| `passage_boeth_cons_67` | Boethius d. 524, De consolatione philosophiae, Cons. 67 | 1,498 |
| `passage_boeth_cons_68` | Boethius d. 524, De consolatione philosophiae, Cons. 68 | 1,437 |
| `passage_boeth_cons_69` | Boethius d. 524, De consolatione philosophiae, Cons. 69 | 1,481 |
| `passage_boeth_cons_7` | Boethius d. 524, De consolatione philosophiae, Cons. 7 | 1,478 |
| `passage_boeth_cons_70` | Boethius d. 524, De consolatione philosophiae, Cons. 70 | 1,495 |
| `passage_boeth_cons_71` | Boethius d. 524, De consolatione philosophiae, Cons. 71 | 1,442 |
| `passage_boeth_cons_72` | Boethius d. 524, De consolatione philosophiae, Cons. 72 | 1,432 |
| `passage_boeth_cons_73` | Boethius d. 524, De consolatione philosophiae, Cons. 73 | 1,392 |
| `passage_boeth_cons_74` | Boethius d. 524, De consolatione philosophiae, Cons. 74 | 1,403 |
| `passage_boeth_cons_75` | Boethius d. 524, De consolatione philosophiae, Cons. 75 | 1,394 |
| `passage_boeth_cons_76` | Boethius d. 524, De consolatione philosophiae, Cons. 76 | 1,363 |
| `passage_boeth_cons_77` | Boethius d. 524, De consolatione philosophiae, Cons. 77 | 1,179 |
| `passage_boeth_cons_78` | Boethius d. 524, De consolatione philosophiae, Cons. 78 | 1,470 |
| `passage_boeth_cons_79` | Boethius d. 524, De consolatione philosophiae, Cons. 79 | 1,462 |
| `passage_boeth_cons_8` | Boethius d. 524, De consolatione philosophiae, Cons. 8 | 1,283 |
| `passage_boeth_cons_80` | Boethius d. 524, De consolatione philosophiae, Cons. 80 | 1,488 |
| `passage_boeth_cons_81` | Boethius d. 524, De consolatione philosophiae, Cons. 81 | 1,312 |
| `passage_boeth_cons_82` | Boethius d. 524, De consolatione philosophiae, Cons. 82 | 1,485 |
| `passage_boeth_cons_83` | Boethius d. 524, De consolatione philosophiae, Cons. 83 | 1,369 |
| `passage_boeth_cons_84` | Boethius d. 524, De consolatione philosophiae, Cons. 84 | 1,470 |
| `passage_boeth_cons_85` | Boethius d. 524, De consolatione philosophiae, Cons. 85 | 1,454 |
| `passage_boeth_cons_86` | Boethius d. 524, De consolatione philosophiae, Cons. 86 | 1,399 |
| `passage_boeth_cons_87` | Boethius d. 524, De consolatione philosophiae, Cons. 87 | 1,455 |
| `passage_boeth_cons_88` | Boethius d. 524, De consolatione philosophiae, Cons. 88 | 1,269 |
| `passage_boeth_cons_89` | Boethius d. 524, De consolatione philosophiae, Cons. 89 | 1,364 |
| `passage_boeth_cons_9` | Boethius d. 524, De consolatione philosophiae, Cons. 9 | 1,451 |
| `passage_boeth_cons_90` | Boethius d. 524, De consolatione philosophiae, Cons. 90 | 1,404 |
| `passage_boeth_cons_91` | Boethius d. 524, De consolatione philosophiae, Cons. 91 | 1,484 |
| `passage_boeth_cons_92` | Boethius d. 524, De consolatione philosophiae, Cons. 92 | 1,410 |
| `passage_boeth_cons_93` | Boethius d. 524, De consolatione philosophiae, Cons. 93 | 1,417 |
| `passage_boeth_cons_94` | Boethius d. 524, De consolatione philosophiae, Cons. 94 | 1,460 |
| `passage_boeth_cons_95` | Boethius d. 524, De consolatione philosophiae, Cons. 95 | 1,497 |
| `passage_boeth_cons_96` | Boethius d. 524, De consolatione philosophiae, Cons. 96 | 1,384 |
| `passage_boeth_cons_97` | Boethius d. 524, De consolatione philosophiae, Cons. 97 | 1,453 |
| `passage_boeth_cons_98` | Boethius d. 524, De consolatione philosophiae, Cons. 98 | 1,395 |
| `passage_boeth_cons_99` | Boethius d. 524, De consolatione philosophiae, Cons. 99 | 1,428 |

### Plato — Ἀπολογία Σωκράτους

- **Language:** Greek
- **Passages:** 125
- **Characters:** 52,378
- **Canonical ID:** `urn:cts:greekLit:tlg0059.tlg002`

| node_id | label | chars |
|---------|-------|-------|
| `passage_plato_apol_17a` | Plato, Ἀπολογία Σωκράτους, 17a | 326 |
| `passage_plato_apol_17b` | Plato, Ἀπολογία Σωκράτους, 17b | 501 |
| `passage_plato_apol_17c` | Plato, Ἀπολογία Σωκράτους, 17c | 486 |
| `passage_plato_apol_17d` | Plato, Ἀπολογία Σωκράτους, 17d | 272 |
| `passage_plato_apol_18a` | Plato, Ἀπολογία Σωκράτους, 18a | 451 |
| `passage_plato_apol_18b` | Plato, Ἀπολογία Σωκράτους, 18b | 436 |
| `passage_plato_apol_18c` | Plato, Ἀπολογία Σωκράτους, 18c | 447 |
| `passage_plato_apol_18d` | Plato, Ἀπολογία Σωκράτους, 18d | 495 |
| `passage_plato_apol_18e` | Plato, Ἀπολογία Σωκράτους, 18e | 229 |
| `passage_plato_apol_19a` | Plato, Ἀπολογία Σωκράτους, 19a | 393 |
| `passage_plato_apol_19b` | Plato, Ἀπολογία Σωκράτους, 19b | 276 |
| `passage_plato_apol_19c` | Plato, Ἀπολογία Σωκράτους, 19c | 444 |
| `passage_plato_apol_19d` | Plato, Ἀπολογία Σωκράτους, 19d | 455 |
| `passage_plato_apol_19e` | Plato, Ἀπολογία Σωκράτους, 19e | 340 |
| `passage_plato_apol_20a` | Plato, Ἀπολογία Σωκράτους, 20a | 429 |
| `passage_plato_apol_20b` | Plato, Ἀπολογία Σωκράτους, 20b | 484 |
| `passage_plato_apol_20c` | Plato, Ἀπολογία Σωκράτους, 20c | 437 |
| `passage_plato_apol_20d` | Plato, Ἀπολογία Σωκράτους, 20d | 487 |
| `passage_plato_apol_20e` | Plato, Ἀπολογία Σωκράτους, 20e | 447 |
| `passage_plato_apol_21a` | Plato, Ἀπολογία Σωκράτους, 21a | 439 |
| `passage_plato_apol_21b` | Plato, Ἀπολογία Σωκράτους, 21b | 472 |
| `passage_plato_apol_21c` | Plato, Ἀπολογία Σωκράτους, 21c | 446 |
| `passage_plato_apol_21d` | Plato, Ἀπολογία Σωκράτους, 21d | 450 |
| `passage_plato_apol_21e` | Plato, Ἀπολογία Σωκράτους, 21e | 292 |
| `passage_plato_apol_22a` | Plato, Ἀπολογία Σωκράτους, 22a | 489 |
| `passage_plato_apol_22b` | Plato, Ἀπολογία Σωκράτους, 22b | 478 |
| `passage_plato_apol_22c` | Plato, Ἀπολογία Σωκράτους, 22c | 431 |
| `passage_plato_apol_22d` | Plato, Ἀπολογία Σωκράτους, 22d | 432 |
| `passage_plato_apol_22e` | Plato, Ἀπολογία Σωκράτους, 22e | 313 |
| `passage_plato_apol_23a` | Plato, Ἀπολογία Σωκράτους, 23a | 439 |
| `passage_plato_apol_23b` | Plato, Ἀπολογία Σωκράτους, 23b | 486 |
| `passage_plato_apol_23c` | Plato, Ἀπολογία Σωκράτους, 23c | 429 |
| `passage_plato_apol_23d` | Plato, Ἀπολογία Σωκράτους, 23d | 478 |
| `passage_plato_apol_23e` | Plato, Ἀπολογία Σωκράτους, 23e | 269 |
| `passage_plato_apol_24a` | Plato, Ἀπολογία Σωκράτους, 24a | 437 |
| `passage_plato_apol_24b` | Plato, Ἀπολογία Σωκράτους, 24b | 436 |
| `passage_plato_apol_24c` | Plato, Ἀπολογία Σωκράτους, 24c | 473 |
| `passage_plato_apol_24d` | Plato, Ἀπολογία Σωκράτους, 24d | 500 |
| `passage_plato_apol_24e` | Plato, Ἀπολογία Σωκράτους, 24e | 379 |
| `passage_plato_apol_25a` | Plato, Ἀπολογία Σωκράτους, 25a | 421 |
| `passage_plato_apol_25b` | Plato, Ἀπολογία Σωκράτους, 25b | 446 |
| `passage_plato_apol_25c` | Plato, Ἀπολογία Σωκράτους, 25c | 424 |
| `passage_plato_apol_25d` | Plato, Ἀπολογία Σωκράτους, 25d | 454 |
| `passage_plato_apol_25e` | Plato, Ἀπολογία Σωκράτους, 25e | 328 |
| `passage_plato_apol_26a` | Plato, Ἀπολογία Σωκράτους, 26a | 417 |
| `passage_plato_apol_26b` | Plato, Ἀπολογία Σωκράτους, 26b | 443 |
| `passage_plato_apol_26c` | Plato, Ἀπολογία Σωκράτους, 26c | 380 |
| `passage_plato_apol_26d` | Plato, Ἀπολογία Σωκράτους, 26d | 478 |
| `passage_plato_apol_26e` | Plato, Ἀπολογία Σωκράτους, 26e | 424 |
| `passage_plato_apol_27a` | Plato, Ἀπολογία Σωκράτους, 27a | 454 |
| `passage_plato_apol_27b` | Plato, Ἀπολογία Σωκράτους, 27b | 485 |
| `passage_plato_apol_27c` | Plato, Ἀπολογία Σωκράτους, 27c | 463 |
| `passage_plato_apol_27d` | Plato, Ἀπολογία Σωκράτους, 27d | 463 |
| `passage_plato_apol_27e` | Plato, Ἀπολογία Σωκράτους, 27e | 386 |
| `passage_plato_apol_28a` | Plato, Ἀπολογία Σωκράτους, 28a | 439 |
| `passage_plato_apol_28b` | Plato, Ἀπολογία Σωκράτους, 28b | 470 |
| `passage_plato_apol_28c` | Plato, Ἀπολογία Σωκράτους, 28c | 485 |
| `passage_plato_apol_28d` | Plato, Ἀπολογία Σωκράτους, 28d | 493 |
| `passage_plato_apol_28e` | Plato, Ἀπολογία Σωκράτους, 28e | 353 |
| `passage_plato_apol_29a` | Plato, Ἀπολογία Σωκράτους, 29a | 454 |
| `passage_plato_apol_29b` | Plato, Ἀπολογία Σωκράτους, 29b | 520 |
| `passage_plato_apol_29c` | Plato, Ἀπολογία Σωκράτους, 29c | 439 |
| `passage_plato_apol_29d` | Plato, Ἀπολογία Σωκράτους, 29d | 497 |
| `passage_plato_apol_29e` | Plato, Ἀπολογία Σωκράτους, 29e | 279 |
| `passage_plato_apol_30a` | Plato, Ἀπολογία Σωκράτους, 30a | 448 |
| `passage_plato_apol_30b` | Plato, Ἀπολογία Σωκράτους, 30b | 432 |
| `passage_plato_apol_30c` | Plato, Ἀπολογία Σωκράτους, 30c | 492 |
| `passage_plato_apol_30d` | Plato, Ἀπολογία Σωκράτους, 30d | 395 |
| `passage_plato_apol_30e` | Plato, Ἀπολογία Σωκράτους, 30e | 387 |
| `passage_plato_apol_31a` | Plato, Ἀπολογία Σωκράτους, 31a | 452 |
| `passage_plato_apol_31b` | Plato, Ἀπολογία Σωκράτους, 31b | 479 |
| `passage_plato_apol_31c` | Plato, Ἀπολογία Σωκράτους, 31c | 408 |
| `passage_plato_apol_31d` | Plato, Ἀπολογία Σωκράτους, 31d | 438 |
| `passage_plato_apol_31e` | Plato, Ἀπολογία Σωκράτους, 31e | 218 |
| `passage_plato_apol_32a` | Plato, Ἀπολογία Σωκράτους, 32a | 450 |
| `passage_plato_apol_32b` | Plato, Ἀπολογία Σωκράτους, 32b | 438 |
| `passage_plato_apol_32c` | Plato, Ἀπολογία Σωκράτους, 32c | 448 |
| `passage_plato_apol_32d` | Plato, Ἀπολογία Σωκράτους, 32d | 444 |
| `passage_plato_apol_32e` | Plato, Ἀπολογία Σωκράτους, 32e | 256 |
| `passage_plato_apol_33a` | Plato, Ἀπολογία Σωκράτους, 33a | 450 |
| `passage_plato_apol_33b` | Plato, Ἀπολογία Σωκράτους, 33b | 441 |
| `passage_plato_apol_33c` | Plato, Ἀπολογία Σωκράτους, 33c | 453 |
| `passage_plato_apol_33d` | Plato, Ἀπολογία Σωκράτους, 33d | 495 |
| `passage_plato_apol_33e` | Plato, Ἀπολογία Σωκράτους, 33e | 379 |
| `passage_plato_apol_34a` | Plato, Ἀπολογία Σωκράτους, 34a | 443 |
| `passage_plato_apol_34b` | Plato, Ἀπολογία Σωκράτους, 34b | 373 |
| `passage_plato_apol_34c` | Plato, Ἀπολογία Σωκράτους, 34c | 448 |
| `passage_plato_apol_34d` | Plato, Ἀπολογία Σωκράτους, 34d | 503 |
| `passage_plato_apol_34e` | Plato, Ἀπολογία Σωκράτους, 34e | 291 |
| `passage_plato_apol_35a` | Plato, Ἀπολογία Σωκράτους, 35a | 448 |
| `passage_plato_apol_35b` | Plato, Ἀπολογία Σωκράτους, 35b | 495 |
| `passage_plato_apol_35c` | Plato, Ἀπολογία Σωκράτους, 35c | 453 |
| `passage_plato_apol_35d` | Plato, Ἀπολογία Σωκράτους, 35d | 452 |
| `passage_plato_apol_35e` | Plato, Ἀπολογία Σωκράτους, 35e | 50 |
| `passage_plato_apol_36a` | Plato, Ἀπολογία Σωκράτους, 36a | 481 |
| `passage_plato_apol_36b` | Plato, Ἀπολογία Σωκράτους, 36b | 442 |
| `passage_plato_apol_36c` | Plato, Ἀπολογία Σωκράτους, 36c | 443 |
| `passage_plato_apol_36d` | Plato, Ἀπολογία Σωκράτους, 36d | 502 |
| `passage_plato_apol_36e` | Plato, Ἀπολογία Σωκράτους, 36e | 109 |
| `passage_plato_apol_37a` | Plato, Ἀπολογία Σωκράτους, 37a | 419 |
| `passage_plato_apol_37b` | Plato, Ἀπολογία Σωκράτους, 37b | 448 |
| `passage_plato_apol_37c` | Plato, Ἀπολογία Σωκράτους, 37c | 438 |
| `passage_plato_apol_37d` | Plato, Ἀπολογία Σωκράτους, 37d | 447 |
| `passage_plato_apol_37e` | Plato, Ἀπολογία Σωκράτους, 37e | 290 |
| `passage_plato_apol_38a` | Plato, Ἀπολογία Σωκράτους, 38a | 446 |
| `passage_plato_apol_38b` | Plato, Ἀπολογία Σωκράτους, 38b | 484 |
| `passage_plato_apol_38c` | Plato, Ἀπολογία Σωκράτους, 38c | 382 |
| `passage_plato_apol_38d` | Plato, Ἀπολογία Σωκράτους, 38d | 477 |
| `passage_plato_apol_38e` | Plato, Ἀπολογία Σωκράτους, 38e | 335 |
| `passage_plato_apol_39a` | Plato, Ἀπολογία Σωκράτους, 39a | 401 |
| `passage_plato_apol_39b` | Plato, Ἀπολογία Σωκράτους, 39b | 395 |
| `passage_plato_apol_39c` | Plato, Ἀπολογία Σωκράτους, 39c | 440 |
| `passage_plato_apol_39d` | Plato, Ἀπολογία Σωκράτους, 39d | 486 |
| `passage_plato_apol_39e` | Plato, Ἀπολογία Σωκράτους, 39e | 273 |
| `passage_plato_apol_40a` | Plato, Ἀπολογία Σωκράτους, 40a | 437 |
| `passage_plato_apol_40b` | Plato, Ἀπολογία Σωκράτους, 40b | 447 |
| `passage_plato_apol_40c` | Plato, Ἀπολογία Σωκράτους, 40c | 488 |
| `passage_plato_apol_40d` | Plato, Ἀπολογία Σωκράτους, 40d | 453 |
| `passage_plato_apol_40e` | Plato, Ἀπολογία Σωκράτους, 40e | 370 |
| `passage_plato_apol_41a` | Plato, Ἀπολογία Σωκράτους, 41a | 431 |
| `passage_plato_apol_41b` | Plato, Ἀπολογία Σωκράτους, 41b | 455 |
| `passage_plato_apol_41c` | Plato, Ἀπολογία Σωκράτους, 41c | 464 |
| `passage_plato_apol_41d` | Plato, Ἀπολογία Σωκράτους, 41d | 443 |
| `passage_plato_apol_41e` | Plato, Ἀπολογία Σωκράτους, 41e | 380 |
| `passage_plato_apol_42a` | Plato, Ἀπολογία Σωκράτους, 42a | 215 |

### Aristotle — Ἠθικὰ Νικομάχεια

- **Language:** Greek
- **Passages:** 116
- **Characters:** 331,590
- **Canonical ID:** `oga:tlg0086.tlg010.perseus-grc2`

| node_id | label | chars |
|---------|-------|-------|
| `passage_arist_ne_1_1` | Aristotle, Ἠθικὰ Νικομάχεια, 1.1 | 950 |
| `passage_arist_ne_1_10` | Aristotle, Ἠθικὰ Νικομάχεια, 1.10 | 4,509 |
| `passage_arist_ne_1_11` | Aristotle, Ἠθικὰ Νικομάχεια, 1.11 | 1,244 |
| `passage_arist_ne_1_12` | Aristotle, Ἠθικὰ Νικομάχεια, 1.12 | 1,666 |
| `passage_arist_ne_1_13` | Aristotle, Ἠθικὰ Νικομάχεια, 1.13 | 4,108 |
| `passage_arist_ne_1_2` | Aristotle, Ἠθικὰ Νικομάχεια, 1.2 | 1,192 |
| `passage_arist_ne_1_3` | Aristotle, Ἠθικὰ Νικομάχεια, 1.3 | 1,667 |
| `passage_arist_ne_1_4` | Aristotle, Ἠθικὰ Νικομάχεια, 1.4 | 1,772 |
| `passage_arist_ne_1_5` | Aristotle, Ἠθικὰ Νικομάχεια, 1.5 | 1,649 |
| `passage_arist_ne_1_6` | Aristotle, Ἠθικὰ Νικομάχεια, 1.6 | 4,056 |
| `passage_arist_ne_1_7` | Aristotle, Ἠθικὰ Νικομάχεια, 1.7 | 5,342 |
| `passage_arist_ne_1_8` | Aristotle, Ἠθικὰ Νικομάχεια, 1.8 | 3,630 |
| `passage_arist_ne_1_9` | Aristotle, Ἠθικὰ Νικομάχεια, 1.9 | 1,927 |
| `passage_arist_ne_10_1` | Aristotle, Ἠθικὰ Νικομάχεια, 10.1 | 1,437 |
| `passage_arist_ne_10_2` | Aristotle, Ἠθικὰ Νικομάχεια, 10.2 | 2,299 |
| `passage_arist_ne_10_3` | Aristotle, Ἠθικὰ Νικομάχεια, 10.3 | 3,847 |
| `passage_arist_ne_10_4` | Aristotle, Ἠθικὰ Νικομάχεια, 10.4 | 4,444 |
| `passage_arist_ne_10_5` | Aristotle, Ἠθικὰ Νικομάχεια, 10.5 | 4,579 |
| `passage_arist_ne_10_6` | Aristotle, Ἠθικὰ Νικομάχεια, 10.6 | 2,906 |
| `passage_arist_ne_10_7` | Aristotle, Ἠθικὰ Νικομάχεια, 10.7 | 3,659 |
| `passage_arist_ne_10_8` | Aristotle, Ἠθικὰ Νικομάχεια, 10.8 | 5,220 |
| `passage_arist_ne_10_9` | Aristotle, Ἠθικὰ Νικομάχεια, 10.9 | 8,742 |
| `passage_arist_ne_2_1` | Aristotle, Ἠθικὰ Νικομάχεια, 2.1 | 2,572 |
| `passage_arist_ne_2_2` | Aristotle, Ἠθικὰ Νικομάχεια, 2.2 | 2,512 |
| `passage_arist_ne_2_3` | Aristotle, Ἠθικὰ Νικομάχεια, 2.3 | 2,577 |
| `passage_arist_ne_2_4` | Aristotle, Ἠθικὰ Νικομάχεια, 2.4 | 1,840 |
| `passage_arist_ne_2_5` | Aristotle, Ἠθικὰ Νικομάχεια, 2.5 | 1,442 |
| `passage_arist_ne_2_6` | Aristotle, Ἠθικὰ Νικομάχεια, 2.6 | 4,538 |
| `passage_arist_ne_2_7` | Aristotle, Ἠθικὰ Νικομάχεια, 2.7 | 4,474 |
| `passage_arist_ne_2_8` | Aristotle, Ἠθικὰ Νικομάχεια, 2.8 | 2,319 |
| `passage_arist_ne_2_9` | Aristotle, Ἠθικὰ Νικομάχεια, 2.9 | 2,334 |
| `passage_arist_ne_3_1` | Aristotle, Ἠθικὰ Νικομάχεια, 3.1 | 5,852 |
| `passage_arist_ne_3_10` | Aristotle, Ἠθικὰ Νικομάχεια, 3.10 | 2,903 |
| `passage_arist_ne_3_11` | Aristotle, Ἠθικὰ Νικομάχεια, 3.11 | 2,534 |
| `passage_arist_ne_3_12` | Aristotle, Ἠθικὰ Νικομάχεια, 3.12 | 1,777 |
| `passage_arist_ne_3_2` | Aristotle, Ἠθικὰ Νικομάχεια, 3.2 | 2,679 |
| `passage_arist_ne_3_3` | Aristotle, Ἠθικὰ Νικομάχεια, 3.3 | 3,520 |
| `passage_arist_ne_3_4` | Aristotle, Ἠθικὰ Νικομάχεια, 3.4 | 1,179 |
| `passage_arist_ne_3_5` | Aristotle, Ἠθικὰ Νικομάχεια, 3.5 | 5,588 |
| `passage_arist_ne_3_6` | Aristotle, Ἠθικὰ Νικομάχεια, 3.6 | 1,901 |
| `passage_arist_ne_3_7` | Aristotle, Ἠθικὰ Νικομάχεια, 3.7 | 2,390 |
| `passage_arist_ne_3_8` | Aristotle, Ἠθικὰ Νικομάχεια, 3.8 | 4,577 |
| `passage_arist_ne_3_9` | Aristotle, Ἠθικὰ Νικομάχεια, 3.9 | 1,564 |
| `passage_arist_ne_4_1` | Aristotle, Ἠθικὰ Νικομάχεια, 4.1 | 9,341 |
| `passage_arist_ne_4_2` | Aristotle, Ἠθικὰ Νικομάχεια, 4.2 | 4,768 |
| `passage_arist_ne_4_3` | Aristotle, Ἠθικὰ Νικομάχεια, 4.3 | 7,472 |
| `passage_arist_ne_4_4` | Aristotle, Ἠθικὰ Νικομάχεια, 4.4 | 1,386 |
| `passage_arist_ne_4_5` | Aristotle, Ἠθικὰ Νικομάχεια, 4.5 | 3,117 |
| `passage_arist_ne_4_6` | Aristotle, Ἠθικὰ Νικομάχεια, 4.6 | 2,109 |
| `passage_arist_ne_4_7` | Aristotle, Ἠθικὰ Νικομάχεια, 4.7 | 3,031 |
| `passage_arist_ne_4_8` | Aristotle, Ἠθικὰ Νικομάχεια, 4.8 | 2,554 |
| `passage_arist_ne_4_9` | Aristotle, Ἠθικὰ Νικομάχεια, 4.9 | 1,466 |
| `passage_arist_ne_5_1` | Aristotle, Ἠθικὰ Νικομάχεια, 5.1 | 4,426 |
| `passage_arist_ne_5_10` | Aristotle, Ἠθικὰ Νικομάχεια, 5.10 | 2,439 |
| `passage_arist_ne_5_11` | Aristotle, Ἠθικὰ Νικομάχεια, 5.11 | 2,535 |
| `passage_arist_ne_5_2` | Aristotle, Ἠθικὰ Νικομάχεια, 5.2 | 3,411 |
| `passage_arist_ne_5_3` | Aristotle, Ἠθικὰ Νικομάχεια, 5.3 | 2,714 |
| `passage_arist_ne_5_4` | Aristotle, Ἠθικὰ Νικομάχεια, 5.4 | 3,506 |
| `passage_arist_ne_5_5` | Aristotle, Ἠθικὰ Νικομάχεια, 5.5 | 5,304 |
| `passage_arist_ne_5_6` | Aristotle, Ἠθικὰ Νικομάχεια, 5.6 | 2,079 |
| `passage_arist_ne_5_7` | Aristotle, Ἠθικὰ Νικομάχεια, 5.7 | 1,804 |
| `passage_arist_ne_5_8` | Aristotle, Ἠθικὰ Νικομάχεια, 5.8 | 3,344 |
| `passage_arist_ne_5_9` | Aristotle, Ἠθικὰ Νικομάχεια, 5.9 | 4,974 |
| `passage_arist_ne_6_1` | Aristotle, Ἠθικὰ Νικομάχεια, 6.1 | 943 |
| `passage_arist_ne_6_10` | Aristotle, Ἠθικὰ Νικομάχεια, 6.10 | 1,031 |
| `passage_arist_ne_6_11` | Aristotle, Ἠθικὰ Νικομάχεια, 6.11 | 1,796 |
| `passage_arist_ne_6_12` | Aristotle, Ἠθικὰ Νικομάχεια, 6.12 | 3,047 |
| `passage_arist_ne_6_13` | Aristotle, Ἠθικὰ Νικομάχεια, 6.13 | 2,545 |
| `passage_arist_ne_6_2` | Aristotle, Ἠθικὰ Νικομάχεια, 6.2 | 2,701 |
| `passage_arist_ne_6_3` | Aristotle, Ἠθικὰ Νικομάχεια, 6.3 | 1,203 |
| `passage_arist_ne_6_4` | Aristotle, Ἠθικὰ Νικομάχεια, 6.4 | 1,209 |
| `passage_arist_ne_6_5` | Aristotle, Ἠθικὰ Νικομάχεια, 6.5 | 2,238 |
| `passage_arist_ne_6_6` | Aristotle, Ἠθικὰ Νικομάχεια, 6.6 | 652 |
| `passage_arist_ne_6_7` | Aristotle, Ἠθικὰ Νικομάχεια, 6.7 | 2,630 |
| `passage_arist_ne_6_8` | Aristotle, Ἠθικὰ Νικομάχεια, 6.8 | 2,234 |
| `passage_arist_ne_6_9` | Aristotle, Ἠθικὰ Νικομάχεια, 6.9 | 2,020 |
| `passage_arist_ne_7_1` | Aristotle, Ἠθικὰ Νικομάχεια, 7.1 | 2,324 |
| `passage_arist_ne_7_10` | Aristotle, Ἠθικὰ Νικομάχεια, 7.10 | 1,609 |
| `passage_arist_ne_7_11` | Aristotle, Ἠθικὰ Νικομάχεια, 7.11 | 1,311 |
| `passage_arist_ne_7_12` | Aristotle, Ἠθικὰ Νικομάχεια, 7.12 | 2,655 |
| `passage_arist_ne_7_13` | Aristotle, Ἠθικὰ Νικομάχεια, 7.13 | 2,297 |
| `passage_arist_ne_7_14` | Aristotle, Ἠθικὰ Νικομάχεια, 7.14 | 3,349 |
| `passage_arist_ne_7_2` | Aristotle, Ἠθικὰ Νικομάχεια, 7.2 | 3,102 |
| `passage_arist_ne_7_3` | Aristotle, Ἠθικὰ Νικομάχεια, 7.3 | 4,406 |
| `passage_arist_ne_7_4` | Aristotle, Ἠθικὰ Νικομάχεια, 7.4 | 3,456 |
| `passage_arist_ne_7_5` | Aristotle, Ἠθικὰ Νικομάχεια, 7.5 | 2,365 |
| `passage_arist_ne_7_6` | Aristotle, Ἠθικὰ Νικομάχεια, 7.6 | 2,957 |
| `passage_arist_ne_7_7` | Aristotle, Ἠθικὰ Νικομάχεια, 7.7 | 3,083 |
| `passage_arist_ne_7_8` | Aristotle, Ἠθικὰ Νικομάχεια, 7.8 | 1,957 |
| `passage_arist_ne_7_9` | Aristotle, Ἠθικὰ Νικομάχεια, 7.9 | 2,580 |
| `passage_arist_ne_8_1` | Aristotle, Ἠθικὰ Νικομάχεια, 8.1 | 2,748 |
| `passage_arist_ne_8_10` | Aristotle, Ἠθικὰ Νικομάχεια, 8.10 | 2,733 |
| `passage_arist_ne_8_11` | Aristotle, Ἠθικὰ Νικομάχεια, 8.11 | 1,963 |
| `passage_arist_ne_8_12` | Aristotle, Ἠθικὰ Νικομάχεια, 8.12 | 3,168 |
| `passage_arist_ne_8_13` | Aristotle, Ἠθικὰ Νικομάχεια, 8.13 | 3,388 |
| `passage_arist_ne_8_14` | Aristotle, Ἠθικὰ Νικομάχεια, 8.14 | 2,160 |
| `passage_arist_ne_8_2` | Aristotle, Ἠθικὰ Νικομάχεια, 8.2 | 1,336 |
| `passage_arist_ne_8_3` | Aristotle, Ἠθικὰ Νικομάχεια, 8.3 | 3,440 |
| `passage_arist_ne_8_4` | Aristotle, Ἠθικὰ Νικομάχεια, 8.4 | 2,350 |
| `passage_arist_ne_8_5` | Aristotle, Ἠθικὰ Νικομάχεια, 8.5 | 1,712 |
| `passage_arist_ne_8_6` | Aristotle, Ἠθικὰ Νικομάχεια, 8.6 | 2,559 |
| `passage_arist_ne_8_7` | Aristotle, Ἠθικὰ Νικομάχεια, 8.7 | 2,059 |
| `passage_arist_ne_8_8` | Aristotle, Ἠθικὰ Νικομάχεια, 8.8 | 2,597 |
| `passage_arist_ne_8_9` | Aristotle, Ἠθικὰ Νικομάχεια, 8.9 | 2,221 |
| `passage_arist_ne_9_1` | Aristotle, Ἠθικὰ Νικομάχεια, 9.1 | 3,285 |
| `passage_arist_ne_9_10` | Aristotle, Ἠθικὰ Νικομάχεια, 9.10 | 1,939 |
| `passage_arist_ne_9_11` | Aristotle, Ἠθικὰ Νικομάχεια, 9.11 | 2,378 |
| `passage_arist_ne_9_12` | Aristotle, Ἠθικὰ Νικομάχεια, 9.12 | 1,216 |
| `passage_arist_ne_9_2` | Aristotle, Ἠθικὰ Νικομάχεια, 9.2 | 2,694 |
| `passage_arist_ne_9_3` | Aristotle, Ἠθικὰ Νικομάχεια, 9.3 | 2,035 |
| `passage_arist_ne_9_4` | Aristotle, Ἠθικὰ Νικομάχεια, 9.4 | 3,466 |
| `passage_arist_ne_9_5` | Aristotle, Ἠθικὰ Νικομάχεια, 9.5 | 1,455 |
| `passage_arist_ne_9_6` | Aristotle, Ἠθικὰ Νικομάχεια, 9.6 | 1,595 |
| `passage_arist_ne_9_7` | Aristotle, Ἠθικὰ Νικομάχεια, 9.7 | 2,524 |
| `passage_arist_ne_9_8` | Aristotle, Ἠθικὰ Νικομάχεια, 9.8 | 4,394 |
| `passage_arist_ne_9_9` | Aristotle, Ἠθικὰ Νικομάχεια, 9.9 | 4,778 |

### Tatian — Oratio ad Graecos

- **Language:** Greek
- **Passages:** 98
- **Characters:** 67,319
- **Canonical ID:** `urn:cts:greekLit:tlg1766.tlg001`

| node_id | label | chars |
|---------|-------|-------|
| `passage_tatian_1_1` | Tatian, Oratio ad Graecos, 1.1 | 706 |
| `passage_tatian_1_2` | Tatian, Oratio ad Graecos, 1.2 | 1,267 |
| `passage_tatian_1_3` | Tatian, Oratio ad Graecos, 1.3 | 71 |
| `passage_tatian_10_1` | Tatian, Oratio ad Graecos, 10.1 | 78 |
| `passage_tatian_10_2` | Tatian, Oratio ad Graecos, 10.2 | 1,030 |
| `passage_tatian_10_3` | Tatian, Oratio ad Graecos, 10.3 | 405 |
| `passage_tatian_11_1` | Tatian, Oratio ad Graecos, 11.1 | 854 |
| `passage_tatian_11_2` | Tatian, Oratio ad Graecos, 11.2 | 514 |
| `passage_tatian_12_1` | Tatian, Oratio ad Graecos, 12.1 | 510 |
| `passage_tatian_12_2` | Tatian, Oratio ad Graecos, 12.2 | 871 |
| `passage_tatian_12_3` | Tatian, Oratio ad Graecos, 12.3 | 1,125 |
| `passage_tatian_12_4` | Tatian, Oratio ad Graecos, 12.4 | 566 |
| `passage_tatian_13_1` | Tatian, Oratio ad Graecos, 13.1 | 490 |
| `passage_tatian_13_2` | Tatian, Oratio ad Graecos, 13.2 | 1,112 |
| `passage_tatian_14_1` | Tatian, Oratio ad Graecos, 14.1 | 788 |
| `passage_tatian_14_2` | Tatian, Oratio ad Graecos, 14.2 | 625 |
| `passage_tatian_15_1` | Tatian, Oratio ad Graecos, 15.1 | 751 |
| `passage_tatian_15_2` | Tatian, Oratio ad Graecos, 15.2 | 1,027 |
| `passage_tatian_15_3` | Tatian, Oratio ad Graecos, 15.3 | 436 |
| `passage_tatian_16_1` | Tatian, Oratio ad Graecos, 16.1 | 660 |
| `passage_tatian_16_2` | Tatian, Oratio ad Graecos, 16.2 | 1,064 |
| `passage_tatian_17_1` | Tatian, Oratio ad Graecos, 17.1 | 877 |
| `passage_tatian_17_2` | Tatian, Oratio ad Graecos, 17.2 | 1,189 |
| `passage_tatian_17_3` | Tatian, Oratio ad Graecos, 17.3 | 398 |
| `passage_tatian_18_1` | Tatian, Oratio ad Graecos, 18.1 | 724 |
| `passage_tatian_18_2` | Tatian, Oratio ad Graecos, 18.2 | 946 |
| `passage_tatian_19_1` | Tatian, Oratio ad Graecos, 19.1 | 1,076 |
| `passage_tatian_19_2` | Tatian, Oratio ad Graecos, 19.2 | 1,039 |
| `passage_tatian_19_3` | Tatian, Oratio ad Graecos, 19.3 | 174 |
| `passage_tatian_2_1` | Tatian, Oratio ad Graecos, 2.1 | 857 |
| `passage_tatian_2_2` | Tatian, Oratio ad Graecos, 2.2 | 375 |
| `passage_tatian_20_1` | Tatian, Oratio ad Graecos, 20.1 | 610 |
| `passage_tatian_20_2` | Tatian, Oratio ad Graecos, 20.2 | 876 |
| `passage_tatian_21_1` | Tatian, Oratio ad Graecos, 21.1 | 359 |
| `passage_tatian_21_2` | Tatian, Oratio ad Graecos, 21.2 | 1,036 |
| `passage_tatian_21_3` | Tatian, Oratio ad Graecos, 21.3 | 667 |
| `passage_tatian_22_1` | Tatian, Oratio ad Graecos, 22.1 | 173 |
| `passage_tatian_22_2` | Tatian, Oratio ad Graecos, 22.2 | 1,307 |
| `passage_tatian_23_1` | Tatian, Oratio ad Graecos, 23.1 | 909 |
| `passage_tatian_23_2` | Tatian, Oratio ad Graecos, 23.2 | 339 |
| `passage_tatian_24_1` | Tatian, Oratio ad Graecos, 24.1 | 549 |
| `passage_tatian_25_1` | Tatian, Oratio ad Graecos, 25.1 | 1,354 |
| `passage_tatian_25_2` | Tatian, Oratio ad Graecos, 25.2 | 211 |
| `passage_tatian_26_1` | Tatian, Oratio ad Graecos, 26.1 | 908 |
| `passage_tatian_26_2` | Tatian, Oratio ad Graecos, 26.2 | 881 |
| `passage_tatian_26_3` | Tatian, Oratio ad Graecos, 26.3 | 309 |
| `passage_tatian_27_1` | Tatian, Oratio ad Graecos, 27.1 | 1,065 |
| `passage_tatian_27_2` | Tatian, Oratio ad Graecos, 27.2 | 509 |
| `passage_tatian_28_1` | Tatian, Oratio ad Graecos, 28.1 | 482 |
| `passage_tatian_29_1` | Tatian, Oratio ad Graecos, 29.1 | 861 |
| `passage_tatian_29_2` | Tatian, Oratio ad Graecos, 29.2 | 263 |
| `passage_tatian_3_1` | Tatian, Oratio ad Graecos, 3.1 | 633 |
| `passage_tatian_3_2` | Tatian, Oratio ad Graecos, 3.2 | 1,166 |
| `passage_tatian_3_3` | Tatian, Oratio ad Graecos, 3.3 | 293 |
| `passage_tatian_30_1` | Tatian, Oratio ad Graecos, 30.1 | 912 |
| `passage_tatian_31_1` | Tatian, Oratio ad Graecos, 31.1 | 1,142 |
| `passage_tatian_31_2` | Tatian, Oratio ad Graecos, 31.2 | 1,124 |
| `passage_tatian_31_3` | Tatian, Oratio ad Graecos, 31.3 | 182 |
| `passage_tatian_32_1` | Tatian, Oratio ad Graecos, 32.1 | 792 |
| `passage_tatian_32_2` | Tatian, Oratio ad Graecos, 32.2 | 704 |
| `passage_tatian_32_3` | Tatian, Oratio ad Graecos, 32.3 | 272 |
| `passage_tatian_33_1` | Tatian, Oratio ad Graecos, 33.1 | 1,100 |
| `passage_tatian_33_2` | Tatian, Oratio ad Graecos, 33.2 | 998 |
| `passage_tatian_33_3` | Tatian, Oratio ad Graecos, 33.3 | 468 |
| `passage_tatian_34_1` | Tatian, Oratio ad Graecos, 34.1 | 531 |
| `passage_tatian_34_2` | Tatian, Oratio ad Graecos, 34.2 | 1,095 |
| `passage_tatian_34_3` | Tatian, Oratio ad Graecos, 34.3 | 336 |
| `passage_tatian_35_1` | Tatian, Oratio ad Graecos, 35.1 | 786 |
| `passage_tatian_35_2` | Tatian, Oratio ad Graecos, 35.2 | 398 |
| `passage_tatian_36_1` | Tatian, Oratio ad Graecos, 36.1 | 597 |
| `passage_tatian_36_2` | Tatian, Oratio ad Graecos, 36.2 | 602 |
| `passage_tatian_37_1` | Tatian, Oratio ad Graecos, 37.1 | 582 |
| `passage_tatian_37_2` | Tatian, Oratio ad Graecos, 37.2 | 123 |
| `passage_tatian_38_1` | Tatian, Oratio ad Graecos, 38.1 | 741 |
| `passage_tatian_39_1` | Tatian, Oratio ad Graecos, 39.1 | 270 |
| `passage_tatian_39_2` | Tatian, Oratio ad Graecos, 39.2 | 992 |
| `passage_tatian_39_3` | Tatian, Oratio ad Graecos, 39.3 | 600 |
| `passage_tatian_4_1` | Tatian, Oratio ad Graecos, 4.1 | 803 |
| `passage_tatian_4_2` | Tatian, Oratio ad Graecos, 4.2 | 564 |
| `passage_tatian_40_1` | Tatian, Oratio ad Graecos, 40.1 | 553 |
| `passage_tatian_40_2` | Tatian, Oratio ad Graecos, 40.2 | 223 |
| `passage_tatian_41_1` | Tatian, Oratio ad Graecos, 41.1 | 844 |
| `passage_tatian_41_2` | Tatian, Oratio ad Graecos, 41.2 | 940 |
| `passage_tatian_41_3` | Tatian, Oratio ad Graecos, 41.3 | 329 |
| `passage_tatian_42_1` | Tatian, Oratio ad Graecos, 42.1 | 369 |
| `passage_tatian_5_1` | Tatian, Oratio ad Graecos, 5.1 | 481 |
| `passage_tatian_5_2` | Tatian, Oratio ad Graecos, 5.2 | 1,014 |
| `passage_tatian_6_1` | Tatian, Oratio ad Graecos, 6.1 | 973 |
| `passage_tatian_6_2` | Tatian, Oratio ad Graecos, 6.2 | 259 |
| `passage_tatian_7_1` | Tatian, Oratio ad Graecos, 7.1 | 765 |
| `passage_tatian_7_2` | Tatian, Oratio ad Graecos, 7.2 | 859 |
| `passage_tatian_8_1` | Tatian, Oratio ad Graecos, 8.1 | 360 |
| `passage_tatian_8_2` | Tatian, Oratio ad Graecos, 8.2 | 86 |
| `passage_tatian_8_3` | Tatian, Oratio ad Graecos, 8.3 | 1,048 |
| `passage_tatian_8_4` | Tatian, Oratio ad Graecos, 8.4 | 994 |
| `passage_tatian_8_5` | Tatian, Oratio ad Graecos, 8.5 | 194 |
| `passage_tatian_9_1` | Tatian, Oratio ad Graecos, 9.1 | 978 |
| `passage_tatian_9_2` | Tatian, Oratio ad Graecos, 9.2 | 971 |

### Methodius — De Libero Arbitrio

- **Language:** Greek
- **Passages:** 97
- **Characters:** 136,997
- **Canonical ID:** `urn:cts:greekLit:tlg2959.tlg001`

| node_id | label | chars |
|---------|-------|-------|
| `passage_meth_dla_1` | Methodius, De Libero Arbitrio, PG 18.1 | 1,331 |
| `passage_meth_dla_10` | Methodius, De Libero Arbitrio, PG 18.10 | 1,494 |
| `passage_meth_dla_100` | Methodius, De Libero Arbitrio, PG 18.100 | 1,062 |
| `passage_meth_dla_101` | Methodius, De Libero Arbitrio, PG 18.101 | 1,357 |
| `passage_meth_dla_102` | Methodius, De Libero Arbitrio, PG 18.102 | 1,329 |
| `passage_meth_dla_103` | Methodius, De Libero Arbitrio, PG 18.103 | 1,462 |
| `passage_meth_dla_104` | Methodius, De Libero Arbitrio, PG 18.104 | 1,448 |
| `passage_meth_dla_105` | Methodius, De Libero Arbitrio, PG 18.105 | 1,365 |
| `passage_meth_dla_106` | Methodius, De Libero Arbitrio, PG 18.106 | 1,486 |
| `passage_meth_dla_107` | Methodius, De Libero Arbitrio, PG 18.107 | 1,156 |
| `passage_meth_dla_11` | Methodius, De Libero Arbitrio, PG 18.11 | 1,473 |
| `passage_meth_dla_12` | Methodius, De Libero Arbitrio, PG 18.12 | 1,455 |
| `passage_meth_dla_13_s13` | Methodius, De Libero Arbitrio, PG 18.13 | 1,356 |
| `passage_meth_dla_14` | Methodius, De Libero Arbitrio, PG 18.14 | 1,332 |
| `passage_meth_dla_15` | Methodius, De Libero Arbitrio, PG 18.15 | 1,499 |
| `passage_meth_dla_16_s16` | Methodius, De Libero Arbitrio, PG 18.16 | 1,331 |
| `passage_meth_dla_17` | Methodius, De Libero Arbitrio, PG 18.17 | 1,404 |
| `passage_meth_dla_18` | Methodius, De Libero Arbitrio, PG 18.18 | 1,470 |
| `passage_meth_dla_19` | Methodius, De Libero Arbitrio, PG 18.19 | 1,405 |
| `passage_meth_dla_2` | Methodius, De Libero Arbitrio, PG 18.2 | 1,336 |
| `passage_meth_dla_20` | Methodius, De Libero Arbitrio, PG 18.20 | 1,317 |
| `passage_meth_dla_21` | Methodius, De Libero Arbitrio, PG 18.21 | 1,478 |
| `passage_meth_dla_22` | Methodius, De Libero Arbitrio, PG 18.22 | 1,442 |
| `passage_meth_dla_23` | Methodius, De Libero Arbitrio, PG 18.23 | 1,381 |
| `passage_meth_dla_24` | Methodius, De Libero Arbitrio, PG 18.24 | 1,425 |
| `passage_meth_dla_25` | Methodius, De Libero Arbitrio, PG 18.25 | 1,453 |
| `passage_meth_dla_26` | Methodius, De Libero Arbitrio, PG 18.26 | 1,441 |
| `passage_meth_dla_27` | Methodius, De Libero Arbitrio, PG 18.27 | 1,498 |
| `passage_meth_dla_28` | Methodius, De Libero Arbitrio, PG 18.28 | 1,479 |
| `passage_meth_dla_29` | Methodius, De Libero Arbitrio, PG 18.29 | 1,462 |
| `passage_meth_dla_3` | Methodius, De Libero Arbitrio, PG 18.3 | 1,475 |
| `passage_meth_dla_30` | Methodius, De Libero Arbitrio, PG 18.30 | 1,419 |
| `passage_meth_dla_31` | Methodius, De Libero Arbitrio, PG 18.31 | 1,383 |
| `passage_meth_dla_32` | Methodius, De Libero Arbitrio, PG 18.32 | 1,453 |
| `passage_meth_dla_33` | Methodius, De Libero Arbitrio, PG 18.33 | 1,489 |
| `passage_meth_dla_34` | Methodius, De Libero Arbitrio, PG 18.34 | 1,405 |
| `passage_meth_dla_35` | Methodius, De Libero Arbitrio, PG 18.35 | 1,498 |
| `passage_meth_dla_36` | Methodius, De Libero Arbitrio, PG 18.36 | 1,449 |
| `passage_meth_dla_37` | Methodius, De Libero Arbitrio, PG 18.37 | 1,450 |
| `passage_meth_dla_38` | Methodius, De Libero Arbitrio, PG 18.38 | 1,406 |
| `passage_meth_dla_39` | Methodius, De Libero Arbitrio, PG 18.39 | 1,435 |
| `passage_meth_dla_4` | Methodius, De Libero Arbitrio, PG 18.4 | 1,336 |
| `passage_meth_dla_40` | Methodius, De Libero Arbitrio, PG 18.40 | 1,422 |
| `passage_meth_dla_41` | Methodius, De Libero Arbitrio, PG 18.41 | 1,404 |
| `passage_meth_dla_42` | Methodius, De Libero Arbitrio, PG 18.42 | 1,386 |
| `passage_meth_dla_43` | Methodius, De Libero Arbitrio, PG 18.43 | 1,390 |
| `passage_meth_dla_44` | Methodius, De Libero Arbitrio, PG 18.44 | 1,400 |
| `passage_meth_dla_45` | Methodius, De Libero Arbitrio, PG 18.45 | 1,438 |
| `passage_meth_dla_46` | Methodius, De Libero Arbitrio, PG 18.46 | 1,488 |
| `passage_meth_dla_47_s47` | Methodius, De Libero Arbitrio, PG 18.47 | 1,441 |
| `passage_meth_dla_48` | Methodius, De Libero Arbitrio, PG 18.48 | 1,397 |
| `passage_meth_dla_49` | Methodius, De Libero Arbitrio, PG 18.49 | 1,416 |
| `passage_meth_dla_5_s5` | Methodius, De Libero Arbitrio, PG 18.5 | 1,274 |
| `passage_meth_dla_50` | Methodius, De Libero Arbitrio, PG 18.50 | 1,484 |
| `passage_meth_dla_51` | Methodius, De Libero Arbitrio, PG 18.51 | 1,442 |
| `passage_meth_dla_52` | Methodius, De Libero Arbitrio, PG 18.52 | 1,387 |
| `passage_meth_dla_53` | Methodius, De Libero Arbitrio, PG 18.53 | 1,469 |
| `passage_meth_dla_54` | Methodius, De Libero Arbitrio, PG 18.54 | 1,493 |
| `passage_meth_dla_55` | Methodius, De Libero Arbitrio, PG 18.55 | 1,406 |
| `passage_meth_dla_56` | Methodius, De Libero Arbitrio, PG 18.56 | 1,415 |
| `passage_meth_dla_57` | Methodius, De Libero Arbitrio, PG 18.57 | 1,389 |
| `passage_meth_dla_58` | Methodius, De Libero Arbitrio, PG 18.58 | 1,476 |
| `passage_meth_dla_59` | Methodius, De Libero Arbitrio, PG 18.59 | 1,476 |
| `passage_meth_dla_6` | Methodius, De Libero Arbitrio, PG 18.6 | 1,499 |
| `passage_meth_dla_60` | Methodius, De Libero Arbitrio, PG 18.60 | 1,246 |
| `passage_meth_dla_61` | Methodius, De Libero Arbitrio, PG 18.61 | 1,495 |
| `passage_meth_dla_62` | Methodius, De Libero Arbitrio, PG 18.62 | 1,359 |
| `passage_meth_dla_65` | Methodius, De Libero Arbitrio, PG 18.65 | 1,358 |
| `passage_meth_dla_66` | Methodius, De Libero Arbitrio, PG 18.66 | 1,420 |
| `passage_meth_dla_67` | Methodius, De Libero Arbitrio, PG 18.67 | 1,494 |
| `passage_meth_dla_68` | Methodius, De Libero Arbitrio, PG 18.68 | 1,496 |
| `passage_meth_dla_69` | Methodius, De Libero Arbitrio, PG 18.69 | 1,477 |
| `passage_meth_dla_7` | Methodius, De Libero Arbitrio, PG 18.7 | 1,304 |
| `passage_meth_dla_70_s70` | Methodius, De Libero Arbitrio, PG 18.70 | 1,490 |
| `passage_meth_dla_71_s71` | Methodius, De Libero Arbitrio, PG 18.71 | 1,423 |
| `passage_meth_dla_72_s72` | Methodius, De Libero Arbitrio, PG 18.72 | 1,480 |
| `passage_meth_dla_73` | Methodius, De Libero Arbitrio, PG 18.73 | 1,352 |
| `passage_meth_dla_74` | Methodius, De Libero Arbitrio, PG 18.74 | 1,498 |
| `passage_meth_dla_75` | Methodius, De Libero Arbitrio, PG 18.75 | 1,493 |
| `passage_meth_dla_76` | Methodius, De Libero Arbitrio, PG 18.76 | 1,250 |
| `passage_meth_dla_77` | Methodius, De Libero Arbitrio, PG 18.77 | 1,404 |
| `passage_meth_dla_78` | Methodius, De Libero Arbitrio, PG 18.78 | 1,465 |
| `passage_meth_dla_8` | Methodius, De Libero Arbitrio, PG 18.8 | 1,269 |
| `passage_meth_dla_80` | Methodius, De Libero Arbitrio, PG 18.80 | 1,282 |
| `passage_meth_dla_81` | Methodius, De Libero Arbitrio, PG 18.81 | 1,446 |
| `passage_meth_dla_83` | Methodius, De Libero Arbitrio, PG 18.83 | 1,436 |
| `passage_meth_dla_84` | Methodius, De Libero Arbitrio, PG 18.84 | 1,221 |
| `passage_meth_dla_85` | Methodius, De Libero Arbitrio, PG 18.85 | 1,457 |
| `passage_meth_dla_86` | Methodius, De Libero Arbitrio, PG 18.86 | 1,305 |
| `passage_meth_dla_87` | Methodius, De Libero Arbitrio, PG 18.87 | 1,420 |
| `passage_meth_dla_88` | Methodius, De Libero Arbitrio, PG 18.88 | 1,475 |
| `passage_meth_dla_89` | Methodius, De Libero Arbitrio, PG 18.89 | 1,443 |
| `passage_meth_dla_9` | Methodius, De Libero Arbitrio, PG 18.9 | 1,468 |
| `passage_meth_dla_91` | Methodius, De Libero Arbitrio, PG 18.91 | 1,388 |
| `passage_meth_dla_94` | Methodius, De Libero Arbitrio, PG 18.94 | 1,482 |
| `passage_meth_dla_95` | Methodius, De Libero Arbitrio, PG 18.95 | 1,450 |
| `passage_meth_dla_98` | Methodius, De Libero Arbitrio, PG 18.98 | 1,434 |

### Plato — Τίμαιος (Timaeus)

- **Language:** Greek
- **Passages:** 76
- **Characters:** 145,208
- **Canonical ID:** `urn:cts:greekLit:tlg0059.tlg031`

| node_id | label | chars |
|---------|-------|-------|
| `passage_plato_tim_17` | Plato, Τίμαιος (Timaeus), 17 | 1,353 |
| `passage_plato_tim_18` | Plato, Τίμαιος (Timaeus), 18 | 1,747 |
| `passage_plato_tim_19` | Plato, Τίμαιος (Timaeus), 19 | 1,995 |
| `passage_plato_tim_20` | Plato, Τίμαιος (Timaeus), 20 | 1,726 |
| `passage_plato_tim_21` | Plato, Τίμαιος (Timaeus), 21 | 2,203 |
| `passage_plato_tim_22` | Plato, Τίμαιος (Timaeus), 22 | 1,909 |
| `passage_plato_tim_23` | Plato, Τίμαιος (Timaeus), 23 | 2,098 |
| `passage_plato_tim_24` | Plato, Τίμαιος (Timaeus), 24 | 1,817 |
| `passage_plato_tim_25` | Plato, Τίμαιος (Timaeus), 25 | 2,027 |
| `passage_plato_tim_26` | Plato, Τίμαιος (Timaeus), 26 | 1,661 |
| `passage_plato_tim_27` | Plato, Τίμαιος (Timaeus), 27 | 1,731 |
| `passage_plato_tim_28` | Plato, Τίμαιος (Timaeus), 28 | 1,139 |
| `passage_plato_tim_29` | Plato, Τίμαιος (Timaeus), 29 | 1,953 |
| `passage_plato_tim_30` | Plato, Τίμαιος (Timaeus), 30 | 1,332 |
| `passage_plato_tim_31` | Plato, Τίμαιος (Timaeus), 31 | 1,208 |
| `passage_plato_tim_32` | Plato, Τίμαιος (Timaeus), 32 | 1,416 |
| `passage_plato_tim_33` | Plato, Τίμαιος (Timaeus), 33 | 1,472 |
| `passage_plato_tim_34` | Plato, Τίμαιος (Timaeus), 34 | 1,234 |
| `passage_plato_tim_35` | Plato, Τίμαιος (Timaeus), 35 | 895 |
| `passage_plato_tim_36` | Plato, Τίμαιος (Timaeus), 36 | 1,948 |
| `passage_plato_tim_37` | Plato, Τίμαιος (Timaeus), 37 | 1,986 |
| `passage_plato_tim_38` | Plato, Τίμαιος (Timaeus), 38 | 1,885 |
| `passage_plato_tim_39` | Plato, Τίμαιος (Timaeus), 39 | 2,239 |
| `passage_plato_tim_40` | Plato, Τίμαιος (Timaeus), 40 | 2,039 |
| `passage_plato_tim_41` | Plato, Τίμαιος (Timaeus), 41 | 2,313 |
| `passage_plato_tim_42` | Plato, Τίμαιος (Timaeus), 42 | 1,538 |
| `passage_plato_tim_43` | Plato, Τίμαιος (Timaeus), 43 | 2,241 |
| `passage_plato_tim_44` | Plato, Τίμαιος (Timaeus), 44 | 1,887 |
| `passage_plato_tim_45` | Plato, Τίμαιος (Timaeus), 45 | 2,058 |
| `passage_plato_tim_46` | Plato, Τίμαιος (Timaeus), 46 | 1,920 |
| `passage_plato_tim_47` | Plato, Τίμαιος (Timaeus), 47 | 1,984 |
| `passage_plato_tim_48` | Plato, Τίμαιος (Timaeus), 48 | 1,742 |
| `passage_plato_tim_49` | Plato, Τίμαιος (Timaeus), 49 | 2,126 |
| `passage_plato_tim_50` | Plato, Τίμαιος (Timaeus), 50 | 2,209 |
| `passage_plato_tim_51` | Plato, Τίμαιος (Timaeus), 51 | 1,906 |
| `passage_plato_tim_52` | Plato, Τίμαιος (Timaeus), 52 | 1,813 |
| `passage_plato_tim_53` | Plato, Τίμαιος (Timaeus), 53 | 2,257 |
| `passage_plato_tim_54` | Plato, Τίμαιος (Timaeus), 54 | 1,843 |
| `passage_plato_tim_55` | Plato, Τίμαιος (Timaeus), 55 | 2,135 |
| `passage_plato_tim_56` | Plato, Τίμαιος (Timaeus), 56 | 1,980 |
| `passage_plato_tim_57` | Plato, Τίμαιος (Timaeus), 57 | 2,056 |
| `passage_plato_tim_58` | Plato, Τίμαιος (Timaeus), 58 | 2,116 |
| `passage_plato_tim_59` | Plato, Τίμαιος (Timaeus), 59 | 1,987 |
| `passage_plato_tim_60` | Plato, Τίμαιος (Timaeus), 60 | 2,180 |
| `passage_plato_tim_61` | Plato, Τίμαιος (Timaeus), 61 | 1,733 |
| `passage_plato_tim_62` | Plato, Τίμαιος (Timaeus), 62 | 2,100 |
| `passage_plato_tim_63` | Plato, Τίμαιος (Timaeus), 63 | 2,027 |
| `passage_plato_tim_64` | Plato, Τίμαιος (Timaeus), 64 | 1,973 |
| `passage_plato_tim_65` | Plato, Τίμαιος (Timaeus), 65 | 1,793 |
| `passage_plato_tim_66` | Plato, Τίμαιος (Timaeus), 66 | 2,043 |
| `passage_plato_tim_67` | Plato, Τίμαιος (Timaeus), 67 | 1,946 |
| `passage_plato_tim_68` | Plato, Τίμαιος (Timaeus), 68 | 2,113 |
| `passage_plato_tim_69` | Plato, Τίμαιος (Timaeus), 69 | 2,026 |
| `passage_plato_tim_70` | Plato, Τίμαιος (Timaeus), 70 | 1,998 |
| `passage_plato_tim_71` | Plato, Τίμαιος (Timaeus), 71 | 2,006 |
| `passage_plato_tim_72` | Plato, Τίμαιος (Timaeus), 72 | 1,889 |
| `passage_plato_tim_73` | Plato, Τίμαιος (Timaeus), 73 | 2,147 |
| `passage_plato_tim_74` | Plato, Τίμαιος (Timaeus), 74 | 2,225 |
| `passage_plato_tim_75` | Plato, Τίμαιος (Timaeus), 75 | 1,862 |
| `passage_plato_tim_76` | Plato, Τίμαιος (Timaeus), 76 | 2,180 |
| `passage_plato_tim_77` | Plato, Τίμαιος (Timaeus), 77 | 2,035 |
| `passage_plato_tim_78` | Plato, Τίμαιος (Timaeus), 78 | 1,959 |
| `passage_plato_tim_79` | Plato, Τίμαιος (Timaeus), 79 | 2,123 |
| `passage_plato_tim_80` | Plato, Τίμαιος (Timaeus), 80 | 1,939 |
| `passage_plato_tim_81` | Plato, Τίμαιος (Timaeus), 81 | 1,981 |
| `passage_plato_tim_82` | Plato, Τίμαιος (Timaeus), 82 | 2,071 |
| `passage_plato_tim_83` | Plato, Τίμαιος (Timaeus), 83 | 1,974 |
| `passage_plato_tim_84` | Plato, Τίμαιος (Timaeus), 84 | 2,189 |
| `passage_plato_tim_85` | Plato, Τίμαιος (Timaeus), 85 | 1,706 |
| `passage_plato_tim_86` | Plato, Τίμαιος (Timaeus), 86 | 2,292 |
| `passage_plato_tim_87` | Plato, Τίμαιος (Timaeus), 87 | 2,038 |
| `passage_plato_tim_88` | Plato, Τίμαιος (Timaeus), 88 | 2,122 |
| `passage_plato_tim_89` | Plato, Τίμαιος (Timaeus), 89 | 1,832 |
| `passage_plato_tim_90` | Plato, Τίμαιος (Timaeus), 90 | 2,235 |
| `passage_plato_tim_91` | Plato, Τίμαιος (Timaeus), 91 | 2,013 |
| `passage_plato_tim_92` | Plato, Τίμαιος (Timaeus), 92 | 1,334 |

### Aristotle — Physica

- **Language:** Greek
- **Passages:** 71
- **Characters:** 451,788
- **Canonical ID:** `oga:tlg0086.tlg031.1st1K-grc1`

| node_id | label | chars |
|---------|-------|-------|
| `passage_arist_phys_1_1` | Aristotle, Physica, 1.1 | 1,734 |
| `passage_arist_phys_1_2` | Aristotle, Physica, 1.2 | 6,854 |
| `passage_arist_phys_1_3` | Aristotle, Physica, 1.3 | 6,309 |
| `passage_arist_phys_1_4` | Aristotle, Physica, 1.4 | 6,535 |
| `passage_arist_phys_1_5` | Aristotle, Physica, 1.5 | 5,481 |
| `passage_arist_phys_1_6` | Aristotle, Physica, 1.6 | 4,468 |
| `passage_arist_phys_1_7` | Aristotle, Physica, 1.7 | 8,393 |
| `passage_arist_phys_1_8` | Aristotle, Physica, 1.8 | 3,931 |
| `passage_arist_phys_1_9` | Aristotle, Physica, 1.9 | 3,397 |
| `passage_arist_phys_2_1` | Aristotle, Physica, 2.1 | 6,980 |
| `passage_arist_phys_2_2` | Aristotle, Physica, 2.2 | 5,278 |
| `passage_arist_phys_2_3` | Aristotle, Physica, 2.3 | 7,032 |
| `passage_arist_phys_2_4` | Aristotle, Physica, 2.4 | 4,209 |
| `passage_arist_phys_2_5` | Aristotle, Physica, 2.5 | 5,078 |
| `passage_arist_phys_2_6` | Aristotle, Physica, 2.6 | 4,053 |
| `passage_arist_phys_2_7` | Aristotle, Physica, 2.7 | 2,666 |
| `passage_arist_phys_2_8` | Aristotle, Physica, 2.8 | 8,158 |
| `passage_arist_phys_2_9` | Aristotle, Physica, 2.9 | 3,670 |
| `passage_arist_phys_3_1` | Aristotle, Physica, 3.1 | 6,004 |
| `passage_arist_phys_3_2` | Aristotle, Physica, 3.2 | 2,673 |
| `passage_arist_phys_3_3` | Aristotle, Physica, 3.3 | 4,463 |
| `passage_arist_phys_3_4` | Aristotle, Physica, 3.4 | 6,783 |
| `passage_arist_phys_3_5` | Aristotle, Physica, 3.5 | 11,743 |
| `passage_arist_phys_3_6` | Aristotle, Physica, 3.6 | 7,451 |
| `passage_arist_phys_3_7` | Aristotle, Physica, 3.7 | 3,535 |
| `passage_arist_phys_3_8` | Aristotle, Physica, 3.8 | 1,517 |
| `passage_arist_phys_4_1` | Aristotle, Physica, 4.1 | 6,243 |
| `passage_arist_phys_4_10` | Aristotle, Physica, 4.10 | 4,681 |
| `passage_arist_phys_4_11` | Aristotle, Physica, 4.11 | 8,428 |
| `passage_arist_phys_4_12` | Aristotle, Physica, 4.12 | 9,671 |
| `passage_arist_phys_4_13` | Aristotle, Physica, 4.13 | 4,330 |
| `passage_arist_phys_4_14` | Aristotle, Physica, 4.14 | 7,089 |
| `passage_arist_phys_4_2` | Aristotle, Physica, 4.2 | 4,257 |
| `passage_arist_phys_4_3` | Aristotle, Physica, 4.3 | 4,137 |
| `passage_arist_phys_4_4` | Aristotle, Physica, 4.4 | 8,594 |
| `passage_arist_phys_4_5` | Aristotle, Physica, 4.5 | 4,012 |
| `passage_arist_phys_4_6` | Aristotle, Physica, 4.6 | 4,292 |
| `passage_arist_phys_4_7` | Aristotle, Physica, 4.7 | 3,912 |
| `passage_arist_phys_4_8` | Aristotle, Physica, 4.8 | 11,786 |
| `passage_arist_phys_4_9` | Aristotle, Physica, 4.9 | 6,284 |
| `passage_arist_phys_5_1` | Aristotle, Physica, 5.1 | 7,737 |
| `passage_arist_phys_5_2` | Aristotle, Physica, 5.2 | 6,789 |
| `passage_arist_phys_5_3` | Aristotle, Physica, 5.3 | 4,393 |
| `passage_arist_phys_5_4` | Aristotle, Physica, 5.4 | 8,177 |
| `passage_arist_phys_5_5` | Aristotle, Physica, 5.5 | 3,905 |
| `passage_arist_phys_5_6` | Aristotle, Physica, 5.6 | 7,276 |
| `passage_arist_phys_6_1` | Aristotle, Physica, 6.1 | 5,196 |
| `passage_arist_phys_6_10` | Aristotle, Physica, 6.10 | 6,267 |
| `passage_arist_phys_6_2` | Aristotle, Physica, 6.2 | 8,826 |
| `passage_arist_phys_6_3` | Aristotle, Physica, 6.3 | 3,847 |
| `passage_arist_phys_6_4` | Aristotle, Physica, 6.4 | 5,465 |
| `passage_arist_phys_6_5` | Aristotle, Physica, 6.5 | 6,912 |
| `passage_arist_phys_6_6` | Aristotle, Physica, 6.6 | 6,122 |
| `passage_arist_phys_6_7` | Aristotle, Physica, 6.7 | 5,577 |
| `passage_arist_phys_6_8` | Aristotle, Physica, 6.8 | 4,364 |
| `passage_arist_phys_6_9` | Aristotle, Physica, 6.9 | 5,540 |
| `passage_arist_phys_7_1` | Aristotle, Physica, 7.1 | 7,004 |
| `passage_arist_phys_7_2` | Aristotle, Physica, 7.2 | 7,480 |
| `passage_arist_phys_7_3` | Aristotle, Physica, 7.3 | 8,116 |
| `passage_arist_phys_7_4` | Aristotle, Physica, 7.4 | 8,249 |
| `passage_arist_phys_7_5` | Aristotle, Physica, 7.5 | 3,375 |
| `passage_arist_phys_8_1` | Aristotle, Physica, 8.1 | 10,774 |
| `passage_arist_phys_8_10` | Aristotle, Physica, 8.10 | 8,899 |
| `passage_arist_phys_8_2` | Aristotle, Physica, 8.2 | 4,003 |
| `passage_arist_phys_8_3` | Aristotle, Physica, 8.3 | 7,646 |
| `passage_arist_phys_8_4` | Aristotle, Physica, 8.4 | 8,247 |
| `passage_arist_phys_8_5` | Aristotle, Physica, 8.5 | 14,868 |
| `passage_arist_phys_8_6` | Aristotle, Physica, 8.6 | 8,913 |
| `passage_arist_phys_8_7` | Aristotle, Physica, 8.7 | 9,073 |
| `passage_arist_phys_8_8` | Aristotle, Physica, 8.8 | 17,563 |
| `passage_arist_phys_8_9` | Aristotle, Physica, 8.9 | 5,074 |

### Justin Martyr — Apologia Prima

- **Language:** Greek
- **Passages:** 68
- **Characters:** 93,258
- **Canonical ID:** `urn:cts:greekLit:tlg0645.tlg001`

| node_id | label | chars |
|---------|-------|-------|
| `passage_just_apol1_1` | Justin Martyr, Apologia Prima, 1 | 425 |
| `passage_just_apol1_10` | Justin Martyr, Apologia Prima, 10 | 1,287 |
| `passage_just_apol1_11` | Justin Martyr, Apologia Prima, 11 | 501 |
| `passage_just_apol1_12` | Justin Martyr, Apologia Prima, 12 | 2,397 |
| `passage_just_apol1_13` | Justin Martyr, Apologia Prima, 13 | 1,199 |
| `passage_just_apol1_14` | Justin Martyr, Apologia Prima, 14 | 1,461 |
| `passage_just_apol1_15` | Justin Martyr, Apologia Prima, 15 | 2,930 |
| `passage_just_apol1_16` | Justin Martyr, Apologia Prima, 16 | 2,414 |
| `passage_just_apol1_17` | Justin Martyr, Apologia Prima, 17 | 967 |
| `passage_just_apol1_18` | Justin Martyr, Apologia Prima, 18 | 1,161 |
| `passage_just_apol1_19` | Justin Martyr, Apologia Prima, 19 | 1,727 |
| `passage_just_apol1_2` | Justin Martyr, Apologia Prima, 2 | 1,012 |
| `passage_just_apol1_20` | Justin Martyr, Apologia Prima, 20 | 941 |
| `passage_just_apol1_21` | Justin Martyr, Apologia Prima, 21 | 1,700 |
| `passage_just_apol1_22` | Justin Martyr, Apologia Prima, 22 | 1,008 |
| `passage_just_apol1_23` | Justin Martyr, Apologia Prima, 23 | 798 |
| `passage_just_apol1_24` | Justin Martyr, Apologia Prima, 24 | 635 |
| `passage_just_apol1_25` | Justin Martyr, Apologia Prima, 25 | 777 |
| `passage_just_apol1_26` | Justin Martyr, Apologia Prima, 26 | 2,011 |
| `passage_just_apol1_27` | Justin Martyr, Apologia Prima, 27 | 1,120 |
| `passage_just_apol1_28` | Justin Martyr, Apologia Prima, 28 | 932 |
| `passage_just_apol1_29` | Justin Martyr, Apologia Prima, 29 | 762 |
| `passage_just_apol1_3` | Justin Martyr, Apologia Prima, 3 | 1,152 |
| `passage_just_apol1_30` | Justin Martyr, Apologia Prima, 30 | 448 |
| `passage_just_apol1_31` | Justin Martyr, Apologia Prima, 31 | 2,050 |
| `passage_just_apol1_32` | Justin Martyr, Apologia Prima, 32 | 2,893 |
| `passage_just_apol1_33` | Justin Martyr, Apologia Prima, 33 | 1,926 |
| `passage_just_apol1_34` | Justin Martyr, Apologia Prima, 34 | 473 |
| `passage_just_apol1_35` | Justin Martyr, Apologia Prima, 35 | 1,643 |
| `passage_just_apol1_36` | Justin Martyr, Apologia Prima, 36 | 761 |
| `passage_just_apol1_37` | Justin Martyr, Apologia Prima, 37 | 1,096 |
| `passage_just_apol1_38` | Justin Martyr, Apologia Prima, 38 | 937 |
| `passage_just_apol1_39` | Justin Martyr, Apologia Prima, 39 | 1,222 |
| `passage_just_apol1_4` | Justin Martyr, Apologia Prima, 4 | 1,878 |
| `passage_just_apol1_40` | Justin Martyr, Apologia Prima, 40 | 2,953 |
| `passage_just_apol1_41` | Justin Martyr, Apologia Prima, 41 | 730 |
| `passage_just_apol1_42` | Justin Martyr, Apologia Prima, 42 | 761 |
| `passage_just_apol1_43` | Justin Martyr, Apologia Prima, 43 | 1,716 |
| `passage_just_apol1_44` | Justin Martyr, Apologia Prima, 44 | 2,610 |
| `passage_just_apol1_45` | Justin Martyr, Apologia Prima, 45 | 1,223 |
| `passage_just_apol1_46` | Justin Martyr, Apologia Prima, 46 | 1,347 |
| `passage_just_apol1_47` | Justin Martyr, Apologia Prima, 47 | 892 |
| `passage_just_apol1_48` | Justin Martyr, Apologia Prima, 48 | 741 |
| `passage_just_apol1_49` | Justin Martyr, Apologia Prima, 49 | 1,244 |
| `passage_just_apol1_5` | Justin Martyr, Apologia Prima, 5 | 1,245 |
| `passage_just_apol1_50` | Justin Martyr, Apologia Prima, 50 | 2,019 |
| `passage_just_apol1_51` | Justin Martyr, Apologia Prima, 51 | 1,348 |
| `passage_just_apol1_52` | Justin Martyr, Apologia Prima, 52 | 1,824 |
| `passage_just_apol1_53` | Justin Martyr, Apologia Prima, 53 | 2,401 |
| `passage_just_apol1_54` | Justin Martyr, Apologia Prima, 54 | 2,324 |
| `passage_just_apol1_55` | Justin Martyr, Apologia Prima, 55 | 1,539 |
| `passage_just_apol1_56` | Justin Martyr, Apologia Prima, 56 | 957 |
| `passage_just_apol1_57` | Justin Martyr, Apologia Prima, 57 | 968 |
| `passage_just_apol1_58` | Justin Martyr, Apologia Prima, 58 | 881 |
| `passage_just_apol1_59` | Justin Martyr, Apologia Prima, 59 | 881 |
| `passage_just_apol1_6` | Justin Martyr, Apologia Prima, 6 | 484 |
| `passage_just_apol1_60` | Justin Martyr, Apologia Prima, 60 | 1,722 |
| `passage_just_apol1_61` | Justin Martyr, Apologia Prima, 61 | 2,319 |
| `passage_just_apol1_62` | Justin Martyr, Apologia Prima, 62 | 1,089 |
| `passage_just_apol1_63` | Justin Martyr, Apologia Prima, 63 | 3,184 |
| `passage_just_apol1_64` | Justin Martyr, Apologia Prima, 64 | 842 |
| `passage_just_apol1_65` | Justin Martyr, Apologia Prima, 65 | 1,048 |
| `passage_just_apol1_66` | Justin Martyr, Apologia Prima, 66 | 1,179 |
| `passage_just_apol1_67` | Justin Martyr, Apologia Prima, 67 | 1,698 |
| `passage_just_apol1_68` | Justin Martyr, Apologia Prima, 68 | 1,518 |
| `passage_just_apol1_7` | Justin Martyr, Apologia Prima, 7 | 815 |
| `passage_just_apol1_8` | Justin Martyr, Apologia Prima, 8 | 975 |
| `passage_just_apol1_9` | Justin Martyr, Apologia Prima, 9 | 1,137 |

### Seneca — De Providentia

- **Language:** Latin
- **Passages:** 68
- **Characters:** 27,627
- **Canonical ID:** `urn:cts:latinLit:stoa0255.stoa012`

| node_id | label | chars |
|---------|-------|-------|
| `passage_sen_prov_1_1_1` | Seneca, De Providentia, 1.1.1 | 365 |
| `passage_sen_prov_1_1_2` | Seneca, De Providentia, 1.1.2 | 655 |
| `passage_sen_prov_1_1_3` | Seneca, De Providentia, 1.1.3 | 448 |
| `passage_sen_prov_1_1_4` | Seneca, De Providentia, 1.1.4 | 480 |
| `passage_sen_prov_1_1_5` | Seneca, De Providentia, 1.1.5 | 426 |
| `passage_sen_prov_1_1_6` | Seneca, De Providentia, 1.1.6 | 351 |
| `passage_sen_prov_1_2_1` | Seneca, De Providentia, 1.2.1 | 403 |
| `passage_sen_prov_1_2_10` | Seneca, De Providentia, 1.2.10 | 611 |
| `passage_sen_prov_1_2_11` | Seneca, De Providentia, 1.2.11 | 309 |
| `passage_sen_prov_1_2_12` | Seneca, De Providentia, 1.2.12 | 379 |
| `passage_sen_prov_1_2_2` | Seneca, De Providentia, 1.2.2 | 289 |
| `passage_sen_prov_1_2_3` | Seneca, De Providentia, 1.2.3 | 291 |
| `passage_sen_prov_1_2_4` | Seneca, De Providentia, 1.2.4 | 277 |
| `passage_sen_prov_1_2_5` | Seneca, De Providentia, 1.2.5 | 321 |
| `passage_sen_prov_1_2_6` | Seneca, De Providentia, 1.2.6 | 410 |
| `passage_sen_prov_1_2_7` | Seneca, De Providentia, 1.2.7 | 257 |
| `passage_sen_prov_1_2_8` | Seneca, De Providentia, 1.2.8 | 305 |
| `passage_sen_prov_1_2_9` | Seneca, De Providentia, 1.2.9 | 350 |
| `passage_sen_prov_1_3_1` | Seneca, De Providentia, 1.3.1 | 481 |
| `passage_sen_prov_1_3_10` | Seneca, De Providentia, 1.3.10 | 497 |
| `passage_sen_prov_1_3_11` | Seneca, De Providentia, 1.3.11 | 274 |
| `passage_sen_prov_1_3_12` | Seneca, De Providentia, 1.3.12 | 263 |
| `passage_sen_prov_1_3_13` | Seneca, De Providentia, 1.3.13 | 282 |
| `passage_sen_prov_1_3_14` | Seneca, De Providentia, 1.3.14 | 559 |
| `passage_sen_prov_1_3_2` | Seneca, De Providentia, 1.3.2 | 778 |
| `passage_sen_prov_1_3_3` | Seneca, De Providentia, 1.3.3 | 683 |
| `passage_sen_prov_1_3_4` | Seneca, De Providentia, 1.3.4 | 450 |
| `passage_sen_prov_1_3_5` | Seneca, De Providentia, 1.3.5 | 211 |
| `passage_sen_prov_1_3_6` | Seneca, De Providentia, 1.3.6 | 499 |
| `passage_sen_prov_1_3_7` | Seneca, De Providentia, 1.3.7 | 626 |
| `passage_sen_prov_1_3_8` | Seneca, De Providentia, 1.3.8 | 244 |
| `passage_sen_prov_1_3_9` | Seneca, De Providentia, 1.3.9 | 397 |
| `passage_sen_prov_1_4_1` | Seneca, De Providentia, 1.4.1 | 240 |
| `passage_sen_prov_1_4_10` | Seneca, De Providentia, 1.4.10 | 353 |
| `passage_sen_prov_1_4_11` | Seneca, De Providentia, 1.4.11 | 410 |
| `passage_sen_prov_1_4_12` | Seneca, De Providentia, 1.4.12 | 422 |
| `passage_sen_prov_1_4_13` | Seneca, De Providentia, 1.4.13 | 370 |
| `passage_sen_prov_1_4_14` | Seneca, De Providentia, 1.4.14 | 298 |
| `passage_sen_prov_1_4_15` | Seneca, De Providentia, 1.4.15 | 403 |
| `passage_sen_prov_1_4_16` | Seneca, De Providentia, 1.4.16 | 332 |
| `passage_sen_prov_1_4_2` | Seneca, De Providentia, 1.4.2 | 263 |
| `passage_sen_prov_1_4_3` | Seneca, De Providentia, 1.4.3 | 471 |
| `passage_sen_prov_1_4_4` | Seneca, De Providentia, 1.4.4 | 510 |
| `passage_sen_prov_1_4_5` | Seneca, De Providentia, 1.4.5 | 722 |
| `passage_sen_prov_1_4_6` | Seneca, De Providentia, 1.4.6 | 285 |
| `passage_sen_prov_1_4_7` | Seneca, De Providentia, 1.4.7 | 559 |
| `passage_sen_prov_1_4_8` | Seneca, De Providentia, 1.4.8 | 405 |
| `passage_sen_prov_1_4_9` | Seneca, De Providentia, 1.4.9 | 382 |
| `passage_sen_prov_1_5_1` | Seneca, De Providentia, 1.5.1 | 321 |
| `passage_sen_prov_1_5_10` | Seneca, De Providentia, 1.5.10 | 119 |
| `passage_sen_prov_1_5_11` | Seneca, De Providentia, 1.5.11 | 332 |
| `passage_sen_prov_1_5_2` | Seneca, De Providentia, 1.5.2 | 359 |
| `passage_sen_prov_1_5_3` | Seneca, De Providentia, 1.5.3 | 433 |
| `passage_sen_prov_1_5_4` | Seneca, De Providentia, 1.5.4 | 375 |
| `passage_sen_prov_1_5_5` | Seneca, De Providentia, 1.5.5 | 500 |
| `passage_sen_prov_1_5_6` | Seneca, De Providentia, 1.5.6 | 300 |
| `passage_sen_prov_1_5_7` | Seneca, De Providentia, 1.5.7 | 420 |
| `passage_sen_prov_1_5_8` | Seneca, De Providentia, 1.5.8 | 456 |
| `passage_sen_prov_1_5_9` | Seneca, De Providentia, 1.5.9 | 621 |
| `passage_sen_prov_1_6_1` | Seneca, De Providentia, 1.6.1 | 391 |
| `passage_sen_prov_1_6_2` | Seneca, De Providentia, 1.6.2 | 432 |
| `passage_sen_prov_1_6_3` | Seneca, De Providentia, 1.6.3 | 265 |
| `passage_sen_prov_1_6_4` | Seneca, De Providentia, 1.6.4 | 435 |
| `passage_sen_prov_1_6_5` | Seneca, De Providentia, 1.6.5 | 350 |
| `passage_sen_prov_1_6_6` | Seneca, De Providentia, 1.6.6 | 462 |
| `passage_sen_prov_1_6_7` | Seneca, De Providentia, 1.6.7 | 454 |
| `passage_sen_prov_1_6_8` | Seneca, De Providentia, 1.6.8 | 434 |
| `passage_sen_prov_1_6_9` | Seneca, De Providentia, 1.6.9 | 572 |

### Plato — Φαίδων

- **Language:** Greek
- **Passages:** 59
- **Characters:** 24,964
- **Canonical ID:** `urn:cts:greekLit:tlg0059.tlg004`

| node_id | label | chars |
|---------|-------|-------|
| `passage_plato_phd_43a` | Plato, Φαίδων, 43a | 322 |
| `passage_plato_phd_43b` | Plato, Φαίδων, 43b | 503 |
| `passage_plato_phd_43c` | Plato, Φαίδων, 43c | 433 |
| `passage_plato_phd_43d` | Plato, Φαίδων, 43d | 375 |
| `passage_plato_phd_44a` | Plato, Φαίδων, 44a | 415 |
| `passage_plato_phd_44b` | Plato, Φαίδων, 44b | 466 |
| `passage_plato_phd_44c` | Plato, Φαίδων, 44c | 406 |
| `passage_plato_phd_44d` | Plato, Φαίδων, 44d | 473 |
| `passage_plato_phd_44e` | Plato, Φαίδων, 44e | 316 |
| `passage_plato_phd_45a` | Plato, Φαίδων, 45a | 444 |
| `passage_plato_phd_45b` | Plato, Φαίδων, 45b | 439 |
| `passage_plato_phd_45c` | Plato, Φαίδων, 45c | 495 |
| `passage_plato_phd_45d` | Plato, Φαίδων, 45d | 453 |
| `passage_plato_phd_45e` | Plato, Φαίδων, 45e | 341 |
| `passage_plato_phd_46a` | Plato, Φαίδων, 46a | 436 |
| `passage_plato_phd_46b` | Plato, Φαίδων, 46b | 433 |
| `passage_plato_phd_46c` | Plato, Φαίδων, 46c | 425 |
| `passage_plato_phd_46d` | Plato, Φαίδων, 46d | 475 |
| `passage_plato_phd_46e` | Plato, Φαίδων, 46e | 178 |
| `passage_plato_phd_47a` | Plato, Φαίδων, 47a | 437 |
| `passage_plato_phd_47b` | Plato, Φαίδων, 47b | 453 |
| `passage_plato_phd_47c` | Plato, Φαίδων, 47c | 517 |
| `passage_plato_phd_47d` | Plato, Φαίδων, 47d | 470 |
| `passage_plato_phd_47e` | Plato, Φαίδων, 47e | 310 |
| `passage_plato_phd_48a` | Plato, Φαίδων, 48a | 474 |
| `passage_plato_phd_48b` | Plato, Φαίδων, 48b | 464 |
| `passage_plato_phd_48c` | Plato, Φαίδων, 48c | 446 |
| `passage_plato_phd_48d` | Plato, Φαίδων, 48d | 407 |
| `passage_plato_phd_48e` | Plato, Φαίδων, 48e | 266 |
| `passage_plato_phd_49a` | Plato, Φαίδων, 49a | 479 |
| `passage_plato_phd_49b` | Plato, Φαίδων, 49b | 428 |
| `passage_plato_phd_49c` | Plato, Φαίδων, 49c | 379 |
| `passage_plato_phd_49d` | Plato, Φαίδων, 49d | 494 |
| `passage_plato_phd_49e` | Plato, Φαίδων, 49e | 366 |
| `passage_plato_phd_50a` | Plato, Φαίδων, 50a | 421 |
| `passage_plato_phd_50b` | Plato, Φαίδων, 50b | 449 |
| `passage_plato_phd_50c` | Plato, Φαίδων, 50c | 445 |
| `passage_plato_phd_50d` | Plato, Φαίδων, 50d | 429 |
| `passage_plato_phd_50e` | Plato, Φαίδων, 50e | 528 |
| `passage_plato_phd_51a` | Plato, Φαίδων, 51a | 490 |
| `passage_plato_phd_51b` | Plato, Φαίδων, 51b | 502 |
| `passage_plato_phd_51c` | Plato, Φαίδων, 51c | 445 |
| `passage_plato_phd_51d` | Plato, Φαίδων, 51d | 452 |
| `passage_plato_phd_51e` | Plato, Φαίδων, 51e | 400 |
| `passage_plato_phd_52a` | Plato, Φαίδων, 52a | 455 |
| `passage_plato_phd_52b` | Plato, Φαίδων, 52b | 448 |
| `passage_plato_phd_52c` | Plato, Φαίδων, 52c | 509 |
| `passage_plato_phd_52d` | Plato, Φαίδων, 52d | 403 |
| `passage_plato_phd_52e` | Plato, Φαίδων, 52e | 348 |
| `passage_plato_phd_53a` | Plato, Φαίδων, 53a | 475 |
| `passage_plato_phd_53b` | Plato, Φαίδων, 53b | 441 |
| `passage_plato_phd_53c` | Plato, Φαίδων, 53c | 445 |
| `passage_plato_phd_53d` | Plato, Φαίδων, 53d | 455 |
| `passage_plato_phd_53e` | Plato, Φαίδων, 53e | 334 |
| `passage_plato_phd_54a` | Plato, Φαίδων, 54a | 513 |
| `passage_plato_phd_54b` | Plato, Φαίδων, 54b | 443 |
| `passage_plato_phd_54c` | Plato, Φαίδων, 54c | 440 |
| `passage_plato_phd_54d` | Plato, Φαίδων, 54d | 400 |
| `passage_plato_phd_54e` | Plato, Φαίδων, 54e | 76 |

### Marcus Tullius Cicero — De Fato

- **Language:** Latin
- **Passages:** 48
- **Characters:** 33,621
- **Canonical ID:** `urn:cts:latinLit:phi0474.phi049`

| node_id | label | chars |
|---------|-------|-------|
| `passage_cic_fat_1` | Marcus Tullius Cicero, De Fato, Fat. 1 | 751 |
| `passage_cic_fat_10` | Marcus Tullius Cicero, De Fato, Fat. 10 | 718 |
| `passage_cic_fat_11` | Marcus Tullius Cicero, De Fato, Fat. 11 | 565 |
| `passage_cic_fat_12` | Marcus Tullius Cicero, De Fato, Fat. 12 | 938 |
| `passage_cic_fat_13` | Marcus Tullius Cicero, De Fato, Fat. 13 | 785 |
| `passage_cic_fat_14` | Marcus Tullius Cicero, De Fato, Fat. 14 | 589 |
| `passage_cic_fat_15` | Marcus Tullius Cicero, De Fato, Fat. 15 | 965 |
| `passage_cic_fat_16` | Marcus Tullius Cicero, De Fato, Fat. 16 | 545 |
| `passage_cic_fat_17` | Marcus Tullius Cicero, De Fato, Fat. 17 | 956 |
| `passage_cic_fat_18` | Marcus Tullius Cicero, De Fato, Fat. 18 | 786 |
| `passage_cic_fat_19` | Marcus Tullius Cicero, De Fato, Fat. 19 | 584 |
| `passage_cic_fat_2` | Marcus Tullius Cicero, De Fato, Fat. 2 | 655 |
| `passage_cic_fat_20` | Marcus Tullius Cicero, De Fato, Fat. 20 | 612 |
| `passage_cic_fat_21` | Marcus Tullius Cicero, De Fato, Fat. 21 | 888 |
| `passage_cic_fat_22` | Marcus Tullius Cicero, De Fato, Fat. 22 | 590 |
| `passage_cic_fat_23` | Marcus Tullius Cicero, De Fato, Fat. 23 | 833 |
| `passage_cic_fat_24` | Marcus Tullius Cicero, De Fato, Fat. 24 | 611 |
| `passage_cic_fat_25` | Marcus Tullius Cicero, De Fato, Fat. 25 | 460 |
| `passage_cic_fat_26` | Marcus Tullius Cicero, De Fato, Fat. 26 | 415 |
| `passage_cic_fat_27` | Marcus Tullius Cicero, De Fato, Fat. 27 | 576 |
| `passage_cic_fat_28` | Marcus Tullius Cicero, De Fato, Fat. 28 | 883 |
| `passage_cic_fat_29` | Marcus Tullius Cicero, De Fato, Fat. 29 | 663 |
| `passage_cic_fat_3` | Marcus Tullius Cicero, De Fato, Fat. 3 | 815 |
| `passage_cic_fat_30` | Marcus Tullius Cicero, De Fato, Fat. 30 | 914 |
| `passage_cic_fat_31` | Marcus Tullius Cicero, De Fato, Fat. 31 | 504 |
| `passage_cic_fat_32` | Marcus Tullius Cicero, De Fato, Fat. 32 | 566 |
| `passage_cic_fat_33` | Marcus Tullius Cicero, De Fato, Fat. 33 | 891 |
| `passage_cic_fat_34` | Marcus Tullius Cicero, De Fato, Fat. 34 | 638 |
| `passage_cic_fat_35` | Marcus Tullius Cicero, De Fato, Fat. 35 | 531 |
| `passage_cic_fat_36` | Marcus Tullius Cicero, De Fato, Fat. 36 | 519 |
| `passage_cic_fat_37` | Marcus Tullius Cicero, De Fato, Fat. 37 | 713 |
| `passage_cic_fat_38` | Marcus Tullius Cicero, De Fato, Fat. 38 | 470 |
| `passage_cic_fat_39` | Marcus Tullius Cicero, De Fato, Fat. 39 | 553 |
| `passage_cic_fat_4` | Marcus Tullius Cicero, De Fato, Fat. 4 | 570 |
| `passage_cic_fat_40` | Marcus Tullius Cicero, De Fato, Fat. 40 | 908 |
| `passage_cic_fat_41` | Marcus Tullius Cicero, De Fato, Fat. 41 | 919 |
| `passage_cic_fat_42` | Marcus Tullius Cicero, De Fato, Fat. 42 | 770 |
| `passage_cic_fat_43` | Marcus Tullius Cicero, De Fato, Fat. 43 | 621 |
| `passage_cic_fat_44` | Marcus Tullius Cicero, De Fato, Fat. 44 | 884 |
| `passage_cic_fat_45` | Marcus Tullius Cicero, De Fato, Fat. 45 | 517 |
| `passage_cic_fat_46` | Marcus Tullius Cicero, De Fato, Fat. 46 | 503 |
| `passage_cic_fat_47` | Marcus Tullius Cicero, De Fato, Fat. 47 | 473 |
| `passage_cic_fat_48` | Marcus Tullius Cicero, De Fato, Fat. 48 | 1,511 |
| `passage_cic_fat_5` | Marcus Tullius Cicero, De Fato, Fat. 5 | 864 |
| `passage_cic_fat_6` | Marcus Tullius Cicero, De Fato, Fat. 6 | 518 |
| `passage_cic_fat_7` | Marcus Tullius Cicero, De Fato, Fat. 7 | 706 |
| `passage_cic_fat_8` | Marcus Tullius Cicero, De Fato, Fat. 8 | 629 |
| `passage_cic_fat_9` | Marcus Tullius Cicero, De Fato, Fat. 9 | 746 |

### Plutarch — De Stoicorum Repugnantiis (On Stoic Self-Contradictions)

- **Language:** Greek
- **Passages:** 47
- **Characters:** 75,155
- **Canonical ID:** `urn:cts:greekLit:tlg0007.tlg136`

| node_id | label | chars |
|---------|-------|-------|
| `passage_plut_stoic_rep_1` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 1 | 369 |
| `passage_plut_stoic_rep_10` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 10 | 4,637 |
| `passage_plut_stoic_rep_11` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 11 | 1,827 |
| `passage_plut_stoic_rep_12` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 12 | 888 |
| `passage_plut_stoic_rep_13` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 13 | 3,630 |
| `passage_plut_stoic_rep_14` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 14 | 1,665 |
| `passage_plut_stoic_rep_15` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 15 | 3,395 |
| `passage_plut_stoic_rep_16` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 16 | 1,520 |
| `passage_plut_stoic_rep_17` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 17 | 1,094 |
| `passage_plut_stoic_rep_18` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 18 | 2,124 |
| `passage_plut_stoic_rep_19` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 19 | 1,272 |
| `passage_plut_stoic_rep_2` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 2 | 1,739 |
| `passage_plut_stoic_rep_20` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 20 | 3,304 |
| `passage_plut_stoic_rep_21` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 21 | 2,238 |
| `passage_plut_stoic_rep_22` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 22 | 881 |
| `passage_plut_stoic_rep_23` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 23 | 2,278 |
| `passage_plut_stoic_rep_24` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 24 | 929 |
| `passage_plut_stoic_rep_25` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 25 | 684 |
| `passage_plut_stoic_rep_26` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 26 | 1,106 |
| `passage_plut_stoic_rep_27` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 27 | 784 |
| `passage_plut_stoic_rep_28` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 28 | 815 |
| `passage_plut_stoic_rep_29` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 29 | 1,175 |
| `passage_plut_stoic_rep_3` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 3 | 415 |
| `passage_plut_stoic_rep_30` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 30 | 2,306 |
| `passage_plut_stoic_rep_31` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 31 | 1,635 |
| `passage_plut_stoic_rep_32` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 32 | 1,872 |
| `passage_plut_stoic_rep_33` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 33 | 815 |
| `passage_plut_stoic_rep_34` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 34 | 2,422 |
| `passage_plut_stoic_rep_35` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 35 | 1,339 |
| `passage_plut_stoic_rep_36` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 36 | 521 |
| `passage_plut_stoic_rep_37` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 37 | 1,250 |
| `passage_plut_stoic_rep_38` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 38 | 1,930 |
| `passage_plut_stoic_rep_39` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 39 | 1,480 |
| `passage_plut_stoic_rep_4` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 4 | 542 |
| `passage_plut_stoic_rep_40` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 40 | 426 |
| `passage_plut_stoic_rep_41` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 41 | 2,653 |
| `passage_plut_stoic_rep_42` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 42 | 365 |
| `passage_plut_stoic_rep_43` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 43 | 1,464 |
| `passage_plut_stoic_rep_44` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 44 | 3,926 |
| `passage_plut_stoic_rep_45` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 45 | 524 |
| `passage_plut_stoic_rep_46` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 46 | 824 |
| `passage_plut_stoic_rep_47` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 47 | 4,543 |
| `passage_plut_stoic_rep_5` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 5 | 273 |
| `passage_plut_stoic_rep_6` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 6 | 503 |
| `passage_plut_stoic_rep_7` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 7 | 1,030 |
| `passage_plut_stoic_rep_8` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 8 | 679 |
| `passage_plut_stoic_rep_9` | Plutarch, De Stoicorum Repugnantiis (On Stoic Self-Contradictions), 9 | 3,064 |

### Aristotle — Ἠθικὰ Εὐδήμεια

- **Language:** Greek
- **Passages:** 41
- **Characters:** 153,220
- **Canonical ID:** `oga:tlg0086.tlg009.perseus-grc2`

| node_id | label | chars |
|---------|-------|-------|
| `passage_arist_ee_1_1` | Aristotle, Ἠθικὰ Εὐδήμεια, 1.1 | 2,155 |
| `passage_arist_ee_1_2` | Aristotle, Ἠθικὰ Εὐδήμεια, 1.2 | 1,172 |
| `passage_arist_ee_1_3` | Aristotle, Ἠθικὰ Εὐδήμεια, 1.3 | 1,481 |
| `passage_arist_ee_1_4` | Aristotle, Ἠθικὰ Εὐδήμεια, 1.4 | 1,671 |
| `passage_arist_ee_1_5` | Aristotle, Ἠθικὰ Εὐδήμεια, 1.5 | 4,868 |
| `passage_arist_ee_1_6` | Aristotle, Ἠθικὰ Εὐδήμεια, 1.6 | 1,797 |
| `passage_arist_ee_1_7` | Aristotle, Ἠθικὰ Εὐδήμεια, 1.7 | 1,254 |
| `passage_arist_ee_1_8` | Aristotle, Ἠθικὰ Εὐδήμεια, 1.8 | 5,892 |
| `passage_arist_ee_2_1` | Aristotle, Ἠθικὰ Εὐδήμεια, 2.1 | 6,941 |
| `passage_arist_ee_2_10` | Aristotle, Ἠθικὰ Εὐδήμεια, 2.10 | 8,487 |
| `passage_arist_ee_2_11` | Aristotle, Ἠθικὰ Εὐδήμεια, 2.11 | 2,748 |
| `passage_arist_ee_2_2` | Aristotle, Ἠθικὰ Εὐδήμεια, 2.2 | 1,197 |
| `passage_arist_ee_2_3` | Aristotle, Ἠθικὰ Εὐδήμεια, 2.3 | 4,295 |
| `passage_arist_ee_2_4` | Aristotle, Ἠθικὰ Εὐδήμεια, 2.4 | 996 |
| `passage_arist_ee_2_5` | Aristotle, Ἠθικὰ Εὐδήμεια, 2.5 | 2,798 |
| `passage_arist_ee_2_6` | Aristotle, Ἠθικὰ Εὐδήμεια, 2.6 | 2,706 |
| `passage_arist_ee_2_7` | Aristotle, Ἠθικὰ Εὐδήμεια, 2.7 | 3,146 |
| `passage_arist_ee_2_8` | Aristotle, Ἠθικὰ Εὐδήμεια, 2.8 | 6,420 |
| `passage_arist_ee_2_9` | Aristotle, Ἠθικὰ Εὐδήμεια, 2.9 | 1,182 |
| `passage_arist_ee_3_1` | Aristotle, Ἠθικὰ Εὐδήμεια, 3.1 | 9,662 |
| `passage_arist_ee_3_2` | Aristotle, Ἠθικὰ Εὐδήμεια, 3.2 | 4,814 |
| `passage_arist_ee_3_3` | Aristotle, Ἠθικὰ Εὐδήμεια, 3.3 | 1,208 |
| `passage_arist_ee_3_4` | Aristotle, Ἠθικὰ Εὐδήμεια, 3.4 | 1,666 |
| `passage_arist_ee_3_5` | Aristotle, Ἠθικὰ Εὐδήμεια, 3.5 | 5,008 |
| `passage_arist_ee_3_6` | Aristotle, Ἠθικὰ Εὐδήμεια, 3.6 | 1,329 |
| `passage_arist_ee_3_7` | Aristotle, Ἠθικὰ Εὐδήμεια, 3.7 | 4,039 |
| `passage_arist_ee_7_1` | Aristotle, Ἠθικὰ Εὐδήμεια, 7.1 | 3,857 |
| `passage_arist_ee_7_10` | Aristotle, Ἠθικὰ Εὐδήμεια, 7.10 | 8,518 |
| `passage_arist_ee_7_11` | Aristotle, Ἠθικὰ Εὐδήμεια, 7.11 | 2,084 |
| `passage_arist_ee_7_12` | Aristotle, Ἠθικὰ Εὐδήμεια, 7.12 | 7,803 |
| `passage_arist_ee_7_2` | Aristotle, Ἠθικὰ Εὐδήμεια, 7.2 | 13,205 |
| `passage_arist_ee_7_3` | Aristotle, Ἠθικὰ Εὐδήμεια, 7.3 | 1,400 |
| `passage_arist_ee_7_4` | Aristotle, Ἠθικὰ Εὐδήμεια, 7.4 | 2,292 |
| `passage_arist_ee_7_5` | Aristotle, Ἠθικὰ Εὐδήμεια, 7.5 | 2,293 |
| `passage_arist_ee_7_6` | Aristotle, Ἠθικὰ Εὐδήμεια, 7.6 | 3,967 |
| `passage_arist_ee_7_7` | Aristotle, Ἠθικὰ Εὐδήμεια, 7.7 | 1,929 |
| `passage_arist_ee_7_8` | Aristotle, Ἠθικὰ Εὐδήμεια, 7.8 | 891 |
| `passage_arist_ee_7_9` | Aristotle, Ἠθικὰ Εὐδήμεια, 7.9 | 1,661 |
| `passage_arist_ee_8_1` | Aristotle, Ἠθικὰ Εὐδήμεια, 8.1 | 2,653 |
| `passage_arist_ee_8_2` | Aristotle, Ἠθικὰ Εὐδήμεια, 8.2 | 7,188 |
| `passage_arist_ee_8_3` | Aristotle, Ἠθικὰ Εὐδήμεια, 8.3 | 4,547 |

### Augustine — De Natura Boni

- **Language:** Latin
- **Passages:** 39
- **Characters:** 52,457
- **Canonical ID:** `urn:cts:latinLit:stoa0040.stoa054`

| node_id | label | chars |
|---------|-------|-------|
| `passage_aug_nat_bon_1` | Augustine, De Natura Boni, Augu. 1 | 1,453 |
| `passage_aug_nat_bon_10` | Augustine, De Natura Boni, Augu. 10 | 1,477 |
| `passage_aug_nat_bon_11` | Augustine, De Natura Boni, Augu. 11 | 1,393 |
| `passage_aug_nat_bon_12` | Augustine, De Natura Boni, Augu. 12 | 1,323 |
| `passage_aug_nat_bon_13` | Augustine, De Natura Boni, Augu. 13 | 1,402 |
| `passage_aug_nat_bon_14` | Augustine, De Natura Boni, Augu. 14 | 1,447 |
| `passage_aug_nat_bon_15` | Augustine, De Natura Boni, Augu. 15 | 1,500 |
| `passage_aug_nat_bon_16` | Augustine, De Natura Boni, Augu. 16 | 1,386 |
| `passage_aug_nat_bon_17` | Augustine, De Natura Boni, Augu. 17 | 1,406 |
| `passage_aug_nat_bon_18` | Augustine, De Natura Boni, Augu. 18 | 1,445 |
| `passage_aug_nat_bon_19` | Augustine, De Natura Boni, Augu. 19 | 1,328 |
| `passage_aug_nat_bon_2` | Augustine, De Natura Boni, Augu. 2 | 1,492 |
| `passage_aug_nat_bon_20` | Augustine, De Natura Boni, Augu. 20 | 1,474 |
| `passage_aug_nat_bon_21` | Augustine, De Natura Boni, Augu. 21 | 1,348 |
| `passage_aug_nat_bon_22` | Augustine, De Natura Boni, Augu. 22 | 1,210 |
| `passage_aug_nat_bon_23` | Augustine, De Natura Boni, Augu. 23 | 1,486 |
| `passage_aug_nat_bon_24` | Augustine, De Natura Boni, Augu. 24 | 1,440 |
| `passage_aug_nat_bon_25` | Augustine, De Natura Boni, Augu. 25 | 1,190 |
| `passage_aug_nat_bon_26` | Augustine, De Natura Boni, Augu. 26 | 1,494 |
| `passage_aug_nat_bon_27` | Augustine, De Natura Boni, Augu. 27 | 1,344 |
| `passage_aug_nat_bon_28` | Augustine, De Natura Boni, Augu. 28 | 1,492 |
| `passage_aug_nat_bon_29` | Augustine, De Natura Boni, Augu. 29 | 1,145 |
| `passage_aug_nat_bon_3` | Augustine, De Natura Boni, Augu. 3 | 1,466 |
| `passage_aug_nat_bon_30` | Augustine, De Natura Boni, Augu. 30 | 1,462 |
| `passage_aug_nat_bon_31` | Augustine, De Natura Boni, Augu. 31 | 1,339 |
| `passage_aug_nat_bon_32` | Augustine, De Natura Boni, Augu. 32 | 1,222 |
| `passage_aug_nat_bon_33` | Augustine, De Natura Boni, Augu. 33 | 1,320 |
| `passage_aug_nat_bon_34` | Augustine, De Natura Boni, Augu. 34 | 1,486 |
| `passage_aug_nat_bon_35` | Augustine, De Natura Boni, Augu. 35 | 1,419 |
| `passage_aug_nat_bon_36` | Augustine, De Natura Boni, Augu. 36 | 1,448 |
| `passage_aug_nat_bon_37` | Augustine, De Natura Boni, Augu. 37 | 896 |
| `passage_aug_nat_bon_38` | Augustine, De Natura Boni, Augu. 38 | 1,087 |
| `passage_aug_nat_bon_39` | Augustine, De Natura Boni, Augu. 39 | 585 |
| `passage_aug_nat_bon_4` | Augustine, De Natura Boni, Augu. 4 | 1,360 |
| `passage_aug_nat_bon_5` | Augustine, De Natura Boni, Augu. 5 | 1,477 |
| `passage_aug_nat_bon_6` | Augustine, De Natura Boni, Augu. 6 | 1,405 |
| `passage_aug_nat_bon_7` | Augustine, De Natura Boni, Augu. 7 | 1,334 |
| `passage_aug_nat_bon_8` | Augustine, De Natura Boni, Augu. 8 | 1,111 |
| `passage_aug_nat_bon_9` | Augustine, De Natura Boni, Augu. 9 | 1,365 |

### Evodius Bishop of Uzalis -424 — De fide Contra Manicheos

- **Language:** Latin
- **Passages:** 36
- **Characters:** 48,895
- **Canonical ID:** `cpl:evodius.de_fide`

| node_id | label | chars |
|---------|-------|-------|
| `passage_evodius_1` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 1 | 1,432 |
| `passage_evodius_10` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 10 | 1,386 |
| `passage_evodius_11` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 11 | 1,438 |
| `passage_evodius_12` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 12 | 1,389 |
| `passage_evodius_13` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 13 | 1,388 |
| `passage_evodius_14` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 14 | 1,397 |
| `passage_evodius_15` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 15 | 1,385 |
| `passage_evodius_16` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 16 | 1,463 |
| `passage_evodius_17` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 17 | 1,011 |
| `passage_evodius_18` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 18 | 1,437 |
| `passage_evodius_19` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 19 | 1,446 |
| `passage_evodius_2` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 2 | 1,422 |
| `passage_evodius_20` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 20 | 1,497 |
| `passage_evodius_21` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 21 | 1,491 |
| `passage_evodius_22` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 22 | 1,400 |
| `passage_evodius_23` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 23 | 1,461 |
| `passage_evodius_24` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 24 | 1,459 |
| `passage_evodius_25` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 25 | 1,463 |
| `passage_evodius_26` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 26 | 1,192 |
| `passage_evodius_27` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 27 | 1,209 |
| `passage_evodius_28` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 28 | 1,418 |
| `passage_evodius_29` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 29 | 1,485 |
| `passage_evodius_3` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 3 | 1,382 |
| `passage_evodius_30` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 30 | 1,498 |
| `passage_evodius_31` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 31 | 1,495 |
| `passage_evodius_32` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 32 | 1,323 |
| `passage_evodius_33` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 33 | 1,471 |
| `passage_evodius_34` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 34 | 1,395 |
| `passage_evodius_35` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 35 | 1,438 |
| `passage_evodius_36` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 36 | 76 |
| `passage_evodius_4` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 4 | 1,477 |
| `passage_evodius_5` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 5 | 1,382 |
| `passage_evodius_6` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 6 | 1,447 |
| `passage_evodius_7` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 7 | 1,497 |
| `passage_evodius_8` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 8 | 1,299 |
| `passage_evodius_9` | Evodius Bishop of Uzalis -424, De fide Contra Manicheos, Evod. 9 | 1,046 |

### Porphyrius — Ad Marcellam

- **Language:** Greek
- **Passages:** 35
- **Characters:** 29,250
- **Canonical ID:** `urn:cts:greekLit:tlg2034.tlg009`

| node_id | label | chars |
|---------|-------|-------|
| `passage_porph_marc_1` | Porphyrius, Ad Marcellam, Porp. 1 | 1,107 |
| `passage_porph_marc_10` | Porphyrius, Ad Marcellam, Porp. 10 | 943 |
| `passage_porph_marc_11` | Porphyrius, Ad Marcellam, Porp. 11 | 779 |
| `passage_porph_marc_12` | Porphyrius, Ad Marcellam, Porp. 12 | 837 |
| `passage_porph_marc_13` | Porphyrius, Ad Marcellam, Porp. 13 | 876 |
| `passage_porph_marc_14` | Porphyrius, Ad Marcellam, Porp. 14 | 723 |
| `passage_porph_marc_15` | Porphyrius, Ad Marcellam, Porp. 15 | 803 |
| `passage_porph_marc_16` | Porphyrius, Ad Marcellam, Porp. 16 | 870 |
| `passage_porph_marc_17` | Porphyrius, Ad Marcellam, Porp. 17 | 690 |
| `passage_porph_marc_18` | Porphyrius, Ad Marcellam, Porp. 18 | 731 |
| `passage_porph_marc_19` | Porphyrius, Ad Marcellam, Porp. 19 | 767 |
| `passage_porph_marc_2` | Porphyrius, Ad Marcellam, Porp. 2 | 812 |
| `passage_porph_marc_20` | Porphyrius, Ad Marcellam, Porp. 20 | 484 |
| `passage_porph_marc_21` | Porphyrius, Ad Marcellam, Porp. 21 | 901 |
| `passage_porph_marc_22` | Porphyrius, Ad Marcellam, Porp. 22 | 626 |
| `passage_porph_marc_23` | Porphyrius, Ad Marcellam, Porp. 23 | 711 |
| `passage_porph_marc_24` | Porphyrius, Ad Marcellam, Porp. 24 | 613 |
| `passage_porph_marc_25` | Porphyrius, Ad Marcellam, Porp. 25 | 965 |
| `passage_porph_marc_26` | Porphyrius, Ad Marcellam, Porp. 26 | 964 |
| `passage_porph_marc_27` | Porphyrius, Ad Marcellam, Porp. 27 | 976 |
| `passage_porph_marc_28` | Porphyrius, Ad Marcellam, Porp. 28 | 732 |
| `passage_porph_marc_29` | Porphyrius, Ad Marcellam, Porp. 29 | 668 |
| `passage_porph_marc_3` | Porphyrius, Ad Marcellam, Porp. 3 | 894 |
| `passage_porph_marc_30` | Porphyrius, Ad Marcellam, Porp. 30 | 608 |
| `passage_porph_marc_31` | Porphyrius, Ad Marcellam, Porp. 31 | 448 |
| `passage_porph_marc_32` | Porphyrius, Ad Marcellam, Porp. 32 | 911 |
| `passage_porph_marc_33` | Porphyrius, Ad Marcellam, Porp. 33 | 891 |
| `passage_porph_marc_34` | Porphyrius, Ad Marcellam, Porp. 34 | 459 |
| `passage_porph_marc_35` | Porphyrius, Ad Marcellam, Porp. 35 | 845 |
| `passage_porph_marc_4` | Porphyrius, Ad Marcellam, Porp. 4 | 893 |
| `passage_porph_marc_5` | Porphyrius, Ad Marcellam, Porp. 5 | 1,470 |
| `passage_porph_marc_6` | Porphyrius, Ad Marcellam, Porp. 6 | 1,075 |
| `passage_porph_marc_7` | Porphyrius, Ad Marcellam, Porp. 7 | 1,042 |
| `passage_porph_marc_8` | Porphyrius, Ad Marcellam, Porp. 8 | 1,049 |
| `passage_porph_marc_9` | Porphyrius, Ad Marcellam, Porp. 9 | 1,087 |

### Gregory of Nazianzus — De Spiritu Sancto (Orat. 31)

- **Language:** Greek
- **Passages:** 33
- **Characters:** 37,776
- **Canonical ID:** `urn:cts:greekLit:tlg2022.tlg011`

| node_id | label | chars |
|---------|-------|-------|
| `passage_greg_naz_011_1` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.1 | 628 |
| `passage_greg_naz_011_10` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.10 | 1,408 |
| `passage_greg_naz_011_11` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.11 | 1,053 |
| `passage_greg_naz_011_12` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.12 | 1,951 |
| `passage_greg_naz_011_13` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.13 | 1,183 |
| `passage_greg_naz_011_14` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.14 | 707 |
| `passage_greg_naz_011_15` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.15 | 724 |
| `passage_greg_naz_011_16` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.16 | 1,129 |
| `passage_greg_naz_011_17` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.17 | 709 |
| `passage_greg_naz_011_18` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.18 | 1,195 |
| `passage_greg_naz_011_19` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.19 | 1,642 |
| `passage_greg_naz_011_2` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.2 | 887 |
| `passage_greg_naz_011_20` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.20 | 1,312 |
| `passage_greg_naz_011_21` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.21 | 888 |
| `passage_greg_naz_011_22` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.22 | 1,205 |
| `passage_greg_naz_011_23` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.23 | 1,106 |
| `passage_greg_naz_011_24` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.24 | 1,036 |
| `passage_greg_naz_011_25` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.25 | 1,656 |
| `passage_greg_naz_011_26` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.26 | 1,505 |
| `passage_greg_naz_011_27` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.27 | 1,000 |
| `passage_greg_naz_011_28` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.28 | 801 |
| `passage_greg_naz_011_29` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.29 | 2,301 |
| `passage_greg_naz_011_3` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.3 | 1,339 |
| `passage_greg_naz_011_30` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.30 | 971 |
| `passage_greg_naz_011_31` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.31 | 770 |
| `passage_greg_naz_011_32` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.32 | 912 |
| `passage_greg_naz_011_33` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.33 | 1,064 |
| `passage_greg_naz_011_4` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.4 | 726 |
| `passage_greg_naz_011_5` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.5 | 1,273 |
| `passage_greg_naz_011_6` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.6 | 1,170 |
| `passage_greg_naz_011_7` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.7 | 1,320 |
| `passage_greg_naz_011_8` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.8 | 1,210 |
| `passage_greg_naz_011_9` | Gregory of Nazianzus, De Spiritu Sancto (Orat. 31), PG 35.9 | 995 |

### Gregory of Nazianzus — De Theologia (Orat. 28)

- **Language:** Greek
- **Passages:** 31
- **Characters:** 45,061
- **Canonical ID:** `urn:cts:greekLit:tlg2022.tlg008`

| node_id | label | chars |
|---------|-------|-------|
| `passage_greg_naz_008_1` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 1 | 879 |
| `passage_greg_naz_008_10` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 10 | 1,108 |
| `passage_greg_naz_008_11` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 11 | 1,145 |
| `passage_greg_naz_008_12` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 12 | 1,837 |
| `passage_greg_naz_008_13` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 13 | 1,828 |
| `passage_greg_naz_008_14` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 14 | 897 |
| `passage_greg_naz_008_15` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 15 | 1,489 |
| `passage_greg_naz_008_16` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 16 | 1,333 |
| `passage_greg_naz_008_17` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 17 | 780 |
| `passage_greg_naz_008_18` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 18 | 1,245 |
| `passage_greg_naz_008_19` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 19 | 1,675 |
| `passage_greg_naz_008_2` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 2 | 2,031 |
| `passage_greg_naz_008_20` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 20 | 936 |
| `passage_greg_naz_008_21` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 21 | 1,816 |
| `passage_greg_naz_008_22` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 22 | 2,122 |
| `passage_greg_naz_008_23` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 23 | 1,074 |
| `passage_greg_naz_008_24` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 24 | 1,528 |
| `passage_greg_naz_008_25` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 25 | 1,522 |
| `passage_greg_naz_008_26` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 26 | 2,019 |
| `passage_greg_naz_008_27` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 27 | 1,459 |
| `passage_greg_naz_008_28` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 28 | 2,333 |
| `passage_greg_naz_008_29` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 29 | 1,531 |
| `passage_greg_naz_008_3` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 3 | 1,436 |
| `passage_greg_naz_008_30` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 30 | 1,490 |
| `passage_greg_naz_008_31` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 31 | 2,238 |
| `passage_greg_naz_008_4` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 4 | 992 |
| `passage_greg_naz_008_5` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 5 | 903 |
| `passage_greg_naz_008_6` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 6 | 1,360 |
| `passage_greg_naz_008_7` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 7 | 842 |
| `passage_greg_naz_008_8` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 8 | 1,496 |
| `passage_greg_naz_008_9` | Gregory of Nazianzus, De Theologia (Orat. 28), Greg. 9 | 1,717 |

### Aristotle — De anima

- **Language:** Greek
- **Passages:** 30
- **Characters:** 117,844
- **Canonical ID:** `first1k:tlg0086.tlg002.1st1K-grc1`

| node_id | label | chars |
|---------|-------|-------|
| `passage_arist_da_1_1` | Aristotle, De anima, 1.1 | 5,712 |
| `passage_arist_da_1_2` | Aristotle, De anima, 1.2 | 7,626 |
| `passage_arist_da_1_3` | Aristotle, De anima, 1.3 | 7,109 |
| `passage_arist_da_1_4` | Aristotle, De anima, 1.4 | 5,974 |
| `passage_arist_da_1_5` | Aristotle, De anima, 1.5 | 8,558 |
| `passage_arist_da_2_1` | Aristotle, De anima, 2.1 | 3,433 |
| `passage_arist_da_2_10` | Aristotle, De anima, 2.10 | 2,348 |
| `passage_arist_da_2_11` | Aristotle, De anima, 2.11 | 5,336 |
| `passage_arist_da_2_12` | Aristotle, De anima, 2.12 | 1,977 |
| `passage_arist_da_2_2` | Aristotle, De anima, 2.2 | 4,637 |
| `passage_arist_da_2_3` | Aristotle, De anima, 2.3 | 2,856 |
| `passage_arist_da_2_4` | Aristotle, De anima, 2.4 | 6,160 |
| `passage_arist_da_2_5` | Aristotle, De anima, 2.5 | 4,135 |
| `passage_arist_da_2_6` | Aristotle, De anima, 2.6 | 1,043 |
| `passage_arist_da_2_7` | Aristotle, De anima, 2.7 | 4,168 |
| `passage_arist_da_2_8` | Aristotle, De anima, 2.8 | 5,733 |
| `passage_arist_da_2_9` | Aristotle, De anima, 2.9 | 3,561 |
| `passage_arist_da_3_1` | Aristotle, De anima, 3.1 | 3,026 |
| `passage_arist_da_3_10` | Aristotle, De anima, 3.10 | 2,996 |
| `passage_arist_da_3_11` | Aristotle, De anima, 3.11 | 1,210 |
| `passage_arist_da_3_12` | Aristotle, De anima, 3.12 | 2,987 |
| `passage_arist_da_3_13` | Aristotle, De anima, 3.13 | 2,140 |
| `passage_arist_da_3_2` | Aristotle, De anima, 3.2 | 5,555 |
| `passage_arist_da_3_3` | Aristotle, De anima, 3.3 | 6,192 |
| `passage_arist_da_3_4` | Aristotle, De anima, 3.4 | 3,448 |
| `passage_arist_da_3_5` | Aristotle, De anima, 3.5 | 877 |
| `passage_arist_da_3_6` | Aristotle, De anima, 3.6 | 2,040 |
| `passage_arist_da_3_7` | Aristotle, De anima, 3.7 | 2,627 |
| `passage_arist_da_3_8` | Aristotle, De anima, 3.8 | 1,233 |
| `passage_arist_da_3_9` | Aristotle, De anima, 3.9 | 3,147 |

### Aristotle — De interpretatione

- **Language:** Greek
- **Passages:** 29
- **Characters:** 35,482
- **Canonical ID:** `first1k:tlg0086.tlg017.1st1K-grc1`

| node_id | label | chars |
|---------|-------|-------|
| `passage_arist_di_1_1` | Aristotle, De interpretatione, 1.1 | 103 |
| `passage_arist_di_1_3` | Aristotle, De interpretatione, 1.3 | 844 |
| `passage_arist_di_10_11` | Aristotle, De interpretatione, 10.11 | 865 |
| `passage_arist_di_10_15` | Aristotle, De interpretatione, 10.15 | 549 |
| `passage_arist_di_10_17` | Aristotle, De interpretatione, 10.17 | 648 |
| `passage_arist_di_10_2` | Aristotle, De interpretatione, 10.2 | 2,921 |
| `passage_arist_di_11_2` | Aristotle, De interpretatione, 11.2 | 1,002 |
| `passage_arist_di_11_5` | Aristotle, De interpretatione, 11.5 | 758 |
| `passage_arist_di_11_7` | Aristotle, De interpretatione, 11.7 | 1,659 |
| `passage_arist_di_12_2` | Aristotle, De interpretatione, 12.2 | 3,364 |
| `passage_arist_di_13_11` | Aristotle, De interpretatione, 13.11 | 2,109 |
| `passage_arist_di_13_2` | Aristotle, De interpretatione, 13.2 | 830 |
| `passage_arist_di_13_4` | Aristotle, De interpretatione, 13.4 | 2,100 |
| `passage_arist_di_14_2` | Aristotle, De interpretatione, 14.2 | 4,202 |
| `passage_arist_di_2_2` | Aristotle, De interpretatione, 2.2 | 610 |
| `passage_arist_di_2_4` | Aristotle, De interpretatione, 2.4 | 466 |
| `passage_arist_di_3_1` | Aristotle, De interpretatione, 3.1 | 319 |
| `passage_arist_di_3_3` | Aristotle, De interpretatione, 3.3 | 734 |
| `passage_arist_di_4_2` | Aristotle, De interpretatione, 4.2 | 421 |
| `passage_arist_di_4_4` | Aristotle, De interpretatione, 4.4 | 343 |
| `passage_arist_di_5_2` | Aristotle, De interpretatione, 5.2 | 906 |
| `passage_arist_di_6_2` | Aristotle, De interpretatione, 6.2 | 649 |
| `passage_arist_di_7_12` | Aristotle, De interpretatione, 7.12 | 755 |
| `passage_arist_di_7_2` | Aristotle, De interpretatione, 7.2 | 2,226 |
| `passage_arist_di_8_2` | Aristotle, De interpretatione, 8.2 | 842 |
| `passage_arist_di_9_12` | Aristotle, De interpretatione, 9.12 | 867 |
| `passage_arist_di_9_15` | Aristotle, De interpretatione, 9.15 | 1,179 |
| `passage_arist_di_9_2` | Aristotle, De interpretatione, 9.2 | 2,103 |
| `passage_arist_di_9_9` | Aristotle, De interpretatione, 9.9 | 1,108 |

### Augustine — Libellus Adversus Fulgentium Donatistam

- **Language:** Latin
- **Passages:** 26
- **Characters:** 36,423
- **Canonical ID:** `urn:cts:latinLit:stoa0040.adv_fulg`

| node_id | label | chars |
|---------|-------|-------|
| `passage_aug_fulg_1` | Augustine, Libellus Adversus Fulgentium Donatistam, Augu. 1 | 1,386 |
| `passage_aug_fulg_10` | Augustine, Libellus Adversus Fulgentium Donatistam, Augu. 10 | 1,439 |
| `passage_aug_fulg_11` | Augustine, Libellus Adversus Fulgentium Donatistam, Augu. 11 | 1,463 |
| `passage_aug_fulg_12` | Augustine, Libellus Adversus Fulgentium Donatistam, Augu. 12 | 1,484 |
| `passage_aug_fulg_13` | Augustine, Libellus Adversus Fulgentium Donatistam, Augu. 13 | 1,490 |
| `passage_aug_fulg_14` | Augustine, Libellus Adversus Fulgentium Donatistam, Augu. 14 | 1,431 |
| `passage_aug_fulg_15` | Augustine, Libellus Adversus Fulgentium Donatistam, Augu. 15 | 1,431 |
| `passage_aug_fulg_16` | Augustine, Libellus Adversus Fulgentium Donatistam, Augu. 16 | 1,444 |
| `passage_aug_fulg_17` | Augustine, Libellus Adversus Fulgentium Donatistam, Augu. 17 | 1,320 |
| `passage_aug_fulg_18` | Augustine, Libellus Adversus Fulgentium Donatistam, Augu. 18 | 1,325 |
| `passage_aug_fulg_19` | Augustine, Libellus Adversus Fulgentium Donatistam, Augu. 19 | 1,474 |
| `passage_aug_fulg_2` | Augustine, Libellus Adversus Fulgentium Donatistam, Augu. 2 | 1,278 |
| `passage_aug_fulg_20` | Augustine, Libellus Adversus Fulgentium Donatistam, Augu. 20 | 1,304 |
| `passage_aug_fulg_21` | Augustine, Libellus Adversus Fulgentium Donatistam, Augu. 21 | 1,498 |
| `passage_aug_fulg_22` | Augustine, Libellus Adversus Fulgentium Donatistam, Augu. 22 | 1,381 |
| `passage_aug_fulg_23` | Augustine, Libellus Adversus Fulgentium Donatistam, Augu. 23 | 1,486 |
| `passage_aug_fulg_24` | Augustine, Libellus Adversus Fulgentium Donatistam, Augu. 24 | 1,374 |
| `passage_aug_fulg_25` | Augustine, Libellus Adversus Fulgentium Donatistam, Augu. 25 | 1,494 |
| `passage_aug_fulg_26` | Augustine, Libellus Adversus Fulgentium Donatistam, Augu. 26 | 1,243 |
| `passage_aug_fulg_3` | Augustine, Libellus Adversus Fulgentium Donatistam, Augu. 3 | 1,316 |
| `passage_aug_fulg_4` | Augustine, Libellus Adversus Fulgentium Donatistam, Augu. 4 | 1,420 |
| `passage_aug_fulg_5` | Augustine, Libellus Adversus Fulgentium Donatistam, Augu. 5 | 1,323 |
| `passage_aug_fulg_6` | Augustine, Libellus Adversus Fulgentium Donatistam, Augu. 6 | 1,258 |
| `passage_aug_fulg_7` | Augustine, Libellus Adversus Fulgentium Donatistam, Augu. 7 | 1,449 |
| `passage_aug_fulg_8` | Augustine, Libellus Adversus Fulgentium Donatistam, Augu. 8 | 1,478 |
| `passage_aug_fulg_9` | Augustine, Libellus Adversus Fulgentium Donatistam, Augu. 9 | 1,434 |

### Augustine — De Gratia et Libero Arbitrio

- **Language:** Latin
- **Passages:** 25
- **Characters:** 119,507
- **Canonical ID:** `urn:cts:latinLit:stoa0040.stoa044`

| node_id | label | chars |
|---------|-------|-------|
| `passage_aug_grat_1_1` | Augustine, De Gratia et Libero Arbitrio, Book 1, Section 1.1 | 4,919 |
| `passage_aug_grat_1_10` | Augustine, De Gratia et Libero Arbitrio, Book 1, Section 1.10 | 5,012 |
| `passage_aug_grat_1_11` | Augustine, De Gratia et Libero Arbitrio, Book 1, Section 1.11 | 5,007 |
| `passage_aug_grat_1_12` | Augustine, De Gratia et Libero Arbitrio, Book 1, Section 1.12 | 4,986 |
| `passage_aug_grat_1_13` | Augustine, De Gratia et Libero Arbitrio, Book 1, Section 1.13 | 4,983 |
| `passage_aug_grat_1_14` | Augustine, De Gratia et Libero Arbitrio, Book 1, Section 1.14 | 4,983 |
| `passage_aug_grat_1_15` | Augustine, De Gratia et Libero Arbitrio, Book 1, Section 1.15 | 5,001 |
| `passage_aug_grat_1_16` | Augustine, De Gratia et Libero Arbitrio, Book 1, Section 1.16 | 4,860 |
| `passage_aug_grat_1_17` | Augustine, De Gratia et Libero Arbitrio, Book 1, Section 1.17 | 4,879 |
| `passage_aug_grat_1_18` | Augustine, De Gratia et Libero Arbitrio, Book 1, Section 1.18 | 4,688 |
| `passage_aug_grat_1_19` | Augustine, De Gratia et Libero Arbitrio, Book 1, Section 1.19 | 4,836 |
| `passage_aug_grat_1_2` | Augustine, De Gratia et Libero Arbitrio, Book 1, Section 1.2 | 4,931 |
| `passage_aug_grat_1_20` | Augustine, De Gratia et Libero Arbitrio, Book 1, Section 1.20 | 5,035 |
| `passage_aug_grat_1_21` | Augustine, De Gratia et Libero Arbitrio, Book 1, Section 1.21 | 4,751 |
| `passage_aug_grat_1_22` | Augustine, De Gratia et Libero Arbitrio, Book 1, Section 1.22 | 5,010 |
| `passage_aug_grat_1_23` | Augustine, De Gratia et Libero Arbitrio, Book 1, Section 1.23 | 5,011 |
| `passage_aug_grat_1_24` | Augustine, De Gratia et Libero Arbitrio, Book 1, Section 1.24 | 5,254 |
| `passage_aug_grat_1_25` | Augustine, De Gratia et Libero Arbitrio, Book 1, Section 1.25 | 905 |
| `passage_aug_grat_1_3` | Augustine, De Gratia et Libero Arbitrio, Book 1, Section 1.3 | 4,988 |
| `passage_aug_grat_1_4` | Augustine, De Gratia et Libero Arbitrio, Book 1, Section 1.4 | 5,020 |
| `passage_aug_grat_1_5` | Augustine, De Gratia et Libero Arbitrio, Book 1, Section 1.5 | 4,995 |
| `passage_aug_grat_1_6` | Augustine, De Gratia et Libero Arbitrio, Book 1, Section 1.6 | 4,858 |
| `passage_aug_grat_1_7` | Augustine, De Gratia et Libero Arbitrio, Book 1, Section 1.7 | 4,843 |
| `passage_aug_grat_1_8` | Augustine, De Gratia et Libero Arbitrio, Book 1, Section 1.8 | 4,775 |
| `passage_aug_grat_1_9` | Augustine, De Gratia et Libero Arbitrio, Book 1, Section 1.9 | 4,977 |

### Gregory of Nazianzus — De Filio (Orat. 29)

- **Language:** Greek
- **Passages:** 21
- **Characters:** 29,009
- **Canonical ID:** `urn:cts:greekLit:tlg2022.tlg009`

| node_id | label | chars |
|---------|-------|-------|
| `passage_greg_naz_009_1` | Gregory of Nazianzus, De Filio (Orat. 29), PG 35.1 | 1,216 |
| `passage_greg_naz_009_10` | Gregory of Nazianzus, De Filio (Orat. 29), PG 35.10 | 1,186 |
| `passage_greg_naz_009_11` | Gregory of Nazianzus, De Filio (Orat. 29), PG 35.11 | 1,365 |
| `passage_greg_naz_009_12` | Gregory of Nazianzus, De Filio (Orat. 29), PG 35.12 | 1,163 |
| `passage_greg_naz_009_13` | Gregory of Nazianzus, De Filio (Orat. 29), PG 35.13 | 1,388 |
| `passage_greg_naz_009_14` | Gregory of Nazianzus, De Filio (Orat. 29), PG 35.14 | 1,903 |
| `passage_greg_naz_009_15` | Gregory of Nazianzus, De Filio (Orat. 29), PG 35.15 | 935 |
| `passage_greg_naz_009_16` | Gregory of Nazianzus, De Filio (Orat. 29), PG 35.16 | 1,419 |
| `passage_greg_naz_009_17` | Gregory of Nazianzus, De Filio (Orat. 29), PG 35.17 | 1,243 |
| `passage_greg_naz_009_18` | Gregory of Nazianzus, De Filio (Orat. 29), PG 35.18 | 1,501 |
| `passage_greg_naz_009_19` | Gregory of Nazianzus, De Filio (Orat. 29), PG 35.19 | 1,265 |
| `passage_greg_naz_009_2` | Gregory of Nazianzus, De Filio (Orat. 29), PG 35.2 | 1,468 |
| `passage_greg_naz_009_20` | Gregory of Nazianzus, De Filio (Orat. 29), PG 35.20 | 2,141 |
| `passage_greg_naz_009_21` | Gregory of Nazianzus, De Filio (Orat. 29), PG 35.21 | 1,384 |
| `passage_greg_naz_009_3` | Gregory of Nazianzus, De Filio (Orat. 29), PG 35.3 | 1,084 |
| `passage_greg_naz_009_4` | Gregory of Nazianzus, De Filio (Orat. 29), PG 35.4 | 950 |
| `passage_greg_naz_009_5` | Gregory of Nazianzus, De Filio (Orat. 29), PG 35.5 | 1,208 |
| `passage_greg_naz_009_6` | Gregory of Nazianzus, De Filio (Orat. 29), PG 35.6 | 1,853 |
| `passage_greg_naz_009_7` | Gregory of Nazianzus, De Filio (Orat. 29), PG 35.7 | 704 |
| `passage_greg_naz_009_8` | Gregory of Nazianzus, De Filio (Orat. 29), PG 35.8 | 1,596 |
| `passage_greg_naz_009_9` | Gregory of Nazianzus, De Filio (Orat. 29), PG 35.9 | 2,037 |

### Gregory of Nazianzus — De Filio (Orat. 30)

- **Language:** Greek
- **Passages:** 21
- **Characters:** 29,118
- **Canonical ID:** `urn:cts:greekLit:tlg2022.tlg010`

| node_id | label | chars |
|---------|-------|-------|
| `passage_greg_naz_010_1` | Gregory of Nazianzus, De Filio (Orat. 30), Greg. 1 | 778 |
| `passage_greg_naz_010_10` | Gregory of Nazianzus, De Filio (Orat. 30), Greg. 10 | 1,619 |
| `passage_greg_naz_010_11` | Gregory of Nazianzus, De Filio (Orat. 30), Greg. 11 | 2,156 |
| `passage_greg_naz_010_12` | Gregory of Nazianzus, De Filio (Orat. 30), Greg. 12 | 2,039 |
| `passage_greg_naz_010_13` | Gregory of Nazianzus, De Filio (Orat. 30), Greg. 13 | 2,084 |
| `passage_greg_naz_010_14` | Gregory of Nazianzus, De Filio (Orat. 30), Greg. 14 | 1,025 |
| `passage_greg_naz_010_15` | Gregory of Nazianzus, De Filio (Orat. 30), Greg. 15 | 1,058 |
| `passage_greg_naz_010_16` | Gregory of Nazianzus, De Filio (Orat. 30), Greg. 16 | 1,396 |
| `passage_greg_naz_010_17` | Gregory of Nazianzus, De Filio (Orat. 30), Greg. 17 | 876 |
| `passage_greg_naz_010_18` | Gregory of Nazianzus, De Filio (Orat. 30), Greg. 18 | 910 |
| `passage_greg_naz_010_19` | Gregory of Nazianzus, De Filio (Orat. 30), Greg. 19 | 1,146 |
| `passage_greg_naz_010_2` | Gregory of Nazianzus, De Filio (Orat. 30), Greg. 2 | 1,533 |
| `passage_greg_naz_010_20` | Gregory of Nazianzus, De Filio (Orat. 30), Greg. 20 | 2,530 |
| `passage_greg_naz_010_21` | Gregory of Nazianzus, De Filio (Orat. 30), Greg. 21 | 1,996 |
| `passage_greg_naz_010_3` | Gregory of Nazianzus, De Filio (Orat. 30), Greg. 3 | 774 |
| `passage_greg_naz_010_4` | Gregory of Nazianzus, De Filio (Orat. 30), Greg. 4 | 1,336 |
| `passage_greg_naz_010_5` | Gregory of Nazianzus, De Filio (Orat. 30), Greg. 5 | 1,652 |
| `passage_greg_naz_010_6` | Gregory of Nazianzus, De Filio (Orat. 30), Greg. 6 | 2,314 |
| `passage_greg_naz_010_7` | Gregory of Nazianzus, De Filio (Orat. 30), Greg. 7 | 894 |
| `passage_greg_naz_010_8` | Gregory of Nazianzus, De Filio (Orat. 30), Greg. 8 | 713 |
| `passage_greg_naz_010_9` | Gregory of Nazianzus, De Filio (Orat. 30), Greg. 9 | 289 |

### Augustine — De Correptione et Gratia

- **Language:** Latin
- **Passages:** 21
- **Characters:** 103,272
- **Canonical ID:** `urn:cts:latinLit:stoa0040.stoa045`

| node_id | label | chars |
|---------|-------|-------|
| `passage_aug_corrept_1_1` | Augustine, De Correptione et Gratia, PL 44.1.1 | 5,026 |
| `passage_aug_corrept_1_10` | Augustine, De Correptione et Gratia, PL 44.1.10 | 4,990 |
| `passage_aug_corrept_1_11` | Augustine, De Correptione et Gratia, PL 44.1.11 | 5,008 |
| `passage_aug_corrept_1_12` | Augustine, De Correptione et Gratia, PL 44.1.12 | 4,944 |
| `passage_aug_corrept_1_13` | Augustine, De Correptione et Gratia, PL 44.1.13 | 4,973 |
| `passage_aug_corrept_1_14` | Augustine, De Correptione et Gratia, PL 44.1.14 | 4,888 |
| `passage_aug_corrept_1_15` | Augustine, De Correptione et Gratia, PL 44.1.15 | 4,977 |
| `passage_aug_corrept_1_16` | Augustine, De Correptione et Gratia, PL 44.1.16 | 4,585 |
| `passage_aug_corrept_1_17` | Augustine, De Correptione et Gratia, PL 44.1.17 | 4,725 |
| `passage_aug_corrept_1_18` | Augustine, De Correptione et Gratia, PL 44.1.18 | 4,631 |
| `passage_aug_corrept_1_19` | Augustine, De Correptione et Gratia, PL 44.1.19 | 5,008 |
| `passage_aug_corrept_1_2` | Augustine, De Correptione et Gratia, PL 44.1.2 | 5,015 |
| `passage_aug_corrept_1_20` | Augustine, De Correptione et Gratia, PL 44.1.20 | 4,749 |
| `passage_aug_corrept_1_21` | Augustine, De Correptione et Gratia, PL 44.1.21 | 5,138 |
| `passage_aug_corrept_1_3` | Augustine, De Correptione et Gratia, PL 44.1.3 | 4,942 |
| `passage_aug_corrept_1_4` | Augustine, De Correptione et Gratia, PL 44.1.4 | 4,972 |
| `passage_aug_corrept_1_5` | Augustine, De Correptione et Gratia, PL 44.1.5 | 4,964 |
| `passage_aug_corrept_1_6` | Augustine, De Correptione et Gratia, PL 44.1.6 | 5,049 |
| `passage_aug_corrept_1_7` | Augustine, De Correptione et Gratia, PL 44.1.7 | 4,808 |
| `passage_aug_corrept_1_8` | Augustine, De Correptione et Gratia, PL 44.1.8 | 4,906 |
| `passage_aug_corrept_1_9` | Augustine, De Correptione et Gratia, PL 44.1.9 | 4,974 |

### Plutarch — De fato

- **Language:** Greek
- **Passages:** 19
- **Characters:** 24,677
- **Canonical ID:** `urn:cts:greekLit:tlg0007.tlg099`

| node_id | label | chars |
|---------|-------|-------|
| `passage_plut_fat_1_s1` | Plutarch, De fato, Mor. 1 | 1,307 |
| `passage_plut_fat_10_s10` | Plutarch, De fato, Mor. 10 | 1,254 |
| `passage_plut_fat_11_s11` | Plutarch, De fato, Mor. 11 | 1,051 |
| `passage_plut_fat_12_s12` | Plutarch, De fato, Mor. 12 | 1,439 |
| `passage_plut_fat_13_s13` | Plutarch, De fato, Mor. 13 | 1,497 |
| `passage_plut_fat_14_s14` | Plutarch, De fato, Mor. 14 | 1,389 |
| `passage_plut_fat_15_s15` | Plutarch, De fato, Mor. 15 | 1,265 |
| `passage_plut_fat_16_s16` | Plutarch, De fato, Mor. 16 | 1,514 |
| `passage_plut_fat_17_s17` | Plutarch, De fato, Mor. 17 | 1,386 |
| `passage_plut_fat_18_s18` | Plutarch, De fato, Mor. 18 | 1,323 |
| `passage_plut_fat_19_s19` | Plutarch, De fato, Mor. 19 | 238 |
| `passage_plut_fat_2_s2` | Plutarch, De fato, Mor. 2 | 1,449 |
| `passage_plut_fat_3_s3` | Plutarch, De fato, Mor. 3 | 1,428 |
| `passage_plut_fat_4_s4` | Plutarch, De fato, Mor. 4 | 1,102 |
| `passage_plut_fat_5_s5` | Plutarch, De fato, Mor. 5 | 1,426 |
| `passage_plut_fat_6_s6` | Plutarch, De fato, Mor. 6 | 1,299 |
| `passage_plut_fat_7_s7` | Plutarch, De fato, Mor. 7 | 1,452 |
| `passage_plut_fat_8_s8` | Plutarch, De fato, Mor. 8 | 1,472 |
| `passage_plut_fat_9_s9` | Plutarch, De fato, Mor. 9 | 1,386 |

### Justin Martyr — Apologia Secunda

- **Language:** Greek
- **Passages:** 15
- **Characters:** 21,198
- **Canonical ID:** `urn:cts:greekLit:tlg0645.tlg002`

| node_id | label | chars |
|---------|-------|-------|
| `passage_just_apol2_1` | Justin Martyr, Apologia Secunda, 1 | 950 |
| `passage_just_apol2_10` | Justin Martyr, Apologia Secunda, 10 | 1,622 |
| `passage_just_apol2_11` | Justin Martyr, Apologia Secunda, 11 | 1,588 |
| `passage_just_apol2_12` | Justin Martyr, Apologia Secunda, 12 | 1,971 |
| `passage_just_apol2_13` | Justin Martyr, Apologia Secunda, 13 | 1,156 |
| `passage_just_apol2_14` | Justin Martyr, Apologia Secunda, 14 | 675 |
| `passage_just_apol2_15` | Justin Martyr, Apologia Secunda, 15 | 749 |
| `passage_just_apol2_2` | Justin Martyr, Apologia Secunda, 2 | 3,296 |
| `passage_just_apol2_3` | Justin Martyr, Apologia Secunda, 3 | 829 |
| `passage_just_apol2_4` | Justin Martyr, Apologia Secunda, 4 | 1,339 |
| `passage_just_apol2_5` | Justin Martyr, Apologia Secunda, 5 | 1,285 |
| `passage_just_apol2_6` | Justin Martyr, Apologia Secunda, 6 | 2,117 |
| `passage_just_apol2_7` | Justin Martyr, Apologia Secunda, 7 | 951 |
| `passage_just_apol2_8` | Justin Martyr, Apologia Secunda, 8 | 1,430 |
| `passage_just_apol2_9` | Justin Martyr, Apologia Secunda, 9 | 1,240 |

### Gregory of Nazianzus — Adversus Eunomianos (orat. 27)

- **Language:** Greek
- **Passages:** 9
- **Characters:** 13,056
- **Canonical ID:** `urn:cts:greekLit:tlg2022.tlg007`

| node_id | label | chars |
|---------|-------|-------|
| `passage_greg_naz_007_1` | Gregory of Nazianzus, Adversus Eunomianos (orat. 27), PG 35.1 | 808 |
| `passage_greg_naz_007_2` | Gregory of Nazianzus, Adversus Eunomianos (orat. 27), PG 35.2 | 1,624 |
| `passage_greg_naz_007_3` | Gregory of Nazianzus, Adversus Eunomianos (orat. 27), PG 35.3 | 1,445 |
| `passage_greg_naz_007_4` | Gregory of Nazianzus, Adversus Eunomianos (orat. 27), PG 35.4 | 1,053 |
| `passage_greg_naz_007_5` | Gregory of Nazianzus, Adversus Eunomianos (orat. 27), PG 35.5 | 1,661 |
| `passage_greg_naz_007_6` | Gregory of Nazianzus, Adversus Eunomianos (orat. 27), PG 35.6 | 1,047 |
| `passage_greg_naz_007_7` | Gregory of Nazianzus, Adversus Eunomianos (orat. 27), PG 35.7 | 1,443 |
| `passage_greg_naz_007_8` | Gregory of Nazianzus, Adversus Eunomianos (orat. 27), PG 35.8 | 1,700 |
| `passage_greg_naz_007_9` | Gregory of Nazianzus, Adversus Eunomianos (orat. 27), PG 35.9 | 2,275 |

### Aspasius — In Ethica Nicomachea Commentaria

- **Language:** Greek
- **Passages:** 6
- **Characters:** 411,890
- **Canonical ID:** `aspasius_in_en_cag`

| node_id | label | chars |
|---------|-------|-------|
| `passage_aspasius_1` | Aspasius, In Ethica Nicomachea Commentaria, 1 | 75,680 |
| `passage_aspasius_2` | Aspasius, In Ethica Nicomachea Commentaria, 2 | 46,453 |
| `passage_aspasius_3` | Aspasius, In Ethica Nicomachea Commentaria, 3 | 86,641 |
| `passage_aspasius_4` | Aspasius, In Ethica Nicomachea Commentaria, 4 | 70,561 |
| `passage_aspasius_5` | Aspasius, In Ethica Nicomachea Commentaria, 5 | 68,768 |
| `passage_aspasius_6` | Aspasius, In Ethica Nicomachea Commentaria, 6 | 63,787 |

### Plutarch — De Communibus Notitiis adversus Stoicos

- **Language:** Greek
- **Passages:** 6
- **Characters:** 7,236
- **Canonical ID:** `urn:cts:greekLit:tlg0007.tlg135`

| node_id | label | chars |
|---------|-------|-------|
| `passage_plut_cn_1` | Plutarch, De Communibus Notitiis adversus Stoicos, 1 | 276 |
| `passage_plut_cn_2` | Plutarch, De Communibus Notitiis adversus Stoicos, 2 | 344 |
| `passage_plut_cn_3` | Plutarch, De Communibus Notitiis adversus Stoicos, 3 | 1,051 |
| `passage_plut_cn_4` | Plutarch, De Communibus Notitiis adversus Stoicos, 4 | 2,391 |
| `passage_plut_cn_5` | Plutarch, De Communibus Notitiis adversus Stoicos, 5 | 2,372 |
| `passage_plut_cn_6` | Plutarch, De Communibus Notitiis adversus Stoicos, 6 | 802 |

### Didache — Didache - Complete Works

- **Language:** Greek
- **Passages:** 6
- **Characters:** 11,668
- **Canonical ID:** `urn:cts:greekLit:tlg1311.tlg001`

| node_id | label | chars |
|---------|-------|-------|
| `passage_didache_1` | Didache, Didache - Complete Works, Did. 1 | 2,114 |
| `passage_didache_2` | Didache, Didache - Complete Works, Did. 2 | 2,113 |
| `passage_didache_3` | Didache, Didache - Complete Works, Did. 3 | 2,124 |
| `passage_didache_4` | Didache, Didache - Complete Works, Did. 4 | 2,088 |
| `passage_didache_5` | Didache, Didache - Complete Works, Did. 5 | 2,098 |
| `passage_didache_6` | Didache, Didache - Complete Works, Did. 6 | 1,131 |

### Calcidius — Commentarius in Platonis Timaeum

- **Language:** Latin
- **Passages:** 5
- **Characters:** 338
- **Canonical ID:** `digiliblt:DLT000607`

| node_id | label | chars |
|---------|-------|-------|
| `passage_calcid_142` | Calcidius, Commentarius in Platonis Timaeum, In Tim. 142 | 61 |
| `passage_calcid_143` | Calcidius, Commentarius in Platonis Timaeum, In Tim. 143 | 64 |
| `passage_calcid_144` | Calcidius, Commentarius in Platonis Timaeum, In Tim. 144 | 63 |
| `passage_calcid_145` | Calcidius, Commentarius in Platonis Timaeum, In Tim. 145 | 71 |
| `passage_calcid_146` | Calcidius, Commentarius in Platonis Timaeum, In Tim. 146 | 79 |

### Alcinous — Handbook of Platonism (Didaskalikos)

- **Language:** Greek
- **Passages:** 1
- **Characters:** 8,433
- **Canonical ID:** `urn:cts:greekLit:tlg0720.tlg001`

| node_id | label | chars |
|---------|-------|-------|
| `passage_alcin_alcinous_untitled_full_text` | Alcinous, Handbook of Platonism (Didaskalikos), Didasc. 1 | 8,433 |

### Aulus Gellius — Noctes Atticae

- **Language:** Latin
- **Passages:** 1
- **Characters:** 3,991
- **Canonical ID:** `urn:cts:latinLit:phi1254.phi001`

| node_id | label | chars |
|---------|-------|-------|
| `passage_gellius_7_2` | Aulus Gellius, Noctes Atticae, 7.2 | 3,991 |

### Aristotle — Nicomachean Ethics

- **Language:** Greek
- **Passages:** 1
- **Characters:** 369

| node_id | label | chars |
|---------|-------|-------|
| `passage_aristotle_en_iii_1_1110a15` | EN III.1, 1110a15-17 (ἐπʼ αὐτῷ καὶ τὸ πράττειν καὶ μή) | 369 |
