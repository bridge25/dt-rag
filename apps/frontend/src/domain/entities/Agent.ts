/**
 * Agent Domain Entity
 *
 * Core business entity representing an AI Agent.
 * This entity is framework-agnostic and contains only business logic.
 *
 * @CODE:CLEAN-ARCHITECTURE-DOMAIN
 */

/**
 * Agent status enumeration
 */
export type AgentStatus = 'active' | 'idle' | 'training' | 'error';

/**
 * Agent rarity level (Pokemon-style)
 */
export type AgentRarity = 'common' | 'rare' | 'epic' | 'legendary';

/**
 * Agent statistics
 */
export interface AgentStats {
  readonly users: number;
  readonly robos: number;
  readonly revenue: number;
  readonly growth: number;
}

/**
 * Agent Entity - Immutable Domain Object
 */
export interface Agent {
  readonly id: string;
  readonly name: string;
  readonly description?: string;
  readonly robotImage: string;
  readonly status: AgentStatus;
  readonly progress: number;
  readonly stats: AgentStats;
  readonly taxonomyScope?: readonly string[];
  readonly level?: number;
  readonly xp?: number;
  readonly rarity?: AgentRarity;
  readonly createdAt?: Date;
  readonly updatedAt?: Date;
}

/**
 * Agent creation parameters
 */
export interface CreateAgentParams {
  name: string;
  description?: string;
  taxonomyScope?: string[];
  robotImage?: string;
}

/**
 * Agent update parameters
 */
export interface UpdateAgentParams {
  name?: string;
  description?: string;
  status?: AgentStatus;
  taxonomyScope?: string[];
}

/**
 * Agent filter parameters for queries
 */
export interface AgentFilterParams {
  status?: AgentStatus;
  minLevel?: number;
  maxLevel?: number;
  minCoverage?: number;
  rarity?: AgentRarity;
  limit?: number;
  offset?: number;
}

/**
 * Domain logic: Calculate agent level from XP
 */
export function calculateAgentLevel(xp: number): number {
  if (xp < 100) return 1;
  if (xp < 300) return 2;
  if (xp < 600) return 3;
  if (xp < 1000) return 4;
  if (xp < 1500) return 5;
  if (xp < 2100) return 6;
  if (xp < 2800) return 7;
  if (xp < 3600) return 8;
  if (xp < 4500) return 9;
  return 10;
}

/**
 * Domain logic: Calculate rarity from level
 */
export function calculateAgentRarity(level: number): AgentRarity {
  if (level >= 8) return 'legendary';
  if (level >= 6) return 'epic';
  if (level >= 3) return 'rare';
  return 'common';
}

/**
 * Domain logic: Check if agent is performant
 */
export function isAgentPerformant(agent: Agent): boolean {
  return agent.progress >= 70 && agent.stats.growth > 0;
}

/**
 * Domain logic: Calculate agent health score
 */
export function calculateAgentHealthScore(agent: Agent): number {
  const statusScore = agent.status === 'active' ? 100 : agent.status === 'idle' ? 50 : 0;
  const progressScore = agent.progress;
  const growthScore = Math.min(agent.stats.growth * 2, 100);

  return Math.round((statusScore + progressScore + growthScore) / 3);
}
