"use client";

/**
 * ProgressZone Component
 * Ethereal Glass Aesthetic
 *
 * Progress dashboard for Research Agent showing stages, metrics, and results.
 * @CODE:FRONTEND-UX-002
 */

// React imports (useMemo reserved for future optimization)
import {
  Search,
  FileText,
  FolderTree,
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { DocumentPreview } from "./DocumentPreview";
import type { ResearchSession, ResearchStage, StageInfo } from "@/types/research";

// ============================================================================
// Props
// ============================================================================

interface ProgressZoneProps {
  session: ResearchSession | null;
  selectedDocumentIds: string[];
  expandedDocumentIds: string[];
  onConfirm?: () => void;
  onCancel?: () => void;
  onRetry?: () => void;
  onDocumentSelect?: (id: string) => void;
  onDocumentExpand?: (id: string) => void;
  onSelectAll?: () => void;
  onDeselectAll?: () => void;
}

// ============================================================================
// Stage Configuration
// ============================================================================

const STAGE_CONFIG: Record<
  ResearchStage,
  { icon: typeof Search; color: string; label: string }
> = {
  idle: { icon: Sparkles, color: "text-white/40", label: "대기 중" },
  analyzing: { icon: Sparkles, color: "text-blue-400", label: "분석 중" },
  searching: { icon: Search, color: "text-blue-400", label: "검색 중" },
  collecting: { icon: FileText, color: "text-amber-400", label: "수집 중" },
  organizing: { icon: FolderTree, color: "text-purple-400", label: "정리 중" },
  confirming: { icon: CheckCircle2, color: "text-green-400", label: "확인 대기" },
  completed: { icon: CheckCircle2, color: "text-green-400", label: "완료" },
  error: { icon: XCircle, color: "text-red-400", label: "오류" },
};

const STAGE_ORDER: ResearchStage[] = [
  "analyzing",
  "searching",
  "collecting",
  "organizing",
  "confirming",
];

// ============================================================================
// Circular Progress Component
// ============================================================================

function CircularProgress({ progress, size = 180 }: { progress: number; size?: number }) {
  const strokeWidth = 12;
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (progress / 100) * circumference;

  return (
    <div
      className="relative inline-flex items-center justify-center"
      role="progressbar"
      aria-valuenow={Math.round(progress)}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={`진행률 ${Math.round(progress)}%`}
    >
      {/* Glow effect behind the circle */}
      <div className="absolute inset-0 bg-blue-500/20 blur-3xl rounded-full" />

      <svg width={size} height={size} className="-rotate-90 relative z-10" aria-hidden="true">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-white/10"
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="text-blue-500 transition-all duration-500 drop-shadow-[0_0_10px_rgba(59,130,246,0.5)]"
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center z-10">
        <span className="text-4xl font-bold text-white drop-shadow-lg">{Math.round(progress)}%</span>
        <span className="text-sm text-white/60">진행률</span>
      </div>
    </div>
  );
}

// ============================================================================
// Stage Timeline Component
// ============================================================================

function StageTimeline({
  currentStage,
  timeline,
}: {
  currentStage: ResearchStage;
  timeline: StageInfo[];
}) {
  const currentIndex = STAGE_ORDER.indexOf(currentStage);

  return (
    <div className="flex items-center justify-between px-2">
      {STAGE_ORDER.map((stage, index) => {
        const config = STAGE_CONFIG[stage];
        const Icon = config.icon;
        const isActive = stage === currentStage;
        const isCompleted = currentIndex > index || currentStage === "completed";
        const isPending = currentIndex < index;

        return (
          <div key={stage} className="flex flex-1 items-center">
            <div className="flex flex-col items-center relative">
              <div
                className={cn(
                  "flex h-10 w-10 items-center justify-center rounded-full border-2 transition-all duration-300 relative z-10",
                  isCompleted && "border-green-500/50 bg-green-500/20 shadow-[0_0_15px_rgba(34,197,94,0.3)]",
                  isActive && "border-blue-500 bg-blue-500/20 shadow-[0_0_20px_rgba(59,130,246,0.5)] scale-110",
                  isPending && "border-white/10 bg-white/5"
                )}
              >
                <Icon
                  className={cn(
                    "h-5 w-5 transition-colors duration-300",
                    isCompleted && "text-green-400",
                    isActive && "text-blue-400",
                    isPending && "text-white/20"
                  )}
                />
              </div>
              <span
                className={cn(
                  "mt-3 text-xs transition-colors duration-300 absolute -bottom-6 w-max text-center",
                  isActive ? "font-medium text-white drop-shadow-md" : "text-white/40"
                )}
              >
                {config.label}
              </span>
            </div>
            {index < STAGE_ORDER.length - 1 && (
              <div
                className={cn(
                  "h-0.5 flex-1 mx-2 transition-colors duration-500",
                  isCompleted ? "bg-green-500/50 shadow-[0_0_5px_rgba(34,197,94,0.3)]" : "bg-white/10"
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ============================================================================
// Metrics Cards Component
// ============================================================================

function MetricsCards({
  sourcesSearched,
  documentsFound,
  qualityScore,
  estimatedTime,
}: {
  sourcesSearched: number;
  documentsFound: number;
  qualityScore: number;
  estimatedTime?: number;
}) {
  const metrics = [
    {
      label: "검색된 소스",
      value: sourcesSearched,
      icon: Search,
      color: "text-blue-400",
      bgColor: "bg-blue-500/10",
      borderColor: "border-blue-500/20",
    },
    {
      label: "발견된 문서",
      value: documentsFound,
      icon: FileText,
      color: "text-amber-400",
      bgColor: "bg-amber-500/10",
      borderColor: "border-amber-500/20",
    },
    {
      label: "품질 점수",
      value: `${Math.round(qualityScore * 100)}%`,
      icon: Sparkles,
      color: "text-purple-400",
      bgColor: "bg-purple-500/10",
      borderColor: "border-purple-500/20",
    },
    ...(estimatedTime !== undefined
      ? [
        {
          label: "예상 시간",
          value: `${Math.ceil(estimatedTime / 60)}분`,
          icon: Clock,
          color: "text-green-400",
          bgColor: "bg-green-500/10",
          borderColor: "border-green-500/20",
        },
      ]
      : []),
  ];

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      {metrics.map((metric) => {
        const Icon = metric.icon;
        return (
          <div
            key={metric.label}
            className={cn(
              "p-4 rounded-xl border backdrop-blur-sm transition-all hover:bg-white/5",
              metric.bgColor,
              metric.borderColor
            )}
          >
            <div className="flex items-center gap-2 mb-2">
              <Icon className={cn("h-4 w-4", metric.color)} />
              <span className="text-xs text-white/60">{metric.label}</span>
            </div>
            <p className="text-2xl font-bold text-white drop-shadow-sm">{metric.value}</p>
          </div>
        );
      })}
    </div>
  );
}

// ============================================================================
// Empty State Component
// ============================================================================

function EmptyState() {
  return (
    <div className="flex h-full flex-col items-center justify-center text-center p-8">
      <div className="rounded-full bg-white/5 p-8 mb-6 border border-white/10 shadow-glass animate-pulse-slow">
        <Search className="h-12 w-12 text-white/20" />
      </div>
      <h3 className="text-xl font-medium text-white mb-2">리서치 대기 중</h3>
      <p className="max-w-sm text-sm text-white/40 leading-relaxed">
        왼쪽 채팅 영역에서 원하는 지식 영역을 입력하면<br />자동으로 관련 자료를 수집하고 분석합니다.
      </p>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function ProgressZone({
  session,
  selectedDocumentIds = [],
  expandedDocumentIds = [],
  onConfirm,
  onCancel,
  onRetry,
  onDocumentSelect,
  onDocumentExpand,
  onSelectAll,
  onDeselectAll,
}: ProgressZoneProps) {
  const isIdle = !session || session.stage === "idle";
  const isError = session?.stage === "error";
  const isConfirming = session?.stage === "confirming";
  const isCompleted = session?.stage === "completed";
  const isInProgress = session && !isIdle && !isError && !isCompleted;

  if (isIdle) {
    return (
      <div
        className="flex h-full flex-col"
        role="region"
        aria-label="리서치 진행 상황"
      >
        <header className="border-b border-white/10 px-6 py-4 bg-white/5 backdrop-blur-md">
          <h2 className="text-lg font-semibold text-white">진행 상황</h2>
        </header>
        <div className="flex-1">
          <EmptyState />
        </div>
      </div>
    );
  }

  return (
    <div
      className="flex h-full flex-col"
      role="region"
      aria-label="리서치 진행 상황"
      aria-live="polite"
    >
      {/* Header */}
      <header className="border-b border-white/10 px-6 py-4 bg-white/5 backdrop-blur-md">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white" id="progress-title">진행 상황</h2>
          {session && (
            <span
              role="status"
              aria-label={`현재 상태: ${STAGE_CONFIG[session.stage].label}`}
              className={cn(
                "rounded-full px-3 py-1 text-xs font-medium border backdrop-blur-sm shadow-sm",
                isError && "bg-red-500/10 text-red-400 border-red-500/20",
                isCompleted && "bg-green-500/10 text-green-400 border-green-500/20",
                isInProgress && "bg-blue-500/10 text-blue-400 border-blue-500/20 animate-pulse"
              )}
            >
              {STAGE_CONFIG[session.stage].label}
            </span>
          )}
        </div>
      </header>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 custom-scrollbar space-y-8">
        {/* Circular Progress */}
        <div className="flex justify-center py-6">
          <CircularProgress progress={session?.progress || 0} />
        </div>

        {/* Stage Timeline */}
        <div className="bg-white/5 rounded-2xl p-6 border border-white/10 shadow-glass">
          <h3 className="text-sm font-medium text-white/80 mb-6 px-2">진행 단계</h3>
          <div className="pb-4">
            <StageTimeline
              currentStage={session?.stage || "idle"}
              timeline={session?.timeline || []}
            />
          </div>
        </div>

        {/* Metrics */}
        <MetricsCards
          sourcesSearched={session?.metrics.sourcesSearched || 0}
          documentsFound={session?.metrics.documentsFound || 0}
          qualityScore={session?.metrics.qualityScore || 0}
          estimatedTime={session?.metrics.estimatedTimeRemaining}
        />

        {/* Error State */}
        {isError && session?.error && (
          <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 backdrop-blur-sm">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-red-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-red-300">오류가 발생했습니다</p>
                <p className="mt-1 text-sm text-red-400/80">{session.error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Document Preview */}
        {(session?.documents.length || 0) > 0 && (
          <div className="bg-white/5 rounded-2xl border border-white/10 shadow-glass overflow-hidden">
            <div className="px-6 py-4 border-b border-white/10">
              <h3 className="text-sm font-medium text-white/80">수집된 문서</h3>
            </div>
            <div className="p-4">
              <DocumentPreview
                documents={session?.documents || []}
                selectedIds={selectedDocumentIds}
                expandedIds={expandedDocumentIds}
                onSelect={onDocumentSelect || (() => { })}
                onExpand={onDocumentExpand || (() => { })}
                onSelectAll={onSelectAll || (() => { })}
                onDeselectAll={onDeselectAll || (() => { })}
              />
            </div>
          </div>
        )}
      </div>

      {/* Actions */}
      {(isConfirming || isError) && (
        <div className="border-t border-white/10 p-6 bg-white/5 backdrop-blur-md">
          <div className="flex gap-3">
            {isConfirming && (
              <>
                <Button
                  variant="outline"
                  className="flex-1 bg-white/5 border-white/10 text-white hover:bg-white/10 hover:text-white"
                  onClick={onCancel}
                >
                  취소
                </Button>
                <Button
                  className="flex-1 bg-green-600 hover:bg-green-500 text-white shadow-lg shadow-green-500/20 border-none"
                  onClick={onConfirm}
                >
                  확인 및 저장
                </Button>
              </>
            )}
            {isError && (
              <>
                <Button
                  variant="outline"
                  className="flex-1 bg-white/5 border-white/10 text-white hover:bg-white/10 hover:text-white"
                  onClick={onCancel}
                >
                  취소
                </Button>
                <Button
                  className="flex-1 bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/20 border-none"
                  onClick={onRetry}
                >
                  다시 시도
                </Button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default ProgressZone;
