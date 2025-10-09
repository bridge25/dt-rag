---
id: REFLECTION-001-ACCEPTANCE
version: 0.1.0
status: draft
created: 2025-10-09
updated: 2025-10-09
author: @claude
---

# SPEC-REFLECTION-001: Acceptance Criteria

@ACCEPTANCE:REFLECTION-001 @VERSION:0.1.0

## 수락 기준 개요

이 문서는 SPEC-REFLECTION-001의 완료를 판단하기 위한 상세한 수락 기준을 정의합니다.

---

## Scenario 1: ExecutionLog 기록

### Given
- CaseBank에 케이스 'case-test' 존재
- Meta-Planner가 케이스를 실행

### When
- 케이스 실행 성공: `execute_case('case-test')`

### Then
- ExecutionLog 레코드 생성:
  - case_id='case-test'
  - success=True
  - error_type=NULL
  - execution_time_ms > 0
  - created_at=현재 시각
- 로그 기록 시간 < 10ms (비동기 처리)

---

## Scenario 2: 실행 실패 로그

### Given
- 케이스 'case-fail' 존재
- 실행 시 오류 발생 (예: 도구 호출 실패)

### When
- 케이스 실행 실패: `execute_case('case-fail')`

### Then
- ExecutionLog 레코드 생성:
  - success=False
  - error_type='ToolExecutionError'
  - error_message='Tool XYZ not found'
  - execution_time_ms > 0
- 로그에 상세 컨텍스트 포함 (context JSON 필드)

---

## Scenario 3: Success Rate 계산

### Given
- 케이스 'case-sr' 실행 로그 10개 존재:
  - 성공: 7개
  - 실패: 3개

### When
- POST `/reflection/analyze` with body: `{"case_id": "case-sr"}`

### Then
- 응답:
  - success_rate=70.0
  - total_executions=10
- CaseBank.success_rate 필드 업데이트: 70.0

---

## Scenario 4: 오류 패턴 분석

### Given
- 케이스 'case-errors' 실행 로그 20개 존재:
  - 'ToolNotFound': 10개
  - 'TimeoutError': 5개
  - 'InvalidInput': 3개
  - 성공: 2개

### When
- ReflectionEngine.analyze_case_performance('case-errors')

### Then
- 응답 common_errors:
  ```json
  [
    {"error_type": "ToolNotFound", "count": 10, "percentage": 50.0},
    {"error_type": "TimeoutError", "count": 5, "percentage": 25.0},
    {"error_type": "InvalidInput", "count": 3, "percentage": 15.0}
  ]
  ```
- success_rate=10.0 (2/20)

---

## Scenario 5: LLM 개선 제안 생성

### Given
- 케이스 'case-low' 존재 (success_rate=30%)
- OpenAI API 키 설정 완료

### When
- ReflectionEngine.generate_improvement_suggestions('case-low')

### Then
- LLM 호출 성공
- 응답에 3개 이상의 개선 제안 포함:
  - 예: "Update tool parameters to handle edge cases"
  - 예: "Add input validation before execution"
  - 예: "Increase timeout threshold"
- LLM 호출 시간 < 5초

---

## Scenario 6: 배치 Reflection 실행

### Given
- CaseBank에 케이스 50개 존재
- 각 케이스에 최소 10개 이상의 실행 로그
- 저성능 케이스 5개 (success_rate < 50%)

### When
- POST `/reflection/batch`

### Then
- 50개 케이스 분석 완료
- success_rate 업데이트 완료 (CaseBank 테이블)
- 저성능 케이스 5개에 대해 개선 제안 생성
- 응답:
  ```json
  {
    "analyzed_cases": 50,
    "low_performance_cases": 5,
    "suggestions": [...]
  }
  ```
- 배치 실행 시간 < 60초

---

## Scenario 7: 시간 가중 Success Rate

### Given
- 케이스 'case-time' 실행 로그 20개:
  - 오래된 로그 10개 (7일 전): 성공 2개
  - 최근 로그 10개 (1일 전): 성공 8개

### When
- ReflectionEngine.analyze_case_performance('case-time', time_weighted=True)

### Then
- 시간 가중 success_rate > 단순 평균 (50%)
- 최근 로그에 높은 가중치 적용
- 예상 success_rate ≈ 65% (최근 성능 반영)

---

## Scenario 8: 저성능 케이스 경고 플래그

### Given
- 케이스 'case-warning' 존재 (success_rate=45%)

### When
- 배치 Reflection 실행

### Then
- CaseBank.status가 'active'에서 'warning'으로 변경
- Meta-Planner가 해당 케이스 선택 우선순위 낮춤
- 관리자에게 경고 알림 발송

---

## Scenario 9: 고성능 케이스 (제안 생략)

### Given
- 케이스 'case-high' 존재 (success_rate=95%)

### When
- ReflectionEngine.generate_improvement_suggestions('case-high')

### Then
- 빈 리스트 반환 (개선 제안 불필요)
- LLM 호출 없음 (비용 절감)
- 로그에 "High-performance case, skipping suggestions" 기록

---

## Scenario 10: 로그 아카이빙

### Given
- ExecutionLog에 45일 이전 로그 1000개 존재

### When
- 자동 아카이빙 배치 실행 (cron: 일일 1회)

### Then
- 30일 이전 로그 아카이빙:
  - 요약 통계만 보관 (case_id, success_rate, execution_count)
  - 원본 로그 삭제
- ExecutionLog 테이블 크기 감소 확인
- 아카이빙된 데이터는 별도 테이블 (execution_log_archive)에 저장

---

## Scenario 11: 동시 분석 처리

### Given
- 배치 Reflection 실행 중
- 새로운 케이스 실행 10회 발생

### When
- 실행 로그 계속 기록됨

### Then
- Reflection 분석은 기존 스냅샷 기반 (동시성 충돌 없음)
- 새 로그는 다음 배치 분석에 포함
- 데이터베이스 잠금(lock) 발생하지 않음

---

## Scenario 12: API 권한 검증

### Given
- 인증되지 않은 사용자

### When
- POST `/reflection/analyze` without API key

### Then
- HTTP 401 Unauthorized 응답
- 분석 실행되지 않음

---

## 품질 게이트

### 테스트 커버리지
- 단위 테스트 커버리지 > 85%
- 통합 테스트: 12개 시나리오 모두 통과
- LLM 응답 모킹 테스트 포함

### 성능 기준
- 로그 기록 시간 < 10ms
- Success Rate 계산 시간 < 100ms (케이스당)
- 배치 Reflection 시간 < 60초 (케이스 50개 기준)
- LLM 호출 시간 < 5초

### 신뢰성 기준
- 최소 100회 이상 실행 로그 시 분석 수행
- LLM 실패 시 기본 통계 분석만 반환 (Fallback)
- 데이터베이스 트랜잭션 무결성 보장

---

## 완료 조건 (Definition of Done)

- [ ] 모든 시나리오 (1~12) 테스트 통과
- [ ] 품질 게이트 기준 충족
- [ ] ExecutionLog 스키마 및 마이그레이션 완료
- [ ] ReflectionEngine 클래스 구현 완료
- [ ] LLM 통합 및 개선 제안 생성 성공
- [ ] 배치 Reflection 스케줄러 동작 확인
- [ ] API 엔드포인트 구현 및 문서화
- [ ] 로그 아카이빙 로직 검증
- [ ] 코드 리뷰 완료 (2명 이상 승인)
- [ ] 프로덕션 배포 준비 완료

---

**END OF ACCEPTANCE CRITERIA**
