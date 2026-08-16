#!/usr/bin/env python3
"""Data for ``apply_2026_08_17_linguistic_repairs.py`` (wave 6, linguistic).

The 2026-08-16 deep linguistic audit
(``data/audit/2026-08-16_deep_audit_linguistic.jsonl``) reported 1,589 findings.
This module carries the subset that could be **verified piece by piece against a
source on disk** — the TLG E corpus at ``~/Desktop/Romain/TLGE`` (author table
``AUTHTAB.DIR``, work tables ``TLG****.IDT``) and the critical editions under
``~/Desktop/DOCTORAT/Doctorat SHAL/``.

Nothing here was composed. Every Greek string below is a mechanical
beta-code-to-Unicode decoding of a byte range of a TLG E author file, and the
byte range is recorded with it so any reviewer can re-read the same bytes:

    python3 - <<'EOF'
    import beta_code, re
    raw = open('~/Desktop/Romain/TLGE/TLG0086.TXT','rb').read()
    seg = bytes(c for c in raw[B0:B1] if 0x20 <= c < 0x80).decode('ascii')
    print(beta_code.beta_code_to_greek(re.sub(r'[@{}<>$&%#"\\d]+',' ',seg).lower()))
    EOF

Where the source could not be pinned down with certainty, the item is **flagged,
not rewritten**. That is the only acceptable outcome for an unverified reading.

Findings that turned out to be audit false positives are recorded here too, with
the measurement that refutes them, so the next wave does not re-open them.
"""

from __future__ import annotations

# ===========================================================================
# LOT 1 — Magna Moralia: OCR-corrupted Greek restored from TLG E
# ===========================================================================
#
# 434 ``passage_arist_mm_*`` nodes carry the Magna Moralia under
# ``urn:cts:greekLit:tlg0086.tlg022.1st1K-grc1`` — a URN that TLG0086.IDT
# confirms ("022  Magna moralia"). Their text is a bad OCR of that work: 39 of
# them show the corruption openly as ``??`` or ``**`` runs, but the same OCR also
# silently substituted letters throughout (``βελσίστης`` for ``βελτίστης``,
# ``ὠλλὰ`` for ``ἀλλὰ``, ``αὐτῇς`` for ``αὐτῆς``, ``ἔικεν`` for ``ἔοικεν``).
# Only the 39 openly-corrupt nodes are repaired here; the silent substitutions in
# the other 395 are reported, not touched (see the plan).
#
# Method — a whole-work sequential alignment, not a per-node guess:
#   1. The 434 nodes are sorted by canonical_ref (1.1.1 … 2.17.2).
#   2. Each node is reduced to accent-stripped base letters and its first clean
#      4-word window is located in the same reduction of TLG0086.TXT, searching
#      forward from the previous node's position. 433/434 anchor; the starts are
#      strictly monotonic and the span/length ratio has median 1.01.
#   3. Node i occupies [start(i), start(i+1)); boundaries are then refined by
#      difflib against a padded window and snapped to word boundaries.
#   4. The resulting byte range is decoded with ``beta_code``. Line-break
#      hyphenation and the beta-code capital marker are undone; a final sigma
#      before a bracket is restored.
#
# Verification recorded per node: the decoded text is >=92.9% Greek letters, the
# new/old length ratio has median 1.005, and no ``?`` survives.
#
# Worked example — passage_arist_mm_1_1_10, TLG0086 bytes 3099211-3099637:
#   old: "εἰ οὖν πασῶν τῶν δυνάμεων ἀγαθὸν τ?? τέλος, δῆλον ὡς καὶ τῆς βελσίστης
#         βέλτιστον ἂν εἴη. ὠλλὰ μ??ν γε π??λισικὴ βελείστη δύναμις …"
#   new: "εἰ οὖν πασῶν τῶν δυνάμεων ἀγαθὸν τὸ τέλος, δῆλον ὡς καὶ τῆς βελτίστης
#         βέλτιστον ἂν εἴη. ἀλλὰ μὴν ἥ γε πολιτικὴ βελτίστη δύναμις …"

MAGNA_MORALIA_TLG_FILE = "TLG0086.TXT"
MAGNA_MORALIA_TLG_WORK = "tlg0086.tlg022 (TLG0086.IDT: '022  Magna moralia')"

