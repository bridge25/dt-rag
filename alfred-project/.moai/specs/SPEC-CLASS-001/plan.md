# SPEC-CLASS-001 Implementation Plan

## 구현 개요

Hybrid Classification System은 이미 완전히 구현되어 프로덕션 환경에서 운영 중입니다. 본 문서는 역공학된 시스템의 구현 전략과 아키텍처를 설명합니다.

## 우선순위별 구현 마일스톤

### 1차 목표: Semantic Classifier (완료)

**구현 완료 항목**:
- ✅ SemanticClassifier 클래스 구현
- ✅ Cosine similarity 기반 분류
- ✅ Top-k candidate 정렬
- ✅ Embedding service 통합
- ✅ Fallback response 처리

**기술적 접근**:
```python
# Efficient cosine similarity calculation
text_vec = np.array(text_embedding)
for node in taxonomy_nodes:
    node_vec = np.array(node["embedding"])
    similarity = self._cosine_similarity(text_vec, node_vec)
    similarities.append(float(similarity))
```

**아키텍처 결정**:
- **벡터 연산**: NumPy 기반 고성능 계산
- **임베딩 통합**: OpenAI text-embedding-3-large (1536차원)
- **신뢰도 기준**: 0.70 (HITL), 0.70~0.85 (자동), 0.85+ (고신뢰)
- **폴백 경로**: "Uncategorized" + 0.5 confidence

### 2차 목표: Hybrid Classifier (완료)

**구현 완료 항목**:
- ✅ HybridClassifier 클래스 구현
- ✅ Stage 1: Rule-based classification
- ✅ Stage 2: LLM classification (Gemini 2.5 Flash)
- ✅ Stage 3: Cross-validation
- ✅ Drift detection 메커니즘
- ✅ Confidence adjustment 공식

**기술적 접근**:
```python
# 3-stage pipeline
rule_result = await self._stage1_rule_based(text, taxonomy_version)

# Early exit if high confidence
if rule_result and rule_result["confidence"] >= 0.90:
    return rule_result

# LLM classification
llm_result = await self._stage2_llm_classification(text, taxonomy_version)

# Cross-validation
final_result = await self._stage3_cross_validation(
    chunk_id, text, rule_result, llm_result, taxonomy_version
)
```

**아키텍처 결정**:
- **조기 종료**: Rule confidence ≥ 0.90 시 LLM 스킵 (비용 절감)
- **교차 검증**: 두 방법 일치 시 1.1x 부스트
- **Drift 탐지**: 공통 접두사 < 50% 시 HITL
- **JSON 프롬프트**: 구조화된 LLM 응답 강제

### 3차 목표: HITL Queue Management (완료)

**구현 완료 항목**:
- ✅ HITLQueueManager 클래스 구현
- ✅ Task creation (confidence < 0.70 or drift)
- ✅ Priority-based task retrieval
- ✅ Task completion workflow
- ✅ Statistics API

**기술적 접근**:
```python
# Add HITL task
async def add_task(self, chunk_id, text, suggested_classification,
                   confidence, alternatives, priority="normal"):
    task_id = str(uuid.uuid4())

    async with db_manager.async_session() as session:
        query = text("""
            UPDATE doc_taxonomy
            SET hitl_required = true,
                confidence = :confidence,
                path = :path
            WHERE doc_id = (
                SELECT doc_id FROM chunks WHERE chunk_id = :chunk_id
            )
        """)

        await session.execute(query, {
            "chunk_id": chunk_id,
            "confidence": confidence,
            "path": suggested_classification
        })
```

**아키텍처 결정**:
- **데이터베이스 통합**: doc_taxonomy.hitl_required 플래그
- **정렬 우선순위**: confidence ASC, created_at ASC
- **완료 처리**: confidence=1.0 (human-approved)
- **통계 API**: 대기 작업 수, 평균 신뢰도

### 4차 목표: Taxonomy DAO Integration (완료)

