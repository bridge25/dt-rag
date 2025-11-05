---
id: CONSOLIDATION-001
version: 0.1.0
status: completed
created: 2025-10-09
updated: 2025-11-05
author: @claude
priority: medium
category: feature
labels:
  - memory-consolidation
  - lifecycle-management
  - optimization
  - phase-3
depends_on:
  - CASEBANK-002
  - REFLECTION-001
blocks: []
related_specs:
  - NEURAL-001
  - SEARCH-001
scope:
  packages:
    - apps/orchestration
  files:
    - apps/orchestration/src/consolidation_policy.py
  tests:
    - tests/unit/test_consolidation_policy.py
---

# @SPEC:CONSOLIDATION-001: Memory Consolidation Policy - 케이스 라이프사이클 자동 관리

@SPEC:CONSOLIDATION-001 @VERSION:0.1.0 @STATUS:draft

## HISTORY

### v0.1.0 (2025-10-09)
- **INITIAL**: Memory Consolidation Policy SPEC 최초 작성
- **AUTHOR**: @claude
- **SCOPE**: 케이스 라이프사이클 자동 관리, 저성능 케이스 제거, 중복 케이스 병합
- **CONTEXT**: PRD 1.5P Phase 3 - Memory Consolidation 및 최적화
- **BASELINE**: CASEBANK-002 완료 (lifecycle 필드), REFLECTION-001 완료 (성능 분석)

---

## 1. 개요

### 목적
Memory Consolidation Policy는 CaseBank의 케이스를 자동으로 관리하여 시스템 성능과 메모리 효율성을 유지합니다. 저성능 케이스를 제거하고, 중복 케이스를 병합하며, 사용되지 않는 케이스를 아카이빙하여 CaseBank를 최적 상태로 유지합니다.

### 범위
- **저성능 케이스 제거**: success_rate < 30% 케이스 자동 archived 처리
- **중복 케이스 병합**: 유사도 > 95% 케이스 통합 (임베딩 기반)
- **사용 빈도 기반 정리**: 90일간 미사용 케이스 아카이빙
- **자동 스케줄러**: 주간 1회 자동 실행

---

## 2. Environment (환경)

### 기술 스택
- **Database**: PostgreSQL (CaseBank 메타데이터 활용)
- **Vector Similarity**: pgvector (중복 탐지)
- **스케줄러**: APScheduler or Celery Beat
- **비동기 처리**: asyncio

### 기존 구현 상태
- **CaseBank 메타데이터** (CASEBANK-002):
  - usage_count, success_rate, last_accessed_at, status
- **Reflection Engine** (REFLECTION-001):
  - 성능 분석 및 success_rate 계산
- **Neural 검색** (NEURAL-001):
  - Vector 유사도 계산

### 제약사항
- 케이스 삭제는 복구 불가능하므로 신중한 정책 필요
- 중복 병합 시 원본 데이터 보존 (아카이빙)
- 프로덕션 환경에서는 수동 승인 옵션 제공

---

## 3. Assumptions (가정)

### 데이터 가정
1. 모든 케이스에 메타데이터(usage_count, success_rate) 존재
2. 임베딩 벡터(query_vector)가 생성된 케이스만 중복 탐지 대상
3. archived 상태 케이스는 복구 가능

### 아키텍처 가정
1. Consolidation Policy는 주간 배치로 실행
2. 정책 실행 중 검색 API는 정상 동작
3. 아카이빙된 케이스는 별도 테이블에 백업

---

## 4. Requirements (요구사항)

### Ubiquitous Requirements

**@REQ:CONSOLIDATION-001.1** Low Performance Removal
- 시스템은 success_rate < 30%이고 usage_count > 10인 케이스를 archived 상태로 변경해야 한다
- 제거 전 관리자에게 알림을 보내야 한다

**@REQ:CONSOLIDATION-001.2** Duplicate Detection
- 시스템은 Vector 유사도 > 95% 케이스를 중복으로 판단해야 한다
- 중복 케이스 중 usage_count가 높은 케이스를 유지해야 한다

**@REQ:CONSOLIDATION-001.3** Inactivity Archiving
- 시스템은 90일간 last_accessed_at이 갱신되지 않은 케이스를 아카이빙해야 한다
- 단, usage_count > 100 케이스는 예외 처리해야 한다

### Event-driven Requirements

**@REQ:CONSOLIDATION-001.4** WHEN Consolidation Runs
- WHEN Consolidation Policy가 실행되면, 시스템은 분석 결과를 로그에 기록해야 한다
- WHEN 케이스가 archived 처리되면, 시스템은 변경 이력을 저장해야 한다

**@REQ:CONSOLIDATION-001.5** WHEN Duplicate Found
- WHEN 중복 케이스가 발견되면, 시스템은 usage_count와 success_rate를 비교해야 한다
- WHEN 병합이 완료되면, 원본 케이스는 archived 상태로 변경해야 한다

