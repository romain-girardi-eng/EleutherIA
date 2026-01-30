/**
 * Type declarations for d3-force-3d
 * 3D force simulation extending d3-force
 */

declare module 'd3-force-3d' {
  import { Simulation, SimulationNodeDatum, SimulationLinkDatum } from 'd3-force';

  export interface Node3D extends SimulationNodeDatum {
    x?: number;
    y?: number;
    z?: number;
    vx?: number;
    vy?: number;
    vz?: number;
    fx?: number | null;
    fy?: number | null;
    fz?: number | null;
  }

  export interface Link3D<NodeType extends Node3D = Node3D> extends SimulationLinkDatum<NodeType> {
    source: string | NodeType;
    target: string | NodeType;
  }

  export function forceSimulation<NodeType extends Node3D = Node3D>(
    nodes?: NodeType[]
  ): Simulation<NodeType, undefined>;

  export function forceManyBody<NodeType extends Node3D = Node3D>(): {
    (alpha: number): void;
    initialize: (nodes: NodeType[]) => void;
    strength: {
      (): number | ((d: NodeType, i: number, data: NodeType[]) => number);
      (value: number | ((d: NodeType, i: number, data: NodeType[]) => number)): ReturnType<typeof forceManyBody>;
    };
    distanceMin: {
      (): number;
      (value: number): ReturnType<typeof forceManyBody>;
    };
    distanceMax: {
      (): number;
      (value: number): ReturnType<typeof forceManyBody>;
    };
    theta: {
      (): number;
      (value: number): ReturnType<typeof forceManyBody>;
    };
  };

  export function forceLink<
    NodeType extends Node3D = Node3D,
    LinkType extends Link3D<NodeType> = Link3D<NodeType>
  >(
    links?: LinkType[]
  ): {
    (alpha: number): void;
    initialize: (nodes: NodeType[]) => void;
    links: {
      (): LinkType[];
      (links: LinkType[]): ReturnType<typeof forceLink>;
    };
    id: {
      (): (node: NodeType) => string;
      (id: (node: NodeType) => string): ReturnType<typeof forceLink>;
    };
    distance: {
      (): number | ((link: LinkType, i: number, links: LinkType[]) => number);
      (value: number | ((link: LinkType, i: number, links: LinkType[]) => number)): ReturnType<typeof forceLink>;
    };
    strength: {
      (): number | ((link: LinkType, i: number, links: LinkType[]) => number);
      (value: number | ((link: LinkType, i: number, links: LinkType[]) => number)): ReturnType<typeof forceLink>;
    };
    iterations: {
      (): number;
      (value: number): ReturnType<typeof forceLink>;
    };
  };

  export function forceCenter<NodeType extends Node3D = Node3D>(
    x?: number,
    y?: number,
    z?: number
  ): {
    (alpha: number): void;
    initialize: (nodes: NodeType[]) => void;
    x: {
      (): number;
      (value: number): ReturnType<typeof forceCenter>;
    };
    y: {
      (): number;
      (value: number): ReturnType<typeof forceCenter>;
    };
    z: {
      (): number;
      (value: number): ReturnType<typeof forceCenter>;
    };
    strength: {
      (): number;
      (value: number): ReturnType<typeof forceCenter>;
    };
  };

  export function forceCollide<NodeType extends Node3D = Node3D>(
    radius?: number | ((node: NodeType) => number)
  ): {
    (alpha: number): void;
    initialize: (nodes: NodeType[]) => void;
    radius: {
      (): number | ((node: NodeType) => number);
      (value: number | ((node: NodeType) => number)): ReturnType<typeof forceCollide>;
    };
    strength: {
      (): number;
      (value: number): ReturnType<typeof forceCollide>;
    };
    iterations: {
      (): number;
      (value: number): ReturnType<typeof forceCollide>;
    };
  };

  export function forceX<NodeType extends Node3D = Node3D>(
    x?: number | ((node: NodeType) => number)
  ): {
    (alpha: number): void;
    initialize: (nodes: NodeType[]) => void;
    x: {
      (): number | ((node: NodeType) => number);
      (value: number | ((node: NodeType) => number)): ReturnType<typeof forceX>;
    };
    strength: {
      (): number | ((node: NodeType) => number);
      (value: number | ((node: NodeType) => number)): ReturnType<typeof forceX>;
    };
  };

  export function forceY<NodeType extends Node3D = Node3D>(
    y?: number | ((node: NodeType) => number)
  ): {
    (alpha: number): void;
    initialize: (nodes: NodeType[]) => void;
    y: {
      (): number | ((node: NodeType) => number);
      (value: number | ((node: NodeType) => number)): ReturnType<typeof forceY>;
    };
    strength: {
      (): number | ((node: NodeType) => number);
      (value: number | ((node: NodeType) => number)): ReturnType<typeof forceY>;
    };
  };

  export function forceZ<NodeType extends Node3D = Node3D>(
    z?: number | ((node: NodeType) => number)
  ): {
    (alpha: number): void;
    initialize: (nodes: NodeType[]) => void;
    z: {
      (): number | ((node: NodeType) => number);
      (value: number | ((node: NodeType) => number)): ReturnType<typeof forceZ>;
    };
    strength: {
      (): number | ((node: NodeType) => number);
      (value: number | ((node: NodeType) => number)): ReturnType<typeof forceZ>;
    };
  };

  export function forceRadial<NodeType extends Node3D = Node3D>(
    radius?: number | ((node: NodeType) => number),
    x?: number,
    y?: number,
    z?: number
  ): {
    (alpha: number): void;
    initialize: (nodes: NodeType[]) => void;
    radius: {
      (): number | ((node: NodeType) => number);
      (value: number | ((node: NodeType) => number)): ReturnType<typeof forceRadial>;
    };
    x: {
      (): number;
      (value: number): ReturnType<typeof forceRadial>;
    };
    y: {
      (): number;
      (value: number): ReturnType<typeof forceRadial>;
    };
    z: {
      (): number;
      (value: number): ReturnType<typeof forceRadial>;
    };
    strength: {
      (): number | ((node: NodeType) => number);
      (value: number | ((node: NodeType) => number)): ReturnType<typeof forceRadial>;
    };
  };
}
