/**
 * Research Agent API Service
 *
 * Provides API methods for interacting with the Research Agent backend:
 * - Start research sessions
 * - Get session status
 * - Subscribe to SSE events for real-time updates
 * - Import documents
 * - Cancel research
 *
 * @CODE:FRONTEND-UX-001:API
 */

import { apiClient } from "./client";
import { env } from "../env";
import type {
  StartResearchRequest,
  StartResearchResponse,
  ResearchSession,
  ConfirmResearchRequest,
  ConfirmResearchResponse,
  ResearchEventType,
  ResearchProgressData,
  StageChangeData,
  DocumentFoundData,
  MetricsUpdateData,
  ErrorData,
  CompletedData,
} from "@/types/research";

// ============================================================================
// Types
// ============================================================================

export interface ResearchSSEEvent {
  type: ResearchEventType;
  id: string;
  data:
    | ResearchProgressData
    | StageChangeData
    | DocumentFoundData
    | MetricsUpdateData
    | ErrorData
    | CompletedData;
}

export interface ResearchAPICallbacks {
  onProgress?: (data: ResearchProgressData) => void;
  onStageChange?: (data: StageChangeData) => void;
  onDocumentFound?: (data: DocumentFoundData) => void;
  onMetricsUpdate?: (data: MetricsUpdateData) => void;
  onError?: (data: ErrorData) => void;
  onCompleted?: (data: CompletedData) => void;
  onConnectionError?: (error: Error) => void;
}

// ============================================================================
// API Methods
// ============================================================================

/**
 * Start a new research session
 */
export async function startResearch(
  request: StartResearchRequest
): Promise<StartResearchResponse> {
  const response = await apiClient.post<StartResearchResponse>(
    "/research",
    request
  );
  return response.data;
}

/**
 * Get research session status
 */
export async function getResearchSession(
  sessionId: string
): Promise<ResearchSession> {
  const response = await apiClient.get<{ session: ResearchSession }>(
    `/research/${sessionId}`
  );
  return response.data.session;
}

/**
 * Import selected documents
 */
export async function importDocuments(
  sessionId: string,
  request: Omit<ConfirmResearchRequest, "sessionId">
): Promise<ConfirmResearchResponse> {
  const response = await apiClient.post<ConfirmResearchResponse>(
    `/research/${sessionId}/import`,
    request
  );
  return response.data;
}

/**
 * Cancel research session
 */
export async function cancelResearch(sessionId: string): Promise<void> {
  await apiClient.delete(`/research/${sessionId}`);
}

// ============================================================================
// SSE Event Stream
// ============================================================================

/**
 * Subscribe to research session events via SSE
 *
 * @param sessionId - Research session ID
 * @param callbacks - Event handlers for different event types
 * @param lastEventId - Optional last event ID for reconnection
 * @returns Cleanup function to close the connection
 */
export function subscribeToResearchEvents(
  sessionId: string,
  callbacks: ResearchAPICallbacks,
  lastEventId?: string
): () => void {
  // Build SSE URL
  const baseUrl = env.NEXT_PUBLIC_API_URL.replace("/api/v1", "");
  const sseUrl = `${baseUrl}/api/v1/research/${sessionId}/stream`;

  // Create EventSource with headers via fetch (EventSource doesn't support custom headers)
  // So we'll use a custom SSE implementation with fetch
  const controller = new AbortController();

  const connectSSE = async () => {
    try {
      const headers: HeadersInit = {
        Accept: "text/event-stream",
        "Cache-Control": "no-cache",
      };

      // Add API key if available
      if (env.NEXT_PUBLIC_API_KEY) {
        headers["X-API-Key"] = env.NEXT_PUBLIC_API_KEY;
      }

      // Add Last-Event-ID for reconnection
      if (lastEventId) {
        headers["Last-Event-ID"] = lastEventId;
      }

      const response = await fetch(sseUrl, {
        method: "GET",
        headers,
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`SSE connection failed: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("No response body reader");
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          console.log("SSE stream ended");
          break;
        }

        buffer += decoder.decode(value, { stream: true });

        // Parse SSE events from buffer
        const events = parseSSEBuffer(buffer);
        buffer = events.remaining;

        for (const event of events.parsed) {
          handleSSEEvent(event, callbacks);
        }
      }
    } catch (error) {
      if ((error as Error).name === "AbortError") {
        console.log("SSE connection aborted");
        return;
      }
      console.error("SSE connection error:", error);
      callbacks.onConnectionError?.(error as Error);
    }
  };

  // Start connection
  connectSSE();

  // Return cleanup function
  return () => {
    controller.abort();
  };
}

// ============================================================================
// SSE Parsing Helpers
// ============================================================================

interface ParsedSSEEvents {
  parsed: ResearchSSEEvent[];
  remaining: string;
}

function parseSSEBuffer(buffer: string): ParsedSSEEvents {
  const events: ResearchSSEEvent[] = [];
  const lines = buffer.split("\n");

  let currentEvent: Partial<ResearchSSEEvent> = {};
  let remaining = "";

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Check if we have a complete event (empty line ends an event)
    if (line === "") {
      if (currentEvent.type && currentEvent.data) {
        events.push(currentEvent as ResearchSSEEvent);
      }
      currentEvent = {};
      continue;
    }

    // Check if this is an incomplete line (last line without newline)
    if (i === lines.length - 1 && !buffer.endsWith("\n")) {
      remaining = line;
      continue;
    }

    // Parse SSE fields
    if (line.startsWith("id: ")) {
      currentEvent.id = line.slice(4);
    } else if (line.startsWith("event: ")) {
      currentEvent.type = line.slice(7) as ResearchEventType;
    } else if (line.startsWith("data: ")) {
      try {
        currentEvent.data = JSON.parse(line.slice(6));
      } catch {
        console.warn("Failed to parse SSE data:", line);
      }
    }
  }

  return { parsed: events, remaining };
}

function handleSSEEvent(
  event: ResearchSSEEvent,
  callbacks: ResearchAPICallbacks
): void {
  console.log("SSE Event received:", event.type, event.data);

  switch (event.type) {
    case "progress":
      callbacks.onProgress?.(event.data as ResearchProgressData);
      break;
    case "stage_change":
      callbacks.onStageChange?.(event.data as StageChangeData);
      break;
    case "document_found":
      callbacks.onDocumentFound?.(event.data as DocumentFoundData);
      break;
    case "metrics_update":
      callbacks.onMetricsUpdate?.(event.data as MetricsUpdateData);
      break;
    case "error":
      callbacks.onError?.(event.data as ErrorData);
      break;
    case "completed":
      callbacks.onCompleted?.(event.data as CompletedData);
      break;
    default:
      console.warn("Unknown SSE event type:", event.type);
  }
}

// ============================================================================
// Exports
// ============================================================================

export const researchApi = {
  startResearch,
  getResearchSession,
  importDocuments,
  cancelResearch,
  subscribeToResearchEvents,
};

export default researchApi;
