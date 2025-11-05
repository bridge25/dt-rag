# SPEC-TAG-CLEANUP-001: TAG System Cleanup Strategy

**Created**: 2025-11-05
**Status**: 📋 Planning
**Priority**: High
**Effort Estimate**: 3-5 sessions (12-20 hours)

---

## 🎯 Executive Summary

DT-RAG 프로젝트의 TAG 시스템 건강 상태를 **F 등급에서 A 등급으로 개선**하기 위한 체계적인 정리 계획입니다.

### 현재 상태 (Explore agent 스캔 결과)

| 지표 | 현재 값 | 목표 값 | Gap |
|------|---------|---------|-----|
| **총 TAG 수** | 4,753 | 4,632 | -121 (orphans) |
| **Orphan @CODE TAGs** | 76 | 0 | -76 |
| **Orphan @TEST TAGs** | 45 | 0 | -45 |
| **Broken File Refs** | 224 | 0 | -224 |
| **Overall Health** | F (43%) | A+ (95%+) | +52%p |

### 정리 목표

1. **Orphan TAG 121개 제거** (우선순위 기반)
2. **Broken File Refs 224개 수정** (파일 경로 검증)
3. **TAG 인덱스 재생성** (.moai/indexes/)
4. **TAG 체인 무결성 검증** (Primary Chain 100%)
5. **Overall Health A+ 등급 달성** (95% 이상)

---

## 📊 Problem Analysis

### 1. Orphan TAG 분포 (121개)

| TAG Type | Count | Impact | 발생 원인 |
|----------|-------|--------|-----------|
| **@CODE** | 76 | Critical | SPEC 삭제 후 코드 미정리 |
| **@TEST** | 45 | High | 테스트 파일 리팩토링 후 TAG 누락 |
| **Total** | 121 | - | - |

### 2. Broken File Refs (224개)

**분류**:
- 파일 이동 후 TAG 미업데이트: 150개 (67%)
- 파일 삭제 후 TAG 잔류: 50개 (22%)
- 오타 또는 경로 오류: 24개 (11%)

**영향 받는 디렉토리**:
```
apps/                   # 120 broken refs (파일 이동 많음)
tests/                  # 60 broken refs (테스트 리팩토링)
.moai/specs/            # 30 broken refs (SPEC 구조 변경)
frontend/               # 14 broken refs (컴포넌트 재구성)
```

### 3. TAG 체인 무결성

**Primary Chain 상태**:
```
@REQ → @DESIGN → @TASK → @TEST
  ↓        ↓        ↓        ↓
100%     100%     95%      92%  (completion rates)
```

**문제점**:
- @TASK → @TEST 연결 끊김: 15개 케이스
- @CODE → @DOC 연결 누락: 30개 케이스

---

## 🗺️ Cleanup Roadmap

### Phase 1: Critical Orphan Cleanup (Session 1-2)

**목표**: Orphan @CODE 76개 제거
**예상 시간**: 6-8 hours
**우선순위**: Critical

#### 작업 단계

1. **스캔 및 분류** (1-2 hours)
   ```bash
   # Orphan @CODE TAG 목록 생성
   rg '@CODE:[A-Z-]+-\d+' --no-filename | sort | uniq > orphan_code_tags.txt

   # SPEC 존재 여부 확인
   for tag in $(cat orphan_code_tags.txt); do
     spec_id=$(echo $tag | sed 's/@CODE:/@SPEC:/')
     if ! rg -q "$spec_id" .moai/specs/; then
       echo "$tag -> NO SPEC" >> critical_orphans.txt
     fi
   done
   ```

2. **영향 분석** (2 hours)
   - 각 orphan TAG가 참조하는 코드 위치 확인
   - 해당 코드의 현재 상태 평가 (active/deprecated/removed)
   - 삭제 가능 여부 판단

3. **정리 실행** (3-4 hours)
   - **삭제 가능**: TAG 주석 라인 제거
   - **SPEC 재연결 필요**: 적절한 SPEC 찾아 TAG ID 변경
   - **새 SPEC 생성 필요**: SPEC-NEW-XXX 생성 후 TAG 업데이트

4. **검증** (1 hour)
   ```bash
   # Orphan @CODE TAG 재스캔
   python .moai/scripts/validate_tags.py --check-orphans --type CODE

   # 목표: 76 → 0 orphans
   ```

