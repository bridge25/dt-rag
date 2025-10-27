# Taxonomy System 분석 및 Coverage Meter 통합 전략

> **작성일**: 2025-10-12
> **목적**: 기존 Taxonomy 시스템 분석 및 Agent Growth Platform의 Coverage Meter 통합 방안 수립

---

## 📋 목차

1. [기존 Taxonomy 시스템 현황](#1-기존-taxonomy-시스템-현황)
2. [핵심 컴포넌트 분석](#2-핵심-컴포넌트-분석)
3. [Coverage Meter 통합 방안](#3-coverage-meter-통합-방안)
4. [Agent 범위 선택 구현 전략](#4-agent-범위-선택-구현-전략)
5. [데이터베이스 스키마 변경](#5-데이터베이스-스키마-변경)
6. [구현 우선순위](#6-구현-우선순위)

---

## 1. 기존 Taxonomy 시스템 현황

### 1.1 전체 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│  Taxonomy Layer (apps/api)                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  taxonomy_dag.py (1061 lines)                           │
│  ├─ TaxonomyDAGManager: 핵심 DAG 관리자                 │
│  ├─ NetworkX 기반 그래프 검증                            │
│  ├─ Semantic versioning (integer-based)                 │
│  ├─ Migration & Rollback (TTR ≤ 15분)                  │
│  └─ Cycle detection & validation                        │
│                                                         │
│  taxonomy_router.py (344 lines)                         │
│  ├─ GET /taxonomy/versions                              │
│  ├─ GET /taxonomy/{version}/tree                        │
│  ├─ GET /taxonomy/{version}/statistics                  │
│  ├─ GET /taxonomy/{version}/validate                    │
│  └─ GET /taxonomy/{version}/search                      │
│                                                         │
│  taxonomy_service.py (293 lines)                        │
│  └─ TaxonomyService: 실제 DB 쿼리 실행                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Database Layer (apps/api/database.py)                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  TaxonomyNode 테이블                                     │
│  ├─ node_id: UUID (PK)                                  │
│  ├─ label: TEXT                                         │
│  ├─ canonical_path: TEXT[] (예: ["AI", "RAG"])         │
│  ├─ version: TEXT                                       │
│  └─ confidence: FLOAT                                   │
│                                                         │
│  TaxonomyEdge 테이블                                     │
│  ├─ parent: UUID (FK, PK)                               │
│  ├─ child: UUID (FK, PK)                                │
│  └─ version: TEXT (PK)                                  │
│                                                         │
│  DocTaxonomy 테이블 (@SPEC:SCHEMA-SYNC-001)             │
│  ├─ doc_id: UUID (FK, PK)                               │
│  ├─ node_id: UUID (FK, PK)                              │
│  ├─ version: TEXT (PK)                                  │
│  ├─ path: TEXT[] (canonical_path 복사)                  │
│  ├─ confidence: FLOAT                                   │
│  ├─ hitl_required: BOOLEAN                              │
│  └─ created_at: TIMESTAMP                               │
│                                                         │
│  TaxonomyMigration 테이블                                │
│  └─ 버전 관리 및 롤백 데이터                             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 1.2 주요 특징

#### ✅ **이미 구현된 기능**
1. **DAG 기반 계층 구조**: NetworkX로 그래프 검증
2. **Semantic Versioning**: 버전별 Taxonomy 관리
3. **Migration & Rollback**: 안전한 구조 변경
4. **Cycle Detection**: 순환 참조 방지
5. **Document Mapping**: DocTaxonomy 테이블로 문서-분류 연결
6. **Confidence Scoring**: 분류 신뢰도 저장

#### ⚠️ **현재 없는 기능**
1. **Coverage Meter**: 토픽별 문서 채움률 계산
2. **Agent Scope Selection**: Taxonomy 범위 기반 에이전트 생성
3. **Knowledge Source Tracking**: 자동/수동 수집 구분
4. **Gap Detection**: 커버리지 공백 자동 탐지

---

## 2. 핵심 컴포넌트 분석

### 2.1 TaxonomyDAGManager (taxonomy_dag.py)

```python
class TaxonomyDAGManager:
    """핵심 기능"""

    async def validate_dag(version) -> ValidationResult:
        """DAG 검증 (cycle, orphaned nodes, semantic consistency)"""
        # NetworkX로 그래프 구축
        graph = await self._build_networkx_graph(version)

        # 1. Cycle detection
        if not nx.is_directed_acyclic_graph(graph):
            cycles = nx.find_cycle(graph)

        # 2. Orphaned nodes
        roots = [n for n in graph.nodes() if graph.in_degree(n) == 0]

        # 3. Disconnected components
        components = nx.weakly_connected_components(graph)

        # 4. Semantic consistency (canonical path 검증)
        # 5. Canonical path uniqueness

    async def get_taxonomy_tree(version) -> Dict[str, Any]:
        """트리 구조 반환 (캐싱 지원)"""
        # 캐시 확인
        cache_key = f"tree_{version}"
        if cache_key in self._graph_cache:
            return self._graph_cache[cache_key]

        # DB에서 nodes + edges 조회
        # 트리 구조로 변환

    async def get_node_ancestry(node_id, version) -> List[Dict]:
        """노드의 조상 경로 반환 (Root → Node)"""
        # NetworkX shortest_path 사용
        path = nx.shortest_path(graph, root, node_id)
```

**활용 가능성**:
- ✅ `get_taxonomy_tree()`: Coverage Meter의 기반 데이터
- ✅ `get_node_ancestry()`: 에이전트 범위 선택 시 경로 표시
- ✅ `validate_dag()`: 새 노드 추가 시 무결성 보장

### 2.2 TaxonomyService (taxonomy_service.py)

```python
class TaxonomyService:
    """실제 DB 쿼리 실행"""

    async def get_tree(version: str) -> Dict:
        """Taxonomy 트리 조회"""
        nodes = await TaxonomyDAO.get_tree(version)
        edges = await self._build_edges(nodes)
        return {"nodes": nodes, "edges": edges}

    async def get_statistics(version: str) -> Dict:
        """통계 정보"""
        # total_nodes, max_depth, unique_paths
        # ⚠️ 현재는 노드 개수만 반환, 문서 개수는 없음!
```

**문제점**:
- ❌ **문서 개수 통계 없음**: Coverage Meter에 필요한 핵심 데이터
- ❌ **토픽별 문서 분포 없음**: 어떤 노드에 문서가 몇 개 있는지 모름

### 2.3 DocTaxonomy 테이블 (database.py:182-211)

```python
class DocTaxonomy(Base):
    __tablename__ = "doc_taxonomy"

    # Composite Primary Key (doc_id, node_id, version)
    doc_id: Mapped[uuid.UUID] = ForeignKey('documents.doc_id', ondelete='CASCADE')
    node_id: Mapped[uuid.UUID] = ForeignKey('taxonomy_nodes.node_id', ondelete='CASCADE')
    version: Mapped[str] = Text

    # 메타데이터
    path: Mapped[List[str]]  # canonical_path 복사 (검색 최적화)
    confidence: Mapped[float]
    hitl_required: Mapped[bool]  # Human-in-the-Loop 필요 여부
    created_at: Mapped[datetime]
```

**중요한 발견**:
- ✅ **이미 문서-분류 매핑 존재**: Coverage 계산의 기반
- ✅ **Confidence 저장**: 고품질 분류 필터링 가능
- ✅ **path 필드**: 빠른 경로 기반 검색

**활용 방법**:
```sql
-- 특정 노드의 문서 개수 (Coverage 계산)
SELECT node_id, COUNT(DISTINCT doc_id) as doc_count
FROM doc_taxonomy
WHERE version = '1.0.0'
  AND confidence >= 0.7  -- 신뢰도 필터
GROUP BY node_id;

-- 특정 경로 prefix의 문서 개수
SELECT path, COUNT(DISTINCT doc_id) as doc_count
FROM doc_taxonomy
WHERE path @> ARRAY['AI', 'RAG']::text[]  -- PostgreSQL array contains
  AND version = '1.0.0'
GROUP BY path;
```

---

## 3. Coverage Meter 통합 방안

### 3.1 Coverage Meter 정의

**목표**: Taxonomy 노드별 문서 채움률을 계산하고 시각화

```python
coverage = (노드에 매핑된 문서 수) / (타깃 문서 수 또는 기준값)
```

**예시**:
```
의학 > 암 치료 > 유방암 (45 docs)
├─ 병기별 커버리지:
│   ├─ Stage I: 12 docs → 100% (타깃 12개)
│   ├─ Stage II: 9 docs → 90% (타깃 10개)
│   ├─ Stage III: 6 docs → 60% (타깃 10개)
│   └─ Stage IV: 3 docs → 30% (타깃 10개)
└─ 전체 커버리지: 30/42 = 71%
```

### 3.2 구현 설계

#### Step 1: CoverageMeterService 신규 생성

```python
# apps/knowledge_builder/coverage/meter.py

class CoverageMeterService:
    """Taxonomy 기반 커버리지 계산"""

    async def calculate_coverage(
        self,
        agent_id: str,
        taxonomy_node_ids: List[str],
        version: str = "1.0.0"
    ) -> CoverageResult:
        """
        에이전트의 커버리지 계산

        Args:
            agent_id: 에이전트 ID
            taxonomy_node_ids: 선택된 Taxonomy 노드 ID 배열
            version: Taxonomy 버전

        Returns:
            CoverageResult: 노드별 문서 개수 및 커버리지 %
        """
        async with db_manager.async_session() as session:
            # 1. 선택된 노드의 모든 하위 노드 조회 (재귀)
            all_node_ids = await self._get_descendant_nodes(
                session, taxonomy_node_ids, version
            )

            # 2. 각 노드의 문서 개수 조회
            coverage_data = await self._count_documents_per_node(
                session, all_node_ids, version
            )

            # 3. 타깃 문서 개수 설정 (사용자 정의 또는 자동 계산)
            targets = await self._get_target_document_counts(
                session, all_node_ids
            )

            # 4. 커버리지 % 계산
            coverage_percentages = {}
            for node_id, doc_count in coverage_data.items():
                target = targets.get(node_id, doc_count)  # 타깃 없으면 현재 개수 사용
                coverage_percentages[node_id] = (doc_count / max(target, 1)) * 100

            # 5. 전체 커버리지 계산
            total_docs = sum(coverage_data.values())
            total_target = sum(targets.values())
            overall_coverage = (total_docs / max(total_target, 1)) * 100

            return CoverageResult(
                agent_id=agent_id,
                overall_coverage=overall_coverage,
                node_coverage=coverage_percentages,
                document_counts=coverage_data,
                target_counts=targets,
                version=version
            )

    async def _get_descendant_nodes(
        self,
        session: AsyncSession,
        root_node_ids: List[str],
        version: str
    ) -> List[str]:
        """재귀적으로 모든 하위 노드 ID 반환"""
        # NetworkX 그래프 활용 또는 재귀 쿼리
        graph = await self._build_graph(session, version)

        descendants = set(root_node_ids)
        for root_id in root_node_ids:
            # NetworkX descendants
            descendants.update(nx.descendants(graph, root_id))

        return list(descendants)

    async def _count_documents_per_node(
        self,
        session: AsyncSession,
        node_ids: List[str],
        version: str
    ) -> Dict[str, int]:
        """각 노드의 문서 개수 집계"""
        query = text("""
            SELECT node_id, COUNT(DISTINCT doc_id) as doc_count
            FROM doc_taxonomy
            WHERE node_id = ANY(:node_ids)
              AND version = :version
              AND confidence >= 0.7  -- 신뢰도 필터
            GROUP BY node_id
        """)

        result = await session.execute(query, {
            "node_ids": node_ids,
            "version": version
        })

        return {str(row[0]): row[1] for row in result.fetchall()}

    async def detect_gaps(
        self,
        coverage_result: CoverageResult,
        threshold: float = 0.5
    ) -> List[Gap]:
        """커버리지 공백 탐지"""
        gaps = []

        for node_id, coverage_pct in coverage_result.node_coverage.items():
            if coverage_pct < threshold * 100:
                gaps.append(Gap(
                    node_id=node_id,
                    current_coverage=coverage_pct,
                    target_coverage=threshold * 100,
                    missing_docs=int(
                        coverage_result.target_counts[node_id]
                        - coverage_result.document_counts[node_id]
                    ),
                    recommendation=f"Collect {missing_docs} more documents for this topic"
                ))

        return gaps

@dataclass
class CoverageResult:
    agent_id: str
    overall_coverage: float  # 전체 커버리지 %
    node_coverage: Dict[str, float]  # 노드별 커버리지 %
    document_counts: Dict[str, int]  # 노드별 문서 개수
    target_counts: Dict[str, int]  # 노드별 타깃 문서 개수
    version: str

@dataclass
class Gap:
    node_id: str
    current_coverage: float
    target_coverage: float
    missing_docs: int
    recommendation: str
```

#### Step 2: API 엔드포인트 추가

```python
# apps/api/routers/coverage_router.py

@coverage_router.get("/agents/{agent_id}/coverage", response_model=CoverageResult)
async def get_agent_coverage(
    agent_id: str,
    version: str = Query("1.0.0", description="Taxonomy version"),
    service: CoverageMeterService = Depends(get_coverage_service)
):
    """
    에이전트의 커버리지 조회

    Returns:
        - overall_coverage: 전체 커버리지 %
        - node_coverage: 노드별 커버리지 %
        - document_counts: 노드별 문서 개수
    """
    # agents 테이블에서 taxonomy_node_ids 조회
    agent = await AgentDAO.get_agent(agent_id)

    if not agent:
        raise HTTPException(404, "Agent not found")

    coverage = await service.calculate_coverage(
        agent_id, agent.taxonomy_node_ids, version
    )

    return coverage

@coverage_router.get("/agents/{agent_id}/gaps", response_model=List[Gap])
async def get_agent_gaps(
    agent_id: str,
    threshold: float = Query(0.5, ge=0.0, le=1.0, description="Coverage threshold"),
    service: CoverageMeterService = Depends(get_coverage_service)
):
    """
    에이전트의 커버리지 공백 탐지

    Returns:
        - 커버리지가 threshold 미만인 노드 목록
        - 추천 보강 액션
    """
    agent = await AgentDAO.get_agent(agent_id)
    coverage = await service.calculate_coverage(
        agent_id, agent.taxonomy_node_ids, "1.0.0"
    )

    gaps = await service.detect_gaps(coverage, threshold)

    return gaps
```

### 3.3 기존 시스템 통합 포인트

**1. TaxonomyDAGManager 활용**:
```python
# Coverage Meter에서 그래프 활용
from ..api.taxonomy_dag import taxonomy_dag_manager

async def _build_graph(session, version):
    # 기존 캐시 재사용
    return await taxonomy_dag_manager._build_networkx_graph(version)
```

**2. TaxonomyService 확장**:
```python
# apps/api/services/taxonomy_service.py

async def get_statistics(self, version: str) -> Dict[str, Any]:
    """통계 확장: 문서 개수 추가"""
    async with db_manager.async_session() as session:
        # 기존 쿼리
        query = text("""
            SELECT
                t.node_id,
                t.label,
                COUNT(DISTINCT dt.doc_id) as doc_count,
                AVG(dt.confidence) as avg_confidence
            FROM taxonomy_nodes t
            LEFT JOIN doc_taxonomy dt ON t.node_id = dt.node_id
            WHERE t.version = :version
            GROUP BY t.node_id, t.label
        """)

        result = await session.execute(query, {"version": version})

        node_stats = []
        for row in result.fetchall():
            node_stats.append({
                "node_id": str(row[0]),
                "label": row[1],
                "document_count": row[2],
                "avg_confidence": float(row[3]) if row[3] else 0.0
            })

        return {
            "total_nodes": len(node_stats),
            "total_documents": sum(n["document_count"] for n in node_stats),
            "node_statistics": node_stats
        }
```

---

## 4. Agent 범위 선택 구현 전략

### 4.1 에이전트 생성 플로우

```
사용자 → Taxonomy Tree UI 조회 → 노드 선택 → 에이전트 생성
```

#### UI Flow

```typescript
// apps/frontend/components/AgentCreation.tsx

interface TaxonomyNode {
  node_id: string;
  label: string;
  canonical_path: string[];
  children: TaxonomyNode[];
  document_count: number;  // Coverage Meter 데이터
}

function TaxonomyTreeSelector() {
  const [selectedNodes, setSelectedNodes] = useState<string[]>([]);
  const [taxonomyTree, setTaxonomyTree] = useState<TaxonomyNode | null>(null);
  const [coverage, setCoverage] = useState<CoverageResult | null>(null);

  // 1. Taxonomy Tree 로드
  useEffect(() => {
    fetch('/api/v1/taxonomy/1.0.0/tree')
      .then(res => res.json())
      .then(data => setTaxonomyTree(data));
  }, []);

  // 2. 노드 선택 시 Coverage 미리보기
  const handleNodeSelect = async (nodeId: string) => {
    setSelectedNodes([...selectedNodes, nodeId]);

    // Coverage 미리 계산
    const coverageRes = await fetch('/api/v1/coverage/preview', {
      method: 'POST',
      body: JSON.stringify({ node_ids: [...selectedNodes, nodeId] })
    });
    const coverageData = await coverageRes.json();
    setCoverage(coverageData);
  };

  // 3. 에이전트 생성
  const handleCreateAgent = async () => {
    const response = await fetch('/api/v1/agents/from-taxonomy', {
      method: 'POST',
      body: JSON.stringify({
        name: "유방암 치료 전문가",
        taxonomy_node_ids: selectedNodes,
        version: "1.0.0"
      })
    });

    const agent = await response.json();
    router.push(`/agents/${agent.agent_id}`);
  };

  return (
    <div>
      <TaxonomyTreeView
        tree={taxonomyTree}
        selectedNodes={selectedNodes}
        onNodeSelect={handleNodeSelect}
      />

      {coverage && (
        <CoveragePreview coverage={coverage} />
      )}

      <Button onClick={handleCreateAgent}>에이전트 생성</Button>
    </div>
  );
}
```

### 4.2 범위 기반 검색 필터링

에이전트가 쿼리를 받으면, Taxonomy 범위 내에서만 검색:

```python
# apps/api/routers/orchestration_router.py

@orchestration_router.post("/agents/{agent_id}/query")
async def query_agent(
    agent_id: str,
    request: QueryRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """에이전트 쿼리 (Taxonomy 범위 제한)"""

    # 1. 에이전트 조회
    agent = await AgentDAO.get_agent(session, agent_id)

    if not agent:
        raise HTTPException(404, "Agent not found")

    # 2. Taxonomy 범위 내 문서만 검색
    filters = {
        "canonical_in": agent.taxonomy_node_ids,  # Taxonomy 범위 필터
        "version": agent.taxonomy_version
    }

    # 3. 하이브리드 검색 (필터 적용)
    search_results = await SearchDAO.hybrid_search(
        query=request.query,
        filters=filters,
        topk=agent.retrieval_config.get("top_k", 5)
    )

    # 4. LangGraph Pipeline 실행
    answer = await langgraph_service.execute_pipeline(
        query=request.query,
        search_results=search_results,
        agent_config=agent.features_config
    )

    # 5. XP 부여 (Agent Growth System)
    xp_gained = await calculate_xp(answer.quality)
    await AgentDAO.gain_xp(session, agent_id, xp_gained)

    return answer
```

**핵심**: `SearchDAO.hybrid_search()`에 `filters={"canonical_in": node_ids}` 전달

**기존 database.py:958-994 활용**:
```python
# apps/api/database.py:_build_filter_clause()

@staticmethod
def _build_filter_clause(filters: Dict = None) -> str:
    """필터 조건 SQL 절 생성"""
    if not filters:
        return ""

    conditions = []

    # canonical_in 필터 (이미 구현됨!)
    if "canonical_in" in filters:
        canonical_paths = filters["canonical_in"]
        if canonical_paths:
            path_conditions = []
            for path in canonical_paths:
                if isinstance(path, list) and path:
                    path_str = "{" + ",".join(f"'{p}'" for p in path) + "}"
                    path_conditions.append(f"dt.path = '{path_str}'::text[]")

            if path_conditions:
                conditions.append(f"({' OR '.join(path_conditions)})")

    return " AND " + " AND ".join(conditions) if conditions else ""
```

**발견**: 이미 `canonical_in` 필터가 구현되어 있음! 바로 사용 가능.

---

## 5. 데이터베이스 스키마 변경

### 5.1 agents 테이블 (신규)

```sql
CREATE TABLE agents (
    agent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,

    -- Taxonomy 범위
    taxonomy_node_ids UUID[] NOT NULL,  -- 선택한 노드 ID 배열
    taxonomy_version TEXT NOT NULL DEFAULT '1.0.0',
    scope_description TEXT,  -- "유방암 치료 전문가"

    -- 지식 통계 (Coverage Meter 결과 캐시)
    total_documents INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 0,
    coverage_percent FLOAT DEFAULT 0.0,
    last_coverage_update TIMESTAMP,

    -- 레벨 시스템
    level INTEGER DEFAULT 1,
    current_xp INTEGER DEFAULT 0,
    total_queries INTEGER DEFAULT 0,
    successful_queries INTEGER DEFAULT 0,

    -- 성능 지표
    avg_faithfulness FLOAT DEFAULT 0.0,
    avg_response_time_ms FLOAT DEFAULT 0.0,

    -- Config (JSON)
    retrieval_config JSONB DEFAULT '{"top_k": 5, "strategy": "hybrid"}',
    features_config JSONB DEFAULT '{}',  -- 레벨별 Feature Flags

    -- 메타
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_query_at TIMESTAMP,

    CONSTRAINT valid_level CHECK (level >= 1 AND level <= 5),
    CONSTRAINT valid_xp CHECK (current_xp >= 0),
    CONSTRAINT valid_coverage CHECK (coverage_percent >= 0 AND coverage_percent <= 100)
);

-- 인덱스
CREATE INDEX idx_agents_taxonomy ON agents USING GIN (taxonomy_node_ids);
CREATE INDEX idx_agents_level ON agents (level);
CREATE INDEX idx_agents_coverage ON agents (coverage_percent DESC);
```

### 5.2 agent_knowledge_sources 테이블 (신규)

```sql
CREATE TABLE agent_knowledge_sources (
    source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(agent_id) ON DELETE CASCADE,

    -- 지식 소스 타입
    source_type TEXT NOT NULL CHECK (source_type IN ('autonomous', 'manual')),
    -- 'autonomous': Knowledge Builder 자동 수집
    -- 'manual': 사용자 직접 업로드

    -- 문서 참조
    document_ids UUID[],  -- documents 테이블 ID 배열

    -- 메타
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,  -- "NCCN Guidelines 자동 수집"

    -- 통계 (캐시)
    document_count INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0
);

CREATE INDEX idx_agent_knowledge_agent ON agent_knowledge_sources (agent_id);
CREATE INDEX idx_agent_knowledge_type ON agent_knowledge_sources (source_type);
```

### 5.3 coverage_targets 테이블 (선택 사항)

```sql
-- 사용자 정의 커버리지 타깃 (선택 사항)
CREATE TABLE coverage_targets (
    target_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(agent_id) ON DELETE CASCADE,
    node_id UUID REFERENCES taxonomy_nodes(node_id) ON DELETE CASCADE,

    -- 타깃 문서 개수
    target_document_count INTEGER NOT NULL DEFAULT 10,

    -- 메타
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(agent_id, node_id)
);

CREATE INDEX idx_coverage_targets_agent ON coverage_targets (agent_id);
```

### 5.4 기존 DocTaxonomy 활용

**변경 불필요**: 이미 완벽한 구조

```sql
-- 기존 테이블 그대로 사용
SELECT
    dt.node_id,
    tn.label,
    tn.canonical_path,
    COUNT(DISTINCT dt.doc_id) as doc_count,
    AVG(dt.confidence) as avg_confidence
FROM doc_taxonomy dt
JOIN taxonomy_nodes tn ON dt.node_id = tn.node_id
WHERE dt.version = '1.0.0'
  AND dt.confidence >= 0.7
  AND tn.node_id = ANY(:agent_taxonomy_node_ids)  -- 범위 필터
GROUP BY dt.node_id, tn.label, tn.canonical_path
ORDER BY doc_count DESC;
```

---

## 6. 구현 우선순위

### Phase 0: Foundation (1주)

#### ✅ 즉시 활용 가능한 것
1. **DocTaxonomy 기반 문서 카운트**
   - 파일: `apps/api/services/taxonomy_service.py`
   - 작업: `get_statistics()` 메서드 확장 (10줄)

2. **범위 기반 검색 필터**
   - 파일: `apps/api/database.py`
   - 작업: 이미 구현됨! `_build_filter_clause()` 활용

3. **Taxonomy Tree API**
   - 파일: `apps/api/routers/taxonomy_router.py`
   - 작업: 이미 구현됨! `/taxonomy/{version}/tree` 활용

#### 🆕 신규 구현 필요한 것
4. **agents 테이블 생성**
   - 파일: `apps/api/database.py`
   - 작업: SQLAlchemy 모델 추가 (30줄)
   - 마이그레이션: Alembic 스크립트

5. **AgentDAO 구현**
   - 파일: `apps/api/database.py` (또는 신규 `agent_dao.py`)
   - 작업: CRUD 메서드 (100줄)

6. **CoverageMeterService 구현**
   - 파일: `apps/knowledge_builder/coverage/meter.py` (신규)
   - 작업: 커버리지 계산 로직 (200줄)

### Phase 1: Integration (2주)

7. **Agent Creation API**
   - 파일: `apps/api/routers/agent_router.py`
   - 엔드포인트: `POST /agents/from-taxonomy`

8. **Coverage API**
   - 파일: `apps/api/routers/coverage_router.py` (신규)
   - 엔드포인트:
     - `GET /agents/{agent_id}/coverage`
     - `GET /agents/{agent_id}/gaps`

9. **Agent Query API (Taxonomy 범위 제한)**
   - 파일: `apps/api/routers/orchestration_router.py`
   - 수정: 기존 쿼리 로직에 범위 필터 추가

10. **UI: Taxonomy Tree Selector**
    - 파일: `apps/frontend/components/TaxonomyTreeSelector.tsx` (신규)
    - 작업: 트리 뷰 + 선택 + 미리보기

### Phase 2: Growth System (2주)

11. **XP & Leveling System**
    - 파일: `apps/knowledge_builder/growth/leveling.py` (신규)
    - 작업: XP 계산, 레벨업 로직

12. **Memento Integration**
    - 파일: 기존 `apps/orchestration/src/` 확장
    - 작업: ExecutionLog → XP 연동

13. **UI: Agent Status Dashboard**
    - 파일: `apps/frontend/components/AgentDashboard.tsx` (신규)
    - 작업: 상태창 UI (지식/경험/능력/커버리지)

---

## 📊 요약

### ✅ 기존 시스템 강점
1. **DAG 기반 Taxonomy**: 검증된 구조, 버전 관리 완료
2. **DocTaxonomy 매핑**: 문서-분류 연결 완료
3. **범위 기반 필터**: 이미 구현됨 (`canonical_in`)
4. **API 인프라**: Taxonomy Tree API 사용 가능

### 🆕 추가 필요 사항
1. **Coverage Meter**: 노드별 문서 개수 집계 및 시각화
2. **agents 테이블**: 에이전트 메타데이터 저장
3. **Agent Creation Flow**: Taxonomy 선택 → 에이전트 생성
4. **Growth System**: XP/레벨/능력 해금

### 🔗 통합 포인트
1. **TaxonomyDAGManager**: 그래프 검증 및 노드 조회
2. **DocTaxonomy**: 커버리지 계산의 기반
3. **SearchDAO.hybrid_search()**: 범위 필터 적용
4. **Memento Framework**: ExecutionLog → XP 연동

### 📈 예상 작업량
- **Phase 0 (Foundation)**: 5-7일 (agents 테이블 + Coverage 계산)
- **Phase 1 (Integration)**: 10-14일 (API + UI)
- **Phase 2 (Growth)**: 10-12일 (레벨 시스템 + Memento)
- **총 기간**: 25-33일 (약 5-7주)

---

**다음 단계**: `agents` 테이블 스키마 확정 및 마이그레이션 스크립트 작성
