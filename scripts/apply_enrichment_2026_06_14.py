#!/usr/bin/env python3
"""Apply 2026-06-14 enrichment proposals to the KG snapshot (data/kg/{nodes,edges}.jsonl).

Idempotent, backup-first, dry-run by default. Pass --write to mutate.
Scope: 8 dedup merges, 15 Bobzien period reclassifications, 4 new nodes
(3 debates incl. the 'origins of the notion of will' modern-paradigm node + Honorius I),
and the validated wave1/wave2/wave3 edges (wave3 grounded_in remapped to the
in-ontology publication--discusses-->argument convention).
"""
import json, sys, uuid, collections, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
KG = ROOT / "data" / "kg"
PROP = KG / "enrichment_proposals"
WRITE = "--write" in sys.argv
TS = "2026-06-14T00:00:00+00:00"
PROV = "enrichment_2026_06_14"

ont = json.load(open(ROOT / "knowledge graph" / "ontology" / "edge_types.json"))["edge_types"]
ALLOWED_REL = set(ont.keys() if isinstance(ont, dict) else [e["id"] for e in ont]) | {"advanced_in"}
ALLOWED_TYPES = set(json.load(open(ROOT / "knowledge graph" / "ontology" / "node_types.json"))["node_types"].keys())

nodes = {}
norder = []
for line in open(KG / "nodes.jsonl"):
    n = json.loads(line); nodes[n["id"]] = n; norder.append(n["id"])
edges = [json.loads(l) for l in open(KG / "edges.jsonl") if l.strip()]

log = []
def note(m): log.append(m)

# ---- 1. MERGES (canonical <- duplicate) : verified policy ----
MERGES = [
    ("scholar_albrecht_dihle", "scholar_dihle_albrecht"),                       # same person (1923-2020)
    ("pub_amand_1945_fatalisme", "pub_amand_1973_fatalisme_liberte"),           # same monograph (ISBN match)
    ("pub_voelke_1973_idee_volonte", "scholarly_work_voelke_1973_l_id_e_de_volont_dans_le_sto_cisme"),
    ("pub_dihle_1982_theory_of_will", "pub_dihle_1982_theory_will"),
    ("pub_eliasson_2008_notion_eph_hemin_plotinus", "scholarly_work_eliasson_2008_the_notion_of_that_which_depends_on_us_i"),
    ("pub_sharples_2008_accident_determinisme", "scholarly_work_sharples_2008_l_accident_du_d_terminisme_alexandre_d_a"),
    ("pub_sharples_1983_alexander_fate", "scholarly_work_sharples_1983_alex_de_fato"),  # orphan (0 edges)
]
merge_map = {}
for canon, dup in MERGES:
    if canon not in nodes:
        note(f"SKIP merge: canonical missing {canon}"); continue
    if dup not in nodes:
        note(f"SKIP merge: duplicate missing {dup}"); continue
    merge_map[dup] = canon
def resolve(i): return merge_map.get(i, i)

# redirect edges through merge_map
for e in edges:
    for k in ("source", "source_id", "target", "target_id"):
        if e.get(k) in merge_map:
            e[k] = merge_map[e[k]]
# drop self-loops created by merge + dedupe (source,relation,target)
seen = set(); kept = []
dropped_selfloop = dropped_dup = 0
for e in edges:
    s, t, r = e.get("source"), e.get("target"), e.get("relation")
    if s == t:
        dropped_selfloop += 1; continue
    key = (s, r, t)
    if key in seen:
        dropped_dup += 1; continue
    seen.add(key); kept.append(e)
edges = kept
# remove duplicate nodes
for dup in merge_map:
    nodes.pop(dup, None)
note(f"MERGES applied: {len(merge_map)} dup nodes removed; "
     f"{dropped_selfloop} self-loops + {dropped_dup} duplicate edges dropped post-merge")

# ---- 2. BOBZIEN reclassification (period -> Contemporary; type stays 'argument') ----
recl = 0
for nid, n in nodes.items():
    if nid.startswith("argument_bobzien_2001") and n.get("period") != "Contemporary":
        n["period"] = "Contemporary"
        md = n.get("metadata")
        try: md = json.loads(md) if isinstance(md, str) else (md or {})
        except Exception: md = {}
        md["scholarly_reconstruction"] = True
        md["period_reclassified"] = PROV
        n["metadata"] = json.dumps(md, ensure_ascii=False)
        n["updated_at"] = TS
        recl += 1
