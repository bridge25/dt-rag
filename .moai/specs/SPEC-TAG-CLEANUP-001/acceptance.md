# Acceptance Criteria: SPEC-TAG-CLEANUP-001

> **TAG 시스템 정리 Phase 1-2 검수 기준**
> **SPEC ID**: TAG-CLEANUP-001
> **Version**: 0.0.1
> **Date**: 2025-11-05

---

## 📋 Overview

이 문서는 TAG 시스템 정리 Phase 1-2 (Orphan @CODE TAG 76개 제거) 작업의 완료 기준을 정의합니다. 모든 시나리오는 **Given-When-Then** 형식으로 작성되며, 각 검수 항목은 자동 또는 수동으로 검증 가능합니다.

---

## 🎯 Acceptance Scenarios

### Scenario 1: @CODE:ID Placeholder 자동 교체

**Goal**: 210개 @CODE:ID placeholder를 실제 SPEC ID로 자동 교체

#### AC-1.1: Placeholder TAG 스캔

```gherkin
Given: 프로젝트 디렉토리에 @CODE:ID TAG가 210개 존재하는 상태
When: 자동 스캔 스크립트를 실행하면
  Command: rg '@CODE:ID' --no-filename | wc -l
Then: 출력 결과는 210이어야 함
And: 스캔 결과가 orphan_code_tags.txt에 저장되어야 함
```

**검증 방법**:
```bash
# 실행
rg '@CODE:ID' --no-filename | wc -l

# 예상 결과
210

# 파일 생성 확인
ls -la orphan_code_tags.txt
```

**Pass Criteria**:
- [ ] @CODE:ID 개수 = 210
- [ ] orphan_code_tags.txt 파일 생성됨

---

#### AC-1.2: Placeholder TAG 자동 교체

```gherkin
Given: orphan_code_tags.txt에 210개 @CODE:ID가 기록된 상태
When: 자동 교체 스크립트를 실행하면
  Command: python .moai/scripts/replace_placeholder_tags.py --dry-run
Then: Dry-run 모드에서 변경 사항이 미리 표시되어야 함
And: 실제 파일은 변경되지 않아야 함
```

**검증 방법**:
```bash
# Dry-run 실행
python .moai/scripts/replace_placeholder_tags.py --dry-run > dry_run_output.txt

# 변경 사항 확인
cat dry_run_output.txt

# 파일 변경 없음 확인
git status --short  # 빈 출력
```

**Pass Criteria**:
- [ ] Dry-run 출력에 210개 교체 대상 표시
- [ ] Git status가 clean 상태 유지

---

#### AC-1.3: Placeholder TAG 교체 검증

```gherkin
Given: Dry-run 검증이 완료된 상태
When: 자동 교체 스크립트를 실제 실행하면
  Command: python .moai/scripts/replace_placeholder_tags.py --execute
Then: 모든 @CODE:ID는 실제 SPEC ID로 교체되어야 함
And: 교체 후 @CODE:ID 개수는 0이어야 함
And: 모든 테스트는 통과해야 함
And: MyPy 타입 검증은 통과해야 함
```

**검증 방법**:
```bash
# 실제 실행
python .moai/scripts/replace_placeholder_tags.py --execute

# @CODE:ID 개수 확인
rg '@CODE:ID' --no-filename | wc -l  # 예상: 0

# 테스트 실행
pytest tests/ --tb=short

# MyPy 검증
mypy --config-file pyproject.toml .
```

**Pass Criteria**:
- [ ] @CODE:ID 개수 = 0 (210 → 0)
- [ ] 모든 테스트 통과 (77.8% 이상)
- [ ] MyPy 타입 오류 0개

---

### Scenario 2: @CODE:AUTH-001 예제 TAG 정리

**Goal**: 144개 @CODE:AUTH-001 TAG를 프로덕션/예제로 분류하고 적절히 처리

#### AC-2.1: 예제 TAG 파일 목록 생성

```gherkin
Given: 프로젝트에 @CODE:AUTH-001 TAG가 144개 존재하는 상태
When: 파일 목록 생성 명령을 실행하면
  Command: rg '@CODE:AUTH-001' -l > auth_001_files.txt
Then: auth_001_files.txt 파일이 생성되어야 함
And: 파일 목록에는 144개 TAG가 포함된 모든 파일이 나열되어야 함
```

