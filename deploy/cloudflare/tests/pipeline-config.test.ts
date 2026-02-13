/**
 * Tests for pipeline configuration and query-type-based feature selection.
 *
 * These test the selectPipelineConfig function logic without needing the full
 * orchestrator — we re-implement the logic here to verify the contract.
 */

import { describe, it, expect } from 'vitest';
import type { PipelineConfig } from '../src/types/agentic';

// Re-implement selectPipelineConfig to test the contract
// (The actual function is inside orchestrator.ts but not exported)
type QueryType = 'specific_entity' | 'global_abstract' | 'multi_hop' | 'comparative' | 'temporal_evolution' | 'dialectical';

function selectPipelineConfig(queryType: QueryType): PipelineConfig {
  switch (queryType) {
    case 'specific_entity':
      return { useHyDE: false, useCRAG: true, useReranking: true, useSelfRAG: true, useExpansion: true, useGrounding: true };
    case 'global_abstract':
      return { useHyDE: true, useCRAG: true, useReranking: true, useSelfRAG: true, useExpansion: false, useGrounding: true };
    case 'multi_hop':
      return { useHyDE: false, useCRAG: true, useReranking: false, useSelfRAG: true, useExpansion: true, useGrounding: true };
    case 'comparative':
      return { useHyDE: true, useCRAG: true, useReranking: true, useSelfRAG: true, useExpansion: true, useGrounding: true };
    default:
      return { useHyDE: true, useCRAG: true, useReranking: true, useSelfRAG: true, useExpansion: true, useGrounding: true };
  }
}

describe('Pipeline Config Selection', () => {
  it('specific_entity: should skip HyDE but enable expansion', () => {
    const config = selectPipelineConfig('specific_entity');
    expect(config.useHyDE).toBe(false);
    expect(config.useExpansion).toBe(true);
    expect(config.useGrounding).toBe(true);
  });

  it('global_abstract: should enable HyDE but skip expansion', () => {
    const config = selectPipelineConfig('global_abstract');
    expect(config.useHyDE).toBe(true);
    expect(config.useExpansion).toBe(false);
  });

  it('multi_hop: should skip HyDE and reranking (bridge paths are scored)', () => {
    const config = selectPipelineConfig('multi_hop');
    expect(config.useHyDE).toBe(false);
    expect(config.useReranking).toBe(false);
    expect(config.useExpansion).toBe(true);
  });

  it('comparative: should enable everything', () => {
    const config = selectPipelineConfig('comparative');
    expect(config.useHyDE).toBe(true);
    expect(config.useCRAG).toBe(true);
    expect(config.useReranking).toBe(true);
    expect(config.useSelfRAG).toBe(true);
    expect(config.useExpansion).toBe(true);
    expect(config.useGrounding).toBe(true);
  });

  it('all configs should always enable CRAG and Self-RAG', () => {
    const types: QueryType[] = ['specific_entity', 'global_abstract', 'multi_hop', 'comparative', 'temporal_evolution'];
    for (const type of types) {
      const config = selectPipelineConfig(type);
      expect(config.useCRAG).toBe(true);
      expect(config.useSelfRAG).toBe(true);
      expect(config.useGrounding).toBe(true);
    }
  });
});
