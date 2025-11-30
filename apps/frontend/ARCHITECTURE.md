# Frontend Clean Architecture

**DT-RAG Frontend - Clean Architecture Implementation**

> 재사용성과 관심사 분리를 통해 UI·상태·비즈니스 로직을 구조화하고, 확장 가능한 클린 아키텍처

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Presentation Layer                        │
│  React Components, Hooks (React Query), Zustand Stores      │
│                         ↓                                   │
├─────────────────────────────────────────────────────────────┤
│                     Domain Layer                            │
│  Entities, Use Cases, Repository Interfaces                 │
│                         ↓                                   │
├─────────────────────────────────────────────────────────────┤
│                      Data Layer                             │
│  Repository Impl, Data Sources (API/Mock), Mappers          │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Directory Structure

```
src/
├── domain/                    # 🎯 Domain Layer (Innermost)
│   ├── entities/              # Core business models
│   │   ├── Agent.ts           # Agent entity + business rules
│   │   ├── Taxonomy.ts        # Taxonomy entity + tree logic
│   │   └── SearchResult.ts    # Search entity + scoring
│   ├── repositories/          # Repository interfaces (contracts)
│   │   ├── IAgentRepository.ts
│   │   ├── ITaxonomyRepository.ts
│   │   └── ISearchRepository.ts
│   └── usecases/              # Business logic orchestration
│       ├── agent/
│       │   ├── GetAgentsUseCase.ts
│       │   ├── GetAgentByIdUseCase.ts
│       │   └── CreateAgentUseCase.ts
│       ├── search/
│       │   └── SearchDocumentsUseCase.ts
│       └── taxonomy/
│           └── GetTaxonomyTreeUseCase.ts
│
├── data/                      # 💾 Data Layer
│   ├── datasources/           # Data providers
│   │   ├── remote/            # API communication
│   │   │   ├── api-client.ts  # Axios configuration
│   │   │   └── AgentRemoteDataSource.ts
│   │   └── local/             # Mock data for dev/test
│   │       └── MockAgentDataSource.ts
│   ├── mappers/               # DTO ↔ Entity transformers
│   │   └── AgentMapper.ts
│   └── repositories/          # Repository implementations
│       └── AgentRepositoryImpl.ts
│
├── presentation/              # 🎨 Presentation Layer
│   ├── hooks/                 # React Query hooks
│   │   └── useAgentsQuery.ts  # Agents data fetching
│   ├── containers/            # Smart components
│   └── stores/                # Zustand UI state
│
└── shared/                    # 🔧 Shared Utilities
    └── config/
        └── di-container.ts    # Dependency injection
```

## 🔑 Key Principles

### 1. Dependency Rule
```
Presentation → Domain ← Data
              ↑
         NO REVERSE
```
- **Domain knows NOTHING** about Presentation or Data implementation
- Data layer implements Domain interfaces
- Presentation uses Domain through Use Cases

### 2. Separation of Concerns

| Layer | Responsibility | Dependencies |
|-------|---------------|--------------|
| **Domain** | Business logic, validation, rules | None (pure) |
| **Data** | API calls, storage, transformation | Domain interfaces |
| **Presentation** | UI rendering, user interaction | Domain use cases |

### 3. Testability
- Each layer can be tested independently
- Mock implementations for repositories
- Use cases are pure business logic

---

## 🧩 Layer Details

### Domain Layer (Pure Business Logic)

```typescript
// Entity with business rules
export interface Agent {
  readonly id: string;
  readonly name: string;
  readonly status: AgentStatus;
  readonly stats: AgentStats;
}

// Business logic function
export function calculateAgentHealthScore(agent: Agent): number {
  const statusScore = agent.status === 'active' ? 100 : 50;
  const progressScore = agent.progress;
  return Math.round((statusScore + progressScore) / 2);
}
```

### Data Layer (External Communication)

