---
id: AGENT-GROWTH-001
version: 0.1.0
status: completed
created: 2025-10-12
updated: 2025-11-05
author: @sonheungmin
priority: high
category: feature
labels:
  - agent-growth
  - coverage-meter
  - taxonomy
  - gamification
scope:
  packages:
    - apps/api
    - apps/knowledge_builder
  files:
    - database.py
    - coverage_meter.py
    - agent_dao.py
depends_on:
  - DATABASE-001
  - SCHEMA-SYNC-001
---

# @SPEC:AGENT-GROWTH-001: Agent Growth Platform Phase 0 - Foundation Layer

## HISTORY

### v0.1.0 (2025-10-12)
- **INITIAL**: Agent Growth Platform Phase 0 명세 최초 작성
- **AUTHOR**: @sonheungmin
- **SCOPE**: agents 테이블, CoverageMeterService, AgentDAO 구현
- **CONTEXT**: TaxonomySystem_Analysis_v1.0.md 기반 설계
- **DEPENDENCIES**: SPEC-DATABASE-001 (database schema), SPEC-SCHEMA-SYNC-001 (DocTaxonomy)
- **PHASE**: Phase 0 Foundation (1주 예상)

## EARS Requirements

### Ubiquitous Requirements (Core Schema & Services)

**U-REQ-001**: System SHALL maintain Agents table with columns: agent_id (UUID PK), name (TEXT NOT NULL), taxonomy_node_ids (UUID[] NOT NULL), taxonomy_version (TEXT NOT NULL DEFAULT '1.0.0'), scope_description (TEXT), total_documents (INTEGER DEFAULT 0), total_chunks (INTEGER DEFAULT 0), coverage_percent (FLOAT DEFAULT 0.0), last_coverage_update (TIMESTAMP), level (INTEGER DEFAULT 1), current_xp (INTEGER DEFAULT 0), total_queries (INTEGER DEFAULT 0), successful_queries (INTEGER DEFAULT 0), avg_faithfulness (FLOAT DEFAULT 0.0), avg_response_time_ms (FLOAT DEFAULT 0.0), retrieval_config (JSONB DEFAULT '{"top_k": 5, "strategy": "hybrid"}'), features_config (JSONB DEFAULT '{}'), created_at (TIMESTAMP DEFAULT now()), updated_at (TIMESTAMP DEFAULT now()), last_query_at (TIMESTAMP).

**U-REQ-002**: System SHALL enforce constraint on agents.level: MUST be between 1 and 5 inclusive.

**U-REQ-003**: System SHALL enforce constraint on agents.current_xp: MUST be >= 0.

**U-REQ-004**: System SHALL enforce constraint on agents.coverage_percent: MUST be between 0.0 and 100.0 inclusive.

**U-REQ-005**: System SHALL create GIN index on agents.taxonomy_node_ids for array containment queries.

**U-REQ-006**: System SHALL create index on agents.level for level-based filtering.

**U-REQ-007**: System SHALL create index on agents.coverage_percent DESC for coverage ranking.

**U-REQ-008**: System SHALL provide CoverageMeterService class with method calculate_coverage(agent_id, taxonomy_node_ids, version) returning CoverageResult.

**U-REQ-009**: CoverageMeterService.calculate_coverage() SHALL return CoverageResult dataclass with fields: agent_id (str), overall_coverage (float), node_coverage (Dict[str, float]), document_counts (Dict[str, int]), target_counts (Dict[str, int]), version (str).

**U-REQ-010**: System SHALL provide CoverageMeterService.detect_gaps(coverage_result, threshold) method returning List[Gap].

**U-REQ-011**: Gap dataclass SHALL contain fields: node_id (str), current_coverage (float), target_coverage (float), missing_docs (int), recommendation (str).

**U-REQ-012**: System SHALL provide AgentDAO class with CRUD methods: create_agent(), get_agent(), update_agent(), delete_agent(), list_agents().

**U-REQ-013**: AgentDAO.create_agent() SHALL accept parameters: name (str), taxonomy_node_ids (List[UUID]), taxonomy_version (str DEFAULT '1.0.0'), scope_description (str OPTIONAL), retrieval_config (Dict OPTIONAL), features_config (Dict OPTIONAL).

