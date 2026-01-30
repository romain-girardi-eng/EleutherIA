/**
 * Spatial Partitioning Utilities for O(n log n) Force Simulation
 *
 * Implements Barnes-Hut algorithm via Quadtree for 2D and Octree for 3D
 * Reduces force calculations from O(n²) to O(n log n)
 */

export interface Point2D {
  x: number;
  y: number;
}

export interface Point3D extends Point2D {
  z: number;
}

export interface QuadTreeNode<T extends Point2D> {
  bounds: { x: number; y: number; width: number; height: number };
  points: T[];
  children: QuadTreeNode<T>[] | null;
  centerOfMass: Point2D;
  totalMass: number;
}

const MAX_POINTS_PER_NODE = 4;
const THETA = 0.3; // Barnes-Hut threshold (lower = more accurate, higher = faster)
// 0.3 = high quality (visually perfect), 0.5 = standard, 0.7 = fast but approximate

/**
 * QuadTree for 2D spatial partitioning
 * Used by CosmicKGVisualizer for O(n log n) force calculations
 */
export class QuadTree<T extends Point2D & { mass?: number }> {
  private root: QuadTreeNode<T>;

  constructor(bounds: { x: number; y: number; width: number; height: number }) {
    this.root = this.createNode(bounds);
  }

  private createNode(bounds: QuadTreeNode<T>['bounds']): QuadTreeNode<T> {
    return {
      bounds,
      points: [],
      children: null,
      centerOfMass: { x: 0, y: 0 },
      totalMass: 0,
    };
  }

  /**
   * Insert a point into the quadtree
   */
  insert(point: T): void {
    this.insertIntoNode(this.root, point);
  }

  private insertIntoNode(node: QuadTreeNode<T>, point: T): void {
    // Update center of mass
    const mass = point.mass ?? 1;
    const totalMass = node.totalMass + mass;
    node.centerOfMass.x = (node.centerOfMass.x * node.totalMass + point.x * mass) / totalMass;
    node.centerOfMass.y = (node.centerOfMass.y * node.totalMass + point.y * mass) / totalMass;
    node.totalMass = totalMass;

    // If no children and under capacity, add to this node
    if (!node.children && node.points.length < MAX_POINTS_PER_NODE) {
      node.points.push(point);
      return;
    }

    // Subdivide if needed
    if (!node.children) {
      this.subdivide(node);
    }

    // Insert into appropriate child
    const childIndex = this.getChildIndex(node, point);
    this.insertIntoNode(node.children![childIndex], point);
  }

  private subdivide(node: QuadTreeNode<T>): void {
    const { x, y, width, height } = node.bounds;
    const halfW = width / 2;
    const halfH = height / 2;

    node.children = [
      this.createNode({ x, y, width: halfW, height: halfH }), // NW
      this.createNode({ x: x + halfW, y, width: halfW, height: halfH }), // NE
      this.createNode({ x, y: y + halfH, width: halfW, height: halfH }), // SW
      this.createNode({ x: x + halfW, y: y + halfH, width: halfW, height: halfH }), // SE
    ];

    // Re-insert existing points into children
    for (const point of node.points) {
      const childIndex = this.getChildIndex(node, point);
      this.insertIntoNode(node.children[childIndex], point);
    }
    node.points = [];
  }

  private getChildIndex(node: QuadTreeNode<T>, point: Point2D): number {
    const midX = node.bounds.x + node.bounds.width / 2;
    const midY = node.bounds.y + node.bounds.height / 2;
    const isRight = point.x >= midX;
    const isBottom = point.y >= midY;
    return (isRight ? 1 : 0) + (isBottom ? 2 : 0);
  }

  /**
   * Calculate force on a point using Barnes-Hut approximation
   * Returns { fx, fy } force vector
   */
  calculateForce(
    point: T,
    repulsionStrength: number,
    minDistance: number = 1
  ): { fx: number; fy: number } {
    return this.calculateForceFromNode(this.root, point, repulsionStrength, minDistance);
  }

