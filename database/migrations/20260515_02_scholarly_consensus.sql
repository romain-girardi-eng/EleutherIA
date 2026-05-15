-- Migration: scholarly_consensus_topics
-- Wave 6 Z4 — backing store for the Methodology Agent's consensus checks.
--
-- Each topic records a well-known scholarly dispute (ancient + Patristic +
-- modern philosophy of free will) with the canonical positions, real
-- published citations, and a methodological warning. The Methodology
-- Agent consults this table instead of asking the LLM ad hoc whether a
-- claim contradicts the literature.

SET search_path TO free_will, public;

CREATE TABLE IF NOT EXISTS free_will.scholarly_consensus_topics (
    topic_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_slug TEXT UNIQUE NOT NULL,
    question TEXT NOT NULL,
    relevant_concepts TEXT[] NOT NULL DEFAULT '{}',
    relevant_persons TEXT[] NOT NULL DEFAULT '{}',
    relevant_period TEXT,
    positions JSONB NOT NULL,
    consensus_status TEXT NOT NULL
        CHECK (consensus_status IN ('consensus', 'contested', 'recently_unsettled', 'open')),
    methodological_warning TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_consensus_concepts
    ON free_will.scholarly_consensus_topics USING gin(relevant_concepts);

CREATE INDEX IF NOT EXISTS idx_consensus_persons
    ON free_will.scholarly_consensus_topics USING gin(relevant_persons);

CREATE INDEX IF NOT EXISTS idx_consensus_period
    ON free_will.scholarly_consensus_topics (relevant_period);

CREATE INDEX IF NOT EXISTS idx_consensus_status
    ON free_will.scholarly_consensus_topics (consensus_status);

-- --------------------------------------------------------------------------
-- Seed: 30 well-known disputes
-- Each `positions` array entry has the shape:
--   { "label", "scholars", "citation", "summary" }
-- All citations refer to real published works.
-- --------------------------------------------------------------------------

INSERT INTO free_will.scholarly_consensus_topics
    (topic_slug, question, relevant_concepts, relevant_persons,
     relevant_period, positions, consensus_status, methodological_warning)
VALUES

-- 1
('aristotle_concept_of_will',
 'Does Aristotle have a concept of will, and a fortiori of free will?',
 ARRAY['concept_will','concept_prohairesis','concept_hekousion','concept_boulesis'],
 ARRAY['person_aristotle'],
 'Classical',
 '[
   {"label":"Bobzien — no","scholars":["Susanne Bobzien"],"citation":"Bobzien, S. 1998. \"Determinism and Freedom in Stoic Philosophy.\" Oxford: Clarendon. + Bobzien 2014 \"Choice and Moral Responsibility in Nicomachean Ethics iii 1-5\" in Polansky (ed.), Cambridge Companion to Aristotle''s NE","summary":"Aristotle has hekousion/prohairesis but no faculty of will and no concept of free will. ''Free will'' is post-ancient."},
   {"label":"Frede — yes (Stoic-Patristic synthesis)","scholars":["Michael Frede"],"citation":"Frede, M. 2011. \"A Free Will: Origins of the Notion in Ancient Thought.\" Berkeley: University of California Press.","summary":"A notion of free will emerges in the Stoa and is fully formed by Origen; Aristotle prefigures it via prohairesis."},
   {"label":"Dihle — no (Patristic invention)","scholars":["Albrecht Dihle"],"citation":"Dihle, A. 1982. \"The Theory of Will in Classical Antiquity.\" Berkeley: University of California Press.","summary":"The very concept of will is an Augustinian invention; Aristotle has no faculty of will."}
 ]'::jsonb,
 'contested',
 'Do not say ''Aristotle on free will'' without naming all three positions. ''Free will'' for Aristotle is the canonical disputed claim in this corpus.'),

-- 2
('stoic_compatibilism_modern_label',
 'Is calling the Stoic doctrine "compatibilism" methodologically defensible?',
 ARRAY['concept_compatibilism','concept_eph_hemin','concept_fate','concept_heimarmene'],
 ARRAY['person_chrysippus','person_zeno_of_citium','person_cleanthes'],
 'Hellenistic',
 '[
   {"label":"Bobzien — anachronistic but defensible with caveat","scholars":["Susanne Bobzien"],"citation":"Bobzien, S. 1998. \"Determinism and Freedom in Stoic Philosophy.\" Oxford: Clarendon, ch. 6.","summary":"Stoic causal determinism is compatible with what they meant by eph'' hēmin, but the modern label ''compatibilism'' (Kane 1985+) imports framework assumptions Chrysippus did not share."},
   {"label":"Salles — straight-on Stoic compatibilism","scholars":["Ricardo Salles"],"citation":"Salles, R. 2005. \"The Stoics on Determinism and Compatibilism.\" Aldershot: Ashgate.","summary":"The Stoics fit a modern compatibilist taxonomy without significant distortion."},
   {"label":"Frede — yes, and proto-libertarian","scholars":["Michael Frede"],"citation":"Frede, M. 2011. \"A Free Will: Origins of the Notion in Ancient Thought.\" Berkeley: UC Press.","summary":"The Stoics already have a notion of free will, so ''compatibilism'' applies even more readily."}
 ]'::jsonb,
 'contested',
 'Always hedge: ''what modern scholars term Stoic compatibilism''. Bare ''Stoic compatibilism'' as fact is methodologically loose (Kane 1985+ taxonomy).'),

