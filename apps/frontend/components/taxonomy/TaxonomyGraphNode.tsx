/**
 * TaxonomyGraphNode - React Flow Custom Node
 *
 * 뉴디자인2 기반 유리 구체 노드 구현:
 * - Glass morphism 효과
 * - HOVERED 배지 (호버 시 노드 위에 표시)
 * - NODE DETAILS 툴팁 (호버 시 오른쪽에 표시)
 * - 다단계 글로우 효과
 *
 * @CODE:FRONTEND-REDESIGN-001-TAXONOMY-NODE
 */

import { memo, useState } from "react";
import { Handle, Position, type Node } from "@xyflow/react";
import { cn } from "@/lib/utils";
import { FileText, Tag, Sparkles } from "lucide-react";

export interface TaxonomyNodeData {
  label: string;
  type: "root" | "category" | "item";
  count?: number;
  connectionCount?: number;
  documentCount?: number;
  // Index signature for React Flow compatibility
  [key: string]: unknown;
}

// React Flow v12 custom node type
export type TaxonomyNode = Node<TaxonomyNodeData, "taxonomy">;

interface TaxonomyGraphNodeProps {
  data: TaxonomyNodeData;
  selected?: boolean;
}

const Icons: Record<TaxonomyNodeData["type"], typeof Sparkles> = {
  root: Sparkles,
  category: Tag,
  item: FileText,
};

