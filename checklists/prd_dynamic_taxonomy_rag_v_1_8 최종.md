# PRD — Dynamic Taxonomy RAG v1.8.1 (단일 통합 완전 설계서 · PRD)

**문서 상태**: Draft→Review→Baseline _(본 문서는 v1.8 Baseline을 PRD 수준으로 확장한 v1.8.1 초안)_  
**작성일**: 2025-09-02 (KST) · **오너**: Chief Philosopher‑Architect  
**목표 출시(1P)**: 2025-09-16 10:00 (KST) · **1.5P 게이트 심사**: 2025-09-30 18:00 (KST)

---

## 1. 제품 비전 & 성공 기준
### 1.1 비전
"**동적으로 심화되는 다단계 카테고리화(DAG+버전/롤백)**로 지식을 정리하고, **트리형 UI**를 통해 사용자에게 투명하게 노출하며, **선택한 카테고리 범위만 사용하는 전문 에이전트**를 몇 클릭으로 만들고 운영할 수 있는 안전한 지식 운영 제품."

### 1.2 핵심 가치
- **근거 있는 답변**: 출처≥2, 날짜·버전·Confidence 표기(설명가능성).  
- **안전한 운영**: p95≤4s, ≤₩10/쿼리, 정책 100%, 실패 시 즉시 디그레이드/롤백.  
- **유연한 분류**: 정해진 3단(대/중/소) 고정이 아닌 **유동 다단계**(DAG)와 버전 관리.

### 1.3 성공 지표(KPI)
| 구분 | 지표 | 목표(1P) | 비고 |
|---|---|---:|---|
| 품질 | Faithfulness(오프라인) | ≥ 0.85 | RAGAS 기반 골든셋 |
| 성능 | p95 지연 | ≤ 4s | retrieve→rerank→compose 합산 |
| 비용 | 평균 비용/쿼리 | ≤ ₩10 | 모델·툴 호출 포함 |
| 사용성 | CSAT | ≥ 4.3/5.0 | 챗/트리뷰/Agent Factory |
| 운영 | 롤백 TTR | ≤ 15분 | 자동화 스크립트 |

---

## 2. 범위(1P/1.5P) & 비범위
### 2.1 1P(출시)
- 문서 인입/정제/PII 필터/라이선스 태그 · 청킹/임베딩(벡터) · BM25 토큰화.  
- **동적 택소노미(DAG + canonical path)**, `taxonomy_version` 버저닝/ diff/ 롤백.  
- **혼합 분류**(룰→LLM 후보→근거 교차검증→HITL 임계).  
- 하이브리드 검색(BM25+Vector) → **Rerank(50→5)**.  
- **트리형 UI**(버전 드롭다운·diff·되돌리기·Confidence/HITL 보정).  
- **Agent Factory**(트리 노드 선택→카테고리‑한정 에이전트 매니페스트 생성).  
- **LangGraph 7‑Step 오케스트레이션**, Planner‑Executor(+MCP 화이트리스트).  
- **CaseBank(CBR) read‑only** 축적.  
- 관측/평가/디그레이드/카나리(3일/3%)·런북·RBAC/ABAC/감사로그.

### 2.2 1.5P(게이트)
- **Neural Case Selector**(CBR에서 정책 입력으로 승격).  
- **Soft‑Q/밴딧**(보상: 정확/유용/비용/지연) · Debate/툴 사용 확률 정책화.  
- 실패 시 즉시 OFF·롤백, 쿨다운 14일.

### 2.3 비범위(Out of Scope)
- 모델 파인튜닝, 공격적/비인가 크롤링, 결제·정산, 다국어 풀 현지화, 모바일 앱.

---