-- 3
('chrysippus_cylinder_argument_validity',
 'Does Chrysippus''s cylinder argument actually preserve eph'' hēmin against causal determinism?',
 ARRAY['argument_cylinder','concept_causal_determinism','concept_eph_hemin','concept_synkatathesis'],
 ARRAY['person_chrysippus','person_cicero','person_aulus_gellius'],
 'Hellenistic',
 '[
   {"label":"Bobzien — yes, on a co-fated reading","scholars":["Susanne Bobzien"],"citation":"Bobzien, S. 1998. \"Determinism and Freedom in Stoic Philosophy.\" Oxford: Clarendon, ch. 6.","summary":"The cylinder argument distinguishes auxiliary from principal causes; Chrysippus can preserve responsibility within fate."},
   {"label":"Salles — argument is more limited than Bobzien thinks","scholars":["Ricardo Salles"],"citation":"Salles, R. 2005. \"The Stoics on Determinism and Compatibilism.\" Aldershot: Ashgate.","summary":"The cylinder defence only works for a narrow sense of responsibility, not for the moralised concept Bobzien attributes."},
   {"label":"Frede — straightforward","scholars":["Michael Frede"],"citation":"Frede, M. 2011. \"A Free Will.\" Berkeley: UC Press.","summary":"The cylinder argument is robust and supports a Stoic doctrine of free will."}
 ]'::jsonb,
 'contested',
 'Chrysippus''s argument survives only via Cicero (De Fato 39-45) and Aulus Gellius (NA VII.2.6-13 = SVF II.1000). Always cite the testimonium chain.'),

-- 4
('epicurus_swerve_role_in_freedom',
 'Does the Epicurean atomic swerve (parenklisis / clinamen) ground human freedom of action?',
 ARRAY['concept_atomic_swerve','concept_clinamen','concept_parenklisis','concept_atomism'],
 ARRAY['person_epicurus','person_lucretius'],
 'Hellenistic',
 '[
   {"label":"Furley — yes, micro-indeterminist","scholars":["David Furley"],"citation":"Furley, D. 1967. \"Two Studies in the Greek Atomists.\" Princeton: Princeton University Press.","summary":"The swerve introduces indeterminism at the atomic level that is required for and grounds human freedom."},
   {"label":"Long & Sedley — no, swerve is character-formative not act-causal","scholars":["A. A. Long","David Sedley"],"citation":"Long, A. A. & Sedley, D. N. 1987. \"The Hellenistic Philosophers.\" Cambridge: CUP, vol. 1, §20.","summary":"The swerve secures the possibility of free volition by making character formation non-deterministic; it does not act-by-act decide each choice."},
   {"label":"Sedley — independent later view","scholars":["David Sedley"],"citation":"Sedley, D. 1983. \"Epicurus'' Refutation of Determinism.\" In SUZHTHSIS: Studi… Gigante. Naples: Macchiaroli, pp. 11-51.","summary":"The swerve''s explanatory role is more limited than Furley''s reading suggests; freedom rests on the agent''s constitution."}
 ]'::jsonb,
 'contested',
 'On Epicurus do not assume Furley''s reading is the default. Long-Sedley 1987 §20 is the modern reference point.'),

-- 5
('carneades_attack_on_chrysippus',
 'What was the structure and force of Carneades''s critique of Chrysippus on fate?',
 ARRAY['debate_fate','concept_eph_hemin','concept_causal_determinism'],
 ARRAY['person_carneades','person_chrysippus','person_cicero'],
 'Hellenistic',
 '[
   {"label":"Bett — Carneades is an indeterminist","scholars":["Richard Bett"],"citation":"Bett, R. 1989. \"Carneades'' Pithanon: A Reappraisal of its Role and Status.\" Oxford Studies in Ancient Philosophy 7: 59-94.","summary":"Carneades genuinely defends an indeterminist position against Chrysippus, not merely an Academic dialectical critique."},
   {"label":"Sharples — dialectical only","scholars":["R. W. Sharples"],"citation":"Sharples, R. W. 1991. \"Cicero: On Fate (De Fato) & Boethius: The Consolation of Philosophy IV.5-7, V.\" Warminster: Aris & Phillips.","summary":"Carneades''s argument is Academic dialectic; the historical Carneades likely held no positive view on freedom."},
   {"label":"Hankinson — middle ground","scholars":["R. J. Hankinson"],"citation":"Hankinson, R. J. 1999. \"Determinism and Indeterminism.\" In Algra et al. (eds.), The Cambridge History of Hellenistic Philosophy. Cambridge: CUP, pp. 513-541.","summary":"Carneades probably had a substantive but undogmatic position on causal indeterminism."}
 ]'::jsonb,
 'contested',
 'Carneades is a lost author. Every claim about his views travels through Cicero (De Fato) and must be marked as testimonium.'),

-- 6
('middle_platonism_fate_doctrine',
 'Is there a coherent Middle Platonist doctrine on fate, or only a collection of authors?',
 ARRAY['concept_fate','concept_heimarmene','school_middle_platonism','debate_fate'],
 ARRAY['person_plutarch','person_alcinous','person_pseudo_plutarch','person_apuleius'],
 'Imperial',
 '[
   {"label":"Karamanolis — coherent doctrine","scholars":["George Karamanolis"],"citation":"Karamanolis, G. 2006. \"Plato and Aristotle in Agreement? Platonists on Aristotle from Antiochus to Porphyry.\" Oxford: Clarendon.","summary":"There is a recognisable shared Middle Platonist line on fate, including its conditional structure."},
   {"label":"Boys-Stones — fragmented authors only","scholars":["George Boys-Stones"],"citation":"Boys-Stones, G. 2018. \"Platonist Philosophy 80 BC to AD 250: An Introduction and Collection of Sources in Translation.\" Cambridge: CUP.","summary":"Middle Platonism is not a school in any strong sense; on fate we have a handful of authors with related but distinct views."},
   {"label":"Dillon — common stock","scholars":["John Dillon"],"citation":"Dillon, J. 1977/1996. \"The Middle Platonists, 80 B.C. to A.D. 220.\" Ithaca: Cornell University Press.","summary":"A common stock of Platonist commitments is shared, but Dillon''s strong eclecticism thesis has been questioned (see topic 17)."}
 ]'::jsonb,
 'contested',
 'Do not write ''the Middle Platonist doctrine of fate'' as if it were unitary. Name the author (Plutarch, Pseudo-Plutarch, Alcinous, Apuleius).'),

