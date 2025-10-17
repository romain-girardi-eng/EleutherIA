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
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-200px)]">
      {/* Main Chat Area */}
      <div className="lg:col-span-2 flex flex-col h-full">
        {/* Header */}
        <div className="academic-card mb-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-serif font-bold mb-2">GraphRAG Question Answering</h1>
              <p className="text-academic-muted">
                Ask questions about ancient philosophy, grounded in the knowledge graph
              </p>
            </div>
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="academic-button-outline"
            >
              ⚙️ Settings
            </button>
          </div>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <div className="academic-card mb-4 bg-blue-50 border-blue-200">
            <h3 className="font-semibold mb-3">Advanced Settings</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Semantic K</label>
                <input
                  type="number"
                  value={semanticK}
                  onChange={(e) => setSemanticK(Number(e.target.value))}
                  min={1}
                  max={50}
                  className="w-full px-3 py-1 border border-academic-border rounded text-sm"
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
                  className="w-full px-3 py-1 border border-academic-border rounded text-sm"
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
                  className="w-full px-3 py-1 border border-academic-border rounded text-sm"
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

        {/* Messages Area */}
        <div className="flex-1 academic-card overflow-y-auto mb-4 p-4 space-y-4">
          {messages.length === 0 && !streaming && (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">💬</div>
              <h2 className="text-2xl font-semibold mb-2">Ask a Question</h2>
              <p className="text-academic-muted mb-4">
                Get scholarly answers grounded in the Ancient Free Will Database
              </p>
              <div className="text-sm text-academic-muted space-y-1">
                <p><strong>Try asking:</strong></p>
                <p>"What is Aristotle's concept of voluntary action?"</p>
                <p>"How did the Stoics view fate and free will?"</p>
                <p>"What is Augustine's position on grace and free will?"</p>
              </div>
            </div>
          )}

          {messages.map((message, index) => (
            <MessageBubble key={index} message={message} />
          ))}

          {streaming && (
            <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <div className="spinner w-4 h-4"></div>
                <span className="text-sm text-primary-700 font-medium">{streamStatus}</span>
              </div>
              {streamedAnswer && (
                <div className="markdown-content prose prose-sm">
                  <ReactMarkdown>{streamedAnswer}</ReactMarkdown>
                </div>
              )}
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
              <p className="font-medium">Error: {error}</p>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <form onSubmit={handleSubmit} className="academic-card">
          <div className="flex space-x-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a question about ancient free will debates..."
              disabled={loading || streaming}
              className="flex-1 px-4 py-2 border border-academic-border rounded focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
            />
            {streaming ? (
              <button
                type="button"
                onClick={stopStreaming}
                className="px-6 py-2 bg-red-600 text-white rounded hover:bg-red-700"
              >
                Stop
              </button>
            ) : (
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="academic-button disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Thinking...' : 'Ask'}
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Sidebar */}
      <div className="lg:col-span-1 space-y-4">
        {/* Info Card */}
        <div className="academic-card">
          <h3 className="font-semibold mb-3">How It Works</h3>
          <ol className="text-sm text-academic-text space-y-2 list-decimal list-inside">
            <li>Semantic search finds relevant KG nodes</li>
            <li>Graph traversal expands context via BFS</li>
            <li>Citations are extracted automatically</li>
            <li>Gemini 2.5 Pro generates grounded answer</li>
            <li>Reasoning path shows which nodes were used</li>
          </ol>
        </div>

        {/* Last Response Stats */}
        {messages.length > 0 && messages[messages.length - 1].role === 'assistant' && (
          <div className="academic-card">
            <h3 className="font-semibold mb-3">Last Response</h3>
            {messages[messages.length - 1].citations && (
              <div className="space-y-2 text-sm">
                <div>
                  <span className="font-medium">Ancient Sources:</span>{' '}
                  <span className="text-primary-600">
                    {messages[messages.length - 1].citations!.ancient_sources.length}
                  </span>
                </div>
                <div>
                  <span className="font-medium">Modern Scholarship:</span>{' '}
                  <span className="text-primary-600">
                    {messages[messages.length - 1].citations!.modern_scholarship.length}
                  </span>
                </div>
                {messages[messages.length - 1].reasoning_path && (
                  <div>
                    <span className="font-medium">Nodes Used:</span>{' '}
                    <span className="text-primary-600">
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

// Message Bubble Component
function MessageBubble({ message }: { message: GraphRAGChatMessage }) {
  const [showCitations, setShowCitations] = useState(false);

  return (
    <div className={`${message.role === 'user' ? 'ml-auto max-w-2xl' : 'mr-auto max-w-3xl'}`}>
      <div
        className={`rounded-lg p-4 ${
          message.role === 'user'
            ? 'bg-primary-600 text-white'
            : 'bg-academic-paper border border-academic-border'
        }`}
      >
        {message.role === 'user' ? (
          <p>{message.content}</p>
        ) : (
          <div className="space-y-3">
            <div className="markdown-content prose prose-sm max-w-none">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>

            {message.citations && (
              <div className="border-t border-academic-border pt-3">
                <button
                  onClick={() => setShowCitations(!showCitations)}
                  className="text-sm font-medium text-primary-600 hover:text-primary-700"
                >
                  {showCitations ? '▼' : '▶'} View Citations (
                  {message.citations.ancient_sources.length +
                    message.citations.modern_scholarship.length}
                  )
                </button>

                {showCitations && (
                  <div className="mt-3 space-y-3 text-sm">
                    {message.citations.ancient_sources.length > 0 && (
                      <div>
                        <h4 className="font-semibold mb-2">Ancient Sources:</h4>
                        <ul className="list-disc list-inside space-y-1 text-academic-muted">
                          {message.citations.ancient_sources.slice(0, 5).map((source, i) => (
                            <li key={i} className="citation">
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
                        <ul className="list-disc list-inside space-y-1 text-academic-muted">
                          {message.citations.modern_scholarship.slice(0, 3).map((source, i) => (
                            <li key={i} className="citation">
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
