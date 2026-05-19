"""Process Bobzien needs_evidence args → produce e2 patch.

For each argument:
  1. Determine PDF (1998 / 2001 / 2021 essays) using e1_pub_id hint + heuristics
  2. Build a list of candidate keyword phrases derived from the description
  3. Score candidate pages, pick top match
  4. Extract verbatim (1–2 sentences containing densest keyword overlap)
  5. Verify verbatim is actually in the file (grep)
"""
import json
import pickle
import re
import datetime
from pathlib import Path

BASE_DOC = "[local-path] SHAL/04_Littérature_secondaire/01_Philosophie_antique"
PDF_1998 = f"{BASE_DOC}/Bobzien - 1998 - The Inadvertent Conception and Late Birth of the F.pdf"
PDF_2001 = f"{BASE_DOC}/Bobzien - 2001 - Determinism and Freedom in Stoic Philosophy.pdf"
PDF_2021 = f"{BASE_DOC}/bobzien_2021_determinism_freedom_essays.pdf"

TXT_1998 = "/tmp/bobzien_txt/bobzien_1998_inadvertent.txt"
TXT_2001 = "/tmp/bobzien_txt/bobzien_2001_determinism.txt"
TXT_2021 = "/tmp/bobzien_txt/bobzien_2021_essays.txt"


def load_pagemap(path):
    with open(path, "rb") as f:
        return pickle.load(f)


PAGEMAPS = {
    "1998": load_pagemap("/tmp/bobzien_txt/pagemap_1998.pkl"),
    "2001": load_pagemap("/tmp/bobzien_txt/pagemap_2001.pkl"),
    "2021": load_pagemap("/tmp/bobzien_txt/pagemap_2021.pkl"),
}

PDF_PATHS = {
    "1998": PDF_1998,
    "2001": PDF_2001,
    "2021": PDF_2021,
}

PUB_IDS = {
    "1998": "scholarly_work_bobzien_1998_inadvertent_conception_free_will_problem",
    "2001": "scholarly_work_bobzien_2001_determinism_and_freedom_in_stoic_philoso",
    "2021": "scholarly_work_bobzien_2021_determinism_freedom_essays",
}


def pick_pdf(target):
    """Decide which PDF to consult for a given argument."""
    nid = target["id"]
    meta = target.get("meta", {})
    e1_pub = meta.get("e1_pub_id", "") or ""
    desc = (target.get("description") or "").lower()
    label = (target.get("label") or "").lower()

    if "2021" in nid or "2021" in e1_pub:
        return "2021"
    if "2014" in nid or "destree" in nid.lower():
        return "2021"  # Destrée 2014 = Bobzien essay collected in 2021
    if "1998" in e1_pub or "1998" in nid:
        # The 1998 article + the 1998 monograph share metadata; the monograph
        # is the "determinism_and_freedom_in_stoic_philoso" entry, the
        # article is the "determinism" entry.
        if "determinism" in e1_pub and "freedom" not in e1_pub:
            return "1998"
        # default to 2001 book for "determinism_and_freedom_in_stoic_philoso"
        if "determinism_and_freedom" in e1_pub:
            return "2001"
        if "inadvertent" in e1_pub or "free_will_problem" in e1_pub:
            return "1998"
        return "1998"
    if "2001" in nid or "2001" in e1_pub:
        return "2001"
    if "2000" in e1_pub or "epicurus" in e1_pub:
        # 2000 Epicurus paper not in our PDFs; fall back to the 2021 collection
        return "2021"

    # heuristic by content
    if any(t in desc + label for t in ["epicurus", "swerve", "atom"]):
        return "2021"
    return "2001"


_TEXT_CACHE: dict[str, str] = {}


def get_text(key):
    if key in _TEXT_CACHE:
        return _TEXT_CACHE[key]
    paths = {"1998": TXT_1998, "2001": TXT_2001, "2021": TXT_2021}
    with open(paths[key]) as f:
        _TEXT_CACHE[key] = f.read()
    return _TEXT_CACHE[key]


def get_pages(key):
    txt = get_text(key)
    return txt.split("\f")


# --- keyword extraction ---
STOP = set(
    """the a an of in on at by for to from with into onto upon as is are was
    were be been being and or not no nor but if so do does did doing have has
    had having can could would should may might will shall this that these
    those it its their there here our we us i you he she they them his her
    bobzien which what who whom whose how when where why all any some none
    such only than then thus also more most much many also however moreover
    nevertheless rather merely just very own other another within without between
    among against through across after before during about under over while
    further still also one two three first second third fourth fifth seventh
    sixth eighth ninth tenth e.g. i.e. cf. p. pp. ch. chs. e1 b1 cf chapter
    bobzien: les des une un dans est sont son ses sa ce cette ces nous vous ils
    elles selon entre pour avec sur sans plus moins aussi déjà encore très
    cle clés cle' synthese reconstruction analyse approfondie selon distincts
    distinctes notamment ainsi puisque parce parce-que parceque dont quoi
    monograph ch chapitre p. pp. fr eng paragraphe synthèse argument arguments
    these thèse pivot central centrale stoic stoicien stoicienne stoiciens
    section §""".split()
)