note(f"BOBZIEN reclassified to Contemporary: {recl}")

# ---- 3. NEW NODES ----
def mknode(nid, typ, label, desc, period, meta):
    assert typ in ALLOWED_TYPES, f"bad type {typ}"
    return {"id": nid, "node_id": nid, "type": typ, "label": label, "description": desc,
            "period": period, "role": None, "school": None, "alternative_names": "[]",
            "metadata": json.dumps(meta, ensure_ascii=False), "created_at": TS, "updated_at": TS}

NEW_NODES = []
# 3a. monothelite-dyothelite controversy (debate)
NEW_NODES.append(mknode(
    "debate_monothelite_dyothelite_controversy", "debate",
    "The Monothelite–Dyothelite Controversy (7th c.)",
    ("The 7th-century Christological dispute over whether Christ has one will/energy (monothelitism/"
     "monoenergism) or two (dyothelitism/dyoenergism). Maximus the Confessor and Sophronius defended two "
     "natural wills against the imperial Ekthesis; the dispute is the principal late-antique site at which "
     "θέλημα/θέλησις and the distinction between natural will (θέλημα φυσικόν) and gnomic will (θέλημα "
     "γνωμικόν / γνώμη) become explicit dogmatic stakes. Resolved at the Third Council of Constantinople "
     "(680–681). This node collects the protagonists, texts, and arguments of the controversy."),
    "Late Antiquity",
    {"century": "7th", "resolution": "Third Council of Constantinople (680-681)", "provenance": PROV}))
# 3b. Honorius I
NEW_NODES.append(mknode(
    "person_honorius_i_pope_d638", "person", "Pope Honorius I (d. 638)",
    ("Bishop of Rome (625–638). His correspondence with Sergius of Constantinople was read as endorsing "
     "a single will in Christ; he was posthumously anathematized at the Third Council of Constantinople "
     "(680–681) — a key figure in the monothelite controversy."),
    "Late Antiquity", {"died": "638", "provenance": PROV}))
# 3c. Carneadean anti-astrology tradition (debate)
NEW_NODES.append(mknode(
    "debate_carneadean_antiastrology_tradition", "debate",
    "The Carneadean Anti-Astrology / Anti-Fatalist Tradition",
    ("The transmission, traced by Amand de Mendieta (1945/1973), of Carneades' anti-astrological and "
     "moral anti-fatalist arguments through Clitomachus, Cicero (De Divinatione II), Philo, and into the "
     "Christian authors (Origen, Eusebius, Basil, Gregory of Nyssa, Diodore of Tarsus, Nemesius, "
     "Chrysostom). Collects the recurring topoi — nomima barbarika, collective deaths, the equal fate of "
     "animals — and the witnesses that redeploy them against εἱμαρμένη."),
    "Cross-period", {"reconstructed_by": "Amand de Mendieta 1945/1973", "provenance": PROV}))
# 3d. NEW: origins-of-the-notion-of-will modern paradigm (per user feedback)
NEW_NODES.append(mknode(
    "debate_origins_notion_of_will_modern_paradigm", "debate",
    "Origins of the Notion of Will (Modern Scholarly Paradigm)",
    ("A historiographical meta-debate among modern scholars over whether, when, and by whom a discrete "
     "notion of 'the will' first emerged in antiquity. Dihle (1982) locates the philosophical concept of "
     "will in Augustine's reception of Paul against Manichaean determinism; Frede (2011) locates the first "
     "genuine notion of a free will in Epictetus and the Stoic tradition; Fürst situates Origen within a "
     "history of freedom. These positions disagree on agent and date while sharing an 'origin-hunting' "
     "frame. The frame is itself contested: critics regard the reification of 'the will' as a single thing "
     "whose invention can be dated as an anachronistic, teleological construction projected onto the "
     "sources. This node collects the attributed scholarly positions; it does NOT assert that 'the will' "
     "was invented at any point."),
    "Contemporary",
    {"kind": "historiographical_meta_debate", "positions_are_attributed_not_endorsed": True,
     "key_scholars": ["Dihle 1982", "Frede 2011", "Fürst"], "provenance": PROV}))

