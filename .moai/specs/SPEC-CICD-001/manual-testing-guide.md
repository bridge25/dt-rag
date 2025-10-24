# Manual Testing Guide for SPEC-CICD-001

**@DOC:CICD-001**

## Overview

이 문서는 `.github/workflows/import-validation.yml` 워크플로우의 수동 테스트 절차를 설명합니다.

## Prerequisites

- Git repository with GitHub remote configured
- Feature branch: `feature/SPEC-CICD-001`
- GitHub Actions enabled on repository
- Write access to repository

## Test Scenarios

### Scenario 1: Normal Code (All Stages Pass)

**목적**: 정상 코드에서 3단계 검증이 모두 통과하는지 확인

**테스트 절차**:

1. 현재 브랜치 확인:
   ```bash
   git branch
   # Should show: feature/SPEC-CICD-001
   ```

2. 워크플로우 파일 커밋:
   ```bash
   git add .github/workflows/import-validation.yml
   git commit -m "feat(cicd): add import validation workflow

   Implements SPEC-CICD-001 Phase 1:
   - Stage 1: Python syntax validation (compileall)
   - Stage 2: Alembic migration validation
   - Stage 3: API import validation

   Refs: @CODE:CICD-001"
   ```

3. GitHub에 push:
   ```bash
   git push origin feature/SPEC-CICD-001
   ```

4. GitHub Actions UI 확인:
   - GitHub repository → Actions 탭 이동
   - "Import Validation" 워크플로우 실행 확인
   - 실행 로그에서 각 단계 확인:
     - ✓ Stage 1: Python 구문 검증 완료
     - ✓ Stage 2: Alembic 마이그레이션 검증 완료
     - ✓ Stage 3: API import 검증 완료
     - ✓ 모든 import 검증 단계 통과

**예상 결과**:
- ✅ Workflow status: Success (green checkmark)
- ✅ All 3 validation stages pass
- ✅ Total execution time < 5 minutes

---

### Scenario 2: Syntax Error (Stage 1 Failure)

**목적**: 구문 오류 시 Stage 1에서 실패하는지 확인 (오늘 발생한 실제 오류 재현)

**테스트 절차**:

1. 의도적으로 구문 오류 삽입:
   ```bash
   # apps/core/env_manager.py 파일에 임시로 따옴표 제거
   sed -i 's/"ERROR":/ERROR:/' apps/core/env_manager.py
   ```

2. 변경사항 커밋 및 push:
   ```bash
   git add apps/core/env_manager.py
   git commit -m "test(cicd): intentionally break syntax for testing"
   git push origin feature/SPEC-CICD-001
   ```

3. GitHub Actions UI 확인:
   - "Import Validation" 워크플로우가 실패하는지 확인
   - Stage 1에서 실패 메시지 확인

4. 오류 복구:
   ```bash
   git revert HEAD
   git push origin feature/SPEC-CICD-001
   ```

**예상 결과**:
- ❌ Workflow status: Failed (red X)
- ❌ Stage 1: Python 구문 검증 - FAILED
- 🔴 Error message shows: "SyntaxError: invalid syntax"
- ⏸️ Stage 2, 3 should NOT execute (fail-fast behavior)

---

### Scenario 3: Import Error (Stage 3 Failure)

**목적**: Import 오류 시 Stage 3에서 실패하는지 확인

**테스트 절차**:

1. 의도적으로 import 오류 삽입:
   ```bash
   # apps/api/main.py 파일에 존재하지 않는 import 추가
   echo "from apps.nonexistent_module import NonexistentClass" >> apps/api/main.py
   ```

2. 변경사항 커밋 및 push:
   ```bash
   git add apps/api/main.py
   git commit -m "test(cicd): intentionally break import for testing"
   git push origin feature/SPEC-CICD-001
   ```

3. GitHub Actions UI 확인:
   - Stage 1, 2는 통과하고 Stage 3에서 실패하는지 확인
   - Import 오류 메시지 확인

4. 오류 복구:
   ```bash
   git revert HEAD
   git push origin feature/SPEC-CICD-001
   ```