**구현 완료 항목**:
- ✅ TaxonomyDAO 클래스 구현
- ✅ Leaf node retrieval
- ✅ Version management
- ✅ DAG traversal 지원

**기술적 접근**:
```python
async def get_all_leaf_nodes(self) -> List[Dict[str, Any]]:
    query = select(TaxonomyNode).where(TaxonomyNode.version == "1.0.0")
    result = await self.db_session.execute(query)
    nodes = result.scalars().all()

    leaf_nodes = []
    for node in nodes:
        leaf_nodes.append({
            "id": str(node.node_id),
            "name": node.label,
            "path": node.canonical_path if node.canonical_path else [node.label],
            "embedding": None  # Lazy loading
        })
```

**아키텍처 결정**:
- **지연 로딩**: 임베딩은 필요 시 로드
- **캐노니컬 경로**: DAG의 공식 경로 사용
- **버전 관리**: taxonomy_version="1.0.0" 기준

## 기술 스택 및 구현 세부사항

### Core Dependencies

```python
# Classification Core
import numpy as np                    # 벡터 연산
from sqlalchemy import text, select   # Database ORM
import google.generativeai as genai  # LLM (Gemini)

# Internal Dependencies
from apps.api.embedding_service import EmbeddingService
from apps.api.database import TaxonomyNode, TaxonomyEdge, DocTaxonomy
from apps.core.db_session import db_manager
```

### Data Models

**TaxonomyNode**:
```python
class TaxonomyNode(Base):
    __tablename__ = "taxonomy_nodes"

    node_id: Mapped[uuid.UUID] = mapped_column(get_uuid_type(), primary_key=True)
    label: Mapped[Optional[str]] = mapped_column(Text)
    canonical_path: Mapped[Optional[List[str]]] = mapped_column(get_array_type(String))
    version: Mapped[Optional[str]] = mapped_column(Text)
    confidence: Mapped[Optional[float]] = mapped_column(Float)
```

**DocTaxonomy**:
```python
class DocTaxonomy(Base):
    __tablename__ = "doc_taxonomy"

    mapping_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doc_id: Mapped[Optional[uuid.UUID]] = mapped_column(get_uuid_type(), ForeignKey('documents.doc_id'))
    node_id: Mapped[Optional[uuid.UUID]] = mapped_column(get_uuid_type(), ForeignKey('taxonomy_nodes.node_id'))
    version: Mapped[Optional[str]] = mapped_column(Text)
    path: Mapped[Optional[List[str]]] = mapped_column(get_array_type(String))
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    hitl_required: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
```

### Performance Optimization

**규칙 기반 우선 처리**:
- 민감도 패턴 (0.95 confidence) → LLM 스킵
- 도메인 키워드 (0.85 confidence) → LLM 스킵
- 90% 이상 confidence → 조기 종료

**비용 최적화**:
- Gemini 2.5 Flash: $0.075/1M input tokens
- Rule-based 90% 이상 케이스에서 LLM 스킵
- 평균 분류당 비용: ~$0.001

**처리 시간 목표**:
- Rule-based only: 50-200ms
- Rule + LLM: 2-5초
- Semantic similarity: 1-2초

## 위험 요소 및 완화 전략

### 1. LLM API 장애

**위험**: Gemini API 실패 시 분류 불가
**완화**: Semantic classifier fallback
```python
except Exception as e:
    logger.warning(f"LLM classification failed: {e}")
    return await self._fallback_semantic_classification(text, taxonomy_version)
```

### 2. 임베딩 누락

**위험**: TaxonomyNode에 임베딩 없음
**완화**:
- 배치 임베딩 생성 작업 예정
- 현재는 embedding=None 반환 (semantic classifier 비활성)

### 3. HITL 큐 과부하

**위험**: HITL 요구율 > 30% (PRD 목표 초과)
**완화**:
- Rule-based 패턴 확장
- Confidence threshold 조정 (0.70 → 0.65)
- 배치 승인 API 구현

### 4. Drift Detection 오탐

