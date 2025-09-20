# Agent Factory vs PRD v1.8.1 Gap 분석 보고서

## 개요

PRD v1.8.1의 핵심 요구사항과 현재 구현된 Gemini Agent Factory 설계 간의 Gap을 분석하고 개선 방안을 제시합니다.

---

## 1. 핵심 요구사항 충족도 분석

### 1.1 Agent Factory 요구사항 (PRD 섹션 5.5)

| PRD 요구사항 | 현재 구현 상태 | 충족도 | Gap |
|-------------|---------------|-------|-----|
| **노드 선택→카테고리‑한정 에이전트 생성** | ✅ 부분적 구현 | 70% | 노드 선택 UI 미연동 |
| **Agent Manifest 생성** | ✅ 구현됨 | 90% | YAML 출력 형태 미정의 |
| **필터 canonical 강제** | ❌ 미구현 | 0% | retrieval 필터링 로직 누락 |
| **debate/HITL 토글** | ✅ 구현됨 | 100% | ProcessingConfig에 포함 |
| **매니페스트 미리보기/테스트/저장** | ❌ 미구현 | 0% | 카탈로그 시스템 누락 |

**충족도: 52% (5/5 중 2.6개 완전 충족)**

### 1.2 성능/비용 목표 (PRD 섹션 1.3)

| 지표 | PRD 목표 | 현재 구현 | 충족 가능성 | Gap |
|-----|----------|-----------|------------|-----|
| **p95 지연** | ≤ 4초 | 미측정 | 불확실 | 성능 측정/최적화 체계 부재 |
| **비용/쿼리** | ≤ ₩10 | 미측정 | 불확실 | 비용 계산/제어 로직 부재 |
| **Faithfulness** | ≥ 0.85 | 미측정 | 가능 | RAGAS 평가 시스템 필요 |
| **Answer Relevance** | ≥ 0.8 | 미측정 | 가능 | 품질 메트릭 수집 필요 |

**충족도: 0% (측정 체계 부재)**

### 1.3 7-Step 오케스트레이션 통합 (PRD 섹션 5.5)

| 단계 | PRD 요구사항 | 현재 구현 | 충족도 | Gap |
|-----|-------------|-----------|-------|-----|
| **Step 0** | Agent Enhancement | ✅ 구현 | 100% | - |
| **Step 1** | intent (Agent가 영향) | ✅ 구현 | 80% | 카테고리별 intent 분류 미세조정 |
| **Step 2** | retrieve (Agent 가중치) | ✅ 구현 | 90% | canonical path 필터링 누락 |
| **Step 3** | plan (Agent 전략) | ✅ 구현 | 70% | 카테고리별 plan 전략 부족 |
| **Step 4** | tools/debate (Agent 설정) | ✅ 구현 | 85% | MCP 도구 매핑 필요 |
| **Step 5** | compose (Agent 스타일) | ✅ 구현 | 80% | 응답 형식 템플릿 보강 |
| **Step 6** | cite (출처 요구사항) | ❌ 미구현 | 0% | ≥2개 출처 강제 로직 누락 |
| **Step 7** | respond (최종 검증) | ✅ 구현 | 60% | 품질 임계값 검증 누락 |

**평균 충족도: 71%**

---

## 2. 주요 Gap 상세 분석

### 2.1 ❌ CRITICAL: canonical path 필터링 부재

**PRD 요구사항:**
- Agent Factory가 선택한 노드의 `canonical_path` 기준으로 검색 범위 강제 제한
- 범위 외 자료 접근 차단 (PRD 수용기준 D)

**현재 상태:**
```python
# apps/agent_system/src/integrated_agent_factory.py
# retrieval_config에는 가중치만 있고 필터링 로직이 없음
"retrieval_config": {
    "search_weights": agent_profile.retrieval_config.weights,
    "max_results": agent_profile.retrieval_config.max_results,
    # canonical_path 필터가 누락됨
}
```

**영향도:** HIGH - 보안 및 데이터 거버넌스 위반

### 2.2 ❌ CRITICAL: 출처 품질 강제 로직 부재

**PRD 요구사항:**
- 출처 ≥2개 강제 (PRD 섹션 1.2, 15.B)
- 날짜·버전·Confidence 표기 (PRD 섹션 4.7)