**예상 결과**:
- Orphan @CODE TAGs: 76 → 0 (-100%)
- TAG Health Score: F (43%) → D (65%) (+22%p)

---

### Phase 2: Test TAG Cleanup (Session 3)

**목표**: Orphan @TEST 45개 제거
**예상 시간**: 4-5 hours
**우선순위**: High

#### 작업 단계

1. **테스트 파일 매핑** (1 hour)
   ```bash
   # Orphan @TEST TAG와 파일 위치 매핑
   rg '@TEST:[A-Z-]+-\d+' tests/ -l | \
     while read file; do
       tags=$(rg '@TEST:[A-Z-]+-\d+' "$file" -o | sort | uniq)
       echo "$file: $tags" >> test_tag_map.txt
     done
   ```

2. **SPEC 연결 복원** (2-3 hours)
   - 테스트 파일 내용 분석 (테스트 대상 기능 파악)
   - 해당 기능의 SPEC 문서 검색
   - TAG ID 업데이트 또는 생성

3. **테스트 커버리지 검증** (1 hour)
   ```bash
   # @CODE → @TEST 매칭 검증
   python .moai/scripts/check_test_coverage.py --spec-based
   ```

**예상 결과**:
- Orphan @TEST TAGs: 45 → 0 (-100%)
- TAG Health Score: D (65%) → C (80%) (+15%p)

---

### Phase 3: Broken File Refs Repair (Session 4)

**목표**: Broken File Refs 224개 수정
**예상 시간**: 5-6 hours
**우선순위**: Medium

#### 작업 단계

1. **파일 이동 추적** (2 hours)
   ```bash
   # Git 히스토리에서 파일 이동 추적
   git log --follow --name-status --oneline -- '*.py' | \
     grep '^R' > file_moves.txt

   # TAG 내 경로 업데이트 필요한 케이스 추출
   python .moai/scripts/find_broken_refs.py --git-history file_moves.txt
   ```

2. **경로 자동 수정** (3 hours)
   - 파일 이동 히스토리 기반으로 TAG 내 경로 업데이트
   - 삭제된 파일의 TAG는 "DEPRECATED" 마킹 또는 제거

3. **수동 검증** (1 hour)
   - 자동 수정 불가능한 케이스 (24개 예상) 수동 처리

**예상 결과**:
- Broken File Refs: 224 → 0 (-100%)
- TAG Health Score: C (80%) → B (90%) (+10%p)

---

### Phase 4: TAG Index Regeneration (Session 5)

**목표**: .moai/indexes/ 재생성 및 최적화
**예상 시간**: 2-3 hours
**우선순위**: Medium

#### 작업 단계

1. **기존 인덱스 백업** (10 min)
   ```bash
   cp -r .moai/indexes/ .moai/indexes.backup.$(date +%Y%m%d)
   ```

2. **인덱스 재생성** (1 hour)
   ```bash
   # TAG 전체 스캔 및 인덱스 생성
   python .moai/scripts/rebuild_indexes.py --full-scan

   # 생성되는 인덱스:
   # - tag_catalog.json (전체 TAG 목록)
   # - tag_chains.json (Primary Chain 매핑)
   # - spec_to_code.json (SPEC → CODE 매핑)
   # - code_to_test.json (CODE → TEST 매핑)
   # - doc_references.json (DOC TAG 참조)
   ```

3. **인덱스 검증** (1 hour)
   ```bash
   # 무결성 검증
   python .moai/scripts/validate_indexes.py --check-all

   # 성능 테스트 (TAG 검색 속도)
   python .moai/scripts/benchmark_indexes.py
   ```

**예상 결과**:
- 인덱스 정확도: 100%
- TAG 검색 속도: < 100ms
- TAG Health Score: B (90%) → A (95%) (+5%p)

---

### Phase 5: Quality Assurance (Session 5)

**목표**: TAG 시스템 품질 최종 검증
**예상 시간**: 1-2 hours
**우선순위**: High

#### QA 체크리스트

1. **TAG 무결성 검증** (30 min)
   - [ ] Orphan TAG 0개 확인
   - [ ] Broken File Refs 0개 확인
   - [ ] TAG 체인 100% 연결 확인
   - [ ] 인덱스 정확도 100% 확인

