---
id: HOOKS-REFACTOR-001
version: v1.0.0
status: completed
created: 2025-10-24
author: "@Alfred"
priority: high
domain: Hooks
related_specs:
  - SPEC-CICD-001
tags:
  - hooks
  - architecture
  - refactoring
  - srp
---

# SPEC-HOOKS-REFACTOR-001: Alfred Hooks 라우터 리팩토링

## 📋 Overview

**목적**: Claude Code 이벤트를 적절한 핸들러로 라우팅하는 중앙 라우터 시스템

**비즈니스 가치**: MoAI-ADK Hook 시스템의 중추 - 모든 Claude Code 이벤트를 받아 적절한 핸들러로 분배하여 확장 가능하고 유지보수 가능한 이벤트 처리 아키텍처 제공

**범위**:
- 8개 이벤트 타입 라우팅 (SessionStart, UserPromptSubmit, SessionEnd, PreToolUse, PostToolUse, Notification, Stop, SubagentStop)
- 3단계 모듈 분리: Router → Event Handlers → Business Logic
- JSON I/O 처리 (stdin/stdout)
- 에러 처리 및 exit code 표준화

---

## 🏷️ TAG References

### Primary TAG
- **@CODE:HOOKS-REFACTOR-001** - `.claude/hooks/alfred/alfred_hooks.py`

### Implementation Structure

#### Router Layer
- `alfred_hooks.py` - Main entry point, event routing (153 LOC)

#### Event Handlers Layer (`handlers/`)
- `session.py` - SessionStart, SessionEnd handlers
- `user.py` - UserPromptSubmit handler
- `tool.py` - PreToolUse, PostToolUse handlers
- `notification.py` - Notification, Stop, SubagentStop handlers
- `__init__.py` - Handler exports

#### Business Logic Layer (`core/`)
- `project.py` - Language detection, Git info, SPEC progress
- `context.py` - JIT Retrieval, workflow context
- `checkpoint.py` - Event-Driven Checkpoint system
- `__init__.py` - Core exports

---

## 🎯 Environment

**WHEN** MoAI-ADK Hook 시스템이 Claude Code 이벤트를 수신할 때

**Operational Context**:
- Claude Code가 이벤트 발생 시 자동으로 Hook 스크립트 호출
- Python 3.10+ 환경
- stdin을 통한 JSON payload 수신
- stdout으로 JSON 응답 반환

**System State**:
- `.moai/` 디렉토리 구조 존재
- 프로젝트 메타데이터 (`.moai/config.json`) 접근 가능
- Git 저장소 (선택적)

---

## 💡 Assumptions

1. **입력 형식**: 모든 이벤트는 유효한 JSON 형식으로 stdin을 통해 전달됨
2. **이벤트 타입**: 지원되는 8개 이벤트 타입 중 하나만 CLI 인자로 전달됨
3. **에러 처리**: 핸들러는 예외를 발생시킬 수 있으며 라우터가 최종 에러 처리 담당
4. **단일 책임**: 각 핸들러는 특정 이벤트 타입만 처리 (SRP 준수)
5. **비동기 미지원**: 현재 구현은 동기 처리만 지원 (향후 asyncio 고려 가능)

---

## 📌 Requirements

### FR-1: 이벤트 라우팅 (핵심 기능)

**WHEN** CLI 인자로 이벤트 이름을 받을 때
**THE SYSTEM SHALL** 해당 이벤트에 맞는 핸들러를 선택하고 호출한다

**상세 요구사항**:
- 8개 이벤트 타입 지원: SessionStart, UserPromptSubmit, SessionEnd, PreToolUse, PostToolUse, Notification, Stop, SubagentStop
- 핸들러 맵 기반 라우팅 (`handlers` dict)
- 미지원 이벤트는 빈 HookResult 반환

### FR-2: JSON I/O 처리

**WHEN** stdin에서 데이터를 읽고 처리가 완료될 때
**THE SYSTEM SHALL** JSON 파싱 후 핸들러 실행 결과를 JSON으로 stdout에 출력한다

**상세 요구사항**:
- stdin에서 JSON payload 읽기
- `cwd` 필드 추출 (기본값: ".")
- 일반 이벤트: `result.to_dict()` 형식 출력
- UserPromptSubmit: `result.to_user_prompt_submit_dict()` 특수 형식 출력

### FR-3: 에러 처리 및 Exit Code 표준화

**WHEN** JSON 파싱 실패, 핸들러 예외, 또는 CLI 인자 누락 시
**THE SYSTEM SHALL** 명확한 에러 메시지를 stderr에 출력하고 적절한 exit code를 반환한다

**Exit Code 규칙**:
- `0`: 정상 처리
- `1`: 에러 (CLI 인자 누락, JSON 파싱 실패, 예외 발생)

### NFR-1: 단일 책임 원칙 (SRP)

**CONSTRAINT**: 각 모듈은 하나의 명확한 책임만 가진다

**모듈 분리 규칙**:
- **Router** (`alfred_hooks.py`): CLI 인자 파싱, JSON I/O, 이벤트 라우팅
- **Event Handlers** (`handlers/`): 이벤트 타입별 처리 로직
- **Business Logic** (`core/`): 공통 비즈니스 로직 (언어 감지, Git 정보, 체크포인트)

### NFR-2: 확장성

**CONSTRAINT**: 새 이벤트 타입 추가 시 기존 코드 수정 최소화

**확장 방법**:
1. `handlers/` 디렉토리에 새 핸들러 모듈 추가
2. `handlers/__init__.py`에서 핸들러 export
3. `alfred_hooks.py`의 `handlers` dict에 등록

---

## 🔧 Specifications

### 시스템 아키텍처