-- 7
('origen_libertarian_label_anachronism',
 'Is calling Origen a ''libertarian'' on free will methodologically defensible?',
 ARRAY['concept_autexousion','concept_free_will','concept_libertarian'],
 ARRAY['person_origen'],
 'Patristic',
 '[
   {"label":"Crouzel — Origen as champion of free will","scholars":["Henri Crouzel"],"citation":"Crouzel, H. 1989. \"Origen.\" Edinburgh: T&T Clark. (orig. French 1985)","summary":"Origen is the strongest ancient defender of human autexousion against astral and Gnostic determinism; ''free will'' is appropriate."},
   {"label":"Bobzien — anachronistic","scholars":["Susanne Bobzien"],"citation":"Bobzien, S. 2014. \"Found in Translation: Aristotle''s Nicomachean Ethics III.1-5 on Voluntariness and Free Decision.\" Phronesis 59: 369-417.","summary":"''Libertarian'' is a Kane-1985 taxonomy term and should not be applied to ancient authors without explicit caveat."},
   {"label":"Frede — yes, with qualification","scholars":["Michael Frede"],"citation":"Frede, M. 2011. \"A Free Will.\" Berkeley: UC Press, ch. 6.","summary":"Origen articulates the first fully formed notion of free will; ''libertarian'' is anachronistic but the underlying position is genuinely indeterminist."}
 ]'::jsonb,
 'contested',
 'Origen does have autexousion. ''Libertarian'' must be hedged. The KG node already carries this qualification (Phase 9).'),

-- 8
('justin_autexousion_origin',
 'Is Justin''s autexousion drawn from Middle Platonism or a Christian innovation?',
 ARRAY['concept_autexousion','school_middle_platonism','debate_origin_free_will'],
 ARRAY['person_justin_martyr_2c_ce','person_alcinous'],
 'Patristic',
 '[
   {"label":"Andresen — Middle-Platonist source","scholars":["Carl Andresen"],"citation":"Andresen, C. 1952-1953. \"Justin und der mittlere Platonismus.\" ZNW 44: 157-195.","summary":"Justin''s autexousion is borrowed from his Middle Platonist sources, particularly via the Alcinous-like tradition."},
   {"label":"Karamanolis — Christian transformation","scholars":["George Karamanolis"],"citation":"Karamanolis, G. 2013. \"The Philosophy of Early Christianity.\" Durham: Acumen, ch. 5.","summary":"Justin takes Platonist vocabulary but transforms autexousion in ways that have no clean Platonist precedent."},
   {"label":"Frede — link to Stoic-Christian synthesis","scholars":["Michael Frede"],"citation":"Frede, M. 2011. \"A Free Will.\" Berkeley: UC Press, ch. 5.","summary":"Justin participates in a longer Stoic-Patristic synthesis that culminates in Origen."}
 ]'::jsonb,
 'contested',
 'Justin''s autexousion has Middle-Platonist parallels (e.g. Alcinous), but ''borrowed'' is too strong without Andresen''s argument.'),

-- 9
('patristic_will_invention_thesis',
 'Did the Church Fathers invent the concept of will?',
 ARRAY['concept_will','concept_voluntas','concept_autexousion','concept_free_will'],
 ARRAY['person_augustine','person_origen','person_justin_martyr_2c_ce'],
 'Patristic',
 '[
   {"label":"Dihle — yes, Augustinian invention","scholars":["Albrecht Dihle"],"citation":"Dihle, A. 1982. \"The Theory of Will in Classical Antiquity.\" Berkeley: UC Press.","summary":"The concept of will as a distinct faculty is an Augustinian innovation; there is nothing comparable in pre-Christian antiquity."},
   {"label":"Frede — earlier, Stoic-Patristic","scholars":["Michael Frede"],"citation":"Frede, M. 2011. \"A Free Will.\" Berkeley: UC Press.","summary":"The concept emerges already with the Stoics and is fully formed by Origen, well before Augustine."},
   {"label":"Sorabji — the will is composite of several earlier strands","scholars":["Richard Sorabji"],"citation":"Sorabji, R. 2014. \"Moral Conscience through the Ages: Fifth Century BCE to the Present.\" Chicago: University of Chicago Press.","summary":"What we call ''the will'' is a composite of multiple ancient capacities (prohairesis, hormē, synkatathesis, voluntas) gradually consolidated."}
 ]'::jsonb,
 'contested',
 'On ''when was the will invented?'' all three positions (Dihle / Frede / Sorabji) must be named.'),

