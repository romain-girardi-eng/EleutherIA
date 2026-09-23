/**
 * Frozen layout for the complete Atlas.
 *
 * The complete release (~23k points, ~56k links) used to run Cosmograph's
 * force simulation on every visit: roughly four minutes of GPU work at
 * ~28 fps before the map settled. The settled positions are deterministic
 * enough to be computed once, so the renderer now receives them as fixed
 * coordinates and never simulates the full graph in the browser.
 *
 * Sources, in order:
 *   1. the per-browser IndexedDB cache for this exact release;
 *   2. the layout shipped with the frontend bundle (may belong to an older
 *      release — nodes it lacks are placed beside their neighbours);
 *   3. none: the caller runs the live simulation and saves its end state.
 */

export interface AtlasLayoutRecord {
  releaseId: string;
  ids: string[];
  /** Interleaved x/y pairs, `positions[2 * i]` belongs to `ids[i]`. */
  positions: Float32Array;
}

interface SerializedAtlasLayout {
  version: 1;
  release_id: string;
  ids: string[];
  positions_f32_base64: string;
}

export type AtlasPositionMap = ReadonlyMap<string, readonly [number, number]>;

export interface AtlasLayoutNode {
  id: string;
}

export interface AtlasLayoutEdge {
  source: string;
  target: string;
}

/** Below this share of known points the frozen map no longer describes the
 * release faithfully, and the live simulation is the honest fallback. */
export const MIN_LAYOUT_COVERAGE = 0.85;

const DB_NAME = 'eleutheria-atlas';
const STORE_NAME = 'layouts';
const FULL_LAYOUT_KEY = 'full';

function encodeFloat32(values: Float32Array): string {
  const bytes = new Uint8Array(values.buffer, values.byteOffset, values.byteLength);
  let binary = '';
  const chunk = 0x8000;
  for (let offset = 0; offset < bytes.length; offset += chunk) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + chunk));
  }
  return btoa(binary);
}

function decodeFloat32(encoded: string): Float32Array {
  const binary = atob(encoded);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return new Float32Array(bytes.buffer);
}

export function serializeAtlasLayout(record: AtlasLayoutRecord): SerializedAtlasLayout {
  return {
    version: 1,
    release_id: record.releaseId,
    ids: record.ids,
    positions_f32_base64: encodeFloat32(record.positions),
  };
}

export function parseAtlasLayout(value: unknown): AtlasLayoutRecord | null {
  if (!value || typeof value !== 'object') return null;
  const raw = value as Partial<SerializedAtlasLayout>;
  if (
    raw.version !== 1
    || typeof raw.release_id !== 'string'
    || !Array.isArray(raw.ids)
    || typeof raw.positions_f32_base64 !== 'string'
  ) return null;
  try {
    const positions = decodeFloat32(raw.positions_f32_base64);
    if (positions.length !== raw.ids.length * 2) return null;
    for (const coordinate of positions) {
      if (!Number.isFinite(coordinate)) return null;
    }
    return { releaseId: raw.release_id, ids: raw.ids.map(String), positions };
  } catch {
    return null;
  }
}

/** Capture Cosmograph's flat `[x0, y0, x1, y1, …]` output in point order. */
export function atlasLayoutFromPositions(
  releaseId: string,
  nodes: ReadonlyArray<AtlasLayoutNode>,
  flatPositions: ArrayLike<number>,
): AtlasLayoutRecord | null {
  if (flatPositions.length < nodes.length * 2) return null;
  const positions = new Float32Array(nodes.length * 2);
  for (let index = 0; index < nodes.length * 2; index += 1) {
    const value = flatPositions[index];
    if (!Number.isFinite(value)) return null;
    positions[index] = value;
  }
  return { releaseId, ids: nodes.map((node) => node.id), positions };
}

