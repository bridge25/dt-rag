# NEW_SESSION_INSTRUCTIONS.md
# 🚀 새 세션 시작용 복사-붙여넣기 지시문

> **⚠️ 이 문서를 새 Claude 세션에 전체 복사-붙여넙어 즉시 컨텍스트 로딩**

---

## 📌 즉시 실행 명령

새 세션을 시작하면 다음 4개 문서를 **반드시 순서대로** Read tool로 읽으세요:

```
1. CLAUDE.md (프로젝트 원칙)
2. 바이브코딩_완성_정제본_쉬운말로_연결한_한_권.md (개발 방법론)
3. FRONTEND_CONTEXT.md (백엔드 API 검증 사실)
4. FRONTEND_PLAN.md (전체 로드맵)
5. FRONTEND_IG_CHECKLIST.md (IG 임계치 체크리스트)
6. ABSTAIN.md (보류 항목)
```

**읽기 완료 후** 아래 "현재 상태 요약"을 확인하고 작업을 이어가세요.

---

## 🎯 프로젝트 목표

**DT-RAG 프로젝트의 프로덕션급 프론트엔드 구현**

- **기술 스택**: Next.js 14.2.0 + TypeScript + shadcn/ui + React Query
- **백엔드**: FastAPI (포트 8000)
- **데이터베이스**: PostgreSQL + pgvector
- **목표**: 15개 백엔드 API 엔드포인트를 완전히 활용하는 관리자 대시보드

---

## 📊 현재 프로젝트 상태 (2025-10-05 기준)

### ✅ 완료된 작업

1. **백엔드 API 검증** (apps/api/main.py 640줄 직접 읽음)
   - 15개 엔드포인트 그룹 확인
   - CORS, Rate Limiting, 에러 핸들링 확인
   - RFC 7807 형식 에러 응답 확인

2. **기존 프론트엔드 분석** (find 명령어로 실제 파일 검증)
   - apps/frontend-admin: 실제 구현 파일 3개만 존재
   - src/components, app/admin 등 모든 하위 디렉터리 **빈 폴더**
   - 결론: 프론트엔드 ~0% 완성

3. **기술 스택 선정** (2025년 웹 서치 완료)
   - Next.js 14 + shadcn/ui 확정
   - v0.dev 활용 계획
   - TypeScript strict 모드

4. **문서화 완료**
   - FRONTEND_CONTEXT.md (백엔드 API 사실)
   - FRONTEND_PLAN.md (Phase 0-6 로드맵)
   - FRONTEND_IG_CHECKLIST.md (IG 임계치)
   - ABSTAIN.md (11개 보류 항목)

### 🔴 미완료 작업 (현재 세션에서 수행)

#### Phase 0: 프로젝트 초기화 (✅ 즉시 시작 가능)
- Next.js 14.2.0 설치
- TypeScript strict 모드 설정
- Tailwind + shadcn/ui 설정
- 기본 환경 변수 설정

#### Phase 1: shadcn/ui 및 레이아웃 (✅ 즉시 시작 가능)
- shadcn/ui 컴포넌트 10개 설치
- AppShell, Sidebar, Header 구현
- 반응형 레이아웃

#### Phase 2-6: API 통합 및 페이지 (🔴 Abstain 해제 후 가능)
- **Blocker**: ABSTAIN.md의 Critical 항목 3개 해결 필요
- 예상 해결 시간: 4-6시간

---

## 🚨 필수 준수 원칙 (CLAUDE.md + 바이브코딩)

### CLAUDE.md 12가지 원칙

1. **가정과 추측 절대 금지** - 확인된 사실만 사용
2. **문서가 아닌 코드를 직접 읽기**
3. **모든 코드 Read tool로 읽기** - 방대해도 건너뛰지 않음
4. **모든 코드 tool로 작성**
5. **모든 에러 즉시 해결** - 나중으로 미루지 않음
6. **import 시에도 추측 금지** - 모든 코드 직접 읽기
7. **지시한 내용만 수행** - 불필요한 제안 금지
8. **현재 목표에만 집중** - 관련 없는 개선 금지
9. **문제 해결은 정석으로만** - 임시방편 금지
10. **주석보다 코드 우선** - 주석은 최신 아닐 수 있음
11. **주석/문서 최소화** - Code = Source of Truth
12. **.env.local 함부로 가정 금지** - AI 접근 제한됨

### 바이브코딩 핵심 원칙

1. **7-Stage Loop 준수**
   ```
   Scope → Context Load → Synthesis → Plan(≤5파일) →
   Explain(10줄) → Implement → Verify
   ```

2. **IG 임계치 확인**
   - "지금 정보로 모호함이 충분히 줄었는가?"
   - 입력 ≥ 출력 × 20
   - 미달 시 **즉시 Abstain**

