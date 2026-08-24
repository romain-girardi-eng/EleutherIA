import type { CosmographConfig } from '@cosmograph/react';

let preparationQueue: Promise<void> = Promise.resolve();

/** Cosmograph's data-kit coalesces concurrent calls globally, even when their
 * datasets differ. Start each preparation only after the previous one has
 * settled so every caller receives Arrow data for its own requested slice. */
export function enqueueCosmographPreparation<T>(task: () => Promise<T>): Promise<T> {
  const result = preparationQueue.then(task, task);
  preparationQueue = result.then(
    () => undefined,
    () => undefined,
  );
  return result;
}

/**
 * `prepareCosmographData` rewrites arbitrary source columns into this stable
 * Arrow schema. Cosmograph 2.3 validates these mappings before reading the
 * prepared tables, so keep them explicit even if the data-kit result omits a
 * mapping during a concurrent/StrictMode preparation cycle.
 */
export function preparedCosmographContract(
  config: Omit<CosmographConfig, 'points' | 'links'>,
  hasLinks: boolean,
): Omit<CosmographConfig, 'points' | 'links'> {
  return {
    ...config,
    pointIdBy: 'id',
    pointIndexBy: 'idx',
    ...(hasLinks
      ? {
          linkSourceBy: 'source',
          linkSourceIndexBy: 'sourceidx',
          linkTargetBy: 'target',
          linkTargetIndexBy: 'targetidx',
        }
      : {}),
  };
}
