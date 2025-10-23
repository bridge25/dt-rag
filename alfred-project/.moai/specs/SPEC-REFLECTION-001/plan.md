---
id: REFLECTION-001-PLAN
version: 0.1.0
status: draft
created: 2025-10-09
updated: 2025-10-09
author: @claude
---

# SPEC-REFLECTION-001: Implementation Plan

@PLAN:REFLECTION-001 @VERSION:0.1.0

## 구현 우선순위

### 1차 목표: ExecutionLog 스키마 및 기본 추적
- ExecutionLog 테이블 생성 (마이그레이션 SQL)
- SQLAlchemy ExecutionLog 모델 구현
- 케이스 실행 시 로그 기록 로직 (Meta-Planner 통합)
- 단위 테스트: 로그 생성 및 조회

### 2차 목표: 성능 분석 엔진
- ReflectionEngine 클래스 구현
- Success Rate 계산 로직
- 오류 패턴 분석 함수
- 실행 시간 통계 계산

### 3차 목표: LLM 기반 개선 제안
- OpenAI GPT-4 통합
- 개선 제안 프롬프트 최적화
- 저성능 케이스 자동 탐지
- 제안 결과 저장 및 알림

### 최종 목표: 배치 실행 및 자동화
- 배치 Reflection 스케줄러 (일일 1회)
- API 엔드포인트 구현 (`/reflection/analyze`, `/reflection/batch`)
- 통합 테스트 (전체 Reflection 흐름)
- 대시보드 연동 (성능 지표 시각화)

## 기술적 접근 방법

### 로그 수집 전략
1. **비동기 로깅**: 케이스 실행 후 백그라운드 태스크로 로그 기록
2. **배치 삽입**: 다수 로그를 bulk insert로 성능 최적화
3. **인덱스 최적화**: case_id, created_at 복합 인덱스

### 분석 알고리즘
- **Success Rate**: 시간 가중 평균 (최근 로그에 높은 가중치)
- **Error Pattern**: 오류 타입별 빈도 분석 (pandas groupby)
- **Anomaly Detection**: 급격한 성능 저하 탐지 (이동 평균 비교)

### LLM 활용 전략
- **Rate Limiting**: 분당 5회 호출 제한 (asyncio.Semaphore)
- **Cost Optimization**: 저성능 케이스만 LLM 분석 (success_rate < 50%)
- **Prompt Engineering**: 구조화된 출력 요청 (JSON 형식)

## 아키텍처 설계 방향

### 데이터 흐름
```
케이스 실행 (Meta-Planner)
    ↓
ExecutionLog 기록 (비동기)
    ↓
Reflection Engine 분석 (배치)
    ↓
CaseBank.success_rate 업데이트
    ↓
개선 제안 생성 (LLM)
    ↓
알림 발송 (관리자)
```

### 의존성 관리
- **상위 의존성**: CASEBANK-002 (메타데이터 필드), PLANNER-001 (실행 로직)
- **하위 블로킹**: CONSOLIDATION-001
- **선택적 연동**: EVAL-001 (평가 메트릭)

## 리스크 및 대응 방안

### 리스크 1: LLM 호출 비용 증가
- **확률**: 높음
- **영향**: 중간 (운영 비용 증가)
- **대응**:
  - 저성능 케이스만 분석 (필터링)
  - 분석 주기 조정 (일일 → 주간)
  - GPT-4 대신 GPT-3.5 사용 고려

### 리스크 2: 로그 데이터 누적
- **확률**: 높음
- **영향**: 중간 (스토리지 비용)
- **대응**:
  - 30일 이전 로그 자동 아카이빙
  - 요약 통계만 보관 (로그 삭제)
  - 압축 스토리지 활용

### 리스크 3: 분석 결과 신뢰도 낮음
- **확률**: 중간
- **영향**: 높음 (잘못된 개선)
- **대응**:
  - 최소 100회 이상 실행 로그 필요
  - 사람의 최종 승인 필수
  - A/B 테스트로 개선 효과 검증

## 구현 순서

1. **ExecutionLog 스키마 생성** → Meta-Planner 통합 → 로그 수집 시작
2. **ReflectionEngine 구현** → Success Rate 계산 → 단위 테스트
3. **LLM 통합** → 개선 제안 생성 → 프롬프트 최적화
4. **배치 실행** → 스케줄러 설정 → 알림 연동

## 완료 조건 (Definition of Done)

- [ ] ExecutionLog 테이블 생성 및 마이그레이션 완료
- [ ] ReflectionEngine 클래스 구현 완료
- [ ] Success Rate 계산 로직 검증
- [ ] LLM 기반 개선 제안 생성 성공
- [ ] 배치 Reflection 스케줄러 동작 확인
- [ ] API 엔드포인트 구현 및 테스트
- [ ] 단위 테스트 커버리지 > 85%
- [ ] 통합 테스트 통과 (전체 흐름)
- [ ] 성능 테스트 통과 (로그 10,000개 분석 < 60초)
- [ ] 문서 업데이트 (API 문서, 운영 가이드)

---

**END OF PLAN**
