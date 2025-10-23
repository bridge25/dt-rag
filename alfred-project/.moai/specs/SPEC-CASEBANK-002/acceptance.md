---
id: CASEBANK-002-ACCEPTANCE
version: 0.1.0
status: draft
created: 2025-10-09
updated: 2025-10-09
author: @claude
---

# SPEC-CASEBANK-002: Acceptance Criteria

@ACCEPTANCE:CASEBANK-002 @VERSION:0.1.0

## 수락 기준 개요

이 문서는 SPEC-CASEBANK-002의 완료를 판단하기 위한 상세한 수락 기준을 정의합니다.

---

## Scenario 1: 스키마 마이그레이션

### Given
- PostgreSQL 데이터베이스 실행 중
- 기존 CaseBank 테이블 존재 (FOUNDATION-001 스키마)
- 마이그레이션 스크립트 준비 완료 (002_extend_casebank_metadata.sql)

### When
- 마이그레이션 SQL 실행: `psql < db/migrations/002_extend_casebank_metadata.sql`

### Then
- 8개 새 컬럼 추가 성공:
  - usage_count (INTEGER, DEFAULT 0)
  - success_rate (REAL, NULL)
  - last_accessed_at (TIMESTAMP WITH TIME ZONE, NULL)
  - version (INTEGER, DEFAULT 1)
  - updated_by (VARCHAR(255), NULL)
  - status (VARCHAR(50), DEFAULT 'active')
  - created_at (TIMESTAMP WITH TIME ZONE, DEFAULT CURRENT_TIMESTAMP)
  - updated_at (TIMESTAMP WITH TIME ZONE, DEFAULT CURRENT_TIMESTAMP)
- 3개 인덱스 생성 성공:
  - idx_casebank_status
  - idx_casebank_last_accessed
  - idx_casebank_usage_count
- 기존 레코드는 NULL 또는 기본값으로 초기화
- 트리거 생성 성공: trigger_casebank_update_timestamp

---

## Scenario 2: 메타데이터 업데이트 (Usage Count)

### Given
- CaseBank에 케이스 1개 존재 (case_id='test-001', usage_count=0)
- 검색 API 활성화

### When
- POST `/search?q=test query`
- 검색 결과에 'test-001' 케이스 포함

### Then
- 'test-001'의 usage_count가 1로 증가
- last_accessed_at이 현재 시각으로 갱신
- updated_at이 자동으로 갱신
- 검색 응답 지연 < 10ms (메타데이터 업데이트는 비동기)

---

## Scenario 3: 케이스 버전 관리

### Given
- 케이스 'case-v1' 존재 (version=1, query="original query")

### When
- PUT `/cases/case-v1` with body: `{"query": "updated query", "updated_by": "user@example.com"}`

### Then
- 케이스 내용 업데이트 성공
- version이 2로 증가
- updated_by가 "user@example.com"으로 설정
- updated_at이 현재 시각으로 갱신
- 이전 버전 데이터는 보존 (옵션: 버전 히스토리 테이블)

---

## Scenario 4: 라이프사이클 상태 변경 (Active → Archived)

### Given
- 케이스 'case-archive' 존재 (status='active')

### When
- PATCH `/cases/case-archive/status` with body: `{"status": "archived"}`

### Then
- status가 'archived'로 변경
- 기본 검색 API에서 제외됨 (POST `/search?q=...`)
- 명시적 검색 시 조회 가능 (POST `/search?q=...&include_archived=true`)
- 상태 변경 로그 기록: "Case case-archive archived at 2025-10-09T12:00:00Z"

---

## Scenario 5: Success Rate 업데이트

### Given
- 케이스 'case-success' 존재 (success_rate=NULL, usage_count=10)
- Reflection Engine이 성공률 계산 완료: 0.85

### When
- POST `/internal/cases/case-success/metrics` with body: `{"success_rate": 0.85}`

### Then
- 'case-success'의 success_rate가 0.85로 설정
- updated_at 자동 갱신
- version 증가하지 않음 (메타데이터 업데이트는 버전 변경 아님)

