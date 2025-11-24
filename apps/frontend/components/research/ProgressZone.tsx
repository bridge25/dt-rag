"use client";

/**
 * ProgressZone Component
 *
 * Progress dashboard for Research Agent showing stages, metrics, and results.
 * @CODE:FRONTEND-UX-001
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
import type { ResearchSession, ResearchStage, StageInfo } from "@/types/research";

// ============================================================================
// Props
// ============================================================================

interface ProgressZoneProps {
  session: ResearchSession | null;
  onConfirm?: () => void;
  onCancel?: () => void;
  onRetry?: () => void;
}

// ============================================================================
// Stage Configuration
// ============================================================================

const STAGE_CONFIG: Record<
  ResearchStage,
  { icon: typeof Search; color: string; label: string }
> = {
  idle: { icon: Sparkles, color: "text-muted-foreground", label: "대기 중" },
  analyzing: { icon: Sparkles, color: "text-blue-500", label: "분석 중" },
  searching: { icon: Search, color: "text-blue-500", label: "검색 중" },
  collecting: { icon: FileText, color: "text-amber-500", label: "수집 중" },
  organizing: { icon: FolderTree, color: "text-purple-500", label: "정리 중" },
  confirming: { icon: CheckCircle2, color: "text-green-500", label: "확인 대기" },
  completed: { icon: CheckCircle2, color: "text-green-500", label: "완료" },
  error: { icon: XCircle, color: "text-red-500", label: "오류" },
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
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="-rotate-90">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-secondary"
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
          className="text-primary transition-all duration-500"
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center">
        <span className="text-4xl font-bold">{Math.round(progress)}%</span>
        <span className="text-sm text-muted-foreground">진행률</span>
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
    <div className="flex items-center justify-between">
      {STAGE_ORDER.map((stage, index) => {
        const config = STAGE_CONFIG[stage];
        const Icon = config.icon;
        const isActive = stage === currentStage;
        const isCompleted = currentIndex > index || currentStage === "completed";
        const isPending = currentIndex < index;

        return (
          <div key={stage} className="flex flex-1 items-center">
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  "flex h-10 w-10 items-center justify-center rounded-full border-2 transition-colors",
                  isCompleted && "border-green-500 bg-green-500/10",
                  isActive && "border-primary bg-primary/10 animate-pulse",
                  isPending && "border-muted bg-muted/50"
                )}
              >
                <Icon
                  className={cn(
                    "h-5 w-5",
                    isCompleted && "text-green-500",
                    isActive && "text-primary",
                    isPending && "text-muted-foreground"
                  )}
                />
              </div>
              <span
                className={cn(
                  "mt-2 text-xs",
                  isActive ? "font-medium text-foreground" : "text-muted-foreground"
                )}
              >
                {config.label}
              </span>
            </div>
            {index < STAGE_ORDER.length - 1 && (
              <div
                className={cn(
                  "h-0.5 flex-1 mx-2",
                  isCompleted ? "bg-green-500" : "bg-muted"
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
      color: "text-blue-500",
    },
    {
      label: "발견된 문서",
      value: documentsFound,
      icon: FileText,
      color: "text-amber-500",
    },
    {
      label: "품질 점수",
      value: `${Math.round(qualityScore * 100)}%`,
      icon: Sparkles,
      color: "text-purple-500",
    },
    ...(estimatedTime !== undefined
      ? [
          {
            label: "예상 시간",
            value: `${Math.ceil(estimatedTime / 60)}분`,
            icon: Clock,
            color: "text-green-500",
          },
        ]
      : []),
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {metrics.map((metric) => {
        const Icon = metric.icon;
        return (
          <Card key={metric.label} className="p-3">
            <div className="flex items-center gap-2">
              <Icon className={cn("h-4 w-4", metric.color)} />
              <span className="text-xs text-muted-foreground">{metric.label}</span>
            </div>
            <p className="mt-1 text-xl font-semibold">{metric.value}</p>
          </Card>
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
    <div className="flex h-full flex-col items-center justify-center text-center">
      <div className="rounded-full bg-secondary p-6">
        <Search className="h-12 w-12 text-muted-foreground" />
      </div>
      <h3 className="mt-6 text-lg font-medium">리서치 대기 중</h3>
      <p className="mt-2 max-w-sm text-sm text-muted-foreground">
        왼쪽 채팅 영역에서 원하는 지식 영역을 입력하면 자동으로 관련 자료를 수집합니다.
      </p>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function ProgressZone({
  session,
  onConfirm,
  onCancel,
  onRetry,
}: ProgressZoneProps) {
  const isIdle = !session || session.stage === "idle";
  const isError = session?.stage === "error";
  const isConfirming = session?.stage === "confirming";
  const isCompleted = session?.stage === "completed";
  const isInProgress = session && !isIdle && !isError && !isCompleted;

  if (isIdle) {
    return (
      <div className="flex h-full flex-col border-l bg-muted/30">
        <div className="border-b px-4 py-3">
          <h2 className="text-lg font-semibold">진행 상황</h2>
        </div>
        <div className="flex-1 p-4">
          <EmptyState />
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col border-l bg-muted/30">
      {/* Header */}
      <div className="border-b px-4 py-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">진행 상황</h2>
          {session && (
            <span
              className={cn(
                "rounded-full px-3 py-1 text-xs font-medium",
                isError && "bg-red-100 text-red-700",
                isCompleted && "bg-green-100 text-green-700",
                isInProgress && "bg-blue-100 text-blue-700"
              )}
            >
              {STAGE_CONFIG[session.stage].label}
            </span>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-6">
          {/* Circular Progress */}
          <div className="flex justify-center py-4">
            <CircularProgress progress={session?.progress || 0} />
          </div>

          {/* Stage Timeline */}
          <Card>
            <CardHeader className="pb-2">
              <h3 className="text-sm font-medium">진행 단계</h3>
            </CardHeader>
            <CardContent>
              <StageTimeline
                currentStage={session?.stage || "idle"}
                timeline={session?.timeline || []}
              />
            </CardContent>
          </Card>

          {/* Metrics */}
          <MetricsCards
            sourcesSearched={session?.metrics.sourcesSearched || 0}
            documentsFound={session?.metrics.documentsFound || 0}
            qualityScore={session?.metrics.qualityScore || 0}
            estimatedTime={session?.metrics.estimatedTimeRemaining}
          />

          {/* Error State */}
          {isError && session?.error && (
            <Card className="border-red-200 bg-red-50">
              <CardContent className="flex items-start gap-3 pt-4">
                <AlertCircle className="h-5 w-5 text-red-500 shrink-0" />
                <div>
                  <p className="font-medium text-red-800">오류가 발생했습니다</p>
                  <p className="mt-1 text-sm text-red-600">{session.error}</p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Document Count Summary */}
          {(session?.documents.length || 0) > 0 && (
            <Card>
              <CardContent className="pt-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">
                    수집된 문서
                  </span>
                  <span className="text-lg font-semibold">
                    {session?.documents.length}개
                  </span>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Actions */}
      {(isConfirming || isError) && (
        <div className="border-t p-4">
          <div className="flex gap-2">
            {isConfirming && (
              <>
                <Button variant="outline" className="flex-1" onClick={onCancel}>
                  취소
                </Button>
                <Button className="flex-1" onClick={onConfirm}>
                  확인 및 저장
                </Button>
              </>
            )}
            {isError && (
              <>
                <Button variant="outline" className="flex-1" onClick={onCancel}>
                  취소
                </Button>
                <Button className="flex-1" onClick={onRetry}>
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
