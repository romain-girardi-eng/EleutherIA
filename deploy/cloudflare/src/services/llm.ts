/**
 * LLM Service - Supports Gemini and Kimi K2 (Moonshot)
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

export class LLMService {
  private genAI: GoogleGenerativeAI;
  private embeddingModel: string;
  private moonshotApiKey?: string;
  private moonshotBaseUrl: string;

  constructor(env: Env) {
    this.genAI = new GoogleGenerativeAI(env.GEMINI_API_KEY);
    this.embeddingModel = 'models/gemini-embedding-001';  // Supports 128-3072 dimensions
    this.moonshotApiKey = env.MOONSHOT_API_KEY;
    this.moonshotBaseUrl = env.MOONSHOT_BASE_URL || 'https://api.moonshot.ai/v1';
  }

  /**
   * Generate embeddings for text
   */
  async embed(text: string): Promise<number[]> {
    try {
      const model = this.genAI.getGenerativeModel({ model: this.embeddingModel });
      const result = await model.embedContent(text);
      return result.embedding.values;
    } catch (error) {
      logger.error('Embedding generation error', error);
      throw error;
    }
  }

  /**
   * Generate embeddings for multiple texts in batch
   */
  async batchEmbed(texts: string[]): Promise<number[][]> {
    try {
      const model = this.genAI.getGenerativeModel({ model: this.embeddingModel });
      const results = await Promise.all(
        texts.map(text => model.embedContent(text))
      );
      return results.map(r => r.embedding.values);
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
    modelName: string = 'gemini-3-flash-preview',
    deterministic: boolean = true
  ): Promise<string> {
    // Try Kimi K2 first if available (no rate limits on paid tier)
    if (this.moonshotApiKey) {
      try {
        const result = await this.generateWithKimiSimple(prompt, deterministic);
        return result;
      } catch (error: any) {
        logger.warn('Kimi K2 failed, falling back to Gemini:', error?.message || error);
      }
    }

    // Fallback to Gemini
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
    } catch (error) {
      logger.error('Text generation error', error);
      throw error;
    }
  }

  /**
   * Simple Kimi K2 generation without thinking mode (for general text generation)
   */
  private async generateWithKimiSimple(
    prompt: string,
    deterministic: boolean = true
  ): Promise<string> {
    if (!this.moonshotApiKey) {
      throw new Error('Moonshot API key not configured');
    }

    const modelName = 'kimi-latest';
    logger.info(`Generating with Kimi K2 simple (model=${modelName})`);

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
      throw new Error('No response from Kimi K2');
    }

    return result.choices[0].message.content;
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
   * Generate streaming response - Uses Kimi K2 as primary, Gemini as fallback
   */
  async *generateStream(prompt: string, modelName: string = 'gemini-3-flash-preview') {
    // Try Kimi K2 streaming first if available
    if (this.moonshotApiKey) {
      try {
        logger.info('Starting Kimi K2 streaming generation');
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
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ') && line !== 'data: [DONE]') {
              try {
                const data = JSON.parse(line.slice(6)) as {
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
        logger.warn('Kimi K2 streaming failed, falling back to Gemini:', error?.message || error);
      }
    }

    // Fallback to Gemini streaming
    try {
      const model = this.genAI.getGenerativeModel({ model: modelName });
      const result = await model.generateContentStream(prompt);

      for await (const chunk of result.stream) {
        const text = chunk.text();
        if (text) {
          yield text;
        }
      }
    } catch (error) {
      logger.error('Streaming generation error', error);
      throw error;
    }
  }

  /**
   * Generate text using Kimi K2 Thinking via Moonshot Platform
   * Supports deep reasoning with <think>...</think> tags
   */
  async generateWithKimi(
    prompt: string,
    systemPrompt?: string,
    useThinking: boolean = false
  ): Promise<ThinkingResult> {
    if (!this.moonshotApiKey) {
      throw new Error('Moonshot API key not configured');
    }

    const modelName = useThinking ? 'kimi-k2-thinking' : 'kimi-latest';
    logger.info(`Generating with Kimi K2 (model=${modelName}, thinking=${useThinking})`);

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
      throw new Error('No response from Kimi K2');
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
   * Generate with thinking support - uses Kimi K2 if available, falls back to Gemini
   */
  async generateWithThinking(
    prompt: string,
    systemPrompt?: string,
    useThinking: boolean = false
  ): Promise<ThinkingResult> {
    // If thinking mode requested and Moonshot is available, use Kimi K2
    if (useThinking && this.moonshotApiKey) {
      try {
        return await this.generateWithKimi(prompt, systemPrompt, true);
      } catch (error) {
        logger.warn('Kimi K2 failed, falling back to Gemini:', error);
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
   * Check if Kimi K2 thinking is available
   */
  hasThinkingSupport(): boolean {
    return !!this.moonshotApiKey;
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
