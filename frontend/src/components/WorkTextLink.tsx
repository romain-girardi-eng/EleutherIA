import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText } from 'lucide-react';
import { apiClient } from '../api/client';

interface WorkTextLinkProps {
  nodeId: string;
  nodeType: string;
  nodeLabel: string;
  className?: string;
  compact?: boolean;
}

/**
 * Component that checks if a KG work node has a linked text and displays a link to it
 */
export function WorkTextLink({ nodeId, nodeType, nodeLabel, className = '', compact = false }: WorkTextLinkProps) {
  const [textId, setTextId] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Only check for linked works if this is a work node
    if (nodeType === 'work') {
      setChecking(true);
      // Use the new works API - work nodes now directly reference work_id
      apiClient.getWork(nodeId)
        .then((work) => {
          if (work) {
            setTextId(work.work_id);
          }
        })
        .catch((error) => {
          console.error('Error checking for linked work:', error);
        })
        .finally(() => {
          setChecking(false);
        });
    }
  }, [nodeId, nodeType]);

  // Don't render anything if not a work node
  if (nodeType !== 'work') {
    return null;
  }

  // Show loading state
  if (checking) {
    return compact ? (
      <span className={`text-xs text-gray-400 ${className}`}>...</span>
    ) : (
      <div className={`text-xs text-gray-400 ${className}`}>Checking for text...</div>
    );
  }

  // Show link if text exists
  if (textId) {
    return (
      <button
        onClick={(e) => {
          e.stopPropagation();
          navigate(`/texts/${textId}`);
        }}
        className={`inline-flex items-center gap-1 text-primary-600 hover:text-primary-700 transition-colors ${className}`}
        title={`Read ${nodeLabel} in full text viewer`}
        aria-label={`Read ${nodeLabel}`}
      >
        <FileText className={compact ? 'w-3 h-3' : 'w-4 h-4'} />
        {!compact && <span className="text-xs">Open Text</span>}
      </button>
    );
  }

  // No text available - optionally show a message for non-compact mode
  if (!compact) {
    return (
      <span className={`text-xs text-gray-400 ${className}`}>
        Text not available
      </span>
    );
  }

  return null;
}