MAGNA_MORALIA_REPAIRS: dict[str, dict] = {
    "passage_arist_mm_1_1_8": {
        "canonical_ref": "1.1.8",
        "db_passage_id": "9ab23664-258f-4900-ad28-fbd3e65b9a27",
        "tlg_bytes": (3098300, 3098861),
        "old_len": 441,
        "text": (
            "διὸ οὐκ ὀρθῶς ἥψατο ταύτῃ τῶν ἀρετῶν. Μετὰ ταῦτα δὲ Πλάτων διείλετο τὴν "
            "ψυχὴν εἴς τε τὸ λόγον ἔχον καὶ εἰς τὸ ἄλογον ὀρθῶς, καὶ ἀπέδωκεν ἑκάστῳ "
            "[τὰς] ἀρετὰς τὰς προσηκούσας. μέχρι μὲν οὖν τούτου καλῶς· μετὰ μέντοι "
            "τοῦτο οὐκέτι ὀρθῶς. τὴν γὰρ ἀρετὴν κατέμιξεν [καὶ συνέζευξεν] εἰς τὴν "
            "πραγματείαν τὴν ὑπὲρ τἀγαθοῦ, οὐ δὴ ὀρθῶς· οὐ γὰρ οἰκεῖον· ὑπὲρ γὰρ τῶν "
            "ὄντων καὶ ἀληθείας λέγοντα οὐκ ἔδει ὑπὲρ ἀρετῆς φράζειν· οὐδὲν γὰρ τούτῳ "
            "κἀκείνῳ κοινόν."
        ),
    },
    "passage_arist_mm_1_1_9": {
        "canonical_ref": "1.1.9",
        "db_passage_id": "d625bbbb-658c-4dba-98c9-9f70246273c9",
        "tlg_bytes": (3098865, 3099209),
        "old_len": 277,
        "text": (
            "Οὗτοι μὲν οὖν ἐπὶ τοσοῦτον ἐφήψαντο καὶ οὕτως· ἐχόμενον δ' ἂν εἴη μετὰ "
            "ταῦτα σκέψασθαι τί δεῖ αὐτοὺς λέγειν ὑπὲρ τούτων. Πρῶτον μὲν οὖν ἰδεῖν "
            "δεῖ ὅτι πάσης ἐπιστήμης καὶ δυνάμεως ἐστί τι τέλος, καὶ τοῦτ' ἀγαθόν· "
            "οὐδεμία γὰρ οὔτ' ἐπιστήμη οὔτε δύναμις ἕνεκεν κακοῦ ἐστίν."
        ),
    },
    "passage_arist_mm_1_1_10": {
        "canonical_ref": "1.1.10",
        "db_passage_id": "e5fdac35-e7fa-44c0-8ee9-706aa45342df",
        "tlg_bytes": (3099211, 3099637),
        "old_len": 339,
        "text": (
            "εἰ οὖν πασῶν τῶν δυνάμεων ἀγαθὸν τὸ τέλος, δῆλον ὡς καὶ τῆς βελτίστης "
            "βέλτιστον ἂν εἴη. ἀλλὰ μὴν ἥ γε πολιτικὴ βελτίστη δύναμις, ὥστε τὸ τέλος "
            "αὐτῆς ἂν εἴη ἀγαθόν. ὑπὲρ ἀγαθοῦ ἄρα, ὡς ἔοικεν, ἡμῖν λεκτέον, καὶ ὑπὲρ "
            "ἀγαθοῦ οὐ τοῦ ἁπλῶς, ἀλλὰ τοῦ ἡμῖν· οὐ γὰρ τοῦ θεῶν ἀγαθοῦ· ἀλλ' ὑπὲρ "
            "μὲν τούτου καὶ ἄλλος λόγος καὶ ἀλλοτρία ἡ σκέψις."
        ),
    },
    "passage_arist_mm_1_1_11": {
        "canonical_ref": "1.1.11",
        "db_passage_id": "e5ad04b6-7285-4198-871d-5890ec3f9834",
        "tlg_bytes": (3099639, 3100017),
        "old_len": 296,
        "text": (
            "ὑπὲρ τοῦ πολιτικοῦ ἄρα ἡμῖν λεκτέον ἀγαθοῦ. Πάλιν δὲ καὶ τοῦτο διελεῖν "
            "δεῖ. ὑπὲρ ἀγαθοῦ τοῦ πῶς λεγομένου; οὐ γάρ ἐστιν ἁπλοῦν. λέγεται γὰρ "
            "ἀγαθὸν ἢ τὸ ἄριστον ἐν ἑκάστῳ τῶν ὄντων, τοῦτο δ' ἐστὶ τὸ διὰ τὴν αὑτοῦ "
            "φύσιν αἱρετόν· ἢ οὗ τἆλλα μετασχόντα ἀγαθὰ ἐστίν, τοῦτο δέ ἐστιν ἡ ἰδέα "
            "τἀγαθοῦ."
        ),
    },
    "passage_arist_mm_1_1_21": {
        "canonical_ref": "1.1.21",
        "db_passage_id": "2b8fb1be-6e56-4844-963a-7196e66dc99d",
        "tlg_bytes": (3103734, 3104062),
        "old_len": 258,
        "text": (
            "ἀρίστου. Ἴσως δὲ οὐδὲ δεῖ βουλόμενόν τι δεικνύναι, τοῖς μὴ φανεροῖς "
            "παραδείγμασι χρῆσθαι, ἀλλ' ὑπὲρ τῶν ἀφανῶν τοῖς φανεροῖς, καὶ ὑπὲρ τῶν "
            "νοητῶν τοῖς αἰσθητοῖς. [καὶ] ταῦτα γὰρ φανερώτερα. ὅταν οὖν ὑπὲρ τἀγαθοῦ "
            "τις ἐγχειρῇ λέγειν, οὐ λεκτέον ἐστὶν ὑπὲρ τῆς ἰδέας."
        ),
    },
    "passage_arist_mm_1_1_22": {
        "canonical_ref": "1.1.22",
        "db_passage_id": "aa4af56c-b2ef-4b7f-b61e-8110db58018f",
        "tlg_bytes": (3104064, 3104345),
        "old_len": 212,
        "text": (
            "καίτοι οἴονταί γε [δεῖν], ὅταν ὑπὲρ τοῦ ἀγαθοῦ λέγωσιν, ὑπὲρ τῆς ἰδέας "
            "δεῖν λέγειν· ὑπὲρ γὰρ τοῦ μάλιστα ἀγαθοῦ φασι δεῖν λέγειν, αὐτὸ δὲ "
            "ἕκαστον μάλιστ' ἐστὶν [τὸ] τοιοῦτον, ὥστε μάλιστ' ἂν εἴη ἀγαθὸν ἡ ἰδέα, "
            "ὡς οἴονται."
        ),
    },
    "passage_arist_mm_1_1_23": {
        "canonical_ref": "1.1.23",
        "db_passage_id": "3ac24f6d-4751-4bb9-944c-c54de9cb5bdc",
        "tlg_bytes": (3104348, 3104796),
        "old_len": 322,
        "text": (
            "ὁ δὴ τοιοῦτος λόγος ἀληθὴς μέν ἐστιν ἴσως· ἀλλ' οὐχ ἡ πολιτικὴ ἐπιστήμη "
            "ἢ δύναμις, ὑπὲρ ἧς νῦν ἐστιν ὁ λόγος, οὐχ ὑπὲρ τούτου σκοπεῖ τἀγαθοῦ, "
            "ἀλλὰ τοῦ ἡμῖν ἀγαθοῦ. [οὐδεμία γὰρ οὔτ' ἐπιστήμη οὔτε δύναμις ὑπὲρ τοῦ "
            "τέλους λέγει ὅτι ἀγαθόν, ὥστε οὐδ' ἡ πολιτική.] διὸ οὐχ ὑπὲρ τοῦ κατὰ "
            "τὴν ἰδέαν ἀγαθοῦ τὸν λόγον ποιεῖται. Ἀλλ'"
        ),
    },
    "passage_arist_mm_1_1_24": {
        "canonical_ref": "1.1.24",
        "db_passage_id": "694f1545-4775-4181-a42c-10355daea397",
        "tlg_bytes": (3104790, 3105113),
        "old_len": 254,
        "text": (
            "Ἀλλ' ἴσως [φησὶ] τούτῳ τἀγαθῷ ἀρχῇ χρησάμενος ὑπὲρ τῶν καθ' ἕκαστα, ἐκ "
            "τούτου προβάς, ἐρεῖ. οὐδ' οὕτως ὀρθῶς. δεῖ γὰρ τὰς ἀρχὰς οἰκείας "
            "λαμβάνειν. ἄτοπον γάρ, εἴ τις βουλόμενος τὸ τρίγωνον ὡς δυσὶν ὀρθαῖς "
            "ἴσας ἔχον δεῖξαι, λάβοι ἀρχὴν ὅτι ἡ ψυχὴ ἀθάνατος."
        ),
    },
    "passage_arist_mm_1_1_25": {
        "canonical_ref": "1.1.25",
        "db_passage_id": "c36aa0fb-5d78-4e5a-97d5-2ceb300b20a7",
        "tlg_bytes": (3105115, 3105307),
        "old_len": 155,
        "text": (
            "οὐ γὰρ οἰκεία, δεῖ δὲ τὴν ἀρχὴν οἰκείαν εἶναι καὶ συνημμένην· νῦν δὲ καὶ "
            "ἄνευ τοῦ τὴν ψυχὴν εἶναι ἀθάνατον δείξει τις δυσὶν ὀρθαῖς ἴσας ἔχον τὸ "
            "τρίγωνον."
        ),
    },
    "passage_arist_mm_1_1_26": {
        "canonical_ref": "1.1.26",
        "db_passage_id": "ed16ed93-a120-432e-8ef6-4e6b1ff69cb3",
        "tlg_bytes": (3105309, 3106217),
        "old_len": 690,
        "text": (
            "ὁμοίως δὲ καὶ ἐπὶ τῶν ἀγαθῶν ἐστι θεάσασθαι τὰ ἄλλα ἄνευ τοῦ κατὰ τὴν "
            "ἰδέαν ἀγαθοῦ διὸ οὐκ οἰκείαν ἀρχὴν εἶναι τούτου τἀγαθοῦ. Οὐκ ὀρθῶς δὲ "
            "οὐδ' ὁ Σωκράτης ἐπιστήμας ἐποίει τὰς ἀρετάς. ἐκεῖνος γὰρ οὐδὲν ᾤετο δεῖν "
            "μάτην εἶναι, ἐκ δὲ τοῦ τὰς ἀρετὰς ἐπιστήμας εἶναι συνέβαινεν αὐτῷ τὰς "
            "ἀρετὰς μάτην εἶναι. διὰ τί; ὅτι ἐπὶ τῶν ἐπιστημῶν συμβαίνει ἅμα εἰδέναι "
            "τὴν ἐπιστήμην τί ἐστι καὶ εἶναι ἐπιστήμονα [ εἰ γὰρ ἰατρικήν τις οἶδεν "
            "τί ἐστίν, καὶ ἰατρὸς οὗτος εὐθέως ἐστίν, ὁμοίως δὲ καὶ τῶν ἄλλων "
            "ἐπιστημῶν]· ἀλλ' οὐκ ἐπὶ τῶν ἀρετῶν τοῦτο συμβαίνει. οὐ γὰρ εἴ τις οἶδεν "
            "τὴν δικαιοσύνην τί ἐστίν, εὐθέως δίκαιος ἐστίν, ὡς δ' αὔτως κἀπὶ τῶν "
            "ἄλλων. συμβαίνει οὖν καὶ μάτην τὰς ἀρετὰς εἶναι καὶ μὴ εἶναι ἐπιστήμας."
        ),
    },
    "passage_arist_mm_1_2_1": {
        "canonical_ref": "1.2.1",
        "db_passage_id": "e2abe236-1849-492d-992c-0cbf66dc804e",
        "tlg_bytes": (3106223, 3106752),
        "old_len": 411,
        "text": (
            "Ἐπεὶ δ' ὑπὲρ τούτων διώρισται, πειραθῶμεν λέγειν τἀγαθὸν ποσαχῶς "
            "λέγεται. Ἔστι γὰρ τῶν ἀγαθῶν τὰ μὲν τίμια, τὰ δ' ἐπαινετά, τὰ δὲ "
            "δυνάμεις. τὸ δὲ τίμιον λέγω τὸ τοιοῦτον, τὸ θεῖον, τὸ βέλτιον, οἷον "
            "ψυχή, νοῦς, τὸ ἀρχαιότερον, ἡ ἀρχή, τὰ τοιαῦτα· τίμια γὰρ ἐφ' οἷς ἡ "
            "τιμή, τοῖς δὲ τοιούτοις πᾶσιν τιμὴ ἀκολουθεῖ. οὐκοῦν καὶ ἡ ἀρετὴ τίμιον, "
            "ὅταν γε δὴ ἀπ' αὐτῆς σπουδαῖός τις γένηται· ἤδη γὰρ οὗτος εἰς τὸ τῆς "
            "ἀρετῆς σχῆμα ἥκει."
        ),
    },
    "passage_arist_mm_1_2_2": {
        "canonical_ref": "1.2.2",
        "db_passage_id": "214738f1-48ac-4bfe-b34a-5409d3b39f8c",
        "tlg_bytes": (3106754, 3107000),
        "old_len": 198,
        "text": (
            "τὰ δ' ἐπαινετά, οἷον ἀρεταί· ἀπὸ γὰρ τῶν κατ' αὐτὰς πράξεων ὁ ἔπαινος "
            "γίνεται. τὰ δὲ δυνάμεις, οἷον ἀρχὴ πλοῦτος ἰσχὺς κάλλος· τούτοις γὰρ καὶ "
            "ὁ σπουδαῖος εὖ ἂν δύνηται χρήσασθαι καὶ ὁ φαῦλος κακῶς"
        ),
    },
    "passage_arist_mm_1_3_2": {
        "canonical_ref": "1.3.2",
        "db_passage_id": "f5ff8289-167a-4ea7-93b5-0f565414389b",
        "tlg_bytes": (3110722, 3111029),
        "old_len": 240,
        "text": (
            "τὰ δ' ἐν ψυχῇ διώρισται ἀγαθὰ εἰς τρία, εἰς φρόνησιν εἰς ἀρετὴν καὶ "
            "ἡδονήν. Ἤδη τοίνυν τὸ μετὰ τοῦτο, ὃ καὶ λέγομεν πάντες καὶ δοκεῖ καὶ "
            "τέλος τῶν ἀγαθῶν καὶ τελειότατον εἶναι, ἡ εὐδαιμονία, καὶ τοῦτο ταὐτό "
            "φαμεν εἶναι τὸ εὖ πράττειν καὶ εὖ ζῆν."
        ),
    },
    "passage_arist_mm_1_3_3": {
        "canonical_ref": "1.3.3",
        "db_passage_id": "2d27e3e1-4c08-4f91-a484-4199abaf532a",
        "tlg_bytes": (3111031, 3111363),
        "old_len": 257,
        "text": (
            "τὸ δὲ τέλος ἐστὶν οὐχ ἁπλοῦν ἀλλὰ διττόν· ἐνίων μὲν γάρ ἐστι τὸ τέλος "
            "αὐτὴ ἡ ἐνέργεια καὶ ἡ χρῆσις, οἷον τῆς ὄψεως [ἐστιν ἡ ὅρασις]· καὶ ἔστιν "
            "γε ἡ χρῆσις αἱρετωτέρα τῆς ἕξεως· τέλος γὰρ ἡ χρῆσις· οὐδεὶς γὰρ ἂν "
            "βούλοιτο ἔχειν τὴν ὄψιν μὴ μέλλων ὁρᾶν ἀλλὰ μύειν."
        ),
    },
    "passage_arist_mm_1_3_4": {
        "canonical_ref": "1.3.4",
        "db_passage_id": "c538788a-53c5-4b7b-b503-325ca1a500f3",
        "tlg_bytes": (3111366, 3111611),
        "old_len": 193,
        "text": (
            "ὁμοίως δὲ καὶ ἐπ' ἀκοῆς καὶ τῶν τοιούτων. ὧν ἄρα καὶ [ἡ] χρῆσις καὶ ἕξις "
            "ἐστίν, ἀεὶ βέλτιον καὶ αἱρετώτερον ἡ χρῆσις τῆς ἕξεως· ἡ γὰρ χρῆσις καὶ "
            "ἡ ἐνέργεια τέλος, ἡ δ' ἕξις τῆς χρήσεως ἕνεκεν."
        ),
    },
    "passage_arist_mm_1_3_5": {
        "canonical_ref": "1.3.5",
        "db_passage_id": "22726c88-ced5-49ae-8d14-d66ac4b27f16",
        "tlg_bytes": (3111615, 3111943),
        "old_len": 243,
        "text": (
            "Μετὰ τοῦτο τοίνυν τοῦτ' ἐάν τις σκοπῇ ἐπὶ τῶν ἐπιστημῶν πασῶν, ὄψεται "
            "οὐκ ἄλλην μὲν ποιοῦσαν οἰκίαν, ἄλλην δὲ σπουδαίαν οἰκίαν, ἀλλὰ τὴν "
            "οἰκοδομικήν· καὶ οὗ ποιητικὸς ὁ οἰκοδόμος, ἡ τούτου ἀρετὴ τοῦ αὐτοῦ "
            "τούτου εὖ ποιητική. ὁμοίως [καὶ] ἐπὶ τῶν ἄλλων ἁπάντων."
        ),
    },
    "passage_arist_mm_1_4_1": {
        "canonical_ref": "1.4.1",
        "db_passage_id": "39678df4-05c5-41e6-b536-181229f91979",
        "tlg_bytes": (3111947, 3112319),
        "old_len": 287,
        "text": (
            "Μετὰ τοίνυν τοῦτο ὁρῶμεν ὅτι οὐθενὶ ἄλλῳ ἢ ψυχῇ ζῶμεν· ἐν ψυχῇ δέ ἐστιν "
            "ἀρετή· τὸ αὐτό γέ τοί φαμεν τήν τε ψυχὴν ποιεῖν καὶ τὴν τῆς ψυχῆς "
            "ἀρετήν. ἀλλ' ἡ μὲν ἀρετὴ ἐν ἑκάστῳ τοῦτο ποιεῖ [ εὖ] οὗ ἐστιν ἀρετή, ἡ "
            "δὲ ψυχὴ καὶ τἆλλα μέν, ψυχῇ δὲ ζῶμεν· διὰ τὴν τῆς ψυχῆς ἀρετὴν ἄρα εὖ "
            "ζήσομεν."
        ),
    },
    "passage_arist_mm_1_4_2": {
        "canonical_ref": "1.4.2",
        "db_passage_id": "b3a966f7-916a-4a0b-b925-29e96f8d3582",
        "tlg_bytes": (3112323, 3112616),
        "old_len": 218,
        "text": (
            "Τὸ δέ γε εὖ ζῆν καὶ εὖ πράττειν οὐθὲν ἄλλο ἢ τὸ εὐδαιμονεῖν λέγομεν. τὸ "
            "ἄρα εὐδαιμονεῖν καὶ ἡ εὐδαιμονία ἐν τῷ εὖ ζῆν ἐστίν, τὸ δ' εὖ ζῆν ἐν τῷ "
            "κατὰ τὰς ἀρετὰς ζῆν. τοῦτ' ἄρ' ἐστὶν τέλος καὶ ἡ εὐδαιμονία καὶ τὸ "
            "ἄριστον. Ἐν"
        ),
    },
    "passage_arist_mm_1_4_5": {
        "canonical_ref": "1.4.5",
        "db_passage_id": "90973c2d-b8a6-4521-971b-e2a864410aec",
        "tlg_bytes": (3113291, 3113851),
        "old_len": 440,
        "text": (
            "Ἐπεὶ δ' οὖν ἐστιν ἡ εὐδαιμονία τέλειον ἀγαθὸν καὶ τέλος, οὐδὲ τοῦτο δεῖ "
            "λανθάνειν ὅτι καὶ ἐν τελείῳ ἔσται. οὐ γὰρ ἔσται ἐν παιδί [ οὐ γάρ ἐστι "
            "παῖς εὐδαίμων], ἀλλ' ἐν ἀνδρί· οὗτος γὰρ τέλειος. Οὐδ' ἐν χρόνῳ γε "
            "ἀτελεῖ, ἀλλ' ἐν τελείῳ. τέλειος δ' ἂν εἴη χρόνος, ὅσον ἄνθρωπος βιοῖ. "
            "καὶ γὰρ λέγεται ὀρθῶς παρὰ τοῖς πολλοῖς ὅτι δεῖ τὸν εὐδαίμονα ἐν τῷ "
            "μεγίστῳ χρόνῳ τοῦ βίου κρίνειν, ὡς δέον τὸ τέλειον εἶναι καὶ ἐν χρόνῳ "
            "τελείῳ καὶ ἐν ἀνθρώπῳ."
        ),
    },
    "passage_arist_mm_1_5_3": {
        "canonical_ref": "1.5.3",
        "db_passage_id": "1f55109a-38bb-4cfd-a7c4-51645d590651",
        "tlg_bytes": (3116978, 3117533),
        "old_len": 444,
        "text": (
            "Ἔστιν δ' ἡ ἀρετὴ ἡ ἠθικὴ ὑπὸ ἐνδείας καὶ ὑπερβολῆς φθειρομένη. ὅτι δὲ ἡ "
            "ἔνδεια καὶ ἡ ὑπερβολὴ φθείρει, τοῦτ' ἰδεῖν ἔστιν ἐκ τῶν ἠθικῶν [ δεῖ δ' "
            "ὑπὲρ τῶν ἀφανῶν τοῖς φανεροῖς μαρτυρίοις χρῆσθαι]. εὐθέως γὰρ ἐπὶ "
            "γυμνασίων ἴδοι ἄν τις· πολλῶν γὰρ γινομένων φθείρεται ἡ ἰσχύς, ὀλίγων τε "
            "ὡσαύτως. ἐπί τε ποτῶν καὶ σιτίων ὡσαύτως· πολλῶν τε γὰρ δὴ γινομένων "
            "φθείρεται ἡ ὑγίεια, ὀλίγων τε ὡσαύτως, συμμέτρων δὲ γινομένων σῴζεται ἡ "
            "ἰσχὺς καὶ ἡ ὑγίεια."
        ),
    },
    "passage_arist_mm_1_5_5": {
        "canonical_ref": "1.5.5",
        "db_passage_id": "09d52d98-2164-4886-9274-097dd9f94370",
        "tlg_bytes": (3117935, 3118268),
        "old_len": 261,
        "text": (
            "καὶ γὰρ οἱ λίαν φόβοι καὶ πάντες φθείρουσι, καὶ οἱ περὶ μηθὲν δὲ ὁμοίως. "
            "ἔστιν δ' ἡ ἀνδρεία περὶ φόβους, ὥστε οἱ μέτριοι φόβοι αὔξουσι τὴν "
            "ἀνδρείαν. ὑπὸ τῶν αὐτῶν ἄρα καὶ αὔξεται καὶ φθείρεται ἡ ἀνδρεία· ὑπὸ "
            "φόβων γὰρ τοῦτο πάσχουσιν. ὁμοίως δὲ καὶ αἱ ἄλλαι ἀρεταί."
        ),
    },
    "passage_arist_mm_1_6_2": {
        "canonical_ref": "1.6.2",
        "db_passage_id": "eaa772c3-e6e6-48b1-8e2c-a5342a4c4e99",
        "tlg_bytes": (3118563, 3118829),
        "old_len": 205,
        "text": (
            "ἔστιν οὖν ἡ ἀρετὴ περὶ ἡδονὰς καὶ λύπας. Ἡ δ' ἠθικὴ ἀρετὴ ἐντεῦθεν τὰς "
            "ἐπωνυμίας ἔχει, εἰ δεῖ παρὰ γράμμα λέγοντα τὴν ἀλήθειαν ὡς ἔχει σκοπεῖν "
            "[ δεῖ δ' ἴσως]. τὸ γὰρ ἦθος ἀπὸ τοῦ ἔθους ἔχει τὴν ἐπωνυμίαν"
        ),
    },
    "passage_arist_mm_1_6_3": {
        "canonical_ref": "1.6.3",
        "db_passage_id": "29c69f7b-c1b4-4268-a137-c77d30823995",
        "tlg_bytes": (3118831, 3119287),
        "old_len": 357,
        "text": (
            "ἠθικὴ γὰρ καλεῖται διὰ τὸ ἐθίζεσθαι. ᾧ καὶ δῆλον ὅτι οὐδεμία ἡμῖν τῶν "
            "ἀρετῶν τῶν τοῦ ἀλόγου μέρους φύσει ἐγγίνεται· οὐθὲν γὰρ τῶν ὄντων φύσει "
            "ἔθει ἄλλως γίνεται. οἷον ὁ λίθος καὶ ὅλως τὰ βαρέα πέφυκε κάτω φέρεσθαι· "
            "ἄν τις οὖν ἄνω ῥίπτῃ πολλάκις καὶ ἐθίζῃ ἄνω φέρεσθαι, ὅμως οὐκ ἄν ποτε "
            "ἄνω ἐνεχθείη, ἀλλ' ἀεὶ κάτω. ὁμοίως [καὶ] ἐπὶ τῶν ἄλλων τῶν τοιούτων."
        ),
    },
    "passage_arist_mm_1_9_7": {
        "canonical_ref": "1.9.7",
        "db_passage_id": "d2491997-f074-4ce5-b186-20ff2dbd73ac",
        "tlg_bytes": (3124383, 3124753),
        "old_len": 278,
        "text": (
            "Ἐπεὶ δ' οὖν ὑπὲρ ἀρετῆς εἴρηται, μετὰ τοῦτ' ἂν εἴη σκεπτέον πότερον "
            "δυνατὴ παραγενέσθαι ἢ οὔ, ἀλλ' ὥσπερ Σωκράτης ἔφη, οὐκ ἐφ' ἡμῖν γενέσθαι "
            "τὸ σπουδαίους εἶναι ἢ φαύλους. εἰ γάρ τις, φησίν, ἐρωτήσειεν ὁντιναοῦν "
            "πότερον ἂν βούλοιτο δίκαιος εἶναι ἢ ἄδικος, οὐθεὶς ἂν ἕλοιτο τὴν "
            "ἀδικίαν."
        ),
    },
    "passage_arist_mm_1_28_1": {
        "canonical_ref": "1.28.1",
        "db_passage_id": "c1bef3d7-a1c1-437f-8c37-f4b7a154583b",
        "tlg_bytes": (3155536, 3155865),
        "old_len": 264,
        "text": (
            "Σεμνότης δέ ἐστιν αὐθαδείας ἀνὰ μέσον τε καὶ ἀρεσκείας, ἔστιν δὲ περὶ "
            "τὰς ἐντεύξεις. ὅ τε γὰρ αὐθάδης τοιοῦτός ἐστιν οἷος μηθενὶ ἐντυχεῖν μηδὲ "
            "διαλεγῆναι [ ἀλλὰ τοὔνομα ἔοικεν ἀπὸ τοῦ τρόπου κεῖσθαι· ὁ γὰρ αὐθάδης "
            "αὐτοάδης τις ἐστίν, ἀπὸ τοῦ αὐτὸς αὑτῷ ἀρέσκειν"
        ),
    },
    "passage_arist_mm_2_6_5": {
        "canonical_ref": "2.6.5",
        "db_passage_id": "4624f631-8611-47f4-ae76-84fe2264fbf5",
        "tlg_bytes": (3199774, 3200238),
        "old_len": 364,
        "text": (
            "Ἀλλ' ἆρά γε ἐπιστήμη μὲν οὔ, δόξα δέ; ἀλλ' εἰ δόξαν ἔχει ὁ ἀκρατής, οὐκ "
            "ἂν εἴη ψεκτός. εἰ γὰρ φαῦλόν τι πράττει μὴ ἀκριβῶς εἰδὼς ἀλλὰ δοξάζων, "
            "συγγνώμην ἄν τις ἀποδοίη προσθέσθαι τῇ ἡδονῇ καὶ πρᾶξαι τὰ φαῦλα, μὴ "
            "ἀκριβῶς εἰδότα ὅτι [οὐ] φαῦλα εἰσίν, ἀλλὰ δοξάζοντα· οἷς δέ γε συγγνώμην "
            "ἔχομεν, τούτους οὐ ψέγομεν· ὥστε ὁ ἀκρατής, εἴπερ δόξαν ἔχει, οὐκ ἔσται "
            "ψεκτός."
        ),
    },
    "passage_arist_mm_2_10_7": {
        "canonical_ref": "2.10.7",
        "db_passage_id": "6b2b6ffe-47d8-4ae8-a693-feb71bbbbf65",
        "tlg_bytes": (3240879, 3241071),
        "old_len": 149,
        "text": (
            "τὴν δὲ χρῆσιν καὶ τὴν ἐνέργειαν τούτων οὐκ ἔστι ταύτης τῆς πραγματείας "
            "τὸ παραδιδόναι· οὐδὲ γὰρ ἄλλη ἐπιστήμη οὐδεμία τὴν χρῆσιν παραδίδωσιν, "
            "ἀλλὰ τὴν ἕξιν."
        ),
    },
    "passage_arist_mm_2_11_1": {
        "canonical_ref": "2.11.1",
        "db_passage_id": "5f3d3682-3143-4fa4-bf96-b27af166a427",
        "tlg_bytes": (3241075, 3241355),
        "old_len": 195,
        "text": (
            "Ἐφ' ἅπασι δὲ τούτοις ὑπὲρ φιλίας ἀναγκαῖόν ἐστιν εἰπεῖν, τί ἐστιν καὶ ἐν "
            "τίσι καὶ περὶ τί· ἐπειδὴ γὰρ ὁρῶμεν παρὰ πάντα τὸν βίον παρατείνουσαν "
            "καὶ ἐν παντὶ καιρῷ, καὶ οὖσαν ἀγαθόν, συμπαραληπτέα ἂν εἴη πρὸς τὴν "
            "εὐδαιμονίαν."
        ),
    },
    "passage_arist_mm_2_11_2": {
        "canonical_ref": "2.11.2",
        "db_passage_id": "2fbcb04a-10c5-4a5f-b6f5-fdb506821815",
        "tlg_bytes": (3241359, 3241933),
        "old_len": 443,
        "text": (
            "Πρῶτον μὲν οὖν ἴσως ἃ ἀπορεῖται καὶ ζητεῖται, βέλτιον διελθεῖν. πότερον "
            "γάρ ἐστιν ἡ φιλία ἐν τοῖς ὁμοίοις, ὥσπερ δοκεῖ καὶ λέγεται; καὶ γὰρ "
            "κολοιός φασι παρὰ κολοιὸν ἱζάνει, καὶ αἰεί τοι τὸν ὅμοιον ἄγει θεὸς ὡς "
            "τὸν ὅμοιον. φασὶν δὲ καὶ κυνός ποτε ἀεὶ καθευδούσης ἐπὶ τῆς αὐτῆς "
            "κεραμῖδος, ἐρωτηθέντα τὸν Ἐμπεδοκλέα, διὰ τί ποτε ἡ κύων ἐπὶ τῆς αὐτῆς "
            "κεραμῖδος καθεύδει, εἰπεῖν ὅτι ἔχει τι τῇ κεραμῖδι ὅμοιον ἡ κύων, ὡς διὰ "
            "τὸ ὅμοιον τὴν κύνα φοιτῶσαν."
        ),
    },
    "passage_arist_mm_2_11_3": {
        "canonical_ref": "2.11.3",
        "db_passage_id": "f6bda576-14fc-4043-9a92-764e5299e5d6",
        "tlg_bytes": (3241935, 3242318),
        "old_len": 301,
        "text": (
            "πάλιν δ' αὖ δοκεῖ ἄλλοις τισὶν ἐν τοῖς ἐναντίοις μᾶλλον ἐγγίνεσθαι ἡ "
            "φιλία. ἐρᾷ μὲν γάρ, φασίν, ὄμβρου γαῖα, ὅταν ξηρὸν πέδον· τὸ δὴ "
            "ἐναντίον, φασίν, τῷ ἐναντίῳ βούλεσθαι φίλον εἶναι. ἐν μὲν γὰρ τοῖς "
            "ὁμοίοις οὐδὲ ἐνδέχεσθαι γίνεσθαι. τὸ γὰρ ὅμοιον, φασίν, τοῦ ὁμοίου οὐδὲν "
            "προσδεῖται, καὶ τὰ τοιαῦτα δή."
        ),
    },
    "passage_arist_mm_2_11_6": {
        "canonical_ref": "2.11.6",
        "db_passage_id": "0142f61c-acaa-4677-b9c3-e8c89ea89166",
        "tlg_bytes": (3242749, 3243140),
        "old_len": 302,
        "text": (
            "Πρῶτον μὲν οὖν διοριστέον ἂν εἴη ὑπὲρ φιλίας ποίας σκοποῦμεν. ἔστι γάρ, "
            "ὡς οἴονται, φιλία καὶ πρὸς θεὸν καὶ τὰ ἄψυχα, οὐκ ὀρθῶς. τὴν γὰρ φιλίαν "
            "ἐνταῦθά φαμεν εἶναι οὗ ἐστὶ τὸ ἀντιφιλεῖσθαι, ἡ δὲ πρὸς θεὸν φιλία οὔτε "
            "ἀντιφιλεῖσθαι δέχεται, οὔθ' ὅλως τὸ φιλεῖν· ἄτοπον γὰρ ἂν εἴη εἴ τις "
            "φαίη φιλεῖν τὸν Δία"
        ),
    },
    "passage_arist_mm_2_11_9": {
        "canonical_ref": "2.11.9",
        "db_passage_id": "e31e3ae8-f964-4de5-b70a-7fa058b89c3d",
        "tlg_bytes": (3243697, 3243945),
        "old_len": 200,
        "text": (
            "βουλητὸν μὲν γὰρ τὸ ἁπλῶς ἀγαθόν, βουλητέον δὲ τὸ ἑκάστῳ ἀγαθόν· οὕτω "
            "καὶ φιλητὸν μὲν τὸ ἁπλῶς ἀγαθόν, φιλητέον δὲ τὸ αὑτῷ ἀγαθόν, ὥστε τὸ μὲν "
            "φιλητέον καὶ φιλητόν, τὸ δὲ φιλητὸν οὐκ ἔστι φιλητέον."
        ),
    },
    "passage_arist_mm_2_11_10": {
        "canonical_ref": "2.11.10",
        "db_passage_id": "bb74a2e7-9476-4680-af94-a967c57fc312",
        "tlg_bytes": (3243949, 3244289),
        "old_len": 229,
        "text": (
            "Ἐνταῦθα οὖν ἐστιν καὶ διὰ τὸ τοιοῦτον ἡ ἀπορία, πότερόν ἐστιν ὁ "
            "σπουδαῖος τῷ φαύλῳ φίλος ἢ οὔ. συνῆπται γάρ πως τἀγαθῷ τὸ αὐτῷ ἀγαθὸν "
            "καὶ τὸ φιλητέον τῷ φιλητῷ, ἔχεται δὲ καὶ ἀκολουθεῖ τῷ ἀγαθῷ καὶ τὸ ἡδὺ "
            "εἶναι καὶ τὸ συμφέρον."
        ),
    },
    "passage_arist_mm_2_11_23": {
        "canonical_ref": "2.11.23",
        "db_passage_id": "e394ff02-2c45-451a-bb23-93d4d39a5777",
        "tlg_bytes": (3247932, 3248209),
        "old_len": 221,
        "text": (
            "Συμβαίνει δὲ καὶ ἀγανακτεῖν, ὅταν φαύλοις ἐντύχωσιν τοῖς φίλοις, καὶ "
            "θαυμάζειν· ἔστι δὲ οὐδὲν ἄτοπον. ὅταν γὰρ ἡ φιλία λάβῃ τὴν ἡδονὴν ἀρχήν, "
            "δι' ἣν φίλοι εἰσίν, ἢ τὸ συμφέρον, ἅμα ταῦτ' ἀπολείπει καὶ ἡ φιλία οὐ "
            "διαμένει."
        ),
    },
    "passage_arist_mm_2_11_28": {
        "canonical_ref": "2.11.28",
        "db_passage_id": "63f76dae-671a-4880-ad96-615beb5ee667",
        "tlg_bytes": (3249738, 3250301),
        "old_len": 439,
        "text": (
            "Ἐπεὶ δὲ διῄρηνται αἱ φιλίαι εἰς τρία εἴδη, καὶ ἐν ταύταις ἠπορεῖτο, "
            "πότερον ἐν ἰσότητι ἡ φιλία ἐγγίνεται ἢ ἐν ἀνισότητι· ἔστιν οὖν κατ' "
            "ἀμφότερα. ἡ μὲν γὰρ καθ' ὁμοιότητα ἡ τῶν σπουδαίων καὶ ἡ τελεία φιλία· ἡ "
            "δὲ κατ' ἀνομοιότητα ἡ κατὰ τὸ συμφέρον. τῷ γὰρ εὐπόρῳ ὁ πένης διὰ τὴν "
            "ἔνδειαν ὧν ὁ πλούσιος εὐπορεῖ φίλος ἐστί, καὶ τῷ σπουδαίῳ ὁ φαῦλος διὰ "
            "ταὐτό· διὰ γὰρ τὴν ἔνδειαν τὴν τῆς ἀρετῆς, παρ' οὗ οἴεται αὑτῷ ἔσεσθαι, "
            "διὰ τοῦτο τούτῳ φίλος."
        ),
    },
    "passage_arist_mm_2_11_29": {
        "canonical_ref": "2.11.29",
        "db_passage_id": "b3c786d2-1375-4d27-9ec4-eaf1bc33e6dc",
        "tlg_bytes": (3250303, 3250633),
        "old_len": 260,
        "text": (
            "γίνεται οὖν ἐν τοῖς ἀνομοίοις φιλία κατὰ τὸ συμφέρον· διὸ καὶ Εὐριπίδης "
            "ἐρᾷ μὲν ὄμβρου γαῖ', ὅταν ξηρὸν πέδον· ὡς ἐναντίοις οὖσιν τούτοις "
            "ἐγγίγνεται φιλία ἡ διὰ τὸ συμφέρον. καὶ γὰρ εἰ θέλεις τὰ ἐναντιώτατα "
            "ποιῆσαι πῦρ καὶ ὕδωρ, ταῦτα ἀλλήλοις χρήσιμα εἰσίν."
        ),
    },
    "passage_arist_mm_2_11_32": {
        "canonical_ref": "2.11.32",
        "db_passage_id": "94918239-7a51-4b0d-adb8-3d862eb6f86d",
        "tlg_bytes": (3251444, 3251813),
        "old_len": 270,
        "text": (
            "οὐ μὴν ἀλλ' ἐπὶ μὲν τῶν τοιούτων ὧν τὸ αὐτό ἐστι τέλος τῆς φιλίας, οἷον "
            "εἰ ἀμφότεροι κατὰ τὸ συμφέρον ἀλλήλοις φίλοι ἢ κατὰ τὸ ἡδὺ ἢ κατ' "
            "ἀρετήν, εὔδηλος ἡ ἔλλειψις ἡ παρὰ τοῦ ἑτέρου, ἐὰν οὖν πλείω ἀγαθὰ σύ μοι "
            "ποιῇς ἢ ἐγὼ σοί, οὐδ' ἀμφισβητῶ ἔτι μὴ οὐ δεῖν σε μᾶλλον ὑπ' ἐμοῦ "
            "φιλεῖσθαι"
        ),
    },
    "passage_arist_mm_2_17_2": {
        "canonical_ref": "2.17.2",
        "db_passage_id": "2ebd3751-07a1-43cb-bda7-1dfad88409d8",
        "tlg_bytes": (3269822, 3270278),
        "old_len": 362,
        "text": (
            "ἐν δὲ ἀνίσοις φίλοις οὐκ ἔστι τὸ ἴσον, ἔστι δὲ ἡ πατρὸς πρὸς υἱὸν φιλία "
            "ἐν ἀνίσῳ, ὁμοίως ἡ γυναικὸς πρὸς ἄνδρα ἢ οἰκέτου πρὸς δεσπότην, καὶ ὅλως "
            "δὲ χείρονος καὶ βελτίονος. οὐχ ἕξουσιν δὴ τὰ τοιαῦτα ἐγκλήματα. ἀλλ' ἐν "
            "τοῖς ἴσοις φίλοις καὶ ἐν τῇ [ τοι] αύτῃ φιλίᾳ τὸ τοιοῦτον ἔγκλημα. ὥστε "
            "σκεπτέον ἂν εἴη τὸ πῶς δεῖ χρῆσθαι φίλῳ ἐν τῇ ἐν ἴσοις φίλοις φιλίᾳ."
        ),
    },
}

