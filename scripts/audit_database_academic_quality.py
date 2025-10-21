#!/usr/bin/env python3
"""
Database Academic Quality Audit Script
=======================================

Uses the Agent Skill standards to audit the entire Ancient Free Will Database
for academic quality, FAIR compliance, and enhancement opportunities.

This script generates a comprehensive report identifying:
- Missing citations (ancient sources or modern scholarship)
- Invalid controlled vocabulary usage
- Malformed node IDs
- Missing Greek/Latin terminology
- Incomplete person/concept/argument data
- FAIR compliance issues
- Enhancement opportunities

Run this script, then work with Claude to address flagged issues systematically.
"""

import json
import re
from collections import defaultdict, Counter
from typing import Dict, List, Tuple

# ============================================================================
# CONTROLLED VOCABULARIES (from skill)
# ============================================================================

VALID_NODE_TYPES = {
    'person', 'work', 'concept', 'argument', 'debate', 'controversy',
    'reformulation', 'event', 'school', 'group', 'argument_framework',
    'quote', 'conceptual_evolution'
}

VALID_RELATIONS = {
    'formulated', 'authored', 'developed', 'influenced', 'transmitted',
    'transmitted_in_writing_by', 'refutes', 'supports', 'defends',
    'opposes', 'targets', 'appropriates', 'employs', 'used', 'adapted',
    'reinterprets', 'develops', 'synthesizes', 'exemplifies',
    'component_of', 'related_to', 'reformulated_as', 'centers_on',
    'includes', 'structures', 'translates'
}

VALID_PERIODS = {
    'Classical Greek', 'Hellenistic Greek', 'Roman Republican',
    'Roman Imperial', 'Patristic', 'Late Antiquity'
}

VALID_SCHOOLS = {
    'Peripatetic', 'Aristotelian', 'Epicurean', 'Stoic', 'Academic',
    'Academic Skeptic', 'Platonist', 'Middle Platonist', 'Neoplatonist',
    'Patristic', 'Christian Platonist', 'Presocratic',
    'Early Stoa', 'Middle Stoa', 'Late Stoa'
}

# ============================================================================
# LOAD DATABASE
# ============================================================================

