import { useState, useCallback, useEffect } from 'react';
import { apiClient } from '../../../api/client';
import type { Conversation } from '../../../components/graphrag/ConversationSidebar';
import type { GraphRAGChatMessage, ConversationMessage } from '../../../types';

export interface ConversationState {
  conversationId: string | null;
  conversations: Conversation[];
  conversationsLoading: boolean;
  showSidebar: boolean;
  sidebarCollapsed: boolean;
}

export interface ConversationActions {
  setConversationId: React.Dispatch<React.SetStateAction<string | null>>;
  setShowSidebar: React.Dispatch<React.SetStateAction<boolean>>;
  setSidebarCollapsed: React.Dispatch<React.SetStateAction<boolean>>;
  loadConversations: () => Promise<void>;
  handleNewConversation: () => void;
  handleSelectConversation: (id: string) => Promise<GraphRAGChatMessage[]>;
  handleDeleteConversation: (id: string) => Promise<void>;
  createConversation: (settings: Record<string, unknown>) => Promise<string | null>;
}

export function useConversation(
  isAuthenticated: boolean,
  onMessagesLoaded?: (messages: GraphRAGChatMessage[]) => void,
  onReset?: () => void
): ConversationState & ConversationActions {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [conversationsLoading, setConversationsLoading] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Load conversations when authenticated
  const loadConversations = useCallback(async () => {
    if (!isAuthenticated) return;

    setConversationsLoading(true);
    try {
      const response = await apiClient.listConversations(50, 0);
      if (response.success) {
        setConversations(response.conversations);
      }
    } catch (err) {
      console.error('Failed to load conversations:', err);
    } finally {
      setConversationsLoading(false);
    }
  }, [isAuthenticated]);

  // Load on mount and auth change
  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  // Create new conversation (reset state)
  const handleNewConversation = useCallback(() => {
    setConversationId(null);
    onReset?.();
  }, [onReset]);

  // Select existing conversation
  const handleSelectConversation = useCallback(async (id: string): Promise<GraphRAGChatMessage[]> => {
    setConversationId(id);

    try {
      const response = await apiClient.getConversationMessages(id);
      if (response.success) {
        // Convert messages to GraphRAGChatMessage format
        const loadedMessages: GraphRAGChatMessage[] = response.messages
          .filter((msg: ConversationMessage) => msg.role === 'user' || msg.role === 'assistant')
          .map((msg: ConversationMessage) => ({
          role: msg.role as 'user' | 'assistant',
          content: msg.content,
          citations: msg.citations as GraphRAGChatMessage['citations'],
          reasoning_path: msg.reasoning_path as GraphRAGChatMessage['reasoning_path'],
          thinking_process: msg.thinking_process,
          tokens_used: msg.tokens_used,
          llm_provider: msg.llm_provider,
          llm_model: msg.llm_model,
          timestamp: new Date(msg.created_at),
        }));

        onMessagesLoaded?.(loadedMessages);
        return loadedMessages;
      }
    } catch (err) {
      console.error('Failed to load conversation messages:', err);
      throw err;
    }

    return [];
  }, [onMessagesLoaded]);

  // Delete conversation
  const handleDeleteConversation = useCallback(async (id: string) => {
    try {
      const response = await apiClient.deleteConversation(id);
      if (response.success) {
        // Remove from list
        setConversations((prev) => prev.filter((c) => c.conversation_id !== id));
        // Clear if active
        if (conversationId === id) {
          handleNewConversation();
        }
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    }
  }, [conversationId, handleNewConversation]);

  // Create a new conversation with settings
  const createConversation = useCallback(async (settings: Record<string, unknown>): Promise<string | null> => {
    if (!isAuthenticated) return null;

    try {
      const response = await apiClient.createConversation({ settings });
      if (response.success) {
        const newId = response.conversation.conversation_id;
        setConversationId(newId);
        console.log('[Conversation] Created new conversation:', newId);
        return newId;
      }
    } catch (err) {
      console.error('[Conversation] Failed to create:', err);
    }

    return null;
  }, [isAuthenticated]);

  return {
    // State
    conversationId,
    conversations,
    conversationsLoading,
    showSidebar,
    sidebarCollapsed,

    // Setters
    setConversationId,
    setShowSidebar,
    setSidebarCollapsed,

    // Actions
    loadConversations,
    handleNewConversation,
    handleSelectConversation,
    handleDeleteConversation,
    createConversation,
  };
}