MAGNA_MORALIA_UNRESOLVED: list[tuple[str, str]] = [
    (
        "passage_arist_mm_2_11_5",
        "no clean 4-word window of this node survives uniquely in TLG0086, so its "
        "position in the Magna Moralia could not be fixed with certainty; flagged "
        "needs_reingestion, not rewritten",
    ),
]

# The 395 Magna Moralia nodes that do NOT show `??` carry the same OCR's silent
# letter substitutions. They are reported in the plan and deliberately left
# alone: rewriting 395 passages wholesale is a re-ingestion, not a repair wave.
MAGNA_MORALIA_SILENT_OCR_COUNT = 395


# ===========================================================================
# LOT 1b — single-node surgical repairs (verbatim token substitution)
# ===========================================================================
#
# These three nodes are otherwise faithful to a good edition (difflib ratio
# against the TLG text is 0.99+), and their editorial apparatus — quotation
# marks, elision marks — is worth keeping. So rather than swapping the whole
# description for the TLG decoding, only the corrupt token is replaced, with the
# TLG reading, and the byte anchor of the enclosing passage is recorded.

TOKEN_REPAIRS: list[dict] = [
    {
        "node": "passage_just_apol1_40",
        "old": "(??) αρέστησαν",
        "new": "παρέστησαν",
        "tlg": "TLG0645 (Justinus Martyr) bytes 61989-65745, 1 Apol. 40",
        "why": "Ps. 2:2 LXX as quoted by Justin; TLG reads 'παρέστησαν οἱ "
        "βασιλεῖς τῆς γῆς'. The OCR lost the initial pi.",
    },
    {
        "node": "passage_just_apol1_40",
        "old": "ἐν τρ (??) μῳ",
        "new": "ἐν τρόμῳ",
        "tlg": "TLG0645 (Justinus Martyr) bytes 61989-65745, 1 Apol. 40",
        "why": "Ps. 2:11 LXX; TLG reads 'ἀγαλλιᾶσθε αὐτῷ ἐν τρόμῳ'.",
    },
    {
        "node": "passage_plotinus_vi_9_136",
        "old": "ʽ??’αιρεῖ",
        "new": "διαιρεῖ",
        "tlg": "TLG2000 (Plotinus) bytes 885839-886887, Enn. V.1.9",
        "why": "TLG reads 'Τῷ δὲ Ἐμπεδοκλεῖ τὸ νεῖκος μὲν διαιρεῖ, ἡ δὲ φιλία τὸ ἕν'.",
    },
    {
        "node": "passage_plotinus_vi_9_136",
        "old": "τοσἁ??’τα",
        "new": "τοσαῦτα",
        "tlg": "TLG2000 (Plotinus) bytes 885839-886887, Enn. V.1.9",
        "why": "TLG reads 'καὶ τοσαῦτα, ὁπόσαι ἐν οὐρανῷ σφαῖραι'.",
    },
]

