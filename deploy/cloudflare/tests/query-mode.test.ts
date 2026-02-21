/**
 * Tests for Query Mode Service (philological mode detection)
 */

import { describe, it, expect } from 'vitest';
import { isPhilologicalQuery } from '../src/services/query-mode';

describe('isPhilologicalQuery', () => {
  it('should detect "exact arguments" pattern', () => {
    expect(isPhilologicalQuery("What are Origen's exact arguments for free will?")).toBe(true);
  });

  it('should detect "close reading" pattern', () => {
    expect(isPhilologicalQuery('Provide a close reading of De Fato 39.')).toBe(true);
  });

  it('should detect "philological" pattern', () => {
    expect(isPhilologicalQuery('Give a philological analysis of this passage.')).toBe(true);
  });

  it('should detect "what exactly does X say" pattern', () => {
    expect(isPhilologicalQuery('What exactly does Chrysippus say about fate?')).toBe(true);
  });

  it('should detect "what exactly did X say" pattern', () => {
    expect(isPhilologicalQuery('What exactly did Alexander say about determinism?')).toBe(true);
  });

  it('should detect "Greek term" pattern', () => {
    expect(isPhilologicalQuery('What is the Greek term for free will in the Stoics?')).toBe(true);
  });

  it('should detect "Latin term" pattern', () => {
    expect(isPhilologicalQuery('Explain the Latin term liberum arbitrium.')).toBe(true);
  });

  it('should detect "grammatical analysis" pattern', () => {
    expect(isPhilologicalQuery('Provide a grammatical analysis of this Greek sentence.')).toBe(true);
  });

  it('should detect "original Greek text" pattern', () => {
    expect(isPhilologicalQuery('Show me the original Greek text of this passage.')).toBe(true);
  });

  it('should detect "exegesis of" pattern', () => {
    expect(isPhilologicalQuery('Provide an exegesis of De Principiis III.1.')).toBe(true);
  });

  it('should detect "literal meaning" pattern', () => {
    expect(isPhilologicalQuery('What is the literal meaning of αὐτεξούσιον?')).toBe(true);
  });

  it('should NOT trigger on general questions', () => {
    expect(isPhilologicalQuery('What is Stoic free will?')).toBe(false);
  });

  it('should NOT trigger on comparative questions', () => {
    expect(isPhilologicalQuery('How do the Stoics differ from the Epicureans on fate?')).toBe(false);
  });

  it('should NOT trigger on simple entity questions', () => {
    expect(isPhilologicalQuery('Who was Chrysippus?')).toBe(false);
  });

  it('should NOT trigger on temporal questions', () => {
    expect(isPhilologicalQuery('How did views on free will evolve from the Presocratics to the Stoics?')).toBe(false);
  });

  it('should be case-insensitive', () => {
    expect(isPhilologicalQuery('WHAT ARE THE EXACT ARGUMENTS for determinism?')).toBe(true);
    expect(isPhilologicalQuery('Close Reading of De Fato.')).toBe(true);
  });
});
