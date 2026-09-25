"""Decisions — the 470 pairs of the C2 queue ``queue_a_misaligned.csv`` (Jev same_content <= 0.3).

Every pair was read on 2026-09-24: the original (Greek/Latin, as stored in the node) against its
English "translation". All 470 English nodes come from one machine batch
(metadata.translation_source = "AI batch: claude-opus-4-6", translation_type = "machine").

Verdicts:
  misaligned          the English does not render this passage: it renders another passage, is
                      a synopsis of another chapter, or adds sentences absent from the original
                      (hybrid / fabricated). -> node withdrawn (edges, corpus twin and citation
                      quarantined).
  aligned_partial     faithful rendering of (the opening of) the same passage -> kept, stamped.
  aligned_exceeds     faithful, but runs on into the following verses -> kept, flagged.
  aligned_strip_note  faithful, followed by a bracketed editorial summary inside the text ->
                      the bracket is moved to metadata, the translation is kept.
  aligned_paraphrase  a synopsis of the same passage in the editor's voice -> kept, relabelled
                      translation_type = machine_paraphrase.
  not_a_pair          vocabulary_gloss original -> no change.

Notes are English only. Glosses between ‹ › are the reviewer's renderings, not quotations; text
between straight quotes is verbatim from the node. The Greek/Latin evidence is copied verbatim
from the node by the apply script, never typed here.
"""

