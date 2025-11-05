---
id: TAG-CLEANUP-001
version: 0.0.1
status: draft
created: 2025-11-05
updated: 2025-11-05
author: @bridge25
priority: high
category: quality
labels: [technical-debt, tag-system, traceability]
scope:
  packages:
    - apps/
    - tests/
    - .moai/specs/
  files:
    - .moai/scripts/validate_tags.py
    - .moai/scripts/rebuild_indexes.py
depends_on: []
blocks: []
related_specs: []
---

# SPEC-TAG-CLEANUP-001: TAG 시스템 정리 Phase 1-2

## 📋 HISTORY

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| v0.0.1 | 2025-11-05 | @bridge25 | INITIAL - TAG Health F → A+ 개선을 위한 Phase 1-2 SPEC 생성 |

### 목적

DT-RAG 프로젝트의 TAG 시스템 건강도를 **F 등급 (43%)**에서 **A+ 등급 (95%+)**으로 개선하기 위한 체계적인 정리 작업입니다. 이 SPEC은 특히 **Phase 1-2 (Orphan @CODE TAG 76개 제거)**에 집중합니다.

### 범위

- **대상**: 76개 orphan @CODE TAG 제거
- **기간**: Phase 1-2 (6-8시간 예상)
- **영향**: TAG Health F (43%) → D (65%) 개선
- **제약**: 코드 기능 변경 금지, 테스트 통과율 77.8% 유지, MyPy 100% 타입 안전성 유지

---

## 🎯 Environment (환경)

### 현재 시스템 상태

#### TAG 스캔 결과 (Explore agent)
- **총 TAG 수**: 4,753개
  - @SPEC: 1,220개
  - @CODE: 1,695개
  - @TEST: 1,303개
  - @DOC: 535개
- **TAG Health 등급**: F (43%) - Critical
- **Primary Chain Integrity**: 92% (목표: 100%)

#### Orphan TAG 분포
- **Orphan @CODE TAGs**: 76개 (중복 포함 210개 이상)
  - @CODE:ID: 210개 (placeholder)
  - @CODE:AUTH-001: 144개 (예제 코드)
  - @CODE:EXISTING: 21개 (레거시)
- **Orphan @TEST TAGs**: 45개 (중복 포함 162개 이상)
  - @TEST:0: 162개
  - @TEST:AUTH-001: 137개
  - @TEST:ID: 96개

#### 기술 환경
- **Python 버전**: 3.13+
- **MyPy 타입 안전성**: 100% (77/77 errors resolved)
- **테스트 통과율**: 77.8% (유지 필요)
- **Git 브랜치**: `fix/ci-cd-workflow-syntax` (현재)
- **도구**: ripgrep (rg), Git, Python scripts

### 개발 환경
- **프로젝트 모드**: Personal
- **Git 전략**: Feature branch → 로컬 커밋 → 수동 PR
- **도구 체인**: Python, ripgrep, Git, MyPy, pytest

---

## 🔍 Assumptions (가정 사항)

### 기술적 가정

1. **TAG 스캔 정확성**
   - Explore agent의 TAG 스캔 결과는 100% 정확하다고 가정
   - 76개 orphan @CODE TAG 목록은 검증되었으며 최신 상태임

2. **코드 안정성**
   - 현재 코드베이스는 테스트 통과율 77.8%를 유지하고 있음
   - TAG 정리 중 코드 기능은 변경되지 않음
   - MyPy 타입 안전성 100%는 TAG 정리 후에도 유지됨

3. **Git 히스토리 무결성**
   - 모든 TAG 정리 작업은 Git 커밋으로 추적 가능
   - 롤백이 필요한 경우 Git을 통해 완전 복원 가능

### 프로세스 가정

4. **SPEC 존재 여부**
   - Orphan @CODE TAG 대부분은 대응하는 @SPEC이 없거나 삭제됨
   - 일부 TAG는 적절한 SPEC으로 재연결 가능

5. **자동화 가능성**
   - Placeholder TAG (@CODE:ID)는 스크립트로 자동 교체 가능
   - 예제 코드 TAG (@CODE:AUTH-001)는 수동 검토 필요

6. **리소스 가용성**
   - Phase 1-2 작업에 6-8시간 할당 가능
   - doc-syncer, tag-agent, git-manager 협력 가능

---

## 📜 Requirements (요구사항)

### 1. Ubiquitous Requirements (항상 참)

