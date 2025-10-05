# ABSTAIN.md
# 🛑 프론트엔드 구현 보류 항목

> **이 문서의 목적**:
> - 정보 부족으로 구현 불가능한 항목 명시
> - 진행 조건 명확화
> - 바이브코딩 원칙 "IG 임계치 미달 시 Abstain" 준수
>
> **참조**: `FRONTEND_IG_CHECKLIST.md` 의 🔴 항목들

---

## 📋 현재 Abstain 상태 항목

### 🔴 Critical (Phase 2 시작 전 필수 해결)

#### 1. API 응답 상세 스키마 (15개 엔드포인트)

**문제**:
- `apps/api/routers/*.py` 파일들을 직접 읽지 않음
- 각 엔드포인트의 정확한 응답 구조 미확정
- TypeScript 타입 정의 불가능

**필요 정보**:
```
읽어야 할 파일 (우선순위 순):
1. apps/api/routers/search_router.py
2. apps/api/routers/classification_router.py
3. apps/api/routers/taxonomy_router.py
4. apps/api/routers/orchestration_router.py
5. apps/api/routers/agent_factory_router.py
6. apps/api/routers/monitoring_router.py
7. apps/api/routers/ingestion.py
8. apps/api/routers/embedding_router.py
9. apps/api/routers/evaluation.py
10. apps/api/routers/batch_search.py
11. apps/api/routers/health.py
12. apps/api/routers/admin/api_keys.py
13. apps/api/models/common_models.py (타입 정의)
14. apps/api/models/taxonomy_models.py
```

**진행 조건**:
- [ ] 위 14개 파일 Read tool로 직접 읽기
- [ ] 각 엔드포인트별 Pydantic 모델 확인
- [ ] TypeScript 타입 정의 가능 상태

**예상 작업**:
- 파일당 100-500줄
- 총 읽기 시간: 30-60분
- Zod 스키마 작성 시간: 2-3시간

---

#### 2. 환경 변수 전체 목록

**문제**:
- `apps/api/config.py` 미읽음
- 백엔드가 요구하는 환경 변수 전체 목록 불명

**필요 정보**:
```
읽어야 할 파일:
- apps/api/config.py

확인할 항목:
- CORS allow_origins 값
- Redis 연결 설정
- 데이터베이스 URL
- Sentry DSN (선택)
- API 인증 관련 환경 변수
```

**진행 조건**:
- [ ] `apps/api/config.py` Read tool로 읽기
- [ ] Pydantic Settings 모델 확인
- [ ] 필수 vs 선택 환경 변수 구분
- [ ] 기본값 확인

**예상 작업**:
- 읽기 시간: 5-10분
- .env.example 작성: 10분

---

#### 3. 인증/권한 시스템

**문제**:
- 백엔드 인증 방식 미확정
- JWT? API Key? OAuth? 없음?
- 프론트엔드에서 어떻게 인증 헤더 추가?

**필요 정보**:
```
확인 필요:
1. apps/api/middleware/ 디렉터리 존재 여부
2. apps/api/deps.py (의존성 주입)
3. apps/api/routers/admin/api_keys.py (API 키 관리)
4. apps/api/security/ 디렉터리 (있다면)

질문:
- 현재 인증이 구현되어 있는가?
- 없다면 프론트엔드에서 구현해야 하는가?
- API 키 저장 방식? (localStorage? Cookie?)
```

**진행 조건**:
- [ ] 인증 방식 확정 (JWT / API Key / None)
- [ ] 인증 헤더 형식 확정 (Authorization: Bearer vs X-API-Key)
- [ ] 토큰/키 저장 방식 결정
- [ ] 로그인/로그아웃 플로우 설계

**예상 작업**:
- 조사: 30분
- 구현 (필요 시): 2-4시간

---

### 🟡 High Priority (Phase 3 시작 전 해결)

#### 4. SearchRequest 필드별 정확한 의미

**문제**:
- `canonical_in` 필드 구조 불명확
  - `[["Tech", "AI"]]` vs `["Tech/AI"]` vs 다른 형식?
- `include_highlights` 동작 방식
  - 응답에 어떤 필드가 추가되는가?
