# Acceptance Criteria: SPEC-ROUTER-CONFLICT-001

## 📋 검수 기준 개요

**SPEC ID**: ROUTER-CONFLICT-001
**목표**: API 라우터 엔드포인트 충돌 해결 검증
**검증 범위**: 라우터 접근성, 테스트 통과, API 문서 정확성

---

## ✅ 핵심 검수 시나리오 (Given-When-Then)

### Scenario 1: agent_factory_router 엔드포인트 접근 가능

**@TEST:ROUTER-CONFLICT-001-AC01**

```gherkin
Given FastAPI 애플리케이션이 정상적으로 실행 중이고
And agent_factory_router가 "/factory/agents" 접두사로 등록되어 있을 때

When 클라이언트가 "GET /api/v1/factory/agents/{agent_id}" 요청을 보내면

Then HTTP 200 응답을 받아야 하고
And 응답 body에 agent 정보가 포함되어야 하며
And agent_factory_router의 핸들러가 요청을 처리해야 한다
```

**검증 방법**:
```bash
# 1. FastAPI 앱 실행
uvicorn apps.api.main:app --reload

# 2. curl로 엔드포인트 테스트
curl -X GET "http://localhost:8000/api/v1/factory/agents/test-agent-id" \
  -H "accept: application/json"

# 기대 결과:
# - HTTP 200 OK
# - JSON 응답에 agent_id, name, type 등 필드 포함
# - agent_factory_router의 AgentFactoryService 로직 실행
```

**통과 기준**:
- ✅ HTTP 상태 코드 200
- ✅ 응답 JSON 구조 정상
- ✅ agent_factory_router 핸들러 실행 (로그 확인)

---

### Scenario 2: agent_router 엔드포인트 접근 가능 (기존 경로 유지)

**@TEST:ROUTER-CONFLICT-001-AC02**

```gherkin
Given FastAPI 애플리케이션이 정상적으로 실행 중이고
And agent_router가 "/agents" 접두사로 등록되어 있을 때

When 클라이언트가 "GET /api/v1/agents/{agent_id}" 요청을 보내면

Then HTTP 200 응답을 받아야 하고
And 응답 body에 agent 정보가 포함되어야 하며
And agent_router의 핸들러가 요청을 처리해야 한다
And agent_factory_router가 아닌 agent_router가 처리해야 한다
```

**검증 방법**:
```bash
# curl로 엔드포인트 테스트
curl -X GET "http://localhost:8000/api/v1/agents/test-agent-id" \
  -H "accept: application/json"

# 기대 결과:
# - HTTP 200 OK
# - JSON 응답에 agent_id 포함
# - agent_router의 AgentDAO 로직 실행 (factory가 아님)
```

**통과 기준**:
- ✅ HTTP 상태 코드 200
- ✅ 응답 JSON 구조 정상
- ✅ agent_router 핸들러 실행 (agent_factory_router 아님)

**중요**: 이 시나리오는 하위 호환성 검증을 위해 필수입니다.

---

### Scenario 3: 단위 테스트 통과 (test_agent_router.py)

**@TEST:ROUTER-CONFLICT-001-AC03**

```gherkin
Given 코드 변경이 완료되었고
And agent_factory_router 접두사가 "/factory/agents"로 변경되었을 때

When pytest로 "tests/unit/test_agent_router.py::test_get_agent_success" 테스트를 실행하면

Then 테스트가 통과해야 하고
And agent_router가 정상적으로 라우팅되어야 하며
And 모든 assertion이 성공해야 한다
```

**검증 방법**:
```bash
# 1. 특정 테스트 실행
pytest tests/unit/test_agent_router.py::test_get_agent_success -v

# 2. 전체 agent_router 테스트 실행
pytest tests/unit/test_agent_router.py -v

# 3. 상세 로그 확인
pytest tests/unit/test_agent_router.py::test_get_agent_success -vv -s
```

**통과 기준**:
- ✅ 테스트 실행 결과: `PASSED`
- ✅ 에러 또는 실패 없음
- ✅ agent_router 엔드포인트 정상 라우팅

**추가 검증** (선택 사항):
```bash
# agent_factory_router 테스트도 확인 (존재 시)
pytest tests/unit/test_agent_factory_router.py -v
```

---

## 🧪 추가 검증 시나리오

### Scenario 4: API 문서 정확성 (Swagger UI)

**@DOC:ROUTER-CONFLICT-001-AC04**

```gherkin
Given FastAPI 애플리케이션이 실행 중일 때

When Swagger UI (http://localhost:8000/docs)에 접속하면

Then "agent-factory" 태그 아래 "/api/v1/factory/agents/{agent_id}" 엔드포인트가 표시되어야 하고
And "agents" 태그 아래 "/api/v1/agents/{agent_id}" 엔드포인트가 표시되어야 하며
And 두 엔드포인트의 설명이 명확히 구분되어야 한다
```