**검증 방법**:
```bash
# 파일 목록 생성
rg '@CODE:AUTH-001' -l > auth_001_files.txt

# 파일 개수 확인
wc -l auth_001_files.txt

# 내용 확인
cat auth_001_files.txt
```

**Pass Criteria**:
- [ ] auth_001_files.txt 파일 생성됨
- [ ] 파일 목록에 @CODE:AUTH-001 포함 파일 모두 나열됨

---

#### AC-2.2: 프로덕션 코드 TAG 교체

```gherkin
Given: auth_001_files.txt에서 프로덕션 코드 파일을 식별한 상태
When: 프로덕션 코드의 TAG를 AUTH-002로 교체하면
  Command: sed -i 's/@CODE:AUTH-001/@CODE:AUTH-002/g' {production_file}
Then: 프로덕션 코드는 @CODE:AUTH-002를 사용해야 함
And: 예제 코드는 @CODE:AUTH-001을 유지해야 함 (이동 전)
```

**검증 방법**:
```bash
# 프로덕션 파일 TAG 교체 (예: apps/core/auth.py)
sed -i 's/@CODE:AUTH-001/@CODE:AUTH-002/g' apps/core/auth.py

# 교체 확인
rg '@CODE:AUTH-002' apps/core/auth.py

# 예제 파일은 그대로 유지
rg '@CODE:AUTH-001' examples/auth_example.py
```

**Pass Criteria**:
- [ ] 프로덕션 코드: @CODE:AUTH-001 → @CODE:AUTH-002 교체 완료
- [ ] 예제 코드: @CODE:AUTH-001 유지 (이동 전)

---

#### AC-2.3: 예제 코드 이동

```gherkin
Given: 예제 코드 파일을 식별한 상태
When: 예제 코드를 examples/ 디렉토리로 이동하면
  Command: mv {example_file} examples/
Then: 예제 파일은 examples/ 디렉토리에 존재해야 함
And: 원래 위치에는 파일이 없어야 함
And: Git 히스토리에 파일 이동이 기록되어야 함
```

**검증 방법**:
```bash
# 예제 파일 이동
mv docs/examples/auth_example.py examples/

# 이동 확인
ls examples/auth_example.py  # 존재
ls docs/examples/auth_example.py  # 없음

# Git 상태 확인
git status
# Renamed: docs/examples/auth_example.py -> examples/auth_example.py
```

**Pass Criteria**:
- [ ] 예제 파일이 examples/ 디렉토리에 존재
- [ ] 원래 위치에 파일 없음
- [ ] Git이 파일 이동을 "Renamed"로 인식

---

#### AC-2.4: 예제 TAG 정리 완료 검증

```gherkin
Given: 모든 @CODE:AUTH-001 TAG 처리가 완료된 상태
When: 정리 완료 검증을 실행하면
Then: 프로덕션 코드는 @CODE:AUTH-002만 사용해야 함
And: 예제 코드는 examples/ 디렉토리에만 존재해야 함
And: @CODE:AUTH-001 개수는 144개에서 0개로 감소해야 함 (프로덕션)
```

**검증 방법**:
```bash
# 프로덕션 코드에서 AUTH-001 제거 확인
rg '@CODE:AUTH-001' apps/ src/ | wc -l  # 예상: 0

# 예제 디렉토리에서만 AUTH-001 존재 확인
rg '@CODE:AUTH-001' examples/ -l

# AUTH-002 사용 확인
rg '@CODE:AUTH-002' apps/ src/ -l
```

**Pass Criteria**:
- [ ] 프로덕션 코드: @CODE:AUTH-001 = 0개
- [ ] 예제 코드: examples/ 디렉토리에만 존재
- [ ] 프로덕션 코드: @CODE:AUTH-002 사용 확인

---

### Scenario 3: @CODE:EXISTING 레거시 TAG 정리

**Goal**: 21개 @CODE:EXISTING TAG를 삭제하거나 새 SPEC 생성

#### AC-3.1: 레거시 TAG 파일 활성 상태 확인

