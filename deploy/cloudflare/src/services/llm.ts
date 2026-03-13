/**
 * LLM Service - Supports Gemini and Moonshot Kimi
 */

import { GoogleGenerativeAI } from '@google/generative-ai';
import { Env } from '../types';
import { getLogger } from '../utils/logger';

const logger = getLogger('LLMService');

export interface ThinkingResult {
  response: string;
  thinkingProcess?: string;
  model: string;
  provider: string;
}

interface EmbedOptions {
  taskType?: 'RETRIEVAL_QUERY' | 'RETRIEVAL_DOCUMENT' | 'SEMANTIC_SIMILARITY';
  title?: string;
}

export class LLMService {
  private genAI: GoogleGenerativeAI;
  private embeddingModel: string;
  private moonshotApiKey?: string;
  private moonshotBaseUrl: string;
  private openRouterApiKey?: string;
  private openRouterBaseUrl: string;
  private openRouterModel: string;
  private openRouterThinkingModel: string;
  private openRouterProviderOnly?: string;
  private openRouterProviderOrder?: string;
  private openRouterReasoningEffort: string;
  private openRouterHttpReferer?: string;
  private openRouterAppName?: string;

  constructor(env: Env) {
    this.genAI = new GoogleGenerativeAI(env.GEMINI_API_KEY);
    this.embeddingModel = env.GEMINI_EMBEDDING_MODEL || 'models/gemini-embedding-001';
    this.moonshotApiKey = env.MOONSHOT_API_KEY;
    this.moonshotBaseUrl = env.MOONSHOT_BASE_URL || 'https://api.moonshot.ai/v1';
    this.openRouterApiKey = env.OPENROUTER_API_KEY;
    this.openRouterBaseUrl = env.OPENROUTER_BASE_URL || 'https://openrouter.ai/api/v1';
    this.openRouterModel = env.OPENROUTER_MODEL || 'google/gemini-3-flash-preview';
    this.openRouterThinkingModel = env.OPENROUTER_THINKING_MODEL || 'openai/gpt-oss-120b:nitro';
    this.openRouterProviderOnly = env.OPENROUTER_PROVIDER_ONLY;
    this.openRouterProviderOrder = env.OPENROUTER_PROVIDER_ORDER;
    this.openRouterReasoningEffort = env.OPENROUTER_REASONING_EFFORT || 'low';
    this.openRouterHttpReferer = env.OPENROUTER_HTTP_REFERER;
    this.openRouterAppName = env.OPENROUTER_APP_NAME;
  }

  /**
   * Generate embeddings for text
   */
  async embed(text: string, options: EmbedOptions = {}): Promise<number[]> {
    try {
      const model = this.genAI.getGenerativeModel({ model: this.embeddingModel });
      const result = await model.embedContent({
        content: { role: 'user', parts: [{ text }] },
        taskType: options.taskType || 'RETRIEVAL_QUERY',
        ...(options.title ? { title: options.title } : {}),
      });
      return result.embedding.values;
    } catch (error) {
      logger.error('Embedding generation error', error);
      throw error;
    }
  }

  /**
   * Generate embeddings for multiple texts in batch
   */
  async batchEmbed(
    texts: string[],
    options: EmbedOptions = {}
  ): Promise<number[][]> {
    try {
      const model = this.genAI.getGenerativeModel({ model: this.embeddingModel });
      const requests = texts.map(text => ({
        content: { role: 'user', parts: [{ text }] },
        taskType: options.taskType || 'RETRIEVAL_QUERY',
        ...(options.title ? { title: options.title } : {}),
      }));
      const results = await model.batchEmbedContents({ requests });
      return results.embeddings.map(r => r.values);
    } catch (error) {
      logger.error('Batch embedding generation error', error);
      throw error;
    }
  }

