/**
 * Research Store Tests
 *
 * Tests for Zustand store managing Research Agent state.
 * @CODE:FRONTEND-TEST-001
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { useResearchStore } from "../researchStore";
import type { ResearchStage, DiscoveredDocument } from "@/types/research";

// Reset store before each test
beforeEach(() => {
  useResearchStore.getState().reset();
});

describe("researchStore", () => {
  describe("initial state", () => {
    it("should have null session initially", () => {
      const state = useResearchStore.getState();
      expect(state.session).toBeNull();
    });

    it("should have isLoading as false initially", () => {
      const state = useResearchStore.getState();
      expect(state.isLoading).toBe(false);
    });

    it("should have empty messages array initially", () => {
      const state = useResearchStore.getState();
      expect(state.messages).toEqual([]);
    });

    it("should have empty selection arrays initially", () => {
      const state = useResearchStore.getState();
      expect(state.selectedDocumentIds).toEqual([]);
      expect(state.expandedDocumentIds).toEqual([]);
    });

    it("should have null error initially", () => {
      const state = useResearchStore.getState();
      expect(state.error).toBeNull();
    });
  });

  describe("startResearch", () => {
    it("should create a new session with query", () => {
      const { startResearch } = useResearchStore.getState();
      startResearch("test query");

      const state = useResearchStore.getState();
      expect(state.session).not.toBeNull();
      expect(state.session?.query).toBe("test query");
    });

    it("should set stage to analyzing", () => {
      const { startResearch } = useResearchStore.getState();
      startResearch("test query");

      const state = useResearchStore.getState();
      expect(state.session?.stage).toBe("analyzing");
    });

    it("should set isLoading to true", () => {
      const { startResearch } = useResearchStore.getState();
      startResearch("test query");

      const state = useResearchStore.getState();
      expect(state.isLoading).toBe(true);
    });

    it("should clear any previous error", () => {
      useResearchStore.setState({ error: "previous error" });
      const { startResearch } = useResearchStore.getState();
      startResearch("test query");

      const state = useResearchStore.getState();
      expect(state.error).toBeNull();
    });

    it("should add initial timeline entry", () => {
      const { startResearch } = useResearchStore.getState();
      startResearch("test query");

      const state = useResearchStore.getState();
      expect(state.session?.timeline).toHaveLength(1);
      expect(state.session?.timeline[0].stage).toBe("analyzing");
    });

    it("should add assistant message about starting research", () => {
      const { startResearch } = useResearchStore.getState();
      startResearch("test query");

      const state = useResearchStore.getState();
      expect(state.messages).toHaveLength(1);
      expect(state.messages[0].role).toBe("assistant");
      expect(state.messages[0].content).toContain("test query");
    });

    it("should accept optional config", () => {
      const { startResearch } = useResearchStore.getState();
      const config = { maxDocuments: 10, language: "ko" };
      startResearch("test query", config);

      const state = useResearchStore.getState();
      expect(state.session?.config).toEqual(config);
    });

    it("should generate unique session id", () => {
      // Use fake timers to ensure unique timestamps
      vi.useFakeTimers();
      vi.setSystemTime(new Date("2024-01-01T00:00:00.000Z"));

      const { startResearch } = useResearchStore.getState();
      startResearch("test query");
      const firstId = useResearchStore.getState().session?.id;

      useResearchStore.getState().reset();

      // Advance time to ensure different timestamp
      vi.setSystemTime(new Date("2024-01-01T00:00:01.000Z"));
      startResearch("another query");
      const secondId = useResearchStore.getState().session?.id;

      expect(firstId).not.toBe(secondId);

      vi.useRealTimers();
    });
  });

  describe("cancelResearch", () => {
    it("should set session to null", () => {
      const { startResearch, cancelResearch } = useResearchStore.getState();
      startResearch("test query");
      cancelResearch();

      const state = useResearchStore.getState();
      expect(state.session).toBeNull();
    });

    it("should set isLoading to false", () => {
      const { startResearch, cancelResearch } = useResearchStore.getState();
      startResearch("test query");
      cancelResearch();

      const state = useResearchStore.getState();
      expect(state.isLoading).toBe(false);
    });

    it("should add system message about cancellation", () => {
      const { startResearch, cancelResearch } = useResearchStore.getState();
      startResearch("test query");
      cancelResearch();

      const state = useResearchStore.getState();
      // First message from startResearch, second from cancelResearch
      expect(state.messages).toHaveLength(2);
      expect(state.messages[1].role).toBe("system");
      expect(state.messages[1].content).toContain("취소");
    });
  });

  describe("confirmResearch", () => {
    it("should set stage to completed", () => {
      const { startResearch, confirmResearch } = useResearchStore.getState();
      startResearch("test query");
      confirmResearch();

      const state = useResearchStore.getState();
      expect(state.session?.stage).toBe("completed");
    });

    it("should set isLoading to false", () => {
      const { startResearch, confirmResearch } = useResearchStore.getState();
      startResearch("test query");
      confirmResearch();

      const state = useResearchStore.getState();
      expect(state.isLoading).toBe(false);
    });

    it("should add completedAt timestamp", () => {
      const { startResearch, confirmResearch } = useResearchStore.getState();
      startResearch("test query");
      confirmResearch();

      const state = useResearchStore.getState();
      expect(state.session?.completedAt).toBeDefined();
    });

    it("should add completed stage to timeline", () => {
      const { startResearch, confirmResearch } = useResearchStore.getState();
      startResearch("test query");
      confirmResearch();

      const state = useResearchStore.getState();
      const lastEntry = state.session?.timeline[state.session.timeline.length - 1];
      expect(lastEntry?.stage).toBe("completed");
    });

    it("should do nothing if no session exists", () => {
      const { confirmResearch } = useResearchStore.getState();
      confirmResearch();

      const state = useResearchStore.getState();
      expect(state.session).toBeNull();
    });
  });

  describe("addMessage", () => {
    it("should add message to messages array", () => {
      const { addMessage } = useResearchStore.getState();
      addMessage({ role: "user", content: "Hello" });

      const state = useResearchStore.getState();
      expect(state.messages).toHaveLength(1);
      expect(state.messages[0].content).toBe("Hello");
    });

    it("should generate unique id for each message", () => {
      const { addMessage } = useResearchStore.getState();
      addMessage({ role: "user", content: "First" });
      addMessage({ role: "user", content: "Second" });

      const state = useResearchStore.getState();
      expect(state.messages[0].id).not.toBe(state.messages[1].id);
    });

    it("should add timestamp to message", () => {
      const { addMessage } = useResearchStore.getState();
      addMessage({ role: "user", content: "Test" });

      const state = useResearchStore.getState();
      expect(state.messages[0].timestamp).toBeDefined();
    });

    it("should preserve message role", () => {
      const { addMessage } = useResearchStore.getState();
      addMessage({ role: "assistant", content: "Response" });

      const state = useResearchStore.getState();
      expect(state.messages[0].role).toBe("assistant");
    });
  });

  describe("clearMessages", () => {
    it("should clear all messages", () => {
      const { addMessage, clearMessages } = useResearchStore.getState();
      addMessage({ role: "user", content: "First" });
      addMessage({ role: "user", content: "Second" });
      clearMessages();

      const state = useResearchStore.getState();
      expect(state.messages).toEqual([]);
    });
  });

  describe("updateProgress", () => {
    it("should update session progress", () => {
      const { startResearch, updateProgress } = useResearchStore.getState();
      startResearch("test query");
      updateProgress(50);

      const state = useResearchStore.getState();
      expect(state.session?.progress).toBe(50);
    });

    it("should clamp progress to minimum 0", () => {
      const { startResearch, updateProgress } = useResearchStore.getState();
      startResearch("test query");
      updateProgress(-10);

      const state = useResearchStore.getState();
      expect(state.session?.progress).toBe(0);
    });

    it("should clamp progress to maximum 100", () => {
      const { startResearch, updateProgress } = useResearchStore.getState();
      startResearch("test query");
      updateProgress(150);

      const state = useResearchStore.getState();
      expect(state.session?.progress).toBe(100);
    });

    it("should do nothing if no session exists", () => {
      const { updateProgress } = useResearchStore.getState();
      updateProgress(50);

      const state = useResearchStore.getState();
      expect(state.session).toBeNull();
    });
  });

  describe("updateStage", () => {
    it("should update session stage", () => {
      const { startResearch, updateStage } = useResearchStore.getState();
      startResearch("test query");
      updateStage("searching");

      const state = useResearchStore.getState();
      expect(state.session?.stage).toBe("searching");
    });

    it("should add new stage to timeline", () => {
      const { startResearch, updateStage } = useResearchStore.getState();
      startResearch("test query");
      updateStage("searching");

      const state = useResearchStore.getState();
      expect(state.session?.timeline).toHaveLength(2);
      expect(state.session?.timeline[1].stage).toBe("searching");
    });

    it("should complete previous stage in timeline", () => {
      const { startResearch, updateStage } = useResearchStore.getState();
      startResearch("test query");
      updateStage("searching");

      const state = useResearchStore.getState();
      expect(state.session?.timeline[0].completedAt).toBeDefined();
    });

    it("should set isLoading to false for terminal stages", () => {
      const terminalStages: ResearchStage[] = ["completed", "error", "confirming"];

      for (const stage of terminalStages) {
        useResearchStore.getState().reset();
        const { startResearch, updateStage } = useResearchStore.getState();
        startResearch("test query");
        updateStage(stage);

        const state = useResearchStore.getState();
        expect(state.isLoading).toBe(false);
      }
    });

    it("should keep isLoading true for non-terminal stages", () => {
      const nonTerminalStages: ResearchStage[] = ["analyzing", "searching", "collecting", "organizing"];

      for (const stage of nonTerminalStages) {
        useResearchStore.getState().reset();
        const { startResearch, updateStage } = useResearchStore.getState();
        startResearch("test query");
        updateStage(stage);

        const state = useResearchStore.getState();
        expect(state.isLoading).toBe(true);
      }
    });
  });

  describe("updateMetrics", () => {
    it("should update session metrics", () => {
      const { startResearch, updateMetrics } = useResearchStore.getState();
      startResearch("test query");
      updateMetrics({ sourcesSearched: 5, documentsFound: 10 });

      const state = useResearchStore.getState();
      expect(state.session?.metrics.sourcesSearched).toBe(5);
      expect(state.session?.metrics.documentsFound).toBe(10);
    });

    it("should merge partial metrics", () => {
      const { startResearch, updateMetrics } = useResearchStore.getState();
      startResearch("test query");
      updateMetrics({ sourcesSearched: 5 });
      updateMetrics({ qualityScore: 85 });

      const state = useResearchStore.getState();
      expect(state.session?.metrics.sourcesSearched).toBe(5);
      expect(state.session?.metrics.qualityScore).toBe(85);
    });
  });

  describe("addDocument", () => {
    it("should add document to session documents", () => {
      const { startResearch, addDocument } = useResearchStore.getState();
      startResearch("test query");

      const doc: DiscoveredDocument = {
        id: "doc-1",
        title: "Test Document",
        url: "https://example.com",
        snippet: "Test snippet",
        source: "web",
        confidence: 0.9,
        discoveredAt: new Date(),
      };
      addDocument(doc);

      const state = useResearchStore.getState();
      expect(state.session?.documents).toHaveLength(1);
      expect(state.session?.documents[0].id).toBe("doc-1");
    });

    it("should increment documentsFound metric", () => {
      const { startResearch, addDocument } = useResearchStore.getState();
      startResearch("test query");

      const doc: DiscoveredDocument = {
        id: "doc-1",
        title: "Test Document",
        url: "https://example.com",
        snippet: "Test snippet",
        source: "web",
        confidence: 0.9,
        discoveredAt: new Date(),
      };
      addDocument(doc);

      const state = useResearchStore.getState();
      expect(state.session?.metrics.documentsFound).toBe(1);
    });
  });

  describe("document selection", () => {
    it("should toggle document selection on", () => {
      const { toggleDocumentSelection } = useResearchStore.getState();
      toggleDocumentSelection("doc-1");

      const state = useResearchStore.getState();
      expect(state.selectedDocumentIds).toContain("doc-1");
    });

    it("should toggle document selection off", () => {
      useResearchStore.setState({ selectedDocumentIds: ["doc-1"] });
      const { toggleDocumentSelection } = useResearchStore.getState();
      toggleDocumentSelection("doc-1");

      const state = useResearchStore.getState();
      expect(state.selectedDocumentIds).not.toContain("doc-1");
    });

    it("should select all documents", () => {
      const { startResearch, addDocument, selectAllDocuments } = useResearchStore.getState();
      startResearch("test query");

      addDocument({
        id: "doc-1",
        title: "Doc 1",
        url: "https://example.com/1",
        snippet: "Snippet 1",
        source: "web",
        confidence: 0.9,
        discoveredAt: new Date(),
      });
      addDocument({
        id: "doc-2",
        title: "Doc 2",
        url: "https://example.com/2",
        snippet: "Snippet 2",
        source: "web",
        confidence: 0.8,
        discoveredAt: new Date(),
      });

      selectAllDocuments();

      const state = useResearchStore.getState();
      expect(state.selectedDocumentIds).toContain("doc-1");
      expect(state.selectedDocumentIds).toContain("doc-2");
    });

    it("should deselect all documents", () => {
      useResearchStore.setState({ selectedDocumentIds: ["doc-1", "doc-2"] });
      const { deselectAllDocuments } = useResearchStore.getState();
      deselectAllDocuments();

      const state = useResearchStore.getState();
      expect(state.selectedDocumentIds).toEqual([]);
    });
  });

  describe("document expand", () => {
    it("should toggle document expand on", () => {
      const { toggleDocumentExpand } = useResearchStore.getState();
      toggleDocumentExpand("doc-1");

      const state = useResearchStore.getState();
      expect(state.expandedDocumentIds).toContain("doc-1");
    });

    it("should toggle document expand off", () => {
      useResearchStore.setState({ expandedDocumentIds: ["doc-1"] });
      const { toggleDocumentExpand } = useResearchStore.getState();
      toggleDocumentExpand("doc-1");

      const state = useResearchStore.getState();
      expect(state.expandedDocumentIds).not.toContain("doc-1");
    });
  });

  describe("reset", () => {
    it("should reset all state to initial values", () => {
      const { startResearch, addMessage, toggleDocumentSelection, reset } =
        useResearchStore.getState();

      startResearch("test query");
      addMessage({ role: "user", content: "Hello" });
      toggleDocumentSelection("doc-1");

      reset();

      const state = useResearchStore.getState();
      expect(state.session).toBeNull();
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
      expect(state.messages).toEqual([]);
      expect(state.selectedDocumentIds).toEqual([]);
      expect(state.expandedDocumentIds).toEqual([]);
    });
  });
});