## 3. 사용자 & 페르소나
| 페르소나 | 목표 | 주요 과업 |
|---|---|---|
| **Ops 관리자** | 카테고리 트리·버전 운영, 품질/비용 가드 | 택소노미 PR 승인, 롤백, 카나리 관제 |
| **도메인 PM/에디터** | 문서 업로드·보정·HITL | 분류 결과 보정, 근거 확인·주석 |
| **전문 사용자(상담/분석)** | 특정 범위로 한정된 에이전트 사용 | 트리 노드 지정→에이전트 생성→챗 사용 |

---

## 4. 사용자 시나리오(Top 12) — Given/When/Then
1) **문서 인입**  
_Given_ CSV/URL/파일 업로드  
_When_ 인입 파이프라인 실행  
_Then_ 라이선스 태그·PII 필터·청킹·임베딩·BM25 토큰 저장.

2) **다단계 분류(혼합)**  
_Given_ 새 청크  
_When_ 룰 1차→LLM 2차 후보→근거 교차검증  
_Then_ `doc_taxonomy`에 (복수)경로·`canonical`·`confidence` 기록, `<0.70`은 HITL 큐로.

3) **트리 확인 & 버전 드롭다운**  
_Given_ 트리뷰  
_When_ `taxonomy_version` 변경  
_Then_ 노드수/Conf/변경내역 갱신·diff 가능.

4) **PR 제안 & 승인**  
_Given_ 에디터가 분류 보정 PR 제안  
_When_ Ops가 검토/승인  
_Then_ 새 버전 생성(`1.4.2 → 1.5.0`).

5) **롤백**  
_Given_ 품질/비용 가드 위반  
_When_ Ops가 롤백 실행  
_Then_ 15분 내 이전 버전으로 복구, 감사로그 기록.

6) **카테고리‑한정 에이전트 생성**  
_Given_ 특정 노드 선택  
_When_ Agent Factory 실행  
_Then_ `manifest.yaml` 생성, retrieval 필터 canonical 강제.

7) **챗 응답(출처·버전·Conf)**  
_Given_ 에이전트 챗  
_When_ 질의 수행  
_Then_ 응답 하단에 출처≥2·날짜·`taxonomy_version`·Confidence.

8) **정확도 우선 모드**  
_When_ 토글 ON  
_Then_ 비용/지연 경고 후 깊은 검색/추가 검증 경로 수행.

9) **HITL 보정**  
_Given_ Conf<0.70  
_When_ 보정 UI에서 수동 라벨  
_Then_ 승인 후 새 버전에 반영.

10) **카나리 릴리스**  
_When_ 1P 코드 프리즈 후  
_Then_ 3일/3% 트래픽, 실패 시 즉시 중단/원복.

11) **관측·알람**  
_When_ p95>4s(1h) or 비용>₩10(1h) or Faithfulness −10%p(24h)  
_Then_ 디그레이드→Debate/학습 OFF→폴백→알람→포스트모템.

12) **보안/프라이버시**  
_When_ R2BF 요청  
_Then_ 데이터 삭제 워크플로·감사 흔적 보존 정책 실행.

---

## 5. 기능 요구사항(Functional)
### 5.1 인입/정제/색인
- 파일/URL 업로드, 중복 방지, 라이선스 태그(`license_tag`), 버전 태그(`version_tag`).  
- PII 마스킹(이메일/전화/주민번호 등 정규식+룰), 비공개 코퍼스 접근 제어.  
- 청킹 기본 500 tokens, overlap 128(도메인별 조정 가능).  
- 임베딩(벡터 1536), BM25 토큰 저장.

### 5.2 동적 택소노미(DAG + canonical)
- 문서/청크는 복수 경로(`path[]`)에 매핑 가능, 집계/권한/메트릭은 `canonical_path` 기준.  
- 버전 관리: MAJOR.MINOR.PATCH, diff 유형(추가/이동/병합/삭제), 롤백 트랜잭션.

### 5.3 분류 파이프라인(혼합)
- 룰 1차(민감도/형태) → LLM 2차(후보+근거≥2) → 교차검증/Conf 산출.  
- Conf<0.70 또는 drift 탐지 시 HITL 큐로 이동.

