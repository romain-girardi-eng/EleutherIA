import { useCallback, useRef, type RefObject } from 'react';
import {
  Cosmograph,
  type CosmographConfig,
  type CosmographProps,
  type CosmographRef,
} from '@cosmograph/react';

const COSMOGRAPH_CANVAS_STYLE = { width: '100%', height: '100%' } as const;

export interface StableCosmographHandlers {
  onMount: NonNullable<CosmographProps['onMount']>;
  onGraphRebuilt: NonNullable<CosmographProps['onGraphRebuilt']>;
  onSimulationStart: NonNullable<CosmographProps['onSimulationStart']>;
  onSimulationUnpause: NonNullable<CosmographProps['onSimulationUnpause']>;
  onSimulationPause: NonNullable<CosmographProps['onSimulationPause']>;
  onSimulationEnd: NonNullable<CosmographProps['onSimulationEnd']>;
  onZoom: NonNullable<CosmographProps['onZoom']>;
  onPointClick: NonNullable<CosmographProps['onPointClick']>;
  onLabelClick: NonNullable<CosmographProps['onLabelClick']>;
  onBackgroundClick: NonNullable<CosmographProps['onBackgroundClick']>;
}

/**
 * Keep Cosmograph's expensive config identity stable across workspace-only
 * renders. The upstream React wrapper calls `setConfig` whenever its rest-props
 * object changes; without this boundary, persisting a camera frame can reload
 * the WebGL renderer and snap an authored transition back to the overview.
 */
export default function StableCosmographCanvas({
  config,
  revision,
  graphRef,
  handlers,
}: {
  config: Partial<CosmographConfig>;
  revision: object;
  graphRef: RefObject<CosmographRef>;
  handlers: StableCosmographHandlers;
}) {
  const handlersRef = useRef(handlers);
  handlersRef.current = handlers;
  const configRef = useRef({ revision, config });
  if (configRef.current.revision !== revision) {
    configRef.current = { revision, config };
  }

  const onMount = useCallback<StableCosmographHandlers['onMount']>(
    (...args) => handlersRef.current.onMount(...args),
    [],
  );
  const onSimulationStart = useCallback<StableCosmographHandlers['onSimulationStart']>(
    (...args) => handlersRef.current.onSimulationStart(...args),
    [],
  );
  const onGraphRebuilt = useCallback<StableCosmographHandlers['onGraphRebuilt']>(
    (...args) => handlersRef.current.onGraphRebuilt(...args),
    [],
  );
  const onSimulationUnpause = useCallback<StableCosmographHandlers['onSimulationUnpause']>(
    (...args) => handlersRef.current.onSimulationUnpause(...args),
    [],
  );
  const onSimulationPause = useCallback<StableCosmographHandlers['onSimulationPause']>(
    (...args) => handlersRef.current.onSimulationPause(...args),
    [],
  );
  const onSimulationEnd = useCallback<StableCosmographHandlers['onSimulationEnd']>(
    (...args) => handlersRef.current.onSimulationEnd(...args),
    [],
  );
  const onZoom = useCallback<StableCosmographHandlers['onZoom']>(
    (...args) => handlersRef.current.onZoom(...args),
    [],
  );
  const onPointClick = useCallback<StableCosmographHandlers['onPointClick']>(
    (...args) => handlersRef.current.onPointClick(...args),
    [],
  );
  const onLabelClick = useCallback<StableCosmographHandlers['onLabelClick']>(
    (...args) => handlersRef.current.onLabelClick(...args),
    [],
  );
  const onBackgroundClick = useCallback<StableCosmographHandlers['onBackgroundClick']>(
    (...args) => handlersRef.current.onBackgroundClick(...args),
    [],
  );

  return (
    <Cosmograph
      {...configRef.current.config}
      ref={graphRef}
      onMount={onMount}
      onGraphRebuilt={onGraphRebuilt}
      onSimulationStart={onSimulationStart}
      onSimulationUnpause={onSimulationUnpause}
      onSimulationPause={onSimulationPause}
      onSimulationEnd={onSimulationEnd}
      onZoom={onZoom}
      onPointClick={onPointClick}
      onLabelClick={onLabelClick}
      onBackgroundClick={onBackgroundClick}
      style={COSMOGRAPH_CANVAS_STYLE}
    />
  );
}