**REQ-1.1**: TAG 시스템은 100% 추적 가능성을 제공해야 한다.
- 모든 @CODE TAG는 대응하는 @SPEC이 존재해야 함
- TAG 체인 (@SPEC → @CODE → @TEST → @DOC)은 끊기지 않아야 함

**REQ-1.2**: TAG 정리 작업은 코드 기능을 변경하지 않아야 한다.
- TAG 주석만 수정/삭제
- 프로덕션 코드 로직 변경 금지
- 테스트 통과율 77.8% 유지 필수

**REQ-1.3**: TAG 정리 작업은 타입 안전성을 유지해야 한다.
- MyPy 100% 타입 안전성 유지
- 타입 주석 변경 금지

### 2. Event-driven Requirements (이벤트 기반)

**REQ-2.1**: WHEN orphan @CODE TAG가 발견되면, THEN 시스템은 자동으로 경고를 발생시켜야 한다.
- 검증 스크립트 (`validate_tags.py --check-orphans --type CODE`)
- Orphan TAG 목록을 `orphan_code_tags.txt`에 출력

**REQ-2.2**: WHEN TAG cleanup이 실행되면, THEN 모든 변경 사항은 Git 커밋으로 추적되어야 한다.
- 각 정리 단계마다 독립적 커밋 생성
- 커밋 메시지: `refactor(tags): Remove orphan @CODE:ID placeholders (210 → 0)`

**REQ-2.3**: WHEN placeholder TAG (@CODE:ID)가 발견되면, THEN 자동으로 실제 SPEC ID로 교체되어야 한다.
- 스크립트 기반 자동 교체
- 파일별 검증 필수

**REQ-2.4**: WHEN 예제 코드 TAG (@CODE:AUTH-001)가 발견되면, THEN 수동 검토 후 적절히 처리되어야 한다.
- 프로덕션 코드: AUTH-002로 교체
- 예제 코드: examples/ 디렉토리로 이동 또는 제거

### 3. State-driven Requirements (상태 기반)

**REQ-3.1**: WHILE TAG Health가 F등급인 상태에서, THEN 시스템은 정리 작업을 권장해야 한다.
- TAG Health < 50% 시 경고
- 정리 계획 (plan.md) 제공

**REQ-3.2**: WHILE cleanup이 진행 중인 동안, THEN 다른 SPEC 개발은 보류되어야 한다.
- TAG 정리 중 새 SPEC 생성 금지
- 기존 SPEC 수정 최소화

**REQ-3.3**: WHILE Git 커밋이 생성된 상태에서, THEN 롤백이 가능해야 한다.
- 각 커밋은 독립적으로 revert 가능
- `.moai/backup/removed_tags.json`에 제거된 TAG 백업

### 4. Optional Requirements (선택적)

**REQ-4.1**: WHERE 자동화가 가능한 경우, IF 스크립트 기반 TAG 교체를 수행할 수 있다.
- Placeholder TAG (@CODE:ID) 자동 교체
- Dry-run 모드로 먼저 검증

**REQ-4.2**: WHERE 수동 검토가 필요한 경우, IF 파일별 체크리스트를 제공할 수 있다.
- 예제 코드 TAG 목록 생성
- 파일 경로 + TAG ID + 처리 방침

**REQ-4.3**: WHERE TAG 인덱스가 존재하는 경우, IF 정리 후 재생성할 수 있다.
- `.moai/indexes/tag_catalog.json` 업데이트
- TAG 체인 무결성 재검증

### 5. Unwanted Behaviors (원치 않는 동작)

**REQ-5.1**: IF TAG 정리 중 코드 기능이 변경되면, THEN 시스템은 즉시 중단되어야 한다.
- 테스트 실행 (`pytest tests/`)
- 실패 시 롤백 및 작업 중단

**REQ-5.2**: IF 잘못된 TAG 교체가 감지되면, THEN 롤백 절차가 실행되어야 한다.
- Git revert로 이전 커밋 복원
- 변경 로그 (`tag_changes.log`) 확인

**REQ-5.3**: IF MyPy 타입 오류가 발생하면, THEN TAG 정리는 중단되어야 한다.
- MyPy 검증 (`mypy --config-file pyproject.toml .`)
- 타입 안전성 100% 유지 필수

---

## 🛠️ Specifications (상세 사양)

### SPEC-1: Orphan @CODE TAG 스캔 및 분류

