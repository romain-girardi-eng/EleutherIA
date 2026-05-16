"""Migrate i18n locale JSON files so stat counts use {{placeholder}} interpolation.

Hardcoded numbers in frontend/src/i18n/locales/{en,fr,de,it,el}.json drift away
from reality whenever the KG/corpus grows. This script rewrites the offending
strings to use react-i18next interpolation tokens. The frontend hook
`useKgStats` provides live values which components pass to `t(key, {...})`.

REPLACEMENT TABLE
─────────────────────────────────────────────────────────────────────────────
Static (kept hardcoded — physical/historical constants):
  - "1,200 years" / "1.200 ans" / "1 200" — historical span of debate
  - "3,072 dimensions"                    — embedding vector size
  - "12-node FSM"                         — pipeline graph node count

Dynamic (replaced with placeholders):
  - {{nodeCount}}        — live total kg_nodes
  - {{edgeCount}}        — live total kg_edges
  - {{workCount}}        — live total works
  - {{passageCount}}     — live total passages

For each locale file, this script:
  1. Loads the JSON
  2. For each known stat-bearing key, rewrites the string with the right
     placeholders (locale-aware: each language's existing phrasing preserved)
  3. Writes back with the same indentation
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

LOCALES_DIR = Path(__file__).resolve().parent.parent / "frontend" / "src" / "i18n" / "locales"
LOCALES = ["en", "fr", "de", "it", "el"]

# For each (path, locale) → new string. None means "do not touch this locale" if
# the key shape varies. Path is dot-separated.

# fmt: off
REWRITES: dict[str, dict[str, str]] = {
    # home.features
    "home.features.kg.description": {
        "en": "Explore {{nodeCount}} nodes and {{edgeCount}} relationships in an interactive network visualization",
        "fr": "Explorez {{nodeCount}} nœuds et {{edgeCount}} relations dans une visualisation de réseau interactive",
        "de": "Erkunden Sie {{nodeCount}} Knoten und {{edgeCount}} Beziehungen in einer interaktiven Netzwerkvisualisierung",
        "it": "Esplora {{nodeCount}} nodi e {{edgeCount}} relazioni in una visualizzazione di rete interattiva",
        "el": "Εξερευνήστε {{nodeCount}} κόμβους και {{edgeCount}} σχέσεις σε μια διαδραστική οπτικοποίηση δικτύου",
    },
    "home.features.search.description": {
        "en": "Full-text, lemmatic, and semantic search across {{workCount}} ancient works with {{passageCount}} passages",
        "fr": "Recherche plein texte, lemmatique et sémantique sur {{workCount}} œuvres antiques avec {{passageCount}} passages",
        "de": "Volltext-, lemmatische und semantische Suche in {{workCount}} antiken Werken mit {{passageCount}} Passagen",
        "it": "Ricerca full-text, lemmatica e semantica su {{workCount}} opere antiche con {{passageCount}} passi",
        "el": "Αναζήτηση πλήρους κειμένου, λημματική και σημασιολογική σε {{workCount}} αρχαία έργα με {{passageCount}} χωρία",
    },
    "home.features.texts.description": {
        "en": "Browse and read {{workCount}} ancient Greek and Latin works with lemmatization",
        "fr": "Parcourez et lisez {{workCount}} œuvres grecques et latines antiques avec lemmatisation",
        "de": "Durchsuchen und lesen Sie {{workCount}} antike griechische und lateinische Werke mit Lemmatisierung",
        "it": "Consulta e leggi {{workCount}} opere greche e latine antiche con lemmatizzazione",
        "el": "Περιηγηθείτε και διαβάστε {{workCount}} αρχαία ελληνικά και λατινικά έργα με λημματοποίηση",
    },
    "home.about.description2": {
        "en": "The database combines a comprehensive knowledge graph with {{workCount}} ancient works ({{passageCount}} passages), enabling advanced research workflows: cross-referencing arguments, tracing influence networks, and connecting modern scholarship to primary sources through agentic GraphRAG.",
        "fr": "La base de données combine un graphe de connaissances complet avec {{workCount}} œuvres antiques ({{passageCount}} passages), permettant une recherche avancée : recoupement des arguments, traçage des réseaux d'influence et connexion de la recherche moderne aux sources primaires via le GraphRAG agentique.",
        "de": "Die Datenbank kombiniert einen umfassenden Wissensgraph mit {{workCount}} antiken Werken ({{passageCount}} Passagen) und ermöglicht fortgeschrittene Forschung: Querverweise zu Argumenten, Verfolgung von Einflussnetzwerken und Verbindung moderner Forschung mit Primärquellen über agentisches GraphRAG.",
        "it": "Il database combina un completo grafo di conoscenza con {{workCount}} opere antiche ({{passageCount}} passi), consentendo ricerche avanzate: riferimenti incrociati di argomenti, tracciamento delle reti di influenza e connessione della ricerca moderna alle fonti primarie tramite GraphRAG Agentico.",
        "el": "Η βάση δεδομένων συνδυάζει ένα ολοκληρωμένο γράφημα γνώσης με {{workCount}} αρχαία έργα ({{passageCount}} χωρία), επιτρέποντας προηγμένη έρευνα: διασταυρώσεις επιχειρημάτων, παρακολούθηση δικτύων επιρροής και σύνδεση σύγχρονης έρευνας με πρωτογενείς πηγές μέσω agentic GraphRAG.",
    },
    # search
    "search.subtitle": {
        "en": "Search across {{workCount}} ancient texts using full-text, lemmatic, and semantic approaches",
        "fr": "Recherchez dans {{workCount}} textes antiques en utilisant des approches plein texte, lemmatique et sémantique",
        "de": "Durchsuchen Sie {{workCount}} antike Texte mit Volltext-, lemmatischen und semantischen Ansätzen",
        "it": "Cerca tra {{workCount}} testi antichi utilizzando approcci full-text, lemmatici e semantici",
        "el": "Αναζητήστε σε {{workCount}} αρχαία κείμενα χρησιμοποιώντας προσεγγίσεις πλήρους κειμένου, λημματικές και σημασιολογικές",
    },
    "search.loadingMessage": {
        "en": "Searching across {{workCount}} ancient texts...",
        "fr": "Recherche dans {{workCount}} textes antiques...",
        "de": "Durchsuche {{workCount}} antike Texte...",
        "it": "Ricerca tra {{workCount}} testi antichi...",
        "el": "Αναζήτηση σε {{workCount}} αρχαία κείμενα...",
    },
    "advancedSearch.subtitle": {
        "en": "Real-time search across {{passageCount}} passages from {{workCount}} ancient works",
        "fr": "Recherche en temps réel dans {{passageCount}} passages de {{workCount}} œuvres antiques",
        "de": "Echtzeit-Suche in {{passageCount}} Passagen aus {{workCount}} antiken Werken",
        "it": "Ricerca in tempo reale su {{passageCount}} passi da {{workCount}} opere antiche",
        "el": "Αναζήτηση σε πραγματικό χρόνο σε {{passageCount}} χωρία από {{workCount}} αρχαία έργα",
    },
    # agenticGraphrag
    "agenticGraphrag.overview.description": {
        "en": "EleutherIA uses an Agentic GraphRAG pipeline that combines a curated knowledge graph ({{nodeCount}} nodes, {{edgeCount}} edges) with an autonomous retrieval and synthesis system. Unlike traditional RAG, our system uses Claude as a reasoning agent to navigate the graph, build context, and synthesize scholarly answers.",
        "fr": "EleutherIA utilise un pipeline GraphRAG Agentique qui combine un graphe de connaissances curé ({{nodeCount}} nœuds, {{edgeCount}} arêtes) avec un système autonome de récupération et de synthèse. Contrairement au RAG traditionnel, notre système utilise Claude comme agent de raisonnement pour naviguer le graphe, construire le contexte et synthétiser des réponses académiques.",
        "de": "EleutherIA nutzt eine agentische GraphRAG-Pipeline, die einen kurierten Wissensgraphen ({{nodeCount}} Knoten, {{edgeCount}} Kanten) mit einem autonomen Such- und Synthese-System kombiniert. Anders als traditionelles RAG nutzt unser System Claude als Reasoning-Agent, um den Graphen zu navigieren, Kontext aufzubauen und wissenschaftliche Antworten zu synthetisieren.",
        "it": "EleutherIA utilizza una pipeline GraphRAG Agentico che combina un grafo della conoscenza curato ({{nodeCount}} nodi, {{edgeCount}} archi) con un sistema autonomo di recupero e sintesi. A differenza del RAG tradizionale, il nostro sistema utilizza Claude come agente di ragionamento per navigare il grafo, costruire il contesto e sintetizzare risposte accademiche.",
        "el": "Το EleutherIA χρησιμοποιεί μια pipeline Agentic GraphRAG που συνδυάζει έναν επιμελημένο γράφο γνώσης ({{nodeCount}} κόμβοι, {{edgeCount}} ακμές) με ένα αυτόνομο σύστημα ανάκτησης και σύνθεσης. Σε αντίθεση με το παραδοσιακό RAG, το σύστημά μας χρησιμοποιεί τον Claude ως agent συλλογισμού.",
    },
    "agenticGraphrag.summary.resultText": {
        "en": "Scholarly answers grounded in {{nodeCount}} KG nodes and {{passageCount}}+ passages with full citation tracking and reasoning transparency",
        "fr": "Réponses académiques ancrées dans {{nodeCount}} nœuds KG et plus de {{passageCount}} passages avec suivi complet des citations et transparence du raisonnement",
        "de": "Wissenschaftliche Antworten basierend auf {{nodeCount}} KG-Knoten und {{passageCount}}+ Passagen mit vollständiger Zitatverfolgung und Argumentationstransparenz",
        "it": "Risposte accademiche ancorate a {{nodeCount}} nodi KG e oltre {{passageCount}} passi con tracciamento completo delle citazioni e trasparenza del ragionamento",
        "el": "Ακαδημαϊκές απαντήσεις βασισμένες σε {{nodeCount}} κόμβους KG και {{passageCount}}+ αποσπάσματα με πλήρη παρακολούθηση παραπομπών και διαφάνεια συλλογισμού",
    },
    # kg
    "kg.statsDisplay": {
        "en": "{{nodeCount}} nodes · {{edgeCount}} edges",
        "fr": "{{nodeCount}} nœuds · {{edgeCount}} arêtes",
        "de": "{{nodeCount}} Knoten · {{edgeCount}} Kanten",
        "it": "{{nodeCount}} nodi · {{edgeCount}} relazioni",
        "el": "{{nodeCount}} κόμβοι · {{edgeCount}} ακμές",
    },
    # learn.overview.pillars
    "learn.overview.pillars.kg.description": {
        "en": "{{nodeCount}} interconnected concepts, persons, arguments, and works spanning 1,200 years of philosophical debate.",
        "fr": "{{nodeCount}} concepts, personnes, arguments et œuvres interconnectés couvrant 1 200 ans de débat philosophique.",
        "de": "{{nodeCount}} vernetzte Konzepte, Personen, Argumente und Werke über 1.200 Jahre philosophischer Debatte.",
        "it": "{{nodeCount}} concetti, persone, argomenti e opere interconnessi che coprono 1.200 anni di dibattito filosofico.",
        "el": "{{nodeCount}} διασυνδεδεμένες έννοιες, πρόσωπα, επιχειρήματα και έργα που εκτείνονται σε 1.200 χρόνια φιλοσοφικής συζήτησης.",
    },
    "learn.overview.pillars.texts.description": {
        "en": "{{workCount}} canonical works with {{passageCount}} passages in Greek, Latin, Hebrew, and English with full morphological analysis.",
        "fr": "{{workCount}} œuvres canoniques avec {{passageCount}} passages en grec, latin, hébreu et anglais avec analyse morphologique complète.",
        "de": "{{workCount}} kanonische Werke mit {{passageCount}} Passagen auf Griechisch, Latein, Hebräisch und Englisch mit vollständiger morphologischer Analyse.",
        "it": "{{workCount}} opere canoniche con {{passageCount}} passaggi in greco, latino, ebraico e inglese con analisi morfologica completa.",
        "el": "{{workCount}} κανονικά έργα με {{passageCount}} χωρία στα Ελληνικά, Λατινικά, Εβραϊκά και Αγγλικά με πλήρη μορφολογική ανάλυση.",
    },
    "learn.ancientTexts.subtitle": {
        "en": "{{workCount}} works, {{passageCount}} passages, 5 languages",
        "fr": "{{workCount}} œuvres, {{passageCount}} passages, 5 langues",
        "de": "{{workCount}} Werke, {{passageCount}} Passagen, 5 Sprachen",
        "it": "{{workCount}} opere, {{passageCount}} passaggi, 5 lingue",
        "el": "{{workCount}} έργα, {{passageCount}} χωρία, 5 γλώσσες",
    },
    "learn.graphrag.steps.semanticSearch.detail": {
        "en": "Your question becomes a 3,072-number vector. We compare it to all {{nodeCount}} KG nodes and find the top 10 most similar.",
        "fr": "Votre question devient un vecteur de 3 072 nombres. Nous le comparons aux {{nodeCount}} nœuds du graphe et trouvons les 10 plus proches.",
        "de": "Ihre Frage wird zu einem 3.072-Zahlen-Vektor. Wir vergleichen ihn mit allen {{nodeCount}} KG-Knoten und finden die 10 ähnlichsten.",
        "it": "La tua domanda diventa un vettore di 3.072 numeri. Lo confrontiamo con tutti i {{nodeCount}} nodi del grafo e troviamo i 10 più simili.",
        "el": "Η ερώτησή σας γίνεται διάνυσμα 3.072 αριθμών. Το συγκρίνουμε με όλους τους {{nodeCount}} κόμβους KG και βρίσκουμε τους 10 πιο παρόμοιους.",
    },
}
# fmt: on


def set_nested(obj: dict, path: str, value: str) -> bool:
    keys = path.split(".")
    cur = obj
    for k in keys[:-1]:
        if not isinstance(cur, dict) or k not in cur:
            return False
        cur = cur[k]
    if not isinstance(cur, dict) or keys[-1] not in cur:
        return False
    cur[keys[-1]] = value
    return True


def main() -> int:
    total_changed = 0
    for loc in LOCALES:
        p = LOCALES_DIR / f"{loc}.json"
        if not p.exists():
            print(f"  [skip] {p.name} missing")
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        changed = 0
        missing_keys = []
        for path, by_loc in REWRITES.items():
            if loc not in by_loc:
                continue
            ok = set_nested(data, path, by_loc[loc])
            if ok:
                changed += 1
            else:
                missing_keys.append(path)
        # Write back with same shape
        p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"  {p.name}: {changed} keys rewritten" + (f", missing: {missing_keys}" if missing_keys else ""))
        total_changed += changed
    print(f"\nTotal keys rewritten across locales: {total_changed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
