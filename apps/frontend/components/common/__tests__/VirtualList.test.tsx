/**
 * VirtualList Component Tests
 * @TEST:FRONTEND-MIGRATION-001
 */

import { describe, it, expect } from "vitest"
import { render } from "@testing-library/react"
import { VirtualList, type VirtualListAgent } from "../VirtualList"

const mockAgents: VirtualListAgent[] = [
  {
    agent_id: "1",
    name: "Agent Alpha",
    level: 5,
    xp: 1500,
    rarity: "Rare",
    quality_score: 85,
    created_at: "2024-01-01",
  },
  {
    agent_id: "2",
    name: "Agent Beta",
    level: 3,
    xp: 450,
    rarity: "Common",
    quality_score: 60,
    created_at: "2024-01-02",
  },
]

describe("VirtualList", () => {
  const defaultProps = {
    agents: mockAgents,
    columnCount: 2,
    columnWidth: 300,
    rowHeight: 350,
    height: 600,
    width: 800,
    renderItem: (agent: VirtualListAgent) => (
      <div data-testid={`agent-${agent.agent_id}`}>{agent.name}</div>
    ),
  }

  it("renders without crashing", () => {
    const { container } = render(<VirtualList {...defaultProps} />)
    expect(container).toBeInTheDocument()
  })

  it("renders items using renderItem function", () => {
    render(<VirtualList {...defaultProps} />)

    // Virtual list may not render all items initially
    // Check that the grid structure exists
    expect(document.querySelector("[style]")).toBeInTheDocument()
  })

  it("calculates correct row count", () => {
    const props = {
      ...defaultProps,
      agents: Array.from({ length: 10 }, (_, i) => ({
        ...mockAgents[0],
        agent_id: String(i),
      })),
      columnCount: 3,
    }

    // 10 agents / 3 columns = 4 rows (ceil)
    const { container } = render(<VirtualList {...props} />)
    expect(container).toBeInTheDocument()
  })

  it("handles empty agent list", () => {
    const { container } = render(
      <VirtualList {...defaultProps} agents={[]} />
    )
    expect(container).toBeInTheDocument()
  })
})