**U-REQ-014**: AgentDAO.create_agent() SHALL calculate initial coverage using CoverageMeterService and store in agents table.

**U-REQ-015**: AgentDAO.list_agents() SHALL support filtering by: status (optional), level (optional), min_coverage (optional), max_results (int DEFAULT 50).

### Event-driven Requirements (Coverage Calculation & Agent Lifecycle)

**E-REQ-001**: WHEN agent is created, System SHALL calculate initial coverage using CoverageMeterService and populate total_documents, total_chunks, coverage_percent fields.

**E-REQ-002**: WHEN agent is created, System SHALL set level=1, current_xp=0, total_queries=0, successful_queries=0.

**E-REQ-003**: WHEN agent is created, System SHALL set created_at and updated_at to current timestamp.

**E-REQ-004**: WHEN CoverageMeterService.calculate_coverage() is invoked, System SHALL retrieve all descendant nodes of selected taxonomy_node_ids using recursive graph traversal.

**E-REQ-005**: WHEN CoverageMeterService.calculate_coverage() is invoked, System SHALL query doc_taxonomy table to count DISTINCT doc_id per node_id WHERE confidence >= 0.7.

**E-REQ-006**: WHEN CoverageMeterService.calculate_coverage() is invoked, System SHALL calculate coverage percentage as (document_count / MAX(target_count, 1)) * 100 for each node.

**E-REQ-007**: WHEN CoverageMeterService.calculate_coverage() is invoked, System SHALL calculate overall_coverage as (SUM(document_counts) / MAX(SUM(target_counts), 1)) * 100.

**E-REQ-008**: WHEN CoverageMeterService.detect_gaps() is invoked with threshold 0.5, System SHALL identify all nodes where coverage_percent < 50%.

**E-REQ-009**: WHEN gap is detected, System SHALL generate recommendation string in format: "Collect {missing_docs} more documents for this topic".

**E-REQ-010**: WHEN agent is updated via AgentDAO.update_agent(), System SHALL set updated_at to current timestamp.

**E-REQ-011**: WHEN agent is deleted via AgentDAO.delete_agent(), System SHALL perform soft delete by setting deleted_at timestamp (if soft delete is implemented) OR hard delete from agents table.

**E-REQ-012**: WHEN AgentDAO.get_agent() receives non-existent agent_id, System SHALL return None (not raise exception).

**E-REQ-013**: WHEN AgentDAO.list_agents() receives no filters, System SHALL return all active agents ordered by created_at DESC.

**E-REQ-014**: WHEN _get_descendant_nodes() is invoked, System SHALL reuse cached NetworkX graph from TaxonomyDAGManager to avoid redundant graph construction.

**E-REQ-015**: WHEN _count_documents_per_node() query executes, System SHALL use native PostgreSQL ARRAY operations (= ANY(:node_ids)) for efficiency.

### State-driven Requirements (Coverage Calculation Logic)

**S-REQ-001**: WHILE using DocTaxonomy table for coverage calculation, System SHALL filter by confidence >= 0.7 to exclude low-quality classifications.

**S-REQ-002**: WHILE calculating node coverage, System SHALL use target_counts from coverage_targets table if exists, OTHERWISE use current document_count as target.

**S-REQ-003**: WHILE building NetworkX graph for descendant traversal, System SHALL cache graph instance per taxonomy version to avoid repeated construction.

**S-REQ-004**: WHILE calculating overall_coverage, System SHALL handle zero target_counts by using MAX(total_target, 1) to prevent division by zero.

**S-REQ-005**: WHILE agent has taxonomy_node_ids array, System SHALL support multiple root nodes for cross-category agents (e.g., ["AI", "Medicine"] scope).

**S-REQ-006**: WHILE agents table has coverage_percent field, System SHALL keep it as cached value and update via scheduled job or on-demand refresh.

**S-REQ-007**: WHILE using PostgreSQL backend, System SHALL leverage GIN index on taxonomy_node_ids for fast array containment queries.

**S-REQ-008**: WHILE using SQLite backend for testing, System SHALL fallback to JSON serialization for array fields via ArrayType TypeDecorator.

