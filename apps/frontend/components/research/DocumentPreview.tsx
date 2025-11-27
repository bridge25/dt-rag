"use client";

/**
 * DocumentPreview Component
 * Ethereal Glass Aesthetic
 *
 * Displays discovered documents with selection and filtering capabilities.
 * @CODE:FRONTEND-UX-002
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
  high: "bg-green-500/20 text-green-300 border-green-500/30",
  medium: "bg-amber-500/20 text-amber-300 border-amber-500/30",
  low: "bg-red-500/20 text-red-300 border-red-500/30",
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
    <div
      className={cn(
        "group relative rounded-xl border transition-all duration-300 cursor-pointer overflow-hidden backdrop-blur-sm",
        isSelected
          ? "bg-blue-500/10 border-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.2)]"
          : "bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20"
      )}
      onClick={onExpand}
    >
      {/* Selection Indicator Line */}
      <div
        className={cn(
          "absolute left-0 top-0 bottom-0 w-1 transition-colors duration-300",
          isSelected ? "bg-blue-500" : "bg-transparent group-hover:bg-white/10"
        )}
      />

      <div className="p-4 pl-5">
        {/* Header Row */}
        <div className="flex items-start gap-4">
          {/* Checkbox */}
          <div
            className="mt-1"
            onClick={(e) => e.stopPropagation()}
          >
            <Checkbox
              checked={isSelected}
              onCheckedChange={onSelect}
              className={cn(
                "border-white/30 data-[state=checked]:bg-blue-500 data-[state=checked]:border-blue-500",
                "h-5 w-5 rounded-md transition-all duration-200"
              )}
            />
          </div>

          {/* Source Icon */}
          <div className={cn(
            "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border transition-colors",
            isSelected
              ? "bg-blue-500/20 border-blue-500/30 text-blue-300"
              : "bg-white/5 border-white/10 text-white/40 group-hover:text-white/60"
          )}>
            <SourceIcon className="h-5 w-5" />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <h4 className={cn(
                "font-medium text-sm line-clamp-2 transition-colors",
                isSelected ? "text-blue-100" : "text-white/90"
              )}>
                {document.title}
              </h4>
              <div className="flex items-center gap-1 shrink-0 bg-black/20 rounded-full px-2 py-0.5 border border-white/5">
                <Star className="h-3 w-3 text-amber-400 fill-amber-400/20" />
                <span className="text-xs font-medium text-amber-200">{relevancePercent}%</span>
              </div>
            </div>

            {/* Source Info */}
            <div className="mt-2 flex items-center gap-2 text-xs text-white/50">
              <span className="truncate max-w-[150px]">{document.source.name}</span>
              <Badge
                variant="outline"
                className={cn(
                  "text-[10px] px-1.5 py-0 h-5 border",
                  RELIABILITY_COLORS[document.source.reliability]
                )}
              >
                신뢰도: {RELIABILITY_LABELS[document.source.reliability]}
              </Badge>
            </div>

            {/* Snippet */}
            <p
              className={cn(
                "mt-3 text-xs text-white/60 leading-relaxed",
                isExpanded ? "" : "line-clamp-2"
              )}
            >
              {document.snippet}
            </p>

            {/* Expanded Content */}
            {isExpanded && (
              <div className="mt-4 space-y-3 pt-3 border-t border-white/10 animate-in fade-in slide-in-from-top-2 duration-300">
                {/* Categories */}
                {document.categories && document.categories.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {document.categories.map((cat) => (
                      <Badge
                        key={cat}
                        variant="outline"
                        className="text-[10px] bg-white/5 border-white/10 text-white/70 hover:bg-white/10"
                      >
                        {cat}
                      </Badge>
                    ))}
                  </div>
                )}

                <div className="flex items-center justify-between">
                  {/* Collected Time */}
                  <p className="text-[10px] text-white/30">
                    수집: {new Date(document.collectedAt).toLocaleString("ko-KR")}
                  </p>

                  {/* URL Link */}
                  {document.source.url && (
                    <a
                      href={document.source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 hover:underline transition-colors"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <ExternalLink className="h-3 w-3" />
                      원본 보기
                    </a>
                  )}
                </div>
              </div>
            )}

            {/* Expand Toggle */}
            <div className="mt-2 flex justify-center">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onExpand();
                }}
                className="flex items-center gap-1 text-[10px] text-white/30 hover:text-white/60 transition-colors py-1"
              >
                {isExpanded ? (
                  <ChevronUp className="h-3 w-3" />
                ) : (
                  <ChevronDown className="h-3 w-3" />
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
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
        <span className="text-sm text-white/60">
          <span className="text-blue-400 font-medium">{selectedCount}</span>
          <span className="mx-1">/</span>
          {documents.length} 선택됨
        </span>
        <div className="h-4 w-px bg-white/10 mx-2" />
        <Button
          variant="ghost"
          size="sm"
          onClick={onSelectAll}
          className="h-7 text-xs text-white/60 hover:text-white hover:bg-white/10"
        >
          전체 선택
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={onDeselectAll}
          className="h-7 text-xs text-white/60 hover:text-white hover:bg-white/10"
        >
          선택 해제
        </Button>
      </div>

      {/* Filter Controls */}
      <div className="flex items-center gap-1 bg-white/5 p-1 rounded-lg border border-white/10">
        <div className="px-2">
          <Filter className="h-3.5 w-3.5 text-white/40" />
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onFilterChange(null)}
          className={cn(
            "h-6 text-[10px] px-2 rounded-md transition-all",
            filterType === null
              ? "bg-blue-500/20 text-blue-300 shadow-sm"
              : "text-white/50 hover:text-white hover:bg-white/5"
          )}
        >
          전체
        </Button>
        {sourceTypes.map((type) => {
          const Icon = SOURCE_ICONS[type];
          return (
            <Button
              key={type}
              variant="ghost"
              size="sm"
              onClick={() => onFilterChange(type)}
              className={cn(
                "h-6 text-[10px] px-2 rounded-md gap-1 transition-all",
                filterType === type
                  ? "bg-blue-500/20 text-blue-300 shadow-sm"
                  : "text-white/50 hover:text-white hover:bg-white/5"
              )}
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
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="h-16 w-16 rounded-full bg-white/5 flex items-center justify-center mb-4 border border-white/10">
          <FileText className="h-8 w-8 text-white/20" />
        </div>
        <p className="text-sm text-white/40">
          아직 수집된 문서가 없습니다
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
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
      <div className="space-y-3">
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
        <div className="py-8 text-center text-sm text-white/40 border border-dashed border-white/10 rounded-xl bg-white/5">
          해당 유형의 문서가 없습니다
        </div>
      )}
    </div>
  );
}

export default DocumentPreview;
