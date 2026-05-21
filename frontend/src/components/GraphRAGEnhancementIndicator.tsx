import { Badge } from './ui/badge';
import { Info, Zap, GitBranch, Users, Link2 } from 'lucide-react';
import { useKgStats, formatCount } from '../hooks/useKgStats';

interface GraphRAGEnhancementIndicatorProps {
  enhancements?: {
    mode: 'original' | 'enhanced';
    relationship_types_used?: number;
    debates_found?: number;
    influence_chains?: number;
  };
  className?: string;
}

export function GraphRAGEnhancementIndicator({
  enhancements,
  className = '',
}: GraphRAGEnhancementIndicatorProps) {
  const stats = useKgStats();
  const edgeTypeCount = Object.keys(stats.edgeTypes).length || Number.NaN;
  if (!enhancements || enhancements.mode === 'original') {
    return null;
  }

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <Badge
        variant="secondary"
        className="flex items-center gap-1 bg-gradient-to-r from-purple-500/10 to-blue-500/10 text-purple-700 dark:text-purple-300"
        title={`Using ULTRA-ENHANCED GraphRAG with edge relationships - Leverages ${formatCount(stats.edges)} edges with ${formatCount(edgeTypeCount)} relationship types`}
      >
        <Zap className="h-3 w-3" />
        Enhanced Mode
      </Badge>

      {enhancements.relationship_types_used && enhancements.relationship_types_used > 0 && (
        <Badge
          variant="outline"
          className="flex items-center gap-1"
          title={`${enhancements.relationship_types_used} unique relationship types used - Includes: criticized, influenced, refuted, etc.`}
        >
          <Link2 className="h-3 w-3" />
          {enhancements.relationship_types_used} relationships
        </Badge>
      )}

      {enhancements.debates_found && enhancements.debates_found > 0 && (
        <Badge
          variant="outline"
          className="flex items-center gap-1 text-red-600 dark:text-red-400"
          title={`${enhancements.debates_found} philosophical debates identified - Conflicts and disagreements between philosophers`}
        >
          <Users className="h-3 w-3" />
          {enhancements.debates_found} debates
        </Badge>
      )}

      {enhancements.influence_chains && enhancements.influence_chains > 0 && (
        <Badge
          variant="outline"
          className="flex items-center gap-1 text-blue-600 dark:text-blue-400"
          title={`${enhancements.influence_chains} influence chains traced - How ideas spread across schools and time`}
        >
          <GitBranch className="h-3 w-3" />
          {enhancements.influence_chains} influences
        </Badge>
      )}
    </div>
  );
}

export function GraphRAGModeToggle({
  enhanced,
  onToggle,
  className = '',
}: {
  enhanced: boolean;
  onToggle: (enhanced: boolean) => void;
  className?: string;
}) {
  const stats = useKgStats();
  const edgeTypeCount = Object.keys(stats.edgeTypes).length || Number.NaN;
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={enhanced}
          onChange={(e) => onToggle(e.target.checked)}
          className="w-4 h-4 text-purple-600 bg-gray-100 border-gray-300 rounded focus:ring-purple-500 dark:focus:ring-purple-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
        />
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Enhanced Mode
        </span>
      </label>

      <div
        className="inline-block"
        title={`🚀 ULTRA-ENHANCED GraphRAG - Enhanced mode leverages all ${formatCount(stats.edges)} edges with ${formatCount(edgeTypeCount)} relationship types to provide: ⚔️ Philosophical debate identification, 💫 Influence chain tracking, 🔨 Argument network mapping, 💬 Rich relationship context. Results in dramatically richer, more accurate philosophical understanding.`}
      >
        <Info className="h-4 w-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 cursor-help" />
      </div>
    </div>
  );
}
