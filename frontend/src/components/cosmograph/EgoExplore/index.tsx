import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { AnimatePresence, motion } from 'framer-motion';

import type { AtlasNodeMeta } from '../AtlasHelpers';
import type { KGNode } from '../../../types';
import { pickAtlasNodeIds } from '../FreeWillAtlas';
import Breadcrumb from './Breadcrumb';
import ExploreSearch from './ExploreSearch';
import FocalCard from './FocalCard';
import SpokeGroup from './SpokeGroup';
import { groupNeighborsByRelation, pickInitialFocalId } from './relationGrouping';

export interface EgoExploreRelationship {
  readonly id: string;
  readonly label: string;
  readonly type: string;
  readonly relation: string;
  readonly direction: 'incoming' | 'outgoing';
}

interface EgoExploreProps {
  readonly meta: ReadonlyArray<AtlasNodeMeta>;
  readonly rawById: Map<string, KGNode>;
  readonly relationships: Map<string, ReadonlyArray<EgoExploreRelationship>>;
  readonly initialNodeId?: string;
  readonly onPickNode?: (id: string) => void;
  readonly compactHeader?: boolean;
}

function ExploreSkeleton() {
  return (
    <div className="space-y-4">
      <div className="h-6 w-2/3 animate-pulse rounded-full bg-amber-100/60" />
      <div className="rounded-3xl border border-amber-200/60 bg-white/60 p-5">
        <div className="flex items-start gap-4">
          <div className="h-12 w-12 animate-pulse rounded-2xl bg-amber-100/70" />
          <div className="min-w-0 flex-1 space-y-2">
            <div className="h-5 w-1/2 animate-pulse rounded-full bg-amber-100/70" />
            <div className="h-3 w-1/3 animate-pulse rounded-full bg-amber-100/50" />
            <div className="h-3 w-full animate-pulse rounded-full bg-amber-100/40" />
            <div className="h-3 w-5/6 animate-pulse rounded-full bg-amber-100/40" />
          </div>
        </div>
      </div>
      {[0, 1, 2].map((i) => (
        <div key={i} className="space-y-2">
          <div className="h-3 w-32 animate-pulse rounded-full bg-amber-100/60" />
          <div className="flex gap-2">
            {[0, 1, 2].map((j) => (
              <div
                key={j}
                className="h-12 w-40 shrink-0 animate-pulse rounded-2xl bg-white/60"
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function EgoExplore({
  meta,
  rawById,
  relationships,
  initialNodeId,
  onPickNode,
  compactHeader,
}: EgoExploreProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const metaById = useMemo(() => new Map(meta.map((m) => [m.id, m])), [meta]);

  const atlasIds = useMemo(
    () => pickAtlasNodeIds(meta.map((m) => ({ id: m.id, type: m.typeKey }))),
    [meta],
  );

  const seedId = useMemo(() => {
    if (initialNodeId && metaById.has(initialNodeId)) return initialNodeId;
    const fromAtlas = pickInitialFocalId(meta, atlasIds);
    if (fromAtlas) return fromAtlas;
    return [...meta].sort((a, b) => b.degree - a.degree)[0]?.id;
  }, [initialNodeId, metaById, atlasIds, meta]);

  const [trail, setTrail] = useState<ReadonlyArray<string>>(() =>
    seedId ? [seedId] : [],
  );

  useEffect(() => {
    if (!seedId) return;
    if (trail.length === 0) {
      setTrail([seedId]);
      return;
    }
    if (initialNodeId && trail[trail.length - 1] !== initialNodeId && metaById.has(initialNodeId)) {
      setTrail((current) => {
        const last = current[current.length - 1];
        if (last === initialNodeId) return current;
        const existing = current.lastIndexOf(initialNodeId);
        if (existing >= 0) {
          return current.slice(0, existing + 1);
        }
        return [...current, initialNodeId];
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialNodeId, seedId, metaById]);

  const focalId = trail[trail.length - 1];
  const focalMeta = focalId ? metaById.get(focalId) ?? null : null;
  const focalRaw = focalId ? rawById.get(focalId) ?? null : null;

  useEffect(() => {
    if (!focalId) return;
    onPickNode?.(focalId);
    navigate(`/visualizer/${focalId}`, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focalId]);

  const pushNode = useCallback((id: string) => {
    setTrail((current) => {
      if (current[current.length - 1] === id) return current;
      const existing = current.lastIndexOf(id);
      if (existing >= 0) {
        return current.slice(0, existing + 1);
      }
      return [...current, id];
    });
  }, []);

  const onBreadcrumbPick = useCallback((_id: string, indexInTrail: number) => {
    setTrail((current) => current.slice(0, indexInTrail + 1));
  }, []);

  const onSearchPick = useCallback((node: AtlasNodeMeta) => {
    setTrail([node.id]);
  }, []);

  const groups = useMemo(
    () => groupNeighborsByRelation(
      focalId ? relationships.get(focalId) ?? [] : [],
      metaById,
    ),
    [focalId, relationships, metaById],
  );

  if (meta.length === 0) {
    return (
      <div className="mx-auto w-full max-w-2xl px-4 py-6">
        <ExploreSkeleton />
      </div>
    );
  }

  return (
    <div className="absolute inset-0 flex flex-col bg-parchment-50">
      <div aria-hidden className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_18%_8%,rgba(217,119,6,0.10),transparent_36%),radial-gradient(circle_at_82%_18%,rgba(180,83,9,0.08),transparent_30%)]" />
      </div>

      {!compactHeader && (
        <header className="relative z-10 border-b border-amber-200/40 bg-white/55 px-4 pb-2 pt-3 backdrop-blur-md md:px-6 md:pt-4">
          <Breadcrumb trail={trail} metaById={metaById} onPick={onBreadcrumbPick} />
        </header>
      )}

      <div
        role="status"
        aria-live="polite"
        className="sr-only"
      >
        {focalMeta
          ? t('cosmograph.explore.announceFocal', 'Now exploring {{name}}', {
              name: focalMeta.label,
            })
          : ''}
      </div>

      <main className="relative z-10 flex-1 overflow-y-auto px-4 pb-32 pt-4 md:px-6">
        <div className="mx-auto w-full max-w-2xl space-y-5">
          <AnimatePresence mode="wait">
            {focalMeta && (
              <motion.div
                key={focalMeta.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.22, ease: [0.22, 0.7, 0.36, 1] }}
                className="space-y-5"
              >
                <FocalCard meta={focalMeta} raw={focalRaw} />

                {groups.length === 0 ? (
                  <p className="rounded-2xl border border-amber-200/50 bg-white/60 px-4 py-3 text-[13px] leading-6 text-stone-600">
                    {t(
                      'cosmograph.explore.noNeighbors',
                      'This node has no neighbors in the curated graph. Use search to jump elsewhere.',
                    )}
                  </p>
                ) : (
                  groups.map((group) => (
                    <SpokeGroup
                      key={group.key}
                      group={group}
                      metaById={metaById}
                      onPick={pushNode}
                    />
                  ))
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      <div
        data-explore-search
        className="pointer-events-none absolute inset-x-0 bottom-0 z-20 px-4 pb-4 md:px-6 md:pb-6"
      >
        <div className="pointer-events-auto mx-auto w-full max-w-2xl">
          <ExploreSearch nodes={meta} onPick={onSearchPick} />
        </div>
      </div>
    </div>
  );
}
