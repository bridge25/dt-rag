"use client";

/**
 * Research Agent Page
 *
 * Main page for the Research Agent interface with split layout.
 * Left: ChatZone (40%) - Natural language interaction
 * Right: ProgressZone (60%) - Real-time progress and results
 *
 * @CODE:FRONTEND-UX-001
 */

import { useCallback } from "react";
import { ChatZone } from "@/components/research/ChatZone";
import { ProgressZone } from "@/components/research/ProgressZone";
import {
  useResearchStore,
  selectSession,
  selectMessages,
  selectIsLoading,
} from "@/stores/researchStore";

// ============================================================================
// Page Component
// ============================================================================

export default function ResearchPage() {
  // Store selectors
  const session = useResearchStore(selectSession);
  const messages = useResearchStore(selectMessages);
  const isLoading = useResearchStore(selectIsLoading);

  // Actions
  const startResearch = useResearchStore((state) => state.startResearch);
  const addMessage = useResearchStore((state) => state.addMessage);
  const confirmResearch = useResearchStore((state) => state.confirmResearch);
  const cancelResearch = useResearchStore((state) => state.cancelResearch);

  // Handlers
  const handleSendMessage = useCallback(
    (content: string) => {
      // Add user message
      addMessage({ role: "user", content });

      // If no active session, start research
      if (!session || session.stage === "idle" || session.stage === "completed") {
        startResearch(content);

        // Simulate progress updates (will be replaced by WebSocket)
        simulateResearchProgress();
      }
    },
    [session, addMessage, startResearch]
  );

  const handleConfirm = useCallback(() => {
    confirmResearch();
  }, [confirmResearch]);

  const handleCancel = useCallback(() => {
    cancelResearch();
  }, [cancelResearch]);

  const handleRetry = useCallback(() => {
    if (session?.query) {
      startResearch(session.query);
      simulateResearchProgress();
    }
  }, [session, startResearch]);

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col lg:flex-row">
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
          onConfirm={handleConfirm}
          onCancel={handleCancel}
          onRetry={handleRetry}
        />
      </div>
    </div>
  );
}

// ============================================================================
// Mock Progress Simulation (temporary - will be replaced by WebSocket)
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