### 5.4 검색/재순위
- 하이브리드(BM25 `topk=12` + Vector `topk=12`) → 후보 union/dedup.  
- Cross‑Encoder Rerank `50→5` 최종 세트.

### 5.5 오케스트레이션 & 에이전트
- LangGraph 7‑Step: intent→retrieve→plan→(tools/debate)→compose→cite→respond.  
- Agent Factory: 노드 선택→`Agent Manifest` 생성(필터 canonical 강제, debate/HITL 토글).  
- Planner‑Executor(+MCP): 도구 화이트리스트 기반 실행.

### 5.6 프론트엔드
- 트리뷰: 버전 드롭다운, 노드 메타(문서수/Conf/변경일), diff/되돌리기, PR 제안/HITL 큐.  
- Agent Factory: 매니페스트 미리보기/테스트/저장(카탈로그).  
- Chat UI: 출처≥2·날짜·버전·Confidence 고정, 정확도 우선 토글.

### 5.7 관측/운영/릴리스
- Langfuse/메트릭 수집(지연/비용/정확/CSAT/오류).  
- 디그레이드 룰: p95/비용/품질 임계 초과 시 자동 경로 단순화/폴백.  
- 카나리(3일/3%), 실패 시 즉시 중단/원복, 롤백 TTR≤15분.

---

## 6. 비기능 요구사항(NFR)
- **성능**: p95≤4s, p50≤1.5s.  
- **가용성**: 99.5% (업무시간), 유지보수 창 제외.  
- **보안**: RBAC/ABAC, 비밀 관리, 감사로그, IP 허용 목록(옵션).  
- **프라이버시**: PII 마스킹 기본, R2BF 워크플로, 보존 주기 12개월.  
- **신뢰도**: 각 응답에 Confidence 표기, 근거 스니펫.

---

## 7. 정보 구조 & 데이터 모델
### 7.1 핵심 테이블(요약)
- `documents(doc_id, source_url, version_tag, license_tag, created_at)`  
- `chunks(chunk_id, doc_id, text, span, created_at)`  
- `embeddings(chunk_id, vec(1536), bm25_tokens)`  
- `taxonomy_nodes(node_id, label, canonical_path[], version, confidence)`  
- `taxonomy_edges(parent, child, version)`  
- `doc_taxonomy(doc_id, node_id, version, path[], confidence, hitl_required)`  
- `taxonomy_migrations(from_version, to_version, from_path[], to_path[], rationale)`  
- `case_bank(case_id, query, answer, sources(jsonb), category_path[], quality)`

### 7.2 인덱스/제약(필수)
- `embeddings.vec`(ivfflat) · `embeddings.bm25_tokens`(GIN).  
- FK 무결성, `taxonomy_edges(parent,child,version)` PK 복합키.  
- `doc_taxonomy(doc_id, node_id, version)` 고유.

---

## 8. API(요약·예제)
### 8.1 Taxonomy Registry Service(TRS)
- `GET /taxonomy/versions` → `["1.4.2","1.5.0"]`  
- `GET /taxonomy/{version}/tree` → `{nodes:[...], edges:[...]}`  
- `GET /taxonomy/{version}/diff/{base}` → `{added:[...], moved:[...], removed:[...]}`  
- `POST /taxonomy/{version}/rollback` → `{ok:true, rolled_back_to:"1.4.2"}`  
- `POST /classify`(Req: `{chunk_id,text}`) → `canonical, candidates[], hitl`

### 8.2 Search/Retrieve
- `POST /search`(Req: `{q, filters:{canonical_in:[...]}}`) → `{hits:[{chunk_id, score, source:{url,title,date,version}}], latency}`

### 8.3 Agents/Chat
- `POST /agents/from-category`(Req:`{version,node_paths[],options}`) → `Agent Manifest`  
- `POST /chat/run`(Req:`{agent_id, messages[]}`) → `{answer, sources[], confidence, cost, latency}`

---

