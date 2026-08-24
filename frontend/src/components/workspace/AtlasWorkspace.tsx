import {
  AlertTriangle,
  BookOpen,
  Camera,
  ChevronLeft,
  Clock3,
  Focus,
  Map as MapIcon,
  Network,
  Pause,
  Play,
  Route,
  Settings,
  Sparkles,
  X,
} from 'lucide-react';
import { startTransition, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { formatCompact } from '../../lib/formatCompact';
import {
  CosmographProvider,
  prepareCosmographData,
  type CosmographConfig,
  type CosmographData,
  type CosmographRef,
} from '@cosmograph/react';
import { AnimatePresence } from 'framer-motion';

import NodeDetailPanel from '../NodeDetailPanel';

import {
  type AtlasEdgeMeta,
  type AtlasNodeMeta,
} from '../cosmograph/AtlasHelpers';
import {
  ATLAS_CONSTELLATION_POSITIONS,
  atlasConstellationKey,
  type AtlasConstellationKey,
  pickAtlasLandingEdges,
  pickAtlasLandingNodeIds,
  pickAtlasNodeIds,
} from '../cosmograph/FreeWillAtlas';
import KgSearchBar from '../cosmograph/KgSearchBar';
import KgFilters, { type KgFilterState } from '../cosmograph/KgFilters';
import KnowledgeGraphLoader from '../cosmograph/KnowledgeGraphLoader';
import Legend from '../cosmograph/Legend';
import MobileGraphControls from '../cosmograph/MobileGraphControls';
import PathFinder, { type PathResult } from '../cosmograph/PathFinder';
import EgoExplore from '../cosmograph/EgoExplore';
import { useResponsive } from '../../hooks/useResponsive';
import { shouldShowKnowledgeGraphLoader } from '../cosmograph/graphRuntime';
import { ATLAS_THEME } from '../cosmograph/atlasTheme';
import { useGraphWorkspace } from '../../context/GraphWorkspaceContext';
import {
  inspectAtlasGraphicsCapability,
  isAtlasRendererFailure,
  type AtlasGraphicsCapability,
} from './atlasGraphicsCapability';
import {
  defaultAtlasTab,
  semanticZoomConfig,
  type AtlasTab,
  type AtlasZoomTier,
} from './atlasViewState';
import StableCosmographCanvas from './StableCosmographCanvas';

import { Component, type ErrorInfo, type ReactNode } from 'react';

/** Catches render-time crashes from the cosmograph WebGL layer
 *  so the page doesn't go white. Surfaces a recovery card with a
 *  reload button — the actual error is logged to the console. */
class CosmographErrorBoundary extends Component<
  { children: ReactNode; onFailure?: (error: Error) => void },
  { hasError: boolean; message: string }
> {
  state = { hasError: false, message: '' };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, message: error.message ?? 'Unknown error' };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Cosmograph crashed:', error, info.componentStack);
    this.props.onFailure?.(error);
  }

  render() {
    if (!this.state.hasError) return this.props.children;
    return (
      <div className="absolute inset-0 flex items-center justify-center p-6">
        <div className="max-w-md rounded-2xl border border-stone-300 bg-[#fffdf9]/95 p-6 text-center text-stone-900 shadow-[0_30px_90px_rgba(72,52,36,0.18)] backdrop-blur-md">
          <p className="text-base font-semibold text-orange-800">
            Atlas renderer stopped
          </p>
          <p className="mt-2 text-sm text-stone-600">
            {this.state.message}
          </p>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="mt-4 inline-flex min-h-11 items-center justify-center rounded-full bg-stone-900 px-4 py-2 text-sm font-medium text-[#fffaf1] transition-colors hover:bg-orange-900"
          >
            Recharger
          </button>
        </div>
      </div>
    );
  }
}

function AtlasGraphicsFallback({
  capability,
  onOpenScholar,
  onOpenChronos,
}: {
  capability: AtlasGraphicsCapability;
  onOpenScholar: () => void;
  onOpenChronos: () => void;
}) {
  const reason = capability.reason === 'software_renderer'
    ? 'This browser is using a software renderer.'
    : capability.reason === 'insufficient_texture_size'
      ? 'The available graphics texture limit is below the Atlas safety floor.'
      : capability.reason === 'initialization_timeout'
        ? 'The hardware renderer did not become ready within the Atlas safety window.'
        : capability.reason === 'initialization_error'
          ? 'The Atlas renderer reported an initialization error.'
        : capability.reason === 'context_lost'
          ? 'The browser reported that the Atlas graphics context was lost.'
        : 'Hardware-accelerated WebGL 2 is unavailable or disabled.';

  return (
    <section
      id="workspace-panel-atlas"
      role="tabpanel"
      aria-labelledby="workspace-mode-atlas"
      tabIndex={0}
      className="absolute inset-0 z-30 flex items-center justify-center overflow-y-auto bg-[#f7f2e9] px-5 py-24 text-stone-900 outline-none"
    >
      <div className="w-full max-w-3xl border-y border-stone-300 bg-[#fffdf9]/88 px-5 py-8 shadow-[0_30px_90px_rgba(72,52,36,0.15)] backdrop-blur-xl sm:px-9 sm:py-10">
        <div className="flex items-start gap-4">
          <span className="mt-1 flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-orange-300 bg-orange-50 text-orange-800">
            <AlertTriangle className="h-5 w-5" aria-hidden="true" />
          </span>
          <div>
            <p className="font-body text-[10px] font-semibold uppercase tracking-[0.24em] text-orange-800">
              Atlas compatibility guard
            </p>
            <h1 className="mt-2 font-display text-3xl leading-tight text-stone-950 sm:text-5xl">
              The complete graph is safe. This renderer is not.
            </h1>
            <p className="mt-4 max-w-2xl font-reader text-lg leading-7 text-stone-600">
              {reason} Atlas has been stopped before allocating its GPU surfaces, so the page stays responsive and no partial graph is shown. The same release, selection, filters, comparison, and Evidence Thread remain available in the light research modes.
            </p>
          </div>
        </div>

        <div className="mt-8 grid gap-3 sm:grid-cols-2">
          <button
            type="button"
            onClick={onOpenScholar}
            className="group min-h-20 border border-orange-800 bg-orange-800 px-5 py-4 text-left text-white outline-none transition hover:bg-orange-900 focus-visible:ring-2 focus-visible:ring-orange-800 focus-visible:ring-offset-2 focus-visible:ring-offset-[#fffdf9]"
          >
            <span className="flex items-center gap-2 font-body text-sm font-bold">
              <BookOpen className="h-4 w-4" aria-hidden="true" /> Open Scholar
            </span>
            <span className="mt-1 block font-body text-xs leading-5 text-orange-50">Search, compare, and inspect every node in an accessible table.</span>
          </button>
          <button
            type="button"
            onClick={onOpenChronos}
            className="min-h-20 border border-stone-300 bg-white/60 px-5 py-4 text-left text-stone-900 outline-none transition hover:border-teal-700 hover:bg-teal-50 focus-visible:ring-2 focus-visible:ring-teal-700 focus-visible:ring-offset-2 focus-visible:ring-offset-[#fffdf9]"
          >
            <span className="flex items-center gap-2 font-body text-sm font-bold">
              <Clock3 className="h-4 w-4" aria-hidden="true" /> Open Chronos
            </span>
            <span className="mt-1 block font-body text-xs leading-5 text-stone-600">Follow the same evidence across periods without a GPU renderer.</span>
          </button>
        </div>

        <details className="mt-7 border-t border-stone-200 pt-4 font-body text-xs text-stone-500">
          <summary className="min-h-11 cursor-pointer py-3 font-semibold text-stone-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700">
            Graphics diagnostic
          </summary>
          <dl className="mt-2 grid gap-2 sm:grid-cols-[10rem_1fr]">
            <dt>Reason</dt><dd>{capability.reason ?? 'unknown'}</dd>
            <dt>Renderer</dt><dd className="break-words">{capability.renderer || 'not exposed by the browser'}</dd>
            <dt>Max texture</dt><dd>{capability.maxTextureSize?.toLocaleString() ?? 'unavailable'}</dd>
          </dl>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="mt-4 min-h-11 border border-stone-300 px-4 font-semibold text-stone-700 hover:border-orange-700 hover:text-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700"
          >
            Retry after enabling hardware acceleration
          </button>
        </details>
      </div>
    </section>
  );
}

