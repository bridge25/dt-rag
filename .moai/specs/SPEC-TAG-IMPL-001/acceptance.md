# SPEC-TAG-IMPL-001: 수락 기준 (Acceptance Criteria)

## 개요

| 항목 | 값 |
|------|-----|
| **SPEC ID** | TAG-IMPL-001 |
| **버전** | 0.0.1 |
| **작성일** | 2025-11-21 |

---

## 1. 전체 수락 기준

### AC-1: TAG 체인 완성률 90% 이상

```gherkin
Given 코드베이스에 ~370개 파일이 존재할 때
When TAG 검증 스크립트를 실행하면
Then TAG 체인 완성률이 90% 이상이어야 한다
And 고아 TAG가 0개여야 한다
```

### AC-2: 모든 Backend 파일에 @CODE TAG 존재

```gherkin
Given apps/ 디렉토리에 138개 Python 파일이 존재할 때
When 모든 Python 파일을 스캔하면
Then 각 파일의 상단에 @CODE:DOMAIN-NNN 형식의 TAG가 있어야 한다
And TAG가 유효한 SPEC을 참조해야 한다
```

### AC-3: 모든 테스트 파일에 @TEST TAG 존재

```gherkin
Given tests/ 디렉토리에 108개 테스트 파일이 존재할 때
When 모든 테스트 파일을 스캔하면
Then 각 파일의 상단에 @TEST:DOMAIN-NNN 형식의 TAG가 있어야 한다
And @TEST TAG가 대응하는 @CODE TAG와 매핑되어야 한다
```

### AC-4: TAG 인덱스 자동 생성

```gherkin
Given TAG 인덱스 생성 스크립트가 존재할 때
When 스크립트를 실행하면
Then .moai/indexes/tag_catalog.json 파일이 생성되어야 한다
And 파일에 모든 TAG와 관련 파일 목록이 포함되어야 한다
And chain_completeness 필드가 정확한 값을 반영해야 한다
```

### AC-5: CI 파이프라인 통합

```gherkin
Given GitHub Actions에 TAG 검증 워크플로우가 설정되어 있을 때
When PR이 생성되면
Then TAG 검증이 자동으로 실행되어야 한다
And TAG 체인 완성률이 90% 미만이면 경고가 표시되어야 한다
```

---

## 2. Phase별 수락 기준

### Phase 1: 핵심 Backend 모듈

#### AC-P1-1: 핵심 모듈 TAG 완성

```gherkin
Given apps/api/routers/, apps/search/, apps/orchestration/ 디렉토리가 존재할 때
When Phase 1이 완료되면
Then 모든 핵심 파일 (~50개)에 @CODE TAG가 추가되어야 한다
And 기존 테스트가 모두 통과해야 한다
```

#### AC-P1-2: 코드 기능 무변경

```gherkin
Given Phase 1에서 TAG가 추가된 파일들이 있을 때
When git diff로 변경사항을 확인하면
Then 모든 변경사항이 주석 추가에만 해당해야 한다
And 코드 로직 변경이 없어야 한다
```

---

### Phase 2: 나머지 Backend 파일

#### AC-P2-1: Backend 전체 TAG 완성

```gherkin
Given apps/ 디렉토리의 모든 Python 파일이 존재할 때
When Phase 2가 완료되면
Then 138개 모든 Backend 파일에 @CODE TAG가 있어야 한다
And Backend TAG 체인 완성률이 100%여야 한다
```

---

### Phase 3: Frontend 컴포넌트

#### AC-P3-1: Frontend TAG 완성

```gherkin
Given frontend/ 및 apps/frontend/ 디렉토리가 존재할 때
When Phase 3이 완료되면
Then 모든 TypeScript 컴포넌트 파일에 @CODE TAG가 있어야 한다
And Frontend TAG 체인 완성률이 100%여야 한다
```

#### AC-P3-2: TypeScript TAG 형식

```gherkin
Given TypeScript 파일에 TAG를 추가할 때
When TAG 형식을 확인하면
Then JSDoc 주석 형식 (/** */)을 사용해야 한다
And @CODE:DOMAIN-NNN 형식을 준수해야 한다
```

---

### Phase 4: 테스트 파일

#### AC-P4-1: 테스트-코드 매핑 완성

```gherkin
Given tests/ 디렉토리의 모든 테스트 파일이 존재할 때
When Phase 4가 완료되면
Then 모든 테스트 파일에 @TEST TAG가 있어야 한다
And 각 @TEST TAG가 대응하는 @CODE TAG의 SPEC을 참조해야 한다
```

#### AC-P4-2: 테스트 통과 유지

