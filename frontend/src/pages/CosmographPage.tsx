import {
  Camera,
  ChevronLeft,
  Focus,
  Map as MapIcon,
  Network,
  Pause,
  Play,
  RefreshCw,
  Route,
  Settings,
  Sparkles,
  X,
} from 'lucide-react';
import { startTransition, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Cosmograph,
  CosmographProvider,
  prepareCosmographData,
  type CosmographConfig,
  type CosmographData,
  type CosmographRef,
} from '@cosmograph/react';

import { apiClient } from '../api/client';
import type { KGEdge, KGNode } from '../types';

import ModeSwitcher from '../components/canvas/ModeSwitcher';
import NodeDetailPanel from '../components/NodeDetailPanel';

import {
  buildAtlasMeta,
  type AtlasEdgeMeta,
  type AtlasNodeMeta,
} from '../components/cosmograph/AtlasHelpers';
import { pickAtlasNodeIds } from '../components/cosmograph/FreeWillAtlas';
import KgSearchBar from '../components/cosmograph/KgSearchBar';
import KgFilters, { type KgFilterState } from '../components/cosmograph/KgFilters';
import Legend from '../components/cosmograph/Legend';
import MobileGraphControls from '../components/cosmograph/MobileGraphControls';
import PathFinder, { type PathResult } from '../components/cosmograph/PathFinder';
import { useResponsive } from '../hooks/useResponsive';
import { useMobileGraphTiers } from '../hooks/useMobileGraphTiers';

import { Component, type ErrorInfo, type ReactNode } from 'react';

/** Catches render-time crashes from the cosmograph WebGL layer
 *  so the page doesn't go white. Surfaces a recovery card with a
 *  reload button — the actual error is logged to the console. */
class CosmographErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean; message: string }
> {
  state = { hasError: false, message: '' };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, message: error.message ?? 'Unknown error' };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Cosmograph crashed:', error, info.componentStack);
  }

  render() {
    if (!this.state.hasError) return this.props.children;
    return (
      <div className="absolute inset-0 flex items-center justify-center p-6">
        <div className="max-w-md rounded-2xl border border-amber-300/40 bg-slate-950/85 p-6 text-center shadow-2xl backdrop-blur-md">
          <p className="text-base font-semibold text-amber-200">
            Le graphe a planté
          </p>
          <p className="mt-2 text-sm text-slate-300">
            {this.state.message}
          </p>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="mt-4 inline-flex items-center justify-center rounded-full bg-amber-500/90 px-4 py-2 text-sm font-medium text-slate-950 transition-colors hover:bg-amber-400"
          >
            Recharger
          </button>
        </div>
      </div>
    );
  }
}

type Tab = 'atlas' | 'full' | 'path' | 'filter';

type EdgeApiResponse = KGEdge[] | { edges?: KGEdge[] };

interface BoundGraph {
  meta: ReadonlyArray<AtlasNodeMeta>;
  edges: ReadonlyArray<AtlasEdgeMeta>;
  rawById: Map<string, KGNode>;
  metaById: Map<string, AtlasNodeMeta>;
  relationships: Map<string, Array<{ id: string; label: string; type: string; relation: string; direction: 'incoming' | 'outgoing' }>>;
}

interface CosmoData {
  points: CosmographData | undefined;
  links: CosmographData | undefined;
  cosmographConfig: Omit<CosmographConfig, 'points' | 'links'>;
  colorByMap: Record<string, string>;
  colorById: Record<string, string>;
  sizeById: Record<string, number>;
}

const EMPTY_RELATIONSHIPS: BoundGraph['relationships'] = new Map();

function compactNode(meta: AtlasNodeMeta, colorKey: string) {
  return {
    id: meta.id,
    label: meta.label,
    typeLabel: meta.typeLabel,
    typeKey: meta.typeKey,
    schoolLabel: meta.schoolLabel,
    periodLabel: meta.periodLabel,
    degree: meta.degree,
    importance: meta.importance,
    colorKey,
    layer: meta.layer,
  };
}

function colorKeyFor(meta: AtlasNodeMeta): string {
  // Unique key per (type, layer) — kept stable so the colorByMap stays small.
  return `${meta.layer}:${meta.typeKey}`;
}

