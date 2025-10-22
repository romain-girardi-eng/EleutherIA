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
  ArgumentEvidenceOverview,
  ConceptClusterOverview,
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
  argumentEvidence: ArgumentEvidenceOverview | null;
  conceptClusters: ConceptClusterOverview | null;
  influenceMatrix: InfluenceMatrixOverview | null;
  loading: boolean;
  error: string | null;
}

interface WorkspaceContextValue {
  state: WorkspaceState;
  setFilters: (updater: Partial<KGFilterState> | ((prev: KGFilterState) => KGFilterState)) => void;
  updateSelection: (updater: Partial<KGSelectionState> | ((prev: KGSelectionState) => KGSelectionState)) => void;
  refresh: () => Promise<void>;
  computePath: (request: KGPathRequest) => Promise<KGPathResponse>;
}

const KGWorkspaceContext = createContext<WorkspaceContextValue | undefined>(undefined);

export function KGWorkspaceProvider({ children }: { children: ReactNode }) {
  const [filters, setFilters] = useState<KGFilterState>(defaultFilters);
  const [selection, setSelection] = useState<KGSelectionState>(defaultSelection);
  const [timeline, setTimeline] = useState<TimelineOverview | null>(null);
  const [argumentEvidence, setArgumentEvidence] = useState<ArgumentEvidenceOverview | null>(null);
  const [conceptClusters, setConceptClusters] = useState<ConceptClusterOverview | null>(null);
  const [influenceMatrix, setInfluenceMatrix] = useState<InfluenceMatrixOverview | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(
    async (activeFilters: KGFilterState) => {
      setLoading(true);
      setError(null);

      try {
        // Load fast endpoints first for immediate feedback
        const [timelineData, matrixData] = await Promise.all([
          apiClient.getTimelineOverview(activeFilters),
          apiClient.getInfluenceMatrix(activeFilters),
        ]);

        setTimeline(timelineData);
        setInfluenceMatrix(matrixData);
        setLoading(false); // Allow UI to render with partial data

        // Load slower endpoints in background
        const clusterFilters: KGFilterState = {
          ...activeFilters,
          nodeTypes:
            activeFilters.nodeTypes && activeFilters.nodeTypes.length > 0
              ? Array.from(new Set([...activeFilters.nodeTypes, 'concept']))
              : ['concept'],
        };

        const [argumentData, clusterData] = await Promise.all([
          apiClient.getArgumentEvidenceOverview(activeFilters),
          apiClient.getConceptClusterOverview(clusterFilters),
        ]);

        setArgumentEvidence(argumentData);
        setConceptClusters(clusterData);
      } catch (err: any) {
        console.error('Error loading KG workspace data:', err);
        setError(err?.message || 'Failed to load knowledge graph analytics');
        setLoading(false);
      }
    },
    []
  );

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
      argumentEvidence,
      conceptClusters,
      influenceMatrix,
      loading,
      error,
    }),
    [filters, selection, timeline, argumentEvidence, conceptClusters, influenceMatrix, loading, error]
  );

  const value = useMemo<WorkspaceContextValue>(
    () => ({
      state,
      setFilters: handleSetFilters,
      updateSelection: handleUpdateSelection,
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