**S-REQ-009**: WHILE level is between 1-5, System SHALL reserve level field for future XP/leveling system integration (Phase 2).

**S-REQ-010**: WHILE features_config is JSONB, System SHALL store level-gated feature flags (e.g., {"debate": true, "tools": false}).

### Optional Features (Future Enhancements)

**O-REQ-001**: WHERE user defines custom coverage targets, System MAY create coverage_targets table rows mapping agent_id + node_id to target_document_count.

**O-REQ-002**: WHERE coverage_targets table exists, CoverageMeterService MAY use user-defined targets instead of automatic estimates.

**O-REQ-003**: WHERE agent requires gap detection, System MAY expose GET /agents/{agent_id}/gaps API endpoint returning Gap list.

**O-REQ-004**: WHERE agent queries are tracked in ExecutionLog (Memento Framework), System MAY calculate avg_faithfulness from historical query quality scores.

**O-REQ-005**: WHERE performance monitoring is enabled, System MAY track avg_response_time_ms from query execution timestamps.

### Constraints (Performance & Data Integrity)

**C-REQ-001**: Agent creation including initial coverage calculation SHALL complete within 5 seconds for taxonomies with < 100 nodes.

**C-REQ-002**: CoverageMeterService.calculate_coverage() SHALL execute within 2 seconds for agent scopes with < 50 nodes and < 10,000 documents.

**C-REQ-003**: _get_descendant_nodes() graph traversal SHALL leverage NetworkX descendants() algorithm with O(E) time complexity where E = edge count.

**C-REQ-004**: _count_documents_per_node() query SHALL use single GROUP BY query to avoid N+1 problem.

**C-REQ-005**: agents.taxonomy_node_ids array SHALL NOT be empty (enforce via application-level validation or CHECK constraint).

**C-REQ-006**: agents.name SHALL be unique per agent (UNIQUE constraint optional, enforce via application logic).

**C-REQ-007**: coverage_percent SHALL be calculated to 2 decimal places (e.g., 75.23%).

**C-REQ-008**: CoverageResult.node_coverage dictionary keys SHALL be string UUIDs (not UUID objects) for JSON serialization compatibility.

**C-REQ-009**: Gap.recommendation string SHALL be human-readable and actionable (e.g., "Collect 15 more documents for Machine Learning > Neural Networks").

**C-REQ-010**: AgentDAO methods SHALL use async/await pattern for non-blocking database operations.

**C-REQ-011**: All database writes SHALL use AsyncSession context manager for proper transaction management.

**C-REQ-012**: Foreign key references to taxonomy_nodes.node_id SHALL NOT use ON DELETE CASCADE to preserve agent configuration even if taxonomy node is deleted (application-level validation required).

**C-REQ-013**: agents table schema changes SHALL be versioned via Alembic migration scripts following existing 000X_*.py naming convention.

**C-REQ-014**: CoverageMeterService SHALL reuse TaxonomyDAGManager's cached graph via _build_networkx_graph(version) method to avoid redundant parsing.

**C-REQ-015**: DocTaxonomy confidence filter (>= 0.7) SHALL be configurable via CoverageMeterService constructor parameter (default: 0.7).

## Schema Overview

### Agents Table Definition

**Purpose**: Stores agent metadata, taxonomy scope, and performance metrics for Agent Growth Platform.

