/**
 * Research Agent Store
 *
 * Zustand store for managing Research Agent state.
 * @CODE:FRONTEND-UX-001
 */

import { create } from "zustand";
import { devtools } from "zustand/middleware";
import type {
  ResearchSession,
  ResearchStage,
  ChatMessage,
  DiscoveredDocument,
  ResearchMetrics,
  StageInfo,
  ResearchConfig,
} from "@/types/research";

// ============================================================================
// Store State Interface
// ============================================================================

interface ResearchState {
  // Session State
  session: ResearchSession | null;
  isLoading: boolean;
  error: string | null;

  // Chat State
  messages: ChatMessage[];

  // UI State
  selectedDocumentIds: string[];
  expandedDocumentIds: string[];

  // Actions
  startResearch: (query: string, config?: ResearchConfig) => void;
  cancelResearch: () => void;
  confirmResearch: () => void;

  // Chat Actions
  addMessage: (message: Omit<ChatMessage, "id" | "timestamp">) => void;
  clearMessages: () => void;

  // Progress Actions
  updateProgress: (progress: number) => void;
  updateStage: (stage: ResearchStage) => void;
  updateMetrics: (metrics: Partial<ResearchMetrics>) => void;
  addDocument: (document: DiscoveredDocument) => void;

  // Document Selection
  toggleDocumentSelection: (id: string) => void;
  selectAllDocuments: () => void;
  deselectAllDocuments: () => void;
  toggleDocumentExpand: (id: string) => void;

  // Reset
  reset: () => void;
}

// ============================================================================
// Initial State
// ============================================================================

const initialSession: ResearchSession = {
  id: "",
  query: "",
  stage: "idle",
  progress: 0,
  metrics: {
    sourcesSearched: 0,
    documentsFound: 0,
    qualityScore: 0,
  },
  config: {},
  documents: [],
  timeline: [],
  startedAt: new Date(),
};

const STAGE_LABELS: Record<ResearchStage, { label: string; description: string }> = {
  idle: { label: "대기 중", description: "리서치 쿼리를 입력해 주세요" },
  analyzing: { label: "분석 중", description: "쿼리를 분석하고 있습니다" },
  searching: { label: "검색 중", description: "관련 소스를 검색하고 있습니다" },
  collecting: { label: "수집 중", description: "문서를 수집하고 있습니다" },
  organizing: { label: "정리 중", description: "카테고리를 구성하고 있습니다" },
  confirming: { label: "확인 대기", description: "결과를 확인해 주세요" },
  completed: { label: "완료", description: "리서치가 완료되었습니다" },
  error: { label: "오류", description: "문제가 발생했습니다" },
};

// ============================================================================
// Helper Functions
// ============================================================================

