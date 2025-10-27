# 테스트 실패 백로그 (2025-10-14)

## 요약
- **전체 커버리지**: 38% (13,084 statements, 8,118 missing)
- **테스트 통과**: 403 passed / 95 failed / 19 errors
- **통과율**: 78%

## 실패 원인 분류

### 1. Agent Router Mock 문제 (14개)
**우선순위**: Medium
**원인**: Mock이 실제 DB를 호출하는 문제
**영향**: agent_router 테스트 불안정

**실패 목록**:
- test_get_agent_success
- test_get_agent_not_found
- test_get_agent_invalid_uuid
- test_list_agents_no_filters
- test_list_agents_with_level_filter
- test_list_agents_exceeding_max_results
- test_delete_agent_success
- test_search_agents_with_query
- test_search_agents_no_query
- test_search_agents_exceeding_max_results
- test_refresh_coverage_background_true
- test_get_coverage_task_status
- test_get_coverage_history
- test_get_coverage_history_with_date_filters

**해결 방안**:
- fixture 재설계
- dependency override 검증
- Mock 적용 시점 확인

### 2. Consolidation Policy 속성 미구현 (8개)
**우선순위**: Low
**원인**: `CaseBank.usage_count` 속성 없음
**영향**: Consolidation 정책 테스트 전체 실패

**실패 목록**:
- test_remove_low_performance_cases
- test_remove_low_performance_skip_high_usage
- test_merge_duplicate_cases
- test_merge_keep_higher_usage
- test_archive_inactive_cases
- test_archive_skip_high_usage
- test_dry_run_mode
- test_run_consolidation_batch

**해결 방안**:
- CaseBank 모델에 usage_count 컬럼 추가
- 또는 테스트 로직 수정

### 3. Redis/Database 통합 테스트 (50+개)
**우선순위**: Low (환경 의존)
**원인**: 로컬 테스트 환경의 Redis/DB 연결 문제
**영향**: 통합 테스트 불안정

**카테고리**:
- test_redis_manager.py (25개)
- test_health_check.py (17개)
- test_search_router.py (13개)
- test_database.py (8개)

**해결 방안**:
- Docker Compose 기반 테스트 환경 구축
- CI/CD 환경에서 재검증
- 또는 integration 마커로 분리

### 4. 데이터베이스 동시성 에러 (19 errors)
**우선순위**: High
**원인**: SQLAlchemy "another operation is in progress" 에러
**영향**: execution_log, reflection_engine 테스트 실패

**실패 목록**:
- test_execution_log_* (5개)
- test_reflection_engine_* (8개)
- test_case_embedding_* (3개)
- test_redis_manager integration (3개)

**해결 방안**:
- 트랜잭션 격리 개선
- 각 테스트마다 독립적 세션 사용
- asyncio 동시성 제어

## 개선 계획

### Phase 1: 블로커 해결 (완료)
- ✅ 405 Method Not Allowed 에러 해결
- ✅ agent_router 등록

### Phase 2: 새 기능 개발 (진행 중)
- Service Layer 확장
- Redis Queue 도입
- Batch Classification 최적화
- **목표 커버리지**: 각 85%+

### Phase 3: 기존 테스트 개선 (백로그)
- Agent Router Mock 수정
- DB 동시성 문제 해결
- 환경 의존성 분리

## 참고
- 현재 38% 커버리지는 기존 레거시 코드 포함
- 새 기능은 SPEC-First TDD로 85%+ 달성 예정
- 전체 평균은 점진적으로 상승 예상
