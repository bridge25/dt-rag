"use client";

/**
 * DocumentPreview Component
 *
 * Displays discovered documents with selection and filtering capabilities.
 * @CODE:FRONTEND-UX-001
 */

import { useState, useMemo } from "react";
import {
  FileText,
  Globe,
  Database,
  FileJson,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Star,
  Filter,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { DiscoveredDocument, SourceInfo } from "@/types/research";

// ============================================================================
// Props
// ============================================================================

interface DocumentPreviewProps {
  documents: DiscoveredDocument[];
  selectedIds: string[];
  expandedIds: string[];
  onSelect: (id: string) => void;
  onExpand: (id: string) => void;
  onSelectAll: () => void;
  onDeselectAll: () => void;
}

// ============================================================================
// Source Type Icons
// ============================================================================

const SOURCE_ICONS: Record<SourceInfo["type"], typeof Globe> = {
  web: Globe,
  pdf: FileText,
  api: FileJson,
  database: Database,
};

const RELIABILITY_COLORS: Record<SourceInfo["reliability"], string> = {
  high: "bg-green-100 text-green-700 border-green-200",
  medium: "bg-amber-100 text-amber-700 border-amber-200",
  low: "bg-red-100 text-red-700 border-red-200",
};

const RELIABILITY_LABELS: Record<SourceInfo["reliability"], string> = {
  high: "높음",
  medium: "보통",
  low: "낮음",
};

// ============================================================================
// Document Card Component
// ============================================================================

function DocumentCard({
  document,
  isSelected,
  isExpanded,
  onSelect,
  onExpand,
}: {
  document: DiscoveredDocument;
  isSelected: boolean;
  isExpanded: boolean;
  onSelect: () => void;
  onExpand: () => void;
}) {
  const SourceIcon = SOURCE_ICONS[document.source.type];
  const relevancePercent = Math.round(document.relevanceScore * 100);

  return (
    <Card
      className={cn(
        "transition-all duration-200 cursor-pointer",
        isSelected && "ring-2 ring-primary border-primary",
        !isSelected && "hover:border-muted-foreground/50"
      )}
    >
      <CardContent className="p-4">
        {/* Header Row */}
        <div className="flex items-start gap-3">
          {/* Checkbox */}
          <Checkbox
            checked={isSelected}
            onCheckedChange={onSelect}
            className="mt-1"
          />

          {/* Source Icon */}
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-secondary">
            <SourceIcon className="h-5 w-5 text-muted-foreground" />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <h4 className="font-medium text-sm line-clamp-2">
                {document.title}
              </h4>
              <div className="flex items-center gap-1 shrink-0">
                <Star className="h-3 w-3 text-amber-500" />
                <span className="text-xs font-medium">{relevancePercent}%</span>
              </div>
            </div>

            {/* Source Info */}
            <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
              <span>{document.source.name}</span>
              <Badge
                variant="outline"
                className={cn(
                  "text-[10px] px-1.5 py-0",
                  RELIABILITY_COLORS[document.source.reliability]
                )}
              >
                신뢰도: {RELIABILITY_LABELS[document.source.reliability]}
              </Badge>
            </div>

            {/* Snippet */}
            <p
              className={cn(
                "mt-2 text-xs text-muted-foreground",
                isExpanded ? "" : "line-clamp-2"
              )}
            >
              {document.snippet}
            </p>

            {/* Expanded Content */}
            {isExpanded && (
              <div className="mt-3 space-y-2">
                {/* Categories */}
                {document.categories && document.categories.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {document.categories.map((cat) => (
                      <Badge key={cat} variant="outline" className="text-[10px]">
                        {cat}
                      </Badge>
                    ))}
                  </div>
                )}

                {/* URL Link */}
                {document.source.url && (
                  <a
                    href={document.source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <ExternalLink className="h-3 w-3" />
                    원본 보기
                  </a>
                )}

                {/* Collected Time */}
                <p className="text-[10px] text-muted-foreground">
                  수집 시간: {new Date(document.collectedAt).toLocaleString("ko-KR")}
                </p>
              </div>
            )}

            {/* Expand Toggle */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                onExpand();
              }}
              className="mt-2 flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="h-3 w-3" />
                  접기
                </>
              ) : (
                <>
                  <ChevronDown className="h-3 w-3" />
                  더 보기
                </>
              )}
            </button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Filter Bar Component
// ============================================================================

function FilterBar({
  documents,
  selectedCount,
  onSelectAll,
  onDeselectAll,
  filterType,
  onFilterChange,
}: {
  documents: DiscoveredDocument[];
  selectedCount: number;
  onSelectAll: () => void;
  onDeselectAll: () => void;
  filterType: string | null;
  onFilterChange: (type: string | null) => void;
}) {
  const sourceTypes = useMemo(() => {
    const types = new Set(documents.map((d) => d.source.type));
    return Array.from(types);
  }, [documents]);

  return (
    <div className="flex items-center justify-between gap-4 py-2">
      {/* Selection Controls */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">
          {selectedCount}/{documents.length} 선택됨
        </span>
        <Button
          variant="ghost"
          size="sm"
          onClick={onSelectAll}
          className="h-7 text-xs"
        >
          전체 선택
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={onDeselectAll}
          className="h-7 text-xs"
        >
          선택 해제
        </Button>
      </div>

      {/* Filter Controls */}
      <div className="flex items-center gap-1">
        <Filter className="h-4 w-4 text-muted-foreground" />
        <Button
          variant={filterType === null ? "secondary" : "ghost"}
          size="sm"
          onClick={() => onFilterChange(null)}
          className="h-7 text-xs"
        >
          전체
        </Button>
        {sourceTypes.map((type) => {
          const Icon = SOURCE_ICONS[type];
          return (
            <Button
              key={type}
              variant={filterType === type ? "secondary" : "ghost"}
              size="sm"
              onClick={() => onFilterChange(type)}
              className="h-7 text-xs gap-1"
            >
              <Icon className="h-3 w-3" />
              {type.toUpperCase()}
            </Button>
          );
        })}
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function DocumentPreview({
  documents,
  selectedIds,
  expandedIds,
  onSelect,
  onExpand,
  onSelectAll,
  onDeselectAll,
}: DocumentPreviewProps) {
  const [filterType, setFilterType] = useState<string | null>(null);

  const filteredDocuments = useMemo(() => {
    if (!filterType) return documents;
    return documents.filter((d) => d.source.type === filterType);
  }, [documents, filterType]);

  if (documents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <FileText className="h-12 w-12 text-muted-foreground/50" />
        <p className="mt-4 text-sm text-muted-foreground">
          아직 수집된 문서가 없습니다
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Filter Bar */}
      <FilterBar
        documents={documents}
        selectedCount={selectedIds.length}
        onSelectAll={onSelectAll}
        onDeselectAll={onDeselectAll}
        filterType={filterType}
        onFilterChange={setFilterType}
      />

      {/* Document List */}
      <div className="space-y-2">
        {filteredDocuments.map((doc) => (
          <DocumentCard
            key={doc.id}
            document={doc}
            isSelected={selectedIds.includes(doc.id)}
            isExpanded={expandedIds.includes(doc.id)}
            onSelect={() => onSelect(doc.id)}
            onExpand={() => onExpand(doc.id)}
          />
        ))}
      </div>

      {/* Filtered Empty State */}
      {filteredDocuments.length === 0 && documents.length > 0 && (
        <div className="py-4 text-center text-sm text-muted-foreground">
          해당 유형의 문서가 없습니다
        </div>
      )}
    </div>
  );
}

export default DocumentPreview;