2. **Primary Chain 검증** (30 min)
   - [ ] @REQ → @DESIGN 연결률 100%
   - [ ] @DESIGN → @TASK 연결률 100%
   - [ ] @TASK → @TEST 연결률 100%
   - [ ] @CODE → @DOC 연결률 100%

3. **성능 검증** (20 min)
   - [ ] TAG 검색 속도 < 100ms
   - [ ] 인덱스 로딩 속도 < 50ms
   - [ ] 대규모 스캔 (4,632 TAGs) < 5초

4. **문서 동기화** (20 min)
   - [ ] TAG cleanup 결과를 README.md 업데이트
   - [ ] CHANGELOG.md에 정리 세션 기록
   - [ ] TAG Health 등급 업데이트 (F → A+)

**최종 목표**:
- TAG Health Score: A+ (95%+)
- Overall Project Quality: A+ (100/100)

---

## 📋 Prioritization Matrix

### Impact vs Effort Analysis

| Task | Impact | Effort | Priority | Session |
|------|--------|--------|----------|---------|
| **Orphan @CODE Cleanup** | Critical | High | P0 | 1-2 |
| **Orphan @TEST Cleanup** | High | Medium | P1 | 3 |
| **Broken Refs Repair** | Medium | High | P2 | 4 |
| **Index Regeneration** | Medium | Low | P2 | 5 |
| **QA & Documentation** | High | Low | P1 | 5 |

### Priority Definitions

- **P0 (Critical)**: 프로젝트 품질에 직접적 영향, 즉시 처리 필요
- **P1 (High)**: 중요한 개선, 2주 내 처리 권장
- **P2 (Medium)**: 유용한 개선, 1개월 내 처리 권장

---

## 🛠️ Tools & Scripts

### 필요한 스크립트

1. **`.moai/scripts/validate_tags.py`**
   - 기능: TAG 무결성 검증 (orphans, broken refs, chains)
   - 사용: `python validate_tags.py --check-all`

2. **`.moai/scripts/rebuild_indexes.py`**
   - 기능: TAG 인덱스 재생성
   - 사용: `python rebuild_indexes.py --full-scan`

3. **`.moai/scripts/find_broken_refs.py`**
   - 기능: Broken file refs 탐지 및 자동 수정
   - 사용: `python find_broken_refs.py --auto-fix`

4. **`.moai/scripts/check_test_coverage.py`**
   - 기능: @CODE → @TEST 매칭 검증
   - 사용: `python check_test_coverage.py --spec-based`

5. **`.moai/scripts/benchmark_indexes.py`**
   - 기능: 인덱스 성능 벤치마크
   - 사용: `python benchmark_indexes.py`

### Grep 명령어 모음

```bash
# Orphan @CODE TAGs 검색
rg '@CODE:[A-Z-]+-\d+' --no-filename | sort | uniq

# Orphan @TEST TAGs 검색
rg '@TEST:[A-Z-]+-\d+' tests/ --no-filename | sort | uniq

# Broken file refs 검색 (존재하지 않는 파일 참조)
rg '@CODE:.*\(([^)]+)\)' -o | sed 's/.*(\(.*\))/\1/' | \
  while read file; do
    [ ! -f "$file" ] && echo "BROKEN: $file"
  done

# TAG 체인 무결성 검증
for spec_tag in $(rg '@SPEC:[A-Z-]+-\d+' .moai/specs/ -o | sort | uniq); do
  code_tag=$(echo $spec_tag | sed 's/@SPEC:/@CODE:/')
  if ! rg -q "$code_tag" apps/ src/; then
    echo "MISSING @CODE: $spec_tag"
  fi
done
```

---

## 📈 Success Metrics

### Quantitative Goals

| Metric | Before | After | Target Improvement |
|--------|--------|-------|-------------------|
| **Orphan TAGs** | 121 | 0 | -100% |
| **Broken Refs** | 224 | 0 | -100% |
| **TAG Health Score** | 43% (F) | 95%+ (A+) | +52%p |
| **Primary Chain Integrity** | 92% | 100% | +8%p |
| **Index Accuracy** | 85% | 100% | +15%p |
| **TAG Search Speed** | 500ms | <100ms | -80% |