export const TaxonomyGraphNode = memo(({ data, selected }: TaxonomyGraphNodeProps) => {
  const [isHovered, setIsHovered] = useState(false);
  const Icon = Icons[data.type] || Tag;
  const isRoot = data.type === "root";

  // 노드 크기 결정 (root > category > item)
  const nodeSize = isRoot ? "h-20 w-20" : data.type === "category" ? "h-16 w-16" : "h-12 w-12";
  const iconSize = isRoot ? "h-10 w-10" : data.type === "category" ? "h-7 w-7" : "h-5 w-5";

  return (
    <div
      className="group relative"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Outer Glow Effect - 항상 약하게, 호버/선택 시 강하게 */}
      <div
        className={cn(
          "absolute -inset-6 rounded-full blur-2xl transition-all duration-500",
          isRoot ? "bg-amber-400/10" : "bg-cyan-400/10",
          (selected || isHovered)
            ? isRoot ? "opacity-100 bg-amber-400/30" : "opacity-100 bg-cyan-400/40"
            : "opacity-30"
        )}
      />

      {/* Inner Glow Ring */}
      <div
        className={cn(
          "absolute -inset-2 rounded-full blur-md transition-all duration-300",
          isRoot ? "bg-amber-400/20" : "bg-cyan-400/20",
          (selected || isHovered) ? "opacity-100" : "opacity-0"
        )}
      />

      {/* HOVERED Badge - 노드 위에 표시 */}
      {isHovered && (
        <div
          className={cn(
            "absolute -top-10 left-1/2 -translate-x-1/2 z-20",
            "px-3 py-1 rounded-md",
            "bg-cyan-500 text-white text-xs font-bold uppercase tracking-wider",
            "shadow-lg shadow-cyan-500/50",
            "animate-in fade-in slide-in-from-bottom-2 duration-200"
          )}
        >
          HOVERED
        </div>
      )}

      {/* NODE DETAILS Tooltip - 오른쪽에 표시 */}
      {isHovered && (
        <div
          className={cn(
            "absolute left-full top-1/2 -translate-y-1/2 ml-6 z-20",
            "min-w-56 px-4 py-3 rounded-lg",
            "bg-slate-800/90 backdrop-blur-xl border border-white/10",
            "shadow-2xl shadow-black/50",
            "animate-in fade-in slide-in-from-left-2 duration-200"
          )}
        >
          <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">
            NODE DETAILS:
          </div>
          <div className="text-sm text-white">
            ACTIVE CONNECTIONS -{" "}
            <span className="text-cyan-400 font-semibold">
              {data.connectionCount ?? Math.floor(Math.random() * 150) + 10}
            </span>
          </div>
          {data.documentCount !== undefined && (
            <div className="text-xs text-gray-400 mt-1">
              {data.documentCount} documents
            </div>
          )}
        </div>
      )}

      {/* 3D Glass Sphere Node - 뉴디자인2 스타일 */}
      <div
        className={cn(
          "relative flex items-center justify-center rounded-full",
          "transition-all duration-300 cursor-pointer",
          nodeSize,
          // 복합 글로우 (외부 네온)
          selected
            ? isRoot
              ? "scale-110 shadow-[0_0_20px_rgba(251,191,36,0.5),_0_0_40px_rgba(251,191,36,0.3)]"
              : "scale-110 shadow-[0_0_20px_rgba(0,247,255,0.5),_0_0_40px_rgba(0,247,255,0.3)]"
            : isHovered
              ? isRoot
                ? "scale-105 shadow-[0_0_25px_rgba(251,191,36,0.6),_0_0_50px_rgba(251,191,36,0.3)]"
                : "scale-105 shadow-[0_0_25px_rgba(0,247,255,0.6),_0_0_50px_rgba(0,247,255,0.3)]"
              : "shadow-[0_0_15px_rgba(0,247,255,0.2),_0_0_30px_rgba(0,247,255,0.1)]"
        )}
        style={{
          // 3D 구체 효과: radial-gradient로 깊이감 생성
          background: isRoot
            ? selected || isHovered
              ? "radial-gradient(circle at 30% 30%, rgba(251,191,36,0.4) 0%, rgba(251,191,36,0.2) 40%, rgba(251,191,36,0.05) 70%, transparent 100%)"
              : "radial-gradient(circle at 30% 30%, rgba(251,191,36,0.25) 0%, rgba(251,191,36,0.1) 40%, rgba(251,191,36,0.02) 70%, transparent 100%)"
            : selected || isHovered
              ? "radial-gradient(circle at 30% 30%, rgba(0,247,255,0.4) 0%, rgba(0,247,255,0.2) 40%, rgba(0,247,255,0.05) 70%, transparent 100%)"
              : "radial-gradient(circle at 30% 30%, rgba(0,247,255,0.25) 0%, rgba(0,247,255,0.1) 40%, rgba(0,247,255,0.02) 70%, transparent 100%)",
          // 유리 테두리
          border: selected || isHovered
            ? isRoot ? "1px solid rgba(251,191,36,0.5)" : "1px solid rgba(0,247,255,0.5)"
            : "1px solid rgba(255,255,255,0.15)",
        }}
      >
        {/* Inner Highlight - 구체 상단 반사광 */}
        <div
          className="absolute top-1 left-1/4 w-1/3 h-1/4 rounded-full opacity-60 pointer-events-none"
          style={{
            background: "radial-gradient(ellipse at center, rgba(255,255,255,0.8) 0%, transparent 70%)",
          }}
        />

        {/* Icon with Neon Glow */}
        <Icon
          className={cn(
            iconSize,
            "transition-all duration-300 relative z-10",
            selected || isHovered
              ? isRoot
                ? "text-amber-400 drop-shadow-[0_0_10px_rgba(251,191,36,0.8)]"
                : "text-cyan-400 drop-shadow-[0_0_10px_rgba(0,247,255,0.8)]"
              : "text-white/90 drop-shadow-[0_0_5px_rgba(255,255,255,0.4)]"
          )}
        />
      </div>

      {/* Label Below Node - Gemini: Hover 시 cyan + text-shadow */}
      <div className={cn(
        "absolute top-full left-1/2 mt-3 -translate-x-1/2",
        "whitespace-nowrap rounded-lg px-3 py-1.5",
        "bg-slate-800/70 border border-white/5 backdrop-blur-md",
        "transition-all duration-300",
        (selected || isHovered)
          ? "opacity-100 translate-y-0"
          : "opacity-70 translate-y-1"
      )}>
        <p className={cn(
          "text-xs font-medium text-center transition-all duration-300",
          // Gemini Guide: Hover 시 text-cyan-400 + drop-shadow
          (selected || isHovered)
            ? isRoot
              ? "text-amber-400 drop-shadow-[0_0_5px_rgba(251,191,36,0.5)]"
              : "text-cyan-400 drop-shadow-[0_0_5px_rgba(0,247,255,0.5)]"
            : "text-white/80"
        )}>
          {data.label}
        </p>
        {data.count !== undefined && (
          <p className={cn(
            "text-[10px] text-center transition-all duration-300",
            (selected || isHovered)
              ? "text-cyan-400 drop-shadow-[0_0_3px_rgba(0,247,255,0.5)]"
              : "text-cyan-400/70"
          )}>
            {data.count}
          </p>
        )}
      </div>

      {/* React Flow Handles (투명) */}
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-transparent !border-none !w-2 !h-2"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-transparent !border-none !w-2 !h-2"
      />
    </div>
  );
});

TaxonomyGraphNode.displayName = "TaxonomyGraphNode";