**Columns**:
- agent_id: UUID PRIMARY KEY (default: uuid4())
- name: TEXT NOT NULL (agent display name, e.g., "Breast Cancer Treatment Specialist")
- taxonomy_node_ids: UUID[] NOT NULL (selected taxonomy node IDs defining agent scope)
- taxonomy_version: TEXT NOT NULL DEFAULT '1.0.0' (taxonomy version used)
- scope_description: TEXT (nullable, human-readable scope description)
- total_documents: INTEGER DEFAULT 0 (cached document count in scope)
- total_chunks: INTEGER DEFAULT 0 (cached chunk count in scope)
- coverage_percent: FLOAT DEFAULT 0.0 (cached overall coverage percentage)
- last_coverage_update: TIMESTAMP (nullable, last coverage calculation timestamp)
- level: INTEGER DEFAULT 1 (agent level, 1-5, reserved for Phase 2)
- current_xp: INTEGER DEFAULT 0 (current experience points, reserved for Phase 2)
- total_queries: INTEGER DEFAULT 0 (total query count)
- successful_queries: INTEGER DEFAULT 0 (successful query count)
- avg_faithfulness: FLOAT DEFAULT 0.0 (average faithfulness score from Memento)
- avg_response_time_ms: FLOAT DEFAULT 0.0 (average response time in milliseconds)
- retrieval_config: JSONB DEFAULT '{"top_k": 5, "strategy": "hybrid"}' (retrieval configuration)
- features_config: JSONB DEFAULT '{}' (level-gated feature flags)
- created_at: TIMESTAMP DEFAULT now()
- updated_at: TIMESTAMP DEFAULT now()
- last_query_at: TIMESTAMP (nullable, last query execution timestamp)

**Indexes**:
- PRIMARY KEY: agent_id
- GIN INDEX: idx_agents_taxonomy ON agents USING GIN (taxonomy_node_ids)
- INDEX: idx_agents_level ON agents (level)
- INDEX: idx_agents_coverage ON agents (coverage_percent DESC)

**Constraints**:
- CHECK: valid_level CHECK (level >= 1 AND level <= 5)
- CHECK: valid_xp CHECK (current_xp >= 0)
- CHECK: valid_coverage CHECK (coverage_percent >= 0 AND coverage_percent <= 100)

### CoverageResult Dataclass

**Purpose**: Returns coverage calculation results from CoverageMeterService.

**Fields**:
```python
@dataclass
class CoverageResult:
    agent_id: str                      # Agent UUID as string
    overall_coverage: float            # Overall coverage percentage (0.0-100.0)
    node_coverage: Dict[str, float]    # Per-node coverage {node_id: percentage}
    document_counts: Dict[str, int]    # Per-node document count {node_id: count}
    target_counts: Dict[str, int]      # Per-node target count {node_id: target}
    version: str                       # Taxonomy version used
```

### Gap Dataclass

**Purpose**: Represents coverage gap detected by CoverageMeterService.

**Fields**:
```python
@dataclass
class Gap:
    node_id: str                  # Taxonomy node UUID as string
    current_coverage: float       # Current coverage percentage
    target_coverage: float        # Target coverage percentage (threshold * 100)
    missing_docs: int             # Number of missing documents
    recommendation: str           # Human-readable recommendation
```

## Implementation Details

### CoverageMeterService Architecture

**File**: `apps/knowledge_builder/coverage/meter.py`

**Key Methods**:

#### 1. calculate_coverage()
```python
async def calculate_coverage(
    self,
    agent_id: str,
    taxonomy_node_ids: List[str],
    version: str = "1.0.0"
) -> CoverageResult:
    """
    Calculate coverage for agent's taxonomy scope.

    Algorithm:
    1. Get all descendant nodes using NetworkX graph traversal
    2. Query doc_taxonomy for document counts per node (confidence >= 0.7)
    3. Retrieve target counts from coverage_targets or use current counts
    4. Calculate coverage percentages
    5. Return CoverageResult
    """
```

#### 2. _get_descendant_nodes()
```python
async def _get_descendant_nodes(
    self,
    session: AsyncSession,
    root_node_ids: List[str],
    version: str
) -> List[str]:
    """
    Get all descendant nodes recursively using NetworkX.

    Optimization: Reuse TaxonomyDAGManager's cached graph.
    """
    graph = await taxonomy_dag_manager._build_networkx_graph(version)

    descendants = set(root_node_ids)
    for root_id in root_node_ids:
        descendants.update(nx.descendants(graph, root_id))

    return list(descendants)
```

#### 3. _count_documents_per_node()
```python
async def _count_documents_per_node(
    self,
    session: AsyncSession,
    node_ids: List[str],
    version: str
) -> Dict[str, int]:
    """
    Count documents per node using single GROUP BY query.

    SQL:
    SELECT node_id, COUNT(DISTINCT doc_id) as doc_count
    FROM doc_taxonomy
    WHERE node_id = ANY(:node_ids)
      AND version = :version
      AND confidence >= 0.7
    GROUP BY node_id
    """
```

