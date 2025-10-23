# SPEC-TEST-001 문서 동기화 계획 - 요약본

**작성일**: 2025-10-22
**상태**: 사용자 승인 대기
**총 소요 시간**: 약 35분

---

## 한눈에 보기

### 현재 상황
```
TEST-001 작업 완료 ✅
  ├─ 32개 테스트 구현 완료
  ├─ 커버리지 47% → 85% 달성
  ├─ 모든 성능 요구사항 충족
  └─ 7개 파일 변경 (865줄)

BUT: 문서-코드 연결 불완전 ⚠️
  ├─ TAG 무결성: 70% (4개 라우터에 @CODE TAG 누락)
  ├─ README 미동기화 (Testing 섹션 미업데이트)
  └─ SPEC 상태 미변경 (draft → completed)
```

---

## 동기화 계획의 4가지 Phase

### Phase 1: @CODE TAG 추가 (4개 라우터)

누락된 코드 추적성 TAG를 4개 라우터에 추가합니다.

```
apps/api/routers/
├── classify.py    ← @CODE:TEST-001:TAG-001 추가
├── search.py      ← @CODE:TEST-001:TAG-002 추가
├── taxonomy.py    ← @CODE:TEST-001:TAG-003 추가
└── health.py      ← @CODE:TEST-001:TAG-004 추가
```

**효과**:
- TEST → CODE 체인 완성
- 모든 엔드포인트가 추적 가능해짐

---

### Phase 2: SPEC 파일 업데이트

SPEC 파일을 최종 상태로 변경합니다.

```yaml
# 변경 사항:
status:    draft      → completed
version:   0.0.1      → 0.1.0
updated:   2025-10-22 (변경 없음)
completed_date: 2025-10-22 (신규)

# HISTORY에 v0.1.0 완료 항목 추가
```

**효과**:
- 작업 완료 공식화
- 버전 관리 체계 확립

---

### Phase 3: README Living Document 동기화

README.md의 Testing 섹션을 최신 상태로 갱신합니다.

```markdown
# 변경 전:
- **Overall Coverage**: 47%
- **Integration Tests**: test_database_integration, test_ml_classifier
- 마지막 업데이트: (구 정보)

# 변경 후:
- **Overall Coverage**: 85% ⬆️
- **Integration Tests**:
  - test_api_endpoints.py (NEW) ⭐
    - /classify: 8 tests
    - /search: 10 tests
    - /taxonomy: 8 tests
    - /healthz: 6 tests
  - test_database_integration
  - test_ml_classifier
- 마지막 업데이트: 2025-10-22
```

**효과**:
- CODE → DOC 체인 완성
- 사용자 대면 문서 최신화

---

### Phase 4: 동기화 보고서 생성

`.moai/reports/sync-report.md`에 완료 보고서를 생성합니다.

**포함 내용**:
- 변경 통계 (7개 파일, 865줄)
- TAG 무결성 개선 (70% → 100%)
- 커버리지 개선 통계
- 성공 기준 검증 결과
- 다음 단계 제안

---

## 핵심 개선 사항

### TAG 무결성 개선 (70% → 100%)

```
Before (70%):
  ✅ SPEC → TEST: @SPEC:TEST-001 → @TEST:TEST-001
  ⚠️  TEST → CODE: classify, search, taxonomy, health에 TAG 없음
  ❌ CODE → DOC: README 미동기화

After (100%):
  ✅ SPEC → TEST: @SPEC:TEST-001 → @TEST:TEST-001
  ✅ TEST → CODE: 모든 라우터에 @CODE:TEST-001:TAG-* 추가
  ✅ CODE → DOC: README Testing 섹션 업데이트 완료
```

### 커버리지 개선 (47% → 85%)

| 항목 | Before | After | 증가 |
|------|--------|-------|------|
| 전체 테스트 | 47% | 85% | +38% |
| API 엔드포인트 | 16개 | 32개 | +16개 |
| /classify | 4개 | 8개 | +4개 |
| /search | 4개 | 10개 | +6개 |
| /taxonomy | 4개 | 8개 | +4개 |
| /healthz | 4개 | 6개 | +2개 |

---

## 실행 체크리스트

진행 전 확인사항:

