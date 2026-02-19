import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { Zap } from 'lucide-react';
import { CitationRenderer } from '../../components/CitationRenderer';
import type { GraphRAGChatMessage } from '../../types';

interface MessageBubbleProps {
  message: GraphRAGChatMessage;
  onNodeClick: (nodeId: string) => void;
  onCitationClick: (citationIndex: number) => void;
}

export default function MessageBubble({ message, onNodeClick, onCitationClick }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.25 }}
      className={isUser ? 'ml-auto max-w-2xl' : 'max-w-full'}
    >
      <div
        className={`rounded-2xl ${
          isUser
            ? 'bg-gradient-to-br from-gray-900 to-gray-800 shadow-md'
            : 'bg-white border border-gray-200 shadow-sm'
        }`}
      >
        <div className={`p-5 ${isUser ? 'text-white' : 'text-gray-900'}`}>
          {isUser ? (
            <p className="text-[15px] leading-relaxed">{message.content}</p>
          ) : (
            <div className="space-y-3">
              {message.graphrag_response?.service && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] font-semibold bg-blue-50 text-blue-600 border border-blue-100">
                  <Zap className="w-3 h-3" />
                  {message.graphrag_response.service}
                </span>
              )}

              {message.graphrag_response?.sources ? (
                <div className="prose prose-sm max-w-none prose-gray">
                  <CitationRenderer
                    content={message.content}
                    sources={message.graphrag_response.sources}
                    onNodeClick={(nodeId) => {
                      const idx = message.graphrag_response!.sources!.findIndex(
                        (s) => s.nodeId === nodeId,
                      );
                      onNodeClick(nodeId);
                      if (idx !== -1) onCitationClick(idx);
                    }}
                  />
                </div>
              ) : (
                <div className="prose prose-sm max-w-none prose-gray">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
              )}
            </div>
          )}

          <div className={`text-[10px] mt-3 ${isUser ? 'text-white/50' : 'text-gray-400'}`}>
            {typeof message.timestamp === 'string'
              ? new Date(message.timestamp).toLocaleTimeString()
              : message.timestamp.toLocaleTimeString()}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