  /**
   * Generate text - Uses Kimi K2 as primary, Gemini as fallback
   */
  async generate(
    prompt: string,
    modelName: string = 'gemini-3.1-pro-preview',
    deterministic: boolean = true
  ): Promise<string> {
    // Gemini is the primary generation model.
    try {
      const generationConfig = deterministic
        ? {
            temperature: 0.0,      // No randomness for deterministic outputs
            topK: 1,              // Only select highest probability token
            topP: 0.1,            // Minimal randomness
            candidateCount: 1,    // Single consistent output
            maxOutputTokens: 4096, // Increased for academic answers
          }
        : {
            temperature: 0.3,     // Some creativity for planning
            topK: 10,
            topP: 0.8,
            candidateCount: 1,
            maxOutputTokens: 4096, // Increased for academic answers
          };

      const model = this.genAI.getGenerativeModel({
        model: modelName,
        generationConfig,
      });

      const result = await model.generateContent(prompt);
      const response = await result.response;
      return response.text();
    } catch (error: any) {
      logger.warn('Gemini failed, attempting provider fallback:', error?.message || error);
    }

    if (this.openRouterApiKey) {
      try {
        const result = await this.generateWithOpenRouter(prompt, undefined, false, deterministic);
        return result.response;
      } catch (error: any) {
        logger.warn('OpenRouter failed, falling back to Kimi:', error?.message || error);
      }
    }

    if (this.moonshotApiKey) {
      try {
        return await this.generateWithKimiSimple(prompt, deterministic);
      } catch (error) {
        logger.error('Text generation error', error);
        throw error;
      }
    }

    throw new Error('No LLM provider available');
  }

  /**
   * Simple Kimi generation (for general text generation)
   */
  private async generateWithKimiSimple(
    prompt: string,
    deterministic: boolean = true
  ): Promise<string> {
    if (!this.moonshotApiKey) {
      throw new Error('Moonshot API key not configured');
    }

    const modelName = 'kimi-latest';
    logger.info(`Generating with Kimi simple (model=${modelName})`);

    const response = await fetch(`${this.moonshotBaseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.moonshotApiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: modelName,
        messages: [{ role: 'user', content: prompt }],
        temperature: deterministic ? 0.0 : 0.3,
        max_tokens: 4096,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Moonshot API error: ${response.status} - ${errorText}`);
    }

    const result = await response.json() as {
      choices: Array<{ message: { content: string } }>;
    };

    if (!result.choices || result.choices.length === 0) {
      throw new Error('No response from Kimi');
    }

