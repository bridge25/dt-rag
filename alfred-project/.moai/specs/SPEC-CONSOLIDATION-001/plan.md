---
id: CONSOLIDATION-001-PLAN
version: 0.1.0
status: draft
created: 2025-10-09
updated: 2025-10-09
author: @claude
---

# SPEC-CONSOLIDATION-001: Implementation Plan

@PLAN:CONSOLIDATION-001 @VERSION:0.1.0

## 구현 우선순위

### 1차 목표: Archive 인프라 구축
- CaseBankArchive 테이블 생성 (마이그레이션 SQL)
- SQLAlchemy Archive 모델 구현
- 백업 및 복구 함수 구현
- 단위 테스트: 아카이빙 및 복구

### 2차 목표: Consolidation Policy 핵심 로직
- ConsolidationPolicy 클래스 구현
- 저성능 케이스 제거 로직
- 중복 케이스 탐지 및 병합 로직
- 미사용 케이스 아카이빙 로직

### 3차 목표: API 및 Dry-Run 모드
- Consolidation API 엔드포인트 구현
- Dry-Run 모드 (시뮬레이션)
- 복구 API 엔드포인트
- 통합 테스트

### 최종 목표: 스케줄러 및 자동화
- APScheduler 통합
- 주간 배치 실행 설정
- 알림 시스템 연동
- 모니터링 대시보드

## 기술적 접근 방법

### 중복 탐지 전략
1. **배치 처리**: 케이스를 100개 단위로 나누어 처리
2. **캐싱**: 이미 비교한 케이스 쌍은 스킵
3. **인덱스 활용**: query_vector가 NULL이 아닌 케이스만 조회

### 유사도 계산 최적화
- **NumPy 활용**: 벡터 연산 최적화
- **병렬 처리**: asyncio.gather로 다중 비교
- **조기 종료**: 유사도 < 0.90이면 즉시 스킵

### 안전 장치
- **Dry-Run 모드**: 기본값으로 설정 (프로덕션 안전)
- **수동 승인**: 관리자 확인 후 실제 적용
- **롤백 기능**: archived 케이스 복구 API

## 아키텍처 설계 방향

### 데이터 흐름
```
Consolidation Policy 실행
    ↓
[1] 저성능 케이스 탐지 → Archive → status='archived'
    ↓
[2] 중복 케이스 탐지 → 병합 → 원본 archived
    ↓
[3] 미사용 케이스 탐지 → Archive → status='archived'
    ↓
결과 보고서 생성 → 관리자 알림
```

### 의존성 관리
- **상위 의존성**: CASEBANK-002 (메타데이터), REFLECTION-001 (성능 분석)
- **독립 실행**: 검색 API와 독립적 (백그라운드 배치)

## 리스크 및 대응 방안

### 리스크 1: 오탐지 (False Positive)
- **확률**: 중간
- **영향**: 높음 (유용한 케이스 제거)
- **대응**:
  - Dry-Run 모드로 사전 검증
  - 높은 임계값 설정 (similarity > 0.95)
  - 수동 승인 프로세스

### 리스크 2: 중복 탐지 성능 저하
- **확률**: 높음
- **영향**: 중간 (배치 실행 시간 증가)
- **대응**:
  - 배치 크기 제한 (100개)
  - 병렬 처리 (asyncio)
  - 조기 종료 최적화

### 리스크 3: 데이터 손실
- **확률**: 낮음
- **영향**: 매우 높음
- **대응**:
  - Archive 테이블에 백업 필수
  - 복구 API 제공
  - 90일간 Archive 보관

## 구현 순서

1. **Archive 인프라** → Archive 테이블 생성 → 백업/복구 테스트
2. **Consolidation Policy** → 핵심 로직 구현 → 단위 테스트
3. **API 엔드포인트** → Dry-Run 모드 → 통합 테스트
4. **스케줄러** → 주간 배치 설정 → 알림 연동

## 완료 조건 (Definition of Done)

- [ ] CaseBankArchive 테이블 생성 완료
- [ ] ConsolidationPolicy 클래스 구현 완료
- [ ] 저성능 케이스 제거 로직 검증
- [ ] 중복 케이스 병합 로직 검증 (유사도 계산)
- [ ] 미사용 케이스 아카이빙 로직 검증
- [ ] Dry-Run 모드 동작 확인
- [ ] 복구 API 구현 및 테스트
- [ ] 주간 스케줄러 설정 완료
- [ ] 단위 테스트 커버리지 > 85%
- [ ] 통합 테스트 통과
- [ ] 성능 테스트 통과 (케이스 1000개 처리 < 5분)
- [ ] 문서 업데이트 (운영 가이드)

---

**END OF PLAN**
