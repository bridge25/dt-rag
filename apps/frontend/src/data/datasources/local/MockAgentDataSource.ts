/**
 * Mock Agent Data Source
 *
 * Provides mock data for development and testing.
 * Implements the same interface as the remote data source.
 *
 * @CODE:CLEAN-ARCHITECTURE-DATA
 */

import type {
  AgentDTOType,
  AgentMetricsDTOType,
  AgentCoverageDTOType,
  CreateAgentRequestDTOType,
  UpdateAgentRequestDTOType,
} from '../remote/AgentRemoteDataSource';

// ============================================================================
// Mock Data
// ============================================================================

const MOCK_AGENTS: AgentDTOType[] = [
  {
    agent_id: 'agent-001',
    name: 'DataBot',
    description: 'AI-powered data analysis assistant',
    robotImage: '/avatars/robots/robot-common-01.png',
    status: 'active',
    progress: 78,
    stats: { users: 12453, robos: 8900, revenue: 45200, growth: 23 },
    taxonomy_scope: ['Technology', 'Data Science'],
    level: 3,
    xp: 650,
    rarity: 'rare',
  },
  {
    agent_id: 'agent-002',
    name: 'CodeAssist',
    description: 'Programming and code review helper',
    robotImage: '/avatars/robots/robot-rare-01.png',
    status: 'active',
    progress: 92,
    stats: { users: 8721, robos: 12400, revenue: 67800, growth: 31 },
    taxonomy_scope: ['Technology', 'Software Development'],
    level: 5,
    xp: 1200,
    rarity: 'epic',
  },
  {
    agent_id: 'agent-003',
    name: 'AnalyzerPro',
    description: 'Business analytics and reporting',
    robotImage: '/avatars/robots/robot-epic-01.png',
    status: 'active',
    progress: 65,
    stats: { users: 5432, robos: 6700, revenue: 34500, growth: 18 },
    taxonomy_scope: ['Business', 'Analytics'],
    level: 4,
    xp: 890,
    rarity: 'rare',
  },
  {
    agent_id: 'agent-004',
    name: 'QueryMaster',
    description: 'Database query optimization specialist',
    robotImage: '/avatars/robots/robot-legendary-01.png',
    status: 'active',
    progress: 88,
    stats: { users: 15678, robos: 18200, revenue: 89400, growth: 42 },
    taxonomy_scope: ['Technology', 'Databases'],
    level: 8,
    xp: 3800,
    rarity: 'legendary',
  },
  {
    agent_id: 'agent-005',
    name: 'DocuHelper',
    description: 'Documentation and knowledge management',
    robotImage: '/avatars/robots/robot-common-02.png',
    status: 'idle',
    progress: 45,
    stats: { users: 3421, robos: 4500, revenue: 21300, growth: 12 },
    taxonomy_scope: ['Documentation'],
    level: 2,
    xp: 280,
    rarity: 'common',
  },
  {
    agent_id: 'agent-006',
    name: 'SearchBot',
    description: 'Intelligent search and retrieval',
    robotImage: '/avatars/robots/robot-rare-02.png',
    status: 'active',
    progress: 71,
    stats: { users: 7890, robos: 9800, revenue: 52100, growth: 27 },
    taxonomy_scope: ['Technology', 'Search'],
    level: 4,
    xp: 920,
    rarity: 'rare',
  },
  {
    agent_id: 'agent-007',
    name: 'TaskRunner',
    description: 'Workflow automation and task management',
    robotImage: '/avatars/robots/robot-epic-02.png',
    status: 'active',
    progress: 83,
    stats: { users: 9234, robos: 11100, revenue: 61200, growth: 35 },
    taxonomy_scope: ['Productivity', 'Automation'],
    level: 6,
    xp: 2200,
    rarity: 'epic',
  },
  {
    agent_id: 'agent-008',
    name: 'LogicEngine',
    description: 'Advanced reasoning and problem solving',
    robotImage: '/avatars/robots/robot-legendary-02.png',
    status: 'active',
    progress: 96,
    stats: { users: 18923, robos: 22400, revenue: 112500, growth: 48 },
    taxonomy_scope: ['AI', 'Machine Learning'],
    level: 9,
    xp: 4600,
    rarity: 'legendary',
  },
  {
    agent_id: 'agent-009',
    name: 'AutoPilot',
    description: 'Self-guided process automation',
    robotImage: '/avatars/robots/robot-common-03.png',
    status: 'training',
    progress: 52,
    stats: { users: 4567, robos: 5600, revenue: 28900, growth: 15 },
    taxonomy_scope: ['Automation'],
    level: 2,
    xp: 350,
    rarity: 'common',
  },
  {
    agent_id: 'agent-010',
    name: 'SynthBot',
    description: 'Content synthesis and summarization',
    robotImage: '/avatars/robots/robot-rare-03.png',
    status: 'active',
    progress: 67,
    stats: { users: 6123, robos: 7400, revenue: 38700, growth: 21 },
    taxonomy_scope: ['Content', 'NLP'],
    level: 3,
    xp: 580,
    rarity: 'rare',
  },
  {
    agent_id: 'agent-011',
    name: 'NeuralNet',
    description: 'Deep learning model integration',
    robotImage: '/avatars/robots/robot-epic-03.png',
    status: 'active',
    progress: 79,
    stats: { users: 10456, robos: 13200, revenue: 72800, growth: 38 },
    taxonomy_scope: ['AI', 'Deep Learning'],
    level: 7,
    xp: 2900,
    rarity: 'epic',
  },
  {
    agent_id: 'agent-012',
    name: 'QuantumAI',
    description: 'Quantum computing algorithms',
    robotImage: '/avatars/robots/robot-legendary-03.png',
    status: 'active',
    progress: 94,
    stats: { users: 21345, robos: 28900, revenue: 145600, growth: 56 },
    taxonomy_scope: ['AI', 'Quantum Computing'],
    level: 10,
    xp: 5500,
    rarity: 'legendary',
  },
  {
    agent_id: 'agent-013',
    name: 'DataMiner',
    description: 'Data extraction and ETL processes',
    robotImage: '/avatars/robots/robot-common-04.png',
    status: 'error',
    progress: 38,
    stats: { users: 2345, robos: 3200, revenue: 15800, growth: 8 },
    taxonomy_scope: ['Data', 'ETL'],
    level: 1,
    xp: 80,
    rarity: 'common',
  },
  {
    agent_id: 'agent-014',
    name: 'FlowBot',
    description: 'Workflow orchestration',
    robotImage: '/avatars/robots/robot-rare-04.png',
    status: 'active',
    progress: 61,
    stats: { users: 5678, robos: 6900, revenue: 35400, growth: 19 },
    taxonomy_scope: ['Workflow', 'Integration'],
    level: 3,
    xp: 520,
    rarity: 'rare',
  },
  {
    agent_id: 'agent-015',
    name: 'InsightGen',
    description: 'Business insight generation',
    robotImage: '/avatars/robots/robot-epic-04.png',
    status: 'active',
    progress: 86,
    stats: { users: 11234, robos: 14600, revenue: 78900, growth: 41 },
    taxonomy_scope: ['Business', 'Analytics', 'AI'],
    level: 6,
    xp: 2350,
    rarity: 'epic',
  },
];

