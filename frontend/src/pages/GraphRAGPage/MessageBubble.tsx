import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { useTranslation } from 'react-i18next';
import { Zap, BookOpen, ChevronDown, ChevronUp, Clock, Cpu, FileText, ExternalLink, AlertTriangle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { CitationRenderer, SourcesPanel } from '../../components/CitationRenderer';
import type { GraphRAGChatMessage } from '../../types';

interface MessageBubbleProps {
  message: GraphRAGChatMessage;
  onNodeClick: (nodeId: string) => void;
  onCitationClick: (citationIndex: number) => void;
  onPassageCitationClick?: (passageId: string) => void;
}

export default function MessageBubble({ message, onNodeClick, onCitationClick, onPassageCitationClick }: MessageBubbleProps) {
  const { t } = useTranslation();
  const isUser = message.role === 'user';
  const navigate = useNavigate();
  const [showSources, setShowSources] = useState(false);
  const [showPassages, setShowPassages] = useState(false);
  const [expandedPassage, setExpandedPassage] = useState<number | null>(null);

  const resp = message.graphrag_response;
  const verifiedPassages = resp?.verified_passages;
  // Ancient-text verifier report — unverified quoted Greek/Latin must be
  // surfaced, never silently rendered as if it were corpus-verified.
  const textVerification = resp?.metadata?.text_verification;
  const unverifiedTexts = textVerification?.unverified_texts ?? [];
  const unverifiedCount =
    textVerification?.unverified ?? unverifiedTexts.length;
  const sources = resp?.sources;
  const processingTime = resp?.processing_time;
  const tokensUsed = message.tokens_used;
  const llmModel = message.llm_model;
  const retrievalMode = message.retrieval_mode;
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
            ? 'bg-gradient-to-br from-stone-100 to-stone-50 border border-amber-200/60 shadow-md'
            : 'bg-white border border-amber-200/40 shadow-sm'
        }`}
      >
        <div className={`p-5 xl:p-7 ${isUser ? 'text-stone-800' : 'text-stone-800'}`}>
          {isUser ? (
            <p className="text-[15px] xl:text-base 2xl:text-lg leading-relaxed">{message.content}</p>
          ) : (
            <div className="space-y-4">
              {/* Service badge + metadata row */}
              <div className="flex flex-wrap items-center gap-2">
                {resp?.service && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] xl:text-xs font-semibold bg-amber-50 text-orange-600 border border-amber-200">
                    <Zap className="w-3 h-3 xl:w-3.5 xl:h-3.5" />
                    {resp.service}
                  </span>
                )}
                {llmModel && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] xl:text-xs font-medium bg-parchment-50 text-stone-500 border border-amber-200/40">
                    <Cpu className="w-3 h-3" />
                    {llmModel}
                  </span>
                )}
                {retrievalMode && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] xl:text-xs font-medium bg-blue-50 text-blue-600 border border-blue-200/40">
                    {retrievalMode}
                  </span>
                )}
                {processingTime && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] xl:text-xs font-medium bg-parchment-50 text-stone-500 border border-amber-200/40">
                    <Clock className="w-3 h-3" />
                    {(processingTime / 1000).toFixed(1)}s
                  </span>
                )}
                {nodesUsed !== undefined && (
                  <span className="text-[10px] xl:text-xs text-stone-400">
                    {t('graphRagUi.messageBubble.nodesEdges', { nodes: nodesUsed, edges: edgesTraversed ?? 0 })}
                  </span>
                )}
                {tokensUsed !== undefined && (
                  <span className="text-[10px] xl:text-xs text-stone-400">
                    {t('graphRagUi.messageBubble.tokens', { count: tokensUsed })}
                  </span>
                )}
              </div>

              {/* Unverified ancient text banner (text_verification report) */}
              {unverifiedCount > 0 && (
                <div
                  role="alert"
                  className="rounded-xl border border-amber-300 bg-amber-50 px-4 py-3"
                >
                  <div className="flex items-center gap-2 text-amber-800">
                    <AlertTriangle className="w-4 h-4 shrink-0" aria-hidden="true" />
                    <span className="text-xs xl:text-sm font-semibold">
                      {t('graphRagUi.textVerification.title')}
                    </span>
                  </div>
                  <p className="mt-1 text-[11px] xl:text-xs text-amber-700">
                    {t('graphRagUi.textVerification.body', { count: unverifiedCount })}
                  </p>
                  {unverifiedTexts.length > 0 && (
                    <ul className="mt-2 space-y-1">
                      {unverifiedTexts.slice(0, 5).map((item, i) => (
                        <li
                          key={i}
                          className="text-[11px] xl:text-xs font-mono text-amber-900/80 truncate"
                        >
                          {item.text}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}

              {/* Main answer content */}
              {(sources && sources.length > 0) ||
              ((resp as unknown as { passage_citations?: unknown[] } | undefined)
                ?.passage_citations?.length ?? 0) > 0 ? (
                <div className="prose prose-sm xl:prose-base max-w-none prose-stone">
                  <CitationRenderer
                    content={message.content}
                    sources={sources ?? []}
                    passageCitations={
                      ((resp as unknown as {
                        passage_citations?: Array<{
                          id?: string | null;
                          ref?: string | null;
                          type?: string | null;
                          label?: string | null;
                        }>;
                      } | undefined)?.passage_citations) ?? []
                    }
                    onSourceClick={(sourceIndex) => {
                      if (sourceIndex !== -1) {
                        onCitationClick(sourceIndex);
                      }
                    }}
                    onPassageCitationClick={onPassageCitationClick}
                  />
                </div>
              ) : (
                <div className="prose prose-sm xl:prose-base max-w-none prose-stone">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
              )}

              {/* Verified Passages (clickable original texts) */}
              {verifiedPassages && verifiedPassages.length > 0 && (
                <div className="border-t border-amber-200/40 pt-3">
                  <button
                    onClick={() => setShowPassages(!showPassages)}
                    className="flex items-center gap-2 text-sm xl:text-base font-medium text-stone-700 hover:text-stone-800 transition-colors w-full"
                  >
                    <BookOpen className="w-4 h-4" />
                    <span>{t('graphRagUi.messageBubble.verifiedPassages', { count: verifiedPassages.length })}</span>
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
                              className="rounded-lg border border-amber-200/40 bg-parchment-50/50 overflow-hidden"
                            >
                              {/* Passage header - always visible, clickable */}
                              <button
                                onClick={() => setExpandedPassage(expandedPassage === idx ? null : idx)}
                                className="w-full flex items-start gap-3 px-4 py-3 text-left hover:bg-parchment-100 transition-colors"
                              >
                                <span className="shrink-0 mt-0.5 inline-flex items-center justify-center w-5 h-5 rounded text-[10px] font-bold bg-amber-100 text-amber-700">
                                  {idx + 1}
                                </span>
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2 flex-wrap">
                                    <span className="text-xs xl:text-sm font-semibold text-stone-800">
                                      {passage.author}
                                    </span>
                                    <span className="text-xs text-stone-500">
                                      {passage.work_title}
                                    </span>
                                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-stone-200 text-stone-600 font-mono">
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
                                  <ChevronUp className="w-4 h-4 text-stone-400 shrink-0 mt-0.5" />
                                ) : (
                                  <ChevronDown className="w-4 h-4 text-stone-400 shrink-0 mt-0.5" />
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
                                      <div className="p-3 rounded-lg bg-white border border-amber-200/60">
                                        <p className="text-[10px] uppercase tracking-wider text-stone-400 mb-1 font-semibold">
                                          {passage.language === 'greek' ? 'Greek' : passage.language === 'latin' ? 'Latin' : passage.language}
                                        </p>
                                        <p className="text-sm xl:text-base leading-relaxed font-serif text-stone-800 italic">
                                          {passage.original_text}
                                        </p>
                                      </div>

                                      {/* Transliteration if available */}
                                      {passage.transliteration && passage.transliteration !== passage.original_text && (
                                        <div className="p-3 rounded-lg bg-amber-50/50 border border-amber-200/40">
                                          <p className="text-[10px] uppercase tracking-wider text-amber-500 mb-1 font-semibold">
                                            Transliteration
                                          </p>
                                          <p className="text-sm xl:text-base leading-relaxed text-amber-800">
                                            {passage.transliteration}
                                          </p>
                                        </div>
                                      )}

                                      {/* CTS URN + navigate link */}
                                      <div className="flex items-center gap-3 pt-1">
                                        {passage.cts_urn && (
                                          <span className="text-[10px] font-mono text-stone-400">
                                            {passage.cts_urn}
                                          </span>
                                        )}
                                        <button
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            navigate(`/texts?passage=${passage.passage_id}`);
                                          }}
                                          className="inline-flex items-center gap-1 text-xs text-orange-600 hover:text-orange-700 font-medium"
                                        >
                                          <ExternalLink className="w-3 h-3" />
                                          {t('graphRagUi.messageBubble.viewInTextReader')}
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
                <div className="border-t border-amber-200/40 pt-3">
                  <button
                    onClick={() => setShowPassages(!showPassages)}
                    className="flex items-center gap-2 text-sm xl:text-base font-medium text-stone-700 hover:text-stone-800 transition-colors w-full"
                  >
                    <FileText className="w-4 h-4" />
                    <span>{t('graphRagUi.messageBubble.referencedTexts', { count: Object.keys(message.citationTexts).length })}</span>
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
                            <div key={citation} className="p-3 rounded-lg border border-amber-200/40 bg-parchment-50/50">
                              <p className="text-xs xl:text-sm font-semibold text-stone-700 mb-2">{citation}</p>
                              {text.original && (
                                <div className="mb-2">
                                  <p className="text-[10px] uppercase tracking-wider text-stone-400 mb-0.5 font-semibold">
                                    {text.originalLanguage || t('graphRagUi.messageBubble.originalText')}
                                  </p>
                                  <p className="text-sm xl:text-base leading-relaxed font-serif text-stone-700 italic">
                                    {text.original}
                                  </p>
                                </div>
                              )}
                              {text.translation && (
                                <div>
                                  <p className="text-[10px] uppercase tracking-wider text-stone-400 mb-0.5 font-semibold">
                                    {t('graphRagUi.messageBubble.translation')}
                                  </p>
                                  <p className="text-sm xl:text-base leading-relaxed text-stone-600">
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
                <div className="border-t border-amber-200/40 pt-3">
                  <button
                    onClick={() => setShowSources(!showSources)}
                    className="flex items-center gap-2 text-sm xl:text-base font-medium text-stone-700 hover:text-stone-800 transition-colors w-full"
                  >
                    <FileText className="w-4 h-4" />
                    <span>{t('graphRagUi.messageBubble.sources', { count: sources.length })}</span>
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

          <div className={`text-[10px] xl:text-xs mt-3 ${isUser ? 'text-stone-400' : 'text-stone-400'}`}>
            {typeof message.timestamp === 'string'
              ? new Date(message.timestamp).toLocaleTimeString()
              : message.timestamp.toLocaleTimeString()}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