async function buildCosmoData(
  meta: ReadonlyArray<AtlasNodeMeta>,
  edges: ReadonlyArray<AtlasEdgeMeta>,
): Promise<CosmoData> {
  const colorByMap: Record<string, string> = {};
  const colorById: Record<string, string> = {};
  const sizeById: Record<string, number> = {};

  meta.forEach((node) => {
    const key = colorKeyFor(node);
    colorByMap[key] = node.color;
    colorById[node.id] = node.color;
    sizeById[node.id] = node.size;
  });

  const points = meta.map((node) => compactNode(node, colorKeyFor(node)));
  const links = edges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    relation: edge.relation,
    width: edge.width,
    color: edge.color,
  }));

  const prepared = await prepareCosmographData(
    {
      points: {
        pointIdBy: 'id',
        pointLabelBy: 'label',
        pointSizeBy: 'importance',
        pointColorBy: 'colorKey',
        pointIncludeColumns: ['*'],
        pointDefaultColor: '#7dd3fc',
        pointDefaultSize: 2,
      },
      links: {
        linkSourceBy: 'source',
        linkTargetsBy: ['target'],
        linkWidthBy: 'width',
        linkColorBy: 'color',
        linkIncludeColumns: ['*'],
        linkDefaultWidth: 1,
        linkDefaultColor: 'rgba(148, 163, 184, 0.28)',
      },
    },
    points,
    links,
  );

  return {
    points: prepared?.points,
    links: prepared?.links,
    cosmographConfig: prepared?.cosmographConfig ?? {},
    colorByMap,
    colorById,
    sizeById,
  };
}

function buildRelationships(meta: ReadonlyArray<AtlasNodeMeta>, edges: ReadonlyArray<AtlasEdgeMeta>) {
  const map: BoundGraph['relationships'] = new Map();
  meta.forEach((node) => map.set(node.id, []));
  edges.forEach((edge) => {
    const src = map.get(edge.source);
    const tgt = map.get(edge.target);
    if (src) {
      const target = meta.find((n) => n.id === edge.target);
      if (target) {
        src.push({ id: target.id, label: target.label, type: target.typeKey, relation: edge.relation, direction: 'outgoing' });
      }
    }
    if (tgt) {
      const source = meta.find((n) => n.id === edge.source);
      if (source) {
        tgt.push({ id: source.id, label: source.label, type: source.typeKey, relation: edge.relation, direction: 'incoming' });
      }
    }
  });
  // Cap to 32 for panel performance, sorted by partner importance desc.
  const metaById = new Map(meta.map((m) => [m.id, m]));
  map.forEach((rels, id) => {
    rels.sort((a, b) => (metaById.get(b.id)?.importance ?? 0) - (metaById.get(a.id)?.importance ?? 0));
    map.set(id, rels.slice(0, 32));
  });
  return map;
}

function filterMeta(
  meta: ReadonlyArray<AtlasNodeMeta>,
  filters: KgFilterState,
): ReadonlyArray<AtlasNodeMeta> {
  if (
    filters.periods.length === 0 &&
    filters.types.length === 0 &&
    filters.schools.length === 0
  ) {
    return meta;
  }
  return meta.filter((node) => {
    if (filters.types.length > 0) {
      const want = filters.types.includes(node.typeKey) || (node.layer === 'modern' && filters.types.includes('scholar'));
      if (!want) return false;
    }
    if (filters.periods.length > 0 && !filters.periods.includes(node.periodLabel)) {
      return false;
    }
    if (filters.schools.length > 0 && !filters.schools.includes(node.schoolLabel)) {
      return false;
    }
    return true;
  });
}