---

## Scenario 6: 검색 필터링 (Active Cases Only)

### Given
- 케이스 3개 존재:
  - 'case-1' (status='active')
  - 'case-2' (status='active')
  - 'case-3' (status='archived')

### When
- POST `/search?q=test query&max_results=10`

### Then
- 검색 결과에 'case-1', 'case-2'만 포함
- 'case-3'은 제외 (archived 상태)
- 응답에 total_candidates=2 표시

---

## Scenario 7: 메타데이터 기반 정렬

### Given
- 케이스 3개 존재:
  - 'case-A' (usage_count=100, last_accessed_at='2025-10-09 10:00:00')
  - 'case-B' (usage_count=50, last_accessed_at='2025-10-09 11:00:00')
  - 'case-C' (usage_count=200, last_accessed_at='2025-10-09 09:00:00')

### When
- GET `/cases?sort_by=usage_count&order=desc`

### Then
- 결과 순서: case-C (200) → case-A (100) → case-B (50)

### When
- GET `/cases?sort_by=last_accessed_at&order=desc`

### Then
- 결과 순서: case-B (11:00) → case-A (10:00) → case-C (09:00)

---

## Scenario 8: 백워드 호환성 (기존 검색 API)

### Given
- CASEBANK-002 마이그레이션 적용 완료
- 기존 검색 API 사용 중인 클라이언트

### When
- POST `/search?q=test query` (변경 전과 동일한 요청)

### Then
- 검색 결과 반환 성공 (기존 동작과 동일)
- 새 필드는 응답에 포함되지 않음 (옵션: 기본 스키마 유지)
- 응답 지연 증가 < 5% (인덱스 최적화 적용)

---

## Scenario 9: 성능 테스트 (대량 케이스)

### Given
- CaseBank에 케이스 10,000개 존재
- 모든 케이스에 메타데이터 초기화 완료

### When
- POST `/search?q=complex query&max_results=100`

### Then
- 검색 응답 시간 < 200ms
- status 인덱스 활용 확인 (EXPLAIN ANALYZE)
- 메타데이터 업데이트는 비동기 처리 (응답 시간 영향 없음)

---

## Scenario 10: 마이그레이션 롤백

### Given
- CASEBANK-002 마이그레이션 적용 완료
- 롤백 필요 상황 발생 (예: 치명적 버그)

### When
- 롤백 SQL 실행: `psql < db/migrations/002_rollback.sql`

### Then
- 8개 새 컬럼 삭제 성공
- 3개 인덱스 삭제 성공
- 트리거 삭제 성공
- 기존 케이스 데이터 손실 없음
- 기존 검색 API 정상 동작

---

## 품질 게이트

### 테스트 커버리지
- 단위 테스트 커버리지 > 90%
- 통합 테스트: 10개 시나리오 모두 통과
- 마이그레이션 테스트: 적용 + 롤백 성공

### 성능 기준
- 검색 API 응답 시간 증가 < 5%
- 인덱스 크기 < 기존 테이블 크기의 20%
- 메타데이터 업데이트 비동기 처리 시간 < 10ms

### 보안 기준
- 상태 변경 API는 인증 필수
- 메타데이터 조작 방지 (SQL Injection 테스트)
- 민감 정보 로깅 금지 (updated_by는 마스킹)

---

## 완료 조건 (Definition of Done)

- [ ] 모든 시나리오 (1~10) 테스트 통과
- [ ] 품질 게이트 기준 충족
- [ ] 마이그레이션 스크립트 검증 완료 (로컬 + 스테이징)
- [ ] 롤백 스크립트 검증 완료
- [ ] 성능 벤치마크 보고서 작성
- [ ] API 문서 업데이트 (OpenAPI/Swagger)
- [ ] 코드 리뷰 완료 (2명 이상 승인)
- [ ] 프로덕션 배포 준비 완료

---

**END OF ACCEPTANCE CRITERIA**