**@REQ:CONSOLIDATION-001.6** WHEN Archived Case Accessed
- WHEN archived 케이스가 검색 요청되면, 시스템은 경고 로그를 기록해야 한다
- WHEN 복구 요청이 들어오면, 시스템은 status를 'active'로 변경해야 한다

### State-driven Requirements

**@REQ:CONSOLIDATION-001.7** WHILE Consolidation Active
- WHILE Consolidation 실행 중, 시스템은 진행 상태를 모니터링해야 한다
- WHILE 정책 실행 중, 검색 API는 정상 동작해야 한다

**@REQ:CONSOLIDATION-001.8** WHILE Dry-Run Mode
- WHILE dry-run 모드일 때, 시스템은 실제 변경 없이 분석 결과만 반환해야 한다
- WHILE dry-run 중, 예상 제거/병합 대상을 리스트로 출력해야 한다

### Constraints

**@REQ:CONSOLIDATION-001.9** Safety Constraints
- IF 케이스가 최근 7일 내 접근된 경우, 아카이빙하지 않아야 한다
- IF usage_count > 500인 경우, 자동 제거 대상에서 제외해야 한다
- IF success_rate이 NULL인 경우, 제거 정책을 적용하지 않아야 한다

**@REQ:CONSOLIDATION-001.10** Performance Constraint
- Consolidation 실행은 검색 API 응답 시간에 영향을 주지 않아야 한다
- 중복 탐지 시 배치 크기는 최대 100개로 제한되어야 한다

---

## 5. Specifications (상세 구현 명세)

### IMPL 0.1: Consolidation Policy Core

**@IMPL:CONSOLIDATION-001.0.1** ConsolidationPolicy Class
```python
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

class ConsolidationPolicy:
    def __init__(self, db_session: AsyncSession, dry_run: bool = False):
        self.db = db_session
        self.dry_run = dry_run
        self.removed_cases = []
        self.merged_cases = []
        self.archived_cases = []

    async def run_consolidation(self) -> Dict[str, Any]:
        """전체 Consolidation 정책 실행"""
        # 1. 저성능 케이스 제거
        low_performance_cases = await self.remove_low_performance_cases()

        # 2. 중복 케이스 병합
        duplicate_cases = await self.merge_duplicate_cases()

        # 3. 미사용 케이스 아카이빙
        inactive_cases = await self.archive_inactive_cases()

        return {
            "removed_cases": len(low_performance_cases),
            "merged_cases": len(duplicate_cases),
            "archived_cases": len(inactive_cases),
            "dry_run": self.dry_run,
            "details": {
                "removed": low_performance_cases,
                "merged": duplicate_cases,
                "archived": inactive_cases
            }
        }

    async def remove_low_performance_cases(self) -> List[str]:
        """저성능 케이스 제거"""
        # success_rate < 30% AND usage_count > 10
        stmt = select(CaseBank).where(
            CaseBank.status == 'active',
            CaseBank.success_rate < 30,
            CaseBank.usage_count > 10
        )
        result = await self.db.execute(stmt)
        cases = result.scalars().all()

        removed_ids = []
        for case in cases:
            if not self.dry_run:
                case.status = 'archived'
                await self.db.commit()
            removed_ids.append(case.case_id)

        return removed_ids

    async def merge_duplicate_cases(self, similarity_threshold: float = 0.95) -> List[Dict[str, str]]:
        """중복 케이스 병합"""
        # Vector 유사도 기반 중복 탐지
        stmt = select(CaseBank).where(
            CaseBank.status == 'active',
            CaseBank.query_vector.isnot(None)
        )
        result = await self.db.execute(stmt)
        cases = result.scalars().all()

        merged_pairs = []
        processed = set()

        for i, case1 in enumerate(cases):
            if case1.case_id in processed:
                continue

            for case2 in cases[i+1:]:
                if case2.case_id in processed:
                    continue

                # 코사인 유사도 계산
                similarity = await self._calculate_similarity(case1.query_vector, case2.query_vector)

                if similarity > similarity_threshold:
                    # usage_count 높은 케이스 유지
                    keeper, remover = (case1, case2) if case1.usage_count >= case2.usage_count else (case2, case1)

                    if not self.dry_run:
                        # 메타데이터 병합
                        keeper.usage_count += remover.usage_count
                        keeper.success_rate = (keeper.success_rate + remover.success_rate) / 2
                        remover.status = 'archived'
                        await self.db.commit()

                    merged_pairs.append({
                        "keeper": keeper.case_id,
                        "removed": remover.case_id,
                        "similarity": similarity
                    })
                    processed.add(remover.case_id)

        return merged_pairs

    async def archive_inactive_cases(self, days: int = 90) -> List[str]:
        """미사용 케이스 아카이빙"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = select(CaseBank).where(
            CaseBank.status == 'active',
            CaseBank.last_accessed_at < cutoff_date,
            CaseBank.usage_count < 100  # 고빈도 케이스 예외
        )
        result = await self.db.execute(stmt)
        cases = result.scalars().all()

        archived_ids = []
        for case in cases:
            if not self.dry_run:
                case.status = 'archived'
                await self.db.commit()
            archived_ids.append(case.case_id)

        return archived_ids

    async def _calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """코사인 유사도 계산"""
        from numpy import dot
        from numpy.linalg import norm
        return float(dot(vec1, vec2) / (norm(vec1) * norm(vec2)))
```