function hashUnit(id: string, salt: number): number {
  let hash = 2166136261 ^ salt;
  for (let index = 0; index < id.length; index += 1) {
    hash ^= id.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return ((hash >>> 0) % 10_000) / 10_000;
}

/**
 * Map every node of the current release to a position. Nodes missing from the
 * frozen layout (added after it was computed) sit at the mean of their placed
 * neighbours, with a deterministic offset so siblings never stack. Returns
 * `null` when the layout covers too little of the release to be faithful.
 */
export function resolveAtlasPositions(
  layout: AtlasLayoutRecord,
  nodes: ReadonlyArray<AtlasLayoutNode>,
  edges: ReadonlyArray<AtlasLayoutEdge>,
): Map<string, readonly [number, number]> | null {
  if (nodes.length === 0) return null;
  const known = new Map<string, readonly [number, number]>();
  layout.ids.forEach((id, index) => {
    known.set(id, [layout.positions[index * 2], layout.positions[index * 2 + 1]]);
  });

  const positions = new Map<string, readonly [number, number]>();
  const missing: string[] = [];
  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;
  for (const node of nodes) {
    const position = known.get(node.id);
    if (!position) {
      missing.push(node.id);
      continue;
    }
    positions.set(node.id, position);
    minX = Math.min(minX, position[0]);
    maxX = Math.max(maxX, position[0]);
    minY = Math.min(minY, position[1]);
    maxY = Math.max(maxY, position[1]);
  }
  if (positions.size / nodes.length < MIN_LAYOUT_COVERAGE) return null;
  if (missing.length === 0) return positions;

  const neighbours = new Map<string, string[]>();
  const missingSet = new Set(missing);
  for (const edge of edges) {
    if (missingSet.has(edge.source)) {
      const list = neighbours.get(edge.source) ?? [];
      list.push(edge.target);
      neighbours.set(edge.source, list);
    }
    if (missingSet.has(edge.target)) {
      const list = neighbours.get(edge.target) ?? [];
      list.push(edge.source);
      neighbours.set(edge.target, list);
    }
  }

  const span = Math.max(maxX - minX, maxY - minY, 1);
  const jitter = span * 0.004;
  const centre: readonly [number, number] = [(minX + maxX) / 2, (minY + maxY) / 2];
  let pending = missing;
  // Chains of new nodes resolve outward from the placed graph; a few passes
  // cover every realistic delta, the remainder falls back to the centre.
  for (let pass = 0; pass < 4 && pending.length > 0; pass += 1) {
    const next: string[] = [];
    for (const id of pending) {
      let sumX = 0;
      let sumY = 0;
      let count = 0;
      for (const neighbour of neighbours.get(id) ?? []) {
        const position = positions.get(neighbour);
        if (!position) continue;
        sumX += position[0];
        sumY += position[1];
        count += 1;
      }
      if (count === 0) {
        next.push(id);
        continue;
      }
      positions.set(id, [
        sumX / count + (hashUnit(id, 1) - 0.5) * jitter,
        sumY / count + (hashUnit(id, 2) - 0.5) * jitter,
      ]);
    }
    if (next.length === pending.length) break;
    pending = next;
  }
  for (const id of pending) {
    positions.set(id, [
      centre[0] + (hashUnit(id, 1) - 0.5) * span * 0.05,
      centre[1] + (hashUnit(id, 2) - 0.5) * span * 0.05,
    ]);
  }
  return positions;
}

function openLayoutDb(): Promise<IDBDatabase | null> {
  return new Promise((resolve) => {
    try {
      if (typeof indexedDB === 'undefined') {
        resolve(null);
        return;
      }
      const request = indexedDB.open(DB_NAME, 1);
      request.onupgradeneeded = () => {
        if (!request.result.objectStoreNames.contains(STORE_NAME)) {
          request.result.createObjectStore(STORE_NAME);
        }
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => resolve(null);
      request.onblocked = () => resolve(null);
    } catch {
      resolve(null);
    }
  });
}

async function readCachedLayout(): Promise<AtlasLayoutRecord | null> {
  const db = await openLayoutDb();
  if (!db) return null;
  return new Promise((resolve) => {
    try {
      const request = db.transaction(STORE_NAME, 'readonly').objectStore(STORE_NAME).get(FULL_LAYOUT_KEY);
      request.onsuccess = () => {
        db.close();
        resolve(parseAtlasLayout(request.result));
      };
      request.onerror = () => {
        db.close();
        resolve(null);
      };
    } catch {
      db.close();
      resolve(null);
    }
  });
}

export async function cacheAtlasLayout(record: AtlasLayoutRecord): Promise<void> {
  const db = await openLayoutDb();
  if (!db) return;
  await new Promise<void>((resolve) => {
    try {
      const transaction = db.transaction(STORE_NAME, 'readwrite');
      transaction.objectStore(STORE_NAME).put(serializeAtlasLayout(record), FULL_LAYOUT_KEY);
      transaction.oncomplete = () => resolve();
      transaction.onerror = () => resolve();
      transaction.onabort = () => resolve();
    } catch {
      resolve();
    }
  });
  db.close();
}

async function fetchBundledLayout(): Promise<AtlasLayoutRecord | null> {
  try {
    const { default: url } = await import('../../assets/atlas-full-layout.json?url');
    const response = await fetch(url);
    if (!response.ok) return null;
    return parseAtlasLayout(await response.json());
  } catch {
    return null;
  }
}

/** The bundled layout is authoritative for its own release. A browser-cached
 * live run only wins when it matches the served release and the bundle does
 * not; otherwise a stale bundle is still better than no layout. */
export async function loadAtlasLayout(releaseId: string | null): Promise<AtlasLayoutRecord | null> {
  const bundled = await fetchBundledLayout();
  if (bundled && bundled.ids.length > 0 && bundled.releaseId === releaseId) return bundled;
  const cached = await readCachedLayout();
  if (cached && cached.releaseId === releaseId) return cached;
  return bundled && bundled.ids.length > 0 ? bundled : cached;
}
