"""PART B.2 -- build the candidate list for the school-attribution CHOICE
question: every person and work node, plus argument nodes (cheap, included).

Read-only on data/kg/nodes.jsonl. No Jev call here.
"""

from __future__ import annotations

import json

from lib_common import CAMPAIGN_DIR, load_nonpassage_nodes

MAX_DESC_CHARS = 2200
TYPES = ("person", "work", "argument")

SCHOOL_CRITERIA = {
    "Stoic": "Zeno, Chrysippus, Seneca, Epictetus, Marcus Aurelius; fate, providence, assent, what is up to us",
    "Epicurean": "Epicurus, Lucretius, Philodemus; atoms, the swerve, freedom from fate and from the gods",
    "Peripatetic": "Aristotle and his school (e.g. Alexander of Aphrodisias); the voluntary, deliberation, prohairesis",
    "Academic/Platonist": "Plato and the (Old/Middle/New) Academy broadly; dialogues, forms, tripartite soul, providence and fate",
    "Middle Platonist": "Alcinous, Plutarch, Numenius, Apuleius; 2nd-c. Platonism, three levels of providence/fate",
    "Neoplatonist": "Plotinus, Porphyry, Iamblichus, Proclus, Simplicius; the One, intellect, soul, providence, freedom of the soul",
    "Pyrrhonist/Sceptic": "Pyrrho, Carneades, Sextus Empiricus, Cicero reporting the Academy; suspension of judgment, arguments against fate",
    "Presocratic": "pre-Socratic Greek thinkers (Heraclitus, Parmenides, Democritus, etc.); early cosmology and necessity",
    "Cynic": "Diogenes of Sinope and the Cynic tradition; asceticism, rejection of convention",
    "Christian (patristic)": "Church Fathers, Greek or Latin, 2nd-8th c. CE (apologists, Origen, Augustine, Cappadocians, etc.)",
    "Gnostic": "Gnostic teachers and texts (Valentinus, Basilides, etc.); the demiurge, hidden knowledge, dualism",
    "Jewish": "Jewish authors or traditions (Philo of Alexandria, rabbinic sources) apart from Christian patristic reception",
    "Hermetic": "Hermes Trismegistus / Corpus Hermeticum tradition",
    "Modern scholarship": "a modern (post-1700) scholar, philosopher, or commentator writing ABOUT the ancient debate, not an ancient primary source",
    "No school affiliation / not a school-bound figure": "the description gives no basis for any school or intellectual-tradition affiliation",
    "Cannot be determined from the description": "the description is too thin, generic, or ambiguous to decide among the above",
}


def node_state(n: dict) -> dict:
    return {
        "id": n["id"],
        "name": n.get("label"),
        "type": n.get("type"),
        "period": n.get("period"),
        "description": (n.get("description") or "")[:MAX_DESC_CHARS],
    }


def main() -> None:
    nodes = load_nonpassage_nodes()
    rows = []
    for n in nodes:
        if n.get("type") not in TYPES:
            continue
        desc = (n.get("description") or "").strip()
        if len(desc) < 20:
            continue  # too thin to ask anything of -- would just waste a call
        rows.append({
            "node_id": n["id"],
            "type": n.get("type"),
            "existing_school": n.get("school"),
            "state": node_state(n),
        })

    out_path = CAMPAIGN_DIR / "candidates_school.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    by_type = {}
    for r in rows:
        by_type[r["type"]] = by_type.get(r["type"], 0) + 1
    print(f"candidates_school: {len(rows)} nodes -> {out_path}")
    print(by_type)
    print(f"existing school non-null among these: {sum(1 for r in rows if r['existing_school'])}")


if __name__ == "__main__":
    main()
