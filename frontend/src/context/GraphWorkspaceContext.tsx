import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useReducer,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';

import { apiClient, workspaceReleaseMismatchFromError } from '../api/client';
import {
  buildAtlasMeta,
  type AtlasEdgeMeta,
  type AtlasNodeMeta,
} from '../components/cosmograph/AtlasHelpers';
import type { KgFilterState } from '../components/cosmograph/KgFilters';
import {
  buildRelationships,
  loadCompleteKnowledgeGraph,
  type GraphRelationships,
} from '../components/cosmograph/graphRuntime';
import type { KGNode } from '../types';

export type GraphWorkspaceMode = 'atlas' | 'chronos' | 'scholar';

export interface GraphTimeWindow {
  start: number | null;
  end: number | null;
}

export interface GraphCameraState {
  x: number;
  y: number;
  zoom: number;
}

export interface GraphWorkspaceState {
  mode: GraphWorkspaceMode;
  releaseId: string | null;
  primarySelection: string | null;
  compareIds: string[];
  evidenceThread: string[];
  filters: KgFilterState;
  timeWindow: GraphTimeWindow;
  cameraByMode: Record<GraphWorkspaceMode, GraphCameraState | null>;
}

export interface GraphWorkspaceHistory {
  past: GraphWorkspaceState[];
  present: GraphWorkspaceState;
  future: GraphWorkspaceState[];
}

export interface GraphWorkspaceData {
  meta: ReadonlyArray<AtlasNodeMeta>;
  edges: ReadonlyArray<AtlasEdgeMeta>;
  rawById: Map<string, KGNode>;
  relationships: GraphRelationships;
}

export interface GraphNodeDetailState {
  loading: boolean;
  error: Error | null;
}

export const EMPTY_GRAPH_WORKSPACE_DATA: GraphWorkspaceData = {
  meta: [],
  edges: [],
  rawById: new Map(),
  relationships: new Map(),
};

const MODES: readonly GraphWorkspaceMode[] = ['atlas', 'chronos', 'scholar'];
const MODE_SHORTCUTS: Readonly<Record<string, GraphWorkspaceMode>> = {
  Digit1: 'atlas',
  Digit2: 'chronos',
  Digit3: 'scholar',
};
const MAX_COMPARE = 4;
const MAX_HISTORY = 60;
const MAX_URL_LIST = 50;

export class GraphReleaseMismatchError extends Error {
  readonly requestedRelease: string;
  readonly servedRelease: string;

  constructor(requested: string, served: string) {
    super(
      `This permalink targets graph release ${requested}, but the API serves ${served}. `
      + 'The workspace will not silently substitute a different scholarly release.',
    );
    this.name = 'GraphReleaseMismatchError';
    this.requestedRelease = requested;
    this.servedRelease = served;
  }
}

export const DEFAULT_GRAPH_WORKSPACE_STATE: GraphWorkspaceState = {
  mode: 'atlas',
  releaseId: null,
  primarySelection: null,
  compareIds: [],
  evidenceThread: [],
  filters: { periods: [], types: [], schools: [] },
  timeWindow: { start: null, end: null },
  cameraByMode: { atlas: null, chronos: null, scholar: null },
};

type WorkspaceAction =
  | { type: 'commit'; next: GraphWorkspaceState }
  | { type: 'patch'; patch: Partial<GraphWorkspaceState> }
  | { type: 'toggle_compare'; nodeId: string }
  | { type: 'camera'; mode: GraphWorkspaceMode; camera: GraphCameraState | null }
  | { type: 'hydrate'; next: GraphWorkspaceState }
  | { type: 'release'; releaseId: string }
  | { type: 'undo' }
  | { type: 'redo' };

function unique(values: ReadonlyArray<string>, limit = MAX_URL_LIST): string[] {
  return [...new Set(values.map((value) => value.trim()).filter(Boolean))].slice(0, limit);
}

function finiteOrNull(value: number | null | undefined): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function normalizeCamera(value: GraphCameraState | null | undefined): GraphCameraState | null {
  if (!value) return null;
  const x = finiteOrNull(value.x);
  const y = finiteOrNull(value.y);
  const zoom = finiteOrNull(value.zoom);
  if (x === null || y === null || zoom === null || zoom <= 0) return null;
  return { x, y, zoom };
}