## 9. UX/UI 요구사항(컴포넌트 수준)
### 9.1 Tree Viewer
- **컴포넌트**: `TreePanel`, `NodeMetaCard`, `VersionDropdown`, `DiffViewer`, `RollbackDialog`, `HITLQueue`.  
- **성능**: 1만 노드 가상 스크롤, p95 렌더 < 200ms.  
- **상태**: Loading/Empty/Error/Out‑of‑date 표시.

### 9.2 Agent Factory
- **필수 옵션**: tools allowlist, debate/HITL 토글, cost guard.  
- **출력**: `manifest.yaml` 미리보기/다운로드, 카탈로그 등록.

### 9.3 Chat UI
- **하단 고정영역**: 출처≥2·날짜·taxonomy_version·Confidence.  
- **정확도 우선 토글**: 경고 모달(비용/지연 증가), 해제 시 기본 경로 복귀.  
- **접근성**: 키보드 네비, 스크린리더 라벨.

---

## 10. 품질/평가 전략
### 10.1 오프라인(사전)
- 골든셋(1k): 쿼리↔정답↔근거 링크, RAGAS/BLEU/Precision@k.  
- 분류 정확/재현, HITL 요구율 ≤ 30%.

### 10.2 온라인(운영)
- A/B: rerank 가중/threshold 실험.  
- 카나리: 3일/3%, 실패 조건 → 즉시 중단/롤백.  
- 메트릭: latency, cost, faithfulness, CSAT, error rate.

---

## 11. 보안/프라이버시/컴플라이언스
- RBAC/ABAC 권한, 서비스 계정/시크릿 저장소, IP 허용 목록(옵션).  
- PII 마스킹, DLP 룰, R2BF 절차: 요청→검증→삭제→증빙 발행.  
- 감사로그: 누가/언제/무엇을.

---

## 12. 릴리스·운영(런북 포함)
- **Feature Flags**: `debate`, `hitl`, `cost_guard`, `softq_auto`, `selector_policy`.  
- **디그레이드 규칙**: p95>4s(1h)·비용>₩10(1h)·Faithfulness −10%p(24h) → Debate/학습 OFF → 소형모델 폴백 → 롤백.  
- **런북**: ① 성능 악화 ② 비용 급증 ③ 품질 하락 ④ 정책 위반 각 케이스별 체크리스트(알림·TTR·책임자·복구 절차).

---

## 13. 로드맵 & 마일스톤(KST)
- **M1 (2025-09-03 12:00)**: API/DDL 동결, 트리/Agent Factory 와이어 확정.  
- **M2 (2025-09-09 18:00)**: 1P 코드 프리즈, 수용 테스트 통과.  
- **M3 (2025-09-12 14:00)**: 카나리 시작(3일/3%).  
- **M4 (2025-09-16 10:00)**: 본적용 or 롤백 결정.  
- **M5 (2025-09-30 18:00)**: 1.5P 게이트 심사(Neural Selector/Soft‑Q 카나리 준비).

---

## 14. 리스크 & 대응
| 리스크 | 영향 | 대응 |
|---|---|---|
| 분류 드리프트 | 품질 저하 | 혼합 분류/교차검증/HITL, 주간 회귀 |
| 과/과소 세분화 | 탐색성/정확도 저하 | 히트 도메인 우선 세분화, 롤백 |
| 비용/지연 악화 | SLO 위반 | 디그레이드·캐시·모델 폴백 |
| 에이전트 스프롤 | 운영 복잡도 | 카탈로그(오너/만료), 승인 워크플로 |

---

## 15. 수용 기준(Acceptance)
- A) p95≤4s / 비용≤₩10 / 정책 100%  
- B) 응답에 출처≥2·날짜·taxonomy_version·Confidence  
- C) 트리 diff/되돌리기·HITL 보정 동작  
- D) 카테고리‑한정 에이전트가 범위 외 자료 접근 차단.

---