# passage_meth_dla_41 was listed by the audit with the Magna Moralia group. It is
# not corrupt Greek at all: it is the GCS critical apparatus (German: "u. verb.",
# "nach Gifford", "mit dem Vorhergehenden"; sigla C D E S Ph). It is handled by
# LOT 5's apparatus rule, not here.


# ===========================================================================
# LOT 2 — nine "Simplicius" passages that are Theophrastus, Historia Plantarum
# ===========================================================================
#
# ``passage_simpl_in_ench_1..9`` are labelled "Simplicius, In Epicteti
# Enchiridion Commentarius" and carry ``urn:cts:greekLit:tlg0093.tlg001…``.
# TLG0093.IDT reads: author TLG0093 = Theophrastus, work 001 = Historia
# plantarum. The URN is therefore honest and the label is the lie: the text is
# botany, with no bearing on free will.
#
# Attested on disk:
#   _1  "Τῶν φυτῶν τὰς διαφορὰς καὶ τὴν ἄλλην φύσιν ληπτέον…"
#       = HP I.1.1, TLG0093 byte 100 (heading ΘΕΟΦΡΑΣΤΟΥ ΠΕΡΙ ΦΥΤΩΝ ΙΣΤΟΡΙΑΣ Α)
#   _6  "Περὶ μὲν οὖν δένδρων καὶ θάμνων εἴρηται πρότερον…"
#       = HP VI.1.1, TLG0093 byte 324364 (book marker Ζ)
#   _1  also mentions Μενέστωρ, the 5th-c. BCE botanist cited only by Theophrastus.
#
# The nodes are deleted rather than relabelled: an accidental slice of the
# Historia Plantarum has no place in this graph, and R2 forbids leaving a second
# identity for a text the corpus does not otherwise hold.

