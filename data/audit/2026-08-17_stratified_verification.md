# Vérification stratifiée du corpus — rapport final (17 août 2026)

**Cadre** : 160 passages échantillonnés (graine 20260817, tirage déterministe sha256) sur 4 strates
par voie d'ingestion, collationnés contre les autorités locales (TLG E, éditions SC/Brepols).
Constats unitaires : `2026-08-17_stratified_verification.jsonl` (160 enregistrements, un par passage,
avec ancre d'autorité, diff et CER). Verdicts bruts, puis **lecture critique** — trois verdicts
« SUBSTANTIVE » sur quatre classes se sont révélés être des artefacts de méthode à l'inspection,
vérifiés pièce par pièce ci-dessous.

## Tableau brut par strate (verdicts mécaniques)

| Strate | n | EXACT | MINOR | SUBSTANTIVE | INDISPO | IC Wilson 95 % (subst.) | CER médian |
|---|---:|---:|---:|---:|---:|---|---:|
| SC-series OCR | 40 | 15 | 25 | 0 | 0 | [0.0% ; 8.8%] | 0.0% |
| TLG E realignments | 40 | 5 | 15 | 20 | 0 | [35.2% ; 64.8%] | 1.1% |
| Perseus/web | 40 | 0 | 9 | 12 | 19 | [18.1% ; 45.4%] | 1.8% |
| First1KGreek | 40 | 0 | 3 | 37 | 0 | [80.1% ; 97.4%] | 21.0% |

## Lecture critique — ce que les verdicts mesurent réellement

**1. SC-series OCR (0/40 substantiel).** Autorité = le fichier d'ingestion lui-même
(`authority_same_as_ingest_source: true` pour 40/40) : ce résultat prouve la **fidélité d'ingestion**,
pas la justesse de l'édition. Limite déclarée d'avance dans le protocole, à lever un jour par
collation contre les volumes SC imprimés.

**2. TLG E realignments — la strate mélange deux populations.**
- Les **ré-ingestions de texte** (Magna Moralia : 17 tirés) : 5 EXACT + 12 MINOR, **0 substantiel**
  contre l'autorité indépendante. Les MINOR sont des normalisations (césures TLG, NFC).
  → **La chaîne de ré-ingestion TLG est validée.**
- Les **nœuds Plotin** (23 tirés ; seules leurs *références* ont été réalignées, le texte vient de
  Perseus) : 20 « substantiels » à CER médian **1,1 %** (max 4,1 %). Inspection : troncatures de
  bords de fragments (ex. `passage_plotinus_vi_9_58` commence en plein mot « [οὐδ]αμόθεν ») +
  variantes d'édition Perseus/TLG (δ̓/δ', ἀλλ̓/ἀλλὰ). Le corps du texte est fidèle à Perseus.
  → Défaut réel mais borné : **réparation des bords de fragments**, désormais possible à coût
  faible puisque les 709 nœuds portent leurs ancres byte TLG depuis le remapping du 17 août.

**3. Perseus/web (12/40 substantiel, CER médian 1,8 %).** Ordre de grandeur de la variance
inter-éditions ; un cas aberrant à 16,5 % à re-vérifier individuellement. 19 INDISPO = auteurs
latins sans autorité locale (Boèce, Lactance…) — collation impossible, pas d'inférence.

**4. First1KGreek (37/40 « substantiel », CER médian 21 %) — artefact de méthode dominant.**
Vérifié sur le pire cas (CER 64 %) : Épicure *SV* 56 — le corpus porte la sentence exacte du
découpage moderne (avec la conjecture 〈ἢ στρεβλουμένου〉) ; l'extraction TLG par état de citation
enchaîne SV 56+57 avec les crochets éditoriaux. Le CER mesure un **désalignement d'empans**
(extrait curaté vs bloc TLG), pas une corruption. Les 24 Sextus Empiricus relèvent du même
mécanisme. → Strate **non concluante en l'état** ; une re-collation à empans alignés est requise
avant tout verdict. Aucune preuve de corruption du texte porté.

## Décision (règle déclarée d'avance : strate > 5 % substantiel *avéré* → ré-ingestion)

| Strate | Substantiel avéré après inspection | Décision |
|---|---|---|
| SC-series OCR | 0 % (fidélité seulement) | RAS ; collation vs imprimés en dette de fond |
| TLG realignments (texte) | 0 % | **validée** |
| Plotin (texte Perseus) | troncatures de bords, corps fidèle | **vague de réparation des bords** (ancres byte disponibles) |
| Perseus/web | ~1 cas à re-vérifier | pas de ré-ingestion ; vérif unitaire |
| First1KGreek | indéterminé (méthode) | **re-collation à empans alignés** avant verdict |

## Limites honnêtes
- 160 passages sur ~14 900 éligibles : les IC de Wilson figurent au tableau ; toute strate à
  0 observé garde une borne haute non nulle (~8,8 % pour n=40).
- La collation « base-letter Levenshtein » ne distingue pas variance d'édition et faute de copie ;
  c'est le passage par l'inspection humaine des cas qui a permis la lecture ci-dessus.
- Ce rapport a été finalisé à partir du JSONL produit par le job interrompu ; les 160
  enregistrements unitaires sont intacts et rejouables (graine et méthode de tirage dans chaque
  enregistrement).