**검증 방법**:
```bash
# 1. FastAPI 앱 실행
uvicorn apps.api.main:app --reload

# 2. 브라우저에서 Swagger UI 접속
# http://localhost:8000/docs

# 3. 다음 항목 확인:
# - agent-factory 태그에 GET /api/v1/factory/agents/{agent_id} 존재
# - agents 태그에 GET /api/v1/agents/{agent_id} 존재
# - 각 엔드포인트의 summary/description 명확
```

**통과 기준**:
- ✅ 두 엔드포인트 모두 Swagger UI에 표시
- ✅ 태그 구분 명확 (agent-factory vs agents)
- ✅ 중복 경로 없음
- ✅ operationId 고유

---

### Scenario 5: 라우팅 충돌 제거 확인

**@TEST:ROUTER-CONFLICT-001-AC05**

```gherkin
Given 두 라우터가 모두 등록되어 있을 때

When FastAPI의 라우팅 테이블을 확인하면

Then "/api/v1/factory/agents/{agent_id}"와 "/api/v1/agents/{agent_id}"가 별도 경로로 등록되어야 하고
And 경로 충돌이 없어야 하며
And 각 경로가 올바른 라우터 핸들러를 가리켜야 한다
```

**검증 방법**:
```python
# FastAPI 앱의 라우팅 테이블 출력
from apps.api.main import app

for route in app.routes:
    if hasattr(route, 'path') and 'agents' in route.path:
        print(f"Path: {route.path}, Name: {route.name}, Methods: {route.methods}")

# 기대 출력:
# Path: /api/v1/factory/agents/{agent_id}, Name: ..., Methods: {'GET'}
# Path: /api/v1/agents/{agent_id}, Name: ..., Methods: {'GET'}
```

**통과 기준**:
- ✅ 두 경로 모두 독립적으로 등록
- ✅ 경로 충돌 없음
- ✅ 각 경로의 핸들러 함수 다름

---

## 🔍 품질 게이트 기준

### 필수 통과 항목 (MUST PASS)

1. **테스트 통과**:
   - ✅ `test_agent_router.py::test_get_agent_success` 통과
   - ✅ 전체 단위 테스트 회귀 테스트 통과

2. **엔드포인트 접근성**:
   - ✅ `GET /api/v1/factory/agents/{agent_id}` 접근 가능
   - ✅ `GET /api/v1/agents/{agent_id}` 접근 가능

3. **라우팅 정확성**:
   - ✅ 각 경로가 올바른 라우터 핸들러 호출
   - ✅ 라우팅 충돌 없음

### 권장 통과 항목 (SHOULD PASS)

4. **API 문서**:
   - ✅ Swagger UI에 두 엔드포인트 모두 표시
   - ✅ 태그 및 설명 명확

5. **회귀 테스트**:
   - ✅ 기존 모든 테스트 통과
   - ✅ 통합 테스트 정상 (존재 시)

---

## 🛠️ 검증 도구 및 방법

### 1. 자동화된 테스트

**pytest 실행**:
```bash
# 특정 테스트
pytest tests/unit/test_agent_router.py::test_get_agent_success -v

# 전체 단위 테스트
pytest tests/unit/ -v

# Coverage 포함
pytest tests/unit/ --cov=apps.api.routers --cov-report=html
```

**기대 결과**:
- 모든 테스트 `PASSED`
- Coverage 90% 이상 유지

---

### 2. 수동 검증 (Manual Testing)

**curl 테스트**:
```bash
# agent_factory_router 테스트
curl -X GET "http://localhost:8000/api/v1/factory/agents/{agent_id}" \
  -H "accept: application/json"

# agent_router 테스트
curl -X GET "http://localhost:8000/api/v1/agents/{agent_id}" \
  -H "accept: application/json"
```

**Postman Collection** (선택 사항):
```json
{
  "name": "SPEC-ROUTER-CONFLICT-001 Verification",
  "requests": [
    {
      "name": "GET agent_factory endpoint",
      "method": "GET",
      "url": "{{base_url}}/api/v1/factory/agents/{{agent_id}}"
    },
    {
      "name": "GET agent endpoint",
      "method": "GET",
      "url": "{{base_url}}/api/v1/agents/{{agent_id}}"
    }
  ]
}
```

---

### 3. API 문서 검증

**Swagger UI 확인**:
1. 브라우저에서 `http://localhost:8000/docs` 접속
2. `agent-factory` 태그 확장
3. `GET /api/v1/factory/agents/{agent_id}` 엔드포인트 확인
4. `agents` 태그 확장
5. `GET /api/v1/agents/{agent_id}` 엔드포인트 확인

