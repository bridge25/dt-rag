"use client";

/**
 * Research Agent Page
 *
 * Main page for the Research Agent interface with split layout.
 * Left: ChatZone (40%) - Natural language interaction
 * Right: ProgressZone (60%) - Real-time progress and results
 *
 * Now integrated with real backend API via SSE for real-time updates.
 *
 * @CODE:FRONTEND-UX-001
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

// ============================================================================
// Configuration
// ============================================================================

// Set to true to use mock simulation, false to use real API
const USE_MOCK_API = process.env.NEXT_PUBLIC_USE_MOCK_API === "true";

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

  // Cleanup SSE on unmount
  useEffect(() => {
    return () => {
      if (sseCleanupRef.current) {
        sseCleanupRef.current();
      }
    };
  }, []);

  // Real API integration
  const startResearchWithAPI = useCallback(
    async (query: string) => {
      try {
        setConnectionError(null);

        // Call backend API to start research
        const response = await researchApi.startResearch({ query });
        const { sessionId, estimatedDuration } = response;

        // Update store with real session ID
        startResearchAction(query);

        // Update session ID in store
        useResearchStore.setState((state) => ({
          session: state.session
            ? { ...state.session, id: sessionId }
            : null,
        }));

        // Set up SSE callbacks
        const callbacks: ResearchAPICallbacks = {
          onProgress: (data) => {
            console.log("Progress:", data);
            updateProgress(data.progress * 100); // Backend sends 0-1, frontend uses 0-100
          },
          onStageChange: (data) => {
            console.log("Stage change:", data);
            updateStage(data.newStage as ResearchStage);
          },
          onDocumentFound: (data) => {
            console.log("Document found:", data);
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
            console.log("Metrics update:", data);
            updateMetrics(data.metrics);
          },
          onError: (data) => {
            console.error("Research error:", data);
            updateStage("error");
            addMessage({
              role: "system",
              content: `오류가 발생했습니다: ${data.message}`,
            });
          },
          onCompleted: (data) => {
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
            console.error("SSE connection error:", error);
            setConnectionError(error.message);
            addMessage({
              role: "system",
              content: `서버 연결 오류: ${error.message}. 다시 시도해 주세요.`,
            });
          },
        };

        // Subscribe to SSE events
        sseCleanupRef.current = researchApi.subscribeToResearchEvents(
          sessionId,
          callbacks
        );

        console.log(
          `Research started: session=${sessionId}, estimated=${estimatedDuration}s`
        );
      } catch (error) {
        console.error("Failed to start research:", error);
        setConnectionError((error as Error).message);
        addMessage({
          role: "system",
          content: `리서치 시작 실패: ${(error as Error).message}`,
        });
      }
    },
    [startResearchAction, updateStage, updateProgress, updateMetrics, addDocument, addMessage]
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
    <div className="flex h-[calc(100vh-4rem)] flex-col lg:flex-row">
      {/* Connection Error Banner */}
      {connectionError && (
        <div className="absolute left-0 right-0 top-0 z-50 bg-red-500 p-2 text-center text-white">
          연결 오류: {connectionError}
          <button
            onClick={() => setConnectionError(null)}
            className="ml-4 underline"
          >
            닫기
          </button>
        </div>
      )}

      {/* API Mode Indicator (dev only) */}
      {process.env.NODE_ENV === "development" && (
        <div className="absolute right-4 top-2 z-50 rounded bg-gray-800 px-2 py-1 text-xs text-white">
          {USE_MOCK_API ? "🎭 Mock Mode" : "🔗 API Mode"}
        </div>
      )}

      {/* Chat Zone - 40% on desktop, full width stacked on mobile */}
      <div className="h-1/2 w-full lg:h-full lg:w-2/5 lg:min-w-[400px]">
        <ChatZone
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          disabled={isLoading && session?.stage !== "confirming"}
        />
      </div>

      {/* Progress Zone - 60% on desktop, full width stacked on mobile */}
      <div className="h-1/2 w-full lg:h-full lg:w-3/5">
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