def load_database(filepath='ancient_free_will_database.json'):
    """Load the database"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

# ============================================================================
# AUDIT FUNCTIONS
# ============================================================================

def audit_node_id_format(node: Dict) -> List[str]:
    """Check if node ID follows format: <type>_<name>_<dates-or-hash>"""
    issues = []
    node_id = node['id']

    # Check lowercase
    if node_id != node_id.lower():
        issues.append("ID not all lowercase")

    # Check starts with type
    if not node_id.startswith(node['type'] + '_'):
        issues.append(f"ID should start with '{node['type']}_'")

    # Check has at least 3 parts (type_name_suffix)
    parts = node_id.split('_')
    if len(parts) < 3:
        issues.append("ID missing dates or hash suffix")

    return issues

def audit_controlled_vocabulary(node: Dict) -> List[str]:
    """Check if node uses valid controlled vocabulary"""
    issues = []

    # Check node type
    if node['type'] not in VALID_NODE_TYPES:
        issues.append(f"Invalid node type: '{node['type']}'")

    # Check period if present
    if 'period' in node and node['period']:
        if node['period'] not in VALID_PERIODS:
            issues.append(f"Invalid period: '{node['period']}'")

    # Check school if present
    if 'school' in node and node['school']:
        # Allow partial matches for schools (e.g., "Late Stoic")
        if not any(school in node['school'] for school in VALID_SCHOOLS):
            issues.append(f"Non-standard school: '{node['school']}'")

    return issues

def audit_citations(node: Dict) -> List[str]:
    """Check if node has proper citations"""
    issues = []

    # Critical node types that MUST have citations
    critical_types = {'person', 'concept', 'argument', 'work'}

    if node['type'] in critical_types:
        has_ancient = 'ancient_sources' in node and node['ancient_sources']
        has_modern = 'modern_scholarship' in node and node['modern_scholarship']

        if not has_ancient and not has_modern:
            issues.append("Missing both ancient sources AND modern scholarship")
        elif not has_ancient:
            issues.append("Missing ancient sources (recommended)")

    return issues

def audit_greek_latin_terminology(node: Dict) -> List[str]:
    """Check if concept nodes have Greek/Latin terms"""
    issues = []

    if node['type'] == 'concept':
        has_greek = 'greek_term' in node and node['greek_term']
        has_latin = 'latin_term' in node and node['latin_term']
        has_english = 'english_term' in node and node['english_term']

        if not has_greek and not has_latin:
            issues.append("Missing Greek or Latin terminology")

        if not has_english:
            issues.append("Missing English translation")

        # Check if Greek term has Unicode characters
        if has_greek:
            greek_unicode = re.search(r'[\u0370-\u03FF\u1F00-\u1FFF]', node['greek_term'])
            if not greek_unicode:
                issues.append("Greek term lacks proper Unicode characters")

    return issues

def audit_person_completeness(node: Dict) -> List[str]:
    """Check if person nodes have complete information"""
    issues = []

    if node['type'] == 'person':
        recommended_fields = {
            'dates': 'birth-death dates',
            'school': 'philosophical school',
            'period': 'historical period',
            'position_on_free_will': 'position on free will',
            'major_works': 'major works',
        }

        for field, description in recommended_fields.items():
            if field not in node or not node[field]:
                issues.append(f"Missing {description}")

    return issues

def audit_concept_completeness(node: Dict) -> List[str]:
    """Check if concept nodes have complete information"""
    issues = []

    if node['type'] == 'concept':
        recommended_fields = {
            'formulated_by': 'originator',
            'relation_to_free_will': 'relation to free will',
            'related_concepts': 'related concepts',
        }

        for field, description in recommended_fields.items():
            if field not in node or not node[field]:
                issues.append(f"Missing {description}")

    return issues

def audit_argument_completeness(node: Dict) -> List[str]:
    """Check if argument nodes have complete information"""
    issues = []

    if node['type'] == 'argument':
        recommended_fields = {
            'formulated_by': 'originator',
            'source_text': 'source text citation',
            'argument_type': 'argument classification',
            'philosophical_importance': 'philosophical importance',
        }

        for field, description in recommended_fields.items():
            if field not in node or not node[field]:
                issues.append(f"Missing {description}")

    return issues

def audit_required_fields(node: Dict) -> List[str]:
    """Check if node has all required fields"""
    issues = []
    required = ['id', 'label', 'type', 'category', 'description']

    for field in required:
        if field not in node:
            issues.append(f"Missing required field: {field}")
        elif not node[field]:
            issues.append(f"Empty required field: {field}")

    return issues

def audit_edge_validity(edge: Dict, node_ids: set) -> List[str]:
    """Check if edge is valid"""
    issues = []

    # Check required fields
    if 'source' not in edge:
        issues.append("Missing source")
    elif edge['source'] not in node_ids:
        issues.append(f"Source node not found: {edge['source']}")

    if 'target' not in edge:
        issues.append("Missing target")
    elif edge['target'] not in node_ids:
        issues.append(f"Target node not found: {edge['target']}")

    if 'relation' not in edge:
        issues.append("Missing relation")
    elif edge['relation'] not in VALID_RELATIONS:
        issues.append(f"Invalid relation: '{edge['relation']}'")

    return issues

def audit_description_quality(node: Dict) -> List[str]:
    """Check description quality"""
    issues = []

    if 'description' in node:
        desc = node['description']

        # Too short
        if len(desc) < 50:
            issues.append("Description too brief (< 50 chars)")

        # Check for placeholder text
        placeholders = ['to be added', 'tba', '[add', 'TODO', 'FIXME']
        if any(ph.lower() in desc.lower() for ph in placeholders):
            issues.append("Description contains placeholder text")

    return issues

# ============================================================================
# ENHANCEMENT OPPORTUNITIES
# ============================================================================

def find_enhancement_opportunities(node: Dict) -> List[str]:
    """Identify opportunities to enhance node"""
    opportunities = []

    # Ancient sources but no modern scholarship
    if node.get('ancient_sources') and not node.get('modern_scholarship'):
        opportunities.append("Add modern scholarship references")

    # Concept with English but no Greek/Latin
    if node['type'] == 'concept' and node.get('english_term'):
        if not node.get('greek_term') and not node.get('latin_term'):
            opportunities.append("Add Greek or Latin terminology")

    # Person with school but no position on free will
    if node['type'] == 'person' and node.get('school'):
        if not node.get('position_on_free_will'):
            opportunities.append("Add explicit position on free will")

    # Short description could be expanded
    if node.get('description') and 50 < len(node['description']) < 200:
        opportunities.append("Description could be expanded (currently brief)")

    # Has sources but no key_concepts
    if (node.get('ancient_sources') or node.get('modern_scholarship')):
        if not node.get('key_concepts'):
            opportunities.append("Add key concepts array")

    return opportunities

# ============================================================================
# MAIN AUDIT
# ============================================================================

def audit_database(db: Dict) -> Dict:
    """Perform comprehensive database audit"""

    nodes = db['nodes']
    edges = db['edges']
    node_ids = {n['id'] for n in nodes}

    report = {
        'summary': {},
        'critical_issues': [],
        'warnings': [],
        'enhancements': [],
        'node_type_stats': Counter(),
        'relation_stats': Counter(),
    }

    # Audit nodes
    for node in nodes:
        node_issues = {
            'node_id': node['id'],
            'label': node['label'],
            'type': node['type'],
            'issues': [],
            'enhancements': []
        }

        # Run all audit functions
        node_issues['issues'].extend(audit_required_fields(node))
        node_issues['issues'].extend(audit_node_id_format(node))
        node_issues['issues'].extend(audit_controlled_vocabulary(node))
        node_issues['issues'].extend(audit_citations(node))
        node_issues['issues'].extend(audit_greek_latin_terminology(node))
        node_issues['issues'].extend(audit_person_completeness(node))
        node_issues['issues'].extend(audit_concept_completeness(node))
        node_issues['issues'].extend(audit_argument_completeness(node))
        node_issues['issues'].extend(audit_description_quality(node))

        # Find enhancement opportunities
        node_issues['enhancements'].extend(find_enhancement_opportunities(node))

        # Categorize by severity
        critical_keywords = ['missing required', 'invalid', 'not found']
        has_critical = any(
            any(kw in issue.lower() for kw in critical_keywords)
            for issue in node_issues['issues']
        )

        if has_critical or len(node_issues['issues']) >= 3:
            report['critical_issues'].append(node_issues)
        elif node_issues['issues'] or node_issues['enhancements']:
            report['warnings'].append(node_issues)

        # Count by type
        report['node_type_stats'][node['type']] += 1

    # Audit edges
    edge_issues_count = 0
    for i, edge in enumerate(edges):
        issues = audit_edge_validity(edge, node_ids)
        if issues:
            edge_issues_count += 1
            report['critical_issues'].append({
                'edge_index': i,
                'source': edge.get('source', 'MISSING'),
                'target': edge.get('target', 'MISSING'),
                'relation': edge.get('relation', 'MISSING'),
                'issues': issues,
                'enhancements': []
            })

        # Count relations
        if 'relation' in edge:
            report['relation_stats'][edge['relation']] += 1

    # Generate summary statistics
    report['summary'] = {
        'total_nodes': len(nodes),
        'total_edges': len(edges),
        'nodes_with_critical_issues': len([n for n in report['critical_issues'] if 'node_id' in n]),
        'nodes_with_warnings': len(report['warnings']),
        'edges_with_issues': edge_issues_count,
        'total_issues': sum(len(n['issues']) for n in report['critical_issues'] + report['warnings']),
        'enhancement_opportunities': sum(len(n['enhancements']) for n in report['warnings']),
        'academic_quality_score': 0.0  # Calculate below
    }

    # Calculate academic quality score (0-100)
    total = len(nodes)
    with_citations = sum(1 for n in nodes if n.get('ancient_sources') or n.get('modern_scholarship'))
    with_complete_info = total - len(report['critical_issues'])

    citation_score = (with_citations / total) * 50 if total > 0 else 0
    completeness_score = (with_complete_info / total) * 50 if total > 0 else 0
    report['summary']['academic_quality_score'] = round(citation_score + completeness_score, 1)

    return report

# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_text_report(report: Dict, output_file='DATABASE_AUDIT_REPORT.md'):
    """Generate human-readable markdown report"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Database Academic Quality Audit Report\n\n")
        f.write(f"**Generated**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Executive Summary
        f.write("## Executive Summary\n\n")
        s = report['summary']
        f.write(f"- **Total Nodes**: {s['total_nodes']}\n")
        f.write(f"- **Total Edges**: {s['total_edges']}\n")
        f.write(f"- **Academic Quality Score**: {s['academic_quality_score']}/100\n")
        f.write(f"- **Nodes with Critical Issues**: {s['nodes_with_critical_issues']}\n")
        f.write(f"- **Nodes with Warnings**: {s['nodes_with_warnings']}\n")
        f.write(f"- **Enhancement Opportunities**: {s['enhancement_opportunities']}\n\n")

        # Quality Assessment
        score = s['academic_quality_score']
        if score >= 90:
            assessment = "Excellent - Publication ready"
        elif score >= 75:
            assessment = "Good - Minor improvements recommended"
        elif score >= 60:
            assessment = "Fair - Notable improvements needed"
        else:
            assessment = "Needs Work - Significant improvements required"

        f.write(f"**Assessment**: {assessment}\n\n")

        f.write("---\n\n")

        # Critical Issues
        f.write("## Critical Issues\n\n")
        if report['critical_issues']:
            f.write(f"Found {len(report['critical_issues'])} nodes/edges with critical issues.\n\n")
            for item in report['critical_issues'][:20]:  # First 20
                if 'node_id' in item:
                    f.write(f"### {item['label']} (`{item['node_id']}`)\n\n")
                    f.write(f"**Type**: {item['type']}\n\n")
                else:
                    f.write(f"### Edge {item.get('edge_index', '?')}\n\n")

                f.write("**Issues**:\n")
                for issue in item['issues']:
                    f.write(f"- ❌ {issue}\n")
                f.write("\n")

            if len(report['critical_issues']) > 20:
                f.write(f"... and {len(report['critical_issues']) - 20} more critical issues.\n\n")
        else:
            f.write("✓ No critical issues found!\n\n")

        f.write("---\n\n")

        # Warnings
        f.write("## Warnings and Recommendations\n\n")
        if report['warnings']:
            f.write(f"Found {len(report['warnings'])} nodes with warnings or missing optional fields.\n\n")
            for item in report['warnings'][:10]:  # First 10
                f.write(f"### {item['label']} (`{item['node_id']}`)\n\n")

                if item['issues']:
                    f.write("**Issues**:\n")
                    for issue in item['issues']:
                        f.write(f"- ⚠️ {issue}\n")
                    f.write("\n")

                if item['enhancements']:
                    f.write("**Enhancement Opportunities**:\n")
                    for enh in item['enhancements']:
                        f.write(f"- 💡 {enh}\n")
                    f.write("\n")

            if len(report['warnings']) > 10:
                f.write(f"... and {len(report['warnings']) - 10} more warnings.\n\n")
        else:
            f.write("✓ No warnings!\n\n")

        f.write("---\n\n")

        # Statistics
        f.write("## Database Statistics\n\n")
        f.write("### Node Types\n\n")
        for ntype, count in sorted(report['node_type_stats'].items(), key=lambda x: -x[1]):
            f.write(f"- {ntype}: {count}\n")

        f.write("\n### Top Relation Types\n\n")
        for rel, count in report['relation_stats'].most_common(10):
            f.write(f"- {rel}: {count}\n")

        f.write("\n---\n\n")

        # Recommendations
        f.write("## Recommendations for Enhancement\n\n")
        f.write("### Priority 1: Address Critical Issues\n\n")
        f.write("Work with Claude using the Agent Skill to:\n")
        f.write("1. Fix all nodes with missing required fields\n")
        f.write("2. Correct invalid controlled vocabulary usage\n")
        f.write("3. Repair malformed node IDs\n")
        f.write("4. Add missing citations to critical node types\n\n")

        f.write("### Priority 2: Complete Missing Data\n\n")
        f.write("Systematically add:\n")
        f.write("1. Ancient sources for all concepts and arguments\n")
        f.write("2. Modern scholarship references\n")
        f.write("3. Greek/Latin terminology for concepts\n")
        f.write("4. Complete person information (dates, school, position)\n\n")

        f.write("### Priority 3: Enhance Academic Quality\n\n")
        f.write("1. Expand brief descriptions\n")
        f.write("2. Add key concepts arrays\n")
        f.write("3. Cross-reference related nodes\n")
        f.write("4. Verify all citations against sources\n\n")

        f.write("---\n\n")
        f.write("**Next Steps**: Use this report with Claude and the Agent Skill to systematically improve the database.\n")

    print(f"✓ Report generated: {output_file}")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("ANCIENT FREE WILL DATABASE - ACADEMIC QUALITY AUDIT")
    print("=" * 70)
    print()

    # Load database
    print("Loading database...")
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, '..', 'ancient_free_will_database.json')
    db = load_database(db_path)
    print(f"✓ Loaded {len(db['nodes'])} nodes and {len(db['edges'])} edges")
    print()

    # Run audit
    print("Running comprehensive audit...")
    report = audit_database(db)
    print("✓ Audit complete")
    print()

    # Generate report
    print("Generating report...")
    report_path = os.path.join(script_dir, '..', 'DATABASE_AUDIT_REPORT.md')
    generate_text_report(report, report_path)
    print()

    # Display summary
    print("=" * 70)
    print("AUDIT SUMMARY")
    print("=" * 70)
    s = report['summary']
    print(f"Academic Quality Score: {s['academic_quality_score']}/100")
    print(f"Critical Issues: {s['nodes_with_critical_issues']} nodes")
    print(f"Warnings: {s['nodes_with_warnings']} nodes")
    print(f"Enhancement Opportunities: {s['enhancement_opportunities']}")
    print()
    print(f"See DATABASE_AUDIT_REPORT.md for full details.")
    print("=" * 70)
