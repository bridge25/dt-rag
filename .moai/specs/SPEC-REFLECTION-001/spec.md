---
id: REFLECTION-001
version: 0.1.0
status: draft
created: 2025-10-09
updated: 2025-10-09
author: @claude
priority: high
category: feature
labels:
  - reflection
  - meta-learning
  - self-improvement
  - phase-3
depends_on:
  - CASEBANK-002
  - NEURAL-001
blocks: []
related_specs:
  - CONSOLIDATION-001
  - EVAL-001
scope:
  packages:
    - apps/orchestration
  files:
    - apps/orchestration/src/reflection_engine.py
  tests:
    - tests/unit/test_reflection_engine.py
---

# @SPEC:REFLECTION-001: Reflection Engine 구현 - 자기 성찰 및 개선

@SPEC:REFLECTION-001 @VERSION:0.1.0 @STATUS:draft

## HISTORY

### v0.1.0 (2025-10-09)
- **INITIAL**: Reflection Engine SPEC 최초 작성
- **AUTHOR**: @claude
- **SCOPE**: 케이스 실행 결과 분석, 성공/실패 패턴 학습, 자동 개선 제안
- **CONTEXT**: PRD 1.5P Phase 3 - Reflection 및 Self-Improvement
- **BASELINE**: CASEBANK-002 완료 (메타데이터 필드), NEURAL-001 완료 (검색 기능)

---

## 1. 개요

### 목적
Reflection Engine은 시스템의 실행 결과를 분석하고, 성공/실패 패턴을 학습하여 케이스 선택 및 실행 전략을 자동으로 개선합니다. 메타 학습(Meta-Learning)을 통해 시스템이 자기 성찰(Self-Reflection) 능력을 갖추도록 합니다.

### 범위
- **실행 결과 추적**: 케이스 적용 결과 (성공/실패, 실행 시간, 오류 타입) 기록
- **패턴 분석**: 성공/실패 케이스의 공통 패턴 도출
- **메트릭 계산**: 케이스별 success_rate, confidence_score 계산
- **개선 제안**: 저성능 케이스 개선 또는 제거 추천

---

## 2. Environment (환경)

### 기술 스택
- **Database**: PostgreSQL (CaseBank 메타데이터 활용)
- **분석 엔진**: Python (pandas, numpy)
- **LLM**: OpenAI GPT-4 (패턴 분석 및 개선 제안)
- **비동기 처리**: asyncio, background tasks

### 기존 구현 상태
- **CaseBank 메타데이터** (CASEBANK-002):
  - usage_count, success_rate, last_accessed_at
- **Neural 검색** (NEURAL-001):
  - Vector 유사도 기반 케이스 검색
- **Meta-Planner** (PLANNER-001):
  - 케이스 선택 및 실행 로직

### 제약사항
- 실행 결과 추적은 Meta-Planner와 통합 필요
- Reflection 수행 시 LLM 호출 비용 발생
- 실시간 반영보다는 주기적(배치) 분석 권장

---

## 3. Assumptions (가정)

### 데이터 가정
1. 케이스 실행 결과가 구조화된 로그로 저장됨
2. 성공/실패 기준이 명확히 정의됨 (예: 도구 실행 성공 여부)
3. 최소 100회 이상의 실행 로그가 있어야 패턴 분석 유의미

### 아키텍처 가정
1. Reflection Engine은 독립적인 서비스로 동작
2. 메타데이터 업데이트는 비동기로 처리
3. LLM 기반 분석은 일일 1회 배치 실행

---

## 4. Requirements (요구사항)

### Ubiquitous Requirements

**@REQ:REFLECTION-001.1** Execution Result Tracking
- 시스템은 모든 케이스 실행 결과를 ExecutionLog 테이블에 기록해야 한다
- 로그는 case_id, success, error_type, execution_time, timestamp를 포함해야 한다

