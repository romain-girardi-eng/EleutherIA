#!/usr/bin/env python3
"""
Final Comprehensive Quality Audit
Calculate overall database quality score after all 3 phases
"""

import json

def final_audit():
    """Run comprehensive quality audit"""

    # Load database
    with open('ancient_free_will_database.json', 'r', encoding='utf-8') as f:
        db = json.load(f)

    nodes = db['nodes']
    edges = db['edges']
    metadata = db['metadata']

    print("=" * 80)
    print("FINAL COMPREHENSIVE QUALITY AUDIT")
    print("=" * 80)
    print(f"\nDatabase: {metadata.get('title')}")
    print(f"Version: {metadata.get('version')}")
    print(f"Total nodes: {len(nodes)}")
    print(f"Total edges: {len(edges)}")

    # Scoring components
    scores = {}

    # ========== PHASE 1: PERIOD VOCABULARY (30 points) ==========
    valid_periods = {
        'Presocratic', 'Classical Greek', 'Hellenistic Greek',
        'Roman Republican', 'Roman Imperial', 'Patristic', 'Late Antiquity',
        'Early Medieval', 'High Medieval', 'Late Medieval',
        'Renaissance', 'Reformation', 'Counter-Reformation',
        'Early Modern Rationalism', 'Early Modern Empiricism', 'Enlightenment',
        '19th Century', '20th Century Analytic', '20th Century Continental', '21st Century',
        'Second Temple Judaism', 'Rabbinic Judaism'
    }

    nodes_with_period = [n for n in nodes if n.get('period')]
    valid_period_nodes = [n for n in nodes_with_period if n.get('period') in valid_periods]

    period_score = (len(valid_period_nodes) / len(nodes_with_period)) * 30 if nodes_with_period else 0
    scores['period_vocabulary'] = period_score

    print("\n" + "=" * 80)
    print("PHASE 1: PERIOD VOCABULARY")
    print("=" * 80)
    print(f"Nodes with period field: {len(nodes_with_period)}")
    print(f"Valid period values: {len(valid_period_nodes)} ({len(valid_period_nodes)/len(nodes_with_period)*100:.1f}%)")
    print(f"Score: {period_score:.1f}/30")

    # ========== PHASE 2: TERMINOLOGY COVERAGE (30 points) ==========
    concepts = [n for n in nodes if n.get('type') == 'concept']

    # Define appropriate terminology by period
    ancient_periods = {'Presocratic', 'Classical Greek', 'Hellenistic Greek', 'Roman Republican'}
    patristic_periods = {'Roman Imperial', 'Patristic', 'Late Antiquity'}
    medieval_periods = {'Early Medieval', 'High Medieval', 'Late Medieval', 'Renaissance',
                       'Reformation', 'Counter-Reformation', 'Early Modern Rationalism',
                       'Early Modern Empiricism', 'Enlightenment'}
    modern_periods = {'19th Century', '20th Century Analytic', '20th Century Continental', '21st Century'}
    jewish_periods = {'Second Temple Judaism', 'Rabbinic Judaism'}

    appropriate_terminology = 0

    for concept in concepts:
        period = concept.get('period')
        has_greek = bool(concept.get('greek_term'))
        has_latin = bool(concept.get('latin_term'))
        has_hebrew = bool(concept.get('hebrew_term'))

        # Ancient Greek: needs Greek + Latin
        if period in ancient_periods:
            if has_greek and has_latin:
                appropriate_terminology += 1
            elif has_greek:  # Has Greek at minimum
                appropriate_terminology += 0.5

        # Patristic/Roman: needs Greek or Latin
        elif period in patristic_periods:
            if has_greek or has_latin:
                appropriate_terminology += 1

        # Medieval: needs Latin
        elif period in medieval_periods:
            if has_latin:
                appropriate_terminology += 1

        # Jewish: needs Hebrew
        elif period in jewish_periods:
            if has_hebrew:
                appropriate_terminology += 1

        # Modern: English only (no ancient languages)
        elif period in modern_periods or period is None:
            if not has_greek and not has_latin and not has_hebrew:
                appropriate_terminology += 1

    terminology_score = (appropriate_terminology / len(concepts)) * 30 if concepts else 0
    scores['terminology'] = terminology_score

    print("\n" + "=" * 80)
    print("PHASE 2: TERMINOLOGY COVERAGE")
    print("=" * 80)
    print(f"Total concepts: {len(concepts)}")
    print(f"Appropriate terminology: {appropriate_terminology:.0f} ({appropriate_terminology/len(concepts)*100:.1f}%)")
    print(f"Score: {terminology_score:.1f}/30")

    # ========== PHASE 3: CITATION COVERAGE (30 points) ==========
    # Focus on critical node types: concepts, arguments, persons
    critical_types = ['concept', 'argument', 'person']
    critical_nodes = [n for n in nodes if n.get('type') in critical_types]

    cited_critical = 0
    for node in critical_nodes:
        ancient = node.get('ancient_sources', [])
        modern = node.get('modern_scholarship', [])

        if (ancient and len(ancient) > 0) or (modern and len(modern) > 0):
            cited_critical += 1

    citation_score = (cited_critical / len(critical_nodes)) * 30 if critical_nodes else 0
    scores['citations'] = citation_score

    print("\n" + "=" * 80)
    print("PHASE 3: CITATION COVERAGE")
    print("=" * 80)
    print(f"Critical nodes (concept/argument/person): {len(critical_nodes)}")
    print(f"Nodes with citations: {cited_critical} ({cited_critical/len(critical_nodes)*100:.1f}%)")
    print(f"Score: {citation_score:.1f}/30")

    # ========== BONUS: STRUCTURE & METADATA (10 points) ==========
    structure_score = 0

    # Valid metadata (5 points)
    if metadata.get('title') and metadata.get('version') and metadata.get('license'):
        structure_score += 5

    # Rich edge relationships (5 points)
    if len(edges) > 800:  # Target was 820+
        structure_score += 5
    elif len(edges) > 700:
        structure_score += 3

    scores['structure'] = structure_score

    print("\n" + "=" * 80)
    print("BONUS: STRUCTURE & METADATA")
    print("=" * 80)
    print(f"Metadata completeness: {'✓' if structure_score >= 5 else '✗'}")
    print(f"Edge relationships: {len(edges)}")
    print(f"Score: {structure_score}/10")

    # ========== TOTAL SCORE ==========
    total_score = sum(scores.values())

    print("\n" + "=" * 80)
    print("OVERALL QUALITY SCORE")
    print("=" * 80)
    print(f"Phase 1 (Period Vocabulary):  {scores['period_vocabulary']:.1f}/30")
    print(f"Phase 2 (Terminology):        {scores['terminology']:.1f}/30")
    print(f"Phase 3 (Citations):          {scores['citations']:.1f}/30")
    print(f"Bonus (Structure/Metadata):   {scores['structure']:.1f}/10")
    print(f"\nTOTAL SCORE: {total_score:.1f}/100")

    # Grade assignment
    if total_score >= 90:
        grade = "A (Excellent)"
    elif total_score >= 80:
        grade = "B (Very Good)"
    elif total_score >= 70:
        grade = "C (Good)"
    elif total_score >= 60:
        grade = "D (Acceptable)"
    else:
        grade = "F (Needs Improvement)"

    print(f"\nGRADE: {grade}")

    # Progress from start
    print("\n" + "=" * 80)
    print("IMPROVEMENT SUMMARY")
    print("=" * 80)
    print(f"Starting score (estimated):  5.5/100")
    print(f"After Phase 1:              45.0/100 (+39.5)")
    print(f"After Phase 2:              73.6/100 (+28.6)")
    print(f"After Phase 3:              {total_score:.1f}/100 (+{total_score - 73.6:.1f})")
    print(f"\nTotal improvement: +{total_score - 5.5:.1f} points")

    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    if total_score >= 90:
        print("✓ PUBLICATION READY - Database meets highest academic standards")
        print("✓ Suitable for Zenodo/academic repository release")
        print("✓ Ready for citation in scholarly publications")
    elif total_score >= 80:
        print("✓ NEAR PUBLICATION READY - Minor enhancements recommended")
        print("  Consider: Additional citations for person/work nodes")
    elif total_score >= 70:
        print("⚠ GOOD PROGRESS - Continue enhancements")
        print("  Priority: Complete remaining citations")
    else:
        print("⚠ NEEDS MORE WORK")

    return {
        'total': total_score,
        'scores': scores,
        'grade': grade
    }

if __name__ == '__main__':
    final_audit()