type Tab = AtlasTab;

const ATLAS_ENTRY_POINT_MATCHERS = {
  agency: (node: AtlasNodeMeta) => node.id.startsWith('concept_eph_hemin'),
  fate: (node: AtlasNodeMeta) => node.id.startsWith('person_chrysippus'),
  christian: (node: AtlasNodeMeta) => node.id.startsWith('concept_autexousion'),
  reception: (node: AtlasNodeMeta) => node.id.toLowerCase().includes('bobzien'),
} as const;
const ATLAS_ENTRY_POINT_CONSTELLATIONS: Readonly<Record<string, AtlasConstellationKey>> = {
  agency: 'agency',
  fate: 'stoic',
  christian: 'christian',
  reception: 'reception',
};

interface CosmoData {
  points: CosmographData | undefined;
  links: CosmographData | undefined;
  cosmographConfig: Omit<CosmographConfig, 'points' | 'links'>;
  colorByMap: Record<string, string>;
  colorById: Record<string, string>;
  sizeById: Record<string, number>;
  customLabels?: NonNullable<CosmographConfig['customLabels']>;
}

function compactNode(
  meta: AtlasNodeMeta,
  colorKey: string,
  constellation: string,
  constellationKey: AtlasConstellationKey,
  position?: readonly [number, number],
) {
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
    constellation,
    constellationStrength: constellationKey === 'core' ? 1 : 0.88,
    x: position?.[0],
    y: position?.[1],
    layer: meta.layer,
  };
}

function colorKeyFor(meta: AtlasNodeMeta): string {
  // Unique key per (type, layer) — kept stable so the colorByMap stays small.
  return `${meta.layer}:${meta.typeKey}`;
}

function buildAtlasConstellationLayout(
  meta: ReadonlyArray<AtlasNodeMeta>,
  constellationLabels: Readonly<Record<AtlasConstellationKey, string>>,
): {
  positions: Map<string, readonly [number, number]>;
  labels: NonNullable<CosmographConfig['customLabels']>;
} {
  const groups = new Map<AtlasConstellationKey, AtlasNodeMeta[]>();
  for (const node of meta) {
    const key = atlasConstellationKey(node);
    const group = groups.get(key) ?? [];
    group.push(node);
    groups.set(key, group);
  }

  const positions = new Map<string, readonly [number, number]>();
  const labels: NonNullable<CosmographConfig['customLabels']> = [];
  for (const [key, unsorted] of groups) {
    const nodes = [...unsorted].sort((left, right) =>
      right.importance - left.importance || left.id.localeCompare(right.id));
    const hub = ATLAS_CONSTELLATION_POSITIONS[key];
    if (key === 'core') {
      nodes.forEach((node, index) => {
        const angle = index * Math.PI * (3 - Math.sqrt(5));
        const radius = index === 0 ? 0 : 55 + index * 16;
        positions.set(node.id, [Math.cos(angle) * radius, Math.sin(angle) * radius]);
      });
    } else {
      const baseAngle = Math.atan2(hub[1], hub[0]);
      const hubRadius = Math.hypot(hub[0], hub[1]);
      const branchCount = Math.max(3, Math.min(7, Math.ceil(Math.sqrt(nodes.length))));
      nodes.forEach((node, index) => {
        if (index === 0) {
          positions.set(node.id, hub);
          return;
        }
        const branch = (index - 1) % branchCount;
        const level = Math.floor((index - 1) / branchCount) + 1;
        const branchOffset = (branch - (branchCount - 1) / 2) * 0.115;
        const angle = baseAngle + branchOffset;
        const radius = hubRadius + 115 + level * 105;
        positions.set(node.id, [Math.cos(angle) * radius, Math.sin(angle) * radius]);
      });
    }

    const labelPosition: [number, number] = key === 'core'
      ? [0, -90]
      : [hub[0] * 0.86, hub[1] * 0.86];
    labels.push({
      text: constellationLabels[key],
      position: labelPosition,
      weight: key === 'core' ? 1 : 0.92,
      fontSize: key === 'core' ? 15 : 13,
      maxWidth: 220,
      className: [
        'background: rgba(255,253,249,0.88)',
        'border: 1px solid rgba(120,113,108,0.22)',
        'color: #44403c',
        'border-radius: 999px',
        'font-weight: 750',
        'letter-spacing: 0.075em',
        'text-transform: uppercase',
        'box-shadow: 0 10px 28px rgba(72,52,36,0.10)',
      ].join('; '),
      padding: { left: 9, top: 5, right: 9, bottom: 5 },
    });
  }
  return { positions, labels };
}

