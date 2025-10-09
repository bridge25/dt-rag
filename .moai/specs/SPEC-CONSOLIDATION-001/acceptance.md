---
id: CONSOLIDATION-001-ACCEPTANCE
version: 0.1.0
status: draft
created: 2025-10-09
updated: 2025-10-09
author: @claude
---

# SPEC-CONSOLIDATION-001: Acceptance Criteria

@ACCEPTANCE:CONSOLIDATION-001 @VERSION:0.1.0

## 수락 기준 개요

이 문서는 SPEC-CONSOLIDATION-001의 완료를 판단하기 위한 상세한 수락 기준을 정의합니다.

---

## Scenario 1: 저성능 케이스 제거

### Given
- CaseBank에 케이스 5개 존재:
  - 'case-low-1' (success_rate=25%, usage_count=20)
  - 'case-low-2' (success_rate=28%, usage_count=15)
  - 'case-high' (success_rate=85%, usage_count=50)
  - 'case-mid' (success_rate=50%, usage_count=30)
  - 'case-unused' (success_rate=20%, usage_count=5) # 제외 (usage < 10)

### When
- POST `/consolidation/run`

### Then
- 'case-low-1', 'case-low-2'의 status가 'archived'로 변경
- 'case-unused'는 제외 (usage_count < 10)
- 'case-high', 'case-mid'는 'active' 유지
- Archive 테이블에 백업 레코드 2개 생성
- 응답:
  ```json
  {
    "removed_cases": 2,
    "details": {
      "removed": ["case-low-1", "case-low-2"]
    }
  }
  ```

---

## Scenario 2: 중복 케이스 병합

### Given
- CaseBank에 케이스 3개 존재:
  - 'case-A' (query="How to deploy?", usage_count=100, vector=[0.1, 0.2, ...])
  - 'case-B' (query="How to deploy app?", usage_count=50, vector=[0.12, 0.21, ...]) # 유사도 96%
  - 'case-C' (query="What is deployment?", usage_count=30, vector=[0.9, 0.8, ...]) # 유사도 40%

### When
- POST `/consolidation/run`

### Then
- 'case-A'와 'case-B' 병합:
  - 'case-A' 유지 (usage_count=150, success_rate=(A+B)/2)
  - 'case-B' archived
- 'case-C'는 유지 (유사도 < 95%)
- 응답:
  ```json
  {
    "merged_cases": 1,
    "details": {
      "merged": [
        {
          "keeper": "case-A",
          "removed": "case-B",
          "similarity": 0.96
        }
      ]
    }
  }
  ```

---

## Scenario 3: 미사용 케이스 아카이빙

### Given
- CaseBank에 케이스 3개 존재:
  - 'case-old' (last_accessed_at=100일 전, usage_count=50)
  - 'case-popular' (last_accessed_at=100일 전, usage_count=200) # 예외 (고빈도)
  - 'case-recent' (last_accessed_at=10일 전, usage_count=10)

### When
- POST `/consolidation/run` (default: days=90)

### Then
- 'case-old' archived (90일 초과 + usage_count < 100)
- 'case-popular' 유지 (usage_count > 100 예외)
- 'case-recent' 유지 (최근 접근)
- 응답:
  ```json
  {
    "archived_cases": 1,
    "details": {
      "archived": ["case-old"]
    }
  }
  ```

---

## Scenario 4: Dry-Run 모드 (시뮬레이션)

### Given
- CaseBank에 제거 대상 케이스 10개 존재

### When
- POST `/consolidation/dry-run`

### Then
- 실제 변경 없음 (status 유지)
- 예상 결과만 반환:
  ```json
  {
    "removed_cases": 3,
    "merged_cases": 2,
    "archived_cases": 5,
    "dry_run": true,
    "details": {...}
  }
  ```
- CaseBank 테이블 변경 없음 확인

---

## Scenario 5: 아카이빙된 케이스 복구

### Given
- 케이스 'case-archived' 존재 (status='archived')

### When
- POST `/consolidation/restore/case-archived`

### Then
- 'case-archived'의 status가 'active'로 변경
- 복구 성공 응답:
  ```json
  {
    "case_id": "case-archived",
    "status": "restored"
  }
  ```
- 검색 API에서 다시 조회 가능

---