**목적**: 76개 orphan @CODE TAG를 우선순위별로 분류하고 처리 방침 결정

**구현 방법**:
```bash
# 1. Orphan @CODE TAG 목록 생성
rg '@CODE:[A-Z-]+-\d+' --no-filename | sort | uniq > orphan_code_tags.txt

# 2. SPEC 존재 여부 확인
for tag in $(cat orphan_code_tags.txt); do
  spec_id=$(echo $tag | sed 's/@CODE:/@SPEC:/')
  if ! rg -q "$spec_id" .moai/specs/; then
    echo "$tag -> NO SPEC" >> critical_orphans.txt
  fi
done

# 3. 우선순위 분류
# - P0: Placeholder TAG (@CODE:ID) → 자동 교체
# - P1: 예제 TAG (@CODE:AUTH-001) → 수동 검토
# - P2: 레거시 TAG (@CODE:EXISTING) → 삭제 또는 SPEC 생성
```

**검증 기준**:
- orphan_code_tags.txt 파일 생성 확인
- critical_orphans.txt에 76개 TAG 기록 확인
- 우선순위별 분류 완료

---

### SPEC-2: Placeholder TAG (@CODE:ID) 자동 교체

**목적**: 210개 @CODE:ID placeholder를 실제 SPEC ID로 자동 교체

**구현 방법**:
```python
# .moai/scripts/replace_placeholder_tags.py
import re
import os
from pathlib import Path

def replace_code_id_tags(base_dir: str):
    """Replace @CODE:ID placeholders with actual SPEC IDs"""

    # 1. Find files with @CODE:ID
    files = subprocess.run(
        ['rg', '@CODE:ID', '-l', base_dir],
        capture_output=True,
        text=True
    ).stdout.splitlines()

    # 2. For each file, analyze context and determine correct SPEC ID
    for file_path in files:
        with open(file_path, 'r') as f:
            content = f.read()

        # Find function/class context
        # Match with existing SPEC based on filename/module
        # Replace @CODE:ID with @CODE:{SPEC-ID}

        # 3. Write updated content
        with open(file_path, 'w') as f:
            f.write(updated_content)

    return len(files)

# Dry-run mode for safety
if __name__ == "__main__":
    dry_run = True
    replace_code_id_tags("apps/", dry_run=dry_run)
```

**검증 기준**:
- Dry-run 모드로 변경 사항 미리 확인
- @CODE:ID 개수: 210 → 0
- 테스트 통과 확인 (`pytest tests/`)
- MyPy 타입 검증 통과

---

### SPEC-3: 예제 TAG (@CODE:AUTH-001) 수동 검토

**목적**: 144개 @CODE:AUTH-001 TAG를 프로덕션/예제로 분류하고 적절히 처리

**구현 방법**:
```bash
# 1. @CODE:AUTH-001 파일 목록 생성
rg '@CODE:AUTH-001' -l > auth_001_files.txt

# 2. 파일별 검토 체크리스트 생성
while read file; do
  echo "File: $file"
  echo "  - [ ] Production code? (Y/N)"
  echo "  - [ ] Example code? (Y/N)"
  echo "  - [ ] Action: (Replace with AUTH-002 | Move to examples/ | Remove)"
  echo ""
done < auth_001_files.txt > auth_001_checklist.md

# 3. 수동 검토 후 처리
# - Production: sed 's/@CODE:AUTH-001/@CODE:AUTH-002/g'
# - Example: mv {file} examples/
# - Remove: git rm {file} (if obsolete)
```

**검증 기준**:
- auth_001_checklist.md 생성 확인
- 144개 TAG 100% 처리 완료
- 프로덕션 코드는 AUTH-002로 교체
- 예제 코드는 examples/ 디렉토리로 이동
- 테스트 통과 확인

---

### SPEC-4: 레거시 TAG (@CODE:EXISTING) 정리

**목적**: 21개 @CODE:EXISTING TAG를 삭제하거나 새 SPEC 생성

**구현 방법**:
```bash
# 1. @CODE:EXISTING 파일 목록
rg '@CODE:EXISTING' -l > existing_tags.txt

# 2. 각 파일의 코드 활성 상태 확인
for file in $(cat existing_tags.txt); do
  # Git 히스토리 확인 (최근 6개월 이내 수정)
  last_commit=$(git log -1 --format="%ci" -- "$file")
  echo "$file: $last_commit"
done

# 3. 처리 방침
# - Active (최근 6개월 이내 수정): 새 SPEC 생성 필요
# - Inactive (6개월 이상 수정 없음): TAG 제거 또는 DEPRECATED 마킹
```

