---
id: PRODUCT-001
version: 2.0.0
status: active
created: 2025-10-01
updated: 2025-10-13
authors: ["@project-manager", "@sonheungmin"]
---

# . Product Definition

## HISTORY

### v2.0.0 (2025-10-13)
- **LEGACY_ANALYSIS**: 기존 프로젝트 분석 완료 (README.md, pyproject.toml, main.py, SPEC-AGENT-GROWTH-001~004)
- **AUTHOR**: @project-manager
- **UPDATES**: 핵심 미션, 사용자층, 문제 정의, 차별점, 성공 지표, Legacy Context 작성
- **PROJECT_TYPE**: Legacy Project (Greenfield → Production-Ready Phase)
- **CONTEXT**: DT-RAG v2.0.0 - Dynamic Taxonomy RAG System with Memento Integration

### v0.1.0 (2025-10-01)
- **INITIAL**: 프로젝트 제품 정의 문서 템플릿 생성
- **AUTHOR**: @project-owner

---

## @DOC:MISSION-001 핵심 미션

### 핵심 가치 제안

**DT-RAG는 동적 분류체계(Dynamic Taxonomy)와 사례 기반 추론(Case-Based Reasoning)을 결합하여, 기존 RAG 시스템의 "정적 지식 베이스" 한계를 극복한 차세대 지능형 문서 검색 시스템입니다.**

**핵심 차별점**:
1. **Dynamic Taxonomy**: 고정된 폴더 구조가 아닌, 계층적 DAG(Directed Acyclic Graph) 기반의 동적 분류체계로 문서를 체계화
2. **7-Step LangGraph Pipeline**: Meta-Planning → Retrieval → Tools → Debate → Compose → Cite → Response로 구성된 엔터프라이즈급 RAG 파이프라인
3. **Adaptive Retrieval**: Soft Q-learning Bandit 기반 강화학습으로 쿼리 복잡도에 따라 검색 전략 자동 선택 (BM25/Vector/Hybrid)
4. **Multi-Agent Debate**: 2-agent debate 구조 (Affirmative vs Critical)로 답변 품질 향상 및 Hallucination 감소
5. **Agent Growth Platform**: 게임화된 에이전트 성장 시스템으로 도메인 특화 지식 범위(Coverage)를 관리하고 확장

### 비즈니스 목표

- **정확도 (Faithfulness)**: RAGAS 평가 기준 ≥ 0.85 달성 (기존 0.72 → 목표 0.85+)
- **응답 속도 (Latency)**: p95 응답 시간 ≤ 4초 (하이브리드 검색 + 벡터 인덱스 최적화)
- **비용 효율 (Cost)**: 쿼리당 비용 ≤ ₩10 (pgvector로 OpenAI Embedding API 비용 절감)
- **Human-in-the-Loop**: HITL 개입률 ≤ 30% (신뢰도 기반 자동 분류로 전문가 개입 최소화)
- **롤백 복구 시간**: ≤ 15분 (자동화 스크립트 및 Alembic 마이그레이션 관리)

---

## @SPEC:USER-001 주요 사용자층

### 1차 사용자: 기업 지식 관리 담당자 (Knowledge Manager)

**프로필**:
- 대규모 문서 데이터베이스를 관리하는 기업 내부 담당자
- 의료, 법률, 금융, 연구 기관 등 전문 지식 기반 산업 종사자
- 수백~수천 개의 문서를 체계적으로 분류하고 검색 가능하게 만들어야 하는 니즈

**핵심 니즈**:
1. **자동 분류**: 수작업 대신 ML 기반 자동 분류로 문서 업로드 시간 단축 (1000건 → 50분 이내)
2. **계층적 체계**: 고정 폴더가 아닌 유연한 다중 상속 분류체계로 복잡한 도메인 지식 표현
3. **검색 정확도**: 키워드 검색 대신 의미 기반 검색 (Vector Similarity + BM25 Hybrid)
4. **품질 보증**: Confidence Threshold 기반 분류 + HITL로 품질 관리

**핵심 시나리오**:
- 시나리오 1: "암 치료 관련 최신 논문 500건을 업로드하고, 자동으로 '유방암', '폐암', '항암제' 카테고리에 분류"
- 시나리오 2: "사용자가 'HER2 양성 유방암 치료법은?'이라고 질문하면, 관련 논문 10개를 신뢰도 순으로 제공"
- 시나리오 3: "분류 신뢰도가 0.7 미만인 문서는 전문가 검토 대기열에 자동 추가"