# French → English term map for searching English-only PDFs
FR_TO_EN = {
    "destin": "fate",
    "destinée": "fate",
    "liberté": "freedom",
    "libre": "free",
    "arbitre": "will",
    "déterminisme": "determinism",
    "determinisme": "determinism",
    "causal": "causal",
    "causale": "causal",
    "causation": "causation",
    "ancien": "ancient",
    "ancienne": "ancient",
    "anciens": "ancient",
    "anciennes": "ancient",
    "stoïcien": "stoic",
    "stoïciens": "stoic",
    "stoicien": "stoic",
    "stoiciens": "stoic",
    "ame": "soul",
    "âme": "soul",
    "providence": "providence",
    "nature": "nature",
    "evenement": "event",
    "evenements": "events",
    "événement": "event",
    "événements": "events",
    "argument": "argument",
    "arguments": "arguments",
    "paresseux": "idle",
    "modalite": "modality",
    "modalité": "modality",
    "modal": "modal",
    "logique": "logic",
    "necessite": "necessity",
    "nécessité": "necessity",
    "possible": "possible",
    "contingence": "contingency",
    "assentiment": "assent",
    "responsabilite": "responsibility",
    "responsabilité": "responsibility",
    "morale": "moral",
    "moral": "moral",
    "regularite": "regularity",
    "régularité": "regularity",
    "universelle": "universal",
    "universel": "universal",
    "divination": "divination",
    "anti-stoicien": "anti-stoic",
    "anti-stoiciens": "anti-stoic",
    "anti-stoïcien": "anti-stoic",
    "compatibilisme": "compatibilism",
    "incompatibilisme": "incompatibilism",
    "cylindre": "cylinder",
    "agent": "agent",
    "principe": "principle",
    "actif": "active",
    "epictete": "epictetus",
    "épictète": "epictetus",
    "epicure": "epicurus",
    "épicure": "epicurus",
    "alexandre": "alexander",
    "origene": "origen",
    "origène": "origen",
    "justin": "justin",
    "tatien": "tatian",
    "platon": "plato",
    "aristote": "aristotle",
    "ciceron": "cicero",
    "cicéron": "cicero",
    "diodore": "diodorus",
    "philon": "philo",
    "carneade": "carneades",
    "stoa": "stoa",
    "stoïque": "stoic",
    "swerve": "swerve",
    "clinamen": "clinamen",
    "pneumatique": "pneumatic",
    "pneuma": "pneuma",
    "celse": "celsus",
    "eusebe": "eusebius",
    "eusèbe": "eusebius",
    "ignava": "ignava",
    "ratio": "ratio",
    "argos logos": "idle argument",
}


def keywords(text):
    """Return ordered list of distinctive lowercase tokens, with FR→EN expansion."""
    text = re.sub(r"[—–]", " ", text)
    text = re.sub(
        r"[^A-Za-zÀ-ɏα-ωΑ-Ωῖἐἀἁἄἅἆἇἑἒἓἔἕἠἡἢἣἤἥἦἧἰἱἲἳἴἵἶἷὀὁὂὃὄὅὐὑὒὓὔὕὖὗὠὡὢὣὤὥὦὧὰάὲέὴήὶίὸόὺύὼώᾳᾴᾶᾷῃῄῆῇῐῑῒΐῖῗῠῡῢΰῤῥῦῧῲῴῶῷ\-' ]",
        " ",
        text,
    )
    toks = text.lower().split()
    out = []
    seen = set()
    for t in toks:
        t = t.strip("'-.,;:")
        if not t or len(t) < 3:
            continue
        if t in STOP:
            continue
        # FR → EN substitution
        if t in FR_TO_EN:
            t = FR_TO_EN[t]
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


