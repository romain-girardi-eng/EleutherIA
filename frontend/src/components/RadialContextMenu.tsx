import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  GitBranch,
  EyeOff,
  Building2,
  BarChart3,
  MessageSquare,
  Link as LinkIcon,
} from 'lucide-react';
import type { KGNode } from '../types';
import { useToast } from './ui/Toast';

interface RadialContextMenuProps {
  isOpen: boolean;
  position: { x: number; y: number };
  node: KGNode | null;
  onClose: () => void;
  onFindPath?: (sourceNodeId: string) => void;
  onHideNode?: (nodeId: string) => void;
  onFilterBySchool?: (school: string) => void;
  onShowInfluence?: (nodeId: string) => void;
}

interface MenuAction {
  id: string;
  label: string;
  icon: React.ElementType;
  color: string;
  glowColor: string;
  onClick: () => void | Promise<void>;
}

export default function RadialContextMenu({
  isOpen,
  position,
  node,
  onClose,
  onFindPath,
  onHideNode,
  onFilterBySchool,
  onShowInfluence,
}: RadialContextMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const { showToast } = useToast();

  // Calculate orbital positions for menu items
  const calculateOrbitalPosition = (index: number, total: number, radius: number) => {
    // Start at top (-90 degrees) and distribute evenly
    const angleStep = 360 / total;
    const angle = -90 + index * angleStep;
    const radian = (angle * Math.PI) / 180;

    return {
      x: Math.cos(radian) * radius,
      y: Math.sin(radian) * radius,
    };
  };

  // Handle click outside to close
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    // Delay adding listener to avoid immediate close from the right-click event
    const timer = setTimeout(() => {
      document.addEventListener('mousedown', handleClickOutside);
    }, 100);

    return () => {
      clearTimeout(timer);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  // Handle escape key
  useEffect(() => {
    if (!isOpen) return;

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  if (!node) return null;

  // Define menu actions with handlers
  const actions: MenuAction[] = [
    {
      id: 'find-path',
      label: 'Find Path To...',
      icon: GitBranch,
      color: 'bg-violet-500',
      glowColor: 'shadow-violet-500/50',
      onClick: () => {
        if (onFindPath) {
          onFindPath(node.id);
        }
        onClose();
      },
    },
    {
      id: 'hide',
      label: 'Hide from View',
      icon: EyeOff,
      color: 'bg-slate-500',
      glowColor: 'shadow-slate-500/50',
      onClick: () => {
        if (onHideNode) {
          onHideNode(node.id);
        }
        onClose();
      },
    },
    {
      id: 'school',
      label: 'Show Same School',
      icon: Building2,
      color: 'bg-indigo-500',
      glowColor: 'shadow-indigo-500/50',
      onClick: () => {
        console.log('🏫 RadialContextMenu: School filter clicked');
        console.log('🏫 Node data:', { id: node.id, label: node.label, school: node.school });
        if (node.school && node.school !== 'Unknown' && onFilterBySchool) {
          console.log('✅ Calling onFilterBySchool with:', node.school);
          onFilterBySchool(node.school);
        } else {
          console.warn('⚠️ School filter NOT triggered because:', {
            hasSchool: !!node.school,
            school: node.school,
            isUnknown: node.school === 'Unknown',
            hasCallback: !!onFilterBySchool,
          });
        }
        onClose();
      },
    },
    {
      id: 'influence',
      label: 'Analyze Influence',
      icon: BarChart3,
      color: 'bg-emerald-500',
      glowColor: 'shadow-emerald-500/50',
      onClick: () => {
        if (onShowInfluence) {
          onShowInfluence(node.id);
        }
        onClose();
      },
    },
    {
      id: 'graphrag',
      label: 'Ask GraphRAG',
      icon: MessageSquare,
      color: 'bg-orange-500',
      glowColor: 'shadow-orange-500/50',
      onClick: () => {
        navigate('/graphrag', {
          state: {
            initialQuery: `Tell me about ${node.label}${
              node.description ? `: ${node.description}` : ''
            }`,
          },
        });
        onClose();
      },
    },
    {
      id: 'link',
      label: 'Copy Link',
      icon: LinkIcon,
      color: 'bg-cyan-500',
      glowColor: 'shadow-cyan-500/50',
      onClick: async () => {
        const url = `${window.location.origin}/visualizer?nodeId=${node.id}`;
        try {
          await navigator.clipboard.writeText(url);
          showToast('Link copied to clipboard', 'success');
        } catch (error) {
          console.error('Failed to copy link:', error);
          showToast('Failed to copy link to clipboard', 'error');
        }
        onClose();
      },
    },
  ];

  const radius = 90; // Radius of the orbital circle

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          ref={menuRef}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.8 }}
          transition={{ duration: 0.2, ease: 'easeOut' }}
          className="fixed pointer-events-none z-[1000]"
          style={{
            left: position.x,
            top: position.y,
            transform: 'translate(-50%, -50%)',
          }}
        >
          {/* Central node indicator */}
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.1, type: 'spring', stiffness: 200 }}
            className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-4 h-4 rounded-full bg-gradient-to-br from-white to-gray-200 shadow-lg shadow-white/30"
          >
            <div className="absolute inset-0 rounded-full animate-ping bg-white/50"></div>
          </motion.div>

          {/* Orbital ring */}
          <motion.div
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 0.2 }}
            transition={{ delay: 0.05 }}
            className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full border border-white/30"
            style={{
              width: radius * 2,
              height: radius * 2,
            }}
          ></motion.div>

          {/* Menu action items */}
          {actions.map((action, index) => {
            const pos = calculateOrbitalPosition(index, actions.length, radius);
            const Icon = action.icon as React.ElementType;

            return (
              <motion.button
                key={action.id}
                initial={{
                  x: 0,
                  y: 0,
                  scale: 0,
                  opacity: 0,
                }}
                animate={{
                  x: pos.x,
                  y: pos.y,
                  scale: 1,
                  opacity: 1,
                }}
                exit={{
                  x: 0,
                  y: 0,
                  scale: 0,
                  opacity: 0,
                }}
                transition={{
                  delay: index * 0.05,
                  type: 'spring',
                  stiffness: 300,
                  damping: 20,
                }}
                whileHover={{
                  scale: 1.2,
                  transition: { duration: 0.2 },
                }}
                whileTap={{ scale: 0.95 }}
                onClick={action.onClick}
                className={`
                  absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
                  w-14 h-14 rounded-full pointer-events-auto
                  ${action.color} text-white
                  shadow-xl ${action.glowColor}
                  flex items-center justify-center
                  cursor-pointer group
                  backdrop-blur-sm
                  border-2 border-white/20
                  transition-all duration-300
                `}
                title={action.label}
              >
                {React.createElement(Icon, { className: "w-6 h-6" })}

                {/* Label on hover */}
                <motion.span
                  initial={{ opacity: 0, y: 10 }}
                  whileHover={{ opacity: 1, y: 0 }}
                  className="absolute top-full mt-2 px-3 py-1 rounded-full bg-black/90 backdrop-blur-lg text-white text-xs font-medium whitespace-nowrap shadow-lg border border-white/20 pointer-events-none"
                >
                  {action.label}
                </motion.span>
              </motion.button>
            );
          })}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
