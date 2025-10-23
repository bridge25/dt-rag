# MoAI-ADK 활용 가이드

**작성일**: 2025-10-10
**버전**: v0.2.13
**대상**: dt-rag 프로젝트 개발자

---

## 📖 목차

1. [MoAI-ADK란?](#moai-adk란)
2. [핵심 개념](#핵심-개념)
3. [3단계 워크플로우](#3단계-워크플로우)
4. [실전 활용법](#실전-활용법)
5. [@TAG 시스템 마스터하기](#tag-시스템-마스터하기)
6. [TRUST 원칙 적용](#trust-원칙-적용)
7. [CLI 명령어](#cli-명령어)
8. [팁 & 트릭](#팁--트릭)

---

## MoAI-ADK란?

**MoAI-ADK (Modu-AI's Agentic Development Kit)**는 AI 에이전트와 개발자가 협업하여 고품질 소프트웨어를 체계적으로 개발할 수 있게 해주는 **SPEC 우선 TDD 프레임워크**입니다.

### 핵심 철학

```
"명세 없으면 코드 없다. 테스트 없으면 구현 없다."
```

### 주요 특징

| 특징 | 설명 |
|------|------|
| **SPEC 우선** | 모든 개발은 SPEC 문서부터 시작 |
| **TDD 통합** | Red-Green-Refactor 사이클 완벽 지원 |
| **@TAG 추적성** | SPEC → TEST → CODE → DOC 완전 추적 |
| **다언어 지원** | Python, TypeScript, Java, Go, Rust 등 |
| **AI 친화적** | Claude Code 등 AI 에이전트 최적화 |

---

## 핵심 개념

### 1. SPEC (Specification)

**SPEC는 개발의 시작점이자 진실의 원천입니다.**

```
.moai/specs/SPEC-{ID}/
├── spec.md          # 핵심 명세 (EARS 방식)
├── plan.md          # 구현 계획
└── acceptance.md    # 검수 기준
```

**SPEC의 역할**:
- ✅ 무엇을 만들지 명확히 정의
- ✅ 팀원 간 합의된 요구사항
- ✅ 테스트와 구현의 기준
- ✅ 문서화의 출처

### 2. @TAG 시스템

**모든 코드와 테스트를 SPEC에 연결하는 추적 시스템**

```
@SPEC:ID → @TEST:ID → @CODE:ID → @DOC:ID
```

**예시**:
```python
# @CODE:AUTH-001 | SPEC: SPEC-AUTH-001.md | TEST: tests/auth/test_service.py
def authenticate_user(username: str, password: str) -> Token:
    """사용자 인증 및 JWT 토큰 발급"""
    # @TEST:AUTH-001에서 정의된 테스트 케이스 통과
    ...
```

### 3. EARS 요구사항 작성법

**EARS (Easy Approach to Requirements Syntax)**: 명확하고 테스트 가능한 요구사항 작성 방법

#### 5가지 구문

| 구문 | 형식 | 예시 |
|------|------|------|
| **기본** | 시스템은 [기능]을 제공해야 한다 | 시스템은 사용자 인증 기능을 제공해야 한다 |
| **이벤트** | WHEN [조건]이면, 시스템은 [동작]해야 한다 | WHEN 로그인하면, 시스템은 JWT 토큰을 발급해야 한다 |
| **상태** | WHILE [상태]일 때, 시스템은 [동작]해야 한다 | WHILE 인증된 상태일 때, 시스템은 보호된 리소스 접근을 허용해야 한다 |
| **선택** | WHERE [조건]이면, 시스템은 [동작]할 수 있다 | WHERE 리프레시 토큰이 있으면, 시스템은 액세스 토큰을 갱신할 수 있다 |
| **제약** | IF [조건]이면, 시스템은 [제약]해야 한다 | IF 토큰이 만료되면, 시스템은 접근을 거부해야 한다 |

### 4. TRUST 5원칙

MoAI-ADK의 품질 보증 체계:

1. **T**est-driven (테스트 주도)
2. **R**eadability-driven (가독성 주도)
3. **U**nified Architecture (통합 아키텍처)
4. **S**ecurity-first (보안 우선)
5. **T**raceability (추적성)

---

## 3단계 워크플로우

MoAI-ADK의 핵심 개발 루프는 **3단계 Alfred 커맨드**로 구성됩니다.

### 1️⃣ SPEC 작성: `/alfred:1-spec`

**목적**: 구현할 기능의 명세를 작성합니다.

**사용 시점**:
- ✅ 새로운 기능을 추가할 때
- ✅ 버그를 수정할 때 (명세 먼저!)
- ✅ 리팩토링을 계획할 때

**명령어 형식**:
```bash
/alfred:1-spec 제목1 제목2 ... | SPEC-ID 수정내용
```

**예시**:
```bash
# 새 SPEC 생성
/alfred:1-spec JWT 인증 시스템 구현

# 기존 SPEC 수정
/alfred:1-spec SPEC-AUTH-001 리프레시 토큰 기능 추가
```

**출력물**:
```
.moai/specs/SPEC-AUTH-001/
├── spec.md          # EARS 방식 요구사항
├── plan.md          # 구현 계획 및 작업 분해
└── acceptance.md    # 검수 기준 (Definition of Done)
```

**SPEC 구조**:
```markdown
---
id: AUTH-001
version: 0.1.0
status: draft
created: 2025-10-10
updated: 2025-10-10
author: @username
priority: high
category: feature
---

# @SPEC:AUTH-001: JWT 인증 시스템

## HISTORY
### v0.1.0 (2025-10-10)
- **INITIAL**: JWT 기반 인증 시스템 명세 작성
- **AUTHOR**: @username
- **SCOPE**: 토큰 발급, 검증, 갱신

## EARS 요구사항

### Ubiquitous Requirements (기본 요구사항)
- 시스템은 JWT 기반 인증 기능을 제공해야 한다
- 시스템은 토큰 검증 기능을 제공해야 한다

### Event-driven Requirements (이벤트 기반)
- WHEN 사용자가 유효한 자격증명으로 로그인하면, 시스템은 JWT 토큰을 발급해야 한다
- WHEN 토큰이 만료되면, 시스템은 401 에러를 반환해야 한다

### Constraints (제약사항)
- 액세스 토큰 만료시간은 15분을 초과하지 않아야 한다
- 토큰은 HMAC-SHA256으로 서명되어야 한다
```

---

### 2️⃣ TDD 구현: `/alfred:2-build`

**목적**: SPEC을 기반으로 TDD 방식으로 코드를 구현합니다.

**사용 시점**:
- ✅ SPEC 작성이 완료된 후
- ✅ Red-Green-Refactor 사이클 진행 시

**명령어 형식**:
```bash
/alfred:2-build SPEC-ID
/alfred:2-build all  # 모든 draft SPEC 구현
```

**예시**:
```bash
/alfred:2-build SPEC-AUTH-001
```

**TDD 사이클**:

```
1. RED (실패하는 테스트 작성)
   ↓
   tests/auth/test_service.py
   @TEST:AUTH-001 | SPEC: SPEC-AUTH-001.md

2. GREEN (최소한의 구현)
   ↓
   src/auth/service.py
   @CODE:AUTH-001 | SPEC: SPEC-AUTH-001.md | TEST: tests/auth/test_service.py

3. REFACTOR (품질 개선)
   ↓
   @CODE:AUTH-001 개선
   - 가독성 향상
   - 중복 제거
   - 성능 최적화
```

**언어별 TDD 도구**:

| 언어 | 테스트 프레임워크 | 실행 명령어 |
|------|-----------------|------------|
| Python | pytest | `pytest tests/` |
| TypeScript | Vitest | `npm run test` |
| Java | JUnit | `mvn test` |
| Go | go test | `go test ./...` |
| Rust | cargo test | `cargo test` |

**출력물**:
```
tests/auth/
├── test_service.py     # @TEST:AUTH-001
└── test_token.py       # @TEST:AUTH-002

src/auth/
├── service.py          # @CODE:AUTH-001
└── token.py            # @CODE:AUTH-002
```

---

### 3️⃣ 문서 동기화: `/alfred:3-sync`

**목적**: 구현 완료 후 문서를 업데이트하고 추적성을 검증합니다.

**사용 시점**:
- ✅ TDD 구현이 완료된 후
- ✅ PR 생성 전
- ✅ SPEC 상태를 completed로 전환할 때

**명령어 형식**:
```bash
/alfred:3-sync 모드 대상경로

# 모드:
# - auto: 자동 동기화 (기본값)
# - force: 강제 동기화
# - status: 현재 상태만 확인
# - project: 전체 프로젝트 동기화
```

**예시**:
```bash
# 기본 동기화
/alfred:3-sync auto .

# 전체 프로젝트 동기화
/alfred:3-sync project .

# 상태 확인만
/alfred:3-sync status .
```

**동기화 작업**:
1. **@TAG 검증**: 모든 TAG 관계 확인
2. **Living Document 생성**: README, CHANGELOG 업데이트
3. **SPEC 상태 업데이트**: draft → active → completed
4. **추적성 보고서**: `.moai/reports/sync-report-{ID}.md` 생성

**출력물**:
```
.moai/reports/
└── sync-report-AUTH-001.md   # 동기화 보고서

docs/
├── README.md                  # 자동 업데이트
└── auth/
    └── jwt-guide.md          # @DOC:AUTH-001
```

---

## 실전 활용법

### 시나리오 1: 새로운 기능 추가

**상황**: 사용자 관리 기능을 추가하려고 합니다.

**단계별 진행**:

```bash
# 1. SPEC 작성
/alfred:1-spec 사용자 관리 기능

# → .moai/specs/SPEC-USER-001/ 생성됨
# → spec.md에 EARS 요구사항 작성

# 2. SPEC 확인 및 수정
# spec.md를 열어서 요구사항 상세화
# - Ubiquitous Requirements 작성
# - Event-driven Requirements 작성
# - Constraints 정의

# 3. TDD 구현
/alfred:2-build SPEC-USER-001

# → tests/user/test_service.py (@TEST:USER-001)
# → src/user/service.py (@CODE:USER-001)

# 4. 테스트 실행 및 구현
pytest tests/user/

# 5. 문서 동기화
/alfred:3-sync auto .

# → SPEC 상태: draft → completed
# → docs/user/user-guide.md (@DOC:USER-001) 생성
```

---

### 시나리오 2: 버그 수정

**상황**: 인증 시스템에서 토큰 갱신 버그 발견

**단계별 진행**:

```bash
# 1. 버그를 위한 SPEC 생성
/alfred:1-spec 토큰 갱신 버그 수정

# → .moai/specs/SPEC-BUGFIX-001/ 생성

# 2. spec.md에 버그 상세 기술
# - 현재 동작 (버그)
# - 기대 동작 (정상)
# - 재현 방법

# 3. 실패하는 테스트 먼저 작성 (RED)
/alfred:2-build SPEC-BUGFIX-001

# → tests/auth/test_token_refresh.py
#    def test_token_refresh_with_valid_refresh_token():
#        # 현재는 실패하는 테스트

# 4. 버그 수정 (GREEN)
# src/auth/token.py 수정
# @CODE:BUGFIX-001

# 5. 테스트 통과 확인
pytest tests/auth/test_token_refresh.py

# 6. 문서 동기화
/alfred:3-sync auto .
```

---

### 시나리오 3: 리팩토링

**상황**: 검색 엔진 성능 개선을 위한 리팩토링

**단계별 진행**:

```bash
# 1. 리팩토링 SPEC 작성
/alfred:1-spec 검색 엔진 성능 최적화

# → .moai/specs/SPEC-REFACTOR-001/

# 2. spec.md에 리팩토링 목표 작성
# - 현재 성능 지표 (baseline)
# - 목표 성능 지표 (target)
# - 개선 방법론

# 3. 기존 테스트가 여전히 통과하는지 확인
pytest tests/search/

# 4. 리팩토링 진행
/alfred:2-build SPEC-REFACTOR-001

# → @CODE:REFACTOR-001로 태그하면서 리팩토링

# 5. 모든 테스트 통과 확인
pytest tests/

# 6. 성능 측정 및 문서화
/alfred:3-sync auto .
```

---

### 시나리오 4: 기존 SPEC 확장

**상황**: SPEC-AUTH-001에 2FA 기능 추가

**단계별 진행**:

```bash
# 1. 기존 SPEC 수정
/alfred:1-spec SPEC-AUTH-001 2FA 기능 추가

# → SPEC-AUTH-001/spec.md 업데이트
# → version: 0.1.0 → 0.2.0 (MINOR 증가)

# 2. HISTORY 섹션에 기록
# ### v0.2.0 (2025-10-10)
# - **ADDED**: 2FA (Two-Factor Authentication) 기능 추가
# - **AUTHOR**: @username
# - **REASON**: 보안 강화 요구사항

# 3. TDD 구현
/alfred:2-build SPEC-AUTH-001

# → tests/auth/test_2fa.py (@TEST:AUTH-001:2FA)
# → src/auth/2fa.py (@CODE:AUTH-001:2FA)

# 4. 문서 동기화
/alfred:3-sync auto .
```

---

## @TAG 시스템 마스터하기

### TAG 명명 규칙

**형식**: `<도메인>-<3자리 숫자>`

**예시**:
- `AUTH-001` ✅
- `SEARCH-042` ✅
- `API-123` ✅
- `REFACTOR-005` ✅

**디렉토리 명명**:
```
.moai/specs/SPEC-{ID}/
```

**예시**:
- `.moai/specs/SPEC-AUTH-001/` ✅
- `.moai/specs/SPEC-SEARCH-042/` ✅
- `.moai/specs/SPEC-REFACTOR-005/` ✅

### TAG 사용 예시

#### SPEC 문서
```markdown
---
id: AUTH-001
version: 0.1.0
status: active
---

# @SPEC:AUTH-001: JWT 인증 시스템

## HISTORY
### v0.1.0 (2025-10-10)
- **INITIAL**: JWT 인증 시스템 명세 작성
```

#### 테스트 코드
```python
# tests/auth/test_service.py
# @TEST:AUTH-001 | SPEC: SPEC-AUTH-001.md

import pytest
from auth.service import authenticate_user

class TestAuthentication:
    """@SPEC:AUTH-001 JWT 인증 테스트"""

    def test_authenticate_with_valid_credentials(self):
        """
        @TEST:AUTH-001:VALID
        유효한 자격증명으로 인증 시 JWT 토큰 발급
        """
        token = authenticate_user("user@example.com", "password123")
        assert token is not None
        assert token.is_valid()
```

#### 구현 코드
```python
# src/auth/service.py
# @CODE:AUTH-001 | SPEC: SPEC-AUTH-001.md | TEST: tests/auth/test_service.py

from typing import Optional
from .token import create_jwt_token
from .models import Token

def authenticate_user(username: str, password: str) -> Optional[Token]:
    """
    @CODE:AUTH-001:API
    사용자 인증 및 JWT 토큰 발급

    Args:
        username: 사용자 이메일
        password: 비밀번호

    Returns:
        Token: JWT 액세스 토큰 (인증 실패 시 None)

    Raises:
        ValidationError: 입력값이 유효하지 않을 때
    """
    # @SPEC:AUTH-001 Event-driven: WHEN 유효한 자격증명이면...
    if validate_credentials(username, password):
        return create_jwt_token(username)
    return None
```

#### 문서
```markdown
<!-- docs/auth/jwt-guide.md -->
<!-- @DOC:AUTH-001 | SPEC: SPEC-AUTH-001.md -->

# JWT 인증 가이드

> **@SPEC:AUTH-001** 기반 구현

## 개요
JWT (JSON Web Token) 기반 인증 시스템입니다.

## 사용 방법
...
```

### TAG 검증하기

```bash
# 모든 TAG 스캔
rg '@(SPEC|TEST|CODE|DOC):' -n .moai/specs/ tests/ src/ docs/

# 특정 SPEC의 모든 참조 찾기
rg '@.*:AUTH-001' -n

# 깨진 TAG 링크 찾기 (SPEC이 없는데 CODE만 있는 경우)
rg '@CODE:' src/ | while read line; do
  id=$(echo $line | grep -oP '(?<=@CODE:)[A-Z]+-\d+')
  if [ ! -d ".moai/specs/SPEC-$id" ]; then
    echo "Missing SPEC: $id"
  fi
done
```

---

## TRUST 원칙 적용

### T - Test-driven (테스트 주도)

**원칙**: SPEC → TEST → CODE 순서 엄수

**실전 적용**:
```python
# 1. SPEC 작성 (.moai/specs/SPEC-CALC-001/spec.md)
# "시스템은 두 숫자의 합을 계산하는 기능을 제공해야 한다"

# 2. RED: 실패하는 테스트
# tests/test_calculator.py
# @TEST:CALC-001 | SPEC: SPEC-CALC-001.md
def test_add_two_numbers():
    assert add(2, 3) == 5  # NameError: add is not defined

# 3. GREEN: 최소 구현
# src/calculator.py
# @CODE:CALC-001 | SPEC: SPEC-CALC-001.md | TEST: tests/test_calculator.py
def add(a, b):
    return a + b

# 4. REFACTOR: 품질 개선
def add(a: int, b: int) -> int:
    """@CODE:CALC-001 두 정수의 합을 계산"""
    return a + b
```

---

### R - Readability (가독성)

**원칙**: SPEC 용어를 코드에 그대로 반영

**나쁜 예**:
```python
# SPEC: "시스템은 사용자 인증 기능을 제공해야 한다"
def process(u, p):  # ❌ SPEC 용어와 불일치
    return check(u, p)
```

**좋은 예**:
```python
# SPEC: "시스템은 사용자 인증 기능을 제공해야 한다"
def authenticate_user(username: str, password: str) -> bool:  # ✅ SPEC 용어 사용
    """@CODE:AUTH-001 사용자 인증"""
    return verify_credentials(username, password)
```

---

### U - Unified Architecture (통합 아키텍처)

**원칙**: SPEC이 아키텍처 경계를 정의

**프로젝트 구조 (SPEC 기반)**:
```
dt-rag/
├── .moai/
│   └── specs/
│       ├── SPEC-API-001/      # API 레이어
│       ├── SPEC-SEARCH-001/   # 검색 엔진
│       ├── SPEC-DATABASE-001/ # 데이터베이스
│       └── SPEC-AUTH-001/     # 인증 시스템
│
├── src/
│   ├── api/           # @CODE:API-001
│   ├── search/        # @CODE:SEARCH-001
│   ├── database/      # @CODE:DATABASE-001
│   └── auth/          # @CODE:AUTH-001
│
└── tests/
    ├── api/           # @TEST:API-001
    ├── search/        # @TEST:SEARCH-001
    ├── database/      # @TEST:DATABASE-001
    └── auth/          # @TEST:AUTH-001
```

---

### S - Security-first (보안 우선)

**원칙**: SPEC에 보안 요구사항 명시, TDD 단계에서 구현

**SPEC 예시**:
```markdown
## Security Requirements

### Constraints (제약사항)
- IF 비밀번호가 8자 미만이면, 시스템은 거부해야 한다
- 비밀번호는 bcrypt로 해시되어 저장되어야 한다
- API 키는 환경 변수로만 관리되어야 한다

### Threat Model
- **SQL Injection**: Parameterized queries 사용
- **XSS**: 입력값 sanitization
- **CSRF**: CSRF 토큰 검증
```

**테스트 예시**:
```python
# @TEST:AUTH-001:SECURITY | SPEC: SPEC-AUTH-001.md
class TestSecurityRequirements:
    def test_reject_short_password(self):
        """비밀번호 8자 미만 거부"""
        with pytest.raises(ValidationError):
            create_user("user@test.com", "abc123")  # 6자

    def test_password_is_hashed(self):
        """비밀번호 해시 저장"""
        user = create_user("user@test.com", "password123")
        assert user.password != "password123"
        assert user.password.startswith("$2b$")  # bcrypt
```

---

### T - Traceability (추적성)

**원칙**: 코드 스캔으로 TAG 추적성 보장

**추적성 검증**:
```bash
# 1. 모든 TAG 수집
rg '@(SPEC|TEST|CODE|DOC):' -n --json | jq -r '.data.lines.text'

# 2. SPEC → CODE 추적
for spec in .moai/specs/SPEC-*/; do
  id=$(basename $spec | sed 's/SPEC-//')
  echo "=== $id ==="
  echo "SPEC: $(ls $spec/*.md)"
  echo "TEST: $(rg -l "@TEST:$id" tests/)"
  echo "CODE: $(rg -l "@CODE:$id" src/)"
  echo "DOC: $(rg -l "@DOC:$id" docs/)"
done

# 3. 고아 CODE 찾기 (SPEC 없는 구현)
rg '@CODE:([A-Z]+-\d+)' src/ -o --no-filename | sort -u | while read tag; do
  id=$(echo $tag | sed 's/@CODE://')
  if [ ! -d ".moai/specs/SPEC-$id" ]; then
    echo "Orphan CODE: $tag"
  fi
done
```

---

## CLI 명령어

### moai doctor

**목적**: 시스템 환경 진단

```bash
moai doctor

# 출력 예시:
# ✅ Node.js: v18.17.0
# ✅ Python: 3.12.3
# ✅ Git: 2.34.1
# ✅ pytest: 8.0.0
# ⚠️  TypeScript: Not found
```

**사용 시점**:
- 프로젝트 초기 설정 시
- 환경 문제 디버깅 시

---

### moai init

**목적**: 새 MoAI 프로젝트 초기화

```bash
moai init [project-name]

# 대화형 설정:
# ? Project name: my-project
# ? Project type: Full
# ? Language: TypeScript
# ? Git integration: Yes
```

**생성되는 구조**:
```
my-project/
├── .moai/
│   ├── config.json
│   ├── project/
│   │   ├── product.md
│   │   ├── structure.md
│   │   └── tech.md
│   ├── specs/
│   ├── memory/
│   └── reports/
└── .claude/
    └── commands/
        └── alfred/
```

---

### moai status

**목적**: 프로젝트 상태 확인

```bash
moai status

# 출력 예시:
# 📊 MoAI-ADK Project Status
#
# 📂 Project: /path/to/dt-rag
# 🗿 MoAI System: ✅
# 📝 SPEC Count: 19
#    - draft: 0
#    - active: 3
#    - completed: 16
# 🔗 Git: ✅ (master branch)
```

**사용 시점**:
- 현재 프로젝트 상태 확인
- SPEC 진행률 점검

---

### moai restore

**목적**: 백업에서 프로젝트 복원

```bash
moai restore <backup-path>

# 예시:
moai restore .moai-backup/2025-10-09-00-23-23/
```

**사용 시점**:
- 실수로 SPEC 삭제 시
- 이전 상태로 롤백 시

---

## 팁 & 트릭

### 💡 Tip 1: SPEC 먼저, 코드 나중에

**잘못된 순서**:
```
코드 작성 → 나중에 SPEC 추가 ❌
```

**올바른 순서**:
```
SPEC 작성 → TDD 구현 → 문서 동기화 ✅
```

**이유**:
- SPEC 없이 코드를 작성하면 요구사항이 불명확
- 나중에 SPEC를 역으로 작성하면 추적성 손실
- TDD 사이클 깨짐

---

### 💡 Tip 2: EARS로 명확하게

**모호한 요구사항**:
```markdown
- 시스템은 빠르게 동작해야 한다 ❌
```

**EARS 방식**:
```markdown
### Constraints
- 검색 응답 시간은 4초를 초과하지 않아야 한다 ✅
- p95 latency는 2초 이하여야 한다 ✅
```

**이유**:
- "빠르게"는 측정 불가능
- EARS 제약사항으로 구체적인 기준 제시
- 테스트 작성 가능

---

### 💡 Tip 3: TAG는 영구 불변

**❌ 하지 말 것**:
```
SPEC-AUTH-001 → SPEC-AUTH-002로 변경
```

**✅ 해야 할 것**:
```
SPEC-AUTH-001:
  - version: 0.1.0 → 0.2.0
  - HISTORY에 변경 기록
```

**이유**:
- TAG ID는 추적성의 핵심
- ID 변경 시 모든 참조가 깨짐
- version과 HISTORY로 변경 관리

---

### 💡 Tip 4: 작은 SPEC으로 시작

**큰 SPEC (❌)**:
```
SPEC-AUTH-001: 완전한 인증 시스템
- 로그인
- 회원가입
- 비밀번호 재설정
- 이메일 인증
- 2FA
- OAuth
```

**작은 SPEC들 (✅)**:
```
SPEC-AUTH-001: 기본 로그인
SPEC-AUTH-002: 회원가입
SPEC-AUTH-003: 비밀번호 재설정
SPEC-AUTH-004: 2FA
```

**이유**:
- 작은 SPEC은 빠르게 완료 가능
- 명확한 scope
- 병렬 작업 가능

---

### 💡 Tip 5: Context Engineering 활용

**문제**: Claude Code가 너무 많은 문서를 로드해서 느림

**해결책**: JIT (Just-in-Time) Retrieval
```bash
# ❌ 모든 SPEC을 한 번에 로드하지 마세요
Read .moai/specs/SPEC-*/spec.md  # 19개 파일

# ✅ 필요한 SPEC만 로드하세요
Read .moai/specs/SPEC-AUTH-001/spec.md  # 1개 파일
```

**Compaction 활용**:
- 토큰 사용량 > 140,000 (70%) 시
- `/clear` 또는 `/new` 명령으로 새 세션 시작
- 요약본을 새 세션의 시작점으로 사용

---

### 💡 Tip 6: 리팩토링도 SPEC으로

**리팩토링 SPEC 예시**:
```markdown
---
id: REFACTOR-001
version: 0.1.0
category: refactor
---

# @SPEC:REFACTOR-001: 검색 엔진 성능 최적화

## 현재 상태 (Baseline)
- p95 latency: 3.5초
- 평균 응답 시간: 1.8초

## 목표 (Target)
- p95 latency: 2.0초 이하
- 평균 응답 시간: 1.0초 이하

## 개선 방법
1. 벡터 검색 캐싱
2. BM25 인덱스 최적화
3. 데이터베이스 쿼리 개선

## 제약사항
- 기존 테스트는 모두 통과해야 한다
- 검색 정확도는 유지되어야 한다
```

---

### 💡 Tip 7: HISTORY는 소중한 자산

**HISTORY 작성 예시**:
```markdown
## HISTORY

### v0.3.0 (2025-10-15)
- **ADDED**: 리프레시 토큰 기능 추가
- **AUTHOR**: @alice
- **REVIEW**: @bob (approved)
- **REASON**: 사용자 경험 개선 - 로그인 유지 시간 연장
- **RELATED**: Issue #123

### v0.2.1 (2025-10-12)
- **FIXED**: 토큰 만료 시간 계산 버그 수정
- **AUTHOR**: @charlie
- **REASON**: 토큰이 15분이 아닌 15초로 설정됨

### v0.2.0 (2025-10-10)
- **ADDED**: 2FA 기능 추가
- **AUTHOR**: @dave
- **BREAKING**: 기존 로그인 API 시그니처 변경
- **MIGRATION**: docs/migration-guide.md 참조

### v0.1.0 (2025-10-01)
- **INITIAL**: JWT 인증 시스템 명세 작성
- **AUTHOR**: @eve
```

**활용**:
```bash
# SPEC의 변경 이력 확인
rg -A 30 "## HISTORY" .moai/specs/SPEC-AUTH-001/spec.md

# 누가 언제 무엇을 변경했는지 추적
rg "AUTHOR: @alice" .moai/specs/ -A 2

# Breaking changes 찾기
rg "BREAKING" .moai/specs/
```

---

### 💡 Tip 8: 디버깅도 SPEC 기반

**버그 발견 시**:
1. ✅ SPEC 확인: 요구사항이 명확한가?
2. ✅ TEST 확인: 테스트가 요구사항을 커버하는가?
3. ✅ CODE 확인: 구현이 SPEC과 일치하는가?
4. ✅ TAG 확인: 추적성이 유지되는가?

**디버깅 명령어**:
```bash
# 1. 관련 SPEC 찾기
rg "authentication" .moai/specs/

# 2. 관련 테스트 찾기
rg "@TEST:AUTH" tests/

# 3. 관련 코드 찾기
rg "@CODE:AUTH" src/

# 4. TAG 관계 확인
rg "@.*:AUTH-001" -n
```

---

## 실전 체크리스트

### ✅ 개발 시작 전

- [ ] `.moai/project/product.md` 읽고 프로젝트 이해
- [ ] `.moai/memory/development-guide.md` 숙지
- [ ] `moai status`로 현재 SPEC 진행률 확인
- [ ] 관련 SPEC 문서 읽기

### ✅ SPEC 작성 시

- [ ] EARS 5가지 구문 활용
- [ ] HISTORY 섹션 작성
- [ ] 측정 가능한 기준 정의
- [ ] 보안 요구사항 포함
- [ ] 중복 SPEC 확인 (`rg "@SPEC:{ID}"`)

### ✅ TDD 구현 시

- [ ] RED: 실패하는 테스트 먼저
- [ ] GREEN: 최소한의 구현
- [ ] REFACTOR: 품질 개선
- [ ] @TAG 주석 추가
- [ ] 테스트 커버리지 85% 이상

### ✅ 문서 동기화 시

- [ ] `/alfred:3-sync` 실행
- [ ] sync-report 확인
- [ ] TAG 추적성 검증
- [ ] Living Document 업데이트
- [ ] SPEC 상태 전환 (draft → completed)

### ✅ PR 생성 전

- [ ] 모든 테스트 통과
- [ ] Linter 통과
- [ ] @TAG 관계 검증
- [ ] SPEC과 코드 일치성 확인
- [ ] 문서 업데이트 완료

---

## 자주 묻는 질문

### Q1: SPEC를 너무 자세하게 작성해야 하나요?

**A**: 아니요. **Just Enough Documentation** 원칙을 따르세요.

- ✅ 요구사항이 명확하고 테스트 가능하면 충분
- ✅ EARS 5가지 구문으로 핵심만 작성
- ❌ 구현 세부사항까지 SPEC에 작성하지 않음

---

### Q2: 이미 작성된 코드는 어떻게 하나요?

**A**: 점진적으로 SPEC를 역으로 작성하세요.

1. 기존 코드 분석
2. 요구사항 추출
3. SPEC 작성 (역공학)
4. @TAG 추가
5. 테스트 보강

---

### Q3: TAG ID는 어떻게 정하나요?

**A**: 도메인별로 일련번호를 사용하세요.

```
AUTH-001, AUTH-002, AUTH-003, ...
SEARCH-001, SEARCH-002, SEARCH-003, ...
API-001, API-002, API-003, ...
```

---

### Q4: SPEC이 변경되면 어떻게 하나요?

**A**: version과 HISTORY를 업데이트하세요.

```markdown
---
version: 0.2.0  # Minor 증가
---

## HISTORY
### v0.2.0 (2025-10-10)
- **ADDED**: 새 기능 추가
- **AUTHOR**: @username
```

---

### Q5: 여러 개발자가 동시에 작업할 때는?

**A**: SPEC 단위로 작업을 분리하세요.

```bash
# Developer A
/alfred:1-spec 로그인 기능
/alfred:2-build SPEC-AUTH-001

# Developer B
/alfred:1-spec 회원가입 기능
/alfred:2-build SPEC-AUTH-002

# 독립적인 SPEC이므로 충돌 없음
```

---

## 다음 단계

### 1. 프로젝트 상태 확인
```bash
moai status
moai doctor
```

### 2. 첫 SPEC 작성해보기
```bash
/alfred:1-spec 내 첫 기능
```

### 3. TDD로 구현해보기
```bash
/alfred:2-build SPEC-001
```

### 4. 문서 동기화
```bash
/alfred:3-sync auto .
```

---

## 참고 문서

- `.moai/memory/development-guide.md` - 전체 개발 가이드
- `.moai/memory/systematic-validation-strategy.md` - 검증 방법론
- `.moai/project/product.md` - 프로젝트 제품 정의
- `.moai/project/tech.md` - 기술 스택 문서

---

**작성일**: 2025-10-10
**버전**: v0.2.13
**문서 관리**: MoAI-ADK Development Team

_이 가이드는 실전 경험을 바탕으로 지속적으로 업데이트됩니다._