```gherkin
Given TAG 추가 전 테스트 결과가 있을 때
When TAG 추가 후 테스트를 실행하면
Then 테스트 통과율이 TAG 추가 전과 동일하거나 높아야 한다
```

---

### Phase 5: 자동화 및 CI 통합

#### AC-P5-1: 검증 스크립트 동작

```gherkin
Given .moai/scripts/validate_tags.py가 존재할 때
When 스크립트를 실행하면
Then TAG 체인 완성률이 출력되어야 한다
And 고아 TAG 목록이 출력되어야 한다
And 누락된 TAG 목록이 출력되어야 한다
```

#### AC-P5-2: GitHub Actions 통합

```gherkin
Given .github/workflows/tag-validation.yml이 존재할 때
When PR이 생성되면
Then TAG 검증 잡이 자동으로 실행되어야 한다
And 검증 결과가 PR 상태에 반영되어야 한다
```

---

## 3. TAG 형식 검증 기준

### AC-FORMAT-1: Python TAG 형식

```gherkin
Given Python 파일에 TAG를 추가할 때
When TAG 형식을 검증하면
Then 다음 형식을 준수해야 한다:
  - 파일 상단 docstring 내 위치
  - "@CODE:DOMAIN-NNN" 또는 "@TEST:DOMAIN-NNN" 형식
  - DOMAIN은 알파벳 대문자와 하이픈만 허용
  - NNN은 3자리 숫자
```

### AC-FORMAT-2: TypeScript TAG 형식

```gherkin
Given TypeScript 파일에 TAG를 추가할 때
When TAG 형식을 검증하면
Then 다음 형식을 준수해야 한다:
  - JSDoc 주석 (/** */) 내 위치
  - "@CODE:DOMAIN-NNN" 형식
  - 파일 최상단 주석에 위치
```

### AC-FORMAT-3: TAG 정규식

```regex
# 유효한 TAG 패턴
@(SPEC|CODE|TEST|DOC):([A-Z][A-Z0-9-]*)-(\d{3})

# 예시
@CODE:SEARCH-001     ✓ 유효
@TEST:API-001        ✓ 유효
@CODE:search-001     ✗ 소문자 불가
@CODE:SEARCH-1       ✗ 3자리 숫자 필수
@CODE:SEARCH001      ✗ 하이픈 필수
```

---

## 4. 품질 기준

### QA-1: 테스트 통과율 유지

```gherkin
Given TAG 구현 전 테스트 통과율이 X%일 때
When TAG 구현이 완료되면
Then 테스트 통과율이 X% 이상이어야 한다
```

### QA-2: 빌드 성공

```gherkin
Given TAG가 추가된 코드베이스가 있을 때
When 프로젝트를 빌드하면
Then 빌드가 성공해야 한다
And 경고 메시지가 증가하지 않아야 한다
```

### QA-3: MyPy 타입 체크 유지

```gherkin
Given MyPy 100% 타입 안전성이 달성된 상태에서
When TAG를 추가한 후 MyPy를 실행하면
Then MyPy 오류가 0개여야 한다
```

---

## 5. 부정 테스트 케이스

### NEG-1: 잘못된 TAG 형식 거부

```gherkin
Given 잘못된 형식의 TAG가 있을 때
When TAG 검증을 실행하면
Then 해당 TAG가 오류로 보고되어야 한다
And 유효하지 않은 형식이 명시되어야 한다
```

### NEG-2: 존재하지 않는 SPEC 참조 감지

```gherkin
Given @CODE:NONEXISTENT-001 형식의 TAG가 있을 때
When TAG 검증을 실행하면
Then 해당 TAG가 고아 TAG로 분류되어야 한다
And 관련 SPEC이 없음이 경고되어야 한다
```

### NEG-3: 코드 기능 변경 방지

```gherkin
Given TAG 추가 커밋이 있을 때
When 커밋 diff를 분석하면
Then 주석 외의 코드 변경이 없어야 한다
And 함수 시그니처 변경이 없어야 한다
```

---

## 6. 완료 체크리스트

### 전체 완료 조건

- [ ] TAG 체인 완성률 90% 이상
- [ ] 고아 TAG 0개
- [ ] 모든 Backend 파일 (@CODE) TAG 완료
- [ ] 모든 Frontend 파일 (@CODE) TAG 완료
- [ ] 모든 테스트 파일 (@TEST) TAG 완료
- [ ] TAG 검증 스크립트 동작
- [ ] TAG 인덱스 자동 생성 동작
- [ ] CI 파이프라인 통합 완료
- [ ] 모든 테스트 통과
- [ ] MyPy 100% 유지
- [ ] 문서화 완료

---

**문서 작성**: spec-builder agent
**상태**: draft