async function buildCosmoData(
  meta: ReadonlyArray<AtlasNodeMeta>,
  edges: ReadonlyArray<AtlasEdgeMeta>,
  constellationLabels?: Readonly<Record<AtlasConstellationKey, string>>,
): Promise<CosmoData> {
  const colorByMap: Record<string, string> = {};
  const colorById: Record<string, string> = {};
  const sizeById: Record<string, number> = {};

  meta.forEach((node) => {
    const isCore = constellationLabels && atlasConstellationKey(node) === 'core';
    const key = isCore ? 'atlas:core' : colorKeyFor(node);
    const color = isCore ? ATLAS_THEME.hover : node.color;
    colorByMap[key] = color;
    colorById[node.id] = color;
    sizeById[node.id] = isCore ? 38 : node.size;
  });

  const layout = constellationLabels
    ? buildAtlasConstellationLayout(meta, constellationLabels)
    : null;
  const points = meta.map((node) => {
    const constellationKey = atlasConstellationKey(node);
    const colorKey = constellationLabels && constellationKey === 'core'
      ? 'atlas:core'
      : colorKeyFor(node);
    return compactNode(
      node,
      colorKey,
      constellationLabels?.[constellationKey] ?? constellationKey,
      constellationKey,
      layout?.positions.get(node.id),
    );
  });
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
        ...(constellationLabels
          ? {
              pointClusterBy: 'constellation',
              pointClusterStrengthBy: 'constellationStrength',
              pointXBy: 'x',
              pointYBy: 'y',
            }
          : {}),
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
    customLabels: layout?.labels,
  };
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

