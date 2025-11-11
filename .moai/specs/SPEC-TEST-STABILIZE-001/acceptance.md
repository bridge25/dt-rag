# Acceptance Criteria: SPEC-TEST-STABILIZE-001

## @TAG BLOCK

**Acceptance TAG**: `@ACCEPTANCE:TEST-STABILIZE-001`
**Related SPEC**: `@SPEC:TEST-STABILIZE-001`
**Related PLAN**: `@PLAN:TEST-STABILIZE-001`

---

## OVERVIEW

이 문서는 테스트 안정화 Phase 1의 승인 기준을 Given-When-Then 형식으로 정의합니다. 각 시나리오는 독립적으로 검증 가능하며, 모든 시나리오를 통과해야 이 SPEC이 완료된 것으로 간주됩니다.

### 승인 원칙

1. **객관적 검증**: 모든 기준은 측정 가능하고 자동화 가능합니다
2. **회귀 방지**: 기존 기능이 손상되지 않았는지 확인합니다
3. **품질 보증**: 수정된 테스트가 올바르게 작동하는지 검증합니다
4. **CI 통과**: 전체 파이프라인이 통과해야 합니다

---

## ACCEPTANCE SCENARIOS

### Scenario 1: Reflection API Fixture 주입 성공

**Given**: CI 파이프라인이 통합 테스트를 실행합니다
**And**: `tests/conftest.py`의 픽스처 이름이 `async_client`로 변경되었습니다
**And**: Reflection API 테스트가 `async_client` 픽스처를 요청합니다

**When**: Reflection API 테스트 4개가 실행됩니다
- `test_reflection_suggestions_authentication`
- `test_reflection_health_check`
- `test_reflection_analyze_performance`
- `test_reflection_batch_performance`

**Then**: 다음 조건을 모두 만족해야 합니다
- ✅ 4개 테스트 모두 PASSED 상태
- ✅ Fixture 주입 오류 (ERROR) 없음
- ✅ `async_client` 픽스처가 성공적으로 주입됨
- ✅ 테스트 실행 시간이 정상 범위 내 (각 테스트 < 5초)
- ✅ pytest 출력에서 "fixture 'async_client' not found" 오류 없음

**검증 명령**:
```bash
pytest tests/integration/test_phase3_reflection.py -v
```

**성공 출력 예시**:
```
tests/integration/test_phase3_reflection.py::test_reflection_suggestions_authentication PASSED
tests/integration/test_phase3_reflection.py::test_reflection_health_check PASSED
tests/integration/test_phase3_reflection.py::test_reflection_analyze_performance PASSED
tests/integration/test_phase3_reflection.py::test_reflection_batch_performance PASSED

====== 4 passed in 2.34s ======
```

---

### Scenario 2: Hybrid Search 인증 우회 성공

**Given**: CI 파이프라인이 통합 테스트를 실행합니다
**And**: `tests/integration/test_hybrid_search.py`에 인증 우회 로직이 적용되었습니다
**And**: 테스트 환경에서는 API 인증이 우회됩니다

**When**: Hybrid Search 테스트 2개가 POST /search 엔드포인트를 호출합니다
- `test_hybrid_search_bm25_only` (Line 189-202)
- `test_hybrid_search_with_neural` (Line 204-217)

**Then**: 다음 조건을 모두 만족해야 합니다
- ✅ 2개 테스트 모두 PASSED 상태
- ✅ HTTP 200 OK 응답 수신 (403 Forbidden 아님)
- ✅ 403 인증 오류 없음
- ✅ JSON 응답 검증 성공
- ✅ 검색 결과가 예상 형식으로 반환됨
- ✅ 테스트 실행 시간이 정상 범위 내 (각 테스트 < 10초)

**검증 명령**:
```bash
pytest tests/integration/test_hybrid_search.py::test_hybrid_search_bm25_only -v
pytest tests/integration/test_hybrid_search.py::test_hybrid_search_with_neural -v
```

**성공 출력 예시**:
```
tests/integration/test_hybrid_search.py::test_hybrid_search_bm25_only PASSED
tests/integration/test_hybrid_search.py::test_hybrid_search_with_neural PASSED

====== 2 passed in 3.12s ======
```

