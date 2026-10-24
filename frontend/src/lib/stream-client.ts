/**
 * Server-Sent Events (SSE) streaming client for Gayatri Cloud AI Tutor.
 * Supports token streaming, citation extraction, and client cancellation.
 */

import { Citation, PedagogyMode } from './types/tutoring';

export interface StreamEventHandlers {
  onToken?: (token: string) => void;
  onCitation?: (citation: Citation) => void;
  onMode?: (mode: PedagogyMode) => void;
  onComplete?: (fullText: string, citations: Citation[]) => void;
  onError?: (error: Error) => void;
}

export class TutorStreamClient {
  private abortController: AbortController | null = null;
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }

  public streamTurn(
    sessionId: string,
    message: string,
    mode: PedagogyMode = 'socratic',
    token: string | null = null,
    organizationId: string | null = null,
    handlers: StreamEventHandlers = {}
  ): () => void {
    this.abortController = new AbortController();
    const signal = this.abortController.signal;

    const url = new URL(`${this.baseUrl}/api/v1/tutoring/sessions/${sessionId}/stream`);
    url.searchParams.set('message', message);
    url.searchParams.set('pedagogy_mode', mode);

    const headers: Record<string, string> = {
      Accept: 'text/event-stream',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    if (organizationId) {
      headers['X-Organization-Id'] = organizationId;
    }

    let fullText = '';
    const citations: Citation[] = [];

    fetch(url.toString(), {
      method: 'GET',
      headers,
      signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Tutor stream failed: HTTP ${response.status}`);
        }
        if (!response.body) {
          throw new Error('Streaming response body is null');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          let currentEvent = 'message';
          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed) continue;

            if (trimmed.startsWith('event:')) {
              currentEvent = trimmed.replace('event:', '').trim();
            } else if (trimmed.startsWith('data:')) {
              const rawData = trimmed.replace('data:', '').trim();

              try {
                const parsed = JSON.parse(rawData);

                if (currentEvent === 'token' || parsed.token) {
                  const chunk = parsed.token || parsed.content || '';
                  fullText += chunk;
                  handlers.onToken?.(chunk);
                } else if (currentEvent === 'citation' || parsed.citation) {
                  const cit: Citation = parsed.citation || parsed;
                  citations.push(cit);
                  handlers.onCitation?.(cit);
                } else if (currentEvent === 'mode' || parsed.mode) {
                  handlers.onMode?.(parsed.mode as PedagogyMode);
                } else if (currentEvent === 'done' || parsed.done) {
                  handlers.onComplete?.(fullText, citations);
                  return;
                }
              } catch {
                // If plain text token
                if (currentEvent === 'token' || currentEvent === 'message') {
                  fullText += rawData;
                  handlers.onToken?.(rawData);
                }
              }
            }
          }
        }

        handlers.onComplete?.(fullText, citations);
      })
      .catch((err: Error) => {
        if (err.name === 'AbortError') {
          // Stream cancelled by user
          return;
        }
        handlers.onError?.(err);
      });

    // Return cancellation function
    return () => {
      if (this.abortController) {
        this.abortController.abort();
        this.abortController = null;
      }
    };
  }
}
