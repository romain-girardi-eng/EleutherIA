import { describe, expect, it } from 'vitest';

import { glossary } from './glossary';

const byId = new Map(glossary.map((entry) => [entry.id, entry]));

function definition(id: string): string {
  const entry = byId.get(id);
  expect(entry, `missing glossary entry ${id}`).toBeDefined();
  return entry?.definition ?? '';
}

describe('source-collated glossary contract', () => {
  it('keeps the reviewed cohort unique and bound to canonical graph routes', () => {
    expect(glossary).toHaveLength(27);
    expect(new Set(glossary.map((entry) => entry.id)).size).toBe(27);
    for (const entry of glossary) {
      expect(entry.nodeUrl).toBe(`/visualizer/${entry.id}`);
      expect(entry.definition.length).toBeGreaterThan(180);
    }
  });

  it('does not revive the blocked factual claims from the first audit', () => {
    const serialized = JSON.stringify(glossary);
    expect(serialized).not.toContain('ἀσύμβατον');
    expect(serialized).not.toContain('distinctively Christian concept');
    expect(serialized).not.toContain('reported in the doxography (Diogenes Laertius X)');
    expect(definition('concept_clinamen_atomic_swerve_epicurus_m3n4o5p6')).toContain(
      'does not mention the swerve',
    );
    expect(definition('concept_cylinder_analogy_chrysippus_e5f6g7h8')).toContain(
      'do not unambiguously establish',
    );
  });

  it('locks the corrected loci and disputed-status boundaries', () => {
    expect(definition('concept_divine_prescience')).toContain('De oratione 6.3');
    expect(definition('concept_divine_prescience')).toContain('later shorthand');
    expect(definition('concept_heimarmene_fate_stoics_j0k1l2m3')).toContain(
      'SVF II.1000',
    );
    expect(definition('concept_libertas_indifferentiae_4f8a9b57')).toContain(
      'lowest grade of freedom',
    );
    expect(definition('concept_tuche_chance_alex')).toContain(
      'Bruns 172.17–174.28',
    );
  });

  it('keeps PAP, modality, and Latin genealogy corrections explicit', () => {
    expect(definition('concept_principle_alternative_possibilities_5s6t7u8v')).toContain(
      'Consequence Argument supports incompatibilism',
    );
    expect(definition('concept_endechomenon_contingent_aristotle_e5f6g7h8')).toContain(
      'exact status he gives their present truth values is disputed',
    );
    expect(definition('concept_liberum_arbitrium_u3v4w5x6')).toContain('De anima 21.6');
  });
});