```
Claude Code (Event Trigger)
    ↓
alfred_hooks.py (Router)
    ├─ CLI argument parsing
    ├─ JSON I/O (stdin/stdout)
    └─ Event routing
         ↓
handlers/ (Event Handlers)
    ├─ session.py (SessionStart, SessionEnd)
    ├─ user.py (UserPromptSubmit)
    ├─ tool.py (PreToolUse, PostToolUse)
    └─ notification.py (Notification, Stop, SubagentStop)
         ↓
core/ (Business Logic)
    ├─ project.py (Language detection, Git info)
    ├─ context.py (JIT Retrieval)
    └─ checkpoint.py (Event-Driven Checkpoint)
```

### 라우팅 로직

```python
# alfred_hooks.py - 핵심 라우팅 로직
handlers = {
    "SessionStart": handle_session_start,
    "UserPromptSubmit": handle_user_prompt_submit,
    "SessionEnd": handle_session_end,
    "PreToolUse": handle_pre_tool_use,
    "PostToolUse": handle_post_tool_use,
    "Notification": handle_notification,
    "Stop": handle_stop,
    "SubagentStop": handle_subagent_stop,
}

handler = handlers.get(event_name)
result = handler({"cwd": cwd, **data}) if handler else HookResult()
```

### 출력 형식 분기

```python
# UserPromptSubmit은 특수 출력 형식 사용
if event_name == "UserPromptSubmit":
    print(json.dumps(result.to_user_prompt_submit_dict()))
else:
    print(json.dumps(result.to_dict()))
```

### TDD History (코드 주석 기반)

1. **RED**: 모듈 분리 설계, 이벤트 라우팅 테스트
2. **GREEN**: 1233 LOC → 9개 모듈로 분리 (SRP 준수)
3. **REFACTOR**: Import 최적화, 에러 처리 강화

---

## ✅ Acceptance Criteria

### AC-1: SessionStart 이벤트 라우팅

**Given**: `alfred_hooks.py SessionStart < payload.json` 명령 실행
**When**: payload에 `{"cwd": "."}` 포함
**Then**:
- `handle_session_start` 핸들러가 호출됨
- 프로젝트 상태 카드가 JSON 형식으로 stdout에 출력됨
- Exit code `0` 반환

### AC-2: UserPromptSubmit 특수 출력 형식

**Given**: `alfred_hooks.py UserPromptSubmit < payload.json` 명령 실행
**When**: 사용자 프롬프트 제출됨
**Then**:
- `handle_user_prompt_submit` 핸들러가 호출됨
- `to_user_prompt_submit_dict()` 형식으로 출력 (additionalContext 포함)
- Exit code `0` 반환

### AC-3: JSON 파싱 에러 처리

**Given**: 잘못된 JSON 형식 입력
**When**: stdin에서 JSON 파싱 실패
**Then**:
- "JSON parse error: <details>" 메시지가 stderr에 출력됨
- Exit code `1` 반환

### AC-4: CLI 인자 누락 에러

**Given**: 이벤트 이름 없이 `alfred_hooks.py` 실행
**When**: `sys.argv` 길이가 2 미만
**Then**:
- "Usage: alfred_hooks.py <event>" 메시지가 stderr에 출력됨
- Exit code `1` 반환

### AC-5: 미지원 이벤트 처리

**Given**: 지원하지 않는 이벤트 이름 전달 (예: `UnknownEvent`)
**When**: handlers dict에서 핸들러를 찾을 수 없음
**Then**:
- 빈 `HookResult()` 객체가 반환됨
- 빈 JSON 객체 `{}` 출력
- Exit code `0` 반환 (에러가 아님)

### AC-6: 모듈 분리 구조 검증

**Given**: 프로젝트 디렉토리 구조 확인
**When**: `.claude/hooks/alfred/` 디렉토리 검사
**Then**:
- `alfred_hooks.py` (153 LOC) 존재
- `handlers/` 디렉토리 존재 (session.py, user.py, tool.py, notification.py)
- `core/` 디렉토리 존재 (project.py, context.py, checkpoint.py)
- 각 모듈이 SRP 준수

---

## 📊 Constraints

1. **성능**: 이벤트 처리 시간 < 2초 (SessionStart 제외, 프로젝트 스캔 포함 시 최대 10초)
2. **코드 품질**: 각 파일 < 300 LOC (Router는 153 LOC로 준수)
3. **Python 버전**: Python 3.10+ 호환
4. **의존성**: 최소화 (표준 라이브러리 우선 사용)

---

## 🔗 Traceability

### Related Specifications
- **SPEC-CICD-001**: Pre-commit Hook에서 import-validator.py 사용 (Hooks 시스템 연계)

### Implementation Files
- **Router**: `.claude/hooks/alfred/alfred_hooks.py` (@CODE:HOOKS-REFACTOR-001)
- **Handlers**: `.claude/hooks/alfred/handlers/` (session.py, user.py, tool.py, notification.py)
- **Core Logic**: `.claude/hooks/alfred/core/` (project.py, context.py, checkpoint.py)

### Tests
- **Manual Testing**: Claude Code 이벤트 발생 시 자동 검증
- **Unit Tests**: 향후 추가 예정 (핸들러별 단위 테스트)

---

## 📝 HISTORY

### v1.0.0 (2025-10-24)
- **RETROACTIVE DOCUMENTATION**: 기존 구현을 소급 문서화
- TDD History: RED (설계) → GREEN (1233 LOC → 9개 모듈 분리) → REFACTOR (최적화)
- 8개 이벤트 타입 라우팅 시스템 완성
- SRP 기반 3계층 아키텍처 (Router → Handlers → Core)
- JSON I/O 및 에러 처리 표준화