```gherkin
Given: @CODE:EXISTING TAG가 21개 존재하는 상태
When: 각 파일의 최근 수정 날짜를 확인하면
  Command: git log -1 --format="%ci" -- {file}
Then: 최근 6개월 이내 수정된 파일은 "Active"로 분류되어야 함
And: 6개월 이상 수정 없는 파일은 "Inactive"로 분류되어야 함
```

**검증 방법**:
```bash
# 레거시 TAG 파일 목록
rg '@CODE:EXISTING' -l > existing_tags.txt

# 각 파일의 최근 수정 날짜 확인
while read file; do
  last_commit=$(git log -1 --format="%ci" -- "$file")
  echo "$file: $last_commit"
done < existing_tags.txt > existing_tags_status.txt

# 6개월 기준 분류
# Active: 2025-05-05 이후
# Inactive: 2025-05-05 이전
```

**Pass Criteria**:
- [ ] existing_tags.txt 생성됨 (21개 파일)
- [ ] existing_tags_status.txt에 각 파일의 최근 수정 날짜 기록
- [ ] Active/Inactive 분류 완료

---

#### AC-3.2: Active 코드 새 SPEC 생성

```gherkin
Given: Active 레거시 파일을 식별한 상태
When: 새 SPEC을 생성하면 (예: SPEC-LEGACY-001)
Then: .moai/specs/SPEC-LEGACY-001/ 디렉토리가 생성되어야 함
And: spec.md, plan.md, acceptance.md 파일이 생성되어야 함
And: @CODE:EXISTING TAG는 @CODE:LEGACY-001로 교체되어야 함
```

**검증 방법**:
```bash
# 새 SPEC 생성 (Alfred 또는 수동)
# /alfred:1-plan "Legacy feature documentation"

# SPEC 디렉토리 확인
ls -la .moai/specs/SPEC-LEGACY-001/

# TAG 교체
sed -i 's/@CODE:EXISTING/@CODE:LEGACY-001/g' {active_file}

# 교체 확인
rg '@CODE:LEGACY-001' {active_file}
```

**Pass Criteria**:
- [ ] SPEC-LEGACY-001 디렉토리 생성됨
- [ ] 3개 파일 (spec.md, plan.md, acceptance.md) 존재
- [ ] Active 파일: @CODE:EXISTING → @CODE:LEGACY-001 교체 완료

---

#### AC-3.3: Inactive 코드 TAG 제거

```gherkin
Given: Inactive 레거시 파일을 식별한 상태
When: TAG를 제거하거나 DEPRECATED 마킹을 하면
  Command: sed -i 's/@CODE:EXISTING/# DEPRECATED: @CODE:EXISTING/g' {inactive_file}
Then: Inactive 파일은 TAG가 제거되거나 DEPRECATED 마킹되어야 함
And: 코드 기능은 변경되지 않아야 함
```

**검증 방법**:
```bash
# TAG DEPRECATED 마킹
sed -i 's/@CODE:EXISTING/# DEPRECATED: @CODE:EXISTING/g' apps/legacy/old_module.py

# 변경 확인
rg 'DEPRECATED: @CODE:EXISTING' apps/legacy/old_module.py

# 테스트 통과 확인
pytest tests/
```

**Pass Criteria**:
- [ ] Inactive 파일: TAG 제거 또는 DEPRECATED 마킹 완료
- [ ] 코드 기능 변경 없음
- [ ] 모든 테스트 통과

---

### Scenario 4: TAG Health 개선 검증

**Goal**: Phase 1-2 완료 후 TAG Health가 F (43%) → D (65%)로 개선되었는지 검증

#### AC-4.1: Orphan TAG 제거 확인

```gherkin
Given: Phase 1-2 정리 작업이 완료된 상태
When: Orphan @CODE TAG 개수를 재스캔하면
  Command: python .moai/scripts/validate_tags.py --check-orphans --type CODE
Then: Orphan @CODE TAG 개수는 0이어야 함
And: 초기 76개에서 100% 감소해야 함
```

**검증 방법**:
```bash
# Orphan TAG 재스캔
python .moai/scripts/validate_tags.py --check-orphans --type CODE

# 예상 출력
# Orphan @CODE TAGs: 0
# Improvement: 76 → 0 (-100%)
```