**@REQ:REFLECTION-001.2** Success Rate Calculation
- 시스템은 각 케이스의 성공률을 계산해야 한다
- success_rate = (성공 횟수 / 총 실행 횟수) × 100
- 계산 결과는 CaseBank.success_rate 필드에 저장되어야 한다

**@REQ:REFLECTION-001.3** Pattern Analysis
- 시스템은 성공/실패 케이스의 공통 패턴을 분석해야 한다
- 패턴 분석 결과는 JSON 형식으로 저장되어야 한다

### Event-driven Requirements

**@REQ:REFLECTION-001.4** WHEN Case Execution Completes
- WHEN 케이스 실행이 완료되면, 시스템은 ExecutionLog를 생성해야 한다
- WHEN 실행 로그가 100건 이상 누적되면, 시스템은 Reflection 분석을 트리거해야 한다

**@REQ:REFLECTION-001.5** WHEN Reflection Analysis
- WHEN Reflection 분석이 실행되면, 시스템은 성공률을 재계산해야 한다
- WHEN 저성능 케이스가 발견되면, 시스템은 개선 제안을 생성해야 한다

**@REQ:REFLECTION-001.6** WHEN Improvement Suggestion
- WHEN 개선 제안이 생성되면, 시스템은 관리자에게 알림을 보내야 한다
- WHEN 사용자가 제안을 승인하면, 시스템은 케이스를 수정 또는 archived 상태로 변경해야 한다

### State-driven Requirements

**@REQ:REFLECTION-001.7** WHILE Reflection Active
- WHILE Reflection 분석 중, 시스템은 진행 상태를 로그에 기록해야 한다
- WHILE 분석 중, 새로운 실행 로그는 계속 수집되어야 한다

**@REQ:REFLECTION-001.8** WHILE Low Success Rate
- WHILE 케이스의 success_rate < 50%일 때, 시스템은 경고 플래그를 설정해야 한다
- WHILE 경고 플래그가 활성화된 상태일 때, 해당 케이스는 선택 우선순위가 낮아져야 한다

### Constraints

**@REQ:REFLECTION-001.9** Performance Constraint
- Reflection 분석은 시스템 성능에 영향을 주지 않아야 한다 (백그라운드 실행)
- LLM 호출은 분당 최대 5회로 제한되어야 한다

**@REQ:REFLECTION-001.10** Data Retention
- 실행 로그는 최소 30일간 보관되어야 한다
- 오래된 로그는 자동으로 아카이빙되어야 한다

---

## 5. Specifications (상세 구현 명세)

### IMPL 0.1: ExecutionLog Schema

**@IMPL:REFLECTION-001.0.1** ExecutionLog Table
```sql
CREATE TABLE IF NOT EXISTS execution_log (
    log_id SERIAL PRIMARY KEY,
    case_id VARCHAR(255) NOT NULL,
    success BOOLEAN NOT NULL,
    error_type VARCHAR(100),
    error_message TEXT,
    execution_time_ms INTEGER,
    context JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES case_bank(case_id)
);

CREATE INDEX idx_execution_log_case_id ON execution_log(case_id);
CREATE INDEX idx_execution_log_created_at ON execution_log(created_at DESC);
CREATE INDEX idx_execution_log_success ON execution_log(success);
```

**@IMPL:REFLECTION-001.0.2** SQLAlchemy Model
```python
class ExecutionLog(Base):
    __tablename__ = "execution_log"

    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(255), ForeignKey("case_bank.case_id"), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_type: Mapped[str] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    context: Mapped[dict] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    case = relationship("CaseBank", back_populates="execution_logs")
```

### IMPL 0.2: Reflection Engine Core

