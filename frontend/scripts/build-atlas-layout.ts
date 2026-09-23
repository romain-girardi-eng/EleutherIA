/**
 * Precompute the frozen layout of the complete Atlas.
 *
 *   node scripts/build-atlas-layout.ts [--api https://free-will.app] [--iterations 900]
 *
 * Fetches the served workspace release (the exact node/edge set the visualizer
 * renders), lays it out with ForceAtlas2 in LinLog mode — tight communities,
 * visible gaps between them — seeded by the Atlas constellations so the named
 * regions stay where their labels are, then removes point overlap. Writes
 * `src/assets/atlas-full-layout.json`, consumed by `atlasLayout.ts`.
 *
 * Re-run after each KG release. A stale layout still works: nodes added since
 * are placed beside their neighbours at load time.
 */
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import Graph from 'graphology';
import forceAtlas2 from 'graphology-layout-forceatlas2';

import {
  ATLAS_CONSTELLATION_POSITIONS,
  atlasConstellationKey,
} from '../src/components/cosmograph/FreeWillAtlas.ts';

interface WorkspaceNode {
  id: string;
  type?: string;
  period?: string | null;
  school?: string | null;
  scholarly_role?: string | null;
}

interface WorkspaceEdge {
  source: string;
  target: string;
  relation?: string;
}

interface ReleasePage {
  release_id: string;
  nodes?: WorkspaceNode[];
  edges?: WorkspaceEdge[];
}

const here = dirname(fileURLToPath(import.meta.url));
const OUTPUT = resolve(here, '../src/assets/atlas-full-layout.json');
const PAGE_SIZE = 50_000;

