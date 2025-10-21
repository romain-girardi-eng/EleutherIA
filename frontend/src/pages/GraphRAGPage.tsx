import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { apiClient } from '../api/client';
import type { GraphRAGResponse, GraphRAGStreamEvent, GraphRAGChatMessage } from '../types';

export default function GraphRAGPage() {
  const [messages, setMessages] = useState<GraphRAGChatMessage[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [streamedAnswer, setStreamedAnswer] = useState('');
  const [streamStatus, setStreamStatus] = useState('');
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Advanced settings
  const [semanticK, setSemanticK] = useState(10);
  const [graphDepth, setGraphDepth] = useState(2);
  const [maxContext, setMaxContext] = useState(15);
  const [useStreaming, setUseStreaming] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const [showHowItWorks, setShowHowItWorks] = useState(false); // Collapsible How It Works
  const [showBenefits, setShowBenefits] = useState(false); // Start collapsed to prevent layout issues

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamedAnswer]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!query.trim() || loading || streaming) return;

    // Add user message
    const userMessage: GraphRAGChatMessage = {
      role: 'user',
      content: query.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentQuery = query.trim();
    setQuery('');
    setError(null);

    if (useStreaming) {
      await handleStreamingQuery(currentQuery);
    } else {
      await handleStandardQuery(currentQuery);
    }
  };

  const handleStandardQuery = async (queryText: string) => {
    setLoading(true);

    try {
      const response = await apiClient.graphragQuery({
        query: queryText,
        semantic_k: semanticK,
        graph_depth: graphDepth,
        max_context: maxContext,
      });

      const assistantMessage: GraphRAGChatMessage = {
        role: 'assistant',
        content: response.answer,
        citations: response.citations,
        reasoning_path: response.reasoning_path,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      console.error('GraphRAG error:', err);
      setError(err.message || 'Failed to get answer');
    } finally {
      setLoading(false);
    }
  };

  const handleStreamingQuery = async (queryText: string) => {
    setStreaming(true);
    setStreamedAnswer('');
    setStreamStatus('Initializing...');

    try {
      const params = new URLSearchParams({
        query: queryText,
        semantic_k: semanticK.toString(),
        graph_depth: graphDepth.toString(),
        max_context: maxContext.toString(),
      });

      const eventSource = new EventSource(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/graphrag/query/stream?${params}`
      );
      eventSourceRef.current = eventSource;

      let fullAnswer = '';
      let finalResponse: GraphRAGResponse | null = null;

      eventSource.onmessage = (event) => {
        try {
          const data: GraphRAGStreamEvent = JSON.parse(event.data);

          switch (data.type) {
            case 'status':
              setStreamStatus(data.message || 'Processing...');
              break;

            case 'answer_chunk':
              fullAnswer += data.data;
              setStreamedAnswer(fullAnswer);
              break;

            case 'complete':
              finalResponse = data.data as GraphRAGResponse;
              break;

            case 'error':
              setError(data.message || 'Stream error');
              break;
          }
        } catch (err) {
          console.error('Error parsing stream event:', err);
        }
      };

      eventSource.onerror = () => {
        eventSource.close();

        if (finalResponse) {
          const assistantMessage: GraphRAGChatMessage = {
            role: 'assistant',
            content: finalResponse.answer,
            citations: finalResponse.citations,
            reasoning_path: finalResponse.reasoning_path,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, assistantMessage]);
        } else if (fullAnswer) {
          const assistantMessage: GraphRAGChatMessage = {
            role: 'assistant',
            content: fullAnswer,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, assistantMessage]);
        }

        setStreaming(false);
        setStreamedAnswer('');
        setStreamStatus('');
      };
    } catch (err: any) {
      console.error('Streaming error:', err);
      setError(err.message || 'Failed to stream answer');
      setStreaming(false);
    }
  };

  const stopStreaming = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setStreaming(false);
    setStreamedAnswer('');
    setStreamStatus('');
  };

  return (
    <div className="flex flex-col lg:grid lg:grid-cols-3 gap-4 lg:gap-6 lg:h-[calc(100vh-180px)]">
      {/* Main Chat Area */}
      <div className="lg:col-span-2 flex flex-col lg:h-full">
        {/* Header */}
        <div className="academic-card mb-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <h1 className="text-2xl sm:text-3xl font-serif font-bold mb-1 sm:mb-2">GraphRAG Question Answering</h1>
              <p className="text-sm sm:text-base text-academic-muted leading-relaxed">
                Graph-based Retrieval-Augmented Generation combines vector search with knowledge graph
                traversal to provide scholarly answers grounded in primary sources and modern scholarship.
              </p>
            </div>
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="academic-button-outline whitespace-nowrap self-start sm:self-auto"
            >
              ⚙️ Settings
            </button>
          </div>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <div className="academic-card mb-4 bg-primary-50 border-primary-200">
            <h3 className="font-semibold mb-3">Advanced Settings</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Semantic K</label>
                <input
                  type="number"
                  value={semanticK}
                  onChange={(e) => setSemanticK(Number(e.target.value))}
                  min={1}
                  max={50}
                  className="w-full px-3 py-2 border border-academic-border rounded text-sm"
                />
                <p className="text-xs text-academic-muted mt-1">Starting nodes from search</p>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Graph Depth</label>
                <input
                  type="number"
                  value={graphDepth}
                  onChange={(e) => setGraphDepth(Number(e.target.value))}
                  min={1}
                  max={5}
                  className="w-full px-3 py-2 border border-academic-border rounded text-sm"
                />
                <p className="text-xs text-academic-muted mt-1">BFS traversal depth</p>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Max Context</label>
                <input
                  type="number"
                  value={maxContext}
                  onChange={(e) => setMaxContext(Number(e.target.value))}
                  min={5}
                  max={30}
                  className="w-full px-3 py-2 border border-academic-border rounded text-sm"
                />
                <p className="text-xs text-academic-muted mt-1">Nodes in LLM context</p>
              </div>
              <div>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={useStreaming}
                    onChange={(e) => setUseStreaming(e.target.checked)}
                    className="rounded"
                  />
                  <span className="text-sm">Enable Streaming</span>
                </label>
                <p className="text-xs text-academic-muted mt-1">Real-time progress updates</p>
              </div>
            </div>
          </div>
        )}

        {/* Why It's Brilliant Section - Mobile Only */}
        <div className="lg:hidden mb-4">
          <div className="academic-card bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
            <button
              onClick={() => setShowBenefits(!showBenefits)}
              className="w-full flex items-center justify-between text-left hover:opacity-80 transition-opacity"
            >
              <h3 className="font-semibold text-base text-green-900 flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                Why It's Brilliant
              </h3>
              <span className="text-green-700 text-sm font-medium">
                {showBenefits ? '▼ Hide' : '▶ Show'}
              </span>
            </button>
            {showBenefits && <div className="mt-3 pt-3 border-t border-green-200"></div>}
            {showBenefits && (
              <div className="text-xs space-y-2.5 max-h-96 overflow-y-auto">
                <BenefitsContent />
              </div>
            )}
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 academic-card overflow-y-auto mb-4 p-3 sm:p-4 space-y-4 min-h-[300px] max-h-[600px] lg:max-h-none">
          {messages.length === 0 && !streaming && (
            <div className="text-center py-8 sm:py-12">
              <div className="text-5xl sm:text-6xl mb-3 sm:mb-4">💬</div>
              <h2 className="text-xl sm:text-2xl font-semibold mb-2">Ask a Question</h2>
              <p className="text-sm sm:text-base text-academic-muted mb-2 px-4 leading-relaxed">
                GraphRAG retrieves relevant nodes from the knowledge graph, traverses their connections,
                and synthesizes scholarly answers with automatic citations.
              </p>
              <p className="text-xs sm:text-sm text-academic-muted mb-3 sm:mb-4 px-4">
                <strong>508 nodes • 831 relationships • 860+ sources</strong>
              </p>
              <div className="text-xs sm:text-sm text-academic-muted space-y-1 px-4">
                <p className="font-medium mb-1">Example questions:</p>
                <p className="italic">"What is Aristotle's concept of voluntary action?"</p>
                <p className="italic">"How did the Stoics reconcile fate with moral responsibility?"</p>
                <p className="italic">"What arguments did Carneades use against Stoic determinism?"</p>
                <p className="italic">"How does Augustine's view of grace relate to free will?"</p>
              </div>
            </div>
          )}

          {messages.map((message, index) => (
            <MessageBubble key={index} message={message} />
          ))}

          {streaming && (
            <div className="bg-primary-50 border border-primary-200 rounded-lg p-3 sm:p-4">
              <div className="flex items-center space-x-2 mb-2">
                <div className="spinner w-4 h-4 flex-shrink-0"></div>
                <span className="text-xs sm:text-sm text-primary-700 font-medium break-words">{streamStatus}</span>
              </div>
              {streamedAnswer && (
                <div className="markdown-content prose prose-sm max-w-none overflow-x-auto">
                  <ReactMarkdown>{streamedAnswer}</ReactMarkdown>
                </div>
              )}
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 sm:p-4 text-red-800">
              <p className="font-medium text-sm sm:text-base break-words">Error: {error}</p>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <form onSubmit={handleSubmit} className="academic-card">
          <div className="flex flex-col sm:flex-row gap-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a question about ancient free will debates..."
              disabled={loading || streaming}
              className="flex-1 px-3 sm:px-4 py-2 border border-academic-border rounded focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 text-sm sm:text-base"
            />
            {streaming ? (
              <button
                type="button"
                onClick={stopStreaming}
                className="px-6 py-2 bg-red-600 text-white rounded hover:bg-red-700 font-medium whitespace-nowrap"
              >
                Stop
              </button>
            ) : (
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="academic-button disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
              >
                {loading ? 'Thinking...' : 'Ask'}
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Sidebar - Hidden on mobile, shown on desktop */}
      <div className="hidden lg:block lg:col-span-1 space-y-4 h-full overflow-y-auto">
        {/* How GraphRAG Works Section - Collapsible */}
        <div className="academic-card bg-gradient-to-br from-blue-50 to-indigo-50 border-primary-200">
          <button
            onClick={() => setShowHowItWorks(!showHowItWorks)}
            className="w-full flex items-center justify-between text-left hover:opacity-80 transition-opacity"
          >
            <h3 className="font-semibold text-base text-primary-900 flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              How GraphRAG Works
            </h3>
            <span className="text-primary-700 text-sm font-medium">
              {showHowItWorks ? '▼ Hide' : '▶ Show'}
            </span>
          </button>
          {showHowItWorks && <div className="mt-3 pt-3 border-t border-primary-200"></div>}
          {showHowItWorks && (
            <div className="text-xs space-y-2.5 max-h-96 overflow-y-auto pr-2">
              <div className="bg-white/80 rounded-lg p-2.5 border border-blue-100">
                <div className="font-semibold text-primary-800 mb-1.5">1. Vector Search</div>
                <p className="text-academic-muted leading-relaxed text-xs">
                  Your query is embedded using Gemini and compared against 508 KG node embeddings
                  in Qdrant to find semantically relevant starting points.
                </p>
              </div>
              <div className="bg-white/80 rounded-lg p-2.5 border border-blue-100">
                <div className="font-semibold text-primary-800 mb-1.5">2. Graph Expansion</div>
                <p className="text-academic-muted leading-relaxed text-xs">
                  Breadth-first search traverses relationships (authored, influenced, refutes)
                  to gather connected nodes, creating rich contextual networks.
                </p>
              </div>
              <div className="bg-white/80 rounded-lg p-2.5 border border-blue-100">
                <div className="font-semibold text-primary-800 mb-1.5">3. Context Building</div>
                <p className="text-academic-muted leading-relaxed text-xs">
                  Ancient sources and modern scholarship are extracted from retrieved nodes,
                  prioritized by node type (persons, arguments, concepts).
                </p>
              </div>
              <div className="bg-white/80 rounded-lg p-2.5 border border-blue-100">
                <div className="font-semibold text-primary-800 mb-1.5">4. LLM Synthesis</div>
                <p className="text-academic-muted leading-relaxed text-xs">
                  An LLM generates a scholarly answer grounded exclusively in the retrieved
                  Knowledge Graph context, with strict citation requirements.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Why It's Brilliant Section */}
        <div className="academic-card bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
          <button
            onClick={() => setShowBenefits(!showBenefits)}
            className="w-full flex items-center justify-between text-left hover:opacity-80 transition-opacity"
          >
            <h3 className="font-semibold text-base text-green-900 flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              Why It's Brilliant
            </h3>
            <span className="text-green-700 text-sm font-medium">
              {showBenefits ? '▼ Hide' : '▶ Show'}
            </span>
          </button>
          {showBenefits && <div className="mt-3 pt-3 border-t border-green-200"></div>}
          {showBenefits && (
            <div className="text-xs space-y-2.5 max-h-96 overflow-y-auto pr-2">
              <BenefitsContent />
            </div>
          )}
        </div>

        {/* Last Response Stats */}
        {messages.length > 0 && messages[messages.length - 1].role === 'assistant' && (
          <div className="academic-card">
            <h3 className="font-semibold mb-3 text-base">Last Response</h3>
            {messages[messages.length - 1].citations && (
              <div className="space-y-2 text-xs sm:text-sm">
                <div className="flex justify-between items-center">
                  <span className="font-medium">Ancient Sources:</span>
                  <span className="text-primary-600 font-semibold">
                    {messages[messages.length - 1].citations!.ancient_sources.length}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="font-medium">Modern Scholarship:</span>
                  <span className="text-primary-600 font-semibold">
                    {messages[messages.length - 1].citations!.modern_scholarship.length}
                  </span>
                </div>
                {messages[messages.length - 1].reasoning_path && (
                  <div className="flex justify-between items-center">
                    <span className="font-medium">Nodes Used:</span>
                    <span className="text-primary-600 font-semibold">
                      {messages[messages.length - 1].reasoning_path!.total_nodes}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// Benefits Content Component (reusable for mobile and desktop)
function BenefitsContent() {
  return (
    <>
      {/* Benefit 1: Relationship Discovery */}
      <div className="bg-white/80 rounded-lg p-2.5 border border-green-100">
        <div className="font-semibold text-green-800 mb-1.5">
          Discovers Hidden Relationships
        </div>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>Traditional search:</strong> "Augustine free will" → finds Augustine's writings.
        </p>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>GraphRAG:</strong> Finds Augustine → traverses to Pelagius (opponent) →
          discovers the Pelagian Controversy → connects to earlier Stoic concepts Augustine adapted
          → reveals the complete debate context.
        </p>
        <p className="text-green-700 text-xs font-medium italic">
          → You understand Augustine's position through his intellectual battles and sources.
        </p>
      </div>

      {/* Benefit 2: Contextual Understanding */}
      <div className="bg-white/80 rounded-lg p-2.5 border border-green-100">
        <div className="font-semibold text-green-800 mb-1.5">
          Provides Rich Historical Context
        </div>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>Simple RAG:</strong> Retrieves isolated text chunks about "ἐφ' ἡμῖν" (in our power).
        </p>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>GraphRAG:</strong> Shows how the concept evolved from Aristotle (4th c. BCE) →
          adopted by Stoics → critiqued by Carneades → reformulated by Epictetus →
          transmitted to Latin as "in nostra potestate" → influenced Christian theology.
        </p>
        <p className="text-green-700 text-xs font-medium italic">
          → You see the intellectual genealogy spanning 800 years.
        </p>
      </div>

      {/* Benefit 3: Argument Networks */}
      <div className="bg-white/80 rounded-lg p-2.5 border border-green-100">
        <div className="font-semibold text-green-800 mb-1.5">
          Maps Complete Argument Networks
        </div>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>Keyword search:</strong> "Chrysippus determinism" → scattered mentions.
        </p>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>GraphRAG:</strong> Retrieves Chrysippus's arguments → follows "refutes" edges to
          Carneades's counter-arguments → finds Cicero's synthesis → discovers later Neoplatonic
          responses → extracts all cited sources.
        </p>
        <p className="text-green-700 text-xs font-medium italic">
          → You get the full dialectical landscape, not isolated opinions.
        </p>
      </div>

      {/* Benefit 4: Automatic Citations */}
      <div className="bg-white/80 rounded-lg p-2.5 border border-green-100">
        <div className="font-semibold text-green-800 mb-1.5">
          Grounds Every Claim in Sources
        </div>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>Standard LLM:</strong> Might hallucinate "Plato discussed compatibilism in Republic X."
        </p>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>GraphRAG:</strong> Only uses information from retrieved nodes. Automatically extracts
          ancient sources (e.g., "Aristotle, <em>EN</em> III.1, 1110a1-4") and modern scholarship
          (e.g., "Bobzien 1998, Frede 2011") from node metadata.
        </p>
        <p className="text-green-700 text-xs font-medium italic">
          → Verifiable, academically rigorous answers you can cite in your own research.
        </p>
      </div>

      {/* Benefit 5: Multi-hop Reasoning */}
      <div className="bg-white/80 rounded-lg p-2.5 border border-green-100">
        <div className="font-semibold text-green-800 mb-1.5">
          Enables Multi-Hop Reasoning
        </div>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>Question:</strong> "How did Aristotelian ethics influence Christian theology?"
        </p>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>GraphRAG path:</strong> Aristotle → "influenced" → Alexander of Aphrodisias →
          "transmitted_by" → Arabic commentators → "influenced" → Thomas Aquinas →
          "synthesized_with" → Augustine's theology.
        </p>
        <p className="text-green-700 text-xs font-medium italic">
          → Traces intellectual transmission across cultures and centuries in a single query.
        </p>
      </div>
    </>
  );
}

// Message Bubble Component
function MessageBubble({ message }: { message: GraphRAGChatMessage }) {
  const [showCitations, setShowCitations] = useState(false);

  return (
    <div className={`${message.role === 'user' ? 'ml-auto max-w-[95%] sm:max-w-2xl' : 'mr-auto max-w-[98%] sm:max-w-3xl'}`}>
      <div
        className={`rounded-lg p-3 sm:p-4 ${
          message.role === 'user'
            ? 'bg-primary-600 text-white'
            : 'bg-academic-paper border border-academic-border'
        }`}
      >
        {message.role === 'user' ? (
          <p className="text-sm sm:text-base break-words">{message.content}</p>
        ) : (
          <div className="space-y-3">
            <div className="markdown-content prose prose-sm max-w-none overflow-x-auto">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>

            {message.citations && (
              <div className="border-t border-academic-border pt-3">
                <button
                  onClick={() => setShowCitations(!showCitations)}
                  className="text-xs sm:text-sm font-medium text-primary-600 hover:text-primary-700"
                >
                  {showCitations ? '▼' : '▶'} View Citations (
                  {message.citations.ancient_sources.length +
                    message.citations.modern_scholarship.length}
                  )
                </button>

                {showCitations && (
                  <div className="mt-3 space-y-3 text-xs sm:text-sm">
                    {message.citations.ancient_sources.length > 0 && (
                      <div>
                        <h4 className="font-semibold mb-2">Ancient Sources:</h4>
                        <ul className="list-disc list-inside space-y-1 text-academic-muted pl-2">
                          {message.citations.ancient_sources.slice(0, 5).map((source, i) => (
                            <li key={i} className="citation break-words">
                              {source}
                            </li>
                          ))}
                          {message.citations.ancient_sources.length > 5 && (
                            <li className="text-xs">
                              ...and {message.citations.ancient_sources.length - 5} more
                            </li>
                          )}
                        </ul>
                      </div>
                    )}

                    {message.citations.modern_scholarship.length > 0 && (
                      <div>
                        <h4 className="font-semibold mb-2">Modern Scholarship:</h4>
                        <ul className="list-disc list-inside space-y-1 text-academic-muted pl-2">
                          {message.citations.modern_scholarship.slice(0, 3).map((source, i) => (
                            <li key={i} className="citation break-words">
                              {source}
                            </li>
                          ))}
                          {message.citations.modern_scholarship.length > 3 && (
                            <li className="text-xs">
                              ...and {message.citations.modern_scholarship.length - 3} more
                            </li>
                          )}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        <div className="text-xs mt-2 opacity-70">
          {message.timestamp.toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}