export function normalizeGraphWorkspaceState(
  value: Partial<GraphWorkspaceState>,
): GraphWorkspaceState {
  const mode = MODES.includes(value.mode as GraphWorkspaceMode)
    ? (value.mode as GraphWorkspaceMode)
    : 'atlas';
  const compareIds = unique(value.compareIds ?? [], MAX_COMPARE);
  const start = finiteOrNull(value.timeWindow?.start);
  const end = finiteOrNull(value.timeWindow?.end);
  const orderedWindow = start !== null && end !== null && start > end
    ? { start: end, end: start }
    : { start, end };

  return {
    mode,
    releaseId:
      typeof value.releaseId === 'string' && value.releaseId.trim()
        ? value.releaseId.trim().slice(0, 160)
        : null,
    primarySelection:
      typeof value.primarySelection === 'string' && value.primarySelection.trim()
        ? value.primarySelection.trim().slice(0, 300)
        : null,
    compareIds,
    evidenceThread: unique(value.evidenceThread ?? [], 24),
    filters: {
      periods: unique(value.filters?.periods ?? []).sort(),
      types: unique(value.filters?.types ?? []).sort(),
      schools: unique(value.filters?.schools ?? []).sort(),
    },
    timeWindow: orderedWindow,
    cameraByMode: {
      atlas: normalizeCamera(value.cameraByMode?.atlas),
      chronos: normalizeCamera(value.cameraByMode?.chronos),
      scholar: normalizeCamera(value.cameraByMode?.scholar),
    },
  };
}

function stateFingerprint(state: GraphWorkspaceState): string {
  return JSON.stringify(normalizeGraphWorkspaceState(state));
}

export function graphWorkspaceReducer(
  history: GraphWorkspaceHistory,
  action: WorkspaceAction,
): GraphWorkspaceHistory {
  if (action.type === 'hydrate') {
    return { past: [], present: normalizeGraphWorkspaceState(action.next), future: [] };
  }
  if (action.type === 'release') {
    const carryRelease = (state: GraphWorkspaceState) => ({
      ...state,
      releaseId: action.releaseId,
    });
    return {
      past: history.past.map(carryRelease),
      present: carryRelease(history.present),
      future: history.future.map(carryRelease),
    };
  }
  if (action.type === 'undo') {
    const previous = history.past.at(-1);
    if (!previous) return history;
    return {
      past: history.past.slice(0, -1),
      present: previous,
      future: [history.present, ...history.future].slice(0, MAX_HISTORY),
    };
  }
  if (action.type === 'redo') {
    const next = history.future[0];
    if (!next) return history;
    return {
      past: [...history.past, history.present].slice(-MAX_HISTORY),
      present: next,
      future: history.future.slice(1),
    };
  }
  if (action.type === 'camera') {
    return {
      ...history,
      present: normalizeGraphWorkspaceState({
        ...history.present,
        cameraByMode: {
          ...history.present.cameraByMode,
          [action.mode]: action.camera,
        },
      }),
    };
  }

  let candidate: GraphWorkspaceState;
  if (action.type === 'patch') {
    candidate = { ...history.present, ...action.patch };
  } else if (action.type === 'toggle_compare') {
    const exists = history.present.compareIds.includes(action.nodeId);
    candidate = {
      ...history.present,
      compareIds: exists
        ? history.present.compareIds.filter((id) => id !== action.nodeId)
        : [...history.present.compareIds, action.nodeId].slice(-MAX_COMPARE),
    };
  } else {
    candidate = action.next;
  }

  const next = normalizeGraphWorkspaceState(candidate);
  if (stateFingerprint(next) === stateFingerprint(history.present)) return history;
  return {
    past: [...history.past, history.present].slice(-MAX_HISTORY),
    present: next,
    future: [],
  };
}

function appendMany(params: URLSearchParams, key: string, values: ReadonlyArray<string>) {
  values.forEach((value) => params.append(key, value));
}