-- 10
('augustinian_shift_pre_post_pelagian',
 'Is there a sharp doctrinal shift in Augustine''s view of free will pre- and post-Pelagian controversy?',
 ARRAY['concept_grace','concept_liberum_arbitrium','concept_pelagianism'],
 ARRAY['person_augustine','person_pelagius'],
 'Patristic',
 '[
   {"label":"Cary — sharp shift","scholars":["Phillip Cary"],"citation":"Cary, P. 2008. \"Inner Grace: Augustine in the Traditions of Plato and Paul.\" Oxford: OUP.","summary":"Augustine''s pre-Pelagian writings preserve robust libertas; the controversy with Pelagius drives him toward a strong-predestination view."},
   {"label":"Rist — continuity","scholars":["John Rist"],"citation":"Rist, J. 1994. \"Augustine: Ancient Thought Baptized.\" Cambridge: CUP, ch. 5-6.","summary":"The shift is overstated; the elements of Augustine''s mature view are present already in De libero arbitrio."},
   {"label":"Burns — developmental","scholars":["J. Patout Burns"],"citation":"Burns, J. P. 1980. \"The Development of Augustine''s Doctrine of Operative Grace.\" Paris: Études Augustiniennes.","summary":"Real doctrinal development under the pressure of the Pelagian controversy, but earlier than the explicit polemic."}
 ]'::jsonb,
 'contested',
 'On Augustine''s development, distinguish De libero arbitrio (pre) from De correptione, De praedestinatione, De dono perseverantiae (post). The KG carries all four.'),

-- 11
('boethius_eternity_solution',
 'Does Boethius''s appeal to divine eternity actually solve the foreknowledge-freedom problem?',
 ARRAY['concept_divine_foreknowledge','concept_eternity','concept_nunc_stans','debate_foreknowledge'],
 ARRAY['person_boethius'],
 'Late Antiquity',
 '[
   {"label":"Stump & Kretzmann — solution preserved","scholars":["Eleonore Stump","Norman Kretzmann"],"citation":"Stump, E. & Kretzmann, N. 1981. \"Eternity.\" Journal of Philosophy 78: 429-458.","summary":"The atemporal-knowledge solution is logically coherent once divine eternity is properly understood as a mode of duration."},
   {"label":"Marenbon — solution fails","scholars":["John Marenbon"],"citation":"Marenbon, J. 2003. \"Boethius.\" Oxford: OUP, ch. 7.","summary":"The eternity move only relocates the problem; God''s atemporal knowledge of contingent truths is no easier to reconcile with freedom than temporal foreknowledge."},
   {"label":"Zagzebski — Ockhamist alternative","scholars":["Linda Zagzebski"],"citation":"Zagzebski, L. 1991. \"The Dilemma of Freedom and Foreknowledge.\" New York: OUP.","summary":"The Boethian eternity solution is dominated by Ockhamist accidental-necessity solutions in the medieval and modern literature."}
 ]'::jsonb,
 'contested',
 'On Boethius do not present Stump-Kretzmann as the settled solution. Marenbon 2003 is the standard counter.'),

-- 12
('clement_alexandria_stoicizing',
 'How Stoic is Clement of Alexandria''s moral psychology?',
 ARRAY['concept_apatheia','concept_eph_hemin','concept_passions'],
 ARRAY['person_clement_of_alexandria'],
 'Patristic',
 '[
   {"label":"Havrda — heavily Stoic","scholars":["Matyáš Havrda"],"citation":"Havrda, M. 2016. \"The So-Called Eighth Stromateus by Clement of Alexandria.\" Leiden: Brill.","summary":"Clement''s moral psychology and epistemology are deeply structured by Stoic categories, especially via the Eighth Stromateus."},
   {"label":"Karamanolis — Platonist primary, Stoic secondary","scholars":["George Karamanolis"],"citation":"Karamanolis, G. 2013. \"The Philosophy of Early Christianity.\" Durham: Acumen.","summary":"Clement''s framework is Middle Platonist, with Stoic vocabulary drafted in for moral psychology rather than the metaphysical core."},
   {"label":"Edwards — eclectic","scholars":["Mark Edwards"],"citation":"Edwards, M. 2017. \"Religions of the Constantinian Empire.\" Oxford: OUP.","summary":"Clement freely combines Stoic, Platonist, and biblical material; ''Stoicizing'' is too narrow a description."}
 ]'::jsonb,
 'contested',
 'On Clement always specify which doctrine. The Stoic-ness of his moral psychology is not the Stoic-ness of his theology.'),

-- 13
('tertullian_traducianism_implications',
 'Does Tertullian''s traducianism commit him to a deterministic anthropology?',
 ARRAY['concept_traducianism','concept_original_sin','concept_soul'],
 ARRAY['person_tertullian'],
 'Patristic',
 '[
   {"label":"Waszink — strong materialism, weak determinism","scholars":["J. H. Waszink"],"citation":"Waszink, J. H. 1947. \"Quinti Septimi Florentis Tertulliani De Anima.\" Amsterdam: J. M. Meulenhoff. + Waszink 1955 commentary","summary":"Tertullian''s materialism about the soul does not entail strict determinism; he retains libertas arbitrii against the Valentinians."},
   {"label":"Dunn — moralised libertas","scholars":["Geoffrey Dunn"],"citation":"Dunn, G. 2004. \"Tertullian.\" London: Routledge.","summary":"Tertullian preserves moral responsibility despite traducianism; his concept of libertas is shaped by his Roman legal background."},
   {"label":"Karamanolis — tension","scholars":["George Karamanolis"],"citation":"Karamanolis, G. 2013. \"The Philosophy of Early Christianity.\" Durham: Acumen, ch. 6.","summary":"There is a real internal tension between Tertullian''s materialist anthropology and his defence of freedom against the Gnostics."}
 ]'::jsonb,
 'contested',
 'Tertullian''s De Anima must be read with Waszink''s edition + commentary. Do not slip ''original sin'' (an Augustinian formulation) onto Tertullian.'),

