import { Modal } from './ui/Modal';
import type { WorkKGNode } from '../types/index';
import { useNavigate } from 'react-router-dom';

interface KGNodeSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  workTitle: string;
  workAuthor: string;
  nodes: WorkKGNode[];
}

export function KGNodeSelectionModal({
  isOpen,
  onClose,
  workTitle,
  workAuthor,
  nodes
}: KGNodeSelectionModalProps) {
  const navigate = useNavigate();

  const handleNodeClick = (nodeId: string) => {
    // Navigate to visualizer with selected node
    navigate(`/visualizer/${nodeId}`);
    onClose();
  };

  if (nodes.length === 0) {
    return (
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        title="No Knowledge Graph Citations"
        size="md"
      >
        <p className="text-academic-muted">
          This work is not currently cited in any knowledge graph nodes.
        </p>
      </Modal>
    );
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Select Knowledge Graph Node"
      description={`Nodes citing passages from "${workTitle}" by ${workAuthor}`}
      size="lg"
    >
      <div className="space-y-3">
        {nodes.map((node) => (
          <button
            key={node.kg_node_id}
            onClick={() => handleNodeClick(node.kg_node_id)}
            className="w-full text-left academic-card hover:shadow-md transition-shadow cursor-pointer p-4"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <h3 className="font-semibold text-lg mb-1">
                  {node.kg_node_id}
                </h3>
                <div className="flex items-center space-x-4 text-sm text-academic-muted">
                  <span>
                    <strong>{node.citation_count}</strong>{' '}
                    {node.citation_count === 1 ? 'passage' : 'passages'} cited
                  </span>
                </div>
              </div>
              <span className="ml-2 px-2 py-1 bg-primary-100 text-primary-700 rounded-full text-xs font-semibold flex-shrink-0">
                ⭐ {node.citation_count}
              </span>
            </div>

            {/* Show cited passages */}
            {node.canonical_refs && node.canonical_refs.length > 0 && (
              <div className="mt-2 pt-2 border-t border-academic-border">
                <p className="text-xs text-academic-muted mb-1">
                  <strong>Cited Passages:</strong>
                </p>
                <div className="flex flex-wrap gap-1">
                  {node.canonical_refs.slice(0, 5).map((ref, idx) => (
                    <span
                      key={idx}
                      className="text-xs px-2 py-0.5 bg-gray-100 rounded"
                    >
                      {ref}
                    </span>
                  ))}
                  {node.canonical_refs.length > 5 && (
                    <span className="text-xs px-2 py-0.5 bg-gray-100 rounded">
                      +{node.canonical_refs.length - 5} more
                    </span>
                  )}
                </div>
              </div>
            )}

            <div className="mt-3 text-xs text-primary-600 font-medium">
              Click to view in Knowledge Graph →
            </div>
          </button>
        ))}
      </div>
    </Modal>
  );
}
