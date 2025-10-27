# 다음 세션 작업 가이드

**작성일**: 2025-10-27
**현재 브랜치**: master
**프로젝트**: dt-rag-standalone

---

## 📌 현재 상황 요약

### 완료된 작업 (세션 1)

#### 1️⃣ 브랜치 정리 Phase 1-4 완료
- **초기 브랜치**: 31개
- **삭제 완료**: 5개 (모두 백업 태그 생성)
  - feature/SPEC-AGENT-GROWTH-004-v2 (중복)
  - feature/SPEC-ENV-VALIDATE-001-checkpoint (중복)
  - feature/SPEC-ORDER-PARSER-001 (고아 브랜치)
  - feature/SPEC-OCR-CASCADE-001 (고아 브랜치, SPEC은 PR #4로 추가)
  - feature/SPEC-OCR-001 (내용 없음)
- **현재 브랜치**: 27개

#### 2️⃣ PR 생성 완료
**총 11개 PR 생성** (모두 OPEN 상태)

| PR# | 브랜치 | 카테고리 | 우선순위 |
|-----|--------|----------|----------|
| #3 | feature/SPEC-API-INTEGRATION-001 | Critical SPEC | 🔴 높음 |
| #4 | feat/add-ocr-cascade-spec | Critical SPEC | 🔴 높음 |
| #5 | chore/bootstrap-ci-governance | Phase 4 | 🔴 높음 |
| #6 | chore/codex-auto-review | Phase 4 | 🟡 중간 |
| #7 | dt-rag/chore/a-readme-hardening | Phase 4 | 🟡 중간 |
| #8 | dt-rag/feat/a-api-services | Phase 4 | 🟡 중간 |
| #9 | dt-rag/feat/a-hitl-worker | Phase 4 | 🟡 중간 |
| #10 | dt-rag/feat/a-ingest-pipeline | Phase 4 | 🟡 중간 |
| #11 | dt-rag/feat/a-observability | Phase 4 | 🟡 중간 |
| #12 | dt-rag/feat/a-packaging | Phase 4 | 🟡 중간 |
| #13 | dt-rag/feat/c-frontend | Phase 4 | 🟠 중-높음 |

#### 3️⃣ 핵심 발견사항
- **SPEC과 코드 분리**: 18개 브랜치에서 SPEC은 master에 있으나 코드는 브랜치에만 존재
- **대규모 변경**: 모든 SPEC-in-master 브랜치가 600-1,100 파일 변경
- **프로젝트 구조 변경 흔적**: 일부 브랜치가 다른 경로 구조 사용 (alfred-project 등)

---

## 🎯 남은 작업 (다음 세션)

### 2단계: v1.8.1 메이저 버전 검토 (1개 브랜치)

#### 대상 브랜치
- **feat/dt-rag-v1.8.1-implementation**

#### 통계
- **변경 규모**: 618 files, +188,070 insertions, -20,219 deletions
- **Ahead/Behind**: 30 ahead, 29 behind
- **마지막 커밋**: "Setup MoAI-ADK infrastructure for Phase 0-4 Memento integration"

#### 최근 커밋 5개
```
1a8e0f2b chore: Setup MoAI-ADK infrastructure for Phase 0-4 Memento integration
bb50f0da fix: 교차 검증 기반 Critical/Medium 이슈 수정
373b5c06 feat: Reconstruct Phase 2 API client with VibeCoding methodology
e9cf8d8b refactor: Remove default app/page.tsx
75497343 docs: Update README and configuration
```

#### 왜 별도 검토가 필요한가?
1. **변경 규모가 매우 큼**: 188k+ 삽입, 20k 삭제
2. **메이저 버전 작업**: 프로젝트 전체 구조 변경 가능성
3. **신중한 병합 필요**: 충돌 가능성 높음
4. **분할 병합 고려**: 한 번에 병합하기엔 위험할 수 있음

#### 검토 작업 체크리스트
- [ ] 브랜치 체크아웃 및 상태 확인
- [ ] diff --stat 전체 확인
- [ ] 주요 변경 파일 카테고리 분류
  - [ ] 인프라 변경 (CI/CD, Docker 등)
  - [ ] 코드 변경 (apps/, src/ 등)
  - [ ] 문서 변경 (README, docs/)
  - [ ] 설정 변경 (config files)
- [ ] 테스트 상태 확인
- [ ] 충돌 가능성 확인 (git merge --no-commit --no-ff master)
- [ ] 분할 전략 수립 (필요시)
- [ ] PR 생성 또는 보류 결정

#### 실행 명령어
```bash
# 브랜치 체크아웃
git checkout feat/dt-rag-v1.8.1-implementation

# 전체 diff 확인
git diff --stat master...feat/dt-rag-v1.8.1-implementation > v1.8.1_full_diff.txt

# 변경된 파일 목록
git diff --name-only master...feat/dt-rag-v1.8.1-implementation | tee v1.8.1_files.txt

# 카테고리별 분류
git diff --name-only master...feat/dt-rag-v1.8.1-implementation | grep -E "^\.github/|^docker/|^\.docker" | tee v1.8.1_infra.txt
git diff --name-only master...feat/dt-rag-v1.8.1-implementation | grep -E "^apps/|^src/" | tee v1.8.1_code.txt
git diff --name-only master...feat/dt-rag-v1.8.1-implementation | grep -E "README|\.md$" | tee v1.8.1_docs.txt

# 충돌 시뮬레이션
git checkout master
git merge --no-commit --no-ff feat/dt-rag-v1.8.1-implementation
git merge --abort  # 시뮬레이션 후 취소
```

---

### 3단계: Phase 2 브랜치 선별 검토 (15개 브랜치)

#### 대상 브랜치 목록
모두 **SPEC은 master에 있으나, 코드는 브랜치에만 존재**

| 브랜치 | 파일 수 | Ahead | Behind | SPEC ID |
|--------|---------|-------|--------|---------|
| feature/SPEC-AGENT-GROWTH-001 | 781 | 79 | 29 | SPEC-AGENT-GROWTH-001 |
| feature/SPEC-AGENT-GROWTH-002 | 791 | 81 | 29 | SPEC-AGENT-GROWTH-002 |
| feature/SPEC-AGENT-GROWTH-004 | 809 | 83 | 29 | SPEC-AGENT-GROWTH-004 |
| feature/SPEC-AGENT-GROWTH-005 | 1,121 | 86 | 29 | SPEC-AGENT-GROWTH-005 |
| feature/SPEC-CASEBANK-002 | 664 | 54 | 29 | SPEC-CASEBANK-002 |
| feature/SPEC-CONSOLIDATION-001 | 664 | 54 | 29 | SPEC-CONSOLIDATION-001 |
| feature/SPEC-DEBATE-001 | 651 | 43 | 29 | SPEC-DEBATE-001 |
| feature/SPEC-ENV-VALIDATE-001 | 771 | 77 | 29 | SPEC-ENV-VALIDATE-001 |
| feature/SPEC-FOUNDATION-001 | 627 | 35 | 29 | SPEC-FOUNDATION-001 |
| feature/SPEC-JOB-OPTIMIZE-001 | 765 | 73 | 29 | SPEC-JOB-OPTIMIZE-001 |
| feature/SPEC-REDIS-COMPAT-001 | 763 | 71 | 29 | SPEC-REDIS-COMPAT-001 |
| feature/SPEC-REFLECTION-001 | 664 | 54 | 29 | SPEC-REFLECTION-001 |
| feature/SPEC-REPLAY-001 | 640 | 41 | 29 | SPEC-REPLAY-001 |
| feature/SPEC-SOFTQ-001 | 639 | 37 | 29 | SPEC-SOFTQ-001 |
| feature/SPEC-UI-INTEGRATION-001 | 745 | 88 | 29 | SPEC-UI-INTEGRATION-001 |

#### 왜 선별 검토가 필요한가?
1. **SPEC과 코드 분리**: SPEC 문서만 병합되고 실제 코드는 미병합
2. **대규모 변경**: 각 브랜치당 600-1,100 파일 변경
3. **프로젝트 필요성 판단**: 모든 SPEC이 현재 프로젝트에 필요한지 확인 필요
4. **리소스 제약**: 한 번에 모두 검토하기 어려움

#### 검토 전략

##### Step 1: SPEC 문서 읽기 (각 브랜치)
```bash
# SPEC 문서 확인 (master에 있음)
cat .moai/specs/SPEC-AGENT-GROWTH-001/spec.md | head -100

# 주요 확인 사항:
# - Priority (critical, high, medium, low)
# - Category (feature, bugfix, refactor)
# - 목적 및 요구사항
# - 현재 프로젝트 로드맵과의 관련성
```

##### Step 2: 프로젝트 필요성 평가
각 SPEC에 대해 다음 질문에 답하기:
1. **현재 프로젝트에 필요한 기능인가?**
2. **Priority가 높은가? (critical, high)**
3. **다른 기능과 의존성이 있는가?**
4. **보류 시 프로젝트에 공백이 생기는가?**

##### Step 3: 우선순위 분류
- 🔴 **즉시 PR 생성**: Critical/High priority, 핵심 기능
- 🟡 **선택적 PR 생성**: Medium priority, 개선 사항
- ⚪ **보류 또는 삭제**: Low priority, 불필요한 기능

##### Step 4: 실행
```bash
# 1. SPEC 문서 읽기
for spec_id in AGENT-GROWTH-001 AGENT-GROWTH-002 AGENT-GROWTH-004 AGENT-GROWTH-005 \
               CASEBANK-002 CONSOLIDATION-001 DEBATE-001 ENV-VALIDATE-001 \
               FOUNDATION-001 JOB-OPTIMIZE-001 REDIS-COMPAT-001 REFLECTION-001 \
               REPLAY-001 SOFTQ-001 UI-INTEGRATION-001; do
  echo "=== SPEC-${spec_id} ==="
  cat .moai/specs/SPEC-${spec_id}/spec.md | head -50
  echo ""
done > phase2_spec_summary.txt

# 2. 판정 기록
cat > phase2_spec_decisions.md <<'EOF'
# Phase 2 SPEC 판정 기록

| SPEC ID | Priority | Category | 판정 | 사유 |
|---------|----------|----------|------|------|
| AGENT-GROWTH-001 | ? | ? | ? | ? |
| AGENT-GROWTH-002 | ? | ? | ? | ? |
...
EOF

# 3. 선택된 브랜치 PR 생성
# (판정 후 실행)
```

#### 자동화 스크립트 (phase2_review_helper.py)
```python
#!/usr/bin/env python3
"""Phase 2 브랜치 검토 도우미"""
import subprocess
from pathlib import Path

SPEC_IDS = [
    "AGENT-GROWTH-001", "AGENT-GROWTH-002", "AGENT-GROWTH-004", "AGENT-GROWTH-005",
    "CASEBANK-002", "CONSOLIDATION-001", "DEBATE-001", "ENV-VALIDATE-001",
    "FOUNDATION-001", "JOB-OPTIMIZE-001", "REDIS-COMPAT-001", "REFLECTION-001",
    "REPLAY-001", "SOFTQ-001", "UI-INTEGRATION-001"
]

def extract_spec_metadata(spec_id: str) -> dict:
    """SPEC 메타데이터 추출"""
    spec_path = Path(f".moai/specs/SPEC-{spec_id}/spec.md")
    if not spec_path.exists():
        return {"error": "SPEC not found"}

    content = spec_path.read_text(encoding="utf-8")
    lines = content.split("\n")

    metadata = {}
    in_frontmatter = False

    for line in lines[:50]:  # 앞 50줄만 확인
        if line.strip() == "---":
            in_frontmatter = not in_frontmatter
            continue

        if in_frontmatter and ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()

    return metadata

def main():
    print("=" * 80)
    print("Phase 2 SPEC 메타데이터 요약")
    print("=" * 80)
    print()

    results = []

    for spec_id in SPEC_IDS:
        metadata = extract_spec_metadata(spec_id)

        priority = metadata.get("priority", "?")
        category = metadata.get("category", "?")
        status = metadata.get("status", "?")

        results.append({
            "spec_id": spec_id,
            "priority": priority,
            "category": category,
            "status": status
        })

        print(f"SPEC-{spec_id}")
        print(f"  Priority: {priority}")
        print(f"  Category: {category}")
        print(f"  Status: {status}")
        print()

    # Markdown 테이블 생성
    with open("phase2_spec_metadata.md", "w", encoding="utf-8") as f:
        f.write("# Phase 2 SPEC 메타데이터\n\n")
        f.write("| SPEC ID | Priority | Category | Status | 판정 | 사유 |\n")
        f.write("|---------|----------|----------|--------|------|------|\n")

        for r in results:
            f.write(f"| {r['spec_id']} | {r['priority']} | {r['category']} | {r['status']} | ? | ? |\n")

    print("✅ phase2_spec_metadata.md 생성 완료")
    print("   - 이 파일을 편집하여 각 SPEC의 판정을 기록하세요")

if __name__ == "__main__":
    main()
```

---

## 📚 참고 문서

### 필독 문서
1. **FINAL_BRANCH_CLEANUP_REPORT.md** - 전체 상황 종합 리포트
2. **BRANCH_CLEANUP_EXECUTION_REPORT.md** - Phase 1-3 실행 상세
3. **phase2_diff_details.txt** - 16개 브랜치 상세 diff
4. **phase4_quick_scan.txt** - Phase 4 브랜치 스캔 결과

### 생성할 문서 (다음 세션)
1. **v1.8.1_analysis_report.md** - v1.8.1 브랜치 분석 리포트
2. **phase2_spec_decisions.md** - Phase 2 SPEC 판정 기록
3. **phase2_pr_batch.md** - Phase 2 선택된 브랜치 PR 생성 계획

---

## 🔧 유용한 명령어

### 브랜치 상태 확인
```bash
# 현재 브랜치 확인
git branch --show-current

# 모든 feature 브랜치 목록
git branch | grep -E "feature/|dt-rag/|feat/|chore/"

# 브랜치 수 카운트
git branch | grep -E "feature/|dt-rag/|feat/|chore/" | wc -l
```

### SPEC 확인
```bash
# master에 있는 SPEC 목록
ls -1 .moai/specs/

# 특정 SPEC 읽기
cat .moai/specs/SPEC-AGENT-GROWTH-001/spec.md | head -100

# SPEC 메타데이터만 추출
cat .moai/specs/SPEC-AGENT-GROWTH-001/spec.md | sed -n '/^---$/,/^---$/p'
```

### 브랜치 비교
```bash
# 특정 브랜치의 변경 파일 수
git diff --stat master...feature/SPEC-AGENT-GROWTH-001 | tail -1

# 변경된 파일 목록
git diff --name-only master...feature/SPEC-AGENT-GROWTH-001

# 특정 파일의 변경 내용
git diff master...feature/SPEC-AGENT-GROWTH-001 -- path/to/file.py
```

### PR 관리
```bash
# PR 목록 확인
gh pr list --limit 20

# 특정 PR 상태 확인
gh pr view 3

# PR 병합
gh pr merge 3 --squash
```

### 백업 태그 확인
```bash
# 백업된 태그 목록
git tag | grep archive/

# 특정 태그 복원 (필요시)
git checkout -b restore-branch archive/BRANCH-NAME
```

---

## ⚠️ 주의사항

### 1. 작업 전 확인사항
- [ ] 현재 브랜치가 master인지 확인
- [ ] 로컬 master가 origin/master와 동기화되었는지 확인
- [ ] 변경사항이 커밋되지 않은 파일이 없는지 확인

```bash
git checkout master
git pull origin master
git status
```

### 2. 안전 수칙
- **항상 백업 태그 생성**: 삭제 전 `git tag archive/BRANCH-NAME BRANCH-NAME`
- **단계적 진행**: 한 번에 많은 브랜치를 처리하지 말 것
- **충돌 확인**: 병합 전 반드시 충돌 시뮬레이션
- **테스트 실행**: 병합 후 반드시 테스트 실행

### 3. 의사결정 가이드라인

#### PR 생성 기준
- ✅ Priority: Critical 또는 High
- ✅ 현재 프로젝트 로드맵에 포함
- ✅ 다른 기능과 의존성이 있음
- ✅ 보류 시 프로젝트에 공백 발생

#### 보류 또는 삭제 기준
- ❌ Priority: Low
- ❌ 현재 프로젝트 범위 밖
- ❌ 중복된 기능
- ❌ 실험적 기능 (더 이상 필요 없음)

---

## 🎯 작업 순서 권장

### Option A: v1.8.1 먼저 (메이저 버전 우선)
1. v1.8.1 브랜치 상세 분석
2. 분할 전략 수립 (필요시)
3. PR 생성 또는 단계별 병합
4. Phase 2 브랜치 검토

**장점**: 큰 작업을 먼저 처리, 이후 작업이 단순해짐
**단점**: 시간이 오래 걸릴 수 있음

### Option B: Phase 2 먼저 (빠른 성과 우선)
1. Phase 2 SPEC 메타데이터 자동 추출
2. Priority 높은 브랜치만 먼저 PR 생성 (3-5개)
3. v1.8.1 브랜치 분석
4. 나머지 Phase 2 브랜치 처리

**장점**: 빠른 성과, 점진적 진행
**단점**: v1.8.1 병합 시 충돌 가능성

### 권장: Option B (점진적 접근)
큰 작업(v1.8.1)보다 작은 작업들(Phase 2)을 먼저 처리하여 성과를 쌓고,
v1.8.1은 충분한 시간을 들여 신중히 검토하는 것을 권장합니다.

---

## 📞 세션 시작 시 실행할 명령어

```bash
# 1. 현재 상황 확인
cd /mnt/c/MYCLAUDE_PROJECT/sonheungmin/dt-rag-standalone
git checkout master
git status
git branch | wc -l

# 2. PR 목록 확인
gh pr list --limit 15

# 3. 남은 브랜치 확인
git branch | grep -E "feature/SPEC-|feat/dt-rag-v1.8.1"

# 4. 이 가이드 읽기
cat NEXT_SESSION_GUIDE.md

# 5. 작업 선택
# Option A: v1.8.1 먼저
# Option B: Phase 2 먼저 (권장)
```

---

## 🏁 완료 조건

### 2단계 완료 조건
- [ ] v1.8.1 브랜치 전체 분석 완료
- [ ] 분석 리포트 작성 (v1.8.1_analysis_report.md)
- [ ] PR 생성 또는 분할 전략 수립
- [ ] 병합 완료 (또는 보류 사유 기록)

### 3단계 완료 조건
- [ ] 15개 브랜치 모두 SPEC 검토 완료
- [ ] 각 브랜치 판정 기록 (phase2_spec_decisions.md)
- [ ] 선택된 브랜치 PR 생성 완료
- [ ] 불필요한 브랜치 백업 후 삭제

### 전체 완료 조건
- [ ] 브랜치 수 최소화 (목표: 10개 이하)
- [ ] 모든 필요한 기능 PR로 보존
- [ ] 최종 리포트 업데이트
- [ ] 팀 공유 (필요시)

---

**다음 세션에서 이 가이드를 읽고 Option B부터 시작하세요!** 🚀
