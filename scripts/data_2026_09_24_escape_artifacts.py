#!/usr/bin/env python3
"""Decisions: import escapes printed literally in public descriptions.

Two bibliographic records show a literal "&#13;" and literal backslash-n
sequences where the source had line breaks. The Beta Code Greek in
passage_sen_ep_15_99_25 also contains "\\n", but there "\\" is a grave accent
and "n" a letter: it is left for Romain (the Greek needs the edition).
"""

# node id -> exact literal sequences to replace by a newline, in order
FIX = {
    "pub_arfe_2009_servano_da_segni_gen_14_la_confutazione_del_fatalismo_astrologic": ["&#13;\\n"],
    "pub_fauske_2005_paideia_versus_soteria_et_studium_av_menneskesynets_utvikling_an": ["\\n"],
}
NEEDS_ROMAIN = {
    "passage_sen_ep_15_99_25": "Seneca's Greek quotation is stored in raw Beta Code; it should be replaced by the Greek of the edition.",
}