const generateId = () => `msg_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;

const createStageInfo = (stage: ResearchStage): StageInfo => ({
  stage,
  label: STAGE_LABELS[stage].label,
  description: STAGE_LABELS[stage].description,
  startedAt: new Date(),
});

// ============================================================================
// Store Implementation
// ============================================================================

export const useResearchStore = create<ResearchState>()(
  devtools(
    (set, get) => ({
      // Initial State
      session: null,
      isLoading: false,
      error: null,
      messages: [],
      selectedDocumentIds: [],
      expandedDocumentIds: [],

      // Start Research
      startResearch: (query: string, config?: ResearchConfig) => {
        const sessionId = `research_${Date.now()}`;

        set({
          session: {
            ...initialSession,
            id: sessionId,
            query,
            stage: "analyzing",
            config: config || {},
            startedAt: new Date(),
            timeline: [createStageInfo("analyzing")],
          },
          isLoading: true,
          error: null,
        });

        // Add assistant message
        get().addMessage({
          role: "assistant",
          content: `"${query}"에 대한 리서치를 시작합니다. 관련 자료를 수집하겠습니다.`,
        });
      },

      // Cancel Research
      cancelResearch: () => {
        set({
          session: null,
          isLoading: false,
        });

        get().addMessage({
          role: "system",
          content: "리서치가 취소되었습니다.",
        });
      },

      // Confirm Research
      confirmResearch: () => {
        const { session, selectedDocumentIds } = get();
        if (!session) return;

        set((state) => ({
          session: state.session
            ? {
                ...state.session,
                stage: "completed",
                completedAt: new Date(),
                timeline: [
                  ...state.session.timeline,
                  createStageInfo("completed"),
                ],
              }
            : null,
          isLoading: false,
        }));

        get().addMessage({
          role: "assistant",
          content: `${selectedDocumentIds.length}개의 문서가 지식 베이스에 추가되었습니다.`,
        });
      },

      // Add Chat Message
      addMessage: (message) => {
        set((state) => ({
          messages: [
            ...state.messages,
            {
              ...message,
              id: generateId(),
              timestamp: new Date(),
            },
          ],
        }));
      },

      // Clear Messages
      clearMessages: () => {
        set({ messages: [] });
      },

      // Update Progress
      updateProgress: (progress: number) => {
        set((state) => ({
          session: state.session
            ? { ...state.session, progress: Math.min(100, Math.max(0, progress)) }
            : null,
        }));
      },

      // Update Stage
      updateStage: (stage: ResearchStage) => {
        set((state) => {
          if (!state.session) return state;

          const updatedTimeline = [...state.session.timeline];
          const lastStage = updatedTimeline[updatedTimeline.length - 1];

          if (lastStage && !lastStage.completedAt) {
            lastStage.completedAt = new Date();
          }

          updatedTimeline.push(createStageInfo(stage));

          return {
            session: {
              ...state.session,
              stage,
              timeline: updatedTimeline,
            },
            isLoading: stage !== "completed" && stage !== "error" && stage !== "confirming",
          };
        });
      },

      // Update Metrics
      updateMetrics: (metrics: Partial<ResearchMetrics>) => {
        set((state) => ({
          session: state.session
            ? {
                ...state.session,
                metrics: { ...state.session.metrics, ...metrics },
              }
            : null,
        }));
      },

      // Add Document
      addDocument: (document: DiscoveredDocument) => {
        set((state) => ({
          session: state.session
            ? {
                ...state.session,
                documents: [...state.session.documents, document],
                metrics: {
                  ...state.session.metrics,
                  documentsFound: state.session.documents.length + 1,
                },
              }
            : null,
        }));
      },

      // Toggle Document Selection
      toggleDocumentSelection: (id: string) => {
        set((state) => ({
          selectedDocumentIds: state.selectedDocumentIds.includes(id)
            ? state.selectedDocumentIds.filter((i) => i !== id)
            : [...state.selectedDocumentIds, id],
        }));
      },

      // Select All Documents
      selectAllDocuments: () => {
        const { session } = get();
        if (!session) return;

        set({
          selectedDocumentIds: session.documents.map((d) => d.id),
        });
      },

      // Deselect All Documents
      deselectAllDocuments: () => {
        set({ selectedDocumentIds: [] });
      },

      // Toggle Document Expand
      toggleDocumentExpand: (id: string) => {
        set((state) => ({
          expandedDocumentIds: state.expandedDocumentIds.includes(id)
            ? state.expandedDocumentIds.filter((i) => i !== id)
            : [...state.expandedDocumentIds, id],
        }));
      },

      // Reset
      reset: () => {
        set({
          session: null,
          isLoading: false,
          error: null,
          messages: [],
          selectedDocumentIds: [],
          expandedDocumentIds: [],
        });
      },
    }),
    { name: "research-store" }
  )
);

// ============================================================================
// Selectors
// ============================================================================

export const selectSession = (state: ResearchState) => state.session;
export const selectMessages = (state: ResearchState) => state.messages;
export const selectIsLoading = (state: ResearchState) => state.isLoading;
export const selectCurrentStage = (state: ResearchState) => state.session?.stage || "idle";
export const selectProgress = (state: ResearchState) => state.session?.progress || 0;
export const selectMetrics = (state: ResearchState) => state.session?.metrics;
export const selectDocuments = (state: ResearchState) => state.session?.documents || [];
export const selectSelectedDocumentIds = (state: ResearchState) => state.selectedDocumentIds;