**실패 시 나타나지 말아야 할 오류**:
```
❌ AssertionError: assert 403 == 200
❌ {"detail": "Not authenticated"}
❌ fastapi.exceptions.HTTPException: 403 Forbidden
```

---

### Scenario 3: 전체 테스트 스위트 회귀 없음

**Given**: Phase 1 수정이 완료되었습니다
**And**: 기존에 68개의 테스트가 통과했습니다
**And**: 6개의 테스트가 새로 수정되었습니다

**When**: 전체 테스트 스위트가 병렬로 실행됩니다
```bash
pytest -n 4 -v
```

**Then**: 다음 조건을 모두 만족해야 합니다
- ✅ 최소 74개 테스트 통과 (68 + 6)
- ✅ 새로운 테스트 실패 0건
- ✅ 기존 68개 통과 테스트가 여전히 PASSED 상태
- ✅ ERROR 상태 테스트 없음
- ✅ 테스트 전체 실행 시간 < 5분

**성공 출력 예시**:
```
====== 74 passed, 14 failed in 180.45s ======
```

**검증 사항**:
- 통과 테스트 수 증가: 68 → 74 (6개 증가)
- 실패 테스트 수 감소: 20 → 14 (6개 감소)
- 전체 테스트 수 불변: 88개

---

### Scenario 4: CI 파이프라인 호환성

**Given**: 로컬 환경에서 모든 테스트가 통과했습니다
**And**: 수정 사항이 Git에 커밋되고 푸시되었습니다
**And**: CI 파이프라인이 자동으로 트리거되었습니다

**When**: GitHub Actions (또는 해당 CI 플랫폼)가 테스트를 실행합니다

**Then**: 다음 조건을 모두 만족해야 합니다
- ✅ CI 빌드 성공 (녹색 체크)
- ✅ 74개 이상의 테스트 통과
- ✅ 품질 게이트 충족 (커버리지, 린트 등)
- ✅ 타임아웃 없음
- ✅ 환경 변수 오류 없음

**검증 방법**:
- GitHub Actions 로그 확인
- CI 대시보드에서 빌드 상태 확인
- 이메일 알림 또는 Slack 알림 확인

**성공 지표**:
- Build Status: ✅ Passing
- Test Results: 74 passed, 14 failed
- Duration: < 5 minutes

---

### Scenario 5: Reflection API 테스트 개별 검증

**Given**: Reflection API 픽스처가 수정되었습니다
**And**: 각 테스트가 독립적으로 실행 가능합니다

**When**: 각 Reflection API 테스트를 개별적으로 실행합니다

**Then**: 다음 조건을 만족해야 합니다

#### Test 1: test_reflection_suggestions_authentication
```bash
pytest tests/integration/test_phase3_reflection.py::test_reflection_suggestions_authentication -v
```
- ✅ PASSED 상태
- ✅ 인증 관련 기능 정상 작동
- ✅ 예상 응답 형식 반환

#### Test 2: test_reflection_health_check
```bash
pytest tests/integration/test_phase3_reflection.py::test_reflection_health_check -v
```
- ✅ PASSED 상태
- ✅ Health check 엔드포인트 응답
- ✅ 시스템 상태 정보 포함

#### Test 3: test_reflection_analyze_performance
```bash
pytest tests/integration/test_phase3_reflection.py::test_reflection_analyze_performance -v
```
- ✅ PASSED 상태
- ✅ 성능 분석 결과 반환
- ✅ 메트릭 데이터 유효성 검증

#### Test 4: test_reflection_batch_performance
```bash
pytest tests/integration/test_phase3_reflection.py::test_reflection_batch_performance -v
```
- ✅ PASSED 상태
- ✅ 배치 처리 성공
- ✅ 배치 결과 집계 정확성

---

### Scenario 6: Hybrid Search 테스트 개별 검증

**Given**: Hybrid Search 인증 우회가 적용되었습니다
**And**: 각 테스트가 POST /search 엔드포인트를 호출합니다

**When**: 각 Hybrid Search 테스트를 개별적으로 실행합니다

**Then**: 다음 조건을 만족해야 합니다

#### Test 1: test_hybrid_search_bm25_only
```bash
pytest tests/integration/test_hybrid_search.py::test_hybrid_search_bm25_only -v
```
- ✅ PASSED 상태
- ✅ HTTP 200 응답
- ✅ BM25 알고리즘 결과 반환
- ✅ Neural reranking 없이 작동
- ✅ JSON 응답 스키마 검증