**예상 결과**:
- ✅ Stage 1: Python 구문 검증 - PASSED
- ✅ Stage 2: Alembic 마이그레이션 검증 - PASSED
- ❌ Stage 3: API import 검증 - FAILED
- 🔴 Error message shows: "ModuleNotFoundError: No module named 'apps.nonexistent_module'"

---

### Scenario 4: Pull Request Validation

**목적**: PR 생성 시 자동으로 검증이 실행되는지 확인

**테스트 절차**:

1. GitHub UI에서 Pull Request 생성:
   - Base: `master`
   - Compare: `feature/SPEC-CICD-001`
   - Title: "feat(cicd): add import validation automation (SPEC-CICD-001)"

2. PR 페이지에서 Checks 탭 확인:
   - "Import Validation" 체크가 자동으로 실행되는지 확인
   - 모든 단계가 통과하는지 확인

3. PR 상태 확인:
   - ✅ All checks have passed
   - Merge 가능 상태 확인

**예상 결과**:
- ✅ Import Validation check: Success
- ✅ Merge button enabled
- ✅ No blocking issues

---

## Verification Checklist

Phase 1 구현 완료 후 다음 항목을 확인하세요:

- [ ] **Workflow File**
  - [ ] `.github/workflows/import-validation.yml` 파일 존재
  - [ ] `@CODE:CICD-001` TAG 포함
  - [ ] 3단계 검증 구현 (compileall → alembic → api)

- [ ] **GitHub Actions Integration**
  - [ ] master 브랜치 push 시 자동 실행
  - [ ] feature/** 브랜치 push 시 자동 실행
  - [ ] PR to master 시 자동 실행

- [ ] **Validation Stages**
  - [ ] Stage 1: compileall 검증 정상 작동
  - [ ] Stage 2: Alembic 검증 정상 작동 (dry-run)
  - [ ] Stage 3: API import 검증 정상 작동

- [ ] **Error Detection**
  - [ ] 구문 오류 감지 (Stage 1)
  - [ ] Import 오류 감지 (Stage 3)
  - [ ] 명확한 오류 메시지 출력

- [ ] **Performance**
  - [ ] 전체 실행 시간 < 5분
  - [ ] 각 단계 timeout 설정 (1분)

- [ ] **Documentation**
  - [ ] 주석으로 각 단계 설명 추가
  - [ ] HISTORY 섹션 작성

---

## Troubleshooting

### Issue: Workflow not triggering

**증상**: Push 후 GitHub Actions에서 워크플로우가 실행되지 않음

**해결 방법**:
1. GitHub repository → Settings → Actions → General 확인
2. "Allow all actions and reusable workflows" 선택 확인
3. Workflow permissions: "Read and write permissions" 선택

### Issue: Stage 2 (Alembic) fails with "command not found"

**증상**: `alembic: command not found` 오류

**해결 방법**:
1. `requirements.txt`에 `alembic==1.16.4` 포함 확인
2. "Install dependencies" 단계 로그 확인
3. 필요시 `pip install alembic` 명시적 추가

### Issue: Stage 3 (API import) fails locally but passes in CI

**증상**: 로컬에서는 실패하지만 GitHub Actions에서는 성공

**원인**: 환경 변수 차이 (로컬 `.env` vs GitHub Secrets)

**해결 방법**:
1. 로컬에서 `.env` 파일 설정 확인
2. GitHub repository → Settings → Secrets에 필요한 환경변수 추가
3. 워크플로우에 `env:` 섹션 추가

---

## Next Steps

Phase 1 테스트 완료 후:

1. **PR Merge**: feature/SPEC-CICD-001 → master
2. **Monitor Production**: master 브랜치에서 워크플로우 동작 확인
3. **Phase 2 Planning**: Pre-commit hook 구현 계획 수립
4. **Documentation Update**: 실제 테스트 결과를 바탕으로 문서 업데이트

---

**문서 작성자**: tdd-implementer agent
**최종 수정일**: 2025-01-24
**관련 SPEC**: SPEC-CICD-001/spec.md
**관련 TAG**: @CODE:CICD-001, @DOC:CICD-001