function cameraParam(camera: GraphCameraState | null): string | null {
  if (!camera) return null;
  return [camera.x, camera.y, camera.zoom]
    .map((value) => Number(value.toFixed(4)).toString())
    .join(',');
}

export function serializeGraphWorkspaceState(state: GraphWorkspaceState): string {
  const normalized = normalizeGraphWorkspaceState(state);
  const params = new URLSearchParams();
  params.set('workspace', '1');
  if (normalized.mode !== 'atlas') params.set('mode', normalized.mode);
  if (normalized.releaseId) params.set('release', normalized.releaseId);
  if (normalized.primarySelection) params.set('node', normalized.primarySelection);
  appendMany(params, 'compare', normalized.compareIds);
  appendMany(params, 'thread', normalized.evidenceThread);
  appendMany(params, 'type', normalized.filters.types);
  appendMany(params, 'period', normalized.filters.periods);
  appendMany(params, 'school', normalized.filters.schools);
  if (normalized.timeWindow.start !== null) {
    params.set('from', normalized.timeWindow.start.toString());
  }
  if (normalized.timeWindow.end !== null) {
    params.set('to', normalized.timeWindow.end.toString());
  }
  MODES.forEach((mode) => {
    const encoded = cameraParam(normalized.cameraByMode[mode]);
    if (encoded) params.set(`camera_${mode}`, encoded);
  });
  return params.toString();
}