**검증 기준**:
- existing_tags.txt 생성 확인
- 21개 TAG 100% 처리 완료
- Active 코드: 새 SPEC 생성 (SPEC-LEGACY-XXX)
- Inactive 코드: TAG 제거 또는 DEPRECATED 마킹

---

### SPEC-5: TAG Health 개선 검증

**목적**: Phase 1-2 완료 후 TAG Health가 F (43%) → D (65%)로 개선되었는지 검증

**구현 방법**:
```bash
# 1. TAG 전체 재스캔
python .moai/scripts/validate_tags.py --check-all > tag_health_report.txt

# 2. Orphan TAG 개수 확인
orphan_count=$(rg '@CODE:[A-Z-]+-\d+' --no-filename | sort | uniq | wc -l)
echo "Orphan @CODE TAGs: $orphan_count (Target: 0)"

# 3. TAG Health 점수 계산
# - Total TAGs: 4,753 → 4,632 (121 orphans removed)
# - Orphan @CODE: 76 → 0
# - Primary Chain Integrity: 92% → 95%+
# - Overall Health: F (43%) → D (65%)

# 4. 검증 결과를 sync-report에 기록
echo "## TAG Health Improvement" >> .moai/reports/sync-report-session17.md
echo "- Before: F (43%)" >> .moai/reports/sync-report-session17.md
echo "- After: D (65%)" >> .moai/reports/sync-report-session17.md
echo "- Improvement: +22%p" >> .moai/reports/sync-report-session17.md
```

**검증 기준**:
- Orphan @CODE TAGs: 76 → 0 (-100%)
- TAG Health Score: F (43%) → D (65%) (+22%p)
- Primary Chain Integrity: 92% → 95%+
- 모든 테스트 통과 (77.8% 유지)
- MyPy 타입 안전성 100% 유지

---

### SPEC-6: Git 커밋 및 문서화

**목적**: TAG 정리 작업을 Git 커밋으로 추적하고 문서화

**구현 방법**:
```bash
# 1. 정리 단계별 커밋 생성
git add .
git commit -m "refactor(tags): Remove 210 @CODE:ID placeholder tags

- Replace @CODE:ID with actual SPEC IDs
- Script: .moai/scripts/replace_placeholder_tags.py
- Impact: 76 files affected
- Tests: All passing (77.8%)
- MyPy: 100% type safety maintained

@CODE:TAG-CLEANUP-001
"

# 2. 체크포인트 브랜치 생성 (Personal mode)
git branch checkpoint/tag-cleanup-phase1-$(date +%Y%m%d)

# 3. 문서 업데이트
# - .moai/specs/SPEC-TAG-CLEANUP-001/spec.md (version: 0.0.1 → 0.1.0)
# - .moai/reports/sync-report-session17.md (TAG Health 개선 기록)
# - CHANGELOG.md (Phase 1-2 완료 기록)
```

**검증 기준**:
- Git 커밋 메시지에 @CODE:TAG-CLEANUP-001 포함
- 체크포인트 브랜치 생성 확인
- SPEC version 0.0.1 → 0.1.0 업데이트
- sync-report에 TAG Health 개선 결과 기록

---

## 🔗 Traceability (추적성)

### TAG 체인

| TAG ID | Description | Location |
|--------|-------------|----------|
| **@SPEC:TAG-CLEANUP-001** | 이 명세서 | `.moai/specs/SPEC-TAG-CLEANUP-001/spec.md` |
| **@CODE:TAG-CLEANUP-001** | TAG cleanup 스크립트 (Phase 2에서 생성 예정) | `.moai/scripts/replace_placeholder_tags.py` |
| **@TEST:TAG-CLEANUP-001** | TAG 검증 테스트 (Phase 2에서 생성 예정) | `tests/test_tag_validation.py` |
| **@DOC:TAG-CLEANUP-001** | 구현 계획 및 전략 | `.moai/specs/SPEC-TAG-CLEANUP-001/plan.md` |

### 관련 문서

- **plan.md**: 5-phase TAG cleanup 전략 (500+ lines)
- **sync-report-session16.md**: TAG Health F 등급 원인 분석
- **CLAUDE-RULES.md**: TAG 명명 규칙 및 생명주기
- **CLAUDE-PRACTICES.md**: TAG 시스템 베스트 프랙티스