### 2차 사용자: 도메인 전문가 (Domain Expert)

**프로필**:
- 의사, 변호사, 연구원 등 특정 분야의 깊은 전문 지식을 가진 사용자
- 자신의 전문 분야 문서를 빠르게 검색하고 참조해야 하는 니즈
- 일반 검색 엔진으로는 찾기 어려운 전문 용어 기반 검색 필요

**핵심 니즈**:
1. **도메인 특화 에이전트**: 자신의 전문 분야 (예: 유방암 치료) 에만 집중하는 AI 에이전트 생성
2. **높은 정확도**: Hallucination 없는 Citation 기반 답변 (Source Tracing)
3. **빠른 응답**: 복잡한 질문도 4초 이내 답변 (p95 latency)
4. **Context-Aware Search**: 단순 키워드가 아닌 맥락 이해 기반 검색

**핵심 시나리오**:
- 시나리오 1: "유방암 치료 전문 에이전트 생성 → 'HER2 양성 환자에게 Herceptin 병용 요법 효과는?' 질문 → 관련 논문 5개와 답변 생성"
- 시나리오 2: "Multi-Agent Debate 모드로 '항암제 A vs B 효능 비교' 질문 → 2-agent가 각자 답변 생성 후 상호 비평 → 최종 통합 답변"

### 3차 사용자: AI/ML 엔지니어 (System Operator)

**프로필**:
- DT-RAG 시스템을 운영하고 성능을 최적화하는 엔지니어
- LLM 품질 평가 (RAGAS), 검색 성능 모니터링, Feature Flag 관리

**핵심 니즈**:
1. **실험적 기능 관리**: Feature Flag로 Meta-Planner, Debate Mode, Soft Q-Bandit 등 실험 기능 on/off
2. **성능 모니터링**: 실시간 Latency, Token Usage, Faithfulness 추적
3. **A/B 테스트**: BM25 vs Vector vs Hybrid 검색 전략 비교 실험

**핵심 시나리오**:
- 시나리오 1: "Feature Flag FEATURE_DEBATE_MODE=true로 설정 → Debate 모드 활성화 → A/B 테스트로 답변 품질 비교"
- 시나리오 2: "Soft Q-learning Bandit으로 쿼리 복잡도별 최적 검색 전략 학습 → 성능 향상 확인"

---

## @SPEC:PROBLEM-001 해결하는 핵심 문제

### 우선순위 높음

1. **정적 지식 베이스의 확장성 한계**
   - **문제**: 기존 RAG는 고정된 폴더 구조나 단순 태그로 문서 관리 → 복잡한 도메인 지식 표현 불가능
   - **증상**: 1000개 이상 문서가 쌓이면 검색 정확도 급감, 관련 없는 문서 검색 빈번
   - **근본 원인**: 문서 간 관계를 표현할 수단이 없음 (예: "유방암"이 "암"의 하위 개념이라는 계층 관계 부재)
   - **해결 방법**: Dynamic Taxonomy DAG 구조로 계층적 다중 상속 분류체계 구축

2. **단일 검색 전략의 성능 한계**
   - **문제**: BM25(키워드 기반)만 사용하면 의미 검색 실패, Vector만 사용하면 정확한 키워드 매칭 실패
   - **증상**: 쿼리 복잡도에 따라 검색 정확도 편차 큼 (단순 쿼리 70%, 복잡 쿼리 50%)
   - **근본 원인**: 모든 쿼리에 동일한 검색 전략 적용
   - **해결 방법**: Adaptive Retrieval (Soft Q-learning Bandit)로 쿼리 복잡도에 따라 BM25/Vector/Hybrid 자동 선택

3. **LLM Hallucination 및 낮은 신뢰도**
   - **문제**: LLM이 검색 결과와 무관한 정보를 생성하거나 (Hallucination), 잘못된 답변 제공
   - **증상**: RAGAS Faithfulness Score ≤ 0.7 (목표 0.85 미달)
   - **근본 원인**: 단일 LLM만 사용하면 self-check 기능 부재
   - **해결 방법**: Multi-Agent Debate (Affirmative vs Critical) 구조로 상호 검증 및 품질 향상

### 우선순위 중간

