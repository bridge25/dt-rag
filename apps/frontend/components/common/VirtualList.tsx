"use client"

/**
 * Virtual list component for efficient rendering of large agent lists
 * Uses react-window v1.x FixedSizeGrid for virtualization
 * @CODE:FRONTEND-MIGRATION-001
 */

import { FixedSizeGrid as Grid, type GridChildComponentProps } from "react-window"

export interface VirtualListAgent {
  agent_id: string
  name: string
  level: number
  xp: number
  rarity: "Common" | "Rare" | "Epic" | "Legendary"
  quality_score: number
  created_at: string
}

interface CellData {
  agents: VirtualListAgent[]
  columnCount: number
  renderItem: (agent: VirtualListAgent) => React.ReactNode
}

interface VirtualListProps {
  agents: VirtualListAgent[]
  columnCount: number
  columnWidth: number
  rowHeight: number
  height: number
  width: number
  renderItem: (agent: VirtualListAgent) => React.ReactNode
}

function Cell({ columnIndex, rowIndex, style, data }: GridChildComponentProps<CellData>) {
  const { agents, columnCount, renderItem } = data
  const index = rowIndex * columnCount + columnIndex

  if (index >= agents.length) return null

  const agent = agents[index]

  return (
    <div style={style}>
      <div className="p-4">{renderItem(agent)}</div>
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
  renderItem,
}: VirtualListProps) {
  const rowCount = Math.ceil(agents.length / columnCount)

  const itemData: CellData = {
    agents,
    columnCount,
    renderItem,
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