export default function CosmographPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { nodeId } = useParams();
  const graphRef = useRef<CosmographRef>(undefined);
  const { isMobile } = useResponsive();

  const [tab, setTab] = useState<Tab>('atlas');
  const [filters, setFilters] = useState<KgFilterState>({ periods: [], types: [], schools: [] });
  const [allMeta, setAllMeta] = useState<ReadonlyArray<AtlasNodeMeta>>([]);
  const [allEdges, setAllEdges] = useState<ReadonlyArray<AtlasEdgeMeta>>([]);
  const [rawById, setRawById] = useState<Map<string, KGNode>>(new Map());
  const [relationships, setRelationships] = useState<BoundGraph['relationships']>(EMPTY_RELATIONSHIPS);

  const [cosmo, setCosmo] = useState<CosmoData | null>(null);
  const [activeMeta, setActiveMeta] = useState<ReadonlyArray<AtlasNodeMeta>>([]);
  const [, setActiveEdges] = useState<ReadonlyArray<AtlasEdgeMeta>>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [graphReady, setGraphReady] = useState(false);

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [pathSource, setPathSource] = useState<AtlasNodeMeta | null>(null);
  const [pathTarget, setPathTarget] = useState<AtlasNodeMeta | null>(null);
  const [pathResult, setPathResult] = useState<PathResult | null>(null);
  const [simulationRunning, setSimulationRunning] = useState(true);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [helpDismissed, setHelpDismissed] = useState(false);

  // --- Load: nodes + edges once, build full Atlas meta ---
  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [nodesResponse, edgesResponse] = await Promise.all([
          apiClient.getNodes({ limit: 50000 }),
          apiClient.getEdges({ limit: 50000 }) as Promise<EdgeApiResponse>,
        ]);
        if (cancelled) return;
        const nodes = nodesResponse?.nodes ?? [];
        const edgePayload = edgesResponse;
        const edges = Array.isArray(edgePayload) ? edgePayload : edgePayload?.edges ?? [];

        const { nodes: meta, edges: decoratedEdges } = buildAtlasMeta(nodes, edges);
        const rawMap = new Map(nodes.map((n) => [n.id, n]));
        const rels = buildRelationships(meta, decoratedEdges);

        if (cancelled) return;
        setAllMeta(meta);
        setAllEdges(decoratedEdges);
        setRawById(rawMap);
        setRelationships(rels);
        setLoading(false);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : 'Failed to load the knowledge graph.');
        setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  // --- Mobile progressive zoom tier (disabled on desktop) ---
  // On mobile, the active slice is driven by the cosmograph zoom level rather
  // than by the Atlas/Full/Filter tab. The tab still drives behaviour: when the
  // user picks "Filter" we apply filters to the tier-selected slice; "Full"
  // becomes "Detail" tier seed; "Path" still uses the whole graph for BFS.
  const mobileTiers = useMobileGraphTiers({
    enabled: isMobile,
    meta: allMeta,
    edges: allEdges,
    graphRef,
    graphReady,
  });

  // --- Derive active slice (atlas / full / filtered) ---
  useEffect(() => {
    if (allMeta.length === 0) return;
    let cancelled = false;

    async function computeActive() {
      let metaSlice: ReadonlyArray<AtlasNodeMeta> = allMeta;
      let edgeSlice: ReadonlyArray<AtlasEdgeMeta>;

      if (isMobile && mobileTiers.slice && tab !== 'path') {
        // Mobile: tier-based slice (Atlas / Schools / Detail) wins over tab.
        let tierMeta = mobileTiers.slice.metaSlice;
        let tierEdges = mobileTiers.slice.edgeSlice;
        if (tab === 'filter') {
          const filteredAll = filterMeta(allMeta, filters);
          const filterIds = new Set(filteredAll.map((m) => m.id));
          tierMeta = tierMeta.filter((m) => filterIds.has(m.id));
          const tierIds = new Set(tierMeta.map((m) => m.id));
          tierEdges = tierEdges.filter(
            (e) => tierIds.has(e.source) && tierIds.has(e.target),
          );
        }
        metaSlice = tierMeta;
        edgeSlice = tierEdges;
      } else {
        // Desktop: original tab-driven slice.
        if (tab === 'atlas') {
          const ids = pickAtlasNodeIds(allMeta.map((m) => ({ id: m.id, type: m.typeKey })));
          metaSlice = allMeta.filter((m) => ids.has(m.id));
        }
        if (tab === 'filter') {
          metaSlice = filterMeta(allMeta, filters);
        }
        // tab === 'full' and 'path' use the whole graph
        const idSet = new Set(metaSlice.map((m) => m.id));
        edgeSlice = allEdges.filter((e) => idSet.has(e.source) && idSet.has(e.target));
      }

      const built = await buildCosmoData(metaSlice, edgeSlice);
      if (cancelled) return;
      setActiveMeta(metaSlice);
      setActiveEdges(edgeSlice);
      setCosmo(built);
    }

    void computeActive();
    return () => {
      cancelled = true;
    };
  }, [allMeta, allEdges, tab, filters, isMobile, mobileTiers.slice]);

  // Path mode forces full graph behind the scenes so BFS can find anything.
  useEffect(() => {
    if (tab === 'path' && allMeta.length > 0 && activeMeta.length !== allMeta.length) {
      // ensure full graph data is loaded
      const idSet = new Set(allMeta.map((m) => m.id));
      const edgeSlice = allEdges.filter((e) => idSet.has(e.source) && idSet.has(e.target));
      void (async () => {
        const built = await buildCosmoData(allMeta, edgeSlice);
        setActiveMeta(allMeta);
        setActiveEdges(edgeSlice);
        setCosmo(built);
      })();
    }
  }, [tab, allMeta, allEdges, activeMeta.length]);

  const selectedRaw = selectedNodeId ? rawById.get(selectedNodeId) ?? null : null;
  const selectedRelationships = selectedNodeId ? relationships.get(selectedNodeId) ?? [] : [];

  const focusNodeById = useCallback(
    async (id: string, opts?: { pushRoute?: boolean; zoomScale?: number }) => {
      if (!graphRef.current) return;
      const indices = await graphRef.current.getPointIndicesByIds([id]);
      const pointIndex = indices?.[0];
      if (pointIndex === undefined) {
        // Not in the active slice — open detail without focusing.
        startTransition(() => setSelectedNodeId(id));
        if (opts?.pushRoute !== false) {
          navigate(`/visualizer/${id}`, { replace: true });
        }
        return;
      }
      graphRef.current.selectPoints([pointIndex], false);
      graphRef.current.setFocusedPoint(pointIndex);
      graphRef.current.zoomToPoint(pointIndex, 500, opts?.zoomScale ?? 2.0, true);
      startTransition(() => setSelectedNodeId(id));
      if (opts?.pushRoute !== false) {
        navigate(`/visualizer/${id}`, { replace: true });
      }
    },
    [navigate],
  );

  useEffect(() => {
    if (!graphReady || !nodeId) return;
    if (selectedNodeId === nodeId) return;
    void focusNodeById(nodeId, { pushRoute: false });
  }, [graphReady, nodeId, selectedNodeId, focusNodeById]);

  // Mobile: when the tier slice changes (e.g. Atlas → Schools), re-fit the view
  // so the user always sees the active subgraph centred. `fitViewOnInit` only
  // runs once; this keeps the experience tight after every tier transition.
  const lastFittedNodeCount = useRef<number>(0);
  useEffect(() => {
    if (!isMobile || !graphReady || !graphRef.current) return;
    const count = activeMeta.length;
    if (count === 0) return;
    if (lastFittedNodeCount.current === count) return;
    lastFittedNodeCount.current = count;
    // The simulation needs several hundred ms to lay out the new node set.
    // Three passes catch the early/medium/late states so the user is never
    // looking at an off-screen cluster.
    const handles = [600, 1400, 2400].map((delay) =>
      window.setTimeout(() => {
        graphRef.current?.fitView(500, 0.24);
      }, delay),
    );
    return () => handles.forEach((h) => window.clearTimeout(h));
  }, [isMobile, graphReady, activeMeta.length]);


  function clearSelection() {
    graphRef.current?.unselectAllPoints();
    graphRef.current?.setFocusedPoint(undefined);
    setSelectedNodeId(null);
    navigate('/visualizer', { replace: true });
  }

  function fitView() {
    graphRef.current?.fitView(550, 0.14);
  }

  function toggleSimulation() {
    if (!graphRef.current) return;
    if (simulationRunning) {
      graphRef.current.pause();
    } else {
      graphRef.current.unpause();
    }
  }

  function exportScreenshot() {
    graphRef.current?.captureScreenshot('eleutheria-knowledge-graph', 2);
  }

  // --- Path highlighting on the canvas (greyout + ring) ---
  const pathIdSet = useMemo(() => new Set(pathResult?.ids ?? []), [pathResult]);

  // Build dynamic CosmographConfig
  const dynamicConfig: Partial<CosmographConfig> | undefined = cosmo
    ? {
        ...cosmo.cosmographConfig,
        points: cosmo.points,
        links: cosmo.links,
        backgroundColor: '#020617',
        renderHoveredPointRing: true,
        hoveredPointRingColor: '#fde68a',
        focusedPointRingColor: '#22d3ee',
        pointDefaultColor: '#7dd3fc',
        pointDefaultSize: 1.6,
        pointGreyoutOpacity: pathResult ? 0.07 : 0.16,
        linkDefaultColor: 'rgba(148,163,184,0.22)',
        linkGreyoutOpacity: pathResult ? 0.03 : 0.05,
        linkDefaultWidth: 1,
        hoveredLinkColor: '#f8fafc',
        hoveredLinkWidthIncrease: 1.5,
        linkVisibilityDistanceRange: [32, 120],
        linkVisibilityMinTransparency: 0.08,
        curvedLinks: true,
        linkDefaultArrows: false,
        enableZoom: true,
        enableDrag: true,
        enableRightClickRepulsion: true,
        enableSimulationDuringZoom: false,
        fitViewOnInit: true,
        fitViewDelay: 360,
        fitViewDuration: 500,
        fitViewPadding: 0.2,
        randomSeed: 'eleutheria-atlas-v3',
        spaceSize: isMobile
          ? mobileTiers.tier === 'overview'
            ? 3600
            : mobileTiers.tier === 'mid'
              ? 5400
              : 7200
          : tab === 'atlas'
            ? 2200
            : 7200,
        pointSamplingDistance: isMobile
          ? 160
          : tab === 'atlas'
            ? 60
            : 260,
        pointColorBy: 'colorKey',
        pointColorByMap: cosmo.colorByMap,
        pointSizeBy: 'importance',
        pointSizeByFn: (value: unknown, index?: number) => {
          const numeric = typeof value === 'number' ? value : Number(value);
          if (!Number.isFinite(numeric)) return 2;
          const pointId = typeof index === 'number' ? activeMeta[index]?.id : undefined;
          const fromMap = pointId ? cosmo.sizeById[pointId] ?? null : null;
          const base = fromMap ?? Math.max(6, Math.min(30, 6 + Math.sqrt(numeric) * 3));
          if (pointId && pathIdSet.has(pointId)) {
            return Math.min(36, base * 1.35 + 2);
          }
          if (pointId && pointId === selectedNodeId) {
            return Math.min(36, base * 1.3 + 2);
          }
          return base;
        },
        pointSizeRange: [4, 30],
        showLabels: false,
        showDynamicLabels: false,
        showTopLabels: isMobile ? true : tab === 'atlas',
        showTopLabelsLimit: isMobile
          ? Math.max(mobileTiers.slice?.labelNodeIds.size ?? 12, 8)
          : tab === 'atlas'
            ? 14
            : 0,
        showFocusedPointLabel: true,
        showHoveredPointLabel: true,
        showSelectedLabels: true,
        selectedPointLabelsLimit: 24,
        pointLabelBy: 'label',
        pointLabelFontSize: 11,
        labelMargin: 5,
        labelPadding: [5, 3, 5, 3],
        pointLabelClassName: () =>
          [
            'background: rgba(7,14,28,0.78)',
            'border: 1px solid rgba(148,163,184,0.18)',
            'color: #f8fafc',
            'border-radius: 999px',
            'backdrop-filter: blur(8px)',
            'font-weight: 600',
            'max-width: 220px',
            'overflow: hidden',
            'text-overflow: ellipsis',
          ].join('; '),
        selectPointOnClick: true,
        focusPointOnClick: true,
        selectPointOnLabelClick: true,
        focusPointOnLabelClick: true,
        resetSelectionOnEmptyCanvasClick: true,
        linkWidthRange: [0.18, 2.4],
        // Mobile: kill the physics simulation entirely. The continuous
        // force loop was triggering the white-screen crash on pinch
        // (Cosmograph's sampling APIs throw mid-simulation under iOS).
        // We render the nodes once at their initial positions and let
        // the user pan/zoom around a static layout — way less GPU on
        // a phone too. Desktop keeps the full simulation.
        enableSimulation: !isMobile,
        simulationDecay: isMobile ? 0 : 4300,
        simulationGravity: isMobile
          ? 0
          : tab === 'atlas'
            ? 0.18
            : 0.08,
        simulationCenter: isMobile ? 0 : 0.01,
        simulationRepulsion: isMobile
          ? 0
          : tab === 'atlas'
            ? 1.6
            : 2.2,
        simulationRepulsionTheta: 1.08,
        simulationLinkSpring: isMobile ? 0 : 0.74,
        simulationLinkDistance: isMobile
          ? 0
          : tab === 'atlas'
            ? 28
            : 36,
        simulationFriction: 0.9,
        simulationImpulse: 0,
      }
    : undefined;

  // --- Highlight path: when path computed, isolate via Cosmograph point filter ---
  useEffect(() => {
    if (!graphReady || !graphRef.current) return;
    if (!pathResult) {
      graphRef.current.unselectAllPoints();
      return;
    }
    (async () => {
      const indices = await graphRef.current?.getPointIndicesByIds([...pathResult.ids]);
      const clean = (indices ?? []).filter((i): i is number => typeof i === 'number');
      if (clean.length > 0) {
        graphRef.current?.selectPoints(clean, false);
        graphRef.current?.fitViewByIndices(clean, 600, 0.18);
      }
    })();
  }, [graphReady, pathResult]);

  return (
    <div className="fixed inset-x-0 bottom-0 top-12 overflow-hidden bg-[#020617]">
      {/* Decorative gradient backdrop, behind canvas */}
      <div aria-hidden className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_18%_20%,rgba(34,211,238,0.10),transparent_34%),radial-gradient(circle_at_78%_18%,rgba(251,191,36,0.10),transparent_30%),radial-gradient(circle_at_50%_85%,rgba(244,114,182,0.10),transparent_28%)]" />
      </div>

      {loading && <LoadingOverlay />}
      {!loading && error && <ErrorOverlay message={error} onRetry={() => window.location.reload()} />}

      {cosmo && dynamicConfig && (
        <CosmographProvider>
          <CosmographErrorBoundary>
          <Cosmograph
            {...dynamicConfig}
            ref={graphRef}
            onMount={() => setGraphReady(true)}
            onSimulationStart={() => setSimulationRunning(true)}
            onSimulationUnpause={() => setSimulationRunning(true)}
            onSimulationPause={() => setSimulationRunning(false)}
            onSimulationEnd={() => setSimulationRunning(false)}
            onZoom={isMobile ? mobileTiers.handleZoom : undefined}
            onPointClick={(index) => {
              const clicked = activeMeta[index];
              if (!clicked) return;
              void focusNodeById(clicked.id);
            }}
            onLabelClick={(_index, id) => {
              void focusNodeById(id);
            }}
            onBackgroundClick={() => clearSelection()}
            style={{ width: '100%', height: '100%' }}
          />
          </CosmographErrorBoundary>

          {/* === Mobile-only controls (FAB, bottom-sheet, tier pill, hint) === */}
          {isMobile && (
            <MobileGraphControls
              tier={mobileTiers.tier}
              visibleNodeCount={mobileTiers.slice?.visibleNodeIds.size ?? 0}
              nodes={allMeta}
              activeTab={tab}
              onTabChange={(next) => {
                setTab(next);
                if (next !== 'path') {
                  setPathResult(null);
                }
              }}
              filters={filters}
              onFiltersChange={setFilters}
              onPickNode={(node) => {
                if (tab === 'atlas') setTab('full');
                void focusNodeById(node.id);
              }}
              onOpenPathFinder={() => {
                setTab('path');
              }}
            />
          )}

          {/* === Top bar: search + tabs (desktop only; mobile uses
              MobileGraphControls below) === */}
          <div className="pointer-events-none absolute inset-x-0 top-3 z-30 hidden px-3 md:block md:top-4 md:px-6">
            <div className="pointer-events-auto mx-auto flex w-full max-w-3xl flex-col gap-3">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => navigate('/')}
                  className="hidden h-10 w-10 shrink-0 items-center justify-center rounded-full border border-white/10 bg-slate-950/75 text-slate-300 transition-colors hover:border-white/20 hover:text-white md:inline-flex"
                  aria-label={t('cosmograph.back', 'Back')}
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>

                <div className="flex-1">
                  <KgSearchBar
                    placeholder={t(
                      'cosmograph.searchPlaceholder',
                      'Search a concept, thinker, work, or scholar — αὐτεξούσιον, Chrysippus, Bobzien…',
                    )}
                    nodes={allMeta}
                    onPick={(node) => {
                      // Picking from search should jump even if outside the curated Atlas.
                      if (tab === 'atlas') setTab('full');
                      void focusNodeById(node.id);
                    }}
                    ariaLabel={t('cosmograph.searchAria', 'Search the knowledge graph')}
                    emptyLabel={t(
                      'cosmograph.searchEmpty',
                      'No match. Try a Greek/Latin term, a surname, or one of: αὐτεξούσιον, prohairesis, heimarmene, Bobzien.',
                    )}
                    resultsLabel={t('cosmograph.searchResults', 'Search results')}
                  />
                </div>
              </div>

              <TabStrip
                value={tab}
                onChange={(next) => {
                  setTab(next);
                  // Reset path state when leaving the path tab.
                  if (next !== 'path') {
                    setPathResult(null);
                  }
                }}
                labels={{
                  atlas: t('cosmograph.tabs.atlas', 'Atlas'),
                  full: t('cosmograph.tabs.full', 'Full graph'),
                  path: t('cosmograph.tabs.path', 'Find a path'),
                  filter: t('cosmograph.tabs.filter', 'Filter'),
                }}
                counts={{
                  atlas: tab === 'atlas' ? activeMeta.length : 0,
                  full: allMeta.length,
                  filter: tab === 'filter' ? activeMeta.length : 0,
                }}
              />

              {tab === 'filter' && (
                <KgFilters
                  state={filters}
                  nodes={allMeta}
                  onChange={setFilters}
                  labels={{
                    period: t('cosmograph.filters.period', 'Period'),
                    type: t('cosmograph.filters.type', 'Type'),
                    school: t('cosmograph.filters.school', 'School'),
                    clear: t('cosmograph.filters.clear', 'Clear filters'),
                  }}
                />
              )}

              {tab === 'path' && (
                <PathFinder
                  nodes={allMeta}
                  edges={allEdges}
                  source={pathSource}
                  target={pathTarget}
                  onSourceChange={setPathSource}
                  onTargetChange={setPathTarget}
                  onPathComputed={setPathResult}
                  onNavigateToNode={(id) => {
                    void focusNodeById(id);
                  }}
                  labels={{
                    title: t('cosmograph.path.title', 'Find a path between two nodes'),
                    description: t(
                      'cosmograph.path.description',
                      'Select a source and a target. The shortest semantic path will be highlighted on the graph.',
                    ),
                    sourcePlaceholder: t('cosmograph.path.source', 'Source — e.g. Chrysippus'),
                    targetPlaceholder: t('cosmograph.path.target', 'Target — e.g. Augustine'),
                    searchAriaLabel: t('cosmograph.path.searchAria', 'Search for a node'),
                    searchEmpty: t('cosmograph.searchEmpty', 'No match.'),
                    searchResults: t('cosmograph.searchResults', 'Search results'),
                    computing: t('cosmograph.path.computing', 'Computing the shortest path…'),
                    noPath: t(
                      'cosmograph.path.noPath',
                      'No path within 6 hops. Try the Atlas to pick more central anchors.',
                    ),
                    error: t('cosmograph.path.error', 'Could not compute path'),
                    pathLength: (n) =>
                      t('cosmograph.path.length', '{{count}} hops', { count: n }) as string,
                    clear: t('cosmograph.path.clear', 'Clear'),
                    swap: t('cosmograph.path.swap', 'Swap source and target'),
                  }}
                />
              )}
            </div>
          </div>

          {/* === Top-right: engine switcher + screenshot/help (desktop only) === */}
          <div className="absolute right-3 top-3 z-30 hidden flex-col items-end gap-2 md:right-6 md:top-4 md:flex">
            {/* Semativerse/Cytoscape switcher hidden on mobile (touch
                + tiny viewport make the alternate engines unusable). */}
            <div className="hidden md:block rounded-full border border-white/10 bg-slate-950/75 p-1 shadow-[0_14px_40px_rgba(2,6,23,0.4)] backdrop-blur-xl">
              <ModeSwitcher />
            </div>
            <div className="flex items-center gap-1">
              <IconButton
                label={t('cosmograph.controls.fit', 'Fit view')}
                icon={<Focus className="h-4 w-4" />}
                onClick={fitView}
              />
              <IconButton
                label={
                  simulationRunning
                    ? t('cosmograph.controls.pause', 'Pause layout')
                    : t('cosmograph.controls.resume', 'Resume layout')
                }
                icon={simulationRunning ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                onClick={toggleSimulation}
              />
              <IconButton
                label={t('cosmograph.controls.screenshot', 'Screenshot')}
                icon={<Camera className="h-4 w-4" />}
                onClick={exportScreenshot}
              />
              <IconButton
                label={t('cosmograph.controls.settings', 'Advanced')}
                icon={<Settings className="h-4 w-4" />}
                onClick={() => setAdvancedOpen((open) => !open)}
              />
            </div>
          </div>

          {/* === Bottom-right: Legend (desktop only) === */}
          <div className="pointer-events-none absolute bottom-4 right-3 z-20 hidden md:right-6 md:block">
            <Legend
              labels={{
                title: t('cosmograph.legend.title', 'Legend'),
                types: t('cosmograph.legend.types', 'Node types'),
                period: t('cosmograph.legend.period', 'Period (opacity)'),
                relations: t('cosmograph.legend.relations', 'Edge weight'),
                presocratic: t('cosmograph.legend.presocratic', 'Presocratic'),
                lateAntiquity: t('cosmograph.legend.lateAntiquity', 'Late Antiquity'),
                modern: t('cosmograph.legend.modern', 'Modern'),
                structural: t('cosmograph.legend.structural', 'authored / member_of'),
                doctrinal: t('cosmograph.legend.doctrinal', 'interprets / critiques'),
                citation: t('cosmograph.legend.citation', 'cites / mentions'),
              }}
            />
          </div>

          {/* === Bottom-left: contextual hint (Atlas first-time, desktop) === */}
          {tab === 'atlas' && !helpDismissed && !isMobile && (
            <div className="pointer-events-auto absolute bottom-4 left-3 z-20 hidden max-w-sm rounded-2xl border border-white/10 bg-slate-950/80 p-4 text-[12px] text-slate-300 shadow-[0_18px_50px_rgba(2,6,23,0.4)] backdrop-blur-xl md:left-6 md:block">
              <div className="mb-1 flex items-center gap-2 text-cyan-100">
                <Sparkles className="h-3.5 w-3.5" />
                <span className="text-[11px] font-semibold uppercase tracking-[0.18em]">
                  {t('cosmograph.atlas.hintLabel', 'Free Will Atlas')}
                </span>
                <button
                  type="button"
                  onClick={() => setHelpDismissed(true)}
                  aria-label={t('common.dismiss', 'Dismiss')}
                  className="ml-auto inline-flex h-6 w-6 items-center justify-center rounded-full border border-white/10 bg-white/[0.04] text-slate-300 transition-colors hover:border-white/20 hover:text-white"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
              <p className="leading-5">
                {t(
                  'cosmograph.atlas.hintBody',
                  'A curated view of the load-bearing concepts, schools, thinkers, and modern scholars on free will. Search to dive deeper, switch to the full graph for the 17.7k-node map, or open Find a path to trace a connection.',
                )}
              </p>
            </div>
          )}

          {/* Advanced drawer (formerly Simulation lab) */}
          {advancedOpen && (
            <AdvancedDrawer onClose={() => setAdvancedOpen(false)} />
          )}

          {/* Node detail panel — full-height right rail on desktop,
              half-height bottom sheet on mobile. */}
          <NodeDetailPanel
            node={selectedRaw}
            onClose={clearSelection}
            relationships={selectedRelationships}
            onNavigateToNode={(nextNodeId) => {
              void focusNodeById(nextNodeId);
            }}
            mobileHalf={isMobile}
          />
        </CosmographProvider>
      )}

      {/* BottomTabNav (Observatory ↔ Semativerse) removed on mobile —
          the alternate engine isn't usable at this viewport and the
          tab strip stole 64 px of canvas. */}
    </div>
  );
}