**@IMPL:REFLECTION-001.0.2.1** Reflection Engine Class
```python
class ReflectionEngine:
    def __init__(self, db_session: AsyncSession, llm_client: OpenAI):
        self.db = db_session
        self.llm = llm_client

    async def analyze_case_performance(self, case_id: str) -> Dict[str, Any]:
        """케이스 성능 분석"""
        logs = await self.get_execution_logs(case_id, limit=100)

        total_executions = len(logs)
        successful_executions = sum(1 for log in logs if log.success)
        success_rate = (successful_executions / total_executions) * 100 if total_executions > 0 else 0.0

        # 오류 패턴 분석
        error_types = [log.error_type for log in logs if not log.success and log.error_type]
        common_errors = self._analyze_error_patterns(error_types)

        # 실행 시간 분석
        execution_times = [log.execution_time_ms for log in logs if log.execution_time_ms]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0

        return {
            "case_id": case_id,
            "total_executions": total_executions,
            "success_rate": success_rate,
            "common_errors": common_errors,
            "avg_execution_time_ms": avg_execution_time
        }

    async def generate_improvement_suggestions(self, case_id: str) -> List[str]:
        """LLM 기반 개선 제안 생성"""
        performance = await self.analyze_case_performance(case_id)

        if performance["success_rate"] >= 80:
            return []  # 고성능 케이스는 제안 불필요

        case = await self.db.get(CaseBank, case_id)
        prompt = f"""
        Analyze the following case and suggest improvements:

        Case ID: {case_id}
        Query: {case.query}
        Response: {case.response_text}
        Success Rate: {performance['success_rate']}%
        Common Errors: {performance['common_errors']}

        Provide 3 specific suggestions to improve this case's success rate.
        """

        response = await self.llm.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )

        suggestions = response.choices[0].message.content.strip().split("\n")
        return [s.strip() for s in suggestions if s.strip()]

    async def run_reflection_batch(self) -> Dict[str, Any]:
        """배치 Reflection 실행"""
        cases = await self.get_active_cases_with_logs()
        results = []

        for case in cases:
            performance = await self.analyze_case_performance(case.case_id)

            # success_rate 업데이트
            await self.update_case_success_rate(case.case_id, performance["success_rate"])

            # 저성능 케이스 개선 제안
            if performance["success_rate"] < 50:
                suggestions = await self.generate_improvement_suggestions(case.case_id)
                results.append({
                    "case_id": case.case_id,
                    "performance": performance,
                    "suggestions": suggestions
                })

        return {
            "analyzed_cases": len(cases),
            "low_performance_cases": len(results),
            "suggestions": results
        }
```

### IMPL 0.3: API Endpoints

**@IMPL:REFLECTION-001.0.3.1** Reflection API
```python
@reflection_router.post("/analyze", response_model=ReflectionAnalysisResponse)
async def analyze_case_performance(
    request: ReflectionAnalysisRequest,
    engine: ReflectionEngine = Depends(get_reflection_engine),
    api_key: APIKeyInfo = Depends(verify_api_key)
):
    """케이스 성능 분석"""
    performance = await engine.analyze_case_performance(request.case_id)
    return ReflectionAnalysisResponse(**performance)

@reflection_router.post("/batch", response_model=ReflectionBatchResponse)
async def run_reflection_batch(
    engine: ReflectionEngine = Depends(get_reflection_engine),
    api_key: APIKeyInfo = Depends(verify_api_key)
):
    """배치 Reflection 실행"""
    results = await engine.run_reflection_batch()
    return ReflectionBatchResponse(**results)
```

---

## 6. Traceability (추적성)

### 상위 SPEC 의존성
- **@SPEC:CASEBANK-002**: success_rate 필드 활용
- **@SPEC:NEURAL-001**: 케이스 검색 기능
- **@SPEC:PLANNER-001**: 케이스 실행 로직

### 하위 SPEC 블로킹
- **@SPEC:CONSOLIDATION-001**: Reflection 결과 기반 메모리 정리

### 관련 SPEC
- **@SPEC:EVAL-001**: 평가 메트릭과 연동

---

**END OF SPEC**