#### 4. detect_gaps()
```python
async def detect_gaps(
    self,
    coverage_result: CoverageResult,
    threshold: float = 0.5
) -> List[Gap]:
    """
    Detect coverage gaps below threshold.

    Returns gaps sorted by missing_docs DESC (highest priority first).
    """
```

### AgentDAO Architecture

**File**: `apps/api/database.py` (or separate `apps/api/agent_dao.py`)

**Key Methods**:

#### 1. create_agent()
```python
async def create_agent(
    session: AsyncSession,
    name: str,
    taxonomy_node_ids: List[UUID],
    taxonomy_version: str = "1.0.0",
    scope_description: str = None,
    retrieval_config: Dict = None,
    features_config: Dict = None
) -> Agent:
    """
    Create new agent with initial coverage calculation.

    Steps:
    1. Validate taxonomy_node_ids exist in taxonomy_nodes table
    2. Calculate initial coverage using CoverageMeterService
    3. Create Agent ORM instance
    4. Insert into database
    5. Return Agent
    """
```

#### 2. get_agent()
```python
async def get_agent(
    session: AsyncSession,
    agent_id: UUID
) -> Optional[Agent]:
    """
    Get agent by ID.

    Returns None if not found (no exception).
    """
```

#### 3. update_agent()
```python
async def update_agent(
    session: AsyncSession,
    agent_id: UUID,
    **kwargs
) -> Agent:
    """
    Update agent fields.

    Automatically sets updated_at to current timestamp.
    """
```

#### 4. delete_agent()
```python
async def delete_agent(
    session: AsyncSession,
    agent_id: UUID
) -> bool:
    """
    Delete agent (hard delete).

    Returns True if deleted, False if not found.
    """
```

#### 5. list_agents()
```python
async def list_agents(
    session: AsyncSession,
    status: Optional[str] = None,
    level: Optional[int] = None,
    min_coverage: Optional[float] = None,
    max_results: int = 50
) -> List[Agent]:
    """
    List agents with optional filters.

    Default order: created_at DESC
    """
```

### Integration Points

#### 1. TaxonomyDAGManager Integration
```python
# Reuse existing graph cache
from apps.api.taxonomy_dag import taxonomy_dag_manager

graph = await taxonomy_dag_manager._build_networkx_graph(version)
```

#### 2. DocTaxonomy Table Usage
```python
# Existing table, no changes required
SELECT node_id, COUNT(DISTINCT doc_id) as doc_count
FROM doc_taxonomy
WHERE node_id = ANY(:node_ids)
  AND version = :version
  AND confidence >= 0.7
GROUP BY node_id;
```

#### 3. SearchDAO.hybrid_search() Integration (Future Phase 1)
```python
# Range-based filtering already implemented
filters = {
    "canonical_in": agent.taxonomy_node_ids,
    "version": agent.taxonomy_version
}
results = await SearchDAO.hybrid_search(query, filters=filters)
```

## Migration Strategy

### Alembic Migration Script: `00XX_add_agents_table.py`

