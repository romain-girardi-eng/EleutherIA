# kg_work_id collision report

One KG work node claimed by several distinct corpus works (`work_canonical_id` of its `part_of` passages). Each group below needs manual per-work remediation: keep the passages that truly belong to the work node, re-home the rest under their own work node, then remove the group from `data/audit/kg_work_id_known_collisions.json`.

Generated read-only by `scripts/check_kg_work_id_uniqueness.py --report` from `data/kg/nodes.jsonl` + `data/kg/edges.jsonl`.

**Colliding KG work nodes: 0**