## 16. 오픈 이슈/결정 필요(Decision Log)
- [ ] Conf 산식 가중치( rerank vs source agreement vs answer consistency ) 최종 수치  
- [ ] PII 룰셋 범위 확정(국가별)  
- [ ] CaseBank 스키마의 품질 라벨 체계(5점/10점)

---

## 17. 부록(샘플 프롬프트/매니페스트/설정)
- **Classifier JSON 프롬프트**(근거≥2·DAG 후보)  
- **Answer Composer 가이드**(출처·날짜·버전·Confidence 표기)  
- **Agent Manifest 샘플** 및 기본 설정값(`bm25_topk=12`, `vector_topk=12`, `rerank 50→5`, `chunk 500/128`).


### C.4 Alembic 마이그레이션 표준(샘플) (계속)
**초기 스키마(versions/0001_init.py)**
```python
from alembic import op
import sqlalchemy as sa

def upgrade():
  op.execute('CREATE EXTENSION IF NOT EXISTS vector')
  op.create_table('documents',
    sa.Column('doc_id', sa.UUID(), primary_key=True),
    sa.Column('source_url', sa.Text()),
    sa.Column('version_tag', sa.Text()),
    sa.Column('license_tag', sa.Text()),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'))
  )
  op.create_table('chunks',
    sa.Column('chunk_id', sa.UUID(), primary_key=True),
    sa.Column('doc_id', sa.UUID(), sa.ForeignKey('documents.doc_id')),
    sa.Column('text', sa.Text()),
    sa.Column('span', sa.TEXT()),  # int4range 대체 직렬화
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'))
  )
  op.create_table('embeddings',
    sa.Column('chunk_id', sa.UUID(), sa.ForeignKey('chunks.chunk_id'), primary_key=True),
    sa.Column('vec', sa.dialects.postgresql.VECTOR(1536)),
    sa.Column('bm25_tokens', sa.dialects.postgresql.TSVECTOR())
  )
  op.create_table('taxonomy_nodes',
    sa.Column('node_id', sa.UUID(), primary_key=True),
    sa.Column('label', sa.Text()),
    sa.Column('canonical_path', sa.ARRAY(sa.Text())),
    sa.Column('version', sa.Text()),
    sa.Column('confidence', sa.Float())
  )
  op.create_table('taxonomy_edges',
    sa.Column('parent', sa.UUID(), sa.ForeignKey('taxonomy_nodes.node_id'), primary_key=True),
    sa.Column('child', sa.UUID(), sa.ForeignKey('taxonomy_nodes.node_id'), primary_key=True),
    sa.Column('version', sa.Text(), primary_key=True)
  )
  op.create_table('doc_taxonomy',
    sa.Column('doc_id', sa.UUID(), sa.ForeignKey('documents.doc_id')),
    sa.Column('node_id', sa.UUID(), sa.ForeignKey('taxonomy_nodes.node_id')),
    sa.Column('version', sa.Text()),
    sa.Column('path', sa.ARRAY(sa.Text())),
    sa.Column('confidence', sa.Float()),
    sa.Column('hitl_required', sa.Boolean(), server_default=sa.text('false'))
  )
  op.create_table('taxonomy_migrations',
    sa.Column('from_version', sa.Text()),
    sa.Column('to_version', sa.Text()),
    sa.Column('from_path', sa.ARRAY(sa.Text())),
    sa.Column('to_path', sa.ARRAY(sa.Text())),
    sa.Column('rationale', sa.Text()),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'))
  )

def downgrade():
  for t in ['taxonomy_migrations','doc_taxonomy','taxonomy_edges','taxonomy_nodes','embeddings','chunks','documents']:
    op.drop_table(t)
  op.execute('DROP EXTENSION IF EXISTS vector')
```