```python
"""Add agents table for Agent Growth Platform Phase 0

Revision ID: 00XX
Revises: 0009
Create Date: 2025-10-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '00XX'
down_revision = '0009'
branch_labels = None
depends_on = None

def upgrade():
    # Detect PostgreSQL backend
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == 'postgresql'

    if is_postgresql:
        # PostgreSQL version with native types
        op.execute("RAISE NOTICE 'Creating agents table (PostgreSQL)'")

        op.create_table(
            'agents',
            sa.Column('agent_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('name', sa.Text(), nullable=False),
            sa.Column('taxonomy_node_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False),
            sa.Column('taxonomy_version', sa.Text(), nullable=False, server_default='1.0.0'),
            sa.Column('scope_description', sa.Text(), nullable=True),
            sa.Column('total_documents', sa.Integer(), server_default='0'),
            sa.Column('total_chunks', sa.Integer(), server_default='0'),
            sa.Column('coverage_percent', sa.Float(), server_default='0.0'),
            sa.Column('last_coverage_update', sa.DateTime(), nullable=True),
            sa.Column('level', sa.Integer(), server_default='1'),
            sa.Column('current_xp', sa.Integer(), server_default='0'),
            sa.Column('total_queries', sa.Integer(), server_default='0'),
            sa.Column('successful_queries', sa.Integer(), server_default='0'),
            sa.Column('avg_faithfulness', sa.Float(), server_default='0.0'),
            sa.Column('avg_response_time_ms', sa.Float(), server_default='0.0'),
            sa.Column('retrieval_config', postgresql.JSONB(), server_default='{"top_k": 5, "strategy": "hybrid"}'),
            sa.Column('features_config', postgresql.JSONB(), server_default='{}'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('last_query_at', sa.DateTime(), nullable=True),
        )

        # Create indexes
        op.create_index('idx_agents_taxonomy', 'agents', ['taxonomy_node_ids'], postgresql_using='gin')
        op.create_index('idx_agents_level', 'agents', ['level'])
        op.create_index('idx_agents_coverage', 'agents', [sa.desc('coverage_percent')])

        # Add constraints
        op.execute("""
            ALTER TABLE agents ADD CONSTRAINT valid_level
            CHECK (level >= 1 AND level <= 5)
        """)
        op.execute("""
            ALTER TABLE agents ADD CONSTRAINT valid_xp
            CHECK (current_xp >= 0)
        """)
        op.execute("""
            ALTER TABLE agents ADD CONSTRAINT valid_coverage
            CHECK (coverage_percent >= 0 AND coverage_percent <= 100)
        """)

        op.execute("RAISE NOTICE 'agents table created successfully'")

    else:
        # SQLite version with type adapters
        op.create_table(
            'agents',
            sa.Column('agent_id', sa.String(36), primary_key=True),
            sa.Column('name', sa.Text(), nullable=False),
            sa.Column('taxonomy_node_ids', sa.Text(), nullable=False),  # JSON array
            sa.Column('taxonomy_version', sa.Text(), nullable=False, server_default='1.0.0'),
            sa.Column('scope_description', sa.Text(), nullable=True),
            sa.Column('total_documents', sa.Integer(), server_default='0'),
            sa.Column('total_chunks', sa.Integer(), server_default='0'),
            sa.Column('coverage_percent', sa.Float(), server_default='0.0'),
            sa.Column('last_coverage_update', sa.DateTime(), nullable=True),
            sa.Column('level', sa.Integer(), server_default='1'),
            sa.Column('current_xp', sa.Integer(), server_default='0'),
            sa.Column('total_queries', sa.Integer(), server_default='0'),
            sa.Column('successful_queries', sa.Integer(), server_default='0'),
            sa.Column('avg_faithfulness', sa.Float(), server_default='0.0'),
            sa.Column('avg_response_time_ms', sa.Float(), server_default='0.0'),
            sa.Column('retrieval_config', sa.Text(), server_default='{"top_k": 5, "strategy": "hybrid"}'),
            sa.Column('features_config', sa.Text(), server_default='{}'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('last_query_at', sa.DateTime(), nullable=True),
        )

        # Create indexes (B-tree only for SQLite)
        op.create_index('idx_agents_level', 'agents', ['level'])
        op.create_index('idx_agents_coverage', 'agents', ['coverage_percent'])

def downgrade():
    op.drop_table('agents')
```

## Test Requirements

### Unit Tests

**File**: `tests/unit/test_coverage_meter.py`

**Coverage Calculation Tests**:
1. Test calculate_coverage() with single root node
2. Test calculate_coverage() with multiple root nodes
3. Test calculate_coverage() with empty taxonomy (no descendants)
4. Test calculate_coverage() with zero documents (coverage = 0%)
5. Test _get_descendant_nodes() graph traversal correctness
6. Test _count_documents_per_node() SQL query result parsing
7. Test detect_gaps() with various thresholds (0.3, 0.5, 0.7)
8. Test detect_gaps() with no gaps (all 100% coverage)

**File**: `tests/unit/test_agent_dao.py`