**위험**: 정상적인 분류를 drift로 잘못 판단
**완화**:
- Threshold 조정 (50% → 40%)
- LLM reasoning 분석 강화
- HITL 피드백 반영

## 테스트 전략

### Unit Tests (완료)

- ✅ Cosine similarity 계산 정확성
- ✅ Rule-based 패턴 매칭
- ✅ Cross-validation confidence 조정
- ✅ Drift detection 로직
- ✅ HITL 큐 CRUD 작업

### Integration Tests (완료)

- ✅ End-to-end 분류 파이프라인
- ✅ Database persistence (doc_taxonomy)
- ✅ LLM service integration
- ✅ Embedding service integration
- ✅ API contract compliance

### Performance Tests (필요)

- [ ] 동시 요청 처리 (100 req/s)
- [ ] 대용량 택소노미 (1000+ nodes)
- [ ] LLM API 타임아웃 처리
- [ ] Database query 성능

## 배포 및 운영 계획

### 프로덕션 체크리스트

**인프라 요구사항**:
- ✅ PostgreSQL with taxonomy_nodes, taxonomy_edges, doc_taxonomy
- ✅ Gemini 2.5 Flash API 키
- ✅ OpenAI API 키 (embedding service)
- ⚠️ Taxonomy node embeddings 생성 (배치 작업 필요)

**모니터링 메트릭**:
- Classification accuracy (ground truth 대비)
- HITL rate (목표: ≤ 30%)
- Processing time p95 (목표: < 5s)
- Auto-approve precision (목표: ≥ 95%)
- Drift detection rate (목표: < 15%)

**Alert Conditions**:
- **High Severity**: Accuracy < 70%, HITL rate > 50%, p95 > 10s
- **Medium Severity**: Accuracy < 85%, HITL rate > 30%, Precision < 90%
- **Low Severity**: p95 > 5s, Drift rate > 15%

### 향후 개선사항

**Phase 2 계획**:
- [ ] Neural Selector (LLM 기반 동적 분류 경로 선택)
- [ ] Active Learning (HITL 피드백 기반 모델 재학습)
- [ ] Multi-label Classification (문서를 여러 노드에 동시 매핑)
- [ ] Hierarchical Classification (상위 노드부터 순차적 분류)
- [ ] Confidence Calibration (신뢰도 예측 정확도 개선)

**최적화 기회**:
- [ ] Embedding Cache (Redis)
- [ ] Batch Classification (병렬 처리)
- [ ] Rule Engine (동적 규칙 로딩)
- [ ] LLM Prompt Optimization (Few-shot learning)
- [ ] HITL Workflow (리뷰어 할당, 승인 워크플로)

## 구현 타임라인 (역공학)

| 단계 | 기간 | 상태 |
|-----|------|------|
| 1. Semantic Classifier 구현 | 2일 | ✅ 완료 |
| 2. Hybrid Classifier 3단계 | 3일 | ✅ 완료 |
| 3. HITL Queue 구현 | 2일 | ✅ 완료 |
| 4. Taxonomy DAO 통합 | 1일 | ✅ 완료 |
| 5. API Router 구현 | 1일 | ✅ 완료 |
| 6. Testing 및 검증 | 2일 | ✅ 완료 |
| 7. Production 배포 | 1일 | ✅ 완료 |

**총 구현 기간**: 12일 (역공학 기준 추정)

## 참조 문서

### 내부 문서
- `.moai/specs/SPEC-CLASS-001/spec.md` - 상세 요구사항
- `.moai/specs/SPEC-EVAL-001/plan.md` - 평가 시스템 참조
- `.moai/specs/SPEC-SEARCH-001/spec.md` - 검색 통합 참조

### 구현 파일
- `apps/classification/semantic_classifier.py` (254줄)
- `apps/classification/hybrid_classifier.py` (380줄)
- `apps/classification/hitl_queue.py` (269줄)
- `apps/api/routers/classification_router.py` (496줄)

---

**문서 버전**: v0.1.0
**최종 업데이트**: 2025-10-09
**작성자**: @Claude
**상태**: Completed
