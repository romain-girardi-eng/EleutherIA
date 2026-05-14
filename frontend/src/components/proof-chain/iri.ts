/**
 * IRI utilities for proof-chain rendering.
 *
 * Shortens EleutherIA IRIs into human-readable CURIEs used in the
 * derivation panel:
 *   https://free-will.app/kg/X       -> res:X
 *   https://free-will.app/ontology/X -> kg:X
 *
 * Unknown IRIs are returned untouched so the caller can display them
 * verbatim. Pure functions, no side effects, deterministic — safe to
 * call inside render.
 */

const KG_PREFIX = 'https://free-will.app/kg/';
const ONTOLOGY_PREFIX = 'https://free-will.app/ontology/';

export interface ShortIri {
  /** Original IRI (always preserved for tooltips / debugging). */
  readonly iri: string;
  /** Display form: `res:foo`, `kg:wrote`, or the original IRI. */
  readonly display: string;
  /** Local name only, without prefix. Useful when joining with a node label. */
  readonly local: string;
  /** The curie prefix, when matched. */
  readonly prefix: 'res' | 'kg' | null;
}

export function shortenIri(iri: string): ShortIri {
  if (iri.startsWith(KG_PREFIX)) {
    const local = iri.slice(KG_PREFIX.length);
    return { iri, display: `res:${local}`, local, prefix: 'res' };
  }
  if (iri.startsWith(ONTOLOGY_PREFIX)) {
    const local = iri.slice(ONTOLOGY_PREFIX.length);
    return { iri, display: `kg:${local}`, local, prefix: 'kg' };
  }
  return { iri, display: iri, local: iri, prefix: null };
}
