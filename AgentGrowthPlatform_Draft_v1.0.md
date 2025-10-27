# Agent Growth Platform - Draft v1.0

> **"게임 캐릭터처럼 성장하는 전문가 에이전트"**
>
> 지식 획득 (대화형 + 수동) → Taxonomy 통합 → 에이전트 생성 → 경험 축적 → 레벨업

---

## 📝 원본 의도 (사용자 메모)

```
이게 지금 우리 기존 prd에 taxonomy 라는 개념이 있잖아.

지식 데이터를 카테고리형 트리로 생성해서 선택한 트리 범위 내에서
지식 검색하고 답변한다는.

이 기능하고 저걸 결합하는게 목표가 될거 같아
그럼 대화형 지식 인입 + 내가 넣은 문서

이 두가지 형태의 rag가 모두 통합 카테고리 트리로 나타나고
거기서 범위 지정해서 에이전트 생성 되는 방식.

만약에 생성된 에이전트가 메멘토 기능에 의해 피드백 학습이 되기까지 한다면

진짜 게임 상태창 처럼
지식과 경험치를 표시해서
레벨업 개념을 넣어주기까지 하면 좋겠다
```

---

## 🎯 시스템 정의

### One-liner
**"지식을 먹고 자라는 전문가 에이전트 육성 플랫폼"**

