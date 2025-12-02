"use client";

/**
 * Research Agent Page
 * Ethereal Glass Aesthetic
 *
 * Main page for the Research Agent interface with split layout.
 * Left: ChatZone (40%) - Natural language interaction
 * Right: ProgressZone (60%) - Real-time progress and results
 *
 * Now integrated with real backend API via SSE for real-time updates.
 *
 * @CODE:FRONTEND-UX-002
 */

import { useCallback, useRef, useEffect, useState } from "react";
import { ChatZone } from "@/components/research/ChatZone";
import { ProgressZone } from "@/components/research/ProgressZone";
import {
  useResearchStore,
  selectSession,
  selectMessages,
  selectIsLoading,
  selectSelectedDocumentIds,
} from "@/stores/researchStore";
import {
  researchApi,
  type ResearchAPICallbacks,
} from "@/lib/api/research";
import type { ResearchStage } from "@/types/research";
import { WifiOff } from "lucide-react";

// ============================================================================
// Configuration
// ============================================================================

// Set to true to use mock simulation, false to use real API
const USE_MOCK_API = process.env.NEXT_PUBLIC_USE_MOCK_API === "true";

// HIGH PRIORITY FIX #7: Input validation constants
const MIN_QUERY_LENGTH = 3;
const MAX_QUERY_LENGTH = 1000;

// ============================================================================
// Page Component
// ============================================================================