### IMPL 0.2: Archive Management

**@IMPL:CONSOLIDATION-001.0.2.1** Archive Table
```sql
CREATE TABLE IF NOT EXISTS case_bank_archive (
    archive_id SERIAL PRIMARY KEY,
    case_id VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,
    response_text TEXT NOT NULL,
    category_path VARCHAR(255),
    query_vector VECTOR(1536),
    usage_count INTEGER,
    success_rate REAL,
    archived_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    archived_reason VARCHAR(255)
);

CREATE INDEX idx_archive_case_id ON case_bank_archive(case_id);
CREATE INDEX idx_archive_archived_at ON case_bank_archive(archived_at DESC);
```

**@IMPL:CONSOLIDATION-001.0.2.2** Archive Function
```python
async def archive_case_to_backup(
    session: AsyncSession,
    case: CaseBank,
    reason: str
) -> None:
    """케이스를 아카이브 테이블로 백업"""
    archive_record = CaseBankArchive(
        case_id=case.case_id,
        query=case.query,
        response_text=case.response_text,
        category_path=case.category_path,
        query_vector=case.query_vector,
        usage_count=case.usage_count,
        success_rate=case.success_rate,
        archived_reason=reason
    )
    session.add(archive_record)
    await session.commit()
```

### IMPL 0.3: API Endpoints

**@IMPL:CONSOLIDATION-001.0.3.1** Consolidation API
```python
@consolidation_router.post("/run", response_model=ConsolidationResponse)
async def run_consolidation(
    request: ConsolidationRequest,
    policy: ConsolidationPolicy = Depends(get_consolidation_policy),
    api_key: APIKeyInfo = Depends(verify_api_key)
):
    """Consolidation Policy 실행"""
    results = await policy.run_consolidation()
    return ConsolidationResponse(**results)

@consolidation_router.post("/dry-run", response_model=ConsolidationResponse)
async def dry_run_consolidation(
    policy: ConsolidationPolicy = Depends(lambda: ConsolidationPolicy(db, dry_run=True)),
    api_key: APIKeyInfo = Depends(verify_api_key)
):
    """Consolidation Policy 시뮬레이션 (변경 없음)"""
    results = await policy.run_consolidation()
    return ConsolidationResponse(**results)

@consolidation_router.post("/restore/{case_id}")
async def restore_archived_case(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    api_key: APIKeyInfo = Depends(verify_api_key)
):
    """아카이빙된 케이스 복구"""
    case = await db.get(CaseBank, case_id)
    if not case or case.status != 'archived':
        raise HTTPException(status_code=404, detail="Archived case not found")

    case.status = 'active'
    await db.commit()
    return {"case_id": case_id, "status": "restored"}
```

### IMPL 0.4: Scheduler

**@IMPL:CONSOLIDATION-001.0.4** Weekly Scheduler
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

async def schedule_consolidation():
    scheduler = AsyncIOScheduler()

    # 매주 일요일 오전 2시 실행
    scheduler.add_job(
        run_weekly_consolidation,
        CronTrigger(day_of_week='sun', hour=2, minute=0),
        id='weekly_consolidation'
    )

    scheduler.start()

async def run_weekly_consolidation():
    """주간 Consolidation 배치 실행"""
    async with get_db_session() as session:
        policy = ConsolidationPolicy(session, dry_run=False)
        results = await policy.run_consolidation()

        # 결과 로깅 및 알림
        logger.info(f"Weekly consolidation completed: {results}")
        await send_admin_notification("Consolidation Report", results)
```

---

## 6. Traceability (추적성)

### 상위 SPEC 의존성
- **@SPEC:CASEBANK-002**: status, usage_count, last_accessed_at 필드
- **@SPEC:REFLECTION-001**: success_rate 계산
- **@SPEC:NEURAL-001**: Vector 유사도 계산

### 관련 SPEC
- **@SPEC:SEARCH-001**: archived 케이스 필터링
- **@SPEC:DATABASE-001**: Archive 테이블 스키마

---

**END OF SPEC**