**예상 응답 구조**:
```json
{
  "results": [...],
  "algorithm": "bm25",
  "total": 10
}
```

#### Test 2: test_hybrid_search_with_neural
```bash
pytest tests/integration/test_hybrid_search.py::test_hybrid_search_with_neural -v
```
- ✅ PASSED 상태
- ✅ HTTP 200 응답
- ✅ Neural reranking 결과 포함
- ✅ 스코어 재정렬 확인
- ✅ JSON 응답 스키마 검증

**예상 응답 구조**:
```json
{
  "results": [...],
  "algorithm": "hybrid",
  "neural_reranking": true,
  "total": 10
}
```

---

### Scenario 7: 프로덕션 코드 무변경 확인

**Given**: Phase 1 수정이 완료되었습니다
**And**: 수정은 테스트 파일에만 적용되었습니다

**When**: Git diff를 확인합니다

**Then**: 다음 조건을 만족해야 합니다
- ✅ 변경 파일이 `tests/` 디렉토리에만 존재
- ✅ `backend/` 디렉토리의 프로덕션 코드 변경 없음
- ✅ API 엔드포인트 로직 변경 없음
- ✅ 인증 로직 변경 없음 (프로덕션)

**검증 명령**:
```bash
git diff --name-only
```

**예상 출력**:
```
tests/conftest.py
tests/integration/test_hybrid_search.py
```

**허용되지 않는 변경**:
```
❌ backend/app/main.py
❌ backend/app/dependencies.py
❌ backend/app/routers/*.py
```

---

### Scenario 8: 픽스처 이름 변경 부작용 없음

**Given**: `tests/conftest.py`의 픽스처 이름이 `api_client`에서 `async_client`로 변경되었습니다
**And**: 전체 코드베이스에서 영향 분석이 완료되었습니다

**When**: 전체 테스트 스위트를 실행합니다

**Then**: 다음 조건을 만족해야 합니다
- ✅ `api_client` 픽스처를 사용하던 다른 테스트 없음
- ✅ 또는 해당 테스트들도 `async_client`로 업데이트됨
- ✅ Fixture not found 오류 없음
- ✅ 모든 픽스처 주입 성공

**검증 명령**:
```bash
grep -r "api_client" tests/ --include="*.py" | grep -v conftest.py
```

**예상 출력**: 빈 결과 (또는 주석/문서에만 존재)

---

### Scenario 9: 인증 우회 격리 확인

**Given**: Hybrid Search 테스트에 인증 우회가 적용되었습니다
**And**: 프로덕션 환경에서는 인증이 필수입니다

**When**: 프로덕션 API 엔드포인트에 인증 없이 요청을 보냅니다

**Then**: 다음 조건을 만족해야 합니다
- ✅ 프로덕션 환경에서는 여전히 403 Forbidden 반환
- ✅ 테스트 환경에서만 인증 우회 작동
- ✅ 의존성 오버라이드는 테스트 코드에만 존재
- ✅ 프로덕션 보안 손상 없음

**검증 방법** (수동):
1. 프로덕션 또는 스테이징 환경에서 API 호출
2. X-API-Key 헤더 없이 요청
3. 403 Forbidden 응답 확인

---

### Scenario 10: 테스트 실행 시간 성능

**Given**: 6개 테스트가 수정되었습니다
**And**: 테스트 로직은 변경되지 않았습니다

**When**: 수정된 테스트들이 실행됩니다

**Then**: 다음 조건을 만족해야 합니다
- ✅ Reflection API 4개 테스트 총 실행 시간 < 10초
- ✅ Hybrid Search 2개 테스트 총 실행 시간 < 15초
- ✅ 테스트 실행 시간이 수정 전과 비슷함 (±10%)
- ✅ 타임아웃 없음
- ✅ 무한 루프나 데드락 없음

**성능 벤치마크**:
```bash
pytest tests/integration/test_phase3_reflection.py -v --durations=0
pytest tests/integration/test_hybrid_search.py -v --durations=0
```

**예상 결과**:
- 각 Reflection API 테스트: 1-3초
- 각 Hybrid Search 테스트: 3-7초

---

## QUALITY GATES

### 필수 품질 게이트

이 SPEC이 완료되려면 다음 모든 품질 게이트를 통과해야 합니다:

