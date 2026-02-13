/**
 * Visual Pulpit Routes
 * Secure proxy for sermon presentation generation via Gemini API.
 * The prompt and API key live server-side — clients send only sermon text + options.
 */

import { Hono } from 'hono';
import { Env } from '../types';
import { rateLimitMiddleware } from '../middleware/auth';
import { getLogger } from '../utils/logger';
import { SERMON_PRESENTATION_PROMPT, VALID_THEME_NAMES } from '../prompts/sermon-presentation';

const logger = getLogger('VisualPulpit');

const GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models';
const GEMINI_MODEL = 'gemini-3-flash-preview';
const GENERATION_TEMPERATURE = 0.85;
const GENERATION_MAX_TOKENS = 65536;

export const visualPulpitRoutes = new Hono<{ Bindings: Env }>();

// Rate limit: 5 requests per 15 minutes per IP
visualPulpitRoutes.use('*', rateLimitMiddleware(5, 15));

/**
 * POST /generate
 * Generate a three-panel sermon presentation from sermon notes.
 *
 * Request body:
 *   sermonNotes: string (required, 50-100000 chars)
 *   themeName?: string (one of 20 valid theme names)
 *   translation?: string (Bible translation abbreviation)
 *   language?: string (content language)
 *
 * Returns: AISermonPresentationResponse JSON
 */
visualPulpitRoutes.post('/generate', async (c) => {
  const startTime = Date.now();

  // Parse request body
  let body: Record<string, unknown>;
  try {
    body = await c.req.json();
  } catch {
    return c.json({ error: 'Invalid JSON body' }, 400);
  }

  const { sermonNotes, themeName, translation, language } = body as {
    sermonNotes?: string;
    themeName?: string;
    translation?: string;
    language?: string;
  };

  // --- Input validation ---
  if (!sermonNotes || typeof sermonNotes !== 'string') {
    return c.json({ error: 'sermonNotes is required and must be a string' }, 400);
  }

  if (sermonNotes.length < 50) {
    return c.json({ error: 'sermonNotes must be at least 50 characters' }, 400);
  }

  if (sermonNotes.length > 100_000) {
    return c.json({ error: 'sermonNotes must be at most 100,000 characters' }, 400);
  }

  if (themeName !== undefined) {
    if (typeof themeName !== 'string' || !(VALID_THEME_NAMES as readonly string[]).includes(themeName)) {
      return c.json({
        error: `Invalid themeName. Must be one of: ${VALID_THEME_NAMES.join(', ')}`,
      }, 400);
    }
  }

  if (translation !== undefined && typeof translation !== 'string') {
    return c.json({ error: 'translation must be a string' }, 400);
  }

  if (language !== undefined && typeof language !== 'string') {
    return c.json({ error: 'language must be a string' }, 400);
  }

  // --- Build the full prompt (server-side) ---
  let userMessage = `Generate a three-panel sermon presentation from these sermon notes:\n\n${sermonNotes}`;

  if (themeName) {
    userMessage += `\n\nPreferred theme: ${themeName}`;
  }
  if (translation) {
    userMessage += `\n\nBible translation to use: ${translation}`;
  }
  if (language) {
    userMessage += `\n\nThe content is in ${language}. Generate everything in the same language.`;
  }

  const fullPrompt = `${SERMON_PRESENTATION_PROMPT}\n\n---\n\n${userMessage}`;

  // --- Call Gemini API ---
  const apiKey = c.env.GEMINI_API_KEY;
  if (!apiKey) {
    logger.error('GEMINI_API_KEY not configured');
    return c.json({ error: 'Server configuration error' }, 500);
  }

  const geminiUrl = `${GEMINI_API_URL}/${GEMINI_MODEL}:generateContent?key=${apiKey}`;

  logger.info(`Generating sermon presentation (${sermonNotes.length} chars, theme=${themeName || 'auto'})`);

  let geminiResponse: Response;
  try {
    geminiResponse = await fetch(geminiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [
          {
            role: 'user',
            parts: [{ text: fullPrompt }],
          },
        ],
        generationConfig: {
          responseMimeType: 'application/json',
          temperature: GENERATION_TEMPERATURE,
          maxOutputTokens: GENERATION_MAX_TOKENS,
        },
      }),
    });
  } catch (err) {
    logger.error('Gemini fetch failed', err);
    return c.json({ error: 'Failed to reach AI service' }, 502);
  }

  // --- Handle Gemini errors ---
  if (!geminiResponse.ok) {
    const status = geminiResponse.status;

    if (status === 429) {
      // Rate limited by Gemini — propagate with retry info
      const retryAfter = geminiResponse.headers.get('Retry-After') || '60';
      logger.warn('Gemini rate limited');
      return c.json(
        {
          error: 'AI service is temporarily overloaded. Please try again later.',
          retryAfter: parseInt(retryAfter, 10),
        },
        429
      );
    }

    let errorMessage = geminiResponse.statusText;
    try {
      const errorBody = await geminiResponse.json() as { error?: { message?: string } };
      errorMessage = errorBody.error?.message || errorMessage;
    } catch {
      // Use statusText
    }

    logger.error(`Gemini error ${status}: ${errorMessage}`);
    return c.json({ error: 'AI generation failed' }, 502);
  }

  // --- Parse Gemini response ---
  let geminiData: {
    candidates?: Array<{
      content?: { parts?: Array<{ text?: string }> };
      finishReason?: string;
    }>;
  };
  try {
    geminiData = await geminiResponse.json();
  } catch {
    logger.error('Failed to parse Gemini response as JSON');
    return c.json({ error: 'Invalid response from AI service' }, 502);
  }

  const parts = geminiData.candidates?.[0]?.content?.parts;
  if (!parts || parts.length === 0) {
    logger.error('No content in Gemini response');
    return c.json({ error: 'Empty response from AI service' }, 502);
  }

  // Gemini 3 thinking models may return multiple parts (thought + text)
  // Get text from the last part that has a text field
  let text: string | undefined;
  for (const part of parts) {
    if (part.text) {
      text = part.text;
    }
  }

  if (!text) {
    logger.error('No text in Gemini response parts');
    return c.json({ error: 'No text content from AI service' }, 502);
  }

  // Check if response was truncated
  const finishReason = geminiData.candidates?.[0]?.finishReason;
  if (finishReason === 'MAX_TOKENS') {
    logger.warn('Gemini response was truncated (MAX_TOKENS)');
  }

  // --- Parse the JSON response ---
  let presentation: unknown;
  try {
    presentation = JSON.parse(text);
  } catch {
    logger.error(`Failed to parse presentation JSON. First 500 chars: ${text.substring(0, 500)}`);
    logger.error(`Last 200 chars: ${text.substring(text.length - 200)}`);
    logger.error(`Finish reason: ${finishReason}`);
    return c.json({ error: 'AI produced invalid JSON output' }, 502);
  }

  // Gemini sometimes wraps the response in an array — unwrap it
  if (Array.isArray(presentation) && presentation.length === 1) {
    presentation = presentation[0];
  }

  const elapsed = Date.now() - startTime;
  logger.info(`Sermon presentation generated in ${elapsed}ms`);

  return c.json(presentation);
});
