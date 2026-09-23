import {
  AlertTriangle,
  ArrowRight,
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
import { formatCompact, formatFull } from '../../lib/formatCompact';
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
  buildAtlasSearchProjectionIndex,
  type AtlasConstellationKey,
  isAtlasFocusReady,
  pickAtlasLandingEdges,
  pickAtlasLandingNodeIds,
  pickAtlasNodeIds,
  pickAtlasSearchProjectionEdges,
  pickAtlasSearchProjectionNodeIds,
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
  atlasRendererRevision,
  atlasFilterKey,
  defaultAtlasTab,
  atlasFitZoom,
  atlasPositionBounds,
  atlasTabPersistsCamera,
  nearestAtlasIndices,
  resolveAtlasCameraRestore,
  semanticZoomConfig,
  semanticZoomTier,
  shouldAutoFitAtlasView,
  type AtlasTab,
  type AtlasZoomTier,
} from './atlasViewState';
import StableCosmographCanvas from './StableCosmographCanvas';
import {
  atlasLayoutFromPositions,
  cacheAtlasLayout,
  loadAtlasLayout,
  resolveAtlasPositions,
  serializeAtlasLayout,
  type AtlasLayoutRecord,
} from './atlasLayout';
import {
  enqueueCosmographPreparation,
  preparedCosmographContract,
} from './preparedCosmographContract';

import {
  Component,
  type ErrorInfo,
  type KeyboardEvent,
  type MutableRefObject,
  type ReactNode,
} from 'react';

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
    return <RendererStoppedCard message={this.state.message} />;
  }
}

function RendererStoppedCard({ message }: { message: string }) {
  const { t } = useTranslation();
  return (
    <div role="alert" className="absolute inset-0 flex items-center justify-center p-6">
      <div className="max-w-md rounded-2xl border border-stone-300 bg-[#fffdf9]/95 p-6 text-center text-stone-900 shadow-[0_30px_90px_rgba(72,52,36,0.18)] backdrop-blur-md">
        <p className="text-base font-semibold text-orange-800">
          {t('cosmograph.fallback.stopped', 'The Atlas renderer stopped')}
        </p>
        <p className="mt-2 text-sm text-stone-600">{message}</p>
        <button
          type="button"
          onClick={() => window.location.reload()}
          className="mt-4 inline-flex min-h-11 items-center justify-center rounded-full bg-stone-900 px-4 py-2 text-sm font-medium text-[#fffaf1] transition-colors hover:bg-orange-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700 focus-visible:ring-offset-2"
        >
          {t('cosmograph.fallback.reload', 'Reload')}
        </button>
      </div>
    </div>
  );
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
  const { t, i18n } = useTranslation();
  const reason = t(
    `cosmograph.fallback.reasons.${capability.reason ?? 'webgl2_unavailable'}`,
    'Hardware-accelerated WebGL 2 is unavailable or disabled.',
  );

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
              {t('cosmograph.fallback.eyebrow', 'Atlas compatibility guard')}
            </p>
            <h1 className="mt-2 font-display text-3xl leading-tight text-stone-950 sm:text-5xl">
              {t('cosmograph.fallback.title', 'The complete graph is safe. This renderer is not.')}
            </h1>
            <p className="mt-4 max-w-2xl font-reader text-lg leading-7 text-stone-600">
              {reason}{' '}
              {t(
                'cosmograph.fallback.body',
                'Atlas stopped before allocating its GPU surfaces, so the page stays responsive and no partial graph is shown. The same release, selection, filters, comparison and Evidence Thread remain available in the light research modes.',
              )}
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
              <BookOpen className="h-4 w-4" aria-hidden="true" /> {t('cosmograph.fallback.openScholar', 'Open Scholar')}
            </span>
            <span className="mt-1 block font-body text-xs leading-5 text-orange-50">{t('cosmograph.fallback.openScholarBody', 'Search, compare and inspect every node in an accessible table.')}</span>
          </button>
          <button
            type="button"
            onClick={onOpenChronos}
            className="min-h-20 border border-stone-300 bg-white/60 px-5 py-4 text-left text-stone-900 outline-none transition hover:border-teal-700 hover:bg-teal-50 focus-visible:ring-2 focus-visible:ring-teal-700 focus-visible:ring-offset-2 focus-visible:ring-offset-[#fffdf9]"
          >
            <span className="flex items-center gap-2 font-body text-sm font-bold">
              <Clock3 className="h-4 w-4" aria-hidden="true" /> {t('cosmograph.fallback.openChronos', 'Open Chronos')}
            </span>
            <span className="mt-1 block font-body text-xs leading-5 text-stone-600">{t('cosmograph.fallback.openChronosBody', 'Follow the same evidence across periods without a GPU renderer.')}</span>
          </button>
        </div>

        <details className="mt-7 border-t border-stone-200 pt-4 font-body text-xs text-stone-500">
          <summary className="min-h-11 cursor-pointer py-3 font-semibold text-stone-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700">
            {t('cosmograph.fallback.diagnostic', 'Graphics diagnostic')}
          </summary>
          <dl className="mt-2 grid gap-2 sm:grid-cols-[10rem_1fr]">
            <dt>{t('cosmograph.fallback.reason', 'Reason')}</dt>
            <dd>{capability.reason ?? t('cosmograph.fallback.unknown', 'unknown')}</dd>
            <dt>{t('cosmograph.fallback.renderer', 'Renderer')}</dt>
            <dd className="break-words">{capability.renderer || t('cosmograph.fallback.rendererHidden', 'not exposed by the browser')}</dd>
            <dt>{t('cosmograph.fallback.maxTexture', 'Max texture')}</dt>
            <dd>
              {capability.maxTextureSize === undefined
                ? t('cosmograph.fallback.unavailable', 'unavailable')
                : formatFull(capability.maxTextureSize, i18n.language)}
            </dd>
          </dl>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="mt-4 min-h-11 border border-stone-300 px-4 font-semibold text-stone-700 hover:border-orange-700 hover:text-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700"
          >
            {t('cosmograph.fallback.retry', 'Retry after enabling hardware acceleration')}
          </button>
        </details>
      </div>
    </section>
  );
}

type Tab = AtlasTab;

const COMPLETE_CONSTELLATION_HIGHLIGHT = 320;
const COMPLETE_CONSTELLATION_FRAME = 28;
const WORKBENCH_PANEL_ID = 'atlas-workbench-panel';
const TIER_FALLBACK: Readonly<Record<AtlasZoomTier, { name: string; body: string }>> = {
  overview: { name: 'Overview', body: 'Structure first: minor evidence is deliberately quiet.' },
  mid: { name: 'Intermediate', body: 'Intermediate nodes and local labels are now visible.' },
  close: { name: 'Close reading', body: 'Dense labels and small evidence loci are active.' },
};

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
  colorByTier: Record<AtlasZoomTier, Record<string, string>>;
  /** Every point carries a precomputed position; no simulation runs. */
  fixedLayout: boolean;
}

type AtlasSliceKind = 'atlas' | 'explore' | 'full' | 'filter';

function atlasSliceKind(tab: Tab): AtlasSliceKind {
  if (tab === 'path') return 'full';
  return tab;
}

interface BuildCosmoOptions {
  constellationLabels: Readonly<Record<AtlasConstellationKey, string>>;
  /** The curated landing projection: authored constellation geometry. */
  authored: boolean;
  /** Frozen positions for the complete graph and its filtered subsets. */
  positions?: ReadonlyMap<string, readonly [number, number]> | null;
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
    visualSize: constellationKey === 'core' ? 38 : meta.size,
    colorKey,
    constellation,
    constellationStrength: constellationKey === 'core' ? 1.5 : 1.25,
    x: position?.[0],
    y: position?.[1],
    layer: meta.layer,
  };
}

function colorKeyFor(meta: AtlasNodeMeta): string {
  const hierarchy = meta.size >= 11 ? 'hub' : meta.size >= 4.8 ? 'connector' : 'evidence';
  return `${meta.layer}:${meta.typeKey}:${hierarchy}`;
}

function colorWithAlpha(color: string, alpha: number): string {
  const match = /^#([\da-f]{2})([\da-f]{2})([\da-f]{2})$/i.exec(color);
  if (!match) return color;
  return `rgba(${Number.parseInt(match[1], 16)}, ${Number.parseInt(match[2], 16)}, ${Number.parseInt(match[3], 16)}, ${alpha})`;
}

function hierarchyAlpha(key: string, tier: AtlasZoomTier): number {
  if (key === 'atlas:core' || key.endsWith(':hub')) return 1;
  if (key.endsWith(':connector')) return tier === 'overview' ? 0.58 : tier === 'mid' ? 0.82 : 0.96;
  return tier === 'overview' ? 0.075 : tier === 'mid' ? 0.3 : 0.88;
}