## Scenario 6: 안전 제약 (최근 접근 케이스)

### Given
- 케이스 'case-recent-low' 존재:
  - success_rate=20%
  - usage_count=50
  - last_accessed_at=5일 전

### When
- POST `/consolidation/run`

### Then
- 'case-recent-low' 제거되지 않음 (최근 7일 내 접근)
- 응답 removed_cases에 포함되지 않음
- 로그에 "Skipped case-recent-low: accessed within 7 days" 기록

---

## Scenario 7: 안전 제약 (고빈도 케이스)

### Given
- 케이스 'case-high-usage' 존재:
  - success_rate=25% (저성능)
  - usage_count=600 (고빈도)

### When
- POST `/consolidation/run`

### Then
- 'case-high-usage' 제거되지 않음 (usage_count > 500 예외)
- 응답 removed_cases에 포함되지 않음
- 경고 로그: "High-usage case case-high-usage has low success rate"

---

## Scenario 8: Archive 테이블 백업

### Given
- 케이스 'case-backup' 존재 (success_rate=25%, usage_count=20)

### When
- POST `/consolidation/run`

### Then
- 'case-backup' archived 처리
- CaseBankArchive 테이블에 백업 레코드 생성:
  - case_id='case-backup'
  - archived_reason='low_performance'
  - archived_at=현재 시각
- 백업 레코드에 query, response_text, query_vector 모두 포함

---

## Scenario 9: 중복 탐지 배치 처리

### Given
- CaseBank에 케이스 500개 존재 (모두 query_vector 포함)

### When
- POST `/consolidation/run`

### Then
- 배치 크기 100개로 분할 처리
- 총 실행 시간 < 5분
- 메모리 사용량 < 1GB
- 중복 탐지 완료 (유사도 > 95%)

---

## Scenario 10: 주간 스케줄러 실행

### Given
- APScheduler 설정 완료 (매주 일요일 오전 2시)

### When
- 스케줄러 트리거 시각 도래

### Then
- Consolidation Policy 자동 실행
- 실행 결과 로그 기록
- 관리자에게 이메일 알림 발송:
  - 제목: "Weekly Consolidation Report"
  - 내용: removed_cases, merged_cases, archived_cases 통계

---

## Scenario 11: 유사도 계산 성능

### Given
- 케이스 1000개 존재 (모두 1536차원 벡터)

### When
- 중복 탐지 실행

### Then
- 유사도 계산 시간 < 1ms per pair
- NumPy 벡터 연산 활용 확인
- 총 비교 횟수 < 500,000회 (조기 종료 최적화)

---

## Scenario 12: 정책 실행 중 검색 API 동작

### Given
- Consolidation Policy 실행 중
- 동시에 검색 요청 발생

### When
- POST `/search?q=test query`

### Then
- 검색 API 정상 응답 (지연 없음)
- Consolidation과 독립적 실행 (락 충돌 없음)
- 검색 응답 시간 < 200ms

---

## 품질 게이트

### 테스트 커버리지
- 단위 테스트 커버리지 > 85%
- 통합 테스트: 12개 시나리오 모두 통과
- 안전 제약 테스트 포함

### 성능 기준
- 케이스 1000개 처리 시간 < 5분
- 중복 탐지 시간 < 3분
- 검색 API 응답 시간 영향 없음

### 안전성 기준
- Dry-Run 모드 기본 활성화
- Archive 백업 100% 완료
- 복구 API 정상 동작

---

## 완료 조건 (Definition of Done)

- [ ] 모든 시나리오 (1~12) 테스트 통과
- [ ] 품질 게이트 기준 충족
- [ ] Archive 테이블 생성 및 마이그레이션 완료
- [ ] ConsolidationPolicy 클래스 구현 완료
- [ ] Dry-Run 모드 동작 확인
- [ ] 복구 API 구현 및 테스트
- [ ] 주간 스케줄러 설정 완료
- [ ] 성능 테스트 통과 (케이스 1000개)
- [ ] 안전 제약 검증 완료
- [ ] 알림 시스템 연동 완료
- [ ] 코드 리뷰 완료 (2명 이상 승인)
- [ ] 운영 가이드 문서 작성
- [ ] 프로덕션 배포 준비 완료

---

**END OF ACCEPTANCE CRITERIA**