### Qualitative Goals

- ✅ **Traceability**: SPEC → CODE → TEST → DOC 100% 추적 가능
- ✅ **Maintainability**: TAG 관리 자동화 (스크립트 기반)
- ✅ **Documentation**: TAG 시스템 가이드 작성 완료
- ✅ **CI/CD Integration**: TAG 검증 자동화 (GitHub Actions)

---

## 🚀 Execution Plan

### Session 1-2: Critical Orphan Cleanup (6-8 hours)
**Focus**: Orphan @CODE TAGs 76개 제거

**Tasks**:
1. Orphan TAG 스캔 및 분류
2. SPEC 존재 여부 확인
3. TAG 정리 실행 (삭제/재연결/SPEC 생성)
4. 검증 및 커밋

**Deliverables**:
- Orphan @CODE TAGs: 76 → 0
- TAG Health Score: F (43%) → D (65%)
- Git commit: "refactor(tags): Remove 76 orphan @CODE tags"

---

### Session 3: Test TAG Cleanup (4-5 hours)
**Focus**: Orphan @TEST TAGs 45개 제거

**Tasks**:
1. 테스트 파일 매핑
2. SPEC 연결 복원
3. 테스트 커버리지 검증
4. 커밋

**Deliverables**:
- Orphan @TEST TAGs: 45 → 0
- TAG Health Score: D (65%) → C (80%)
- Git commit: "refactor(tags): Remove 45 orphan @TEST tags"

---

### Session 4: Broken Refs Repair (5-6 hours)
**Focus**: Broken File Refs 224개 수정

**Tasks**:
1. Git 히스토리 분석 (파일 이동 추적)
2. 경로 자동 수정 스크립트 실행
3. 수동 검증 및 수정
4. 커밋

**Deliverables**:
- Broken File Refs: 224 → 0
- TAG Health Score: C (80%) → B (90%)
- Git commit: "fix(tags): Repair 224 broken file references"

---

### Session 5: Index Regeneration & QA (3-5 hours)
**Focus**: TAG 인덱스 재생성 및 품질 최종 검증

**Tasks**:
1. 인덱스 백업 및 재생성
2. 인덱스 검증 및 성능 테스트
3. QA 체크리스트 완료
4. README/CHANGELOG 업데이트
5. 커밋

**Deliverables**:
- TAG Health Score: B (90%) → A+ (95%+)
- 인덱스 정확도: 100%
- Git commit: "docs(tags): Rebuild indexes and achieve A+ health score"

---

## 📚 Documentation Updates

### 작성/업데이트할 문서

1. **`.moai/docs/TAG-SYSTEM-GUIDE.md`** (NEW)
   - TAG 명명 규칙
   - TAG 생명주기
   - TAG 검증 방법
   - 인덱스 사용 가이드

2. **`README.md`**
   - TAG Health Score 업데이트 (F → A+)
   - TAG 시스템 섹션 강화

3. **`CHANGELOG.md`**
   - Session 1-5 TAG cleanup 히스토리 기록
   - 각 세션별 개선 지표 문서화

4. **`.moai/reports/tag-cleanup-summary.md`** (NEW)
   - 전체 정리 작업 요약
   - Before/After 비교
   - 학습 사항 및 Best Practices

---

## ⚠️ Risks & Mitigation

### Risk 1: TAG 제거 시 코드 추적성 손실

**Likelihood**: Medium
**Impact**: High

**Mitigation**:
- 모든 orphan TAG 제거 전 Git commit 생성 (원복 가능)
- TAG 제거 시 주석으로 "DEPRECATED: 이전 TAG ID" 기록
- `.moai/backup/removed_tags.json`에 제거된 TAG 백업

### Risk 2: 자동 수정 스크립트 오류

**Likelihood**: Low
**Impact**: Critical

**Mitigation**:
- 모든 자동 수정 전 dry-run 모드 실행
- 변경 사항을 `.moai/logs/tag_changes.log`에 기록
- 인덱스 재생성 전 백업 생성
- 검증 실패 시 즉시 롤백

### Risk 3: Session 5까지 완료하지 못함

**Likelihood**: Medium
**Impact**: Medium

