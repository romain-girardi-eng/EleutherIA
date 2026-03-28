import { Link } from 'react-router-dom';

interface KGPassageLinkProps {
  passageId: string;
  nodeCount: number;
}

export function KGPassageLink({ passageId, nodeCount }: KGPassageLinkProps) {
  if (nodeCount === 0) return null;

  return (
    <Link
      to={`/visualizer?passage=${passageId}`}
      className="absolute -right-2 top-0.5 w-[18px] h-[18px] rounded-full border border-amber-600/25 flex items-center justify-center text-[9px] text-amber-600 opacity-0 group-hover:opacity-60 hover:!opacity-100 hover:bg-amber-600/10 transition-opacity"
      title={`${nodeCount} nœud${nodeCount > 1 ? 's' : ''} lié${nodeCount > 1 ? 's' : ''}`}
    >
      ⟁
    </Link>
  );
}