**현재 상태:**
- `cite` 단계 구현 없음
- 출처 검증 로직 부재

**영향도:** HIGH - 품질 KPI 미달성

### 2.3 ❌ MODERATE: 성능/비용 모니터링 부재

**PRD 요구사항:**
- p95≤4s, ≤₩10/쿼리 실시간 모니터링
- 디그레이드 룰 적용 (PRD 섹션 12)

**현재 상태:**
- 성능 측정 로직 없음
- 비용 계산 로직 없음

**영향도:** MODERATE - 운영 안정성 위험

### 2.4 ❌ MODERATE: Agent Catalog 시스템 부재

**PRD 요구사항:**
- 매니페스트 저장/카탈로그 등록 (PRD 섹션 9.2)
- Agent 스프롤 방지 (PRD 섹션 14)

**현재 상태:**
- 일회성 Agent 생성만 가능
- 재사용/관리 체계 없음

**영향도:** MODERATE - 운영 복잡도 증가

---

## 3. 개선 방안 제시

### 3.1 Phase 1: Critical Gap 해결 (우선순위 1)

#### 3.1.1 canonical path 필터링 구현

```python
# apps/agent_system/src/agent_profile.py 확장
@dataclass
class RetrievalConfig:
    # 기존 필드들...
    canonical_paths: List[str] = field(default_factory=list)  # 추가
    enforce_path_filter: bool = True  # 추가

# apps/orchestration/src/langgraph_pipeline.py 수정
async def step_retrieve(state: PipelineState) -> PipelineState:
    # canonical path 필터 적용
    canonical_filter = state.get("agent_config", {}).get("canonical_paths", [])
    if canonical_filter:
        # WHERE canonical_path && ARRAY[...] 쿼리 추가
        pass
```

**예상 공수:** 2-3일

#### 3.1.2 출처 품질 강제 로직 구현

```python
# apps/orchestration/src/citation_validator.py (신규)
class CitationValidator:
    @staticmethod
    async def validate_citations(sources: List[Dict]) -> bool:
        """출처 ≥2개, 날짜/버전/Confidence 검증"""
        if len(sources) < 2:
            return False

        required_fields = ["url", "title", "date", "version", "confidence"]
        return all(all(field in source for field in required_fields)
                  for source in sources)

# step_cite 단계 구현
async def step_cite(state: PipelineState) -> PipelineState:
    citations = await CitationValidator.validate_citations(state["sources"])
    if not citations:
        # 추가 검색 또는 오류 처리
        pass
```

**예상 공수:** 3-4일

### 3.2 Phase 2: 성능/비용 모니터링 (우선순위 2)

#### 3.2.1 성능 측정 시스템

```python
# apps/monitoring/src/performance_tracker.py (신규)
class PerformanceTracker:
    def __init__(self):
        self.metrics = {
            "latency_p95": deque(maxlen=1000),
            "cost_per_query": deque(maxlen=1000),
            "faithfulness_score": deque(maxlen=100)
        }

    async def track_pipeline_performance(self,
                                       start_time: float,
                                       token_usage: Dict,
                                       quality_score: float):
        """실시간 성능 추적"""
        latency = time.time() - start_time
        cost = self._calculate_cost(token_usage)

        # p95 > 4초 또는 비용 > ₩10 시 알람
        if latency > 4.0 or cost > 10.0:
            await self._trigger_degradation()
```

**예상 공수:** 5-7일

### 3.3 Phase 3: Agent Catalog 시스템 (우선순위 3)

#### 3.3.1 Agent Registry 구현

```python
# apps/agent_system/src/agent_registry.py (신규)
class AgentRegistry:
    """Agent 매니페스트 저장/관리"""

    async def save_agent_manifest(self,
                                 agent_profile: AgentProfile,
                                 manifest_data: Dict) -> str:
        """YAML 매니페스트 저장 및 카탈로그 등록"""
        manifest_id = f"agent_{agent_profile.category.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # YAML 형태로 저장
        manifest_yaml = self._generate_yaml_manifest(agent_profile, manifest_data)

        # 데이터베이스에 메타데이터 저장
        await self._save_to_catalog(manifest_id, agent_profile, manifest_yaml)

        return manifest_id
```