THEOPHRASTUS_MISFILED_NODES: list[str] = [
    "passage_simpl_in_ench_1",
    "passage_simpl_in_ench_2",
    "passage_simpl_in_ench_3",
    "passage_simpl_in_ench_4",
    "passage_simpl_in_ench_5",
    "passage_simpl_in_ench_6",
    "passage_simpl_in_ench_7",
    "passage_simpl_in_ench_8",
    "passage_simpl_in_ench_9",
]

THEOPHRASTUS_MISFILED_CORPUS_IDS: list[str] = [
    "0a9e2c6f-6408-4ac1-99d7-2e340b17f3dc",
    "adf1476c-cc07-44f9-97a0-92e69d1dd770",
    "0dc85dcf-6698-45ba-83f5-634fd4260872",
    "b5c0f678-29a0-4119-b09a-6584b1739328",
    "1ffd4bb9-c3eb-4a05-b336-7b958cfef6a2",
    "62a540c1-f348-48eb-97f9-c54af9f1272d",
    "5ffa617f-e3cf-4da6-9c86-c7c9202af981",
    "2edeccca-8665-44aa-aa90-42667cc0d58d",
    "66009fec-8ceb-4042-bf97-3e36e18bef90",
]

# The nine nodes hold exactly 18 edges: 9 `authored_by` -> person_simplicius_cilicia_490_560ce
# and 9 `part_of` -> work_simplicius_in_enchiridion. Both endpoints survive the
# deletion with other edges, so no orphan is created.
THEOPHRASTUS_EXPECTED_EDGE_COUNT = 18