### 핵심 가치
1. **지식 획득의 이중화**: 자동 수집 + 수동 업로드
2. **Taxonomy 기반 범위 지정**: 카테고리 트리에서 전문성 선택
3. **게이미피케이션**: XP/레벨/능력 해금으로 성장 가시화

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│  1. Knowledge Acquisition Layer (지식 획득)             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Option A: 대화형 인입 (Knowledge Builder)              │
│  ┌─────────────────────────────────────────────────┐   │
│  │ "암 치료 전문가 만들어줘"                        │   │
│  │       ↓                                          │   │
│  │ Research Planner (소스 자동 매핑)                │   │
│  │       ↓                                          │   │
│  │ Source Connectors (크롤러/API)                   │   │
│  │       ↓                                          │   │
│  │ Policy Engine (라이선스 필터링)                  │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Option B: 수동 업로드 (기존 Ingestion)                 │
│  ┌─────────────────────────────────────────────────┐   │
│  │ PDF/DOCX/CSV/TXT 파일 업로드                     │   │
│  │       ↓                                          │   │
│  │ Parsers (파일 형식별 파싱)                       │   │
│  │       ↓                                          │   │
│  │ Intelligent Chunker (청킹)                       │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ▼ 두 소스 모두 동일하게 처리 ▼                         │
│                                                         │
│  Embedding Generation → Hybrid Search Indexing          │
│  (OpenAI 1536d)        (BM25 + pgvector)                │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  2. Taxonomy Integration Layer (분류 통합)              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  모든 문서 → Taxonomy Tree 자동 매핑                     │
│  (Classification: Hybrid Rule-based + Semantic)         │
│                                                         │
│  Taxonomy Tree (예시):                                  │
│  ├─ 의학 (Medical) [250 docs]                          │
│  │   ├─ 암 치료 (Cancer Treatment) [120 docs]         │
│  │   │   ├─ 유방암 (Breast Cancer) [45 docs] ◄─ 선택  │
│  │   │   ├─ 폐암 (Lung Cancer) [30 docs]              │
│  │   │   └─ 대장암 (Colon Cancer) [25 docs]           │
│  │   └─ 당뇨 (Diabetes) [80 docs]                     │
│  │                                                     │
│  └─ 금융 (Finance) [300 docs]                          │
│      └─ 암호화폐 (Cryptocurrency) [200 docs]           │
│          ├─ BTC 투자 (BTC Trading) [120 docs]         │
│          └─ DeFi [80 docs]                             │
│                                                         │
│  Coverage Meter (커버리지 시각화):                      │
│  - 병기별: I (100%), II (90%), III (60%)               │
│  - 치료 라인: 1차 (100%), 2차 (70%), 3차 (40%)         │
│  - 총 커버리지: 80%                                    │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  3. Agent Creation Layer (에이전트 생성)                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  사용자 액션: Taxonomy 노드 선택                         │
│  └─> "의학 > 암 치료 > 유방암" 선택                     │
│                                                         │
│  시스템 액션: 전문 에이전트 생성                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ [에이전트: 유방암 치료 전문가]                   │   │
│  │                                                  │   │
│  │ 초기 스탯:                                       │   │
│  │ - Level: 1                                       │   │
│  │ - XP: 0 / 100                                    │   │
│  │ - Knowledge: 45 documents                        │   │
│  │ - Coverage: 80%                                  │   │
│  │ - Capabilities: [기본 검색]                      │   │
│  │                                                  │   │
│  │ Retrieval Config:                                │   │
│  │ - Scope: taxonomy_node_id = "breast_cancer"      │   │
│  │ - Strategy: hybrid (BM25 + Vector)               │   │
│  │ - Top-k: 5                                       │   │
│  │                                                  │   │
│  │ Feature Flags:                                   │   │
│  │ - FEATURE_DEBATE_MODE: false (Lv 2에 해금)      │   │
│  │ - FEATURE_NEURAL_CASE_SELECTOR: false (Lv 3)    │   │
│  │ - FEATURE_SOFT_Q_BANDIT: false (Lv 4)           │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  4. Query & Growth Layer (쿼리 및 성장)                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  사용자 쿼리: "HER2+ 유방암 1차 치료는?"                 │
│       ↓                                                 │
│  LangGraph 7-Step Pipeline 실행                          │
│  ├─ step1_intent: 의도 분류                             │
│  ├─ step2_retrieve: Taxonomy 범위 내 검색 (45 docs만)  │
│  ├─ step3_plan: 메타 계획                              │
│  ├─ step4_tools_debate: 도구/토론 (Lv 2+)              │
│  ├─ step5_compose: 답변 생성                           │
│  ├─ step6_cite: 인용 추가 (Evidence Receipt)           │
│  └─ step7_respond: 최종 응답                           │
│       ↓                                                 │
│  답변 반환 + 출처 카드                                   │
│       ↓                                                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Memento Framework (자가 학습)                    │  │
│  ├──────────────────────────────────────────────────┤  │
│  │ 1. ExecutionLog 저장                             │  │
│  │    - query, answer, latency, tokens, success     │  │
│  │    - faithfulness, context_relevance             │  │
│  │                                                  │  │
│  │ 2. ReflectionEngine 분석                         │  │
│  │    - 병목 단계 탐지 (p95 > 2s)                   │  │
│  │    - LLM 개선 제안                               │  │
│  │                                                  │  │
│  │ 3. CaseBank 업데이트                             │  │
│  │    - 좋은 답변 사례 저장 (faithfulness > 0.9)    │  │
│  │    - query_vector 임베딩 생성                    │  │
│  │                                                  │  │
│  │ 4. XP 계산 및 부여                               │  │
│  │    xp_gain = base_xp(10)                         │  │
│  │              × quality_multiplier(1.0~2.0)       │  │
│  │              × difficulty_bonus(0.5~1.5)         │  │
│  │                                                  │  │
│  │    예시:                                         │  │
│  │    - 기본 쿼리 (faithfulness 0.8): +10 XP        │  │
│  │    - 우수 답변 (faithfulness 0.95): +20 XP       │  │
│  │    - 복잡한 쿼리 (multi-step): +30 XP            │  │
│  │                                                  │  │
│  │ 5. 레벨업 체크                                   │  │
│  │    if agent.xp >= next_level_xp:                 │  │
│  │        agent.level_up()                          │  │
│  │        unlock_features(agent.level)              │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 🎮 레벨 시스템 설계

### 레벨업 곡선

| 레벨 | 필요 XP (누적) | 필요 쿼리 (대략) | 해금 기능 |
|------|----------------|------------------|-----------|
| **Lv 1** | 0 | 0 | 기본 검색 (BM25 + Vector) |
| **Lv 2** | 100 | ~10 queries | 🔓 Debate Mode (Multi-Agent 토론) |
| **Lv 3** | 400 | ~30 queries | 🔓 Neural Case Selector (과거 경험 활용) |
| **Lv 4** | 900 | ~60 queries | 🔓 Soft Q-learning Bandit (적응형 전략) |
| **Lv 5** | 1600 | ~100 queries | 🔓 Meta Planner (고급 계획) |
| **Lv MAX** | 2500 | ~150 queries | 🏆 Expert Mode (모든 기능 최적화) |

### XP 획득 공식