4. **대규모 문서 분류 작업의 수작업 병목**
   - **문제**: 1000개 문서를 수작업으로 분류하면 수일~수주 소요
   - **해결 방법**: ML 기반 자동 분류 (Semantic Similarity + Confidence Threshold) + HITL

5. **도메인 전문가의 검색 효율 저하**
   - **문제**: 일반 검색 엔진은 전문 용어 이해 부족, 관련 없는 결과 과다 노출
   - **해결 방법**: Agent Growth Platform으로 도메인 특화 에이전트 생성 (Taxonomy Scope Filtering)

### 현재 실패 사례들

**기존 RAG 시스템의 한계**:
- **문제 1**: 고정된 벡터 DB만 사용 → 계층 관계 표현 불가능 → 검색 정확도 한계
- **문제 2**: 단일 Retrieval 전략 → 쿼리 유형별 최적화 불가능 → 평균 품질은 높지만 edge case 실패
- **문제 3**: LLM 단일 호출 → Hallucination 검증 수단 없음 → 신뢰도 낮음
- **문제 4**: Static Prompt → 쿼리 복잡도에 무관하게 동일한 프롬프트 사용 → 성능 편차

**DT-RAG의 해결책**:
- ✅ PostgreSQL + pgvector + Taxonomy DAG → 계층적 벡터 검색
- ✅ Soft Q-learning Bandit → 쿼리별 최적 전략 학습
- ✅ Multi-Agent Debate → 자가 검증 및 품질 향상
- ✅ LangGraph 7-Step Pipeline → Meta-Planning으로 쿼리 복잡도별 맞춤 실행 계획

---

## @DOC:STRATEGY-001 차별점 및 강점

### 경쟁 솔루션 대비 강점

1. **Dynamic Taxonomy DAG (계층적 분류체계)**
   - **발휘 시나리오**: 1000개 이상의 문서를 다층 카테고리로 관리해야 하는 엔터프라이즈 환경
   - **차별점**:
     - 일반 RAG: 단순 태그 또는 flat 벡터 DB → 계층 관계 표현 불가능
     - DT-RAG: DAG 구조로 "유방암 → 암 → 의료" 계층 표현 + versioning 지원
   - **기술적 근거**: NetworkX graph traversal로 descendant nodes 자동 추출 → Agent Coverage 계산 가능
   - **측정 가능한 효과**: 계층적 필터링으로 검색 정확도 15~20% 향상 (baseline 대비)

2. **Adaptive Retrieval with Soft Q-learning Bandit**
   - **발휘 시나리오**: 쿼리 복잡도가 다양한 환경 (단순 키워드 질문 ~ 복잡한 추론 질문 혼재)
   - **차별점**:
     - 일반 RAG: 모든 쿼리에 Hybrid Search 고정 사용 → 단순 쿼리에서는 오버헤드, 복잡 쿼리에서는 부족
     - DT-RAG: 쿼리 복잡도 (simple/medium/complex) 분석 → RL Policy로 BM25/Vector/Hybrid 중 최적 전략 선택
   - **기술적 근거**: Soft Bellman Equation 기반 Q-learning → exploration-exploitation balance
   - **측정 가능한 효과**: 평균 latency 20% 감소 + 정확도 유지 (단순 쿼리는 BM25 only로 속도 향상)

3. **Multi-Agent Debate for Quality Assurance**
   - **발휘 시나리오**: 의료, 법률 등 높은 신뢰도가 요구되는 도메인
   - **차별점**:
     - 일반 RAG: LLM 단일 호출 → Hallucination 검증 불가능
     - DT-RAG: 2-agent (Affirmative vs Critical) → 2-round debate → Synthesizer 통합
   - **기술적 근거**: Parallel LLM 호출 (Round 1/2 각 2회) + Mutual Critique → 자가 검증
   - **측정 가능한 효과**: RAGAS Faithfulness +0.13 향상 (0.72 → 0.85+)

4. **Agent Growth Platform (게임화된 지식 관리)**
   - **발휘 시나리오**: 도메인 전문가가 자신의 전문 분야 에이전트를 생성하고 관리하는 환경
   - **차별점**:
     - 일반 RAG: 모든 사용자가 동일한 전역 검색 사용 → 전문 분야 필터링 불가능
     - DT-RAG: Agent = Taxonomy Scope + Retrieval Config + Level/XP → 도메인 특화 + 성장 시스템
   - **기술적 근거**: CoverageMeterService로 에이전트의 지식 범위(Coverage) 계산 → Gap Detection → 자동 추천
   - **측정 가능한 효과**: 전문가 만족도 향상 + 검색 정확도 향상 (scope filtering)