    return result.choices[0].message.content;
  }

  private async generateWithOpenRouter(
    prompt: string,
    systemPrompt?: string,
    useThinking: boolean = false,
    deterministic: boolean = true
  ): Promise<ThinkingResult> {
    if (!this.openRouterApiKey) {
      throw new Error('OpenRouter API key not configured');
    }

    const messages: Array<{ role: string; content: string }> = [];
    if (systemPrompt) {
      messages.push({ role: 'system', content: systemPrompt });
    }
    messages.push({ role: 'user', content: prompt });

    const provider: Record<string, string[]> = {};
    if (this.openRouterProviderOnly) {
      provider.only = this.openRouterProviderOnly.split(',').map(p => p.trim()).filter(Boolean);
    } else if (this.openRouterProviderOrder) {
      provider.order = this.openRouterProviderOrder.split(',').map(p => p.trim()).filter(Boolean);
    }

    const response = await fetch(`${this.openRouterBaseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.openRouterApiKey}`,
        'Content-Type': 'application/json',
        ...(this.openRouterHttpReferer ? { 'HTTP-Referer': this.openRouterHttpReferer } : {}),
        ...(this.openRouterAppName ? { 'X-Title': this.openRouterAppName } : {}),
      },
      body: JSON.stringify({
        model: useThinking ? this.openRouterThinkingModel : this.openRouterModel,
        messages,
        temperature: deterministic ? 0.0 : 0.3,
        max_tokens: 4096,
        ...(Object.keys(provider).length ? { provider } : {}),
        ...(useThinking ? { reasoning: { effort: this.openRouterReasoningEffort } } : {}),
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`OpenRouter API error: ${response.status} - ${errorText}`);
    }

    const result = await response.json() as {
      provider?: string;
      choices: Array<{ message: { content?: string; reasoning?: string } }>;
      model?: string;
    };

    if (!result.choices || result.choices.length === 0) {
      throw new Error('No response from OpenRouter');
    }

    const message = result.choices[0].message;
    return {
      response: message.content || '',
      thinkingProcess: message.reasoning,
      model: result.model || (useThinking ? this.openRouterThinkingModel : this.openRouterModel),
      provider: result.provider || 'openrouter',
    };
  }

  /**
   * Generate text with automatic retry on rate limits
   */
  async generateWithRetry(
    prompt: string,
    modelName: string = 'gemini-3-flash-preview',
    maxRetries: number = 3
  ): Promise<string> {
    let retries = 0;
    let lastError: Error | null = null;

    while (retries < maxRetries) {
      try {
        return await this.generate(prompt, modelName);
      } catch (error: any) {
        const errorMsg = error?.message || String(error);

        // Check if it's a rate limit error
        if (errorMsg.includes('429') || errorMsg.includes('quota') || errorMsg.includes('Too Many Requests')) {
          retries++;
          const backoffMs = Math.pow(2, retries) * 1000; // Exponential backoff: 2s, 4s, 8s
          logger.warn(`Rate limit hit, retry ${retries}/${maxRetries} after ${backoffMs}ms`);

          if (retries < maxRetries) {
            await this.sleep(backoffMs);
            lastError = error;
          } else {
            // Max retries exceeded
            throw new Error(`Rate limit exceeded after ${maxRetries} retries`);
          }
        } else {
          // Non-rate-limit error, throw immediately
          throw error;
        }
      }
    }

    throw lastError || new Error('Max retries exceeded');
  }

  /**
   * Sleep helper for retry logic
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Generate streaming response - Uses Gemini as primary, Kimi as fallback.
   */
  async *generateStream(prompt: string, modelName: string = 'gemini-3-flash-preview') {
    // Gemini is the primary generation model for streaming.
    try {
      const model = this.genAI.getGenerativeModel({ model: modelName });
      const result = await model.generateContentStream(prompt);

      for await (const chunk of result.stream) {
        const text = chunk.text();
        if (text) {
          yield text;
        }
      }
      return;
    } catch (error: any) {
      logger.warn('Gemini streaming failed, falling back to Kimi:', error?.message || error);
    }

    if (this.moonshotApiKey) {
      try {
        logger.info('Starting Kimi fallback streaming generation');
        const response = await fetch(`${this.moonshotBaseUrl}/chat/completions`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.moonshotApiKey}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            model: 'kimi-latest',
            messages: [{ role: 'user', content: prompt }],
            temperature: 0.3,
            max_tokens: 4096,
            stream: true,
          }),
        });

        if (!response.ok) {
          throw new Error(`Moonshot streaming error: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('No reader available');
        }

        const decoder = new TextDecoder();
        let buffer = '';
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // Keep incomplete trailing line in buffer

          for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith('data: ') && trimmed !== 'data: [DONE]') {
              try {
                const data = JSON.parse(trimmed.slice(6)) as {
                  choices: Array<{ delta: { content?: string } }>;
                };
                const content = data.choices?.[0]?.delta?.content;
                if (content) {
                  yield content;
                }
              } catch {
                // Skip invalid JSON lines
              }
            }
          }
        }
        return; // Successfully completed with Kimi
      } catch (error: any) {
        logger.error('Streaming generation error', error);
        throw error;
      }
    }
  }

  /**
   * Generate text using Moonshot Kimi via Moonshot Platform
   */
  async generateWithKimi(
    prompt: string,
    systemPrompt?: string,
    useThinking: boolean = false
  ): Promise<ThinkingResult> {
    if (!this.moonshotApiKey) {
      throw new Error('Moonshot API key not configured');
    }

    const modelName = 'kimi-latest';
    logger.info(`Generating with Kimi (model=${modelName}, thinking=${useThinking})`);

    const messages: Array<{ role: string; content: string }> = [];
    if (systemPrompt) {
      messages.push({ role: 'system', content: systemPrompt });
    }
    messages.push({ role: 'user', content: prompt });

    const response = await fetch(`${this.moonshotBaseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.moonshotApiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: modelName,
        messages,
        temperature: 0.7,
        max_tokens: 4096,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Moonshot API error: ${response.status} - ${errorText}`);
    }

    const result = await response.json() as {
      choices: Array<{ message: { content: string } }>;
    };

    if (!result.choices || result.choices.length === 0) {
      throw new Error('No response from Kimi');
    }

    let responseText = result.choices[0].message.content;
    let thinkingProcess: string | undefined;

    // Extract thinking process if present
    if (responseText.includes('<think>') && responseText.includes('</think>')) {
      const thinkMatch = responseText.match(/<think>([\s\S]*?)<\/think>/);
      if (thinkMatch) {
        thinkingProcess = thinkMatch[1].trim();
        logger.info(`Extracted thinking process: ${thinkingProcess.length} chars`);
        // Remove thinking tags from response
        responseText = responseText.replace(/<think>[\s\S]*?<\/think>/g, '').trim();
      }
    } else {
      logger.info('No thinking tags found in response');
    }

    logger.info(`Kimi K2 response: ${responseText.length} chars, thinking: ${!!thinkingProcess}`);

    return {
      response: responseText,
      thinkingProcess,
      model: modelName,
      provider: 'moonshot',
    };
  }

  /**
   * Generate with thinking support - uses OpenRouter first, then Kimi, then Gemini
   */
  async generateWithThinking(
    prompt: string,
    systemPrompt?: string,
    useThinking: boolean = false
  ): Promise<ThinkingResult> {
    if (useThinking && this.openRouterApiKey) {
      try {
        return await this.generateWithOpenRouter(prompt, systemPrompt, true, true);
      } catch (error: any) {
        logger.warn('OpenRouter reasoning failed, falling back to Kimi:', error?.message || error);
      }
    }

    if (useThinking && this.moonshotApiKey) {
      try {
        return await this.generateWithKimi(prompt, systemPrompt, true);
      } catch (error: any) {
        logger.warn('Kimi failed, falling back to Gemini:', error?.message || error);
      }
    }

    // Fallback to Gemini (no thinking support)
    const fullPrompt = systemPrompt ? `${systemPrompt}\n\n${prompt}` : prompt;
    const response = await this.generate(fullPrompt);
    return {
      response,
      model: 'gemini-3-flash-preview',
      provider: 'gemini',
    };
  }

  /**
   * Check if Moonshot Kimi is available
   */
  hasThinkingSupport(): boolean {
    return !!this.openRouterApiKey || !!this.moonshotApiKey;
  }

  /**
   * Task-based model routing — auto-selects model for the task type.
   *
   * - classification, reranking, sufficiency → Gemini Flash (fast, cheap, structured JSON)
   * - reasoning → OpenRouter reasoning model with Gemini fallback
   * - synthesis → Gemini Pro
   * - citation_verification, self_rag → Gemini Flash (structured JSON)
   */
  async generateForTask(
    prompt: string,
    taskType: 'classification' | 'reranking' | 'sufficiency' | 'synthesis' | 'reasoning' | 'citation_verification' | 'self_rag' | 'expansion'
  ): Promise<string> {
    const needsReasoning = taskType === 'reasoning';

    if (needsReasoning && this.openRouterApiKey) {
      try {
        const result = await this.generateWithOpenRouter(prompt, undefined, true, true);
        return result.response;
      } catch (error: any) {
        logger.warn(`OpenRouter failed for ${taskType}, falling back to Kimi/Gemini:`, error?.message);
      }
    }

    if (needsReasoning && this.moonshotApiKey) {
      try {
        const result = await this.generateWithKimi(prompt, undefined, true);
        return result.response;
      } catch (error: any) {
        logger.warn(`Kimi failed for ${taskType}, falling back to Gemini:`, error?.message);
      }
    }

    if (taskType === 'synthesis') {
      return this.generate(prompt, 'gemini-3.1-pro-preview', true);
    }

    // Gemini Flash for lightweight or structured tasks (and as fallback)
    return this.generate(prompt, 'gemini-3-flash-preview', true);
  }

  /**
   * Health check - Does not waste API calls
   * Just verifies the service is configured correctly
   */
  async healthCheck(): Promise<boolean> {
    try {
      // Check if GenAI client is initialized properly
      return !!this.genAI && !!this.embeddingModel;
    } catch {
      return false;
    }
  }
}