# Greek/Latin phrases we want to keep verbatim
GREEK_PATS = [
    "ἐφ' ἡμῖν",
    "eph' hēmin",
    "eph' hemin",
    "to_eph_hemin",
    "ἐλευθερία",
    "eleutheria",
    "αὐτεξούσιον",
    "autexousion",
    "συγκατάθεσις",
    "sunkatathesis",
    "synkatathesis",
    "προαίρεσις",
    "prohairesis",
    "heimarmen",
    "ἀνάγκη",
    "anank",
    "phantasi",
    "kurieuon",
    "argos logos",
    "ignava ratio",
    "co-fated",
    "confatalia",
    "co-fatedness",
    "sunheimarmen",
    "συνειμαρμέν",
    "philopator",
    "PHILOPATOR",
    "cylinder",
    "alexander",
    "chrysippus",
    "epictetus",
    "epicurus",
    "stops short",
    "two-sided",
    "one-sided",
    "potestative",
    "causative",
    "indeterminist",
    "compatibilist",
    "carneades",
    "swerve",
    "diodorus",
    "master argument",
    "modal",
    "bivalence",
    "divination",
    "celsus",
    "origen",
    "justin",
    "tatian",
    "providence",
    "fate principle",
    "moral responsibility",
    "MR1",
    "MR2",
]


def score_page(page_text, kws, greek_hits):
    """Higher = better match."""
    pt = page_text.lower()
    score = 0
    matched = []
    for k in kws[:25]:
        if k in pt:
            score += 1
            matched.append(k)
    for g in greek_hits:
        if g.lower() in pt:
            score += 3
            matched.append(g)
    return score, matched


def is_toc_or_index(page_text):
    """Detect TOC / Index / Bibliography pages by signal patterns."""
    head = page_text[:300]
    if "Contents" in head or "CONTENTS" in head:
        return True
    if "Index Locorum" in head or "Subject Index" in head or "Index Nominum" in head:
        return True
    if "Bibliography" in head or "BIBLIOGRAPHY" in head or "References" == head.strip()[:10].rstrip(":"):
        return True
    # TOC heuristic: lots of "trailing page numbers" at end of lines (e.g. "Section title    122")
    lines = page_text.split("\n")
    trailing_pages = sum(
        1 for ln in lines if re.search(r"\.\s{2,}\d{2,4}\s*$", ln) or re.search(r"\s{4,}\d{2,4}\s*$", ln)
    )
    if trailing_pages >= 6:
        return True
    return False


def find_best_pages(key, kws, greek_hits, top_n=5):
    """Return list of (printed_page, pdf_idx, score, matched, page_text)."""
    pm = PAGEMAPS[key]
    scored = []
    for i, printed, chap, page_text in pm:
        if printed is None:
            continue
        if key == "2001" and printed > 416:
            continue
        if is_toc_or_index(page_text):
            continue
        s, m = score_page(page_text, kws, greek_hits)
        if s > 0:
            scored.append((printed, i, s, m, page_text, chap))
    scored.sort(key=lambda x: -x[2])
    return scored[:top_n]


def detect_greek_hits(label, desc):
    text = f"{label} {desc}"
    hits = []
    for g in GREEK_PATS:
        if g.lower() in text.lower():
            hits.append(g)
    return hits


def extract_verbatim(page_text, kws, greek_hits, max_chars=480):
    """Pick the densest 1-2 sentences from the page.

    Strategy: normalize whitespace first so multi-line sentences become single
    strings, drop header line (page number + chapter title), then sentence-split.
    """
    lines = page_text.split("\n")
    # drop the first non-empty line if it's a header (page number + title)
    body_lines = []
    skipped = False
    for ln in lines:
        if not skipped and ln.strip():
            # likely the header
            skipped = True
            continue
        body_lines.append(ln)
    body = "\n".join(body_lines)
    # join hyphenated line breaks
    body = re.sub(r"-\n\s*", "", body)
    body = re.sub(r"\s+", " ", body).strip()

    # sentence split
    sents = re.split(r"(?<=[.!?])\s+(?=[A-Z“‘\(])", body)
    best_s, best_score = None, -1
    for s in sents:
        if len(s) < 40 or len(s) > 800:
            continue
        sc = 0
        sl = s.lower()
        for k in kws[:15]:
            if k in sl:
                sc += 1
        for g in greek_hits:
            if g.lower() in sl:
                sc += 3
        # bias against footnote-like fragments
        if re.match(r"^\s*\d+\s+", s):
            sc -= 2
        # bias against bibliography references "(NAME YEAR ...)"
        if re.match(r"^[A-Z][a-z]+\s+\d{4}[a-z]?", s):
            sc -= 2
        # bias against ancient-source citation lists (many parens with abbreviations)
        cite_pat = len(re.findall(r"\b[IVX]+\s+\d+\b|\b\d+\.\d+\b|cf\.|ad\s+Graec\.|Strom\.|Orat\.", s))
        if cite_pat >= 3:
            sc -= 3
        # bias against starts with closing paren or footnote artifact
        if re.match(r"^[\)\d\s,;:]+", s):
            sc -= 3
        if sc > best_score:
            best_score = sc
            best_s = s
    if best_s is None or best_score <= 0:
        return None
    v = re.sub(r"\s+", " ", best_s).strip()
    if len(v) > max_chars:
        v = v[: max_chars - 1].rsplit(" ", 1)[0] + "…"
    return v