5. **Production-Ready Infrastructure**
   - **발휘 시나리오**: 엔터프라이즈 환경에서 안정적으로 운영해야 하는 경우
   - **차별점**:
     - 일반 RAG: Mock 데이터 또는 In-Memory 벡터 DB → 프로덕션 배포 불가능
     - DT-RAG: PostgreSQL + pgvector + Redis + Background Task Worker → 완전한 프로덕션 인프라
   - **기술적 근거**:
     - Database: Alembic migration + JSONB 활용
     - Background: Redis Queue + AgentTaskWorker (systemd service 지원)
     - Monitoring: Sentry + Prometheus + Health Check
   - **측정 가능한 효과**: Rollback TTR ≤ 15분, 99.9% Uptime 가능

### 기술 스택 차별점

| 영역 | 일반 RAG | DT-RAG | 차별점 |
|------|----------|--------|--------|
| **Retrieval** | Vector DB only | BM25 + Vector + Adaptive | RL 기반 전략 선택 |
| **Taxonomy** | Flat tags | Hierarchical DAG | 계층적 다중 상속 |
| **Quality** | Single LLM | Multi-Agent Debate | 상호 검증 |
| **Scalability** | In-Memory | PostgreSQL + pgvector | 수백만 문서 지원 |
| **Observability** | 없음 | Sentry + Prometheus | 실시간 모니터링 |

---

## @SPEC:SUCCESS-001 성공 지표

### 즉시 측정 가능한 KPI

1. **Faithfulness (답변 정확도)**
   - **베이스라인**: RAGAS Faithfulness Score
   - **현재**: 0.72 (Multi-Agent Debate 미적용 시)
   - **목표**: ≥ 0.85 (Multi-Agent Debate 적용 후)
   - **측정 방법**: RAGAS 평가 API (`/api/v1/evaluation/ragas`) → `apps/evaluation/ragas_evaluator.py`
   - **측정 주기**: 주간 (100개 쿼리 샘플링)

2. **p95 Latency (응답 속도)**
   - **베이스라인**: 95% 백분위수 응답 시간
   - **현재**: 5.2초 (최적화 전)
   - **목표**: ≤ 4초 (하이브리드 검색 + 벡터 인덱스 최적화)
   - **측정 방법**: Prometheus `/api/v1/monitoring/search-analytics` → `latency_p95_ms`
   - **측정 주기**: 일간

3. **Cost per Query (쿼리당 비용)**
   - **베이스라인**: OpenAI API 호출 비용
   - **현재**: ₩15 (Embedding API + GPT-4 호출)
   - **목표**: ≤ ₩10 (pgvector로 Embedding API 호출 최소화)
   - **측정 방법**: LangFuse `/api/v1/monitoring/cost-analytics` → `cost_per_query_krw`
   - **측정 주기**: 월간

4. **HITL Rate (Human-in-the-Loop 개입률)**
   - **베이스라인**: 전문가 검토가 필요한 분류 비율
   - **현재**: 45% (Confidence < 0.7인 문서 비율)
   - **목표**: ≤ 30% (ML 모델 정확도 향상)
   - **측정 방법**: `doc_taxonomy` 테이블에서 `confidence < 0.7` 비율 계산
   - **측정 주기**: 주간

5. **Coverage Completeness (에이전트 지식 범위 완성도)**
   - **베이스라인**: Agent Coverage Percentage
   - **현재**: 평균 65% (신규 에이전트 생성 시)
   - **목표**: ≥ 80% (Gap Detection + 자동 문서 추천)
   - **측정 방법**: `agents.coverage_percent` 평균값
   - **측정 주기**: 주간

### 측정 주기

- **일간**: p95 Latency, Query Count, Error Rate
- **주간**: Faithfulness Score (RAGAS), HITL Rate, Coverage Percentage
- **월간**: Cost per Query, User Satisfaction Score, Rollback Count

---

## Legacy Context

### 기존 README.md 핵심 내용 보존

**프로젝트명**: Dynamic Taxonomy RAG v2.0.0 - Memento Integration Complete

