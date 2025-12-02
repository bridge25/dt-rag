# DT-RAG API - Clean Architecture

## Overview

This document describes the Clean Architecture implementation for the DT-RAG backend API. The architecture follows the **Dependency Inversion Principle** and separates concerns into distinct layers with clear boundaries.

```
┌────────────────────────────────────────────────────────────────────┐
│                        Presentation Layer                         │
│                     (FastAPI Routers, DTOs)                        │
└─────────────────────────────┬──────────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────────┐
│                        Service Layer                               │
│                   (Application Services)                           │
│        AgentService, SearchService, DocumentService                │
└─────────────────────────────┬──────────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────────┐
│                        Domain Layer                                │
│              (Entities, Use Cases, Interfaces)                     │
│         Pure business logic - NO framework dependencies            │
└─────────────────────────────┬──────────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────────┐
│                         Data Layer                                 │
│            (Repositories, Mappers, ORM Models)                     │
│               SQLAlchemy implementations                           │
└────────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
apps/api/
├── domain/                      # Domain Layer (Pure Business Logic)
│   ├── entities/                # Domain Entities (Immutable)
│   │   ├── agent.py             # Agent, AgentStats, AgentConfig
│   │   ├── document.py          # Document, DocumentChunk
│   │   ├── taxonomy.py          # TaxonomyNode, TaxonomyTree
│   │   └── search.py            # SearchResult, SearchQuery
│   │
│   ├── repositories/            # Repository Interfaces (ABC)
│   │   ├── agent_repository.py  # IAgentRepository
│   │   ├── document_repository.py
│   │   ├── taxonomy_repository.py
│   │   └── search_repository.py
│   │
│   └── usecases/                # Business Use Cases
│       ├── agent/               # Agent-related use cases
│       │   ├── get_agents.py
│       │   ├── create_agent.py
│       │   └── query_agent.py
│       ├── search/              # Search-related use cases
│       │   ├── hybrid_search.py
│       │   └── classify_text.py
│       └── taxonomy/            # Taxonomy-related use cases
│           └── get_taxonomy_tree.py
│
├── data/                        # Data Layer (Infrastructure)
│   ├── repositories/            # Repository Implementations
│   │   ├── agent_repository_impl.py
│   │   ├── document_repository_impl.py
│   │   ├── taxonomy_repository_impl.py
│   │   └── search_repository_impl.py
│   │
│   └── mappers/                 # ORM ↔ Entity Transformers
│       ├── agent_mapper.py
│       ├── document_mapper.py
│       └── taxonomy_mapper.py
│
├── services/                    # Service Layer (Application)
│   ├── agent_service.py         # Agent operations orchestration
│   ├── search_service.py        # Search operations orchestration
│   ├── document_service.py      # Document operations orchestration
│   └── taxonomy_service.py      # Taxonomy operations (legacy)
│
├── shared/                      # Cross-cutting Concerns
│   ├── config/
│   │   └── settings.py          # Application settings
│   └── di_container.py          # Dependency Injection Container
│
├── routers/                     # Presentation Layer (FastAPI)
│   ├── agent_router.py
│   ├── search_router.py
│   └── taxonomy_router.py
│
└── database.py                  # ORM Models & Database Config
```

## Layer Responsibilities

### 1. Domain Layer (`domain/`)

The **innermost layer** containing pure business logic with **zero external dependencies**.

#### Entities (`domain/entities/`)

Immutable data classes representing core business objects:

```python
@dataclass(frozen=True)
class Agent:
    agent_id: UUID
    name: str
    taxonomy_node_ids: List[UUID]
    level: int = 1
    current_xp: float = 0.0

    @property
    def xp_to_next_level(self) -> float:
        return self.level ** 2 * 100

    def calculate_query_xp(self, latency_ms: float, faithfulness: float) -> float:
        # Business logic in entity
        base_xp = 10.0
        speed_bonus = max(0, 5 * (1 - latency_ms / 5000))
        return round((base_xp + speed_bonus) * faithfulness, 2)
```

Key principles:
- **Frozen dataclasses**: Ensure immutability
- **Validation in `__post_init__`**: Enforce business rules
- **Rich domain methods**: Business logic lives with the entity
- **No ORM dependencies**: Pure Python types only

#### Repository Interfaces (`domain/repositories/`)

Abstract base classes defining data access contracts:

```python
class IAgentRepository(ABC):
    @abstractmethod
    async def get_by_id(self, agent_id: UUID) -> Optional[Agent]:
        pass

    @abstractmethod
    async def create(self, params: CreateAgentParams) -> Agent:
        pass
```

Key principles:
- **ABC (Abstract Base Class)**: Enforces implementation
- **Domain types only**: Returns entities, not ORM models
- **No SQLAlchemy imports**: Pure interface definition

#### Use Cases (`domain/usecases/`)

Single-responsibility business operations:

```python
class GetAgentsUseCase:
    def __init__(self, agent_repository: IAgentRepository):
        self._agent_repository = agent_repository

    async def execute(self, **filters) -> GetAgentsResult:
        agents = await self._agent_repository.get_all(params)
        return GetAgentsResult(
            agents=agents,
            statistics=self._calculate_stats(agents)
        )
```

Key principles:
- **Single responsibility**: One use case = one business operation
- **Constructor injection**: Dependencies injected at creation
- **Explicit inputs/outputs**: Clear data contracts

### 2. Data Layer (`data/`)