**버전 마이그레이션 샘플(versions/0002_taxonomy_v150.py)**
```python
from alembic import op
import sqlalchemy as sa

def upgrade():
  # 예: ["AI","RAG","Taxonomy"]를 ["AI","RAG","Knowledge Graph","Taxonomy"]로 이동
  conn = op.get_bind()
  conn.execute(sa.text('''
    INSERT INTO taxonomy_migrations(from_version,to_version,from_path,to_path,rationale)
    VALUES(:f,:t,ARRAY['AI','RAG','Taxonomy'],ARRAY['AI','RAG','Knowledge Graph','Taxonomy'],'KG 하위로 이동')
  '''), dict(f='1.4.2', t='1.5.0'))
```

### C.5 롤백 스크립트(SOP)
1) `SELECT * FROM taxonomy_migrations WHERE to_version=:v`로 변경 집합 검토.  
2) 트랜잭션 시작 → `doc_taxonomy`에서 `to_path`를 `from_path`로 역매핑.  
3) `taxonomy_nodes/edges`에서 신규 노드/엣지 삭제, 병합 전 상태 복원.  
4) 감사로그 기록 후 커밋.  

**예시(PL/pgSQL)**
```sql
CREATE OR REPLACE PROCEDURE rollback_taxonomy(to_v TEXT)
LANGUAGE plpgsql AS $$
DECLARE r RECORD; BEGIN
  FOR r IN SELECT * FROM taxonomy_migrations WHERE to_version=to_v LOOP
    UPDATE doc_taxonomy SET path=r.from_path, version=r.from_version WHERE path=r.to_path AND version=to_v;
  END LOOP;
  DELETE FROM taxonomy_nodes WHERE version=to_v;
  DELETE FROM taxonomy_edges WHERE version=to_v;
END $$;
```

### C.6 데이터 품질 규칙(QC)
- `canonical_path`는 루트→리프, 공백/중복 금지, 길이 1~8.  
- `confidence` ∈ [0,1], `<0.70` 시 `hitl_required=true`.  
- orphan edge/노드 금지(외래키 무결성).  

---

## Annex D — Access & AuthZ (RBAC/ABAC · Secrets · 감사)
### D.1 역할·권한 매트릭스(RBAC)
| Role | Read | Write | Approve | Rollback | Admin |
|---|:--:|:--:|:--:|:--:|:--:|
| Reader | ✅ | ❌ | ❌ | ❌ | ❌ |
| Editor | ✅ | ✅(PR) | ❌ | ❌ | ❌ |
| Ops | ✅ | ✅ | ✅ | ✅ | ❌ |
| Admin | ✅ | ✅ | ✅ | ✅ | ✅ |

### D.2 ABAC 예시
- 리소스: `taxonomy.*`, `doc_taxonomy.*`, `agents.*`  
- 속성: `owner_org`, `dataset_tier(public|internal|restricted)`  
- 정책: `restricted`는 Ops 승인 필요, 에이전트 도구 화이트리스트 제한.

### D.3 비밀/키 관리
- KMS(환경별): `JWT_SIGN_KEY`, `OPENAI_API_KEY`, `DB_URL`  
- 로테이션: 분기 1회, 사고 시 즉시 회수.  
- 감사: 접근 로그 보존 12개월.

---

## Annex E — Test Strategy (단위·계약·통합·E2E·성능)
### E.1 테스트 피라미드
- 단위(Pytest) 60% 이상, 계약(스키마/JSON) 100%, 통합(서비스 간) 20%, E2E 10%.  

### E.2 오프라인 RAG 평가
- 골든셋 1k, Precision@k, Faithfulness, Answer Consistency.  
- 합격선: Faithfulness ≥ 0.85, HITL 요구율 ≤ 30%.

### E.3 온라인 실험
- A/B: rerank candidates 30/50, final_topk 3/5.  
- 카나리: 3일/3% → 실패 조건 즉시 OFF.

### E.4 성능·부하
- 1k 동시 사용 가정, p95≤4s 유지.  
- 혼합부하(읽기 90%, 쓰기 10%), 30분 러닝.