**Phase 0-3.2 구현 히스토리**:
1. **Phase 0**: PostgreSQL + pgvector 데이터베이스 구축 (Mock 데이터 제거)
2. **Phase 1**: Meta-Planner 구현 (LLM 기반 쿼리 복잡도 분석)
3. **Phase 2A**: Neural Case Selector (Vector + BM25 하이브리드 검색)
4. **Phase 2B**: MCP Tools (Model Context Protocol 기반 도구 실행)
5. **Phase 3.1**: Soft Q-learning Bandit (RL 기반 적응형 검색 전략)
6. **Phase 3.2**: Multi-Agent Debate Mode (2-agent debate 구조)

**Memento Framework 통합 (2025-10-09)**:
- ✅ CaseBank 메타데이터 확장 (version, status, updated_by)
- ✅ ExecutionLog 테이블 및 ReflectionEngine (성능 분석)
- ✅ CaseBankArchive 테이블 및 ConsolidationPolicy (라이프사이클 관리)
- ✅ 3개 마이그레이션 적용 (002, 003, 004)
- ✅ 44개 테스트 통과 (unit: 14, integration: 13, e2e: 3)

**Agent Growth Platform (SPEC-AGENT-GROWTH-001~004)**:
- **Phase 0**: agents 테이블, CoverageMeterService, AgentDAO 구현
- **Phase 1**: REST API 6개 엔드포인트 구현 (POST /from-taxonomy, GET /{id}, GET /coverage, GET /gaps, POST /query)
- **Phase 2**: XP/Leveling 시스템 (게임화)
- **Phase 3**: Real Background Tasks (Redis Queue + AgentTaskWorker)

### 기존 Feature Flag 시스템

| Flag | 기본값 | 설명 | Phase | 상태 |
|------|--------|------|-------|------|
| `FEATURE_META_PLANNER` | false | 메타 레벨 계획 생성 | 1 | ✅ 완료 |
| `FEATURE_NEURAL_CASE_SELECTOR` | false | Vector 하이브리드 검색 | 2A | ✅ 완료 |
| `FEATURE_MCP_TOOLS` | false | MCP 도구 실행 | 2B | ✅ 완료 |
| `FEATURE_TOOLS_POLICY` | false | 도구 Whitelist 정책 | 2B | ✅ 완료 |
| `FEATURE_SOFT_Q_BANDIT` | false | RL 기반 정책 선택 | 3.1 | ✅ 완료 |
| `FEATURE_DEBATE_MODE` | false | Multi-Agent Debate | 3.2 | ✅ 완료 |
| `FEATURE_EXPERIENCE_REPLAY` | false | 경험 리플레이 버퍼 | 3+ | 🚧 예정 |

### 기존 7-Step LangGraph Pipeline

```
1. step1_intent: 의도 분류 (query → search/answer/classify)
2. step2_retrieve: 문서 검색 (BM25 + Vector)
3. step3_plan: 메타 계획 생성 (FEATURE_META_PLANNER)
4. step4_tools_debate: 도구 실행 / Debate (FEATURE_MCP_TOOLS, FEATURE_DEBATE_MODE)
5. step5_compose: 답변 생성
6. step6_cite: 인용 추가
7. step7_respond: 최종 응답
```

### 프로덕션 체크리스트 (기존 README.md)

- [x] PostgreSQL + pgvector 컨테이너 실행
- [x] 데이터베이스 스키마 초기화 완료
- [x] 문서 임베딩 생성 완료
- [x] 벡터 인덱스 최적화 완료
- [x] 전체 시스템 테스트 통과 (80% 이상)
- [x] API 문서화 확인 (Swagger UI /docs)
- [x] 모니터링 시스템 활성화 (Sentry, Prometheus)
- [ ] 백업 및 복구 계획 수립 (TODO)

---

## TODO:SPEC-BACKLOG-001 다음 단계 SPEC 후보

### 우선순위 높음 (1개월 이내)

1. **SPEC-AGENT-GROWTH-005**: Agent XP/Leveling System Phase 2
   - **목적**: 에이전트 성장 게임화 시스템 완성 (XP 계산, Level Up, Feature Unlocking)
   - **근거**: Phase 0-1 완료 후 사용자 engagement 향상 필요
   - **예상 공수**: 2주

2. **SPEC-MONITORING-001**: Real-time Observability Dashboard
   - **목적**: Grafana + Prometheus 통합 대시보드 구축
   - **근거**: 프로덕션 환경에서 실시간 성능 모니터링 필수
   - **예상 공수**: 1주