**Pass Criteria**:
- [ ] Orphan @CODE TAG = 0개
- [ ] 개선율 = -100% (76 → 0)

---

#### AC-4.2: Primary Chain Integrity 개선

```gherkin
Given: TAG 정리 후 상태
When: Primary Chain 무결성을 재검증하면
  Command: python .moai/scripts/validate_tags.py --check-chains
Then: Primary Chain Integrity는 92%에서 95%+로 개선되어야 함
And: @SPEC → @CODE 연결률은 100%여야 함
```

**검증 방법**:
```bash
# Primary Chain 검증
python .moai/scripts/validate_tags.py --check-chains

# 예상 출력
# Primary Chain Integrity: 95.2%
# @SPEC → @CODE: 100%
# @CODE → @TEST: 92%
# @TEST → @DOC: 93%
```

**Pass Criteria**:
- [ ] Primary Chain Integrity ≥ 95%
- [ ] @SPEC → @CODE 연결률 = 100%

---

#### AC-4.3: TAG Health 등급 개선

```gherkin
Given: 모든 정리 작업이 완료된 상태
When: TAG Health 점수를 재계산하면
  Command: python .moai/scripts/validate_tags.py --health-score
Then: TAG Health 등급은 F (43%)에서 D (65%)로 개선되어야 함
And: 개선폭은 최소 +22%p 이상이어야 함
```

**검증 방법**:
```bash
# TAG Health 점수 계산
python .moai/scripts/validate_tags.py --health-score

# 예상 출력
# TAG Health Score: D (65%)
# Before: F (43%)
# Improvement: +22%p
```

**Pass Criteria**:
- [ ] TAG Health 등급 = D (65%) 이상
- [ ] 개선폭 ≥ +22%p

---

### Scenario 5: 코드 안정성 검증

**Goal**: TAG 정리 작업이 코드 기능, 테스트, 타입 안전성에 영향을 주지 않았는지 검증

#### AC-5.1: 테스트 통과율 유지

```gherkin
Given: TAG 정리 작업이 완료된 상태
When: 전체 테스트 스위트를 실행하면
  Command: pytest tests/ --cov --cov-report=term
Then: 모든 테스트는 통과해야 함
And: 테스트 통과율은 77.8% 이상 유지되어야 함
And: 커버리지는 감소하지 않아야 함
```

**검증 방법**:
```bash
# 전체 테스트 실행
pytest tests/ --cov --cov-report=term

# 예상 출력
# ===== 138 passed, 39 skipped in X.XXs =====
# Coverage: 77.8%
```

**Pass Criteria**:
- [ ] 모든 테스트 통과 (0 failed)
- [ ] 테스트 통과율 ≥ 77.8%
- [ ] 커버리지 유지 또는 증가

---

#### AC-5.2: MyPy 타입 안전성 유지

```gherkin
Given: TAG 정리 작업이 완료된 상태
When: MyPy 타입 검증을 실행하면
  Command: mypy --config-file pyproject.toml .
Then: MyPy 타입 오류는 0개여야 함
And: 타입 안전성 100%가 유지되어야 함
```

**검증 방법**:
```bash
# MyPy 타입 검증
mypy --config-file pyproject.toml .

# 예상 출력
# Success: no issues found in 77 source files
```

**Pass Criteria**:
- [ ] MyPy 오류 = 0개
- [ ] 타입 안전성 = 100%

---

#### AC-5.3: 코드 기능 변경 없음

```gherkin
Given: TAG 정리 전후 상태
When: Git diff를 확인하면
  Command: git diff HEAD~1 --stat
Then: 변경된 파일은 TAG 주석만 포함해야 함
And: 프로덕션 코드 로직은 변경되지 않아야 함
And: 함수 시그니처는 변경되지 않아야 함
```

**검증 방법**:
```bash
# Git diff 확인
git diff HEAD~1 --stat

# 변경 내용 검토
git diff HEAD~1 apps/ | grep '^[+-]' | grep -v '@CODE'

# 예상: TAG 주석만 변경, 코드 로직 변경 없음
```

