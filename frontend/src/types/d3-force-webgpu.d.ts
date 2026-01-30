/* eslint-disable @typescript-eslint/no-explicit-any */
declare module 'd3-force-webgpu' {
  export interface ForceNode {
    index?: number;
    x?: number;
    y?: number;
    vx?: number;
    vy?: number;
    fx?: number | null;
    fy?: number | null;
    [key: string]: any;
  }

  export interface ForceLink<NodeType extends ForceNode = ForceNode> {
    source: NodeType | string | number;
    target: NodeType | string | number;
    index?: number;
    [key: string]: any;
  }

  export interface Simulation<NodeType extends ForceNode = ForceNode, _LinkType extends ForceLink<NodeType> = ForceLink<NodeType>> {
    nodes(nodes?: NodeType[]): this;
    force(name: string, force?: any): this;
    alpha(alpha?: number): this;
    alphaTarget(target?: number): this;
    alphaDecay(decay?: number): this;
    velocityDecay(decay?: number): this;
    tick(iterations?: number): this;
    restart(): this;
    stop(): this;
    on(type: string, listener: ((event: any) => void) | null): this;
  }

  export function forceSimulation<NodeType extends ForceNode = ForceNode>(
    nodes?: NodeType[]
  ): Simulation<NodeType, ForceLink<NodeType>>;

  export function forceLink<LinkType = any>(
    links?: LinkType[]
  ): {
    id(id: (d: any) => string | number): any;
    distance(distance: number | ((d: any) => number)): any;
    strength(strength: number | ((d: any) => number)): any;
    links(links?: LinkType[]): any;
  };

  export function forceManyBody(): {
    strength(strength: number | ((d: any, i: number) => number)): any;
    distanceMin(distance: number): any;
    distanceMax(distance: number): any;
    theta(theta: number): any;
  };

  export function forceCenter(x?: number, y?: number): any;

  export function forceCollide<NodeType = any>(radius?: number | ((d: NodeType) => number)): {
    radius(radius: number | ((d: NodeType) => number)): any;
    strength(strength: number): any;
    iterations(iterations: number): any;
  };

  export function forceX<NodeType = any>(x?: number | ((d: NodeType) => number)): {
    x(x: number | ((d: NodeType) => number)): any;
    strength(strength: number | ((d: NodeType) => number)): any;
  };

  export function forceY<NodeType = any>(y?: number | ((d: NodeType) => number)): {
    y(y: number | ((d: NodeType) => number)): any;
    strength(strength: number | ((d: NodeType) => number)): any;
  };
}
