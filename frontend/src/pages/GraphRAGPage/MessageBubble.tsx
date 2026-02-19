import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { Zap, BookOpen, ChevronDown, ChevronUp, Clock, Cpu, FileText, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { CitationRenderer, SourcesPanel } from '../../components/CitationRenderer';
import type { GraphRAGChatMessage } from '../../types';

interface MessageBubbleProps {
  message: GraphRAGChatMessage;
  onNodeClick: (nodeId: string) => void;
  onCitationClick: (citationIndex: number) => void;
}

export default function MessageBubble({ message, onNodeClick, onCitationClick }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const navigate = useNavigate();
  const [showSources, setShowSources] = useState(false);
  const [showPassages, setShowPassages] = useState(false);
  const [expandedPassage, setExpandedPassage] = useState<number | null>(null);

  const resp = message.graphrag_response;
  const verifiedPassages = resp?.verified_passages;
  const sources = resp?.sources;
  const processingTime = resp?.processing_time;
  const tokensUsed = message.tokens_used;
  const llmModel = message.llm_model;
  const nodesUsed = resp?.nodes_used;
  const edgesTraversed = resp?.edges_traversed;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.25 }}
      className={isUser ? 'ml-auto max-w-2xl xl:max-w-3xl' : 'max-w-full'}
    >
      <div
        className={`rounded-2xl ${
          isUser
            ? 'bg-gradient-to-br from-gray-900 to-gray-800 shadow-md'
            : 'bg-white border border-gray-200 shadow-sm'
        }`}
      >
        <div className={`p-5 xl:p-7 ${isUser ? 'text-white' : 'text-gray-900'}`}>
          {isUser ? (
            <p className="text-[15px] xl:text-base 2xl:text-lg leading-relaxed">{message.content}</p>
          ) : (
            <div className="space-y-4">
              {/* Service badge + metadata row */}
              <div className="flex flex-wrap items-center gap-2">
                {resp?.service && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] xl:text-xs font-semibold bg-blue-50 text-blue-600 border border-blue-100">
                    <Zap className="w-3 h-3 xl:w-3.5 xl:h-3.5" />
                    {resp.service}
                  </span>
                )}
                {llmModel && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] xl:text-xs font-medium bg-gray-50 text-gray-500 border border-gray-100">
                    <Cpu className="w-3 h-3" />
                    {llmModel}
                  </span>
                )}
                {processingTime && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] xl:text-xs font-medium bg-gray-50 text-gray-500 border border-gray-100">
                    <Clock className="w-3 h-3" />
                    {(processingTime / 1000).toFixed(1)}s
                  </span>
                )}
                {nodesUsed !== undefined && (
                  <span className="text-[10px] xl:text-xs text-gray-400">
                    {nodesUsed} nodes, {edgesTraversed ?? 0} edges
                  </span>
                )}
                {tokensUsed !== undefined && (
                  <span className="text-[10px] xl:text-xs text-gray-400">
                    {tokensUsed.toLocaleString()} tokens
                  </span>
                )}
              </div>

              {/* Main answer content */}
              {sources && sources.length > 0 ? (
                <div className="prose prose-sm xl:prose-base max-w-none prose-gray">
                  <CitationRenderer
                    content={message.content}
                    sources={sources}
                    onNodeClick={(nodeId) => {
                      const idx = sources.findIndex((s) => s.nodeId === nodeId);
                      onNodeClick(nodeId);
                      if (idx !== -1) onCitationClick(idx);
                    }}
                  />
                </div>
              ) : (
                <div className="prose prose-sm xl:prose-base max-w-none prose-gray">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
              )}

              {/* Verified Passages (clickable original texts) */}
              {verifiedPassages && verifiedPassages.length > 0 && (
                <div className="border-t border-gray-100 pt-3">
                  <button
                    onClick={() => setShowPassages(!showPassages)}
                    className="flex items-center gap-2 text-sm xl:text-base font-medium text-gray-700 hover:text-gray-900 transition-colors w-full"
                  >
                    <BookOpen className="w-4 h-4" />
                    <span>Verified Passages ({verifiedPassages.length})</span>
                    {showPassages ? <ChevronUp className="w-4 h-4 ml-auto" /> : <ChevronDown className="w-4 h-4 ml-auto" />}
                  </button>

                  <AnimatePresence>
                    {showPassages && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                      >
                        <div className="mt-3 space-y-2">
                          {verifiedPassages.map((passage, idx) => (
                            <div
                              key={passage.passage_id}
                              className="rounded-lg border border-gray-100 bg-gray-50/50 overflow-hidden"
                            >
                              {/* Passage header - always visible, clickable */}
                              <button
                                onClick={() => setExpandedPassage(expandedPassage === idx ? null : idx)}
                                className="w-full flex items-start gap-3 px-4 py-3 text-left hover:bg-gray-50 transition-colors"
                              >
                                <span className="shrink-0 mt-0.5 inline-flex items-center justify-center w-5 h-5 rounded text-[10px] font-bold bg-amber-100 text-amber-700">
                                  {idx + 1}
                                </span>
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2 flex-wrap">
                                    <span className="text-xs xl:text-sm font-semibold text-gray-800">
                                      {passage.author}
                                    </span>
                                    <span className="text-xs text-gray-500">
                                      {passage.work_title}
                                    </span>
                                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-200 text-gray-600 font-mono">
                                      {passage.reference}
                                    </span>
                                    {passage.confidence >= 0.8 && (
                                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-green-100 text-green-700 font-medium">
                                        {(passage.confidence * 100).toFixed(0)}%
                                      </span>
                                    )}
                                  </div>
                                </div>
                                {expandedPassage === idx ? (
                                  <ChevronUp className="w-4 h-4 text-gray-400 shrink-0 mt-0.5" />
                                ) : (
                                  <ChevronDown className="w-4 h-4 text-gray-400 shrink-0 mt-0.5" />
                                )}
                              </button>

                              {/* Expanded passage text */}
                              <AnimatePresence>
                                {expandedPassage === idx && (
                                  <motion.div
                                    initial={{ height: 0 }}
                                    animate={{ height: 'auto' }}
                                    exit={{ height: 0 }}
                                    transition={{ duration: 0.2 }}
                                    className="overflow-hidden"
                                  >
                                    <div className="px-4 pb-4 space-y-2">
                                      {/* Original text */}
                                      <div className="p-3 rounded-lg bg-white border border-gray-200">
                                        <p className="text-[10px] uppercase tracking-wider text-gray-400 mb-1 font-semibold">
                                          {passage.language === 'greek' ? 'Greek' : passage.language === 'latin' ? 'Latin' : passage.language}
                                        </p>
                                        <p className="text-sm xl:text-base leading-relaxed font-serif text-gray-800 italic">
                                          {passage.original_text}
                                        </p>
                                      </div>

                                      {/* Transliteration if available */}
                                      {passage.transliteration && passage.transliteration !== passage.original_text && (
                                        <div className="p-3 rounded-lg bg-blue-50/50 border border-blue-100">
                                          <p className="text-[10px] uppercase tracking-wider text-blue-400 mb-1 font-semibold">
                                            Transliteration
                                          </p>
                                          <p className="text-sm xl:text-base leading-relaxed text-blue-800">
                                            {passage.transliteration}
                                          </p>
                                        </div>
                                      )}

                                      {/* CTS URN + navigate link */}
                                      <div className="flex items-center gap-3 pt-1">
                                        {passage.cts_urn && (
                                          <span className="text-[10px] font-mono text-gray-400">
                                            {passage.cts_urn}
                                          </span>
                                        )}
                                        <button
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            navigate(`/texts?passage=${passage.passage_id}`);
                                          }}
                                          className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-medium"
                                        >
                                          <ExternalLink className="w-3 h-3" />
                                          View in text reader
                                        </button>
                                      </div>
                                    </div>
                                  </motion.div>
                                )}
                              </AnimatePresence>
                            </div>
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )}

              {/* Inline citation texts from citationTexts map */}
              {message.citationTexts && Object.keys(message.citationTexts).length > 0 && !verifiedPassages?.length && (
                <div className="border-t border-gray-100 pt-3">
                  <button
                    onClick={() => setShowPassages(!showPassages)}
                    className="flex items-center gap-2 text-sm xl:text-base font-medium text-gray-700 hover:text-gray-900 transition-colors w-full"
                  >
                    <FileText className="w-4 h-4" />
                    <span>Referenced Texts ({Object.keys(message.citationTexts).length})</span>
                    {showPassages ? <ChevronUp className="w-4 h-4 ml-auto" /> : <ChevronDown className="w-4 h-4 ml-auto" />}
                  </button>

                  <AnimatePresence>
                    {showPassages && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                      >
                        <div className="mt-3 space-y-2">
                          {Object.entries(message.citationTexts).map(([citation, text]) => (
                            <div key={citation} className="p-3 rounded-lg border border-gray-100 bg-gray-50/50">
                              <p className="text-xs xl:text-sm font-semibold text-gray-700 mb-2">{citation}</p>
                              {text.original && (
                                <div className="mb-2">
                                  <p className="text-[10px] uppercase tracking-wider text-gray-400 mb-0.5 font-semibold">
                                    {text.originalLanguage || 'Original'}
                                  </p>
                                  <p className="text-sm xl:text-base leading-relaxed font-serif text-gray-700 italic">
                                    {text.original}
                                  </p>
                                </div>
                              )}
                              {text.translation && (
                                <div>
                                  <p className="text-[10px] uppercase tracking-wider text-gray-400 mb-0.5 font-semibold">
                                    Translation
                                  </p>
                                  <p className="text-sm xl:text-base leading-relaxed text-gray-600">
                                    {text.translation}
                                  </p>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )}

              {/* Sources panel (collapsible) */}
              {sources && sources.length > 0 && (
                <div className="border-t border-gray-100 pt-3">
                  <button
                    onClick={() => setShowSources(!showSources)}
                    className="flex items-center gap-2 text-sm xl:text-base font-medium text-gray-700 hover:text-gray-900 transition-colors w-full"
                  >
                    <FileText className="w-4 h-4" />
                    <span>Sources ({sources.length})</span>
                    {showSources ? <ChevronUp className="w-4 h-4 ml-auto" /> : <ChevronDown className="w-4 h-4 ml-auto" />}
                  </button>

                  <AnimatePresence>
                    {showSources && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                      >
                        <SourcesPanel
                          sources={sources}
                          evidenceMap={resp?.evidenceMap}
                          onNodeClick={(nodeId) => {
                            const idx = sources.findIndex((s) => s.nodeId === nodeId);
                            onNodeClick(nodeId);
                            if (idx !== -1) onCitationClick(idx);
                          }}
                          className="!border-t-0 !pt-0 !mt-2"
                        />
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )}
            </div>
          )}

          <div className={`text-[10px] xl:text-xs mt-3 ${isUser ? 'text-white/50' : 'text-gray-400'}`}>
            {typeof message.timestamp === 'string'
              ? new Date(message.timestamp).toLocaleTimeString()
              : message.timestamp.toLocaleTimeString()}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
