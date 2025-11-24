/**
 * Research Agent Types
 *
 * Type definitions for the Research Agent interface.
 * @CODE:FRONTEND-UX-001
 */

// ============================================================================
// State Types
// ============================================================================

export type ResearchStage =
  | "idle"
  | "analyzing"
  | "searching"
  | "collecting"
  | "organizing"
  | "confirming"
  | "completed"
  | "error";

export interface ResearchMetrics {
  sourcesSearched: number;
  documentsFound: number;
  qualityScore: number;
  estimatedTimeRemaining?: number;
}

export interface StageInfo {
  stage: ResearchStage;
  label: string;
  description: string;
  startedAt?: Date;
  completedAt?: Date;
}

// ============================================================================
// Chat Types
// ============================================================================

export type MessageRole = "user" | "assistant" | "system";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  metadata?: {
    suggestedActions?: string[];
    isLoading?: boolean;
  };
}

export interface ChatSuggestion {
  id: string;
  text: string;
  category: "example" | "action" | "clarification";
}

// ============================================================================
// Document Types
// ============================================================================

export interface SourceInfo {
  id: string;
  name: string;
  type: "web" | "pdf" | "api" | "database";
  url?: string;
  reliability: "high" | "medium" | "low";
}

export interface DiscoveredDocument {
  id: string;
  title: string;
  source: SourceInfo;
  snippet: string;
  relevanceScore: number;
  collectedAt: Date;
  categories?: string[];
}

export interface DocumentPreview {
  document: DiscoveredDocument;
  isSelected: boolean;
  isExpanded: boolean;
}

// ============================================================================
// Research Session Types
// ============================================================================

export interface ResearchConfig {
  maxDocuments?: number;
  qualityThreshold?: number;
  sourcesFilter?: string[];
  depthLevel?: "shallow" | "medium" | "deep";
}

export interface ResearchSession {
  id: string;
  query: string;
  stage: ResearchStage;
  progress: number;
  metrics: ResearchMetrics;
  config: ResearchConfig;
  documents: DiscoveredDocument[];
  timeline: StageInfo[];
  startedAt: Date;
  completedAt?: Date;
  error?: string;
}

// ============================================================================
// API Types
// ============================================================================

export interface StartResearchRequest {
  query: string;
  config?: ResearchConfig;
}

export interface StartResearchResponse {
  sessionId: string;
  estimatedDuration: number;
}

export interface ResearchStatusResponse {
  session: ResearchSession;
}

export interface ConfirmResearchRequest {
  sessionId: string;
  selectedDocumentIds: string[];
  taxonomyId?: string;
}

export interface ConfirmResearchResponse {
  success: boolean;
  documentsImported: number;
  taxonomyUpdated: boolean;
}

// ============================================================================
// WebSocket Event Types
// ============================================================================

export type ResearchEventType =
  | "progress"
  | "stage_change"
  | "document_found"
  | "metrics_update"
  | "error"
  | "completed";

export interface ResearchEvent {
  type: ResearchEventType;
  sessionId: string;
  timestamp: Date;
  data: ResearchProgressData | StageChangeData | DocumentFoundData | MetricsUpdateData | ErrorData | CompletedData;
}

export interface ResearchProgressData {
  progress: number;
  currentSource?: string;
}

export interface StageChangeData {
  previousStage: ResearchStage;
  newStage: ResearchStage;
}

export interface DocumentFoundData {
  document: DiscoveredDocument;
  totalCount: number;
}

export interface MetricsUpdateData {
  metrics: ResearchMetrics;
}

export interface ErrorData {
  message: string;
  recoverable: boolean;
  retryAction?: string;
}

export interface CompletedData {
  totalDocuments: number;
  suggestedCategories: string[];
  qualityScore: number;
}

// ============================================================================
// Component Props Types
// ============================================================================

export interface ChatZoneProps {
  messages: ChatMessage[];
  onSendMessage: (content: string) => void;
  suggestions?: ChatSuggestion[];
  isLoading?: boolean;
  disabled?: boolean;
}

export interface ProgressZoneProps {
  session: ResearchSession | null;
  onConfirm?: () => void;
  onCancel?: () => void;
  onRetry?: () => void;
}

export interface StageTimelineProps {
  stages: StageInfo[];
  currentStage: ResearchStage;
}

export interface MetricsCardProps {
  metrics: ResearchMetrics;
  isAnimated?: boolean;
}

export interface DocumentPreviewProps {
  documents: DiscoveredDocument[];
  onSelect: (id: string) => void;
  onExpand: (id: string) => void;
  selectedIds: string[];
}