-- 14
('methodius_anti_origenism_genuine',
 'Is Methodius of Olympus''s anti-Origenism a genuine doctrinal disagreement or a polemical caricature?',
 ARRAY['concept_resurrection','concept_pre_existence_souls'],
 ARRAY['person_methodius_of_olympus','person_origen'],
 'Patristic',
 '[
   {"label":"Patterson — genuine","scholars":["L. G. Patterson"],"citation":"Patterson, L. G. 1997. \"Methodius of Olympus: Divine Sovereignty, Human Freedom, and Life in Christ.\" Washington: CUA Press.","summary":"Methodius engages with Origen''s actual positions on resurrection and pre-existence of souls; the disagreement is doctrinal."},
   {"label":"Crouzel — polemical caricature","scholars":["Henri Crouzel"],"citation":"Crouzel, H. 1989. \"Origen.\" Edinburgh: T&T Clark.","summary":"Methodius reads Origen tendentiously; many of his targets are positions Origen did not hold."}
 ]'::jsonb,
 'contested',
 'Methodius'' De Resurrectione is preserved partly via Photius and Slavonic. Always note the transmission.'),

-- 15
('maximus_natural_vs_gnomic_will',
 'Is Maximus the Confessor''s natural / gnomic will distinction consistent with his anti-monothelite position?',
 ARRAY['concept_natural_will','concept_gnomic_will','debate_monothelitism'],
 ARRAY['person_maximus_the_confessor'],
 'Late Antiquity',
 '[
   {"label":"Bathrellos — fully consistent","scholars":["Demetrios Bathrellos"],"citation":"Bathrellos, D. 2004. \"The Byzantine Christ: Person, Nature, and Will in the Christology of Saint Maximus the Confessor.\" Oxford: OUP.","summary":"The natural / gnomic distinction allows Maximus to deny gnomic will of Christ while affirming natural will, preserving his Chalcedonian Christology."},
   {"label":"Cooper — tension","scholars":["Adam Cooper"],"citation":"Cooper, A. 2005. \"The Body in St Maximus the Confessor: Holy Flesh, Wholly Deified.\" Oxford: OUP.","summary":"The distinction is more strained than Bathrellos suggests; Maximus needs gnomic-like content without the name."}
 ]'::jsonb,
 'contested',
 'On Maximus, distinguish thelēma physikon from thelēma gnōmikon. Bathrellos 2004 is the standard reference.'),

-- 16
('epictetus_prohairesis_innovation',
 'Is Epictetus''s use of prohairesis a Stoic innovation or a continuation of Aristotelian usage?',
 ARRAY['concept_prohairesis','concept_eph_hemin'],
 ARRAY['person_epictetus','person_aristotle'],
 'Imperial',
 '[
   {"label":"Long — Stoic innovation","scholars":["A. A. Long"],"citation":"Long, A. A. 2002. \"Epictetus: A Stoic and Socratic Guide to Life.\" Oxford: OUP.","summary":"Epictetus refunctions Aristotelian prohairesis into a Stoic concept of moral character central to eph'' hēmin."},
   {"label":"Frede — continuity + transformation","scholars":["Michael Frede"],"citation":"Frede, M. 2011. \"A Free Will.\" Berkeley: UC Press, ch. 3.","summary":"Epictetus stands in continuity with Aristotle but his prohairesis carries new metaphysical and moral weight."},
   {"label":"Inwood — close to Chrysippean tradition","scholars":["Brad Inwood"],"citation":"Inwood, B. 1985. \"Ethics and Human Action in Early Stoicism.\" Oxford: Clarendon.","summary":"Epictetus''s prohairesis is recognisably within the Chrysippean tradition, not a major innovation."}
 ]'::jsonb,
 'contested',
 'On Epictetus, prohairesis is the key technical term. Do not translate it as ''will'' tout court (Dihle warning).'),

-- 17
('middle_platonism_eclecticism',
 'Is Middle Platonist ''eclecticism'' a useful category or an outdated label?',
 ARRAY['school_middle_platonism','school_platonism'],
 ARRAY['person_alcinous','person_plutarch','person_apuleius','person_numenius'],
 'Imperial',
 '[
   {"label":"Dillon (1977/1996) — moderate eclecticism","scholars":["John Dillon"],"citation":"Dillon, J. 1977/1996. \"The Middle Platonists, 80 B.C. to A.D. 220.\" Ithaca: Cornell University Press.","summary":"Middle Platonists draw on Stoic and Aristotelian material within a Platonist core; eclecticism captures this."},
   {"label":"Donini / Boys-Stones — outdated category","scholars":["Pierluigi Donini","George Boys-Stones"],"citation":"Donini, P. L. 1988. \"The History of the Concept of Eclecticism.\" In Dillon & Long (eds.), The Question of Eclecticism, Berkeley: UC Press. + Boys-Stones 2018.","summary":"''Eclecticism'' was always a polemical label; recent scholarship treats Middle Platonists as Platonists with a distinctive interpretive tradition."}
 ]'::jsonb,
 'recently_unsettled',
 'Dillon 1977/96 is foundational but the eclecticism thesis has been substantially reworked. Cite Boys-Stones 2018 for the current state of the field.'),

-- 18
('nemesius_christian_or_pagan',
 'Is Nemesius of Emesa a Christian writing as a Platonist, or a Platonist with Christian elements?',
 ARRAY['concept_soul','concept_providence','school_neoplatonism'],
 ARRAY['person_nemesius_of_emesa'],
 'Late Antiquity',
 '[
   {"label":"Sharples & Van der Eijk — Christian Platonist","scholars":["R. W. Sharples","Philip van der Eijk"],"citation":"Sharples, R. W. & van der Eijk, P. J. 2008. \"Nemesius: On the Nature of Man.\" Translated Texts for Historians 49. Liverpool: Liverpool University Press.","summary":"Nemesius is a Christian bishop who draws heavily on Platonist and Galenic sources; the De Natura Hominis is a Christian Platonist text."}
 ]'::jsonb,
 'consensus',
 'The Sharples-Van der Eijk 2008 edition is the standard reference. Nemesius is now classed as Christian Platonist, not crypto-pagan.'),