function parseNumber(value: string | null): number | null {
  if (value === null || value.trim() === '') return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function parseCamera(value: string | null): GraphCameraState | null {
  if (!value) return null;
  const [x, y, zoom, ...extra] = value.split(',').map(Number);
  if (extra.length > 0) return null;
  return normalizeCamera({ x, y, zoom });
}

export function deserializeGraphWorkspaceState(
  search: string,
  pathNodeId?: string | null,
): GraphWorkspaceState {
  const params = new URLSearchParams(search.startsWith('?') ? search.slice(1) : search);
  const mode = params.get('mode') as GraphWorkspaceMode | null;
  return normalizeGraphWorkspaceState({
    ...DEFAULT_GRAPH_WORKSPACE_STATE,
    mode: mode ?? 'atlas',
    releaseId: params.get('release'),
    primarySelection: params.get('node') ?? pathNodeId ?? null,
    compareIds: params.getAll('compare'),
    evidenceThread: params.getAll('thread'),
    filters: {
      types: params.getAll('type'),
      periods: params.getAll('period'),
      schools: params.getAll('school'),
    },
    timeWindow: {
      start: parseNumber(params.get('from')),
      end: parseNumber(params.get('to')),
    },
    cameraByMode: {
      atlas: parseCamera(params.get('camera_atlas')),
      chronos: parseCamera(params.get('camera_chronos')),
      scholar: parseCamera(params.get('camera_scholar')),
    },
  });
}

type GraphLoader = typeof loadCompleteKnowledgeGraph;

let sharedGraphLoad: ReturnType<GraphLoader> | null = null;
const defaultGraphLoader: GraphLoader = (client, pageSize) => {
  if (!sharedGraphLoad) {
    const request = loadCompleteKnowledgeGraph(client, pageSize);
    sharedGraphLoad = request;
    const releaseSharedRequest = () => {
      if (sharedGraphLoad === request) sharedGraphLoad = null;
    };
    // Coalesce concurrent StrictMode/effect callers, but do not retain the
    // resolved raw edge array after the provider has built its compact indexes.
    void request.then(releaseSharedRequest, releaseSharedRequest);
  }
  return sharedGraphLoad;
};

export interface GraphWorkspaceStore {
  state: GraphWorkspaceState;
  data: GraphWorkspaceData;
  loading: boolean;
  error: Error | null;
  nodeDetailStates: ReadonlyMap<string, GraphNodeDetailState>;
  canUndo: boolean;
  canRedo: boolean;
  permalink: string;
  setMode: (mode: GraphWorkspaceMode) => void;
  selectPrimary: (nodeId: string | null) => void;
  setCompareIds: (nodeIds: string[]) => void;
  toggleCompare: (nodeId: string) => void;
  setEvidenceThread: (nodeIds: string[]) => void;
  setFilters: (filters: KgFilterState) => void;
  setTimeWindow: (timeWindow: GraphTimeWindow) => void;
  setCamera: (mode: GraphWorkspaceMode, camera: GraphCameraState | null) => void;
  ensureNodeDetail: (nodeId: string) => Promise<void>;
  undo: () => void;
  redo: () => void;
}

const GraphWorkspaceContext = createContext<GraphWorkspaceStore | null>(null);

export function GraphWorkspaceProvider({
  children,
  graphLoader = defaultGraphLoader,
}: {
  children: ReactNode;
  graphLoader?: GraphLoader;
}) {
  const location = useLocation();
  const navigate = useNavigate();
  const { nodeId } = useParams();
  const [history, dispatch] = useReducer(graphWorkspaceReducer, undefined, () => ({
    past: [],
    present: deserializeGraphWorkspaceState(location.search, nodeId),
    future: [],
  }));
  const [data, setData] = useState<GraphWorkspaceData>(EMPTY_GRAPH_WORKSPACE_DATA);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [nodeDetailStates, setNodeDetailStates] = useState<
    ReadonlyMap<string, GraphNodeDetailState>
  >(new Map());
  const [loadedReleaseId, setLoadedReleaseId] = useState<string | null>(null);
  const urlWriteMode = useRef<'push' | 'replace'>('replace');
  const mounted = useRef(false);
  const hydratingFromLocation = useRef(false);
  const graphLoadRef = useRef<ReturnType<GraphLoader> | null>(null);
  const detailLoadsRef = useRef(new Map<string, Promise<void>>());
  const loadedNodeDetailsRef = useRef(new Set<string>());
  const loadedNodeIdsRef = useRef(new Set<string>());
  const requestedReleaseRef = useRef(history.present.releaseId);
  const commitPatch = useCallback((patch: Partial<GraphWorkspaceState>, replace = false) => {
    urlWriteMode.current = replace ? 'replace' : 'push';
    dispatch({ type: 'patch', patch });
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    const request = graphLoadRef.current ?? graphLoader(apiClient);
    graphLoadRef.current = request;
    void request
      .then(({ nodes, edges, release_id }) => {
        graphLoadRef.current = null;
        if (cancelled) return;
        const requestedRelease = requestedReleaseRef.current;
        if (requestedRelease && requestedRelease !== release_id) {
          setLoadedReleaseId(release_id);
          setError(new GraphReleaseMismatchError(requestedRelease, release_id));
          setLoading(false);
          return;
        }
        const built = buildAtlasMeta(nodes, edges);
        detailLoadsRef.current.clear();
        loadedNodeDetailsRef.current.clear();
        loadedNodeIdsRef.current = new Set(nodes.map((node) => node.id));
        setNodeDetailStates(new Map());
        setData({
          meta: built.nodes,
          edges: built.edges,
          rawById: new Map(nodes.map((node) => [node.id, node])),
          relationships: buildRelationships(built.nodes, built.edges),
        });
        setLoadedReleaseId(release_id);
        urlWriteMode.current = 'replace';
        dispatch({ type: 'release', releaseId: release_id });
        setLoading(false);
      })
      .catch((reason: unknown) => {
        graphLoadRef.current = null;
        if (cancelled) return;
        setError(reason instanceof Error ? reason : new Error(String(reason)));
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [graphLoader]);

  useEffect(() => {
    const incoming = deserializeGraphWorkspaceState(location.search, nodeId);
    requestedReleaseRef.current = incoming.releaseId;
    if (loadedReleaseId && incoming.releaseId && incoming.releaseId !== loadedReleaseId) {
      const mismatch = new GraphReleaseMismatchError(incoming.releaseId, loadedReleaseId);
      if (!(error instanceof GraphReleaseMismatchError) || error.message !== mismatch.message) {
        setError(mismatch);
      }
      return;
    }
    if (loadedReleaseId && !incoming.releaseId) {
      incoming.releaseId = loadedReleaseId;
    }
    if (
      error instanceof GraphReleaseMismatchError
      && error.servedRelease === loadedReleaseId
    ) setError(null);
    if (stateFingerprint(incoming) !== stateFingerprint(history.present)) {
      hydratingFromLocation.current = true;
      urlWriteMode.current = 'replace';
      dispatch({ type: 'hydrate', next: incoming });
    }
    // `history.present` is intentionally excluded: this effect consumes only
    // browser navigation, while the next effect owns state -> URL writes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [error, loadedReleaseId, location.key, location.pathname, location.search, nodeId]);

  useEffect(() => {
    if (hydratingFromLocation.current) {
      hydratingFromLocation.current = false;
      return;
    }
    const search = serializeGraphWorkspaceState(history.present);
    const current = location.search.startsWith('?') ? location.search.slice(1) : location.search;
    const keepPublicEntityPath = Boolean(
      nodeId
      && history.present.primarySelection === nodeId
      && location.pathname.startsWith('/visualizer/'),
    );
    const canonicalPath = keepPublicEntityPath
      ? `/visualizer/${encodeURIComponent(nodeId!)}`
      : '/visualizer';
    if (location.pathname === canonicalPath && current === search) {
      mounted.current = true;
      return;
    }
    const replace = !mounted.current || urlWriteMode.current === 'replace';
    mounted.current = true;
    urlWriteMode.current = 'push';
    navigate({ pathname: canonicalPath, search: `?${search}` }, { replace });
  }, [history.present, location.pathname, location.search, navigate, nodeId]);

  const setMode = useCallback((mode: GraphWorkspaceMode) => {
    commitPatch({ mode });
  }, [commitPatch]);

  const selectPrimary = useCallback((primarySelection: string | null) => {
    commitPatch({ primarySelection });
  }, [commitPatch]);

  const setCompareIds = useCallback((compareIds: string[]) => {
    commitPatch({ compareIds: unique(compareIds, MAX_COMPARE) });
  }, [commitPatch]);

  const toggleCompare = useCallback((nodeIdToToggle: string) => {
    urlWriteMode.current = 'push';
    dispatch({ type: 'toggle_compare', nodeId: nodeIdToToggle });
  }, []);

  const setEvidenceThread = useCallback((evidenceThread: string[]) => {
    commitPatch({ evidenceThread: unique(evidenceThread, 24) });
  }, [commitPatch]);

  const setFilters = useCallback((filters: KgFilterState) => {
    commitPatch({ filters });
  }, [commitPatch]);

  const setTimeWindow = useCallback((timeWindow: GraphTimeWindow) => {
    commitPatch({ timeWindow });
  }, [commitPatch]);

  const setCamera = useCallback((mode: GraphWorkspaceMode, camera: GraphCameraState | null) => {
    urlWriteMode.current = 'replace';
    dispatch({ type: 'camera', mode, camera });
  }, []);

  const ensureNodeDetail = useCallback((nodeIdToLoad: string): Promise<void> => {
    const releaseId = loadedReleaseId;
    if (!releaseId || loadedNodeDetailsRef.current.has(nodeIdToLoad)) {
      return Promise.resolve();
    }
    if (!loadedNodeIdsRef.current.has(nodeIdToLoad)) {
      const reason = new Error('The selected node is outside the loaded graph release.');
      setNodeDetailStates((current) => {
        const next = new Map(current);
        next.set(nodeIdToLoad, { loading: false, error: reason });
        return next;
      });
      return Promise.resolve();
    }
    const pending = detailLoadsRef.current.get(nodeIdToLoad);
    if (pending) return pending;

    setNodeDetailStates((current) => {
      const next = new Map(current);
      next.set(nodeIdToLoad, { loading: true, error: null });
      return next;
    });

    const request = apiClient.getWorkspaceNode(nodeIdToLoad, releaseId)
      .then((response) => {
        if (response.release_id !== releaseId) {
          throw new GraphReleaseMismatchError(releaseId, response.release_id ?? 'unknown');
        }
        if (response.node.id !== nodeIdToLoad) {
          throw new Error('The workspace node-detail API returned a different node.');
        }
        loadedNodeDetailsRef.current.add(nodeIdToLoad);
        setData((current) => {
          const summary = current.rawById.get(nodeIdToLoad);
          if (!summary) return current;
          const rawById = new Map(current.rawById);
          rawById.set(nodeIdToLoad, { ...summary, ...response.node });
          return { ...current, rawById };
        });
        setNodeDetailStates((current) => {
          const next = new Map(current);
          next.set(nodeIdToLoad, { loading: false, error: null });
          return next;
        });
      })
      .catch((reason: unknown) => {
        const detailError = reason instanceof Error ? reason : new Error(String(reason));
        const apiMismatch = workspaceReleaseMismatchFromError(reason);
        if (detailError instanceof GraphReleaseMismatchError || apiMismatch) {
          setError(
            detailError instanceof GraphReleaseMismatchError
              ? detailError
              : new GraphReleaseMismatchError(releaseId, apiMismatch!.servedReleaseId),
          );
          return;
        }
        setNodeDetailStates((current) => {
          const next = new Map(current);
          next.set(nodeIdToLoad, { loading: false, error: detailError });
          return next;
        });
      })
      .finally(() => {
        detailLoadsRef.current.delete(nodeIdToLoad);
      });
    detailLoadsRef.current.set(nodeIdToLoad, request);
    return request;
  }, [loadedReleaseId]);

  const undo = useCallback(() => {
    urlWriteMode.current = 'push';
    dispatch({ type: 'undo' });
  }, []);
  const redo = useCallback(() => {
    urlWriteMode.current = 'push';
    dispatch({ type: 'redo' });
  }, []);

  useEffect(() => {
    const handleKeyboard = (event: KeyboardEvent) => {
      const target = event.target;
      if (
        target instanceof Element
        && target.closest('input, textarea, select, [contenteditable="true"]')
      ) return;
      const shortcutMode = MODE_SHORTCUTS[event.code];
      if (
        event.altKey
        && event.shiftKey
        && !event.ctrlKey
        && !event.metaKey
        && shortcutMode
      ) {
        event.preventDefault();
        setMode(shortcutMode);
        return;
      }
      const modifier = event.metaKey || event.ctrlKey;
      if (modifier && event.key.toLowerCase() === 'z') {
        event.preventDefault();
        if (event.shiftKey) redo();
        else undo();
      } else if (modifier && event.key.toLowerCase() === 'y') {
        event.preventDefault();
        redo();
      }
    };
    window.addEventListener('keydown', handleKeyboard);
    return () => window.removeEventListener('keydown', handleKeyboard);
  }, [redo, setMode, undo]);

  const permalink = useMemo(() => {
    const path = `/visualizer?${serializeGraphWorkspaceState(history.present)}`;
    return typeof window === 'undefined' ? path : `${window.location.origin}${path}`;
  }, [history.present]);

  const value = useMemo<GraphWorkspaceStore>(() => ({
    state: history.present,
    data,
    loading,
    error,
    nodeDetailStates,
    canUndo: history.past.length > 0,
    canRedo: history.future.length > 0,
    permalink,
    setMode,
    selectPrimary,
    setCompareIds,
    toggleCompare,
    setEvidenceThread,
    setFilters,
    setTimeWindow,
    setCamera,
    ensureNodeDetail,
    undo,
    redo,
  }), [
    data,
    error,
    ensureNodeDetail,
    history.future.length,
    history.past.length,
    history.present,
    loading,
    nodeDetailStates,
    permalink,
    redo,
    selectPrimary,
    setCamera,
    setCompareIds,
    setEvidenceThread,
    setFilters,
    setMode,
    setTimeWindow,
    toggleCompare,
    undo,
  ]);

  return (
    <GraphWorkspaceContext.Provider value={value}>
      {children}
    </GraphWorkspaceContext.Provider>
  );
}

export function useGraphWorkspace(): GraphWorkspaceStore {
  const context = useContext(GraphWorkspaceContext);
  if (!context) {
    throw new Error('useGraphWorkspace must be used within GraphWorkspaceProvider');
  }
  return context;
}