- `search_mode` 가능한 값
  - "hybrid", "bm25", "vector" 3개만인가?

**필요 정보**:
```
apps/api/routers/search_router.py 에서 확인:
1. SearchRequest Pydantic 모델
2. canonical_in 필드 타입 및 검증
3. include_highlights 사용 예제
4. search_mode Literal 타입
5. 각 필드의 기본값
```

**진행 조건**:
- [ ] 모든 필드 타입 확정
- [ ] 예제 요청/응답 확인
- [ ] UI 컴포넌트 설계 가능

**예상 작업**:
- 읽기: 10-15분
- UI 설계 반영: 30분

---

#### 5. 파일 업로드 응답 구조

**문제**:
- `POST /ingestion/upload` 응답 형식 미확정
- 진행 중 상태 확인 방법 (`GET /ingestion/status/{job_id}`)
- WebSocket? Polling? 방식 미확정

**필요 정보**:
```
apps/api/routers/ingestion.py 에서 확인:
1. 업로드 응답 스키마
2. job_id 형식
3. 상태 확인 엔드포인트 응답
4. 실시간 진행률 제공 여부
```

**진행 조건**:
- [ ] 업로드 응답 타입 확정
- [ ] 진행 상태 확인 방법 결정
- [ ] UI 진행률 표시 방법 설계

---

### 🟢 Medium Priority (Phase 5 시작 전 해결)

#### 6. Taxonomy 트리 구조

**문제**:
- `GET /api/v1/taxonomy/{version}/tree` 응답 구조
- DAG 형식? 중첩 객체? Flat array?
- 프론트엔드에서 트리 렌더링 방법

**필요 정보**:
```
apps/api/routers/taxonomy_router.py 에서 확인:
1. TaxonomyNode 타입
2. 부모-자식 관계 표현 방식
3. 최대 깊이
4. 노드별 메타데이터 (문서 수 등)
```

---

#### 7. Agent 생성 요청 구조

**문제**:
- `POST /api/v1/agents/from-category` 요청 파라미터
- category 선택 UI 어떻게?
- 에이전트 설정 옵션

**필요 정보**:
```
apps/api/routers/agent_factory_router.py 에서 확인:
1. AgentCreateRequest 스키마
2. 필수/선택 필드
3. 응답 구조
```

---

#### 8. Pipeline 실행 파라미터

**문제**:
- RAG 파이프라인 설정 옵션
- 비동기 실행 vs 동기 실행
- 실시간 진행 상태

**필요 정보**:
```
apps/api/routers/orchestration_router.py 에서 확인:
1. PipelineExecuteRequest
2. PipelineConfig
3. 응답 구조
```

---

### 🔵 Low Priority (Phase 6 이후)

#### 9. Monitoring 메트릭 구조

**문제**:
- 차트에 표시할 메트릭 종류
- 시계열 데이터 형식

#### 10. Batch Search 응답

**문제**:
- 배치 검색 결과 형식
- UI에 어떻게 표시?

#### 11. Evaluation 응답

**문제**:
- RAGAS 평가 결과 구조
- 품질 지표 종류

---

## 🚦 진행 가능 여부 판단 기준

### Phase별 필수 해결 항목

#### Phase 0: 프로젝트 초기화
- ✅ 진행 가능 (정보 충분)
- 필요: Next.js 설치 명령어, 기본 설정

#### Phase 1: shadcn/ui 및 레이아웃
- ✅ 진행 가능 (정보 충분)
- 필요: shadcn 문서, Next.js 레이아웃 문서

#### Phase 2: API 클라이언트/타입
- 🔴 **진행 불가** (Critical 1, 2, 3 해결 필요)
- 필수:
  - [ ] 15개 라우터 파일 읽기
  - [ ] config.py 읽기
  - [ ] 인증 방식 확정

#### Phase 3: 검색 페이지
- 🟡 **조건부 가능** (High 4 해결 권장)
- Phase 2 완료 후 가능

#### Phase 4: 문서 관리
- 🟡 **조건부 가능** (High 5 해결 권장)
- Phase 2 완료 후 가능

