# 🎯 Taxonomy RAG 프로젝트 현황 분석 및 구현 계획

## 📊 현재 프로젝트 상태 (실제 코드 검증 기반)

### ⚠️ 스캐폴딩 및 부분 구현 상태

#### 1. 기반 인프라 (부분 구축)
- ✅ PostgreSQL + pgvector 마이그레이션 파일 3개 존재
- ✅ Common-schemas 패키지 존재 (중복 없음, Codex 오류)
- ✅ 12개 서브에이전트 MD 파일 및 knowledge-base 연결 설정 완료

#### 2. A팀 (Database/API) - 실행 불가능 상태
- ❌ **database.py SQLAlchemy 오류**: execute() 메서드 파라미터 전달 방식 오류 (172, 227행)
- ❌ **스키마 불일치**: chunks 테이블 - ORM 모델과 실제 마이그레이션 불일치
  - ORM: title, source_url, taxonomy_path 포함
  - 실제 DB: text, span, chunk_index, metadata만 존재
- ⚠️ FastAPI 라우터는 파일 존재하나 더미 구현

#### 3. B팀 (Orchestration) - 구문 오류로 실행 불가
- ❌ **langgraph_pipeline.py 구문 오류**:
  - `import random` 누락 (224, 232행에서 사용)
  - 238-269행 들여쓰기 오류
- ❌ **main.py 스텁 상태**: get_pipeline(), create_cbr_system() 등이 None 반환 (45-49행)
- ⚠️ 7-step 파이프라인 구조는 있으나 실제 구현 없음

#### 4. C팀 (Frontend) - 디렉토리만 존재
- ✅ components 폴더 구조는 생성됨
- ❌ 실제 React/TypeScript 코드 없음

### 🔴 즉시 수정이 필요한 버그들

1. **langgraph_pipeline.py**
   - 11행 다음에 `import random` 추가
   - 238-269행 들여쓰기 수정

2. **database.py**
   - SQLAlchemy 2.0 방식으로 execute 호출 수정
   - dictionary 파라미터 바인딩 사용

3. **DB 스키마 동기화**
   - chunks 테이블 마이그레이션 수정 또는
   - ORM 모델을 실제 스키마에 맞게 수정

## 🚀 구현 계획 (버그 수정 우선 + 서브에이전트 활용)

## Phase 0: 즉시 버그 수정 (Day 1-2)

### 🔧 database-architect가 DB 문제 해결
1. **스키마 불일치 해결**
   - `apps/api/database.py` DocumentChunk 모델 수정
   - 실제 마이그레이션과 일치하도록 title, source_url, taxonomy_path 제거
   - metadata JSONB 필드를 통해 추가 정보 저장

2. **SQLAlchemy 2.0 호출 방식 수정**
   - execute(query, param1, param2) → execute(text(query), {"param1": value1})
   - 172행, 227행 수정

### 🔧 langgraph-orchestrator가 파이프라인 수정
1. **구문 오류 수정**
   - 11행에 `import random` 추가
   - 238-269행 들여쓰기 수정
   - main.py의 더미 함수들을 실제 구현체로 교체

## Phase 1: Database & Search Foundation (Week 1)

### 1. database-architect + hybrid-search-specialist로 벡터 검색 구현
- embeddings 테이블과 chunks 테이블 연동 쿼리 작성
- OpenAI/Cohere 임베딩 함수 구현
- 실제 BM25 + Vector 하이브리드 검색 구현 (현재 더미)
- Cross-encoder reranking 로직 추가

### 2. document-ingestion-specialist로 문서 처리 파이프라인 구축
- PDF, Markdown, HTML 파서 구현
- Chunking 전략 (sliding window, semantic)
- PII 필터링 로직
- 임베딩 생성 및 저장

### 3. taxonomy-architect로 DAG 구조 완성
- 현재 3개 마이그레이션을 기반으로 추가 기능 구현
- Rollback 프로시저 구현
- Cycle detection 알고리즘

## Phase 2: Classification & Orchestration (Week 2)

### 4. classification-pipeline-expert로 분류 시스템 구현
- Rule-based 분류기 (키워드, 패턴)
- LLM 기반 분류기 (GPT-4, Claude)
- Confidence scoring 로직
- HITL 큐 관리 시스템

### 5. langgraph-orchestrator로 7-step 파이프라인 완성
- 각 단계별 실제 구현 (현재 스캐폴딩만 있음)
- MCP 도구 통합
- 에러 복구 메커니즘
- 성능 최적화

### 6. api-designer로 REST API 완성
- OpenAPI 스펙 업데이트
- Rate limiting 구현
- API 키 인증 시스템
- Request/Response 검증

## Phase 3: Frontend & Monitoring (Week 3)

### 7. tree-ui-developer로 프론트엔드 구현
- React 트리 컴포넌트 (virtual scrolling)
- 버전 드롭다운 및 diff viewer
- HITL 큐 인터페이스
- 실시간 업데이트 (WebSocket)

### 8. observability-engineer로 모니터링 설정
- Langfuse 통합
- Grafana 대시보드
- SLO/SLI 정의 (p95 ≤ 4s, cost ≤ ₩10/query)
- Alert 규칙 설정

### 9. security-compliance-auditor로 보안 강화
- SQL injection 방어
- Rate limiting 구현
- PII 탐지 및 마스킹
- 감사 로그 시스템

## Phase 4: Evaluation & Deployment (Week 4)

### 10. rag-evaluation-specialist로 품질 평가
- RAGAS 프레임워크 설정
- Golden dataset 생성
- Faithfulness ≥ 0.85 검증
- A/B 테스트 구현

