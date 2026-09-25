"""Withdraw three `evidenced_by` edges left with a work target by the C3 review.

The C3 citation review (2026-09-24) moved these edges off SC 79, ch. 5 (John
Chrysostom, "Sur la providence de Dieu", a different treatise) onto
`work_pseudo_chrysostom_de_fato_providentia` (PG 50, 765-768, Discourse V),
which is where each argument's own description locates it. `evidenced_by`
only admits a passage target (knowledge graph/ontology/edge_types.json), and
every one of these arguments already carries
`cites_primary_source -> work_pseudo_chrysostom_de_fato_providentia`, which
states the same citation with an admitted type. The retargeted edges are
therefore redundant and ill-typed (KG RDF/SHACL gate, ClassConstraintComponent).
"""

TARGET = "work_pseudo_chrysostom_de_fato_providentia"

DECISIONS = [
    # Amand 1945: "Climax récapitulatif au sein du Discours V"; kept citation:
    # cites_primary_source -> work_pseudo_chrysostom_de_fato_providentia.
    "argument_pseudo_chrysostom_de_fato_recapitulation_amand1945",
    # Amand 1945: "Argument 8 (heimarmene injuste) au sein du Discours V".
    "argument_pseudo_chrysostom_de_fato_v_apologetic_amand1945",
    # Amand 1945: Discourse V witness text (PG 50, 765-768).
    "argument_pseudo_chrysostom_de_fato_v_witness6_amand1945",
]