**Pass Criteria**:
- [ ] 변경된 라인: TAG 주석만 포함
- [ ] 프로덕션 코드 로직 변경 없음
- [ ] 함수 시그니처 변경 없음

---

### Scenario 6: Git 추적성 검증

**Goal**: TAG 정리 작업이 Git 커밋으로 완전히 추적 가능한지 검증

#### AC-6.1: Git 커밋 생성

```gherkin
Given: TAG 정리 작업이 완료된 상태
When: Git 커밋을 생성하면
  Command: git commit -m "refactor(tags): Remove 76 orphan @CODE tags"
Then: 커밋 메시지에 @CODE:TAG-CLEANUP-001이 포함되어야 함
And: 커밋에는 변경된 파일 목록이 포함되어야 함
And: 커밋 히스토리에 정리 작업이 기록되어야 함
```

**검증 방법**:
```bash
# Git 커밋 생성
git add .
git commit -m "refactor(tags): Remove 76 orphan @CODE tags

- @CODE:ID placeholders: 210 → 0
- @CODE:AUTH-001 examples: 144 → 0 (moved to examples/)
- @CODE:EXISTING legacy: 21 → 0 (deprecated or new SPEC)

Impact:
- TAG Health: F (43%) → D (65%) (+22%p)
- Primary Chain: 92% → 95%+
- Tests: All passing (77.8%)
- MyPy: 100% type safety

@CODE:TAG-CLEANUP-001
"

# 커밋 확인
git log -1 --stat
```

**Pass Criteria**:
- [ ] 커밋 메시지에 @CODE:TAG-CLEANUP-001 포함
- [ ] 커밋에 변경된 파일 목록 포함
- [ ] Git log에 정리 작업 기록됨

---

#### AC-6.2: 체크포인트 브랜치 생성

```gherkin
Given: Git 커밋이 생성된 상태
When: 체크포인트 브랜치를 생성하면
  Command: git branch checkpoint/tag-cleanup-phase1-$(date +%Y%m%d)
Then: 체크포인트 브랜치가 생성되어야 함
And: 브랜치 이름에 날짜가 포함되어야 함
And: 브랜치는 현재 커밋을 가리켜야 함
```

**검증 방법**:
```bash
# 체크포인트 브랜치 생성
git branch checkpoint/tag-cleanup-phase1-$(date +%Y%m%d)

# 브랜치 확인
git branch -l checkpoint/tag-cleanup-phase1-*

# 예상 출력
# checkpoint/tag-cleanup-phase1-20251105
```

**Pass Criteria**:
- [ ] 체크포인트 브랜치 생성됨
- [ ] 브랜치 이름에 날짜 포함
- [ ] 브랜치가 최신 커밋을 가리킴

---

#### AC-6.3: 롤백 가능성 검증

```gherkin
Given: Git 커밋과 체크포인트 브랜치가 생성된 상태
When: 롤백 명령을 실행하면 (테스트 목적)
  Command: git checkout checkpoint/tag-cleanup-phase1-YYYYMMDD
Then: 정리 전 상태로 복원되어야 함
And: 모든 TAG 변경 사항은 취소되어야 함
And: 테스트는 다시 통과해야 함
```

**검증 방법**:
```bash
# 현재 브랜치 확인
git branch --show-current

# 체크포인트로 롤백 (테스트)
git checkout checkpoint/tag-cleanup-phase1-20251105

# TAG 상태 확인 (정리 전 상태로 복원됨)
rg '@CODE:ID' --no-filename | wc -l  # 예상: 210

# 원래 브랜치로 복귀
git checkout fix/ci-cd-workflow-syntax
```

**Pass Criteria**:
- [ ] 체크포인트로 롤백 성공
- [ ] TAG 정리 전 상태로 복원됨
- [ ] 원래 브랜치로 복귀 가능

---

### Scenario 7: 문서 동기화 검증

**Goal**: TAG 정리 작업 결과가 문서에 정확히 반영되었는지 검증

#### AC-7.1: sync-report 업데이트

```gherkin
Given: TAG 정리 작업이 완료된 상태
When: /alfred:3-sync를 실행하면
Then: sync-report-session17.md 파일이 생성되어야 함
And: TAG Health 개선 결과가 문서화되어야 함
And: Before/After 비교 표가 포함되어야 함
```

