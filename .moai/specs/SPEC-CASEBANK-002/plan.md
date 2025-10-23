---
id: CASEBANK-002-PLAN
version: 0.1.0
status: draft
created: 2025-10-09
updated: 2025-10-09
author: @claude
---

# SPEC-CASEBANK-002: Implementation Plan

@PLAN:CASEBANK-002 @VERSION:0.1.0

## 구현 우선순위

### 1차 목표: 스키마 확장 및 마이그레이션
- Migration SQL 스크립트 작성 (002_extend_casebank_metadata.sql)
- SQLAlchemy CaseBank 모델 업데이트
- 마이그레이션 실행 및 검증
- 기존 레코드 NULL 허용 확인

### 2차 목표: 메타데이터 업데이트 로직
- usage_count 증가 로직 구현
- last_accessed_at 갱신 로직 구현
- success_rate 계산 및 업데이트 함수
- 검색 API에 메타데이터 업데이트 통합

### 3차 목표: 라이프사이클 관리
- status 필드 기반 검색 필터링
- 케이스 상태 변경 API 엔드포인트
- archived 케이스 조회 기능
- 상태 변경 이력 로깅

### 최종 목표: 테스트 및 문서화
- 단위 테스트 (메타데이터 CRUD)
- 통합 테스트 (검색 + 메타데이터)
- 성능 테스트 (인덱스 효과 검증)
- API 문서 업데이트

## 기술적 접근 방법

### 마이그레이션 전략
1. **점진적 마이그레이션**: 모든 새 필드를 NULL 허용으로 추가
2. **백워드 호환**: 기존 검색 API 동작 변경 없음
3. **롤백 계획**: 마이그레이션 실패 시 롤백 SQL 준비

### 메타데이터 업데이트 전략
- **비동기 업데이트**: 검색 응답 후 백그라운드에서 메타데이터 갱신
- **배치 업데이트**: 다수의 케이스 접근 시 일괄 업데이트
- **캐싱 고려**: 자주 접근되는 케이스의 메타데이터 캐싱

### 인덱스 최적화
- **복합 인덱스**: status + last_accessed_at 조합 인덱스
- **Partial Index**: active 상태만 인덱싱하여 크기 최소화
- **성능 모니터링**: 인덱스 추가 전후 쿼리 성능 비교

## 아키텍처 설계 방향

### 데이터 모델 확장
```
CaseBank (기존)
├── case_id (PK)
├── query
├── response_text
├── category_path
└── query_vector

CaseBank (확장)
├── (기존 필드들)
├── [Metadata]
│   ├── usage_count
│   ├── success_rate
│   └── last_accessed_at
├── [Version Management]
│   ├── version
│   └── updated_by
├── [Lifecycle]
│   └── status
└── [Timestamps]
    ├── created_at
    └── updated_at
```

### 의존성 관리
- **상위 의존성**: FOUNDATION-001 (CaseBank 기본 스키마)
- **하위 블로킹**: REFLECTION-001, CONSOLIDATION-001
- **병렬 개발 가능**: PLANNER-001, TOOLS-001과 독립적

## 리스크 및 대응 방안

### 리스크 1: 마이그레이션 실패
- **확률**: 낮음
- **영향**: 높음 (DB 스키마 손상)
- **대응**:
  - 프로덕션 적용 전 스테이징 환경 테스트
  - 롤백 SQL 스크립트 사전 준비
  - DB 백업 필수

### 리스크 2: 검색 성능 저하
- **확률**: 중간
- **영향**: 중간 (사용자 경험 저하)
- **대응**:
  - 인덱스 최적화
  - 쿼리 실행 계획 분석
  - 성능 벤치마크 수립

### 리스크 3: 메타데이터 업데이트 병목
- **확률**: 중간
- **영향**: 낮음 (비동기 처리 가능)
- **대응**:
  - 비동기 태스크 큐 활용
  - 배치 업데이트로 DB 부하 분산
  - 업데이트 실패 시 재시도 로직

## 구현 순서

1. **마이그레이션 스크립트 작성** → database.py 모델 업데이트 → 테스트 DB 적용
2. **메타데이터 업데이트 함수** → 검색 API 통합 → 단위 테스트
3. **라이프사이클 API** → 상태 관리 로직 → 통합 테스트
4. **성능 최적화** → 인덱스 튜닝 → 벤치마크

## 완료 조건 (Definition of Done)

- [ ] Migration SQL 실행 성공 (로컬 + 스테이징)
- [ ] SQLAlchemy 모델 업데이트 완료
- [ ] 메타데이터 업데이트 로직 구현 및 테스트
- [ ] 라이프사이클 상태 관리 API 구현
- [ ] 단위 테스트 커버리지 > 90%
- [ ] 통합 테스트 통과 (검색 + 메타데이터)
- [ ] 성능 테스트 통과 (인덱스 효과 검증)
- [ ] 기존 검색 API 동작 변경 없음 확인
- [ ] 문서 업데이트 (API 문서, README)

---

**END OF PLAN**
