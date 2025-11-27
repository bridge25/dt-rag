import { memo } from "react";
import { Handle, Position, NodeProps, Node } from "@xyflow/react";
import { cn } from "@/lib/utils";
import { FolderTree, FileText, Tag } from "lucide-react";

export type TaxonomyNodeData = Node<{
    label: string;
    type: string;
    count?: number;
    isHovered?: boolean;
}>["data"];

const Icons = {
    root: FolderTree,
    category: Tag,
    item: FileText,
};

export const TaxonomyGraphNode = memo(({ data, selected }: NodeProps<TaxonomyNodeData>) => {
    const Icon = Icons[data.type as keyof typeof Icons] || Tag;
    const isRoot = data.type === "root";

    return (
        <div className="group relative">
            {/* Glow Effect */}
            <div
                className={cn(
                    "absolute -inset-4 rounded-full bg-accent-glow-blue/20 blur-xl transition-opacity duration-500",
                    selected || data.isHovered ? "opacity-100" : "opacity-0"
                )}
            />

            {/* Glass Orb */}
            <div
                className={cn(
                    "relative flex h-16 w-16 items-center justify-center rounded-full border transition-all duration-300",
                    "bg-glass backdrop-blur-md shadow-glass",
                    selected
                        ? "border-accent-glow-blue shadow-glow-blue scale-110"
                        : "border-white/10 hover:border-white/30 hover:scale-105"
                )}
            >
                <Icon
                    className={cn(
                        "h-8 w-8 transition-colors duration-300",
                        selected ? "text-accent-glow-blue" : "text-white/80"
                    )}
                />
            </div>

            {/* Label */}
            <div className={cn(
                "absolute top-full left-1/2 mt-3 -translate-x-1/2 whitespace-nowrap rounded-lg px-3 py-1.5",
                "bg-glass border border-white/5 backdrop-blur-md transition-all duration-300",
                selected ? "opacity-100 translate-y-0" : "opacity-70 translate-y-1 group-hover:opacity-100 group-hover:translate-y-0"
            )}>
                <p className="text-xs font-medium text-white">{data.label}</p>
                {data.count !== undefined && (
                    <p className="text-[10px] text-center text-gray-400">{data.count} items</p>
                )}
            </div>

            {/* Handles */}
            <Handle
                type="target"
                position={Position.Top}
                className="!bg-transparent !border-none"
            />
            <Handle
                type="source"
                position={Position.Bottom}
                className="!bg-transparent !border-none"
            />
        </div>
    );
});
