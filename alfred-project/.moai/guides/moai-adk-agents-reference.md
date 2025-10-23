# MoAI-ADK Specialized Agents 가이드

**작성일**: 2025-10-10
**버전**: v0.2.13

---

## 📖 목차

1. [Agents 개요](#agents-개요)
2. [3단계별 Agent 매핑](#3단계별-agent-매핑)
3. [Core Agents](#core-agents)
4. [Support Agents](#support-agents)
5. [Agent 협업 구조](#agent-협업-구조)
6. [사용 패턴](#사용-패턴)

---

## Agents 개요

MoAI-ADK의 각 Alfred 커맨드는 **specialized agents**를 활용하여 특정 작업을 전담합니다. 각 agent는 **단일 책임 원칙(Single Responsibility Principle)**을 따르며, 독립적으로 실행됩니다.

### Agent 설계 철학

```
✅ 단일 책임: 각 agent는 하나의 영역만 전담
✅ 독립 실행: agent 간 직접 호출 금지
✅ 명확한 계약: 입력과 출력이 명확
✅ 오케스트레이션: 커맨드 레벨에서만 순차 실행
```

---

## 3단계별 Agent 매핑

### 📊 전체 워크플로우 Agent Map

```
┌─────────────────────────────────────────────────────────────┐
│                    MoAI-ADK 3-Stage Workflow                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  🏗️ STAGE 1: /alfred:1-spec (SPEC 작성)                     │
├─────────────────────────────────────────────────────────────┤
│  Primary Agent:   spec-builder (🏗️ 설계자)                  │
│  Secondary Agent: git-manager (🌿 정원사)                    │
│                                                               │
│  Input:  제목 또는 자동 제안                                 │
│  Output: SPEC-{ID}/ (spec.md, plan.md, acceptance.md)       │
│          + feature/SPEC-{ID} 브랜치                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  ⚒️ STAGE 2: /alfred:2-build (TDD 구현)                     │
├─────────────────────────────────────────────────────────────┤
│  Primary Agent:   code-builder (💎 수석 개발자)             │
│  Quality Gate:    trust-checker (✅ 품질 보증 리드)          │
│  Secondary Agent: git-manager (🚀 릴리스 엔지니어)           │
│                                                               │
│  Input:  SPEC-{ID}                                           │
│  Output: tests/ + src/ (@TAG 포함)                          │
│          + RED-GREEN-REFACTOR 커밋                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  📚 STAGE 3: /alfred:3-sync (문서 동기화)                    │
├─────────────────────────────────────────────────────────────┤
│  Pre-Validator:   trust-checker (✅ 품질 보증 리드)          │
│  Primary Agent:   doc-syncer (📖 테크니컬 라이터)           │
│  Secondary Agent: git-manager (🚀 릴리스 엔지니어)           │
│                                                               │
│  Input:  변경된 코드 + SPEC                                  │
│  Output: 동기화된 문서 + TAG 인덱스                         │
│          + sync-report.md + PR Ready                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Agents

### 1️⃣ spec-builder (🏗️ 설계자)

**역할**: SPEC 문서 작성 전담

**책임 영역**:
- 프로젝트 문서 분석 (product/structure/tech.md)
- SPEC 후보 발굴 및 우선순위 결정
- EARS 방식 명세서 작성
- Acceptance Criteria 작성 (Given-When-Then)
- SPEC 문서 품질 검증
- @TAG 시스템 적용

**사용 커맨드**: `/alfred:1-spec`

**입력**:
```yaml
mode: analysis | creation
target: "제목" 또는 "SPEC-ID"
project_docs: [product.md, structure.md, tech.md]
```

**출력**:
```
.moai/specs/SPEC-{ID}/
├── spec.md          # EARS 구조 명세서
├── plan.md          # 구현 계획서
└── acceptance.md    # 인수 기준 (Given-When-Then)
```

**호출 방식**:
```bash
# 커맨드 레벨에서 호출
@agent-spec-builder "$ARGUMENTS 분석 및 SPEC 계획 수립"
@agent-spec-builder "$ARGUMENTS SPEC 문서 작성 시작 (사용자 승인 완료)"
```

---

### 2️⃣ code-builder (💎 수석 개발자)

**역할**: TDD 구현 전담

**책임 영역**:
- SPEC 분석 및 복잡도 평가
- 언어별 최적화된 TDD 사이클
- RED → GREEN → REFACTOR 순차 구현
- @TAG 주석 직접 작성
- 테스트 실행 및 검증
- 코드 품질 체크

**사용 커맨드**: `/alfred:2-build`

**입력**:
```yaml
mode: analysis | implement
spec_id: "SPEC-{ID}" | "all"
language: Python | TypeScript | Java | Go | Rust
approved: true | false
```

**출력**:
```
tests/
└── test_*.py        # @TEST:{ID}

src/
└── *.py             # @CODE:{ID} | SPEC | TEST

# TDD 커밋 히스토리:
# 1. RED: 실패하는 테스트 작성
# 2. GREEN: 최소 구현으로 테스트 통과
# 3. REFACTOR: 코드 품질 개선
```

**TDD 도구 매핑**:

| 언어 | 테스트 프레임워크 | 성능 목표 | 커버리지 목표 |
|------|-----------------|----------|---------------|
| Python | pytest + mypy | 사용자 정의 | 85%+ |
| TypeScript | Jest + SuperTest | < 50ms | 90%+ |
| Java | JUnit | < 100ms | 85%+ |
| Go | go test | < 50ms | 85%+ |
| Rust | cargo test | < 30ms | 90%+ |

**호출 방식**:
```bash
# 분석 단계
@agent-code-builder --mode=analysis --spec=$ARGUMENTS

# 구현 단계 (승인 후)
@agent-code-builder --mode=implement --spec=$ARGUMENTS --approved=true
```

---

### 3️⃣ doc-syncer (📖 테크니컬 라이터)

**역할**: 문서 동기화 전담

**책임 영역**:
- Living Document 동기화 (코드 ↔ 문서)
- @TAG 시스템 검증 및 업데이트
- API 문서 자동 생성/갱신
- README 및 아키텍처 문서 동기화
- 문서-코드 일치성 검증
- TAG 추적성 매트릭스 갱신

**사용 커맨드**: `/alfred:3-sync`

**입력**:
```yaml
mode: analysis | sync
target: auto | force | status | project
path: "경로" (선택사항)
approved: true | false
```

**출력**:
```
.moai/reports/
└── sync-report-{ID}.md   # 동기화 결과 보고서

docs/
├── README.md             # 자동 업데이트
└── api/                  # API 문서

.moai/indexes/
└── tags.db               # TAG 인덱스 (선택사항)
```

**동기화 범위**:
- SPEC ↔ 코드 일치성
- @TAG 체인 검증 (`rg '@TAG' -n`)
- 끊어진 링크 탐지 및 수정
- 중복/고아 TAG 정리
- Living Document 갱신

**호출 방식**:
```bash
# 분석 단계
@agent-doc-syncer --mode=analysis --target=$ARGUMENTS

# 동기화 단계 (승인 후)
@agent-doc-syncer --mode=sync --target=$ARGUMENTS --approved=true
```

---

### 4️⃣ git-manager (🚀 릴리스 엔지니어)

**역할**: 모든 Git 작업 전담

**책임 영역**:
- Git 브랜치 생성 및 관리
- 모드별 브랜치 전략 적용
  - **Personal 모드**: main/develop에서 분기
  - **Team 모드**: 항상 develop에서 분기 (GitFlow)
- Git 커밋 생성 (add, commit, push)
- GitHub Issue/PR 생성
- PR 상태 전환 (Draft → Ready)
- PR 자동 머지 (--auto-merge 플래그)
- 브랜치 정리 및 전환
- 체크포인트 생성 및 복원
- 리뷰어 자동 할당

**사용 커맨드**: 모든 Alfred 커맨드

**입력**:
```yaml
mode: checkpoint | commit | branch | pr | merge
branch_strategy: personal | team
commit_message: "메시지"
pr_action: create | ready | merge
```

**Git 전략**:

| 모드 | 베이스 브랜치 | 브랜치명 | PR 대상 | 자동 머지 |
|------|-------------|---------|---------|----------|
| **Personal** | main/develop | feature/SPEC-{ID} | 없음 | 로컬 머지 |
| **Team** | develop | feature/SPEC-{ID} | develop | Squash 머지 |

**PR 자동 머지 워크플로우** (--auto-merge):
1. PR 상태 확인 (CI/CD 통과 체크)
2. gh pr merge --squash --delete-branch
3. git checkout develop && git pull
4. 로컬 feature 브랜치 삭제
5. 다음 작업 준비 완료 알림

**호출 방식**:
```bash
# spec-builder가 완료한 후 브랜치 생성
@agent-git-manager --mode=branch --spec=SPEC-{ID}

# code-builder가 완료한 후 커밋 생성
@agent-git-manager --mode=commit --message="TDD 구현 완료"

# doc-syncer가 완료한 후 PR 전환
@agent-git-manager --mode=pr --action=ready
```

---

### 5️⃣ trust-checker (✅ 품질 보증 리드)

**역할**: 품질 검증 전담 (자동 실행)

**책임 영역**:
- TRUST 5원칙 검증
  - **T (Test First)**: 테스트 커버리지 ≥ 85%
  - **R (Readable)**: 코드 가독성 (파일≤300 LOC, 함수≤50 LOC, 복잡도≤10)
  - **U (Unified)**: 아키텍처 통합성
  - **S (Secured)**: 보안 검증 (입력 검증, 로깅)
  - **T (Trackable)**: @TAG 추적성 무결성
- 린터/포매터 검증
- 보안 취약점 스캔
- 성능 지표 검증
- 품질 리포트 생성

**사용 커맨드**: `/alfred:2-build`, `/alfred:3-sync`

**자동 실행 조건**:

| 커맨드 | 실행 시점 | 모드 | 목적 |
|--------|---------|------|------|
| `2-build` | TDD 완료 후 | `--mode=quick` | 구현 품질 검증 |
| `3-sync` | 동기화 전 | `--mode=quick --pre-sync=true` | 문서화 전 코드 품질 체크 |

**검증 결과**:

✅ **Pass (모든 기준 충족)**: 다음 단계 진행

⚠️ **Warning (일부 미달)**: 경고 + 사용자 선택
- "계속 진행" 또는 "수정 후 재검증"

❌ **Critical (필수 미달)**: 진행 차단
- 개선 필요 항목 상세 보고
- code-builder 재호출 권장

**검증 생략**:
```bash
/alfred:2-build SPEC-001 --skip-quality-check
/alfred:3-sync --skip-pre-check
```

**호출 방식**:
```bash
# 2-build 완료 후 자동 실행
@agent-trust-checker --mode=quick --spec=$ARGUMENTS

# 3-sync 전 조건부 자동 실행 (변경 라인 > 50)
@agent-trust-checker --mode=quick --pre-sync=true
```

**출력**:
```
.moai/reports/
└── trust-check-{SPEC-ID}.md   # 품질 검증 보고서

검증 결과:
✅ Test Coverage: 92% (목표: 85%)
✅ Code Readability: 8.5/10
⚠️ Cyclomatic Complexity: 12 (목표: ≤10) - auth_service.py:45
✅ Security Check: Pass
✅ TAG Traceability: 100%
```

---

## Support Agents

### 6️⃣ tag-agent (🏷️ TAG 관리자)

**역할**: @TAG 시스템 전담 관리

**책임 영역**:
- TAG 스캔 (코드 직접 읽기)
- TAG 관계 검증 (@SPEC → @TEST → @CODE → @DOC)
- 끊어진 링크 탐지
- 중복/고아 TAG 식별
- TAG 무결성 보고

**사용법**:
```bash
@agent-tag-agent --mode=scan --path=src/
@agent-tag-agent --mode=validate --spec=SPEC-{ID}
```

---

### 7️⃣ debug-helper (🔧 디버깅 전문가)

**역할**: 에러 분석 및 해결 전담

**책임 영역**:
- 에러 로그 분석
- 스택 트레이스 해석
- 근본 원인 식별
- 해결 방안 제시
- 개발 가이드 위반 체크

**사용법**:
```bash
@agent-debug-helper --error="에러 메시지"
```

---

### 8️⃣ project-manager (📋 프로젝트 매니저)

**역할**: 프로젝트 초기화 전담

**책임 영역**:
- 프로젝트 킥오프 가이드
- 템플릿 제공 (product/structure/tech.md)
- 초기 구조 설정
- MoAI-ADK 설정 안내

**사용법**:
```bash
/alfred:8-project
```

---

## Agent 협업 구조

### 협업 원칙

```
1️⃣ 단일 책임 원칙
   - 각 agent는 하나의 영역만 전담
   - spec-builder: SPEC 작성만
   - code-builder: TDD 구현만
   - doc-syncer: 문서 동기화만
   - git-manager: Git 작업만

2️⃣ 독립 실행
   - Agent 간 직접 호출 금지
   - 모든 호출은 커맨드 레벨에서만

3️⃣ 순차 오케스트레이션
   - 커맨드가 agent들을 순차적으로 호출
   - 명확한 입력/출력 계약

4️⃣ 품질 게이트
   - trust-checker가 자동으로 품질 검증
   - 단계 진행 전 검증 완료
```

### 협업 플로우 예시

#### /alfred:1-spec 협업

```
┌─────────────────────────────────────────────────────────────┐
│  1️⃣ Phase 1: 분석 단계                                       │
├─────────────────────────────────────────────────────────────┤
│  spec-builder (analysis mode)                               │
│  ├─ product.md 읽기                                          │
│  ├─ SPEC 후보 발굴                                           │
│  └─ 구현 계획 보고서 생성                                    │
│                                                               │
│  >>> 사용자 승인 대기 <<<                                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  2️⃣ Phase 2: SPEC 작성 (승인 후)                             │
├─────────────────────────────────────────────────────────────┤
│  spec-builder (creation mode)                               │
│  ├─ spec.md 작성 (EARS 방식)                                │
│  ├─ plan.md 작성                                             │
│  └─ acceptance.md 작성                                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  3️⃣ Phase 3: Git 작업                                        │
├─────────────────────────────────────────────────────────────┤
│  git-manager                                                 │
│  ├─ feature/SPEC-{ID} 브랜치 생성                           │
│  ├─ SPEC 문서 커밋                                           │
│  ├─ GitHub Issue 생성 (Team 모드)                           │
│  └─ Draft PR 생성 (Team 모드)                               │
└─────────────────────────────────────────────────────────────┘
```

#### /alfred:2-build 협업

```
┌─────────────────────────────────────────────────────────────┐
│  1️⃣ Phase 1: 구현 계획                                       │
├─────────────────────────────────────────────────────────────┤
│  code-builder (analysis mode)                               │
│  ├─ SPEC-{ID}/spec.md 읽기                                  │
│  ├─ 복잡도 평가                                              │
│  └─ TDD 전략 수립                                            │
│                                                               │
│  >>> 사용자 승인 대기 <<<                                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  2️⃣ Phase 2: TDD 구현 (승인 후)                              │
├─────────────────────────────────────────────────────────────┤
│  code-builder (implement mode)                              │
│  ├─ RED: 실패하는 테스트 작성                               │
│  ├─ GREEN: 최소 구현으로 테스트 통과                        │
│  └─ REFACTOR: 코드 품질 개선                                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  2.5️⃣ Phase 2.5: 품질 검증 (자동 실행)                       │
├─────────────────────────────────────────────────────────────┤
│  trust-checker (quick mode)                                 │
│  ├─ TRUST 5원칙 검증                                        │
│  ├─ 테스트 커버리지 확인                                    │
│  ├─ 코드 복잡도 체크                                        │
│  └─ @TAG 추적성 검증                                        │
│                                                               │
│  결과:                                                        │
│  ✅ Pass → Phase 3 진행                                      │
│  ⚠️ Warning → 사용자 선택                                    │
│  ❌ Critical → 진행 차단, 수정 요청                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  3️⃣ Phase 3: Git 작업                                        │
├─────────────────────────────────────────────────────────────┤
│  git-manager                                                 │
│  ├─ 체크포인트 생성 (Personal 모드)                         │
│  ├─ RED 커밋                                                 │
│  ├─ GREEN 커밋                                               │
│  ├─ REFACTOR 커밋                                            │
│  └─ 원격 동기화 (push)                                      │
└─────────────────────────────────────────────────────────────┘
```

#### /alfred:3-sync 협업

```
┌─────────────────────────────────────────────────────────────┐
│  0.5️⃣ Phase 0.5: 사전 품질 검증 (조건부 자동 실행)           │
├─────────────────────────────────────────────────────────────┤
│  조건: 코드 변경 라인 > 50                                   │
│                                                               │
│  trust-checker (quick mode, pre-sync)                       │
│  ├─ Level 1 빠른 스캔 (3-5초)                               │
│  ├─ Critical 이슈 조기 발견                                 │
│  └─ 결과 처리:                                               │
│      ✅ Pass → 동기화 진행                                   │
│      ⚠️ Warning → 경고 후 진행                              │
│      ❌ Critical → 중단, 수정 권장                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  1️⃣ Phase 1: 동기화 계획                                     │
├─────────────────────────────────────────────────────────────┤
│  doc-syncer (analysis mode)                                 │
│  ├─ Git 상태 확인                                            │
│  ├─ 문서-코드 일치성 검사                                   │
│  ├─ @TAG 시스템 검증                                        │
│  └─ 동기화 범위 결정                                        │
│                                                               │
│  >>> 사용자 승인 대기 <<<                                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  2️⃣ Phase 2: 문서 동기화 (승인 후)                           │
├─────────────────────────────────────────────────────────────┤
│  doc-syncer (sync mode)                                     │
│  ├─ Living Document 갱신                                    │
│  ├─ @TAG 체인 검증 (rg '@TAG')                             │
│  ├─ sync-report.md 생성                                     │
│  └─ TAG 인덱스 업데이트                                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  3️⃣ Phase 3: Git 작업 + PR 관리                              │
├─────────────────────────────────────────────────────────────┤
│  git-manager                                                 │
│  ├─ 문서 변경사항 커밋                                      │
│  ├─ PR Ready 전환 (Team 모드)                               │
│  ├─ --auto-merge 플래그 처리:                               │
│  │   ├─ CI/CD 상태 확인                                     │
│  │   ├─ gh pr merge --squash --delete-branch               │
│  │   ├─ git checkout develop && git pull                   │
│  │   └─ 로컬 feature 브랜치 삭제                           │
│  └─ 다음 작업 준비 완료 알림                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 사용 패턴

### 패턴 1: 기본 3단계 워크플로우

```bash
# 1️⃣ SPEC 작성
/alfred:1-spec "JWT 인증 시스템"
# → spec-builder: SPEC 문서 작성
# → git-manager: feature/SPEC-AUTH-001 브랜치 생성

# 2️⃣ TDD 구현
/alfred:2-build SPEC-AUTH-001
# → code-builder: TDD 사이클 (RED-GREEN-REFACTOR)
# → trust-checker: 품질 검증 (자동)
# → git-manager: 단계별 커밋

# 3️⃣ 문서 동기화
/alfred:3-sync
# → trust-checker: 사전 검증 (조건부 자동)
# → doc-syncer: Living Document 동기화
# → git-manager: PR Ready 전환
```

### 패턴 2: 완전 자동화 워크플로우

```bash
# 1️⃣ SPEC 작성
/alfred:1-spec "사용자 관리 기능"

# 2️⃣ TDD 구현
/alfred:2-build SPEC-USER-001

# 3️⃣ 문서 동기화 + 자동 머지
/alfred:3-sync --auto-merge
# → doc-syncer: 문서 동기화
# → git-manager: PR 머지 + 브랜치 정리 + develop 체크아웃
# → 다음 작업 준비 완료! (develop 브랜치에서 시작)
```

### 패턴 3: 품질 검증 강화

```bash
# 품질 검증 포함 TDD 구현
/alfred:2-build SPEC-001
# → trust-checker가 자동으로 품질 검증
# → Critical 이슈 발견 시 진행 차단

# 사전 검증 포함 동기화
/alfred:3-sync
# → 변경 라인 > 50이면 trust-checker 자동 실행
# → 품질 문제 있으면 동기화 중단
```

### 패턴 4: 수동 품질 검증

```bash
# trust-checker 직접 호출
@agent-trust-checker --mode=quick --spec=SPEC-001

# 검증 생략
/alfred:2-build SPEC-001 --skip-quality-check
/alfred:3-sync --skip-pre-check
```

---

## Agent 호출 규칙

### ✅ 올바른 사용

```bash
# 커맨드 레벨에서 agent 호출
/alfred:1-spec "제목"
  → spec-builder 호출
  → git-manager 호출

# agent에 명확한 모드 지정
@agent-code-builder --mode=analysis --spec=SPEC-001
@agent-code-builder --mode=implement --spec=SPEC-001 --approved=true
```

### ❌ 잘못된 사용

```bash
# Agent 내에서 다른 agent 직접 호출 (금지!)
# spec-builder 내부에서:
@agent-git-manager ...  # ❌

# 모드 없이 호출
@agent-code-builder SPEC-001  # ❌
```

---

## Agent 디버깅

### Agent 실행 로그 확인

```bash
# 최근 agent 실행 로그
rg "@agent-" .moai/reports/

# 특정 agent 호출 기록
rg "@agent-spec-builder" .moai/reports/
rg "@agent-code-builder" .moai/reports/
```

### Agent 상태 확인

```bash
# 현재 프로젝트 상태
moai status

# 진행 중인 작업 확인
git status
git log --oneline -10
```

---

## 다음 단계

1. **기본 워크플로우 실습**: 3단계 워크플로우로 간단한 기능 구현
2. **Agent 협업 이해**: 각 단계에서 어떤 agent가 실행되는지 관찰
3. **품질 게이트 활용**: trust-checker의 자동 검증 활용
4. **자동화 극대화**: --auto-merge로 완전 자동화 워크플로우 경험

---

## 참고 문서

- `.moai/guides/moai-adk-usage-guide.md` - MoAI-ADK 전체 활용 가이드
- `.moai/memory/development-guide.md` - 개발 가이드 전체
- `.claude/commands/alfred/` - Alfred 커맨드 상세 설명

---

**작성일**: 2025-10-10
**버전**: v0.2.13
**문서 관리**: MoAI-ADK Development Team