  private calculateForceFromNode(
    node: QuadTreeNode<T>,
    point: T,
    repulsionStrength: number,
    minDistance: number
  ): { fx: number; fy: number } {
    if (node.totalMass === 0) {
      return { fx: 0, fy: 0 };
    }

    const dx = point.x - node.centerOfMass.x;
    const dy = point.y - node.centerOfMass.y;
    const distSq = dx * dx + dy * dy;
    const dist = Math.sqrt(distSq) || minDistance;

    // If node is far enough, treat as single body (Barnes-Hut approximation)
    const nodeSize = Math.max(node.bounds.width, node.bounds.height);
    if (!node.children || nodeSize / dist < THETA) {
      // Skip self-interaction
      if (distSq < 0.01) return { fx: 0, fy: 0 };

      const effectiveDist = Math.max(dist, minDistance);
      const force = (repulsionStrength * node.totalMass) / (effectiveDist * effectiveDist);
      return {
        fx: (dx / dist) * force,
        fy: (dy / dist) * force,
      };
    }

    // Otherwise, recursively calculate from children
    let fx = 0;
    let fy = 0;
    for (const child of node.children) {
      const childForce = this.calculateForceFromNode(child, point, repulsionStrength, minDistance);
      fx += childForce.fx;
      fy += childForce.fy;
    }
    return { fx, fy };
  }

  /**
   * Bulk insert for better performance
   */
  static fromPoints<T extends Point2D & { mass?: number }>(
    points: T[],
    padding: number = 50
  ): QuadTree<T> {
    if (points.length === 0) {
      return new QuadTree({ x: 0, y: 0, width: 100, height: 100 });
    }

    // Calculate bounds
    let minX = Infinity, maxX = -Infinity;
    let minY = Infinity, maxY = -Infinity;

    for (const p of points) {
      minX = Math.min(minX, p.x);
      maxX = Math.max(maxX, p.x);
      minY = Math.min(minY, p.y);
      maxY = Math.max(maxY, p.y);
    }

    const bounds = {
      x: minX - padding,
      y: minY - padding,
      width: maxX - minX + padding * 2,
      height: maxY - minY + padding * 2,
    };

    const tree = new QuadTree<T>(bounds);
    for (const point of points) {
      tree.insert(point);
    }
    return tree;
  }
}

/**
 * Octree for 3D spatial partitioning
 * Used by Semativerse3D for O(n log n) force calculations
 */
export interface OctreeNode<T extends Point3D> {
  bounds: { x: number; y: number; z: number; size: number };
  points: T[];
  children: OctreeNode<T>[] | null;
  centerOfMass: Point3D;
  totalMass: number;
}

export class Octree<T extends Point3D & { mass?: number }> {
  private root: OctreeNode<T>;

  constructor(bounds: { x: number; y: number; z: number; size: number }) {
    this.root = this.createNode(bounds);
  }

  private createNode(bounds: OctreeNode<T>['bounds']): OctreeNode<T> {
    return {
      bounds,
      points: [],
      children: null,
      centerOfMass: { x: 0, y: 0, z: 0 },
      totalMass: 0,
    };
  }

  insert(point: T): void {
    this.insertIntoNode(this.root, point);
  }

  private insertIntoNode(node: OctreeNode<T>, point: T): void {
    const mass = point.mass ?? 1;
    const totalMass = node.totalMass + mass;
    node.centerOfMass.x = (node.centerOfMass.x * node.totalMass + point.x * mass) / totalMass;
    node.centerOfMass.y = (node.centerOfMass.y * node.totalMass + point.y * mass) / totalMass;
    node.centerOfMass.z = (node.centerOfMass.z * node.totalMass + point.z * mass) / totalMass;
    node.totalMass = totalMass;

    if (!node.children && node.points.length < MAX_POINTS_PER_NODE) {
      node.points.push(point);
      return;
    }

    if (!node.children) {
      this.subdivide(node);
    }

    const childIndex = this.getChildIndex(node, point);
    this.insertIntoNode(node.children![childIndex], point);
  }

  private subdivide(node: OctreeNode<T>): void {
    const { x, y, z, size } = node.bounds;
    const halfSize = size / 2;

    node.children = [];
    for (let i = 0; i < 8; i++) {
      const ox = (i & 1) ? halfSize : 0;
      const oy = (i & 2) ? halfSize : 0;
      const oz = (i & 4) ? halfSize : 0;
      node.children.push(this.createNode({
        x: x + ox,
        y: y + oy,
        z: z + oz,
        size: halfSize,
      }));
    }

    for (const point of node.points) {
      const childIndex = this.getChildIndex(node, point);
      this.insertIntoNode(node.children[childIndex], point);
    }
    node.points = [];
  }

  private getChildIndex(node: OctreeNode<T>, point: Point3D): number {
    const mid = node.bounds.size / 2;
    const isRight = point.x >= node.bounds.x + mid ? 1 : 0;
    const isTop = point.y >= node.bounds.y + mid ? 2 : 0;
    const isFront = point.z >= node.bounds.z + mid ? 4 : 0;
    return isRight | isTop | isFront;
  }