// === Inline subcomponents ===

function TabStrip({
  value,
  onChange,
  labels,
  counts,
}: {
  value: Tab;
  onChange: (next: Tab) => void;
  labels: Record<Tab, string>;
  counts: { atlas: number; full: number; filter: number };
}) {
  const items: Array<{ id: Tab; icon: import('react').ReactNode; count?: number }> = [
    { id: 'atlas', icon: <Sparkles className="h-3.5 w-3.5" />, count: counts.atlas },
    { id: 'full', icon: <Network className="h-3.5 w-3.5" />, count: counts.full },
    { id: 'path', icon: <Route className="h-3.5 w-3.5" /> },
    { id: 'filter', icon: <MapIcon className="h-3.5 w-3.5" />, count: counts.filter },
  ];

  return (
    <div className="flex items-center gap-1 rounded-full border border-white/10 bg-slate-950/75 p-1 backdrop-blur-xl">
      {items.map((item) => {
        const active = value === item.id;
        return (
          <button
            key={item.id}
            type="button"
            onClick={() => onChange(item.id)}
            aria-pressed={active}
            className={[
              'inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[12px] transition-colors',
              active
                ? 'bg-cyan-300/[0.12] text-cyan-50 shadow-[0_8px_22px_rgba(34,211,238,0.16)]'
                : 'text-slate-300 hover:bg-white/[0.04] hover:text-white',
            ].join(' ')}
          >
            {item.icon}
            <span className="hidden sm:inline">{labels[item.id]}</span>
            {item.count !== undefined && item.count > 0 && (
              <span className="hidden rounded-full bg-white/[0.08] px-1.5 py-0.5 text-[10px] font-medium text-slate-200 sm:inline-block">
                {item.count.toLocaleString()}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

function IconButton({
  icon,
  label,
  onClick,
}: {
  icon: import('react').ReactNode;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      onClick={onClick}
      className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/10 bg-slate-950/75 text-slate-200 transition-colors hover:border-white/20 hover:text-white"
    >
      {icon}
    </button>
  );
}

function LoadingOverlay() {
  const { t } = useTranslation();
  return (
    <div className="absolute inset-0 z-40 flex items-center justify-center bg-slate-950/78 backdrop-blur-xl">
      <div className="mx-6 max-w-md rounded-3xl border border-white/10 bg-slate-950/80 px-8 py-7 text-center shadow-[0_24px_80px_rgba(2,6,23,0.55)]">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full border border-cyan-300/20 bg-cyan-300/10">
          <Network className="h-7 w-7 text-cyan-200" />
        </div>
        <p className="mt-4 text-[11px] font-semibold uppercase tracking-[0.24em] text-cyan-200/80">
          {t('cosmograph.loading.eyebrow', 'Knowledge graph')}
        </p>
        <h2 className="mt-1.5 text-xl font-semibold text-white">
          {t('cosmograph.loading.title', 'Building the Atlas…')}
        </h2>
        <p className="mt-2 text-sm leading-6 text-slate-300">
          {t(
            'cosmograph.loading.body',
            'Loading 17.7k nodes and 42.9k relations across ancient sources and modern reception.',
          )}
        </p>
      </div>
    </div>
  );
}

function ErrorOverlay({ message, onRetry }: { message: string; onRetry: () => void }) {
  const { t } = useTranslation();
  return (
    <div className="absolute inset-0 z-40 flex items-center justify-center bg-slate-950/82 px-6 backdrop-blur-xl">
      <div className="max-w-lg rounded-3xl border border-rose-300/20 bg-slate-950/80 px-8 py-7 shadow-[0_24px_80px_rgba(2,6,23,0.55)]">
        <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-rose-200/80">
          {t('cosmograph.error.eyebrow', 'Knowledge graph')}
        </p>
        <h2 className="mt-2 text-2xl font-semibold text-white">
          {t('cosmograph.error.title', 'Could not load the graph')}
        </h2>
        <p className="mt-3 text-sm leading-6 text-slate-300">{message}</p>
        <div className="mt-6 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-white/10"
          >
            <RefreshCw className="h-4 w-4" />
            {t('cosmograph.error.retry', 'Retry')}
          </button>
          <a
            href="/database"
            className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm font-medium text-slate-200 transition-colors hover:bg-white/[0.08]"
          >
            {t('cosmograph.error.openDatabase', 'Open the database instead')}
          </a>
        </div>
      </div>
    </div>
  );
}

function AdvancedDrawer({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  return (
    <div className="absolute right-3 top-24 z-30 w-[18rem] rounded-2xl border border-white/10 bg-slate-950/85 p-4 text-[12px] text-slate-300 shadow-[0_24px_60px_rgba(2,6,23,0.55)] backdrop-blur-xl md:right-6 md:top-28">
      <div className="mb-2 flex items-center justify-between">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">
          {t('cosmograph.advanced.title', 'Advanced')}
        </p>
        <button
          type="button"
          onClick={onClose}
          aria-label={t('common.close', 'Close')}
          className="inline-flex h-6 w-6 items-center justify-center rounded-full border border-white/10 bg-white/[0.04] text-slate-300 hover:text-white"
        >
          <X className="h-3 w-3" />
        </button>
      </div>
      <p className="leading-5">
        {t(
          'cosmograph.advanced.body',
          'Layout physics, lasso selection and pinning have moved to a developer mode. They will return behind this drawer in a later iteration — for now use Atlas / Full graph / Filter / Find a path for everyday scholarly work.',
        )}
      </p>
    </div>
  );
}