```python
def calculate_xp(query_result):
    base_xp = 10

    # 품질 배수 (faithfulness 기반)
    quality_multiplier = 1.0 + (query_result.faithfulness - 0.8) * 2.0
    # 0.8 faithfulness = 1.0x, 0.9 = 1.2x, 1.0 = 1.4x

    # 난이도 보너스 (쿼리 복잡도)
    difficulty_bonus = {
        'simple': 1.0,   # 단순 검색
        'medium': 1.3,   # 다단계 추론
        'complex': 1.5   # 복잡한 계획 필요
    }[query_result.complexity]

    # 추가 보너스
    bonus = 0
    if query_result.debate_used:
        bonus += 5  # Debate 사용
    if query_result.tools_used:
        bonus += 3  # 도구 사용

    total_xp = int(base_xp * quality_multiplier * difficulty_bonus + bonus)
    return total_xp

# 예시:
# - 간단한 쿼리, faithfulness 0.85: 10 × 1.1 × 1.0 = 11 XP
# - 복잡한 쿼리, faithfulness 0.95, Debate: 10 × 1.3 × 1.5 + 5 = 24 XP
```

### 레벨별 능력 변화

#### Lv 1: 초보자
- 기본 하이브리드 검색 (BM25 + Vector)
- Top-k: 5
- 단순 답변 생성

#### Lv 2: 신중한 전문가
- 🔓 **Debate Mode**: Affirmative vs Critical 2-agent 토론
- Top-k: 7
- 답변 품질 +15%

#### Lv 3: 경험 기반 전문가
- 🔓 **Neural Case Selector**: CaseBank에서 유사 과거 사례 검색
- Top-k: 10
- 답변 속도 +20% (캐시 활용)

#### Lv 4: 적응형 전문가
- 🔓 **Soft Q-learning Bandit**: 쿼리 유형별 최적 전략 자동 선택
- Dynamic Top-k (3~15)
- 답변 정확도 +10%

#### Lv 5: 마스터
- 🔓 **Meta Planner**: LLM 기반 고급 쿼리 계획
- 모든 Feature Flags 활성화
- 최고 성능

---

## 📊 에이전트 상태창 (UI Mock)

