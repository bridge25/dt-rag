"use client"

/**
 * Virtual list component for efficient rendering of large agent lists
 * Uses react-window v1.x FixedSizeGrid for virtualization
 * @CODE:FRONTEND-MIGRATION-001
 */

import { FixedSizeGrid as Grid, type GridChildComponentProps } from "react-window"
import type { AgentCardData } from "@/lib/api/types"
import { AgentCard } from "@/components/agent-card"

interface CellData {
  agents: AgentCardData[]
  columnCount: number
  onView: (agentId: string) => void
  onDelete: (agentId: string) => void
}

interface VirtualListProps {
  agents: AgentCardData[]
  columnCount: number
  columnWidth: number
  rowHeight: number
  height: number
  width: number
  onView: (agentId: string) => void
  onDelete: (agentId: string) => void
}

function Cell({ columnIndex, rowIndex, style, data }: GridChildComponentProps<CellData>) {
  const { agents, columnCount, onView, onDelete: _onDelete } = data
  const index = rowIndex * columnCount + columnIndex

  if (index >= agents.length) return null

  const agent = agents[index]

  return (
    <div style={style}>
      <div
        className="p-4 cursor-pointer"
        onClick={() => onView(agent.agent_id)}
        onKeyDown={(e) => e.key === "Enter" && onView(agent.agent_id)}
        role="button"
        tabIndex={0}
      >
        <AgentCard agent={agent} />
      </div>
    </div>
  )
}

export function VirtualList({
  agents,
  columnCount,
  columnWidth,
  rowHeight,
  height,
  width,
  onView,
  onDelete,
}: VirtualListProps) {
  const rowCount = Math.ceil(agents.length / columnCount)

  const itemData: CellData = {
    agents,
    columnCount,
    onView,
    onDelete,
  }

  return (
    <Grid<CellData>
      columnCount={columnCount}
      columnWidth={columnWidth}
      height={height}
      rowCount={rowCount}
      rowHeight={rowHeight}
      width={width}
      itemData={itemData}
    >
      {Cell}
    </Grid>
  )
}
