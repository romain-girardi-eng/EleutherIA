import { act, createRef, forwardRef, memo } from 'react';
import { render } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { CosmographRef } from '@cosmograph/react';

const { cosmographRender } = vi.hoisted(() => ({
  cosmographRender: vi.fn(),
}));

vi.mock('@cosmograph/react', () => ({
  Cosmograph: memo(forwardRef((props, _ref) => {
    cosmographRender(props);
    return <div data-testid="cosmograph" />;
  })),
}));

import StableCosmographCanvas, {
  type StableCosmographHandlers,
} from './StableCosmographCanvas';

function handlers(): StableCosmographHandlers {
  return {
    onMount: vi.fn(),
    onGraphRebuilt: vi.fn(),
    onSimulationStart: vi.fn(),
    onSimulationUnpause: vi.fn(),
    onSimulationPause: vi.fn(),
    onSimulationEnd: vi.fn(),
    onZoom: vi.fn(),
    onPointClick: vi.fn(),
    onLabelClick: vi.fn(),
    onBackgroundClick: vi.fn(),
  };
}

describe('StableCosmographCanvas', () => {
  beforeEach(() => cosmographRender.mockClear());

  it('does not reconfigure WebGL for workspace-only renders', () => {
    const graphRef = createRef<CosmographRef>();
    const revision = {};
    const firstHandlers = handlers();
    const secondHandlers = handlers();
    const view = render(
      <StableCosmographCanvas
        config={{ backgroundColor: '#fffdf9' }}
        revision={revision}
        graphRef={graphRef}
        handlers={firstHandlers}
      />,
    );
    const stableOnZoom = cosmographRender.mock.calls[0][0].onZoom;
    const stableOnGraphRebuilt = cosmographRender.mock.calls[0][0].onGraphRebuilt;

    view.rerender(
      <StableCosmographCanvas
        config={{ backgroundColor: '#000000' }}
        revision={revision}
        graphRef={graphRef}
        handlers={secondHandlers}
      />,
    );

    expect(cosmographRender).toHaveBeenCalledTimes(1);
    expect(cosmographRender.mock.calls[0][0].backgroundColor).toBe('#fffdf9');
    act(() => stableOnZoom({ k: 2, x: 1, y: 1 }));
    expect(firstHandlers.onZoom).not.toHaveBeenCalled();
    expect(secondHandlers.onZoom).toHaveBeenCalledOnce();
    act(() => stableOnGraphRebuilt({ pointsCount: 2, linksCount: 1 }));
    expect(firstHandlers.onGraphRebuilt).not.toHaveBeenCalled();
    expect(secondHandlers.onGraphRebuilt).toHaveBeenCalledOnce();
  });

  it('reconfigures one persistent instance for a real renderer revision', () => {
    const graphRef = createRef<CosmographRef>();
    const stableHandlers = handlers();
    const view = render(
      <StableCosmographCanvas
        config={{ backgroundColor: '#fffdf9' }}
        revision={{ release: 'one' }}
        graphRef={graphRef}
        handlers={stableHandlers}
      />,
    );
    const firstCanvas = view.getByTestId('cosmograph');

    view.rerender(
      <StableCosmographCanvas
        config={{ backgroundColor: '#000000' }}
        revision={{ release: 'two' }}
        graphRef={graphRef}
        handlers={stableHandlers}
      />,
    );

    expect(cosmographRender).toHaveBeenCalledTimes(2);
    expect(cosmographRender.mock.calls[1][0].backgroundColor).toBe('#000000');
    expect(view.getByTestId('cosmograph')).toBe(firstCanvas);
  });
});