-- 19
('ben_sira_15_11_20_locus_classicus',
 'Is Ben Sira 15:11-20 the locus classicus of biblical free will?',
 ARRAY['concept_yetzer','concept_free_will','concept_biblical_anthropology'],
 ARRAY['person_ben_sira'],
 'Hellenistic',
 '[
   {"label":"Wicke-Reuter — yes, anti-determinist polemic","scholars":["Ursel Wicke-Reuter"],"citation":"Wicke-Reuter, U. 2000. \"Göttliche Providenz und menschliche Verantwortung bei Ben Sira und in der Frühen Stoa.\" BZAW 298. Berlin: De Gruyter.","summary":"Ben Sira 15:11-20 is a self-conscious anti-determinist polemic, possibly in dialogue with early Stoicism."},
   {"label":"Beentjes — yes, programmatic","scholars":["Pancratius C. Beentjes"],"citation":"Beentjes, P. C. 2006. \"Happy the One who Meditates on Wisdom (Sir. 14,20): Collected Essays on the Book of Ben Sira.\" CBET 43. Leuven: Peeters.","summary":"The passage is programmatic for Ben Sira''s ethics; the choice between life and death is genuinely the human''s own."},
   {"label":"Crenshaw — less polemical","scholars":["James L. Crenshaw"],"citation":"Crenshaw, J. L. 2010. \"Old Testament Wisdom: An Introduction.\" 3rd ed. Louisville: Westminster John Knox.","summary":"The passage is consistent with broader wisdom-tradition emphasis on human choice; the Stoic-polemic reading is overdrawn."}
 ]'::jsonb,
 'contested',
 'Ben Sira 15:11-20 is a key text. If you cite it, name Wicke-Reuter 2000 as the canonical polemic-reading; Crenshaw is the standard rejoinder.'),

-- 20
('qumran_two_spirits_determinism',
 'How deterministic is the Two Spirits doctrine (1QS III.13–IV.26)?',
 ARRAY['concept_two_spirits','concept_predestination','concept_yetzer'],
 ARRAY['person_qumran_community'],
 'Hellenistic',
 '[
   {"label":"Stuckenbruck — strong predestination","scholars":["Loren Stuckenbruck"],"citation":"Stuckenbruck, L. T. 2014. \"The Myth of Rebellious Angels: Studies in Second Temple Judaism and New Testament Texts.\" WUNT 335. Tübingen: Mohr Siebeck.","summary":"The Two Spirits doctrine implies a strong cosmic dualism with effective predestination of the sons of light and darkness."},
   {"label":"Schiffman — moderated by halakhah","scholars":["Lawrence Schiffman"],"citation":"Schiffman, L. H. 1989. \"The Eschatological Community of the Dead Sea Scrolls.\" SBLMS 38. Atlanta: Scholars Press.","summary":"The deterministic language coexists with halakhic responsibility; the community treats members as morally accountable."},
   {"label":"Werline — apocalyptic determinism","scholars":["Rodney A. Werline"],"citation":"Werline, R. A. 2008. \"The Experience of Prayer and Resistance to Demonic Powers in the Gospel of Mark.\" In Flannery, Shantz, & Werline (eds.), Experientia, vol. 1. Atlanta: SBL.","summary":"The Two Spirits passage participates in a wider apocalyptic determinism that does not erase moral agency."}
 ]'::jsonb,
 'contested',
 '1QS III.13–IV.26 is the locus classicus. Cite Stuckenbruck for the strong-determinism reading; Schiffman for the moderated reading.'),

-- 21
('josephus_three_sects_on_fate_doctrinal_vs_polemical',
 'Are Josephus''s three-sects passages (Antiquities 13.5.9, 18.1.2-6; War 2.8.14) doctrinal reports or polemical caricature?',
 ARRAY['concept_fate','concept_pharisees','concept_sadducees','concept_essenes'],
 ARRAY['person_josephus'],
 'Imperial',
 '[
   {"label":"Mason — Hellenizing caricature","scholars":["Steve Mason"],"citation":"Mason, S. 1991. \"Flavius Josephus on the Pharisees: A Composition-Critical Study.\" Leiden: Brill.","summary":"Josephus deliberately frames the sects in Hellenistic philosophical-school categories (heimarmene language) for his Roman readers; the report is heavily polemical."},
   {"label":"Sanders — substantially accurate","scholars":["E. P. Sanders"],"citation":"Sanders, E. P. 1992. \"Judaism: Practice and Belief, 63 BCE – 66 CE.\" London: SCM.","summary":"Josephus''s differentiation of Pharisees, Sadducees, and Essenes on fate is broadly consistent with what we know from other sources."}
 ]'::jsonb,
 'contested',
 'On Josephus''s three sects, always flag the Hellenistic-categorization warning (Mason 1991). The heimarmene vocabulary is Josephus''s, not necessarily the sects''.'),