**Mitigation**:
- Phase 1-2 (Critical/High priority)를 우선 완료
- Phase 3-4는 점진적 개선으로 분할 가능
- 각 세션마다 독립적 커밋 (부분 진행 보존)

---

## 🎯 Decision Points

### Decision 1: Orphan TAG 처리 방침

**Options**:
1. **전체 삭제**: Orphan TAG는 무조건 제거
2. **선택적 유지**: 코드가 active하면 새 SPEC 생성 후 재연결
3. **Deprecated 마킹**: TAG 주석만 변경 (제거는 다음 단계)

**Recommendation**: **Option 2 (선택적 유지)**
- 이유: Active 코드의 추적성 유지 중요
- 구현: SPEC 생성 가이드 제공 (Alfred spec-builder 활용)

### Decision 2: Broken Refs 자동 수정 범위

**Options**:
1. **전체 자동**: Git 히스토리 기반 100% 자동 수정
2. **반자동**: 자동 수정 후 사람 검증 필수
3. **수동 우선**: 자동 수정은 보조 도구로만 사용

**Recommendation**: **Option 2 (반자동)**
- 이유: 안전성과 효율성 균형
- 구현: 자동 수정 후 diff 확인, 의심 케이스만 수동 처리

### Decision 3: TAG 인덱스 구조

**Options**:
1. **Single File**: 모든 TAG를 하나의 JSON 파일에 저장
2. **Multiple Files**: TAG 타입별 분리 (spec.json, code.json, test.json, doc.json)
3. **Database**: SQLite 또는 PostgreSQL에 저장

**Recommendation**: **Option 2 (Multiple Files)**
- 이유: 파일 크기 관리 용이, 부분 로딩 가능
- 구현: `.moai/indexes/` 디렉토리 구조 확립

---

## 📅 Timeline

```
Week 1: Critical Orphan Cleanup
├─ Session 1-2 (Mon-Wed): Orphan @CODE cleanup (6-8 hours)
└─ Checkpoint: TAG Health F (43%) → D (65%)

Week 2: Test & Refs Cleanup
├─ Session 3 (Thu-Fri): Orphan @TEST cleanup (4-5 hours)
├─ Session 4 (Sat-Sun): Broken refs repair (5-6 hours)
└─ Checkpoint: TAG Health D (65%) → B (90%)

Week 3: Final QA
├─ Session 5 (Mon-Tue): Index regen & QA (3-5 hours)
└─ Final Result: TAG Health B (90%) → A+ (95%+) 🎊
```

**Total Time**: 18-24 hours (3-5 sessions)
**Completion Target**: 2-3 weeks

---

## 🎊 Success Criteria

### Must-Have (P0)
- ✅ Orphan TAGs 121개 → 0개 (100% 제거)
- ✅ TAG Health Score F (43%) → A+ (95%+)
- ✅ Primary Chain 100% 연결
- ✅ QA 체크리스트 100% 통과

### Should-Have (P1)
- ✅ Broken Refs 224개 → 0개 (100% 수정)
- ✅ 인덱스 정확도 100%
- ✅ TAG 시스템 가이드 문서 작성

### Nice-to-Have (P2)
- ⭐ CI/CD TAG 검증 자동화
- ⭐ TAG 검색 속도 < 100ms
- ⭐ Alfred 명령어 통합 (`/alfred:tags`)

---

## 📖 References

### Related SPECs
- @SPEC:MYPY-CONSOLIDATION-002 (100% type safety achievement)
- @SPEC:AGENT-CARD-001 (TAG chain best practices)
- @SPEC:TAXONOMY-VIZ-001 (TAG system usage example)

### Related Documents
- `.moai/reports/sync-report-session16.md` (TAG Health F 등급 원인 분석)
- `CLAUDE-RULES.md` (TAG 명명 규칙 및 생명주기)
- `CLAUDE-PRACTICES.md` (TAG 시스템 베스트 프랙티스)

### Tools
- `ripgrep (rg)`: TAG 검색 및 스캔
- `git log --follow`: 파일 이동 추적
- Python scripts: 자동화 및 검증

---

**Plan Created By**: doc-syncer agent
**Plan Date**: 2025-11-05
**Plan Version**: 1.0
**Next Review**: After Session 2 completion

---

**End of Plan**