function buildAtlasConstellationLayout(
  meta: ReadonlyArray<AtlasNodeMeta>,
): Map<string, readonly [number, number]> {
  const groups = new Map<AtlasConstellationKey, AtlasNodeMeta[]>();
  for (const node of meta) {
    const key = atlasConstellationKey(node);
    const group = groups.get(key) ?? [];
    group.push(node);
    groups.set(key, group);
  }

  const positions = new Map<string, readonly [number, number]>();
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

  }
  return positions;
}

async function buildCosmoData(
  meta: ReadonlyArray<AtlasNodeMeta>,
  edges: ReadonlyArray<AtlasEdgeMeta>,
  { constellationLabels, authored, positions }: BuildCosmoOptions,
): Promise<CosmoData> {
  const colorByTier: Record<AtlasZoomTier, Record<string, string>> = {
    overview: {},
    mid: {},
    close: {},
  };
  meta.forEach((node) => {
    const isCore = authored && atlasConstellationKey(node) === 'core';
    const key = isCore ? 'atlas:core' : colorKeyFor(node);
    const color = isCore ? ATLAS_THEME.hover : node.color;
    (['overview', 'mid', 'close'] as const).forEach((tier) => {
      colorByTier[tier][key] = colorWithAlpha(color, hierarchyAlpha(key, tier));
    });
  });

  const layoutPositions = authored
    ? buildAtlasConstellationLayout(meta)
    : positions ?? null;
  const fixedLayout = Boolean(layoutPositions)
    && meta.every((node) => layoutPositions?.has(node.id));
  const points = meta.map((node) => {
    const constellationKey = atlasConstellationKey(node);
    const colorKey = authored && constellationKey === 'core'
      ? 'atlas:core'
      : colorKeyFor(node);
    return compactNode(
      node,
      colorKey,
      constellationLabels[constellationKey],
      constellationKey,
      fixedLayout ? layoutPositions?.get(node.id) : undefined,
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

  const prepared = await enqueueCosmographPreparation(() =>
    prepareCosmographData(
      {
        points: {
          pointIdBy: 'id',
          pointLabelBy: 'label',
          pointClusterBy: 'constellation',
          pointClusterStrengthBy: 'constellationStrength',
          ...(fixedLayout
            ? {
                pointXBy: 'x',
                pointYBy: 'y',
              }
            : {}),
          pointSizeBy: 'visualSize',
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
    ),
  );

  if (!prepared?.points) {
    throw new Error('Cosmograph could not prepare the Atlas point table.');
  }
  if (links.length > 0 && !prepared.links) {
    throw new Error('Cosmograph could not prepare the Atlas link table.');
  }

  return {
    points: prepared.points,
    links: prepared.links,
    cosmographConfig: preparedCosmographContract(
      prepared.cosmographConfig,
      Boolean(prepared.links),
    ),
    colorByTier,
    fixedLayout,
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
    nodeDetailStates,
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
  const filtersKey = atlasFilterKey(filters);
  const stableFilters = useMemo<KgFilterState>(
    () => JSON.parse(filtersKey) as KgFilterState,
    [filtersKey],
  );
  const selectedNodeId = workspace.primarySelection;
  // `resolvedLanguage` stays on the English fallback until a lazy locale
  // bundle arrives; number formatting must follow the requested language.
  const locale = i18n.language;
  const nodesCompact = formatCompact(allMeta.length || Number.NaN, locale);
  const allMetaById = useMemo(
    () => new Map(allMeta.map((node) => [node.id, node])),
    [allMeta],
  );
  const atlasNodeRefs = useMemo(
    () => allMeta.map((node) => ({
      id: node.id,
      type: node.typeKey,
      importance: node.importance,
    })),
    [allMeta],
  );
  const atlasAnchorIds = useMemo(
    () => pickAtlasNodeIds(atlasNodeRefs),
    [atlasNodeRefs],
  );
  const atlasSearchIndex = useMemo(
    () => buildAtlasSearchProjectionIndex(atlasNodeRefs, allEdges),
    [allEdges, atlasNodeRefs],
  );
  const atlasLandingNodeIds = useMemo(
    () => pickAtlasLandingNodeIds(atlasNodeRefs, allEdges, 132),
    [allEdges, atlasNodeRefs],
  );
  const [searchProjectionTargetId, setSearchProjectionTargetId] = useState<string | null>(null);
  const searchProjection = useMemo(
    () => searchProjectionTargetId
      ? pickAtlasSearchProjectionNodeIds(
          searchProjectionTargetId,
          atlasNodeRefs,
          allEdges,
          atlasAnchorIds,
          28,
          atlasSearchIndex,
        )
      : null,
    [
      allEdges,
      atlasAnchorIds,
      atlasNodeRefs,
      atlasSearchIndex,
      searchProjectionTargetId,
    ],
  );
  const searchProjectionTarget = searchProjectionTargetId
    ? allMetaById.get(searchProjectionTargetId) ?? null
    : null;
  const searchProjectionAnchor = searchProjection?.anchorId
    ? allMetaById.get(searchProjection.anchorId) ?? null
    : null;
  const projectionSummary = searchProjection
    ? [
        t('cosmograph.atlas.searchProjection.loci', {
          count: searchProjection.nodeIds.size,
          defaultValue: '{{count, number}} connected loci',
        }),
        searchProjectionAnchor
          ? t('cosmograph.atlas.searchProjection.anchoredAt', {
              label: searchProjectionAnchor.label,
              defaultValue: 'anchored at {{label}}',
            })
          : t('cosmograph.atlas.searchProjection.neighbourhood', 'local evidence neighbourhood'),
      ].join(' · ')
    : '';

  // Default tab is *derived* from viewport, not stored on first render. The
  // useState initializer ran during prerender (no `window`), so it had no way
  // of knowing the visitor was on a phone — and the server-rendered value
  // would persist on the client even after hydration because nothing flipped
  // it back. We track only the user's *explicit* choice; the actual `tab`
  // value falls back to a viewport-aware default on every render.
  const [userTab, setUserTab] = useState<Tab | null>(null);
  const tab: Tab = userTab ?? defaultAtlasTab(isMobile);
  const sliceKind = atlasSliceKind(tab);
  const setTab = useCallback((next: Tab | ((current: Tab) => Tab)) => {
    setUserTab((prev) => {
      const current = prev ?? defaultAtlasTab(isMobile);
      return typeof next === 'function' ? (next as (c: Tab) => Tab)(current) : next;
    });
  }, [isMobile]);
  const [cosmo, setCosmo] = useState<CosmoData | null>(null);
  const [activeMeta, setActiveMeta] = useState<ReadonlyArray<AtlasNodeMeta>>([]);
  const [activeEdges, setActiveEdges] = useState<ReadonlyArray<AtlasEdgeMeta>>([]);
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
  const atlasLabelLocale = i18n.resolvedLanguage || i18n.language;
  // Locale bundles load lazily; recompute once the active one has arrived,
  // otherwise the canvas labels stay in the English fallback.
  const atlasLabelBundleReady = i18n.hasResourceBundle(atlasLabelLocale, 'translation');
  const atlasConstellationLabels = useMemo<Readonly<Record<AtlasConstellationKey, string>>>(() => {
    const fixedT = i18n.getFixedT(atlasLabelLocale);
    return {
      core: fixedT('cosmograph.atlas.constellations.core', 'The free-will question'),
      agency: fixedT('cosmograph.atlas.constellations.agency', 'Action and choice'),
      stoic: fixedT('cosmograph.atlas.constellations.stoic', 'Stoic fate'),
      epicurean: fixedT('cosmograph.atlas.constellations.epicurean', 'Epicurean alternatives'),
      peripatetic: fixedT('cosmograph.atlas.constellations.peripatetic', 'Peripatetic critique'),
      christian: fixedT('cosmograph.atlas.constellations.christian', 'Christian freedom'),
      late_antique: fixedT('cosmograph.atlas.constellations.lateAntique', 'Late antique synthesis'),
      reception: fixedT('cosmograph.atlas.constellations.reception', 'Modern interpretations'),
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [atlasLabelBundleReady, atlasLabelLocale, i18n]);

  const [graphReady, setGraphReady] = useState(false);
  const [graphicsCapability, setGraphicsCapability] = useState<
    AtlasGraphicsCapability | { status: 'checking' }
  >({ status: 'checking' });

  useEffect(() => {
    setGraphicsCapability(inspectAtlasGraphicsCapability());
  }, []);

  // `undefined` while loading, `null` when no frozen layout exists.
  const releaseId = workspace.releaseId;
  const [fullLayout, setFullLayout] = useState<AtlasLayoutRecord | null | undefined>(undefined);
  useEffect(() => {
    if (!releaseId) return;
    let cancelled = false;
    void loadAtlasLayout(releaseId).then((layout) => {
      if (!cancelled) setFullLayout(layout);
    });
    return () => {
      cancelled = true;
    };
  }, [releaseId]);
  const fullPositions = useMemo(
    () => fullLayout ? resolveAtlasPositions(fullLayout, allMeta, allEdges) : null,
    [allEdges, allMeta, fullLayout],
  );

  useEffect(() => {
    if (selectedNodeId) void ensureNodeDetail(selectedNodeId);
  }, [ensureNodeDetail, selectedNodeId]);

  // Semantic-zoom tier: derived from current camera zoom, debounced. Drives
  // *render* density only (top-label cap, link visibility range, hub label
  // opacity) — never the underlying point/link dataset. Crossing a tier
  // boundary therefore never restarts the simulation.
  const [zoomTier, setZoomTier] = useState<AtlasZoomTier>('overview');
  const tierName = t(`cosmograph.workbench.detail.${zoomTier}.name`, TIER_FALLBACK[zoomTier].name);
  const zoomTierRef = useRef<AtlasZoomTier>('overview');
  const zoomBaselineRef = useRef<number | null>(null);
  const lodConfigIntentRef = useRef(0);
  const zoomDebounceRef = useRef<number | null>(null);
  const cameraDiveTimeoutRef = useRef<number | null>(null);
  const pendingFocusIdRef = useRef<string | null>(null);
  const pendingFocusAttemptRef = useRef<string | null>(null);
  const focusIntentRef = useRef(0);
  const canvasHostRef = useRef<HTMLDivElement | null>(null);
  // A permalink camera belongs to the first complete-graph frame only; any
  // later slice has already been framed by the visitor or the auto-fit.
  const pendingCameraRestoreRef = useRef(workspace.cameraByMode.atlas);
  const cameraRestoredRef = useRef(false);
  const persistedCameraRef = useRef(workspace.cameraByMode.atlas);
  useEffect(() => {
    persistedCameraRef.current = workspace.cameraByMode.atlas;
  }, [workspace.cameraByMode.atlas]);
  const canvasSize = useCallback((): [number, number] | null => {
    const host = canvasHostRef.current;
    if (!host || host.clientWidth === 0 || host.clientHeight === 0) return null;
    return [host.clientWidth, host.clientHeight];
  }, []);
  const handleSemanticZoom = useCallback((...args: unknown[]) => {
    let next = NaN;
    for (const arg of args) {
      if (typeof arg === 'number' && Number.isFinite(arg)) { next = arg; break; }
      if (arg && typeof arg === 'object' && 'k' in arg && typeof (arg as { k: unknown }).k === 'number') {
        next = (arg as { k: number }).k;
        break;
      }
      if (arg && typeof arg === 'object' && 'transform' in arg) {
        const tf = (arg as { transform?: { k?: number } }).transform;
        if (tf && typeof tf.k === 'number') {
          next = tf.k;
          break;
        }
      }
    }
    if (!Number.isFinite(next)) return;
    if (zoomDebounceRef.current !== null) window.clearTimeout(zoomDebounceRef.current);
    zoomDebounceRef.current = window.setTimeout(() => {
      if (zoomBaselineRef.current === null || next < zoomBaselineRef.current) {
        zoomBaselineRef.current = next;
      }
      const tier = semanticZoomTier(next, zoomBaselineRef.current);
      if (zoomTierRef.current !== tier) {
        zoomTierRef.current = tier;
        setZoomTier(tier);
        const graph = graphRef.current;
        const intent = ++lodConfigIntentRef.current;
        // Cosmograph's setConfig replaces rather than merges its public
        // config. Preserve the committed point/link tables and patch only the
        // cheap visual values, otherwise a zoom-tier change empties/rebuilds
        // the renderer and loses the camera.
        void graph?.getConfig().then((current) => {
          if (graphRef.current !== graph || lodConfigIntentRef.current !== intent) return;
          graph.setConfig({
            ...current,
            ...semanticZoomConfig(tab, tier, isMobile),
            pointColorByMap: cosmo?.colorByTier[tier] ?? current.pointColorByMap,
            showClusterLabels: !selectedNodeId && tab === 'atlas' && tier === 'overview',
            showTopLabels: true,
          });
        });
      }
      if (!atlasTabPersistsCamera(tab)) {
        if (persistedCameraRef.current) setCamera('atlas', null);
        return;
      }
      const size = canvasSize();
      const centre = size
        ? graphRef.current?.screenToSpacePosition([size[0] / 2, size[1] / 2])
        : undefined;
      if (centre) setCamera('atlas', { x: centre[0], y: centre[1], zoom: next });
    }, 180);
  }, [canvasSize, cosmo, isMobile, selectedNodeId, setCamera, tab]);

  useEffect(() => {
    zoomBaselineRef.current = null;
    zoomTierRef.current = 'overview';
    setZoomTier('overview');
  }, [cosmo, tab]);

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

  useEffect(() => {
    // Dataset/mode changes invalidate every delayed camera instruction that
    // captured indices from the previous slice. The next pending focus will
    // acquire a fresh intent against the committed dataset.
    focusIntentRef.current += 1;
    if (cameraDiveTimeoutRef.current !== null) {
      window.clearTimeout(cameraDiveTimeoutRef.current);
      cameraDiveTimeoutRef.current = null;
    }
    setConstellationFocus(null);
  }, [searchProjectionTargetId, setConstellationFocus, tab]);

  // --- Derive active slice (atlas / full / filtered) ---
  //
  // Each slice depends only on its own inputs, so switching between Full graph
  // and Path, or editing filters while another tab is open, never re-prepares
  // the GPU tables. Zoom is purely a camera transform on every device.
  const sliceFilters = sliceKind === 'filter' ? stableFilters : null;
  const sliceProjection = sliceKind === 'atlas' || sliceKind === 'explore'
    ? searchProjection
    : null;
  const slicePositions = sliceKind === 'full' || sliceKind === 'filter'
    ? fullPositions
    : null;
  const sliceLayoutPending = (sliceKind === 'full' || sliceKind === 'filter')
    && fullLayout === undefined;
  useEffect(() => {
    if (graphicsCapability.status !== 'supported') {
      setCosmo(null);
      setGraphReady(false);
      return;
    }
    if (allMeta.length === 0 || sliceLayoutPending) return;
    let cancelled = false;
    const { renderer, maxTextureSize } = graphicsCapability;
    setGraphReady(false);

    async function computeActive() {
      let metaSlice: ReadonlyArray<AtlasNodeMeta> = allMeta;
      let edgeSlice: ReadonlyArray<AtlasEdgeMeta> = allEdges;

      if (sliceKind === 'atlas' || sliceKind === 'explore') {
        const ids = sliceProjection?.nodeIds ?? atlasLandingNodeIds;
        metaSlice = allMeta.filter((m) => ids.has(m.id));
        edgeSlice = sliceProjection
          ? pickAtlasSearchProjectionEdges(sliceProjection, allEdges)
          : pickAtlasLandingEdges(new Set(metaSlice.map((m) => m.id)), allEdges, atlasAnchorIds);
      } else if (sliceKind === 'filter' && sliceFilters) {
        metaSlice = filterMeta(allMeta, sliceFilters);
        if (metaSlice !== allMeta) {
          const idSet = new Set(metaSlice.map((m) => m.id));
          edgeSlice = allEdges.filter((e) => idSet.has(e.source) && idSet.has(e.target));
        }
      }

      let built: CosmoData;
      try {
        built = await buildCosmoData(metaSlice, edgeSlice, {
          constellationLabels: atlasConstellationLabels,
          authored: sliceKind === 'atlas',
          positions: slicePositions,
        });
      } catch (error) {
        if (cancelled) return;
        console.error('Cosmograph data preparation failed:', error);
        setCosmo(null);
        setGraphReady(false);
        setGraphicsCapability({
          status: 'unsupported',
          reason: 'initialization_error',
          renderer,
          maxTextureSize,
        });
        return;
      }
      if (cancelled) return;
      setActiveMeta(metaSlice);
      setActiveEdges(edgeSlice);
      setCosmo(built);
    }

    void computeActive();
    return () => {
      cancelled = true;
    };
  }, [
    allMeta,
    allEdges,
    atlasAnchorIds,
    atlasConstellationLabels,
    atlasLandingNodeIds,
    graphicsCapability,
    sliceFilters,
    sliceKind,
    sliceLayoutPending,
    slicePositions,
    sliceProjection,
  ]);

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
  const selectedDetailState = selectedNodeId
    ? nodeDetailStates.get(selectedNodeId)
    : undefined;

  const focusNodeById = useCallback(
    async (id: string) => {
      const intent = ++focusIntentRef.current;
      if (cameraDiveTimeoutRef.current !== null) {
        window.clearTimeout(cameraDiveTimeoutRef.current);
        cameraDiveTimeoutRef.current = null;
      }
      setConstellationFocus(null);
      const target = allMetaById.get(id);
      if (!target) return false;
      if (!graphRef.current || !activeMetaById.has(id)) {
        pendingFocusIdRef.current = id;
        pendingFocusAttemptRef.current = null;
        lastFocusedNodeRef.current = null;
        if (tab === 'atlas' || tab === 'explore') {
          setSearchProjectionTargetId(id);
          setTab('atlas');
        } else if (tab === 'filter') {
          setTab('full');
        }
        startTransition(() => selectPrimary(id));
        return false;
      }
      startTransition(() => selectPrimary(id));
      const neighbourIds = (relationships.get(id) ?? [])
        .map((relationship) => relationship.id)
        .filter((candidate) => activeMetaById.has(candidate))
        .sort((left, right) =>
          (activeMetaById.get(right)?.importance ?? 0)
          - (activeMetaById.get(left)?.importance ?? 0)
          || left.localeCompare(right))
        .slice(0, 12);
      const focusIds = [id, ...neighbourIds];
      const activeIds = new Set(activeMetaById.keys());

      // A dataset revision reaches Cosmograph just after React commits the new
      // active slice. Wait up to one second for the renderer index, but
      // never let an obsolete search intent seize the camera afterward.
      for (let attempt = 0; attempt < 60; attempt += 1) {
        if (focusIntentRef.current !== intent || !graphRef.current) return false;
        const indices = await graphRef.current.getPointIndicesByIds(focusIds);
        const pointIndex = indices?.[0];
        if (isAtlasFocusReady(id, activeIds, pointIndex)) {
          const clean = (indices ?? []).filter(
            (index): index is number => typeof index === 'number',
          );
          // Commit ownership only after both the semantic ID and renderer
          // index exist in the same active projection.
          lastFocusedNodeRef.current = id;
          graphRef.current.selectPoints(clean, false);
          graphRef.current.setFocusedPoint(pointIndex);
          if (clean.length > 1) {
            graphRef.current.fitViewByIndices(clean, 600, 0.25);
          } else {
            graphRef.current.zoomToPoint(pointIndex, 500, 3.4, true);
          }
          return true;
        }
        await new Promise<void>((resolve) => window.requestAnimationFrame(() => resolve()));
      }
      return false;
    },
    [
      activeMetaById,
      allMetaById,
      relationships,
      selectPrimary,
      setConstellationFocus,
      setTab,
      tab,
    ],
  );

  const openSearchProjection = useCallback((node: AtlasNodeMeta) => {
    focusIntentRef.current += 1;
    pendingFocusIdRef.current = node.id;
    pendingFocusAttemptRef.current = null;
    lastFocusedNodeRef.current = null;
    if (cameraDiveTimeoutRef.current !== null) {
      window.clearTimeout(cameraDiveTimeoutRef.current);
      cameraDiveTimeoutRef.current = null;
    }
    setConstellationFocus(null);
    setSearchProjectionTargetId(node.id);
    startTransition(() => selectPrimary(node.id));
  }, [selectPrimary, setConstellationFocus]);

  const returnToAtlasOverview = useCallback(() => {
    focusIntentRef.current += 1;
    pendingFocusIdRef.current = null;
    pendingFocusAttemptRef.current = null;
    lastFocusedNodeRef.current = null;
    graphRef.current?.unselectAllPoints();
    graphRef.current?.setFocusedPoint(undefined);
    setConstellationFocus(null);
    setSearchProjectionTargetId(null);
    selectPrimary(null);
    setTab('atlas');
  }, [selectPrimary, setConstellationFocus, setTab]);

  const openSearchResultInFullGraph = useCallback(() => {
    if (!searchProjectionTargetId) return;
    focusIntentRef.current += 1;
    pendingFocusIdRef.current = searchProjectionTargetId;
    pendingFocusAttemptRef.current = null;
    lastFocusedNodeRef.current = null;
    setConstellationFocus(null);
    setTab('full');
  }, [searchProjectionTargetId, setConstellationFocus, setTab]);

  const reopenSearchProjection = useCallback(() => {
    if (!searchProjectionTargetId) return;
    focusIntentRef.current += 1;
    pendingFocusIdRef.current = searchProjectionTargetId;
    pendingFocusAttemptRef.current = null;
    lastFocusedNodeRef.current = null;
    setConstellationFocus(null);
    setTab('atlas');
  }, [searchProjectionTargetId, setConstellationFocus, setTab]);

  const focusConstellation = useCallback((key: AtlasConstellationKey) => {
    if (!graphRef.current) return;
    focusIntentRef.current += 1;
    pendingFocusIdRef.current = null;
    pendingFocusAttemptRef.current = null;
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
    const authored = tab === 'atlas';
    // The complete graph holds thousands of members per constellation;
    // selecting a bounded, importance-ranked share keeps the greyout legible.
    const highlighted = authored ? clean : clean.slice(0, COMPLETE_CONSTELLATION_HIGHLIGHT);
    graphRef.current.setFocusedPoint(clean[0]);
    graphRef.current.selectPoints(highlighted, false);
    cameraDiveTimeoutRef.current = window.setTimeout(() => {
      const graph = graphRef.current;
      if (authored) {
        // A fixed department-scale zoom keeps the hub at the visual centre and
        // leaves enough vertical room for its authored branches above the
        // entry rail. Fitting sparse constellations over-zooms them; fitting
        // rich ones suppresses their labels through collision avoidance.
        graph?.zoomToPoint(clean[0], 760, 3.3, false);
      } else {
        // Absolute zoom is meaningless at complete-graph scale: frame the
        // hub with its nearest highlighted members instead.
        const positions = graph?.getPointPositions();
        const framed = positions
          ? nearestAtlasIndices(positions, clean[0], highlighted, COMPLETE_CONSTELLATION_FRAME)
          : [clean[0]];
        graph?.fitViewByIndices(framed, 700, 0.2);
      }
      cameraDiveTimeoutRef.current = window.setTimeout(() => {
        cameraDiveTimeoutRef.current = null;
      }, 820);
    }, 700);
  }, [activeMeta, selectPrimary, setConstellationFocus, tab]);

  useEffect(() => {
    const pendingId = pendingFocusIdRef.current;
    if (
      !graphReady
      || !pendingId
      || pendingFocusAttemptRef.current === pendingId
      || !activeMetaById.has(pendingId)
    ) return;
    pendingFocusAttemptRef.current = pendingId;
    void focusNodeById(pendingId).then(() => {
      if (pendingFocusIdRef.current === pendingId) {
        // Fail open after the bounded renderer handoff: the dossier remains
        // selected, but controls/background clicks must never stay trapped by
        // an unresolved camera request.
        pendingFocusIdRef.current = null;
      }
    }).finally(() => {
      if (pendingFocusAttemptRef.current === pendingId) {
        pendingFocusAttemptRef.current = null;
      }
    });
  }, [activeMetaById, cosmo, focusNodeById, graphReady]);

  useEffect(() => {
    if (
      graphReady &&
      selectedNodeId &&
      pendingFocusIdRef.current !== selectedNodeId &&
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
    const padding = isMobile ? 0.24 : tab === 'atlas' ? 0.16 : 0.08;
    const handle = window.setTimeout(() => {
      const restored = cameraRestoredRef.current;
      cameraRestoredRef.current = false;
      if (!shouldAutoFitAtlasView({
        cameraTransitionActive: cameraDiveTimeoutRef.current !== null,
        focusedNodeId: lastFocusedNodeRef.current,
        focusedConstellation: focusedConstellationRef.current,
        cameraRestored: restored,
      })) return;
      graphRef.current?.fitView(520, padding);
    }, 520);
    return () => window.clearTimeout(handle);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, filters, graphReady, searchProjectionTargetId]);

  // Permalink cameras store the space coordinate under the canvas centre, so
  // they survive viewport size changes. The auto-fit timer above reads
  // `cameraRestoredRef` 520 ms later and yields to the restored frame.
  useEffect(() => {
    if (!graphReady || !graphRef.current) return;
    const pending = pendingCameraRestoreRef.current;
    if (!pending) return;
    pendingCameraRestoreRef.current = null;
    if (!atlasTabPersistsCamera(tab)) return;
    const bounds = atlasPositionBounds(graphRef.current.getPointPositions());
    const camera = resolveAtlasCameraRestore(pending, bounds);
    if (!camera || !bounds) {
      // Legacy translate or foreign release. The init fit was disabled for
      // the pending restore, so frame the map now instead of flashing it.
      graphRef.current.fitView(0, 0.08);
      return;
    }
    cameraRestoredRef.current = true;
    const size = canvasSize();
    if (size) zoomBaselineRef.current = atlasFitZoom(bounds, size, 0.08);
    graphRef.current.setZoomTransformByPointPositions(
      new Float32Array([camera.x, camera.y]),
      0,
      camera.zoom,
    );
    // Only the first ready frame may consume the permalink.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [graphReady]);


  function clearSelection() {
    // Cosmograph can emit a synthetic background click when a programmatic
    // fit begins under the pointer that activated an overlaid entry chip.
    // Ignore that one transition-frame reset; deliberate canvas clicks work
    // again as soon as the branch-selection handoff completes.
    if (
      cameraDiveTimeoutRef.current !== null
      || pendingFocusIdRef.current !== null
      || pendingFocusAttemptRef.current !== null
    ) return;
    focusIntentRef.current += 1;
    lastFocusedNodeRef.current = null;
    graphRef.current?.unselectAllPoints();
    graphRef.current?.setFocusedPoint(undefined);
    selectPrimary(null);
    setConstellationFocus(null);
  }

  function fitView() {
    focusIntentRef.current += 1;
    pendingFocusIdRef.current = null;
    pendingFocusAttemptRef.current = null;
    if (cameraDiveTimeoutRef.current !== null) {
      window.clearTimeout(cameraDiveTimeoutRef.current);
      cameraDiveTimeoutRef.current = null;
    }
    lastFocusedNodeRef.current = null;
    setConstellationFocus(null);
    graphRef.current?.fitView(550, tab === 'atlas' ? 0.14 : 0.08);
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
    // Simulation completion is not user intent. Never seize the camera here.
    // A live run of the complete graph only happens when no frozen layout
    // matched this release; keep its end state so the next visit is instant.
    if (sliceKind !== 'full' || !cosmo || cosmo.fixedLayout || !releaseId) return;
    const flat = graphRef.current?.getPointPositions();
    if (!flat || activeMeta.length !== allMeta.length) return;
    const record = atlasLayoutFromPositions(releaseId, activeMeta, flat);
    if (!record) return;
    void cacheAtlasLayout(record);
    if (new URLSearchParams(window.location.search).has('atlas_layout_export')) {
      // Read by scripts/export-atlas-layout.sh to refresh the bundled layout.
      (window as Window & { __eleutheriaAtlasLayout?: string }).__eleutheriaAtlasLayout =
        JSON.stringify(serializeAtlasLayout(record));
    }
  }

  function exportScreenshot() {
    graphRef.current?.captureScreenshot('eleutheria-knowledge-graph', 2);
  }

  // --- Path highlighting on the canvas (greyout + ring) ---
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
        // A pending permalink camera owns the first frame of the complete
        // graph; the renderer's own init fit would override it.
        fitViewOnInit: !(pendingCameraRestoreRef.current && atlasTabPersistsCamera(tab)),
        fitViewDelay: 360,
        fitViewDuration: 500,
        fitViewPadding: tab === 'atlas' ? 0.2 : 0.08,
        randomSeed: 'eleutheria-atlas-v3',
        spaceSize: isMobile
          ? tab === 'atlas'
            ? 3600
            : 7200
          : tab === 'atlas'
            ? 4200
            : 8000,
        pointColorBy: 'colorKey',
        pointColorByMap: cosmo.colorByTier[zoomTier],
        pointSizeBy: 'visualSize',
        pointSizeByFn: (value: unknown) => {
          const numeric = typeof value === 'number' ? value : Number(value);
          return Number.isFinite(numeric) ? numeric : 2.4;
        },
        pointSizeRange: [2.4, 38],
        // `showTopLabels` is ignored by Cosmograph when the master label gate
        // is false. Keep dynamic sampling off, but render a strictly bounded
        // semantic label budget so the landing Atlas is a map, not unlabeled
        // decorative particles.
        showLabels: true,
        showDynamicLabels: zoomTier !== 'overview',
        showTopLabels: tab !== 'atlas' || Boolean(selectedNodeId),
        // Semantic-zoom label budgets are injected above. The authored
        // landing projection remains fixed while the complete graph reveals
        // labels relative to its own fitted camera scale.
        showFocusedPointLabel: true,
        // Constellation names describe the authored landing geometry only;
        // the complete graph is laid out by topology, so its hubs label it.
        showClusterLabels: !selectedNodeId && tab === 'atlas',
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
        enableSimulation: !isMobile && !cosmo.fixedLayout,
        simulationDecay: isMobile ? 0 : tab === 'atlas' ? 0 : 6800,
        simulationGravity: isMobile
          ? 0
          : tab === 'atlas'
            ? 0.12
            : 0.012,
        simulationCenter: isMobile ? 0 : tab === 'atlas' ? 0.01 : 0.003,
        simulationRepulsion: isMobile
          ? 0
          : tab === 'atlas'
            ? 3.2
            : 9.2,
        simulationRepulsionTheta: 1.08,
        simulationLinkSpring: isMobile ? 0 : tab === 'atlas' ? 0.74 : 0.16,
        simulationLinkDistance: isMobile
          ? 0
          : tab === 'atlas'
            ? 72
            : 68,
        simulationFriction: 0.9,
        simulationImpulse: 0,
      }
    : undefined;

  const rendererRevision = useMemo(
    () => atlasRendererRevision(cosmo, isMobile),
    [cosmo, isMobile],
  );
  // --- Highlight path: when path computed, isolate via Cosmograph point filter ---
  useEffect(() => {
    if (!graphReady || !graphRef.current) return;
    const intent = ++focusIntentRef.current;
    let cancelled = false;
    if (!pathResult) {
      graphRef.current.unselectAllPoints();
      return;
    }
    void (async () => {
      const indices = await graphRef.current?.getPointIndicesByIds([...pathResult.ids]);
      if (cancelled || focusIntentRef.current !== intent) return;
      const clean = (indices ?? []).filter((i): i is number => typeof i === 'number');
      if (clean.length > 0) {
        graphRef.current?.selectPoints(clean, false);
        graphRef.current?.fitViewByIndices(clean, 600, 0.18);
      }
    })();
    return () => {
      cancelled = true;
      if (focusIntentRef.current === intent) focusIntentRef.current += 1;
    };
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
          <div ref={canvasHostRef} className="absolute inset-0 md:left-[23.5rem]">
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
              onMount: () => setGraphReady(false),
              onGraphRebuilt: (stats) => {
                if (
                  stats.pointsCount === activeMeta.length
                  && stats.linksCount === activeEdges.length
                ) {
                  setGraphReady(true);
                  return;
                }
                setGraphicsCapability({
                  status: 'unsupported',
                  reason: 'initialization_error',
                  renderer: graphicsCapability.renderer,
                  maxTextureSize: graphicsCapability.maxTextureSize,
                });
              },
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
          </div>

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
                if (next === 'full' && searchProjectionTargetId) {
                  openSearchResultInFullGraph();
                } else if (next === 'atlas' && searchProjectionTargetId) {
                  reopenSearchProjection();
                } else {
                  setTab(next);
                }
                if (next !== 'path') {
                  setPathResult(null);
                }
              }}
              filters={filters}
              onFiltersChange={setFilters}
              onPickNode={(node) => {
                if (tab === 'atlas') {
                  openSearchProjection(node);
                } else {
                  void focusNodeById(node.id);
                }
              }}
              onOpenPathFinder={() => {
                setTab('path');
              }}
            />
          )}

          {isMobile && tab === 'atlas' && searchProjectionTarget && searchProjection && (
            <div
              role="status"
              aria-live="polite"
              className="pointer-events-auto absolute inset-x-3 top-[4.75rem] z-30 border-l-2 border-orange-700 bg-[#fffdf9]/96 px-3 py-2 text-stone-800 shadow-[0_12px_34px_rgba(72,52,36,0.13)] backdrop-blur-xl md:hidden"
            >
              <p className="truncate font-body text-xs font-semibold">
                <span className="text-stone-500">{t('cosmograph.tabs.atlas', 'Atlas')}</span>
                <span aria-hidden className="mx-1.5 text-stone-400">›</span>
                {searchProjectionTarget.label}
              </p>
              <p className="mt-0.5 truncate font-body text-[11px] text-stone-500">
                {projectionSummary}
              </p>
              <div className="mt-2 flex gap-2">
                <button
                  type="button"
                  onClick={returnToAtlasOverview}
                  className="min-h-11 flex-1 border border-stone-300 px-2 text-xs font-semibold text-stone-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700"
                >
                  {t('cosmograph.atlas.searchProjection.back', 'Return to Atlas')}
                </button>
                <button
                  type="button"
                  onClick={openSearchResultInFullGraph}
                  className="min-h-11 flex-1 border border-stone-900 bg-stone-900 px-2 text-xs font-semibold text-[#fffaf1] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700 focus-visible:ring-offset-2"
                >
                  {t('cosmograph.atlas.searchProjection.full', 'Open full graph')}
                </button>
              </div>
            </div>
          )}

          {/* === Mobile-only Explore <-> Map toggle (top-right) === */}
          {isMobile && (
            <button
              type="button"
              // Mobile Map = the curated Atlas (~130 nodes). The full 23k
              // graph at this viewport collapses into a hairball; Atlas
              // shows the load-bearing thinkers, schools and concepts so
              // the canvas is actually readable.
              onClick={() => {
                if (tab === 'explore' && searchProjectionTargetId) {
                  reopenSearchProjection();
                } else {
                  setTab(tab === 'explore' ? 'atlas' : 'explore');
                }
              }}
              aria-label={
                tab === 'explore'
                  ? (t('cosmograph.explore.openMap', 'Open the map view') as string)
                  : (t('cosmograph.explore.openExplore', 'Open the explore view') as string)
              }
              className={[
                'absolute right-[calc(0.75rem+env(safe-area-inset-right))] z-40 inline-flex min-h-11 items-center gap-1.5 rounded-full px-3 py-1.5 text-[12px] font-medium shadow-[0_8px_24px_-12px_rgba(15,23,42,0.45)] backdrop-blur-md transition-[top,background-color,color,border-color] md:hidden',
                searchProjectionTarget && tab === 'atlas'
                  ? 'top-[calc(11rem+env(safe-area-inset-top))]'
                  : 'top-[calc(4.75rem+env(safe-area-inset-top))]',
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

          {/* Desktop workbench: one stable place for search, projection and
              tools. The graph remains the canvas, not a backdrop behind a
              cloud of unrelated floating controls. */}
          <aside className="pointer-events-auto absolute bottom-4 left-4 top-[5.25rem] z-30 hidden w-[22rem] flex-col overflow-visible border border-stone-300 bg-[#fffdf9]/96 shadow-[0_24px_70px_rgba(72,52,36,0.16)] backdrop-blur-xl md:flex">
            <header className="border-b border-stone-300 px-4 pb-4 pt-4">
              <div className="flex items-start gap-3">
                <button
                  type="button"
                  onClick={() => navigate('/')}
                  className="inline-flex h-11 w-11 shrink-0 items-center justify-center border border-stone-300 text-stone-600 transition hover:border-orange-700 hover:text-orange-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700"
                  aria-label={t('cosmograph.back', 'Back')}
                >
                  <ChevronLeft className="h-4 w-4" aria-hidden="true" />
                </button>
                <div className="min-w-0">
                  <p className="font-body text-[9px] font-bold uppercase tracking-[0.22em] text-orange-800">{t('cosmograph.atlas.eyebrow', 'Atlas of the free-will debate')}</p>
                  <h1 className="mt-1 font-display text-[1.75rem] leading-none text-stone-950">{t('cosmograph.atlas.title', 'Follow the evidence.')}</h1>
                </div>
              </div>
              <div className="mt-4">
                <KgSearchBar
                  size="sm"
                  placeholder={t('cosmograph.searchPlaceholder', 'Concept, thinker, work, passage…')}
                  nodes={allMeta}
                  onPick={(node) => tab === 'atlas' ? openSearchProjection(node) : void focusNodeById(node.id)}
                  ariaLabel={t('cosmograph.searchAria', 'Search the knowledge graph')}
                  emptyLabel={t('cosmograph.searchEmpty', 'No match. Try a Greek or Latin term, a surname, or a work title.')}
                  resultsLabel={t('cosmograph.searchResults', 'Search results')}
                />
              </div>
            </header>

            <div className="border-b border-stone-300 p-2">
              <TabStrip
                value={tab}
                onChange={(next) => {
                  if (next === 'full' && searchProjectionTargetId) openSearchResultInFullGraph();
                  else if (next === 'atlas' && searchProjectionTargetId) reopenSearchProjection();
                  else setTab(next);
                  if (next !== 'path') setPathResult(null);
                }}
                ariaLabel={t('cosmograph.workbench.tablist', 'Atlas views')}
                panelId={WORKBENCH_PANEL_ID}
                labels={{
                  atlas: t('cosmograph.tabs.atlas', 'Atlas'),
                  full: t('cosmograph.tabs.full', 'Full graph'),
                  path: t('cosmograph.tabs.path', 'Path'),
                  filter: t('cosmograph.tabs.filter', 'Filter'),
                }}
                countLabel={(label, count) => t('cosmograph.workbench.tabCount', {
                  label,
                  count,
                  defaultValue: '{{label}}, {{count, number}} nodes',
                })}
                counts={{
                  atlas: tab === 'atlas' ? activeMeta.length : 0,
                  full: allMeta.length,
                  filter: tab === 'filter' ? activeMeta.length : 0,
                }}
              />
            </div>

            <div
              id={WORKBENCH_PANEL_ID}
              role="tabpanel"
              aria-labelledby={`${WORKBENCH_PANEL_ID}-tab-${tab === 'explore' ? 'atlas' : tab}`}
              className="min-h-0 flex-1 overflow-y-auto px-4 py-4 font-body"
            >
              {tab === 'atlas' && searchProjectionTarget && searchProjection ? (
                <section aria-live="polite">
                  <p className="text-[9px] font-bold uppercase tracking-[0.2em] text-orange-800">{t('cosmograph.atlas.searchProjection.eyebrow', 'Local evidence field')}</p>
                  <h2 className="mt-2 font-display text-2xl leading-tight text-stone-950">{searchProjectionTarget.label}</h2>
                  <p className="mt-2 text-xs leading-5 text-stone-600">{projectionSummary}</p>
                  <div className="mt-5 grid gap-2">
                    <button type="button" onClick={returnToAtlasOverview} className="min-h-11 border border-stone-300 px-3 text-left text-xs font-semibold text-stone-700 hover:border-orange-700 hover:text-orange-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700">
                      <span aria-hidden="true">← </span>{t('cosmograph.atlas.searchProjection.back', 'Return to Atlas')}
                    </button>
                    <button type="button" onClick={openSearchResultInFullGraph} className="min-h-11 bg-stone-900 px-3 text-left text-xs font-semibold text-[#fffaf1] hover:bg-orange-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700 focus-visible:ring-offset-2">
                      {t('cosmograph.atlas.searchProjection.full', 'Open in the complete graph')}<span aria-hidden="true"> →</span>
                    </button>
                  </div>
                </section>
              ) : tab === 'atlas' ? (
                <ConstellationEntryList
                  navRef={entryNavigationRef}
                  title={t('cosmograph.atlas.startTitle', 'Start with a question')}
                  body={t('cosmograph.atlas.startBody', 'Enter through a major controversy, then zoom to reveal its witnesses and textual loci.')}
                  entries={atlasEntryPoints}
                  activeKey={focusedConstellationRef.current}
                  labelFor={(key) => t(`cosmograph.atlas.entryPoints.${key}`, key)}
                  onPick={focusConstellation}
                />
              ) : tab === 'full' ? (
                <div className="grid gap-6">
                  <section>
                    <p className="text-[9px] font-bold uppercase tracking-[0.2em] text-stone-500">{t('cosmograph.workbench.full.eyebrow', 'Complete release')}</p>
                    <h2 className="mt-2 font-display text-2xl leading-tight text-stone-950">
                      {t('cosmograph.workbench.full.title', {
                        nodes: nodesCompact,
                        defaultValue: '{{nodes}} nodes, one frozen map.',
                      })}
                    </h2>
                    <p className="mt-2 font-reader text-[0.95rem] leading-6 text-stone-600">
                      {t('cosmograph.workbench.full.body', 'At overview only structural hubs and major labels lead. Zoom to reveal minor loci; click any node to frame it with its neighbours.')}
                    </p>
                  </section>
                  <ConstellationEntryList
                    navRef={entryNavigationRef}
                    title={t('cosmograph.atlas.startTitle', 'Start with a question')}
                    body={t('cosmograph.atlas.startBodyFull', 'Each question flies to its hub in the complete graph and highlights the loci around it.')}
                    entries={atlasEntryPoints}
                    activeKey={focusedConstellationRef.current}
                    labelFor={(key) => t(`cosmograph.atlas.entryPoints.${key}`, key)}
                    onPick={focusConstellation}
                    compact
                  />
                  <LayoutGrammar
                    title={t('cosmograph.workbench.grammar.title', 'How to read the map')}
                    items={[
                      {
                        glyph: 'work',
                        name: t('cosmograph.workbench.grammar.work.name', 'Works'),
                        body: t('cosmograph.workbench.grammar.work.body', 'Each work is a disc of its passages, set in canonical order.'),
                      },
                      {
                        glyph: 'argument',
                        name: t('cosmograph.workbench.grammar.argument.name', 'Arguments'),
                        body: t('cosmograph.workbench.grammar.argument.body', 'Arguments cluster around the publication that states them.'),
                      },
                      {
                        glyph: 'author',
                        name: t('cosmograph.workbench.grammar.author.name', 'Authors'),
                        body: t('cosmograph.workbench.grammar.author.body', 'An author sits at the centre of their main work.'),
                      },
                    ]}
                  />
                  <div aria-live="polite" className="border-t border-stone-300 pt-3 text-xs leading-5 text-stone-600">
                    <p className="flex items-baseline justify-between gap-3">
                      <span className="text-[9px] font-bold uppercase tracking-[0.2em] text-stone-500">{t('cosmograph.workbench.detail.label', 'Detail level')}</span>
                      <strong className="font-semibold text-teal-800">{tierName}</strong>
                    </p>
                    <TierMeter tier={zoomTier} />
                    <p className="mt-2">{t(`cosmograph.workbench.detail.${zoomTier}.body`, TIER_FALLBACK[zoomTier].body)}</p>
                  </div>
                </div>
              ) : null}

              {tab === 'filter' && (
                <KgFilters state={filters} nodes={allMeta} onChange={setFilters} labels={{ period: t('cosmograph.filters.period', 'Period'), type: t('cosmograph.filters.type', 'Type'), school: t('cosmograph.filters.school', 'School'), clear: t('cosmograph.filters.clear', 'Clear filters') }} />
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
                  onNavigateToNode={(id) => void focusNodeById(id)}
                  labels={{ title: t('cosmograph.path.title', 'Find a path between two nodes'), description: t('cosmograph.path.description', 'Choose two loci. Their shortest semantic route becomes your Evidence Thread.'), sourcePlaceholder: t('cosmograph.path.source', 'Source — e.g. Chrysippus'), targetPlaceholder: t('cosmograph.path.target', 'Target — e.g. Augustine'), searchAriaLabel: t('cosmograph.path.searchAria', 'Search for a node'), searchEmpty: t('cosmograph.searchEmpty', 'No match.'), searchResults: t('cosmograph.searchResults', 'Search results'), computing: t('cosmograph.path.computing', 'Computing the shortest path…'), noPath: t('cosmograph.path.noPath', 'No path within 6 hops.'), error: t('cosmograph.path.error', 'Could not compute path'), pathLength: (n) => t('cosmograph.path.length', '{{count}} hops', { count: n }) as string, clear: t('cosmograph.path.clear', 'Clear'), swap: t('cosmograph.path.swap', 'Swap source and target') }}
                />
              )}
            </div>

            <footer className="grid grid-cols-3 border-t border-stone-300 bg-[#f7f2e9] text-center font-body">
              <FooterStat label={t('cosmograph.workbench.footer.visible', 'Visible')} value={formatFull(activeMeta.length, locale)} divider />
              <FooterStat label={t('cosmograph.workbench.footer.relations', 'Relations')} value={formatFull(activeEdges.length, locale)} divider />
              <FooterStat label={t('cosmograph.workbench.footer.detail', 'Detail')} value={tierName} />
            </footer>
          </aside>

          {/* Canvas controls are grouped as one instrument rail, outside the
              primary workbench and away from the dossier close target. */}
          <div className="absolute bottom-4 left-[23.5rem] z-30 hidden items-center border border-stone-300 bg-[#fffdf9]/94 p-1 shadow-[0_12px_34px_rgba(72,52,36,0.11)] backdrop-blur-xl md:flex">
            <div className="flex items-center gap-1">
              <IconButton
                label={t('cosmograph.controls.fit', 'Fit view')}
                icon={<Focus className="h-4 w-4" aria-hidden="true" />}
                onClick={fitView}
              />
              <IconButton
                label={t('cosmograph.atlas.guide', 'Atlas guide')}
                icon={<Sparkles className="h-4 w-4" aria-hidden="true" />}
                onClick={() => setHelpOpen((open) => !open)}
                expanded={helpOpen}
                controls="atlas-guide-hint"
              />
              <IconButton
                label={legendOpen
                  ? t('cosmograph.legend.hide', 'Hide legend')
                  : t('cosmograph.legend.show', 'Show legend')}
                icon={<MapIcon className="h-4 w-4" aria-hidden="true" />}
                onClick={() => setLegendOpen((open) => !open)}
                pressed={legendOpen}
              />
              <IconButton
                label={t('cosmograph.controls.settings', 'Advanced')}
                icon={<Settings className="h-4 w-4" aria-hidden="true" />}
                onClick={() => setAdvancedOpen((open) => !open)}
                expanded={advancedOpen}
                controls="atlas-advanced-drawer"
              />
            </div>
          </div>

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

          {/* === Contextual guide (desktop), phrased for the active view === */}
          {helpOpen && !isMobile && (
            <div
              id="atlas-guide-hint"
              role="note"
              className="pointer-events-auto absolute bottom-[5.25rem] left-[23.5rem] z-20 hidden max-w-sm border border-stone-300 bg-[#fffdf9]/96 p-4 text-[12px] text-stone-600 shadow-[0_18px_50px_rgba(72,52,36,0.14)] backdrop-blur-xl md:block"
            >
              <div className="mb-1 flex items-center gap-2 text-teal-800">
                <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
                <span className="text-[11px] font-semibold uppercase tracking-[0.18em]">
                  {t('cosmograph.atlas.hintLabel', 'Free Will Atlas')}
                </span>
                <DismissButton label={t('common.dismiss', 'Dismiss')} onClick={() => setHelpOpen(false)} />
              </div>
              <p className="leading-5">
                {tab === 'atlas'
                  ? t(
                      'cosmograph.atlas.hintBody',
                      'A curated view of the load-bearing concepts, schools, thinkers, and modern scholars on free will. Search to dive deeper, switch to the full graph for the {{nodes}}-node map, or open Find a path to trace a connection.',
                      { nodes: nodesCompact },
                    )
                  : t(
                      'cosmograph.atlas.hintBodyFull',
                      'The complete release, laid out once and frozen. Zoom to reveal minor loci, click a node to open its dossier, or switch to Atlas for the curated backbone.',
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
              layoutIsFixed={Boolean(cosmo?.fixedLayout)}
              fixedLayoutLabel={tab === 'atlas'
                ? t('cosmograph.advanced.fixedLayout', 'Deterministic constellation layout')
                : t('cosmograph.workbench.fixedLayoutFull', 'Precomputed layout of the complete release')}
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
              detailState={selectedDetailState}
              onRetryDetail={selectedNodeId
                ? () => void ensureNodeDetail(selectedNodeId)
                : undefined}
              releaseId={workspace.releaseId}
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

const DESKTOP_TABS: ReadonlyArray<DesktopTab> = ['atlas', 'full', 'path', 'filter'];

function TabStrip({
  value,
  onChange,
  labels,
  counts,
  countLabel,
  ariaLabel,
  panelId,
}: {
  value: Tab;
  onChange: (next: DesktopTab) => void;
  labels: Record<DesktopTab, string>;
  counts: { atlas: number; full: number; filter: number };
  countLabel: (label: string, count: number) => string;
  ariaLabel: string;
  panelId: string;
}) {
  const refs = useRef<Array<HTMLButtonElement | null>>([]);
  const icons: Record<DesktopTab, ReactNode> = {
    atlas: <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />,
    full: <Network className="h-3.5 w-3.5" aria-hidden="true" />,
    path: <Route className="h-3.5 w-3.5" aria-hidden="true" />,
    filter: <MapIcon className="h-3.5 w-3.5" aria-hidden="true" />,
  };
  const countFor = (id: DesktopTab): number =>
    id === 'path' ? 0 : counts[id];
  const focusable = Math.max(0, DESKTOP_TABS.indexOf(value as DesktopTab));

  // Manual activation: switching slices rebuilds GPU tables, so arrow keys
  // only move focus and Enter/Space commits the choice.
  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    const current = refs.current.findIndex((button) => button === document.activeElement);
    const from = current === -1 ? focusable : current;
    let next = from;
    if (event.key === 'ArrowRight') next = (from + 1) % DESKTOP_TABS.length;
    else if (event.key === 'ArrowLeft') next = (from - 1 + DESKTOP_TABS.length) % DESKTOP_TABS.length;
    else if (event.key === 'Home') next = 0;
    else if (event.key === 'End') next = DESKTOP_TABS.length - 1;
    else return;
    event.preventDefault();
    refs.current[next]?.focus();
  };

  return (
    <div
      role="tablist"
      aria-label={ariaLabel}
      onKeyDown={handleKeyDown}
      className="grid w-full grid-cols-4 bg-[#fffdf9]"
    >
      {DESKTOP_TABS.map((id, index) => {
        const active = value === id;
        const count = countFor(id);
        return (
          <button
            key={id}
            ref={(element) => { refs.current[index] = element; }}
            id={`${panelId}-tab-${id}`}
            type="button"
            role="tab"
            aria-selected={active}
            aria-controls={panelId}
            tabIndex={index === focusable ? 0 : -1}
            onClick={() => onChange(id)}
            aria-label={count > 0 ? countLabel(labels[id], count) : undefined}
            className={[
              'relative inline-flex min-h-11 items-center justify-center gap-1.5 px-1.5 py-2 text-[10px] font-semibold uppercase tracking-[0.06em] outline-none transition-colors focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-orange-600',
              active
                ? 'bg-stone-900 text-[#fffaf1]'
                : 'text-stone-600 hover:bg-stone-100 hover:text-stone-950',
            ].join(' ')}
          >
            {icons[id]}
            <span>{labels[id]}</span>
          </button>
        );
      })}
    </div>
  );
}

interface ConstellationEntry {
  key: string;
  node: AtlasNodeMeta;
}

function ConstellationEntryList({
  navRef,
  title,
  body,
  entries,
  activeKey,
  labelFor,
  onPick,
  compact = false,
}: {
  navRef: MutableRefObject<HTMLElement | null>;
  title: string;
  body: string;
  entries: ReadonlyArray<ConstellationEntry>;
  activeKey: AtlasConstellationKey | null;
  labelFor: (key: string) => string;
  onPick: (key: AtlasConstellationKey) => void;
  compact?: boolean;
}) {
  if (entries.length === 0) return null;
  return (
    <nav ref={navRef} aria-label={title}>
      <p className="text-[9px] font-bold uppercase tracking-[0.2em] text-stone-500">{title}</p>
      <p className={compact
        ? 'mt-1.5 text-xs leading-5 text-stone-600'
        : 'mt-2 font-reader text-base leading-6 text-stone-600'}
      >
        {body}
      </p>
      <ol className={compact ? 'mt-3 border-t border-stone-300' : 'mt-4 border-t border-stone-300'}>
        {entries.map(({ key, node }, index) => {
          const constellation = ATLAS_ENTRY_POINT_CONSTELLATIONS[key] ?? atlasConstellationKey(node);
          const active = activeKey === constellation;
          return (
            <li key={key} className="border-b border-stone-200">
              <button
                type="button"
                onClick={() => onPick(constellation)}
                data-constellation={constellation}
                data-active={String(active)}
                aria-pressed={active}
                className={[
                  'group grid w-full grid-cols-[1.75rem_1fr_auto] items-center gap-2 text-left outline-none transition hover:text-orange-900 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-orange-700 data-[active=true]:text-orange-900',
                  compact ? 'min-h-11 py-1.5' : 'min-h-14 py-2',
                ].join(' ')}
              >
                <span className={[
                  'font-display text-stone-400 group-data-[active=true]:text-orange-800',
                  compact ? 'text-base' : 'text-lg',
                ].join(' ')}
                >
                  {String(index + 1).padStart(2, '0')}
                </span>
                <span className="text-sm font-semibold">{labelFor(key)}</span>
                <ArrowRight className="h-3.5 w-3.5 text-stone-400 transition-transform group-hover:translate-x-1 motion-reduce:transition-none motion-reduce:group-hover:translate-x-0" aria-hidden="true" />
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

type GrammarGlyph = 'work' | 'argument' | 'author';

/** Miniature drawings of the frozen layout's three spatial rules. */
function GrammarGlyphMark({ glyph }: { glyph: GrammarGlyph }) {
  const ring = Array.from({ length: 12 }, (_, index) => {
    const angle = -Math.PI / 2 + (index / 12) * Math.PI * 2;
    return { x: 20 + Math.cos(angle) * 13, y: 20 + Math.sin(angle) * 13, index };
  });
  return (
    <svg viewBox="0 0 40 40" className="h-10 w-10 shrink-0" aria-hidden="true">
      {glyph === 'work' && (
        <>
          <circle cx="20" cy="20" r="13" fill="none" stroke="#d6d3d1" strokeDasharray="1.5 2.5" />
          {ring.map(({ x, y, index }) => (
            <circle key={index} cx={x} cy={y} r={index === 0 ? 2.4 : 1.8} fill="#57534e" fillOpacity={0.3 + (index / 11) * 0.7} />
          ))}
        </>
      )}
      {glyph === 'argument' && (
        <>
          {[[-9, -5], [-4, -11], [6, -10], [11, -2], [8, 9], [-2, 11], [-10, 6]].map(([dx, dy]) => (
            <line key={`${dx}:${dy}`} x1="20" y1="20" x2={20 + dx} y2={20 + dy} stroke="#e7e5e4" />
          ))}
          {[[-9, -5], [-4, -11], [6, -10], [11, -2], [8, 9], [-2, 11], [-10, 6]].map(([dx, dy]) => (
            <circle key={`p${dx}:${dy}`} cx={20 + dx} cy={20 + dy} r="2" fill="#c2410c" fillOpacity="0.75" />
          ))}
          <rect x="16.5" y="16.5" width="7" height="7" fill="#fffdf9" stroke="#292524" strokeWidth="1.4" />
        </>
      )}
      {glyph === 'author' && (
        <>
          {ring.map(({ x, y, index }) => (
            <circle key={index} cx={x} cy={y} r="1.6" fill="#a8a29e" />
          ))}
          <circle cx="20" cy="20" r="6" fill="#0f766e" fillOpacity="0.14" />
          <circle cx="20" cy="20" r="3.6" fill="#0f766e" />
        </>
      )}
    </svg>
  );
}

function LayoutGrammar({
  title,
  items,
}: {
  title: string;
  items: ReadonlyArray<{ glyph: GrammarGlyph; name: string; body: string }>;
}) {
  return (
    <section aria-label={title}>
      <p className="text-[9px] font-bold uppercase tracking-[0.2em] text-stone-500">{title}</p>
      <dl className="mt-3 grid gap-3">
        {items.map(({ glyph, name, body }) => (
          <div key={glyph} className="grid grid-cols-[2.5rem_1fr] items-center gap-3">
            <GrammarGlyphMark glyph={glyph} />
            <div>
              <dt className="text-xs font-semibold text-stone-900">{name}</dt>
              <dd className="text-xs leading-5 text-stone-600">{body}</dd>
            </div>
          </div>
        ))}
      </dl>
    </section>
  );
}

const TIER_ORDER: ReadonlyArray<AtlasZoomTier> = ['overview', 'mid', 'close'];

function TierMeter({ tier }: { tier: AtlasZoomTier }) {
  const reached = TIER_ORDER.indexOf(tier);
  return (
    <div className="mt-2 grid grid-cols-3 gap-1" aria-hidden="true">
      {TIER_ORDER.map((step, index) => (
        <span
          key={step}
          className={[
            'h-1 transition-colors duration-300 motion-reduce:transition-none',
            index <= reached ? 'bg-teal-700' : 'bg-stone-200',
          ].join(' ')}
        />
      ))}
    </div>
  );
}

function FooterStat({
  label,
  value,
  divider = false,
}: {
  label: string;
  value: string;
  divider?: boolean;
}) {
  return (
    <div className={divider ? 'border-r border-stone-300 px-2 py-2' : 'px-2 py-2'}>
      <span className="block text-[9px] uppercase tracking-wider text-stone-500">{label}</span>
      <strong className="block truncate text-xs text-stone-900">{value}</strong>
    </div>
  );
}

function DismissButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      // The visible chip stays small; the pseudo-element extends the hit
      // area to 44 px.
      className="relative ml-auto inline-flex h-7 w-7 items-center justify-center rounded-full border border-stone-300 bg-white/70 text-stone-500 transition-colors before:absolute before:-inset-2 before:content-[''] hover:border-orange-500 hover:text-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700"
    >
      <X className="h-3 w-3" aria-hidden="true" />
    </button>
  );
}

function IconButton({
  icon,
  label,
  onClick,
  pressed,
  expanded,
  controls,
}: {
  icon: ReactNode;
  label: string;
  onClick: () => void;
  pressed?: boolean;
  expanded?: boolean;
  controls?: string;
}) {
  const active = Boolean(pressed || expanded);
  return (
    <button
      type="button"
      aria-label={label}
      aria-pressed={pressed}
      aria-expanded={expanded}
      aria-controls={expanded ? controls : undefined}
      title={label}
      onClick={onClick}
      className={[
        'inline-flex h-11 w-11 items-center justify-center transition-colors hover:bg-orange-50 hover:text-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-orange-700',
        active ? 'bg-stone-900 text-[#fffaf1] hover:bg-stone-800 hover:text-[#fffaf1]' : 'text-stone-600',
      ].join(' ')}
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
  fixedLayoutLabel,
}: {
  onClose: () => void;
  simulationRunning: boolean;
  onToggleSimulation: () => void;
  onExportScreenshot: () => void;
  layoutIsFixed: boolean;
  fixedLayoutLabel: string;
}) {
  const { t } = useTranslation();
  return (
    <div
      id="atlas-advanced-drawer"
      role="region"
      aria-label={t('cosmograph.advanced.title', 'Advanced')}
      className="absolute right-3 top-24 z-30 w-[18rem] rounded-2xl border border-stone-300 bg-[#fffdf9]/95 p-4 text-[12px] text-stone-600 shadow-[0_24px_60px_rgba(72,52,36,0.16)] backdrop-blur-xl md:right-6 md:top-28"
    >
      <div className="mb-2 flex items-center justify-between">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-stone-500">
          {t('cosmograph.advanced.title', 'Advanced')}
        </p>
        <DismissButton label={t('common.close', 'Close')} onClick={onClose} />
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
            <Focus className="h-4 w-4 shrink-0" aria-hidden="true" />
            {fixedLayoutLabel}
          </div>
        ) : (
        <button
          type="button"
          onClick={onToggleSimulation}
          className="flex min-h-11 items-center gap-2 rounded-xl border border-stone-300 bg-white/70 px-3 text-left font-semibold text-stone-700 transition hover:border-orange-500 hover:text-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700"
        >
          {simulationRunning ? <Pause className="h-4 w-4" aria-hidden="true" /> : <Play className="h-4 w-4" aria-hidden="true" />}
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
          <Camera className="h-4 w-4" aria-hidden="true" />
          {t('cosmograph.controls.screenshot', 'Export screenshot')}
        </button>
      </div>
    </div>
  );
}
