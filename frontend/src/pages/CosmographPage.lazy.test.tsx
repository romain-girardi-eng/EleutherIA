import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { WorkspaceSurfaceFallback } from './CosmographPage';

function source(relativePath: string) {
  return readFileSync(resolve(process.cwd(), relativePath), 'utf8');
}

describe('multi-mode lazy surface contract', () => {
  it('keeps the WebGL renderer behind the Atlas-only dynamic boundary', () => {
    const shell = source('src/pages/CosmographPage.tsx');
    const loaders = source('src/components/workspace/workspaceLoaders.ts');
    const switcher = source('src/components/canvas/ModeSwitcher.tsx');
    const atlas = source('src/components/workspace/AtlasWorkspace.tsx');
    const chronos = source('src/components/workspace/ChronosWorkspace.tsx');
    const scholar = source('src/components/workspace/ScholarWorkspace.tsx');

    expect(shell).not.toContain("from '@cosmograph/react'");
    expect(shell).toContain('lazy(loadAtlasWorkspace)');
    expect(shell).toContain('lazy(loadChronosWorkspace)');
    expect(shell).toContain('lazy(loadScholarWorkspace)');
    expect(shell).toContain('MountedWorkspaceSurfaces');
    expect(shell).toContain('keep it mounted for the rest of the');
    expect(loaders).toContain("import('./AtlasWorkspace')");
    expect(loaders).toContain("import('./ChronosWorkspace')");
    expect(loaders).toContain("import('./ScholarWorkspace')");
    expect(loaders).not.toContain("from '@cosmograph/react'");
    expect(switcher).toContain('onPointerEnter={() => preloadWorkspace(mode.id)}');
    expect(switcher).toContain('onFocus={() => preloadWorkspace(mode.id)}');
    expect(atlas).toContain("from '@cosmograph/react'");
    expect(chronos).not.toContain('@cosmograph/react');
    expect(scholar).not.toContain('@cosmograph/react');
  });

  it('provides an announced, reduced-motion-safe loading state', () => {
    const { container } = render(
      <WorkspaceSurfaceFallback mode="scholar" phase="surface" />,
    );

    expect(screen.getByRole('status')).toHaveAccessibleName('Opening Scholar…');
    const spinner = container.querySelector('svg');
    expect(spinner).toHaveClass('motion-safe:animate-spin');
    expect(spinner).not.toHaveClass('animate-spin');
  });

  it('keeps keyboard focus visible and tablet chrome clear of the mode switcher', () => {
    const styles = source('src/index.css');
    const chrome = source('src/components/workspace/GraphWorkspaceChrome.tsx');

    expect(styles).toContain(':focus:not(:focus-visible)');
    expect(styles).not.toContain('*:focus-visible');
    expect(styles).not.toContain('--tw-ring-color: transparent !important');
    expect(chrome).toContain("text-[11px] xl:flex");
    expect(chrome).not.toContain("text-[11px] lg:flex");
  });
});