### E.5 체크리스트
- [ ] OpenAPI 스키마 변경 시 contract-test 통과  
- [ ] DB 마이그/롤백 dry-run  
- [ ] 보안/PII 테스트(레드팀 샘플)

---

## Annex F — Capacity & Cost Plan
### F.1 가정(초기)
- 문서 200k, 평균 2.5 청크/문서, 벡터 1536.
- QPS 피크 20, 평균 5.

### F.2 자원 계획(초안)
- DB: pg16 + pgvector, vCPU 4 / RAM 16GB, SSD 200GB.  
- Reranker/LLM: g5.xlarge 등 GPU(선택) 또는 CPU 서빙 + 캐시.  
- 캐시: Redis top‑hits, TTL 10m.

### F.3 비용 모델(주요 항목)
- 임베딩/LLM 토큰, 스토리지/네트워크, 모니터링.  
- 목표: 평균 ₩10/쿼리 이하.

---

## Annex G — Release & Runbooks
### G.1 릴리스 체크리스트
- [ ] OpenAPI/DDL 동결  
- [ ] 마이그/롤백 스크립트 포함  
- [ ] 카나리 구간/트래픽 설정  
- [ ] 알람 임계(p95/cost/faithfulness) 설정

### G.2 카나리 절차(3일/3%)
1) 릴리스 노트 서명 → 2) 3% 트래픽 전환 → 3) 지표 모니터 → 4) 합격 시 100% 승격, 실패 시 롤백.

### G.3 런북(사례)
- **성능 악화**: 모델 단순화→rerank off→소형모델 폴백→알람→포스트모템.  
- **비용 급증**: 캐시 상향→rerank candidates 축소→경보 임계 조정.  
- **품질 하락**: debate ON(게이트)→근거 강화→원인 케이스 분석.

---

## Annex H — Security & Privacy (STRIDE · R2BF)
### H.1 STRIDE 요약
| Threat | 시나리오 | 대응 |
|---|---|---|
| Spoofing | 토큰 탈취 | JWT 만료/회전, mTLS(옵션) |
| Tampering | 마이그 스크립트 변조 | 서명/체크섬, 승인 워크플로 |
| Repudiation | 롤백 부인 | 감사로그 불변 저장 |
| Information Disclosure | PII 노출 | DLP/마스킹, 민감 카테고리 차단 |
| Denial of Service | 과도 트래픽 | 레이트리밋, 캐시, 서킷브레이커 |
| Elevation of Privilege | 권한 상승 | RBAC/ABAC, 최소권한, 승격 로그 |

### H.2 R2BF SOP
1) 요청 접수→2) 신원/권한 확인→3) 삭제 범위 산정→4) `documents/chunks/embeddings/doc_taxonomy` 정합 삭제→5) 증빙 발행→6) 감사로그.

---

## Annex I — UI Spec (컴포넌트/상태/오류)
### I.1 Tree Viewer
- Props: `version`, `nodes[]`, `edges[]`, `onRollback(version)`.  
- 상태: Loading/Empty/Error/OutOfDate.  
- 오류: 404/409/429 매핑, 재시도 UX.

### I.2 Agent Factory
- Props: `selectedPaths[][]`, `options{tools,hitl,debate}`.  
- 출력: `manifest.yaml` 다운로드/카탈로그 등록 이벤트.

### I.3 Chat UI
- 고정 영역: 출처≥2·날짜·버전·Confidence.  
- 토글: 정확도 우선(경고 모달).

---

## Annex J — Governance & RACI
### J.1 PR 워크플로(택소노미)
- 제안(에디터) → 검토(Ops) → 승인(Ops/Admin) → `taxonomy_version` 승격 → 카나리 관제.

### J.2 RACI
| 작업 | R | A | C | I |
|---|---|---|---|---|
| taxonomy 변경 | Editor | Ops | Admin | Reader |
| 롤백 | Ops | Admin | Editor | All |
| 릴리스 | Ops | Admin | Editor | All |

— End of Annexes —