### 11. agent-factory-builder로 에이전트 관리
- 12개 서브에이전트 통합
- 카테고리별 에이전트 매핑
- 동적 에이전트 로딩
- 권한 관리 시스템

### 12. 통합 테스트 및 배포
- E2E 테스트 시나리오
- 성능 벤치마크
- Docker 컨테이너화
- CI/CD 파이프라인 완성

## 📋 즉시 시작 가능한 작업들 (우선순위별)

### 🚨 Priority 1: 버그 수정 (Phase 0)

#### 1. database-architect: DB 오류 수정
```python
# apps/api/database.py 수정
class DocumentChunk(Base):
    __tablename__ = "chunks"
    chunk_id: Mapped[str] = mapped_column(String, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # title, source_url, taxonomy_path 제거
    meta_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

# SQLAlchemy 2.0 방식으로 수정
result = await session.execute(text(query), {"param1": value1})
```

#### 2. langgraph-orchestrator: 구문 오류 수정
```python
# apps/orchestration/src/langgraph_pipeline.py
import random  # 11행에 추가

# 238-269행 들여쓰기 수정
# main.py의 None 반환 함수들 실제 구현
```

### ⚡ Priority 2: 핵심 기능 구현 (Phase 1)

#### 3. hybrid-search-specialist: 실제 검색 구현
```python
# apps/api/routers/search.py에 실제 하이브리드 검색 구현
# 현재 더미 데이터 제거하고 실제 embeddings 테이블 연동
```

#### 4. classification-pipeline-expert: 분류 시스템 구현
```python
# apps/orchestration/src/agents/classifier.py 실제 구현
# Confidence scoring 및 HITL 로직 추가
```

#### 5. tree-ui-developer: Frontend 구현
```typescript
# apps/frontend-admin/src/components/tree/에 React 컴포넌트 구현
# Virtual scrolling으로 10,000+ 노드 지원
```

## 🎯 서브에이전트 역할 분담

| 서브에이전트 | 주요 담당 영역 | 구현 파일 위치 |
|------------|-------------|--------------|
| database-architect | DB 스키마, 마이그레이션 | `alembic/versions/`, `apps/api/database.py` |
| hybrid-search-specialist | BM25+Vector 검색 | `apps/api/routers/search.py` |
| document-ingestion-specialist | 문서 처리 파이프라인 | `apps/ingestion/` (신규) |
| classification-pipeline-expert | 분류 시스템 | `apps/orchestration/src/agents/classifier.py` |
| langgraph-orchestrator | 7-step 파이프라인 | `apps/orchestration/src/langgraph_pipeline.py` |
| tree-ui-developer | 프론트엔드 UI | `apps/frontend-admin/src/components/tree/` |
| api-designer | REST API 설계 | `apps/api/routers/`, `docs/openapi.yaml` |
| observability-engineer | 모니터링 시스템 | `apps/monitoring/` (신규) |
| security-compliance-auditor | 보안 검증 | `apps/api/security/` (신규) |
| rag-evaluation-specialist | 품질 평가 | `tests/evaluation/` (신규) |
| taxonomy-architect | 택소노미 구조 | `apps/api/taxonomy/` (신규) |
| agent-factory-builder | 에이전트 관리 | `apps/orchestration/src/agents/factory.py` (신규) |

## 📈 성공 지표

### 성능 목표
- **응답 시간**: p95 ≤ 4초
- **처리 비용**: ≤ ₩10/쿼리
- **정확도**: Faithfulness ≥ 0.85
- **가용성**: 99.5% uptime

### 기능 목표
- **택소노미 노드**: 10,000+ 지원
- **동시 사용자**: 100+ 지원
- **HITL 처리**: 15분 이내 응답
- **버전 롤백**: 15분 이내 완료

## 🔄 개발 프로세스

1. **Daily Standup**: 각 서브에이전트 진행상황 공유
2. **Code Review**: PR 기반 리뷰 (2명 이상 승인)
3. **Integration Test**: 매일 저녁 통합 테스트
4. **Performance Test**: 주 2회 성능 벤치마크

## 📞 커뮤니케이션 채널

- **기술 이슈**: GitHub Issues
- **PR 리뷰**: GitHub Pull Requests
- **일일 동기화**: Slack #taxonomy-rag
- **긴급 이슈**: 직접 멘션 또는 전화

---

**시작일**: 2025-09-17
**목표 완료일**: 2025-10-15 (4주)
**프로젝트 리더**: TBD
**기술 스택**: PostgreSQL, pgvector, FastAPI, LangGraph, React, TypeScript

---

## 🔍 Codex 검증 결과

### 검증 항목별 정확도 (4/5 정확)
- ✅ DB 스키마 불일치: ORM vs 마이그레이션 불일치 확인됨
- ✅ SQLAlchemy 오류: execute() 파라미터 전달 방식 오류 확인됨
- ✅ LangGraph 구문 오류: random import 누락, 들여쓰기 문제 확인됨
- ❌ Common-schemas 중복: 실제로는 중복 없음 (Codex 오류)
- ✅ 오케스트레이션 스텁: None 반환하는 더미 함수들 확인됨

### 주요 교훈
1. **현실적 상태 평가**: "완료"가 아닌 "스캐폴딩" 또는 "부분 구현" 상태로 정확히 표현
2. **버그 우선 수정**: 기능 추가보다 기존 코드 동작성 확보가 우선
3. **단계적 접근**: Phase 0 (버그 수정) → Phase 1-4 (기능 구현) 순서