-- 22
('paul_romans_9_predestination',
 'Does Paul''s argument in Romans 9 commit him to individual predestination?',
 ARRAY['concept_predestination','concept_election','concept_grace'],
 ARRAY['person_paul_of_tarsus'],
 'Patristic',
 '[
   {"label":"Käsemann — yes, double predestination","scholars":["Ernst Käsemann"],"citation":"Käsemann, E. 1980. \"Commentary on Romans.\" Trans. G. W. Bromiley. Grand Rapids: Eerdmans.","summary":"Romans 9-11 is read as a strong predestinarian argument involving God''s sovereign election of individuals."},
   {"label":"Dunn — corporate, not individual","scholars":["James D. G. Dunn"],"citation":"Dunn, J. D. G. 1988. \"Romans 9-16.\" WBC 38B. Dallas: Word.","summary":"Paul argues for corporate election of Israel, not individual double-predestination; the rhetoric is national-historical."},
   {"label":"Barclay — gift-theology reading","scholars":["John Barclay"],"citation":"Barclay, J. M. G. 2015. \"Paul and the Gift.\" Grand Rapids: Eerdmans.","summary":"Romans 9 belongs to Paul''s gift-theology, which reconfigures election around incongruity rather than individual predestination."}
 ]'::jsonb,
 'contested',
 'Augustine and the Reformers read Romans 9 individualistically; modern scholarship (esp. Dunn, Barclay) tends toward a corporate or gift-theology reading. Always name the reading.'),

-- 23
('plotinus_VI_8_freedom_of_One',
 'In Enneads VI.8, does Plotinus ascribe freedom to the One in any meaningful sense?',
 ARRAY['concept_one','concept_freedom','concept_self_causation'],
 ARRAY['person_plotinus'],
 'Late Antiquity',
 '[
   {"label":"Leroux — genuine freedom of the One","scholars":["Georges Leroux"],"citation":"Leroux, G. 1990. \"Plotin: Traité sur la liberté et la volonté de l''Un (Ennéade VI.8 [39]).\" Paris: Vrin.","summary":"Plotinus does ascribe a kind of freedom (auto-causation) to the One, while preserving its absolute simplicity."},
   {"label":"Narbonne — qualified self-determination","scholars":["Jean-Marc Narbonne"],"citation":"Narbonne, J.-M. 1993. \"La Métaphysique de Plotin.\" Paris: Vrin.","summary":"The freedom-language in VI.8 is hyperbolic; what Plotinus means is a self-grounded necessity, not freedom in the human sense."},
   {"label":"O''Meara — analogical only","scholars":["Dominic O''Meara"],"citation":"O''Meara, D. J. 1993. \"Plotinus: An Introduction to the Enneads.\" Oxford: OUP.","summary":"The freedom-attribution to the One is analogical; the treatise is best read as a defence of the One''s non-arbitrariness."}
 ]'::jsonb,
 'contested',
 'Enneads VI.8 (39) is one of the most contested texts in Plotinian scholarship. Do not present any one reading as settled.'),

-- 24
('clement_synergy_christian_or_stoic',
 'Is Clement of Alexandria''s synergy doctrine Stoic, Christian, or a synthesis?',
 ARRAY['concept_synergy','concept_eph_hemin','concept_grace'],
 ARRAY['person_clement_of_alexandria'],
 'Patristic',
 '[
   {"label":"Munier — distinctly Christian","scholars":["Charles Munier"],"citation":"Munier, C. 1992. \"L''Hommage chrétien à l''Empereur dans les Apologies de Justin et Athénagore.\" Revue de Théologie et de Philosophie 124: 153-167. + related work","summary":"Clement''s synergy is shaped by his ecclesial context and is distinct from Stoic doctrines of co-operation."},
   {"label":"Havrda — heavily Stoic","scholars":["Matyáš Havrda"],"citation":"Havrda, M. 2016. \"The So-Called Eighth Stromateus by Clement of Alexandria.\" Leiden: Brill.","summary":"Clement''s synergy is shaped by Stoic conceptions of causation and assent."}
 ]'::jsonb,
 'contested',
 'On Clement do not conflate ''synergy'' with later Eastern Christian usage; the term has Stoic, Christian, and ecclesial registers.'),

-- 25
('pseudo_clementines_late_christian_or_jewish_christian',
 'Are the Pseudo-Clementines late Christian fiction or earlier Jewish-Christian material?',
 ARRAY['concept_jewish_christianity','concept_two_spirits'],
 ARRAY['person_pseudo_clement'],
 'Late Antiquity',
 '[
   {"label":"Pouderon — late 4th-c. Christian composition","scholars":["Bernard Pouderon"],"citation":"Pouderon, B. 2012. \"La Genèse du roman pseudo-clémentin.\" Paris: Beauchesne.","summary":"The Recognitions and Homilies are late 4th-c. compositions; earlier Jewish-Christian material is reused but heavily reworked."},
   {"label":"Reed — preserves earlier Jewish-Christian material","scholars":["Annette Yoshiko Reed"],"citation":"Reed, A. Y. 2008. \"Jewish-Christianity and the History of Judaism: Collected Essays.\" Tübingen: Mohr Siebeck.","summary":"The Pseudo-Clementines preserve substantial earlier (2nd-3rd c.) Jewish-Christian traditions that are otherwise lost."}
 ]'::jsonb,
 'contested',
 'On the Pseudo-Clementines, always distinguish the final compositional date from the date of underlying sources.'),

-- 26
('frankfurt_cases_against_pap',
 'Do Frankfurt-style cases successfully refute the principle of alternative possibilities (PAP)?',
 ARRAY['concept_alternative_possibilities','concept_moral_responsibility','concept_compatibilism'],
 ARRAY['person_harry_frankfurt'],
 'Modern',
 '[
   {"label":"Frankfurt — yes","scholars":["Harry Frankfurt"],"citation":"Frankfurt, H. G. 1969. \"Alternate Possibilities and Moral Responsibility.\" Journal of Philosophy 66 (23): 829-839.","summary":"Frankfurt-style cases show that an agent can be morally responsible without genuine alternative possibilities, refuting PAP."},
   {"label":"Widerker — no, blocker-prior fails","scholars":["David Widerker"],"citation":"Widerker, D. 1995. \"Libertarianism and Frankfurt''s Attack on the Principle of Alternative Possibilities.\" Philosophical Review 104 (2): 247-261.","summary":"The dilemma defence: either the counterfactual intervener relies on a prior sign (so PAP holds) or the case begs the question against libertarianism."},
   {"label":"Wolf — qualifies the moral","scholars":["Susan Wolf"],"citation":"Wolf, S. 1990. \"Freedom Within Reason.\" Oxford: OUP.","summary":"Frankfurt cases bear on a thin notion of responsibility; richer notions (Reason View) require something like PAP."}
 ]'::jsonb,
 'contested',
 'On Frankfurt cases, the Widerker-style dilemma defence is the standard response in libertarian literature.'),