**검증 방법**:
```bash
# Sync 실행 (Alfred 또는 doc-syncer)
# /alfred:3-sync

# sync-report 확인
cat .moai/reports/sync-report-session17.md

# 예상 내용
# ## TAG Health Improvement
# - Before: F (43%)
# - After: D (65%)
# - Improvement: +22%p
```

**Pass Criteria**:
- [ ] sync-report-session17.md 생성됨
- [ ] TAG Health 개선 결과 문서화됨
- [ ] Before/After 비교 표 포함

---

#### AC-7.2: SPEC version 업데이트

```gherkin
Given: TAG 정리 작업이 완료된 상태
When: SPEC 문서 version을 업데이트하면
Then: spec.md의 version은 0.0.1 → 0.1.0으로 업데이트되어야 함
And: status는 draft → completed로 변경되어야 함
And: updated 필드는 최신 날짜로 업데이트되어야 함
```

**검증 방법**:
```bash
# SPEC version 확인
rg '^version:' .moai/specs/SPEC-TAG-CLEANUP-001/spec.md

# 예상 출력 (업데이트 후)
# version: 0.1.0

# Status 확인
rg '^status:' .moai/specs/SPEC-TAG-CLEANUP-001/spec.md

# 예상 출력
# status: completed
```

**Pass Criteria**:
- [ ] SPEC version = 0.1.0
- [ ] SPEC status = completed
- [ ] updated 필드 = 최신 날짜

---

#### AC-7.3: TAG 인덱스 재생성

```gherkin
Given: TAG 정리 작업이 완료된 상태
When: TAG 인덱스를 재생성하면
  Command: python .moai/scripts/rebuild_indexes.py --full-scan
Then: .moai/indexes/ 디렉토리에 새 인덱스가 생성되어야 함
And: 인덱스 정확도는 100%여야 함
And: TAG 검색 속도는 < 100ms여야 함
```

**검증 방법**:
```bash
# 인덱스 재생성
python .moai/scripts/rebuild_indexes.py --full-scan

# 인덱스 파일 확인
ls -la .moai/indexes/

# 예상 파일
# - tag_catalog.json
# - tag_chains.json
# - spec_to_code.json
# - code_to_test.json

# 인덱스 검증
python .moai/scripts/validate_indexes.py --check-all

# 성능 테스트
python .moai/scripts/benchmark_indexes.py
```

**Pass Criteria**:
- [ ] 인덱스 파일 재생성됨
- [ ] 인덱스 정확도 = 100%
- [ ] TAG 검색 속도 < 100ms

---

## ✅ Definition of Done (완료 기준)

### Must-Have (필수 조건)

- ✅ **Orphan @CODE TAGs**: 76개 → 0개 (-100%)
- ✅ **TAG Health Score**: F (43%) → D (65%) (+22%p)
- ✅ **Primary Chain Integrity**: 92% → 95%+
- ✅ **테스트 통과**: 모든 테스트 통과 (77.8% 이상)
- ✅ **타입 안전성**: MyPy 100% 유지
- ✅ **Git 추적성**: 모든 변경 사항 커밋으로 기록
- ✅ **롤백 가능**: 체크포인트 브랜치 생성 및 검증 완료

### Should-Have (권장 조건)

- ✅ **문서화**: sync-report-session17.md 생성
- ✅ **SPEC 업데이트**: version 0.0.1 → 0.1.0, status: completed
- ✅ **인덱스 재생성**: TAG 인덱스 100% 정확도
- ✅ **체크리스트**: 수동 검토 체크리스트 100% 완료

### Nice-to-Have (선택 조건)

- ⭐ **자동화 스크립트**: Placeholder TAG 자동 교체 스크립트 작동
- ⭐ **백업**: `.moai/backup/removed_tags.json`에 제거된 TAG 백업
- ⭐ **로그**: `.moai/logs/tag_changes.log`에 변경 사항 기록

---

## 📊 Verification Matrix (검증 매트릭스)

