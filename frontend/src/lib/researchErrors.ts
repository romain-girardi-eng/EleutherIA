/**
 * researchErrors — turn a raw stream failure into something a reader can act on.
 *
 * Both research hooks reject with terse technical strings (`HTTP 401`,
 * `no_response_body`, `opencode_unreachable`, a `TypeError` message on a dead
 * network). The page used to print those verbatim, so a logged-out visitor on
 * /research read "Stream failed — HTTP 401" and had no way to know a login was
 * all that was missing.
 *
 * The mapping is deliberately status-driven rather than message-driven: the
 * backend detail strings are not part of any contract, the HTTP status is.
 */

export type ResearchErrorKind =
  | 'authRequired'
  | 'quotaExceeded'
  | 'rateLimited'
  | 'sessionExpired'
  | 'runtimeUnavailable'
  | 'runtimeUnreachable'
  | 'invalidRequest'
  | 'serverError'
  | 'network'
  | 'unknown';

export interface ResearchErrorInfo {
  kind: ResearchErrorKind;
  /** i18n key under `research.errors.*`. */
  i18nKey: string;
  /** True when signing in is what unblocks the user. */
  needsAuth: boolean;
  /** True when retrying the same query has a realistic chance of working. */
  retryable: boolean;
  /** Original message, kept for the details disclosure. */
  raw: string;
}

const KIND_KEYS: Record<ResearchErrorKind, string> = {
  authRequired: 'research.errors.authRequired',
  quotaExceeded: 'research.errors.quotaExceeded',
  rateLimited: 'research.errors.rateLimited',
  sessionExpired: 'research.errors.sessionExpired',
  runtimeUnavailable: 'research.errors.runtimeUnavailable',
  runtimeUnreachable: 'research.errors.runtimeUnreachable',
  invalidRequest: 'research.errors.invalidRequest',
  serverError: 'research.errors.serverError',
  network: 'research.errors.network',
  unknown: 'research.errors.streamFailed',
};

const RETRYABLE: ReadonlySet<ResearchErrorKind> = new Set<ResearchErrorKind>([
  'rateLimited',
  'sessionExpired',
  'runtimeUnreachable',
  'serverError',
  'network',
  'unknown',
]);

function kindForStatus(status: number): ResearchErrorKind {
  if (status === 401) return 'authRequired';
  if (status === 402 || status === 403) return 'quotaExceeded';
  if (status === 410) return 'sessionExpired';
  if (status === 429) return 'rateLimited';
  if (status === 503) return 'runtimeUnavailable';
  if (status === 502 || status === 504) return 'runtimeUnreachable';
  if (status >= 400 && status < 500) return 'invalidRequest';
  return 'serverError';
}

function kindForMessage(message: string): ResearchErrorKind {
  const status = /HTTP (\d{3})/.exec(message)?.[1];
  if (status) return kindForStatus(Number(status));
  if (message === 'no_response_body' || message === 'no_session_id_in_response') {
    return 'serverError';
  }
  // A `fetch` that never reached the server rejects with a TypeError whose
  // message is browser-specific ("Failed to fetch", "NetworkError when…",
  // "Load failed"). Treat the whole family as a network outage.
  if (/failed to fetch|networkerror|load failed|network request failed/i.test(message)) {
    return 'network';
  }
  return 'unknown';
}

export function classifyResearchError(message: string | null): ResearchErrorInfo | null {
  if (!message) return null;
  const kind = kindForMessage(message);
  return {
    kind,
    i18nKey: KIND_KEYS[kind],
    needsAuth: kind === 'authRequired',
    retryable: RETRYABLE.has(kind),
    raw: message,
  };
}