  calculateForce(
    point: T,
    repulsionStrength: number,
    minDistance: number = 1
  ): { fx: number; fy: number; fz: number } {
    return this.calculateForceFromNode(this.root, point, repulsionStrength, minDistance);
  }

  private calculateForceFromNode(
    node: OctreeNode<T>,
    point: T,
    repulsionStrength: number,
    minDistance: number
  ): { fx: number; fy: number; fz: number } {
    if (node.totalMass === 0) {
      return { fx: 0, fy: 0, fz: 0 };
    }

    const dx = point.x - node.centerOfMass.x;
    const dy = point.y - node.centerOfMass.y;
    const dz = point.z - node.centerOfMass.z;
    const distSq = dx * dx + dy * dy + dz * dz;
    const dist = Math.sqrt(distSq) || minDistance;

    if (!node.children || node.bounds.size / dist < THETA) {
      if (distSq < 0.01) return { fx: 0, fy: 0, fz: 0 };

      const effectiveDist = Math.max(dist, minDistance);
      const force = (repulsionStrength * node.totalMass) / (effectiveDist * effectiveDist);
      return {
        fx: (dx / dist) * force,
        fy: (dy / dist) * force,
        fz: (dz / dist) * force,
      };
    }

    let fx = 0, fy = 0, fz = 0;
    for (const child of node.children) {
      const childForce = this.calculateForceFromNode(child, point, repulsionStrength, minDistance);
      fx += childForce.fx;
      fy += childForce.fy;
      fz += childForce.fz;
    }
    return { fx, fy, fz };
  }

  static fromPoints<T extends Point3D & { mass?: number }>(
    points: T[],
    padding: number = 50
  ): Octree<T> {
    if (points.length === 0) {
      return new Octree({ x: 0, y: 0, z: 0, size: 100 });
    }

    let minX = Infinity, maxX = -Infinity;
    let minY = Infinity, maxY = -Infinity;
    let minZ = Infinity, maxZ = -Infinity;

    for (const p of points) {
      minX = Math.min(minX, p.x);
      maxX = Math.max(maxX, p.x);
      minY = Math.min(minY, p.y);
      maxY = Math.max(maxY, p.y);
      minZ = Math.min(minZ, p.z);
      maxZ = Math.max(maxZ, p.z);
    }

    const size = Math.max(maxX - minX, maxY - minY, maxZ - minZ) + padding * 2;

    const tree = new Octree<T>({
      x: minX - padding,
      y: minY - padding,
      z: minZ - padding,
      size,
    });

    for (const point of points) {
      tree.insert(point);
    }
    return tree;
  }
}

/**
 * Pre-computed color palette to avoid string allocation in hot loops
 */
export class ColorCache {
  private cache = new Map<string, string[]>();

  /**
   * Pre-compute color variations at different intensities
   */
  precompute(baseColor: string, steps: number = 10): string[] {
    if (this.cache.has(baseColor)) {
      return this.cache.get(baseColor)!;
    }

    const variations: string[] = [];
    // Parse rgba(r, g, b, a) or hex
    const match = baseColor.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);

    if (match) {
      const [, r, g, b] = match.map(Number);
      for (let i = 0; i <= steps; i++) {
        const intensity = i / steps;
        variations.push(`rgba(${r}, ${g}, ${b}, ${intensity.toFixed(2)})`);
      }
    } else {
      // Fallback: just return the original
      for (let i = 0; i <= steps; i++) {
        variations.push(baseColor);
      }
    }

    this.cache.set(baseColor, variations);
    return variations;
  }

  /**
   * Get color at specific intensity (0-1)
   */
  get(baseColor: string, intensity: number): string {
    const variations = this.precompute(baseColor);
    const index = Math.round(intensity * (variations.length - 1));
    return variations[Math.max(0, Math.min(index, variations.length - 1))];
  }
}

/**
 * Object pool for particles to avoid GC pressure
 */
export class ParticlePool<T> {
  private pool: T[] = [];
  private factory: () => T;
  private reset: (item: T) => void;

  constructor(factory: () => T, reset: (item: T) => void, initialSize: number = 100) {
    this.factory = factory;
    this.reset = reset;

    // Pre-allocate pool
    for (let i = 0; i < initialSize; i++) {
      this.pool.push(factory());
    }
  }

  acquire(): T {
    if (this.pool.length > 0) {
      return this.pool.pop()!;
    }
    return this.factory();
  }

  release(item: T): void {
    this.reset(item);
    this.pool.push(item);
  }

  get size(): number {
    return this.pool.length;
  }
}