for n in NEW_NODES:
    if n["id"] in nodes:
        note(f"NODE exists, skip create: {n['id']}")
    else:
        nodes[n["id"]] = n; note(f"NODE create: {n['id']}")

# ---- 4. EDGES ----
def add_edge(s, t, rel, weight, meta):
    s, t = resolve(s), resolve(t)
    if rel not in ALLOWED_REL: return ("bad_rel", rel)
    if s not in nodes: return ("miss_src", s)
    if t not in nodes: return ("miss_tgt", t)
    if (s, rel, t) in seen: return ("dup", None)
    seen.add((s, rel, t))
    edges.append({"edge_id": str(uuid.uuid4()), "relation": rel, "source": s, "source_id": s,
                  "target": t, "target_id": t, "weight": weight,
                  "metadata": json.dumps(meta, ensure_ascii=False), "created_at": TS})
    return ("ok", None)

stats = collections.Counter()
# 4a. wave1 + wave2 edges (as proposed)
for f in ("wave1_maximus.jsonl", "wave2_amand.jsonl"):
    for line in open(PROP / f):
        if not line.strip(): continue
        r = json.loads(line)
        if r.get("kind") != "edge": continue
        st, _ = add_edge(r["source_id"], r["target_id"], r["relation"], r.get("weight", 0.7),
                         {"provenance": PROV, "wave": f, "rationale": r.get("rationale", "")[:300]})
        stats[(f, st[0])] += 1
        if st[0] not in ("ok", "dup"): note(f"  {f} edge {st}: {r['source_id']} -{r['relation']}-> {r['target_id']}")
# 4b. wave3 grounded_in -> remap to publication--discusses-->argument
for line in open(PROP / "wave3_wiring.jsonl"):
    if not line.strip(): continue
    r = json.loads(line)
    if r.get("kind") != "edge": continue
    arg, pub = r["source_id"], r["target_id"]   # grounded_in: arg -> pub
    st, _ = add_edge(pub, arg, "discusses", 0.8, {"provenance": PROV, "wave": "wave3_wiring",
                     "note": "remapped from proposed grounded_in to discusses (pub->arg) convention"})
    stats[("wave3", st[0])] += 1
    if st[0] not in ("ok", "dup"): note(f"  wave3 edge {st}: {pub} -discusses-> {arg}")
# 4c. paradigm-node edges (attributed positions contribute_to the meta-debate)
PARA = "debate_origins_notion_of_will_modern_paradigm"
for src in ["argument_dihle_1982_augustine_invents_philosophical_voluntas",
            "argument_frede_2011_epictetus_first_free_will",
            "argument_frede_2011_augustine_no_new_notion_vs_dihle",
            "pub_dihle_1982_theory_of_will", "pub_frede_2011_free_will"]:
    st, info = add_edge(src, PARA, "contributes_to", 0.8, {"provenance": PROV, "wave": "paradigm_node"})
    stats[("paradigm", st[0])] += 1
    if st[0] not in ("ok",): note(f"  paradigm edge {st} {info}: {src} -> {PARA}")

note("EDGE stats: " + ", ".join(f"{k}={v}" for k, v in sorted(stats.items())))

# ---- VALIDATE ----
nid_set = set(nodes)
dangling = sum(1 for e in edges if e["source"] not in nid_set or e["target"] not in nid_set)
note(f"VALIDATE: nodes={len(nodes)} edges={len(edges)} dangling={dangling}")
assert dangling == 0, "dangling edges present"

print("\n".join(log))
print(f"\n{'WROTE' if WRITE else 'DRY-RUN (use --write)'}: nodes {len(norder)}->{len(nodes)}, edges ->{len(edges)}")

if WRITE:
    import shutil
    shutil.copy(KG / "nodes.jsonl", KG / "nodes.jsonl.bak")
    shutil.copy(KG / "edges.jsonl", KG / "edges.jsonl.bak")
    # preserve original order; appended new nodes at end
    final_order = [i for i in norder if i in nodes] + [i for i in nodes if i not in set(norder)]
    with open(KG / "nodes.jsonl", "w") as f:
        for i in final_order: f.write(json.dumps(nodes[i], ensure_ascii=False) + "\n")
    with open(KG / "edges.jsonl", "w") as f:
        for e in edges: f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print("Backups: nodes.jsonl.bak, edges.jsonl.bak")