// ============================================================================
// Mock Data Source Class
// ============================================================================

/**
 * Mock Agent Data Source
 *
 * Provides mock data for development and demo purposes.
 */
export class MockAgentDataSource {
  private agents: AgentDTOType[] = [...MOCK_AGENTS];

  /**
   * Get all agents
   */
  async getAll(params?: {
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<AgentDTOType[]> {
    // Simulate network delay
    await this.delay(200);

    let result = [...this.agents];

    // Apply status filter
    if (params?.status) {
      result = result.filter((a) => a.status === params.status);
    }

    // Apply pagination
    const offset = params?.offset || 0;
    const limit = params?.limit || result.length;
    result = result.slice(offset, offset + limit);

    return result;
  }

  /**
   * Get agent by ID
   */
  async getById(id: string): Promise<AgentDTOType | null> {
    await this.delay(100);
    return this.agents.find((a) => a.agent_id === id) || null;
  }

  /**
   * Create a new agent
   */
  async create(data: CreateAgentRequestDTOType): Promise<AgentDTOType> {
    await this.delay(300);

    const newAgent: AgentDTOType = {
      agent_id: `agent-${Date.now()}`,
      name: data.name,
      description: data.description,
      robotImage: data.robot_image || '/avatars/robots/robot-common-01.png',
      status: 'idle',
      progress: 0,
      stats: { users: 0, robos: 0, revenue: 0, growth: 0 },
      taxonomy_scope: data.taxonomy_scope,
      level: 1,
      xp: 0,
      rarity: 'common',
      created_at: new Date().toISOString(),
    };

    this.agents.push(newAgent);
    return newAgent;
  }

  /**
   * Update an agent
   */
  async update(id: string, data: UpdateAgentRequestDTOType): Promise<AgentDTOType> {
    await this.delay(200);

    const index = this.agents.findIndex((a) => a.agent_id === id);
    if (index === -1) {
      throw new Error(`Agent ${id} not found`);
    }

    this.agents[index] = {
      ...this.agents[index],
      ...data,
      updated_at: new Date().toISOString(),
    };

    return this.agents[index];
  }

  /**
   * Delete an agent
   */
  async delete(id: string): Promise<void> {
    await this.delay(200);
    this.agents = this.agents.filter((a) => a.agent_id !== id);
  }

  /**
   * Get agent metrics
   */
  async getMetrics(id: string): Promise<AgentMetricsDTOType> {
    await this.delay(150);

    const agent = this.agents.find((a) => a.agent_id === id);
    if (!agent) {
      throw new Error(`Agent ${id} not found`);
    }

    return {
      query_count: Math.floor(agent.stats.users * 2.5),
      success_rate: 0.85 + Math.random() * 0.14,
      avg_latency: 150 + Math.random() * 100,
      total_users: agent.stats.users,
      daily_active_users: Math.floor(agent.stats.users * 0.3),
      error_rate: 0.01 + Math.random() * 0.04,
    };
  }

  /**
   * Get agent coverage
   */
  async getCoverage(id: string): Promise<AgentCoverageDTOType> {
    await this.delay(150);

    const agent = this.agents.find((a) => a.agent_id === id);
    if (!agent) {
      throw new Error(`Agent ${id} not found`);
    }

    const totalDocs = 1000 + Math.floor(Math.random() * 500);
    const coveragePercent = (agent.progress || 50) + Math.random() * 20;

    return {
      coverage_percentage: Math.min(coveragePercent, 100),
      total_documents: totalDocs,
      covered_documents: Math.floor(totalDocs * (coveragePercent / 100)),
      taxonomy_nodes: (agent.taxonomy_scope?.length || 1) * 5,
      last_calculated: new Date().toISOString(),
    };
  }

  /**
   * Simulate network delay
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

/**
 * Singleton instance
 */
let instance: MockAgentDataSource | null = null;

export function getMockAgentDataSource(): MockAgentDataSource {
  if (!instance) {
    instance = new MockAgentDataSource();
  }
  return instance;
}