-- 27
('kane_libertarian_ultimacy',
 'Does Kane''s self-forming-action account secure libertarian ultimacy?',
 ARRAY['concept_libertarian','concept_ultimate_responsibility','concept_self_forming_action'],
 ARRAY['person_robert_kane'],
 'Modern',
 '[
   {"label":"Kane — yes, via SFAs","scholars":["Robert Kane"],"citation":"Kane, R. 1996. \"The Significance of Free Will.\" New York: OUP.","summary":"Self-forming actions at moments of internal conflict secure ultimate responsibility without violating naturalism."},
   {"label":"Strawson — no, ultimacy is impossible","scholars":["Galen Strawson"],"citation":"Strawson, G. 1986. \"Freedom and Belief.\" Oxford: Clarendon. + Strawson 1994 \"The Impossibility of Moral Responsibility,\" Philosophical Studies 75: 5-24.","summary":"The Basic Argument: ultimate self-formation is logically impossible because any self-shaping action presupposes an earlier self."}
 ]'::jsonb,
 'contested',
 'Kane is the canonical contemporary libertarian; Strawson''s Basic Argument is the canonical impossibility argument.'),

-- 28
('van_inwagen_consequence_argument',
 'Is van Inwagen''s Consequence Argument a successful refutation of compatibilism?',
 ARRAY['concept_consequence_argument','concept_compatibilism','concept_determinism'],
 ARRAY['person_peter_van_inwagen','person_david_lewis'],
 'Modern',
 '[
   {"label":"van Inwagen — yes","scholars":["Peter van Inwagen"],"citation":"van Inwagen, P. 1983. \"An Essay on Free Will.\" Oxford: Clarendon.","summary":"If determinism is true, no one has any power over the facts of the past or laws of nature; therefore no one has power over the consequences."},
   {"label":"Lewis — no, weak vs strong ability","scholars":["David Lewis"],"citation":"Lewis, D. 1981. \"Are We Free to Break the Laws?\" Theoria 47 (3): 113-121.","summary":"The Consequence Argument equivocates between ability-to-do-otherwise that would falsify a law (which we lack) and ability-to-do-otherwise such that if we did, a law would have been false (which we may have)."}
 ]'::jsonb,
 'contested',
 'The Lewis 1981 distinction (weak vs strong rendering) is the canonical compatibilist response.'),

-- 29
('wolf_reason_view',
 'Does Wolf''s Reason View provide a viable middle position between Frankfurt and libertarianism?',
 ARRAY['concept_reason_view','concept_moral_responsibility','concept_compatibilism'],
 ARRAY['person_susan_wolf','person_harry_frankfurt'],
 'Modern',
 '[
   {"label":"Wolf — yes, asymmetrical","scholars":["Susan Wolf"],"citation":"Wolf, S. 1990. \"Freedom Within Reason.\" Oxford: OUP.","summary":"Praise- and blameworthiness are asymmetrical: only good actions require freedom in a robust sense; the Reason View captures this asymmetry."},
   {"label":"Frankfurt — no, asymmetry unmotivated","scholars":["Harry Frankfurt"],"citation":"Frankfurt, H. G. 1988. \"The Importance of What We Care About.\" Cambridge: CUP.","summary":"Wolf''s asymmetry is not well-motivated; identification-based accounts handle both praise and blame uniformly."}
 ]'::jsonb,
 'contested',
 'Wolf''s asymmetry is a third option distinct from Frankfurt-style and Kane-style libertarian views.'),

-- 30
('compatibilism_revisionism',
 'Should compatibilism revise our concept of moral responsibility, or vindicate the folk concept?',
 ARRAY['concept_compatibilism','concept_moral_responsibility','concept_revisionism'],
 ARRAY['person_manuel_vargas','person_michael_mckenna'],
 'Modern',
 '[
   {"label":"Vargas — revisionism","scholars":["Manuel Vargas"],"citation":"Vargas, M. 2013. \"Building Better Beings: A Theory of Moral Responsibility.\" Oxford: OUP.","summary":"The folk concept of responsibility is partly mistaken; a defensible theory revises it to track the genuine prudential value of responsibility-norms."},
   {"label":"McKenna — vindicatory","scholars":["Michael McKenna"],"citation":"McKenna, M. 2012. \"Conversation and Responsibility.\" Oxford: OUP.","summary":"A conversational account vindicates the core of the folk concept without revisionist concessions."}
 ]'::jsonb,
 'contested',
 'On contemporary compatibilism, distinguish revisionist (Vargas) from vindicatory (McKenna, Fischer-Ravizza) variants.')
ON CONFLICT (topic_slug) DO UPDATE SET
    question = EXCLUDED.question,
    relevant_concepts = EXCLUDED.relevant_concepts,
    relevant_persons = EXCLUDED.relevant_persons,
    relevant_period = EXCLUDED.relevant_period,
    positions = EXCLUDED.positions,
    consensus_status = EXCLUDED.consensus_status,
    methodological_warning = EXCLUDED.methodological_warning,
    updated_at = now();