SIMPLICIUS_WORK_NODE = "work_simplicius_in_enchiridion"
SIMPLICIUS_WORK_FLAG = {
    "needs_text_ingestion": True,
    "why": "The nine passages filed under this work were Theophrastus, Historia "
    "Plantarum (TLG0093.tlg001) and have been removed. Simplicius' commentary on "
    "the Enchiridion is now unrepresented in the corpus. The text to ingest is "
    "I. Hadot's edition (Simplicius, Commentaire sur le Manuel d'Épictète, CAG / "
    "Brill 1996; SC 500-503 for the French). Not ingested by this wave.",
}


# ===========================================================================
# LOT 3 — CTS URNs naming the wrong TLG author or work
# ===========================================================================
#
# Every id below was checked against AUTHTAB.DIR and the per-author .IDT work
# tables of the TLG E disc, not against memory.

TLG_AUTHOR_TABLE_EVIDENCE = {
    "tlg9857": "absent from AUTHTAB.DIR — no such TLG author exists",
    "tlg0007": "Plutarchus, Biogr. et Phil.",
    "tlg0094": "Pseudo-Plutarchus — but TLG0094.IDT holds only De fluviis, "
    "De musica, Placita philosophorum; NOT De fato",
    "tlg0338": "Sosiphanes, Trag.",
    "tlg0555": "Clemens Alexandrinus, Theol.",
    "tlg2042": "Origenes, Theol.",
    "tlg2959": "absent from the TLG E disc (its patristic coverage stops short "
    "of Methodius); it is the canonical TLG id used elsewhere in this graph "
    "(work_methodius_de_libero_arbitrio and 3 passage nodes already carry it)",
    "tlg0086": "Aristoteles Phil. et Corpus Aristotelicum",
    "tlg0093": "Theophrastus, Phil.",
}

# --- 3a. Pseudo-Plutarch, De fato -----------------------------------------
#
# 57 ``passage_plut_fat_*`` nodes carry ``urn:cts:greekLit:tlg9857.tlg062.perseus-grc1``.
# tlg9857 does not exist. The audit proposed tlg0094 (Pseudo-Plutarchus); the
# work table refutes that — TLG0094 does not contain De fato.
#
# TLG0007.IDT does, listed among the Moralia as work id 108:
#     "De fato [Sp.] (568b-574f)", the [Sp.] marking it spurious.
# (The decoding of the .IDT work-id bytes is corroborated by its neighbours:
#  067 = De liberis educandis [Sp.], 107 = De sera numinis vindicta,
#  109 = De genio Socratis — all matching the published TLG canon numbers.)
#
# Text attested: passage_plut_fat_1 reads "…εἱμαρμένη διχῶς καὶ λέγεται καὶ
# νοεῖται· ἡ μὲν γάρ ἐστιν ἐνέργεια ἡ δ' οὐσία", found once in TLG0007 at byte
# 6323294, inside the De fato section.
#
# The Perseus version suffix is dropped: `perseus-grc1` was part of the invented
# URN and no Perseus edition of tlg0007.tlg108 could be verified from disk.
# Better a work-level URN that resolves than a version-level one that lies.

# --- 3b. Methodius, De libero arbitrio ------------------------------------
#
# 97 ``passage_meth_dla_*`` nodes carry tlg0338.tlg307 (Sosiphanes, a tragedian —
# and work 307 is beyond anything a tragedian has). A further 14 carry
# tlg2042.tlg014, which TLG2042.IDT identifies as Origen's "Fragmenta in librum
# primum Regnorum (in catenis)". Both are wrong for Methodius.
#
# Content check: passage_meth_dla_1 opens "Ὁ μὲν Ἰθακήσιος γέρων κατὰ τὸν τῶν
# Ἑλλήνων μῦθον, τῆς Σειρήνων βουλόμενος ἀκοῦσαι ᾠδῆς…" — the Odysseus/Sirens
# proem of the De autexousio. The graph already holds tlg2959.tlg002 on
# work_methodius_de_libero_arbitrio and on three passage nodes.

# --- 3c. Origen, Philocalia -----------------------------------------------
#
# 57 ``passage_origen_philocalia_*`` nodes carry tlg2042.tlg028, which
# TLG2042.IDT identifies as "Commentariorum series in evangelium Matthaei".
# The Philocalia is tlg2042.tlg019, "Philocalia sive Ecloga de operibus Origenis
# a Basilio et Gregorio Nazianzeno facta (cap. 1-27)". The author is right, the
# work number is not. (This item is an addition to the audit's list, found while
# checking the tlg2042 family.)

URN_FAMILY_REWRITES: list[dict] = [
    {
        "name": "ps_plutarch_de_fato",
        "old_prefix": "urn:cts:greekLit:tlg9857.tlg062.perseus-grc1",
        "new_prefix": "urn:cts:greekLit:tlg0007.tlg108",
        "expected": 57,
        "id_prefix": "passage_plut_fat",
        "why": "tlg9857 is not a TLG author id; De fato [Sp.] is TLG0007 work "
        "108 per TLG0007.IDT, text attested at TLG0007 byte 6323294",
    },
    {
        "name": "methodius_sosiphanes",
        "old_prefix": "urn:cts:greekLit:tlg0338.tlg307.perseus-grc1",
        "new_prefix": "urn:cts:greekLit:tlg2959.tlg002",
        "expected": 97,
        "id_prefix": "passage_meth_dla",
        "why": "tlg0338 is Sosiphanes the tragedian; Methodius' De autexousio is "
        "tlg2959.tlg002, already used by this graph's own work node",
    },
    {
        "name": "methodius_under_origen",
        "old_prefix": "urn:cts:greekLit:tlg2042.tlg014",
        "new_prefix": "urn:cts:greekLit:tlg2959.tlg002",
        "expected": 14,
        "id_prefix": "passage_meth_dla",
        "why": "tlg2042.tlg014 is Origen's Fragmenta in librum primum Regnorum, "
        "not Methodius",
    },
    {
        "name": "origen_philocalia",
        "old_prefix": "urn:cts:greekLit:tlg2042.tlg028",
        "new_prefix": "urn:cts:greekLit:tlg2042.tlg019",
        "expected": 57,
        "id_prefix": "passage_origen_philocalia",
        "why": "tlg2042.tlg028 is Origen's Commentariorum series in Matthaeum; "
        "the Philocalia is tlg2042.tlg019 per TLG2042.IDT",
    },
]

# --- 3d. THE AUDIT HAD THIS ONE BACKWARDS ---------------------------------
#
# The audit reported "51 passage_clement_* nodes wrongly carrying Origen's
# tlg2042" and proposed rewriting them to Clement (tlg0555). That would have
# destroyed a correct URN.
#
# passage_clement_protr_1 reads:
#   "…Ἀμβρόσιε θεοσεβέστατε καὶ Πρωτόκτητε εὐσεβέστατε…"
# Ambrose and Protoctetus are the dedicatees of Origen's Exhortatio ad
# martyrium. The phrase is found ONCE in the whole of TLG2042, at byte 2355789.
# passage_clement_protr_26 is the Maccabean martyrs before Antiochus (Exh. mart.
# 22-27); passage_clement_protr_51 is the closing paragraph ("Ταῦτά μοι κατὰ τὸ
# δυνατὸν … πρὸς τὸν παρόντα ἀγῶνα χρήσιμα") — and the Exhortatio has exactly 51
# chapters, matching the 51 nodes one for one.
#
# TLG2042.IDT: work 007 = "Exhortatio ad martyrium". The URN tlg2042.tlg007 on
# these nodes is CORRECT. What is wrong is the id, the label, the author, the
# work title and both edges, which all say Clement's Protrepticus.
#
# This is the incident named in docs/development/ingestion-rules.md under R3b —
# recorded there in the opposite direction. The direction is settled here by the
# text.

