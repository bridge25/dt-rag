---
id: JOB-OPTIMIZE-001
version: 0.2.0
status: completed
created: 2025-10-09
updated: 2025-10-22
author: @claude
priority: high
category: optimization
labels:
  - redis
  - job-orchestrator
  - dispatcher-pattern
  - reverse-engineered
scope:
  packages:
    - apps/ingestion/batch
  files:
    - apps/ingestion/batch/job_orchestrator.py (385 LOC)
    - apps/ingestion/batch/job_queue.py (259 LOC)
---

# SPEC-JOB-OPTIMIZE-001: JobOrchestrator Dispatcher 패턴 리팩토링

## HISTORY

### v0.2.0 (2025-10-22)
- **REVERSE_ENGINEERING_COMPLETED**: Git 커밋 307fc03에서 실제 구현 확인
- **IMPLEMENTATION**:
  - Dispatcher 패턴 완전 구현 (단일 Redis 연결)
  - Internal asyncio.Queue 기반 워커 분배
  - 100 workers 지원
  - Redis 연결 100개 → 5개 이하로 감소 달성
- **FILES_RESTORED**: Git checkout으로 복원 완료
- **STATUS_CHANGE**: unknown → completed

### v0.1.0 (2025-10-09)
- **INITIAL**: Dispatcher 패턴 리팩토링 SPEC 초안 작성
- **AUTHOR**: @claude

---

## 배경 및 목적
현재 JobOrchestrator는 최대 100개의 워커를 생성하여 Redis 연결을 과도하게 소비합니다. 이를 개선하여 최적의 리소스 활용과 성능을 달성하고자 합니다.

## 목표
- Redis 연결 수를 100개에서 5개 이하로 감소
- Dispatcher 패턴을 통한 작업 분배 최적화
- 비동기 작업 처리의 효율성 증대

## 세부 요구사항
1. Dispatcher 컴포넌트 설계
2. 워커 풀 관리 메커니즘 구현
3. 작업 큐 최적화
4. 부하 분산 알고리즘 개발
5. 오류 처리 및 복원력 강화

## 기대 효과
- 리소스 사용 효율성 증가
- 시스템 안정성 향상
- Redis 연결 오버헤드 감소