# (translation_id, original_id, verdict, jev_p_same_content)
DECISIONS = [
    # [0] English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)
    ('passage_boethius_cons_35_en', 'passage_boethius_cons_35', 'aligned_partial', 0.25),
    # [1] English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)
    ('passage_boethius_cons_47_en', 'passage_boethius_cons_47', 'aligned_partial', 0.2),
    # [2] English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)
    ('passage_boethius_cons_49_en', 'passage_boethius_cons_49', 'aligned_partial', 0.17),
    # [3] English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)
    ('passage_boethius_cons_51_en', 'passage_boethius_cons_51', 'aligned_partial', 0.17),
    # [4] English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)
    ('passage_boethius_cons_54_en', 'passage_boethius_cons_54', 'aligned_partial', 0.19),
    # [5] English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)
    ('passage_boethius_cons_55_en', 'passage_boethius_cons_55', 'aligned_partial', 0.23),
    # [6] English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)
    ('passage_boethius_cons_57_en', 'passage_boethius_cons_57', 'aligned_partial', 0.3),
    # [7] English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)
    ('passage_boethius_cons_6_en', 'passage_boethius_cons_6', 'aligned_partial', 0.18),
    # [8] English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)
    ('passage_boethius_cons_61_en', 'passage_boethius_cons_61', 'aligned_partial', 0.29),
    # [9] English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)
    ('passage_boethius_cons_63_en', 'passage_boethius_cons_63', 'aligned_partial', 0.25),
    # [10] English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)
    ('passage_boethius_cons_64_en', 'passage_boethius_cons_64', 'aligned_partial', 0.19),
    # [11] English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)
    ('passage_boethius_cons_66_en', 'passage_boethius_cons_66', 'aligned_partial', 0.25),
    # [12] English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)
    ('passage_boethius_cons_67_en', 'passage_boethius_cons_67', 'aligned_partial', 0.09),
    # [13] English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)
    ('passage_boethius_cons_69_en', 'passage_boethius_cons_69', 'aligned_partial', 0.06),
    # [14] English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)
    ('passage_boethius_cons_7_en', 'passage_boethius_cons_7', 'aligned_partial', 0.2),
    # [15] English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)
    ('passage_boethius_cons_74_en', 'passage_boethius_cons_74', 'aligned_partial', 0.29),
    # [16] English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)
    ('passage_boethius_cons_75_en', 'passage_boethius_cons_75', 'aligned_partial', 0.3),
    # [17] English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)
    ('passage_boethius_cons_78_en', 'passage_boethius_cons_78', 'aligned_partial', 0.14),
    # [18] English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)
    ('passage_boethius_cons_80_en', 'passage_boethius_cons_80', 'aligned_partial', 0.14),
    # [19] English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)
    ('passage_boethius_cons_85_en', 'passage_boethius_cons_85', 'aligned_partial', 0.23),
    # [20] English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)
    ('passage_boethius_cons_9_en', 'passage_boethius_cons_9', 'aligned_partial', 0.21),
    # [21] English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)
    ('passage_boethius_cons_93_en', 'passage_boethius_cons_93', 'aligned_partial', 0.24),
    # [22] English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)
    ('passage_boethius_cons_94_en', 'passage_boethius_cons_94', 'aligned_partial', 0.25),
    # [23] vocabulary_gloss original (Greek word list + English commentary); not a translation pair
    ('passage_epict_114_en', 'passage_epict_114', 'not_a_pair', 0.17),
    # [24] Latin 4.1 opens on prosperity coming even to the common crowd; the English gives "I find nothing worthy of you on earth; therefore I challenge you with what is hard" instead — not a rendering of 4.1
    ('passage_sen_prov_4_1_en', 'passage_sen_prov_4_1', 'misaligned', 0.08),
    # [25] English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)
    ('passage_sen_prov_4_5_en', 'passage_sen_prov_4_5', 'aligned_partial', 0.25),
    # [26] Latin 5.1 opens: it is for the good of all that the best men serve as soldiers; the English gives 'Why does God allow anything bad to happen to good men?' and God keeping crimes far from the good — not a rendering of 5.1
    ('passage_sen_prov_5_1_en', 'passage_sen_prov_5_1', 'misaligned', 0.26),
    # [27] (a strange calamity: a long night and palpable darkness); English speaks of those struck and fallen and "no single form of death" — different sentence
    ('sc123_melito_peri_pascha_chap22_en', 'sc123_melito_peri_pascha_chap22', 'misaligned', 0.16),
    # [28] (in the palpable darkness impalpable death lay hidden); English: a newborn brought to the striking angel — different content
    ('sc123_melito_peri_pascha_chap23_en', 'sc123_melito_peri_pascha_chap23', 'misaligned', 0.1),
    # [29] Greek: a firstborn embracing a dark body cries(whom does my right hand hold?); English: Israel guarded by the slaughter of the sheep — different content
    ('sc123_melito_peri_pascha_chap24_en', 'sc123_melito_peri_pascha_chap24', 'misaligned', 0.02),
    # [30] (before the firstborn fell silent, the long silence seized him); English "O strange and inexpressible mystery!" renders chap31, not chap25
    ('sc123_melito_peri_pascha_chap25_en', 'sc123_melito_peri_pascha_chap25', 'misaligned', 0.04),
    # [31] Greek: another firstborn denies being firstborn,(I am not the firstborn); English "Tell me, O angel, what turned you away?" renders chap32
    ('sc123_melito_peri_pascha_chap26_en', 'sc123_melito_peri_pascha_chap26', 'misaligned', 0.02),
    # [32] Greek: lowing of cattle in the fields; English ‹you turned away when you saw the mystery of the Lord› renders chap33
    ('sc123_melito_peri_pascha_chap27_en', 'sc123_melito_peri_pascha_chap27', 'misaligned', 0.02),
    # [33] (wailing ... all Egypt stank); English on the sheep valued on account of the Lord — different content
    ('sc123_melito_peri_pascha_chap28_en', 'sc123_melito_peri_pascha_chap28', 'misaligned', 0.02),
    # [34] (a fearful sight: Egyptian mothers with loosened hair); English "instead of the lamb there was a Son" renders chap5
    ('sc123_melito_peri_pascha_chap29_en', 'sc123_melito_peri_pascha_chap29', 'misaligned', 0.01),
    # [35] (such a calamity engulfed Egypt); English on the Passover consummated in Christ — different content
    ('sc123_melito_peri_pascha_chap30_en', 'sc123_melito_peri_pascha_chap30', 'misaligned', 0.04),
    # [36] (O new and indescribable mystery); English ‹the Law has become Word ... the lamb a Son› — different content
    ('sc123_melito_peri_pascha_chap31_en', 'sc123_melito_peri_pascha_chap31', 'misaligned', 0.05),
    # [37] (tell me, angel, what turned you away); English "as a son he was born ... as a lamb he was led" — different content
    ('sc123_melito_peri_pascha_chap32_en', 'sc123_melito_peri_pascha_chap32', 'misaligned', 0.03),
    # [38] (clearly you were turned away seeing the Lord's mystery); English "He is all things: inasmuch as he judges, he is Law" — different content
    ('sc123_melito_peri_pascha_chap33_en', 'sc123_melito_peri_pascha_chap33', 'misaligned', 0.02),
    # [39] (what is this new mystery, Egypt struck); English "This is Jesus the Christ, to whom be glory forever" — different content
    ('sc123_melito_peri_pascha_chap34_en', 'sc123_melito_peri_pascha_chap34', 'misaligned', 0.01),
    # [40] (nothing said or done without parable); English ‹This is the mystery of the Passover and the reading of the old Law› — different content
    ('sc123_melito_peri_pascha_chap35_en', 'sc123_melito_peri_pascha_chap35', 'misaligned', 0.03),
    # [41] Greek: a model made(of wax, clay or wood); English "What the mystery is ... you shall understand from what follows" — different content
    ('sc123_melito_peri_pascha_chap36_en', 'sc123_melito_peri_pascha_chap36', 'misaligned', 0.02),
    # [42] Greek: the model is destroyed(dissolved as useless) when the reality arises; English "the people was valuable before the church was established" — different content
    ('sc123_melito_peri_pascha_chap37_en', 'sc123_melito_peri_pascha_chap37', 'misaligned', 0.15),
    # [43] (each has its own season, the model its own time); English "when the church arose and the Gospel came forth" — renders chap42
    ('sc123_melito_peri_pascha_chap38_en', 'sc123_melito_peri_pascha_chap38', 'misaligned', 0.03),
    # [44] (as in perishable examples, so in imperishable); English "the type lost its value when the Lord was made manifest" — different content
    ('sc123_melito_peri_pascha_chap39_en', 'sc123_melito_peri_pascha_chap39', 'misaligned', 0.04),
    # [45] (the people became a model, the Law a parable); English on the model of the city abandoned — different content
    ('sc123_melito_peri_pascha_chap40_en', 'sc123_melito_peri_pascha_chap40', 'misaligned', 0.06),
    # [46] (when the church arose, the type was emptied); English ‹the type was once valuable before the reality› — different content
    ('sc123_melito_peri_pascha_chap42_en', 'sc123_melito_peri_pascha_chap42', 'misaligned', 0.22),
    # [47] (once precious the slaughter of the sheep, now worthless); English "The model was dissolved when the city was revealed" — different content
    ('sc123_melito_peri_pascha_chap44_en', 'sc123_melito_peri_pascha_chap44', 'misaligned', 0.14),
    # [48] (precious the Jerusalem below, the narrow inheritance); English renders the opening of chap44 ("once the slaughter of the sheep was precious")
    ('sc123_melito_peri_pascha_chap45_en', 'sc123_melito_peri_pascha_chap45', 'misaligned', 0.06),
    # [49] (what is the Pascha? from suffering); English ‹The blood of the sheep was precious ... the silent lamb› renders chap44
    ('sc123_melito_peri_pascha_chap46_en', 'sc123_melito_peri_pascha_chap46', 'misaligned', 0.02),
    # [50] (to clothe the sufferer and snatch him to heaven); English ‹The temple below was precious ... the Jerusalem below› renders chap44/45
    ('sc123_melito_peri_pascha_chap47_en', 'sc123_melito_peri_pascha_chap47', 'misaligned', 0.02),
    # [51] (man, by nature receptive of good and evil); English "The narrow inheritance was precious" renders chap45
    ('sc123_melito_peri_pascha_chap48_en', 'sc123_melito_peri_pascha_chap48', 'misaligned', 0.01),
    # [52] (he left his children an inheritance ... not freedom but slavery); English "there the almighty God has made his dwelling" renders the end of chap45
    ('sc123_melito_peri_pascha_chap49_en', 'sc123_melito_peri_pascha_chap49', 'misaligned', 0.01),
    # [53] (instead of the lamb God, instead of the sheep a man); English ‹like a sheep he was led to the slaughter, yet he was not a sheep› — different content
    ('sc123_melito_peri_pascha_chap5_en', 'sc123_melito_peri_pascha_chap5', 'misaligned', 0.22),
    # [54] (they were snatched by tyrannical sin); English ‹What is the Passover? Its name is taken from the event› renders chap46
    ('sc123_melito_peri_pascha_chap50_en', 'sc123_melito_peri_pascha_chap50', 'misaligned', 0.01),
    # [55] (father raised a sword against son); English ‹Learn who is the one who suffers› renders chap46–47
    ('sc123_melito_peri_pascha_chap51_en', 'sc123_melito_peri_pascha_chap51', 'misaligned', 0.02),
    # [56] (a mother touched the flesh she had borne); English "God, having made the heavens and the earth ... fashioned humanity" — different content
    ('sc123_melito_peri_pascha_chap52_en', 'sc123_melito_peri_pascha_chap52', 'misaligned', 0.01),
    # [57] (father to child's bed, son to mother's); English on the commandment about the tree of knowledge — different content
    ('sc123_melito_peri_pascha_chap53_en', 'sc123_melito_peri_pascha_chap53', 'misaligned', 0.01),
    # [58] (at these things sin rejoiced); English ‹the human being, by nature capable of receiving both good and evil› renders chap48
    ('sc123_melito_peri_pascha_chap54_en', 'sc123_melito_peri_pascha_chap54', 'misaligned', 0.03),
    # [59] (all flesh fell under sin); English ‹He was cast out into this world as into a prison› renders the end of chap48 + chap49
    ('sc123_melito_peri_pascha_chap55_en', 'sc123_melito_peri_pascha_chap55', 'misaligned', 0.05),
    # [60] Greek: man divided by death, the Father's image left desolate, hence the Pascha mystery fulfilled in the Lord's body; English: sin rejoicing, adultery and fornication — different content
    ('sc123_melito_peri_pascha_chap56_en', 'sc123_melito_peri_pascha_chap56', 'misaligned', 0.03),
    # [61] Greek opens: the Lord prearranged his sufferings in patriarchs and prophets; English prefixes a sentence from the preceding section and stops after the first clause — mixed, not this passage
    ('sc123_melito_peri_pascha_chap57_en', 'sc123_melito_peri_pascha_chap57', 'misaligned', 0.23),
    # [62] Greek: the Lord's mystery, long prefigured, now seen, old by type and new by grace; English: 'He who suspended the earth is himself suspended' renders chap96
    ('sc123_melito_peri_pascha_chap58_en', 'sc123_melito_peri_pascha_chap58', 'misaligned', 0.04),
    # [63] Greek: look to Abel murdered, Isaac bound, Joseph sold, Moses exposed, David persecuted; English: 'O unprecedented murder!' renders chap97
    ('sc123_melito_peri_pascha_chap59_en', 'sc123_melito_peri_pascha_chap59', 'misaligned', 0.03),
    # [64] Greek: the slaughter of the sheep, the Pascha rite and the Law have come to fulfilment in Christ; English: 'instead of the lamb there was a Son' — different sentence (same text also on chap29_en)
    ('sc123_melito_peri_pascha_chap6_en', 'sc123_melito_peri_pascha_chap6', 'misaligned', 0.09),
    # [65] Greek: look at the sheep slaughtered in Egypt that struck Egypt and saved Israel; English: the luminaries turned away (chap97)
    ('sc123_melito_peri_pascha_chap60_en', 'sc123_melito_peri_pascha_chap60', 'misaligned', 0.02),
    # [66] Greek: the mystery proclaimed by the prophets, Moses' ‹you will see your life hanging›; English: the earth trembled while the people did not (chap98)
    ('sc123_melito_peri_pascha_chap61_en', 'sc123_melito_peri_pascha_chap61', 'misaligned', 0.02),
    # [67] Greek: David's ‹Why did the nations rage› (Ps 2); English: ‹Listen, all families of the nations ... an unprecedented murder› (chap94)
    ('sc123_melito_peri_pascha_chap62_en', 'sc123_melito_peri_pascha_chap62', 'misaligned', 0.01),
    # [68] Greek: Jeremiah's ‹I was like an innocent lamb led to be sacrificed›; English: murder in the middle of the street (chap94)
    ('sc123_melito_peri_pascha_chap63_en', 'sc123_melito_peri_pascha_chap63', 'misaligned', 0.02),
    # [69] Greek: Isaiah's ‹like a sheep he was led to slaughter›; English: lifted up upon the tree with a title (chap95)
    ('sc123_melito_peri_pascha_chap64_en', 'sc123_melito_peri_pascha_chap64', 'misaligned', 0.02),
    # [70] Greek: many other things proclaimed by the prophets about the Pascha mystery, which is Christ; English: 'The one who hung the earth in space is himself hung' (chap96)
    ('sc123_melito_peri_pascha_chap65_en', 'sc123_melito_peri_pascha_chap65', 'misaligned', 0.04),
    # [71] Greek: he came from heaven, clothed himself with the sufferer through a virgin's womb; English: 'O unprecedented murder!' (chap97)
    ('sc123_melito_peri_pascha_chap66_en', 'sc123_melito_peri_pascha_chap66', 'misaligned', 0.03),
    # [72] Greek: led as a lamb, he ransomed us from the world's slavery as from Egypt; English: darkening not the Lord's body but men's eyes, earth trembling (chap97–98)
    ('sc123_melito_peri_pascha_chap67_en', 'sc123_melito_peri_pascha_chap67', 'misaligned', 0.01),
    # [73] Greek: ‹O lawless Israel, what is this new crime?›; English: 'He who suspended the earth is himself suspended' (chap96)
    ('sc123_melito_peri_pascha_chap81_en', 'sc123_melito_peri_pascha_chap81', 'misaligned', 0.15),
    # [74] Greek: you did not recognise God, the firstborn begotten before the morning star; English: 'O unprecedented murder!' (chap97)
    ('sc123_melito_peri_pascha_chap82_en', 'sc123_melito_peri_pascha_chap82', 'misaligned', 0.02),
    # [75] Greek: who fitted the stars ... who chose you and guided you from Adam to Noah to Abraham; English: 'Raise your eyes, O Israel' — different content
    ('sc123_melito_peri_pascha_chap83_en', 'sc123_melito_peri_pascha_chap83', 'misaligned', 0.18),
    # [76] Greek: he guided you into Egypt, lit you by the pillar, split the Red Sea; English: the luminaries turned away (chap97)
    ('sc123_melito_peri_pascha_chap84_en', 'sc123_melito_peri_pascha_chap84', 'misaligned', 0.02),
    # [77] Greek: he gave you manna from heaven, water from the rock, the law at Horeb; English: the earth trembled while the people did not (chap98)
    ('sc123_melito_peri_pascha_chap85_en', 'sc123_melito_peri_pascha_chap85', 'misaligned', 0.03),
    # [78] Greek: he came to you, healed your sick, raised your dead ... this is he whom you killed; English: 'you did not tremble at the presence of the Lord' (chap99)
    ('sc123_melito_peri_pascha_chap86_en', 'sc123_melito_peri_pascha_chap86', 'misaligned', 0.03),
    # [79] Greek: ‹Ungrateful Israel, come and be judged ... at what price did you value ...›; English: 'Listen, all families of the nations' (chap94)
    ('sc123_melito_peri_pascha_chap87_en', 'sc123_melito_peri_pascha_chap87', 'misaligned', 0.01),
    # [80] Greek: at what price did you value the ten plagues, the pillar, the manna; English: ‹who is the murderer? ... in the middle of the street› (chap94)
    ('sc123_melito_peri_pascha_chap88_en', 'sc123_melito_peri_pascha_chap88', 'misaligned', 0.01),
    # [81] Greek: value for me the sick he healed, the withered hand he restored; English: lifted up upon the tree with a title (chap95)
    ('sc123_melito_peri_pascha_chap89_en', 'sc123_melito_peri_pascha_chap89', 'misaligned', 0.02),
    # [82] Greek: value for me the blind from birth he enlightened, the dead he raised; English: 'The one who hung the earth in space is himself hung' (chap96)
    ('sc123_melito_peri_pascha_chap90_en', 'sc123_melito_peri_pascha_chap90', 'misaligned', 0.06),
    # [83] Greek is a single clause (for whom you should have died); English: 'O unheard-of murder!' (chap97)
    ('sc123_melito_peri_pascha_chap91_en', 'sc123_melito_peri_pascha_chap91', 'misaligned', 0.06),
    # [84] Greek: you voted against your Lord, whom the nations worshipped, for whom Pilate washed his hands; English: ‹Who is the one who has contended with me? ... I, the Christ› — different content
    ('sc123_melito_peri_pascha_chap92_en', 'sc123_melito_peri_pascha_chap92', 'misaligned', 0.04),
    # [85] Greek: bitter for you the feast of unleavened bread, bitter the nails, the false witnesses, Judas, Herod; English: ‹I bound the strong one ... I am the Christ› — different content
    ('sc123_melito_peri_pascha_chap93_en', 'sc123_melito_peri_pascha_chap93', 'misaligned', 0.01),
    # [86] Greek: ‹Listen, all families of the nations ... a new murder in the midst of Jerusalem›; English: ‹Come, all families of humankind ... receive forgiveness of sins› — different content
    ('sc123_melito_peri_pascha_chap94_en', 'sc123_melito_peri_pascha_chap94', 'misaligned', 0.01),
    # [87] Greek: he is lifted up upon the tree with a title; English: 'I will lead you up to the heights of the heavens' — different content
    ('sc123_melito_peri_pascha_chap95_en', 'sc123_melito_peri_pascha_chap95', 'misaligned', 0.02),
    # [88] Greek: ‹He who hung the earth is hung ... God is murdered›; English: 'This is he who made the heavens and the earth' — different content
    ('sc123_melito_peri_pascha_chap96_en', 'sc123_melito_peri_pascha_chap96', 'misaligned', 0.14),
    # [89] Greek: ‹O new murder ... the luminaries turned away›; English: 'This is he who was raised from the dead' — different content
    ('sc123_melito_peri_pascha_chap97_en', 'sc123_melito_peri_pascha_chap97', 'misaligned', 0.02),
    # [90] Greek: the earth trembled while the people did not; English: 'He is the Alpha and the Omega' — different content
    ('sc123_melito_peri_pascha_chap98_en', 'sc123_melito_peri_pascha_chap98', 'misaligned', 0.01),
    # [91] Greek: ‹Therefore, O Israel, you did not tremble before the Lord›; English: doxology and scribal colophon of the whole homily — different content
    ('sc123_melito_peri_pascha_chap99_en', 'sc123_melito_peri_pascha_chap99', 'misaligned', 0.02),
    # [92] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_i_par11_en', 'sc132_origenes_contra_celsum_i_par11', 'aligned_partial', 0.3),
    # [93] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_i_par12_en', 'sc132_origenes_contra_celsum_i_par12', 'aligned_partial', 0.21),
    # [94] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_i_par13_en', 'sc132_origenes_contra_celsum_i_par13', 'aligned_partial', 0.28),
    # [95] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_i_par14_en', 'sc132_origenes_contra_celsum_i_par14', 'aligned_partial', 0.16),
    # [96] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_i_par15_en', 'sc132_origenes_contra_celsum_i_par15', 'aligned_partial', 0.12),
    # [97] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_i_par16_en', 'sc132_origenes_contra_celsum_i_par16', 'aligned_partial', 0.18),
    # [98] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_i_par19_en', 'sc132_origenes_contra_celsum_i_par19', 'aligned_partial', 0.1),
    # [99] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_i_par20_en', 'sc132_origenes_contra_celsum_i_par20', 'aligned_partial', 0.17),
    # [100] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_i_par21_en', 'sc132_origenes_contra_celsum_i_par21', 'aligned_partial', 0.1),
    # [101] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_i_par22_en', 'sc132_origenes_contra_celsum_i_par22', 'aligned_partial', 0.2),
    # [102] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_i_par23_en', 'sc132_origenes_contra_celsum_i_par23', 'aligned_partial', 0.22),
    # [103] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_i_par24_en', 'sc132_origenes_contra_celsum_i_par24', 'aligned_partial', 0.19),
    # [104] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_i_par25_en', 'sc132_origenes_contra_celsum_i_par25', 'aligned_partial', 0.23),
    # [105] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_i_par26_en', 'sc132_origenes_contra_celsum_i_par26', 'aligned_partial', 0.27),
    # [106] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_i_par26_a_en', 'sc132_origenes_contra_celsum_i_par26_a', 'aligned_partial', 0.16),
    # [107] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_i_par27_en', 'sc132_origenes_contra_celsum_i_par27', 'aligned_partial', 0.27),
    # [108] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_i_par3_en', 'sc132_origenes_contra_celsum_i_par3', 'aligned_partial', 0.2),
    # [109] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_i_par30_en', 'sc132_origenes_contra_celsum_i_par30', 'aligned_partial', 0.29),
    # [110] Greek opens: one might wonder how the disciples, who (as detractors say) had not seen him risen, came not to fear suffering like their master; English opens 'Now that this teaching has spread throughout the whole world ... it was God's will' — not this section's argument
    ('sc132_origenes_contra_celsum_i_par31_en', 'sc132_origenes_contra_celsum_i_par31', 'misaligned', 0.13),
    # [111] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_i_par48_b_en', 'sc132_origenes_contra_celsum_i_par48_b', 'aligned_partial', 0.15),
    # [112] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_i_par57_en', 'sc132_origenes_contra_celsum_i_par57', 'aligned_partial', 0.2),
    # [113] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_i_par6_en', 'sc132_origenes_contra_celsum_i_par6', 'aligned_partial', 0.22),
    # [114] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_ii_par44_a_en', 'sc132_origenes_contra_celsum_ii_par44_a', 'aligned_partial', 0.05),
    # [115] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_ii_par45_en', 'sc132_origenes_contra_celsum_ii_par45', 'aligned_partial', 0.19),
    # [116] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_ii_par62_en', 'sc132_origenes_contra_celsum_ii_par62', 'aligned_partial', 0.21),
    # [117] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_ii_par63_en', 'sc132_origenes_contra_celsum_ii_par63', 'aligned_partial', 0.27),
    # [118] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_ii_par64_en', 'sc132_origenes_contra_celsum_ii_par64', 'aligned_partial', 0.22),
    # [119] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_ii_par65_a_en', 'sc132_origenes_contra_celsum_ii_par65_a', 'aligned_partial', 0.21),
    # [120] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_ii_par68_en', 'sc132_origenes_contra_celsum_ii_par68', 'aligned_partial', 0.26),
    # [121] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_ii_par69_a_en', 'sc132_origenes_contra_celsum_ii_par69_a', 'aligned_partial', 0.27),
    # [122] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_ii_par70_en', 'sc132_origenes_contra_celsum_ii_par70', 'aligned_partial', 0.22),
    # [123] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_ii_par74_en', 'sc132_origenes_contra_celsum_ii_par74', 'aligned_partial', 0.22),
    # [124] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_ii_par75_en', 'sc132_origenes_contra_celsum_ii_par75', 'aligned_partial', 0.2),
    # [125] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_ii_par76_a_en', 'sc132_origenes_contra_celsum_ii_par76_a', 'aligned_partial', 0.13),
    # [126] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_ii_par78_en', 'sc132_origenes_contra_celsum_ii_par78', 'aligned_partial', 0.19),
    # [127] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_ii_par79_a_en', 'sc132_origenes_contra_celsum_ii_par79_a', 'aligned_partial', 0.19),
    # [128] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_ii_par8_en', 'sc132_origenes_contra_celsum_ii_par8', 'aligned_partial', 0.19),
    # [129] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_ii_par8_a_en', 'sc132_origenes_contra_celsum_ii_par8_a', 'aligned_partial', 0.2),
    # [130] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_ii_par9_en', 'sc132_origenes_contra_celsum_ii_par9', 'aligned_partial', 0.21),
    # [131] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc132_origenes_contra_celsum_praef_par4_en', 'sc132_origenes_contra_celsum_praef_par4', 'aligned_partial', 0.19),
    # [132] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc136_origenes_contra_celsum_iii_par15_en', 'sc136_origenes_contra_celsum_iii_par15', 'aligned_partial', 0.16),
    # [133] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc136_origenes_contra_celsum_iii_par2_en', 'sc136_origenes_contra_celsum_iii_par2', 'aligned_partial', 0.18),
    # [134] Greek: Celsus likens worship of one captured and executed to the Getae's Zamolxis, the Cilicians' Mopsus, etc.; English: Jesus gathering 'ten or twenty ... tax-collectors and sailors' — a different section
    ('sc136_origenes_contra_celsum_iii_par34_a_en', 'sc136_origenes_contra_celsum_iii_par34_a', 'misaligned', 0.01),
    # [135] Greek: Celsus misrepresents the calls to repentance addressed to those who lived badly, saying we claim God was sent to sinners; English opens with Celsus likening conversion to Greek doctrines vs. the mysteries of Mithras and Sabazius — not this section
    ('sc136_origenes_contra_celsum_iii_par62_en', 'sc136_origenes_contra_celsum_iii_par62', 'misaligned', 0.03),
    # [136] Greek: Celsus does not understand ‹whoever exalts himself shall be humbled› (with Plato on the humble good man); English: 'let whoever is ignorant come to me ... I shall make wise' — different section
    ('sc136_origenes_contra_celsum_iii_par63_en', 'sc136_origenes_contra_celsum_iii_par63', 'misaligned', 0.02),
    # [137] Greek: ‹What then is this preference for sinners?› — Origen: a sinner as such is not preferred; English: no philosopher says 'Let a robber come to me' — different argument
    ('sc136_origenes_contra_celsum_iii_par64_en', 'sc136_origenes_contra_celsum_iii_par64', 'misaligned', 0.03),
    # [138] Greek: Celsus thinks we court sinners because we cannot win the upright; English: the Jew accuses Jesus of fabricating his virgin birth — different content
    ('sc136_origenes_contra_celsum_iii_par65_en', 'sc136_origenes_contra_celsum_iii_par65', 'misaligned', 0.01),
    # [139] Greek: Celsus denies complete change to those sinful by nature and habit; English: the Jew asks how believers can despise the religion they came from — different content
    ('sc136_origenes_contra_celsum_iii_par66_en', 'sc136_origenes_contra_celsum_iii_par66', 'misaligned', 0.01),
    # [140] Greek: no one could wholly change those naturally and habitually sinful, refuted by philosophers' lives; English: 'What made you abandon the law of your fathers?' — different content
    ('sc136_origenes_contra_celsum_iii_par67_en', 'sc136_origenes_contra_celsum_iii_par67', 'misaligned', 0.01),
    # [141] Greek: order and style of philosophical discourse vs. Celsus' ‹unlearned› words like incantations; English: the Jew addresses converts from Judaism — different content
    ('sc136_origenes_contra_celsum_iii_par68_en', 'sc136_origenes_contra_celsum_iii_par68', 'misaligned', 0.01),
    # [142] Greek: Celsus says changing nature completely is very hard; Origen: one nature of every rational soul; English: the Jew addresses Gentile believers — different content
    ('sc136_origenes_contra_celsum_iii_par69_en', 'sc136_origenes_contra_celsum_iii_par69', 'misaligned', 0.02),
    # [143] Greek: Celsus says the sinless are better companions; English: Egyptians, Scythians and Persians should keep their customs — different content
    ('sc136_origenes_contra_celsum_iii_par69_a_en', 'sc136_origenes_contra_celsum_iii_par69_a', 'misaligned', 0.02),
    # [144] Greek: the whole people leaving Egypt took up Hebrew as a God-given language; English: Jews and Christians both 'revolted' (Egyptians / Jews) — different argument
    ('sc136_origenes_contra_celsum_iii_par7_en', 'sc136_origenes_contra_celsum_iii_par7', 'misaligned', 0.03),
    # [145] Greek: Celsus objects ‹God will be able to do all things›; English: the Jew's 'Not long ago ... yesterday or the day before' — different content
    ('sc136_origenes_contra_celsum_iii_par70_en', 'sc136_origenes_contra_celsum_iii_par70', 'misaligned', 0.01),
    # [146] Greek: Celsus assumes God, slave to pity, relieves the wicked and rejects the good; English: 'Why do you seek yet another origin?' — different content
    ('sc136_origenes_contra_celsum_iii_par71_en', 'sc136_origenes_contra_celsum_iii_par71', 'misaligned', 0.01),
    # [147] Greek: in the person of our teacher Celsus says ‹the wise turn away from what we say›; English: 'If someone predicted to you that the Son of God would come' — different content
    ('sc136_origenes_contra_celsum_iii_par72_en', 'sc136_origenes_contra_celsum_iii_par72', 'misaligned', 0.01),
    # [148] Greek: Celsus reviles the preacher of Christianity as saying ridiculous things; English: 'What sort of God is this who cannot even convince his own offspring?' — different content
    ('sc136_origenes_contra_celsum_iii_par73_en', 'sc136_origenes_contra_celsum_iii_par73', 'misaligned', 0.03),
    # [149] Greek: Celsus charges the teacher with seeking the foolish — ‹whom do you call foolish?›; English: the Jew accuses Jesus of not showing himself God — different content
    ('sc136_origenes_contra_celsum_iii_par74_en', 'sc136_origenes_contra_celsum_iii_par74', 'misaligned', 0.01),
    # [150] Greek: Celsus compares the Christian teacher to one promising health but keeping patients from physicians; English: 'If these things were decreed for him ...' — different content
    ('sc136_origenes_contra_celsum_iii_par75_en', 'sc136_origenes_contra_celsum_iii_par75', 'misaligned', 0.01),
    # [151] Greek: turning people from Epicurus and ‹Epicurean physicians› who deny providence; English: objections to the resurrection appearances — different content
    ('sc136_origenes_contra_celsum_iii_par75_a_en', 'sc136_origenes_contra_celsum_iii_par75_a', 'misaligned', 0.02),
    # [152] Greek: we do not flee to infants and rustics saying ‹avoid physicians›; English: had Jesus appeared to all, Celsus would call it a phantom — different content
    ('sc136_origenes_contra_celsum_iii_par75_b_en', 'sc136_origenes_contra_celsum_iii_par75_b', 'misaligned', 0.02),
    # [153] Greek: Celsus' second example, a drunkard accusing the sober of drunkenness; English: the Jew's list of charges (virgin birth, village, spinner mother) — different content
    ('sc136_origenes_contra_celsum_iii_par76_en', 'sc136_origenes_contra_celsum_iii_par76', 'misaligned', 0.01),
    # [154] Greek: Celsus likens the teacher to one with ophthalmia blaming the sharp-sighted; English: ‹Why, being God, did he not deliver himself from this shame?› — different content
    ('sc136_origenes_contra_celsum_iii_par77_en', 'sc136_origenes_contra_celsum_iii_par77', 'misaligned', 0.01),
    # [155] Greek: Celsus says he could say more but keeps silent; English: 'let us look at what has been taught by this teacher himself' — different content
    ('sc136_origenes_contra_celsum_iii_par78_en', 'sc136_origenes_contra_celsum_iii_par78', 'misaligned', 0.03),
    # [156] Greek: if anyone imagines superstition rather than wickedness among believers ...; English: Celsus on 'Blessed are the poor' and Plato — different content
    ('sc136_origenes_contra_celsum_iii_par79_en', 'sc136_origenes_contra_celsum_iii_par79', 'misaligned', 0.01),
    # [157] Greek: it is false that the Hebrews, being Egyptians, began from a revolt; English: the Jew's charge that Jesus fabricated his virgin birth — different content
    ('sc136_origenes_contra_celsum_iii_par8_en', 'sc136_origenes_contra_celsum_iii_par8', 'misaligned', 0.01),
    # [158] Greek: Celsus says Christians are led by vain hopes; English: the bird at the Jordan and ‹what credible witness saw this?› — different content
    ('sc136_origenes_contra_celsum_iii_par80_en', 'sc136_origenes_contra_celsum_iii_par80', 'misaligned', 0.01),
    # [159] Greek: philosophers on the immortality of the soul, the future blessed life; English: 'What was the purpose of your descent to earth?' — different content
    ('sc136_origenes_contra_celsum_iii_par81_en', 'sc136_origenes_contra_celsum_iii_par81', 'misaligned', 0.01),
    # [160] Greek: closing formula of Book III (‹here we end the third tome›); English: God acting through the incarnation — different content
    ('sc136_origenes_contra_celsum_iii_par81_a_en', 'sc136_origenes_contra_celsum_iii_par81_a', 'misaligned', 0.02),
    # [161] Greek: ‹If all men wished to be Christians, these would no longer wish it› — refuted; English: Celsus on the resurrection of the body as disgusting and impossible — different content
    ('sc136_origenes_contra_celsum_iii_par9_en', 'sc136_origenes_contra_celsum_iii_par9', 'misaligned', 0.01),
    # [162] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc136_origenes_contra_celsum_iv_par11_en', 'sc136_origenes_contra_celsum_iv_par11', 'aligned_partial', 0.2),
    # [163] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc136_origenes_contra_celsum_iv_par13_en', 'sc136_origenes_contra_celsum_iv_par13', 'aligned_partial', 0.26),
    # [164] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc136_origenes_contra_celsum_iv_par17_en', 'sc136_origenes_contra_celsum_iv_par17', 'aligned_partial', 0.26),
    # [165] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc136_origenes_contra_celsum_iv_par2_en', 'sc136_origenes_contra_celsum_iv_par2', 'aligned_partial', 0.08),
    # [166] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc136_origenes_contra_celsum_iv_par23_en', 'sc136_origenes_contra_celsum_iv_par23', 'aligned_partial', 0.24),
    # [167] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc136_origenes_contra_celsum_iv_par26_a_en', 'sc136_origenes_contra_celsum_iv_par26_a', 'aligned_partial', 0.15),
    # [168] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc136_origenes_contra_celsum_iv_par27_en', 'sc136_origenes_contra_celsum_iv_par27', 'aligned_partial', 0.2),
    # [169] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc136_origenes_contra_celsum_iv_par3_b_en', 'sc136_origenes_contra_celsum_iv_par3_b', 'aligned_partial', 0.16),
    # [170] faithful translation of the opening, followed by a bracketed editorial summary appended inside the translation text
    ('sc136_origenes_contra_celsum_iv_par41_en', 'sc136_origenes_contra_celsum_iv_par41', 'aligned_strip_note', 0.24),
    # [171] faithful translation of the opening, followed by a bracketed editorial summary appended inside the translation text
    ('sc136_origenes_contra_celsum_iv_par49_a_en', 'sc136_origenes_contra_celsum_iv_par49_a', 'aligned_strip_note', 0.24),
    # [172] English is a one-line placeholder ('Let us then see what follows in Celsus' text next.') for a 1,071-character Greek section on those who ‹moved from the east›
    ('sc147_origenes_contra_celsum_v_par32_a_en', 'sc147_origenes_contra_celsum_v_par32_a', 'misaligned', 0.02),
    # [173] pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: after the Isaiah quotation it adds 'This universal gathering ... is the fulfillment of what was only partially accomplished in the history of Israel ... the calling of Abraham', absent from the Greek, and omits Celsus' ‹Let the second come›
    ('sc147_origenes_contra_celsum_v_par33_en', 'sc147_origenes_contra_celsum_v_par33', 'misaligned', 0.16),
    # [174] Greek quotes Herodotus on the people of Marea and Apis (Ammon and cows); English says Celsus cites Herodotus 'on ... the disposal of their dead' — content not in the Greek
    ('sc147_origenes_contra_celsum_v_par34_en', 'sc147_origenes_contra_celsum_v_par34', 'misaligned', 0.1),
    # [175] pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek ('This sounds tolerant and reasonable ...')
    ('sc147_origenes_contra_celsum_v_par35_en', 'sc147_origenes_contra_celsum_v_par35', 'misaligned', 0.08),
    # [176] pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: the English asks whether Ammon is 'omnipotent, omniscient, perfectly good', absent from the Greek
    ('sc147_origenes_contra_celsum_v_par36_en', 'sc147_origenes_contra_celsum_v_par36', 'misaligned', 0.05),
    # [177] pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: 'Celsus's moral relativism, if taken seriously ...'
    ('sc147_origenes_contra_celsum_v_par36_a_en', 'sc147_origenes_contra_celsum_v_par36_a', 'misaligned', 0.1),
    # [178] pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: 'nomos engraphos ... varies from people to people ... as even the pagan philosophers recognized' — not in the Greek, which argues one must follow God's law even at the cost of dangers and death
    ('sc147_origenes_contra_celsum_v_par37_en', 'sc147_origenes_contra_celsum_v_par37', 'misaligned', 0.3),
    # [179] pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: the Greek lists Meroe's Zeus and Dionysus, Arabian Urania, Osiris and Isis, Sarapis and the Son ‹firstborn of all creation›; the English gives a generic summary without any of this
    ('sc147_origenes_contra_celsum_v_par37_a_en', 'sc147_origenes_contra_celsum_v_par37_a', 'misaligned', 0.2),
    # [180] pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: the Greek asks whether an Ethiopian in Arabia threatened with death should worship Urania; the English turns it into questions about conversion to philosophy not in the text
    ('sc147_origenes_contra_celsum_v_par38_en', 'sc147_origenes_contra_celsum_v_par38', 'misaligned', 0.17),
    # [181] pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: 'The Egyptian gods Osiris, Isis, and Sarapis have their origins in mythological stories about human beings' — not the Greek (Osiris allegorised as water, Isis as earth)
    ('sc147_origenes_contra_celsum_v_par38_a_en', 'sc147_origenes_contra_celsum_v_par38_a', 'misaligned', 0.05),
    # [182] pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: the Greek discusses edible and inedible animals and the Son as virtue and ‹second God›; the English is a generic polemic on crocodiles
    ('sc147_origenes_contra_celsum_v_par39_en', 'sc147_origenes_contra_celsum_v_par39', 'misaligned', 0.25),
    # [183] pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: the English omits Celsus' question ‹gods or another race?› and adds 'more genuine worship ... more fitting for rational souls'
    ('sc147_origenes_contra_celsum_v_par4_en', 'sc147_origenes_contra_celsum_v_par4', 'misaligned', 0.11),
    # [184] pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: the English attributes to Celsus a charge of 'arrogance (alazoneia)' in separating from other nations, while the Greek quotes Celsus that the Jews are blameless if they keep their own law
    ('sc147_origenes_contra_celsum_v_par41_en', 'sc147_origenes_contra_celsum_v_par41', 'misaligned', 0.04),
    # [185] pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: the Greek describes the Jewish polity (no gymnastic contests, no prostitution); the English invents a dilemma ('if this special relationship is real ...')
    ('sc147_origenes_contra_celsum_v_par42_en', 'sc147_origenes_contra_celsum_v_par42', 'misaligned', 0.08),
    # [186] pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: the first sentence loosely renders the Greek, the second ('Most nations worshipped ... the sun, the moon, statues, animals') is added
    ('sc147_origenes_contra_celsum_v_par42_a_en', 'sc147_origenes_contra_celsum_v_par42_a', 'misaligned', 0.08),
    # [187] pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: 'Origen notes an example of the humanity of Jewish law ... without parallel in the ancient world ... dignity of the human person' — commentary, not the Greek
    ('sc147_origenes_contra_celsum_v_par43_en', 'sc147_origenes_contra_celsum_v_par43', 'misaligned', 0.1),
    # [188] pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: the Greek is on names and incantations losing force in translation; the English adds 'El Shaddai' and 'intrinsic power because they express the very nature of the divine being'
    ('sc147_origenes_contra_celsum_v_par45_en', 'sc147_origenes_contra_celsum_v_par45', 'misaligned', 0.17),
    # [189] pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: 'not because God is jealous in a petty human sense ... This is not arrogance but faithfulness' — absent; the Greek names Zeus, Amun and Papaeus
    ('sc147_origenes_contra_celsum_v_par46_en', 'sc147_origenes_contra_celsum_v_par46', 'misaligned', 0.17),
    # [190] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc147_origenes_contra_celsum_v_par49_en', 'sc147_origenes_contra_celsum_v_par49', 'aligned_partial', 0.3),
    # [191] Greek: it is not reasonable to judge truth-tellers and liars thus; those who practise not being deceived pronounce slowly after inquiry; English: astonishment that the devout are less trusted than Greek philosophers — different content
    ('sc147_origenes_contra_celsum_v_par57_a_en', 'sc147_origenes_contra_celsum_v_par57_a', 'misaligned', 0.03),
    # [192] Greek: Celsus mocks the angel rolling away the stone from the tomb; English: an angel came to the carpenter about Mary and the flight — different content
    ('sc147_origenes_contra_celsum_v_par58_en', 'sc147_origenes_contra_celsum_v_par58', 'misaligned', 0.01),
    # [193] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_v_par6_en', 'sc147_origenes_contra_celsum_v_par6', 'misaligned', 0.16),
    # [194] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_v_par60_en', 'sc147_origenes_contra_celsum_v_par60', 'misaligned', 0.09),
    # [195] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek (it adds a reference to 'the most impious heresy of Marcion, who posits two first principles')
    ('sc147_origenes_contra_celsum_v_par61_en', 'sc147_origenes_contra_celsum_v_par61', 'misaligned', 0.03),
    # [196] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek (it adds 'every rational soul was created with free will (autexousion)', not in this section's Greek)
    ('sc147_origenes_contra_celsum_v_par61_a_en', 'sc147_origenes_contra_celsum_v_par61_a', 'misaligned', 0.1),
    # [197] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_v_par62_en', 'sc147_origenes_contra_celsum_v_par62', 'misaligned', 0.05),
    # [198] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_v_par63_en', 'sc147_origenes_contra_celsum_v_par63', 'misaligned', 0.18),
    # [199] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_v_par63_a_en', 'sc147_origenes_contra_celsum_v_par63_a', 'misaligned', 0.07),
    # [200] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_v_par64_en', 'sc147_origenes_contra_celsum_v_par64', 'misaligned', 0.14),
    # [201] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_v_par64_a_en', 'sc147_origenes_contra_celsum_v_par64_a', 'misaligned', 0.09),
    # [202] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_v_par65_a_en', 'sc147_origenes_contra_celsum_v_par65_a', 'misaligned', 0.09),
    # [203] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek ('for we worship the Creator of heaven, not any created thing')
    ('sc147_origenes_contra_celsum_v_par7_en', 'sc147_origenes_contra_celsum_v_par7', 'misaligned', 0.05),
    # [204] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_v_par8_en', 'sc147_origenes_contra_celsum_v_par8', 'misaligned', 0.08),
    # [205] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_v_par9_en', 'sc147_origenes_contra_celsum_v_par9', 'misaligned', 0.22),
    # [206] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par1_en', 'sc147_origenes_contra_celsum_vi_par1', 'misaligned', 0.07),
    # [207] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par10_en', 'sc147_origenes_contra_celsum_vi_par10', 'misaligned', 0.05),
    # [208] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par10_a_en', 'sc147_origenes_contra_celsum_vi_par10_a', 'misaligned', 0.06),
    # [209] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par10_b_en', 'sc147_origenes_contra_celsum_vi_par10_b', 'misaligned', 0.26),
    # [210] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par11_en', 'sc147_origenes_contra_celsum_vi_par11', 'misaligned', 0.1),
    # [211] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par12_en', 'sc147_origenes_contra_celsum_vi_par12', 'misaligned', 0.14),
    # [212] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par13_en', 'sc147_origenes_contra_celsum_vi_par13', 'misaligned', 0.07),
    # [213] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par13_a_en', 'sc147_origenes_contra_celsum_vi_par13_a', 'misaligned', 0.09),
    # [214] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par14_en', 'sc147_origenes_contra_celsum_vi_par14', 'misaligned', 0.17),
    # [215] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par14_a_en', 'sc147_origenes_contra_celsum_vi_par14_a', 'misaligned', 0.05),
    # [216] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek (the Plato quotation ‹he who lifts himself up in pride will be abandoned by God› is not the Laws passage quoted in the Greek)
    ('sc147_origenes_contra_celsum_vi_par15_en', 'sc147_origenes_contra_celsum_vi_par15', 'misaligned', 0.04),
    # [217] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par15_a_en', 'sc147_origenes_contra_celsum_vi_par15_a', 'misaligned', 0.13),
    # [218] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par16_en', 'sc147_origenes_contra_celsum_vi_par16', 'misaligned', 0.08),
    # [219] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par16_a_en', 'sc147_origenes_contra_celsum_vi_par16_a', 'misaligned', 0.22),
    # [220] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par17_en', 'sc147_origenes_contra_celsum_vi_par17', 'misaligned', 0.08),
    # [221] English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)
    ('sc147_origenes_contra_celsum_vi_par17_a_en', 'sc147_origenes_contra_celsum_vi_par17_a', 'aligned_partial', 0.18),
    # [222] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par18_en', 'sc147_origenes_contra_celsum_vi_par18', 'misaligned', 0.11),
    # [223] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek (the Greek cites ‹Praise God, heavens of heavens›; the English substitutes 'The heavens declare the glory of God')
    ('sc147_origenes_contra_celsum_vi_par19_en', 'sc147_origenes_contra_celsum_vi_par19', 'misaligned', 0.04),
    # [224] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par19_a_en', 'sc147_origenes_contra_celsum_vi_par19_a', 'misaligned', 0.1),
    # [225] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par2_en', 'sc147_origenes_contra_celsum_vi_par2', 'misaligned', 0.15),
    # [226] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par20_en', 'sc147_origenes_contra_celsum_vi_par20', 'misaligned', 0.08),
    # [227] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par21_en', 'sc147_origenes_contra_celsum_vi_par21', 'misaligned', 0.09),
    # [228] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par22_en', 'sc147_origenes_contra_celsum_vi_par22', 'misaligned', 0.15),
    # [229] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par22_a_en', 'sc147_origenes_contra_celsum_vi_par22_a', 'misaligned', 0.11),
    # [230] hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par23_en', 'sc147_origenes_contra_celsum_vi_par23', 'misaligned', 0.04),
    # [231] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek ('Celsus confuses the teachings of obscure Gnostic sects with those of the Church')
    ('sc147_origenes_contra_celsum_vi_par23_a_en', 'sc147_origenes_contra_celsum_vi_par23_a', 'misaligned', 0.26),
    # [232] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par24_en', 'sc147_origenes_contra_celsum_vi_par24', 'misaligned', 0.11),
    # [233] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par24_a_en', 'sc147_origenes_contra_celsum_vi_par24_a', 'misaligned', 0.12),
    # [234] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par25_en', 'sc147_origenes_contra_celsum_vi_par25', 'misaligned', 0.29),
    # [235] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par25_a_en', 'sc147_origenes_contra_celsum_vi_par25_a', 'misaligned', 0.27),
    # [236] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par26_b_en', 'sc147_origenes_contra_celsum_vi_par26_b', 'misaligned', 0.15),
    # [237] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par27_a_en', 'sc147_origenes_contra_celsum_vi_par27_a', 'misaligned', 0.05),
    # [238] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par28_en', 'sc147_origenes_contra_celsum_vi_par28', 'misaligned', 0.12),
    # [239] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par28_a_en', 'sc147_origenes_contra_celsum_vi_par28_a', 'misaligned', 0.21),
    # [240] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par29_en', 'sc147_origenes_contra_celsum_vi_par29', 'misaligned', 0.05),
    # [241] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par29_a_en', 'sc147_origenes_contra_celsum_vi_par29_a', 'misaligned', 0.19),
    # [242] English renders the same Greek section faithfully (the closing sentence matches the Greek ending)
    ('sc147_origenes_contra_celsum_vi_par2_a_en', 'sc147_origenes_contra_celsum_vi_par2_a', 'aligned_partial', 0.14),
    # [243] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par3_en', 'sc147_origenes_contra_celsum_vi_par3', 'misaligned', 0.04),
    # [244] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par30_en', 'sc147_origenes_contra_celsum_vi_par30', 'misaligned', 0.18),
    # [245] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par31_en', 'sc147_origenes_contra_celsum_vi_par31', 'misaligned', 0.16),
    # [246] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par32_a_en', 'sc147_origenes_contra_celsum_vi_par32_a', 'misaligned', 0.14),
    # [247] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par33_en', 'sc147_origenes_contra_celsum_vi_par33', 'misaligned', 0.18),
    # [248] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par34_en', 'sc147_origenes_contra_celsum_vi_par34', 'misaligned', 0.06),
    # [249] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par35_en', 'sc147_origenes_contra_celsum_vi_par35', 'misaligned', 0.15),
    # [250] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek (the gloss on the 'dead soul' departed from God)
    ('sc147_origenes_contra_celsum_vi_par35_b_en', 'sc147_origenes_contra_celsum_vi_par35_b', 'misaligned', 0.19),
    # [251] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par36_en', 'sc147_origenes_contra_celsum_vi_par36', 'misaligned', 0.14),
    # [252] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par36_a_en', 'sc147_origenes_contra_celsum_vi_par36_a', 'misaligned', 0.1),
    # [253] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par37_en', 'sc147_origenes_contra_celsum_vi_par37', 'misaligned', 0.12),
    # [254] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par38_en', 'sc147_origenes_contra_celsum_vi_par38', 'misaligned', 0.13),
    # [255] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par38_a_en', 'sc147_origenes_contra_celsum_vi_par38_a', 'misaligned', 0.16),
    # [256] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par39_en', 'sc147_origenes_contra_celsum_vi_par39', 'misaligned', 0.03),
    # [257] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par39_a_en', 'sc147_origenes_contra_celsum_vi_par39_a', 'misaligned', 0.2),
    # [258] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par4_en', 'sc147_origenes_contra_celsum_vi_par4', 'misaligned', 0.03),
    # [259] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par41_en', 'sc147_origenes_contra_celsum_vi_par41', 'misaligned', 0.15),
    # [260] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par42_en', 'sc147_origenes_contra_celsum_vi_par42', 'misaligned', 0.12),
    # [261] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par42_b_en', 'sc147_origenes_contra_celsum_vi_par42_b', 'misaligned', 0.07),
    # [262] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek ('Christ voluntarily submitted to suffering ... triumphing over the powers of evil')
    ('sc147_origenes_contra_celsum_vi_par42_c_en', 'sc147_origenes_contra_celsum_vi_par42_c', 'misaligned', 0.3),
    # [263] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par43_en', 'sc147_origenes_contra_celsum_vi_par43', 'misaligned', 0.21),
    # [264] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek ('This explains how a being created good could fall into evil')
    ('sc147_origenes_contra_celsum_vi_par44_en', 'sc147_origenes_contra_celsum_vi_par44', 'misaligned', 0.16),
    # [265] English renders the same Greek section faithfully (the closing sentence matches the Greek ending)
    ('sc147_origenes_contra_celsum_vi_par44_a_en', 'sc147_origenes_contra_celsum_vi_par44_a', 'aligned_partial', 0.09),
    # [266] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par44_b_en', 'sc147_origenes_contra_celsum_vi_par44_b', 'misaligned', 0.17),
    # [267] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par45_en', 'sc147_origenes_contra_celsum_vi_par45', 'misaligned', 0.07),
    # [268] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par46_a_en', 'sc147_origenes_contra_celsum_vi_par46_a', 'misaligned', 0.12),
    # [269] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par47_en', 'sc147_origenes_contra_celsum_vi_par47', 'misaligned', 0.26),
    # [270] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par48_a_en', 'sc147_origenes_contra_celsum_vi_par48_a', 'misaligned', 0.23),
    # [271] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par49_a_en', 'sc147_origenes_contra_celsum_vi_par49_a', 'misaligned', 0.05),
    # [272] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par49_b_en', 'sc147_origenes_contra_celsum_vi_par49_b', 'misaligned', 0.07),
    # [273] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par4_a_en', 'sc147_origenes_contra_celsum_vi_par4_a', 'misaligned', 0.22),
    # [274] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par5_en', 'sc147_origenes_contra_celsum_vi_par5', 'misaligned', 0.04),
    # [275] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek
    ('sc147_origenes_contra_celsum_vi_par50_en', 'sc147_origenes_contra_celsum_vi_par50', 'misaligned', 0.03),
    # [276] hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek (the 'days' of creation said to pertain to the 'kosmos noetos')
    ('sc147_origenes_contra_celsum_vi_par50_a_en', 'sc147_origenes_contra_celsum_vi_par50_a', 'misaligned', 0.04),
    # [277] fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek
    ('sc150_origenes_contra_celsum_vii_par1_en', 'sc150_origenes_contra_celsum_vii_par1', 'misaligned', 0.04),
    # [278] fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek
    ('sc150_origenes_contra_celsum_vii_par10_en', 'sc150_origenes_contra_celsum_vii_par10', 'misaligned', 0.04),
    # [279] fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek
    ('sc150_origenes_contra_celsum_vii_par11_en', 'sc150_origenes_contra_celsum_vii_par11', 'misaligned', 0.01),
    # [280] fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek
    ('sc150_origenes_contra_celsum_vii_par12_en', 'sc150_origenes_contra_celsum_vii_par12', 'misaligned', 0.01),
    # [281] fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek
    ('sc150_origenes_contra_celsum_vii_par13_en', 'sc150_origenes_contra_celsum_vii_par13', 'misaligned', 0.01),
    # [282] fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek
    ('sc150_origenes_contra_celsum_vii_par14_en', 'sc150_origenes_contra_celsum_vii_par14', 'misaligned', 0.02),
    # [283] fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek
    ('sc150_origenes_contra_celsum_vii_par14_a_en', 'sc150_origenes_contra_celsum_vii_par14_a', 'misaligned', 0.01),
    # [284] fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek
    ('sc150_origenes_contra_celsum_vii_par15_en', 'sc150_origenes_contra_celsum_vii_par15', 'misaligned', 0.01),
    # [285] fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek; it invents a free-will argument ('the existence of free will (to eph' hemin) in rational creatures ... To prevent sin by removing freedom would ... be tyranny') absent from the Greek, which discusses the Isaiah 53 prophecy
    ('sc150_origenes_contra_celsum_vii_par16_en', 'sc150_origenes_contra_celsum_vii_par16', 'misaligned', 0.01),
    # [286] fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek
    ('sc150_origenes_contra_celsum_vii_par17_en', 'sc150_origenes_contra_celsum_vii_par17', 'misaligned', 0.05),
    # [287] fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek; it invents an argument on God giving freedom 'without which goodness would be merely mechanical', while the Greek quotes Celsus on the Mosaic law of wealth and slaughter
    ('sc150_origenes_contra_celsum_vii_par18_en', 'sc150_origenes_contra_celsum_vii_par18', 'misaligned', 0.01),
    # [288] fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek
    ('sc150_origenes_contra_celsum_vii_par19_en', 'sc150_origenes_contra_celsum_vii_par19', 'misaligned', 0.01),
    # [289] fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek
    ('sc150_origenes_contra_celsum_vii_par2_en', 'sc150_origenes_contra_celsum_vii_par2', 'misaligned', 0.07),
    # [290] fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek
    ('sc150_origenes_contra_celsum_vii_par20_en', 'sc150_origenes_contra_celsum_vii_par20', 'misaligned', 0.01),
    # [291] fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek
    ('sc150_origenes_contra_celsum_vii_par21_en', 'sc150_origenes_contra_celsum_vii_par21', 'misaligned', 0.01),
    # [292] fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek
    ('sc150_origenes_contra_celsum_vii_par22_en', 'sc150_origenes_contra_celsum_vii_par22', 'misaligned', 0.01),
    # [293] fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek
    ('sc150_origenes_contra_celsum_vii_par23_en', 'sc150_origenes_contra_celsum_vii_par23', 'misaligned', 0.01),
    # [294] fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek
    ('sc150_origenes_contra_celsum_vii_par23_a_en', 'sc150_origenes_contra_celsum_vii_par23_a', 'misaligned', 0.02),
    # [295] fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek
    ('sc150_origenes_contra_celsum_vii_par23_b_en', 'sc150_origenes_contra_celsum_vii_par23_b', 'misaligned', 0.01),
    # [296] fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek
    ('sc150_origenes_contra_celsum_vii_par24_en', 'sc150_origenes_contra_celsum_vii_par24', 'misaligned', 0.01),
    # [297] fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek
    ('sc150_origenes_contra_celsum_vii_par25_en', 'sc150_origenes_contra_celsum_vii_par25', 'misaligned', 0.01),
    # [298] fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek
    ('sc150_origenes_contra_celsum_vii_par26_en', 'sc150_origenes_contra_celsum_vii_par26', 'misaligned', 0.01),
    # [299] fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek
    ('sc150_origenes_contra_celsum_vii_par27_en', 'sc150_origenes_contra_celsum_vii_par27', 'misaligned', 0.01),
    # [300] fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek
    ('sc150_origenes_contra_celsum_vii_par28_en', 'sc150_origenes_contra_celsum_vii_par28', 'misaligned', 0.01),
    # [301] fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek
    ('sc150_origenes_contra_celsum_vii_par29_en', 'sc150_origenes_contra_celsum_vii_par29', 'misaligned', 0.01),
    # [302] fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek
    ('sc150_origenes_contra_celsum_vii_par3_en', 'sc150_origenes_contra_celsum_vii_par3', 'misaligned', 0.02),
    # [303] faithful translation of the opening, followed by a bracketed editorial summary appended inside the translation text
    ('sc167_clemens_epistula_ad_corinthios_chap10_en', 'sc167_clemens_epistula_ad_corinthios_chap10', 'aligned_strip_note', 0.27),
    # [304] faithful translation of the opening, followed by a bracketed editorial summary appended inside the translation text
    ('sc167_clemens_epistula_ad_corinthios_chap12_en', 'sc167_clemens_epistula_ad_corinthios_chap12', 'aligned_strip_note', 0.23),
    # [305] faithful translation of the opening, followed by a bracketed editorial summary appended inside the translation text
    ('sc167_clemens_epistula_ad_corinthios_chap35_en', 'sc167_clemens_epistula_ad_corinthios_chap35', 'aligned_strip_note', 0.24),
    # [306] faithful translation of the opening, followed by a bracketed editorial summary appended inside the translation text
    ('sc167_clemens_epistula_ad_corinthios_chap4_en', 'sc167_clemens_epistula_ad_corinthios_chap4', 'aligned_strip_note', 0.2),
    # [307] English renders the same passage (partial or full coverage)
    ('sc167_clemens_epistula_ad_corinthios_chap6_en', 'sc167_clemens_epistula_ad_corinthios_chap6', 'aligned_partial', 0.25),
    # [308] English renders the same passage (partial or full coverage)
    ('sc167_clemens_epistula_ad_corinthios_chap8_en', 'sc167_clemens_epistula_ad_corinthios_chap8', 'aligned_partial', 0.19),
    # [309] English begins with the end of 12.11 and continues with 13.1–3 (Isaac and Rebecca) — not 12.10–11b
    ('sc172_epistula_barnabae_chap_12_verset_10_11b_en', 'sc172_epistula_barnabae_chap_12_verset_10_11b', 'misaligned', 0.02),
    # [310] English begins with the bronze serpent (12.6–7) and continues with 12.8–9, omitting 12.5a–5b
    ('sc172_epistula_barnabae_chap_12_verset_5a_7c_en', 'sc172_epistula_barnabae_chap_12_verset_5a_7c', 'misaligned', 0.07),
    # [311] English renders this passage and then runs on into the following verses (coverage exceeds the locus)
    ('sc172_epistula_barnabae_chap_12_verset_8_9b_en', 'sc172_epistula_barnabae_chap_12_verset_8_9b', 'aligned_exceeds', 0.17),
    # [312] English renders this passage and then runs on into the following verses (coverage exceeds the locus)
    ('sc172_epistula_barnabae_chap_13_verset_1_en', 'sc172_epistula_barnabae_chap_13_verset_1', 'aligned_exceeds', 0.28),
    # [313] English renders 13.4–5 (Jacob, Ephraim and Manasseh), not 13.2a–3 (Isaac and Rebecca)
    ('sc172_epistula_barnabae_chap_13_verset_2a_3_en', 'sc172_epistula_barnabae_chap_13_verset_2a_3', 'misaligned', 0.07),
    # [314] English renders 13.6–7 (Abraham, father of nations), not 13.4–6 (Jacob's blessing)
    ('sc172_epistula_barnabae_chap_13_verset_4_6_en', 'sc172_epistula_barnabae_chap_13_verset_4_6', 'misaligned', 0.04),
    # [315] English 'Therefore both things have been brought to completion ...' does not render 13.7a (‹if he was mentioned also through Abraham, we have the perfection of our knowledge›)
    ('sc172_epistula_barnabae_chap_13_verset_7a_7b_en', 'sc172_epistula_barnabae_chap_13_verset_7a_7b', 'misaligned', 0.16),
    # [316] English is a mixed paraphrase of 14.1–5 ('Moses received it as a servant ...' is 14.4), not a rendering of 14.1a–3c
    ('sc172_epistula_barnabae_chap_14_verset_1a_3c_en', 'sc172_epistula_barnabae_chap_14_verset_1a_3c', 'misaligned', 0.15),
    # [317] English ('Now I want to write many things ... lest the Black One gain entrance') renders a different passage of the epistle, not 14.4a–9 (how we received the covenant)
    ('sc172_epistula_barnabae_chap_14_verset_4a_9_en', 'sc172_epistula_barnabae_chap_14_verset_4a_9', 'misaligned', 0.01),
    # [318] English renders this passage and then runs on into the following verses (coverage exceeds the locus)
    ('sc172_epistula_barnabae_chap_15_verset_1_2_en', 'sc172_epistula_barnabae_chap_15_verset_1_2', 'aligned_exceeds', 0.29),
    # [319] English mixes a garbled 15.6b–7 with 15.9 ('the eighth day on which Jesus arose') — not a rendering of 15.6a–7b
    ('sc172_epistula_barnabae_chap_15_verset_6a_7b_en', 'sc172_epistula_barnabae_chap_15_verset_6a_7b', 'misaligned', 0.15),
    # [320] English renders 16.6–7 (the temple built in the name of the Lord), not 16.5 (city, temple and people handed over)
    ('sc172_epistula_barnabae_chap_16_verset_5a_5c_en', 'sc172_epistula_barnabae_chap_16_verset_5a_5c', 'misaligned', 0.02),
    # [321] English is a closing farewell ('Children of love and peace ...'), not 17.1–2 (‹as far as was possible to explain to you simply›)
    ('sc172_epistula_barnabae_chap_17_verset_1_2_en', 'sc172_epistula_barnabae_chap_17_verset_1_2', 'misaligned', 0.03),
    # [322] English renders the same passage (partial or full coverage)
    ('sc172_epistula_barnabae_chap_19_verset_1a_6c_en', 'sc172_epistula_barnabae_chap_19_verset_1a_6c', 'aligned_partial', 0.05),
    # [323] English begins at 19.5 ('love your neighbor more than your own soul') — it does not start with 19.7a
    ('sc172_epistula_barnabae_chap_19_verset_7a_12c_en', 'sc172_epistula_barnabae_chap_19_verset_7a_12c', 'misaligned', 0.14),
    # [324] English renders this passage and then runs on into the following verses (coverage exceeds the locus)
    ('sc172_epistula_barnabae_chap_21_verset_2_3_en', 'sc172_epistula_barnabae_chap_21_verset_2_3', 'aligned_exceeds', 0.2),
    # [325] English begins at 21.5 and continues with 21.6–7, omitting 21.4
    ('sc172_epistula_barnabae_chap_21_verset_4_5_en', 'sc172_epistula_barnabae_chap_21_verset_4_5', 'misaligned', 0.1),
    # [326] English ('While the good vessel is still with you ... Farewell') renders a different passage, not 21.6–7 (‹be taught by God›)
    ('sc172_epistula_barnabae_chap_21_verset_6_7_en', 'sc172_epistula_barnabae_chap_21_verset_6_7', 'misaligned', 0.04),
    # [327] English renders this passage and then runs on into the following verses (coverage exceeds the locus)
    ('sc172_epistula_barnabae_chap_2_verset_1_3_en', 'sc172_epistula_barnabae_chap_2_verset_1_3', 'aligned_exceeds', 0.11),
    # [328] English ('Did I command your fathers ...', i.e. the content of the 2.7–9 node) does not render 2.4–6 (‹What is the multitude of your sacrifices ...›)
    ('sc172_epistula_barnabae_chap_2_verset_4_6_en', 'sc172_epistula_barnabae_chap_2_verset_4_6', 'misaligned', 0.03),
    # [329] English (the fast God has chosen, Isaiah 58) renders a different passage, not 2.7–9 (‹Did I command your fathers ...›)
    ('sc172_epistula_barnabae_chap_2_verset_7_9_en', 'sc172_epistula_barnabae_chap_2_verset_7_9', 'misaligned', 0.02),
    # [330] English renders the same passage (partial or full coverage)
    ('sc172_epistula_barnabae_chap_4_verset_9a_en', 'sc172_epistula_barnabae_chap_4_verset_9a', 'aligned_partial', 0.29),
    # [331] English (the water and the cross, baptism) renders a different passage, not 5.11–14 (the Son came in the flesh to complete the sins of the persecutors)
    ('sc172_epistula_barnabae_chap_5_verset_11_14_en', 'sc172_epistula_barnabae_chap_5_verset_11_14', 'misaligned', 0.01),
    # [332] English (the prophets prophesied about him; he abolished death) does not render 5.3–4b (thanks for knowledge; ‹nets are not unjustly spread for birds›)
    ('sc172_epistula_barnabae_chap_5_verset_3_4b_en', 'sc172_epistula_barnabae_chap_5_verset_3_4b', 'misaligned', 0.02),
    # [333] English renders 5.9–11 (the choice of sinful apostles), not 5.5–7
    ('sc172_epistula_barnabae_chap_5_verset_5_7_en', 'sc172_epistula_barnabae_chap_5_verset_5_7', 'misaligned', 0.02),
    # [334] English renders 5.12–14 (the shepherd struck, 'Nail my flesh'), not 5.8–10
    ('sc172_epistula_barnabae_chap_5_verset_8_10_en', 'sc172_epistula_barnabae_chap_5_verset_8_10', 'misaligned', 0.02),
    # [335] English renders 6.11–12 (renewal, 'Let us make humanity'), not 6.10a–b (‹Blessed be our Lord who put wisdom in us›)
    ('sc172_epistula_barnabae_chap_6_verset_10a_10b_en', 'sc172_epistula_barnabae_chap_6_verset_10a_10b', 'misaligned', 0.02),
    # [336] English renders 13.1–3 (Isaac and Rebecca), not 6.11–12c
    ('sc172_epistula_barnabae_chap_6_verset_11_12c_en', 'sc172_epistula_barnabae_chap_6_verset_11_12c', 'misaligned', 0.02),
    # [337] English renders 13.4–5 (Jacob crossing his hands), not 6.13–16
    ('sc172_epistula_barnabae_chap_6_verset_13a_16c_en', 'sc172_epistula_barnabae_chap_6_verset_13a_16c', 'misaligned', 0.02),
    # [338] English renders 14.1–3 (the covenant and the tablets), not 6.17–19 (milk and honey)
    ('sc172_epistula_barnabae_chap_6_verset_17a_19_en', 'sc172_epistula_barnabae_chap_6_verset_17a_19', 'misaligned', 0.02),
    # [339] English renders 7.2, not 7.1
    ('sc172_epistula_barnabae_chap_7_verset_1_en', 'sc172_epistula_barnabae_chap_7_verset_1', 'misaligned', 0.03),
    # [340] English (the heifer, the ashes and the scarlet wool on a stick) does not render 7.11 (the wool placed among thorns)
    ('sc172_epistula_barnabae_chap_7_verset_11a_11b_en', 'sc172_epistula_barnabae_chap_7_verset_11a_11b', 'misaligned', 0.03),
    # [341] English renders 7.3, not 7.2
    ('sc172_epistula_barnabae_chap_7_verset_2_en', 'sc172_epistula_barnabae_chap_7_verset_2', 'misaligned', 0.02),
    # [342] English begins mid-verse at 7.3c and omits 7.3a–3b (vinegar and gall, the fast commandment)
    ('sc172_epistula_barnabae_chap_7_verset_3a_5b_en', 'sc172_epistula_barnabae_chap_7_verset_3a_5b', 'misaligned', 0.1),
    # [343] English begins at 7.7 ('Pay attention to how the type of Jesus is revealed') and omits 7.6 (the two goats)
    ('sc172_epistula_barnabae_chap_7_verset_6a_8c_en', 'sc172_epistula_barnabae_chap_7_verset_6a_8c', 'misaligned', 0.21),
    # [344] English ('why is it that they place the wool in the middle of the thorns?' — the content of the 7.11 node) does not render 7.9a–10b
    ('sc172_epistula_barnabae_chap_7_verset_9a_10b_en', 'sc172_epistula_barnabae_chap_7_verset_9a_10b', 'misaligned', 0.03),
    # [345] English renders this passage and then runs on into the following verses (coverage exceeds the locus)
    ('sc172_epistula_barnabae_chap_8_verset_2a_4_en', 'sc172_epistula_barnabae_chap_8_verset_2a_4', 'aligned_exceeds', 0.26),
    # [346] English begins with the wool-and-hyssop question of 8.6a and omits 8.5 (the wool on the wood, the kingdom of Jesus on the wood)
    ('sc172_epistula_barnabae_chap_8_verset_5_6b_en', 'sc172_epistula_barnabae_chap_8_verset_5_6b', 'misaligned', 0.1),
    # [347] English ('By the hearing of the ear they obeyed me') renders a different passage, not 8.7 (‹clear to us, obscure to them›)
    ('sc172_epistula_barnabae_chap_8_verset_7_en', 'sc172_epistula_barnabae_chap_8_verset_7', 'misaligned', 0.04),
    # [348] English renders this passage and then runs on into the following verses (coverage exceeds the locus)
    ('sc172_epistula_barnabae_chap_9_verset_4a_5c_en', 'sc172_epistula_barnabae_chap_9_verset_4a_5c', 'aligned_exceeds', 0.25),
    # [349] English (Abraham circumcising with the doctrine of three letters — the content of the 9.7 node) does not render 9.6 (‹every Syrian and Arab ... are circumcised›)
    ('sc172_epistula_barnabae_chap_9_verset_6_en', 'sc172_epistula_barnabae_chap_9_verset_6', 'misaligned', 0.01),
    # [350] English begins with 9.8 (the 318 men) and omits 9.7 (‹Learn then, children of love ...›)
    ('sc172_epistula_barnabae_chap_9_verset_7_8c_en', 'sc172_epistula_barnabae_chap_9_verset_7_8c', 'misaligned', 0.13),
    # [351] English (Moses on unclean animals) renders a different passage, not 9.9 (‹He knows who placed in us the implanted gift›)
    ('sc172_epistula_barnabae_chap_9_verset_9_en', 'sc172_epistula_barnabae_chap_9_verset_9', 'misaligned', 0.01),
    # [352] English ('Theophilus to Autolycus, greeting. Since an agreeable discourse ...') does not render I.1 (‹A fluent tongue and elegant diction give pleasure ...›)
    ('sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_1_en', 'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_1', 'misaligned', 0.02),
    # [353] English renders a different chapter of Book I; the Greek of this node treats the gods of the Egyptians, Phidias' statues
    ('sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_10_en', 'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_10', 'misaligned', 0.01),
    # [354] English renders a different chapter of Book I; the Greek of this node treats honouring the king without worshipping him
    ('sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_11_en', 'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_11', 'misaligned', 0.01),
    # [355] English renders a different chapter of Book I; the Greek of this node treats the mockery of the name ‹Christian› (christon, anointed)
    ('sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_12_en', 'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_12', 'misaligned', 0.01),
    # [356] English renders a different chapter of Book I; the Greek of this node treats the denial of the resurrection, Heracles and Asclepius
    ('sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_13_en', 'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_13', 'misaligned', 0.01),
    # [357] English renders a different chapter of Book I; the Greek of this node treats ‹Do not disbelieve, but believe› — the prophets
    ('sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_14_en', 'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_14', 'misaligned', 0.01),
    # [358] English renders the same passage (partial or full coverage)
    ('sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_2_en', 'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_2', 'aligned_partial', 0.22),
    # [359] English renders a different chapter of Book I; the Greek of this node treats ‹Tell me the form of God› — ineffable
    ('sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_3_en', 'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_3', 'misaligned', 0.01),
    # [360] English renders a different chapter of Book I; the Greek of this node treats God without beginning, the etymology of theos
    ('sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_4_en', 'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_4', 'misaligned', 0.02),
    # [361] English renders a different chapter of Book I; the Greek of this node treats the soul invisible, the ship and its helmsman
    ('sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_5_en', 'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_5', 'misaligned', 0.05),
    # [362] English renders a different chapter of Book I; the Greek of this node treats ‹Consider, O man, his works›
    ('sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_6_en', 'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_6', 'misaligned', 0.03),
    # [363] English renders a different chapter of Book I; the Greek of this node treats ‹This is my God, the Lord of all›
    ('sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_7_en', 'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_7', 'misaligned', 0.03),
    # [364] English renders a different chapter of Book I; the Greek of this node treats ‹You do not believe the dead are raised›
    ('sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_8_en', 'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_8', 'misaligned', 0.01),
    # [365] English renders a different chapter of Book I; the Greek of this node treats the gods are dead men — Kronos, Zeus
    ('sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_9_en', 'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_9', 'misaligned', 0.01),
    # [366] English renders the same passage (partial or full coverage)
    ('sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_18_en', 'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_18', 'aligned_partial', 0.3),
    # [367] English renders the same passage (partial or full coverage)
    ('sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_37_en', 'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_37', 'aligned_partial', 0.27),
    # [368] English renders the same passage (partial or full coverage)
    ('sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_7_en', 'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_7', 'aligned_partial', 0.3),
    # [369] English renders the same passage (partial or full coverage)
    ('sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_22_en', 'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_22', 'aligned_partial', 0.2),
    # [370] English renders the same passage (partial or full coverage)
    ('sc379_athenagoras_legatio_chap29_en', 'sc379_athenagoras_legatio_chap29', 'aligned_partial', 0.24),
    # [371] English renders the same passage (partial or full coverage)
    ('sc464_pamphilus_apologia_pro_origene_par72_en', 'sc464_pamphilus_apologia_pro_origene_par72', 'aligned_partial', 0.28),
    # [372] English renders the same passage (partial or full coverage)
    ('sc470_aristides_apologia_chap11_en', 'sc470_aristides_apologia_chap11', 'aligned_partial', 0.28),
    # [373] English renders the same passage (partial or full coverage)
    ('sc470_aristides_apologia_chap16_en', 'sc470_aristides_apologia_chap16', 'aligned_partial', 0.3),
    # [374] English is a synopsis in the editor's voice of the same Similitude X ('This chapter constitutes an appendix ...'), not a translation of the Latin
    ('sc53bis_hermas_pastor_chap111_en', 'sc53bis_hermas_pastor_chap111', 'aligned_paraphrase', 0.1),
    # [375] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap12_en', 'sc53bis_hermas_pastor_chap12', 'misaligned', 0.01),
    # [376] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap13_en', 'sc53bis_hermas_pastor_chap13', 'misaligned', 0.04),
    # [377] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap14_en', 'sc53bis_hermas_pastor_chap14', 'misaligned', 0.14),
    # [378] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap15_en', 'sc53bis_hermas_pastor_chap15', 'misaligned', 0.04),
    # [379] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap16_en', 'sc53bis_hermas_pastor_chap16', 'misaligned', 0.02),
    # [380] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap17_en', 'sc53bis_hermas_pastor_chap17', 'misaligned', 0.02),
    # [381] English is a synopsis in the editor's voice of the same chapter (Hermas asks about the three forms of the woman), not a translation
    ('sc53bis_hermas_pastor_chap18_en', 'sc53bis_hermas_pastor_chap18', 'aligned_paraphrase', 0.12),
    # [382] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap19_en', 'sc53bis_hermas_pastor_chap19', 'misaligned', 0.03),
    # [383] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap2_en', 'sc53bis_hermas_pastor_chap2', 'misaligned', 0.07),
    # [384] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap20_en', 'sc53bis_hermas_pastor_chap20', 'misaligned', 0.01),
    # [385] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap21_en', 'sc53bis_hermas_pastor_chap21', 'misaligned', 0.02),
    # [386] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap22_en', 'sc53bis_hermas_pastor_chap22', 'misaligned', 0.01),
    # [387] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap23_en', 'sc53bis_hermas_pastor_chap23', 'misaligned', 0.01),
    # [388] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap24_en', 'sc53bis_hermas_pastor_chap24', 'misaligned', 0.01),
    # [389] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap25_en', 'sc53bis_hermas_pastor_chap25', 'misaligned', 0.03),
    # [390] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap26_en', 'sc53bis_hermas_pastor_chap26', 'misaligned', 0.01),
    # [391] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap27_en', 'sc53bis_hermas_pastor_chap27', 'misaligned', 0.01),
    # [392] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap28_en', 'sc53bis_hermas_pastor_chap28', 'misaligned', 0.01),
    # [393] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap29_en', 'sc53bis_hermas_pastor_chap29', 'misaligned', 0.01),
    # [394] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap3_en', 'sc53bis_hermas_pastor_chap3', 'misaligned', 0.09),
    # [395] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap30_en', 'sc53bis_hermas_pastor_chap30', 'misaligned', 0.01),
    # [396] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap31_en', 'sc53bis_hermas_pastor_chap31', 'misaligned', 0.01),
    # [397] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap32_en', 'sc53bis_hermas_pastor_chap32', 'misaligned', 0.01),
    # [398] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap33_en', 'sc53bis_hermas_pastor_chap33', 'misaligned', 0.03),
    # [399] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap34_en', 'sc53bis_hermas_pastor_chap34', 'misaligned', 0.01),
    # [400] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap35_en', 'sc53bis_hermas_pastor_chap35', 'misaligned', 0.04),
    # [401] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap36_en', 'sc53bis_hermas_pastor_chap36', 'misaligned', 0.13),
    # [402] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap37_en', 'sc53bis_hermas_pastor_chap37', 'misaligned', 0.03),
    # [403] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap38_en', 'sc53bis_hermas_pastor_chap38', 'misaligned', 0.01),
    # [404] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap39_en', 'sc53bis_hermas_pastor_chap39', 'misaligned', 0.01),
    # [405] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap4_en', 'sc53bis_hermas_pastor_chap4', 'misaligned', 0.04),
    # [406] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap40_en', 'sc53bis_hermas_pastor_chap40', 'misaligned', 0.01),
    # [407] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap41_en', 'sc53bis_hermas_pastor_chap41', 'misaligned', 0.01),
    # [408] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap42_en', 'sc53bis_hermas_pastor_chap42', 'misaligned', 0.01),
    # [409] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap43_en', 'sc53bis_hermas_pastor_chap43', 'misaligned', 0.01),
    # [410] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap44_en', 'sc53bis_hermas_pastor_chap44', 'misaligned', 0.01),
    # [411] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap45_en', 'sc53bis_hermas_pastor_chap45', 'misaligned', 0.03),
    # [412] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap46_en', 'sc53bis_hermas_pastor_chap46', 'misaligned', 0.01),
    # [413] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap47_en', 'sc53bis_hermas_pastor_chap47', 'misaligned', 0.03),
    # [414] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap48_en', 'sc53bis_hermas_pastor_chap48', 'misaligned', 0.02),
    # [415] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap49_en', 'sc53bis_hermas_pastor_chap49', 'misaligned', 0.02),
    # [416] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap5_en', 'sc53bis_hermas_pastor_chap5', 'misaligned', 0.02),
    # [417] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap50_en', 'sc53bis_hermas_pastor_chap50', 'misaligned', 0.01),
    # [418] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap51_en', 'sc53bis_hermas_pastor_chap51', 'misaligned', 0.01),
    # [419] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap52_en', 'sc53bis_hermas_pastor_chap52', 'misaligned', 0.02),
    # [420] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap53_en', 'sc53bis_hermas_pastor_chap53', 'misaligned', 0.02),
    # [421] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap54_en', 'sc53bis_hermas_pastor_chap54', 'misaligned', 0.02),
    # [422] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap55_en', 'sc53bis_hermas_pastor_chap55', 'misaligned', 0.01),
    # [423] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap56_en', 'sc53bis_hermas_pastor_chap56', 'misaligned', 0.01),
    # [424] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap57_en', 'sc53bis_hermas_pastor_chap57', 'misaligned', 0.01),
    # [425] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap58_en', 'sc53bis_hermas_pastor_chap58', 'misaligned', 0.01),
    # [426] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap59_en', 'sc53bis_hermas_pastor_chap59', 'misaligned', 0.01),
    # [427] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap6_en', 'sc53bis_hermas_pastor_chap6', 'misaligned', 0.03),
    # [428] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap60_en', 'sc53bis_hermas_pastor_chap60', 'misaligned', 0.01),
    # [429] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap61_en', 'sc53bis_hermas_pastor_chap61', 'misaligned', 0.01),
    # [430] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap62_en', 'sc53bis_hermas_pastor_chap62', 'misaligned', 0.01),
    # [431] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap63_en', 'sc53bis_hermas_pastor_chap63', 'misaligned', 0.02),
    # [432] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap64_en', 'sc53bis_hermas_pastor_chap64', 'misaligned', 0.01),
    # [433] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap65_en', 'sc53bis_hermas_pastor_chap65', 'misaligned', 0.01),
    # [434] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap66_en', 'sc53bis_hermas_pastor_chap66', 'misaligned', 0.01),
    # [435] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap67_en', 'sc53bis_hermas_pastor_chap67', 'misaligned', 0.01),
    # [436] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap68_en', 'sc53bis_hermas_pastor_chap68', 'misaligned', 0.04),
    # [437] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap69_en', 'sc53bis_hermas_pastor_chap69', 'misaligned', 0.02),
    # [438] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap7_en', 'sc53bis_hermas_pastor_chap7', 'misaligned', 0.02),
    # [439] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap70_en', 'sc53bis_hermas_pastor_chap70', 'misaligned', 0.11),
    # [440] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap71_en', 'sc53bis_hermas_pastor_chap71', 'misaligned', 0.11),
    # [441] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap72_en', 'sc53bis_hermas_pastor_chap72', 'misaligned', 0.03),
    # [442] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap73_en', 'sc53bis_hermas_pastor_chap73', 'misaligned', 0.01),
    # [443] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap74_en', 'sc53bis_hermas_pastor_chap74', 'misaligned', 0.03),
    # [444] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap76_en', 'sc53bis_hermas_pastor_chap76', 'misaligned', 0.26),
    # [445] English is a synopsis in the editor's voice of the same chapter (opening of Similitude IX), not a translation
    ('sc53bis_hermas_pastor_chap78_en', 'sc53bis_hermas_pastor_chap78', 'aligned_paraphrase', 0.18),
    # [446] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap79_en', 'sc53bis_hermas_pastor_chap79', 'misaligned', 0.02),
    # [447] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap8_en', 'sc53bis_hermas_pastor_chap8', 'misaligned', 0.01),
    # [448] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap80_en', 'sc53bis_hermas_pastor_chap80', 'misaligned', 0.09),
    # [449] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap81_en', 'sc53bis_hermas_pastor_chap81', 'misaligned', 0.04),
    # [450] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap82_en', 'sc53bis_hermas_pastor_chap82', 'misaligned', 0.03),
    # [451] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap83_en', 'sc53bis_hermas_pastor_chap83', 'misaligned', 0.04),
    # [452] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap84_en', 'sc53bis_hermas_pastor_chap84', 'misaligned', 0.09),
    # [453] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap85_en', 'sc53bis_hermas_pastor_chap85', 'misaligned', 0.14),
    # [454] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap86_en', 'sc53bis_hermas_pastor_chap86', 'misaligned', 0.05),
    # [455] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap87_en', 'sc53bis_hermas_pastor_chap87', 'misaligned', 0.05),
    # [456] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap88_en', 'sc53bis_hermas_pastor_chap88', 'misaligned', 0.01),
    # [457] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap89_en', 'sc53bis_hermas_pastor_chap89', 'misaligned', 0.04),
    # [458] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap9_en', 'sc53bis_hermas_pastor_chap9', 'misaligned', 0.02),
    # [459] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap90_en', 'sc53bis_hermas_pastor_chap90', 'misaligned', 0.02),
    # [460] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap91_en', 'sc53bis_hermas_pastor_chap91', 'misaligned', 0.07),
    # [461] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap92_en', 'sc53bis_hermas_pastor_chap92', 'misaligned', 0.02),
    # [462] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap93_en', 'sc53bis_hermas_pastor_chap93', 'misaligned', 0.01),
    # [463] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap94_en', 'sc53bis_hermas_pastor_chap94', 'misaligned', 0.02),
    # [464] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap95_en', 'sc53bis_hermas_pastor_chap95', 'misaligned', 0.02),
    # [465] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap96_en', 'sc53bis_hermas_pastor_chap96', 'misaligned', 0.02),
    # [466] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap97_en', 'sc53bis_hermas_pastor_chap97', 'misaligned', 0.01),
    # [467] not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node
    ('sc53bis_hermas_pastor_chap98_en', 'sc53bis_hermas_pastor_chap98', 'misaligned', 0.03),
    # [468] English is a close paraphrastic synopsis of the same chapter in the editor's voice ('Chapter 10 of Chrysostom's On Providence ...'), not a translation
    ('sc79_chrysostomus_de_providentia_chap10_en', 'sc79_chrysostomus_de_providentia_chap10', 'aligned_paraphrase', 0.24),
    # [469] English is a close paraphrastic synopsis of the same chapter in the editor's voice ('Chapter 14 of Chrysostom's On Providence ...'), not a translation
    ('sc79_chrysostomus_de_providentia_chap14_en', 'sc79_chrysostomus_de_providentia_chap14', 'aligned_paraphrase', 0.16),
]