EXHORTATIO_REATTRIBUTION = {
    "id_prefix": "passage_clement_protr_",
    "expected": 51,
    "urn": "urn:cts:greekLit:tlg2042.tlg007",
    "wrong_author": "Clement of Alexandria",
    "right_author": "Origen of Alexandria",
    "wrong_work_title": "Protrepticus",
    "right_work_title": "Exhortatio ad martyrium",
    "wrong_person_node": "person_clement_alexandria",
    "right_person_node": "person_origen_alexandria_185_254ce_s9t0u1v2",
    "wrong_work_node": "work_clement_protrepticus",
    "right_work_node": "work_origen_exhortation_martyrdom",
    "label_template": "Origen, Exhortation to Martyrdom {n}",
    "ref_template": "Exh. mart. {n}",
    "evidence": "Ἀμβρόσιε θεοσεβέστατε καὶ Πρωτόκτητε εὐσεβέστατε — unique in "
    "TLG2042 at byte 2355789, in Exhortatio ad martyrium (TLG2042.IDT work 007)",
}

# work_clement_protrepticus loses all 51 of its passages and is left empty.
CLEMENT_PROTREPTICUS_FLAG = {
    "node": "work_clement_protrepticus",
    "needs_text_ingestion": True,
    "why": "The 51 passages filed under Clement's Protrepticus were in fact "
    "Origen's Exhortatio ad martyrium and have been re-pointed. Clement's "
    "Protrepticus (TLG0555.tlg001) is now unrepresented in the corpus.",
}

# The 51 node ids still read `passage_clement_protr_*` while holding Origen.
# Renaming them touches 51 nodes and 102 edge endpoints and no other reference
# (checked: the strings occur nowhere else in nodes.jsonl, edges.jsonl or
# passages.jsonl beyond the nodes' own id/node_id fields and the edges). It is
# a WARN under R9, not a BLOCK, and it changes primary keys that production
# already serves, so this wave records the debt instead of renaming.
EXHORTATIO_ID_DEBT = (
    "passage_clement_protr_1..51 should be renamed passage_origen_exh_mart_1..51 "
    "(R9, honest ids). Deferred: 51 node ids + 102 edge endpoints, no other "
    "references, but production kg_nodes keys change."
)


# ===========================================================================
# LOT 4 — pre-Unicode Greek fonts, OCR'd as pseudo-Latin
# ===========================================================================
#
# 20 blocks (7 KG nodes, 13 corpus lines) where a legacy Greek font was OCR'd as
# a mixture of Latin letters and stray Greek glyphs:
#     "dvo πίϑους, xbv ukv eva xαxωv, tdv ds ἔτεϱοv έἀωv"   (Boethius, Cons. II.pr.2)
# — the Homeric jar-quotation of Il. 24.527-528 as Boethius gives it. The intended
# reading is not written down here: it has not been read off a critical edition,
# and a plausible reconstruction is exactly what this project forbids.
#
# regreek 0.7.2 was tested and does NOT apply. Its decoders map a *uniform*
# legacy-font byte stream; this text is post-OCR debris in which the Latin
# surroundings are real Latin. Its own detector is unable to separate the two:
#
#   >>> regreek.detect_encoding("Nonne adulescentulus dvo πίϑους, xbv ukv eva …")
#   [graeca 0.678, graeca2 0.678, odyssea 0.678, symbolgreek2 0.678]   (a 4-way tie)
#   >>> regreek.decode_text(same, "graeca").text
#   'Νοννε αδυλεσχεντυλυς δό πίϑους ξβ́ ύκ έα xαxωv τδ́ δς ἔτεϱοv έἀωv ιν Ιόις λιμινε'
#
# — the Latin has been Greekified and the Greek is still wrong. Nothing is written.
#
# Nor could the readings be attested from disk: no critical edition of Boethius'
# Consolatio, Lactantius' Divinae Institutiones or Cassian's Conlationes exists
# under ~/Desktop/DOCTORAT/Doctorat SHAL/, and none of the three authors is on
# the TLG E disc (all three write in Latin).
#
# Action: flag only.

PRE_UNICODE_KG_NODES: list[tuple[str, str]] = [
    ("passage_boeth_cons_7", "Cons. 1.M3-1.M4 — 'an ὄνος λύϱας?'"),
    ("passage_boeth_cons_23", "Cons. 2.P2 — 'dvo πίϑους, xbv ukv eva xαxωv'"),
    ("passage_boeth_cons_53", "Cons. 3.P5-3.P6 — tragic quotation, 'ὦ δ…'"),
    ("passage_boethius_cons_7", "Cons. 7 (Fate Under Foot) — same block"),
    ("passage_boethius_cons_23", "Cons. 23 (Memory of Happiness) — same block"),
    ("passage_boethius_cons_23_en", "Cons. 23 English node carrying the same block"),
    ("passage_boethius_cons_53", "Cons. 53 (Conquer Your Passions) — same block"),
]

PRE_UNICODE_CORPUS_IDS: list[tuple[str, str]] = [
    ("0cfa5c41-f478-437a-a9ca-bb38e3b0ad0d", "Cassian, Conl. 13.5.2"),
    ("382e1f75-9c09-40af-8922-396d10ea506a", "Cassian, Conl. 13.5.3"),
    ("0d1f6cea-bc0a-5832-a3e8-0badd762e546", "Boethius, Cons. 2.P2-2.P3"),
    (
        "5722f504-f0a1-4a50-8035-1fb0039016f0",
        "Boethius, Cons. 2.P2-2.P3 (duplicate line)",
    ),
    ("17047ea3-04bf-417f-b2b8-74c2d1ffaf21", "Boethius, Cons. 1.M3-1.M4"),
    ("a01d9244-5f1a-4f1c-bb56-b730b3b104ed", "Boethius, Cons. 3.P5-3.P6"),
    ("60f5b615-3474-4d2f-a842-e1dd6cce214b", "Lactantius, Div. Inst. 6.24.1-8"),
    ("73c5c0d8-f6e6-49e8-8d28-8099dd864831", "Lactantius, Div. Inst. 4.15.9-16"),
    ("7ba78a07-4846-4451-bbdd-87c624f5ae8a", "Lactantius, Div. Inst. 1.5.1-7"),
    ("8dfac733-cf8f-4a1b-a068-8a6a98083630", "Lactantius, Div. Inst. 1.22.16-24"),
    ("96a955b4-fd48-4f2a-ba53-5b23985cfeac", "Lactantius, Div. Inst. 1.7.8-13"),
    ("a2a157bb-86dd-4cf1-bab5-ae4777c852c8", "Lactantius, Div. Inst. 2.14.1-8"),
    ("b8e4849d-a1b1-47aa-8522-28a57eef7708", "Lactantius, Div. Inst. 4.15.17-24"),
]

PRE_UNICODE_FLAG = {
    "pre_unicode_font": True,
    "needs_reocr": True,
    "why": "Greek in this passage was set in a pre-Unicode font and OCR'd as "
    "pseudo-Latin. regreek 0.7.2 cannot decode it (mixed Latin/Greek input; "
    "4-way tie between graeca/graeca2/odyssea/symbolgreek2 and the Latin is "
    "Greekified). No critical edition of the work is available on disk. The "
    "Greek is left as it stands and marked unreliable rather than guessed.",
}

# The corpus JSONL has no metadata column, so a corpus line cannot carry a flag.
# Only the KG nodes are stamped; the corpus ids are listed here and in the plan
# so the re-OCR job knows its worklist.


# ===========================================================================
# LOT 5 — passages that lie about their language
# ===========================================================================
#
# The applier does NOT trust these lists. Each id below is a *candidate*; the
# language is re-detected from the node's live text at apply time and the write
# only happens when detection and candidacy agree. That is what caught 5a.

# --- 5a. "221 lat nodes with no Latin" — 215 of them are a false positive ---
#
# Live measurement over the audit's own 221 ids: 215 contain Latin. The shape is
#     "<English lead-in>.  LATIN TEXT (verified from database, passage_id: …): <Latin>"
# so the audit's language detector, reading only the head of the field, saw
# English. `language: lat` is correct for these; what they need is a marker that
# the field is a composite, not a marker that the language is wrong.
# Only 6 have no Latin at all.
LAT_WITHOUT_LATIN_CANDIDATES_COUNT = 221
LAT_WITHOUT_LATIN_RULE = {
    "requires_declared": ("lat", "Latin"),
    "requires_zero_latin": True,
    "set_language": "eng",
    "set_flags": {"needs_text_ingestion": True},
    "why": "declared lat, but the field holds English commentary with no Latin "
    "text; the node is presented as primary text and is not",
}
COMPOSITE_TEXT_RULE = {
    "requires_declared": ("lat", "Latin"),
    "requires_some_latin": True,
    "set_flags": {"content_kind": "commentary_plus_text"},
    "why": "English commentary followed by the Latin text in the same field; the "
    "language declaration is right, the field is composite",
}

# --- 5b. "121 _en nodes holding the untranslated source" — already fixed ----
#
# All 121 already carry `passage_role: untranslated_duplicate` and the original's
# language, applied by apply_2026_08_16_deep_audit_structural.py. Live check:
#   118 language=lat + untranslated_duplicate, 3 language=grc + untranslated_duplicate,
#   0 still declaring language=eng.
# The audit re-flagged them from the `_en` suffix, not from the current metadata.
# No-op, recorded so it is not re-opened.
EN_UNTRANSLATED_ALREADY_FIXED = 121