def verify_in_pdf(verbatim, key, pdf_idx):
    """Verify verbatim words exist on that PDF page.

    Use a robust anchor: longest contiguous word run from the verbatim that we
    can find on the page after both are whitespace-normalized and line-break
    hyphens collapsed.
    """
    pm = PAGEMAPS[key]
    page = pm[pdf_idx][3]
    page = re.sub(r"-\n\s*", "", page)
    pn = re.sub(r"\s+", " ", page).lower()
    vn = re.sub(r"-\s*", "", verbatim.replace("…", ""))
    vn = re.sub(r"\s+", " ", vn).lower().strip()
    # Try increasing window anchors
    for n in (90, 70, 50, 35):
        if len(vn) >= n:
            anchor = vn[:n]
            if anchor in pn:
                return True
    # fallback: 6-word substring anywhere inside vn
    words = vn.split()
    for start in range(0, max(1, len(words) - 6)):
        chunk = " ".join(words[start : start + 6])
        if chunk in pn:
            return True
    return False


def classify_confidence(score, matched, verified):
    if not verified:
        return "low"
    if score >= 5 and len(matched) >= 3:
        return "high"
    if score >= 3:
        return "medium"
    return "low"


def process(target):
    label = target.get("label") or ""
    desc = target.get("description") or ""
    pdf_key = pick_pdf(target)
    kws = keywords(f"{label} {desc}")
    greek_hits = detect_greek_hits(label, desc)

    best = find_best_pages(pdf_key, kws, greek_hits, top_n=5)

    if not best:
        return {
            "pdf_source": PDF_PATHS[pdf_key],
            "publication_id": PUB_IDS[pdf_key],
            "page": None,
            "chapter": None,
            "quote_verbatim": None,
            "translation_en": None,
            "context": None,
            "verification_confidence": "not_found",
            "quote_attempted_keywords": kws[:10],
            "verified_at": "2026-05-19",
            "verified_by": "e2_bobzien_agent",
        }

    printed, pdf_idx, score, matched, page_text, chap = best[0]
    verbatim = extract_verbatim(page_text, kws, greek_hits)
    verified = bool(verbatim and verify_in_pdf(verbatim, pdf_key, pdf_idx))
    conf = classify_confidence(score, matched, verified)

    # Clean chapter field (drop running-header noise from 2021)
    if chap:
        chap_clean = chap.strip()
        # if the chapter contains no real letters or is all punctuation/digits/commas
        letters = re.sub(r"[^A-Za-zÀ-ɏα-ωΑ-Ω]", "", chap_clean)
        if len(letters) < 4 or re.fullmatch(r"[\s,\.\-:;0-9]+", chap_clean):
            chap_clean = None
    else:
        chap_clean = None

    return {
        "pdf_source": PDF_PATHS[pdf_key],
        "publication_id": PUB_IDS[pdf_key],
        "page": str(printed),
        "chapter": chap_clean,
        "quote_verbatim": verbatim if verified else None,
        "translation_en": None,
        "context": f"Densest keyword match on p. {printed}"
        + (f" ({chap_clean})" if chap_clean else "")
        + f" — keywords matched: {', '.join(matched[:6])}",
        "verification_confidence": conf,
        "match_score": score,
        "match_keywords": matched[:8],
        "quote_attempted_keywords": kws[:10],
        "verified_at": "2026-05-19",
        "verified_by": "e2_bobzien_agent",
    }


def main():
    with open("/tmp/bobzien_targets.json") as f:
        targets = json.load(f)

    patches = {}
    stats = {"high": 0, "medium": 0, "low": 0, "not_found": 0}

    for t in targets:
        patches[t["id"]] = process(t)
        c = patches[t["id"]]["verification_confidence"]
        stats[c] = stats.get(c, 0) + 1

    out = {
        "scholar": "Susanne Bobzien",
        "scholar_node_id": "person_bobzien_susanne_contemporary",
        "pdfs_consulted": list(PDF_PATHS.values()),
        "args_processed": len(targets),
        "args_verified_high": stats["high"],
        "args_verified_medium": stats["medium"],
        "args_verified_low": stats["low"],
        "args_not_found": stats["not_found"],
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "patches": patches,
    }

    out_path = Path("data/kg/e2_patches/bobzien.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"Wrote {out_path}")
    print(f"Stats: {stats}")


if __name__ == "__main__":
    main()