```
사전 확인
  ☐ feature/SPEC-TEST-001 브랜치가 최신 상태?
  ☐ pytest tests/ -v 모두 통과?
  ☐ 커버리지가 85% 이상?

Phase 1: @CODE TAG 추가 (~10분)
  ☐ classify.py에 @CODE:TEST-001:TAG-001 추가
  ☐ search.py에 @CODE:TEST-001:TAG-002 추가
  ☐ taxonomy.py에 @CODE:TEST-001:TAG-003 추가
  ☐ health.py에 @CODE:TEST-001:TAG-004 추가
  ☐ TAG 검증: rg "@CODE:TEST-001" -n apps/api/routers/

Phase 2: SPEC 업데이트 (~5분)
  ☐ status: draft → completed
  ☐ version: 0.0.1 → 0.1.0
  ☐ HISTORY v0.1.0 항목 추가

Phase 3: README 동기화 (~10분)
  ☐ Testing 섹션 커버리지 수치 업데이트 (47% → 85%)
  ☐ Integration Tests에 test_api_endpoints.py 추가
  ☐ 마지막 업데이트 날짜 변경
  ☐ Completed Milestones 업데이트

Phase 4: 보고서 생성 (~5분)
  ☐ .moai/reports/sync-report.md 생성
  ☐ 변경 통계 기록
  ☐ TAG 무결성 개선 결과 기록

검증 및 완료 (~5분)
  ☐ 모든 TAG 체인 검증
  ☐ README 마크다운 형식 확인
  ☐ SPEC 파일 YAML 유효성 검증
```

---

## 승인 필요 항목

다음 3가지에 대해 사용자 승인이 필요합니다:

### 1️⃣ 계획 범위 확인
```
질문: 위 4가지 Phase를 모두 진행하기를 원하십니까?

선택지:
  A) 예, 모든 Phase를 진행해주세요
  B) 일부만 진행해주세요 (제외 Phase 명시)
  C) 수정 후 재검토 필요
```

### 2️⃣ SPEC 상태 변경 확인
```
질문: SPEC-TEST-001을 v0.1.0으로 완료 표시하기를 원하십니까?

선택지:
  A) 예, 상태를 completed로 변경해주세요
  B) 아니오, draft로 유지해주세요
```

### 3️⃣ Git 브랜치 전략
```
질문: feature/SPEC-TEST-001 브랜치를 어떻게 처리하시겠습니까?
(personal 모드이므로 PR은 없음)

선택지:
  A) main에 병합하고 브랜치 삭제
  B) 브랜치 유지만 하고 추후 결정
  C) 아직 병합하지 말아주세요
```

---

## 예상 결과

동기화 완료 후:

```
✅ 완성된 문서-코드 추적성
   SPEC → TEST → CODE → DOC → GIT (모든 단계 연결)

✅ 100% TAG 무결성
   - 4개 라우터 모두 @CODE TAG 포함
   - README에 테스트 명시
   - SPEC 상태 completed로 변경

✅ 사용자 대면 문서 최신화
   - README Testing 섹션 85% 커버리지 명시
   - 32개 API 테스트 목록 기록
   - 마지막 업데이트 2025-10-22로 갱신

✅ 공식 완료 보고서 작성
   - sync-report.md에 변경 통계 기록
   - 성공 기준 검증 결과 저장
   - 다음 단계 제안서 작성
```

---

## 다음 단계 (선택사항)

동기화 완료 후 선택 가능한 항목:

```
즉시 가능:
  1. main에 병합 (feature/SPEC-TEST-001 → main)
  2. v0.1.0 릴리스 공식화
  3. 테스트 성능 프로파일링

장기 계획:
  1. E2E 테스트 추가
  2. 부하 테스트 통합
  3. SPEC-TEST-002 (고급 성능 테스트) 계획
```

---

## 파일 위치

계획 및 보고서 파일:

```
.moai/
├── plans/
│   └── SPEC-TEST-001-SYNC-PLAN.md      ← 상세 계획서 (이 파일)
└── reports/
    ├── sync-report.md                   ← 동기화 보고서 (생성 예정)
    └── SYNC-PLAN-SUMMARY.md             ← 요약본 (현재 파일)
```

---

## 연락처 및 지원

계획 상세 내용:
- `.moai/plans/SPEC-TEST-001-SYNC-PLAN.md` 참조
- 4가지 Phase 상세 설명
- 리스크 및 완화 전략
- TAG 검증 스크립트

---

**준비 완료**: 사용자 승인을 기다리고 있습니다.
**문의사항**: 위 3가지 승인 항목에 답변해주시기 바랍니다.

