// @CODE:FRONTEND-INTEGRATION-001:VIRTUAL-LIST
import { FixedSizeGrid as Grid, type GridChildComponentProps } from 'react-window'
import type { AgentCardData } from '@/lib/api/types'
import { AgentCard } from '@/components/agent-card/AgentCard'

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

  const Cell = ({ columnIndex, rowIndex, style }: GridChildComponentProps) => {
    const index = rowIndex * columnCount + columnIndex
    if (index >= agents.length) return null

    const agent = agents[index]

    return (
      <div style={style}>
        <div className="p-4">
          <AgentCard
            agent={agent}
            onView={() => onView(agent.agent_id)}
            onDelete={() => onDelete(agent.agent_id)}
          />
        </div>
      </div>
    )
  }

  return (
    <Grid
      columnCount={columnCount}
      columnWidth={columnWidth}
      height={height}
      rowCount={rowCount}
      rowHeight={rowHeight}
      width={width}
    >
      {Cell}
    </Grid>
  )
}