```
┌─────────────────────────────────────────────────────────┐
│  [에이전트: 유방암 치료 전문가 Lv 3] ⭐⭐⭐              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  📚 지식 (Knowledge Base)                               │
│  ├─ 총 문서: 45개                                       │
│  │   ├─ 자동 수집: 30개 (Knowledge Builder)            │
│  │   └─ 수동 업로드: 15개 (사용자 제공)                │
│  ├─ 청크: 450개                                         │
│  ├─ 임베딩: 1536d (OpenAI text-embedding-3-small)      │
│  └─ 마지막 업데이트: 2시간 전                           │
│                                                         │
│  📊 커버리지 (Coverage)                                 │
│  ├─ 전체: ████████░░ 80%                                │
│  ├─ 병기별:                                             │
│  │   ├─ Stage I: ██████████ 100%                       │
│  │   ├─ Stage II: █████████░ 90%                       │
│  │   ├─ Stage III: ██████░░░░ 60%                      │
│  │   └─ Stage IV: ███░░░░░░░ 30% ⚠️ 보강 추천          │
│  └─ 치료 라인별:                                        │
│      ├─ 1차 치료: ██████████ 100%                       │
│      ├─ 2차 치료: ███████░░░ 70%                        │
│      └─ 3차 치료: ████░░░░░░ 40% ⚠️ 보강 추천           │
│                                                         │
│  ⚡ 경험 (Experience)                                   │
│  ├─ 레벨: 3 ⭐⭐⭐                                        │
│  ├─ XP: 450 / 900 ████████████░░░░░░░░░░ 50%           │
│  │   └─ 다음 레벨까지: 450 XP (약 30 쿼리)             │
│  ├─ 총 쿼리 수: 45회                                    │
│  ├─ 성공률: 94% (42/45) ✅                              │
│  ├─ 평균 Faithfulness: 0.91 🎯                          │
│  └─ 평균 응답 시간: 1.8초 ⚡                            │
│                                                         │
│  🎯 능력 (Capabilities)                                 │
│  ├─ [Lv 1] 기본 검색 (Hybrid BM25+Vector) ✅            │
│  ├─ [Lv 2] Debate Mode (Multi-Agent) ✅ 해금됨!         │
│  ├─ [Lv 3] Neural Case Selector ✅ 해금됨!              │
│  ├─ [Lv 4] Soft Q-learning Bandit 🔒 (450 XP 필요)     │
│  └─ [Lv 5] Meta Planner 🔒 (1150 XP 필요)              │
│                                                         │
│  📈 성장 기록 (Growth History)                          │
│  ├─ 2025-10-10 12:00: 에이전트 생성 (Lv 1)             │
│  ├─ 2025-10-10 14:30: Lv 1 → 2 (100 XP 달성)          │
│  │   └─ 🎉 Debate Mode 해금!                           │
│  ├─ 2025-10-11 09:15: Lv 2 → 3 (400 XP 달성)          │
│  │   └─ 🎉 Neural Case Selector 해금!                  │
│  └─ 다음 목표: Lv 4 (Soft Q-learning, 적응형 전략)     │
│                                                         │
│  🏆 업적 (Achievements)                                 │
│  ├─ ✅ 첫 걸음: 첫 쿼리 완료                            │
│  ├─ ✅ 열정 가득: 10 쿼리 달성                          │
│  ├─ ✅ 전문가의 길: Faithfulness 0.9 이상 10회          │
│  ├─ ⬜ 완벽주의자: Faithfulness 1.0 달성 (0/1)          │
│  └─ ⬜ 마라토너: 100 쿼리 달성 (45/100)                 │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  액션 버튼                                               │
├─────────────────────────────────────────────────────────┤
│  [지식 추가 +]  [에이전트 훈련]  [성능 분석]  [레벨업 미리보기]  │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 데이터베이스 스키마 확장

### 1. agents 테이블 (신규)

```sql
CREATE TABLE agents (
    agent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,

    -- Taxonomy 범위
    taxonomy_node_ids TEXT[] NOT NULL,  -- 선택한 Taxonomy 노드 ID 배열
    scope_description TEXT,             -- "유방암 치료 전문가"

    -- 지식 통계
    total_documents INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 0,
    coverage_percent FLOAT DEFAULT 0.0,

    -- 레벨 시스템
    level INTEGER DEFAULT 1,
    current_xp INTEGER DEFAULT 0,
    total_queries INTEGER DEFAULT 0,
    successful_queries INTEGER DEFAULT 0,

    -- 성능 지표
    avg_faithfulness FLOAT DEFAULT 0.0,
    avg_response_time_ms FLOAT DEFAULT 0.0,

    -- Config
    retrieval_config JSONB,  -- RetrievalConfig 저장
    features_config JSONB,   -- FeaturesConfig 저장 (레벨별 활성화)

    -- 메타
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_query_at TIMESTAMP,

    CONSTRAINT valid_level CHECK (level >= 1 AND level <= 5),
    CONSTRAINT valid_xp CHECK (current_xp >= 0)
);

CREATE INDEX idx_agents_taxonomy ON agents USING GIN (taxonomy_node_ids);
CREATE INDEX idx_agents_level ON agents (level);
```

### 2. agent_queries 테이블 (신규)

```sql
CREATE TABLE agent_queries (
    query_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(agent_id) ON DELETE CASCADE,

    -- 쿼리 정보
    query_text TEXT NOT NULL,
    answer_text TEXT,

    -- 성능 지표
    faithfulness FLOAT,
    context_relevance FLOAT,
    answer_relevance FLOAT,
    latency_ms INTEGER,
    tokens_used INTEGER,

    -- 복잡도 및 전략
    complexity TEXT CHECK (complexity IN ('simple', 'medium', 'complex')),
    retrieval_strategy TEXT,  -- 'bm25_only', 'vector_only', 'hybrid'
    compose_strategy TEXT,    -- 'direct', 'debate'

    -- XP
    xp_gained INTEGER DEFAULT 0,

    -- 성공 여부
    success BOOLEAN DEFAULT true,
    error_message TEXT,

    -- 메타
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_xp_gain CHECK (xp_gained >= 0)
);

CREATE INDEX idx_agent_queries_agent ON agent_queries (agent_id);
CREATE INDEX idx_agent_queries_created ON agent_queries (created_at DESC);
```

### 3. agent_level_history 테이블 (신규)

```sql
CREATE TABLE agent_level_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(agent_id) ON DELETE CASCADE,

    previous_level INTEGER NOT NULL,
    new_level INTEGER NOT NULL,
    xp_at_level_up INTEGER NOT NULL,

    unlocked_features TEXT[],  -- ['FEATURE_DEBATE_MODE']

    leveled_up_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_level_transition CHECK (new_level = previous_level + 1)
);