| Scenario | Acceptance Criteria | Verification Method | Status |
|----------|---------------------|---------------------|--------|
| **1. Placeholder TAG** | AC-1.1, AC-1.2, AC-1.3 | Automated (script + tests) | ⏳ Pending |
| **2. 예제 TAG** | AC-2.1, AC-2.2, AC-2.3, AC-2.4 | Manual + Automated | ⏳ Pending |
| **3. 레거시 TAG** | AC-3.1, AC-3.2, AC-3.3 | Manual + Automated | ⏳ Pending |
| **4. TAG Health** | AC-4.1, AC-4.2, AC-4.3 | Automated (script) | ⏳ Pending |
| **5. 코드 안정성** | AC-5.1, AC-5.2, AC-5.3 | Automated (tests + mypy) | ⏳ Pending |
| **6. Git 추적성** | AC-6.1, AC-6.2, AC-6.3 | Manual (git commands) | ⏳ Pending |
| **7. 문서 동기화** | AC-7.1, AC-7.2, AC-7.3 | Manual + Automated | ⏳ Pending |

**Status Legend**:
- ⏳ Pending: 작업 대기 중
- 🚧 In Progress: 작업 진행 중
- ✅ Passed: 검증 통과
- ❌ Failed: 검증 실패

---

## 🚀 Execution Checklist (실행 체크리스트)

### Phase 1-2 작업 순서

1. **준비 단계**
   - [ ] plan.md 확인 (5-phase 전략 이해)
   - [ ] 도구 확인 (ripgrep, git, python)
   - [ ] 백업 준비 (`.moai/backup/` 디렉토리)

2. **Placeholder TAG 정리**
   - [ ] AC-1.1: @CODE:ID 스캔
   - [ ] AC-1.2: Dry-run 실행
   - [ ] AC-1.3: 실제 교체 및 검증
   - [ ] Git commit (독립적)

3. **예제 TAG 정리**
   - [ ] AC-2.1: 파일 목록 생성
   - [ ] AC-2.2: 프로덕션 TAG 교체
   - [ ] AC-2.3: 예제 파일 이동
   - [ ] AC-2.4: 정리 완료 검증
   - [ ] Git commit (독립적)

4. **레거시 TAG 정리**
   - [ ] AC-3.1: 파일 활성 상태 확인
   - [ ] AC-3.2: Active 코드 SPEC 생성
   - [ ] AC-3.3: Inactive 코드 TAG 제거
   - [ ] Git commit (독립적)

5. **최종 검증**
   - [ ] AC-4.1, 4.2, 4.3: TAG Health 개선
   - [ ] AC-5.1, 5.2, 5.3: 코드 안정성
   - [ ] AC-6.1, 6.2, 6.3: Git 추적성
   - [ ] AC-7.1, 7.2, 7.3: 문서 동기화

6. **완료 단계**
   - [ ] 체크포인트 브랜치 생성
   - [ ] sync-report 작성
   - [ ] SPEC version 업데이트 (0.0.1 → 0.1.0)
   - [ ] TAG 인덱스 재생성

---

## 📖 References (참고 자료)

### 관련 문서
- `.moai/specs/SPEC-TAG-CLEANUP-001/spec.md`: 요구사항 명세서
- `.moai/specs/SPEC-TAG-CLEANUP-001/plan.md`: 5-phase 전략
- `CLAUDE-RULES.md`: TAG 명명 규칙 및 생명주기

### 검증 스크립트
- `.moai/scripts/validate_tags.py`: TAG 무결성 검증
- `.moai/scripts/rebuild_indexes.py`: TAG 인덱스 재생성
- `.moai/scripts/replace_placeholder_tags.py`: Placeholder TAG 자동 교체

### Git 명령어
```bash
# Git 커밋
git commit -m "refactor(tags): ..."

# 체크포인트 브랜치
git branch checkpoint/tag-cleanup-phase1-$(date +%Y%m%d)

# 롤백 (필요 시)
git checkout checkpoint/tag-cleanup-phase1-YYYYMMDD
```

---

**Document Created By**: spec-builder agent
**Document Date**: 2025-11-05
**Document Version**: 1.0
**Next Review**: After Phase 1-2 completion

---

**End of Acceptance Criteria**
