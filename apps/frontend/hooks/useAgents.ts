/**
 * Hook for fetching list of agents with Pokemon-style card data
 * Includes mock data fallback for demo purposes
 *
 * @CODE:FRONTEND-REDESIGN-001-USE-AGENTS
 */
"use client"

import { useQuery } from "@tanstack/react-query"
import { apiClient } from "@/lib/api/client"
import { AgentCardDataSchema, AgentCardListResponseSchema } from "@/lib/api/types"
import type { AgentCardData, AgentCardListResponse } from "@/lib/api/types"

// Mock data for demo purposes when API returns empty
const MOCK_AGENT_DATA: AgentCardData[] = [
  {
    agent_id: "agent-001",
    name: "DataBot",
    robotImage: "/assets/agents/nobg/common/robot-common-01.png",
    progress: 78,
    stats: { users: 12453, robos: 8900, revenue: 45200, growth: 23 },
    status: "active"
  },
  {
    agent_id: "agent-002",
    name: "CodeAssist",
    robotImage: "/assets/agents/nobg/rare/robot-rare-01.png",
    progress: 92,
    stats: { users: 8721, robos: 12400, revenue: 67800, growth: 31 },
    status: "active"
  },
  {
    agent_id: "agent-003",
    name: "AnalyzerPro",
    robotImage: "/assets/agents/nobg/epic/robot-epic-01.png",
    progress: 65,
    stats: { users: 5432, robos: 6700, revenue: 34500, growth: 18 },
    status: "active"
  },
  {
    agent_id: "agent-004",
    name: "QueryMaster",
    robotImage: "/assets/agents/nobg/legendary/robot-legendary-01.png",
    progress: 88,
    stats: { users: 15678, robos: 18200, revenue: 89400, growth: 42 },
    status: "active"
  },
  {
    agent_id: "agent-005",
    name: "DocuHelper",
    robotImage: "/assets/agents/nobg/common/robot-common-02.png",
    progress: 45,
    stats: { users: 3421, robos: 4500, revenue: 21300, growth: 12 },
    status: "active"
  },
  {
    agent_id: "agent-006",
    name: "SearchBot",
    robotImage: "/assets/agents/nobg/rare/robot-rare-02.png",
    progress: 71,
    stats: { users: 7890, robos: 9800, revenue: 52100, growth: 27 },
    status: "active"
  },
  {
    agent_id: "agent-007",
    name: "TaskRunner",
    robotImage: "/assets/agents/nobg/epic/robot-epic-02.png",
    progress: 83,
    stats: { users: 9234, robos: 11100, revenue: 61200, growth: 35 },
    status: "active"
  },
  {
    agent_id: "agent-008",
    name: "LogicEngine",
    robotImage: "/assets/agents/nobg/legendary/robot-legendary-02.png",
    progress: 96,
    stats: { users: 18923, robos: 22400, revenue: 112500, growth: 48 },
    status: "active"
  },
  {
    agent_id: "agent-009",
    name: "AutoPilot",
    robotImage: "/assets/agents/nobg/common/robot-common-03.png",
    progress: 52,
    stats: { users: 4567, robos: 5600, revenue: 28900, growth: 15 },
    status: "idle"
  },
  {
    agent_id: "agent-010",
    name: "SynthBot",
    robotImage: "/assets/agents/nobg/rare/robot-rare-03.png",
    progress: 67,
    stats: { users: 6123, robos: 7400, revenue: 38700, growth: 21 },
    status: "active"
  },
  {
    agent_id: "agent-011",
    name: "NeuralNet",
    robotImage: "/assets/agents/nobg/epic/robot-epic-03.png",
    progress: 79,
    stats: { users: 10456, robos: 13200, revenue: 72800, growth: 38 },
    status: "active"
  },
  {
    agent_id: "agent-012",
    name: "QuantumAI",
    robotImage: "/assets/agents/nobg/legendary/robot-legendary-03.png",
    progress: 94,
    stats: { users: 21345, robos: 28900, revenue: 145600, growth: 56 },
    status: "active"
  },
  {
    agent_id: "agent-013",
    name: "DataMiner",
    robotImage: "/assets/agents/nobg/common/robot-common-04.png",
    progress: 38,
    stats: { users: 2345, robos: 3200, revenue: 15800, growth: 8 },
    status: "idle"
  },
  {
    agent_id: "agent-014",
    name: "FlowBot",
    robotImage: "/assets/agents/nobg/rare/robot-rare-04.png",
    progress: 61,
    stats: { users: 5678, robos: 6900, revenue: 35400, growth: 19 },
    status: "active"
  },
  {
    agent_id: "agent-015",
    name: "InsightGen",
    robotImage: "/assets/agents/nobg/epic/robot-epic-04.png",
    progress: 86,
    stats: { users: 11234, robos: 14600, revenue: 78900, growth: 41 },
    status: "active"
  }
]

interface FetchAgentsParams {
  level?: number
  min_coverage?: number
  max_results?: number
}

interface UseAgentsReturn {
  agents: AgentCardData[]
  isLoading: boolean
  error: Error | null
  refetch: () => Promise<unknown>
}

async function fetchAgents(params?: FetchAgentsParams): Promise<AgentCardData[]> {
  try {
    const response = await apiClient.get<AgentCardListResponse>("/agents/", { params })
    const validated = AgentCardListResponseSchema.parse(response.data)

    // Return mock data if API returns empty
    if (!validated.agents || validated.agents.length === 0) {
      return MOCK_AGENT_DATA
    }

    return validated.agents
  } catch (error) {
    // Return mock data on API error for demo purposes
    console.warn("Failed to fetch agents from API, using mock data:", error)
    return MOCK_AGENT_DATA
  }
}

export function useAgents(params?: FetchAgentsParams): UseAgentsReturn {
  const { data, isLoading, error, refetch } = useQuery<AgentCardData[], Error>({
    queryKey: ["agents", params],
    queryFn: () => fetchAgents(params),
    retry: false,
    staleTime: 30000,
  })

  return {
    agents: data ?? MOCK_AGENT_DATA, // Fallback to mock data
    isLoading,
    error: error ?? null,
    refetch,
  }
}