NOTES = {
    'passage_boethius_cons_35_en': 'English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)',
    'passage_boethius_cons_47_en': 'English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)',
    'passage_boethius_cons_49_en': 'English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)',
    'passage_boethius_cons_51_en': 'English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)',
    'passage_boethius_cons_54_en': 'English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)',
    'passage_boethius_cons_55_en': 'English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)',
    'passage_boethius_cons_57_en': 'English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)',
    'passage_boethius_cons_6_en': 'English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)',
    'passage_boethius_cons_61_en': 'English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)',
    'passage_boethius_cons_63_en': 'English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)',
    'passage_boethius_cons_64_en': 'English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)',
    'passage_boethius_cons_66_en': 'English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)',
    'passage_boethius_cons_67_en': 'English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)',
    'passage_boethius_cons_69_en': 'English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)',
    'passage_boethius_cons_7_en': 'English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)',
    'passage_boethius_cons_74_en': 'English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)',
    'passage_boethius_cons_75_en': 'English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)',
    'passage_boethius_cons_78_en': 'English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)',
    'passage_boethius_cons_80_en': 'English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)',
    'passage_boethius_cons_85_en': 'English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)',
    'passage_boethius_cons_9_en': 'English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)',
    'passage_boethius_cons_93_en': 'English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)',
    'passage_boethius_cons_94_en': 'English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)',
    'passage_epict_114_en': 'vocabulary_gloss original (Greek word list + English commentary); not a translation pair',
    'passage_sen_prov_4_1_en': 'Latin 4.1 opens on prosperity coming even to the common crowd; the English gives "I find nothing worthy of you on earth; therefore I challenge you with what is hard" instead — not a rendering of 4.1',
    'passage_sen_prov_4_5_en': 'English renders the opening of the same Latin section (partial, condensed rendering; the Latin excerpt is given verbatim in the evidence field)',
    'passage_sen_prov_5_1_en': "Latin 5.1 opens: it is for the good of all that the best men serve as soldiers; the English gives 'Why does God allow anything bad to happen to good men?' and God keeping crimes far from the good — not a rendering of 5.1",
    'sc123_melito_peri_pascha_chap22_en': '(a strange calamity: a long night and palpable darkness); English speaks of those struck and fallen and "no single form of death" — different sentence',
    'sc123_melito_peri_pascha_chap23_en': '(in the palpable darkness impalpable death lay hidden); English: a newborn brought to the striking angel — different content',
    'sc123_melito_peri_pascha_chap24_en': 'Greek: a firstborn embracing a dark body cries(whom does my right hand hold?); English: Israel guarded by the slaughter of the sheep — different content',
    'sc123_melito_peri_pascha_chap25_en': '(before the firstborn fell silent, the long silence seized him); English "O strange and inexpressible mystery!" renders chap31, not chap25',
    'sc123_melito_peri_pascha_chap26_en': 'Greek: another firstborn denies being firstborn,(I am not the firstborn); English "Tell me, O angel, what turned you away?" renders chap32',
    'sc123_melito_peri_pascha_chap27_en': 'Greek: lowing of cattle in the fields; English ‹you turned away when you saw the mystery of the Lord› renders chap33',
    'sc123_melito_peri_pascha_chap28_en': '(wailing ... all Egypt stank); English on the sheep valued on account of the Lord — different content',
    'sc123_melito_peri_pascha_chap29_en': '(a fearful sight: Egyptian mothers with loosened hair); English "instead of the lamb there was a Son" renders chap5',
    'sc123_melito_peri_pascha_chap30_en': '(such a calamity engulfed Egypt); English on the Passover consummated in Christ — different content',
    'sc123_melito_peri_pascha_chap31_en': '(O new and indescribable mystery); English ‹the Law has become Word ... the lamb a Son› — different content',
    'sc123_melito_peri_pascha_chap32_en': '(tell me, angel, what turned you away); English "as a son he was born ... as a lamb he was led" — different content',
    'sc123_melito_peri_pascha_chap33_en': '(clearly you were turned away seeing the Lord\'s mystery); English "He is all things: inasmuch as he judges, he is Law" — different content',
    'sc123_melito_peri_pascha_chap34_en': '(what is this new mystery, Egypt struck); English "This is Jesus the Christ, to whom be glory forever" — different content',
    'sc123_melito_peri_pascha_chap35_en': '(nothing said or done without parable); English ‹This is the mystery of the Passover and the reading of the old Law› — different content',
    'sc123_melito_peri_pascha_chap36_en': 'Greek: a model made(of wax, clay or wood); English "What the mystery is ... you shall understand from what follows" — different content',
    'sc123_melito_peri_pascha_chap37_en': 'Greek: the model is destroyed(dissolved as useless) when the reality arises; English "the people was valuable before the church was established" — different content',
    'sc123_melito_peri_pascha_chap38_en': '(each has its own season, the model its own time); English "when the church arose and the Gospel came forth" — renders chap42',
    'sc123_melito_peri_pascha_chap39_en': '(as in perishable examples, so in imperishable); English "the type lost its value when the Lord was made manifest" — different content',
    'sc123_melito_peri_pascha_chap40_en': '(the people became a model, the Law a parable); English on the model of the city abandoned — different content',
    'sc123_melito_peri_pascha_chap42_en': '(when the church arose, the type was emptied); English ‹the type was once valuable before the reality› — different content',
    'sc123_melito_peri_pascha_chap44_en': '(once precious the slaughter of the sheep, now worthless); English "The model was dissolved when the city was revealed" — different content',
    'sc123_melito_peri_pascha_chap45_en': '(precious the Jerusalem below, the narrow inheritance); English renders the opening of chap44 ("once the slaughter of the sheep was precious")',
    'sc123_melito_peri_pascha_chap46_en': '(what is the Pascha? from suffering); English ‹The blood of the sheep was precious ... the silent lamb› renders chap44',
    'sc123_melito_peri_pascha_chap47_en': '(to clothe the sufferer and snatch him to heaven); English ‹The temple below was precious ... the Jerusalem below› renders chap44/45',
    'sc123_melito_peri_pascha_chap48_en': '(man, by nature receptive of good and evil); English "The narrow inheritance was precious" renders chap45',
    'sc123_melito_peri_pascha_chap49_en': '(he left his children an inheritance ... not freedom but slavery); English "there the almighty God has made his dwelling" renders the end of chap45',
    'sc123_melito_peri_pascha_chap5_en': '(instead of the lamb God, instead of the sheep a man); English ‹like a sheep he was led to the slaughter, yet he was not a sheep› — different content',
    'sc123_melito_peri_pascha_chap50_en': '(they were snatched by tyrannical sin); English ‹What is the Passover? Its name is taken from the event› renders chap46',
    'sc123_melito_peri_pascha_chap51_en': '(father raised a sword against son); English ‹Learn who is the one who suffers› renders chap46–47',
    'sc123_melito_peri_pascha_chap52_en': '(a mother touched the flesh she had borne); English "God, having made the heavens and the earth ... fashioned humanity" — different content',
    'sc123_melito_peri_pascha_chap53_en': "(father to child's bed, son to mother's); English on the commandment about the tree of knowledge — different content",
    'sc123_melito_peri_pascha_chap54_en': '(at these things sin rejoiced); English ‹the human being, by nature capable of receiving both good and evil› renders chap48',
    'sc123_melito_peri_pascha_chap55_en': '(all flesh fell under sin); English ‹He was cast out into this world as into a prison› renders the end of chap48 + chap49',
    'sc123_melito_peri_pascha_chap56_en': "Greek: man divided by death, the Father's image left desolate, hence the Pascha mystery fulfilled in the Lord's body; English: sin rejoicing, adultery and fornication — different content",
    'sc123_melito_peri_pascha_chap57_en': 'Greek opens: the Lord prearranged his sufferings in patriarchs and prophets; English prefixes a sentence from the preceding section and stops after the first clause — mixed, not this passage',
    'sc123_melito_peri_pascha_chap58_en': "Greek: the Lord's mystery, long prefigured, now seen, old by type and new by grace; English: 'He who suspended the earth is himself suspended' renders chap96",
    'sc123_melito_peri_pascha_chap59_en': "Greek: look to Abel murdered, Isaac bound, Joseph sold, Moses exposed, David persecuted; English: 'O unprecedented murder!' renders chap97",
    'sc123_melito_peri_pascha_chap6_en': "Greek: the slaughter of the sheep, the Pascha rite and the Law have come to fulfilment in Christ; English: 'instead of the lamb there was a Son' — different sentence (same text also on chap29_en)",
    'sc123_melito_peri_pascha_chap60_en': 'Greek: look at the sheep slaughtered in Egypt that struck Egypt and saved Israel; English: the luminaries turned away (chap97)',
    'sc123_melito_peri_pascha_chap61_en': "Greek: the mystery proclaimed by the prophets, Moses' ‹you will see your life hanging›; English: the earth trembled while the people did not (chap98)",
    'sc123_melito_peri_pascha_chap62_en': "Greek: David's ‹Why did the nations rage› (Ps 2); English: ‹Listen, all families of the nations ... an unprecedented murder› (chap94)",
    'sc123_melito_peri_pascha_chap63_en': "Greek: Jeremiah's ‹I was like an innocent lamb led to be sacrificed›; English: murder in the middle of the street (chap94)",
    'sc123_melito_peri_pascha_chap64_en': "Greek: Isaiah's ‹like a sheep he was led to slaughter›; English: lifted up upon the tree with a title (chap95)",
    'sc123_melito_peri_pascha_chap65_en': "Greek: many other things proclaimed by the prophets about the Pascha mystery, which is Christ; English: 'The one who hung the earth in space is himself hung' (chap96)",
    'sc123_melito_peri_pascha_chap66_en': "Greek: he came from heaven, clothed himself with the sufferer through a virgin's womb; English: 'O unprecedented murder!' (chap97)",
    'sc123_melito_peri_pascha_chap67_en': "Greek: led as a lamb, he ransomed us from the world's slavery as from Egypt; English: darkening not the Lord's body but men's eyes, earth trembling (chap97–98)",
    'sc123_melito_peri_pascha_chap81_en': "Greek: ‹O lawless Israel, what is this new crime?›; English: 'He who suspended the earth is himself suspended' (chap96)",
    'sc123_melito_peri_pascha_chap82_en': "Greek: you did not recognise God, the firstborn begotten before the morning star; English: 'O unprecedented murder!' (chap97)",
    'sc123_melito_peri_pascha_chap83_en': "Greek: who fitted the stars ... who chose you and guided you from Adam to Noah to Abraham; English: 'Raise your eyes, O Israel' — different content",
    'sc123_melito_peri_pascha_chap84_en': 'Greek: he guided you into Egypt, lit you by the pillar, split the Red Sea; English: the luminaries turned away (chap97)',
    'sc123_melito_peri_pascha_chap85_en': 'Greek: he gave you manna from heaven, water from the rock, the law at Horeb; English: the earth trembled while the people did not (chap98)',
    'sc123_melito_peri_pascha_chap86_en': "Greek: he came to you, healed your sick, raised your dead ... this is he whom you killed; English: 'you did not tremble at the presence of the Lord' (chap99)",
    'sc123_melito_peri_pascha_chap87_en': "Greek: ‹Ungrateful Israel, come and be judged ... at what price did you value ...›; English: 'Listen, all families of the nations' (chap94)",
    'sc123_melito_peri_pascha_chap88_en': 'Greek: at what price did you value the ten plagues, the pillar, the manna; English: ‹who is the murderer? ... in the middle of the street› (chap94)',
    'sc123_melito_peri_pascha_chap89_en': 'Greek: value for me the sick he healed, the withered hand he restored; English: lifted up upon the tree with a title (chap95)',
    'sc123_melito_peri_pascha_chap90_en': "Greek: value for me the blind from birth he enlightened, the dead he raised; English: 'The one who hung the earth in space is himself hung' (chap96)",
    'sc123_melito_peri_pascha_chap91_en': "Greek is a single clause (for whom you should have died); English: 'O unheard-of murder!' (chap97)",
    'sc123_melito_peri_pascha_chap92_en': 'Greek: you voted against your Lord, whom the nations worshipped, for whom Pilate washed his hands; English: ‹Who is the one who has contended with me? ... I, the Christ› — different content',
    'sc123_melito_peri_pascha_chap93_en': 'Greek: bitter for you the feast of unleavened bread, bitter the nails, the false witnesses, Judas, Herod; English: ‹I bound the strong one ... I am the Christ› — different content',
    'sc123_melito_peri_pascha_chap94_en': 'Greek: ‹Listen, all families of the nations ... a new murder in the midst of Jerusalem›; English: ‹Come, all families of humankind ... receive forgiveness of sins› — different content',
    'sc123_melito_peri_pascha_chap95_en': "Greek: he is lifted up upon the tree with a title; English: 'I will lead you up to the heights of the heavens' — different content",
    'sc123_melito_peri_pascha_chap96_en': "Greek: ‹He who hung the earth is hung ... God is murdered›; English: 'This is he who made the heavens and the earth' — different content",
    'sc123_melito_peri_pascha_chap97_en': "Greek: ‹O new murder ... the luminaries turned away›; English: 'This is he who was raised from the dead' — different content",
    'sc123_melito_peri_pascha_chap98_en': "Greek: the earth trembled while the people did not; English: 'He is the Alpha and the Omega' — different content",
    'sc123_melito_peri_pascha_chap99_en': 'Greek: ‹Therefore, O Israel, you did not tremble before the Lord›; English: doxology and scribal colophon of the whole homily — different content',
    'sc132_origenes_contra_celsum_i_par11_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_i_par12_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_i_par13_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_i_par14_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_i_par15_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_i_par16_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_i_par19_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_i_par20_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_i_par21_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_i_par22_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_i_par23_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_i_par24_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_i_par25_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_i_par26_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_i_par26_a_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_i_par27_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_i_par3_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_i_par30_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_i_par31_en': "Greek opens: one might wonder how the disciples, who (as detractors say) had not seen him risen, came not to fear suffering like their master; English opens 'Now that this teaching has spread throughout the whole world ... it was God's will' — not this section's argument",
    'sc132_origenes_contra_celsum_i_par48_b_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_i_par57_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_i_par6_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_ii_par44_a_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_ii_par45_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_ii_par62_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_ii_par63_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_ii_par64_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_ii_par65_a_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_ii_par68_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_ii_par69_a_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_ii_par70_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_ii_par74_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_ii_par75_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_ii_par76_a_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_ii_par78_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_ii_par79_a_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_ii_par8_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_ii_par8_a_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_ii_par9_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc132_origenes_contra_celsum_praef_par4_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc136_origenes_contra_celsum_iii_par15_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc136_origenes_contra_celsum_iii_par2_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc136_origenes_contra_celsum_iii_par34_a_en': "Greek: Celsus likens worship of one captured and executed to the Getae's Zamolxis, the Cilicians' Mopsus, etc.; English: Jesus gathering 'ten or twenty ... tax-collectors and sailors' — a different section",
    'sc136_origenes_contra_celsum_iii_par62_en': 'Greek: Celsus misrepresents the calls to repentance addressed to those who lived badly, saying we claim God was sent to sinners; English opens with Celsus likening conversion to Greek doctrines vs. the mysteries of Mithras and Sabazius — not this section',
    'sc136_origenes_contra_celsum_iii_par63_en': "Greek: Celsus does not understand ‹whoever exalts himself shall be humbled› (with Plato on the humble good man); English: 'let whoever is ignorant come to me ... I shall make wise' — different section",
    'sc136_origenes_contra_celsum_iii_par64_en': "Greek: ‹What then is this preference for sinners?› — Origen: a sinner as such is not preferred; English: no philosopher says 'Let a robber come to me' — different argument",
    'sc136_origenes_contra_celsum_iii_par65_en': 'Greek: Celsus thinks we court sinners because we cannot win the upright; English: the Jew accuses Jesus of fabricating his virgin birth — different content',
    'sc136_origenes_contra_celsum_iii_par66_en': 'Greek: Celsus denies complete change to those sinful by nature and habit; English: the Jew asks how believers can despise the religion they came from — different content',
    'sc136_origenes_contra_celsum_iii_par67_en': "Greek: no one could wholly change those naturally and habitually sinful, refuted by philosophers' lives; English: 'What made you abandon the law of your fathers?' — different content",
    'sc136_origenes_contra_celsum_iii_par68_en': "Greek: order and style of philosophical discourse vs. Celsus' ‹unlearned› words like incantations; English: the Jew addresses converts from Judaism — different content",
    'sc136_origenes_contra_celsum_iii_par69_en': 'Greek: Celsus says changing nature completely is very hard; Origen: one nature of every rational soul; English: the Jew addresses Gentile believers — different content',
    'sc136_origenes_contra_celsum_iii_par69_a_en': 'Greek: Celsus says the sinless are better companions; English: Egyptians, Scythians and Persians should keep their customs — different content',
    'sc136_origenes_contra_celsum_iii_par7_en': "Greek: the whole people leaving Egypt took up Hebrew as a God-given language; English: Jews and Christians both 'revolted' (Egyptians / Jews) — different argument",
    'sc136_origenes_contra_celsum_iii_par70_en': "Greek: Celsus objects ‹God will be able to do all things›; English: the Jew's 'Not long ago ... yesterday or the day before' — different content",
    'sc136_origenes_contra_celsum_iii_par71_en': "Greek: Celsus assumes God, slave to pity, relieves the wicked and rejects the good; English: 'Why do you seek yet another origin?' — different content",
    'sc136_origenes_contra_celsum_iii_par72_en': "Greek: in the person of our teacher Celsus says ‹the wise turn away from what we say›; English: 'If someone predicted to you that the Son of God would come' — different content",
    'sc136_origenes_contra_celsum_iii_par73_en': "Greek: Celsus reviles the preacher of Christianity as saying ridiculous things; English: 'What sort of God is this who cannot even convince his own offspring?' — different content",
    'sc136_origenes_contra_celsum_iii_par74_en': 'Greek: Celsus charges the teacher with seeking the foolish — ‹whom do you call foolish?›; English: the Jew accuses Jesus of not showing himself God — different content',
    'sc136_origenes_contra_celsum_iii_par75_en': "Greek: Celsus compares the Christian teacher to one promising health but keeping patients from physicians; English: 'If these things were decreed for him ...' — different content",
    'sc136_origenes_contra_celsum_iii_par75_a_en': 'Greek: turning people from Epicurus and ‹Epicurean physicians› who deny providence; English: objections to the resurrection appearances — different content',
    'sc136_origenes_contra_celsum_iii_par75_b_en': 'Greek: we do not flee to infants and rustics saying ‹avoid physicians›; English: had Jesus appeared to all, Celsus would call it a phantom — different content',
    'sc136_origenes_contra_celsum_iii_par76_en': "Greek: Celsus' second example, a drunkard accusing the sober of drunkenness; English: the Jew's list of charges (virgin birth, village, spinner mother) — different content",
    'sc136_origenes_contra_celsum_iii_par77_en': 'Greek: Celsus likens the teacher to one with ophthalmia blaming the sharp-sighted; English: ‹Why, being God, did he not deliver himself from this shame?› — different content',
    'sc136_origenes_contra_celsum_iii_par78_en': "Greek: Celsus says he could say more but keeps silent; English: 'let us look at what has been taught by this teacher himself' — different content",
    'sc136_origenes_contra_celsum_iii_par79_en': "Greek: if anyone imagines superstition rather than wickedness among believers ...; English: Celsus on 'Blessed are the poor' and Plato — different content",
    'sc136_origenes_contra_celsum_iii_par8_en': "Greek: it is false that the Hebrews, being Egyptians, began from a revolt; English: the Jew's charge that Jesus fabricated his virgin birth — different content",
    'sc136_origenes_contra_celsum_iii_par80_en': 'Greek: Celsus says Christians are led by vain hopes; English: the bird at the Jordan and ‹what credible witness saw this?› — different content',
    'sc136_origenes_contra_celsum_iii_par81_en': "Greek: philosophers on the immortality of the soul, the future blessed life; English: 'What was the purpose of your descent to earth?' — different content",
    'sc136_origenes_contra_celsum_iii_par81_a_en': 'Greek: closing formula of Book III (‹here we end the third tome›); English: God acting through the incarnation — different content',
    'sc136_origenes_contra_celsum_iii_par9_en': 'Greek: ‹If all men wished to be Christians, these would no longer wish it› — refuted; English: Celsus on the resurrection of the body as disgusting and impossible — different content',
    'sc136_origenes_contra_celsum_iv_par11_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc136_origenes_contra_celsum_iv_par13_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc136_origenes_contra_celsum_iv_par17_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc136_origenes_contra_celsum_iv_par2_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc136_origenes_contra_celsum_iv_par23_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc136_origenes_contra_celsum_iv_par26_a_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc136_origenes_contra_celsum_iv_par27_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc136_origenes_contra_celsum_iv_par3_b_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc136_origenes_contra_celsum_iv_par41_en': 'faithful translation of the opening, followed by a bracketed editorial summary appended inside the translation text',
    'sc136_origenes_contra_celsum_iv_par49_a_en': 'faithful translation of the opening, followed by a bracketed editorial summary appended inside the translation text',
    'sc147_origenes_contra_celsum_v_par32_a_en': "English is a one-line placeholder ('Let us then see what follows in Celsus' text next.') for a 1,071-character Greek section on those who ‹moved from the east›",
    'sc147_origenes_contra_celsum_v_par33_en': "pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: after the Isaiah quotation it adds 'This universal gathering ... is the fulfillment of what was only partially accomplished in the history of Israel ... the calling of Abraham', absent from the Greek, and omits Celsus' ‹Let the second come›",
    'sc147_origenes_contra_celsum_v_par34_en': "Greek quotes Herodotus on the people of Marea and Apis (Ammon and cows); English says Celsus cites Herodotus 'on ... the disposal of their dead' — content not in the Greek",
    'sc147_origenes_contra_celsum_v_par35_en': "pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek ('This sounds tolerant and reasonable ...')",
    'sc147_origenes_contra_celsum_v_par36_en': "pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: the English asks whether Ammon is 'omnipotent, omniscient, perfectly good', absent from the Greek",
    'sc147_origenes_contra_celsum_v_par36_a_en': "pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: 'Celsus's moral relativism, if taken seriously ...'",
    'sc147_origenes_contra_celsum_v_par37_en': "pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: 'nomos engraphos ... varies from people to people ... as even the pagan philosophers recognized' — not in the Greek, which argues one must follow God's law even at the cost of dangers and death",
    'sc147_origenes_contra_celsum_v_par37_a_en': "pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: the Greek lists Meroe's Zeus and Dionysus, Arabian Urania, Osiris and Isis, Sarapis and the Son ‹firstborn of all creation›; the English gives a generic summary without any of this",
    'sc147_origenes_contra_celsum_v_par38_en': "pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: the Greek asks whether an Ethiopian in Arabia threatened with death should worship Urania; the English turns it into questions about conversion to philosophy not in the text",
    'sc147_origenes_contra_celsum_v_par38_a_en': "pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: 'The Egyptian gods Osiris, Isis, and Sarapis have their origins in mythological stories about human beings' — not the Greek (Osiris allegorised as water, Isis as earth)",
    'sc147_origenes_contra_celsum_v_par39_en': "pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: the Greek discusses edible and inedible animals and the Son as virtue and ‹second God›; the English is a generic polemic on crocodiles",
    'sc147_origenes_contra_celsum_v_par4_en': "pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: the English omits Celsus' question ‹gods or another race?› and adds 'more genuine worship ... more fitting for rational souls'",
    'sc147_origenes_contra_celsum_v_par41_en': "pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: the English attributes to Celsus a charge of 'arrogance (alazoneia)' in separating from other nations, while the Greek quotes Celsus that the Jews are blameless if they keep their own law",
    'sc147_origenes_contra_celsum_v_par42_en': "pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: the Greek describes the Jewish polity (no gymnastic contests, no prostitution); the English invents a dilemma ('if this special relationship is real ...')",
    'sc147_origenes_contra_celsum_v_par42_a_en': "pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: the first sentence loosely renders the Greek, the second ('Most nations worshipped ... the sun, the moon, statues, animals') is added",
    'sc147_origenes_contra_celsum_v_par43_en': "pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: 'Origen notes an example of the humanity of Jewish law ... without parallel in the ancient world ... dignity of the human person' — commentary, not the Greek",
    'sc147_origenes_contra_celsum_v_par45_en': "pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: the Greek is on names and incantations losing force in translation; the English adds 'El Shaddai' and 'intrinsic power because they express the very nature of the divine being'",
    'sc147_origenes_contra_celsum_v_par46_en': "pseudo-translation: the English is a free commentary in Origen's name, with arguments absent from the Greek: 'not because God is jealous in a petty human sense ... This is not arrogance but faithfulness' — absent; the Greek names Zeus, Amun and Papaeus",
    'sc147_origenes_contra_celsum_v_par49_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc147_origenes_contra_celsum_v_par57_a_en': 'Greek: it is not reasonable to judge truth-tellers and liars thus; those who practise not being deceived pronounce slowly after inquiry; English: astonishment that the devout are less trusted than Greek philosophers — different content',
    'sc147_origenes_contra_celsum_v_par58_en': 'Greek: Celsus mocks the angel rolling away the stone from the tomb; English: an angel came to the carpenter about Mary and the flight — different content',
    'sc147_origenes_contra_celsum_v_par6_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_v_par60_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_v_par61_en': "hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek (it adds a reference to 'the most impious heresy of Marcion, who posits two first principles')",
    'sc147_origenes_contra_celsum_v_par61_a_en': "hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek (it adds 'every rational soul was created with free will (autexousion)', not in this section's Greek)",
    'sc147_origenes_contra_celsum_v_par62_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_v_par63_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_v_par63_a_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_v_par64_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_v_par64_a_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_v_par65_a_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_v_par7_en': "hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek ('for we worship the Creator of heaven, not any created thing')",
    'sc147_origenes_contra_celsum_v_par8_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_v_par9_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par1_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par10_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par10_a_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par10_b_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par11_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par12_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par13_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par13_a_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par14_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par14_a_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par15_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek (the Plato quotation ‹he who lifts himself up in pride will be abandoned by God› is not the Laws passage quoted in the Greek)',
    'sc147_origenes_contra_celsum_vi_par15_a_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par16_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par16_a_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par17_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par17_a_en': 'English renders the opening of the same Greek section; coverage partial (the English is shorter or a condensation)',
    'sc147_origenes_contra_celsum_vi_par18_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par19_en': "hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek (the Greek cites ‹Praise God, heavens of heavens›; the English substitutes 'The heavens declare the glory of God')",
    'sc147_origenes_contra_celsum_vi_par19_a_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par2_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par20_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par21_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par22_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par22_a_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par23_en': 'hybrid pseudo-translation: the first sentence renders the Greek opening, then the English closes with a sentence absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par23_a_en': "hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek ('Celsus confuses the teachings of obscure Gnostic sects with those of the Church')",
    'sc147_origenes_contra_celsum_vi_par24_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par24_a_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par25_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par25_a_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par26_b_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par27_a_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par28_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par28_a_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par29_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par29_a_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par2_a_en': 'English renders the same Greek section faithfully (the closing sentence matches the Greek ending)',
    'sc147_origenes_contra_celsum_vi_par3_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par30_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par31_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par32_a_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par33_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par34_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par35_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par35_b_en': "hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek (the gloss on the 'dead soul' departed from God)",
    'sc147_origenes_contra_celsum_vi_par36_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par36_a_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par37_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par38_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par38_a_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par39_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par39_a_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par4_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par41_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par42_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par42_b_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par42_c_en': "hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek ('Christ voluntarily submitted to suffering ... triumphing over the powers of evil')",
    'sc147_origenes_contra_celsum_vi_par43_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par44_en': "hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek ('This explains how a being created good could fall into evil')",
    'sc147_origenes_contra_celsum_vi_par44_a_en': 'English renders the same Greek section faithfully (the closing sentence matches the Greek ending)',
    'sc147_origenes_contra_celsum_vi_par44_b_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par45_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par46_a_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par47_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par48_a_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par49_a_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par49_b_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par4_a_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par5_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par50_en': 'hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek',
    'sc147_origenes_contra_celsum_vi_par50_a_en': "hybrid pseudo-translation: the first sentence(s) render the Greek opening, then the English closes with commentary absent from the Greek (the 'days' of creation said to pertain to the 'kosmos noetos')",
    'sc150_origenes_contra_celsum_vii_par1_en': "fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek",
    'sc150_origenes_contra_celsum_vii_par10_en': "fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek",
    'sc150_origenes_contra_celsum_vii_par11_en': "fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek",
    'sc150_origenes_contra_celsum_vii_par12_en': "fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek",
    'sc150_origenes_contra_celsum_vii_par13_en': "fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek",
    'sc150_origenes_contra_celsum_vii_par14_en': "fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek",
    'sc150_origenes_contra_celsum_vii_par14_a_en': "fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek",
    'sc150_origenes_contra_celsum_vii_par15_en': "fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek",
    'sc150_origenes_contra_celsum_vii_par16_en': "fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek; it invents a free-will argument ('the existence of free will (to eph' hemin) in rational creatures ... To prevent sin by removing freedom would ... be tyranny') absent from the Greek, which discusses the Isaiah 53 prophecy",
    'sc150_origenes_contra_celsum_vii_par17_en': "fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek",
    'sc150_origenes_contra_celsum_vii_par18_en': "fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek; it invents an argument on God giving freedom 'without which goodness would be merely mechanical', while the Greek quotes Celsus on the Mosaic law of wealth and slaughter",
    'sc150_origenes_contra_celsum_vii_par19_en': "fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek",
    'sc150_origenes_contra_celsum_vii_par2_en': "fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek",
    'sc150_origenes_contra_celsum_vii_par20_en': "fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek",
    'sc150_origenes_contra_celsum_vii_par21_en': "fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek",
    'sc150_origenes_contra_celsum_vii_par22_en': "fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek",
    'sc150_origenes_contra_celsum_vii_par23_en': "fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek",
    'sc150_origenes_contra_celsum_vii_par23_a_en': "fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek",
    'sc150_origenes_contra_celsum_vii_par23_b_en': "fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek",
    'sc150_origenes_contra_celsum_vii_par24_en': "fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek",
    'sc150_origenes_contra_celsum_vii_par25_en': "fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek",
    'sc150_origenes_contra_celsum_vii_par26_en': "fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek",
    'sc150_origenes_contra_celsum_vii_par27_en': "fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek",
    'sc150_origenes_contra_celsum_vii_par28_en': "fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek",
    'sc150_origenes_contra_celsum_vii_par29_en': "fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek",
    'sc150_origenes_contra_celsum_vii_par3_en': "fabricated: the English is a free composition in Origen's name that does not render any part of this section's Greek",
    'sc167_clemens_epistula_ad_corinthios_chap10_en': 'faithful translation of the opening, followed by a bracketed editorial summary appended inside the translation text',
    'sc167_clemens_epistula_ad_corinthios_chap12_en': 'faithful translation of the opening, followed by a bracketed editorial summary appended inside the translation text',
    'sc167_clemens_epistula_ad_corinthios_chap35_en': 'faithful translation of the opening, followed by a bracketed editorial summary appended inside the translation text',
    'sc167_clemens_epistula_ad_corinthios_chap4_en': 'faithful translation of the opening, followed by a bracketed editorial summary appended inside the translation text',
    'sc167_clemens_epistula_ad_corinthios_chap6_en': 'English renders the same passage (partial or full coverage)',
    'sc167_clemens_epistula_ad_corinthios_chap8_en': 'English renders the same passage (partial or full coverage)',
    'sc172_epistula_barnabae_chap_12_verset_10_11b_en': 'English begins with the end of 12.11 and continues with 13.1–3 (Isaac and Rebecca) — not 12.10–11b',
    'sc172_epistula_barnabae_chap_12_verset_5a_7c_en': 'English begins with the bronze serpent (12.6–7) and continues with 12.8–9, omitting 12.5a–5b',
    'sc172_epistula_barnabae_chap_12_verset_8_9b_en': 'English renders this passage and then runs on into the following verses (coverage exceeds the locus)',
    'sc172_epistula_barnabae_chap_13_verset_1_en': 'English renders this passage and then runs on into the following verses (coverage exceeds the locus)',
    'sc172_epistula_barnabae_chap_13_verset_2a_3_en': 'English renders 13.4–5 (Jacob, Ephraim and Manasseh), not 13.2a–3 (Isaac and Rebecca)',
    'sc172_epistula_barnabae_chap_13_verset_4_6_en': "English renders 13.6–7 (Abraham, father of nations), not 13.4–6 (Jacob's blessing)",
    'sc172_epistula_barnabae_chap_13_verset_7a_7b_en': "English 'Therefore both things have been brought to completion ...' does not render 13.7a (‹if he was mentioned also through Abraham, we have the perfection of our knowledge›)",
    'sc172_epistula_barnabae_chap_14_verset_1a_3c_en': "English is a mixed paraphrase of 14.1–5 ('Moses received it as a servant ...' is 14.4), not a rendering of 14.1a–3c",
    'sc172_epistula_barnabae_chap_14_verset_4a_9_en': "English ('Now I want to write many things ... lest the Black One gain entrance') renders a different passage of the epistle, not 14.4a–9 (how we received the covenant)",
    'sc172_epistula_barnabae_chap_15_verset_1_2_en': 'English renders this passage and then runs on into the following verses (coverage exceeds the locus)',
    'sc172_epistula_barnabae_chap_15_verset_6a_7b_en': "English mixes a garbled 15.6b–7 with 15.9 ('the eighth day on which Jesus arose') — not a rendering of 15.6a–7b",
    'sc172_epistula_barnabae_chap_16_verset_5a_5c_en': 'English renders 16.6–7 (the temple built in the name of the Lord), not 16.5 (city, temple and people handed over)',
    'sc172_epistula_barnabae_chap_17_verset_1_2_en': "English is a closing farewell ('Children of love and peace ...'), not 17.1–2 (‹as far as was possible to explain to you simply›)",
    'sc172_epistula_barnabae_chap_19_verset_1a_6c_en': 'English renders the same passage (partial or full coverage)',
    'sc172_epistula_barnabae_chap_19_verset_7a_12c_en': "English begins at 19.5 ('love your neighbor more than your own soul') — it does not start with 19.7a",
    'sc172_epistula_barnabae_chap_21_verset_2_3_en': 'English renders this passage and then runs on into the following verses (coverage exceeds the locus)',
    'sc172_epistula_barnabae_chap_21_verset_4_5_en': 'English begins at 21.5 and continues with 21.6–7, omitting 21.4',
    'sc172_epistula_barnabae_chap_21_verset_6_7_en': "English ('While the good vessel is still with you ... Farewell') renders a different passage, not 21.6–7 (‹be taught by God›)",
    'sc172_epistula_barnabae_chap_2_verset_1_3_en': 'English renders this passage and then runs on into the following verses (coverage exceeds the locus)',
    'sc172_epistula_barnabae_chap_2_verset_4_6_en': "English ('Did I command your fathers ...', i.e. the content of the 2.7–9 node) does not render 2.4–6 (‹What is the multitude of your sacrifices ...›)",
    'sc172_epistula_barnabae_chap_2_verset_7_9_en': 'English (the fast God has chosen, Isaiah 58) renders a different passage, not 2.7–9 (‹Did I command your fathers ...›)',
    'sc172_epistula_barnabae_chap_4_verset_9a_en': 'English renders the same passage (partial or full coverage)',
    'sc172_epistula_barnabae_chap_5_verset_11_14_en': 'English (the water and the cross, baptism) renders a different passage, not 5.11–14 (the Son came in the flesh to complete the sins of the persecutors)',
    'sc172_epistula_barnabae_chap_5_verset_3_4b_en': 'English (the prophets prophesied about him; he abolished death) does not render 5.3–4b (thanks for knowledge; ‹nets are not unjustly spread for birds›)',
    'sc172_epistula_barnabae_chap_5_verset_5_7_en': 'English renders 5.9–11 (the choice of sinful apostles), not 5.5–7',
    'sc172_epistula_barnabae_chap_5_verset_8_10_en': "English renders 5.12–14 (the shepherd struck, 'Nail my flesh'), not 5.8–10",
    'sc172_epistula_barnabae_chap_6_verset_10a_10b_en': "English renders 6.11–12 (renewal, 'Let us make humanity'), not 6.10a–b (‹Blessed be our Lord who put wisdom in us›)",
    'sc172_epistula_barnabae_chap_6_verset_11_12c_en': 'English renders 13.1–3 (Isaac and Rebecca), not 6.11–12c',
    'sc172_epistula_barnabae_chap_6_verset_13a_16c_en': 'English renders 13.4–5 (Jacob crossing his hands), not 6.13–16',
    'sc172_epistula_barnabae_chap_6_verset_17a_19_en': 'English renders 14.1–3 (the covenant and the tablets), not 6.17–19 (milk and honey)',
    'sc172_epistula_barnabae_chap_7_verset_1_en': 'English renders 7.2, not 7.1',
    'sc172_epistula_barnabae_chap_7_verset_11a_11b_en': 'English (the heifer, the ashes and the scarlet wool on a stick) does not render 7.11 (the wool placed among thorns)',
    'sc172_epistula_barnabae_chap_7_verset_2_en': 'English renders 7.3, not 7.2',
    'sc172_epistula_barnabae_chap_7_verset_3a_5b_en': 'English begins mid-verse at 7.3c and omits 7.3a–3b (vinegar and gall, the fast commandment)',
    'sc172_epistula_barnabae_chap_7_verset_6a_8c_en': "English begins at 7.7 ('Pay attention to how the type of Jesus is revealed') and omits 7.6 (the two goats)",
    'sc172_epistula_barnabae_chap_7_verset_9a_10b_en': "English ('why is it that they place the wool in the middle of the thorns?' — the content of the 7.11 node) does not render 7.9a–10b",
    'sc172_epistula_barnabae_chap_8_verset_2a_4_en': 'English renders this passage and then runs on into the following verses (coverage exceeds the locus)',
    'sc172_epistula_barnabae_chap_8_verset_5_6b_en': 'English begins with the wool-and-hyssop question of 8.6a and omits 8.5 (the wool on the wood, the kingdom of Jesus on the wood)',
    'sc172_epistula_barnabae_chap_8_verset_7_en': "English ('By the hearing of the ear they obeyed me') renders a different passage, not 8.7 (‹clear to us, obscure to them›)",
    'sc172_epistula_barnabae_chap_9_verset_4a_5c_en': 'English renders this passage and then runs on into the following verses (coverage exceeds the locus)',
    'sc172_epistula_barnabae_chap_9_verset_6_en': 'English (Abraham circumcising with the doctrine of three letters — the content of the 9.7 node) does not render 9.6 (‹every Syrian and Arab ... are circumcised›)',
    'sc172_epistula_barnabae_chap_9_verset_7_8c_en': 'English begins with 9.8 (the 318 men) and omits 9.7 (‹Learn then, children of love ...›)',
    'sc172_epistula_barnabae_chap_9_verset_9_en': 'English (Moses on unclean animals) renders a different passage, not 9.9 (‹He knows who placed in us the implanted gift›)',
    'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_1_en': "English ('Theophilus to Autolycus, greeting. Since an agreeable discourse ...') does not render I.1 (‹A fluent tongue and elegant diction give pleasure ...›)",
    'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_10_en': "English renders a different chapter of Book I; the Greek of this node treats the gods of the Egyptians, Phidias' statues",
    'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_11_en': 'English renders a different chapter of Book I; the Greek of this node treats honouring the king without worshipping him',
    'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_12_en': 'English renders a different chapter of Book I; the Greek of this node treats the mockery of the name ‹Christian› (christon, anointed)',
    'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_13_en': 'English renders a different chapter of Book I; the Greek of this node treats the denial of the resurrection, Heracles and Asclepius',
    'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_14_en': 'English renders a different chapter of Book I; the Greek of this node treats ‹Do not disbelieve, but believe› — the prophets',
    'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_2_en': 'English renders the same passage (partial or full coverage)',
    'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_3_en': 'English renders a different chapter of Book I; the Greek of this node treats ‹Tell me the form of God› — ineffable',
    'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_4_en': 'English renders a different chapter of Book I; the Greek of this node treats God without beginning, the etymology of theos',
    'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_5_en': 'English renders a different chapter of Book I; the Greek of this node treats the soul invisible, the ship and its helmsman',
    'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_6_en': 'English renders a different chapter of Book I; the Greek of this node treats ‹Consider, O man, his works›',
    'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_7_en': 'English renders a different chapter of Book I; the Greek of this node treats ‹This is my God, the Lord of all›',
    'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_8_en': 'English renders a different chapter of Book I; the Greek of this node treats ‹You do not believe the dead are raised›',
    'sc20_theophilus_ad_autolycum_i_liv_1_le_dieu_des_chretiens_chap_9_en': 'English renders a different chapter of Book I; the Greek of this node treats the gods are dead men — Kronos, Zeus',
    'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_18_en': 'English renders the same passage (partial or full coverage)',
    'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_37_en': 'English renders the same passage (partial or full coverage)',
    'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_7_en': 'English renders the same passage (partial or full coverage)',
    'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_22_en': 'English renders the same passage (partial or full coverage)',
    'sc379_athenagoras_legatio_chap29_en': 'English renders the same passage (partial or full coverage)',
    'sc464_pamphilus_apologia_pro_origene_par72_en': 'English renders the same passage (partial or full coverage)',
    'sc470_aristides_apologia_chap11_en': 'English renders the same passage (partial or full coverage)',
    'sc470_aristides_apologia_chap16_en': 'English renders the same passage (partial or full coverage)',
    'sc53bis_hermas_pastor_chap111_en': "English is a synopsis in the editor's voice of the same Similitude X ('This chapter constitutes an appendix ...'), not a translation of the Latin",
    'sc53bis_hermas_pastor_chap12_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap13_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap14_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap15_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap16_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap17_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap18_en': "English is a synopsis in the editor's voice of the same chapter (Hermas asks about the three forms of the woman), not a translation",
    'sc53bis_hermas_pastor_chap19_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap2_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap20_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap21_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap22_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap23_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap24_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap25_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap26_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap27_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap28_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap29_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap3_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap30_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap31_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap32_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap33_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap34_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap35_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap36_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap37_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap38_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap39_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap4_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap40_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap41_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap42_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap43_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap44_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap45_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap46_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap47_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap48_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap49_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap5_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap50_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap51_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap52_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap53_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap54_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap55_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap56_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap57_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap58_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap59_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap6_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap60_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap61_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap62_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap63_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap64_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap65_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap66_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap67_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap68_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap69_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap7_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap70_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap71_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap72_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap73_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap74_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap76_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap78_en': "English is a synopsis in the editor's voice of the same chapter (opening of Similitude IX), not a translation",
    'sc53bis_hermas_pastor_chap79_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap8_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap80_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap81_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap82_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap83_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap84_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap85_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap86_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap87_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap88_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap89_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap9_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap90_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap91_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap92_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap93_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap94_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap95_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap96_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap97_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc53bis_hermas_pastor_chap98_en': "not a translation: an English synopsis in the editor's voice that describes a different chapter of the Shepherd than the Greek of this node",
    'sc79_chrysostomus_de_providentia_chap10_en': "English is a close paraphrastic synopsis of the same chapter in the editor's voice ('Chapter 10 of Chrysostom's On Providence ...'), not a translation",
    'sc79_chrysostomus_de_providentia_chap14_en': "English is a close paraphrastic synopsis of the same chapter in the editor's voice ('Chapter 14 of Chrysostom's On Providence ...'), not a translation",
}
