#!/usr/bin/env python3
"""Decisions: engages_with edges whose target is the wrong person.

The 88 engages_with edges of c3_edges_links/queue_A_likely_wrong.csv are
LLM-extracted scholar-to-scholar links (all still carry needs_review). Each
note was read against the identity of the target node. Where the note itself
shows that the person meant is a namesake, the edge is moved to the right
node when it exists, and withdrawn otherwise. One edge outside the queue
(Andresen -> Koch) has the same defect and is included.

Tuples: (edge_id, source, target, verdict, note). Verdicts: "remove",
"retarget:<node_id>", "needs_romain". Queue rows not listed here are
recorded as false_positive (identity consistent with the note).
"""

QUEUE = "c3_edges_links/queue_A_likely_wrong.csv"

DECISIONS = [
    ("b7333cc7-bfeb-49b0-b956-25aacdd39f51", "scholar_jaubert_a", "person_fischer_john_martin_3w4x5y6z", "remove",
     "Note cites 'Die apostolischen Väter (1956)', an edition of the Apostolic Fathers, for 1 Clement; the target is John Martin Fischer (born 1952), a contemporary analytic philosopher. No node for the editor exists."),
    ("c8c86e3e-0d84-4110-9ff6-8b712382863d", "scholar_grant_r", "scholar_koch_i", "remove",
     "Note: 'Cited in Pauly-Wissowa on Origen'. The target is Isabelle Koch (Aix-Marseille, Alexander of Aphrodisias); the Pauly-Wissowa article on Origen is by Hal Koch, who has no node."),
    ("a6ff8959-4656-4ca4-ae30-6c133e73130d", "scholar_crouzel_henri", "scholar_koch_i", "remove",
     "Note: 'Crouzel rejects Koch's representation of Origen as a philosopher'; that is Hal Koch's Origen study (Pronoia und Paideusis, 1932), whereas the target node describes Isabelle Koch's work on Alexander of Aphrodisias. Hal Koch has no node."),
    ("d1e37762-d3f6-4e4f-aa89-5fc1dde0e593", "scholar_andresen_carl", "scholar_koch_i", "remove",
     "Outside the queue. Note names 'Pronoia und Paideusis', Hal Koch's 1932 study of Origen; the target is Isabelle Koch (Aix-Marseille)."),
    ("6f50889d-be94-476d-8db6-0a5c5b3f7a7e", "scholar_ramelli_ilaria", "person_wolf_susan_contemporary", "remove",
     "Note: 'Marx Wolf 2013 positive reaction to Ramelli's Bardaisan reading' - a different scholar (Marx-Wolf) from Susan Wolf, the moral philosopher of the target node. No node for the former."),
    ("e23fc496-2ff0-4473-bf94-83e38986e91d", "scholar_irwin_terence", "person_james_william_4d5e6f7g", "remove",
     "Note: James's criticism of Victorian novels as 'large, loose, baggy monsters' - a novelist's phrase, not William James the philosopher of the target node."),
    ("60a7859e-9150-420d-bab9-1e26d19df631", "scholar_labarri_re_j", "person_taylor_richard_6p7q8r9s", "remove",
     "Note: 'Taylor (1989) on sources of the self' - the 1989 'Sources of the Self' is not by Richard Taylor, the agent-causation libertarian of the target node."),
    ("986e3f57-3804-445f-9c93-c2710edd6869", "scholar_furst_alfons", "person_bobzien_susanne_contemporary", "remove",
     "Note: 'Likely engaged with her work ..., though not explicitly named in provided excerpts' - the extraction itself says the engagement is unattested."),
    ("6a8f0ce2-b31a-48c4-82c9-ddb15912e180", "scholar_list_n", "person_jonathan_edwards_9a3v4w02", "retarget:scholar_edwards_mark",
     "Note: 'On the Platonic School[ing of Justin Martyr]', scope Justin Martyr; the target was the 18th-century Congregationalist theologian. Mark J. Edwards (patristics, Justin, Origen) has a node."),
    ("3115a3d0-cc1f-4eef-9df1-32d63dbcf6aa", "scholar_hall_c", "person_jonathan_edwards_9a3v4w02", "retarget:scholar_edwards_mark",
     "Note: 'doctoral supervisor; work on Origen and Greek philosophy'; an 18th-century theologian cannot be a living scholar's supervisor. Mark J. Edwards has a node."),
    ("a6880eeb-2390-4f0f-a49a-6419a356fcea", "scholar_gibbons_k", "person_jonathan_edwards_9a3v4w02", "retarget:scholar_edwards_mark",
     "Note: 'Edwards called into question the traditional view that Origen had a theory of pre-existent minds' - modern Origen scholarship, not the 18th-century theologian. Mark J. Edwards has a node."),
    ("427dbb28-6404-459f-9acf-12cfd1f5eaf7", "scholar_uster_d", "scholar_frede_michael", "retarget:scholar_frede_dorothea",
     "Note: 'Follows Frede (2003) ...; cites her survey article on Stoic determinism' - the pronoun 'her' and the 2003 survey point to Dorothea Frede, who has a node, not Michael Frede."),
    ("673c1a59-a850-4ad0-90db-dc53605e4068", "scholar_gaventa_b", "scholar_king_p", "needs_romain",
     "Note: '2017 on flesh and spirit terminology' (Pauline scope); whether this King is the node's Peter King needs the bibliography."),
    ("62ccd8c5-f820-499a-a02e-0af79a36b2e1", "scholar_gaventa_b", "scholar_meyer_s", "needs_romain",
     "Note: '2004d, 67-68 on continuity between chapters 6 and 7' in a study of Paul's view of the law; Susan Sauvé Meyer works on Aristotle - probably a Pauline scholar named Meyer. Needs the bibliography."),
    ("eb439c7a-4643-4580-b702-d01fe34e41d6", "scholar_ramelli_ilaria", "scholar_frede_michael", "needs_romain",
     "Note: 'Frede 2009' on Alexander of Aphrodisias; Michael Frede died in 2007 - Michael (posthumous) or Dorothea Frede?"),
    ("c5541f73-5f99-40d9-8898-22028a463a09", "scholar_gourinat_jean_baptiste", "scholar_frede_michael", "needs_romain",
     "Outside the queue. Note: '2003' only; Dorothea Frede's 2003 survey on Stoic determinism is the likely reference (cf. the Šuster edge)."),
    ("eeee3e96-a1c5-481a-a638-533e88346d25", "scholar_gibbons_k", "scholar_koch_i", "needs_romain",
     "Outside the queue. Note: 'Koch suggested Origen's human autonomy requires freedom to do otherwise' - Hal Koch (Origen) or Isabelle Koch?"),
    ("2291f172-13d6-4970-a0fb-e4332c70a959", "scholar_grgi_f", "person_ginet_carl_0t1u2v3w", "needs_romain",
     "Note: 'Pećnjak uses Ginet's concept' - the citing author named is Pećnjak, not the source node."),
    ("1b7c3b88-3f95-42db-8362-09e2b39e6597", "scholar_kowalski_m", "person_kane_robert_1938_2022", "needs_romain",
     "Note: 'cited on Islamic scholars studying Greek philosophers on free will' in a study of Paul; unlikely for Robert Kane, needs the bibliography."),
]