**Infrastructure layer** implementing domain interfaces with concrete technologies.

#### Repository Implementations (`data/repositories/`)

SQLAlchemy implementations of domain interfaces:

```python
class AgentRepositoryImpl(IAgentRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, agent_id: UUID) -> Optional[Agent]:
        result = await self._session.execute(
            select(AgentModel).where(AgentModel.agent_id == agent_id)
        )
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return AgentMapper.to_domain(model)  # ORM → Entity
```

Key principles:
- **Implements domain interface**: Satisfies contract
- **Uses mappers**: Transforms ORM ↔ Entity
- **Manages transactions**: Session handling

#### Mappers (`data/mappers/`)

Transform between ORM models and domain entities:

```python
class AgentMapper:
    @staticmethod
    def to_domain(model: AgentModel) -> Agent:
        return Agent(
            agent_id=model.agent_id,
            name=model.name,
            level=model.level,
            # ... more fields
        )

    @staticmethod
    def to_model_dict(entity: Agent) -> Dict[str, Any]:
        return {
            "agent_id": entity.agent_id,
            "name": entity.name,
            # ... more fields
        }
```

Key principles:
- **Bidirectional**: ORM → Entity and Entity → ORM dict
- **Static methods**: No state needed
- **Type safety**: Explicit field mapping

### 3. Service Layer (`services/`)

**Application orchestration layer** coordinating use cases and handling cross-cutting concerns.

```python
class AgentService:
    def __init__(
        self,
        agent_repository: IAgentRepository,
        search_repository: Optional[ISearchRepository] = None,
    ):
        self._agent_repository = agent_repository
        self._get_agents = GetAgentsUseCase(agent_repository)
        self._create_agent = CreateAgentUseCase(agent_repository)

    async def get_agents(self, **filters) -> Dict[str, Any]:
        result = await self._get_agents.execute(**filters)
        return {
            "agents": [self._to_dict(a) for a in result.agents],
            "total": result.total_count,
        }
```

Key principles:
- **Orchestration**: Coordinates multiple use cases
- **DTO transformation**: Domain → API response format
- **Cross-cutting concerns**: Logging, caching, error handling

### 4. Presentation Layer (`routers/`)

**FastAPI routers** handling HTTP requests/responses.

```python
@router.get("/agents")
async def get_agents(
    page: int = 1,
    page_size: int = 20,
    service: AgentService = Depends(get_agent_service),
):
    return await service.get_agents(page=page, page_size=page_size)
```

Key principles:
- **Thin layer**: Minimal logic, delegates to services
- **DI via Depends**: FastAPI dependency injection
- **HTTP concerns only**: Request validation, response formatting

## Dependency Injection

### DI Container (`shared/di_container.py`)

Centralized dependency management:

```python
class Container:
    def get_agent_service(self, session: AsyncSession) -> AgentService:
        agent_repo = self.get_agent_repository(session)
        search_repo = self.get_search_repository(session)
        return AgentService(agent_repo, search_repo)

# FastAPI dependency
async def get_agent_service(session: AsyncSession = Depends(get_db_session)):
    yield get_container().get_agent_service(session)
```

### Dependency Flow

```
Router → Depends(get_agent_service)
           ↓
       Container.get_agent_service(session)
           ↓
       AgentService(agent_repo, search_repo)
           ↓
       Use Cases execute with repositories
           ↓
       Repositories use session for DB access
```

## Key Design Patterns

### 1. Repository Pattern
- Abstracts data access behind interfaces
- Domain layer defines contracts
- Data layer provides implementations

### 2. Use Case Pattern
- Single-responsibility business operations
- Clear input/output contracts
- Testable in isolation

### 3. Mapper Pattern
- Transforms between layers
- Prevents ORM leakage into domain
- Centralized mapping logic

### 4. Factory Pattern
- DI Container creates instances
- Manages object lifecycles
- Enables testing with mocks

## Testing Strategy

### Unit Tests (Domain Layer)
```python
def test_agent_xp_calculation():
    agent = Agent(agent_id=uuid4(), name="Test", level=5)
    xp = agent.calculate_query_xp(latency_ms=1000, faithfulness=0.9)
    assert xp > 0
```

### Integration Tests (Data Layer)
```python
async def test_agent_repository():
    async with test_session() as session:
        repo = AgentRepositoryImpl(session)
        agent = await repo.create(CreateAgentParams(name="Test"))
        assert agent.agent_id is not None
```

### Service Tests (With Mocks)
```python
async def test_agent_service():
    mock_repo = Mock(spec=IAgentRepository)
    mock_repo.get_all.return_value = [test_agent]

    service = AgentService(mock_repo)
    result = await service.get_agents()

    assert len(result["agents"]) == 1
```

## Benefits

1. **Testability**: Each layer can be tested in isolation
2. **Maintainability**: Clear separation of concerns
3. **Flexibility**: Easy to swap implementations (e.g., different databases)
4. **Scalability**: Add new features without affecting existing code
5. **Domain Focus**: Business logic is central and protected

## Migration Path

Existing code can be migrated incrementally:

1. **Create domain entities** for existing models
2. **Define repository interfaces** for data access patterns
3. **Implement repositories** wrapping existing DAOs
4. **Create services** orchestrating use cases
5. **Update routers** to use services

## References

- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Domain-Driven Design by Eric Evans](https://domainlanguage.com/ddd/)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
