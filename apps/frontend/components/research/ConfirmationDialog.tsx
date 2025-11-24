"use client";

/**
 * ConfirmationDialog Component
 *
 * Dialog for confirming research results before saving to knowledge base.
 * @CODE:FRONTEND-UX-001
 */

import { CheckCircle2, AlertTriangle, FileText, FolderTree } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

// ============================================================================
// Props
// ============================================================================

interface ConfirmationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  onCancel: () => void;
  selectedCount: number;
  totalCount: number;
  taxonomyName?: string;
  isLoading?: boolean;
}

// ============================================================================
// Summary Item Component
// ============================================================================

function SummaryItem({
  icon: Icon,
  label,
  value,
  highlight,
}: {
  icon: typeof FileText;
  label: string;
  value: string | number;
  highlight?: boolean;
}) {
  return (
    <div className="flex items-center gap-3 rounded-lg bg-secondary/50 p-3">
      <div
        className={cn(
          "flex h-10 w-10 items-center justify-center rounded-full",
          highlight ? "bg-primary/10" : "bg-secondary"
        )}
      >
        <Icon
          className={cn(
            "h-5 w-5",
            highlight ? "text-primary" : "text-muted-foreground"
          )}
        />
      </div>
      <div>
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="font-semibold">{value}</p>
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function ConfirmationDialog({
  open,
  onOpenChange,
  onConfirm,
  onCancel,
  selectedCount,
  totalCount,
  taxonomyName,
  isLoading = false,
}: ConfirmationDialogProps) {
  const hasSelection = selectedCount > 0;
  const isPartialSelection = selectedCount < totalCount;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
            <CheckCircle2 className="h-6 w-6 text-green-600" />
          </div>
          <DialogTitle className="text-center">리서치 결과 확인</DialogTitle>
          <DialogDescription className="text-center">
            선택한 문서를 지식 베이스에 추가하시겠습니까?
          </DialogDescription>
        </DialogHeader>

        {/* Summary */}
        <div className="space-y-2 py-4">
          <SummaryItem
            icon={FileText}
            label="선택된 문서"
            value={`${selectedCount}개 / ${totalCount}개`}
            highlight={hasSelection}
          />
          {taxonomyName && (
            <SummaryItem
              icon={FolderTree}
              label="저장 위치"
              value={taxonomyName}
            />
          )}
        </div>

        {/* Warning for partial selection */}
        {isPartialSelection && hasSelection && (
          <div className="flex items-start gap-2 rounded-lg bg-amber-50 p-3 text-sm">
            <AlertTriangle className="h-4 w-4 text-amber-500 mt-0.5 shrink-0" />
            <p className="text-amber-700">
              전체 {totalCount}개 중 {selectedCount}개만 선택되었습니다.
              선택하지 않은 문서는 저장되지 않습니다.
            </p>
          </div>
        )}

        {/* Warning for no selection */}
        {!hasSelection && (
          <div className="flex items-start gap-2 rounded-lg bg-red-50 p-3 text-sm">
            <AlertTriangle className="h-4 w-4 text-red-500 mt-0.5 shrink-0" />
            <p className="text-red-700">
              선택된 문서가 없습니다. 최소 1개 이상의 문서를 선택해 주세요.
            </p>
          </div>
        )}

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            variant="outline"
            onClick={onCancel}
            disabled={isLoading}
          >
            취소
          </Button>
          <Button
            onClick={onConfirm}
            disabled={!hasSelection || isLoading}
          >
            {isLoading ? "저장 중..." : "확인 및 저장"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default ConfirmationDialog;