```typescript
// Mapper: Transform DTO → Entity
export class AgentMapper {
  static toDomain(dto: AgentDTOType): Agent {
    return {
      id: dto.agent_id,
      name: dto.name,
      status: dto.status,
      // ... transform snake_case to camelCase
    };
  }
}

// Repository: Implement interface
export class AgentRepositoryImpl implements IAgentRepository {
  async getAll(): Promise<Agent[]> {
    const dtos = await this.dataSource.getAll();
    return dtos.map(AgentMapper.toDomain);
  }
}
```

### Presentation Layer (UI Logic)

```typescript
// React Query hook using Use Case
export function useAgentsQuery(params?: AgentFilterParams) {
  const useCase = new GetAgentsUseCase(getAgentRepository());

  return useQuery({
    queryKey: ['agents', params],
    queryFn: () => useCase.execute(params),
  });
}
```

---

## 🔄 Data Flow Example

```
1. User clicks "Load Agents" button
   │
2. Component calls useAgentsQuery() hook
   │
3. Hook creates GetAgentsUseCase with repository
   │
4. UseCase.execute() calls repository.getAll()
   │
5. Repository calls DataSource.getAll() (API or Mock)
   │
6. API returns DTO (snake_case)
   │
7. Mapper transforms DTO → Entity (camelCase)
   │
8. UseCase applies business rules (filtering, sorting)
   │
9. Hook receives data, updates React Query cache
   │
10. Component re-renders with new data
```

---

## 🛠️ Path Aliases

```json
// tsconfig.json
{
  "paths": {
    "@/*": ["./*"],
    "@domain/*": ["./src/domain/*"],
    "@data/*": ["./src/data/*"],
    "@presentation/*": ["./src/presentation/*"],
    "@shared/*": ["./src/shared/*"]
  }
}
```

Usage:
```typescript
import { Agent } from '@domain/entities';
import { getAgentRepository } from '@data/repositories';
import { useAgentsQuery } from '@presentation/hooks';
```

---

## 📚 Migration Guide

### From Old Pattern:
```typescript
// ❌ Old: Direct API call in component
const { data } = useQuery({
  queryFn: () => apiClient.get('/agents')
});
```

### To Clean Architecture:
```typescript
// ✅ New: Use domain hook
import { useAgentsQuery } from '@presentation/hooks';

function AgentsPage() {
  const { data, isLoading } = useAgentsQuery();
  // data.agents is already typed as Agent[]
}
```

---

## 🧪 Testing Strategy

```typescript
// 1. Domain Layer - Pure unit tests
describe('GetAgentsUseCase', () => {
  it('should filter performant agents', async () => {
    const mockRepo = createMockAgentRepository();
    const useCase = new GetAgentsUseCase(mockRepo);
    const result = await useCase.execute();
    expect(result.performantCount).toBeGreaterThan(0);
  });
});

// 2. Data Layer - Integration tests
describe('AgentRepositoryImpl', () => {
  it('should transform DTOs to entities', async () => {
    const repo = new AgentRepositoryImpl(mockDataSource);
    const agents = await repo.getAll();
    expect(agents[0]).toHaveProperty('id'); // not agent_id
  });
});

// 3. Presentation Layer - Component tests
describe('useAgentsQuery', () => {
  it('should return agents list', async () => {
    const { result } = renderHook(() => useAgentsQuery());
    await waitFor(() => expect(result.current.data).toBeDefined());
  });
});
```

---

## 📊 Benefits

| Aspect | Benefit |
|--------|---------|
| **Maintainability** | Clear boundaries make changes localized |
| **Testability** | Each layer independently testable |
| **Reusability** | Domain logic reusable across platforms |
| **Scalability** | Easy to add new features without affecting existing |
| **Onboarding** | New developers understand structure quickly |

---

**Created**: 2025-11-29
**Author**: SPEC-FRONTEND-REDESIGN-001
**Version**: 1.0.0