**AgentDAO CRUD Tests**:
1. Test create_agent() with valid parameters
2. Test create_agent() with invalid taxonomy_node_ids (non-existent nodes)
3. Test get_agent() with valid agent_id
4. Test get_agent() with non-existent agent_id (returns None)
5. Test update_agent() updates fields correctly
6. Test update_agent() sets updated_at timestamp
7. Test delete_agent() removes agent
8. Test list_agents() without filters returns all agents
9. Test list_agents() with level filter
10. Test list_agents() with min_coverage filter

### Integration Tests

**File**: `tests/integration/test_agent_growth_foundation.py`

**End-to-End Tests**:
1. Create agent → verify agents table row exists
2. Create agent → verify initial coverage calculated
3. Create agent with taxonomy scope → verify descendants included in coverage
4. Update agent name → verify updated_at changed
5. Delete agent → verify agents table row removed
6. List agents ordered by coverage_percent DESC
7. Coverage calculation matches manual SQL query result
8. Gap detection identifies nodes below threshold

### Performance Tests

**File**: `tests/performance/test_coverage_performance.py`

**Latency Benchmarks**:
1. Agent creation with 10 nodes, 1K documents → < 5 seconds
2. Agent creation with 50 nodes, 10K documents → < 5 seconds
3. Coverage calculation with 10 nodes → < 2 seconds
4. Coverage calculation with 50 nodes → < 2 seconds
5. Graph traversal for 100-node taxonomy → < 500ms
6. Document count query for 50 nodes → < 1 second

## Related Files

### Source Code
- @CODE:AGENT-GROWTH-001:DATA: apps/api/database.py (Agent ORM model)
- @CODE:AGENT-GROWTH-001:DOMAIN: apps/knowledge_builder/coverage/meter.py (CoverageMeterService)
- @CODE:AGENT-GROWTH-001:DATA: apps/api/agent_dao.py (AgentDAO)

### Migration Files
- @MIGRATION: alembic/versions/00XX_add_agents_table.py

### Dependencies
- SPEC-DATABASE-001: Base database schema and ORM patterns
- SPEC-SCHEMA-SYNC-001: DocTaxonomy composite PK for coverage calculation
- TaxonomyDAGManager (apps/api/taxonomy_dag.py): Graph traversal
- TaxonomyService (apps/api/services/taxonomy_service.py): Taxonomy queries

### Test Files
- @TEST:AGENT-GROWTH-001:UNIT: tests/unit/test_coverage_meter.py
- @TEST:AGENT-GROWTH-001:UNIT: tests/unit/test_agent_dao.py
- @TEST:AGENT-GROWTH-001:INTEGRATION: tests/integration/test_agent_growth_foundation.py
- @TEST:AGENT-GROWTH-001:PERFORMANCE: tests/performance/test_coverage_performance.py

## Future Enhancements (Phase 1-2)

### Phase 1: API Integration (Not in this SPEC)
1. Agent Creation API: POST /agents/from-taxonomy
2. Coverage API: GET /agents/{agent_id}/coverage
3. Gap Detection API: GET /agents/{agent_id}/gaps
4. Agent Query API: POST /agents/{agent_id}/query (with taxonomy scope filtering)

### Phase 2: Growth System (Not in this SPEC)
1. XP calculation from query quality scores (Memento integration)
2. Leveling system with XP thresholds
3. Feature unlocking based on level (debate, tools, etc.)
4. UI dashboard with game-like status display

### Optional: Coverage Targets Table
```sql
CREATE TABLE coverage_targets (
    target_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(agent_id) ON DELETE CASCADE,
    node_id UUID REFERENCES taxonomy_nodes(node_id) ON DELETE CASCADE,
    target_document_count INTEGER NOT NULL DEFAULT 10,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    UNIQUE(agent_id, node_id)
);
```

## Revision History

- v0.1.0 (2025-10-12): Initial specification for Phase 0 Foundation
  - agents table schema with 19 columns
  - CoverageMeterService with calculate_coverage() and detect_gaps()
  - AgentDAO with create/read/update/delete/list methods
  - Integration with existing Taxonomy system and DocTaxonomy
  - Alembic migration script for PostgreSQL/SQLite dual support
  - Test requirements (unit, integration, performance)