export default function ResearchPage() {
  // Store selectors
  const session = useResearchStore(selectSession);
  const messages = useResearchStore(selectMessages);
  const isLoading = useResearchStore(selectIsLoading);
  const selectedDocumentIds = useResearchStore(selectSelectedDocumentIds);
  const expandedDocumentIds = useResearchStore((state) => state.expandedDocumentIds);

  // Actions
  const startResearchAction = useResearchStore((state) => state.startResearch);
  const addMessage = useResearchStore((state) => state.addMessage);
  const confirmResearchAction = useResearchStore((state) => state.confirmResearch);
  const cancelResearchAction = useResearchStore((state) => state.cancelResearch);
  const toggleDocumentSelection = useResearchStore((state) => state.toggleDocumentSelection);
  const toggleDocumentExpand = useResearchStore((state) => state.toggleDocumentExpand);
  const selectAllDocuments = useResearchStore((state) => state.selectAllDocuments);
  const deselectAllDocuments = useResearchStore((state) => state.deselectAllDocuments);
  const updateStage = useResearchStore((state) => state.updateStage);
  const updateProgress = useResearchStore((state) => state.updateProgress);
  const updateMetrics = useResearchStore((state) => state.updateMetrics);
  const addDocument = useResearchStore((state) => state.addDocument);

  // SSE cleanup ref
  const sseCleanupRef = useRef<(() => void) | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  // HIGH PRIORITY FIX #5: Lifecycle tracking to prevent stale operations
  const isMountedRef = useRef(true);

  // HIGH PRIORITY FIX #3: Improved cleanup with lifecycle tracking
  useEffect(() => {
    isMountedRef.current = true;

    return () => {
      isMountedRef.current = false;
      if (sseCleanupRef.current) {
        sseCleanupRef.current();
        sseCleanupRef.current = null;
      }
    };
  }, []);

  // HIGH PRIORITY FIX #6: Consolidated error handler
  const handleResearchError = useCallback(
    (error: Error | { message: string }, type: "connection" | "research" | "validation") => {
      const message =
        type === "connection"
          ? `서버 연결 오류: ${error.message}. 다시 시도해 주세요.`
          : type === "validation"
            ? `입력 오류: ${error.message}`
            : `오류가 발생했습니다: ${error.message}`;

      updateStage("error");
      if (type === "connection") {
        setConnectionError(error.message);
      }
      addMessage({
        role: "system",
        content: message,
      });
    },
    [updateStage, setConnectionError, addMessage]
  );

  // Real API integration
  const startResearchWithAPI = useCallback(
    async (query: string) => {
      try {
        // HIGH PRIORITY FIX #7: Input validation
        const trimmedQuery = query.trim();
        if (trimmedQuery.length < MIN_QUERY_LENGTH) {
          throw new Error(
            `검색어는 최소 ${MIN_QUERY_LENGTH}자 이상이어야 합니다.`
          );
        }
        if (trimmedQuery.length > MAX_QUERY_LENGTH) {
          throw new Error(
            `검색어는 최대 ${MAX_QUERY_LENGTH}자를 초과할 수 없습니다.`
          );
        }

        setConnectionError(null);

        // Call backend API to start research
        const response = await researchApi.startResearch({ query: trimmedQuery });
        const { sessionId, estimatedDuration } = response;

        // HIGH PRIORITY FIX #5: Check if component is still mounted
        if (!isMountedRef.current) {
          console.log("Component unmounted, aborting research setup");
          return;
        }

        // Update store with real session ID
        startResearchAction(trimmedQuery);

        // Update session ID in store
        useResearchStore.setState((state) => ({
          session: state.session
            ? { ...state.session, id: sessionId }
            : null,
        }));

        // Set up SSE callbacks
        const callbacks: ResearchAPICallbacks = {
          onProgress: (data) => {
            if (!isMountedRef.current) return;
            console.log("Progress:", data);
            updateProgress(data.progress * 100); // Backend sends 0-1, frontend uses 0-100
          },
          onStageChange: (data) => {
            if (!isMountedRef.current) return;
            console.log("Stage change:", data);
            updateStage(data.newStage as ResearchStage);
          },
          onDocumentFound: (data) => {
            if (!isMountedRef.current) return;
            console.log("Document found:", data);

            // HIGH PRIORITY FIX #9: Check for duplicate documents
            const existingDoc = session?.documents.find(d => d.id === data.document.id);
            if (existingDoc) {
              console.log("Document already exists, skipping:", data.document.id);
              return;
            }

            addDocument({
              id: data.document.id,
              title: data.document.title,
              source: data.document.source,
              snippet: data.document.snippet,
              relevanceScore: data.document.relevanceScore,
              collectedAt: new Date(data.document.collectedAt),
              categories: data.document.categories,
            });
            updateMetrics({ documentsFound: data.totalCount });
          },
          onMetricsUpdate: (data) => {
            if (!isMountedRef.current) return;
            console.log("Metrics update:", data);
            updateMetrics(data.metrics);
          },
          onError: (data) => {
            if (!isMountedRef.current) return;
            console.error("Research error:", data);
            handleResearchError(data, "research");
          },
          onCompleted: (data) => {
            if (!isMountedRef.current) return;
            console.log("Research completed:", data);
            updateStage("confirming");
            updateProgress(90);
            updateMetrics({
              documentsFound: data.totalDocuments,
              qualityScore: data.qualityScore,
            });
            addMessage({
              role: "assistant",
              content: `리서치가 완료되었습니다. ${data.totalDocuments}개의 문서를 찾았습니다. 수집된 문서를 확인하고 저장할지 결정해 주세요.`,
            });
          },
          onConnectionError: (error) => {
            if (!isMountedRef.current) return;
            console.error("SSE connection error:", error);
            handleResearchError(error, "connection");
          },
        };

        // Subscribe to SSE events (now returns Promise)
        const cleanup = await researchApi.subscribeToResearchEvents(
          sessionId,
          callbacks
        );

        // HIGH PRIORITY FIX #5: Only set cleanup if still mounted
        if (isMountedRef.current) {
          sseCleanupRef.current = cleanup;
        } else {
          // Component unmounted during async operation, cleanup immediately
          cleanup();
        }

        console.log(
          `Research started: session=${sessionId}, estimated=${estimatedDuration}s`
        );
      } catch (error) {
        console.error("Failed to start research:", error);
        const errorType = (error as Error).message.includes("검색어")
          ? "validation"
          : "connection";
        handleResearchError(error as Error, errorType);
      }
    },
    // HIGH PRIORITY FIX #4: Add missing setConnectionError dependency
    [
      startResearchAction,
      updateStage,
      updateProgress,
      updateMetrics,
      addDocument,
      addMessage,
      setConnectionError,
      handleResearchError,
      session,
    ]
  );

  // Handlers
  const handleSendMessage = useCallback(
    (content: string) => {
      // Add user message
      addMessage({ role: "user", content });

      // If no active session, start research
      if (!session || session.stage === "idle" || session.stage === "completed") {
        if (USE_MOCK_API) {
          // Use mock simulation
          startResearchAction(content);
          simulateResearchProgress();
        } else {
          // Use real API
          startResearchWithAPI(content);
        }
      }
    },
    [session, addMessage, startResearchAction, startResearchWithAPI]
  );

  const handleConfirm = useCallback(async () => {
    if (!session) return;

    if (USE_MOCK_API) {
      confirmResearchAction();
    } else {
      try {
        // Call backend to import documents
        const result = await researchApi.importDocuments(session.id, {
          selectedDocumentIds,
          taxonomyId: undefined,
        });

        if (result.success) {
          confirmResearchAction();
          addMessage({
            role: "assistant",
            content: `${result.documentsImported}개의 문서가 지식 베이스에 추가되었습니다.`,
          });
        }
      } catch (error) {
        console.error("Failed to import documents:", error);
        addMessage({
          role: "system",
          content: `문서 임포트 실패: ${(error as Error).message}`,
        });
      }
    }
  }, [session, selectedDocumentIds, confirmResearchAction, addMessage]);

  const handleCancel = useCallback(async () => {
    // Clean up SSE connection
    if (sseCleanupRef.current) {
      sseCleanupRef.current();
      sseCleanupRef.current = null;
    }

    if (!USE_MOCK_API && session?.id) {
      try {
        await researchApi.cancelResearch(session.id);
      } catch (error) {
        console.error("Failed to cancel research:", error);
      }
    }

    cancelResearchAction();
  }, [session, cancelResearchAction]);

  const handleRetry = useCallback(() => {
    if (session?.query) {
      if (USE_MOCK_API) {
        startResearchAction(session.query);
        simulateResearchProgress();
      } else {
        startResearchWithAPI(session.query);
      }
    }
  }, [session, startResearchAction, startResearchWithAPI]);

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col lg:flex-row gap-6 p-6 max-w-[1920px] mx-auto">
      {/* Connection Error Banner */}
      {connectionError && (
        <div className="absolute left-0 right-0 top-0 z-50 bg-red-500/90 backdrop-blur-md p-3 text-center text-white flex items-center justify-center gap-2 shadow-lg">
          <WifiOff className="w-4 h-4" />
          <span>연결 오류: {connectionError}</span>
          <button
            onClick={() => setConnectionError(null)}
            className="ml-4 underline hover:text-white/80"
          >
            닫기
          </button>
        </div>
      )}

      {/* API Mode Indicator (dev only) */}
      {process.env.NODE_ENV === "development" && (
        <div className="absolute right-8 top-20 z-50 rounded-full bg-white/5 border border-white/10 px-3 py-1 text-xs text-white/60 backdrop-blur-md">
          {USE_MOCK_API ? "🎭 Mock Mode" : "🔗 API Mode"}
        </div>
      )}

      {/* Chat Zone - 40% on desktop, full width stacked on mobile */}
      <div className="h-1/2 w-full lg:h-full lg:w-2/5 lg:min-w-[400px] rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md overflow-hidden shadow-glass">
        <ChatZone
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          disabled={isLoading && session?.stage !== "confirming"}
        />
      </div>

      {/* Progress Zone - 60% on desktop, full width stacked on mobile */}
      <div className="h-1/2 w-full lg:h-full lg:w-3/5 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md overflow-hidden shadow-glass">
        <ProgressZone
          session={session}
          selectedDocumentIds={selectedDocumentIds}
          expandedDocumentIds={expandedDocumentIds}
          onConfirm={handleConfirm}
          onCancel={handleCancel}
          onRetry={handleRetry}
          onDocumentSelect={toggleDocumentSelection}
          onDocumentExpand={toggleDocumentExpand}
          onSelectAll={selectAllDocuments}
          onDeselectAll={deselectAllDocuments}
        />
      </div>
    </div>
  );
}