#### Gate 1: 테스트 통과율
- ✅ 최소 74개 테스트 통과
- ✅ 6개 대상 테스트 100% 통과
- ✅ 회귀 테스트 0건 실패

#### Gate 2: 코드 품질
- ✅ 린트 오류 없음 (flake8, pylint)
- ✅ 타입 체크 통과 (mypy, 있는 경우)
- ✅ 코딩 스타일 준수 (PEP 8)

#### Gate 3: 보안
- ✅ 프로덕션 인증 로직 무손상
- ✅ 테스트 API 키 하드코딩 없음 (환경 변수 사용)
- ✅ 민감 정보 노출 없음

#### Gate 4: 문서화
- ✅ 변경 사항 SPEC 문서에 반영
- ✅ 커밋 메시지 명확성 (what, why)
- ✅ PR 설명 완전성

---

## VERIFICATION CHECKLIST

### Phase 1: Reflection API Fixture Fix
- [ ] `tests/conftest.py` 픽스처 이름 `async_client`로 변경
- [ ] 전체 코드베이스에서 `api_client` 사용처 검색 완료
- [ ] 영향받는 다른 테스트 확인 및 수정 (있다면)
- [ ] `test_reflection_suggestions_authentication` PASSED
- [ ] `test_reflection_health_check` PASSED
- [ ] `test_reflection_analyze_performance` PASSED
- [ ] `test_reflection_batch_performance` PASSED

### Phase 2: Hybrid Search Authentication Fix
- [ ] 프로젝트의 인증 우회 패턴 확인 완료
- [ ] `test_hybrid_search_bm25_only` 인증 우회 적용
- [ ] `test_hybrid_search_with_neural` 인증 우회 적용
- [ ] 두 테스트 모두 200 OK 응답 수신
- [ ] 403 Forbidden 오류 제거 확인
- [ ] JSON 응답 검증 성공

### Phase 3: Comprehensive Verification
- [ ] 전체 테스트 스위트 실행 (`pytest -n 4`)
- [ ] 74개 이상 테스트 통과 확인
- [ ] 새로운 실패 0건 확인
- [ ] CI 파이프라인 통과 확인
- [ ] 프로덕션 코드 무변경 확인
- [ ] 테스트 실행 시간 정상 범위 확인

### Documentation & Git
- [ ] spec.md 작성 완료
- [ ] plan.md 작성 완료
- [ ] acceptance.md 작성 완료
- [ ] Git 커밋 메시지 작성 (영어)
- [ ] PR 생성 (있다면)

---

## DEFINITION OF DONE

이 SPEC은 다음 조건을 **모두** 만족할 때 완료된 것으로 간주됩니다:

### 기능 완성
1. ✅ Reflection API 4개 테스트 PASSED
2. ✅ Hybrid Search 2개 테스트 PASSED
3. ✅ 전체 테스트 스위트 74개 이상 통과

### 품질 보증
4. ✅ CI 파이프라인 통과
5. ✅ 회귀 테스트 0건
6. ✅ 린트 및 타입 체크 통과

### 보안 확인
7. ✅ 프로덕션 인증 로직 무손상
8. ✅ 테스트 환경 격리 유지

### 문서화
9. ✅ SPEC 3개 파일 작성 완료
10. ✅ 검증 결과 문서화

### Git & PR
11. ✅ 의미 있는 커밋 메시지 (영어)
12. ✅ PR 설명 완전성 (있다면)

---

## ACCEPTANCE SIGN-OFF

### 승인 프로세스

**검토자**: Alfred (MoAI-ADK)
**검토 항목**:
- [ ] 모든 승인 시나리오 통과
- [ ] 품질 게이트 충족
- [ ] Definition of Done 완료

**최종 승인 조건**:
```bash
# 다음 명령이 모두 성공해야 함
pytest -n 4 -v | grep "74 passed"
pytest tests/integration/test_phase3_reflection.py -v | grep "4 passed"
pytest tests/integration/test_hybrid_search.py::test_hybrid_search_bm25_only tests/integration/test_hybrid_search.py::test_hybrid_search_with_neural -v | grep "2 passed"
```

**승인 날짜**: (구현 완료 후 기록)
**승인자 서명**: (Alfred 또는 팀 리더)

---

**Acceptance Document End**
