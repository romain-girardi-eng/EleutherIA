# CORRECTIONS TO APPLY - ACTIONABLE LIST

**Date:** 2025-10-21
**Status:** Ready to apply manually

---

## SOURCES TO REMOVE

### 1. Clitomachus (person_clitomachus_of_carthage_7l2m4o10)

**REMOVE from ancient_sources:**
```
"Diogenes Laertius, Lives IV.67 (brief biography)"
```
**Reason:** Pure biography, does not discuss Clitomachus' role in transmitting free will arguments

---

### 2. Diogenianos (person_diogenianos_8m3n5p21)

**REMOVE from ancient_sources:**
```
"Cicero, De Fato 12-13 (possible allusion to Diogenianus' etymological argument)"
```
**Reason:** Speculation - no evidence Cicero mentions Diogenianos by name

---

### 3. Pseudo-Dionysius Argument (argument_pseudodionysiuss_hierarchical_causation_argument_e0d73eb9)

**REMOVE from ancient_sources:**
```
"Pseudo-Dionysius, De Caelesti Hierarchia (Celestial Hierarchy) (PG 3:119-370; SC 58bis)"
"Pseudo-Dionysius, De Ecclesiastica Hierarchia (Ecclesiastical Hierarchy) (PG 3:369-584)"
"Pseudo-Dionysius, De Mystica Theologia (Mystical Theology) (PG 3:997-1064)"
```
**Reason:** These three works are about hierarchy and apophatic theology, NOT about free will or causation

**KEEP:**
- De Divinis Nominibus 4.18-35 (on causation and evil)
- Epistula VI to Sopatros (on evil)
- Proclus, Elements of Theology (source for causation theory)

---

### 4. Firmicus Maternus (person_firmicus_maternus_2q7r9t65)

**REMOVE from ancient_sources:**
```
"Firmicus Maternus, De Errore Profanarum Religionum (c. 346-350 CE)"
```
**Reason:** Anti-pagan polemic, not about fate or free will. His free will relevance is ONLY in Mathesis.

---

### 5. Tertullian Anti-Marcionite Argument (argument_tertullians_antimarcionite_argument_for_free_will_f49cad73)

**REMOVE from ancient_sources (move to person node if relevant):**
```
"Tertullian, De Anima 20-22, 40 (CCL 2; PL 2:701-752)"
"Tertullian, De Exhortatione Castitatis 1-2 (CCL 2; PL 2:913-930)"
"Tertullian, De Paenitentia 3 (CCL 1; PL 1:1227-1248)"
"Tertullian, Apologeticum 18, 45 (CCL 1; PL 1:257-536)"
```
**Reason:** This is the ANTI-MARCIONITE ARGUMENT node - should only contain Adversus Marcionem

**KEEP:**
- Tertullian, Adversus Marcionem II.5-9, V.17 (the specific anti-Marcionite argument)

**NOTE:** The person node for Tertullian already has "De Anima" generally, so no need to add anything there.

---

### 6. Bardesanes (person_bardesanes_the_syrian_3r8s0u76)

**CONSIDER REMOVING (uncertain):**
```
"Ephrem the Syrian, Prose Refutations of Mani, Marcion and Bardaisan"
```
**Reason:** Cannot verify from PhD files that Ephrem's refutations specifically discuss Bardesanes' FREE WILL doctrine (may be about other theological errors)

**Decision:** REMOVE to be safe (following no-hallucination rule)

---

## SOURCES TO ADD

### 7. Pelagius (person_pelagius_british_monk_4ba38f92)

**ADD to ancient_sources (Pelagius' own writings):**
```
"Pelagius, Epistula ad Demetriadem (Letter to Demetrias) (PL 30:15-45; possibly spurious, perhaps by Julian of Eclanum)"
"Pelagius, Expositio in Epistulam Pauli ad Romanos (Commentary on Romans, fragments survive)"
"Pelagius, Libellus Fidei (Statement of Faith to Pope Innocent I; fragments in Augustine)"
```

**KEEP existing (Augustine/Jerome polemics - secondary sources about Pelagius):**
- Augustine, De Natura et Gratia
- Augustine, De Gratia Christi et de Peccato Originali
- Jerome, Dialogus adversus Pelagianos

---

## SUMMARY

**Total corrections:** 7 nodes
**Sources to remove:** 12 citations
**Sources to add:** 3 citations (Pelagius' own works)

**Nodes verified as GOOD (no changes needed):**
- Celestius ✓
- Nemesius ✓
- Prosper of Aquitaine ✓

---

**Next step:** Apply these corrections manually to ancient_free_will_database.json

**Generated:** 2025-10-21