export default function AtlasWorkspace() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const graphRef = useRef<CosmographRef>(undefined);
  const lastFocusedNodeRef = useRef<string | null>(null);
  const { isMobile } = useResponsive();
  const {
    state: workspace,
    data,
    loading,
    selectPrimary,
    setEvidenceThread,
    setFilters,
    setCamera,
    setMode,
    ensureNodeDetail,
  } = useGraphWorkspace();
  const allMeta = data.meta;
  const allEdges = data.edges;
  const rawById = data.rawById;
  const relationships = data.relationships;
  const filters = workspace.filters;
  const selectedNodeId = workspace.primarySelection;
  const nodesCompact = formatCompact(allMeta.length || Number.NaN, i18n.language);

  // Default tab is *derived* from viewport, not stored on first render. The
  // useState initializer ran during prerender (no `window`), so it had no way
  // of knowing the visitor was on a phone — and the server-rendered value
  // would persist on the client even after hydration because nothing flipped
  // it back. We track only the user's *explicit* choice; the actual `tab`
  // value falls back to a viewport-aware default on every render.
  const [userTab, setUserTab] = useState<Tab | null>(null);
  // Start with the curated intellectual Atlas on desktop. Opening the full
  // 23k-node release as the first frame produces a hairball and makes the
  // highest-value evidence routes harder to discover. The complete graph is
  // still one explicit action away and shares the exact same session state.
  const tab: Tab = userTab ?? defaultAtlasTab(isMobile);
  const setTab = useCallback((next: Tab | ((current: Tab) => Tab)) => {
    setUserTab((prev) => {
      const current = prev ?? defaultAtlasTab(isMobile);
      return typeof next === 'function' ? (next as (c: Tab) => Tab)(current) : next;
    });
  }, [isMobile]);
  const [cosmo, setCosmo] = useState<CosmoData | null>(null);
  const [activeMeta, setActiveMeta] = useState<ReadonlyArray<AtlasNodeMeta>>([]);
  const [, setActiveEdges] = useState<ReadonlyArray<AtlasEdgeMeta>>([]);
  const activeMetaById = useMemo(
    () => new Map(activeMeta.map((node) => [node.id, node])),
    [activeMeta],
  );
  const atlasEntryPoints = useMemo(
    () => Object.entries(ATLAS_ENTRY_POINT_MATCHERS)
      .map(([key, matcher]) => ({ key, node: activeMeta.find(matcher) }))
      .filter((entry): entry is { key: string; node: AtlasNodeMeta } => Boolean(entry.node)),
    [activeMeta],
  );
  const atlasConstellationLabels = useMemo<Readonly<Record<AtlasConstellationKey, string>>>(
    () => ({
      core: t('cosmograph.atlas.constellations.core', 'The free-will question'),
      agency: t('cosmograph.atlas.constellations.agency', 'Action and choice'),
      stoic: t('cosmograph.atlas.constellations.stoic', 'Stoic fate'),
      epicurean: t('cosmograph.atlas.constellations.epicurean', 'Epicurean alternatives'),
      peripatetic: t('cosmograph.atlas.constellations.peripatetic', 'Peripatetic critique'),
      christian: t('cosmograph.atlas.constellations.christian', 'Christian freedom'),
      late_antique: t('cosmograph.atlas.constellations.lateAntique', 'Late antique synthesis'),
      reception: t('cosmograph.atlas.constellations.reception', 'Modern interpretations'),
    }),
    [t],
  );

  const [graphReady, setGraphReady] = useState(false);
  const [graphicsCapability, setGraphicsCapability] = useState<
    AtlasGraphicsCapability | { status: 'checking' }
  >({ status: 'checking' });

  useEffect(() => {
    setGraphicsCapability(inspectAtlasGraphicsCapability());
  }, []);

  useEffect(() => {
    if (selectedNodeId) void ensureNodeDetail(selectedNodeId);
  }, [ensureNodeDetail, selectedNodeId]);

  // Semantic-zoom tier: derived from current camera zoom, debounced. Drives
  // *render* density only (top-label cap, link visibility range, hub label
  // opacity) — never the underlying point/link dataset. Crossing a tier
  // boundary therefore never restarts the simulation.
  const [zoomTier, setZoomTier] = useState<AtlasZoomTier>('overview');
  const zoomDebounceRef = useRef<number | null>(null);
  const cameraDiveTimeoutRef = useRef<number | null>(null);
  const handleSemanticZoom = useCallback((...args: unknown[]) => {
    let next = NaN;
    let x = workspace.cameraByMode.atlas?.x ?? 0;
    let y = workspace.cameraByMode.atlas?.y ?? 0;
    for (const arg of args) {
      if (typeof arg === 'number' && Number.isFinite(arg)) { next = arg; break; }
      if (arg && typeof arg === 'object' && 'k' in arg && typeof (arg as { k: unknown }).k === 'number') {
        const transform = arg as { k: number; x?: number; y?: number };
        next = transform.k;
        if (typeof transform.x === 'number') x = transform.x;
        if (typeof transform.y === 'number') y = transform.y;
        break;
      }
      if (arg && typeof arg === 'object' && 'transform' in arg) {
        const tf = (arg as { transform?: { k?: number; x?: number; y?: number } }).transform;
        if (tf && typeof tf.k === 'number') {
          next = tf.k;
          if (typeof tf.x === 'number') x = tf.x;
          if (typeof tf.y === 'number') y = tf.y;
          break;
        }
      }
    }
    if (!Number.isFinite(next)) return;
    if (zoomDebounceRef.current !== null) window.clearTimeout(zoomDebounceRef.current);
    zoomDebounceRef.current = window.setTimeout(() => {
      const tier = next >= 4.0 ? 'close' : next >= 1.5 ? 'mid' : 'overview';
      setZoomTier((prev) => (prev === tier ? prev : tier));
      setCamera('atlas', { x, y, zoom: next });
    }, 180);
  }, [setCamera, workspace.cameraByMode.atlas]);

  useEffect(() => () => {
    if (zoomDebounceRef.current !== null) window.clearTimeout(zoomDebounceRef.current);
    if (cameraDiveTimeoutRef.current !== null) {
      window.clearTimeout(cameraDiveTimeoutRef.current);
    }
  }, []);

  const [pathSource, setPathSource] = useState<AtlasNodeMeta | null>(null);
  const [pathTarget, setPathTarget] = useState<AtlasNodeMeta | null>(null);
  const [pathResult, setPathResult] = useState<PathResult | null>(null);
  const [simulationRunning, setSimulationRunning] = useState(true);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const [legendOpen, setLegendOpen] = useState(false);
  const focusedConstellationRef = useRef<AtlasConstellationKey | null>(null);
  const entryNavigationRef = useRef<HTMLElement | null>(null);
  const setConstellationFocus = useCallback((key: AtlasConstellationKey | null) => {
    focusedConstellationRef.current = key;
    entryNavigationRef.current
      ?.querySelectorAll<HTMLButtonElement>('[data-constellation]')
      .forEach((button) => {
        const active = button.dataset.constellation === key;
        button.dataset.active = String(active);
        button.setAttribute('aria-pressed', String(active));
      });
  }, []);

  // Mobile zoom-tier system retired: pinching used to swap the slice
  // mid-gesture, which restarted the simulation and felt like a full
  // refresh. The active slice is now driven entirely by the tab on
  // mobile too, so pinch-zoom is purely a camera transform.

  // --- Derive active slice (atlas / full / filtered) ---
  //
  // The mobile "zoom tier" system used to switch slices mid-pinch (overview
  // / mid / detail) whenever the user crossed a zoom threshold. That meant
  // rebuilding the Cosmograph dataset and restarting the simulation on
  // every pinch — perceived as "the whole graph refreshes when I zoom".
  // We now use the same tab-driven slice everywhere; zoom on mobile is
  // purely camera transform, no data churn.
  useEffect(() => {
    if (graphicsCapability.status !== 'supported') {
      setCosmo(null);
      setGraphReady(false);
      return;
    }
    if (allMeta.length === 0) return;
    let cancelled = false;

    async function computeActive() {
      let metaSlice: ReadonlyArray<AtlasNodeMeta> = allMeta;

      if (tab === 'atlas') {
        const ids = pickAtlasLandingNodeIds(
          allMeta.map((m) => ({ id: m.id, type: m.typeKey, importance: m.importance })),
          allEdges,
          72,
        );
        metaSlice = allMeta.filter((m) => ids.has(m.id));
      }
      if (tab === 'filter') {
        metaSlice = filterMeta(allMeta, filters);
      }
      // tab === 'full' and 'path' use the whole graph

      const idSet = new Set(metaSlice.map((m) => m.id));
      const edgeSlice = tab === 'atlas'
        ? pickAtlasLandingEdges(
            idSet,
            allEdges,
            pickAtlasNodeIds(
              allMeta.map((m) => ({ id: m.id, type: m.typeKey, importance: m.importance })),
            ),
          )
        : allEdges.filter((e) => idSet.has(e.source) && idSet.has(e.target));

      const built = await buildCosmoData(
        metaSlice,
        edgeSlice,
        tab === 'atlas' ? atlasConstellationLabels : undefined,
      );
      if (cancelled) return;
      setActiveMeta(metaSlice);
      setActiveEdges(edgeSlice);
      setCosmo(built);
    }

    void computeActive();
    return () => {
      cancelled = true;
    };
  }, [allMeta, allEdges, atlasConstellationLabels, tab, filters, graphicsCapability.status]);

  // Path mode forces full graph behind the scenes so BFS can find anything.
  useEffect(() => {
    if (graphicsCapability.status !== 'supported') return;
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
  }, [tab, allMeta, allEdges, activeMeta.length, graphicsCapability.status]);

  useEffect(() => {
    if (graphicsCapability.status !== 'supported' || !cosmo || graphReady) return;
    const timeout = window.setTimeout(() => {
      setGraphicsCapability({
        status: 'unsupported',
        reason: 'initialization_timeout',
        renderer: graphicsCapability.renderer,
        maxTextureSize: graphicsCapability.maxTextureSize,
      });
    }, 15_000);
    return () => window.clearTimeout(timeout);
  }, [cosmo, graphReady, graphicsCapability]);

  useEffect(() => {
    if (!graphReady || graphicsCapability.status !== 'supported') return;
    const canvas = document.querySelector<HTMLCanvasElement>('#workspace-panel-atlas canvas');
    if (!canvas) return;
    const handleContextLost = (event: Event) => {
      event.preventDefault();
      setGraphicsCapability({
        status: 'unsupported',
        reason: 'context_lost',
        renderer: graphicsCapability.renderer,
        maxTextureSize: graphicsCapability.maxTextureSize,
      });
    };
    canvas.addEventListener('webglcontextlost', handleContextLost);
    return () => canvas.removeEventListener('webglcontextlost', handleContextLost);
  }, [graphReady, graphicsCapability]);

  useEffect(() => {
    if (graphicsCapability.status !== 'supported') return;
    const fail = () => setGraphicsCapability({
      status: 'unsupported',
      reason: 'initialization_error',
      renderer: graphicsCapability.renderer,
      maxTextureSize: graphicsCapability.maxTextureSize,
    });
    const handleError = (event: ErrorEvent) => {
      if (!isAtlasRendererFailure(event.error ?? event.message)) return;
      event.preventDefault();
      fail();
    };
    const handleRejection = (event: PromiseRejectionEvent) => {
      if (!isAtlasRendererFailure(event.reason)) return;
      event.preventDefault();
      fail();
    };
    window.addEventListener('error', handleError);
    window.addEventListener('unhandledrejection', handleRejection);
    return () => {
      window.removeEventListener('error', handleError);
      window.removeEventListener('unhandledrejection', handleRejection);
    };
  }, [graphicsCapability]);

  const selectedRaw = selectedNodeId ? rawById.get(selectedNodeId) ?? null : null;
  const selectedRelationships = selectedNodeId ? relationships.get(selectedNodeId) ?? [] : [];

  const focusNodeById = useCallback(
    async (id: string) => {
      lastFocusedNodeRef.current = id;
      if (cameraDiveTimeoutRef.current === null) {
        setConstellationFocus(null);
      }
      startTransition(() => selectPrimary(id));
      if (!graphRef.current) return;
      const neighbourIds = (relationships.get(id) ?? [])
        .map((relationship) => relationship.id)
        .filter((candidate) => activeMetaById.has(candidate))
        .sort((left, right) =>
          (activeMetaById.get(right)?.importance ?? 0)
          - (activeMetaById.get(left)?.importance ?? 0)
          || left.localeCompare(right))
        .slice(0, 12);
      const focusIds = [id, ...neighbourIds];
      const indices = await graphRef.current.getPointIndicesByIds(focusIds);
      const pointIndex = indices?.[0];
      if (pointIndex === undefined) {
        // Not in the active slice — open detail without focusing.
        return;
      }
      const clean = (indices ?? []).filter((index): index is number => typeof index === 'number');
      graphRef.current.selectPoints(clean, false);
      graphRef.current.setFocusedPoint(pointIndex);
      if (clean.length > 1) {
        graphRef.current.fitViewByIndices(clean, 600, 0.25);
      } else {
        graphRef.current.zoomToPoint(pointIndex, 500, 3.4, true);
      }
    },
    [activeMetaById, relationships, selectPrimary, setConstellationFocus],
  );

  const focusConstellation = useCallback((key: AtlasConstellationKey) => {
    if (!graphRef.current) return;
    // `buildCosmoData` preserves this array order and every canvas callback
    // already indexes `activeMeta` directly. Reusing that deterministic index
    // avoids an unnecessary DuckDB lookup that could briefly return no rows
    // while the selection client refreshed.
    const clean = activeMeta
      .map((node, index) => ({ node, index }))
      .filter(({ node }) => atlasConstellationKey(node) === key)
      .sort(({ node: left }, { node: right }) =>
        right.importance - left.importance || left.id.localeCompare(right.id))
      .map(({ index }) => index);
    if (clean.length === 0) return;
    lastFocusedNodeRef.current = null;
    selectPrimary(null);
    // Reproduce the reference's overview -> department dive. Fitting the
    // selected points was often indistinguishable from the landing view on a
    // wide canvas; anchoring the camera on the constellation's most important
    // node gives the action a clear spatial result while retaining the whole
    // selected branch as context.
    if (cameraDiveTimeoutRef.current !== null) {
      window.clearTimeout(cameraDiveTimeoutRef.current);
    }
    // Keep the navigation state outside React's render cycle: the Cosmograph
    // wrapper reapplies its complete WebGL config on every parent render.
    // Commit the DuckDB selection first as well, then start the camera on the
    // settled renderer so no later refresh can snap it back to the overview.
    setConstellationFocus(key);
    graphRef.current.setFocusedPoint(clean[0]);
    graphRef.current.selectPoints(clean, false);
    cameraDiveTimeoutRef.current = window.setTimeout(() => {
      // A fixed department-scale zoom keeps the hub at the visual centre and
      // leaves enough vertical room for its authored branches above the entry
      // rail. Fitting sparse constellations over-zooms them; fitting rich ones
      // suppresses their labels through collision avoidance.
      graphRef.current?.zoomToPoint(clean[0], 760, 3.3, false);
      cameraDiveTimeoutRef.current = window.setTimeout(() => {
        cameraDiveTimeoutRef.current = null;
      }, 820);
    }, 700);
  }, [activeMeta, selectPrimary, setConstellationFocus]);

  useEffect(() => {
    if (
      graphReady &&
      selectedNodeId &&
      lastFocusedNodeRef.current !== selectedNodeId
    ) {
      void focusNodeById(selectedNodeId);
    }
  }, [focusNodeById, graphReady, selectedNodeId]);

  // Re-fit the view only when the *user* explicitly switches the active
  // slice (tab change, filter change). Crucially, mobile tier transitions
  // are driven by the user's pinch zoom — re-fitting then yanks the camera
  // away from where they're aiming and feels like the graph "refreshes"
  // every time they zoom. We deliberately ignore those.
  useEffect(() => {
    if (!graphReady || !graphRef.current) return;
    if (activeMeta.length === 0) return;
    const padding = isMobile ? 0.24 : 0.16;
    const handles = [600, 1400, 2400].map((delay) =>
      window.setTimeout(() => {
        graphRef.current?.fitView(500, padding);
      }, delay),
    );
    return () => handles.forEach((h) => window.clearTimeout(h));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, filters, graphReady]);

  useEffect(() => {
    if (!graphReady || !graphRef.current) return;
    const camera = workspace.cameraByMode.atlas;
    if (camera) graphRef.current.setZoomLevel(camera.zoom, 0);
    // Restore only when entering/mounting Atlas; live camera changes are
    // captured by onZoom and must not feed back into the renderer.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [graphReady]);


  function clearSelection() {
    // Cosmograph can emit a synthetic background click when a programmatic
    // fit begins under the pointer that activated an overlaid entry chip.
    // Ignore that one transition-frame reset; deliberate canvas clicks work
    // again as soon as the branch-selection handoff completes.
    if (cameraDiveTimeoutRef.current !== null) return;
    lastFocusedNodeRef.current = null;
    graphRef.current?.unselectAllPoints();
    graphRef.current?.setFocusedPoint(undefined);
    selectPrimary(null);
    setConstellationFocus(null);
    graphRef.current?.fitView(500, 0.12);
  }

  function fitView() {
    if (cameraDiveTimeoutRef.current !== null) {
      window.clearTimeout(cameraDiveTimeoutRef.current);
      cameraDiveTimeoutRef.current = null;
    }
    graphRef.current?.unselectAllPoints();
    graphRef.current?.setFocusedPoint(undefined);
    setConstellationFocus(null);
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

  function settleAtlasView() {
    setSimulationRunning(false);
    // The force layout can continue moving after the last scheduled startup
    // fit. Reframe its final coordinates once—unless the scholar is already
    // focused on a node—so disconnected satellites do not leave the actual
    // argument map as a tiny island in a mostly empty canvas.
    if (lastFocusedNodeRef.current === null) {
      graphRef.current?.fitView(0, 0.08);
      const fittedZoom = graphRef.current?.getZoomLevel();
      if (typeof fittedZoom === 'number' && Number.isFinite(fittedZoom)) {
        graphRef.current?.setZoomLevel(fittedZoom * 1.4, 650);
      }
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
        customLabels: [],
        backgroundColor: ATLAS_THEME.surface,
        renderHoveredPointRing: true,
        hoveredPointRingColor: ATLAS_THEME.hover,
        focusedPointRingColor: ATLAS_THEME.focus,
        pointDefaultColor: ATLAS_THEME.nodes.concept,
        pointDefaultSize: 1.6,
        pointGreyoutOpacity: pathResult ? 0.07 : 0.04,
        linkDefaultColor: 'rgba(87,83,78,0.26)',
        linkGreyoutOpacity: pathResult ? 0.03 : 0.012,
        linkDefaultWidth: 1,
        ...semanticZoomConfig(tab, zoomTier, isMobile),
        hoveredLinkColor: ATLAS_THEME.ink,
        hoveredLinkWidthIncrease: 1.5,
        // Semantic zoom: edges fade with distance more aggressively at low
        // zoom (overview) and progressively reveal as the user zooms in.
        // The data array is untouched — only this range changes.
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
          ? tab === 'atlas'
            ? 3600
            : 7200
          : tab === 'atlas'
            ? 2800
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
        pointSizeRange: [4, 38],
        // `showTopLabels` is ignored by Cosmograph when the master label gate
        // is false. Keep dynamic sampling off, but render a strictly bounded
        // semantic label budget so the landing Atlas is a map, not unlabeled
        // decorative particles.
        showLabels: true,
        showDynamicLabels: false,
        showTopLabels: tab !== 'atlas' || Boolean(selectedNodeId),
        // Semantic-zoom label budget is injected above. The authored 66-node
        // Atlas remains fixed; the complete graph scales 12 → 36 → 120.
        showFocusedPointLabel: true,
        showClusterLabels: tab === 'atlas' && !selectedNodeId,
        showClusterLabelsLimit: 8,
        clusterLabelFontSize: 12,
        scaleClusterLabels: false,
        usePointColorStrategyForClusterLabels: false,
        clusterLabelClassName: () => [
          'background: rgba(255,253,249,0.96)',
          'border: 1px solid rgba(120,113,108,0.28)',
          'color: #292524',
          'border-radius: 999px',
          'font-weight: 700',
          'letter-spacing: 0.045em',
          'box-shadow: 0 8px 22px rgba(72,52,36,0.10)',
        ].join('; '),
        showHoveredPointLabel: true,
        showUnselectedPointLabels: tab !== 'atlas' && !selectedNodeId,
        showSelectedLabels: true,
        selectedPointLabelsLimit: 24,
        pointLabelBy: 'label',
        pointLabelFontSize: 11,
        labelMargin: 5,
        labelPadding: [5, 3, 5, 3],
        pointLabelClassName: () =>
          [
            'background: rgba(255,253,249,0.94)',
            'border: 1px solid rgba(120,113,108,0.28)',
            'color: #292524',
            'border-radius: 999px',
            'backdrop-filter: blur(8px)',
            'font-weight: 600',
            'box-shadow: 0 6px 22px rgba(72,52,36,0.12)',
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
        enableSimulation: !isMobile && tab !== 'atlas',
        simulationDecay: isMobile ? 0 : 4300,
        simulationGravity: isMobile
          ? 0
          : tab === 'atlas'
            ? 0.12
            : 0.08,
        simulationCenter: isMobile ? 0 : 0.01,
        simulationRepulsion: isMobile
          ? 0
          : tab === 'atlas'
            ? 3.2
            : 2.2,
        simulationRepulsionTheta: 1.08,
        simulationLinkSpring: isMobile ? 0 : 0.74,
        simulationLinkDistance: isMobile
          ? 0
          : tab === 'atlas'
            ? 58
            : 36,
        simulationFriction: 0.9,
        simulationImpulse: 0,
      }
    : undefined;

  const rendererRevision = useMemo(
    () => ({
      cosmo,
      isMobile,
      pathResult,
      selectedNodeId,
      tab,
    }),
    [cosmo, isMobile, pathResult, selectedNodeId, tab],
  );
  const semanticRendererConfig = useMemo(
    () => semanticZoomConfig(tab, zoomTier, isMobile),
    [isMobile, tab, zoomTier],
  );

  useEffect(() => {
    if (!graphReady || !graphRef.current) return;
    // Partial config only: never resend points/links during camera movement.
    void graphRef.current.setConfig(semanticRendererConfig);
  }, [graphReady, semanticRendererConfig]);

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

  useEffect(() => {
    if (pathResult?.ids.length) {
      setEvidenceThread([...pathResult.ids]);
    }
  }, [pathResult, setEvidenceThread]);

  return (
    <div className="absolute inset-0 overflow-hidden bg-[#f7f2e9]">

      {/* Light-dominant parchment field. The fine atlas grid provides spatial
          orientation without competing with evidence paths or labels. */}
      <div aria-hidden className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_16%_18%,rgba(194,65,12,0.08),transparent_32%),radial-gradient(circle_at_82%_16%,rgba(15,118,110,0.08),transparent_31%),radial-gradient(circle_at_52%_88%,rgba(161,98,7,0.08),transparent_30%)]" />
        <div className="absolute inset-0 opacity-45 [background-image:linear-gradient(rgba(120,113,108,0.055)_1px,transparent_1px),linear-gradient(90deg,rgba(120,113,108,0.055)_1px,transparent_1px)] [background-size:36px_36px]" />
      </div>

      {/* The film is decorative, never a readiness gate. The loader leaves as
          soon as data is complete and Cosmograph has mounted; reduced-motion
          users therefore wait only for real work, never for an 8 s intro. */}
      <AnimatePresence>
        {shouldShowKnowledgeGraphLoader({
          loading,
          graphReady,
          hasError: graphicsCapability.status === 'unsupported',
        }) && (
          <KnowledgeGraphLoader key="kg-loader" />
        )}
      </AnimatePresence>

      {graphicsCapability.status === 'unsupported' && (
        <AtlasGraphicsFallback
          capability={graphicsCapability}
          onOpenScholar={() => setMode('scholar')}
          onOpenChronos={() => setMode('chronos')}
        />
      )}

      {graphicsCapability.status === 'supported' && cosmo && dynamicConfig && (
        <section
          id="workspace-panel-atlas"
          role="tabpanel"
          aria-labelledby="workspace-mode-atlas"
          tabIndex={0}
          className="absolute inset-0 outline-none"
        >
        <CosmographProvider>
          <CosmographErrorBoundary
            onFailure={() => setGraphicsCapability({
              status: 'unsupported',
              reason: 'initialization_error',
              renderer: graphicsCapability.renderer,
              maxTextureSize: graphicsCapability.maxTextureSize,
            })}
          >
          <StableCosmographCanvas
            config={dynamicConfig}
            revision={rendererRevision}
            graphRef={graphRef}
            handlers={{
              onMount: () => setGraphReady(true),
              onSimulationStart: () => setSimulationRunning(true),
              onSimulationUnpause: () => setSimulationRunning(true),
              onSimulationPause: () => setSimulationRunning(false),
              onSimulationEnd: settleAtlasView,
              // Camera transform only — the dataset never changes on zoom.
              // The stable boundary persists camera/tier state without
              // feeding a complete config back into the WebGL renderer.
              onZoom: handleSemanticZoom,
              onPointClick: (index) => {
                const clicked = activeMeta[index];
                if (!clicked) return;
                void focusNodeById(clicked.id);
              },
              onLabelClick: (_index, id) => {
                void focusNodeById(id);
              },
              onBackgroundClick: () => clearSelection(),
            }}
          />
          </CosmographErrorBoundary>

          {/* === Mobile-only controls (FAB, bottom-sheet) ===
              MobileGraphControls owns the 'atlas/full/path/filter' tab set; the
              Explore tab lives in its own dedicated layer and is reached via
              the Explore/Map toggle below. When the user is on Explore we hide
              MobileGraphControls so its FAB doesn't compete with the Explore
              search bar pinned at the bottom of the viewport. */}
          {isMobile && tab !== 'explore' && (
            <MobileGraphControls
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

          {/* === Mobile-only Explore <-> Map toggle (top-right) === */}
          {isMobile && (
            <button
              type="button"
              // Mobile Map = the curated Atlas (~150 nodes). The full 17.7k
              // graph at this viewport collapses into a hairball; Atlas
              // shows the load-bearing thinkers, schools and concepts so
              // the canvas is actually readable.
              onClick={() => setTab((current) => (current === 'explore' ? 'atlas' : 'explore'))}
              aria-label={
                tab === 'explore'
                  ? (t('cosmograph.explore.openMap', 'Open the map view') as string)
                  : (t('cosmograph.explore.openExplore', 'Open the explore view') as string)
              }
              className={[
                'absolute right-[calc(0.75rem+env(safe-area-inset-right))] top-[calc(4.75rem+env(safe-area-inset-top))] z-40 inline-flex min-h-11 items-center gap-1.5 rounded-full px-3 py-1.5 text-[12px] font-medium shadow-[0_8px_24px_-12px_rgba(15,23,42,0.45)] backdrop-blur-md transition-colors md:hidden',
                tab === 'explore'
                  ? 'border border-amber-300/70 bg-white/85 text-amber-900 hover:bg-amber-50'
                  : 'border border-stone-300 bg-[#fffdf9]/90 text-stone-800 hover:border-orange-500 hover:text-orange-800',
              ].join(' ')}
            >
              {tab === 'explore' ? (
                <>
                  <MapIcon className="h-3.5 w-3.5" aria-hidden />
                  {t('cosmograph.explore.toggleMap', 'Map')}
                </>
              ) : (
                <>
                  <Sparkles className="h-3.5 w-3.5" aria-hidden />
                  {t('cosmograph.explore.toggleExplore', 'Explore')}
                </>
              )}
            </button>
          )}

          {/* === Mobile Explore overlay === */}
          {isMobile && tab === 'explore' && (
            <div
              role="region"
              aria-label={t('cosmograph.explore.region', 'Explore the knowledge graph') as string}
              className="absolute inset-0 z-30"
            >
              <EgoExplore
                meta={allMeta}
                rawById={rawById}
                relationships={relationships}
                initialNodeId={selectedNodeId ?? undefined}
                onPickNode={(id) => selectPrimary(id)}
              />
            </div>
          )}

          {/* === Top bar: search + tabs (desktop only; mobile uses
              MobileGraphControls below) === */}
          <div className="pointer-events-none absolute inset-x-0 top-20 z-30 hidden px-3 md:block md:px-6">
            <div className="pointer-events-auto mx-auto flex w-full max-w-[56rem] flex-col gap-3">
              <div className="flex flex-col gap-2 lg:flex-row lg:items-center">
                <div className="flex min-w-0 flex-1 items-center gap-2">
                  <button
                  type="button"
                  onClick={() => navigate('/')}
                  className="hidden h-10 w-10 shrink-0 items-center justify-center rounded-full border border-stone-300 bg-[#fffdf9]/92 text-stone-600 shadow-[0_8px_24px_rgba(72,52,36,0.08)] transition-colors hover:border-orange-500 hover:text-orange-800 md:inline-flex"
                  aria-label={t('cosmograph.back', 'Back')}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </button>

                  <div className="min-w-0 flex-1">
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
              </div>

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

          {/* === Top-right: Atlas canvas controls (desktop only) === */}
          <div className="absolute right-3 top-20 z-30 hidden flex-col items-end gap-2 md:right-6 md:flex">
            <div className="flex items-center gap-1">
              <IconButton
                label={t('cosmograph.controls.fit', 'Fit view')}
                icon={<Focus className="h-4 w-4" />}
                onClick={fitView}
              />
              <IconButton
                label={t('cosmograph.atlas.guide', 'Atlas guide')}
                icon={<Sparkles className="h-4 w-4" />}
                onClick={() => setHelpOpen((open) => !open)}
              />
              <IconButton
                label={legendOpen
                  ? t('cosmograph.legend.hide', 'Hide legend')
                  : t('cosmograph.legend.show', 'Show legend')}
                icon={<MapIcon className="h-4 w-4" />}
                onClick={() => setLegendOpen((open) => !open)}
              />
              <IconButton
                label={t('cosmograph.controls.settings', 'Advanced')}
                icon={<Settings className="h-4 w-4" />}
                onClick={() => setAdvancedOpen((open) => !open)}
              />
            </div>
          </div>

          {tab === 'atlas' && !selectedNodeId && atlasEntryPoints.length > 0 && (
            <nav
              ref={entryNavigationRef}
              aria-label={t('cosmograph.atlas.startWith', 'Start with a question')}
              className="pointer-events-auto absolute bottom-4 left-1/2 z-20 hidden -translate-x-1/2 flex-wrap items-center justify-center gap-1.5 rounded-full border border-stone-300 bg-[#fffdf9]/92 p-1.5 shadow-[0_12px_34px_rgba(72,52,36,0.11)] backdrop-blur-xl md:flex"
            >
              <span className="ml-2 mr-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-stone-500">
                {t('cosmograph.atlas.startWith', 'Start with')}
              </span>
              {atlasEntryPoints.map(({ key, node }) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => void focusConstellation(
                    ATLAS_ENTRY_POINT_CONSTELLATIONS[key] ?? atlasConstellationKey(node),
                  )}
                  data-constellation={ATLAS_ENTRY_POINT_CONSTELLATIONS[key]}
                  data-active={String(
                    focusedConstellationRef.current === ATLAS_ENTRY_POINT_CONSTELLATIONS[key],
                  )}
                  aria-pressed={
                    focusedConstellationRef.current === ATLAS_ENTRY_POINT_CONSTELLATIONS[key]
                  }
                  className="min-h-9 rounded-full px-3 text-[11px] font-semibold text-stone-700 transition hover:bg-orange-50 hover:text-orange-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700 data-[active=true]:bg-stone-900 data-[active=true]:text-[#fffaf1] data-[active=true]:hover:bg-stone-900 data-[active=true]:hover:text-[#fffaf1]"
                >
                  {t(`cosmograph.atlas.entryPoints.${key}`, key)}
                </button>
              ))}
            </nav>
          )}

          {/* === Bottom-right: Legend (desktop only) === */}
          {legendOpen && (
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
          )}

          {/* === Bottom-left: contextual hint (Atlas first-time, desktop) === */}
          {tab === 'atlas' && helpOpen && !isMobile && (
            <div className="pointer-events-auto absolute bottom-4 left-3 z-20 hidden max-w-sm rounded-2xl border border-stone-300 bg-[#fffdf9]/92 p-4 text-[12px] text-stone-600 shadow-[0_18px_50px_rgba(72,52,36,0.14)] backdrop-blur-xl md:left-6 md:block">
              <div className="mb-1 flex items-center gap-2 text-teal-800">
                <Sparkles className="h-3.5 w-3.5" />
                <span className="text-[11px] font-semibold uppercase tracking-[0.18em]">
                  {t('cosmograph.atlas.hintLabel', 'Free Will Atlas')}
                </span>
                <button
                  type="button"
                  onClick={() => setHelpOpen(false)}
                  aria-label={t('common.dismiss', 'Dismiss')}
                  className="ml-auto inline-flex h-6 w-6 items-center justify-center rounded-full border border-stone-300 bg-white/70 text-stone-500 transition-colors hover:border-orange-500 hover:text-orange-800"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
              <p className="leading-5">
                {t(
                  'cosmograph.atlas.hintBody',
                  'A curated view of the load-bearing concepts, schools, thinkers, and modern scholars on free will. Search to dive deeper, switch to the full graph for the {{nodes}}-node map, or open Find a path to trace a connection.',
                  { nodes: nodesCompact },
                )}
              </p>
            </div>
          )}

          {/* Advanced drawer (formerly Simulation lab) */}
          {advancedOpen && (
            <AdvancedDrawer
              onClose={() => setAdvancedOpen(false)}
              simulationRunning={simulationRunning}
              onToggleSimulation={toggleSimulation}
              onExportScreenshot={exportScreenshot}
              layoutIsFixed={tab === 'atlas'}
            />
          )}

          {/* Node detail panel — full-height right rail on desktop,
              half-height bottom sheet on mobile. Hidden when the mobile
              Explore overlay is active because Explore already renders
              the focused node as its main card; rendering both stacks two
              versions of the same node on screen. */}
          {!(isMobile && tab === 'explore') && (
            <NodeDetailPanel
              node={selectedRaw}
              onClose={clearSelection}
              relationships={selectedRelationships}
              workspaceChromeOffset
              onNavigateToNode={(nextNodeId) => {
                void focusNodeById(nextNodeId);
              }}
              mobileHalf={isMobile}
            />
          )}
        </CosmographProvider>
        </section>
      )}

      {/* BottomTabNav (Observatory ↔ Semativerse) removed on mobile —
          the alternate engine isn't usable at this viewport and the
          tab strip stole 64 px of canvas. */}
    </div>
  );
}

// === Inline subcomponents ===

type DesktopTab = Exclude<Tab, 'explore'>;

function TabStrip({
  value,
  onChange,
  labels,
  counts,
}: {
  value: Tab;
  onChange: (next: DesktopTab) => void;
  labels: Record<DesktopTab, string>;
  counts: { atlas: number; full: number; filter: number };
}) {
  const items: Array<{ id: DesktopTab; icon: import('react').ReactNode; count?: number }> = [
    { id: 'atlas', icon: <Sparkles className="h-3.5 w-3.5" />, count: counts.atlas },
    { id: 'full', icon: <Network className="h-3.5 w-3.5" />, count: counts.full },
    { id: 'path', icon: <Route className="h-3.5 w-3.5" /> },
    { id: 'filter', icon: <MapIcon className="h-3.5 w-3.5" />, count: counts.filter },
  ];

  return (
    <div className="flex items-center gap-1 rounded-full border border-stone-300 bg-[#fffdf9]/92 p-1 shadow-[0_8px_30px_rgba(72,52,36,0.10)] backdrop-blur-xl">
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
                ? 'bg-stone-900 text-[#fffaf1] shadow-[0_8px_22px_rgba(72,52,36,0.20)]'
                : 'text-stone-600 hover:bg-stone-100 hover:text-stone-950',
            ].join(' ')}
          >
            {item.icon}
            <span className="hidden sm:inline">{labels[item.id]}</span>
            {item.count !== undefined && item.count > 0 && (
              <span className={['hidden rounded-full px-1.5 py-0.5 text-[10px] font-medium sm:inline-block', active ? 'bg-white/15 text-stone-100' : 'bg-stone-100 text-stone-600'].join(' ')}>
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
      className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-stone-300 bg-[#fffdf9]/92 text-stone-600 shadow-[0_8px_24px_rgba(72,52,36,0.08)] transition-colors hover:border-orange-500 hover:text-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700"
    >
      {icon}
    </button>
  );
}

function AdvancedDrawer({
  onClose,
  simulationRunning,
  onToggleSimulation,
  onExportScreenshot,
  layoutIsFixed,
}: {
  onClose: () => void;
  simulationRunning: boolean;
  onToggleSimulation: () => void;
  onExportScreenshot: () => void;
  layoutIsFixed: boolean;
}) {
  const { t } = useTranslation();
  return (
    <div className="absolute right-3 top-24 z-30 w-[18rem] rounded-2xl border border-stone-300 bg-[#fffdf9]/95 p-4 text-[12px] text-stone-600 shadow-[0_24px_60px_rgba(72,52,36,0.16)] backdrop-blur-xl md:right-6 md:top-28">
      <div className="mb-2 flex items-center justify-between">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-stone-500">
          {t('cosmograph.advanced.title', 'Advanced')}
        </p>
        <button
          type="button"
          onClick={onClose}
          aria-label={t('common.close', 'Close')}
          className="inline-flex h-6 w-6 items-center justify-center rounded-full border border-stone-300 bg-white/70 text-stone-500 hover:border-orange-500 hover:text-orange-800"
        >
          <X className="h-3 w-3" />
        </button>
      </div>
      <p className="leading-5">
        {t(
          'cosmograph.advanced.body',
          'The guided Atlas shows a bounded semantic backbone. Pause its layout for close reading, or export the current frame. The complete relation set remains available in Full graph and each node dossier.',
        )}
      </p>
      <div className="mt-4 grid gap-2">
        {layoutIsFixed ? (
          <div className="flex min-h-11 items-center gap-2 rounded-xl border border-teal-200 bg-teal-50/70 px-3 font-semibold text-teal-900">
            <Focus className="h-4 w-4" />
            {t('cosmograph.advanced.fixedLayout', 'Deterministic constellation layout')}
          </div>
        ) : (
        <button
          type="button"
          onClick={onToggleSimulation}
          className="flex min-h-11 items-center gap-2 rounded-xl border border-stone-300 bg-white/70 px-3 text-left font-semibold text-stone-700 transition hover:border-orange-500 hover:text-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700"
        >
          {simulationRunning ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          {simulationRunning
            ? t('cosmograph.controls.pause', 'Pause layout')
            : t('cosmograph.controls.resume', 'Resume layout')}
        </button>
        )}
        <button
          type="button"
          onClick={onExportScreenshot}
          className="flex min-h-11 items-center gap-2 rounded-xl border border-stone-300 bg-white/70 px-3 text-left font-semibold text-stone-700 transition hover:border-orange-500 hover:text-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700"
        >
          <Camera className="h-4 w-4" />
          {t('cosmograph.controls.screenshot', 'Export screenshot')}
        </button>
      </div>
    </div>
  );
}
