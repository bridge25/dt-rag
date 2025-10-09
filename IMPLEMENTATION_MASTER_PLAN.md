# DT-RAG v1.8.1 구현 마스터 플랜

**문서 상태**: Baseline
**작성일**: 2025-10-06 (KST)
**목표**: PRD 대비 미구현 핵심 기능 완성 (Phase 1~5)
**방법론**: 바이브코딩 7-Stage 루프 + Subagent 병렬 실행

---

## 0. 핵심 원칙 (모든 Subagent 필수 준수)

### 0.1 바이브코딩 철학
- **혼선↓, 정보이득↑**: 모호어('적절히', '아마도', '일반적으로') 발견 시 즉시 Abstain
- **코드가 진실(SOT)**: 문서/주석과 충돌 시 코드 기준
- **입력 ≥ 출력×20**: Explain 단계에서 10줄 알고리즘만 먼저 제시
- **작은 커밋(≤5파일)**: 각 Phase = 1 commit
- **설명→코드 순서**: Explain 승인 후 Implement

### 0.2 CLAUDE.md 준수사항
1. 가정과 추측 금지 → 확인된 사실만
2. 문서/주석 아닌 코드 직접 읽기
3. 모든 코드를 tool로 직접 읽기 (절대 건너뛰지 않음)
4. 모든 에러 처음부터 해결 (linter 포함)
5. import 시 가정 없이 코드 직접 읽기
6. 지시 내용만 수행, 불필요한 제안 금지
7. 현재 목표에만 집중
8. 항상 정석으로만 문제 해결
9. 주석/문서는 필요한 경우만 최소화
10. .env.local 등 접근 불가 파일 가정 금지

### 0.3 7-Stage 루프 (각 Phase마다)
```
1. Scope: 목표/비범위/제약/DoD 명시
2. Context Load: Main vs Reference 분리, 코드 직접 읽기
3. Synthesis: IG 부족 항목 특정 → Abstain 또는 수집
4. Plan: ≤5파일, 린트/타입/테스트 DoD
5. Explain: 10줄 알고리즘 제시 → 승인 대기
6. Implement: 승인 후 코드 작성
7. Verify: 테스트 실행 → 리포트 → Cleanup
```

---

## 1. Phase 구조 (phase1~5.txt 기반)

| Phase | 우선순위 | 담당 Subagent | 의존성 | 예상 파일 수 |
|-------|---------|---------------|--------|-------------|
| Phase 1: Taxonomy DB | P0 | database-architect | None | 3 |
| Phase 2: Taxonomy Service | P0 | api-designer | Phase 1 | 4 |
| Phase 3: 혼합 분류 파이프라인 | P0 | classification-pipeline-expert | Phase 1 | 4 |
| Phase 4: TreeViewer UI | P0 | tree-ui-developer | Phase 2 | 4 |
| Phase 5: LangGraph 통합 | P0 | langgraph-orchestrator | Phase 2 | 3 |

### 병렬 실행 그룹
**Group 1 (독립):**
- Phase 1

**Group 2 (Phase 1 완료 후):**
- Phase 2
- Phase 3

**Group 3 (Phase 2 완료 후):**
- Phase 4
- Phase 5

---

## 2. Context 공유 전략

### 2.1 공통 Context (모든 Subagent에게 제공)
**필수 읽기 파일:**
```
1. C:\MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag\CLAUDE.md
2. C:\MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag\바이브코딩_완성_정제본_쉬운말로_연결한_한_권.md
3. C:\MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag\prd_dynamic_taxonomy_rag_v_1_8 최종 (1).md
4. C:\MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag\phase1~5.txt
5. C:\MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag\IMPLEMENTATION_MASTER_PLAN.md (본 문서)
6. 각 Phase별 CONTEXT_SHEET (아래 3절 참조)
```

### 2.2 Main vs Reference 분리
**Main (수정 대상):**
- `apps/api/`, `apps/classification/`, `apps/frontend-admin/`
- `alembic/versions/`

**Reference (인터페이스만 읽기):**
- PRD 관련 섹션 (DDL, API 엔드포인트, 프롬프트)
- 기존 코드 패턴 (DAO, ORM)

### 2.3 IG 확보 강제
**위험 신호 → 즉시 Abstain:**
- "적절히", "아마도", "일반적으로"
- 파일 경로 불명확
- 스키마/타입 정의 없이 구현 시작

---

## 3. Phase별 Context Sheet

각 Subagent는 시작 시 해당 Context Sheet를 먼저 읽어야 합니다.

**참조 문서:**
- `PHASE1_CONTEXT.md` - Taxonomy DB
- `PHASE2_CONTEXT.md` - Taxonomy Service
- `PHASE3_CONTEXT.md` - 분류 파이프라인
- `PHASE4_CONTEXT.md` - TreeViewer UI
- `PHASE5_CONTEXT.md` - LangGraph 통합

---

## 4. Subagent 실행 프로토콜

### 4.1 시작 시 체크리스트
```markdown
[ ] CLAUDE.md 읽음
[ ] 바이브코딩 문서 읽음
[ ] PRD 전체 읽음
[ ] phase1~5.txt 읽음
[ ] IMPLEMENTATION_MASTER_PLAN.md 읽음
[ ] 해당 Phase Context Sheet 읽음
[ ] Main vs Reference 분리 확인
[ ] IG 부족 항목 특정 → 수집 계획
```

### 4.2 Explain 단계 강제
**형식:**
```markdown
## Explain (10줄 알고리즘)

### 파일 1: [경로]
- 주요 함수/클래스: [목록]
- 에러 처리: [케이스]

### 파일 2: [경로]
...

승인 요청: 위 구조로 진행해도 되는지 확인 부탁드립니다.
```

**승인 전 코드 작성 금지**

### 4.3 Commit 메시지 형식
```
feat(<scope>): <10-word summary> (Phase <N>)

- IG확보: <항목>
- 파일: <≤5개 나열>
- DoD: <테스트 결과>

Refs: PRD line <N>, phase1~5.txt
```

---

## 5. 의존성 관리

**Phase 1 → Phase 2/3:**
- Output: `taxonomy_nodes`, `taxonomy_edges`, `doc_taxonomy`, `taxonomy_migrations` 테이블
- Verification: `psql \d taxonomy_nodes`

**Phase 2 → Phase 4/5:**
- Output: `GET /taxonomy/versions`, `GET /taxonomy/{version}/tree` 엔드포인트
- Verification: `curl http://127.0.0.1:8001/taxonomy/versions`

---

## 6. 새 세션 시작 시 프로토콜

**파일 읽기 순서 (강제):**
```
1. CLAUDE.md
2. 바이브코딩 문서
3. phase1~5.txt
4. IMPLEMENTATION_MASTER_PLAN.md
5. IMPLEMENTATION_STATUS.md (현재 진행 상황)
6. 다음 Phase Context Sheet
```

---

## 7. 환경 정보

- Working Directory: `C:\MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag`
- Backend: `http://127.0.0.1:8001`
- Frontend: `http://localhost:3000`
- Database: `postgresql+asyncpg://postgres:postgres@localhost:5433/dt_rag_test`

---

**End of Master Plan**