# --- 5c. 86 grc nodes with no Greek ---------------------------------------
#
# Live breakdown of the audit's 86 ids:
#   47  passage_origen_philocalia_2[3-7]_*   French (SC translation), language=grc
#   23  passage_origen_pa_3_1_*              French (SC translation), language=grc-lat
#    6  passage_meth_dla_*                   German — GCS apparatus, handled by 5d
#    2  passage_origen_com_rm_7_16*          Latin (Rufinus)
#    8  others                               DO contain Greek (26-41 characters):
#                                            audit false positive, skipped
#
# The 23 De principiis III.1 nodes have a Greek twin: the graph holds
# passage_origen_philocalia_21_1..24 with the *identical* cts_urn
# (urn:cts:greekLit:tlg2042.tlg002:3.1.N) and real Greek. The pointer is
# therefore resolved by URN match at apply time, not by a hard-coded pairing,
# and R7 is satisfied (role=translation, original resolves, text differs).
#
# The 47 Philocalia 23-27 nodes have no Greek twin in the graph. Setting
# `passage_role: translation` on them would create a fresh R7 BLOCK (a
# translation whose original does not resolve), so they keep role `original`,
# get the honest `language: fra`, and are marked
# `content_kind: modern_translation` + `needs_text_ingestion`.

GRC_WITHOUT_GREEK_RULE = {
    "requires_declared": ("grc", "grc-lat", "Greek"),
    "requires_zero_greek": True,
    "detected_to_language": {"fra": "fra", "lat": "lat", "deu": "deu"},
    "translation_pairing": {
        "match_on": "cts_urn",
        "require_target_language": "grc",
        "require_text_differs": True,
    },
    "why": "declared as Greek while holding a modern translation or a Latin "
    "witness; the language claim is withdrawn and, where the Greek original is "
    "in the graph under the same CTS URN, the node is linked to it as its "
    "translation",
}

GRC_WITHOUT_GREEK_EXPECTED = {
    "fra_with_greek_twin": 23,
    "fra_without_greek_twin": 47,
    "lat": 2,
    "deu_apparatus": 6,
    "skipped_false_positive": 8,
}

# --- 5d. the GCS critical apparatus ingested as if it were Methodius -------
#
# passage_meth_dla_41 is representative:
#   "…κακὸς ὑπάρχει < D Ι κακὸς < C ι ἡ ἐνέργεια C Ι ἃ δὲ … S 13 λαμβάνειν S
#    u. verb. ἤρξατο mit dem Vorhergehenden κἀκεῖνος] ἐκεῖνος S …"
# That is Bonwetsch's apparatus criticus from the GCS edition — sigla C D E S Ph,
# German editorial abbreviations, Armenian (Ezn) and Slavonic witnesses.
#
# The audit found 22. A rule requiring >=3 German function words AND an apparatus
# marker (»…«, " < ", "u. ", "wohl", "Ezn", a siglum next to a line number)
# matches 82 of the 97 passage_meth_dla_N nodes. Only ~15 hold real content.
# The rule is applied, not the list; the dry run reports what it matched.
APPARATUS_RULE = {
    "id_pattern": r"^passage_meth_dla_\d+$",
    "min_german_words": 3,
    "marker_pattern": r"»|\s<\s|\bu\.\s|\bwohl\b|\bEzn\b|\bS\b\s*\d",
    "set_flags": {
        "content_kind": "apparatus_gcs",
        "passage_role": "apparatus",
        "needs_text_ingestion": True,
    },
    "set_language": "deu",
    "why": "this node holds the German critical apparatus of the GCS edition "
    "(Bonwetsch), not Methodius' text; it was declared grc and typed as an "
    "original passage, so retrieval could return an apparatus entry as if it "
    "were the ancient author",
}
APPARATUS_AUDIT_COUNT = 22
APPARATUS_RULE_LIVE_COUNT = 82

# --- 5e. batches deliberately left alone ----------------------------------
#
# 279 "grc but mostly English" and 30 "grc but French": these are structured
# multilingual nodes ("**Reference:** … **Original Greek:** … **English:** …").
# They DO contain the Greek they claim. Rewriting `language` on them would be
# wrong; what they need is a `content_kind: structured_multilingual` marker,
# which is a schema decision beyond this wave's brief.
#
# 76 "shell" person/work nodes declared `language: Greek` with English
# descriptions: on a person node `metadata.language` means the language the
# author wrote in, not the language of the description. Not a defect. The only
# real issue is vocabulary drift ("Greek" vs "grc"), reported, not fixed.
DEFERRED_LANGUAGE_BATCHES = {
    "structured_multilingual_grc_eng": 279,
    "structured_multilingual_grc_fra": 30,
    "shell_nodes_language_greek": 76,
}


# ===========================================================================
# LOT 6 — encoding
# ===========================================================================
#
# 6a. 45 lines of edges.jsonl are not NFC. All 45 carry the defect in exactly one
# field, `metadata.provenance.source`, and all 45 are the same bibliographic
# string ("Jean Voelke - L'idée de volonté …") whose accented characters are
# stored decomposed. Normalising the whole line to NFC is safe: Greek text is not
# involved, and NFC is the corpus-wide convention.
NFC_EDGE_EXPECTED = 45
NFC_EDGE_FIELD = "metadata.provenance.source"

# 6b. Greek elision apostrophes in edge metadata: NOTHING TO DO.
# A sweep of every string field of every edge found U+2019 only —
#   63 metadata.provenance.source, 8 metadata.original_citation,
#    4 metadata.note, 1 metadata.furst_source, 1 metadata.scope
# — and zero occurrences of U+1FBD (koronis), U+1FBF (psili) or U+02BC
# (modifier letter apostrophe). The elision mark is already unified on U+2019.
ELISION_ALREADY_UNIFIED = {
    "u2019": 77,
    "u1fbd": 0,
    "u1fbf": 0,
    "u02bc": 0,
}


# ===========================================================================
# LOT 7 — Plotinus: 709 fragment numbers presented as Ennead citations
# ===========================================================================
#
# The defect is intact — no earlier wave touched it. All 709
# ``passage_plotinus_vi_9_N`` nodes carry:
#     cts_urn      urn:cts:greekLit:tlg2000.tlg001.perseus-grc1:1
#     canonical_ref Enn. VI.9.N          (N = 1 … 709)
#     work_title    Enneades
# i.e. every one of them claims to be Ennead VI.9, a tractate of 11 chapters.
#
# What they actually are: consecutive slices of the Enneads in reading order.
# Ten of them were anchored in TLG2000 (Plotinus) by unique text search; the byte
# offsets rise monotonically with N, and the Ennead number read from the nearest
# preceding TLG citation block is:
#
#     node   1   byte  733557   Ennead IV
#     node  50   byte  788447   Ennead IV
#     node 136   byte  885857   Ennead V     (text = Enn. V.1.9, the doxography
#                                             of Anaxagoras/Heraclitus/Empedocles)
#     node 200   byte  960741   Ennead V
#     node 305   byte 1083694   Ennead VI
#     node 306   byte 1084660   Ennead VI
#     node 400   byte 1193081   Ennead VI
#     node 500   byte 1306440   Ennead VI
#     node 600   byte 1423586   Ennead VI
#     node 709   byte 1548122   Ennead VI
#
# So the text is authentic Plotinus, the slice runs from Ennead IV to the end of
# VI, and the canonical_ref is a running index that never was a citation.
#
# Is the true reference recoverable? Partly, and that is not enough:
#   - The Ennead number IS recoverable now, from the TLG citation blocks — but
#     those blocks occur only at 8192-byte boundaries (190 blocks for a 1.5 MB
#     file, roughly one per 3-4 nodes), so the resolution is the Ennead, never
#     the tractate or the chapter.
#   - Tractate and chapter live in the level bytes of the same blocks, which
#     would have to be decoded against the TLG format spec, and would still only
#     be resolved to 8 KB.
# Writing "Enn. V" where the reader expects "Enn. V.1.9" replaces a false precise
# citation with a true vague one — still not a citation. Writing the full
# reference would require re-ingesting the Enneads from a citation-bearing
# edition (Perseus tlg2000.tlg001.perseus-grc1 XML, or Henry-Schwyzer) and
# mapping the existing slices onto it.
#
# Action here: strip the false claims, keep the index, flag for remapping.
# No reference is invented.

PLOTINUS_ID_PATTERN = r"^passage_plotinus_vi_9_\d+$"
PLOTINUS_EXPECTED = 709
PLOTINUS_FALSE_URN = "urn:cts:greekLit:tlg2000.tlg001.perseus-grc1:1"
PLOTINUS_WORK_URN = "urn:cts:greekLit:tlg2000.tlg001"
PLOTINUS_REF_PATTERN = r"^Enn\. VI\.9\.(\d+)$"
PLOTINUS_FLAG = {
    "needs_reference_remapping": True,
    "why": "canonical_ref 'Enn. VI.9.N' is a running fragment index, not a "
    "citation: these 709 nodes are consecutive slices of Enneads IV-VI (ten "
    "sampled nodes anchored in TLG2000 at monotonically rising offsets, node 136 "
    "= Enn. V.1.9, node 305 onward = Ennead VI). The index is preserved as "
    "source_fragment_index; the false reference and the false passage-level URN "
    "are withdrawn. The real citation requires re-ingestion from a "
    "citation-bearing edition, mapped onto these slices.",
}

PLOTINUS_TLG_SAMPLE: list[tuple[int, int, str]] = [
    (1, 733557, "IV"),
    (50, 788447, "IV"),
    (136, 885857, "V"),
    (200, 960741, "V"),
    (305, 1083694, "VI"),
    (306, 1084660, "VI"),
    (400, 1193081, "VI"),
    (500, 1306440, "VI"),
    (600, 1423586, "VI"),
    (709, 1548122, "VI"),
]