3. **SPEC-BACKUP-001**: Automated Backup & Recovery System
   - **목적**: PostgreSQL 자동 백업 + Point-in-Time Recovery
   - **근거**: 데이터 손실 방지 및 재해 복구 전략 수립
   - **예상 공수**: 1주

### 우선순위 중간 (2~3개월)

4. **SPEC-FRONTEND-001**: Agent Management UI (Next.js 14)
   - **목적**: 에이전트 생성, Coverage 시각화, Gap Detection UI
   - **근거**: 비개발자 사용자도 에이전트 관리 가능하도록 GUI 필요
   - **예상 공수**: 3주

5. **SPEC-BATCH-001**: Batch Document Processing Pipeline
   - **목적**: 대량 문서 업로드 시 Background Task로 처리 (현재 동기 처리)
   - **근거**: 1000개 이상 문서 업로드 시 타임아웃 방지
   - **예상 공수**: 2주

6. **SPEC-HITL-001**: Human-in-the-Loop Review Interface
   - **목적**: Confidence < 0.7 문서에 대한 전문가 검토 UI 및 Feedback Loop
   - **근거**: 분류 품질 향상 및 HITL Rate 목표 달성 (30% 이하)
   - **예상 공수**: 2주

### 우선순위 낮음 (4개월 이상)

7. **SPEC-MULTIMODAL-001**: Image & PDF OCR Integration
   - **목적**: 이미지 및 PDF 문서에서 텍스트 추출 및 벡터화
   - **근거**: 현재 Plain Text만 지원, 실무에서는 PDF 문서 다수
   - **예상 공수**: 3주

8. **SPEC-STREAMING-001**: Streaming Response for Long Queries
   - **목적**: SSE (Server-Sent Events) 기반 실시간 답변 스트리밍
   - **근거**: 복잡한 쿼리의 경우 응답 시간이 10초 이상 소요될 수 있음
   - **예상 공수**: 2주

---

## EARS 요구사항 작성 가이드

### EARS (Easy Approach to Requirements Syntax)

SPEC 작성 시 다음 EARS 구문을 활용하여 체계적인 요구사항을 작성하세요:

#### EARS 구문 형식
1. **Ubiquitous Requirements**: 시스템은 [기능]을 제공해야 한다
2. **Event-driven Requirements**: WHEN [조건]이면, 시스템은 [동작]해야 한다
3. **State-driven Requirements**: WHILE [상태]일 때, 시스템은 [동작]해야 한다
4. **Optional Features**: WHERE [조건]이면, 시스템은 [동작]할 수 있다
5. **Constraints**: IF [조건]이면, 시스템은 [제약]해야 한다

#### DT-RAG 적용 예시

```markdown
### Ubiquitous Requirements (핵심 기능)
- 시스템은 동적 분류체계 기반 문서 검색 기능을 제공해야 한다
- 시스템은 BM25 + Vector 하이브리드 검색을 지원해야 한다

### Event-driven Requirements (이벤트 기반)
- WHEN 사용자가 문서를 업로드하면, 시스템은 자동으로 ML 기반 분류를 수행해야 한다
- WHEN 분류 신뢰도가 0.7 미만이면, 시스템은 HITL 검토 대기열에 추가해야 한다

### State-driven Requirements (상태 기반)
- WHILE FEATURE_DEBATE_MODE가 활성화되어 있을 때, 시스템은 Multi-Agent Debate 모드로 답변을 생성해야 한다
- WHILE 에이전트의 Coverage가 50% 미만일 때, 시스템은 Gap Detection을 수행하고 문서 추천을 제공해야 한다

### Optional Features (선택적 기능)
- WHERE 사용자가 실시간 스트리밍을 요청하면, 시스템은 SSE 기반 답변 스트리밍을 제공할 수 있다
- WHERE Prometheus가 설정되어 있으면, 시스템은 실시간 메트릭을 수집할 수 있다

### Constraints (제약사항)
- IF 쿼리 응답 시간이 4초를 초과하면, 시스템은 타임아웃 경고를 발생시켜야 한다
- Coverage 계산은 2초 이내에 완료되어야 한다 (50 nodes, 10K documents 기준)
```

---

_이 문서는 `/alfred:1-spec` 실행 시 SPEC 생성의 기준이 됩니다._
