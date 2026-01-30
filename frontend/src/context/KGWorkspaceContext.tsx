import {
  createContext,
  useContext,
  useState,
  useEffect,
  useMemo,
  useCallback,
  type ReactNode,
} from 'react';
import { apiClient } from '../api/client';
import type {
  CytoscapeData,
  CommunityMeta,
  InfluenceMatrixOverview,
  KGFilterState,
  KGPathRequest,
  KGPathResponse,
  KGSelectionState,
  TimelineOverview,
} from '../types';

const defaultFilters: KGFilterState = {
  nodeTypes: [],
  periods: [],
  schools: [],
  relations: [],
  searchTerm: '',
};

const defaultSelection: KGSelectionState = {
  nodes: [],
  edges: [],
  focusNodeId: null,
};

interface WorkspaceState {
  filters: KGFilterState;
  selection: KGSelectionState;
  timeline: TimelineOverview | null;
  influenceMatrix: InfluenceMatrixOverview | null;
  loading: boolean;
  error: string | null;
  // Cached KG data that persists across navigation
  kgData: CytoscapeData | null;
  kgLoading: boolean;
  kgError: string | null;
  communityAlgorithm: string;
  communityMeta: CommunityMeta | null;
  // Period filter - exclude modern scholarly reception
  ancientOnly: boolean;
}

interface WorkspaceContextValue {
  state: WorkspaceState;
  setFilters: (updater: Partial<KGFilterState> | ((prev: KGFilterState) => KGFilterState)) => void;
  updateSelection: (updater: Partial<KGSelectionState> | ((prev: KGSelectionState) => KGSelectionState)) => void;
  setCommunityAlgorithm: (algorithm: string) => void;
  setAncientOnly: (ancientOnly: boolean) => void;
  refresh: () => Promise<void>;
  computePath: (request: KGPathRequest) => Promise<KGPathResponse>;
}

export const KGWorkspaceContext = createContext<WorkspaceContextValue | undefined>(undefined);

export function KGWorkspaceProvider({ children }: { children: ReactNode }) {
  const [filters, setFilters] = useState<KGFilterState>(defaultFilters);
  const [selection, setSelection] = useState<KGSelectionState>(defaultSelection);
  const [timeline, setTimeline] = useState<TimelineOverview | null>(null);
  const [influenceMatrix, setInfluenceMatrix] = useState<InfluenceMatrixOverview | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // KG data cache - persists across navigation
  const [kgData, setKgData] = useState<CytoscapeData | null>(null);
  const [kgLoading, setKgLoading] = useState<boolean>(true);
  const [kgError, setKgError] = useState<string | null>(null);
  const [communityAlgorithm, setCommunityAlgorithm] = useState<string>('auto');
  const [communityMeta, setCommunityMeta] = useState<CommunityMeta | null>(null);
  const [ancientOnly, setAncientOnly] = useState<boolean>(false);

  // Load KG data once and cache it (persists across navigation)
  const fetchKGData = useCallback(async (algorithm: string, filterAncientOnly: boolean = false) => {
    setKgLoading(true);
    setKgError(null);

    try {
      // Add timeout to prevent infinite loading (30 seconds)
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Request timeout - API took too long to respond')), 30000)
      );

      const dataPromise = apiClient.getCytoscapeData({ algorithm, ancientOnly: filterAncientOnly });

      const data = await Promise.race([dataPromise, timeoutPromise]) as CytoscapeData;
      setKgData(data);
      setCommunityMeta(data.meta?.community ?? null);
      setKgLoading(false);
    } catch (err: unknown) {
      console.error('Error loading KG data:', err);
      setKgError(err instanceof Error ? err.message : 'Failed to load knowledge graph');
      setKgLoading(false);
    }
  }, []);

  // Load analytics data
  const fetchData = useCallback(
    async (activeFilters: KGFilterState) => {
      setLoading(true);
      setError(null);

      try {
        const [timelineData, matrixData] = await Promise.all([
          apiClient.getTimelineOverview(activeFilters).catch((err) => {
            console.error('Error loading timeline:', err);
            return null;
          }),
          apiClient.getInfluenceMatrix(activeFilters).catch((err) => {
            console.error('Error loading influence matrix:', err);
            return null;
          }),
        ]);

        setTimeline(timelineData);
        setInfluenceMatrix(matrixData);
        setLoading(false);
      } catch (err: unknown) {
        console.error('Error loading KG workspace data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load knowledge graph analytics');
        setLoading(false);
      }
    },
    []
  );

  // Load KG data on mount (only once unless algorithm or ancientOnly changes)
  useEffect(() => {
    void fetchKGData(communityAlgorithm, ancientOnly);
  }, [communityAlgorithm, ancientOnly, fetchKGData]);

  // Load analytics data when filters change
  useEffect(() => {
    void fetchData(filters);
  }, [filters, fetchData]);

  const handleSetFilters = useCallback(
    (updater: Partial<KGFilterState> | ((prev: KGFilterState) => KGFilterState)) => {
      setFilters((prev) => {
        const next =
          typeof updater === 'function'
            ? (updater as (prev: KGFilterState) => KGFilterState)(prev)
            : { ...prev, ...updater };

        return {
          nodeTypes: Array.from(new Set(next.nodeTypes || [])).sort(),
          periods: Array.from(new Set(next.periods || [])).sort(),
          schools: Array.from(new Set(next.schools || [])).sort(),
          relations: Array.from(new Set(next.relations || [])).sort(),
          searchTerm: next.searchTerm || '',
          dateRange: next.dateRange,
        };
      });
    },
    []
  );

  const handleUpdateSelection = useCallback(
    (updater: Partial<KGSelectionState> | ((prev: KGSelectionState) => KGSelectionState)) => {
      setSelection((prev) => {
        const next =
          typeof updater === 'function'
            ? (updater as (prev: KGSelectionState) => KGSelectionState)(prev)
            : { ...prev, ...updater };

        return {
          nodes: Array.from(new Set(next.nodes || [])),
          edges: Array.from(new Set(next.edges || [])),
          focusNodeId: next.focusNodeId ?? null,
        };
      });
    },
    []
  );

  const refresh = useCallback(async () => {
    await fetchData(filters);
  }, [fetchData, filters]);

  const computePath = useCallback(async (request: KGPathRequest) => {
    return apiClient.computeGraphPath(request);
  }, []);

  const state: WorkspaceState = useMemo(
    () => ({
      filters,
      selection,
      timeline,
      influenceMatrix,
      loading,
      error,
      kgData,
      kgLoading,
      kgError,
      communityAlgorithm,
      communityMeta,
      ancientOnly,
    }),
    [filters, selection, timeline, influenceMatrix, loading, error, kgData, kgLoading, kgError, communityAlgorithm, communityMeta, ancientOnly]
  );

  const value = useMemo<WorkspaceContextValue>(
    () => ({
      state,
      setFilters: handleSetFilters,
      updateSelection: handleUpdateSelection,
      setCommunityAlgorithm,
      setAncientOnly,
      refresh,
      computePath,
    }),
    [state, handleSetFilters, handleUpdateSelection, refresh, computePath]
  );

  return <KGWorkspaceContext.Provider value={value}>{children}</KGWorkspaceContext.Provider>;
}

export function useKGWorkspace(): WorkspaceContextValue {
  const context = useContext(KGWorkspaceContext);

  if (!context) {
    throw new Error('useKGWorkspace must be used within a KGWorkspaceProvider');
  }

  return context;
}