### 의존성

- **depends_on**: 없음 (독립적 정리 작업)
- **blocks**: 없음 (다른 SPEC에 영향 없음)
- **related_specs**: MYPY-CONSOLIDATION-002 (타입 안전성 유지)

---

## 📊 Success Metrics (성공 지표)

### 정량적 목표 (Phase 1-2)

| 지표 | Before | After | Improvement |
|------|--------|-------|-------------|
| **Orphan @CODE TAGs** | 76 | 0 | -100% |
| **TAG Health Score** | 43% (F) | 65% (D) | +22%p |
| **Primary Chain Integrity** | 92% | 95%+ | +3%p |
| **테스트 통과율** | 77.8% | 77.8% | 유지 |
| **MyPy 타입 안전성** | 100% | 100% | 유지 |

### 정성적 목표

- ✅ **추적성**: 모든 @CODE TAG는 대응하는 @SPEC 존재
- ✅ **안전성**: 코드 기능 변경 없음, 롤백 가능
- ✅ **문서화**: 정리 작업 Git 커밋으로 완전 추적
- ✅ **자동화**: Placeholder TAG 자동 교체 스크립트 작동

---

## ⚠️ Technical Constraints (기술적 제약)

### 시간 제약
- Phase 1-2 예상 시간: 6-8시간
- 실제 소요 시간은 수동 검토 비율에 따라 변동

### 기능 제약
- 코드 기능 변경 금지 (TAG만 수정)
- 테스트 통과율 77.8% 유지 필수
- MyPy 100% 타입 안전성 유지 필수

### 도구 제약
- ripgrep (rg) 필수 (TAG 스캔)
- Git 필수 (변경 추적 및 롤백)
- Python 3.13+ (자동화 스크립트)

### 리소스 제약
- Sub-agent 협력 필요: doc-syncer, tag-agent, git-manager
- Alfred 명령어: `/alfred:2-run TAG-CLEANUP-001` (Phase 2 실행)

---

## 🚨 Risks & Mitigation (위험 요소 및 대응)

### Risk 1: TAG 제거 시 코드 추적성 손실

**발생 가능성**: Medium
**영향도**: High

**완화 조치**:
- 모든 orphan TAG 제거 전 Git commit 생성 (롤백 가능)
- TAG 제거 시 주석으로 "DEPRECATED: 이전 TAG ID" 기록
- `.moai/backup/removed_tags.json`에 제거된 TAG 백업

---

### Risk 2: 자동 수정 스크립트 오류

**발생 가능성**: Low
**영향도**: Critical

**완화 조치**:
- 모든 자동 수정 전 dry-run 모드 실행
- 변경 사항을 `.moai/logs/tag_changes.log`에 기록
- 검증 실패 시 즉시 롤백

---

### Risk 3: 수동 검토 시간 초과

**발생 가능성**: Medium
**영향도**: Medium

**완화 조치**:
- 우선순위 기반 처리 (P0: placeholder → P1: 예제 → P2: 레거시)
- 6시간 내 완료 불가 시 다음 세션으로 이월
- 각 단계마다 독립적 커밋 (부분 진행 보존)

---

## 📖 References (참고 자료)

### 관련 SPEC
- @SPEC:MYPY-CONSOLIDATION-002: MyPy 100% 타입 안전성 달성
- @SPEC:AGENT-CARD-001: TAG 체인 베스트 프랙티스
- @SPEC:TAXONOMY-VIZ-001: TAG 시스템 사용 예제

### 관련 문서
- `.moai/reports/sync-report-session16.md`: TAG Health F 등급 원인 분석
- `CLAUDE-RULES.md`: TAG 명명 규칙 및 생명주기
- `CLAUDE-PRACTICES.md`: TAG 시스템 베스트 프랙티스

### 도구
- **ripgrep (rg)**: TAG 검색 및 스캔
- **git log --follow**: 파일 이동 추적
- **Python scripts**: 자동화 및 검증 (`.moai/scripts/`)

---

**SPEC Created By**: spec-builder agent
**SPEC Date**: 2025-11-05
**SPEC Version**: 0.0.1
**Next Step**: `/alfred:2-run TAG-CLEANUP-001` (Phase 1-2 실행)

---

**End of SPEC**