#### Phase 5: 나머지 페이지
- 🟢 **Phase 2 완료 후 가능** (Medium 6-8 순차 해결)

#### Phase 6: 폴리싱
- 🟢 **Phase 5 완료 후 가능**

---

## 📝 Abstain 해제 프로세스

### 1. Critical 항목 해결 (Phase 2 시작 전 필수)

**작업 순서**:
```
1. apps/api/config.py 읽기 (5분)
   → .env.example 업데이트

2. apps/api/routers/search_router.py 읽기 (15분)
   → SearchRequest, SearchResponse 타입 확정

3. apps/api/routers/classification_router.py 읽기 (15분)
   → ClassifyRequest, ClassifyResponse 타입 확정

4. 나머지 13개 라우터 순차 읽기 (각 10-15분)
   → 각 엔드포인트 타입 확정

5. 인증 방식 조사 (30분)
   → apps/api/middleware/, deps.py 읽기
   → 방식 확정 또는 "없음" 확정

6. lib/api/types.ts 작성 (2-3시간)
   → 모든 Zod 스키마 정의
   → TypeScript 타입 생성
   → 테스트 (런타임 검증)
```

**예상 총 시간**: 4-6시간

**완료 조건**:
- [ ] `lib/api/types.ts` 파일 생성 완료
- [ ] 15개 엔드포인트 타입 모두 정의
- [ ] Zod 런타임 검증 동작
- [ ] TypeScript strict 모드 에러 0개
- [ ] `.env.example` 최신화

### 2. High Priority 항목 해결 (Phase 3-4 시작 전)

**작업**:
- SearchRequest 필드 정밀 분석 (30분)
- 파일 업로드 플로우 확인 (30분)

### 3. Medium/Low Priority (순차 해결)

**방법**:
- 각 Phase 시작 시 해당 Phase에 필요한 항목만 해결
- 전체를 한 번에 해결 시도하지 않음 (바이브코딩 원칙)

---

## 🔄 문서 업데이트 규칙

### Abstain 항목 해결 시

1. 이 문서에서 해당 항목을 ~~취소선~~으로 표시
2. `FRONTEND_IG_CHECKLIST.md`에서 🔴 → ✅로 변경
3. `FRONTEND_CONTEXT.md`에 확정된 정보 추가
4. Git 커밋 (메시지: "docs: Resolve Abstain item #N")

### 새 Abstain 항목 발견 시

1. 이 문서에 즉시 추가
2. Priority 지정 (Critical/High/Medium/Low)
3. 진행 조건 명시
4. Git 커밋 (메시지: "docs: Add new Abstain item")

---

## 📊 현재 상태 요약

```
총 Abstain 항목: 11개

Critical (🔴): 3개
  - API 응답 스키마
  - 환경 변수 목록
  - 인증 방식

High (🟡): 2개
  - SearchRequest 상세
  - 파일 업로드 구조

Medium (🟢): 3개
  - Taxonomy 트리
  - Agent 생성
  - Pipeline 실행

Low (🔵): 3개
  - Monitoring 메트릭
  - Batch Search
  - Evaluation

진행 가능 Phase: 0, 1
진행 불가 Phase: 2, 3, 4, 5, 6

Critical 해결 예상 시간: 4-6시간
```

---

## 🎯 권장 Next Steps

### 즉시 실행 (새 세션 시작 시)

1. **Phase 0, 1 먼저 완료**
   - 프로젝트 초기화
   - shadcn/ui 설정
   - 레이아웃 구현
   - → Critical 항목과 독립적

2. **Critical 항목 집중 해결**
   - 15개 라우터 파일 읽기
   - 타입 정의 작성
   - 인증 조사

3. **Phase 2 재개**
   - Critical 해결 후 시작

### 장기 전략

- **한 번에 전부 해결하지 않음**
- Phase별로 필요한 것만 순차 해결
- 바이브코딩 7-Stage 루프 준수

---

**문서 끝**

이 문서는 바이브코딩 원칙 "IG 임계치 미달 시 Abstain"을 따릅니다.
Abstain 항목 해결 없이 해당 Phase 진행 시도 시 즉시 중단하세요.