3. **모호어 절대 금지**
   - "적절히", "일반적으로", "아마도" 사용 금지
   - "기본", "보통", "대략" 사용 금지

4. **Plan ≤5 파일**
   - 한 번에 5개 파일 이하만 구현
   - 커밋 단위 명확화

5. **SOT = 코드**
   - 주석 3줄 이상 금지
   - 코드가 유일한 진실

---

## 🔍 Abstain 현황 (Phase 2+ 진행 전 필수 해결)

### 🔴 Critical (Phase 2 블로커)

#### 1. API 응답 상세 스키마 (15개 엔드포인트)
**문제**: apps/api/routers/*.py 파일 미읽음

**해결 방법**:
```
읽어야 할 파일 (우선순위 순):
1. apps/api/routers/search_router.py
2. apps/api/routers/classification_router.py
3. apps/api/routers/taxonomy_router.py
4. apps/api/routers/orchestration_router.py
5. apps/api/routers/agent_factory_router.py
6-14. 나머지 10개 라우터
```

**예상 시간**: 2-3시간

**완료 조건**:
- [ ] lib/api/types.ts 작성 완료
- [ ] 15개 엔드포인트 Zod 스키마 정의
- [ ] TypeScript strict 모드 에러 0개

---

#### 2. 환경 변수 전체 목록
**문제**: apps/api/config.py 미읽음

**해결 방법**:
```
1. apps/api/config.py Read tool로 읽기
2. Pydantic Settings 모델 확인
3. 필수 vs 선택 환경 변수 구분
4. .env.example 업데이트
```

**예상 시간**: 10-15분

---

#### 3. 인증/권한 시스템
**문제**: 백엔드 인증 방식 미확정 (JWT? API Key? 없음?)

**해결 방법**:
```
확인 파일:
1. apps/api/middleware/ (존재 여부)
2. apps/api/deps.py (의존성 주입)
3. apps/api/routers/admin/api_keys.py
4. apps/api/security/ (있다면)
```

**예상 시간**: 30분 조사 + 2-4시간 구현 (필요 시)

---

### 🟡 High Priority (Phase 3-4 블로커)

#### 4. SearchRequest 필드별 정확한 의미
- `canonical_in` 구조: `[["Tech", "AI"]]` vs `["Tech/AI"]`?
- `include_highlights` 동작 방식?
- `search_mode` 가능한 값?

#### 5. 파일 업로드 응답 구조
- POST /ingestion/upload 응답 형식
- 진행 상태 확인 방법 (WebSocket? Polling?)

---

### 🟢 Medium/🔵 Low Priority (Phase 5-6)
- Taxonomy 트리 구조
- Agent 생성 요청 구조
- Pipeline 실행 파라미터
- Monitoring 메트릭 구조
- Batch Search 응답
- Evaluation 응답

**전체 내용**: ABSTAIN.md 참조

---

## 🎬 새 세션에서 즉시 실행할 명령

### Step 1: 컨텍스트 로딩 (필수)

```
다음 6개 문서를 Read tool로 순서대로 읽어주세요:

1. CLAUDE.md
2. 바이브코딩_완성_정제본_쉬운말로_연결한_한_권.md
3. FRONTEND_CONTEXT.md
4. FRONTEND_PLAN.md
5. FRONTEND_IG_CHECKLIST.md
6. ABSTAIN.md

읽기 완료 후 "컨텍스트 로딩 완료. Phase 0 시작 준비됨." 이라고 응답하세요.
```

### Step 2: Phase 0 시작 (즉시 가능)

**Phase 0은 Abstain 항목 없이 즉시 시작 가능합니다.**

```
Phase 0: 프로젝트 초기화를 시작하세요.

FRONTEND_PLAN.md의 Phase 0 섹션을 따라:
1. Scope 확인
2. IG 체크리스트 확인 (FRONTEND_IG_CHECKLIST.md)
3. 구현 시작 (≤5 파일)
4. DoD 확인
5. Git 커밋
```

### Step 3: Phase 1 진행 (즉시 가능)

```
Phase 0 완료 후 Phase 1: shadcn/ui 및 레이아웃을 진행하세요.

v0.dev 프롬프트 사용 가능 (FRONTEND_PLAN.md 참조)
```

### Step 4: Phase 2 전 Abstain 해제 (4-6시간 소요)

```
Phase 1 완료 후, Phase 2 시작 전:

ABSTAIN.md의 Critical 항목 3개를 해결하세요:
1. 15개 라우터 파일 읽기 (2-3시간)
2. config.py 읽기 (10분)
3. 인증 방식 조사 (30분-4시간)

완료 후 ABSTAIN.md 업데이트 (~~취소선~~으로 표시)
```

---

## 📂 중요 파일 위치

### 읽어야 할 문서 (새 세션 시작 시)
- `C:\MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag\CLAUDE.md`
- `C:\MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag\바이브코딩_완성_정제본_쉬운말로_연결한_한_권.md`
- `C:\MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag\FRONTEND_CONTEXT.md`
- `C:\MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag\FRONTEND_PLAN.md`
- `C:\MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag\FRONTEND_IG_CHECKLIST.md`
- `C:\MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag\ABSTAIN.md`

### 백엔드 코드 (검증 완료)
- `apps/api/main.py` (640줄, 전체 읽음)
- `apps/api/config.py` (🔴 미읽음 - Critical)
- `apps/api/routers/*.py` (🔴 15개 미읽음 - Critical)
- `openapi.yaml` (일부 읽음)

### 기존 프론트엔드 (거의 빈 상태)
- `apps/frontend-admin/app/layout.tsx` (28줄)
- `apps/frontend-admin/app/page.tsx` (267줄)
- `apps/frontend-admin/next.config.js` (16줄)
- 나머지 디렉터리: **모두 빈 폴더**

### 새로 생성할 위치 (Phase 0-1)
- `apps/frontend/` (새 프로젝트)
- `apps/frontend/package.json`
- `apps/frontend/tsconfig.json`
- `apps/frontend/next.config.js`
- `apps/frontend/.env.local`
- `apps/frontend/components.json` (shadcn)

---

## ⚠️ 세션 중 주의사항

### 1. IG 임계치 체크 항상 수행
- 각 Phase 시작 전 FRONTEND_IG_CHECKLIST.md 확인
- 하나라도 🔴이면 **즉시 중단**
- ABSTAIN.md에 항목 추가

### 2. 모호어 발견 시 즉시 중단
- "적절히", "일반적으로", "아마도" 발견 시
- "기본", "보통", "대략" 발견 시
- → 구체적 값으로 변환 또는 Abstain

### 3. Plan ≤5 파일 엄수
- 한 커밋에 5개 파일 초과 금지
- 초과 시 Phase를 더 작은 단위로 분할

### 4. 코드 직접 읽기
- 문서나 주석 신뢰하지 않음
- 모든 import 대상 코드 직접 읽기
- 추측 절대 금지

### 5. 주석 최소화
- 주석 3줄 이상 금지
- Code = Single Source of Truth
- 불필요한 설명 주석 제거

---

## 🎯 최종 목표 (7일 계획)

### Day 1: Phase 0-1 (Abstain 없음)
- 프로젝트 초기화
- shadcn/ui 설정
- 레이아웃 구현

### Day 2: Critical Abstain 해제 (4-6시간)
- 15개 라우터 읽기
- 타입 정의 작성
- 인증 조사

### Day 3-4: Phase 2-3
- API 클라이언트 구현
- 검색 페이지 구현

### Day 5: Phase 4
- 문서 업로드 구현

### Day 6: Phase 5
- Taxonomy, Agents, Pipeline, Monitoring 페이지

### Day 7: Phase 6
- 폴리싱
- 테스트
- 배포 준비

---

## 📋 체크리스트 (새 세션 시작 시)

- [ ] 6개 문서 Read tool로 읽기 완료
- [ ] CLAUDE.md 원칙 숙지
- [ ] 바이브코딩 7-Stage Loop 숙지
- [ ] IG 임계치 개념 이해
- [ ] Abstain 조건 이해
- [ ] Phase 0 Scope 확인
- [ ] Phase 0 IG 체크리스트 확인
- [ ] git status 확인
- [ ] 작업 디렉터리 확인 (dt-rag)

---

## 🚀 시작 명령어 (복사-붙여넣기)

```
다음 6개 문서를 순서대로 Read tool로 읽어주세요:

1. C:\MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag\CLAUDE.md
2. C:\MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag\바이브코딩_완성_정제본_쉬운말로_연결한_한_권.md
3. C:\MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag\FRONTEND_CONTEXT.md
4. C:\MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag\FRONTEND_PLAN.md
5. C:\MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag\FRONTEND_IG_CHECKLIST.md
6. C:\MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag\ABSTAIN.md

읽기 완료 후:
- git status 확인
- Phase 0 IG 체크리스트 확인 (FRONTEND_IG_CHECKLIST.md)
- Phase 0 시작 가능 여부 보고

Phase 0은 Abstain 항목 없이 즉시 시작 가능합니다.
```

---

**문서 끝**

이 지시문을 새 Claude 세션에 복사-붙여넣으면 모든 컨텍스트가 로딩되고 즉시 작업을 이어갈 수 있습니다.