CREATE INDEX idx_agent_level_history_agent ON agent_level_history (agent_id);
```

### 4. agent_knowledge_sources 테이블 (신규)

```sql
CREATE TABLE agent_knowledge_sources (
    source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(agent_id) ON DELETE CASCADE,

    -- 지식 소스 타입
    source_type TEXT NOT NULL CHECK (source_type IN ('autonomous', 'manual')),
    -- 'autonomous': Knowledge Builder 자동 수집
    -- 'manual': 사용자 직접 업로드

    -- 문서 참조
    document_ids INTEGER[],  -- documents 테이블 ID 배열

    -- 메타
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT  -- "NCCN Guidelines 자동 수집" 또는 "사용자 업로드 PDF"
);

CREATE INDEX idx_agent_knowledge_agent ON agent_knowledge_sources (agent_id);
```

### 5. documents 테이블 확장 (기존 테이블 수정)

```sql
-- 기존 documents 테이블에 컬럼 추가
ALTER TABLE documents
    ADD COLUMN collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN source_version TEXT,           -- "NCCN 2025.1"
    ADD COLUMN evidence_level TEXT,           -- "guideline", "review", "primary"
    ADD COLUMN license TEXT DEFAULT 'OA',     -- "OA", "Licensed", "Internal"
    ADD COLUMN display_rule TEXT DEFAULT 'quote';  -- "quote", "summary", "link_only"