**예상 공수:** 4-6일

---

## 4. 구현 우선순위 및 일정

### 4.1 Critical Path (3주)

| Week | 작업 | 담당 | 산출물 |
|------|------|------|-------|
| W1 | canonical path 필터링 구현 | Backend | 검색 필터링 로직 |
| W1 | 출처 품질 강제 로직 구현 | Backend | Citation Validator |
| W2 | 성능 측정 시스템 구현 | DevOps | Performance Tracker |
| W2 | 비용 계산 로직 구현 | Backend | Cost Calculator |
| W3 | Agent Registry 구현 | Backend | YAML Manifest System |
| W3 | 통합 테스트 및 PRD 수용기준 검증 | QA | 수용기준 체크리스트 |

### 4.2 Risk Mitigation

**Risk 1:** canonical path 필터링 성능 이슈
- **Mitigation:** PostgreSQL partial index 활용, 캐싱 레이어 추가

**Risk 2:** 성능 목표 미달성 (p95 > 4초)
- **Mitigation:** 병렬 처리, 결과 캐싱, 모델 경량화

**Risk 3:** 비용 목표 초과 (> ₩10/쿼리)
- **Mitigation:** 토큰 사용량 최적화, 모델 선택 로직

---

## 5. 수용기준 검증 체크리스트

### 5.1 PRD 수용기준 매핑

| PRD 수용기준 | 구현 방안 | 검증 방법 |
|-------------|----------|----------|
| **A) p95≤4s / 비용≤₩10 / 정책 100%** | Performance Tracker | 자동화 모니터링 |
| **B) 출처≥2·날짜·taxonomy_version·Confidence** | Citation Validator | 단위 테스트 |
| **C) 트리 diff/되돌리기·HITL 보정 동작** | Frontend 연동 | E2E 테스트 |
| **D) 카테고리‑한정 에이전트가 범위 외 자료 접근 차단** | canonical path 필터링 | 보안 테스트 |

### 5.2 통합 테스트 시나리오

```python
async def test_agent_factory_integration():
    """Agent Factory 통합 테스트"""

    # 1. 노드 선택하여 Agent 생성
    query = "Python API 개발 방법"
    selected_nodes = ["technology", "programming", "python"]

    agent_profile, pipeline_config = await create_agent_for_query(
        query, {"selected_nodes": selected_nodes}
    )

    # 2. canonical path 필터링 검증
    assert pipeline_config["canonical_paths"] == selected_nodes

    # 3. 7-Step 파이프라인 실행
    response = await execute_enhanced_pipeline(query, pipeline_config)

    # 4. 수용기준 검증
    assert response.latency <= 4.0  # A) 성능
    assert response.cost <= 10.0    # A) 비용
    assert len(response.sources) >= 2  # B) 출처
    assert all("date" in src for src in response.sources)  # B) 메타데이터
    assert response.confidence >= 0.75  # B) 신뢰도

    # 5. 범위 외 접근 차단 검증
    assert all(any(node in src["canonical_path"] for node in selected_nodes)
              for src in response.sources)  # D) 접근 제어
```

---

## 6. 결론 및 권장사항

### 6.1 현재 구현 평가

**강점:**
- 카테고리별 Agent 차별화 잘 구현됨 (70% 완성도)
- LangGraph Pipeline 통합 아키텍처 우수
- 확장 가능한 설계 구조

**약점:**
- 보안 중요 기능 누락 (canonical path 필터링)
- 품질 보장 체계 부재 (출처 검증)
- 운영 모니터링 시스템 부재

### 6.2 권장 실행 계획

1. **즉시 시작 (Critical):** canonical path 필터링 + 출처 검증
2. **2주 내 완료:** 성능/비용 모니터링 시스템
3. **3주 내 완료:** Agent Registry 및 통합 테스트

### 6.3 성공 지표

- PRD 수용기준 100% 통과
- 성능 목표 달성 (p95≤4s, ≤₩10/쿼리)
- 보안 테스트 통과 (canonical path 격리)
- 품질 메트릭 목표 달성 (Faithfulness≥0.85)

**총 Gap 해결 예상 기간: 3주**
**리소스 요구사항: Backend 2명, DevOps 1명, QA 1명**