// ============================================================================
// Mock Progress Simulation (for development without backend)
// ============================================================================

function simulateResearchProgress() {
  const store = useResearchStore.getState();

  const stages = [
    { stage: "analyzing" as const, progress: 10, delay: 1000 },
    { stage: "searching" as const, progress: 30, delay: 2000 },
    { stage: "collecting" as const, progress: 50, delay: 3000 },
    { stage: "organizing" as const, progress: 70, delay: 2000 },
    { stage: "confirming" as const, progress: 90, delay: 1500 },
  ];

  let totalDelay = 0;

  stages.forEach(({ stage, progress, delay }) => {
    totalDelay += delay;
    setTimeout(() => {
      const currentSession = useResearchStore.getState().session;
      if (currentSession && currentSession.stage !== "completed" && currentSession.stage !== "error") {
        store.updateStage(stage);
        store.updateProgress(progress);

        // Simulate metrics update
        store.updateMetrics({
          sourcesSearched: Math.floor(progress / 10),
          documentsFound: Math.floor(progress / 5),
          qualityScore: 0.7 + (progress / 500),
          estimatedTimeRemaining: Math.max(0, 120 - progress),
        });

        // Add mock documents during collecting stage
        if (stage === "collecting") {
          for (let i = 0; i < 3; i++) {
            store.addDocument({
              id: `doc_${Date.now()}_${i}`,
              title: `발견된 문서 ${i + 1}`,
              source: {
                id: `src_${i}`,
                name: `소스 ${i + 1}`,
                type: "web",
                url: `https://example.com/doc/${i}`,
                reliability: i === 0 ? "high" : "medium",
              },
              snippet: "이 문서는 검색된 주제와 관련된 유용한 정보를 포함하고 있습니다...",
              relevanceScore: 0.9 - i * 0.1,
              collectedAt: new Date(),
              categories: ["research", "knowledge"],
            });
          }
        }

        // Add assistant message at confirming stage
        if (stage === "confirming") {
          store.addMessage({
            role: "assistant",
            content: "리서치가 완료되었습니다. 수집된 문서를 확인하고 저장할지 결정해 주세요.",
          });
        }
      }
    }, totalDelay);
  });
}