**OpenAPI JSON 검증**:
```bash
# OpenAPI 스펙 다운로드
curl http://localhost:8000/openapi.json > openapi.json

# 중복 경로 확인
jq '.paths | keys' openapi.json | grep "agents"

# 기대 결과:
# "/api/v1/factory/agents/{agent_id}"
# "/api/v1/agents/{agent_id}"
```

---

## 📊 Definition of Done (완료 정의)

이 SPEC은 다음 모든 조건이 충족될 때 완료로 간주합니다:

### 코드 변경
- ✅ `agent_factory_router.py` 접두사가 `/factory/agents`로 변경됨
- ✅ `main.py` 라우터 등록 검증 완료
- ✅ 코드 리뷰 승인 (팀원 1명 이상)

### 테스트
- ✅ `test_agent_router.py::test_get_agent_success` 통과
- ✅ 전체 단위 테스트 회귀 테스트 통과
- ✅ 통합 테스트 통과 (존재 시)

### 문서
- ✅ Swagger UI에서 두 엔드포인트 확인
- ✅ API 문서 업데이트 (필요 시)
- ✅ 마이그레이션 가이드 작성 (필요 시)

### Git & PR
- ✅ 커밋 메시지 TRUST 원칙 준수
- ✅ Draft PR 생성 및 리뷰 요청
- ✅ CI/CD 파이프라인 통과

### 품질 지표
- ✅ 테스트 커버리지 90% 이상 유지
- ✅ Linting/Formatting 통과
- ✅ 보안 스캔 통과

---

## 🚨 실패 시나리오 및 대응

### 실패 시나리오 1: 테스트 여전히 실패

**증상**: `test_agent_router.py::test_get_agent_success` 여전히 실패

**원인 분석**:
1. `agent_factory_router` 여전히 `/agents` 접두사 사용
2. 라우터 등록 순서 문제
3. 테스트 자체의 문제 (mock 설정 등)

**대응 방법**:
```bash
# 1. 라우터 등록 순서 확인
grep -n "include_router" apps/api/main.py | grep "agent"

# 2. 접두사 확인
grep -n "prefix=" apps/api/routers/agent_factory_router.py

# 3. 테스트 디버깅
pytest tests/unit/test_agent_router.py::test_get_agent_success -vv -s --pdb
```

---

### 실패 시나리오 2: agent_factory 엔드포인트 404

**증상**: `GET /api/v1/factory/agents/{agent_id}` 요청 시 404 응답

**원인 분석**:
1. 접두사 변경 누락
2. 라우터 미등록
3. 경로 오타

**대응 방법**:
```bash
# 라우팅 테이블 확인
python -c "from apps.api.main import app; [print(r.path) for r in app.routes if hasattr(r, 'path')]"
```

---

### 실패 시나리오 3: 회귀 테스트 실패

**증상**: 기존에 통과하던 다른 테스트가 실패

**원인 분석**:
1. `agent_factory_router` 의존 테스트에서 경로 미업데이트
2. 통합 테스트에서 하드코딩된 경로 사용

**대응 방법**:
```bash
# agent_factory 경로를 사용하는 테스트 검색
grep -r "GET /api/v1/agents" tests/ --include="*.py"

# 해당 테스트에서 /factory/agents 경로로 업데이트
```

---

## 📋 최종 체크리스트

구현 완료 전 다음 체크리스트를 확인하세요:

### 코드 변경
- [ ] `agent_factory_router.py` 접두사 변경 완료
- [ ] `main.py` 라우터 등록 확인 완료
- [ ] 관련 테스트 경로 업데이트 완료 (필요 시)

### 테스트 검증
- [ ] `test_agent_router.py::test_get_agent_success` 통과
- [ ] 전체 단위 테스트 통과
- [ ] 회귀 테스트 문제 없음

### 수동 검증
- [ ] curl로 `/api/v1/factory/agents/{agent_id}` 접근 성공
- [ ] curl로 `/api/v1/agents/{agent_id}` 접근 성공
- [ ] Swagger UI에서 두 엔드포인트 확인

### 문서 및 Git
- [ ] API 문서 업데이트 (필요 시)
- [ ] 커밋 메시지 작성 (영어, @TAG 포함)
- [ ] Draft PR 생성

### 품질 게이트
- [ ] Coverage 90% 이상
- [ ] Linting 통과
- [ ] 보안 스캔 통과

---

## ✅ 최종 승인 기준

**이 SPEC은 다음 조건을 모두 만족할 때 승인됩니다**:

1. ✅ 3가지 핵심 시나리오 모두 통과 (AC01, AC02, AC03)
2. ✅ API 문서 검증 완료 (AC04)
3. ✅ 라우팅 충돌 제거 확인 (AC05)
4. ✅ Definition of Done 모든 항목 체크
5. ✅ 코드 리뷰 승인 (1명 이상)

**승인자**: @bridge25
**승인 일시**: 구현 완료 후 업데이트 예정
