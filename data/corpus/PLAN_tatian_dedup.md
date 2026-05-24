# Tatian Dedup Plan

## Work

`urn_cts_greeklit_tlg1766_tlg001_grc` — Tatian, *Oratio ad Graecos* (Oration to the Greeks)

**Stats:** 98 total passages · 42 unique `cts_urn`s · 56 duplicate passages · 111 total citations

The work was ingested multiple times. For each `cts_urn` that appears more than once, one
passage must be kept and the others deleted. Because `passage_citations.passage_id` is a
foreign key, all citations on passages-to-delete must be re-pointed to the kept passage
before deletion.

## Decision rule

For each duplicate group:
1. Keep the passage with the **highest citation count** (most scholarly linking).
2. Tiebreak: keep the passage with the **lowest `sequence_number`** (earliest ingest).

## Dedup table

| `cts_urn` | Passages (passage_id : seq : citations) | Keep | Re-point citations | Delete |
|-----------|------------------------------------------|------|--------------------|--------|
| `…:1` | `04a012aa` (10001, 1), `98d2f9ed` (10002, 1), `caee9190` (10003, 1) | `04a012aa` (lowest seq, tie) | 2 from `98d2f9ed`, `caee9190` → `04a012aa` | 2 rows |
| `…:2` | `56fa068a` (20001, 1), `cbb585b5` (20002, 1) | `56fa068a` | 1 | 1 |
| `…:3` | `6c3385fb` (30001, 1), `5c2f2a79` (30002, 1), `1954e39f` (30003, 1) | `6c3385fb` | 2 | 2 |
| `…:4` | `d6337b3b` (40001, 1), `f440198a` (40002, 1) | `d6337b3b` | 1 | 1 |
| `…:5` | `3f5fbd39` (50001, 1), `c055123e` (50002, 1) | `3f5fbd39` | 1 | 1 |
| `…:6` | `bea30080` (60001, 1), `dddc0b2d` (60002, 1) | `bea30080` | 1 | 1 |
| `…:7` | `a36c2d9d` (70001, **5**), `56827782` (70002, 1) | `a36c2d9d` (most cits) | 1 | 1 |
| `…:8` | `8ac4c3f3` (80001, **4**), `9049e7c9` (80002, 1), `c5637aac` (80003, 1), `de42fb55` (80004, 1), `f470a2d3` (80005, 1) | `8ac4c3f3` | 4 | 4 |
| `…:9` | `e06ffb4e` (90001, 1), `9f79e224` (90002, 1) | `e06ffb4e` | 1 | 1 |
| `…:10` | `c8077aeb` (100001, 1), `67f85d86` (100002, 1), `2d084d31` (100003, 1) | `c8077aeb` | 2 | 2 |
| `…:11` | `f8ceab87` (110001, **7**), `f0fc5be8` (110002, 1) | `f8ceab87` | 1 | 1 |
| `…:12` | `16167cda` (120001, 1), `9b395079` (120002, 1), `161e51dc` (120003, 1), `9c676659` (120004, 1) | `16167cda` | 3 | 3 |
| `…:13` | `9e1a5801` (130001, 1), `a195bc60` (130002, 1) | `9e1a5801` | 1 | 1 |
| `…:14` | `8e412b53` (140001, 1), `77425415` (140002, 1) | `8e412b53` | 1 | 1 |
| `…:15` | `fdefee1b` (150001, 1), `0ad1bd43` (150002, 1), `2de19140` (150003, 1) | `fdefee1b` | 2 | 2 |
| `…:16` | `ce388f19` (160001, 1), `ee1c8759` (160002, 1) | `ce388f19` | 1 | 1 |
| `…:17` | `c684c41a` (170001, 1), `103575fe` (170002, 1), `96abd640` (170003, 1) | `c684c41a` | 2 | 2 |
| `…:18` | `b8c7e7f9` (180001, 1), `02b9eb09` (180002, 1) | `b8c7e7f9` | 1 | 1 |
| `…:19` | `7cf1609f` (190001, 1), `2bc3ada4` (190002, 1), `f4421893` (190003, 1) | `7cf1609f` | 2 | 2 |
| `…:20` | `e3a3a853` (200001, 1), `abf966e8` (200002, 1) | `e3a3a853` | 1 | 1 |
| `…:21` | `662575cf` (210001, 1), `9b019453` (210002, 1), `3d1d7512` (210003, 1) | `662575cf` | 2 | 2 |
| `…:22` | `6dcfe239` (220001, 1), `63ff5c99` (220002, 1) | `6dcfe239` | 1 | 1 |
| `…:23` | `47437519` (230001, 1), `e0ae5416` (230002, 1) | `47437519` | 1 | 1 |
| `…:25` | `a169384a` (250001, 1), `764b9daa` (250002, 1) | `a169384a` | 1 | 1 |
| `…:26` | `330b4bfc` (260001, 1), `35072cd3` (260002, 1), `842bb2a2` (260003, 1) | `330b4bfc` | 2 | 2 |
| `…:27` | `54589fa1` (270001, 1), `b851c6c6` (270002, 1) | `54589fa1` | 1 | 1 |
| `…:29` | `8cc979d7` (290001, 1), `0b6da01e` (290002, 1) | `8cc979d7` | 1 | 1 |
| `…:31` | `915a040a` (310001, 1), `1e4b0729` (310002, 1), `ba946085` (310003, 1) | `915a040a` | 2 | 2 |
| `…:32` | `f11e9e25` (320001, 1), `80e8fcf5` (320002, 1), `cd7d4168` (320003, 1) | `f11e9e25` | 2 | 2 |
| `…:33` | `ab9edfce` (330001, 1), `25cbef0e` (330002, 1), `e5b22a38` (330003, 1) | `ab9edfce` | 2 | 2 |
| `…:34` | `245a8d4a` (340001, 1), `deacfd2c` (340002, 1), `62f07356` (340003, 1) | `245a8d4a` | 2 | 2 |
| `…:35` | `4b57006b` (350001, 1), `071be711` (350002, 1) | `4b57006b` | 1 | 1 |
| `…:36` | `e3643908` (360001, 1), `abc4d835` (360002, 1) | `e3643908` | 1 | 1 |
| `…:37` | `808cc931` (370001, 1), `bbb59403` (370002, 1) | `808cc931` | 1 | 1 |
| `…:39` | `3c51df53` (390001, 1), `a98b975c` (390002, 1), `32a158e2` (390003, 1) | `3c51df53` | 2 | 2 |
| `…:40` | `890918ec` (400001, 1), `628e5168` (400002, 1) | `890918ec` | 1 | 1 |
| `…:41` | `9a953cc1` (410001, 1), `6a2e7bf0` (410002, 1), `d733e0d8` (410003, 1) | `9a953cc1` | 2 | 2 |

**Totals:**
- Passages to keep: 37 (one per unique cts_urn in the dup groups)
- Citations to re-point: 56 (moved from deleted to kept passage_ids)
- Passage rows to delete: 56

After dedup: 98 - 56 = 42 passages (= 42 unique cts_urns), 111 citations preserved.

## Execution plan

For each duplicate group, in a single transaction per group:
1. `UPDATE free_will.passage_citations SET passage_id = <keep_id> WHERE passage_id IN (<delete_ids>)`
2. Verify no citations remain on delete_ids
3. `DELETE FROM free_will.passages WHERE passage_id IN (<delete_ids>)`

**IMPORTANT:** This plan deletes cited passages. Before executing, re-read the safety rule:
> A DELETE of a cited passage creates a dangling citation — FORBIDDEN unless you first
> re-point those citations to a kept passage.

This plan re-points first, then deletes — the safety rule is satisfied. However, because
this is a destructive multi-row operation, **requires explicit approval before execution**.