CREATE INDEX idx_documents_collected_at ON documents (collected_at DESC);
CREATE INDEX idx_documents_evidence_level ON documents (evidence_level);
```

---

## 🚀 구현 로드맵

### Phase 0: Core Foundation (3주)

#### Week 1: Agent Growth System
- [ ] agents 테이블 생성 및 마이그레이션
- [ ] agent_queries 테이블 생성
- [ ] agent_level_history 테이블 생성
- [ ] AgentGrowthService 구현
  - `create_agent(taxonomy_node_ids, name)`
  - `gain_xp(agent_id, xp_amount)`
  - `check_level_up(agent_id)`
  - `unlock_features(agent_id, level)`
- [ ] XP 계산 로직 구현
- [ ] 레벨업 로직 구현

#### Week 2: Taxonomy-based Agent Scope
- [ ] Taxonomy 범위 기반 검색 필터링
  - `search_within_taxonomy(query, taxonomy_node_ids)`
- [ ] Coverage Meter 구현
  - `calculate_coverage(agent_id)`
  - 병기별/치료 라인별 커버리지 계산
- [ ] agent_knowledge_sources 테이블 통합
- [ ] 기존 Agent Factory Router 확장
  - `POST /agents/from-taxonomy` → 레벨 시스템 통합

#### Week 3: UI - Agent Status Dashboard
- [ ] 에이전트 상태창 UI (apps/frontend)
  - 지식/경험/능력/성장 기록 표시
  - Progress bars, 레벨 아이콘
- [ ] 커버리지 시각화 (Recharts)
  - 히트맵 또는 트리맵
- [ ] 레벨업 알림 (Toast notification)
- [ ] "지식 추가" 버튼 → Knowledge Builder로 연결

### Phase 1: Knowledge Builder Integration (4주)

#### Week 4-5: Knowledge Builder Core
- [ ] Ingestion Wizard UI (5단계 폼)
- [ ] Research Planner v0 (룰 기반 템플릿)
- [ ] Source Connectors (URL 크롤러)
- [ ] agent_knowledge_sources 자동 생성
  - `source_type = 'autonomous'`

#### Week 6-7: Dual Source Integration
- [ ] 기존 Ingestion Pipeline 확장
  - agent_knowledge_sources 자동 생성
  - `source_type = 'manual'`
- [ ] Taxonomy 자동 매핑 강화
  - 자동 수집 문서도 분류
- [ ] Coverage Auto-Fill
  - 공백 탐지 → 자동 보강 추천
- [ ] Policy Engine (OA 소스만)

### Phase 2: Advanced Features (3주)

#### Week 8-9: Memento Integration
- [ ] ExecutionLog → agent_queries 통합
- [ ] ReflectionEngine → XP 계산 연동
- [ ] CaseBank → Neural Case Selector (Lv 3)
- [ ] 자동 레벨업 체크 (매 쿼리마다)

#### Week 10: Polish & Launch
- [ ] 업적 시스템 (Achievements)
- [ ] Agent Recipe 템플릿 (5종)
- [ ] 성능 최적화
- [ ] E2E 테스트
- [ ] 문서화

---

## 📊 성공 지표 (KPI)

### 사용자 참여도
- **에이전트 생성률**: 신규 사용자의 70%가 첫 에이전트 생성
- **레벨 2 도달률**: 생성된 에이전트의 60%가 Lv 2 달성
- **일일 쿼리**: 에이전트당 평균 3 쿼리/일

### 지식 품질
- **커버리지 목표**: 에이전트 생성 시 평균 70% 이상
- **자동 vs 수동 비율**: 자동 수집 60% / 수동 업로드 40%
- **업데이트 빈도**: 자동 수집 소스 < 24h 지연

### 성능 지표
- **Faithfulness**: Lv 3 이상 에이전트 평균 ≥ 0.90
- **응답 시간**: p95 ≤ 3s (Lv 4 에이전트)
- **레벨업 시간**: Lv 1 → Lv 2 평균 2일 이내

### 게이미피케이션 효과
- **세션 길이**: 레벨 시스템 도입 후 +40%
- **재방문율**: 7일 재방문율 +25%
- **쿼리당 만족도**: 레벨 표시 후 +15%

---

## 🎯 핵심 차별화 포인트 (vs AgentFactory_Plan_v1.0)

| 측면 | AgentFactory Plan | Agent Growth Platform |
|------|-------------------|----------------------|
| **지식 소스** | 대화형 인입 (자동 수집만) | 대화형 + 수동 업로드 (이중화) |
| **에이전트 범위** | 명시 안 됨 | Taxonomy 기반 명확한 범위 선택 |
| **성장 메커니즘** | 없음 | 레벨/XP/능력 해금 (게이미피케이션) |
| **사용자 경험** | 도구 중심 (TTV 2시간) | 육성 게임 (지속적 참여) |
| **Memento 통합** | Shadow Mode (비교만) | 경험치 시스템 (성장 가시화) |

---

## 🔮 향후 확장 가능성

### V2: Social Features
- **에이전트 공유**: 다른 사용자에게 에이전트 템플릿 공유
- **리더보드**: Lv 5 에이전트 수, 평균 Faithfulness 순위
- **협업 지식**: 여러 사용자가 같은 Taxonomy 노드에 지식 기여

### V3: Advanced Gamification
- **스킬 트리**: 레벨업 시 능력 선택 (Debate vs Case Selector 중 선택)
- **장비 시스템**: LLM 모델 선택 (GPT-4 = 레전더리 장비)
- **퀘스트**: "Stage IV 커버리지 80% 달성 시 보상"

### V4: Multi-Agent Collaboration
- **에이전트 파티**: 여러 전문가 에이전트 협업 (의학 + 통계)
- **멘토 시스템**: 고레벨 에이전트가 저레벨 에이전트 학습 지원

---

## 📝 다음 단계

### SPEC 작성 (3개 필요)

1. **SPEC-AGENT-GROWTH-001: Agent Leveling System**
   - agents 테이블 설계
   - XP 계산 로직
   - 레벨업 로직
   - Feature Flag 해금

2. **SPEC-TAXONOMY-SCOPE-001: Taxonomy-based Agent Scope**
   - Taxonomy 범위 선택
   - Coverage Meter 구현
   - 범위 기반 검색 필터링

3. **SPEC-KB-INTEGRATION-001: Knowledge Builder Integration**
   - 대화형 인입 + 수동 업로드 통합
   - agent_knowledge_sources 관리
   - 자동 Taxonomy 매핑

### 즉시 시작 가능한 작업
- [ ] agents 테이블 스키마 확정 및 마이그레이션 스크립트 작성
- [ ] XP 계산 로직 프로토타입 (Python 함수)
- [ ] UI Mock-up 디자인 (Figma 또는 손그림)
- [ ] 기존 Taxonomy 시스템 상세 분석 (taxonomy_dag.py 읽기)

---

**최종 목표**: "지식을 먹고 자라는, 게임처럼 재미있는 전문가 에이전트 육성 플랫폼"
