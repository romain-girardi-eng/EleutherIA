import type { GraphWorkspaceMode } from '../../context/GraphWorkspaceContext';

export const loadAtlasWorkspace = () => import('./AtlasWorkspace');
export const loadChronosWorkspace = () => import('./ChronosWorkspace');
export const loadScholarWorkspace = () => import('./ScholarWorkspace');

/** Start fetching a mode chunk on deliberate user intent, before activation. */
export function preloadWorkspace(mode: GraphWorkspaceMode): void {
  if (mode === 'chronos') {
    void loadChronosWorkspace();
  } else if (mode === 'scholar') {
    void loadScholarWorkspace();
  } else {
    void loadAtlasWorkspace();
  }
}