function argument(name: string, fallback: string): string {
  const index = process.argv.indexOf(`--${name}`);
  return index >= 0 && process.argv[index + 1] ? process.argv[index + 1] : fallback;
}

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url, { headers: { accept: 'application/json' } });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText} for ${url}`);
  return (await response.json()) as T;
}

async function fetchRelease(api: string) {
  const stats = await getJson<{ release_id: string; served_total_nodes: number; served_total_edges: number }>(
    `${api}/api/kg/workspace/stats`,
  );
  const fetchAll = async <T>(resource: 'nodes' | 'edges', total: number): Promise<T[]> => {
    const items: T[] = [];
    for (let offset = 0; offset < total; offset += PAGE_SIZE) {
      const page = await getJson<ReleasePage>(
        `${api}/api/kg/workspace/${resource}?limit=${PAGE_SIZE}&offset=${offset}&release_id=${stats.release_id}`,
      );
      if (page.release_id !== stats.release_id) throw new Error(`${resource} page from another release`);
      items.push(...((page[resource] ?? []) as T[]));
    }
    if (items.length !== total) throw new Error(`${resource}: expected ${total}, got ${items.length}`);
    return items;
  };
  const nodes = await fetchAll<WorkspaceNode>('nodes', stats.served_total_nodes);
  const edges = await fetchAll<WorkspaceEdge>('edges', stats.served_total_edges);
  return { releaseId: stats.release_id, nodes, edges };
}

// Mirrors AtlasHelpers: `detectLayer`, and the edge hierarchy behind `edgeWidth`.
function isModern(node: WorkspaceNode): boolean {
  const period = (node.period ?? '').toLowerCase();
  const role = (node.scholarly_role ?? '').toLowerCase();
  return period.includes('modern') || period.includes('contemporary')
    || role.includes('scholar') || role.includes('historian');
}

const STRUCTURAL = new Set(['authored_by', 'member_of', 'creates', 'created_by', 'part_of']);
const DOCTRINAL = new Set([
  'interprets', 'critiques', 'influences', 'influenced_by', 'responds_to', 'refutes',
  'supports', 'opposes', 'agrees_with', 'critiqued_by', 'discusses',
]);

function edgeWeight(relation: string | undefined): number {
  if (relation && STRUCTURAL.has(relation)) return 2;
  if (relation && DOCTRINAL.has(relation)) return 1.4;
  return 1;
}

function hashUnit(id: string, salt: number): number {
  let hash = 2166136261 ^ salt;
  for (let index = 0; index < id.length; index += 1) {
    hash ^= id.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return ((hash >>> 0) % 100_000) / 100_000;
}

const POINT_FOOTPRINT = 3;

/**
 * Remove overlap in two phases. Discs first push each other apart — the
 * smaller one moves more, so large works keep the place ForceAtlas2 found.
 * Lone points then step radially out of any disc they landed in. Returns the
 * number of footprints still overlapping.
 */
function separateDiscs(graph: Graph, discMargin: number, pointMargin: number): number {
  const ids = graph.nodes();
  const x = new Float64Array(ids.length);
  const y = new Float64Array(ids.length);
  const r = new Float64Array(ids.length);
  ids.forEach((id, index) => {
    const attributes = graph.getNodeAttributes(id);
    x[index] = attributes.x;
    y[index] = attributes.y;
    r[index] = attributes.size;
  });
  const discs = ids.map((_, index) => index).filter((index) => r[index] > POINT_FOOTPRINT);
  const points = ids.map((_, index) => index).filter((index) => r[index] <= POINT_FOOTPRINT);

  const overlapping = (i: number, j: number) => {
    const bothDiscs = r[i] > POINT_FOOTPRINT && r[j] > POINT_FOOTPRINT;
    const minimum = r[i] + r[j] + (bothDiscs ? discMargin : pointMargin);
    const dx = x[j] - x[i];
    const dy = y[j] - y[i];
    if (Math.abs(dx) >= minimum || Math.abs(dy) >= minimum) return null;
    const distance = Math.hypot(dx, dy);
    if (distance >= minimum) return null;
    const ux = distance > 1e-9 ? dx / distance : Math.cos(i * 2.399);
    const uy = distance > 1e-9 ? dy / distance : Math.sin(i * 2.399);
    return { gap: minimum - distance, ux, uy };
  };

  for (let pass = 0; pass < 2000; pass += 1) {
    let moved = false;
    for (let a = 0; a < discs.length; a += 1) {
      for (let b = a + 1; b < discs.length; b += 1) {
        const i = discs[a];
        const j = discs[b];
        const hit = overlapping(i, j);
        if (!hit) continue;
        moved = true;
        const share = r[j] / (r[i] + r[j]);
        const push = hit.gap * 1.02;
        x[i] -= hit.ux * push * share;
        y[i] -= hit.uy * push * share;
        x[j] += hit.ux * push * (1 - share);
        y[j] += hit.uy * push * (1 - share);
      }
    }
    if (!moved) break;
    // A jammed packing cannot resolve pairwise; breathe the whole map out a
    // little so every disc gains room without reordering the neighbourhoods.
    if (pass % 20 === 19) {
      for (let index = 0; index < ids.length; index += 1) {
        x[index] *= 1.01;
        y[index] *= 1.01;
      }
    }
  }

  for (let pass = 0; pass < 200; pass += 1) {
    let moved = false;
    for (const point of points) {
      for (const disc of discs) {
        const hit = overlapping(disc, point);
        if (!hit) continue;
        moved = true;
        x[point] += hit.ux * hit.gap * 1.02;
        y[point] += hit.uy * hit.gap * 1.02;
      }
    }
    if (!moved) break;
  }

  let remaining = 0;
  for (const disc of discs) {
    for (let index = 0; index < ids.length; index += 1) {
      if (index !== disc && (r[index] <= POINT_FOOTPRINT || index > disc) && overlapping(disc, index)) {
        remaining += 1;
      }
    }
  }
  ids.forEach((id, index) => graph.mergeNodeAttributes(id, { x: x[index], y: y[index] }));
  return remaining;
}

async function main() {
  const api = argument('api', 'https://free-will.app').replace(/\/+$/, '');
  const iterations = Number(argument('iterations', '900'));
  const cache = argument('cache', '');

  let release: Awaited<ReturnType<typeof fetchRelease>>;
  if (cache) {
    try {
      release = JSON.parse(readFileSync(cache, 'utf8'));
    } catch {
      release = await fetchRelease(api);
      writeFileSync(cache, JSON.stringify(release));
    }
  } else {
    release = await fetchRelease(api);
  }
  console.log(`release ${release.releaseId}: ${release.nodes.length} nodes, ${release.edges.length} edges`);

  const byId = new Map(release.nodes.map((node) => [node.id, node]));

  // 1. Evidence orbits one home. A passage belongs to its work (else its
  //    collection, else its author); a modern argument to the publication that
  //    advances it (else its author). Lower rank wins.
  const HOME_RANK: Readonly<Record<string, Readonly<Record<string, number>>>> = {
    passage: { work: 0, source_collection: 1, person: 2 },
    argument: { publication: 0, person: 1 },
  };
  const home = new Map<string, { id: string; rank: number }>();
  const offerHome = (satellite: string, candidate: string) => {
    const ranks = HOME_RANK[byId.get(satellite)?.type ?? ''];
    const rank = ranks?.[byId.get(candidate)?.type ?? ''];
    if (rank === undefined) return;
    const current = home.get(satellite);
    if (!current || rank < current.rank) home.set(satellite, { id: candidate, rank });
  };
  for (const edge of release.edges) {
    if (!byId.has(edge.source) || !byId.has(edge.target)) continue;
    offerHome(edge.source, edge.target);
    offerHome(edge.target, edge.source);
  }
  // Translations without a home of their own sit with their original.
  for (const edge of release.edges) {
    if (edge.relation !== 'translation_of') continue;
    const original = home.get(edge.target);
    if (!home.has(edge.source) && original) home.set(edge.source, original);
  }
  const orbit = new Map<string, string[]>();
  for (const [satellite, { id }] of home) {
    const list = orbit.get(id) ?? [];
    list.push(satellite);
    orbit.set(id, list);
  }

  // An author whose passages mostly come from one work sits at that work's
  // centre: the authored_by edges then run inside the disc instead of fanning
  // across the map from its rim.
  const authorTotals = new Map<string, number>();
  const authorWork = new Map<string, Map<string, number>>();
  for (const edge of release.edges) {
    if (edge.relation !== 'authored_by' || byId.get(edge.source)?.type !== 'passage') continue;
    const work = home.get(edge.source);
    if (byId.get(edge.target)?.type !== 'person') continue;
    authorTotals.set(edge.target, (authorTotals.get(edge.target) ?? 0) + 1);
    if (!work || byId.get(work.id)?.type !== 'work') continue;
    const counts = authorWork.get(edge.target) ?? new Map<string, number>();
    counts.set(work.id, (counts.get(work.id) ?? 0) + 1);
    authorWork.set(edge.target, counts);
  }
  const anchoredAuthor = new Map<string, string>();
  const workHost = new Map<string, { author: string; count: number }>();
  for (const [author, counts] of authorWork) {
    const [work, count] = [...counts].sort((left, right) => right[1] - left[1])[0];
    if (count < 0.5 * (authorTotals.get(author) ?? 0)) continue;
    const host = workHost.get(work);
    if (!host || count > host.count) workHost.set(work, { author, count });
  }
  for (const [work, { author }] of workHost) {
    anchoredAuthor.set(author, work);
    // The author's own homeless passages join the same disc.
    const own = orbit.get(author);
    if (!own) continue;
    orbit.set(work, [...(orbit.get(work) ?? []), ...own]);
    orbit.delete(author);
  }

  // 2. The backbone: every node without a home. Satellite
  //    edges are lifted onto the backbone as weighted home→target edges, so
  //    a work sits near the concepts and arguments its passages support.
  const graph = new Graph({ type: 'undirected', multi: false, allowSelfLoops: false });
  const seedScale = 12;
  for (const node of release.nodes) {
    if (home.has(node.id) || anchoredAuthor.has(node.id)) continue;
    const key = atlasConstellationKey({
      id: node.id,
      layer: isModern(node) ? 'modern' : 'ancient',
      schoolLabel: node.school ?? '',
      periodLabel: node.period ?? '',
    });
    const [cx, cy] = ATLAS_CONSTELLATION_POSITIONS[key];
    const angle = hashUnit(node.id, 1) * Math.PI * 2;
    const radius = Math.sqrt(hashUnit(node.id, 2)) * 2600;
    graph.addNode(node.id, {
      x: cx * seedScale + Math.cos(angle) * radius,
      y: cy * seedScale + Math.sin(angle) * radius,
      size: 1,
    });
  }
  const backboneOf = (id: string): string | undefined => {
    const resolved = home.get(id)?.id ?? id;
    return anchoredAuthor.get(resolved) ?? (graph.hasNode(resolved) ? resolved : undefined);
  };
  for (const edge of release.edges) {
    const source = backboneOf(edge.source);
    const target = backboneOf(edge.target);
    if (!source || !target || source === target) continue;
    const lifted = source !== edge.source || target !== edge.target;
    const weight = lifted ? 0.35 : edgeWeight(edge.relation);
    if (graph.hasEdge(source, target)) {
      graph.updateEdgeAttribute(source, target, 'weight', (current: number) =>
        Math.min(6, current + weight));
    } else {
      graph.addEdge(source, target, { weight });
    }
  }

  const started = Date.now();
  forceAtlas2.assign(graph, {
    iterations,
    getEdgeWeight: 'weight',
    settings: {
      linLogMode: true,
      outboundAttractionDistribution: false,
      adjustSizes: false,
      barnesHutOptimize: true,
      barnesHutTheta: 0.6,
      edgeWeightInfluence: 1,
      scalingRatio: 4,
      gravity: 1,
      strongGravityMode: false,
      slowDown: 2,
    },
  });
  console.log(`forceatlas2: ${graph.order} backbone nodes, ${iterations} iterations in ${((Date.now() - started) / 1000).toFixed(1)}s`);

  // 3. Scale the backbone so a typical edge spans ~40 units, then give each
  //    home the radius of its passage disc and push discs apart.
  const lengths: number[] = [];
  graph.forEachEdge((_edge, _attributes, source, target, sa, ta) => {
    lengths.push(Math.hypot(sa.x - ta.x, sa.y - ta.y));
  });
  lengths.sort((left, right) => left - right);
  const scale = 40 / Math.max(1e-6, lengths[Math.floor(lengths.length / 2)] ?? 1);
  const SATELLITE_SPACING = 2.2;
  const discRadius = (count: number) => SATELLITE_SPACING * Math.sqrt(count) * 1.05 + 4;
  graph.forEachNode((id, attributes) => {
    graph.mergeNodeAttributes(id, {
      x: attributes.x * scale,
      y: attributes.y * scale,
      size: orbit.has(id) ? discRadius(orbit.get(id)!.length) : POINT_FOOTPRINT,
    });
  });
  // Settle again with the discs' real footprint: attraction pulls each author
  // back against its works while size-aware repulsion keeps discs apart.
  forceAtlas2.assign(graph, {
    iterations: Math.round(iterations / 2),
    getEdgeWeight: 'weight',
    settings: {
      linLogMode: true,
      adjustSizes: true,
      barnesHutOptimize: true,
      barnesHutTheta: 0.6,
      edgeWeightInfluence: 1,
      scalingRatio: 1.2,
      gravity: 2,
      slowDown: 8,
    },
  });
  // Gaps between discs are wide enough for a lone point to sit in them.
  const overlaps = separateDiscs(graph, 16, 2);
  console.log(`overlapping footprints after separation: ${overlaps}`);
  console.log(`layout done in ${((Date.now() - started) / 1000).toFixed(1)}s total`);

  // 4. Satellites fill their home's disc on a sunflower spiral, in canonical
  //    id order, so a work reads as one compact, ordered field of evidence.
  const place = new Map<string, readonly [number, number]>();
  graph.forEachNode((id, attributes) => place.set(id, [attributes.x, attributes.y]));
  for (const [author, work] of anchoredAuthor) {
    const centre = place.get(work);
    if (centre) place.set(author, [centre[0], centre[1] - SATELLITE_SPACING * 0.8]);
  }
  const GOLDEN = Math.PI * (3 - Math.sqrt(5));
  for (const [homeId, satellites] of orbit) {
    const centre = place.get(homeId);
    if (!centre) continue;
    satellites.sort((left, right) => left.localeCompare(right, 'en', { numeric: true }));
    satellites.forEach((satellite, index) => {
      const radius = SATELLITE_SPACING * Math.sqrt(index + 2.5);
      const angle = (index + 2.5) * GOLDEN;
      place.set(satellite, [centre[0] + Math.cos(angle) * radius, centre[1] + Math.sin(angle) * radius]);
    });
  }

  const ids = release.nodes.map((node) => node.id);
  const positions = new Float32Array(ids.length * 2);
  ids.forEach((id, index) => {
    const position = place.get(id);
    if (!position) throw new Error(`no position for ${id}`);
    positions[index * 2] = position[0];
    positions[index * 2 + 1] = position[1];
  });
  mkdirSync(dirname(OUTPUT), { recursive: true });
  writeFileSync(OUTPUT, JSON.stringify({
    version: 1,
    release_id: release.releaseId,
    ids,
    positions_f32_base64: Buffer.from(positions.buffer).toString('base64'),
  }));
  console.log(`wrote ${OUTPUT}`);
}

await main();
